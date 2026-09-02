from flask import Blueprint, render_template, request, jsonify
from database import get_emissions_count, get_all_rubrics, get_all_sermons, get_sermon_detail

# Création du Blueprint
bp_emissions = Blueprint('emissions', __name__, url_prefix='/emissions')

RUBRICS_PAGE_SIZE = 9
SERMONS_PAGE_SIZE = 10

@bp_emissions.route("/")
def index():
    counts = get_emissions_count()
    # TODO : requêtes vers les tables sermons / rubrics (cartes d'entités)
    return render_template(
        "emissions/index.html",
        counts=counts,
        page_title="Émissions",
        active_page="emissions",
    )

@bp_emissions.route("/rubrics")
def rubrics():
    rubrics_data = get_all_rubrics(limit=RUBRICS_PAGE_SIZE, offset=0)
    return render_template(
        "emissions/rubrics.html", 
        rubrics=rubrics_data, 
        page_size=RUBRICS_PAGE_SIZE,
        page_title="Rubriques", 
        active_page="emissions"
    )

@bp_emissions.route("/rubrics/load-more")
def load_more_rubrics():
    """Renvoie le prochain lot de rubriques en HTML (fragment), pour le bouton 'Charger plus'."""
    offset = request.args.get("offset", default=0, type=int)
    rubrics_data = get_all_rubrics(limit=RUBRICS_PAGE_SIZE, offset=offset)
    html = render_template("emissions/_rubric_cards.html", rubrics=rubrics_data)
    return jsonify(html=html, has_more=len(rubrics_data) == RUBRICS_PAGE_SIZE)

@bp_emissions.route("/sermons")
def sermons():
    sermons_data = get_all_sermons(limit=SERMONS_PAGE_SIZE, offset=0)
    return render_template(
        "emissions/sermons.html", 
        sermons=sermons_data, 
        page_size=SERMONS_PAGE_SIZE,
        page_title="Sermons", 
        active_page="emissions"
    )

@bp_emissions.route("/sermons/load-more")
def load_more_sermons():
    """Renvoie le prochain lot de sermons en HTML (fragment), pour le bouton 'Charger plus'."""
    offset = request.args.get("offset", default=0, type=int)
    sermons_data = get_all_sermons(limit=SERMONS_PAGE_SIZE, offset=offset)
    html = render_template("emissions/_sermon_rows.html", sermons=sermons_data)
    return jsonify(html=html, has_more=len(sermons_data) == SERMONS_PAGE_SIZE)

@bp_emissions.route("/sermons/<sermon_id>")
def sermon_detail(sermon_id):
    sermon = get_sermon_detail(sermon_id)
    return render_template(
        "emissions/details_sermon.html", 
        sermon=sermon, 
        page_title=sermon.get("title", "Sermon"), 
        active_page="emissions"
    )
