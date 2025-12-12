# MCP server setup and registration
from mcp.server.fastmcp import FastMCP
from mcp_server_watchlist.db import init_db
from mcp_server_watchlist.tools import add_movie, mark_watched, unwatch_movie, delete_movie
from mcp_server_watchlist.resources import get_movie, get_all_movies, get_unwatched_movies, get_watched_movies
from mcp_server_watchlist.prompts import prompt_add_movie, prompt_unwatch_movie, prompt_delete_movie, prompt_mark_watched

mcp = FastMCP("Movie Watchlist MCP Server")

init_db()

# Register tool functions
mcp.tool()(add_movie)
mcp.tool()(mark_watched)
mcp.tool()(unwatch_movie)
mcp.tool()(delete_movie)

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
	mcp.run()

if __name__ == "__main__":
	main()
