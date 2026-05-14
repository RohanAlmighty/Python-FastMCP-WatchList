
# Watchlist MCP Server

Lights, camera, automation.

This project implements a Movie Watchlist Model Context Protocol (MCP) server using [FastMCP](https://github.com/modelcontext/fastmcp). It gives you a clean way to manage a movie watchlist, including marking movies watched/unwatched, adding ratings, retrieving list views, and generating LLM-powered summaries.

## Demo Recording

Watch the project in action:

[![Demo Video](https://img.youtube.com/vi/zMOPd2BnTOY/0.jpg)](https://www.youtube.com/watch?v=zMOPd2BnTOY)

## Features

### LLM Sampling

Generate friendly, AI-powered summaries of your watchlist. The `summarize_watchlist` tool uses LLM sampling to send your movie list to a language model and returns a brief, insightful summary. It can highlight genres, trends, or fun patterns in your collection.

### Elicitation

Collect extra input when needed. Example: when marking a movie as watched, the server can prompt the user for a rating (out of 10) using an elicitation flow. This behavior is showcased in `mark_watched`.

### Database Schema

Each movie includes:

- `title` (`str`)
- `year` (`int`)
- `watched` (`bool`)
- `rating` (`float`, optional, out of 10)

### Database Connectivity

- Default database: local SQLite (`watchlist.db`)
- Remote databases supported via `DATABASE_URL`
- Supported URL styles:
  - `postgresql://user:[REDACTED_SQL_PASSWORD_1]@host:5432/dbname`
  - `mysql://user:[REDACTED_SQL_PASSWORD_1]@host:3306/dbname`
  - `sqlite:///absolute/or/relative/path.db`

### Tools

- `show_watchlist()` - Return all watchlist entries as formatted rows.
- `add_movie(title: str, year: int)` - Add a movie to the watchlist.
- `mark_watched(title: str)` - Mark a movie as watched (elicits a rating from the user).
- `unwatch_movie(title: str)` - Mark a movie as unwatched (removes rating).
- `delete_movie(title: str)` - Delete a movie from the watchlist.
- `summarize_watchlist()` - Get a friendly, LLM-generated summary of your watchlist (uses LLM sampling).

### Resources

- `watchlist://{title}` - Get details of a movie by title.
- `watchlist://all` - Get all movies in the watchlist.
- `watchlist://unwatched` - Get all unwatched movies.
- `watchlist://watched` - Get all watched movies.

### Prompts

- `prompt_add_movie(title: str, year: int)` - Prompt to add a movie.
- `prompt_unwatch_movie(title: str)` - Prompt to mark a movie as unwatched.
- `prompt_delete_movie(title: str)` - Prompt to delete a movie.
- `prompt_mark_watched(title: str)` - Prompt to mark a movie as watched.

All tools and resources return formatted strings with title, year, watched status, and rating (if available). Elicitation is used where additional user input is required.

## Requirements

- Python: 3.12 or newer (see `pyproject.toml`)
- Node.js: required for MCP Inspector (via `npx`). [Download Node.js](https://nodejs.org/)
- MCP CLI: installed automatically as a dependency (`mcp[cli]` in `pyproject.toml`)

## Getting Started

### 1. Install [uv](https://docs.astral.sh/uv/)

macOS:

```bash
brew install uv
```

Windows:

```bash
winget install --id=astral-sh.uv -e
```

For other platforms, see the [uv docs](https://docs.astral.sh/uv/).

### 2. Install dependencies

Install dependencies from `pyproject.toml`, `uv.lock`, or `requirements.txt`:

```bash
uv sync
```

### 3. Install package in editable mode

```bash
uv pip install -e .
```

### 4. Install/refresh the CLI tool from local source

If you are developing locally, install the CLI from this repo. Use `--force --no-cache` to ensure the installed tool always reflects your latest local code (bypasses uv's build cache):

```bash
uv tool install --force --no-cache .
```

### 5. Run the server locally

Run via module:

```bash
python -m mcp_server_watchlist.server
```

Or run via script entry point (from `pyproject.toml`):

```bash
mcp-server-watchlist
```

To use a remote SQL database, set `DATABASE_URL` before starting:

```bash
export DATABASE_URL="postgresql://username:[REDACTED_SQL_PASSWORD_1]word@db-host:5432/watchlist"
mcp-server-watchlist
```

### 6. Open MCP Inspector

In a separate terminal:

```bash
npx @modelcontextprotocol/inspector
```

Note: Inspector requires Node.js. See [MCP Inspector documentation](https://github.com/modelcontext/inspector).

## Endpoints and Testing

Use **MCP Inspector** as a web interface for interacting with tools, resources, and prompts.

How to use MCP Inspector:

1. Start your server and the Inspector (see Getting Started).
2. Open the Inspector UI (usually http://localhost:6274) and invoke tools, resources, and prompts interactively.

---

## Sample VS Code MCP User Config

Depending on your setup, use one of the following in VS Code user/workspace settings.

### 1. Local setup (run your own server)

Follow all steps in Getting Started, then use:

```jsonc
{
  "servers": {
    "mcp-server-watchlist-local": {
      "url": "http://127.0.0.1:8000/mcp/",
      "type": "http"
    }
  },
  "inputs": []
}
```

### 2. Direct use (hosted server, no setup required)

Use this config to connect to the hosted server:

```jsonc
{
  "servers": {
    "mcp-server-watchlist-remote": {
      "url": "https://python-fastmcp-watchlist.onrender.com/mcp/",
      "type": "http"
    }
  },
  "inputs": []
}
```

Use only the relevant config based on whether you want local or hosted usage.

---

## Troubleshooting and FAQ

### CLI Tool Installation and Usage

You can install the `mcp-server-watchlist` CLI globally using [uv](https://github.com/astral-sh/uv).

#### Install from local source (development)

If you are working locally and want the current development version:

```bash
uv tool install --force .
```

This installs from your local directory and refreshes the installed tool to include your latest changes.

#### Install globally (from PyPI, when published)

Once published:

```bash
uv tool install mcp-server-watchlist
# or for user only:
uv tool install --user mcp-server-watchlist
```

After installation:

```bash
mcp-server-watchlist
```

### Setting the database URL

Set `DATABASE_URL` before running the tool:

```bash
# Use SQLite (default, relative to current directory)
export DATABASE_URL="sqlite:///watchlist.db"
mcp-server-watchlist

# Use a specific absolute path for SQLite
export DATABASE_URL="sqlite:////absolute/path/to/watchlist.db"
mcp-server-watchlist

# Use PostgreSQL
export DATABASE_URL="postgresql://user:[REDACTED_SQL_PASSWORD_1]word@host:5432/dbname"
mcp-server-watchlist

# Use MySQL
export DATABASE_URL="mysql://user:[REDACTED_SQL_PASSWORD_1]word@host:3306/dbname"
mcp-server-watchlist
```

Tip:

If you want to always use the `watchlist.db` file in your repo directory, set `DATABASE_URL` to its absolute path.

```bash
export DATABASE_URL="sqlite:////absolute/path/to/your/repo/watchlist.db"
mcp-server-watchlist
```

One-liner variant:

```bash
DATABASE_URL="sqlite:////absolute/path/to/your/repo/watchlist.db" mcp-server-watchlist
```

This ensures the same DB file is used regardless of where you run the command from.

Windows note:

On Windows, use three slashes for absolute paths (example: `sqlite:///C:/path/to/watchlist.db`). Using four slashes may cause issues with `aiosqlite`. In PowerShell:

```powershell
$env:DATABASE_URL = "sqlite:///C:/path/to/watchlist.db"
```

If `DATABASE_URL` is not set, the tool defaults to a local SQLite file named `watchlist.db` in the current directory.

### Re-resolving dependencies safely

If you need to re-resolve dependencies (for example after editing `pyproject.toml`):

```bash
uv lock
uv sync
```

This updates `uv.lock` and `.venv` to latest compatible versions.

You do not need to re-run `uv tool install` after re-resolving dependencies unless you want to upgrade or refresh the installed tool.

### Common Issues

- New tools or prompts not showing in MCP Inspector after code changes: `mcp-server-watchlist` is a snapshot at install time. Reinstall from project root:

  ```bash
  uv tool install --force .
  ```

- Inspector will not start: verify Node.js is installed and on PATH with `node -v` and `npx -v`.
- Port 8000 already in use: stop the process using port 8000 or change the server port.
- Inspector UI not opening: verify Inspector is running and open http://localhost:6274.
- Python version issues: use Python 3.12+ (required by `pyproject.toml`). Check with `python --version`.

For more help, see [FastMCP documentation](https://github.com/modelcontext/fastmcp) or open an issue in this repository.

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
