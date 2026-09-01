from flask import Flask, render_template, request, jsonify, abort
from datetime import datetime, date, timedelta
import calendar as pycalendar
from database import fetch_content_item, get_featured_content, get_recent_items, get_all_events, get_event_detail
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

    
def _parse_event_datetime(value):
    """Parse une date/heure ISO (renvoyée par Supabase) en datetime, ou None."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def _build_calendar_context(year, month, day_param):
    """Construit la grille du mois + les événements du jour sélectionné.

    Utilisé à la fois par la route HTML (premier chargement) et par la
    route JSON (navigation en AJAX, sans rechargement de page).
    """
    today = date.today()

    # Normalise un mois hors bornes (navigation < / >) en reportant sur l'année
    if month < 1:
        month, year = 12, year - 1
    elif month > 12:
        month, year = 1, year + 1

    # Grille du mois : semaines de 7 dates (Lundi -> Dimanche), déborde sur
    # le mois précédent/suivant pour compléter la première/dernière semaine
    month_calendar = pycalendar.Calendar(firstweekday=0)
    month_weeks = month_calendar.monthdatescalendar(year, month)

    # Récupère les événements et les indexe par jour (un événement multi-jours
    # apparaît sur chacun des jours de sa plage)
    events_by_day = {}
    for event in get_all_events():
        start_dt = _parse_event_datetime(event.get("start_date"))
        if not start_dt:
            continue
        end_dt = _parse_event_datetime(event.get("end_date")) or start_dt

        event["_start"] = start_dt
        cursor = start_dt.date()
        last_day = end_dt.date()
        while cursor <= last_day:
            events_by_day.setdefault(cursor, []).append(event)
            cursor += timedelta(days=1)

    weeks = []
    for week in month_weeks:
        cells = []
        for day_date in week:
            cells.append({
                "date": day_date,
                "day": day_date.day,
                "in_month": day_date.month == month,
                "is_today": day_date == today,
                "events": sorted(
                    events_by_day.get(day_date, []),
                    key=lambda e: e["_start"],
                ),
            })
        weeks.append(cells)

    # Jour sélectionné : celui passé en paramètre, sinon aujourd'hui si on est
    # sur le mois courant, sinon le premier jour du mois affiché
    selected_date = None
    if day_param:
        try:
            selected_date = datetime.strptime(day_param, "%Y-%m-%d").date()
        except ValueError:
            selected_date = None
    if selected_date is None:
        selected_date = today if (today.year == year and today.month == month) else date(year, month, 1)

    selected_events = sorted(
        events_by_day.get(selected_date, []),
        key=lambda e: e["_start"],
    )

    prev_month, prev_year = (12, year - 1) if month == 1 else (month - 1, year)
    next_month, next_year = (1, year + 1) if month == 12 else (month + 1, year)

    return {
        "weeks": weeks,
        "year": year,
        "month": month,
        "month_label": f"{MOIS_FR[month - 1].capitalize()} {year}",
        "prev_year": prev_year,
        "prev_month": prev_month,
        "next_year": next_year,
        "next_month": next_month,
        "today": today,
        "selected_date": selected_date,
        "selected_date_label": f"{selected_date.day} {MOIS_FR[selected_date.month - 1]}",
        "selected_events": selected_events,
    }


def _event_json(event):
    return {
        "id": event.get("id"),
        "title": event.get("title"),
        "time_label": event.get("time_label"),
        "description": event.get("description"),
        "location": event.get("location"),
        "department": event.get("department"),
        "status": event.get("status"),
    }


@app.route("/calendar")
def calendar():
    today = date.today()
    year = request.args.get("year", type=int) or today.year
    month = request.args.get("month", type=int) or today.month

    ctx = _build_calendar_context(year, month, request.args.get("day"))

    return render_template(
        "calendar.html",
        page_title="Calendrier",
        active_page="calendar",
        **ctx,
    )


@app.route("/calendar/events")
def calendar_events():
    """Même logique que /calendar, mais renvoie du JSON — utilisé par le
    script de navigation du calendrier pour éviter un rechargement de page."""
    today = date.today()
    year = request.args.get("year", type=int) or today.year
    month = request.args.get("month", type=int) or today.month

    ctx = _build_calendar_context(year, month, request.args.get("day"))

    weeks_json = [
        [
            {
                "date": cell["date"].isoformat(),
                "day": cell["day"],
                "in_month": cell["in_month"],
                "is_today": cell["is_today"],
                "events": [_event_json(e) for e in cell["events"]],
            }
            for cell in week
        ]
        for week in ctx["weeks"]
    ]

    return jsonify({
        "year": ctx["year"],
        "month": ctx["month"],
        "month_label": ctx["month_label"],
        "prev_year": ctx["prev_year"],
        "prev_month": ctx["prev_month"],
        "next_year": ctx["next_year"],
        "next_month": ctx["next_month"],
        "today": ctx["today"].isoformat(),
        "selected_date": ctx["selected_date"].isoformat(),
        "selected_date_label": ctx["selected_date_label"],
        "selected_events": [_event_json(e) for e in ctx["selected_events"]],
        "weeks": weeks_json,
    })


@app.route("/calendar/event/<event_id>")
def calendar_event(event_id):
    """Page de détail d'un événement (redirigé depuis la liste du calendrier)."""
    event = get_event_detail(event_id)
    if not event:
        abort(404)

    start_dt = _parse_event_datetime(event.get("start_date"))
    end_dt = _parse_event_datetime(event.get("end_date"))
    is_multi_day = bool(start_dt and end_dt and start_dt.date() != end_dt.date())

    # Lien "retour au calendrier" pointant vers le mois et le jour de l'événement
    back_year = start_dt.year if start_dt else date.today().year
    back_month = start_dt.month if start_dt else date.today().month
    back_day = start_dt.date().isoformat() if start_dt else None

    return render_template(
        "calendar_event.html",
        event=event,
        is_multi_day=is_multi_day,
        back_year=back_year,
        back_month=back_month,
        back_day=back_day,
        page_title=event.get("title", "Événement"),
        active_page="calendar",
    )

@app.route("/about")
def about():
    return render_template(
        "about.html",
        page_title="À propos",
        active_page="about",
    )