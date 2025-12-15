
# Tests for resources.py
import pytest
import aiosqlite
from mcp_server_watchlist import db, resources

@pytest.mark.asyncio
async def test_get_movie_and_all_movies(tmp_path):
    test_db = tmp_path / "test_watchlist.db"
    db.DB_PATH = str(test_db)
    await db.init_db()
    # Insert a movie
    async with aiosqlite.connect(str(test_db)) as conn:
        await conn.execute("INSERT INTO watchlist (title, year, watched, rating) VALUES (?, ?, ?, ?)", ("Inception", 2010, 0, None))
        await conn.commit()
    # Test get_movie
    result = await resources.get_movie("Inception")
    assert "Inception" in result
    # Test get_all_movies
    all_movies = await resources.get_all_movies()
    assert any("Inception" in m for m in all_movies)
