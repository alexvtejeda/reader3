# Dark/Light Mode Toggle + CSS Extraction — Design

**Date:** 2026-06-01
**Status:** Approved
**Component:** reader3 web app (`server.py`, `templates/`)

## Goal

Two related improvements to the reader's frontend:

1. **Move inline CSS out of the templates** into dedicated static files for readability and maintainability.
2. **Add a dark/light mode toggle** on both the library and reader pages, with the choice persisted across visits.

Both pages share a single theme; toggling on one page is remembered on the other.

## Background

Currently both templates carry their own inline `<style>` block:

- `templates/library.html` — book-grid / card layout, light gray theme.
- `templates/reader.html` — sidebar + serif reading content + chapter navigation.

Colors are hardcoded hex values scattered through both blocks (`#fff`, `#f8f9fa`, `#212529`, `#3498db`, etc.). There is no `static/` directory and FastAPI does not currently serve static files.

## Decisions

- **Scope:** Toggle appears on **both** pages (library + reader).
- **First-visit behavior:** Follow the OS setting via `prefers-color-scheme`. Once the user toggles, that explicit choice is saved in `localStorage` and takes precedence on every later visit.
- **CSS organization:** Shared base file holding the theme variables, plus one layout file per page.
- **Mechanism:** CSS custom properties (variables) flipped by a `data-theme` attribute on `<html>` (chosen approach A below).

## Approach (chosen: A — CSS variables + `data-theme`)

Define every color once as a CSS variable in `base.css`. Light values live on `:root`; dark overrides live under `[data-theme="dark"]`. Layout CSS references only the variables, so flipping one attribute re-themes the whole page. A tiny inline script sets `data-theme` before first paint to avoid a flash of the wrong theme.

Rejected alternatives:
- **B. Two stylesheets swapped by JS** — more files, duplicated layout rules, visible flash on swap.
- **C. `prefers-color-scheme` only** — no manual override, which the user explicitly wants.

## Architecture

### 1. Static file serving

Add a `static/` directory and mount it in `server.py`:

```python
from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="static"), name="static")
```

Layout:

```
static/
  css/
    base.css      # theme variables (light + dark), shared resets, toggle button styling
    library.css   # book-grid / card layout
    reader.css    # sidebar / content / chapter-nav layout
  js/
    theme.js      # toggle click handler + persistence
```

### 2. Theme variables (`base.css`)

All hardcoded hex values from both templates become CSS variables. Indicative set (final names settled during implementation):

- `--bg`, `--text`, `--muted`
- `--sidebar-bg`, `--border`
- `--accent`, `--accent-contrast`
- `--card-bg`, `--card-shadow`
- `--toc-link`, `--toc-active`

Light values on `:root`; dark overrides under `[data-theme="dark"]`. Layout files reference only variables.

### 3. No-flash init (inline in each template `<head>`)

One small inline script runs before paint. This is the single piece of JS that must stay inline — an external file would load too late and flash the wrong theme.

```html
<script>
  (function () {
    const saved = localStorage.getItem('theme');
    const theme = saved || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    document.documentElement.setAttribute('data-theme', theme);
  })();
</script>
```

### 4. Toggle button + handler

A small glyph button (sun ☀ / moon ☾) appears in the reader's sidebar and in the library header. `static/js/theme.js` flips the `data-theme` attribute, updates the glyph, and writes the new value to `localStorage`. Loaded with `<script src="/static/js/theme.js" defer></script>`.

### 5. Templates after extraction

Each template's `<style>` block is removed and replaced with:

```html
<link rel="stylesheet" href="/static/css/base.css">
<link rel="stylesheet" href="/static/css/library.css">   <!-- or reader.css -->
```

The reader keeps its existing TOC `findAndGo` script inline, because it depends on the Jinja-injected `spineMap`. No other inline JS remains besides the no-flash init.

## Data Flow

1. Browser requests a page → server renders template with `<link>`s to static CSS and the inline no-flash script.
2. No-flash script sets `data-theme` on `<html>` from `localStorage` (or OS preference) before paint.
3. CSS variables resolve to the chosen palette; page renders correctly with no flash.
4. User clicks the toggle → `theme.js` flips `data-theme`, swaps the glyph, saves to `localStorage`.
5. Next page load (either page) reads the saved value and matches.

## Error / Edge Cases

- **`localStorage` unavailable** (private mode / disabled): wrap reads/writes so a failure falls back to OS preference; the toggle still works for the current page session.
- **No saved value:** OS preference decides; absence of `prefers-color-scheme` support resolves to light.
- **Static file 404:** caught early by the import/smoke check and a manual page load during verification.

## Out of Scope

- No changes to EPUB processing, pickling, routing, or the `Book` data model.
- No per-book or per-chapter theme overrides.
- No build step or CSS framework — plain CSS files served statically.

## Verification

- `uv run python -c "import server, reader3"` (catches mount/import errors).
- Start the server; load the library and a chapter.
- Toggle the theme on each page; reload to confirm persistence and that both pages agree.
- Confirm no flash of the wrong theme on load.
- Run the `verify-reader` skill.
- `uv run ruff format . && uv run ruff check --fix .` for the `server.py` change.
