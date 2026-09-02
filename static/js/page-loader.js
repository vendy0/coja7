// Écran de transition entre pages : au clic sur un lien de navigation
// classique, on injecte un squelette (même esprit que les placeholders de
// load-more.js) qui recouvre exactement la zone de contenu — sous le
// header, au-dessus du nav — pendant que la page suivante arrive du
// serveur. Comme il s'agit d'une vraie navigation (pas d'AJAX), l'écran
// disparaît tout seul quand le document est remplacé : pas de logique
// "hide()" à oublier d'appeler.
// N'intercepte jamais les liens gérés en AJAX par calendar.js / load-more.js.

(function () {
  "use strict";

  var LOADER_ID = "page-loader";
  var MAX_LIFETIME_MS = 8000; // filet de sécurité si la navigation échoue/traîne

  function skeletonHtml() {
    var row =
      '<div class="skeleton-row">' +
      '<span class="skeleton-bar sk-meta"></span>' +
      '<span class="skeleton-bar sk-title"></span>' +
      '<span class="skeleton-bar sk-sub"></span>' +
      "</div>";
    return (
      '<div class="page-skeleton-intro">' +
      '<span class="skeleton-bar sk-h1"></span>' +
      '<span class="skeleton-bar sk-h2"></span>' +
      "</div>" +
      new Array(6).join(row)
    );
  }

  function showPageSkeleton() {
    if (document.getElementById(LOADER_ID)) return; // déjà affiché

    var header = document.querySelector("header");
    var nav = document.querySelector("nav");
    var topOffset = header ? header.getBoundingClientRect().height : 0;
    var bottomOffset = nav ? nav.getBoundingClientRect().height : 0;

    var el = document.createElement("div");
    el.id = LOADER_ID;
    el.setAttribute("aria-hidden", "true");
    el.style.top = topOffset + "px";
    el.style.bottom = bottomOffset + "px";
    el.innerHTML = skeletonHtml();
    document.body.appendChild(el);

    setTimeout(function () {
      if (el.parentNode) el.parentNode.removeChild(el);
    }, MAX_LIFETIME_MS);
  }

  document.addEventListener(
    "click",
    function (ev) {
      var link = ev.target.closest("a[href]");
      if (!link) return;

      // Liens gérés en AJAX (calendrier, "charger plus") : pas de rechargement de page.
      if (link.hasAttribute("data-load-more")) return;
      if (link.closest("#calendar-days") || link.closest(".month-nav")) return;

      var href = link.getAttribute("href") || "";
      if (!href || href.charAt(0) === "#") return;
      if (href.indexOf("mailto:") === 0 || href.indexOf("tel:") === 0) return;
      if (link.target === "_blank" || link.hasAttribute("download")) return;
      if (link.origin && link.origin !== window.location.origin) return;
      if (ev.defaultPrevented) return;
      if (ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.altKey || ev.button === 1) return;

      showPageSkeleton();
    },
    true
  );

  // Si la page revient depuis le cache du navigateur (bouton retour), on
  // retire tout squelette qui aurait pu rester affiché.
  window.addEventListener("pageshow", function (ev) {
    if (!ev.persisted) return;
    var el = document.getElementById(LOADER_ID);
    if (el && el.parentNode) el.parentNode.removeChild(el);
  });
})();
