5. Les search bars (Médias, Rubriques, Sermons) avec recommandations pour rechercher
11. Apprendre le MarkDown
13. Les outils SEO (author, robots, TOUT le truc de SEO). Je sais pas comment gérer les balises og aussi
14. La gestion des erreurs supabase, r2, b2. Je sais pas si c déjà fait. 
15. La communication avec l'équipe depuis l'interface user, un truc dans ce genre :

16. Mettre le liens de la gallery correspondante dans un eveneemnt. De même pour sermon => evenement. 
17. Télécharger une image et une gallery. C'est déjà là mais faut configurer le truc cors ou jsp quoi parce que je n'ai pas encore acheté le domaine

Admin
17. Charger un pdf OU un audio dans les communications au lieu de son lien. 
18. Vérifier si y a pas déjà une image dans R2 avant de l'ajouter à nouveau
25. Ajouter un champs rechercher dans l'interface des modifs
26. Dans sermon, afficher l'évènement lié
27. Mettre soit une image ou une vidéo comme hero media dans communications
28. Afficher la barre de chargement du fichier sur le serveur et non sur l'interface
29. Mettre les "page_description"
30. Commenter tout


Maths
1. Passe aux exp, log, ln
  <!--
  <div class="thumb {{ 'video' if item.type == 'sermon' }} tone-{{ item.tone }}"></div>
  -->
  
  Index.html
  {% if federation %}
<a class="federation" style="text-decoration:none;color:inherit;"
   href="{{ url_for('communications.federation_detail', note_id=federation.data.id, federation=federation.data.department) }}">
  <img class="seal-watermark" src="{{ url_for('static', filename='img/logo.jpg') }}" alt="Logo COJA7">
  <div class="ref">{{ federation.data.federation | upper or "" }} · {{ federation.data.reference_number or "Note" }}</div>
  <h3>{{ federation.data.title }}</h3>
  <div class="meta">Publié le {{ federation.data.published_at | date_fr }} · {{ federation.data.department or "" }}</div>
</a>
{% endif %}

# PLAN DE RÉVISION — MATHÉMATIQUES (CHCL)

## 1. ANALYSE & FONCTIONS

- Domaine de définition et parité
- Limites & asymptotes
  - Formes indéterminées
  - Limites avec racines
- Dérivation & étude de variations
- Fonctions usuelles
  - Logarithme népérien `ln`
  - Exponentielle `exp`

## 2. ÉQUATIONS DIFFÉRENTIELLES & INTÉGRATION

- Équations différentielles
  - `y' = ay`
  - `y' = ay + b`
- Équations avec second membre varié
  - Recherche d'une solution particulière
- Primitives usuelles et intégration directe
- Intégration par parties (IPP)
- Calcul d'aires
- Intégrales impropres
  - Limites aux bornes à l'infini

## 3. NOMBRES COMPLEXES

- Forme algébrique `a + ib`
- Module et argument
- Formes trigonométrique et exponentielle
- Résolution d'équations dans `ℂ`
  - Équations du degré 2
- Applications à la trigonométrie
  - `cos` et `sin` de fractions de `π`

## 4. PROBABILITÉS & DÉNOMBREMENT

- Dénombrement
  - Permutations
  - Arrangements
  - Combinaisons
- Probabilités conditionnelles & arbres
- Variables aléatoires
- Loi binomiale

## 5. SUITES NUMÉRIQUES

- Suites arithmétiques
- Suites géométriques
- Limite d'une suite
- Raisonnement par récurrence


# 📐 TD3 — Analyse Mathématique (Excellence Préfac 2026)

Ce dépôt contient mes solutions pas à pas pour le **TD3 complet d'Analyse Mathématique**, préparatoire au concours du **CTPEA / CHCL (Pôle Science, Technologie & Santé)**.

---

## 📚 Formulaire de Dérivation

### 1. Formules composées générales

| Fonction f(x) | Dérivée f′(x) |
| :--- | :--- |
| uⁿ | n · u′ · uⁿ⁻¹ |
| u / v | (u′v − uv′) / v² |
| √u | u′ / (2√u) |
| ln(u) | u′ / u |
| eᵘ | u′ · eᵘ |

### 2. Fonctions trigonométriques

| Fonction f(x) | Dérivée f′(x) | Forme composée f(u) |
| :--- | :--- | :--- |
| sin(x) | cos(x) | u′ · cos(u) |
| cos(x) | −sin(x) | −u′ · sin(u) |
| tan(x) | 1 + tan²(x) = 1 / cos²(x) | u′ · (1 + tan²(u)) |
| cot(x) | −(1 + cot²(x)) = −1 / sin²(x) | −u′ · (1 + cot²(u)) |

### 3. Fonctions réciproques (Arc)

| Fonction f(x) | Dérivée f′(x) | Forme composée f(u) |
| :--- | :--- | :--- |
| arcsin(x) | 1 / √(1 − x²) | u′ / √(1 − u²) |
| arccos(x) | −1 / √(1 − x²) | −u′ / √(1 − u²) |
| arctan(x) | 1 / (1 + x²) | u′ / (1 + u²) |

---

## 📝 Progression du TD3

### Exercice 1 : Dérivation

- [x] **Question 1 :**

  f(x) = ((1 + x) / (1 − x))²

  ➜ f′(x) = 4(1 + x) / (1 − x)³

- [x] **Question 2 :**

  f(x) = √((x + 1) / (x − 1))

  ➜ f′(x) = −1 / ((x − 1)² · √((x + 1) / (x − 1)))

- [x] **Question 3 :**

  f(x) = cos(√(1 + x²))

  ➜ f′(x) = −x / √(1 + x²) · sin(√(1 + x²))

- [ ] **Question 4 :**

  f(x) = 1 + x − tan(x) + ⅓ · tan³(x)

  *tan^4 x*
  
  
  
# Propriétés fondamentales de Exponentielle (e) et Logarithme Nébérien (ln)

## 1. Propriétés de la fonction Logarithme Nébérien (ln)

### Définitions et Limites
* Domaine de définition : ]0, +inf[
* ln(1) = 0
* ln(e) = 1
* Limite en 0+ : lim ln(x) = -inf
* Limite en +inf : lim ln(x) = +inf

### Propriétés Algébriques
* Produit : ln(a * b) = ln(a) + ln(b)
* Quotient : ln(a / b) = ln(a) - ln(b)
* Inverse : ln(1 / a) = -ln(a)
* Puissance : ln(a^n) = n * ln(a)
* Racine carrée : ln(sqrt(a)) = (1/2) * ln(a)

### Dérivation
* Dérivée simple : (ln(x))' = 1 / x
* Dérivée composée : (ln(u))' = u' / u
* Dérivée avec valeur absolue : (ln|u|)' = u' / u

---

## 2. Propriétés de la fonction Exponentielle (e)

### Définitions et Limites
* Domaine de définition : R (tout nombre réel)
* e^0 = 1
* e^1 = e (environ 2.718)
* e^x > 0 (toujours strictement positive)
* Limite en -inf : lim e^x = 0
* Limite en +inf : lim e^x = +inf

### Propriétés Algébriques
* Produit : e^(a + b) = e^a * e^b
* Quotient : e^(a - b) = e^a / e^b
* Inverse : e^(-a) = 1 / e^a
* Puissance : (e^a)^b = e^(a * b)

### Dérivation
* Dérivée simple : (e^x)' = e^x
* Dérivée composée : (e^u)' = u' * e^u

---

## 3. Relations Réciproques et Croissances Comparées

### Passer de ln à e (et inversement)
* e^(ln(x)) = x (pour tout x > 0)
* ln(e^x) = x (pour tout x réel)
* Transformation de puissance variable : a^b = e^(b * ln(a))

### Croissances Comparées (en +inf)
* lim (e^x / x^n) = +inf
* lim (ln(x) / x^n) = 0
* L'exponentielle l'emporte toujours sur les puissances, qui l'emportent toujours sur le logarithme.


# Formulaire : Dérivées n-ièmes Usuelles

## 1. Formules de base usuelles

* **Logarithme :** 
  $$\left(\ln x\right)^{(n)} = \frac{(-1)^{n-1} (n-1)!}{x^n} \quad (n \ge 1)$$

* **Inverses et Puissances négatives :**
  $$\left(\frac{1}{x}\right)^{(n)} = \frac{(-1)^n n!}{x^{n+1}}$$
  $$\left(\frac{1}{ax + b}\right)^{(n)} = \frac{(-1)^n a^n n!}{(ax + b)^{n+1}}$$

* **Puissances générales :**
  $$\left(x^\alpha\right)^{(n)} = \alpha(\alpha - 1)\cdots(\alpha - n + 1)x^{\alpha - n}$$
  $$\left(\sqrt{x}\right)^{(n)} = \frac{(-1)^{n-1} (2n-3)!!}{2^n x^{n - 1/2}} = \frac{(-1)^{n-1} (2n-2)!}{2^{2n-1} (n-1)! x^{n - 1/2}} \quad (n \ge 1)$$

* **Exponentielle :**
  $$\left(e^{ax}\right)^{(n)} = a^n e^{ax}$$

* **Trigonométrie :**
  $$\left(\cos(ax)\right)^{(n)} = a^n \cos\left(ax + n\frac{\pi}{2}\right)$$
  $$\left(\sin(ax)\right)^{(n)} = a^n \sin\left(ax + n\frac{\pi}{2}\right)$$

---

## 2. Formule de Leibniz (Dérivée n-ième d'un produit)

Si $f(x) = u(x) \cdot v(x)$, alors :
$$(u \cdot v)^{(n)} = \sum_{k=0}^{n} \binom{n}{k} u^{(n-k)} v^{(k)}$$

Où $\binom{n}{k} = \frac{n!}{k!(n-k)!}$ est le coefficient binomial.

* **Cas particulier très utile :** Si $v(x) = x$ (polynôme de degré 1), la somme s'arrête à $k=1$ :
  $$(u \cdot x)^{(n)} = x \cdot u^{(n)} + n \cdot u^{(n-1)}$$
