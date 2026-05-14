
"""Resource functions for the Movie Watchlist MCP server."""

# Resource functions
import urllib.parse
from typing import List
from mcp_server_watchlist import db

async def get_movie(title: str) -> str:
    """Get details of a movie from the watchlist."""
    decoded_title = urllib.parse.unquote(title)
    row = await db.fetch_one(
        "SELECT title, year, watched, rating FROM watchlist WHERE title = :title",
        {"title": decoded_title},
    )
    if row:
        return format_movie_row(row)
    return "Movie not found in watchlist."

async def get_all_movies() -> List[str]:
    """Get all movies in the watchlist."""
    rows = await db.fetch_all("SELECT title, year, watched, rating FROM watchlist")
    return [format_movie_row(row) for row in rows]

async def get_unwatched_movies() -> List[str]:
    """Get all unwatched movies in the watchlist."""
    rows = await db.fetch_all(
        "SELECT title, year, watched, rating FROM watchlist WHERE watched = 0"
    )
    return [format_movie_row(row) for row in rows]

async def get_watched_movies() -> List[str]:
    """Get all watched movies in the watchlist."""
    rows = await db.fetch_all(
        "SELECT title, year, watched, rating FROM watchlist WHERE watched = 1"
    )
    return [format_movie_row(row) for row in rows]

def format_movie_row(row) -> str:
    """Format a movie row as 'Title: abc, Year: xxxx, Watched: Yes/No, Rating: x'."""
    watched = "Yes" if row[2] else "No"
    rating = row[3] if row[3] is not None else "N/A"
    return f"Title: {row[0]}, Year: {row[1]}, Watched: {watched}, Rating: {rating}"
