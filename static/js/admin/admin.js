document.addEventListener("DOMContentLoaded", function () {
  // Menu latéral sur mobile
  const burger = document.getElementById("admin-burger");
  const sidebar = document.querySelector(".admin-sidebar");
  if (burger && sidebar) {
    burger.addEventListener("click", function () {
      sidebar.classList.toggle("open");
    });
  }

  // Confirmation avant toute action destructive (data-confirm="message")
  document.querySelectorAll("form[data-confirm]").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      if (!window.confirm(form.dataset.confirm)) {
        e.preventDefault();
      }
    });
  });
});
