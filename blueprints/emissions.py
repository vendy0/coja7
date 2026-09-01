from flask import Blueprint, render_template
from database import get_emissions_count, get_all_rubrics, get_all_sermons, get_sermon_detail

# Création du Blueprint
bp_emissions = Blueprint('emissions', __name__, url_prefix='/emissions')

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
    rubrics_data = get_all_rubrics()
    return render_template(
        "emissions/rubrics.html", 
        rubrics=rubrics_data, 
        page_title="Rubriques", 
        active_page="emissions"
    )

@bp_emissions.route("/sermons")
def sermons():
    sermons_data = get_all_sermons()
    return render_template(
        "emissions/sermons.html", 
        sermons=sermons_data, 
        page_title="Sermons", 
        active_page="emissions"
    )

@bp_emissions.route("/sermons/<sermon_id>")
def sermon_detail(sermon_id):
    sermon = get_sermon_detail(sermon_id)
    return render_template(
        "emissions/details_sermon.html", 
        sermon=sermon, 
        page_title=sermon.get("title", "Sermon"), 
        active_page="emissions"
    )
