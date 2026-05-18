"""Tests for resources.py in mcp_server_watchlist."""

import pytest

from mcp_server_watchlist import db, resources


@pytest.fixture
def reset_db_engine():
    """Reset the global engine and session factory before/after each test."""
    orig_engine = db._engine
    orig_factory = db._session_factory
    db._engine = None
    db._session_factory = None
    yield
    db._engine = orig_engine
    db._session_factory = orig_factory


async def _setup_watchlist(tmp_path, watchlist_key: str = "alpha-list") -> int:
    """Initialize DB and create a watchlist row, returning its id."""
    db.DB_PATH = str(tmp_path / "test_watchlist.db")
    await db.init_db()
    session = await db.get_session()
    async with session:
        watchlist = db.Watchlist(coolname=watchlist_key)
        session.add(watchlist)
        await session.commit()
        return watchlist.id


@pytest.mark.asyncio
async def test_get_movie_and_all_movies(tmp_path, reset_db_engine):
    """Test getting a movie and all movies from the database."""
    watchlist_key = "alpha-list"
    wid = await _setup_watchlist(tmp_path, watchlist_key)
    session = await db.get_session()
    async with session:
        movie = db.WatchlistItem(
            watchlist_id=wid, title="Inception", year=2010, watched=0, rating=None
        )
        session.add(movie)
        await session.commit()
    result = await resources.get_movie(watchlist_key, "Inception")
    assert "Inception" in result
    all_movies = await resources.get_all_movies(watchlist_key)
    assert any("Inception" in m for m in all_movies)


@pytest.mark.asyncio
async def test_get_movie_not_found(tmp_path, reset_db_engine):
    """Test getting a movie that does not exist returns the correct message."""
    watchlist_key = "alpha-list"
    await _setup_watchlist(tmp_path, watchlist_key)
    result = await resources.get_movie(watchlist_key, "Nonexistent")
    assert result == "Movie not found in watchlist."


@pytest.mark.asyncio
async def test_get_movie_unknown_watchlist(tmp_path, reset_db_engine):
    """Test unknown watchlist returns watchlist-not-found response."""
    db.DB_PATH = str(tmp_path / "test_watchlist.db")
    await db.init_db()
    result = await resources.get_movie("missing-list", "Inception")
    assert "Watchlist not found" in result


@pytest.mark.asyncio
async def test_get_unwatched_and_watched_movies(tmp_path, reset_db_engine):
    """Test getting unwatched and watched movies from the database."""
    watchlist_key = "alpha-list"
    wid = await _setup_watchlist(tmp_path, watchlist_key)
    session = await db.get_session()
    async with session:
        movie1 = db.WatchlistItem(
            watchlist_id=wid, title="Movie1", year=2000, watched=0, rating=None
        )
        movie2 = db.WatchlistItem(
            watchlist_id=wid, title="Movie2", year=2001, watched=1, rating=8.5
        )
        session.add(movie1)
        session.add(movie2)
        await session.commit()
    unwatched = await resources.get_unwatched_movies(watchlist_key)
    assert any("Movie1" in m for m in unwatched)
    watched = await resources.get_watched_movies(watchlist_key)
    assert any("Movie2" in m for m in watched)


@pytest.mark.asyncio
async def test_get_all_movies_unknown_watchlist(tmp_path, reset_db_engine):
    """Test list endpoints return not-found message for unknown watchlist."""
    db.DB_PATH = str(tmp_path / "test_watchlist.db")
    await db.init_db()
    result = await resources.get_all_movies("missing-list")
    assert result == ["Watchlist not found: 'missing-list'."]


@pytest.mark.asyncio
async def test_get_unwatched_movies_unknown_watchlist(tmp_path, reset_db_engine):
    """Test unwatched endpoint returns not-found message for unknown watchlist."""
    db.DB_PATH = str(tmp_path / "test_watchlist.db")
    await db.init_db()

    result = await resources.get_unwatched_movies("missing-list")

    assert result == ["Watchlist not found: 'missing-list'."]


@pytest.mark.asyncio
async def test_get_watched_movies_unknown_watchlist(tmp_path, reset_db_engine):
    """Test watched endpoint returns not-found message for unknown watchlist."""
    db.DB_PATH = str(tmp_path / "test_watchlist.db")
    await db.init_db()

    result = await resources.get_watched_movies("missing-list")

    assert result == ["Watchlist not found: 'missing-list'."]


def test_format_movie_row_variants():
    """Test formatting of movie row variants."""
    row = ("TitleA", 2020, 1, 7.5)
    formatted = resources.format_movie_row(row)
    assert "Watched: Yes" in formatted and "Rating: 7.5" in formatted
    row = ("TitleB", 2021, 0, None)
    formatted = resources.format_movie_row(row)
    assert "Watched: No" in formatted and "Rating: N/A" in formatted
