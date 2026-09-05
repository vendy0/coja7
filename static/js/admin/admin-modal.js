// Modale de confirmation stylée, à la place du confirm() natif du
// navigateur. Expose window.adminConfirm(message) -> Promise<boolean>,
// utilisé par admin.js pour toute action destructive (data-confirm=...).
document.addEventListener("DOMContentLoaded", function () {
  const backdrop = document.getElementById("admin-modal-backdrop");
  const text = document.getElementById("admin-modal-text");
  const btnConfirm = document.getElementById("admin-modal-confirm");
  const btnCancel = document.getElementById("admin-modal-cancel");
  if (!backdrop || !text || !btnConfirm || !btnCancel) return;

  let resolvePromise = null;

  function close(result) {
    backdrop.classList.remove("visible");
    if (resolvePromise) {
      resolvePromise(result);
      resolvePromise = null;
    }
  }

  btnConfirm.addEventListener("click", function () { close(true); });
  btnCancel.addEventListener("click", function () { close(false); });
  backdrop.addEventListener("click", function (e) {
    if (e.target === backdrop) close(false);
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && backdrop.classList.contains("visible")) close(false);
  });

  window.adminConfirm = function (message) {
    text.textContent = message;
    backdrop.classList.add("visible");
    return new Promise(function (resolve) {
      resolvePromise = resolve;
    });
  };
});
