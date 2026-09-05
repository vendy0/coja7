// Écran de transition affiché pendant les navigations classiques (liens,
// soumissions de formulaire) — même esprit que page-loader.js côté site
// public. Disparaît de lui-même quand la page suivante se charge (pas de
// "hide()" à appeler), sauf retour arrière depuis le cache navigateur.
document.addEventListener("DOMContentLoaded", function () {
  const loader = document.getElementById("admin-page-loader");
  if (!loader) return;

  function show() { loader.hidden = false; }

  document.addEventListener("click", function (e) {
    const link = e.target.closest("a[href]");
    if (!link) return;
    if (link.target === "_blank" || link.hasAttribute("download")) return;
    const href = link.getAttribute("href") || "";
    if (href.startsWith("#") || href.startsWith("javascript:")) return;
    try {
      const url = new URL(link.href, window.location.href);
      if (url.origin !== window.location.origin) return;
    } catch (e) { return; }
    show();
  });

  document.querySelectorAll("form").forEach(function (form) {
    form.addEventListener("submit", function () {
      // Les formulaires avec confirmation (data-confirm) gèrent leur
      // propre flux via la modale (voir admin.js), qui affiche l'écran de
      // transition lui-même juste avant l'envoi réel.
      if (!form.dataset.confirm) show();
    });
  });

  // Le bouton "Réessayer" d'un envoi ou le menu mobile ne doivent jamais
  // déclencher cet écran : ils ne sont ni des <a> ni des soumissions de
  // formulaire, donc rien à exclure explicitement ici.

  window.addEventListener("pageshow", function (e) {
    if (e.persisted) loader.hidden = true; // retour arrière depuis le cache
  });
});
