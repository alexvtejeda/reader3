// Flips the data-theme attribute, persists the choice, and keeps every
// .theme-toggle button's glyph in sync. The initial theme is set by the
// inline no-flash script in each template's <head>.
(function () {
  function currentTheme() {
    return document.documentElement.getAttribute("data-theme") || "light";
  }

  function glyphFor(theme) {
    // Show the action the click performs: moon while light, sun while dark.
    return theme === "dark" ? "☀" : "☾";
  }

  function updateButtons() {
    var theme = currentTheme();
    var label =
      theme === "dark" ? "Switch to light mode" : "Switch to dark mode";
    document.querySelectorAll(".theme-toggle").forEach(function (btn) {
      btn.textContent = glyphFor(theme);
      btn.setAttribute("aria-label", label);
      btn.setAttribute("title", label);
    });
  }

  function toggle() {
    var next = currentTheme() === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    try {
      localStorage.setItem("theme", next);
    } catch (e) {
      /* localStorage unavailable (private mode); choice lasts this page only. */
    }
    updateButtons();
  }

  function init() {
    document.querySelectorAll(".theme-toggle").forEach(function (btn) {
      btn.addEventListener("click", toggle);
    });
    updateButtons();
  }

  // Bind once the DOM is ready. Guard against an already-parsed DOM so the
  // buttons still wire up if this script is ever loaded without `defer`.
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
