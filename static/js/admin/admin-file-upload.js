// Dès qu'un fichier est choisi dans un champ image/audio/pdf du
// formulaire (voir form.html), on l'envoie tout de suite en AJAX avec une
// vraie barre de progression. En cas de coupure, un bouton "Réessayer"
// relance uniquement ce fichier — le reste du formulaire déjà rempli
// n'est jamais perdu, et il n'y a pas besoin de recharger la page.
//
// Si ça échoue et que l'admin soumet quand même le formulaire, le fichier
// est toujours dans le <input type="file">, donc le serveur retente
// l'envoi classique à la soumission (voir _apply_uploads côté Flask) —
// rien ne casse si ce script ne se charge pas.
document.addEventListener("DOMContentLoaded", function () {
  // Champs "type de média" pilotés automatiquement (voir admins_config.py
  // "auto_type_field") : masqués dès le chargement — leur valeur reste
  // celle déjà en base tant qu'aucun nouveau fichier n'est choisi, et se
  // met à jour toute seule sinon (voir plus bas dans startUpload).
  document.querySelectorAll("input[data-auto-type-target]").forEach(function (input) {
    const target = document.getElementById(input.dataset.autoTypeTarget);
    if (!target) return;
    const wrap = target.closest(".admin-field");
    if (wrap) wrap.hidden = true;
  });

  document.querySelectorAll("input[data-async-upload]").forEach(function (input) {
    const fieldName = input.name;
    const uploadUrl = input.dataset.uploadUrl;
    const hidden = document.getElementById("uploaded-" + fieldName);
    const wrap = document.getElementById("progress-" + fieldName);
    if (!hidden || !wrap || !uploadUrl) return;

    const fill = wrap.querySelector(".admin-upload-progress-fill");
    const text = wrap.querySelector(".admin-upload-progress-text");
    const retryBtn = wrap.querySelector(".admin-upload-retry");
    const autoTypeTarget = input.dataset.autoTypeTarget
      ? document.getElementById(input.dataset.autoTypeTarget)
      : null;
    let currentFile = null;

    function startUpload(file) {
      currentFile = file;
      hidden.value = "";
      wrap.hidden = false;
      retryBtn.hidden = true;
      fill.style.width = "0%";
      text.textContent = "Envoi… 0%";

      if (autoTypeTarget) {
        autoTypeTarget.value = file.type.indexOf("video/") === 0 ? "video" : "image";
      }

      const fd = new FormData();
      fd.append("file", file);

      const xhr = new XMLHttpRequest();
      xhr.open("POST", uploadUrl);
      xhr.upload.addEventListener("progress", function (e) {
        if (e.lengthComputable) {
          const pct = Math.round((e.loaded / e.total) * 100);
          fill.style.width = pct + "%";
          text.textContent = "Envoi… " + pct + "%";
        }
      });
      xhr.onload = function () {
        let data = null;
        try { data = JSON.parse(xhr.responseText); } catch (e) { /* réponse non-JSON */ }
        if (xhr.status >= 200 && xhr.status < 300 && data && data.ok) {
          hidden.value = data.url;
          fill.style.width = "100%";
          text.textContent = "Envoyé ✓";
          retryBtn.hidden = true;
        } else {
          text.textContent = "Échec — " + ((data && data.error) || "erreur serveur");
          retryBtn.hidden = false;
        }
      };
      xhr.onerror = function () {
        text.textContent = "Échec — connexion interrompue";
        retryBtn.hidden = false;
      };
      xhr.send(fd);
    }

    input.addEventListener("change", function () {
      if (input.files && input.files[0]) startUpload(input.files[0]);
    });
    retryBtn.addEventListener("click", function () {
      if (currentFile) startUpload(currentFile);
    });
  });
});
