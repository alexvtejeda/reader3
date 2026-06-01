# reader3 MCP Server Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a local stdio MCP server (`mcp_server.py`) that exposes reader3's processed EPUBs to Claude Desktop via three tools: `list_books`, `get_toc`, `get_chapter`.

**Architecture:** A single new file, sibling to `server.py`, built on FastMCP (official `mcp` SDK). It reuses the pickled `Book` objects in `*_data/` dirs through its own small `@lru_cache`d loader. It does NOT import `server.py` (avoids FastAPI/StaticFiles startup and `server.py`'s `print()`-to-stdout, which would corrupt the JSON-RPC stdio stream). All logging goes to stderr. Real logic lives in plain `_helper` functions; the `@mcp.tool()` functions are thin wrappers so each piece is verifiable without the MCP runtime.

**Tech Stack:** Python 3.10+, `uv`, `mcp[cli]` (FastMCP), existing `reader3` dataclasses.

**Spec:** `docs/superpowers/specs/2026-06-01-mcp-server-design.md`

**Testing note:** This repo has no test suite (per CLAUDE.md), and we are not introducing one (YAGNI — matches convention). Each task is verified with a `uv run python -c "..."` smoke check against the already-processed sample book `a-philosophy-of-software-design-2nd-edition_data`. Commit after each task.

---

## File Structure

- **Create:** `mcp_server.py` (repo root) — the entire server. Responsibilities: load books, the three tools, the stdio entrypoint.
- **Modify:** `pyproject.toml` + `uv.lock` — add the `mcp[cli]` dependency (via `uv add`, do not hand-edit).
- **Unchanged:** `server.py`, `reader3.py`, `templates/`, `static/`. The web reader is not touched.
- **Manual (Windows, not in repo):** `%APPDATA%\Claude\claude_desktop_config.json` — documented in the final task, created by the user.

---

## Task 1: Add the `mcp` dependency

**Files:**
- Modify: `pyproject.toml`, `uv.lock` (via `uv add`)

- [ ] **Step 1: Add the dependency**

Run:
```bash
uv add "mcp[cli]"
```
Expected: resolves and installs `mcp` (and its deps), adds `mcp[cli]` under `[project] dependencies` in `pyproject.toml`, updates `uv.lock`.

- [ ] **Step 2: Verify FastMCP imports**

Run:
```bash
uv run python -c "from mcp.server.fastmcp import FastMCP; print('ok')"
```
Expected: prints `ok` (no ImportError).

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "Add mcp[cli] dependency for the MCP server"
```

---

## Task 2: Server skeleton — loader + stdio entrypoint

Create the file with imports, stderr logging, the cached loader, and a runnable (but tool-less) entrypoint. This makes the server importable and runnable before any tools exist.

**Files:**
- Create: `mcp_server.py`

- [ ] **Step 1: Write the skeleton**

Create `mcp_server.py` with exactly:

```python
"""MCP server exposing reader3 books to Claude Desktop over stdio.

Sibling to server.py. Deliberately does NOT import server.py: that would start
FastAPI, mount StaticFiles, and pull in load_book_cached's print()-to-stdout,
which corrupts the stdio JSON-RPC stream. All logging here goes to stderr only.
"""

import logging
import os
import pickle
import sys
from functools import lru_cache

from mcp.server.fastmcp import FastMCP

# Load-bearing for unpickling: book.pkl is pickled by reader3.py-as-__main__,
# so these names must be importable here for pickle.load to resolve the Book.
# Do not let a linter remove them (mirrors server.py).
from reader3 import Book, BookMetadata, ChapterContent, TOCEntry  # noqa: F401

logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger("reader3-mcp")

# Books live in the working directory (set by the launch command's `cd`),
# identical to server.py's BOOKS_DIR assumption.
BOOKS_DIR = "."

mcp = FastMCP("reader3")


@lru_cache(maxsize=10)
def _load_book(book_id: str) -> Book | None:
    """Load a pickled Book by its *_data folder name. Logs to stderr, never stdout."""
    safe_id = os.path.basename(book_id)
    path = os.path.join(BOOKS_DIR, safe_id, "book.pkl")
    if not os.path.exists(path):
        return None
    try:
        with open(path, "rb") as f:
            return pickle.load(f)
    except Exception as e:
        logger.error("Failed to load book %s: %s", book_id, e)
        return None


if __name__ == "__main__":
    mcp.run()  # stdio transport by default
```

- [ ] **Step 2: Verify it imports and loads the sample book**

Run:
```bash
uv run python -c "import mcp_server; b = mcp_server._load_book('a-philosophy-of-software-design-2nd-edition_data'); print(b.metadata.title, len(b.spine))"
```
Expected: prints the book title and a chapter count > 0 (e.g. `A Philosophy of Software Design ... 22`). Nothing printed to stdout except that line.

- [ ] **Step 3: Verify unknown book returns None (no crash)**

Run:
```bash
uv run python -c "import mcp_server; print(mcp_server._load_book('does-not-exist_data'))"
```
Expected: prints `None`.

- [ ] **Step 4: Commit**

```bash
git add mcp_server.py
git commit -m "Add MCP server skeleton: book loader + stdio entrypoint"
```

---

## Task 3: `list_books` tool

**Files:**
- Modify: `mcp_server.py`

- [ ] **Step 1: Add the tool**

Insert after `_load_book` (before the `if __name__` block):

```python
@mcp.tool()
def list_books() -> list[dict]:
    """List processed books available to read.

    Returns one entry per book with: id (use it for get_toc/get_chapter),
    title, author, num_chapters.
    """
    books = []
    for item in sorted(os.listdir(BOOKS_DIR)):
        if item.endswith("_data") and os.path.isdir(os.path.join(BOOKS_DIR, item)):
            book = _load_book(item)
            if book:
                books.append(
                    {
                        "id": item,
                        "title": book.metadata.title,
                        "author": ", ".join(book.metadata.authors),
                        "num_chapters": len(book.spine),
                    }
                )
    return books
```

- [ ] **Step 2: Verify it lists the sample book**

Run:
```bash
uv run python -c "import mcp_server, json; print(json.dumps(mcp_server.list_books(), indent=2))"
```
Expected: a JSON list containing an entry whose `id` is `a-philosophy-of-software-design-2nd-edition_data`, with a non-empty `title`, `author`, and integer `num_chapters`.

- [ ] **Step 3: Commit**

```bash
git add mcp_server.py
git commit -m "Add list_books MCP tool"
```

---

## Task 4: TOC join helper + `get_toc` tool

`get_chapter` is addressed by spine index, but real chapter titles live in the TOC keyed by filename. `_chapter_list` joins them — the same mapping `reader.html`'s JS does.

**Files:**
- Modify: `mcp_server.py`

- [ ] **Step 1: Add the join helper**

Insert after `_load_book`:

```python
def _chapter_list(book: Book) -> list[dict]:
    """Flat, spine-ordered chapter list with real TOC titles joined by filename.

    Mirrors reader.html's JS: TOC titles are keyed by file_href, spine items by
    href. The first TOC entry pointing at a file wins; spine items with no TOC
    match keep their own fallback title (e.g. "Section 3").
    """
    title_by_file: dict[str, str] = {}

    def walk(entries: list[TOCEntry]) -> None:
        for e in entries:
            if e.file_href and e.file_href not in title_by_file:
                title_by_file[e.file_href] = e.title
            walk(e.children)

    walk(book.toc)

    return [
        {"index": ch.order, "title": title_by_file.get(ch.href, ch.title)}
        for ch in book.spine
    ]
```

- [ ] **Step 2: Add the tool**

Insert after `list_books`:

```python
@mcp.tool()
def get_toc(book_id: str) -> dict:
    """Get a book's flat, numbered chapter list for browsing.

    Returns title, author, and chapters: a list of {index, title}. Pass an
    index to get_chapter to read that chapter.
    """
    book = _load_book(book_id)
    if not book:
        return {"error": f"No book with id '{book_id}'. Call list_books."}
    return {
        "title": book.metadata.title,
        "author": ", ".join(book.metadata.authors),
        "chapters": _chapter_list(book),
    }
```

- [ ] **Step 3: Verify the TOC has real titles and contiguous indices**

Run:
```bash
uv run python -c "import mcp_server, json; t = mcp_server.get_toc('a-philosophy-of-software-design-2nd-edition_data'); print(json.dumps(t['chapters'][:5], indent=2)); print('count', len(t['chapters']))"
```
Expected: first 5 chapters print with `index` 0,1,2,3,4 and human-readable `title` values (not all `"Section N"`); `count` equals the book's chapter count.

- [ ] **Step 4: Verify unknown book returns an error dict**

Run:
```bash
uv run python -c "import mcp_server; print(mcp_server.get_toc('nope_data'))"
```
Expected: `{'error': \"No book with id 'nope_data'. Call list_books.\"}`

- [ ] **Step 5: Commit**

```bash
git add mcp_server.py
git commit -m "Add get_toc MCP tool with TOC-title join helper"
```

---

## Task 5: `get_chapter` tool

**Files:**
- Modify: `mcp_server.py`

- [ ] **Step 1: Add the tool**

Insert after `get_toc`:

```python
@mcp.tool()
def get_chapter(book_id: str, index: int) -> dict:
    """Get the plain text of one chapter by its index (from get_toc).

    Returns index, title, text (plain text), and num_chapters.
    """
    book = _load_book(book_id)
    if not book:
        return {"error": f"No book with id '{book_id}'. Call list_books."}
    n = len(book.spine)
    if index < 0 or index >= n:
        return {"error": f"Chapter {index} out of range; book has {n} chapters (0-{n - 1})."}
    chapter = book.spine[index]
    titles = _chapter_list(book)
    return {
        "index": index,
        "title": titles[index]["title"],
        "text": chapter.text,
        "num_chapters": n,
    }
```

- [ ] **Step 2: Verify a valid chapter returns text**

Run:
```bash
uv run python -c "import mcp_server; c = mcp_server.get_chapter('a-philosophy-of-software-design-2nd-edition_data', 1); print(c['index'], c['num_chapters'], repr(c['title'])); print(c['text'][:200])"
```
Expected: prints index `1`, the chapter count, a title, and the first 200 chars of plain text (no HTML tags).

- [ ] **Step 3: Verify out-of-range and unknown-book errors**

Run:
```bash
uv run python -c "import mcp_server; print(mcp_server.get_chapter('a-philosophy-of-software-design-2nd-edition_data', 9999)); print(mcp_server.get_chapter('nope_data', 0))"
```
Expected: first prints an `out of range` error dict naming the real chapter count; second prints the `No book with id 'nope_data'` error dict.

- [ ] **Step 4: Commit**

```bash
git add mcp_server.py
git commit -m "Add get_chapter MCP tool"
```

---

## Task 6: Lint, end-to-end stdio check, and Claude Desktop wiring

**Files:**
- Modify: `mcp_server.py` (only if ruff reformats)
- Manual: `%APPDATA%\Claude\claude_desktop_config.json` (Windows side, created by user)

- [ ] **Step 1: Format and lint**

Run:
```bash
uv run ruff format . && uv run ruff check .
```
Expected: ruff reports no errors. The `# noqa: F401` on the `reader3` import keeps the load-bearing names. If `ruff format` changed `mcp_server.py`, that's fine.

- [ ] **Step 2: Verify the server starts over stdio and exits cleanly**

Run:
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"smoke","version":"0"}}}' | uv run python mcp_server.py
```
Expected: the process emits a single JSON-RPC response line on **stdout** beginning with `{"jsonrpc":"2.0","id":1,"result":` (the server's `initialize` reply). Log lines, if any, appear on stderr — not mixed into that stdout line. (The process may then wait for more input; Ctrl-C to exit.) This proves stdout carries only protocol data.

- [ ] **Step 3 (optional): Drive it with the MCP Inspector**

If Node/`npx` is available in WSL:
```bash
uv run mcp dev mcp_server.py
```
Open the printed local URL, then call `list_books` → `get_toc` → `get_chapter` and confirm each returns the sample book's data. Skip if `npx` is unavailable — Step 2 already proves the stdio contract.

- [ ] **Step 4: Commit any lint changes**

```bash
git add mcp_server.py
git commit -m "Format mcp_server.py with ruff" || echo "nothing to commit"
```

- [ ] **Step 5: Wire up Claude Desktop (manual, Windows side)**

Edit `%APPDATA%\Claude\claude_desktop_config.json` to add:
```json
{
  "mcpServers": {
    "reader3": {
      "command": "wsl.exe",
      "args": ["-e", "bash", "-lc",
               "cd /home/noob_master/reader3 && exec uv run python mcp_server.py"]
    }
  }
}
```
Notes:
- The `bash -lc` login shell puts `uv` on PATH (it lives in `~/.local/bin`).
- If more than one WSL distro is installed, add `"-d", "<distro>",` right after `"-e"`.
- Fully quit Claude Desktop (system tray → Quit) and reopen to reload the config.

- [ ] **Step 6: Confirm in Claude Desktop**

In a new Claude Desktop conversation, confirm the `reader3` tools appear and that asking it to list books / open a chapter returns the sample book's text.

---

## Self-Review

**Spec coverage:**
- Three tools (`list_books`, `get_toc`, `get_chapter`) — Tasks 3, 4, 5. ✅
- Plain-text chapters — `get_chapter` returns `chapter.text`. ✅
- Flat TOC with titles joined by filename — `_chapter_list`, Task 4. ✅
- `book_id` = `*_data` folder name — used throughout. ✅
- No import of `server.py`; own loader; stderr-only logging — Task 2. ✅
- Error strings for unknown book / out-of-range — Tasks 4, 5. ✅
- stdio over `wsl.exe`, login shell, optional `-d`, full restart — Task 6. ✅
- Verification: import check, smoke calls, stdio contract, optional Inspector, lint — Tasks 1–6. ✅
- New file + `pyproject.toml`/`uv.lock` only; web reader untouched — Tasks 1–2, File Structure. ✅

**Placeholder scan:** No TBD/TODO; every code step shows complete code; every run step shows command + expected output.

**Type consistency:** `_load_book(book_id) -> Book | None`, `_chapter_list(book) -> list[{index,title}]`, tools return `list[dict]`/`dict`, error shape is always `{"error": "..."}`. `index`/`title`/`num_chapters` key names are consistent across `get_toc` and `get_chapter`.
