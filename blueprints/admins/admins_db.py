"""
Fonctions CRUD génériques utilisées par admins_routes.py.

Toutes les fonctions prennent un client Supabase déjà scopé sur l'admin
connecté (g.db, voir admins_auth.build_scoped_client) : c'est ce qui permet
aux policies RLS "Gestion admins des ..." de laisser passer les écritures.
"""
import os
import time
import uuid
import mimetypes
import boto3
from botocore.config import Config
from botocore.exceptions import (
    ConnectionClosedError,
    EndpointConnectionError,
    ReadTimeoutError,
    ConnectTimeoutError,
)
from dotenv import load_dotenv

load_dotenv()

# Ligne temporaire pour vérifier le chargement (à supprimer en production !)
print(f"DEBUG B2_KEY_ID: '{os.environ.get('B2_KEY_ID')}'")

# Config S3 commune : le réseau mobile (Termux) coupe parfois la connexion
# en plein transfert ("Connection was closed before we received a valid
# response"). On mise sur des timeouts plus généreux + plusieurs tentatives
# automatiques côté botocore, doublées d'un retry manuel autour de
# put_object (voir _put_object_with_retry) pour ne pas dépendre uniquement
# du comportement interne de botocore.
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

# Échec de l'envoi de « Fichier audio » : An error occurred (InvalidAccessKeyId) when calling the PutObject operation: Malformed Access Key Id

# Configuration Backblaze B2
B2_KEY_ID = os.environ.get("B2_KEY_ID")
B2_APPLICATION_KEY = os.environ.get("B2_APPLICATION_KEY")
B2_BUCKET_NAME = os.environ.get("B2_BUCKET_NAME", "coja7-audios")
B2_ENDPOINT = os.environ.get("B2_ENDPOINT")
B2_PUBLIC_URL = os.environ.get("B2_PUBLIC_URL")

# Client S3 compatible Backblaze B2
b2_client = boto3.client(
    "s3",
    endpoint_url=B2_ENDPOINT,
    aws_access_key_id=B2_KEY_ID,
    aws_secret_access_key=B2_APPLICATION_KEY,
    config=_S3_CONFIG,
)

_TRANSIENT_S3_ERRORS = (ConnectionClosedError, EndpointConnectionError, ReadTimeoutError, ConnectTimeoutError)


def _put_object_with_retry(client, bucket, key, body_bytes, content_type, content_disposition=None, attempts=4):
    """PUT direct et bufferisé (pas de streaming/multipart) : un seul appel
    HTTP avec un Content-Length connu à l'avance, beaucoup plus robuste
    qu'upload_fileobj sur une connexion mobile instable. Réessaie en cas de
    coupure réseau transitoire, avec un petit backoff entre les tentatives.
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


def upload_audio_to_b2(db, file_storage, folder="sermons"):
    """Envoie un fichier audio vers Backblaze B2 (bucket public) avec téléchargement forcé."""
    if not file_storage or not file_storage.filename:
        return None

    ext = file_storage.filename.rsplit(".", 1)[-1].lower() if "." in file_storage.filename else "mp3"
    filename_only = os.path.basename(file_storage.filename)
    path = f"{folder}/{uuid.uuid4().hex}.{ext}"
    content_type = file_storage.mimetype or mimetypes.guess_type(file_storage.filename)[0] or "audio/mpeg"

    file_storage.stream.seek(0)
    file_bytes = file_storage.read()

    _put_object_with_retry(
        b2_client, B2_BUCKET_NAME, path, file_bytes, content_type,
        content_disposition=f'attachment; filename="{filename_only}"',
    )

    # URL permanente et accessible par tous
    return f"{B2_PUBLIC_URL.rstrip('/')}/{path}"



def delete_audio_by_url(db, url):
    """Supprime un fichier audio du bucket B2 à partir de son URL publique."""
    if not url or not B2_PUBLIC_URL or B2_PUBLIC_URL not in url:
        return
    try:
        path = url.replace(f"{B2_PUBLIC_URL.rstrip('/')}/", "")
        b2_client.delete_object(Bucket=B2_BUCKET_NAME, Key=path)
    except Exception as e:
        print(f"Erreur lors de la suppression sur Backblaze B2: {e}")


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


def upload_file(db, file_storage, folder="uploads"):
    """Envoie un fichier vers Cloudflare R2 et retourne son URL publique.

    file_storage : objet Flask (request.files['xxx'])
    """
    if not file_storage or not file_storage.filename:
        return None

    ext = file_storage.filename.rsplit(".", 1)[-1].lower() if "." in file_storage.filename else "bin"
    path = f"{folder}/{uuid.uuid4().hex}.{ext}"
    content_type = file_storage.mimetype or mimetypes.guess_type(file_storage.filename)[0] or "application/octet-stream"

    file_storage.stream.seek(0)
    file_bytes = file_storage.read()

    # Envoi direct vers Cloudflare R2
    _put_object_with_retry(s3_client, R2_BUCKET_NAME, path, file_bytes, content_type)

    # URL publique accessible par tous les utilisateurs (connectés ou non)
    return f"{R2_PUBLIC_URL.rstrip('/')}/{path}"


def delete_file_by_url(db, url):
    """Supprime un fichier du bucket R2 à partir de son URL publique."""
    if not url or not R2_PUBLIC_URL or R2_PUBLIC_URL not in url:
        return
    try:
        # Extraction du chemin de l'objet dans le bucket à partir de l'URL
        path = url.replace(f"{R2_PUBLIC_URL.rstrip('/')}/", "")
        s3_client.delete_object(Bucket=R2_BUCKET_NAME, Key=path)
    except Exception as e:
        print(f"Erreur lors de la suppression sur Cloudflare R2: {e}")


def counts_summary(db):
    """Compteurs pour le dashboard."""
    summary = {}
    for table in ("events", "communications", "rubrics", "sermons", "galleries"):
        try:
            summary[table] = db.table(table).select("id", count="exact").execute().count or 0
        except Exception:
            summary[table] = None
    return summary
