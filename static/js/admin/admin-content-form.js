// Le <form> classique reste le repli si ce script ne charge pas (JS
// désactivé, erreur) : rien ne change dans ce cas, il se soumet et
// recharge la page normalement, exactement comme avant.
//
// Avec ce script : la sauvegarde part en AJAX. En cas de succès, on
// utilise location.replace() plutôt qu'une navigation classique — ça
// REMPLACE l'entrée d'historique du formulaire au lieu d'en ajouter une
// nouvelle, donc le bouton "retour" depuis la liste ne retombe plus sur ce
// formulaire.
document.addEventListener("DOMContentLoaded", function () {
  const form = document.querySelector("form.admin-content-form");
  if (!form) return;

  const loader = document.getElementById("admin-page-loader");
  const submitBtn = form.querySelector('.admin-form-actions button[type="submit"]');
  if (!submitBtn) return;

  const originalLabel = submitBtn.textContent;

  function showError(message) {
    let box = form.querySelector(".admin-form-error");
    if (!box) {
      box = document.createElement("div");
      box.className = "admin-flash admin-flash-error admin-form-error";
      form.insertBefore(box, form.firstChild);
    }
    box.textContent = message;
    box.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();

    submitBtn.disabled = true;
    submitBtn.textContent = "Enregistrement…";
    if (loader) loader.hidden = false;

    const fd = new FormData(form);

    fetch(form.action || window.location.href, {
      method: "POST",
      headers: { "X-Requested-With": "XMLHttpRequest" },
      body: fd,
    })
      .then(function (res) { return res.json(); })
      .then(function (data) {
        if (data.ok) {
          // history.back() plutôt que location.replace(data.redirect) :
          // l'entrée "liste" existe déjà dans l'historique (celle d'où on
          // a cliqué "Modifier"/"+Ajouter") — la remplacer par une nouvelle
          // créait deux entrées "liste" adjacentes, d'où le double-clic
          // nécessaire sur "retour". Le filet anti-cache est dans admin.js
          // (évènement pageshow) au cas où le retour arrière montre une
          // version en cache de la liste sans le contenu tout juste enregistré.
          history.back();
        } else {
          if (loader) loader.hidden = true;
          submitBtn.disabled = false;
          submitBtn.textContent = originalLabel;
          showError(data.error || "Une erreur est survenue.");
        }
      })
      .catch(function () {
        if (loader) loader.hidden = true;
        submitBtn.disabled = false;
        submitBtn.textContent = originalLabel;
        showError("Connexion interrompue, réessaie.");
      });
  });
});
