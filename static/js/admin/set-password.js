// Supabase renvoie le jeton de session dans le FRAGMENT de l'URL
// (après le #) pour les flux invite/confirm/magic-link — un fragment
// n'est jamais envoyé au serveur dans une requête HTTP, donc ce jeton
// n'existe que côté navigateur. D'où ce script plutôt qu'un traitement
// côté Flask.
//
// Pas de SDK JS Supabase chargé exprès (le reste du projet n'en utilise
// nulle part) : un simple appel à l'API REST de Supabase suffit pour
// mettre à jour le mot de passe.
document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("set-password-form");
  const feedback = document.getElementById("set-password-feedback");
  if (!form) return;

  const params = new URLSearchParams(window.location.hash.replace(/^#/, ""));
  const accessToken = params.get("access_token");

  function showFeedback(message, isError) {
    feedback.innerHTML = "";
    const box = document.createElement("div");
    box.className = "admin-flash " + (isError ? "admin-flash-error" : "admin-flash-success");
    box.textContent = message;
    feedback.appendChild(box);
    feedback.hidden = false;
  }

  if (!accessToken) {
    showFeedback("Lien invalide ou expiré — redemande une invitation.", true);
    form.querySelector("button").disabled = true;
    return;
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    const pw1 = document.getElementById("new-password").value;
    const pw2 = document.getElementById("confirm-password").value;

    if (pw1.length < 8) {
      showFeedback("8 caractères minimum.", true);
      return;
    }
    if (pw1 !== pw2) {
      showFeedback("Les deux mots de passe ne correspondent pas.", true);
      return;
    }

    const btn = form.querySelector("button");
    btn.disabled = true;
    btn.textContent = "Enregistrement…";

    fetch(window.SUPABASE_URL + "/auth/v1/user", {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        "apikey": window.SUPABASE_ANON_KEY,
        "Authorization": "Bearer " + accessToken,
      },
      body: JSON.stringify({ password: pw1 }),
    })
      .then(function (res) {
        if (!res.ok) throw new Error("Échec de la mise à jour.");
        return res.json();
      })
      .then(function () {
        showFeedback("Mot de passe défini — redirection…", false);
        setTimeout(function () {
          window.location.href = "/admin/login";
        }, 1500);
      })
      .catch(function () {
        showFeedback("Une erreur est survenue, réessaie.", true);
        btn.disabled = false;
        btn.textContent = "Valider";
      });
  });
});
