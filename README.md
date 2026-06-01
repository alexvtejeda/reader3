# reader 3

![reader3](reader3.png)

A lightweight, self-hosted EPUB reader that lets you read through EPUB books one chapter at a time. This makes it very easy to copy paste the contents of a chapter to an LLM, to read along. Basically - get epub books (e.g. [Project Gutenberg](https://www.gutenberg.org/) has many), open them up in this reader, copy paste text around to your favorite LLM, and read together and along.

This project was 90% vibe coded just to illustrate how one can very easily [read books together with LLMs](https://x.com/karpathy/status/1990577951671509438). I'm not going to support it in any way, it's provided here as is for other people's inspiration and I don't intend to improve it. Code is ephemeral now and libraries are over, ask your LLM to change it in whatever way you like.

## Usage

The project uses [uv](https://docs.astral.sh/uv/). So for example, download [Dracula EPUB3](https://www.gutenberg.org/ebooks/345) to this directory as `dracula.epub`, then:

```bash
uv run reader3.py dracula.epub
```

This creates the directory `dracula_data`, which registers the book to your local library. We can then run the server:

```bash
uv run server.py
```

And visit [localhost:8123](http://localhost:8123/) to see your current Library. You can easily add more books, or delete them from your library by deleting the folder. It's not supposed to be complicated or complex.

## Dark / light mode

Both the library and the reader have a moon/sun button (top of the sidebar) that toggles dark and light themes. Your choice is saved in the browser, and on first visit it follows your operating system's preference. The theme is applied before the page paints, so there's no flash of the wrong colors.

## Read with Claude Desktop (MCP server)

Instead of copy-pasting chapters by hand, you can let [Claude Desktop](https://claude.ai/download) pull them directly through a small [MCP](https://modelcontextprotocol.io/) server (`mcp_server.py`). It exposes three tools over stdio against the same processed `*_data/` books:

- `list_books()` — the books in your library (id, title, author, chapter count)
- `get_toc(book_id)` — a numbered chapter list to browse
- `get_chapter(book_id, index)` — the plain text of one chapter

It's a sibling to `server.py` and doesn't replace it — process books the same way (`uv run reader3.py book.epub`), and Claude Desktop launches the MCP server itself; you don't run it manually. Using it goes through your Claude subscription (it's local software — no API key, no separate API charges).

Add the server to Claude Desktop's `claude_desktop_config.json` (on Windows: `%APPDATA%\Claude\claude_desktop_config.json`), then fully quit Claude Desktop (tray → Quit) and reopen.

```json
{
  "mcpServers": {
    "reader3": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/reader3", "python", "mcp_server.py"]
    }
  }
}
```

### Running in WSL2 (Claude Desktop on Windows)

If reader3 lives inside WSL2 but Claude Desktop runs on Windows, launch across the boundary with `wsl.exe`. You must pin the **distro** and **user** — with neither, `wsl.exe` uses the default distro (often a Docker one) where your repo path doesn't exist:

```json
{
  "mcpServers": {
    "reader3": {
      "command": "wsl.exe",
      "args": ["-d", "ubuntu", "-u", "noob_master", "-e", "bash", "-lc",
               "cd /home/noob_master/reader3 && exec uv run python mcp_server.py"]
    }
  }
}
```

Adjust `-d ubuntu` (find your exact distro name with `wsl -l -v` in PowerShell), `-u <user>`, and the path to match your setup. The `bash -lc` login shell is what puts `uv` on `PATH`. To sanity-check before restarting Claude Desktop, run this in PowerShell — it should print the repo path and a path to `uv`:

```powershell
wsl.exe -d ubuntu -u noob_master -e bash -lc "cd /home/noob_master/reader3 && pwd && which uv"
```

## License

MIT