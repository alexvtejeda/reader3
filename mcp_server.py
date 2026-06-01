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


if __name__ == "__main__":
    mcp.run()  # stdio transport by default
