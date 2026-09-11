// SortableJS gère le glisser-déposer lui-même (souris ET tactile — le
// HTML5 natif ne fonctionne quasiment pas sur mobile, d'où la
// dépendance plutôt qu'une implémentation maison). On se contente
// d'envoyer le nouvel ordre au serveur une fois le déplacement terminé.
document.addEventListener("DOMContentLoaded", function () {
  const grid = document.getElementById("gallery-media-grid");
  if (!grid || typeof Sortable === "undefined") return;

  const reorderUrl = grid.dataset.reorderUrl;
  if (!reorderUrl) return;

  Sortable.create(grid, {
    animation: 150,
    delay: 120,              // évite de déclencher un drag par accident au simple tap/scroll tactile
    delayOnTouchOnly: true,
    onEnd: function () {
      const order = Array.from(grid.querySelectorAll(".admin-media-tile"))
        .map(function (tile) { return tile.dataset.mediaId; })
        .filter(Boolean);

      fetch(reorderUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Requested-With": "XMLHttpRequest",
          "X-CSRF-Token": window.getCsrfToken ? window.getCsrfToken() : "",
        },
        body: JSON.stringify({ order: order }),
      }).catch(function () {
        // En cas d'échec réseau, l'ordre affiché peut ne plus correspondre
        // à la base — un rechargement de page resynchronise. Pas de retry
        // automatique : mieux vaut que l'admin le remarque et réessaie.
      });
    },
  });
});