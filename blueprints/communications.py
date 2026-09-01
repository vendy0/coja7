from flask import Blueprint, render_template
from database import get_federation_news, get_federation_detail, get_communications_count_by_federation

# Création du Blueprint
bp_communications = Blueprint('communications', __name__, url_prefix='/communications')

@bp_communications.route("/")
def index():
    counts = get_communications_count_by_federation()
    return render_template("communications/index.html", counts=counts, page_title="Communications", active_page="communications")

@bp_communications.route("/<federation>")
def federation_news(federation):
    notes = get_federation_news(federation) or []
    return render_template("communications/federation_news.html", notes=notes, page_title=federation, active_page="communications")

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