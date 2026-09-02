// Gère tous les boutons "Charger plus" du site (galeries, rubriques, sermons, notes...).
// Chaque bouton porte les attributs :
//   data-load-more          -> marqueur pour repérer le bouton
//   data-url="..."          -> endpoint qui renvoie {html, has_more}
//   data-target="#selector" -> conteneur dans lequel injecter le HTML reçu
//   data-offset="N"         -> offset de départ (nombre d'éléments déjà affichés)
//   data-limit="N"          -> taille d'une page (doit correspondre au backend)

document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll("[data-load-more]").forEach(initLoadMoreButton);
});

function initLoadMoreButton(button) {
  const originalLabel = button.textContent;

  button.addEventListener("click", function (event) {
    event.preventDefault();
    loadMore(button, originalLabel);
  });
}

// Construit le HTML des placeholders affichés pendant le chargement, selon
// le type déclaré sur le bouton (data-skeleton="row" | "thumb-row" | "card" | "video").
// Sans attribut data-skeleton, aucun placeholder n'est inséré (repli sur
// l'ancien comportement : juste le texte "Chargement…" sur le bouton).
function buildSkeletonHtml(type, count) {
  var item;
  if (type === "row") {
    item =
      '<div class="skeleton-row skeleton-item">' +
      '<span class="skeleton-bar sk-meta"></span>' +
      '<span class="skeleton-bar sk-title"></span>' +
      '<span class="skeleton-bar sk-sub"></span>' +
      "</div>";
  } else if (type === "thumb-row") {
    item =
      '<div class="skeleton-thumb-row skeleton-item">' +
      '<div class="sk-thumb"></div>' +
      '<div class="sk-content">' +
      '<span class="skeleton-bar sk-meta"></span>' +
      '<span class="skeleton-bar sk-title"></span>' +
      '<span class="skeleton-bar sk-sub"></span>' +
      "</div></div>";
  } else if (type === "card") {
    item = '<div class="skeleton-card skeleton-item"></div>';
  } else if (type === "video") {
    item =
      '<div class="skeleton-video skeleton-item">' +
      '<div class="sk-frame"></div>' +
      '<span class="skeleton-bar sk-title"></span>' +
      '<span class="skeleton-bar sk-sub"></span>' +
      "</div>";
  } else {
    return "";
  }
  return new Array(count + 1).join(item);
}

function loadMore(button, originalLabel) {
  const url = button.dataset.url;
  const targetSelector = button.dataset.target;
  const target = document.querySelector(targetSelector);
  const limit = parseInt(button.dataset.limit, 10) || 10;
  const offset = parseInt(button.dataset.offset, 10) || 0;
  const skeletonType = button.dataset.skeleton;

  if (!url || !target || button.classList.contains("is-loading")) {
    return;
  }

  button.classList.add("is-loading");
  button.textContent = "Chargement…";

  const skeletonHtml = buildSkeletonHtml(skeletonType, limit);
  if (skeletonHtml) {
    target.insertAdjacentHTML("beforeend", skeletonHtml);
  }

  function removeSkeletons() {
    target.querySelectorAll(".skeleton-item").forEach(function (node) {
      node.remove();
    });
  }

  const requestUrl = url + (url.includes("?") ? "&" : "?") + "offset=" + offset + "&limit=" + limit;

  fetch(requestUrl, { headers: { "X-Requested-With": "XMLHttpRequest" } })
    .then(function (response) {
      if (!response.ok) {
        throw new Error("Réponse réseau invalide (" + response.status + ")");
      }
      return response.json();
    })
    .then(function (data) {
      removeSkeletons();
      target.insertAdjacentHTML("beforeend", data.html || "");
      button.dataset.offset = offset + limit;

      if (!data.has_more) {
        button.style.display = "none";
      }
    })
    .catch(function (error) {
      removeSkeletons();
      console.error("Erreur lors du chargement :", error);
    })
    .finally(function () {
      button.classList.remove("is-loading");
      button.textContent = originalLabel;
    });
}
