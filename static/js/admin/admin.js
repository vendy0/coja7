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

    if (typeof window.adminConfirm !== "function") {
      // Filet de sécurité si admin-modal.js n'a pas chargé
      if (window.confirm(form.dataset.confirm)) form.submit();
      return;
    }

    window.adminConfirm(form.dataset.confirm).then(function (ok) {
      if (!ok) return;
      form.dataset.confirmed = "true";
      const loader = document.getElementById("admin-page-loader");
      if (loader) loader.hidden = false;
      form.submit();
    });
  });
});
