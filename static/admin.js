(() => {
  const btn = document.getElementById("menuBtn");
  const sidebar = document.querySelector(".sidebar");
  if (!btn || !sidebar) return;

  btn.addEventListener("click", () => sidebar.classList.toggle("open"));
})();
