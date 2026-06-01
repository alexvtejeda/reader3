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

# book.pkl was created by reader3.py running as __main__, so its Book classes
# are stored under the module name "__main__". _BookUnpickler remaps that to
# "reader3" at load time. This import also provides the Book type used in the
# annotation below; do not let a linter remove it.
from reader3 import Book, BookMetadata, ChapterContent, TOCEntry  # noqa: F401

logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger("reader3-mcp")

# Books live in the working directory (set by the launch command's `cd`),
# identical to server.py's BOOKS_DIR assumption.
BOOKS_DIR = "."

mcp = FastMCP("reader3")


class _BookUnpickler(pickle.Unpickler):
    """Resolve Book classes pickled under __main__ (reader3.py ran as a script)
    back to the reader3 module, regardless of how this server is launched."""

    def find_class(self, module, name):
        if module == "__main__":
            module = "reader3"
        return super().find_class(module, name)


@lru_cache(maxsize=10)
def _load_book(book_id: str) -> Book | None:
    """Load a pickled Book by its *_data folder name. Logs to stderr, never stdout."""
    safe_id = os.path.basename(book_id)
    path = os.path.join(BOOKS_DIR, safe_id, "book.pkl")
    if not os.path.exists(path):
        return None
    try:
        with open(path, "rb") as f:
            return _BookUnpickler(f).load()
    except Exception as e:
        logger.error("Failed to load book %s: %s", book_id, e)
        return None


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

    # Index by list position, not ch.order: get_chapter does book.spine[index],
    # and ch.order can have gaps when reader3.py skipped non-document spine items.
    return [
        {"index": i, "title": title_by_file.get(ch.href, ch.title)}
        for i, ch in enumerate(book.spine)
    ]


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


if __name__ == "__main__":
    mcp.run()  # stdio transport by default
