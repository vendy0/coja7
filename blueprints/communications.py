from flask import Blueprint, render_template, request, jsonify
from database import get_federation_news, get_federation_detail, get_communications_count_by_federation

# Création du Blueprint
bp_communications = Blueprint('communications', __name__, url_prefix='/communications')

NOTES_PAGE_SIZE = 10

@bp_communications.route("/")
def index():
    counts = get_communications_count_by_federation()
    return render_template("communications/index.html", counts=counts, page_title="Communications", active_page="communications")

@bp_communications.route("/<federation>")
def federation_news(federation):
    notes = get_federation_news(federation, limit=NOTES_PAGE_SIZE, offset=0) or []
    return render_template(
        "communications/federation_news.html",
        notes=notes,
        federation=federation,
        page_size=NOTES_PAGE_SIZE,
        page_title=federation,
        active_page="communications",
    )

@bp_communications.route("/<federation>/load-more")
def load_more_federation_news(federation):
    """Renvoie le prochain lot de notes en HTML (fragment), pour le bouton 'Charger plus'."""
    offset = request.args.get("offset", default=0, type=int)
    notes = get_federation_news(federation, limit=NOTES_PAGE_SIZE, offset=offset) or []
    html = render_template("communications/_note_rows.html", notes=notes, offset=offset)
    return jsonify(html=html, has_more=len(notes) == NOTES_PAGE_SIZE)

@bp_communications.route("/<federation>/<note_id>")
def federation_detail(federation, note_id):
    # Requête vers la table communications filtrée sur note_id (UUID)
    note = get_federation_detail(federation, note_id)
    if not note:
        return "<h1>Contenu indisponible</h1>", 404
    return render_template(
        "communications/details.html",
        note=note,
        page_title="Détail de la note",
        active_page="details",
    )
