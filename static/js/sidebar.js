// Toggles the sidebar by flipping `sidebar-closed` on <body>. Icon state is
// handled entirely by CSS; this file only manages the class and the mobile
// backdrop. The initial open/closed state is set by an inline no-flash script
// in reader.html (mirrors the theme.js / _theme_init.html split).
(function () {
  function toggle() {
    document.body.classList.toggle("sidebar-closed");
  }

  function closeSidebar() {
    document.body.classList.add("sidebar-closed");
  }

  function init() {
    var btn = document.getElementById("sidebar-toggle");
    var backdrop = document.getElementById("sidebar-backdrop");
    if (btn) btn.addEventListener("click", toggle);
    if (backdrop) backdrop.addEventListener("click", closeSidebar);
  }

  // Bind once the DOM is ready; guard an already-parsed DOM so it still wires
  // up if ever loaded without `defer`. Same pattern as theme.js.
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
