from connexion import supabase
from collections import Counter

def get_feature():
    # Requête vers la table events sur Supabase
    return supabase.table("rubrics").select("*").execute().data

def get_communications_count_by_federation():
    # 1. Sélectionne uniquement la colonne 'federation'
    response = supabase.table("communications").select("federation").execute()
    # 2. Compte les occurrences (ex: Counter({'fedchas': 14, 'mipah': 3}))
    counts = Counter(item["federation"] for item in response.data if item.get("federation"))
    return dict(counts)

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
