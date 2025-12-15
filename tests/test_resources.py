"""Tests for resources.py in mcp_server_watchlist."""

import pytest
import aiosqlite
from mcp_server_watchlist import db, resources


@pytest.mark.asyncio
async def test_get_movie_and_all_movies(tmp_path):
    """Test getting a movie and all movies from the database."""
    test_db = tmp_path / "test_watchlist.db"
    db.DB_PATH = str(test_db)
    await db.init_db()
    async with aiosqlite.connect(str(test_db)) as conn:
        await conn.execute(
            "INSERT INTO watchlist (title, year, watched, rating) VALUES (?, ?, ?, ?)",
            ("Inception", 2010, 0, None),
        )
        await conn.commit()
    result = await resources.get_movie("Inception")
    assert "Inception" in result
    all_movies = await resources.get_all_movies()
    assert any("Inception" in m for m in all_movies)



@pytest.mark.asyncio
async def test_get_movie_not_found(tmp_path):
    """Test getting a movie that does not exist returns the correct message."""
    test_db = tmp_path / "test_watchlist.db"
    db.DB_PATH = str(test_db)
    await db.init_db()
    result = await resources.get_movie("Nonexistent")
    assert result == "Movie not found in watchlist."



@pytest.mark.asyncio
async def test_get_unwatched_and_watched_movies(tmp_path):
    """Test getting unwatched and watched movies from the database."""
    test_db = tmp_path / "test_watchlist.db"
    db.DB_PATH = str(test_db)
    await db.init_db()
    async with aiosqlite.connect(str(test_db)) as conn:
        await conn.execute(
            "INSERT INTO watchlist (title, year, watched, rating) VALUES (?, ?, ?, ?)",
            ("Movie1", 2000, 0, None),
        )
        await conn.execute(
            "INSERT INTO watchlist (title, year, watched, rating) VALUES (?, ?, ?, ?)",
            ("Movie2", 2001, 1, 8.5),
        )
        await conn.commit()
    unwatched = await resources.get_unwatched_movies()
    assert any("Movie1" in m for m in unwatched)
    watched = await resources.get_watched_movies()
    assert any("Movie2" in m for m in watched)



def test_format_movie_row_variants():
    """Test formatting of movie row variants."""
    row = ("TitleA", 2020, 1, 7.5)
    formatted = resources.format_movie_row(row)
    assert "Watched: Yes" in formatted and "Rating: 7.5" in formatted
    row = ("TitleB", 2021, 0, None)
    formatted = resources.format_movie_row(row)
    assert "Watched: No" in formatted and "Rating: N/A" in formatted
