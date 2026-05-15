
"""MCP server setup and registration for the Movie Watchlist MCP Server."""

import os
import asyncio
import uvicorn
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Route

from mcp.server.fastmcp import FastMCP
from mcp_server_watchlist.db import init_db
from mcp_server_watchlist.templates import get_health_html
from mcp_server_watchlist.prompts import (
    prompt_add_movie, prompt_unwatch_movie, prompt_delete_movie, prompt_mark_watched, prompt_show_watchlist
)
from mcp_server_watchlist.resources import (
	get_movie, get_all_movies, get_unwatched_movies, get_watched_movies
)
from mcp_server_watchlist.tools import (
    add_movie, mark_watched, unwatch_movie, delete_movie, summarize_watchlist, show_watchlist
)

# Get host and port from environment variables, fallback to defaults
HOST = str(os.environ.get("HOST", "127.0.0.1"))
PORT = int(os.environ.get("PORT", 8000))
mcp = FastMCP("Movie Watchlist MCP Server", host=HOST, port=PORT)

def setup_server():
    """Initialize the server, database, and register all tools, resources, and prompts."""
    # Ensure async DB initialization
    asyncio.run(init_db())

    # Register tool functions
    mcp.tool()(add_movie)
    mcp.tool()(show_watchlist)
    mcp.tool()(mark_watched)
    mcp.tool()(unwatch_movie)
    mcp.tool()(delete_movie)
    mcp.tool()(summarize_watchlist)

    # Register resource functions
    mcp.resource("watchlist://{title}")(get_movie)
    mcp.resource("watchlist://all")(get_all_movies)
    mcp.resource("watchlist://unwatched")(get_unwatched_movies)
    mcp.resource("watchlist://watched")(get_watched_movies)

    # Register prompt functions
    mcp.prompt()(prompt_add_movie)
    mcp.prompt()(prompt_unwatch_movie)
    mcp.prompt()(prompt_delete_movie)
    mcp.prompt()(prompt_mark_watched)
    mcp.prompt()(prompt_show_watchlist)


def get_health_data():
    """Return health check data."""
    return {
        "status": "healthy",
        "service": "Movie Watchlist MCP Server",
        "tools": [
            "tools/show_watchlist",
            "tools/add_movie",
            "tools/mark_watched",
            "tools/unwatch_movie",
            "tools/delete_movie",
            "tools/summarize_watchlist",
        ],
        "prompts": [
            "prompts/prompt_add_movie",
            "prompts/prompt_unwatch_movie",
            "prompts/prompt_delete_movie",
            "prompts/prompt_mark_watched",
            "prompts/prompt_show_watchlist",
        ],
        "resources": [
            "resources/watchlist://{title}",
            "resources/watchlist://all",
            "resources/watchlist://unwatched",
            "resources/watchlist://watched",
        ],
    }


async def health_handler(request):
    """Handle health check requests (returns HTML)."""
    data = get_health_data()
    return HTMLResponse(get_health_html(data))


async def health_json_handler(request):
    """Handle health check API requests (returns JSON)."""
    return JSONResponse(get_health_data())


def build_http_app():
    """Build the ASGI app and add CORS support for browser-based MCP clients."""
    app = mcp.streamable_http_app()

    # Add health check routes
    app.router.routes.append(Route("/health", health_handler, methods=["GET"]))
    app.router.routes.append(Route("/health/json", health_json_handler, methods=["GET"]))

    allow_origins_raw = os.environ.get("CORS_ALLOW_ORIGINS", "*")
    allow_origins = [origin.strip() for origin in allow_origins_raw.split(",") if origin.strip()]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["mcp-session-id"],
        max_age=600,
    )
    return app

def main():
    """Entry point for running the MCP server."""
    setup_server()
    app = build_http_app()
    uvicorn.run(app, host=HOST, port=PORT)

if __name__ == "__main__":
    main()
