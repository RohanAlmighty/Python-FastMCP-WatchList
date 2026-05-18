"""Resource functions for the Movie Watchlist MCP server."""

import urllib.parse
from typing import List

from sqlalchemy.future import select

from mcp_server_watchlist import db
from mcp_server_watchlist.db import WatchlistItem, get_session


async def get_movie(watchlist_key: str, title: str) -> str:
    """
    Get details of a movie from a named watchlist.

    Args:
        watchlist_key: The watchlist identifier.
        title: Movie name (URL-encoded).

    Note:
        Returns movie details if found, otherwise returns error message.
    """
    session = await get_session()
    try:
        watchlist_id = await db.get_watchlist_id(session, watchlist_key)
        if watchlist_id is None:
            return f"Watchlist not found: '{watchlist_key}'."
        decoded_title = urllib.parse.unquote(title)
        result = await session.execute(
            select(WatchlistItem).filter_by(
                watchlist_id=watchlist_id, title=decoded_title
            )
        )
        row = result.scalars().first()
        if row:
            return format_movie_row((row.title, row.year, row.watched, row.rating))
        return "Movie not found in watchlist."
    finally:
        await session.rollback()
        await session.close()


async def get_all_movies(watchlist_key: str) -> List[str]:
    """
    Get all movies in a named watchlist.

    Args:
        watchlist_key: The watchlist identifier.

    Note:
        Returns list of formatted movie entries or error message.
    """
    session = await get_session()
    try:
        watchlist_id = await db.get_watchlist_id(session, watchlist_key)
        if watchlist_id is None:
            return [f"Watchlist not found: '{watchlist_key}'."]
        result = await session.execute(
            select(WatchlistItem).filter_by(watchlist_id=watchlist_id)
        )
        rows = result.scalars().all()
        return [
            format_movie_row((row.title, row.year, row.watched, row.rating))
            for row in rows
        ]
    finally:
        await session.rollback()
        await session.close()


async def get_unwatched_movies(watchlist_key: str) -> List[str]:
    """
    Get all unwatched movies in a named watchlist.

    Args:
        watchlist_key: The watchlist identifier.

    Note:
        Returns list of unwatched movie entries or error message.
    """
    session = await get_session()
    try:
        watchlist_id = await db.get_watchlist_id(session, watchlist_key)
        if watchlist_id is None:
            return [f"Watchlist not found: '{watchlist_key}'."]
        result = await session.execute(
            select(WatchlistItem).filter_by(watchlist_id=watchlist_id, watched=0)
        )
        rows = result.scalars().all()
        return [
            format_movie_row((row.title, row.year, row.watched, row.rating))
            for row in rows
        ]
    finally:
        await session.rollback()
        await session.close()


async def get_watched_movies(watchlist_key: str) -> List[str]:
    """
    Get all watched movies in a named watchlist.

    Args:
        watchlist_key: The watchlist identifier.

    Note:
        Returns list of watched movie entries or error message.
    """
    session = await get_session()
    try:
        watchlist_id = await db.get_watchlist_id(session, watchlist_key)
        if watchlist_id is None:
            return [f"Watchlist not found: '{watchlist_key}'."]
        result = await session.execute(
            select(WatchlistItem).filter_by(watchlist_id=watchlist_id, watched=1)
        )
        rows = result.scalars().all()
        return [
            format_movie_row((row.title, row.year, row.watched, row.rating))
            for row in rows
        ]
    finally:
        await session.rollback()
        await session.close()


def format_movie_row(row) -> str:
    """
    Format a movie row as 'Title: abc, Year: xxxx, Watched: Yes/No, Rating: x'.

    Args:
        row: Tuple of (title, year, watched, rating).

    Note:
        Converts watched (0/1) to Yes/No and None ratings to N/A.
    """
    watched = "Yes" if row[2] else "No"
    rating = row[3] if row[3] is not None else "N/A"
    return f"Title: {row[0]}, Year: {row[1]}, Watched: {watched}, Rating: {rating}"
