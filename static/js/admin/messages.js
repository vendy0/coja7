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
        headers: { "X-Requested-With": "XMLHttpRequest" },
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
});
