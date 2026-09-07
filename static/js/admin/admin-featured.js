document.addEventListener("DOMContentLoaded", function () {
  const list = document.getElementById("featured-current-list");
  const emptyMsg = document.getElementById("featured-empty-msg");
  const form = document.getElementById("featured-form");
  if (!list || !form) return;

  const TYPE_LABELS = {
    event: "Événement",
    sermon: "Sermon",
    communication: "Communication",
    rubric: "Rubrique",
  };

  function escapeHtml(s) {
    const d = document.createElement("div");
    d.textContent = s == null ? "" : s;
    return d.innerHTML;
  }

  // Affiche/masque automatiquement "Rien à la une" selon qu'il reste des
  // lignes ou non — fonctionne aussi bien pour les suppressions (gérées
  // génériquement dans admin.js, qui ne connaît pas cet élément) que pour
  // les ajouts ci-dessous.
  function syncEmptyMessage() {
    if (!emptyMsg) return;
    emptyMsg.hidden = list.querySelectorAll(".admin-row").length > 0;
  }
  new MutationObserver(syncEmptyMessage).observe(list, { childList: true });

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalLabel = submitBtn.textContent;
    submitBtn.disabled = true;
    submitBtn.textContent = "Ajout…";

    const visibleSelect = form.querySelector(".admin-featured-options:not([hidden])");
    const selectedOption = visibleSelect ? visibleSelect.options[visibleSelect.selectedIndex] : null;
    const contentType = form.querySelector("#content_type").value;

    fetch(form.action, {
      method: "POST",
      headers: { "X-Requested-With": "XMLHttpRequest" },
      body: new FormData(form),
    })
      .then(function (res) { return res.json(); })
      .then(function (data) {
        if (data.ok && data.item) {
          const row = document.createElement("div");
          row.className = "admin-row";
          row.setAttribute("data-ajax-row", "");
          row.innerHTML =
            '<div class="admin-row-main">' +
            '<p class="admin-row-title">' + escapeHtml(TYPE_LABELS[contentType] || contentType) + "</p>" +
            '<div class="admin-row-meta">' +
            "<span>Ordre " + escapeHtml(data.item.display_order) + "</span>" +
            (selectedOption ? '<span class="sep">·</span><span>' + escapeHtml(selectedOption.textContent) + "</span>" : "") +
            "</div></div>" +
            '<div class="admin-row-actions">' +
            '<form method="post" action="' + list.dataset.deleteUrlTemplate.replace("__ID__", data.item.id) + '" data-confirm="Retirer ce contenu de la une ?" data-ajax-delete>' +
            '<button type="submit" class="admin-link admin-link-danger">Retirer</button>' +
            "</form></div>";
          list.prepend(row);
          form.reset();
          // Le changement de content_type par défaut ne redéclenche pas
          // l'affichage/masquage des <select> par type : on le refait à la main.
          document.getElementById("content_type").dispatchEvent(new Event("change"));
        } else {
          alert((data && data.error) || "Erreur lors de l'ajout.");
        }
      })
      .catch(function () {
        alert("Connexion interrompue.");
      })
      .finally(function () {
        submitBtn.disabled = false;
        submitBtn.textContent = originalLabel;
      });
  });
});
