function openSupportModal() {
  document.getElementById("support_opened_at").value = Date.now() / 1000;
  document.getElementById("supportModal").classList.add("active");
}
function closeSupportModal() {
  document.getElementById("supportModal").classList.remove("active");
}

document.addEventListener("DOMContentLoaded", function () {
  const textarea = document.getElementById("support_message");
  const counter = document.getElementById("char-counter");
  const form = document.getElementById("supportForm");
  const feedback = document.getElementById("support-feedback");
  const modal = document.getElementById("supportModal");
  if (!textarea || !form) return;

  textarea.addEventListener("input", function () {
    const len = textarea.value.length;
    counter.textContent = len + " / 600";
    counter.classList.toggle("limit-reached", len >= 600);
  });

  // Ferme en cliquant en dehors du contenu (pas dessus)
  modal.addEventListener("click", function (e) {
    if (e.target === modal) closeSupportModal();
  });

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    const message = textarea.value.trim();
    if (!message) return;

    const sendBtn = form.querySelector(".btn-send");
    sendBtn.disabled = true;
    sendBtn.textContent = "Envoi…";

    fetch(form.dataset.action, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: "message=" + encodeURIComponent(message),
    })
      .then(function (res) {
        return res.json().then(function (data) {
          return { ok: res.ok, data: data };
        });
      })
      .then(function (result) {
        if (result.ok && result.data.ok) {
          feedback.textContent = "Message envoyé, merci !";
          feedback.className = "support-feedback success";
          feedback.hidden = false;
          textarea.value = "";
          counter.textContent = "0 / 600";
          setTimeout(function () {
            feedback.hidden = true;
            closeSupportModal();
          }, 5000);
        } else {
          feedback.textContent = (result.data && result.data.error) || "Erreur d'envoi, réessaie.";
          feedback.className = "support-feedback error";
          feedback.hidden = false;
        }
      })
      .catch(function () {
        feedback.textContent = "Connexion interrompue, réessaie.";
        feedback.className = "support-feedback error";
        feedback.hidden = false;
      })
      .finally(function () {
        sendBtn.disabled = false;
        sendBtn.textContent = "Envoyer";
      });
  });
});
