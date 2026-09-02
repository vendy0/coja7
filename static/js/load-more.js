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

function loadMore(button, originalLabel) {
  const url = button.dataset.url;
  const targetSelector = button.dataset.target;
  const target = document.querySelector(targetSelector);
  const limit = parseInt(button.dataset.limit, 10) || 10;
  const offset = parseInt(button.dataset.offset, 10) || 0;

  if (!url || !target || button.classList.contains("is-loading")) {
    return;
  }

  button.classList.add("is-loading");
  button.textContent = "Chargement…";

  const requestUrl = url + (url.includes("?") ? "&" : "?") + "offset=" + offset + "&limit=" + limit;

  fetch(requestUrl, { headers: { "X-Requested-With": "XMLHttpRequest" } })
    .then(function (response) {
      if (!response.ok) {
        throw new Error("Réponse réseau invalide (" + response.status + ")");
      }
      return response.json();
    })
    .then(function (data) {
      target.insertAdjacentHTML("beforeend", data.html || "");
      button.dataset.offset = offset + limit;

      if (!data.has_more) {
        button.style.display = "none";
      }
    })
    .catch(function (error) {
      console.error("Erreur lors du chargement :", error);
    })
    .finally(function () {
      button.classList.remove("is-loading");
      button.textContent = originalLabel;
    });
}
