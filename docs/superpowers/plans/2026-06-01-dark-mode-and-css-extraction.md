# Dark/Light Mode Toggle + CSS Extraction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract the inline CSS from both templates into static files and add a persistent dark/light mode toggle on the library and reader pages.

**Architecture:** FastAPI mounts a new `static/` directory. All colors become CSS custom properties defined once in `base.css` (light on `:root`, dark under `[data-theme="dark"]`). A tiny inline script in each template sets `data-theme` before paint to avoid a flash; a glyph button + `theme.js` flips the attribute and persists the choice in `localStorage`. First visit follows `prefers-color-scheme`.

**Tech Stack:** FastAPI (Starlette `StaticFiles`), Jinja2 templates, plain CSS + vanilla JS. Package manager: `uv`. No test framework — verification is an import smoke-check plus `curl`/visual checks against a running server.

---

## File Structure

**Create:**
- `static/css/base.css` — theme variables (light + dark), body/reset rules, `.theme-toggle` button styling
- `static/css/library.css` — library page layout (header, book-grid, cards, button)
- `static/css/reader.css` — reader page layout (sidebar, TOC, content, chapter-nav)
- `static/js/theme.js` — toggle click handler + persistence + glyph update

**Modify:**
- `server.py` — mount `StaticFiles` at `/static`
- `templates/library.html` — remove `<style>`, link CSS, add no-flash script + toggle button
- `templates/reader.html` — remove `<style>`, link CSS, add no-flash script + toggle button (keep existing `findAndGo` TOC script inline)

**Variable reference** (used by every task that writes CSS — names are fixed here so later tasks stay consistent):

| Variable | Light | Dark | Used by |
|---|---|---|---|
| `--page-bg` | `#f4f4f9` | `#121212` | library body |
| `--content-bg` | `#ffffff` | `#1a1a1a` | reader body/main |
| `--text` | `#212529` | `#e0e0e0` | body text |
| `--heading` | `#333333` | `#f0f0f0` | h1/h2/h3 |
| `--muted` | `#666666` | `#aaaaaa` | book-meta |
| `--muted-soft` | `#999999` | `#888888` | "Section X of Y" |
| `--sidebar-bg` | `#f8f9fa` | `#1e1e1e` | reader sidebar |
| `--border` | `#e9ecef` | `#333333` | sidebar border |
| `--border-strong` | `#dddddd` | `#444444` | library h1 underline |
| `--border-mid` | `#dee2e6` | `#333333` | nav-header underline |
| `--border-soft` | `#eeeeee` | `#2a2a2a` | chapter-nav top |
| `--accent` | `#3498db` | `#5dade2` | links/buttons |
| `--accent-hover` | `#2980b9` | `#85c1e9` | button hover |
| `--on-accent` | `#ffffff` | `#0d0d0d` | text on accent fill |
| `--toc-link` | `#495057` | `#c0c0c0` | TOC links |
| `--toc-link-hover` | `#000000` | `#ffffff` | TOC hover |
| `--toc-active` | `#d63384` | `#f06595` | active TOC link |
| `--card-bg` | `#ffffff` | `#1e1e1e` | book cards |
| `--card-shadow` | `rgba(0,0,0,0.1)` | `rgba(0,0,0,0.5)` | card shadow |
| `--book-title` | `#2c3e50` | `#d0d8e0` | card title |
| `--disabled` | `#cccccc` | `#555555` | disabled nav-btn |

---

## Task 1: Mount static files in the server

**Files:**
- Modify: `server.py:1-15`
- Create: `static/.gitkeep` (temporary, so the mount target exists before CSS is written)

- [ ] **Step 1: Create the static directory tree**

```bash
mkdir -p static/css static/js
touch static/.gitkeep
```

- [ ] **Step 2: Add the StaticFiles import**

In `server.py`, add to the existing FastAPI import group (after line 7, the `Jinja2Templates` import):

```python
from fastapi.staticfiles import StaticFiles
```

- [ ] **Step 3: Mount the static directory**

In `server.py`, immediately after the `templates = Jinja2Templates(directory="templates")` line (currently line 15), add:

```python
app.mount("/static", StaticFiles(directory="static"), name="static")
```

- [ ] **Step 4: Verify the app still imports**

Run: `uv run python -c "import server, reader3; print('ok')"`
Expected: prints `ok` with no traceback. (Confirms the mount path `static/` exists and the import resolves.)

- [ ] **Step 5: Commit**

```bash
git add server.py static/.gitkeep
git commit -m "Mount static files directory in server"
```

---

## Task 2: Write base.css (theme variables + toggle button)

**Files:**
- Create: `static/css/base.css`

- [ ] **Step 1: Write the full base stylesheet**

Create `static/css/base.css` with exactly this content:

```css
/* Theme variables: light on :root, dark override under [data-theme="dark"]. */
:root {
  --page-bg: #f4f4f9;
  --content-bg: #ffffff;
  --text: #212529;
  --heading: #333333;
  --muted: #666666;
  --muted-soft: #999999;
  --sidebar-bg: #f8f9fa;
  --border: #e9ecef;
  --border-strong: #dddddd;
  --border-mid: #dee2e6;
  --border-soft: #eeeeee;
  --accent: #3498db;
  --accent-hover: #2980b9;
  --on-accent: #ffffff;
  --toc-link: #495057;
  --toc-link-hover: #000000;
  --toc-active: #d63384;
  --card-bg: #ffffff;
  --card-shadow: rgba(0, 0, 0, 0.1);
  --book-title: #2c3e50;
  --disabled: #cccccc;
}

[data-theme="dark"] {
  --page-bg: #121212;
  --content-bg: #1a1a1a;
  --text: #e0e0e0;
  --heading: #f0f0f0;
  --muted: #aaaaaa;
  --muted-soft: #888888;
  --sidebar-bg: #1e1e1e;
  --border: #333333;
  --border-strong: #444444;
  --border-mid: #333333;
  --border-soft: #2a2a2a;
  --accent: #5dade2;
  --accent-hover: #85c1e9;
  --on-accent: #0d0d0d;
  --toc-link: #c0c0c0;
  --toc-link-hover: #ffffff;
  --toc-active: #f06595;
  --card-bg: #1e1e1e;
  --card-shadow: rgba(0, 0, 0, 0.5);
  --book-title: #d0d8e0;
  --disabled: #555555;
}

/* Toggle button (shared by both pages). */
.theme-toggle {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text);
  border-radius: 4px;
  padding: 6px 10px;
  cursor: pointer;
  font-size: 1.1em;
  line-height: 1;
  transition: color 0.2s, border-color 0.2s;
}
.theme-toggle:hover {
  border-color: var(--accent);
  color: var(--accent);
}
```

- [ ] **Step 2: Verify the file is syntactically sane**

Run: `uv run python -c "import tinycss2" 2>/dev/null && echo has-tinycss || echo "skip lint"`
Expected: likely `skip lint` (no CSS linter installed). No action needed — visual verification happens in Task 8. Confirm the file exists:
Run: `test -f static/css/base.css && echo present`
Expected: `present`

- [ ] **Step 3: Commit**

```bash
git add static/css/base.css
git commit -m "Add base.css with light/dark theme variables and toggle button"
```

---

## Task 3: Write library.css (extracted library layout)

**Files:**
- Create: `static/css/library.css`

Source of truth: the current inline `<style>` in `templates/library.html:7-17`. Every hardcoded color is replaced by the matching variable from base.css. A new `.library-header` flex row holds the `<h1>` and the toggle button.

- [ ] **Step 1: Write the library stylesheet**

Create `static/css/library.css` with exactly this content:

```css
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  background: var(--page-bg);
  color: var(--text);
  margin: 0;
  padding: 40px;
}
.container {
  max-width: 800px;
  margin: 0 auto;
}
.library-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 2px solid var(--border-strong);
  padding-bottom: 10px;
}
.library-header h1 {
  color: var(--heading);
  margin: 0;
  border: none;
  padding: 0;
}
.book-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 20px;
  margin-top: 30px;
}
.book-card {
  background: var(--card-bg);
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 5px var(--card-shadow);
  transition: transform 0.2s;
}
.book-title {
  font-size: 1.2em;
  font-weight: bold;
  color: var(--book-title);
  margin-bottom: 10px;
}
.book-meta {
  color: var(--muted);
  font-size: 0.9em;
  margin-bottom: 15px;
}
.btn {
  display: inline-block;
  background: var(--accent);
  color: var(--on-accent);
  text-decoration: none;
  padding: 8px 15px;
  border-radius: 4px;
  font-size: 0.9em;
}
.btn:hover {
  background: var(--accent-hover);
}
```

- [ ] **Step 2: Confirm the file exists**

Run: `test -f static/css/library.css && echo present`
Expected: `present`

- [ ] **Step 3: Commit**

```bash
git add static/css/library.css
git commit -m "Add library.css extracted from library template"
```

---

## Task 4: Write reader.css (extracted reader layout)

**Files:**
- Create: `static/css/reader.css`

Source of truth: the current inline `<style>` in `templates/reader.html:7-39`. Every hardcoded color is replaced by the matching variable. A new `.sidebar-top` flex row holds the toggle button beside the "Back to Library" link. The inline `style="color: #999; padding: 10px;"` on the "Section X of Y" span (reader.html:111) becomes the `.chapter-count` class here.

- [ ] **Step 1: Write the reader stylesheet**

Create `static/css/reader.css` with exactly this content:

```css
/* Layout */
body {
  margin: 0;
  padding: 0;
  display: flex;
  height: 100vh;
  overflow: hidden;
  font-family: "Georgia", serif;
  background: var(--content-bg);
  color: var(--text);
}

/* Sidebar */
#sidebar {
  width: 300px;
  background: var(--sidebar-bg);
  border-right: 1px solid var(--border);
  overflow-y: auto;
  padding: 20px;
  flex-shrink: 0;
}
.sidebar-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
.nav-header {
  font-family: -apple-system, sans-serif;
  font-weight: bold;
  color: var(--toc-link);
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--border-mid);
}
.nav-home {
  color: var(--accent);
  text-decoration: none;
  font-family: -apple-system, sans-serif;
  font-size: 0.9em;
}

/* TOC Tree */
ul.toc-list {
  list-style: none;
  padding-left: 0;
  margin: 0;
}
ul.toc-list ul {
  padding-left: 20px;
}
li.toc-item {
  margin-bottom: 8px;
}
a.toc-link {
  text-decoration: none;
  color: var(--toc-link);
  font-size: 0.95em;
  display: block;
  padding: 4px 0;
  line-height: 1.4;
}
a.toc-link:hover {
  color: var(--toc-link-hover);
  text-decoration: underline;
}
a.toc-link.active {
  color: var(--toc-active);
  font-weight: bold;
}

/* Main Content */
#main {
  flex-grow: 1;
  overflow-y: auto;
  position: relative;
  scroll-behavior: smooth;
}
.content-container {
  max-width: 700px;
  margin: 0 auto;
  padding: 60px 40px;
  line-height: 1.8;
  font-size: 1.15em;
  color: var(--text);
}

/* Content Styling */
.book-content img {
  max-width: 100%;
  height: auto;
  display: block;
  margin: 20px auto;
}
.book-content h1,
.book-content h2,
.book-content h3 {
  font-family: -apple-system, sans-serif;
  margin-top: 1.5em;
  color: var(--heading);
}
.book-content p {
  margin-bottom: 1.5em;
  text-align: justify;
}

/* Navigation Footer */
.chapter-nav {
  display: flex;
  justify-content: space-between;
  margin-top: 60px;
  padding-top: 20px;
  border-top: 1px solid var(--border-soft);
  font-family: -apple-system, sans-serif;
}
.chapter-count {
  color: var(--muted-soft);
  padding: 10px;
}
.nav-btn {
  text-decoration: none;
  color: var(--accent);
  font-weight: bold;
  padding: 10px 20px;
  border: 1px solid var(--accent);
  border-radius: 4px;
  transition: all 0.2s;
}
.nav-btn:hover {
  background: var(--accent);
  color: var(--on-accent);
}
.nav-btn.disabled {
  opacity: 0.5;
  pointer-events: none;
  border-color: var(--disabled);
  color: var(--disabled);
}
```

- [ ] **Step 2: Confirm the file exists**

Run: `test -f static/css/reader.css && echo present`
Expected: `present`

- [ ] **Step 3: Commit**

```bash
git add static/css/reader.css
git commit -m "Add reader.css extracted from reader template"
```

---

## Task 5: Write theme.js (toggle handler + persistence)

**Files:**
- Create: `static/js/theme.js`

- [ ] **Step 1: Write the toggle script**

Create `static/js/theme.js` with exactly this content:

```javascript
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

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".theme-toggle").forEach(function (btn) {
      btn.addEventListener("click", toggle);
    });
    updateButtons();
  });
})();
```

- [ ] **Step 2: Confirm the file exists**

Run: `test -f static/js/theme.js && echo present`
Expected: `present`

- [ ] **Step 3: Commit**

```bash
git add static/js/theme.js
git commit -m "Add theme.js toggle handler with localStorage persistence"
```

---

## Task 6: Update library.html (link CSS, no-flash script, toggle button)

**Files:**
- Modify: `templates/library.html`

- [ ] **Step 1: Replace the `<head>` style block with stylesheet links + no-flash init**

In `templates/library.html`, replace the entire `<style>...</style>` block (lines 7-17) with:

```html
    <link rel="stylesheet" href="/static/css/base.css">
    <link rel="stylesheet" href="/static/css/library.css">
    <script>
      // Set theme before paint to avoid a flash of the wrong colors.
      (function () {
        var saved = null;
        try { saved = localStorage.getItem("theme"); } catch (e) {}
        var theme =
          saved ||
          (window.matchMedia &&
          matchMedia("(prefers-color-scheme: dark)").matches
            ? "dark"
            : "light");
        document.documentElement.setAttribute("data-theme", theme);
      })();
    </script>
```

- [ ] **Step 2: Wrap the `<h1>` in a header row with the toggle button**

In `templates/library.html`, replace this line (currently line 21):

```html
        <h1>Library</h1>
```

with:

```html
        <div class="library-header">
            <h1>Library</h1>
            <button class="theme-toggle" type="button" aria-label="Toggle theme">&#9790;</button>
        </div>
```

- [ ] **Step 3: Load theme.js before `</body>`**

In `templates/library.html`, immediately before the closing `</body>` tag, add:

```html
    <script src="/static/js/theme.js" defer></script>
```

- [ ] **Step 4: Commit**

```bash
git add templates/library.html
git commit -m "Wire library template to static CSS and theme toggle"
```

---

## Task 7: Update reader.html (link CSS, no-flash script, toggle button)

**Files:**
- Modify: `templates/reader.html`

- [ ] **Step 1: Replace the `<head>` style block with stylesheet links + no-flash init**

In `templates/reader.html`, replace the entire `<style>...</style>` block (lines 7-39) with:

```html
    <link rel="stylesheet" href="/static/css/base.css">
    <link rel="stylesheet" href="/static/css/reader.css">
    <script>
      // Set theme before paint to avoid a flash of the wrong colors.
      (function () {
        var saved = null;
        try { saved = localStorage.getItem("theme"); } catch (e) {}
        var theme =
          saved ||
          (window.matchMedia &&
          matchMedia("(prefers-color-scheme: dark)").matches
            ? "dark"
            : "light");
        document.documentElement.setAttribute("data-theme", theme);
      })();
    </script>
```

- [ ] **Step 2: Add a sidebar top row with the toggle button**

In `templates/reader.html`, replace these two lines (currently lines 45-46):

```html
        <a href="/" class="nav-home">← Back to Library</a>
        <div class="nav-header">{{ book.metadata.title }}</div>
```

with:

```html
        <div class="sidebar-top">
            <a href="/" class="nav-home">← Back to Library</a>
            <button class="theme-toggle" type="button" aria-label="Toggle theme">&#9790;</button>
        </div>
        <div class="nav-header">{{ book.metadata.title }}</div>
```

- [ ] **Step 3: Replace the inline-styled "Section" span with the `.chapter-count` class**

In `templates/reader.html`, replace this line (currently line 111):

```html
                <span style="color: #999; padding: 10px;">
```

with:

```html
                <span class="chapter-count">
```

- [ ] **Step 4: Load theme.js before `</body>`**

In `templates/reader.html`, immediately before the closing `</body>` tag (after the existing `findAndGo` `<script>` block, which stays inline because it needs the Jinja-injected `spineMap`), add:

```html
    <script src="/static/js/theme.js" defer></script>
```

- [ ] **Step 5: Commit**

```bash
git add templates/reader.html
git commit -m "Wire reader template to static CSS and theme toggle"
```

---

## Task 8: End-to-end verification

**Files:** none (verification only)

- [ ] **Step 1: Smoke-check imports**

Run: `uv run python -c "import server, reader3; print('ok')"`
Expected: `ok`, no traceback.

- [ ] **Step 2: Start the server in the background**

Run: `uv run server.py &`  then wait ~2s for startup.
Expected: log line `Starting server at http://127.0.0.1:8123`.

- [ ] **Step 3: Verify the static assets are served**

Run:
```bash
for f in css/base.css css/library.css css/reader.css js/theme.js; do
  printf "%s -> " "$f"; curl -s -o /dev/null -w "%{http_code}\n" "http://127.0.0.1:8123/static/$f";
done
```
Expected: `200` for all four files.

- [ ] **Step 4: Verify the library page references the new assets and has no inline `<style>`**

Run:
```bash
curl -s http://127.0.0.1:8123/ | grep -c 'static/css/base.css'
curl -s http://127.0.0.1:8123/ | grep -c '<style>'
```
Expected: first command prints `1`; second prints `0`.

- [ ] **Step 5: Verify a reader chapter renders with the new assets**

Run:
```bash
curl -s http://127.0.0.1:8123/read/a-philosophy-of-software-design-2nd-edition_data/0 | grep -c 'static/css/reader.css'
curl -s http://127.0.0.1:8123/read/a-philosophy-of-software-design-2nd-edition_data/0 | grep -c 'theme-toggle'
```
Expected: both print `1` (or higher for the toggle if matched per-occurrence — non-zero is the pass condition).

- [ ] **Step 6: Stop the background server**

Run: `kill %1` (or `pkill -f server.py`).
Expected: server process ends.

- [ ] **Step 7: Visual confirmation (manual)**

Load `http://127.0.0.1:8123/` and a chapter in a browser. Confirm:
- Library and reader render identically to before in light mode.
- Clicking the ☾/☀ button flips colors on the current page with no broken/unstyled elements.
- The glyph updates to reflect the new state.
- Reloading the page keeps the chosen theme; navigating library ↔ reader keeps it too.
- No flash of light theme when loading with dark saved.

- [ ] **Step 8: Lint and format the Python change**

Run: `uv run ruff format . && uv run ruff check --fix .`
Expected: no errors. Confirm the load-bearing `# noqa: F401` imports in `server.py` are untouched.

- [ ] **Step 9: Remove the temporary placeholder and commit any lint fixes**

```bash
git rm static/.gitkeep
git commit -am "Remove static placeholder; finalize dark mode and CSS extraction"
```
(If ruff made no changes and nothing else is staged, the `.gitkeep` removal alone is the commit.)

---

## Notes for the implementer

- **Do not** remove the `from reader3 import Book, BookMetadata, ChapterContent, TOCEntry  # noqa: F401` line in `server.py` — it is load-bearing for unpickling. `ruff --fix` may try; verify it survives in Step 8.
- The reader's existing `findAndGo` `<script>` stays inline — it depends on the Jinja-rendered `spineMap`. Only the no-flash init and the `theme.js` `<link>`/`<script>` are added.
- No pickle/dataclass fields change, so existing `*_data/` books do not need reprocessing.
- If `uv run server.py &` is not desired in the execution environment, the user can run `uv run server.py` in their own shell and the `curl` checks can be run against it.
