"""Tool functions for the Movie Watchlist MCP server."""

import logging

from coolname import generate_slug
from mcp.server.fastmcp import Context
from mcp.types import SamplingMessage, TextContent
from pydantic import BaseModel, Field
from sqlalchemy.future import select

from mcp_server_watchlist.db import (
    Watchlist,
    WatchlistItem,
    get_session,
    get_watchlist_id,
)
from mcp_server_watchlist.resources import get_all_movies

logger = logging.getLogger(__name__)

DB_ERROR_MESSAGE = "Database is currently unavailable. Please try again later."


async def create_watchlist() -> str:
    """
    Create a new watchlist with a randomly generated coolname.

    Note:
        Returns the generated coolname (e.g. 'silly-orange-duck') to use in other tools.
    """
    session = await get_session()
    try:
        while True:
            coolname = generate_slug()
            existing_id = await get_watchlist_id(session, coolname)
            if not existing_id:
                break
        new_watchlist = Watchlist(coolname=coolname)
        try:
            session.add(new_watchlist)
            await session.commit()
        except Exception:
            await session.rollback()
            return DB_ERROR_MESSAGE
        return coolname
    finally:
        await session.close()


def _build_watchlist_overview(movies: list[str]) -> str:
    """
    Build watchlist text for the non-sampling summary variant.

    Args:
        movies: List of formatted movie entries.

    Note:
        This helper is used by summarize_watchlist_without_sampling.
    """
    movie_lines = "\n".join(f"- {movie}" for movie in movies)

    return (
        "[Watchlist Summary]\n\n"
        "Sampling is disabled or unavailable. Here is your watchlist:\n"
        f"{movie_lines}"
    )


async def show_watchlist(watchlist_key: str) -> list[str]:
    """
    Return the current watchlist as a plain list of formatted movie entries.

    Args:
        watchlist_key: The watchlist identifier.

    Note:
        This tool returns data directly without LLM summarization.
    """
    return await get_all_movies(watchlist_key)


async def summarize_watchlist_with_sampling(watchlist_key: str, ctx: Context) -> str:
    """
    Summarize a watchlist using LLM sampling.

    Args:
        watchlist_key: The watchlist identifier.
        ctx: MCP context used to call the sampling API.

    Note:
        This variant is registered only when sampling is enabled.
    """
    movies = await get_all_movies(watchlist_key)
    if not movies or movies == [f"Watchlist not found: '{watchlist_key}'."]:
        if not movies:
            return f"Watchlist '{watchlist_key}' is empty. Add some movies to get a summary!"
        return movies[0]

    movie_list = "\n".join(movies)
    prompt = (
        "Here is a user's movie watchlist. "
        "Write a friendly summary or insight about their watchlist. "
        "You may mention genres, years, or trends if you notice any.\n\n"
        f"Watchlist:\n{movie_list}"
    )
    # Use LLM sampling
    message_result = await ctx.session.create_message(
        messages=[
            SamplingMessage(
                role="user",
                content=TextContent(type="text", text=prompt),
            )
        ],
        system_prompt="You are a helpful movie assistant.",
        max_tokens=100,
    )
    if message_result.content.type == "text":
        return f"[Watchlist Summary]\n\n{message_result.content.text}"
    return f"[Watchlist Summary]\n\n{str(message_result.content)}"


async def summarize_watchlist_without_sampling(watchlist_key: str) -> str:
    """
    Return a deterministic watchlist overview without MCP context.

    Args:
        watchlist_key: The watchlist identifier.

    Note:
        This variant is registered only when LLM sampling is disabled.
    """
    movies = await get_all_movies(watchlist_key)
    if not movies:
        return (
            f"Watchlist '{watchlist_key}' is empty. Add some movies to get a summary!"
        )
    if movies == [f"Watchlist not found: '{watchlist_key}'."]:
        return movies[0]
    return _build_watchlist_overview(movies)


class RatingInput(BaseModel):
    """
    Schema for elicited rating input.

    Note:
        Rating must be between 0 and 10.
    """

    rating: float = Field(ge=0, le=10, description="Rate the movie out of 10")


async def add_movie(watchlist_key: str, title: str, year: int) -> str:
    """
    Add a movie to a named watchlist.

    Args:
        watchlist_key: The watchlist identifier.
        title: Movie name (exclude year).
        year: Year of release.

    Note:
        New movies are added as unwatched with rating set to N/A.
    """
    session = await get_session()
    try:
        watchlist_id = await get_watchlist_id(session, watchlist_key)
        if watchlist_id is None:
            return f"Watchlist not found: '{watchlist_key}'. Use create_watchlist to create it first."
        new_movie = WatchlistItem(
            watchlist_id=watchlist_id, title=title, year=year, watched=0, rating=None
        )
        try:
            session.add(new_movie)
            await session.commit()
        except Exception:
            await session.rollback()
            return DB_ERROR_MESSAGE
        return (
            f"Added: Title: {title}, Year: {year}, "
            f"Rating: N/A to watchlist '{watchlist_key}'."
        )
    finally:
        await session.close()


async def _mark_watched_with_rating(
    watchlist_key: str, title: str, rating: float | None
) -> str:
    """
    Internal helper to mark watched and persist an optional rating.

    Args:
        watchlist_key: The watchlist identifier.
        title: Movie name (exclude year).
        rating: Rating value or None.

    Note:
        This helper is shared by elicitation and direct-rating tool variants.
    """
    session = await get_session()
    try:
        watchlist_id = await get_watchlist_id(session, watchlist_key)
        if watchlist_id is None:
            return f"Watchlist not found: '{watchlist_key}'."
        result = await session.execute(
            select(WatchlistItem).filter_by(watchlist_id=watchlist_id, title=title)
        )
        movie = result.scalars().first()
        if not movie:
            return f"Movie not found in watchlist: Title: {title}"
        movie.watched = 1
        movie.rating = rating
        try:
            await session.commit()
        except Exception:
            await session.rollback()
            return DB_ERROR_MESSAGE
        year = movie.year
        return (
            f"Marked as watched: Title: {title}, Year: {year}, "
            f"Rating: {rating if rating is not None else 'N/A'}"
        )
    finally:
        await session.close()


async def mark_watched_with_elicitation(
    watchlist_key: str, title: str, ctx: Context
) -> str:
    """
    Mark watched and collect rating through MCP elicitation.

    Args:
        watchlist_key: The watchlist identifier.
        title: Movie name (exclude year).
        ctx: MCP context used to elicit rating input.

    Note:
        This variant is registered only when elicitation is enabled and
        does not accept rating as a direct tool argument.
    """
    session = await get_session()
    try:
        watchlist_id = await get_watchlist_id(session, watchlist_key)
        if watchlist_id is None:
            return f"Watchlist not found: '{watchlist_key}'."
        result = await session.execute(
            select(WatchlistItem).filter_by(watchlist_id=watchlist_id, title=title)
        )
        movie = result.scalars().first()
        if not movie:
            return f"Movie not found in watchlist: Title: {title}"

        # Elicit rating (don't hold DB session during long-running elicit call)
        rating = None
        result_elicit = await ctx.elicit(
            "Great! Please provide your rating.", RatingInput
        )
        if getattr(result_elicit, "action", None) == "accept" and getattr(
            result_elicit, "data", None
        ):
            accepted_rating = getattr(result_elicit.data, "rating", None)
            if accepted_rating is not None:
                rating = accepted_rating

        # Mark as watched with the collected rating
        movie.watched = 1
        movie.rating = rating
        try:
            await session.commit()
        except Exception:
            await session.rollback()
            return DB_ERROR_MESSAGE
        year = movie.year
        return (
            f"Marked as watched: Title: {title}, Year: {year}, "
            f"Rating: {rating if rating is not None else 'N/A'}"
        )
    finally:
        await session.close()


async def mark_watched_with_rating(
    watchlist_key: str, title: str, rating: float
) -> str:
    """
    Mark watched using direct rating input.

    Args:
        watchlist_key: The watchlist identifier.
        title: Movie name (exclude year).
        rating: Rating value from 0 to 10.

    Note:
        This variant is registered only when elicitation is disabled.
    """
    return await _mark_watched_with_rating(watchlist_key, title, rating)


async def unwatch_movie(watchlist_key: str, title: str) -> str:
    """
    Mark a movie as unwatched.

    Args:
        watchlist_key: The watchlist identifier.
        title: Movie name (exclude year).

    Note:
        Pass only the movie name, not including the year. If the year is
        present, remove it before calling.
    """
    session = await get_session()
    try:
        watchlist_id = await get_watchlist_id(session, watchlist_key)
        if watchlist_id is None:
            return f"Watchlist not found: '{watchlist_key}'."
        result = await session.execute(
            select(WatchlistItem).filter_by(watchlist_id=watchlist_id, title=title)
        )
        movie = result.scalars().first()
        if not movie:
            return f"Movie not found in watchlist: Title: {title}"
        movie.watched = 0
        movie.rating = None
        try:
            await session.commit()
        except Exception:
            await session.rollback()
            return DB_ERROR_MESSAGE
        year = movie.year
        rating = "N/A"
        return f"Marked as unwatched: Title: {title}, Year: {year}, Rating: {rating}"
    finally:
        await session.close()


async def delete_movie(watchlist_key: str, title: str) -> str:
    """
    Delete a movie from a named watchlist.

    Args:
        watchlist_key: The watchlist identifier.
        title: Movie name (exclude year).

    Note:
        Pass only the movie name, not including the year. If the year is
        present, remove it before calling.
    """
    session = await get_session()
    try:
        watchlist_id = await get_watchlist_id(session, watchlist_key)
        if watchlist_id is None:
            return f"Watchlist not found: '{watchlist_key}'."
        result = await session.execute(
            select(WatchlistItem).filter_by(watchlist_id=watchlist_id, title=title)
        )
        movie = result.scalars().first()
        if not movie:
            return f"Movie not found in watchlist: Title: {title}"
        year = movie.year
        rating = movie.rating if movie.rating is not None else "N/A"
        try:
            await session.delete(movie)
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception("Database write failed (delete_movie)")
            return DB_ERROR_MESSAGE
        return (
            f"Deleted: Title: {title}, Year: {year}, "
            f"Rating: {rating} from watchlist '{watchlist_key}'."
        )
    finally:
        await session.close()
