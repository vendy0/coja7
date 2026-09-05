document.addEventListener("DOMContentLoaded", function () {
  // -------------------------------------------------------------------
  // Menu latéral sur mobile : ouverture/fermeture, clic en dehors pour
  // fermer, et le bouton change d'icône (☰ / ✕) au même endroit.
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
  // Clic sur un lien du menu = navigation, donc pas besoin de le refermer
  // explicitement, mais utile si jamais une future version ne recharge pas
  // la page (SPA-like) : referme quand même après un clic dans le menu.
  if (sidebar) {
    sidebar.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", function () {
        setNavOpen(false);
      });
    });
  }
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && sidebar && sidebar.classList.contains("open")) {
      setNavOpen(false);
    }
  });

  // -------------------------------------------------------------------
  // Champs "relation" (voir form.html) : un texte libre avec suggestions
  // (datalist) doit se traduire par l'ID choisi dans un champ caché avant
  // l'envoi du formulaire. Si le texte tapé ne correspond à aucune
  // suggestion, on considère qu'aucun choix n'est fait (champ caché vidé).
  // -------------------------------------------------------------------
  document.querySelectorAll("input[data-relation-hidden]").forEach(function (labelInput) {
    const hidden = document.getElementById(labelInput.dataset.relationHidden);
    const datalist = document.getElementById(labelInput.getAttribute("list"));
    if (!hidden || !datalist) return;

    function sync() {
      const match = Array.from(datalist.options).find(function (o) {
        return o.value === labelInput.value;
      });
      hidden.value = match ? match.dataset.id : "";
    }

    labelInput.addEventListener("input", sync);
    labelInput.addEventListener("change", sync);
  });

  // -------------------------------------------------------------------
  // Confirmation avant toute action destructive (data-confirm="message")
  // -------------------------------------------------------------------
  document.querySelectorAll("form[data-confirm]").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      if (!window.confirm(form.dataset.confirm)) {
        e.preventDefault();
      }
    });
  });
});
