"""
Fonctions CRUD génériques utilisées par admins_routes.py.

Toutes les fonctions prennent un client Supabase déjà scopé sur l'admin
connecté (g.db, voir admins_auth.build_scoped_client) : c'est ce qui permet
aux policies RLS "Gestion admins des ..." de laisser passer les écritures.
"""
import os
import io
import time
import uuid
import hashlib
import mimetypes
import boto3
from boto3.s3.transfer import TransferConfig
from botocore.config import Config
from botocore.exceptions import (
    ClientError,
    ConnectionClosedError,
    EndpointConnectionError,
    ReadTimeoutError,
    ConnectTimeoutError,
)
from dotenv import load_dotenv

# Backblaze B2 : librairie native (pas boto3/S3-compatible — voir la note
# au-dessus de upload_audio_to_b2 pour l'historique de ce choix).
from b2sdk.v2 import InMemoryAccountInfo, B2Api

load_dotenv()

# Config S3 commune : le réseau mobile (Termux) coupe parfois la connexion
# en plein transfert. On mise sur des timeouts plus généreux + plusieurs
# tentatives automatiques côté botocore, doublées d'un retry manuel (voir
# _put_object_with_retry / _upload_fileobj_with_retry) pour ne pas dépendre
# uniquement du comportement interne de botocore.
_S3_CONFIG = Config(
    signature_version="s3v4",
    connect_timeout=15,
    read_timeout=120,
    retries={"max_attempts": 4, "mode": "standard"},
)

# Configuration Cloudflare R2 via variables d'environnement
R2_ACCOUNT_ID = os.environ.get("R2_ACCOUNT_ID")
R2_ACCESS_KEY_ID = os.environ.get("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.environ.get("R2_SECRET_ACCESS_KEY")
R2_BUCKET_NAME = os.environ.get("R2_BUCKET_NAME", "coja7-stockage multimedia")
R2_PUBLIC_URL = os.environ.get("R2_PUBLIC_URL")

# Client S3 compatible Cloudflare R2
s3_client = boto3.client(
    "s3",
    endpoint_url=f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
    aws_access_key_id=R2_ACCESS_KEY_ID,
    aws_secret_access_key=R2_SECRET_ACCESS_KEY,
    region_name="auto",
    config=_S3_CONFIG,
)

# Configuration Backblaze B2 — voir la note au-dessus de upload_audio_to_b2
B2_KEY_ID = os.environ.get("B2_KEY_ID")
B2_APPLICATION_KEY = os.environ.get("B2_APPLICATION_KEY")
B2_BUCKET_NAME = os.environ.get("B2_BUCKET_NAME", "coja7-audios")
B2_PUBLIC_URL = os.environ.get("B2_PUBLIC_URL")


def _get_b2sdk_bucket():
    """Ré-autorise à chaque appel plutôt que de garder un client en cache :
    plus lent (un aller-retour d'auth en plus) mais évite tout souci de
    jeton expiré sur un outil admin à faible trafic — la simplicité prime
    ici sur la micro-optimisation."""
    info = InMemoryAccountInfo()
    api = B2Api(info)
    api.authorize_account("production", B2_KEY_ID, B2_APPLICATION_KEY)
    return api.get_bucket_by_name(B2_BUCKET_NAME)


def _force_connection_close(request, **kwargs):
    """Empêche botocore/urllib3 de réutiliser une connexion HTTP existante
    pour R2. (N'a pas suffi pour B2, qui est passé sur b2sdk — voir plus
    bas — mais coûte rien à garder ici pour R2.)"""
    request.headers["Connection"] = "close"


s3_client.meta.events.register("before-sign.s3", _force_connection_close)

_TRANSIENT_S3_ERRORS = (ConnectionClosedError, EndpointConnectionError, ReadTimeoutError, ConnectTimeoutError)

# Pour B2 spécifiquement : un PUT unique sur un gros fichier audio doit tenir
# la connexion ouverte sans interruption pendant tout le transfert — sur un
# réseau mobile instable, c'est justement ce genre de transfert long qui se
# fait couper. On envoie plutôt par blocs de 5 Mo (minimum S3), un seul à la
# fois (pas de connexions parallèles qui se battent pour la même bande
# passante) : si un bloc échoue, seul ce bloc est retenté par botocore, pas
# tout le fichier.
# NB : ce réglage ne sert plus qu'à R2 en théorie (B2 est passé sur b2sdk,
# voir upload_audio_to_b2) ; laissé disponible si un futur fichier R2
# volumineux en avait besoin.
_CHUNKED_TRANSFER_CONFIG = TransferConfig(
    multipart_threshold=5 * 1024 * 1024,
    multipart_chunksize=5 * 1024 * 1024,
    max_concurrency=1,
    use_threads=False,
)


def _content_key(folder, content_bytes, ext):
    """Nom de fichier dérivé du contenu (hash SHA-256) plutôt qu'aléatoire :
    deux envois du même fichier donnent la même clé, ce qui permet de
    détecter les doublons avant de renvoyer quoi que ce soit (voir
    _object_exists)."""
    digest = hashlib.sha256(content_bytes).hexdigest()
    return f"{folder}/{digest}.{ext}"


def _object_exists(client, bucket, key):
    try:
        client.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as e:
        code = str(e.response.get("Error", {}).get("Code", ""))
        if code in ("404", "NoSuchKey", "NotFound"):
            return False
        # Erreur inattendue (permissions, réseau...) : on ne bloque pas
        # l'upload pour autant, on suppose juste "pas encore là".
        return False
    except Exception:
        return False


def _put_object_with_retry(client, bucket, key, body_bytes, content_type, content_disposition=None, attempts=4):
    """PUT direct et bufferisé (pas de streaming/multipart) : un seul appel
    HTTP avec un Content-Length connu à l'avance. Adapté aux fichiers
    plutôt petits (images, PDF) où un aller-retour unique reste rapide.
    """
    kwargs = {"Bucket": bucket, "Key": key, "Body": body_bytes, "ContentType": content_type}
    if content_disposition:
        kwargs["ContentDisposition"] = content_disposition

    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            client.put_object(**kwargs)
            return
        except _TRANSIENT_S3_ERRORS as exc:
            last_error = exc
            if attempt < attempts:
                time.sleep(0.7 * attempt)
    raise last_error


def _upload_fileobj_with_retry(client, bucket, key, body_bytes, content_type, content_disposition=None,
                                transfer_config=None, attempts=3):
    """Envoi par blocs (voir _CHUNKED_TRANSFER_CONFIG) pour les fichiers plus
    volumineux (audio). Chaque bloc bénéficie déjà des tentatives
    automatiques du client (_S3_CONFIG.retries) ; on ajoute ici un dernier
    filet de sécurité qui relance l'upload entier si toute la tentative de
    transfert s'est écroulée.
    """
    extra_args = {"ContentType": content_type}
    if content_disposition:
        extra_args["ContentDisposition"] = content_disposition

    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            client.upload_fileobj(
                io.BytesIO(body_bytes), bucket, key,
                ExtraArgs=extra_args, Config=transfer_config,
            )
            return
        except _TRANSIENT_S3_ERRORS as exc:
            last_error = exc
            if attempt < attempts:
                time.sleep(1.2 * attempt)
    raise last_error


def _compress_pdf_bytes(file_bytes):
    """Compresse un PDF (flux de contenu des pages) avant envoi. En cas
    d'échec (PDF chiffré, corrompu, pypdf absent...), renvoie l'original
    tel quel plutôt que de bloquer l'envoi."""
    try:
        from pypdf import PdfReader, PdfWriter
    except ImportError:
        return file_bytes

    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        writer = PdfWriter()
        for page in reader.pages:
            try:
                page.compress_content_streams()
            except Exception:
                pass
            writer.add_page(page)
        out = io.BytesIO()
        writer.write(out)
        compressed = out.getvalue()
        # Ne garde la version compressée que si elle est vraiment plus légère
        return compressed if 0 < len(compressed) < len(file_bytes) else file_bytes
    except Exception:
        return file_bytes


# ---------------------------------------------------------------------------
# Uploads — Cloudflare R2 (images, vidéos, PDF)
# ---------------------------------------------------------------------------

def upload_file(db, file_storage, folder="uploads"):
    """Envoie un fichier vers Cloudflare R2 et retourne son URL publique.

    Dédoublonnage : la clé de l'objet est dérivée du contenu du fichier
    (hash SHA-256). Si un fichier identique existe déjà dans le bucket, on
    ne le renvoie pas — on renvoie directement son URL existante.
    """
    if not file_storage or not file_storage.filename:
        return None

    ext = file_storage.filename.rsplit(".", 1)[-1].lower() if "." in file_storage.filename else "bin"
    content_type = file_storage.mimetype or mimetypes.guess_type(file_storage.filename)[0] or "application/octet-stream"

    file_storage.stream.seek(0)
    file_bytes = file_storage.read()
    path = _content_key(folder, file_bytes, ext)

    if not _object_exists(s3_client, R2_BUCKET_NAME, path):
        _put_object_with_retry(s3_client, R2_BUCKET_NAME, path, file_bytes, content_type)

    return f"{R2_PUBLIC_URL.rstrip('/')}/{path}"


def upload_bytes_to_r2(file_bytes, content_type, folder="uploads", ext="bin"):
    """Variante de upload_file qui part directement de bytes en mémoire
    (utile pour les vignettes générées côté client, envoyées en Blob)."""
    if not file_bytes:
        return None
    path = _content_key(folder, file_bytes, ext)
    if not _object_exists(s3_client, R2_BUCKET_NAME, path):
        _put_object_with_retry(s3_client, R2_BUCKET_NAME, path, file_bytes, content_type)
    return f"{R2_PUBLIC_URL.rstrip('/')}/{path}"


def upload_pdf_to_r2(db, file_storage, folder="documents"):
    """Compresse puis envoie un PDF vers Cloudflare R2 (dédoublonné comme
    upload_file, sur le contenu déjà compressé)."""
    if not file_storage or not file_storage.filename:
        return None

    filename_only = os.path.basename(file_storage.filename)
    file_storage.stream.seek(0)
    original_bytes = file_storage.read()
    compressed_bytes = _compress_pdf_bytes(original_bytes)

    path = _content_key(folder, compressed_bytes, "pdf")
    if not _object_exists(s3_client, R2_BUCKET_NAME, path):
        _put_object_with_retry(
            s3_client, R2_BUCKET_NAME, path, compressed_bytes, "application/pdf",
            content_disposition=f'inline; filename="{filename_only}"',
        )
    return f"{R2_PUBLIC_URL.rstrip('/')}/{path}"


def delete_file_by_url(db, url):
    """Supprime un fichier du bucket R2 à partir de son URL publique."""
    if not url or not R2_PUBLIC_URL or R2_PUBLIC_URL not in url:
        return
    try:
        path = url.replace(f"{R2_PUBLIC_URL.rstrip('/')}/", "")
        s3_client.delete_object(Bucket=R2_BUCKET_NAME, Key=path)
    except Exception as e:
        print(f"Erreur lors de la suppression sur Cloudflare R2: {e}")


# ---------------------------------------------------------------------------
# Uploads — Backblaze B2 (audio)
# ---------------------------------------------------------------------------

def upload_audio_to_b2(db, file_storage, folder="sermons"):
    """Envoie un fichier audio vers Backblaze B2, avec dédoublonnage par
    hash.

    Historique : les deux premières versions passaient par boto3 en mode
    "compatible S3" (un PUT unique, puis un envoi par blocs) — les deux ont
    échoué de façon identique sur ce réseau, toujours en pleine attente de
    la réponse, jamais pendant l'envoi du fichier lui-même. Le CLI officiel
    `b2` (qui utilise b2sdk, pas boto3) a réussi sans problème sur le même
    réseau avec le même fichier : le souci était donc dans boto3/botocore
    lui-même, pas dans le réseau. D'où ce choix de b2sdk.
    """
    if not file_storage or not file_storage.filename:
        return None

    ext = file_storage.filename.rsplit(".", 1)[-1].lower() if "." in file_storage.filename else "mp3"
    filename_only = os.path.basename(file_storage.filename)
    content_type = file_storage.mimetype or mimetypes.guess_type(file_storage.filename)[0] or "audio/mpeg"

    file_storage.stream.seek(0)
    file_bytes = file_storage.read()
    path = _content_key(folder, file_bytes, ext)

    bucket = _get_b2sdk_bucket()

    exists = False
    try:
        bucket.get_file_info_by_name(path)
        exists = True
    except Exception:
        exists = False

    if not exists:
        last_error = None
        for attempt in range(1, 4):
            try:
                bucket.upload_bytes(
                    file_bytes,
                    path,
                    content_type=content_type,
                    file_info={"b2-content-disposition": f'attachment; filename="{filename_only}"'},
                )
                last_error = None
                break
            except Exception as exc:
                last_error = exc
                if attempt < 3:
                    time.sleep(1.0 * attempt)
        if last_error:
            raise last_error

    return f"{B2_PUBLIC_URL.rstrip('/')}/{path}"


def delete_audio_by_url(db, url):
    """Supprime un fichier audio du bucket B2 à partir de son URL publique."""
    if not url or not B2_PUBLIC_URL or B2_PUBLIC_URL not in url:
        return
    try:
        path = url.replace(f"{B2_PUBLIC_URL.rstrip('/')}/", "")
        bucket = _get_b2sdk_bucket()
        file_version = bucket.get_file_info_by_name(path)
        bucket.delete_file_version(file_version.id_, file_version.file_name)
    except Exception as e:
        print(f"Erreur lors de la suppression sur Backblaze B2: {e}")


# ---------------------------------------------------------------------------
# CRUD générique
# ---------------------------------------------------------------------------

def list_rows(db, table, order_by=None, order_desc=False, limit=100):
    query = db.table(table).select("*")
    if order_by:
        query = query.order(order_by, desc=order_desc)
    return query.limit(limit).execute().data or []


def get_row(db, table, row_id):
    res = db.table(table).select("*").eq("id", row_id).execute().data
    return res[0] if res else None


def create_row(db, table, payload):
    return db.table(table).insert(payload).execute().data[0]


def update_row(db, table, row_id, payload):
    return db.table(table).update(payload).eq("id", row_id).execute().data


def delete_row(db, table, row_id):
    return db.table(table).delete().eq("id", row_id).execute()


def list_relation_options(db, table, label_field, limit=200):
    """Pour les champs de type 'relation' (ex: choisir un événement lié)."""
    rows = (
        db.table(table)
        .select(f"id,{label_field}")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
        .data
        or []
    )
    return [{"id": r["id"], "label": r.get(label_field) or r["id"]} for r in rows]


def list_distinct_values(db, table, field, limit=300):
    """Pour les champs de type 'text_suggest' (ex: catégories des
    rubriques) : valeurs déjà utilisées dans la colonne, pour alimenter les
    suggestions sans forcer un choix figé (contrairement à 'relation')."""
    rows = db.table(table).select(field).limit(limit).execute().data or []
    seen = []
    for r in rows:
        value = (r.get(field) or "").strip()
        if value and value not in seen:
            seen.append(value)
    return sorted(seen, key=str.lower)


def counts_summary(db):
    """Compteurs pour le dashboard."""
    summary = {}
    for table in ("events", "communications", "rubrics", "sermons", "galleries"):
        try:
            summary[table] = db.table(table).select("id", count="exact").execute().count or 0
        except Exception:
            summary[table] = None
    return summary
