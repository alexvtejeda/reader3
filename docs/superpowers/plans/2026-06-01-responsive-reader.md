# Responsive Reader with Collapsible Sidebar — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the reader usable on a phone — a hamburger-toggled collapsible sidebar on all screen sizes, plus chapter text that adapts on small screens.

**Architecture:** A single `sidebar-closed` class on `<body>` drives state. One fixed top-left toggle button holds two inline lucide SVGs (`menu`/`x`); CSS swaps the icon, JS only flips the class. CSS media queries (768px breakpoint) render the sidebar as an in-flow column on desktop and a sliding overlay on mobile. A separate media query handles responsive text.

**Tech Stack:** Jinja2 template, vanilla CSS (with theme CSS variables already in `base.css`), vanilla JS (mirrors `static/js/theme.js`). No frameworks, no build step.

**Note on testing:** This repo has no automated test suite (see `CLAUDE.md`). Verification is the import sanity check (`uv run python -c "import server, reader3"`) plus manual browser checks. The user runs the dev server themselves (`uv run server.py`); do **not** start it — ask the user to load `http://127.0.0.1:8123/` when a visual check is needed.

**Spec:** `docs/superpowers/specs/2026-06-01-responsive-reader-design.md`

---

## File Structure

- `static/js/sidebar.js` — **new.** Toggle + backdrop click handlers. State only; no icon logic.
- `templates/reader.html` — **modify.** Add the no-flash init script, the toggle button (two SVGs), the backdrop element, and the `<script>` tag for `sidebar.js`.
- `static/css/reader.css` — **modify.** Toggle button + icon-swap rules, desktop collapse, mobile overlay + backdrop, responsive-text media query.

No Python, `server.py`, or MCP files are touched.

---

## Task 1: Collapsible sidebar (desktop) + toggle mechanism

After this task: on a desktop-width browser the hamburger collapses/expands the sidebar and the content re-centers. The no-flash script collapses the sidebar on narrow widths (the polished mobile overlay comes in Task 2).

**Files:**
- Create: `static/js/sidebar.js`
- Modify: `templates/reader.html`
- Modify: `static/css/reader.css`

- [ ] **Step 1: Create the toggle JS**

Create `static/js/sidebar.js`:

```js
// Toggles the sidebar by flipping `sidebar-closed` on <body>. Icon state is
// handled entirely by CSS; this file only manages the class and the mobile
// backdrop. The initial open/closed state is set by an inline no-flash script
// in reader.html (mirrors the theme.js / _theme_init.html split).
(function () {
  function toggle() {
    document.body.classList.toggle("sidebar-closed");
  }

  function close() {
    document.body.classList.add("sidebar-closed");
  }

  function init() {
    var btn = document.getElementById("sidebar-toggle");
    var backdrop = document.getElementById("sidebar-backdrop");
    if (btn) btn.addEventListener("click", toggle);
    if (backdrop) backdrop.addEventListener("click", close);
  }

  // Bind once the DOM is ready; guard an already-parsed DOM so it still wires
  // up if ever loaded without `defer`. Same pattern as theme.js.
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
```

- [ ] **Step 2: Add markup to reader.html**

In `templates/reader.html`, the body currently opens like this (lines 11-14):

```html
<body>

    <!-- SIDEBAR -->
    <div id="sidebar">
```

Replace that opening with the no-flash script, the toggle button (two lucide SVGs), and the backdrop, inserted before the sidebar:

```html
<body>

    <script>
      // Start collapsed on narrow screens; no flash of the wrong layout.
      // document.body exists here because this is the first child of <body>.
      if (window.innerWidth < 768) document.body.classList.add("sidebar-closed");
    </script>

    <!-- SIDEBAR TOGGLE (fixed, top-left, always visible) -->
    <button id="sidebar-toggle" type="button" aria-label="Toggle sidebar">
      <svg class="icon-menu" viewBox="0 0 24 24" fill="none" stroke="currentColor"
           stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <line x1="3" y1="6"  x2="21" y2="6"/>
        <line x1="3" y1="12" x2="21" y2="12"/>
        <line x1="3" y1="18" x2="21" y2="18"/>
      </svg>
      <svg class="icon-close" viewBox="0 0 24 24" fill="none" stroke="currentColor"
           stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <line x1="18" y1="6" x2="6" y2="18"/>
        <line x1="6"  y1="6" x2="18" y2="18"/>
      </svg>
    </button>

    <!-- BACKDROP (shown only behind the mobile sidebar overlay) -->
    <div id="sidebar-backdrop"></div>

    <!-- SIDEBAR -->
    <div id="sidebar">
```

- [ ] **Step 3: Add the sidebar.js script tag**

In `templates/reader.html`, the file currently ends (lines 126-128):

```html
    <script src="/static/js/theme.js"></script>
</body>
</html>
```

Add the sidebar script alongside theme.js:

```html
    <script src="/static/js/theme.js"></script>
    <script src="/static/js/sidebar.js"></script>
</body>
</html>
```

- [ ] **Step 4: Add toggle-button + desktop-collapse CSS**

Append to `static/css/reader.css`:

```css
/* Sidebar toggle button (fixed, top-left, above the sidebar so it stays
   clickable when the mobile overlay is open). Mirrors .theme-toggle styling. */
#sidebar-toggle {
  position: fixed;
  top: 12px;
  left: 12px;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  padding: 0;
  background: var(--sidebar-bg);
  border: 1px solid var(--border);
  border-radius: 4px;
  color: var(--text);
  cursor: pointer;
  transition: color 0.2s, border-color 0.2s;
}
#sidebar-toggle:hover {
  border-color: var(--accent);
  color: var(--accent);
}
#sidebar-toggle svg {
  width: 22px;
  height: 22px;
}

/* Icon swap: x while open, menu while closed. */
#sidebar-toggle .icon-menu {
  display: none;
}
#sidebar-toggle .icon-close {
  display: block;
}
body.sidebar-closed #sidebar-toggle .icon-menu {
  display: block;
}
body.sidebar-closed #sidebar-toggle .icon-close {
  display: none;
}

/* Keep the "Back to Library" link clear of the fixed toggle button. */
.sidebar-top {
  padding-left: 44px;
}

/* Backdrop is desktop-hidden by default; the mobile media query enables it. */
#sidebar-backdrop {
  display: none;
}

/* Desktop collapse: drop the sidebar from flow so content re-centers. */
body.sidebar-closed #sidebar {
  display: none;
}
```

- [ ] **Step 5: Sanity-check imports (no Python changed, but confirm nothing broke)**

Run: `uv run python -c "import server, reader3"`
Expected: no output, exit 0.

- [ ] **Step 6: Lint/format the touched files**

Run: `uv run ruff format . && uv run ruff check --fix .`
Expected: no errors. (Ruff covers Python only; it will not touch the JS/CSS/HTML, but run it per repo convention to confirm the import line edits are clean.)

- [ ] **Step 7: Manual browser check (ask the user)**

Ask the user to load `http://127.0.0.1:8123/`, open a chapter in a desktop-width window, and confirm:
- The sidebar is open by default; an `x` icon shows top-left.
- Clicking the button collapses the sidebar; the icon becomes a hamburger and the chapter content re-centers.
- Clicking again re-opens it.
- The "← Back to Library" link is not hidden under the button.

- [ ] **Step 8: Commit**

```bash
git add static/js/sidebar.js templates/reader.html static/css/reader.css
git commit -m "Add collapsible sidebar toggle to the reader"
```

---

## Task 2: Mobile sidebar overlay + backdrop

After this task: on screens ≤768px the sidebar slides in over the content with a tap-to-close backdrop instead of taking layout space.

**Files:**
- Modify: `static/css/reader.css`

- [ ] **Step 1: Add the mobile overlay media query**

Append to `static/css/reader.css`:

```css
/* Mobile: sidebar becomes a sliding overlay instead of an in-flow column. */
@media (max-width: 768px) {
  #sidebar {
    position: fixed;
    top: 0;
    left: 0;
    height: 100vh;
    z-index: 90;
    transform: translateX(0);
    transition: transform 0.25s ease;
    box-shadow: 2px 0 8px var(--card-shadow);
  }
  /* Override the desktop display:none so the slide-out stays animatable. */
  body.sidebar-closed #sidebar {
    display: block;
    transform: translateX(-100%);
  }

  /* Backdrop shows only while the sidebar is open. */
  #sidebar-backdrop {
    display: block;
    position: fixed;
    inset: 0;
    z-index: 80;
    background: rgba(0, 0, 0, 0.5);
  }
  body.sidebar-closed #sidebar-backdrop {
    display: none;
  }
}
```

(The `body.sidebar-closed #sidebar` rule here has the same specificity as the desktop one in Task 1 but appears later and inside a matching media query, so it wins on mobile. The toggle button's `z-index: 100` keeps it above the sidebar's `90`, so the `x` stays tappable.)

- [ ] **Step 2: Lint/format**

Run: `uv run ruff format . && uv run ruff check --fix .`
Expected: no errors.

- [ ] **Step 3: Manual browser check (ask the user)**

Ask the user to narrow the window below 768px (or load on the phone over Tailscale) and confirm:
- The sidebar starts collapsed; only the chapter and the hamburger show.
- Tapping the hamburger slides the sidebar in over a dark backdrop.
- Tapping the backdrop closes it; tapping the `x` also closes it.
- The sidebar does not push the content sideways (it floats over it).

- [ ] **Step 4: Commit**

```bash
git add static/css/reader.css
git commit -m "Make reader sidebar a sliding overlay on mobile"
```

---

## Task 3: Responsive chapter text

After this task: on screens ≤768px the chapter text uses tighter padding, a fluid font size, left alignment, and a wrapping nav footer.

**Files:**
- Modify: `static/css/reader.css`

- [ ] **Step 1: Add the responsive-text media query**

Append to `static/css/reader.css`:

```css
/* Mobile: tighten the reading column and let the nav footer wrap. */
@media (max-width: 768px) {
  .content-container {
    padding: 24px 18px;
    font-size: clamp(1rem, 0.9rem + 0.6vw, 1.15em);
  }
  .book-content p {
    text-align: left; /* justified text makes ugly rivers in a narrow column */
  }
  .chapter-nav {
    flex-wrap: wrap;
    gap: 12px;
    justify-content: center;
  }
}
```

- [ ] **Step 2: Lint/format**

Run: `uv run ruff format . && uv run ruff check --fix .`
Expected: no errors.

- [ ] **Step 3: Manual browser check (ask the user)**

Ask the user to view a chapter below 768px and confirm:
- Padding is tighter (text reaches closer to the screen edges).
- Font size is slightly smaller and scales with width.
- Paragraphs are left-aligned (not justified).
- The "← Previous / Section N of M / Next →" footer wraps neatly and centers instead of overflowing.

- [ ] **Step 4: Final dark/light check across states (ask the user)**

Ask the user to toggle dark mode with the sidebar both open and closed, on desktop and mobile widths, and confirm the SVG icon and the toggle button follow the theme colors in both modes.

- [ ] **Step 5: Commit**

```bash
git add static/css/reader.css
git commit -m "Make reader chapter text responsive on small screens"
```

---

## Self-Review

**Spec coverage:**
- Toggle mechanism / single `sidebar-closed` class → Task 1 (JS, markup, desktop CSS). ✓
- One button, two inline lucide SVGs, CSS icon swap → Task 1 Step 2 + Step 4. ✓
- `.sidebar-top` left padding to clear the button → Task 1 Step 4. ✓
- No-flash init script → Task 1 Step 2. ✓
- `sidebar.js` mirroring `theme.js`, state + backdrop only → Task 1 Step 1. ✓
- Desktop collapse via `display: none` → Task 1 Step 4. ✓
- Mobile overlay (fixed + translateX), backdrop, z-index ordering → Task 2. ✓
- Responsive text: padding, `clamp()` font, left-align, wrapping nav → Task 3. ✓
- Out of scope (library page, Python/server/MCP, persistence) → respected; no tasks touch them. ✓

**Placeholder scan:** No TBD/TODO; every code step shows complete content. ✓

**Consistency:** Class name `sidebar-closed`, ids `sidebar-toggle` / `sidebar-backdrop`, and SVG classes `icon-menu` / `icon-close` are used identically across the markup, JS, and CSS. The 768px breakpoint matches across all three media queries. ✓
