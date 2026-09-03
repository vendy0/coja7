document.addEventListener("DOMContentLoaded", function () {
  console.log("editor.js chargé");
  console.log("Quill =", typeof Quill);

  if (typeof Quill === "undefined") {
    console.error("ERREUR : Quill n'est pas disponible.");
    return;
  }

  document.querySelectorAll(".admin-rich-editor").forEach(function (container) {
    const fieldName = container.id.replace("editor-", "");
    const source = document.getElementById("f-" + fieldName);

    console.log("Initialisation Quill :", fieldName);

    if (!source) {
      console.error("Textarea introuvable :", "f-" + fieldName);
      return;
    }

    const quill = new Quill(container, {
      theme: "snow",
      placeholder: "Écris ici…",
      modules: {
        toolbar: [
          [{ header: [2, 3, false] }],
          ["bold", "italic", "underline"],
          [{ list: "ordered" }, { list: "bullet" }],
          ["link", "blockquote"],
          ["clean"]
        ]
      }
    });

    // Contenu existant
    if (source.value.trim()) {
      quill.clipboard.dangerouslyPasteHTML(source.value);
    }

    // La textarea reste synchronisée avec Quill
    function syncEditor() {
      source.value = quill.root.innerHTML;
    }

    syncEditor();

    quill.on("text-change", syncEditor);

    const form = source.closest("form");

    if (form) {
      form.addEventListener("submit", syncEditor);
    }
  });
});