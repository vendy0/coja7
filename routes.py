from flask import Flask, render_template
from datetime import datetime
from database import fetch_content_item, get_featured_content, get_recent_items
from blueprints.communications import bp_communications
from blueprints.emissions import bp_emissions
from blueprints.medias import bp_medias
app = Flask(__name__)

# Enregistrement du Blueprint
app.register_blueprint(bp_communications)
app.register_blueprint(bp_emissions)
app.register_blueprint(bp_medias)

MOIS_FR = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
]

@app.template_filter("date_fr")
def date_fr(value):
    """Formate une date ISO (renvoyée par Supabase) en '27 août 2026'."""
    if not value:
        return ""
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return value
    return f"{dt.day} {MOIS_FR[dt.month - 1]} {dt.year}"

@app.route("/")
def index():
    hero, federation = get_featured_content()

    return render_template(
        "index.html",
        hero=hero,
        federation=federation,
        recent_items=get_recent_items(),
        active_page="accueil",
        page_title="Accueil",
    )

    
@app.route("/calendar")
def calendar():
    # TODO : requête vers la table events, groupée par jour du mois affiché
    return render_template(
        "calendar.html",
        page_title="Calendrier",
        active_page="calendar",
    )

@app.route("/about")
def about():
    return render_template(
        "about.html",
        page_title="À propos",
        active_page="about",
    )