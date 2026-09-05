// Remplace <datalist>, dont le support des suggestions est très inégal
// sur les navigateurs mobiles (souvent silencieux, sans erreur — d'où le
// "je sais pas pourquoi ça marche pas"). Ce composant fait la même chose
// à la main : une liste filtrée qui s'affiche sous le champ, tactile.
//
// Deux modes, sur le même mécanisme :
//   - "relation" : le texte affiché est un libellé (ex. titre d'un
//     événement), mais c'est l'ID correspondant qui doit être soumis —
//     un champ caché (data-hidden-target) est synchronisé à la sélection.
//   - "text"     : champ libre, la suggestion choisie remplit directement
//     le champ visible (qui est aussi celui soumis) — pas de champ caché.
document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll("input[data-autocomplete]").forEach(function (input) {
    const mode = input.dataset.mode;
    const listEl = document.getElementById(input.dataset.listId);
    const optionsScript = document.getElementById(input.dataset.optionsId);
    const hidden = mode === "relation" ? document.getElementById(input.dataset.hiddenTarget) : null;
    if (!listEl || !optionsScript) return;

    let rawOptions = [];
    try { rawOptions = JSON.parse(optionsScript.textContent || "[]"); } catch (e) { rawOptions = []; }
    const options = rawOptions.map(function (opt) {
      return mode === "relation" ? opt : { label: opt, id: null };
    });

    let activeIndex = -1;

    function render(matches) {
      listEl.innerHTML = "";
      if (!matches.length) {
        const empty = document.createElement("div");
        empty.className = "admin-autocomplete-empty";
        empty.textContent = "Aucun résultat";
        listEl.appendChild(empty);
      } else {
        matches.forEach(function (opt) {
          const el = document.createElement("div");
          el.className = "admin-autocomplete-option";
          el.textContent = opt.label;
          // mousedown (pas click) : se déclenche avant le blur de l'input,
          // sinon la liste se referme avant que la sélection soit prise en compte
          el.addEventListener("mousedown", function (e) {
            e.preventDefault();
            select(opt);
          });
          listEl.appendChild(el);
        });
      }
      listEl.hidden = false;
      activeIndex = -1;
    }

    function select(opt) {
      input.value = opt.label;
      if (mode === "relation" && hidden) hidden.value = opt.id || "";
      listEl.hidden = true;
    }

    function filter() {
      const q = input.value.trim().toLowerCase();
      const matches = (q
        ? options.filter(function (o) { return o.label.toLowerCase().indexOf(q) !== -1; })
        : options
      ).slice(0, 8);
      render(matches);
    }

    input.addEventListener("focus", filter);
    input.addEventListener("input", function () {
      // On a retapé : tant qu'aucune suggestion n'est re-choisie, on
      // considère qu'il n'y a plus de correspondance valide.
      if (mode === "relation" && hidden) hidden.value = "";
      filter();
    });
    input.addEventListener("keydown", function (e) {
      const opts = Array.from(listEl.querySelectorAll(".admin-autocomplete-option"));
      if (!opts.length || listEl.hidden) return;
      if (e.key === "ArrowDown") {
        e.preventDefault();
        activeIndex = Math.min(activeIndex + 1, opts.length - 1);
        opts.forEach(function (o, i) { o.classList.toggle("is-active", i === activeIndex); });
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        activeIndex = Math.max(activeIndex - 1, 0);
        opts.forEach(function (o, i) { o.classList.toggle("is-active", i === activeIndex); });
      } else if (e.key === "Enter" && activeIndex >= 0) {
        e.preventDefault();
        opts[activeIndex].dispatchEvent(new Event("mousedown"));
      } else if (e.key === "Escape") {
        listEl.hidden = true;
      }
    });
    input.addEventListener("blur", function () {
      // Délai court pour laisser le "mousedown" d'une option s'exécuter avant
      setTimeout(function () { listEl.hidden = true; }, 120);
    });
  });
});
