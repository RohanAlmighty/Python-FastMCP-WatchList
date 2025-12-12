
# MCP server setup and registration
import asyncio
from mcp.server.fastmcp import FastMCP
from db import init_db
from tools import (
	add_movie, mark_watched, unwatch_movie, delete_movie, summarize_watchlist
)
from resources import (
	get_movie, get_all_movies, get_unwatched_movies, get_watched_movies
)
from prompts import (
	prompt_add_movie, prompt_unwatch_movie, prompt_delete_movie, prompt_mark_watched
)

mcp = FastMCP("Movie Watchlist MCP Server", port=8000)



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
	async def startup():
		await init_db()
		mcp.run(transport="streamable-http")
	asyncio.run(startup())

if __name__ == "__main__":
	main()
