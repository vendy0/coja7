from flask import Blueprint, render_template, request, jsonify
from database import get_all_galleries, get_gallery_detail

# Création du Blueprint
bp_medias = Blueprint('medias', __name__, url_prefix='/medias')

GALLERIES_PAGE_SIZE = 12

@bp_medias.route("/medias")
def index():
    galleries = get_all_galleries(limit=GALLERIES_PAGE_SIZE, offset=0)
    return render_template(
        "medias/index.html",
        galleries=galleries,
        page_size=GALLERIES_PAGE_SIZE,
        page_title="Médias",
        active_page="medias",
    )

@bp_medias.route("/medias/load-more")
def load_more_galleries():
    """Renvoie le prochain lot de galeries en HTML (fragment), pour le bouton 'Charger plus'."""
    offset = request.args.get("offset", default=0, type=int)
    galleries = get_all_galleries(limit=GALLERIES_PAGE_SIZE, offset=offset)
    html = render_template("medias/_gallery_cards.html", galleries=galleries)
    return jsonify(html=html, has_more=len(galleries) == GALLERIES_PAGE_SIZE)

@bp_medias.route("/medias/<gallery_id>")
def galerie_detail(gallery_id):
    gallery = get_gallery_detail(gallery_id)
    if not gallery:
        return "<h1>Galerie introuvable</h1>", 404
        
    return render_template(
        "medias/galerie-details.html",
        gallery=gallery,
        page_title=gallery.get("title", "Galerie"),
        active_page="medias",
    )
