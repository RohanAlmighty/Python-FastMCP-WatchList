"""Tests for resources.py in mcp_server_watchlist."""

import pytest
from mcp_server_watchlist import db, resources


async def _setup_watchlist(tmp_path, watchlist_key: str = "alpha-list") -> int:
    """Initialize DB and create a watchlist row, returning its id."""
    db.DB_PATH = str(tmp_path / "test_watchlist.db")
    await db.init_db()
    await db.execute(
        "INSERT INTO watchlists (coolname) VALUES (:coolname)",
        {"coolname": watchlist_key},
    )
    row = await db.fetch_one(
        "SELECT id FROM watchlists WHERE coolname = :coolname",
        {"coolname": watchlist_key},
    )
    return row[0]


@pytest.mark.asyncio
async def test_get_movie_and_all_movies(tmp_path):
    """Test getting a movie and all movies from the database."""
    watchlist_key = "alpha-list"
    wid = await _setup_watchlist(tmp_path, watchlist_key)
    await db.execute(
        "INSERT INTO watchlist (watchlist_id, title, year, watched, rating) "
        "VALUES (:wid, :title, :year, :watched, :rating)",
        {"wid": wid, "title": "Inception", "year": 2010, "watched": 0, "rating": None},
    )
    result = await resources.get_movie(watchlist_key, "Inception")
    assert "Inception" in result
    all_movies = await resources.get_all_movies(watchlist_key)
    assert any("Inception" in m for m in all_movies)


@pytest.mark.asyncio
async def test_get_movie_not_found(tmp_path):
    """Test getting a movie that does not exist returns the correct message."""
    watchlist_key = "alpha-list"
    await _setup_watchlist(tmp_path, watchlist_key)
    result = await resources.get_movie(watchlist_key, "Nonexistent")
    assert result == "Movie not found in watchlist."


@pytest.mark.asyncio
async def test_get_movie_unknown_watchlist(tmp_path):
    """Test unknown watchlist returns watchlist-not-found response."""
    db.DB_PATH = str(tmp_path / "test_watchlist.db")
    await db.init_db()
    result = await resources.get_movie("missing-list", "Inception")
    assert "Watchlist not found" in result


@pytest.mark.asyncio
async def test_get_unwatched_and_watched_movies(tmp_path):
    """Test getting unwatched and watched movies from the database."""
    watchlist_key = "alpha-list"
    wid = await _setup_watchlist(tmp_path, watchlist_key)
    await db.execute(
        "INSERT INTO watchlist (watchlist_id, title, year, watched, rating) "
        "VALUES (:wid, :title, :year, :watched, :rating)",
        {"wid": wid, "title": "Movie1", "year": 2000, "watched": 0, "rating": None},
    )
    await db.execute(
        "INSERT INTO watchlist (watchlist_id, title, year, watched, rating) "
        "VALUES (:wid, :title, :year, :watched, :rating)",
        {"wid": wid, "title": "Movie2", "year": 2001, "watched": 1, "rating": 8.5},
    )
    unwatched = await resources.get_unwatched_movies(watchlist_key)
    assert any("Movie1" in m for m in unwatched)
    watched = await resources.get_watched_movies(watchlist_key)
    assert any("Movie2" in m for m in watched)


@pytest.mark.asyncio
async def test_get_all_movies_unknown_watchlist(tmp_path):
    """Test list endpoints return not-found message for unknown watchlist."""
    db.DB_PATH = str(tmp_path / "test_watchlist.db")
    await db.init_db()
    result = await resources.get_all_movies("missing-list")
    assert result == ["Watchlist not found: 'missing-list'."]


def test_format_movie_row_variants():
    """Test formatting of movie row variants."""
    row = ("TitleA", 2020, 1, 7.5)
    formatted = resources.format_movie_row(row)
    assert "Watched: Yes" in formatted and "Rating: 7.5" in formatted
    row = ("TitleB", 2021, 0, None)
    formatted = resources.format_movie_row(row)
    assert "Watched: No" in formatted and "Rating: N/A" in formatted
