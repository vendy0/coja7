from flask import Blueprint, render_template
from database import get_all_galleries, get_gallery_detail

# Création du Blueprint
bp_medias = Blueprint('medias', __name__, url_prefix='/medias')

@bp_medias.route("/medias")
def index():
    galleries = get_all_galleries()
    return render_template(
        "medias/index.html",
        galleries=galleries,
        page_title="Médias",
        active_page="medias",
    )

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
