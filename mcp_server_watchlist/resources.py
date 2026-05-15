
"""Resource functions for the Movie Watchlist MCP server."""

# Resource functions
import urllib.parse
from typing import List
from mcp_server_watchlist import db

async def get_movie(watchlist_key: str, title: str) -> str:
    """Get details of a movie from a named watchlist."""
    watchlist_id = await db.get_watchlist_id(watchlist_key)
    if watchlist_id is None:
        return f"Watchlist not found: '{watchlist_key}'."
    decoded_title = urllib.parse.unquote(title)
    row = await db.fetch_one(
        "SELECT title, year, watched, rating FROM watchlist "
        "WHERE watchlist_id = :wid AND title = :title",
        {"wid": watchlist_id, "title": decoded_title},
    )
    if row:
        return format_movie_row(row)
    return "Movie not found in watchlist."

async def get_all_movies(watchlist_key: str) -> List[str]:
    """Get all movies in a named watchlist."""
    watchlist_id = await db.get_watchlist_id(watchlist_key)
    if watchlist_id is None:
        return [f"Watchlist not found: '{watchlist_key}'."]
    rows = await db.fetch_all(
        "SELECT title, year, watched, rating FROM watchlist WHERE watchlist_id = :wid",
        {"wid": watchlist_id},
    )
    return [format_movie_row(row) for row in rows]

async def get_unwatched_movies(watchlist_key: str) -> List[str]:
    """Get all unwatched movies in a named watchlist."""
    watchlist_id = await db.get_watchlist_id(watchlist_key)
    if watchlist_id is None:
        return [f"Watchlist not found: '{watchlist_key}'."]
    rows = await db.fetch_all(
        "SELECT title, year, watched, rating FROM watchlist "
        "WHERE watchlist_id = :wid AND watched = 0",
        {"wid": watchlist_id},
    )
    return [format_movie_row(row) for row in rows]

async def get_watched_movies(watchlist_key: str) -> List[str]:
    """Get all watched movies in a named watchlist."""
    watchlist_id = await db.get_watchlist_id(watchlist_key)
    if watchlist_id is None:
        return [f"Watchlist not found: '{watchlist_key}'."]
    rows = await db.fetch_all(
        "SELECT title, year, watched, rating FROM watchlist "
        "WHERE watchlist_id = :wid AND watched = 1",
        {"wid": watchlist_id},
    )
    return [format_movie_row(row) for row in rows]

def format_movie_row(row) -> str:
    """Format a movie row as 'Title: abc, Year: xxxx, Watched: Yes/No, Rating: x'."""
    watched = "Yes" if row[2] else "No"
    rating = row[3] if row[3] is not None else "N/A"
    return f"Title: {row[0]}, Year: {row[1]}, Watched: {watched}, Rating: {rating}"
