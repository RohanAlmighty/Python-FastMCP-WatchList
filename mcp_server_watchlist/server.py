
"""MCP server setup and registration for the Movie Watchlist MCP Server."""

import os
import asyncio
import logging
import uvicorn
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Route

from mcp.server.fastmcp import FastMCP
from mcp_server_watchlist.db import check_database_connection, init_db
from mcp_server_watchlist.templates import get_health_html
from mcp_server_watchlist.prompts import (
    prompt_add_movie, prompt_unwatch_movie, prompt_delete_movie, prompt_mark_watched, prompt_show_watchlist
)
from mcp_server_watchlist.resources import (
	get_movie, get_all_movies, get_unwatched_movies, get_watched_movies
)
from mcp_server_watchlist.tools import (
    add_movie,
    create_watchlist,
    delete_movie,
    mark_watched_with_elicitation,
    mark_watched_with_rating,
    show_watchlist,
    summarize_watchlist_with_sampling,
    summarize_watchlist_without_sampling,
    unwatch_movie,
)

# Get host and port from environment variables, fallback to defaults
HOST = str(os.environ.get("HOST", "127.0.0.1"))
PORT = int(os.environ.get("PORT", 8000))
mcp = FastMCP("Movie Watchlist MCP Server", host=HOST, port=PORT)
logger = logging.getLogger(__name__)


def _is_enabled(env_var: str, default: str = "true") -> bool:
    """Read a boolean feature flag from environment variables."""
    raw = os.environ.get(env_var, default).strip().lower()
    return raw in {"1", "true", "yes", "y", "on"}

def setup_server():
    """Initialize the server, database, and register all tools, resources, and prompts."""
    # Ensure async DB initialization but never crash startup on DB failure.
    try:
        db_initialized = bool(asyncio.run(init_db()))
        if not db_initialized:
            logger.warning("Database initialization failed; server will continue in degraded mode")
    except Exception:
        logger.exception("Database initialization crashed unexpectedly")

    # Register tool functions
    mcp.tool()(create_watchlist)
    mcp.tool()(add_movie)
    mcp.tool()(show_watchlist)
    mcp.tool()(unwatch_movie)
    mcp.tool()(delete_movie)

    # Resolve mark_watched tool schema at startup so clients/LLMs see one mode.
    if _is_enabled("ENABLE_ELICITATION", "true"):
        mcp.tool(name="mark_watched")(mark_watched_with_elicitation)
    else:
        mcp.tool(name="mark_watched")(mark_watched_with_rating)

    # Resolve summarize_watchlist tool schema at startup so clients/LLMs see one mode.
    if _is_enabled("ENABLE_LLM_SAMPLING", "true"):
        mcp.tool(name="summarize_watchlist")(summarize_watchlist_with_sampling)
    else:
        mcp.tool(name="summarize_watchlist")(summarize_watchlist_without_sampling)

    # Register resource functions
    mcp.resource("watchlist://{watchlist_key}/all")(get_all_movies)
    mcp.resource("watchlist://{watchlist_key}/watched")(get_watched_movies)
    mcp.resource("watchlist://{watchlist_key}/unwatched")(get_unwatched_movies)
    mcp.resource("watchlist://{watchlist_key}/movie/{title}")(get_movie)

    # Register prompt functions
    mcp.prompt()(prompt_add_movie)
    mcp.prompt()(prompt_unwatch_movie)
    mcp.prompt()(prompt_delete_movie)
    mcp.prompt()(prompt_mark_watched)
    mcp.prompt()(prompt_show_watchlist)


def get_health_data(db_connected: bool):
    """Return health check data."""
    db_status = "Database: Connected" if db_connected else "Database: Disconnected"
    status = "healthy" if db_connected else "degraded"
    return {
        "status": status,
        "service": "Movie Watchlist MCP Server",
        "database": db_status,
        "database_connected": db_connected,
        "tools": [
            "tools/create_watchlist",
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
            "resources/watchlist://{watchlist_key}/all",
            "resources/watchlist://{watchlist_key}/watched",
            "resources/watchlist://{watchlist_key}/unwatched",
            "resources/watchlist://{watchlist_key}/movie/{title}",
        ],
    }


async def health_handler(request):
    """Handle health check requests (returns HTML)."""
    db_connected = await check_database_connection()
    data = get_health_data(db_connected=db_connected)
    return HTMLResponse(get_health_html(data))


async def health_json_handler(request):
    """Handle health check API requests (returns JSON)."""
    db_connected = await check_database_connection()
    return JSONResponse(get_health_data(db_connected=db_connected))


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
