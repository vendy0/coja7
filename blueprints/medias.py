import io
import zipfile
import requests
from flask import Blueprint, render_template, request, jsonify, send_file, abort
from database import get_all_galleries, get_gallery_detail

# Création du Blueprint
bp_medias = Blueprint('medias', __name__, url_prefix='/medias')

GALLERIES_PAGE_SIZE = 12

@bp_medias.route("/")
def index():
    galleries = get_all_galleries(limit=GALLERIES_PAGE_SIZE, offset=0)
    return render_template(
        "medias/index.html",
        galleries=galleries,
        page_size=GALLERIES_PAGE_SIZE,
        page_title="Médias",
        active_page="medias",
    )

@bp_medias.route("/load-more")
def load_more_galleries():
    """Renvoie le prochain lot de galeries en HTML (fragment), pour le bouton 'Charger plus'."""
    offset = request.args.get("offset", default=0, type=int)
    galleries = get_all_galleries(limit=GALLERIES_PAGE_SIZE, offset=offset)
    html = render_template("medias/_gallery_cards.html", galleries=galleries)
    return jsonify(html=html, has_more=len(galleries) == GALLERIES_PAGE_SIZE)

@bp_medias.route("/<gallery_id>")
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

@bp_medias.route("/<gallery_id>/download")
def download_gallery(gallery_id):
    """Génère un fichier .zip contenant tous les médias d'une galerie."""
    # Récupération des détails de la galerie depuis la base de données
    gallery = get_gallery_detail(gallery_id) #[span_3](start_span)[span_3](end_span)[span_4](start_span)[span_4](end_span)
    if not gallery:
        abort(404)

    media_items = gallery.get("media_items", []) #[span_5](start_span)[span_5](end_span)
    if not media_items:
        return "Galerie vide", 400

    # Création d'un fichier en mémoire (évite de sauvegarder le ZIP sur le serveur)
    memory_file = io.BytesIO()
    
    # Création de l'archive ZIP
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for index, item in enumerate(media_items):
            url = item.get("url") # L'URL du fichier sur Supabase ou ailleurs
            if not url:
                continue
                
            try:
                # Téléchargement du contenu du fichier
                response = requests.get(url, stream=True)
                response.raise_for_status()
                
                # Détermination de l'extension en fonction du type
                item_type = item.get("type", "photo") #[span_6](start_span)[span_6](end_span)
                ext = ".mp4" if item_type == "video" else ".jpg"
                
                # Nom du fichier à l'intérieur de l'archive zip
                filename = f"media_{index + 1}{ext}"
                
                # Ajout du fichier téléchargé dans l'archive
                zf.writestr(filename, response.content)
                
            except requests.RequestException as e:
                # Si une image échoue, on l'ignore et on passe à la suivante
                print(f"Erreur de téléchargement pour {url}: {e}")
                continue

    # Repositionner le curseur au début du fichier en mémoire avant de l'envoyer
    memory_file.seek(0)
    
    # Génération d'un nom de fichier propre basé sur le titre de la galerie
    titre_brut = gallery.get("title", "galerie") #[span_7](start_span)[span_7](end_span)
    titre_propre = "".join(c for c in titre_brut if c.isalnum() or c in (' ', '-', '_')).strip().replace(' ', '_')
    zip_filename = f"{titre_propre}.zip"

    # Envoi du fichier ZIP au client
    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name=zip_filename
    )
