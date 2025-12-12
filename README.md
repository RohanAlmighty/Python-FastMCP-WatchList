# Watchlist MCP Server


This project implements a Movie Watchlist Model Context Protocol (MCP) server using [FastMCP](https://github.com/modelcontext/fastmcp). It provides a simple API to manage a movie watchlist, including marking movies as watched/unwatched, adding ratings, and retrieving lists of movies.



## Elicitation

**Elicitation** is used in this server to collect additional information from the user when required. For example, when marking a movie as watched, the server will prompt the user to provide a rating for the movie (out of 10) using an elicitation flow. This ensures that user input is gathered interactively and only when needed.

Elicitation is handled automatically by the MCP server and is highlighted in the `mark_watched` tool, which will ask the user for a rating before updating the movie's status.

---

## Features

- **Database Schema:**
	- Each movie has: `title` (str), `year` (int), `watched` (bool), and `rating` (float, optional, out of 10).

- **Tools:**
	- `add_movie(title: str, year: int)` — Add a movie to the watchlist.
	- `mark_watched(title: str)` — Mark a movie as watched. (**Uses elicitation to prompt the user for a rating.**)
	- `unwatch_movie(title: str)` — Mark a movie as unwatched (removes rating).
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


All tools and resources return formatted strings with the movie's title, year, watched status, and rating (if available). Elicitation is used where additional user input is required, such as collecting a rating when marking a movie as watched.

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


### 3. Install the package in editable mode

Before running the server in development mode, install the package in editable mode:
```bash
uv pip install -e .
```


### 4. Run the server

To start the server in development mode (with hot reload):
```bash
uv run mcp dev mcp_server_watchlist/server.py
```

Or to run the installed script (if registered in `pyproject.toml`):
```bash
uv run mcp-server-watchlist
```

## Endpoints & Testing

You can test your MCP server using the **MCP Inspector**. MCP Inspector provides a web interface for interacting with your tools, resources, and prompts.

### How to use MCP Inspector


1. Start the server in development mode:
   ```bash
   uv run mcp dev mcp_server_watchlist/server.py
   ```
2. When the server starts, it will print a link to the MCP Inspector (e.g., `http://localhost:6274`). Open this link in your browser.
3. Use the Inspector UI to invoke tools, resources, and prompts interactively. You can enter parameters and view results directly in the browser.
