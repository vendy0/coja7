# Intégration de l'espace admin COJA7

## 1. Fichiers à copier

```
blueprints/admins/__init__.py
blueprints/admins/admins_auth.py
blueprints/admins/admins_config.py
blueprints/admins/admins_db.py
blueprints/admins/admins_routes.py
templates/admin/*.html
static/css/admin/style.css
static/js/admin/editor.js
static/js/admin/admin.js
```

## 2. Brancher le blueprint dans `routes.py`

```python
from blueprints.admins import bp_admins
app.register_blueprint(bp_admins)
```

L'espace admin sera accessible sur `/admin`.

## 3. Variables d'environnement

L'admin a besoin de connaître ton projet Supabase (probablement déjà défini
dans `connexion.py`, à confirmer/adapter si les noms diffèrent) :

```
SUPABASE_URL=...
SUPABASE_ANON_KEY=...     (ou SUPABASE_KEY, les deux sont acceptés)
```

Il faut aussi une **clé secrète Flask** pour que les sessions et les
messages flash fonctionnent (si ton `app.py` n'en a pas déjà une) :

```python
app.secret_key = os.environ["FLASK_SECRET_KEY"]
```

## 4. Dépendance Python

```
pip install supabase
```
(déjà utilisé par `connexion.py` a priori — vérifie juste que la lib est
bien dans ton `requirements.txt`.)

## 5. Créer le bucket Supabase Storage

Dans Supabase → Storage, crée un bucket nommé **`media`** (public), utilisé
pour toutes les images/vidéos/PDF uploadés depuis l'admin. Le nom est
configurable dans `blueprints/admins/admins_db.py` (`STORAGE_BUCKET`).

Ajoute aussi une policy d'écriture sur ce bucket pour les utilisateurs
authentifiés qui sont admins (même logique que `is_admin()` dans
`schema.sql`), par exemple :

```sql
CREATE POLICY "Admins peuvent uploader" ON storage.objects
FOR INSERT TO authenticated
WITH CHECK (bucket_id = 'media' AND is_admin());

CREATE POLICY "Admins peuvent supprimer" ON storage.objects
FOR DELETE TO authenticated
USING (bucket_id = 'media' AND is_admin());

CREATE POLICY "Lecture publique du bucket media" ON storage.objects
FOR SELECT USING (bucket_id = 'media');
```

## 6. Créer ton premier compte admin

1. Supabase → Authentication → Add user (email + mot de passe), ou
   "Invite user" pour qu'iel choisisse son mot de passe.
2. Copie l'`id` (UUID) de cet utilisateur.
3. Ajoute une ligne dans la table `admins` avec ce même `id` :

```sql
INSERT INTO admins (id, first_name, last_name, role, is_active)
VALUES ('<uuid-copié>', 'Vendy', 'Descartes', 'super_admin', true);
```

Connecte-toi ensuite sur `/admin/login`.

## 7. Comment ça marche

- **Auth** : login via Supabase Auth. Le token de session est gardé côté
  Flask (`session`) et sert à créer, à chaque requête admin, un client
  Supabase authentifié comme cet admin — c'est ce qui permet aux policies
  RLS `is_admin()` déjà présentes dans `schema.sql` de fonctionner sans
  rien changer côté base de données.
- **CRUD générique** : les 5 tables de contenu (`events`, `communications`,
  `rubrics`, `sermons`, `galleries`) sont décrites dans
  `admins_config.py` (liste des champs, type d'input). Les vues
  `list.html` / `form.html` s'adaptent automatiquement — pour ajouter un
  champ ou une table, il suffit d'éditer ce fichier de config.
- **Éditeur riche** : Quill.js (chargé depuis un CDN dans
  `base_admin.html`) sur tous les champs `type: "richtext"` — gras,
  italique, titres, listes. Le HTML produit est stocké tel quel dans les
  colonnes `content` / `description` existantes.
- **Médias** : upload direct vers Supabase Storage. Les galeries ont une
  page dédiée (`/admin/galleries/<id>/media`) pour ajouter plusieurs
  photos/vidéos d'un coup.
- **À la une** : `/admin/featured` pour gérer la table `featured_content`
  (ce qui apparaît en avant sur la page d'accueil).
- **Équipe** : `/admin/team` (réservé aux `super_admin`) pour activer/
  désactiver un compte ou changer son rôle. La création du compte
  Supabase Auth lui-même se fait côté dashboard Supabase (voir §6) —
  volontairement laissé en dehors de l'admin pour ne pas avoir à gérer une
  clé `service_role` côté serveur.

## 8. Pistes d'amélioration (pas incluses ici)

- Pagination sur les listes admin (actuellement limité à 100 lignes)
- Réordonnancement drag & drop des médias d'une galerie
- Invitation d'un nouvel admin directement depuis l'interface (nécessite
  la clé `service_role`, à manier avec précaution)
