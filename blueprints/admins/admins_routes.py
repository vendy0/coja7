from datetime import datetime
import time

from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, g, abort, jsonify, session
)
import re
from . import admins_auth
from .admins_auth import (
    login_admin, logout_admin, login_required, super_admin_required,
    get_csrf_token, verify_csrf_token,
)
from .admins_config import CONTENT_TYPES, get_content_type
from . import admins_db as db_ops
from . import admins_service

# Limite de tentatives de connexion, en mémoire — suffisant pour un seul
# processus (dev, ou un VPS avec un seul worker gunicorn dédié au login).
# Avec plusieurs workers/processus en prod, chacun aurait son propre
# compteur ; passer par un stockage partagé (Redis...) serait plus robuste
# à ce moment-là, mais serait de la sur-ingénierie pour ce projet aujourd'hui.
_login_attempts = {}
LOGIN_MAX_ATTEMPTS = 5
LOGIN_WINDOW_SECONDS = 300  # 5 minutes

# Rows per page on admin list views (see content_list)
PAGE_SIZE = 30


def _is_login_rate_limited(ip):
    now = time.time()
    attempts = [t for t in _login_attempts.get(ip, []) if now - t < LOGIN_WINDOW_SECONDS]
    _login_attempts[ip] = attempts
    return len(attempts) >= LOGIN_MAX_ATTEMPTS


def _record_login_failure(ip):
    _login_attempts.setdefault(ip, []).append(time.time())

bp_admins = Blueprint(
    "admins",
    __name__,
    url_prefix="/admin",
    template_folder="../../templates/admin",
    static_folder="../../static",
)


bp_admins.add_app_template_global(get_csrf_token, name="csrf_token")

ROLES = {
    "editor": "Éditeur",
    "admin": "Administrateur"
}
ROLE_EXTENDED = {
    "editor": "Éditeur",
    "admin": "Administrateur",
    "super_admin": "Super Administrateur"
}

@bp_admins.app_context_processor
def inject_roles():
    return {"roles": ROLES}
    
@bp_admins.before_request
def _enforce_csrf():
    """Vérifie le jeton CSRF sur chaque POST admin. Le login est exempté :
    il n'y a pas encore de session/jeton avant la connexion elle-même, et
    forcer une action de connexion n'est pas le scénario que CSRF protège
    (l'attaquant utiliserait ses propres identifiants, pas ceux de la
    victime)."""
    if request.method != "POST" or request.endpoint == "admins.login":
        return
    token = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token")
    if not verify_csrf_token(token):
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify(ok=False, error="Session expirée — recharge la page."), 403
        abort(403)


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
        ip = request.remote_addr
        if _is_login_rate_limited(ip):
            flash("Trop de tentatives — réessaie dans quelques minutes.", "error")
            return render_template("admin/login.html")

        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        admin, error = login_admin(email, password)
        if error:
            _record_login_failure(ip)
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

        if ftype in ("image", "audio", "pdf"):
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

    query = request.args.get("q", "").strip()
    page = max(request.args.get("page", 1, type=int) or 1, 1)

    if query:
        # Search filtering happens in Python (see below), so the Supabase
        # query itself can't be paginated in this branch — we'd risk
        # missing matches sitting on a page we didn't fetch. Instead: pull
        # a large-enough batch, filter it, then paginate the filtered
        # Python list. Fine at this project's scale; would need a real
        # SQL-side filter (ilike/or_) if a table ever grew into the
        # thousands of rows.
        all_rows = db_ops.list_rows(
            g.db, ct["table"], order_by=ct.get("order_by"), order_desc=ct.get("order_desc", False), limit=500
        )
        q_lower = query.lower()
        searchable_fields = [name for name, _ in ct["list_columns"]]
        matched = [
            row for row in all_rows
            if any(q_lower in str(row.get(field) or "").lower() for field in searchable_fields)
        ]
        total = len(matched)
        start = (page - 1) * PAGE_SIZE
        rows = matched[start:start + PAGE_SIZE]
    else:
        total = db_ops.count_rows(g.db, ct["table"])
        offset = (page - 1) * PAGE_SIZE
        rows = db_ops.list_rows(
            g.db, ct["table"], order_by=ct.get("order_by"), order_desc=ct.get("order_desc", False),
            limit=PAGE_SIZE, offset=offset,
        )

    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)

    return render_template(
        "admin/list.html", ct=ct, rows=rows, query=query, page=page, total_pages=total_pages
    )


def _format_date_fr(iso_string):
    """Formate une date ISO en JJ/MM/AAAA HH:MM — utilisé pour les réponses
    JSON (voir messages(), appelée en AJAX) où le filtre Jinja date_fr des
    templates ne s'applique pas."""
    if not iso_string:
        return ""
    try:
        dt = datetime.fromisoformat(str(iso_string).replace("Z", "+00:00"))
        return dt.strftime("%d/%m/%Y %H:%M")
    except (ValueError, TypeError):
        return str(iso_string)


def _apply_uploads(ct, payload):
    """Traite les champs de type image/audio/pdf du formulaire : upload
    vers R2 ou B2, puis injection de l'URL obtenue dans le payload.

    Si le champ a déjà été envoyé en amont via AJAX (voir upload_field +
    static/js/admin/admin-file-upload.js — barre de progression, retry sans
    recharger la page), un champ caché "<name>__uploaded_url" porte déjà
    l'URL : on la réutilise directement sans repasser par R2/B2. Sinon on
    retombe sur l'envoi classique à la soumission du formulaire (ça marche
    même si JS est indisponible).

    Ne touche jamais un champ sans fichier sélectionné (l'URL existante,
    le cas échéant, reste en base puisqu'on n'ajoute simplement pas la clé
    au payload).

    Retourne un message d'erreur (str) si un envoi a échoué, sinon None —
    pour ne jamais afficher "succès" alors qu'un média n'a pas été envoyé.

    NB : cette fonction est utilisée par content_new ET content_edit. Ne
    pas dupliquer cette boucle ailleurs — la dernière fois qu'elle a été
    dupliquée avec un if imbriqué par erreur, l'audio a arrêté de
    s'envoyer en modification sans qu'aucune erreur ne s'affiche.
    """
    for field in ct["fields"]:
        if field["type"] not in ("image", "audio", "pdf"):
            continue

        pre_uploaded = request.form.get(field["name"] + "__uploaded_url")
        if pre_uploaded:
            payload[field["name"]] = pre_uploaded
            continue

        file_obj = request.files.get(field["name"])
        if not file_obj or not file_obj.filename:
            continue
        try:
            if field["type"] == "image":
                uploaded = db_ops.upload_file(g.db, file_obj, folder=ct["table"])
            elif field["type"] == "pdf":
                uploaded = db_ops.upload_pdf_to_r2(g.db, file_obj, folder=ct["table"])
            else:
                uploaded = db_ops.upload_audio_to_b2(g.db, file_obj, folder=ct["table"])
        except Exception as e:
            return f"Échec de l'envoi de « {field['label']} » : {e}"
        if uploaded:
            payload[field["name"]] = uploaded
    return None


@bp_admins.route("/<content_key>/upload-field/<field_name>", methods=["POST"])
@login_required
def upload_field(content_key, field_name):
    """Envoi asynchrone d'UN champ fichier (image/audio/pdf) avant même la
    soumission du formulaire — voir admin-file-upload.js. Permet une barre
    de progression réelle et un retry qui ne recharge pas la page ni ne
    fait perdre le reste du formulaire déjà rempli."""
    ct = get_content_type(content_key)
    if not ct:
        return jsonify(ok=False, error="Type de contenu inconnu."), 404

    field = next((f for f in ct["fields"] if f["name"] == field_name), None)
    if not field or field["type"] not in ("image", "audio", "pdf"):
        return jsonify(ok=False, error="Champ invalide pour un envoi de fichier."), 400

    file_obj = request.files.get("file")
    if not file_obj or not file_obj.filename:
        return jsonify(ok=False, error="Aucun fichier reçu."), 400

    try:
        if field["type"] == "image":
            url = db_ops.upload_file(g.db, file_obj, folder=ct["table"])
        elif field["type"] == "pdf":
            url = db_ops.upload_pdf_to_r2(g.db, file_obj, folder=ct["table"])
        else:
            url = db_ops.upload_audio_to_b2(g.db, file_obj, folder=ct["table"])
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 502

    if not url:
        return jsonify(ok=False, error="Échec de l'envoi (fichier vide)."), 400

    return jsonify(ok=True, url=url)


@bp_admins.route("/<content_key>/new", methods=["GET", "POST"])
@login_required
def content_new(content_key):
    ct = get_content_type(content_key)
    if not ct:
        abort(404)

    relation_options = _relation_options(ct)
    suggestion_options = _suggestion_options(ct)
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    if request.method == "POST":
        payload = _parse_form(ct["fields"], request.form)
        upload_error = _apply_uploads(ct, payload)

        if upload_error:
            if is_ajax:
                return jsonify(ok=False, error=upload_error), 400
            flash(upload_error, "error")
        else:
            try:
                db_ops.create_row(g.db, ct["table"], payload)
                redirect_url = url_for("admins.content_list", content_key=content_key)
                if is_ajax:
                    return jsonify(ok=True, redirect=redirect_url)
                flash(f"{ct['label_singular'].capitalize()} créé·e avec succès.", "success")
                return redirect(redirect_url)
            except Exception as e:
                error_msg = f"Erreur lors de la création : {e}"
                if is_ajax:
                    return jsonify(ok=False, error=error_msg), 502
                flash(error_msg, "error")

    return render_template(
        "admin/form.html", ct=ct, row=None,
        relation_options=relation_options, suggestion_options=suggestion_options,
    )


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
    suggestion_options = _suggestion_options(ct)
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    if request.method == "POST":
        payload = _parse_form(ct["fields"], request.form)
        upload_error = _apply_uploads(ct, payload)
        # sinon (aucun fichier choisi) : on garde l'URL existante, on ne l'écrase pas

        if upload_error:
            if is_ajax:
                return jsonify(ok=False, error=upload_error), 400
            flash(upload_error, "error")
        else:
            try:
                db_ops.update_row(g.db, ct["table"], row_id, payload)
                redirect_url = url_for("admins.content_list", content_key=content_key)
                if is_ajax:
                    return jsonify(ok=True, redirect=redirect_url)
                flash(f"{ct['label_singular'].capitalize()} mis·e à jour.", "success")
                return redirect(redirect_url)
            except Exception as e:
                error_msg = f"Erreur lors de la mise à jour : {e}"
                if is_ajax:
                    return jsonify(ok=False, error=error_msg), 502
                flash(error_msg, "error")

    return render_template(
        "admin/form.html", ct=ct, row=row,
        relation_options=relation_options, suggestion_options=suggestion_options,
    )


@bp_admins.route("/<content_key>/<row_id>/delete", methods=["POST"])
@login_required
def content_delete(content_key, row_id):
    ct = get_content_type(content_key)
    if not ct:
        abort(404)
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    try:
        db_ops.delete_row(g.db, ct["table"], row_id)
        if is_ajax:
            return jsonify(ok=True)
        flash(f"{ct['label_singular'].capitalize()} supprimé·e.", "success")
    except Exception as e:
        if is_ajax:
            return jsonify(ok=False, error=str(e)), 502
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


def _suggestion_options(ct):
    """Pour les champs 'text_suggest' : valeurs déjà utilisées dans la
    colonne, à proposer en suggestions (champ libre, pas de liste figée)."""
    options = {}
    for field in ct["fields"]:
        if field["type"] == "text_suggest":
            options[field["name"]] = db_ops.list_distinct_values(g.db, ct["table"], field["name"])
    return options


# ---------------------------------------------------------------------------
# Galeries : gestion des médias (media_items) — cas particulier imbriqué
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Galeries : gestion des médias (media_items) — cas particulier imbriqué
#
# L'envoi se fait fichier par fichier depuis le JS (voir
# static/js/admin/gallery-upload.js + templates/admin/gallery_media.html) :
# chaque fichier est un appel indépendant à /media/upload. Si la connexion
# coupe en cours de route, seul le fichier en cours échoue — tout ce qui a
# déjà réussi reste enregistré, et l'admin peut relancer juste celui qui a
# échoué au lieu de tout recommencer.
# ---------------------------------------------------------------------------

@bp_admins.route("/galleries/<gallery_id>/media")
@login_required
def gallery_media(gallery_id):
    gallery = db_ops.get_row(g.db, "galleries", gallery_id)
    if not gallery:
        abort(404)

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


@bp_admins.route("/galleries/<gallery_id>/media/upload", methods=["POST"])
@login_required
def gallery_media_upload(gallery_id):
    """Reçoit UN fichier (+ vignette optionnelle pour les vidéos, générée
    côté navigateur) et l'enregistre. Appelé une fois par fichier par le JS
    — jamais en lot — justement pour qu'une coupure réseau ne fasse perdre
    que le fichier en cours."""
    gallery = db_ops.get_row(g.db, "galleries", gallery_id)
    if not gallery:
        return jsonify(ok=False, error="Galerie introuvable."), 404

    file_obj = request.files.get("file")
    if not file_obj or not file_obj.filename:
        return jsonify(ok=False, error="Aucun fichier reçu."), 400

    media_type = request.form.get("type", "photo")
    credit = request.form.get("credit") or "COJA7"

    try:
        media_url = db_ops.upload_file(g.db, file_obj, folder=f"galleries/{gallery_id}")
    except Exception as e:
        return jsonify(ok=False, error=f"Échec de l'envoi : {e}"), 502

    if not media_url:
        return jsonify(ok=False, error="Échec de l'envoi (fichier vide)."), 400

    thumb_url = None
    thumb_file = request.files.get("thumbnail")
    if thumb_file and thumb_file.filename:
        try:
            thumb_url = db_ops.upload_file(g.db, thumb_file, folder=f"galleries/{gallery_id}/thumbs")
        except Exception:
            thumb_url = None  # tant pis, le média reste utilisable sans vignette

    try:
        existing = g.db.table("media_items").select("display_order").eq("gallery_id", gallery_id).execute().data or []
        next_order = (max((m["display_order"] or 0) for m in existing) + 1) if existing else 0
        row = g.db.table("media_items").insert({
            "gallery_id": gallery_id,
            "type": media_type,
            "media_url": media_url,
            "thumbnails_url": thumb_url,
            "credit": credit,
            "display_order": next_order,
        }).execute().data[0]
    except Exception as e:
        return jsonify(ok=False, error=f"Fichier envoyé mais échec de l'enregistrement : {e}"), 502

    return jsonify(ok=True, item=row)


@bp_admins.route("/galleries/<gallery_id>/media/reorder", methods=["POST"])
@login_required
def gallery_media_reorder(gallery_id):
    data = request.get_json(silent=True) or {}
    order = data.get("order") or []
    if not order:
        return jsonify(ok=False, error="Ordre vide."), 400

    try:
        # One UPDATE per item — fine at this project's gallery sizes, but
        # would be worth batching (a single RPC call) if a gallery ever
        # grew into the hundreds of media items.
        for index, media_id in enumerate(order):
            g.db.table("media_items").update({"display_order": index}).eq("id", media_id).eq("gallery_id", gallery_id).execute()
        return jsonify(ok=True)
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 502


@bp_admins.route("/galleries/<gallery_id>/media/<media_id>/delete", methods=["POST"])
@login_required
def gallery_media_delete(gallery_id, media_id):
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    item = db_ops.get_row(g.db, "media_items", media_id)
    if item:
        try:
            db_ops.delete_file_by_url(g.db, item.get("media_url"))
            db_ops.delete_file_by_url(g.db, item.get("thumbnails_url"))
            db_ops.delete_row(g.db, "media_items", media_id)
            if is_ajax:
                return jsonify(ok=True)
            flash("Média supprimé.", "success")
        except Exception as e:
            if is_ajax:
                return jsonify(ok=False, error=str(e)), 502
            flash(f"Erreur lors de la suppression : {e}", "error")
    elif is_ajax:
        return jsonify(ok=False, error="Média introuvable."), 404
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
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    if request.method == "POST":
        content_type = request.form.get("content_type")
        content_id = request.form.get("content_id")
        if content_type in FEATURED_TYPE_TABLE and content_id:
            try:
                result = g.db.table("featured_content").upsert(
                    {
                        "content_type": content_type,
                        "content_id": content_id,
                        "display_order": int(request.form.get("display_order") or 0),
                    },
                    on_conflict="content_type, content_id"  # <--- Spécifier les deux colonnes de la contrainte
                ).execute()
                if is_ajax:
                    new_row = result.data[0] if result.data else None
                    return jsonify(ok=True, item=new_row)
                flash("Contenu ajouté à la une.", "success")
            except Exception as e:
                if is_ajax:
                    return jsonify(ok=False, error=str(e)), 502
                flash(f"Erreur lors de l'ajout à la une : {e}", "error")
        elif is_ajax:
            return jsonify(ok=False, error="Choisis un type et un contenu."), 400
        return redirect(url_for("admins.featured"))

    try:
        current = (
            g.db.table("featured_content").select("*").order("display_order", desc=True).execute().data or []
        )
    except Exception as e:
        flash(f"Erreur de chargement : {e}", "error")
        current = []

    # Options disponibles par type, pour le formulaire d'ajout
    options_by_type = {}
    for ftype, table in FEATURED_TYPE_TABLE.items():
        try:
            options_by_type[ftype] = db_ops.list_relation_options(g.db, table, "title")
        except Exception:
            options_by_type[ftype] = []
    return render_template("admin/featured.html", current=current, options_by_type=options_by_type)


@bp_admins.route("/featured/<featured_id>/delete", methods=["POST"])
@login_required
def featured_delete(featured_id):
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    try:
        db_ops.delete_row(g.db, "featured_content", featured_id)
        if is_ajax:
            return jsonify(ok=True)
        flash("Retiré de la une.", "success")
    except Exception as e:
        if is_ajax:
            return jsonify(ok=False, error=str(e)), 502
        flash(f"Erreur lors du retrait : {e}", "error")
    return redirect(url_for("admins.featured"))


# ---------------------------------------------------------------------------
# Messages reçus depuis le bouton de contact public
# ---------------------------------------------------------------------------

@bp_admins.route("/messages")
@login_required
def messages():
    status = request.args.get("status", "all")
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    try:
        query = g.db.table("support_messages").select("*")
        if status == "resolved":
            query = query.eq("is_resolved", True)
        elif status == "unresolved":
            query = query.eq("is_resolved", False)
        rows = query.order("created_at", desc=True).limit(200).execute().data or []
    except Exception as e:
        if is_ajax:
            return jsonify(ok=False, error=str(e)), 502
        flash(f"Erreur de chargement : {e}", "error")
        rows = []

    if is_ajax:
        for r in rows:
            r["created_at_display"] = _format_date_fr(r.get("created_at"))
        return jsonify(ok=True, messages=rows, status=status)

    return render_template("admin/messages.html", messages=rows, status=status)


@bp_admins.route("/messages/<message_id>/toggle-resolved", methods=["POST"])
@login_required
def message_toggle_resolved(message_id):
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    row = db_ops.get_row(g.db, "support_messages", message_id)

    if not row:
        if is_ajax:
            return jsonify(ok=False, error="Message introuvable."), 404
        flash("Message introuvable.", "error")
        return redirect(url_for("admins.messages"))

    new_status = not row.get("is_resolved", False)
    try:
        db_ops.update_row(g.db, "support_messages", message_id, {"is_resolved": new_status})
        if is_ajax:
            return jsonify(ok=True, is_resolved=new_status)
        flash("Statut mis à jour.", "success")
    except Exception as e:
        if is_ajax:
            return jsonify(ok=False, error=str(e)), 502
        flash(f"Erreur lors de la mise à jour : {e}", "error")
    return redirect(url_for("admins.messages"))


@bp_admins.route("/messages/<message_id>/delete", methods=["POST"])
@login_required
def message_delete(message_id):
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    try:
        db_ops.delete_row(g.db, "support_messages", message_id)
        if is_ajax:
            return jsonify(ok=True)
        flash("Message supprimé.", "success")
    except Exception as e:
        if is_ajax:
            return jsonify(ok=False, error=str(e)), 502
        flash(f"Erreur lors de la suppression : {e}", "error")
    return redirect(url_for("admins.messages"))


# ---------------------------------------------------------------------------
# Gestion des comptes admins (super_admin uniquement)
# ---------------------------------------------------------------------------

@bp_admins.route("/team/invite", methods=["POST"])
@super_admin_required
def team_invite():
    # Kept as a plain form submit (not AJAX) on purpose: this is a rare,
    # sensitive action — a full page reload with a clear flash message is
    # more trustworthy here than a slick inline update.
    email = (request.form.get("email") or "").strip()
    first_name = (request.form.get("first_name") or "").strip()
    last_name = (request.form.get("last_name") or "").strip()
    role = request.form.get("role") or ""
    if not role or role not in ROLES:
        flash("Choisissez le rôle", "error")
        return redirect(request.referrer)
        
    if not email or not first_name or not last_name:
        flash("Email, prénom et nom sont obligatoires.", "error")
        return redirect(request.referrer)

    try:
        redirect_url = url_for("admins.set_password", _external=True)
        admins_service.invite_admin(email, first_name, last_name, role, redirect_to=redirect_url)
        flash(f"Invitation envoyée à {email}.", "success")
    except Exception as e:
        flash(f"Erreur lors de l'invitation : {e}", "error")
    return redirect(url_for("admins.team"))


@bp_admins.route("/set-password")
def set_password():
    """Landing page for the invite email's link. No @login_required: the
    person isn't logged in yet at this point — Supabase hands them a
    short-lived session token instead, delivered in the URL fragment
    (after the #), which the server never sees (fragments aren't sent in
    HTTP requests at all). set-password.js reads it client-side and calls
    Supabase's REST API directly to set the password."""
    return render_template(
        "admin/set_password.html",
        supabase_url=admins_auth.SUPABASE_URL,
        supabase_anon_key=admins_auth.SUPABASE_ANON_KEY,
    )


@bp_admins.route("/team")
@super_admin_required
def team():
    try:
        admins = g.db.table("admins").select("*").order("created_at").execute().data or []
    except Exception as e:
        flash(f"Erreur de chargement : {e}", "error")
        admins = []
    return render_template("admin/team.html", admins=admins)


@bp_admins.route("/team/<admin_id>/toggle-active", methods=["POST"])
@super_admin_required
def team_toggle_active(admin_id):
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    if admin_id == session.get("admin_id"):
        if is_ajax:
            return jsonify(ok=False, error="Tu ne peux pas désactiver ton propre compte."), 403
        flash("Tu ne peux pas désactiver ton propre compte.", "error")
        return redirect(url_for("admins.team"))

    row = db_ops.get_row(g.db, "admins", admin_id)
    if not row:
        if is_ajax:
            return jsonify(ok=False, error="Compte introuvable."), 404
        return redirect(url_for("admins.team"))

    new_status = not row.get("is_active", True)
    try:
        db_ops.update_row(g.db, "admins", admin_id, {"is_active": new_status})
        if is_ajax:
            return jsonify(ok=True, is_active=new_status)
        flash("Statut mis à jour.", "success")
    except Exception as e:
        if is_ajax:
            return jsonify(ok=False, error=str(e)), 502
        flash(f"Erreur lors de la mise à jour : {e}", "error")
    return redirect(url_for("admins.team"))


@bp_admins.route("/team/<admin_id>/role", methods=["POST"])
@super_admin_required
def team_update_role(admin_id):
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    if admin_id == session.get("admin_id"):
        if is_ajax:
            return jsonify(ok=False, error="Tu ne peux pas changer ton propre rôle."), 403
        flash("Tu ne peux pas changer ton propre rôle.", "error")
        return redirect(url_for("admins.team"))

    role = request.form.get("role")
    if role not in ROLE_EXTENDED:
        if is_ajax:
            return jsonify(ok=False, error="Rôle invalide."), 400
        return redirect(url_for("admins.team"))

    try:
        db_ops.update_row(g.db, "admins", admin_id, {"role": role})
        if is_ajax:
            return jsonify(ok=True, role=role)
        flash("Rôle mis à jour.", "success")
    except Exception as e:
        if is_ajax:
            return jsonify(ok=False, error=str(e)), 502
        flash(f"Erreur lors de la mise à jour : {e}", "error")
    return redirect(url_for("admins.team"))