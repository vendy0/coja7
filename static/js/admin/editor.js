// Transforme chaque <div class="admin-rich-editor"> en éditeur Quill
// (titres, gras, italique, souligné, listes, retrait, lien, plein écran)
// et garde une <textarea> cachée synchronisée avec le HTML produit, pour
// un envoi classique en <form>.
//
// Robustesse : la textarea reste visible et utilisable tant que Quill n'a
// pas fini de s'initialiser avec succès (CDN bloqué, coupure réseau...).
// On ne la masque qu'une fois l'éditeur réellement prêt — jamais avant.
document.addEventListener("DOMContentLoaded", function () {
  if (typeof Quill === "undefined") return;

  document.querySelectorAll(".admin-rich-editor").forEach(function (container) {
    const fieldName = container.id.replace("editor-", "");
    const source = document.getElementById("f-" + fieldName);
    const wrap = container.closest(".admin-rich-wrap");
    if (!source) return;

    const quill = new Quill(container, {
      theme: "snow",
      placeholder: source.getAttribute("placeholder") || "Écris ici…",
      modules: {
        toolbar: {
          container: [
            [{ header: [2, 3, false] }],
            ["bold", "italic", "underline"],
            [{ list: "ordered" }, { list: "bullet" }],
            [{ indent: "-1" }, { indent: "+1" }],
            ["blockquote", "link"],
            ["clean"],
            ["fullscreen"],
          ],
          handlers: {
            fullscreen: function () {
              toggleFullscreen(wrap);
            },
          },
        },
      },
    });

    // Pré-remplissage à partir du contenu existant (édition)
    if (source.value.trim()) {
      quill.clipboard.dangerouslyPasteHTML(source.value);
    }

    // Quill est prêt : on peut masquer la textarea brute sans risque
    source.style.display = "none";

    quill.on("text-change", function () {
      source.value = quill.root.innerHTML;
    });

    const form = source.closest("form");
    if (form) {
      form.addEventListener("submit", function () {
        source.value = quill.root.innerHTML;
      });
    }
  });

  // Quill n'a pas d'icône native pour un bouton personnalisé : on en dessine une
  document.querySelectorAll(".ql-fullscreen").forEach(function (btn) {
    btn.innerHTML =
      '<svg viewBox="0 0 18 18" width="16" height="16">' +
      '<polyline points="6 2 2 2 2 6" fill="none" stroke="currentColor" stroke-width="1.6"></polyline>' +
      '<polyline points="12 2 16 2 16 6" fill="none" stroke="currentColor" stroke-width="1.6"></polyline>' +
      '<polyline points="6 16 2 16 2 12" fill="none" stroke="currentColor" stroke-width="1.6"></polyline>' +
      '<polyline points="12 16 16 16 16 12" fill="none" stroke="currentColor" stroke-width="1.6"></polyline>' +
      "</svg>";
    btn.setAttribute("type", "button");
    btn.setAttribute("aria-label", "Basculer le plein écran");
    btn.title = "Plein écran";
  });

  // Échap referme l'éditeur actuellement en plein écran, où qu'on soit dans la page
  document.addEventListener("keydown", function (e) {
    if (e.key !== "Escape") return;
    const openWrap = document.querySelector(".admin-rich-wrap.is-fullscreen");
    if (openWrap) toggleFullscreen(openWrap);
  });
});

function toggleFullscreen(wrap) {
  if (!wrap) return;
  const isFull = wrap.classList.toggle("is-fullscreen");
  document.body.classList.toggle("admin-editor-lock-scroll", isFull);
  const btn = wrap.querySelector(".ql-fullscreen");
  if (btn) btn.classList.toggle("ql-active", isFull);
}
