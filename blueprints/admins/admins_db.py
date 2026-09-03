"""
Fonctions CRUD génériques utilisées par admins_routes.py.

Toutes les fonctions prennent un client Supabase déjà scopé sur l'admin
connecté (g.db, voir admins_auth.build_scoped_client) : c'est ce qui permet
aux policies RLS "Gestion admins des ..." de laisser passer les écritures.
"""
import os
import uuid
import mimetypes
import boto3
from botocore.config import Config
from dotenv import load_dotenv

load_dotenv()

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
    config=Config(signature_version="s3v4")
)


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

    # Envoi direct vers Cloudflare R2
    s3_client.upload_fileobj(
        file_storage,
        R2_BUCKET_NAME,
        path,
        ExtraArgs={"ContentType": content_type}
    )

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
