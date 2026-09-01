# COJA7 — Communauté de Jeunesse Adventiste du Septième Jour

Site média vitrine pour la jeunesse adventiste, affilié à la FEDCHAS (Haïti).
Pas de comptes utilisateurs, pas de commentaires, pas de likes — un seul
administrateur (contenu publié par le porteur du projet uniquement).

---

## À propos

### Histoire

Tout a commencé en mars 2026. Au début, le projet portait le nom de
**« Réseau des Jeunes Adventistes »** : l'objectif était d'utiliser les
réseaux sociaux comme un nouvel espace pour partager la foi, encourager les
jeunes et faire connaître les initiatives de la jeunesse adventiste.

Le projet a ensuite évolué vers une vision plus large : ne pas se limiter à
publier du contenu religieux, mais créer une véritable communauté — un espace
où les jeunes adventistes peuvent se reconnaître, s'exprimer, partager leurs
talents et raconter leurs expériences.

C'est ainsi qu'est né le nom **Communauté de Jeunesse Adventiste du Septième
Jour**, soit **COJA7**.

À travers vidéos, interviews, témoignages, reportages, podcasts et
publications, COJA7 veut informer, inspirer, connecter et évangéliser — en
allant à la rencontre d'une génération déjà présente sur les réseaux sociaux,
plutôt que d'attendre qu'elle vienne à l'Église.

### Slogan

> COJA7 — La voix, les talents et les histoires de la jeunesse adventiste.

### Mission

Mettre en valeur la jeunesse adventiste en racontant ses histoires, en
révélant ses talents et en l'accompagnant dans sa foi, à travers les outils
numériques de sa génération.

### Vision

Devenir la référence médiatique de la jeunesse adventiste — en Haïti et dans
la diaspora — en bâtissant une communauté jeune, connectée et engagée.

### Objectifs

1. **Valoriser les jeunes** — mettre en lumière leurs talents, parcours et réussites
2. **Informer** — couvrir les événements et initiatives de la jeunesse adventiste
3. **Inspirer** — publier des histoires qui encouragent dans la foi, les études, la carrière
4. **Créer une communauté** — connecter les jeunes adventistes entre églises, villes, régions
5. **Promouvoir les initiatives** — donner de la visibilité aux projets sociaux, culturels, éducatifs
6. **Donner la parole aux jeunes** — interviews, débats, témoignages, podcasts
7. **Utiliser les outils numériques au service de la mission** — réseaux sociaux, vidéo, graphisme

### Réseaux & contact

- Facebook : [profil 1](https://www.facebook.com/share/1DZy466QMq/) · [profil 2](https://www.facebook.com/share/1D4mYeq9qE/)
- TikTok : [@coja007](https://tiktok.com/@coja007)
- Instagram : [@co_ja_7](https://www.instagram.com/co_ja_7)
- Email : coja7.adventiste@gmail.com

### Manque encore

- [ ] Équipe / direction (noms + titres)
- [ ] Numéro de contact (WhatsApp) — optionnel
- [ ] Photo(s) pour la page À propos — optionnel

---

## Stack technique

| Composant | Choix |
|---|---|
| Backend | Flask + Jinja2 |
| Base de données | Supabase (Postgres géré, gratuit) |
| Stockage fichiers | Supabase Storage (images, PDF légers) |
| Vidéos | YouTube (embed iframe — jamais stocké sur Supabase) |
| Recherche (Média) | Fuse.js (recherche floue côté client) |
| Keepalive | GitHub Actions (ping pour éviter la pause du plan gratuit Supabase après 7j d'inactivité) |
| Sauvegardes | Exports `pg_dump` manuels réguliers (pas d'auto-backup en plan gratuit) |

**Contrainte budget :** 0€, uniquement des tiers gratuits.

---

## Structure du site

Navigation mobile-first en bottom bar, **5 onglets** :

```
Accueil
Communications  → grille de cartes (FEDCHAS, MIPAH, ...) → liste de notes
Émissions       → grille de cartes (Rubrique, Sermon)     → liste d'épisodes
Média           → grille de galeries (par événement)      → détail masonry
Calendrier      → vue mensuelle + journées mondiales par club
```

À propos : accessible depuis le header, pas dans la bottom bar (page
consultée une fois, pas un flux qu'on revisite).

### Pages existantes (maquettes statiques HTML/CSS)

- `index.html` — Accueil
- `communications.html` — landing Communications (cartes FEDCHAS / MIPAH)
- `fedchas.html` — liste des notes FEDCHAS
- `emissions.html` — landing Émissions (cartes Rubrique / Sermon)
- `sermon.html` — liste des prédications
- `rubrique.html` — liste des épisodes de rubrique
- `media.html` — grille des galeries d'événements
- `galerie-details.html` — détail d'une galerie (masonry, sans header/nav — vue « stack imbriqué »)
- `calendar.html` — calendrier des événements *(gabarit initial existant, à raccorder à la nouvelle nav 5 onglets)*
- À propos — **pas encore maquettée**

### Modèle de contenu (aperçu, à affiner en tables Supabase)

- **Institutions** (Communications) : nom, logo, liste de notes
- **Notes FEDCHAS/MIPAH** : n° de référence, titre, date, département, PDF/image jointe (à confirmer), institution liée
- **Catégories Émissions** : Rubrique / Sermon
- **Sermons** : titre, prédicateur, date, durée, lien YouTube
- **Rubriques** : titre, date, court texte, épisode n°
- **Galeries** (Média) : titre, club, date, liste de médias
- **Médias** : type (photo/vidéo), fichier ou lien YouTube, **crédit photographe (défaut "COJA7", éditable)**
- **Événements/Calendrier** : titre, date, lieu, type (`standard` / `journee_mondiale`), club concerné, visuel (pour les journées mondiales)

**Droits d'auteur :** chaque média a un crédit individuel (pas seulement au niveau de la galerie), + mention légale fixe en bas de la page Média.

---

## Identité visuelle

- **Couleurs** : navy `#14213D`, or `#A9791A`, rouge `#8E2A2E`, paper `#F6F4EE` — палette encore en discussion, direction actuelle : couleurs plus franches/pleines sur certaines sections (pas de rounded cards ni de tons pastel type IA)
- **Typographie** : Source Serif 4 (titres), IBM Plex Sans (corps), IBM Plex Mono (labels/dates/références)
- **Grilles responsive** : `flexbox` + media queries (1 colonne < 340px, 2 par défaut, 3 dès 640px, 4 dès 1000px) — pas de CSS Grid pur (support incertain sur anciens moteurs)
- **Masonry (Média détail)** : `column-count` CSS, pas de JS
- Pas d'icônes/émojis génériques, pas d'avatars ronds avec initiales

---

## Notes techniques à ne pas oublier

- **Chemins d'assets** : actuellement en HTML brut (`assets/img/...`). À la migration Jinja2, remplacer par `{{ url_for('static', filename='...') }}` — sinon les images cassent dès qu'une route n'est plus à la racine.
- **Pagination ("Charger plus")** : AJAX vers un endpoint Flask JSON (`fetch()` + `jsonify`), pas de rechargement de page.
- **Recherche Média** : liste JSON légère chargée au front, matching flou via Fuse.js — pas besoin de moteur de recherche serveur à cette échelle.
- **Header background bug résolu** : `z-index:-1` sur `header::before` casse l'empilement — utiliser `z-index:0`.

---

## À faire

- [ ] Page À propos (attente équipe/contact)
- [ ] Page détail d'une note FEDCHAS/MIPAH (actuellement `details.html` existe pour FEDCHAS, à généraliser)
- [ ] Raccorder `calendar.html` à la nav 5 onglets
- [ ] Barre de recherche + suggestions sur Média (remplace les filtres actuels)
- [ ] Décision finale sur le système de couleurs
- [ ] Migration HTML brut → Flask + Jinja2
