# Responsive Reader with Collapsible Sidebar — Design

**Status:** Approved
**Date:** 2026-06-01
**Scope:** The reader view only (`templates/reader.html`, `static/css/reader.css`, new `static/js/sidebar.js`). No Python, server, or MCP changes. The library page is out of scope.

## Goal

Make the reader usable on a phone (now reachable over Tailscale) without giving up the desktop experience. Two parts:

1. A collapsible sidebar, toggled by a hamburger button, available on **all** screen sizes (focused reading on desktop, space recovery on mobile).
2. Responsive chapter text that adapts padding, size, alignment, and the nav footer on small screens.

No frameworks, no build step — match the project's existing vanilla HTML/CSS/JS and Unicode-glyph-style conventions. The one deliberate exception is inline SVG for the icon (see Icon below).

## Toggle Mechanism

### State: a single body class

The sidebar's open/closed state is a single class on `<body>`: **`sidebar-closed`**.

- Class **present** → sidebar closed.
- Class **absent** → sidebar open.

One class with one meaning across both breakpoints. CSS media queries decide how "closed" and "open" *look* at each width; the class itself never changes meaning.

### One button, two icons

A single toggle button is pinned to the top-left of the viewport (`position: fixed`, top: 12px, left: 12px, highest `z-index` so it stays clickable above the mobile sidebar overlay). It is always visible.

The button contains **two inline lucide SVGs**:

- `menu` (three horizontal lines) — shown when the sidebar is closed.
- `x` — shown when the sidebar is open.

CSS swaps which SVG is visible based on `body.sidebar-closed`; JavaScript does **not** touch the icons. This keeps the JS to pure state toggling.

`.sidebar-top` receives ~44px of left padding so the existing "← Back to Library" link is never hidden under the fixed button when the sidebar is open.

#### Icon markup (lucide `menu` and `x`)

```html
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
```

`stroke="currentColor"` lets the icon inherit the theme's text color in both light and dark modes.

> Note: inline SVG is contrary to the user's global "Font Awesome only / no inline SVG" rule. It was explicitly chosen for this framework-free project, which uses no icon library at all (the theme toggle is a Unicode glyph). Documented here so the deviation is intentional and traceable.

### JavaScript: `static/js/sidebar.js` (new)

A small file mirroring the existing `static/js/theme.js` split. Responsibilities, and nothing more:

1. On click of the toggle button, flip `sidebar-closed` on `<body>`.
2. On click of the backdrop (mobile overlay), add `sidebar-closed` (close).
3. Bind once the DOM is ready, guarding an already-parsed DOM (same pattern as `theme.js`).

It does **not** manage icons (CSS does) and does **not** set the initial state (the no-flash script does).

### No-flash initial state

A tiny inline `<script>` in the reader `<head>` — the same approach as `_theme_init.html` — sets the initial state before paint:

```html
<script>
  if (window.innerWidth < 768) document.body.classList.add("sidebar-closed");
</script>
```

So phones start with the sidebar collapsed and desktops start with it open, with no visible flash of the wrong layout. (If placed in `<head>`, guard for `document.body` existence or place at the top of `<body>`; final placement chosen during implementation to guarantee `document.body` is available.)

## Two Presentations, One Breakpoint (768px)

### Desktop (> 768px)

- Sidebar remains the in-flow `300px` flex child it is today.
- `body.sidebar-closed #sidebar { display: none; }` — when closed, the sidebar is removed from flow and `#main`'s centered `max-width: 700px` content simply re-centers in the freed width.

### Mobile (≤ 768px)

- Sidebar becomes `position: fixed` (full height, left edge), sliding in/out via `transform: translateX(0)` (open) / `translateX(-100%)` (closed), with a CSS transition.
- A backdrop element `#sidebar-backdrop` (semi-transparent, fixed, covering the viewport) appears only when the sidebar is open on mobile. Tapping it closes the sidebar. The backdrop is not displayed on desktop.
- The toggle button's `z-index` is above the sidebar so the `x` remains tappable to close.

## Responsive Text (≤ 768px media query)

All four adjustments apply inside the mobile media query:

| Property | Desktop (current) | Mobile |
|---|---|---|
| `.content-container` padding | `60px 40px` | `24px 18px` |
| `.content-container` font-size | `1.15em` | `clamp(1rem, 0.9rem + 0.6vw, 1.15em)` |
| `.book-content p` text-align | `justify` | `left` |
| `.chapter-nav` layout | `flex` space-between | add `flex-wrap: wrap` + `gap` |

The `clamp()` can be applied at all widths (it caps at `1.15em`), but is specified here as part of the mobile-readability changes; implementation may hoist it to the base rule if cleaner, as long as desktop rendering is unchanged.

## Files Touched

- `templates/reader.html` — add the toggle button (with both SVGs), the `#sidebar-backdrop` element, the inline no-flash init script, and a `<script src="/static/js/sidebar.js">` tag.
- `static/css/reader.css` — toggle button + icon-swap rules, backdrop, mobile sidebar overlay/transform, `.sidebar-top` left padding, and the responsive-text media query.
- `static/js/sidebar.js` — **new**, toggle + backdrop handlers.

## Out of Scope

- The library page (`library.html` / `library.css`).
- Any Python, `server.py`, or MCP changes — the responsive work is entirely client-side.
- Persisting the open/closed choice across page loads (each chapter is a full navigation; the no-flash script re-derives state from width each load). Can be added later if desired.

## Verification

No automated tests in this repo. Verify manually:

1. `uv run python -c "import server, reader3"` still imports cleanly (sanity; no Python changed).
2. Load a chapter on a desktop-width browser: sidebar open by default, hamburger collapses/expands it, content re-centers when collapsed.
3. Narrow the window below 768px (or load on the phone over Tailscale): sidebar starts collapsed, hamburger slides it in over a backdrop, tapping the backdrop or the `x` closes it.
4. Confirm text padding tightens, font scales, paragraphs left-align, and the Prev/Section/Next footer wraps without overflow.
5. Toggle dark mode with the sidebar both open and closed — the SVG icon follows the text color in both themes.
