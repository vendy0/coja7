from flask import url_for
from connexion import supabase
from collections import Counter

CONTENT_TABLE_MAP = {
    "event": "events",
    "sermon": "sermons",
    "communication": "communications",
    "rubric": "rubrics",
}

def get_recent_items(limit=5):
    items = []

    for s in supabase.table("sermons").select("id,title,published_at").order("published_at", desc=True).limit(limit).execute().data:
        items.append({
            "type": "sermon", "title": s["title"], "date": s["published_at"],
            "url": url_for("emissions.sermon_detail", sermon_id=s["id"]),
            "eyebrow": "Sermon", "tone": "blue",
        })

    for c in supabase.table("communications").select("id,title,department,federation,published_at").order("published_at", desc=True).limit(limit).execute().data:
        items.append({
            "type": "communication", "title": c["title"], "date": c["published_at"],
            "url": url_for("communications.federation_detail", note_id=c["id"], federation=c["federation"]),
            "eyebrow": c["department"] or "Communiqué", "tone": "gold",
        })

    for r in supabase.table("rubrics").select("id,title,category,published_at").order("published_at", desc=True).limit(limit).execute().data:
        items.append({
            "type": "rubric", "title": r["title"], "date": r["published_at"],
            "url": url_for("emissions.rubrics"),
            "eyebrow": r["category"] or "Rubrique", "tone": "green",
        })

    for e in supabase.table("events").select("id,title,description, hero_media_url, start_date").order("start_date", desc=True).limit(limit).execute().data:
        items.append({
            "type": "event", "title": e["title"], "date": e["start_date"],
            "url": url_for("calendar"),
            "eyebrow": "Événement", "tone": "green", "description": e["description"], "hero_media_url": e["hero_media_url"]
        })

    items.sort(key=lambda i: i["date"] or "", reverse=True)
    return items[:limit]
    
def fetch_content_item(content_type: str, content_id: str | int) -> dict | None:
    """Récupère les détails d'un contenu spécifique selon son type et son ID."""
    table = CONTENT_TABLE_MAP.get(content_type)
    if not table:
        return None

    res = supabase.table(table).select("*").eq("id", content_id).execute()
    return res.data[0] if res.data else None


def get_featured_content() -> tuple[dict | None, dict | None]:
    """Récupère et catégorise le contenu mis en avant (hero et fédération)."""
    featured_rows = (
        supabase.table("featured_content")
        .select("*")
        .order("display_order")
        .limit(2)
        .execute()
        .data
    )

    hero, federation = None, None

    for row in featured_rows:
        content_type = row["content_type"]
        item_data = fetch_content_item(content_type, row["content_id"])
        
        if not item_data:
            continue

        item = {"type": content_type, "data": item_data}

        if hero is None:
            hero = item
        elif content_type == "communication":
            federation = item

    return hero, federation
    
def get_communications_count_by_federation():
    response = supabase.rpc("count_communications_by_federation").execute()
    return {row["federation"]: row["count"] for row in response.data}

def get_federation_news(federation):
    return (
        supabase.table("communications")
        .select("id, reference_number, title, department, pdf_url, federation, published_at")
        .eq("federation", federation)
        .order("published_at", desc=True)
        .execute()
        .data
    )
    
def get_federation_detail(federation, note_id):
    return (
        supabase.table("communications")
        .select("*")
        .eq("federation", federation)
        .eq("id", note_id)
        .single()
        .execute()
        .data
    )
    
def get_emissions_count():
    # 1. Sélectionne uniquement la colonne 'federation'
    rubrics = (
        supabase.table("rubrics")
        .select("id", count="exact")
        .execute().count
    )
    sermons = (
        supabase.table("sermons")
        .select("id", count="exact")
        .execute().count
    )
    
    # 2. Compte les occurrences (ex: Counter({'fedchas': 14, 'mipah': 3}))
    return {"rubrics": rubrics, "sermons": sermons}

def get_all_rubrics():
    """Récupère toutes les rubriques classées par date de publication."""
    return (
        supabase.table("rubrics")
        .select("*")
        .order("published_at", desc=True)
        .execute()
        .data
    )

def get_all_sermons():
    """Récupère tous les sermons classés par date de publication."""
    return (
        supabase.table("sermons")
        .select("id, title, subtitle, reference, published_at")
        .order("published_at", desc=True)
        .execute()
        .data
    )

def get_sermon_detail(sermon_id):
    """Récupère les détails complets d'un sermon par son ID."""
    return (
        supabase.table("sermons")
        .select("*")
        .eq("id", sermon_id)
        .single()
        .execute()
        .data
    )

def get_all_galleries():
    """Récupère toutes les galeries avec leurs médias associés pour compter photos et vidéos."""
    response = (
        supabase.table("galleries")
        .select("*, media_items(type)")
        .order("event_date", desc=True)
        .execute()
    )
    
    galleries = response.data or []
    
    # Calcul du nombre de photos et vidéos par galerie
    for gallery in galleries:
        items = gallery.get("media_items", [])
        gallery["photo_count"] = sum(1 for item in items if item.get("type") == "photo")
        gallery["video_count"] = sum(1 for item in items if item.get("type") == "video")
        
    return galleries

def get_gallery_detail(gallery_id):
    """Récupère une galerie par son UUID ainsi que la liste de tous ses éléments médias ordonnés."""
    gallery = (
        supabase.table("galleries")
        .select("*")
        .eq("id", gallery_id)
        .single()
        .execute()
        .data
    )
    
    if gallery:
        media_items = (
            supabase.table("media_items")
            .select("*")
            .eq("gallery_id", gallery_id)
            .order("display_order", desc=False)
            .execute()
            .data
        )
        gallery["media_items"] = media_items or []
        
    return gallery
