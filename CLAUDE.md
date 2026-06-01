# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

reader3 is a self-hosted EPUB reader web app (FastAPI + Jinja2). It serves a book one chapter at a time so chapter text can be copy-pasted into an LLM for collaborative reading. Intentionally simple — single project, no test suite.

## Commands

Package manager is **uv** (not pip/poetry). Python 3.10+.

```bash
uv run reader3.py <file.epub>   # process an EPUB → creates <name>_data/ (book.pkl + images/)
uv run server.py                # start the web server at http://127.0.0.1:8123/
uv run ruff format . && uv run ruff check --fix .   # format + lint
```

You may start the server yourself to test changes. There is no test suite — verify a change by processing a sample EPUB and loading a chapter in the reader (or at minimum `uv run python -c "import server, reader3"`).

## Architecture

- `reader3.py` — parses an EPUB with `ebooklib`, cleans HTML (strips scripts/styles/iframes/forms), rewrites image paths to local `images/`, builds a linear **spine** (reading order) and a hierarchical **TOC**, then pickles a `Book` object to `<name>_data/book.pkl`.
- `server.py` — FastAPI app. `/` lists books by scanning `*_data/` dirs; `/read/{book_id}/{chapter_index}` renders a chapter; books are cached with `@lru_cache`.
- `templates/` — `library.html` (card grid) and `reader.html` (TOC sidebar + content; inline CSS/JS, no framework). TOC entries map to spine indices by filename in `reader.html`'s JavaScript.

## Gotchas

- **Pickle fragility**: `book.pkl` is a pickled `Book` dataclass. Adding/renaming dataclass fields in `reader3.py` breaks existing `*_data/` pickles — reprocess the EPUB after such changes.
- **Load-bearing imports**: `server.py`'s `from reader3 import Book, BookMetadata, ChapterContent, TOCEntry` looks partly unused but is required for unpickling (`reader3.py` pickles under `__main__`, and `server.py` is `__main__`). They carry `# noqa: F401` — do NOT remove them; ruff `--fix` will try to. Removing them makes the library load empty and all chapters 404.
- **Hardcoded config**: `BOOKS_DIR = "."` and host/port `127.0.0.1:8123` are hardcoded in `server.py`. Books must live in the working directory.
- **Cache**: `load_book_cached()` uses `@lru_cache` (not thread-safe); fine for local single-user use.
- Style: no enforced convention historically — match the existing code (type hints, dataclasses, docstrings). ruff is now configured; run it on edits.
