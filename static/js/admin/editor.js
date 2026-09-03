// Transforme chaque <div class="admin-rich-editor"> en éditeur Quill
// (gras, italique, titres, listes...) et garde une <textarea> cachée
// synchronisée avec le HTML produit, pour un envoi classique en <form>.
document.addEventListener("DOMContentLoaded", function () {
  if (typeof Quill === "undefined") return;

  document.querySelectorAll(".admin-rich-editor").forEach(function (container) {
    const fieldName = container.id.replace("editor-", "");
    const source = document.getElementById("f-" + fieldName);
    if (!source) return;

    const quill = new Quill(container, {
      theme: "snow",
      placeholder: "Écris ici…",
      modules: {
        toolbar: [
          [{ header: [2, 3, false] }],
          ["bold", "italic", "underline"],
          [{ list: "ordered" }, { list: "bullet" }],
          ["link", "blockquote"],
          ["clean"],
        ],
      },
    });

    // Pré-remplissage à partir du contenu existant (édition)
    if (source.value.trim()) {
      quill.clipboard.dangerouslyPasteHTML(source.value);
    }

    // Le formulaire soumet la textarea cachée : on la garde à jour à chaque frappe
    quill.on("text-change", function () {
      source.value = quill.root.innerHTML;
    });

    // Sécurité supplémentaire au moment de la soumission
    const form = source.closest("form");
    if (form) {
      form.addEventListener("submit", function () {
        source.value = quill.root.innerHTML;
      });
    }
  });
});
