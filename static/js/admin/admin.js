document.addEventListener("DOMContentLoaded", function () {
  // -------------------------------------------------------------------
  // Menu latéral sur mobile. Le fond assombri passait AU-DESSUS de la
  // navbar (bug de z-index), ce qui à la fois l'assombrissait et
  // interceptait tous les clics dessus, empêchant toute navigation —
  // corrigé dans style.css (sidebar z-index 200 > backdrop 150). Les
  // liens naviguent normalement au clic, pas besoin de fermer le menu à
  // la main : la page se recharge.
  // -------------------------------------------------------------------
  const burger = document.getElementById("admin-burger");
  const sidebar = document.querySelector(".admin-sidebar");
  const backdrop = document.getElementById("admin-nav-backdrop");

  function setNavOpen(open) {
    if (!sidebar) return;
    sidebar.classList.toggle("open", open);
    if (backdrop) backdrop.classList.toggle("visible", open);
    if (burger) {
      burger.textContent = open ? "✕" : "☰";
      burger.setAttribute("aria-label", open ? "Fermer le menu" : "Ouvrir le menu");
    }
    document.body.classList.toggle("admin-nav-lock-scroll", open);
  }

  if (burger && sidebar) {
    burger.addEventListener("click", function () {
      setNavOpen(!sidebar.classList.contains("open"));
    });
  }
  if (backdrop) {
    backdrop.addEventListener("click", function () {
      setNavOpen(false);
    });
  }
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && sidebar && sidebar.classList.contains("open")) {
      setNavOpen(false);
    }
  });

  // -------------------------------------------------------------------
  // Confirmation avant toute action destructive (data-confirm="message").
  // Délégué sur `document` (pas un forEach au chargement) pour couvrir
  // aussi les formulaires ajoutés dynamiquement plus tard, comme le
  // bouton "Supprimer" d'un média fraîchement envoyé dans une galerie.
  // -------------------------------------------------------------------
  document.addEventListener("submit", function (e) {
    const form = e.target.closest("form[data-confirm]");
    if (!form || form.dataset.confirmed === "true") return;
    e.preventDefault();

    function proceed() {
      form.dataset.confirmed = "true";

      // Suppression générique en AJAX (data-ajax-delete) : retire la ligne
      // du DOM sans recharger la page, au lieu de soumettre normalement.
      // Le repli (form.submit() classique) reste pour tout le reste.
      if ("ajaxDelete" in form.dataset) {
        const row = form.closest("[data-ajax-row]");
        const btn = form.querySelector("button");
        const originalLabel = btn ? btn.textContent : "";
        if (btn) { btn.disabled = true; btn.textContent = "…"; }

        fetch(form.action, {
          method: "POST",
          headers: { "X-Requested-With": "XMLHttpRequest" },
        })
          .then(function (res) { return res.json(); })
          .then(function (data) {
            if (data.ok) {
              if (row) row.remove();
            } else {
              if (btn) { btn.disabled = false; btn.textContent = originalLabel; }
              alert(data.error || "Erreur lors de la suppression.");
            }
          })
          .catch(function () {
            if (btn) { btn.disabled = false; btn.textContent = originalLabel; }
            alert("Connexion interrompue.");
          });
        return;
      }

      const loader = document.getElementById("admin-page-loader");
      if (loader) loader.hidden = false;
      form.submit();
    }

    if (typeof window.adminConfirm !== "function") {
      // Filet de sécurité si admin-modal.js n'a pas chargé
      if (window.confirm(form.dataset.confirm)) proceed();
      return;
    }

    window.adminConfirm(form.dataset.confirm).then(function (ok) {
      if (ok) proceed();
    });
  });

  // Filet anti-cache : après un enregistrement (voir admin-content-form.js,
  // qui utilise history.back() plutôt que de recharger l'URL), le retour
  // arrière peut restaurer une version en cache de la page — figée avant
  // l'enregistrement, donc sans le contenu tout juste créé/modifié. On
  // force un rechargement dans ce cas précis pour être sûr de voir l'état
  // à jour.
  window.addEventListener("pageshow", function (e) {
    if (e.persisted) location.reload();
  });
});
