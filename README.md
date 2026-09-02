COJA7 — Communauté de Jeunesse Adventiste du Septième Jour

Site média vitrine pour la jeunesse adventiste, affilié à la FEDCHAS (Haïti).
Pas de comptes utilisateurs, pas de commentaires, pas de likes — un seul
administrateur (contenu publié par le porteur du projet uniquement).

---

À propos

Histoire

Tout a commencé en mars 2026. Au début, le projet portait le nom de
« Réseau des Jeunes Adventistes » : l'objectif était d'utiliser les
réseaux sociaux comme un nouvel espace pour partager la foi, encourager les
jeunes et faire connaître les initiatives de la jeunesse adventiste.

Le projet a ensuite évolué vers une vision plus large : ne pas se limiter à
publier du contenu religieux, mais créer une véritable communauté — un espace
où les jeunes adventistes peuvent se reconnaître, s'exprimer, partager leurs
talents et raconter leurs expériences.

C'est ainsi qu'est né le nom Communauté de Jeunesse Adventiste du Septième
Jour, soit COJA7.

À travers vidéos, interviews, témoignages, reportages, podcasts et
publications, COJA7 veut informer, inspirer, connecter et évangéliser — en
allant à la rencontre d'une génération déjà présente sur les réseaux sociaux,
plutôt que d'attendre qu'elle vienne à l'Église.

Slogan

« COJA7 — La voix, les talents et les histoires de la jeunesse adventiste. »

Mission

Mettre en valeur la jeunesse adventiste en racontant ses histoires, en
révélant ses talents et en l'accompagnant dans sa foi, à travers les outils
numériques de sa génération.

Vision

Devenir la référence médiatique de la jeunesse adventiste — en Haïti et dans
la diaspora — en bâtissant une communauté jeune, connectée et engagée.

Objectifs

1. Valoriser les jeunes — mettre en lumière leurs talents, parcours et réussites
2. Informer — couvrir les événements et initiatives de la jeunesse adventiste
3. Inspirer — publier des histoires qui encouragent dans la foi, les études, la carrière
4. Créer une communauté — connecter les jeunes adventistes entre églises, villes, régions
5. Promouvoir les initiatives — donner de la visibilité aux projets sociaux, culturels, éducatifs
6. Donner la parole aux jeunes — interviews, débats, témoignages, podcasts
7. Utiliser les outils numériques au service de la mission — réseaux sociaux, vidéo, graphisme

Réseaux & contact

- Facebook : "profil 1" (https://www.facebook.com/share/1DZy466QMq/) · "profil 2" (https://www.facebook.com/share/1D4mYeq9qE/)
- TikTok : "@coja007" (https://tiktok.com/@coja007)
- Instagram : "@co_ja_7" (https://www.instagram.com/co_ja_7)
- Email : coja7.adventiste@gmail.com

Manque encore

- [ ] Équipe / direction (noms + titres)
- [ ] Numéro de contact (WhatsApp) — optionnel
- [ ] Photo(s) pour la page À propos — optionnel

---

Stack technique

Composant| Choix
Backend| Flask + Jinja2
Base de données| Supabase (Postgres géré)
Images| Cloudflare R2
Optimisation images| Cloudflare Images Transformations — optionnel
Audios| Backblaze B2
Vidéos| YouTube (embed iframe)
Recherche (Média)| Fuse.js (recherche floue côté client)
Keepalive| GitHub Actions (ping pour éviter la pause du plan gratuit Supabase après 7j d'inactivité)
Sauvegardes| Exports "pg_dump" manuels réguliers
Hébergement application| VPS Contabo
Système serveur| Ubuntu Server
Gestion serveur| Pterodactyl Panel + Wings
DNS / réseau| Cloudflare

---

Hébergement & serveur

VPS

L'application Flask sera hébergée sur un VPS Contabo.

Un VPS est un ordinateur virtuel loué dans un centre de données et accessible
en permanence depuis Internet. Il héberge l'application COJA7 et les services
nécessaires à son fonctionnement.

Configuration cible

La configuration initiale recommandée est :

- 2 vCPU minimum
- 4 Go de RAM minimum
- 40–50 Go de stockage SSD/NVMe minimum
- IPv4 publique
- Ubuntu Server 24.04 LTS

Cette configuration est volontairement modeste : l'application Flask effectue
principalement des requêtes vers Supabase et du rendu HTML avec Jinja2. Les
fichiers médias lourds ne sont pas stockés sur le VPS.

Une configuration plus généreuse peut toutefois être choisie si son coût est
faible. L'offre Contabo Cloud VPS 10, par exemple, fournit davantage de
ressources que le minimum recommandé et laisse une marge pour les services
supplémentaires.

Les ressources du VPS pourront être augmentées ultérieurement en fonction de
la croissance réelle du trafic.

---

Pterodactyl

Le VPS sera administré avec Pterodactyl.

L'installation prévue comprend :

- Pterodactyl Panel — interface web permettant de gérer les serveurs
- Pterodactyl Wings — composant installé sur le VPS qui exécute les serveurs
  gérés par Pterodactyl

L'objectif est de permettre la gestion de l'environnement COJA7 depuis
l'interface Pterodactyl tout en conservant la possibilité d'administrer
directement le VPS lorsque cela est nécessaire.

Architecture :

                         INTERNET
                            │
                            ▼
                       Cloudflare
                    DNS + HTTPS + CDN
                            │
                            ▼
                     ┌──────────────┐
                     │     VPS      │
                     │   Contabo    │
                     │              │
                     │ Ubuntu       │
                     │              │
                     │ Pterodactyl  │
                     │ ┌──────────┐ │
                     │ │  Panel   │ │
                     │ └──────────┘ │
                     │      │       │
                     │ ┌──────────┐ │
                     │ │  Wings   │ │
                     │ └────┬─────┘ │
                     │      │       │
                     │      ▼       │
                     │    Flask     │
                     │    COJA7     │
                     └──────┬───────┘
                            │
                            ▼
                         Supabase

---

Configuration du domaine avec Cloudflare

Le domaine principal de COJA7 est géré par Cloudflare.

Le VPS possède une adresse IP publique.

Le DNS Cloudflare associe le domaine à cette adresse IP.

Exemple :

coja7.com
     │
     ▼
Cloudflare DNS
     │
     ▼
IP publique du VPS
     │
     ▼
VPS Contabo
     │
     ▼
COJA7 / Flask

Cloudflare sert principalement de point d'entrée réseau pour le domaine.
Il ne configure pas automatiquement l'application Flask présente sur le VPS.

La configuration du VPS, de Flask, de Pterodactyl et des services réseau est
effectuée séparément.

---

Rôle de Cloudflare

Cloudflare pourra notamment assurer :

- gestion DNS du domaine
- HTTPS / certificats
- protection du serveur
- mise en cache lorsque pertinent
- CDN
- gestion du trafic vers le VPS

Le domaine et le VPS restent deux éléments distincts :

Domaine
   ↓
Cloudflare
   ↓
VPS
   ↓
Application

---

Déploiement de COJA7

Le développement de l'application reste séparé de l'administration du VPS.

Le flux prévu est :

Développement
     │
     ▼
Git / GitHub
     │
     ▼
VPS Contabo
     │
     ▼
Environnement COJA7
     │
     ▼
Application Flask

L'administration initiale du VPS et l'installation de Pterodactyl seront
effectuées par une personne maîtrisant l'administration Linux.

Une fois l'environnement préparé, le porteur du projet pourra principalement
gérer l'application COJA7 depuis l'environnement prévu et déployer ses
modifications.

---

Architecture des médias

Les fichiers lourds ne sont pas stockés directement dans Supabase.

                         COJA7
                           │
              ┌────────────┼────────────┐
              │            │            │
              ↓            ↓            ↓
          Supabase      YouTube     Cloudflare R2
          Database       Vidéos        Images
              │                         │
              │                         ↓
              │                 Cloudflare Images
              │                  Transformations
              │                     (optionnel)
              │
              ↓
        URLs / identifiants
              │
              └────────────┬────────────┘
                           │
                           ↓
                         COJA7

Les audios suivent une infrastructure séparée :

COJA7
  │
  ↓
Backblaze B2
  │
  ↓
Fichiers audio

---

Rôle de chaque service

Supabase — données

Supabase héberge la base PostgreSQL de l'application.

Il contient les métadonnées des contenus et les références vers les fichiers
externes, par exemple :

sermons
├── title
├── description
├── date
├── federation
├── image_url
├── audio_url
└── youtube_id

Supabase n'est donc pas utilisé comme stockage principal des images, audios
ou vidéos.

---

YouTube — vidéos

Les vidéos sont hébergées sur YouTube puis intégrées dans COJA7 avec un
"iframe".

COJA7 ne stocke pas les fichiers vidéo.

COJA7 → YouTube → iframe

---

Cloudflare R2 — images

R2 sert de stockage principal pour les images originales.

Le plan gratuit comprend actuellement :

- 10 Go de stockage Standard par mois
- 1 million d'opérations Class A par mois
- 10 millions d'opérations Class B par mois
- egress Internet gratuit

Le stockage Standard supplémentaire est facturé à environ
0,015 $US/Go-mois.

R2 est donc privilégié comme stockage d'images plutôt qu'ImageKit, car la
capacité de stockage peut évoluer progressivement sans imposer un abonnement
mensuel important.

---

Cloudflare Images Transformations — optimisation

Service optionnel utilisé pour optimiser les images stockées dans R2.

Il peut notamment :

- redimensionner les images
- recadrer les images
- convertir les formats
- optimiser les images pour différents appareils
- mettre en cache les versions générées

Le plan gratuit permet actuellement jusqu'à 5 000 transformations uniques
par mois. Au-delà, aucune facturation automatique n'est appliquée sur le
plan Free : les nouvelles transformations sont simplement bloquées jusqu'au
mois suivant ou à l'activation d'un plan payant.

Les originaux restent dans R2.

---

Backblaze B2 — audios

B2 sert de stockage pour les fichiers audio : sermons, podcasts, émissions,
interviews, etc.

Le plan Pay-as-you-go comprend actuellement :

- 10 Go de stockage gratuits
- egress gratuit jusqu'à 3× le stockage moyen mensuel
- appels API largement gratuits selon les classes d'opérations

Le stockage supplémentaire commence à environ 6,95 $US/TB/mois.

Backblaze permet également l'egress gratuit et illimité via plusieurs
partenaires CDN et services de calcul, notamment Cloudflare.

---

Pourquoi séparer les médias ?

Le projet évite de dépendre d'un seul fournisseur pour tous les fichiers.

Type| Service
Données| Supabase
Images| Cloudflare R2
Audio| Backblaze B2
Vidéo| YouTube

Cette séparation permet de choisir le service le plus adapté à chaque type
de média, de limiter les coûts et de pouvoir remplacer un fournisseur sans
repenser toute la base de données.

---

ImageKit — solution écartée pour le moment

ImageKit reste une alternative possible pour l'optimisation et la diffusion
des images, mais son offre gratuite actuelle est limitée à :

- 3 Go de stockage DAM
- 20 Go de bande passante par mois

Le plan gratuit est donc moins intéressant pour COJA7 comme stockage principal
si la bibliothèque d'images doit devenir importante.

ImageKit pourra éventuellement être réévalué plus tard comme couche
d'optimisation/CDN.

---

Cloudinary — solution écartée

Cloudinary avait initialement été envisagé pour centraliser le stockage et la
gestion des médias.

Cependant, en raison des contraintes de disponibilité rencontrées depuis
Haïti, Cloudinary n'est pas retenu pour l'infrastructure actuelle.

L'utilisation d'un VPN pour contourner ces restrictions n'est pas considérée
comme une solution d'infrastructure fiable pour la production.

---

Budget initial

L'objectif est de maintenir les coûts aussi proches que possible de zéro
pendant la phase de lancement.

Services gratuits

- Supabase — plan Free
- YouTube — hébergement des vidéos
- Cloudflare R2 — jusqu'à 10 Go de stockage Standard
- Cloudflare Images Transformations — jusqu'à 5 000 transformations uniques/mois
- Backblaze B2 — jusqu'à 10 Go de stockage

Dépenses prévues

Nom de domaine

- "coja7.com" — environ 10,46 $US/an actuellement

Hébergement

- VPS Contabo — coût dépendant de l'offre et de la période d'engagement
- configuration cible : environ 2 vCPU / 4 Go RAM / 40–50 Go SSD
- une offre Contabo plus généreuse peut être retenue si son rapport
  ressources/prix est plus intéressant

Le budget initial reste donc faible, mais n'est plus strictement nul en raison
du domaine et du VPS.

Les coûts supplémentaires seront introduits progressivement uniquement en
fonction de la croissance réelle du projet.

---

Domaine & e-mail

Domaine

Domaine principal prévu :

coja7.com

Le domaine est enregistré via Cloudflare Registrar.

Le nom de domaine n'est pas sensible à la casse :

coja7.com
COJA7.COM
CoJa7.com

désignent le même domaine.

E-mail

Le domaine pourra éventuellement être utilisé pour des adresses personnalisées
telles que :

contact@coja7.com
admin@coja7.com
support@coja7.com

Cloudflare Email Routing peut être utilisé pour recevoir ces messages et les
rediriger vers une boîte e-mail existante.

Une solution d'envoi/réception complète pourra être ajoutée ultérieurement si
COJA7 en a besoin.

---

Structure du site

Navigation mobile-first en bottom bar, 5 onglets :

Accueil
Communications  → grille de cartes (FEDCHAS, MIPAH, ...) → liste de notes
Émissions       → grille de cartes (Rubrique, Sermon)     → liste d'épisodes
Média           → grille de galeries (par événement)      → détail masonry
Calendrier      → vue mensuelle + journées mondiales par club

À propos : accessible depuis le header, pas dans la bottom bar (page
consultée une fois, pas un flux qu'on revisite).

Pages existantes (maquettes statiques HTML/CSS)

- "index.html" — Accueil
- "communications.html" — landing Communications (cartes FEDCHAS / MIPAH)
- "fedchas.html" — liste des notes FEDCHAS
- "emissions.html" — landing Émissions (cartes Rubrique / Sermon)
- "sermon.html" — liste des prédications
- "rubrique.html" — liste des épisodes de rubrique
- "media.html" — grille des galeries d'événements
- "galerie-details.html" — détail d'une galerie (masonry, sans header/nav — vue « stack imbriqué »)
- "calendar.html" — calendrier des événements
- À propos — pas encore maquettée

---

Modèle de contenu

Aperçu, à affiner en tables Supabase :

- Institutions (Communications) : nom, logo, liste de notes
- Notes FEDCHAS/MIPAH : n° de référence, titre, date, département, PDF/image jointe, institution liée
- Catégories Émissions : Rubrique / Sermon
- Sermons : titre, prédicateur, date, durée, lien YouTube, audio éventuel
- Rubriques : titre, date, court texte, épisode n°
- Galeries (Média) : titre, club, date, liste de médias
- Médias : type (photo/vidéo), fichier ou lien YouTube, crédit photographe (défaut "COJA7", éditable)
- Événements/Calendrier : titre, date, lieu, type ("standard" / "journee_mondiale"), club concerné, visuel (pour les journées mondiales)

Droits d'auteur : chaque média a un crédit individuel (pas seulement au niveau
de la galerie), + mention légale fixe en bas de la page Média.

---

Identité visuelle

- Couleurs : navy "#14213D", or "#A9791A", rouge "#8E2A2E", paper "#F6F4EE" — palette encore en discussion, direction actuelle : couleurs plus franches/pleines sur certaines sections (pas de rounded cards ni de tons pastel type IA)
- Typographie : Source Serif 4 (titres), IBM Plex Sans (corps), IBM Plex Mono (labels/dates/références)
- Grilles responsive : flexbox + media queries (1 colonne < 340px, 2 par défaut, 3 dès 640px, 4 dès 1000px) — pas de CSS Grid pur
- Masonry (Média détail) : "column-count" CSS, pas de JS
- Pas d'icônes/émojis génériques, pas d'avatars ronds avec initiales

---

Notes techniques à ne pas oublier

- Chemins d'assets : actuellement en HTML brut ("assets/img/..."). À la migration Jinja2, remplacer par "{{ url_for('static', filename='...') }}" — sinon les images cassent dès qu'une route n'est plus à la racine.
- Pagination ("Charger plus") : AJAX vers un endpoint Flask JSON ("fetch()" + "jsonify"), pas de rechargement de page.
- Recherche Média : liste JSON légère chargée au front, matching flou via Fuse.js — pas besoin de moteur de recherche serveur à cette échelle.
- Header background bug résolu : "z-index:-1" sur "header::before" casse l'empilement — utiliser "z-index:0".
- Médias externes : les URLs des fichiers stockés sur R2/B2 et les identifiants YouTube sont enregistrés dans Supabase, pas les fichiers eux-mêmes.
- Images originales : conserver les originaux haute qualité dans R2 ; générer les variantes optimisées à la demande lorsque nécessaire.
- Audio : stocker les fichiers audio dans B2 et conserver leur URL/référence dans Supabase.
- Vidéos : conserver uniquement l'identifiant ou l'URL YouTube dans Supabase.
- Hébergement : l'application Flask est destinée à tourner sur le VPS Contabo.
- Pterodactyl : le VPS utilise Pterodactyl Panel + Wings pour la gestion de l'environnement serveur.
- Cloudflare DNS : le domaine pointe vers l'adresse IP publique du VPS.
- Le VPS ne stocke pas les médias lourds : les images, audios et vidéos restent sur leurs services de stockage respectifs.

---

À faire

- [ ] Page À propos (attente équipe/contact)
- [ ] Page détail d'une note FEDCHAS/MIPAH (actuellement "details.html" existe pour FEDCHAS, à généraliser)
- [ ] Raccorder "calendar.html" à la nav 5 onglets
- [ ] Barre de recherche + suggestions sur Média (remplace les filtres actuels)
- [ ] Décision finale sur le système de couleurs
- [ ] Migration HTML brut → Flask + Jinja2
- [ ] Créer le bucket Cloudflare R2 pour les images
- [ ] Créer le bucket Backblaze B2 pour les audios
- [ ] Définir la convention de nommage des fichiers médias
- [ ] Définir la structure finale des tables Supabase
- [ ] Mettre en place les URLs sécurisées pour les médias
- [ ] Décider si Cloudflare Images Transformations est nécessaire dès le lancement
- [ ] Enregistrer "coja7.com"
- [ ] Configurer le DNS du domaine
- [ ] Configurer éventuellement le routage e-mail "@coja7.com"
- [ ] Acheter/configurer le VPS Contabo
- [ ] Installer Ubuntu Server
- [ ] Installer et configurer Pterodactyl Panel
- [ ] Installer et configurer Pterodactyl Wings
- [ ] Déployer l'application Flask sur le VPS
- [ ] Configurer le domaine Cloudflare vers l'adresse IP du VPS
- [ ] Configurer HTTPS
- [ ] Tester le déploiement en production

---

Principes d'infrastructure

COJA7 privilégie :

- Simplicité — éviter les services inutiles
- Coût minimal — utiliser les free tiers aussi longtemps que possible
- Séparation des responsabilités — chaque service fait ce pour quoi il est adapté
- Évolutivité — pouvoir augmenter les capacités progressivement
- Indépendance — éviter de dépendre entièrement d'un seul fournisseur
- Qualité média — conserver les originaux en haute qualité et optimiser la diffusion
- Sécurité — ne jamais exposer directement les clés secrètes ou credentials dans le frontend
- Hébergement raisonnable — commencer avec un VPS adapté aux besoins réels plutôt que surdimensionner l'infrastructure
- Séparation application/médias — ne pas utiliser le VPS comme stockage principal des fichiers lourds