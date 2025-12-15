
# MCP server setup and registration
import os
import asyncio

from mcp.server.fastmcp import FastMCP
from mcp_server_watchlist.db import init_db
from mcp_server_watchlist.prompts import (
	prompt_add_movie, prompt_unwatch_movie, prompt_delete_movie, prompt_mark_watched
)
from mcp_server_watchlist.resources import (
	get_movie, get_all_movies, get_unwatched_movies, get_watched_movies
)
from mcp_server_watchlist.tools import (
	add_movie, mark_watched, unwatch_movie, delete_movie, summarize_watchlist
)

# Get host and port from environment variables, fallback to defaults
host = str(os.environ.get("HOST", "127.0.0.1"))
port = int(os.environ.get("PORT", 8000))
mcp = FastMCP("Movie Watchlist MCP Server", host=host, port=port)



# Initialization and registration logic moved to a function for testability
def setup_server():
	# Ensure async DB initialization
	asyncio.run(init_db())

	# Register tool functions
	mcp.tool()(add_movie)
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

def main():
	setup_server()
	mcp.run(transport="streamable-http")

if __name__ == "__main__":
	main()
