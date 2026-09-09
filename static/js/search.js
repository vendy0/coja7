// Recherche floue côté client, partagée entre plusieurs pages (sermons,
// galeries, rubriques). Charge une seule fois un petit index JSON (tous
// les titres), puis filtre en local à chaque frappe — pas de requête
// serveur par lettre tapée.
//
// Deux comportements possibles pour un même champ, choisis via
// data-search-mode :
//   "dropdown" -> affiche une liste de suggestions sous le champ, cliquer
//                 une suggestion navigue vers sa page de détail (sermons,
//                 galeries)
//   "filter"   -> filtre en direct la grille déjà affichée sur la page
//                 (rubriques, qui n'ont pas de page de détail)
document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll("input[data-search-index-url]").forEach(function (input) {
    const indexUrl = input.dataset.searchIndexUrl;
    const mode = input.dataset.searchMode || "dropdown";
    const keys = (input.dataset.searchKeys || "title").split(",");

    let fuse = null;
    let indexLoaded = false;
    let indexLoading = null;

    function loadIndex() {
      if (indexLoading) return indexLoading;
      indexLoading = fetch(indexUrl, { headers: { "X-Requested-With": "XMLHttpRequest" } })
        .then(function (res) { return res.json(); })
        .then(function (data) {
          fuse = new Fuse(data.items || [], { keys: keys, threshold: 0.35 });
          indexLoaded = true;
        })
        .catch(function () {
          indexLoaded = false;
        });
      return indexLoading;
    }

    // Chargement dès qu'on interagit avec le champ, pas au chargement de la
    // page — pas besoin de télécharger l'index si personne ne cherche.
    input.addEventListener("focus", loadIndex, { once: true });

    if (mode === "dropdown") {
      setupDropdown(input, function () { return fuse; });
    } else {
      setupFilter(input, function () { return fuse; });
    }
  });

  function escapeHtml(s) {
    const d = document.createElement("div");
    d.textContent = s == null ? "" : s;
    return d.innerHTML;
  }

  // -------------------------------------------------------------------
  // Mode "dropdown" : suggestions sous le champ, clic = navigation
  // -------------------------------------------------------------------
  function setupDropdown(input, getFuse) {
    const listEl = document.getElementById(input.dataset.searchListId);
    if (!listEl) return;
    const urlTemplate = input.dataset.searchUrlTemplate; // avec __ID__

    function render(results) {
      listEl.innerHTML = "";
      if (!results.length) {
        const empty = document.createElement("div");
        empty.className = "search-suggestion-empty";
        empty.textContent = "Aucun résultat";
        listEl.appendChild(empty);
      } else {
        results.slice(0, 8).forEach(function (r) {
          const item = r.item;
          const el = document.createElement("a");
          el.className = "search-suggestion";
          el.href = urlTemplate.replace("__ID__", item.id);
          el.innerHTML =
            '<span class="search-suggestion-title">' + escapeHtml(item.title) + "</span>" +
            (item.subtitle || item.reference || item.department
              ? '<span class="search-suggestion-meta">' + escapeHtml(item.subtitle || item.reference || item.department) + "</span>"
              : "");
          listEl.appendChild(el);
        });
      }
      listEl.hidden = false;
    }

    input.addEventListener("input", function () {
      const fuse = getFuse();
      const q = input.value.trim();
      if (!fuse || !q) {
        listEl.hidden = true;
        return;
      }
      render(fuse.search(q));
    });

    input.addEventListener("blur", function () {
      setTimeout(function () { listEl.hidden = true; }, 150);
    });
    input.addEventListener("focus", function () {
      if (input.value.trim()) input.dispatchEvent(new Event("input"));
    });
  }

  // -------------------------------------------------------------------
  // Mode "filter" : filtre en direct la grille déjà présente sur la page
  // -------------------------------------------------------------------
  function setupFilter(input, getFuse) {
    const grid = document.getElementById(input.dataset.searchGridId);
    const loadMoreBtn = document.querySelector(input.dataset.searchLoadMoreSelector || "[data-load-more]");
    if (!grid) return;

    let originalHtml = null;

    input.addEventListener("input", function () {
      const fuse = getFuse();
      const q = input.value.trim();

      if (!q) {
        // Recherche effacée : on remet la grille normale (pagination incluse)
        if (originalHtml !== null) grid.innerHTML = originalHtml;
        if (loadMoreBtn) loadMoreBtn.hidden = false;
        return;
      }
      if (!fuse) return; // index pas encore chargé (focus trop récent)

      if (originalHtml === null) originalHtml = grid.innerHTML;
      if (loadMoreBtn) loadMoreBtn.hidden = true;

      const results = fuse.search(q);
      if (!results.length) {
        grid.innerHTML = '<p class="search-no-results">Aucune rubrique ne correspond à « ' + escapeHtml(q) + ' ».</p>';
        return;
      }
      grid.innerHTML = results.map(function (r) { return buildRubricCard(r.item); }).join("");
    });
  }

  function buildRubricCard(item) {
    return (
      '<div class="video-card">' +
      '<div class="video-wrapper">' +
      '<iframe src="https://www.youtube.com/embed/' + escapeHtml(item.youtube_id) + '" title="' + escapeHtml(item.title) + '" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>' +
      "</div>" +
      '<div class="video-info">' +
      '<span class="category-tag">' + escapeHtml(item.category || "Non catégorisé") + "</span>" +
      "<h3>" + escapeHtml(item.title) + "</h3>" +
      '<div class="speaker">' +
      '<svg viewBox="0 0 24 24" fill="none" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>' +
      "<span>" + escapeHtml(item.speaker || "Intervenant") + "</span>" +
      "</div></div></div>"
    );
  }
});
