# COJA7 — Documentation technique

Site média vitrine pour la Communauté de Jeunesse Adventiste du Septième
Jour (COJA7), avec une interface d'administration complète pour publier
le contenu. Pas de comptes visiteurs, pas de commentaires — le contenu
est géré exclusivement par une petite équipe d'administrateurs.

Ce document est la référence technique du projet : architecture, mise en
route, déploiement. Pour l'histoire et la mission du projet, voir le
README existant.

---

## Stack technique

| Composant | Choix |
|---|---|
| Backend | Flask (Python) — pas de framework async, pas de FastAPI |
| Templates | Jinja2, rendu côté serveur |
| Base de données | Supabase (Postgres géré) — accès via `supabase-py` |
| Auth admin | Supabase Auth (email/mot de passe) + policies RLS via `is_admin()` |
| Stockage images/vidéos/PDF | Cloudflare R2 (compatible S3, via `boto3`) |
| Stockage audio (sermons) | Backblaze B2 (API native, via `b2sdk` — **pas** boto3, voir plus bas) |
| Recherche publique | Fuse.js (recherche floue côté client) |
| Éditeur de texte riche (admin) | Quill.js (Pas encore top) |
| Vidéos (rubriques) | Embed YouTube, pas d'hébergement vidéo propre |

Aucun framework JS, aucun bundler. Le JS est écrit à la main, en fichiers
séparés par fonctionnalité, chargés via `<script src>` classiques.

---

## Structure du projet

```
routes.py              # Routes de premier niveau (accueil, calendrier, about, contact...)
database.py            # Toutes les requêtes Supabase (lecture publique)
connexion.py           # Client Supabase partagé (anonyme)

communications.py      # Blueprint : communications (Par fédération)
emissions.py            # Blueprint : sermons + rubriques vidéo
medias.py               # Blueprint : galeries photo/vidéo

blueprints/admins/      # Tout l'admin, isolé du reste
  admins_routes.py       # Routes (CRUD générique + cas particuliers)
  admins_config.py       # Config déclarative des types de contenu gérés
  admins_auth.py          # Auth Supabase, sessions, décorateurs @login_required
  admins_db.py            # Upload R2/B2, CRUD générique, dédoublonnage

templates/               # Templates du site public
templates/admin/         # Templates de l'admin (base séparée : base_admin.html)

static/css/style.css           # Style du site public
static/css/admin/style.css      # Style de l'admin (palette différente, volontairement)
static/js/                      # JS du site public
static/js/admin/                # JS de l'admin
```

### Pourquoi l'admin est isolé dans son propre blueprint

Un seul fichier `admins_config.py` décrit chaque type de contenu géré
(événements, communications, rubriques, sermons, galeries) : ses champs,
leurs types (texte, image, audio, pdf, relation, richtext...), leurs
options. Les vues (`list.html`, `form.html`) sont **génériques** — elles
s'adaptent à cette config plutôt que d'avoir un template dédié par type de
contenu. Ajouter un champ à un type de contenu existant = éditer
`admins_config.py`, rien d'autre (sauf besoin d'un nouveau type de champ,
auquel cas il faut aussi étendre `form.html` et `admins_routes.py`).

---

## Variables d'environnement

Aucune valeur par défaut sensible n'est codée en dur. Fichier `.env`
attendu à la racine (jamais commité — vérifier `.gitignore`) :

```bash
# Flask
FLASK_SECRET_KEY=            # généré une fois avec: python3 -c "import secrets; print(secrets.token_hex(32))"

# Supabase
SUPABASE_URL=
SUPABASE_ANON_KEY=           # ou SUPABASE_KEY, les deux noms sont acceptés

# Cloudflare R2 (images, vidéos, PDF)
R2_ACCOUNT_ID=
R2_ACCESS_KEY_ID=
R2_SECRET_ACCESS_KEY=
R2_BUCKET_NAME=
R2_PUBLIC_URL=                # URL publique du bucket (domaine R2.dev ou domaine personnalisé)

# Backblaze B2 (audio des sermons)
B2_KEY_ID=
B2_APPLICATION_KEY=
B2_BUCKET_NAME=
B2_PUBLIC_URL=
```

**Important** : `B2_ENDPOINT` n'est plus utilisé — l'upload audio est
passé de boto3 (S3-compatible) à `b2sdk` (API native de Backblaze) après
des échecs de connexion récurrents et non résolus avec boto3 sur réseau
mobile. R2 reste sur boto3 (jamais eu ce problème).

---

## Mise en route locale

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt   # à maintenir à jour — voir note plus bas
python3 run.py                    # ou l'équivalent selon le point d'entrée réel
```

### Dépendances à vérifier dans `requirements.txt`

Le projet a accumulé des dépendances au fil des fonctionnalités ; à
minima, ces paquets doivent y figurer :
`flask`, `supabase`, `python-dotenv`, `boto3`, `b2sdk`, `pypdf`
(compression des PDF avant envoi sur R2).

---

## Base de données (Supabase)

- Toutes les tables ont RLS (Row Level Security) activé.
- `is_admin()` est une fonction Postgres `SECURITY DEFINER` qui vérifie si
  `auth.uid()` correspond à un admin actif — utilisée dans la majorité des
  policies d'écriture (`USING (is_admin())`).
- **Piège déjà rencontré** : une policy qui fait `SELECT` sur la table
  `admins` en comparant à `auth.uid() IN (SELECT id FROM admins)` boucle à
  l'infini (RLS récursif). Toujours comparer directement `auth.uid() = id`
  pour la lecture de son propre profil.
- Tables principales : `events`, `communications`, `rubrics`, `sermons`,
  `galleries`, `media_items`, `featured_content`, `admins`,
  `support_messages`.
- `support_messages` : seule table où l'écriture (`INSERT`) est ouverte au
  rôle anonyme (`WITH CHECK (true)`) — c'est la table qui reçoit les
  messages du bouton de contact public. Toutes les autres écritures
  passent par `is_admin()`.

### Créer le premier compte admin

1. Supabase → Authentication → *Add user* (ou *Invite user*).
2. Copier l'`id` (UUID) généré.
3. Insérer une ligne dans `admins` avec ce même `id` :

```sql
INSERT INTO admins (id, first_name, last_name, role, is_active)
VALUES ('<uuid>', 'Prénom', 'Nom', 'super_admin', true);
```

Il n'y a volontairement pas d'interface pour créer un compte admin depuis
l'admin lui-même — ça éviterait de manier une clé `service_role` côté
serveur pour un besoin très rare (ajout d'un membre de l'équipe).

---

## Stockage : R2 vs B2, et pourquoi

- **Cloudflare R2** : images, vidéos, PDF. Client `boto3` (API
  compatible S3). Dédoublonnage par hash SHA-256 du contenu — deux envois
  du même fichier ne créent pas deux objets, la clé de l'objet EST le hash.
- **Backblaze B2** : uniquement l'audio des sermons. Client `b2sdk`
  (API native, pas boto3). Sur ce projet, boto3 vers B2 échouait de façon
  répétée et non-diagnostiquable à distance ("connexion fermée avant
  réception d'une réponse valide") ; le CLI officiel `b2` (qui utilise
  b2sdk en interne) fonctionnait parfaitement avec les mêmes identifiants,
  sur le même réseau. D'où le choix définitif de b2sdk pour B2.
- Les deux stockages exigent que le bucket soit **public en lecture**
  (les URLs générées sont directement utilisées comme `src`).
- Compression des PDF avant envoi (`pypdf`, best-effort — si la
  compression échoue, le PDF original est envoyé tel quel).

---

## Déploiement — liste avant mise en production

Le développement s'est fait entièrement sur Termux (Android). Rien de ce
qui suit n'a encore été mis en place :

- [ ] **Hébergement réel** : un serveur qui reste allumé (VPS, Render,
      Railway, PythonAnywhere...) — pas un téléphone.
- [ ] **Serveur WSGI de production** (gunicorn ou équivalent) — jamais
      `app.run()` / le serveur de dev Flask en public.
- [ ] **`debug=False`** en production (sinon Flask expose la trace
      complète des erreurs, y compris des détails de config).
- [ ] **Domaine + HTTPS** — bloque aussi : Cloudflare Images
      Transformations (nécessite un domaine proxié par Cloudflare), CORS
      pour le téléchargement direct d'images côté client.
- [ ] **Protection CSRF** sur les formulaires admin (actuellement
      absente — risque limité tant qu'il y a un seul admin de confiance,
      mais à corriger avant d'ouvrir l'accès à plus de monde).
- [ ] **Limitation des tentatives de connexion** sur `/admin/login`
      (aucune actuellement).
- [ ] **`MAX_CONTENT_LENGTH`** Flask non configuré — un upload
      volumineux pourrait consommer beaucoup de mémoire serveur.
- [ ] Cookies de session : régler explicitement `SESSION_COOKIE_SECURE`,
      `SESSION_COOKIE_HTTPONLY`, `SESSION_COOKIE_SAMESITE`.
- [ ] Remplacer les `print()` de debug par une vraie journalisation
      (module `logging`), pour garder une trace une fois en ligne.
- [ ] Vérifier la politique de sauvegarde de la base Supabase (plan
      utilisé, fréquence de point-in-time recovery).

---

## Fonctionnalités notables (pour comprendre le code sans tout relire)

- **Formulaires admin en AJAX** : créer/modifier un contenu ne recharge
  pas la page. En cas de succès, `history.back()` est utilisé (pas
  `location.replace()`) pour éviter que le bouton "retour" du navigateur
  ne remontre le formulaire déjà soumis. En cas d'échec (JS désactivé,
  erreur), tout retombe sur un `<form>` classique — comportement
  identique à avant, aucune régression possible de ce côté.
- **Upload de fichiers avec barre de progression réelle** : chaque champ
  fichier s'envoie dès sa sélection (avant même la soumission du
  formulaire), avec un vrai pourcentage puis un indicateur "envoi vers le
  serveur de stockage" une fois le transfert navigateur→serveur terminé
  (le transfert serveur→R2/B2 n'a pas de pourcentage connu).
- **Recherche publique (Fuse.js)** : l'index complet (tous les titres,
  pas seulement la page courante) est chargé une fois au premier focus du
  champ de recherche, puis filtré en local — pas de requête serveur par
  lettre tapée, et les résultats couvrent tout le contenu, pas seulement
  ce qui est déjà chargé à l'écran.
- **Suggestions "relation" et "catégorie" (admin)** : implémentées en JS
  maison plutôt qu'avec `<datalist>`, dont le support des suggestions est
  très inégal sur navigateurs mobiles.

---

## Limitations connues / à faire

- `page_description` et JSON-LD (données structurées SEO) pas encore
  présents sur toutes les pages de détail (événements, galeries,
  accueil — sermons et communications sont faits).
- Téléchargement direct d'une image (pas juste une galerie zippée) en
  attente du domaine (CORS).
- Code pas encore commenté de façon systématique.
