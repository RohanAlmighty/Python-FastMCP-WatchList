# Watchlist MCP Server

This project implements a Movie Watchlist Model Context Protocol (MCP) server using [FastMCP](https://github.com/modelcontext/fastmcp).

## Features

- **Tools:**
	- `add_movie(title: str, year: int)` — Add a movie to the watchlist.
	- `mark_watched(title: str)` — Mark a movie as watched.
	- `unwatch_movie(title: str)` — Mark a movie as unwatched.
	- `delete_movie(title: str)` — Delete a movie from the watchlist.
- **Resources:**
	- `watchlist://{title}` — Get details of a movie by title.
	- `watchlist://all` — Get all movies in the watchlist.
	- `watchlist://unwatched` — Get all unwatched movies.
	- `watchlist://watched` — Get all watched movies.
- **Prompts:**
	- `prompt_add_movie(title: str, year: int)` — Prompt to add a movie.
	- `prompt_unwatch_movie(title: str)` — Prompt to mark a movie as unwatched.
	- `prompt_delete_movie(title: str)` — Prompt to delete a movie.
	- `prompt_mark_watched(title: str)` — Prompt to mark a movie as watched.

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
Or see the [uv docs](https://docs.astral.sh/uv/) for other platforms.

### 2. Install dependencies

To install dependencies (from `pyproject.toml`, `uv.lock`, or `requirements.txt`), simply run:
```bash
uv sync
```

### 3. Run the server

To start the server in development mode (with hot reload):
```bash
uv run mcp dev watchlist_mcp_server/server.py
```

Or to run the installed script (if registered in `pyproject.toml`):
```bash
uv run watchlist-mcp-server
```

## Endpoints & Testing

You can test your MCP server using the **MCP Inspector**. MCP Inspector provides a web interface for interacting with your tools, resources, and prompts.

### How to use MCP Inspector

1. Start the server in development mode:
	```bash
	uv run mcp dev watchlist_mcp_server/server.py
	```
2. When the server starts, it will print a link to the MCP Inspector (e.g., `http://localhost:6274`). Open this link in your browser.
3. Use the Inspector UI to invoke tools, resources, and prompts interactively. You can enter parameters and view results directly in the browser.
