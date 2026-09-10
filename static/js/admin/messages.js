// Bascule "traité"/"non traité" sans recharger la page. Le <form> classique
// reste en place (repli si JS indisponible) : on intercepte juste sa
// soumission pour l'envoyer en AJAX à la place.
document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll("form[data-ajax-toggle]").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();

      const btn = form.querySelector("button");
      const statusEl = form.closest(".admin-row").querySelector(".msg-status");
      const originalLabel = btn.textContent;
      btn.disabled = true;
      btn.textContent = "…";

      // Avertit si on essaie de quitter/recharger pendant l'envoi (bref, mais demandé explicitement)
      function warnBeforeUnload(ev) {
        ev.preventDefault();
        ev.returnValue = "";
      }
      window.addEventListener("beforeunload", warnBeforeUnload);

      fetch(form.action, {
        method: "POST",
        headers: { "X-Requested-With": "XMLHttpRequest", "X-CSRF-Token": window.getCsrfToken() },
      })
        .then(function (res) { return res.json(); })
        .then(function (data) {
          if (data.ok) {
            statusEl.textContent = data.is_resolved ? "Traité" : "Non traité";
            btn.textContent = data.is_resolved ? "Non traité" : "Traité";
          } else {
            btn.textContent = originalLabel;
            statusEl.textContent = "Erreur : " + (data.error || "réessaie");
          }
        })
        .catch(function () {
          btn.textContent = originalLabel;
          statusEl.textContent = "Connexion interrompue";
        })
        .finally(function () {
          btn.disabled = false;
          window.removeEventListener("beforeunload", warnBeforeUnload);
        });
    });
  });

  // -------------------------------------------------------------------
  // Filtres "Tous / Non traités / Traités" en AJAX (voir messages.html)
  // -------------------------------------------------------------------
  const list = document.getElementById("messages-list");
  const tabs = document.querySelectorAll(".admin-filter-tabs a");
  const countEl = document.querySelector(".admin-toolbar-count");
  if (!list || !tabs.length) return;

  const toggleTemplate = list.dataset.toggleUrlTemplate;
  const deleteTemplate = list.dataset.deleteUrlTemplate;

  function escapeHtml(s) {
    const d = document.createElement("div");
    d.textContent = s == null ? "" : s;
    return d.innerHTML;
  }

  function buildRow(msg) {
    const row = document.createElement("div");
    row.className = "admin-row";
    row.setAttribute("data-ajax-row", "");
    row.innerHTML =
      '<div class="admin-row-main">' +
      '<p class="admin-row-title admin-row-title-wrap">' + escapeHtml(msg.message) + "</p>" +
      '<div class="admin-row-meta">' +
      "<span>" + escapeHtml(msg.created_at_display) + "</span>" +
      '<span class="sep">·</span>' +
      '<span class="msg-status">' + (msg.is_resolved ? "Traité" : "Non traité") + "</span>" +
      (msg.contact ? '<span class="sep">·</span><span>' + escapeHtml(msg.contact) + "</span>" : "") +
      "</div></div>" +
      '<div class="admin-row-actions">' +
      '<form method="post" action="' + toggleTemplate.replace("__ID__", msg.id) + '" class="admin-inline-form" data-ajax-toggle>' +
      '<button type="submit" class="admin-link">' + (msg.is_resolved ? "Non traité" : "Traité") + "</button>" +
      "</form>" +
      '<form method="post" action="' + deleteTemplate.replace("__ID__", msg.id) + '" class="admin-inline-form" data-confirm="Supprimer ce message ?" data-ajax-delete>' +
      '<button type="submit" class="admin-link admin-link-danger">Supprimer</button>' +
      "</form></div>";
    return row;
  }

  function render(messages, status) {
    list.innerHTML = "";
    if (!messages.length) {
      const p = document.createElement("p");
      p.className = "admin-empty";
      p.textContent = "Aucun message" + (status !== "all" ? " dans ce filtre" : "") + ".";
      list.appendChild(p);
    } else {
      messages.forEach(function (m) { list.appendChild(buildRow(m)); });
    }
    if (countEl) countEl.textContent = messages.length + " message(s)";
  }

  tabs.forEach(function (tab) {
    tab.addEventListener("click", function (e) {
      e.preventDefault();
      const url = tab.href;

      tabs.forEach(function (t) { t.classList.remove("active"); });
      tab.classList.add("active");
      list.classList.add("is-loading");

      fetch(url, { headers: { "X-Requested-With": "XMLHttpRequest" } })
        .then(function (res) { return res.json(); })
        .then(function (data) {
          if (data.ok) {
            render(data.messages, data.status);
            history.pushState(null, "", url);
          }
        })
        .catch(function () { /* on laisse l'affichage tel quel en cas d'échec */ })
        .finally(function () {
          list.classList.remove("is-loading");
        });
    });
  });
});
