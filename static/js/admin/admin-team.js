document.addEventListener("DOMContentLoaded", function () {
  // -------------------------------------------------------------------
  // Activer / désactiver un compte — gère sa propre confirmation (via
  // window.adminConfirm) plutôt que de passer par le mécanisme générique
  // de admin.js, qui ne sait faire que "supprimer une ligne" ; ici on veut
  // mettre à jour le statut affiché, pas retirer la ligne. stopPropagation
  // empêche admin.js de traiter le même clic une deuxième fois.
  // -------------------------------------------------------------------
  document.querySelectorAll("form[data-ajax-toggle-active]").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      e.stopPropagation();

      function proceed() {
        const btn = form.querySelector("button");
        const row = form.closest(".admin-row");
        const statusEl = row ? row.querySelector(".admin-status") : null;
        const originalLabel = btn.textContent;
        btn.disabled = true;
        btn.textContent = "…";

        fetch(form.action, { method: "POST", headers: { "X-Requested-With": "XMLHttpRequest" } })
          .then(function (res) { return res.json(); })
          .then(function (data) {
            if (data.ok) {
              if (statusEl) statusEl.textContent = data.is_active ? "Actif" : "Désactivé";
              btn.textContent = data.is_active ? "Désactiver" : "Réactiver";
              btn.classList.toggle("admin-link-danger", data.is_active);
            } else {
              btn.textContent = originalLabel;
              alert(data.error || "Erreur.");
            }
          })
          .catch(function () {
            btn.textContent = originalLabel;
            alert("Connexion interrompue.");
          })
          .finally(function () {
            btn.disabled = false;
          });
      }

      if (typeof window.adminConfirm !== "function") {
        if (window.confirm(form.dataset.confirm)) proceed();
        return;
      }
      window.adminConfirm(form.dataset.confirm).then(function (ok) {
        if (ok) proceed();
      });
    });
  });

  // -------------------------------------------------------------------
  // Changer un rôle — select qui s'auto-soumet, converti en AJAX
  // -------------------------------------------------------------------
  document.querySelectorAll("select[data-ajax-role]").forEach(function (select) {
    select.dataset.previousValue = select.value;

    select.addEventListener("focus", function () {
      select.dataset.previousValue = select.value;
    });

    select.addEventListener("change", function () {
      const form = select.closest("form");
      const previousValue = select.dataset.previousValue;
      select.disabled = true;

      fetch(form.action, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
          "X-Requested-With": "XMLHttpRequest",
        },
        body: "role=" + encodeURIComponent(select.value),
      })
        .then(function (res) { return res.json(); })
        .then(function (data) {
          if (data.ok) {
            select.dataset.previousValue = data.role;
          } else {
            select.value = previousValue;
            alert(data.error || "Erreur.");
          }
        })
        .catch(function () {
          select.value = previousValue;
          alert("Connexion interrompue.");
        })
        .finally(function () {
          select.disabled = false;
        });
    });
  });
});
