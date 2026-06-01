---
name: verify-reader
description: Use when you've edited reader3.py, server.py, or the templates and need to confirm the EPUB reader still works before calling the change done.
---

# Verify reader3

Run these checks after changing code. Report a pass/fail line for each step.

**Pre-existing failures don't block your change.** If a step fails, check whether it's caused by *your* edit or was already broken on `HEAD`: `git diff` the lines involved, and for the step-3 serve check, `git stash` your edit and re-run to see if it fails on `HEAD` too. Report pre-existing failures, but only treat a NEW failure your change introduced as blocking.

## 1. Import check

```bash
uv run python -c "import server, reader3"
```
Both modules must import without error.

## 2. Lint / format (run both; don't chain with `&&`)

```bash
uv run ruff check .
uv run ruff format --check .
```
Run them separately so a lint failure doesn't hide a formatting one. Apply the pre-existing-failure rule above — reader3.py may carry old lint debt; what matters is that your edit added none.

## 3. Process + serve a book end-to-end (the real test)

A status-200 on `/` is NOT enough — `library_view` swallows pickle-load errors and still returns 200 with an empty page. The authoritative signal is the **chapter route**: it returns `200` only if the pickle actually loaded (you can't render a chapter otherwise), so a 200 there proves the round-trip works. Don't grep the library HTML for the title — title-from-dirname munging is unreliable and gives false passes.

```bash
cd /home/noob_master/reader3
# pick a sample EPUB (ask the user if none exists)
EPUB=$(ls *.epub 2>/dev/null | head -1)
uv run reader3.py "$EPUB"                      # regenerates <name>_data/book.pkl + images/

# free port 8123 by PORT, not name (a name match like `pkill -f server.py`
# also matches this very shell's command line and kills your session)
lsof -ti tcp:8123 | xargs -r kill 2>/dev/null
nohup uv run server.py >/tmp/reader3-verify.log 2>&1 & SRV=$!; disown
for i in $(seq 1 20); do curl -sf http://127.0.0.1:8123/ >/dev/null 2>&1 && break; sleep 0.3; done

BID=$(ls -d *_data | head -1)
CH_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8123/read/$BID/0")
kill "$SRV" 2>/dev/null                          # kill the captured PID, never `pkill -f server.py`

echo "chapter 0 status: $CH_CODE (want 200)"
grep -i "error loading book" /tmp/reader3-verify.log && echo "PICKLE LOAD FAILED"
```

**Pass requires both:** chapter 0 returns `200` AND the log shows no `error loading book`. (Open `http://127.0.0.1:8123/` in a browser for a manual sanity look, but don't gate on grepping its HTML.)

Capture the PID (`SRV=$!`) and `kill "$SRV"` — never `kill %1` or `pkill -f server.py` (the latter matches your own shell). If your shell can't background reliably (some agent harnesses abort the whole command with exit 144 on `&`), start the server with your tool's background-run mode instead and poll in a separate step. Use the readiness poll, not a fixed `sleep`.

## Known failure mode

If the log shows `Can't get attribute 'BookMetadata' on <module '__main__'>` (or `Book`, `ChapterContent`, `TOCEntry`):

`reader3.py` pickles the book while running as a script, so the classes are stored under `__main__.*`. `server.py` runs as `__main__` too, so `pickle.load` resolves those names against **server.py's** namespace — which only works because `server.py` imports them: `from reader3 import Book, BookMetadata, ChapterContent, TOCEntry`. These imports look unused to a linter (ruff F401) but are load-bearing; they carry a `# noqa: F401`. **If this error appears, the usual cause is that those imports got removed from server.py** (e.g. an auto-fix) — restore them. Reprocessing the EPUB will NOT fix it. (A dataclass change in reader3.py also requires reprocessing, but the symptom there is a different attribute/field error, not this one.)
