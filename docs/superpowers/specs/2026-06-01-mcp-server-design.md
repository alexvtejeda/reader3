# MCP Server for reader3 — Design

**Date:** 2026-06-01
**Status:** Approved (design phase)

## Purpose

Let Claude Desktop read and discuss a processed EPUB without copy-pasting chapter
text by hand. A local MCP server exposes reader3's already-parsed books to Claude
Desktop, which fetches chapters on demand and browses book structure.

This replaces the manual copy-paste workflow. It was chosen over a built-in
Claude-API chat panel (different product direction, requires an API key).

## Scope

**In scope:** pull chapters on demand, browse book structure (library + per-book
chapter list).

**Out of scope (deliberately dropped during brainstorming):**

- Full-text search within a book.
- Loading the whole book at once (context-blowing, unnecessary for the workflow).
- Returning HTML — chapters are returned as plain text only.
- Any change to the web reader (`server.py`) or the EPUB processor (`reader3.py`).

## Architecture

A single new file, **`mcp_server.py`**, in the repo root (~70–90 lines). It is a
*sibling* to `server.py`, not a replacement — the web reader keeps working
unchanged.

- Built on **FastMCP**, the high-level decorator API in the official `mcp` Python
  SDK. Added as a dependency via `uv add mcp`.
- Communicates over **stdio** (the JSON-RPC transport Claude Desktop uses for
  local servers).
- Does **not** import `server.py` — that would spin up FastAPI, mount
  `StaticFiles`, and (worse) pull in `load_book_cached`'s `print()`-to-stdout,
  which corrupts the stdio protocol stream.
- **Does** import `from reader3 import Book, BookMetadata, ChapterContent,
  TOCEntry`. These names must be in the module namespace so `pickle.load` can
  resolve the pickled `Book` (same load-bearing reason `server.py` imports them).
  They carry `# noqa: F401`.
- Carries its own ~10-line pickle loader, wrapped in `@lru_cache`, that logs
  failures to **stderr** (never stdout).

## Tool Surface

Three tools:

```
list_books() -> list[{ id, title, author, num_chapters }]
    Scans the working directory for *_data/ folders containing book.pkl,
    loads each, returns metadata only (no chapter content).

get_toc(book_id) -> { title, author, chapters: [{ index, title }] }
    A flat, numbered chapter list for Claude to browse before pulling a chapter.

get_chapter(book_id, index) -> { index, title, text, num_chapters }
    Returns chapter.text (plain text). num_chapters lets Claude know where it
    is in the book and when to stop.
```

`book_id` is the `*_data` folder name (e.g.
`a-philosophy-of-software-design-2nd-edition_data`) — the exact id `server.py`
already uses, so there is no second id scheme to reconcile.

### Chapter titles (the one real data-modeling decision)

`get_chapter` is addressed by **spine index** (`0 .. N-1`): clean and
unambiguous. But spine items carry only fallback titles (`"Section 1"`); the real
titles live in the TOC, keyed by filename (`file_href`).

So `get_toc` **joins TOC titles onto spine indices** by matching `file_href`
against each spine item's `href` — the same mapping `reader.html`'s JavaScript
does today, reimplemented in ~10 lines of Python. Spine items with no matching
TOC entry fall back to their existing title.

`get_toc` returns a **flat** numbered list, not the nested TOC tree. Rationale:
it maps 1:1 to the `index` that `get_chapter` takes, it is trivial for Claude to
scan, and it avoids the messiness of nested entries that share one spine file via
anchors. Visual hierarchy is lost, which is irrelevant for "what's chapter 12,
pull it."

## Data Flow

```
Claude Desktop (Windows)
  └─ spawns: wsl.exe -e bash -lc "cd /home/noob_master/reader3 && exec uv run python mcp_server.py"
       └─ FastMCP server (stdio, inside WSL)
            ├─ list_books   → os.listdir(".") → *_data/ → load_book(pkl) → metadata only
            ├─ get_toc      → load_book(pkl) → join TOC titles onto spine indices → flat list
            └─ get_chapter  → load_book(pkl) → spine[index].text
```

The launch command's `cd` sets the working directory to the repo root, so the
`BOOKS_DIR = "."` assumption holds identically to the web server. `@lru_cache` on
the loader means repeated `get_chapter` calls on one book don't re-read the
pickle.

## Error Handling

Tools return readable error strings to Claude rather than raising — Claude can
then self-correct.

- **Unknown `book_id`** → `{ error: "No book with id '<id>'. Call list_books." }`
- **`index` out of range** →
  `{ error: "Chapter <i> out of range; book has <N> chapters (0-<N-1>)." }`,
  bounds-checked exactly like `read_chapter` (`< 0 or >= len(spine)`).
- **Corrupt/missing pickle** → loader logs the exception to **stderr** and the
  tool returns an error string. A bad book never crashes the server or poisons
  the JSON-RPC stream.

No `print()` to stdout anywhere in this file — the load-bearing stdio rule.

## WSL2 Launch

Claude Desktop runs on Windows; reader3 lives in WSL2. Desktop launches local MCP
servers as child processes, so it must cross the WSL boundary. `wsl.exe` pipes
stdin/stdout straight through to a process inside the distro.

**`claude_desktop_config.json`** (Windows side, `%APPDATA%\Claude\`):

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

- The `bash -lc` **login shell** loads the user profile so `uv` is on `PATH`
  (it lives in `~/.local/bin`, which a bare `wsl.exe -e uv` often can't see).
- If more than one WSL distro is installed, add `-d <distro>` to target the
  right one.
- Restart Claude Desktop fully (tray → Quit) to reload the config.

Chosen over running an HTTP/SSE server in WSL: stdio is Claude Desktop's
first-class local-server path (Desktop manages lifecycle, no port to manage, no
process to start manually). HTTP/SSE targets hosted/authenticated remote servers
and is strictly more fragile for a local single-user tool.

## Verification

No test suite in this repo, so verification is manual and staged to isolate
"is the server correct" from "is the WSL bridge correct":

1. `uv run python -c "import mcp_server"` — imports cleanly.
2. `uv run mcp dev mcp_server.py` — MCP Inspector opens a local web UI that drives
   the server over stdio. Click each tool; confirm `list_books` → `get_toc` →
   `get_chapter` returns the philosophy-of-software-design book's text. Proves the
   server before involving Claude Desktop.
3. Wire up the Desktop config; confirm the tools appear and return chapter text in
   a real conversation.
4. `uv run ruff format . && uv run ruff check .` — the repo's lint gate.

## Files Touched

- **New:** `mcp_server.py` (repo root).
- **Modified:** `pyproject.toml` / `uv.lock` (adds `mcp` dependency).
- **Unchanged:** `server.py`, `reader3.py`, `templates/`. The web reader is not
  affected.
