5. Les search bars (Médias, Rubriques, Sermons) avec recommandations pour rechercher
10. Lier la page about à l'interface users. Jusqu'à présent y a aucun lien vers.
11. Apprendre le MarkDown
13. Les outils SEO (author, robots, TOUT le truc de SEO). Je sais pas comment gérer les balises og aussi
14. La gestion des erreurs supabase, r2, b2. Je sais pas si c déjà fait. 
15. La communication avec l'équipe depuis l'interface user, un truc dans ce genre :
        -         <!--    Bouton FAB      -->
        <button id="support-fab" class="fab-button {{'fab_notif_off' if not current_user.push_subscription else 'fab_notif_on'}}" onclick="openSupportModal()">
            <svg viewBox="0 0 24 24" class="icon-fab">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
        </button>

        <div id="supportModal" class="support-modal">
            <div class="support-modal-content">
                <h4>Contacter l'Admin</h4>
                <p>Un problème ou une suggestion ? Dites-nous tout.</p>

                <form id="supportForm" method="POST" action="{{ url_for('send_message_route') }}">
                    <div class="textarea-wrapper">
                        <textarea name="message" id="support_message" rows="5" placeholder="Votre message ici..." maxlength="400" required></textarea>
                        <div id="char-counter">0 / 400</div>
                    </div>

                    <div class="modal-actions">
                        <button type="button" class="btn-cancel" onclick="closeSupportModal()">Annuler</button>
                        <button type="submit" class="btn-send">Envoyer</button>
                    </div>
                </form>
            </div>
        </div>
        
                /* RESET */
        @import url('fonts.css');
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        textarea{resize: none;}
        
        svg {
          /* --- SUPPRESSION DU BACKGROUND AU CLIC (MOBILE/PC) --- */
          -webkit-tap-highlight-color: transparent;
          user-select: none; /* Empêche de sélectionner l'icône comme du texte */
        }
        
        summary{
          -webkit-tap-highlight-color: transparent;
        }
        
        .nav-item, .fab-button, .subscription{
          -webkit-tap-highlight-color: transparent;
        }
        
        .action-list .action-item{
            -webkit-tap-highlight-color: transparent;
        }
        
        .action-list .action-item:active{
        	animation: back 0.2s ease;
        }
        	
        @keyframes back{
        	from{
        		background-color: white;
        	}to{
        		background-color: gray;
        	}
        } 
        
        #flash-container {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
        }
        
        .flash-message {
            position: relative;
            background: white;
            padding: 15px 25px;
            margin-bottom: 10px;
            border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            display: flex;
            align-items: center;
            min-width: 250px;
            /* Animation : Apparition (0.5s) puis Disparition après 4.5s */
            animation:
                slideIn 0.5s ease-out forwards,
                fadeOut 0.5s ease-in 4.5s forwards;
        }
        
        .flash-message.success {
            border-left: 5px solid #1ba94c;
        }
        .flash-message.error {
            border-left: 5px solid #e74c3c;
        }
        
        .flash-icon {
            margin-right: 12px;
            font-size: 1.2rem;
        }
        .flash-text {
            color: #333;
            font-weight: 500;
            flex-grow: 1;
        }
        
        .flash-close {
            background: none;
            border: none;
            cursor: pointer;
            font-size: 1.2rem;
            color: #999;
        }
        
        /* Barre de progression */
        .progress-bar {
            position: absolute;
            bottom: 0;
            left: 0;
            height: 4px;
            width: 100%;
        }
        
        .flash-message.success .progress-bar {
            background: #1ba94c;
        }
        .flash-message.error .progress-bar {
            background: #e74c3c;
        }
        
        .progress-bar {
            animation: shrink 5s linear forwards;
        }
        
        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        @keyframes fadeOut {
            from {
                opacity: 1;
                transform: translateX(0);
            }
            to {
                opacity: 0;
                transform: translateX(20px);
            }
        }
        
        @keyframes shrink {
            from {
                width: 100%;
            }
            to {
                width: 0%;
            }
        }
        
        body {
            background: #f0f2f5;
            color: #222;
            padding-bottom: 80px;
            /* min-height: 1000px; */
        }
        
        /* 🔝 BARRE DU HAUT */
        .top-bar {
            width: 100%;
            height: 130px; /* Légèrement plus grand pour accommoder la zone user */
            background: linear-gradient(90deg, #0f9d58, #12b76a);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 15px;
            color: white;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15);
            z-index: 100;
            border-radius: 0 0 15px 15px;
        }
        
        /* 🟢 BRAND (InterPam) */
        .brand {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 12px;
        }
        
        .logo {
            width: 150px;
            height: auto;
            /* background: white; */
            padding: 8px;
            border-radius: 12px;
            display: block;
        }
        /* 
        .brand-name {
          font-size: 1.6rem;
          font-weight: 800;
          letter-spacing: -0.5px;
          text-transform: uppercase; Pour coller au style de l'image
          display: block;
        } */
        
        /* 👤 USER ZONE (Version Agrandie et Contrastée) */
        .user-zone {
            background: #1a2a44; /* Bleu nuit pour trancher avec le vert */
            padding: 8px 12px;
            border-radius: 12px;
            text-align: right;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            min-width: 140px;
            align-items: center;
            justify-content: center;
            align-content: center;
            line-height: 1.4;
        }
        
        .user-name {
            display: block;
            font-size: 1.05rem;
            font-weight: 700;
            color: #fff;
            margin: 0;
            padding: 0;
        }
        
        .username {
            display: block;
            font-size: 0.9rem;
            opacity: 0.8;
            color: #a0aec0;
            margin: 8px;
        }
        
        .balance {
            background: rgba(255, 255, 255, 0.15); /* Fond subtil */
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 0.85rem;
            font-weight: 600;
            color: #63b3ed; /* Bleu clair pour le montant */
            display: inline-block;
        }
        
        .balance strong {
            color: white;
            margin-left: 3px;
        }
        
        /* --- FLOATING ACTION BUTTON --- */
        .fab-button {
            position: fixed;
            right: 20px;
            bottom: 125px;
            width: 56px;
            height: 56px;
            background: #0f9d58;
            border-radius: 50%;
            border: none;
            color: white;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 998;
            transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275), background 0.2s, bottom 1.5s ease;
        }
        
        .fab-button.fab_notif_on{
            bottom: 85px; /* Juste au-dessus de la bottom-nav (70px + 15px de marge) */
        }
        
        .fab-button.fab_notif_off{
            bottom: 125px; /* Juste au-dessus de la bottom-nav (70px + 15px de marge) */
        }
        
        .fab-button:hover {
            transform: scale(1.1);
            background: #12b76a;
        }
        
        .icon-fab {
            width: 28px;
            height: 28px;
            stroke: currentColor;
            fill: none;
            stroke-width: 2;
        }
        
        /* --- MODAL SUPPORT --- */
        .support-modal {
            display: none; /* Masqué par défaut */
            position: fixed;
            z-index: 1001;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background: rgba(15, 34, 61, 0.7); /* Overlay bleu nuit transparent */
            align-items: center;
            justify-content: center;
            padding: 20px;
            backdrop-filter: blur(4px);
        }
        
        .support-modal-content {
            background: white;
            padding: 24px;
            border-radius: 16px;
            width: 100%;
            max-width: 400px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
            transform: scale(0.8);
            opacity: 0;
            transition: all 0.3s ease-out;
        }
        
        /* Animation d'ouverture */
        .support-modal.active {
            display: flex;
        }
        
        .support-modal.active .support-modal-content {
            transform: scale(1);
            opacity: 1;
        }
        
        .support-modal-content h4 {
            color: #1a2a44;
            font-family: 'Space Grotesk', sans-serif;
            margin-bottom: 8px;
            font-size: 1.2rem;
        }
        
        .support-modal-content p {
            color: #666;
            font-size: 0.9rem;
            margin-bottom: 20px;
        }
        
        /* Container pour positionner le compteur par dessus le textarea */
        .textarea-wrapper {
            position: relative;
            width: 100%;
        }
        #char-counter {
            position: absolute;
            bottom: 6px;
            right: 10px;
            font-size: 0.7rem;
            color: #9aa3ad;
            pointer-events: none;
            background: transparent;
            padding: 0;
            border-radius: 0;
            line-height: 1;
        }
        
        #char-counter.limit-reached {
            color: var(--admin-danger);
            font-weight: 600;
        }
        
        
        .support-modal-content textarea {
            width: 100%;
            padding: 12px;
            border: 1.5px solid #e3e3e3;
            border-radius: 10px;
            resize: none;
            font-family: inherit;
            font-size: 0.95rem;
            transition: border-color 0.2s;
            margin-bottom: 20px;
        }
        
        .support-modal-content textarea:focus {
            outline: none;
            border-color: #0f9d58;
        }
        
        /* Boutons */
        .modal-actions {
            display: flex;
            gap: 12px;
        }
        
        .btn-cancel, .btn-send {
            flex: 1;
            padding: 12px;
            border-radius: 10px;
            font-weight: 600;
            cursor: pointer;
            border: none;
            transition: 0.2s;
        }
        
        .btn-cancel {
            background: #f0f2f5;
            color: #555;
        }
        
        .btn-send {
            background: #1a2a44;
            color: white;
        }
        
        .btn-send:hover {
            background: #243b5e;
        }
        
        .subscription{
            position: fixed;
            bottom: 70px;
            left: 0;
            width: 100vw;
            display: flex;
            justify-content: center;
            height: 40px;
            border-radius: 10px 10px 0 0;
            border-bottom: none;
            border: 1px solid black;
            transition: bottom 2s ease;
        }
        #btn-push{
            display:none; 
            padding: 10px; 
            background: #2ecc71; 
            color: white; 
            border: none; 
            cursor: pointer;
            height: 100%;
            width: 100%;
            border-radius: inherit;
        }
        
        /* 🔽 BARRE DU BAS */
        .bottom-nav {
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            height: 70px;
            margin: 0;
            padding: 0;
            background: #fff;
            border-top: 1px solid #e3e3e3;
            display: flex;
            justify-content: space-around;
            align-items: center;
            box-shadow: 0 -2px 5px rgba(0, 0, 0, 0.05);
        }
        
        .nav-item {
            text-decoration: none;
            color: #888;
            font-size: 0.7rem;
            display: flex;
            flex-direction: column;
            align-items: center;
            transition: color 0.2s ease;
        }
        
        .nav-item .icon {
            width: 22px;
            height: 22px;
            stroke: currentColor;
            fill: none;
            stroke-width: 2;
            margin-bottom: 4px;
        }
        
        .nav-item.active {
            color: #0f9d58;
        }
        
        .nav-item:hover {
            color: #14b96a;
        }


16. Mettre le liens de la gallery correspondante dans un eveneemnt. De même pour sermon => evenement. 
17. Télécharger une image et une gallery. C'est déjà là mais faut configurer le truc cors ou jsp quoi parce que je n'ai pas encore acheté le domaine

Admin
17. Charger un pdf OU un audio dans les communications au lieu de son lien. 
18. Vérifier si y a pas déjà une image dans R2 avant de l'ajouter à nouveau
24. Mettre automatiquement les types image et audio au lieu de choisir
25. Ajouter un champs rechercher dans l'interface des modifs
26. Dans sermon, afficher l'évènement lié


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
