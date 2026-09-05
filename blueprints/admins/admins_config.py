"""
Configuration déclarative de l'interface admin.

Chaque entrée de CONTENT_TYPES décrit une table Supabase et comment
l'afficher/l'éditer dans les vues génériques (list.html / form.html).
Ajouter une nouvelle table gérable par l'admin = ajouter une entrée ici,
sans toucher aux routes ni aux templates.

Types de champ supportés par form.html :
  - text        : <input type="text">
  - text_suggest: <input type="text"> avec suggestions (valeurs déjà
                  utilisées dans la colonne) mais champ libre — pas de
                  liste figée, contrairement à "relation"
  - textarea    : <textarea> simple (pas d'éditeur riche)
  - richtext    : éditeur Quill (voir static/js/admin/editor.js)
  - datetime    : <input type="datetime-local">
  - date        : <input type="date">
  - select      : <select> à partir de "options"
  - image       : upload vers Cloudflare R2
  - audio       : upload vers Backblaze B2 (par blocs, voir admins_db.py)
  - pdf         : upload vers Cloudflare R2, compressé avant envoi
  - relation    : champ texte avec suggestions dont la sélection doit
                  correspondre à une ligne existante d'une autre table
                  (voir "relation_table" / "relation_label") — au-delà
                  d'une simple liste déroulante pour rester utilisable
                  quand il y a beaucoup d'options
"""

CONTENT_TYPES = {
    "events": {
        "label": "Événements",
        "label_singular": "un événement",
        "table": "events",
        "order_by": "start_date",
        "order_desc": True,
        "list_columns": [
            ("title", "Titre"),
            ("start_date", "Début"),
            ("status", "Statut"),
        ],
        "fields": [
            {"name": "title", "label": "Titre", "type": "text", "required": True},
            {"name": "description", "label": "Description", "type": "richtext"},
            {"name": "start_date", "label": "Date de début", "type": "datetime", "required": True},
            {"name": "end_date", "label": "Date de fin", "type": "datetime"},
            {"name": "time_label", "label": "Horaire (texte libre, ex: 9h – 12h)", "type": "text"},
            {"name": "location", "label": "Lieu", "type": "text"},
            {"name": "department", "label": "Département", "type": "text"},
            {
                "name": "status", "label": "Statut", "type": "select",
                "options": ["upcoming", "ongoing", "past", "cancelled"],
                "default": "upcoming",
            },
            {"name": "hero_media_url", "label": "Image de couverture", "type": "image"},
        ],
    },
    "communications": {
        "label": "Communications",
        "label_singular": "une communication",
        "table": "communications",
        "order_by": "published_at",
        "order_desc": True,
        "list_columns": [
            ("title", "Titre"),
            ("federation", "Fédération"),
            ("department", "Département"),
            ("published_at", "Publié le"),
        ],
        "fields": [
            {"name": "title", "label": "Titre", "type": "text", "required": True},
            {"name": "subtitle", "label": "Sous-titre", "type": "text"},
            {"name": "reference_number", "label": "Numéro de référence", "type": "text"},
            {
                "name": "federation", "label": "Fédération", "type": "select",
                "options": ["fedchas", "mipah"],
            },
            {"name": "department", "label": "Département", "type": "text"},
            {"name": "author", "label": "Auteur", "type": "text"},
            {"name": "content", "label": "Contenu", "type": "richtext"},
            {
                "name": "hero_media_type", "label": "Type du média principal", "type": "select",
                "options": ["image", "video"],
            },
            {"name": "hero_media_url", "label": "Média principal", "type": "image"},
            {"name": "hero_media_description", "label": "Légende du média", "type": "text"},
            {"name": "download_url", "label": "Document à télécharger (PDF)", "type": "pdf"},
            {"name": "download_type", "label": "Type de téléchargement (ex: PDF)", "type": "text"},
            {
                "name": "event_id", "label": "Événement lié", "type": "relation",
                "relation_table": "events", "relation_label": "title",
            },
            {"name": "published_at", "label": "Date de publication", "type": "datetime"},
        ],
    },
    "rubrics": {
        "label": "Rubriques vidéo",
        "label_singular": "une rubrique",
        "table": "rubrics",
        "order_by": "published_at",
        "order_desc": True,
        "list_columns": [
            ("title", "Titre"),
            ("category", "Catégorie"),
            ("published_at", "Publié le"),
        ],
        "fields": [
            {"name": "title", "label": "Titre", "type": "text", "required": True},
            {"name": "category", "label": "Catégorie", "type": "text_suggest"},
            {"name": "speaker", "label": "Intervenant", "type": "text"},
            {"name": "description", "label": "Description", "type": "richtext"},
            {
                "name": "youtube_id",
                "label": "Lien YouTube",
                "type": "text",
                "required": True,
                "help": "Collez le lien complet de la vidéo YouTube.",
            },
            {"name": "published_at", "label": "Date de publication", "type": "datetime"},
        ],
    },
    "sermons": {
        # --- Dans admins_config.py, sous "sermons" ---
        "label": "Sermons",
        "label_singular": "un sermon",
        "table": "sermons",
        "order_by": "published_at",
        "order_desc": True,
        "list_columns": [
            ("title", "Titre"),
            ("reference", "Référence"),
            ("published_at", "Publié le"),
        ],
        
        "fields": [
            {"name": "title", "label": "Titre", "type": "text", "required": True},
            {"name": "subtitle", "label": "Sous-titre", "type": "text"},
            {"name": "reference", "label": "Référence biblique", "type": "text"},
            {"name": "author", "label": "Prédicateur", "type": "text"},
            {"name": "content", "label": "Contenu", "type": "richtext"},
            {
                "name": "hero_media_type", "label": "Type du média principal", "type": "select",
                "options": ["image", "video"],
            },
            {"name": "hero_media_url", "label": "Média principal", "type": "image"},
            {"name": "pdf_url", "label": "Fichier PDF", "type": "pdf"},
            {
                "name": "event_id", "label": "Événement lié", "type": "relation",
                "relation_table": "events", "relation_label": "title",
            },
            {"name": "published_at", "label": "Date de publication", "type": "datetime"},
            {
                "name": "audio_url",
                "label": "Fichier audio",
                "type": "audio",
                "accept": "audio/*",
                "storage": "b2"
            },
        ],
    },
    "galleries": {
        "label": "Galeries",
        "label_singular": "une galerie",
        "table": "galleries",
        "order_by": "event_date",
        "order_desc": True,
        "list_columns": [
            ("title", "Titre"),
            ("department", "Département"),
            ("event_date", "Date"),
        ],
        "fields": [
            {"name": "title", "label": "Titre", "type": "text", "required": True},
            {"name": "department", "label": "Département", "type": "text"},
            {"name": "description", "label": "Description", "type": "textarea"},
            {"name": "cover_image_url", "label": "Image de couverture", "type": "image"},
            {"name": "event_date", "label": "Date", "type": "date"},
            {
                "name": "event_id", "label": "Événement lié", "type": "relation",
                "relation_table": "events", "relation_label": "title",
            },
        ],
        # Les médias d'une galerie se gèrent sur une page dédiée, pas dans le formulaire
        "has_media_manager": True,
    },
}


def get_content_type(key):
    ct = CONTENT_TYPES.get(key)
    if not ct:
        return None
    return {"key": key, **ct}
