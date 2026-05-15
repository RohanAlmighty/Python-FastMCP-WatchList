
"""Tool functions for the Movie Watchlist MCP server."""

from pydantic import BaseModel, Field
from mcp.server.fastmcp import Context
from mcp.types import SamplingMessage, TextContent
from mcp_server_watchlist.resources import get_all_movies
from mcp_server_watchlist import db


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


async def show_watchlist() -> list[str]:
    """
    Return the current watchlist as a plain list of formatted movie entries.
    Note:
        This tool returns data directly without LLM summarization.
    """
    return await get_all_movies()

async def summarize_watchlist_with_sampling(ctx: Context) -> str:
    """
    Summarize the watchlist using LLM sampling.

    Args:
        ctx: MCP context used to call the sampling API.
    Note:
        This variant is registered only when sampling is enabled.
    """
    movies = await get_all_movies()
    if not movies:
        return "Your watchlist is empty. Add some movies to get a summary!"

    movie_list = '\n'.join(movies)
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
        return (
            f"[Watchlist Summary]\n\n"
            f"{message_result.content.text}"
        )
    return (
        f"[Watchlist Summary]\n\n"
        f"{str(message_result.content)}"
    )


async def summarize_watchlist_without_sampling() -> str:
    """
    Return a deterministic watchlist overview without MCP context.
    Note:
        This variant is registered only when LLM sampling is disabled.
    """
    movies = await get_all_movies()
    if not movies:
        return "Your watchlist is empty. Add some movies to get a summary!"
    return _build_watchlist_overview(movies)

class RatingInput(BaseModel):
    """
    Schema for elicited rating input.
    Note:
        Rating must be between 0 and 10.
    """
    rating: float = Field(ge=0, le=10, description="Rate the movie out of 10")

async def add_movie(title: str, year: int) -> str:
    """
    Add a movie to the watchlist.
    Args:
        title: Movie name (exclude year)
        year: Year of release
    Note:
        New movies are added as unwatched with rating set to N/A.
    """
    await db.execute(
        "INSERT INTO watchlist (title, year) VALUES (:title, :year)",
        {"title": title, "year": year},
    )
    # New movies have no rating by default
    return (
        f"Added: Title: {title}, Year: {year}, "
        f"Rating: N/A to watchlist."
    )


async def _mark_watched_with_rating(title: str, rating: float | None) -> str:
    """
    Internal helper to mark watched and persist an optional rating.
    Args:
        title: Movie name (exclude year)
        rating: Rating value or None.
    Note:
        This helper is shared by elicitation and direct-rating tool variants.
    """
    row = await db.fetch_one(
        "SELECT year FROM watchlist WHERE title = :title",
        {"title": title},
    )
    if not row:
        return f"Movie not found in watchlist: Title: {title}"
    await db.execute(
        "UPDATE watchlist SET watched = 1, rating = :rating WHERE title = :title",
        {"rating": rating, "title": title},
    )
    year = row[0]
    return (
        f"Marked as watched: Title: {title}, Year: {year}, "
        f"Rating: {rating if rating is not None else 'N/A'}"
    )


async def mark_watched_with_elicitation(title: str, ctx: Context) -> str:
    """
    Mark watched and collect rating through MCP elicitation.

    Args:
        title: Movie name (exclude year)
        ctx: MCP context used to elicit rating input.
    Note:
        This variant is registered only when elicitation is enabled and does not accept rating as a direct tool argument.
    """
    row = await db.fetch_one(
        "SELECT year FROM watchlist WHERE title = :title",
        {"title": title},
    )
    if not row:
        return f"Movie not found in watchlist: Title: {title}"

    rating = None
    result = await ctx.elicit("Great! Please provide your rating.", RatingInput)
    if getattr(result, "action", None) == "accept" and getattr(result, "data", None):
        accepted_rating = getattr(result.data, "rating", None)
        if accepted_rating is not None:
            rating = accepted_rating
    return await _mark_watched_with_rating(title, rating)


async def mark_watched_with_rating(title: str, rating: float) -> str:
    """
    Mark watched using direct rating input.

    Args:
        title: Movie name (exclude year)
        rating: Rating value from 0 to 10.
    Note:
        This variant is registered only when elicitation is disabled.
    """
    return await _mark_watched_with_rating(title, rating)

async def unwatch_movie(title: str) -> str:
    """
    Mark a movie as unwatched.
    Args:
        title: Movie name (exclude year)
    Note:
        Pass only the movie name, not including the year. If the year is present, remove it before calling.
    """
    row = await db.fetch_one(
        "SELECT year, rating FROM watchlist WHERE title = :title",
        {"title": title},
    )
    if not row:
        return f"Movie not found in watchlist: Title: {title}"
    await db.execute(
        "UPDATE watchlist SET watched = 0, rating = NULL WHERE title = :title",
        {"title": title},
    )
    year = row[0]
    rating = row[1] if row[1] is not None else 'N/A'
    return (
        f"Marked as unwatched: Title: {title}, Year: {year}, "
        f"Rating: {rating}"
    )

async def delete_movie(title: str) -> str:
    """
    Delete a movie from the watchlist.
    Args:
        title: Movie name (exclude year)
    Note:
        Pass only the movie name, not including the year. If the year is present, remove it before calling.
    """
    row = await db.fetch_one(
        "SELECT year, rating FROM watchlist WHERE title = :title",
        {"title": title},
    )
    if not row:
        return f"Movie not found in watchlist: Title: {title}"
    await db.execute(
        "DELETE FROM watchlist WHERE title = :title",
        {"title": title},
    )
    year = row[0]
    rating = row[1] if row[1] is not None else 'N/A'
    return (
        f"Deleted: Title: {title}, Year: {year}, "
        f"Rating: {rating} from watchlist."
    )
