from datetime import datetime

from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, g, abort, jsonify
)
import re
from .admins_auth import login_admin, logout_admin, login_required, super_admin_required
from .admins_config import CONTENT_TYPES, get_content_type
from . import admins_db as db_ops

bp_admins = Blueprint(
    "admins",
    __name__,
    url_prefix="/admin",
    template_folder="../../templates/admin",
    static_folder="../../static",
)


@bp_admins.app_template_filter("admin_datetime_local")
def admin_datetime_local(value):
    """Formate une date ISO Supabase pour un <input type="datetime-local">."""
    if not value:
        return ""
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%dT%H:%M")
    except (ValueError, AttributeError):
        return ""


# ---------------------------------------------------------------------------
# Authentification
# ---------------------------------------------------------------------------

@bp_admins.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        admin, error = login_admin(email, password)
        if error:
            flash(error, "error")
            return render_template("admin/login.html", email=email)
        return redirect(request.args.get("next") or url_for("admins.dashboard"))

    return render_template("admin/login.html")


@bp_admins.route("/logout")
def logout():
    logout_admin()
    return redirect(url_for("admins.login"))


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@bp_admins.route("/")
@login_required
def dashboard():
    counts = db_ops.counts_summary(g.db)
    return render_template(
        "admin/dashboard.html",
        counts=counts,
        content_types=CONTENT_TYPES,
    )

# ---------------------------------------------------------------------------
# CRUD générique, piloté par admins_config.CONTENT_TYPES
# ---------------------------------------------------------------------------
def _extract_youtube_id(value):
    """Extrait l'ID d'une vidéo YouTube depuis une URL ou retourne l'ID tel quel."""
    if not value:
        return None

    value = value.strip()

    # Déjà un ID YouTube
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", value):
        return value

    patterns = [
        r"(?:youtube\.com/watch\?v=)([A-Za-z0-9_-]{11})",
        r"(?:youtu\.be/)([A-Za-z0-9_-]{11})",
        r"(?:youtube\.com/embed/)([A-Za-z0-9_-]{11})",
        r"(?:youtube\.com/shorts/)([A-Za-z0-9_-]{11})",
    ]

    for pattern in patterns:
        match = re.search(pattern, value)
        if match:
            return match.group(1)

    return None

def _parse_form(fields, form):
    """Convertit un formulaire HTML en payload prêt pour Supabase."""
    payload = {}

    for field in fields:
        name = field["name"]
        ftype = field["type"]

        if ftype in ("image", "audio"):
            continue

        if ftype == "relation":
            value = form.get(name) or None
            payload[name] = value
            continue

        value = form.get(name, "")
        if name == "youtube_id":
            payload[name] = _extract_youtube_id(value)
            continue        

        if name == "hero_media_type":
            payload[name] = value or None

        elif ftype == "datetime" and value:
            try:
                payload[name] = datetime.fromisoformat(value).isoformat()
            except ValueError:
                payload[name] = None

        elif value == "" and ftype in ("date", "datetime"):
            payload[name] = None

        else:
            payload[name] = value

    return payload


@bp_admins.route("/<content_key>")
@login_required
def content_list(content_key):
    ct = get_content_type(content_key)
    if not ct:
        abort(404)
    rows = db_ops.list_rows(g.db, ct["table"], order_by=ct.get("order_by"), order_desc=ct.get("order_desc", False))
    return render_template("admin/list.html", ct=ct, rows=rows)


@bp_admins.route("/<content_key>/new", methods=["GET", "POST"])
@login_required
def content_new(content_key):
    ct = get_content_type(content_key)
    if not ct:
        abort(404)

    relation_options = _relation_options(ct)

    if request.method == "POST":
        payload = _parse_form(ct["fields"], request.form)
        # Dans content_new et content_edit :
        for field in ct["fields"]:
            file_obj = request.files.get(field["name"])
            if field["type"] == "image":
                uploaded = db_ops.upload_file(g.db, file_obj, folder=ct["table"])
                if uploaded:
                    payload[field["name"]] = uploaded
            elif field["type"] == "audio":
                uploaded = db_ops.upload_audio_to_b2(g.db, file_obj, folder=ct["table"])
                if uploaded:
                    payload[field["name"]] = uploaded

        try:
            db_ops.create_row(g.db, ct["table"], payload)
            flash(f"{ct['label_singular'].capitalize()} créé·e avec succès.", "success")
            return redirect(url_for("admins.content_list", content_key=content_key))
        except Exception as e:
            flash(f"Erreur lors de la création : {e}", "error")

    return render_template("admin/form.html", ct=ct, row=None, relation_options=relation_options)

@bp_admins.route("/<content_key>/<row_id>/edit", methods=["GET", "POST"])
@login_required
def content_edit(content_key, row_id):
    ct = get_content_type(content_key)
    if not ct:
        abort(404)

    row = db_ops.get_row(g.db, ct["table"], row_id)
    if not row:
        abort(404)

    relation_options = _relation_options(ct)

    if request.method == "POST":
        payload = _parse_form(ct["fields"], request.form)
        for field in ct["fields"]:
            if field["type"] == "image":
                file_obj = request.files.get(field["name"])
                # --- CODE MODIFIÉ ICI ---
                if file_obj and file_obj.filename:
                    if field["type"] == "image":
                        uploaded = db_ops.upload_file(g.db, file_obj, folder=ct["table"])
                        if uploaded:
                            payload[field["name"]] = uploaded
                    elif field["type"] == "audio":
                        uploaded = db_ops.upload_audio_to_b2(g.db, file_obj, folder=ct["table"])
                        if uploaded:
                            payload[field["name"]] = uploaded
            # sinon : on garde l'URL existante, on ne l'écrase pas
        try:
            db_ops.update_row(g.db, ct["table"], row_id, payload)
            flash(f"{ct['label_singular'].capitalize()} mis·e à jour.", "success")
            return redirect(url_for("admins.content_list", content_key=content_key))
        except Exception as e:
            flash(f"Erreur lors de la mise à jour : {e}", "error")

    return render_template("admin/form.html", ct=ct, row=row, relation_options=relation_options)


@bp_admins.route("/<content_key>/<row_id>/delete", methods=["POST"])
@login_required
def content_delete(content_key, row_id):
    ct = get_content_type(content_key)
    if not ct:
        abort(404)
    try:
        db_ops.delete_row(g.db, ct["table"], row_id)
        flash(f"{ct['label_singular'].capitalize()} supprimé·e.", "success")
    except Exception as e:
        flash(f"Erreur lors de la suppression : {e}", "error")
    return redirect(url_for("admins.content_list", content_key=content_key))


def _relation_options(ct):
    options = {}
    for field in ct["fields"]:
        if field["type"] == "relation":
            options[field["name"]] = db_ops.list_relation_options(
                g.db, field["relation_table"], field["relation_label"]
            )
    return options


# ---------------------------------------------------------------------------
# Galeries : gestion des médias (media_items) — cas particulier imbriqué
# ---------------------------------------------------------------------------

@bp_admins.route("/galleries/<gallery_id>/media", methods=["GET", "POST"])
@login_required
def gallery_media(gallery_id):
    gallery = db_ops.get_row(g.db, "galleries", gallery_id)
    if not gallery:
        abort(404)

    if request.method == "POST":
        files = request.files.getlist("files")
        media_type = request.form.get("type", "photo")
        credit = request.form.get("credit", "")
        existing = g.db.table("media_items").select("display_order").eq("gallery_id", gallery_id).execute().data or []
        next_order = (max((m["display_order"] or 0) for m in existing) + 1) if existing else 0

        uploaded_count = 0
        for f in files:
            if not f or not f.filename:
                continue
            url = db_ops.upload_file(g.db, f, folder=f"galleries/{gallery_id}")
            if not url:
                continue
            g.db.table("media_items").insert({
                "gallery_id": gallery_id,
                "type": media_type,
                "media_url": url,
                "credit": credit,
                "display_order": next_order,
            }).execute()
            next_order += 1
            uploaded_count += 1

        if uploaded_count:
            flash(f"{uploaded_count} média(s) ajouté(s).", "success")
        else:
            flash("Aucun fichier valide n'a été envoyé.", "error")
        return redirect(url_for("admins.gallery_media", gallery_id=gallery_id))

    media_items = (
        g.db.table("media_items")
        .select("*")
        .eq("gallery_id", gallery_id)
        .order("display_order")
        .execute()
        .data
        or []
    )
    return render_template("admin/gallery_media.html", gallery=gallery, media_items=media_items)


@bp_admins.route("/galleries/<gallery_id>/media/<media_id>/delete", methods=["POST"])
@login_required
def gallery_media_delete(gallery_id, media_id):
    item = db_ops.get_row(g.db, "media_items", media_id)
    if item:
        db_ops.delete_file_by_url(g.db, item.get("media_url"))
        db_ops.delete_row(g.db, "media_items", media_id)
        flash("Média supprimé.", "success")
    return redirect(url_for("admins.gallery_media", gallery_id=gallery_id))


# ---------------------------------------------------------------------------
# Contenu "à la une" (featured_content)
# ---------------------------------------------------------------------------

FEATURED_TYPE_TABLE = {
    "event": "events",
    "sermon": "sermons",
    "communication": "communications",
    "rubric": "rubrics",
}

@bp_admins.route("/featured", methods=["GET", "POST"])
@login_required
def featured():
    if request.method == "POST":
        content_type = request.form.get("content_type")
        content_id = request.form.get("content_id")
        if content_type in FEATURED_TYPE_TABLE and content_id:
            g.db.table("featured_content").upsert(
                {
                    "content_type": content_type,
                    "content_id": content_id,
                    "display_order": int(request.form.get("display_order") or 0),
                },
                on_conflict="content_type, content_id"  # <--- Spécifier les deux colonnes de la contrainte
            ).execute()
            flash("Contenu ajouté à la une.", "success")
        return redirect(url_for("admins.featured"))

    current = (
        g.db.table("featured_content").select("*").order("display_order").execute().data or []
    )
    # Options disponibles par type, pour le formulaire d'ajout
    options_by_type = {
        ftype: db_ops.list_relation_options(g.db, table, "title")
        for ftype, table in FEATURED_TYPE_TABLE.items()
    }
    return render_template("admin/featured.html", current=current, options_by_type=options_by_type)


@bp_admins.route("/featured/<featured_id>/delete", methods=["POST"])
@login_required
def featured_delete(featured_id):
    db_ops.delete_row(g.db, "featured_content", featured_id)
    flash("Retiré de la une.", "success")
    return redirect(url_for("admins.featured"))


# ---------------------------------------------------------------------------
# Gestion des comptes admins (super_admin uniquement)
# ---------------------------------------------------------------------------

@bp_admins.route("/team")
@super_admin_required
def team():
    admins = g.db.table("admins").select("*").order("created_at").execute().data or []
    return render_template("admin/team.html", admins=admins)


@bp_admins.route("/team/<admin_id>/toggle-active", methods=["POST"])
@super_admin_required
def team_toggle_active(admin_id):
    row = db_ops.get_row(g.db, "admins", admin_id)
    if row:
        db_ops.update_row(g.db, "admins", admin_id, {"is_active": not row.get("is_active", True)})
        flash("Statut mis à jour.", "success")
    return redirect(url_for("admins.team"))


@bp_admins.route("/team/<admin_id>/role", methods=["POST"])
@super_admin_required
def team_update_role(admin_id):
    role = request.form.get("role")
    if role in ("super_admin", "admin", "editor"):
        db_ops.update_row(g.db, "admins", admin_id, {"role": role})
        flash("Rôle mis à jour.", "success")
    return redirect(url_for("admins.team"))
