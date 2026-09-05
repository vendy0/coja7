// Envoi des médias de galerie, un fichier à la fois (voir gallery_media.html).
//
// Pourquoi un fichier à la fois plutôt qu'un <form> classique avec
// plusieurs fichiers : sur un réseau mobile instable, un seul gros envoi
// qui tombe en panne au 8e fichier sur 10 fait tout perdre et oblige à
// tout recommencer. Ici, chaque fichier est son propre appel réseau : ce
// qui a réussi reste enregistré, et on ne relance que ce qui a échoué.
(function () {
  document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("gallery-upload-form");
    if (!form) return;

    const input = document.getElementById("gallery-files");
    const creditInput = document.getElementById("gallery-credit");
    const queueEl = document.getElementById("gallery-upload-queue");
    const gridEl = document.getElementById("gallery-media-grid");
    const uploadUrl = form.dataset.uploadUrl;
    const deleteUrlTemplate = form.dataset.deleteUrlTemplate;

    let queue = [];
    let processing = false;

    input.addEventListener("change", function () {
      Array.from(input.files || []).forEach(function (file) {
        queue.push({ id: randomId(), file: file, status: "pending", progress: 0, error: null });
      });
      input.value = ""; // permet de resélectionner les mêmes fichiers plus tard si besoin
      renderQueue();
      processQueue();
    });

    function randomId() {
      return "f" + Math.random().toString(36).slice(2) + Date.now().toString(36);
    }

    function escapeHtml(s) {
      const d = document.createElement("div");
      d.textContent = s == null ? "" : s;
      return d.innerHTML;
    }

    function statusLabel(item) {
      switch (item.status) {
        case "pending": return "En attente…";
        case "uploading": return "Envoi… " + (item.progress || 0) + "%";
        case "done": return "Envoyé ✓";
        case "error": return "Échec — " + (item.error || "réessaie");
        default: return "";
      }
    }

    function renderQueue() {
      queueEl.innerHTML = "";
      queue.forEach(function (item) {
        if (item.status === "done") return; // le fichier apparaît désormais dans la grille, plus besoin de le lister ici
        const row = document.createElement("div");
        row.className = "admin-upload-row admin-upload-" + item.status;
        row.innerHTML =
          '<span class="admin-upload-name">' + escapeHtml(item.file.name) + "</span>" +
          '<span class="admin-upload-status">' + statusLabel(item) + "</span>" +
          (item.status === "error"
            ? '<button type="button" class="admin-link" data-retry="' + item.id + '">Réessayer</button>'
            : "");
        queueEl.appendChild(row);
      });
      queueEl.querySelectorAll("[data-retry]").forEach(function (btn) {
        btn.addEventListener("click", function () {
          const item = queue.find(function (q) { return q.id === btn.dataset.retry; });
          if (item) {
            item.status = "pending";
            item.error = null;
            renderQueue();
            processQueue();
          }
        });
      });
    }

    async function processQueue() {
      if (processing) return;
      processing = true;
      for (const item of queue) {
        if (item.status !== "pending") continue;
        item.status = "uploading";
        item.progress = 0;
        renderQueue();
        try {
          const mediaType = item.file.type.indexOf("video/") === 0 ? "video" : "photo";
          let thumbnailBlob = null;
          if (mediaType === "video") {
            try {
              thumbnailBlob = await generateVideoThumbnail(item.file);
            } catch (e) {
              thumbnailBlob = null; // pas grave : la vidéo s'enverra sans vignette
            }
          }
          const savedItem = await uploadOne(item.file, mediaType, thumbnailBlob, function (pct) {
            item.progress = pct;
            renderQueue();
          });
          item.status = "done";
          renderQueue();
          appendTile(savedItem);
        } catch (e) {
          item.status = "error";
          item.error = (e && e.message) || "Erreur réseau";
          renderQueue();
        }
      }
      processing = false;
    }

    function uploadOne(file, mediaType, thumbnailBlob, onProgress) {
      return new Promise(function (resolve, reject) {
        const fd = new FormData();
        fd.append("file", file);
        fd.append("type", mediaType);
        fd.append("credit", creditInput.value || "");
        if (thumbnailBlob) fd.append("thumbnail", thumbnailBlob, "thumb.jpg");

        const xhr = new XMLHttpRequest();
        xhr.open("POST", uploadUrl);
        xhr.upload.addEventListener("progress", function (e) {
          if (e.lengthComputable) onProgress(Math.round((e.loaded / e.total) * 100));
        });
        xhr.onload = function () {
          let data = null;
          try { data = JSON.parse(xhr.responseText); } catch (e) { /* réponse non-JSON */ }
          if (xhr.status >= 200 && xhr.status < 300 && data && data.ok) {
            resolve(data.item);
          } else {
            reject(new Error((data && data.error) || "Erreur serveur (" + xhr.status + ")"));
          }
        };
        xhr.onerror = function () {
          reject(new Error("Connexion interrompue"));
        };
        xhr.send(fd);
      });
    }

    // Grabbe une image de la vidéo (vers ~1s ou la moitié si plus courte)
    // directement dans le navigateur, sans repasser par le serveur.
    function generateVideoThumbnail(file) {
      return new Promise(function (resolve, reject) {
        const url = URL.createObjectURL(file);
        const video = document.createElement("video");
        video.preload = "metadata";
        video.muted = true;
        video.playsInline = true;
        video.src = url;

        const cleanup = function () { URL.revokeObjectURL(url); };
        const timeout = setTimeout(function () {
          cleanup();
          reject(new Error("Délai dépassé pour la vignette"));
        }, 15000);

        video.addEventListener("loadedmetadata", function () {
          const seekTo = Math.min(1, (video.duration || 2) / 2);
          video.currentTime = seekTo;
        });
        video.addEventListener("seeked", function () {
          try {
            const canvas = document.createElement("canvas");
            canvas.width = video.videoWidth || 320;
            canvas.height = video.videoHeight || 180;
            canvas.getContext("2d").drawImage(video, 0, 0, canvas.width, canvas.height);
            canvas.toBlob(function (blob) {
              clearTimeout(timeout);
              cleanup();
              if (blob) resolve(blob); else reject(new Error("Vignette vide"));
            }, "image/jpeg", 0.8);
          } catch (e) {
            clearTimeout(timeout);
            cleanup();
            reject(e);
          }
        });
        video.addEventListener("error", function () {
          clearTimeout(timeout);
          cleanup();
          reject(new Error("Vidéo illisible"));
        });
      });
    }

    function appendTile(item) {
      const emptyMsg = gridEl.querySelector(".admin-empty");
      if (emptyMsg) emptyMsg.remove();

      const tile = document.createElement("div");
      tile.className = "admin-media-tile";
      const mediaHtml = item.type === "video"
        ? '<video src="' + item.media_url + '" controls poster="' + (item.thumbnails_url || "") + '"></video>'
        : '<img src="' + (item.thumbnails_url || item.media_url) + '" alt="">';
      tile.innerHTML =
        mediaHtml +
        '<div class="admin-media-tile-meta">' +
        "<span>" + escapeHtml(item.credit || "—") + "</span>" +
        '<form method="post" action="' + deleteUrlTemplate.replace("__ID__", item.id) + '" data-confirm="Supprimer ce média ?">' +
        '<button type="submit" class="admin-link admin-link-danger">Supprimer</button>' +
        "</form></div>";
      gridEl.prepend(tile);

      // admin.js a déjà attaché les confirmations au chargement de la page,
      // avant que ce tile existe : on refait le même branchement pour lui.
      const delForm = tile.querySelector("form[data-confirm]");
      if (delForm) {
        delForm.addEventListener("submit", function (e) {
          if (!window.confirm(delForm.dataset.confirm)) e.preventDefault();
        });
      }
    }
  });
})();
