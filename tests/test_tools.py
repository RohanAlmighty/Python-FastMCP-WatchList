import pytest

@pytest.mark.asyncio
async def test_summarize_watchlist_non_text(tmp_path):
    # Patch get_all_movies to return a non-empty list
    orig = tools.get_all_movies
    async def async_movies():
        return ["Movie1 (2020)"]
    tools.get_all_movies = staticmethod(async_movies)
    # Dummy context and message with non-text content
    class DummyContent:
        type = "not_text"
        def __str__(self):
            return "[DummyContent]"
    class DummyMsg:
        content = DummyContent()
    class DummySession:
        @staticmethod
        async def create_message(*args, **kwargs):
            return DummyMsg()
    class DummyCtx:
        session = DummySession()
    result = await tools.summarize_watchlist(DummyCtx())
    assert "[Watchlist Summary]" in result and "[DummyContent]" in result
    tools.get_all_movies = orig

# Tests for tools.py
import pytest
from mcp_server_watchlist import db, tools

@pytest.mark.asyncio
async def test_add_and_delete_movie(tmp_path):
    test_db = tmp_path / "test_watchlist.db"
    orig_path = db.DB_PATH
    db.DB_PATH = str(test_db)
    await db.init_db()
    # Add movie
    result = await tools.add_movie("Inception", 2010)
    assert "Added: Title: Inception" in result
    # Delete movie
    del_result = await tools.delete_movie("Inception")
    assert "Deleted: Title: Inception" in del_result
    db.DB_PATH = orig_path


@pytest.mark.asyncio
async def test_delete_movie_not_found(tmp_path):
    test_db = tmp_path / "test_watchlist.db"
    orig_path = db.DB_PATH
    db.DB_PATH = str(test_db)
    await db.init_db()
    result = await tools.delete_movie("Nonexistent")
    assert "Movie not found in watchlist" in result
    db.DB_PATH = orig_path


@pytest.mark.asyncio
async def test_unwatch_movie(tmp_path):
    test_db = tmp_path / "test_watchlist.db"
    orig_path = db.DB_PATH
    db.DB_PATH = str(test_db)
    await db.init_db()
    # Add and mark as watched
    await tools.add_movie("TestMovie", 2022)
    # Mark as watched (simulate rating input)
    # Mark as unwatched
    result = await tools.unwatch_movie("TestMovie")
    assert "Marked as unwatched: Title: TestMovie" in result
    db.DB_PATH = orig_path


@pytest.mark.asyncio
async def test_unwatch_movie_not_found(tmp_path):
    test_db = tmp_path / "test_watchlist.db"
    db.DB_PATH = str(test_db)
    await db.init_db()
    result = await tools.unwatch_movie("Nonexistent")
    assert "Movie not found in watchlist" in result


@pytest.mark.asyncio
async def test_mark_watched_not_found(tmp_path):
    class DummyCtx:
        async def elicit(self, message, schema):
            return type("Dummy", (), {"action": "accept", "data": type("Data", (), {"rating": 9.0})()})()
    test_db = tmp_path / "test_watchlist.db"
    db.DB_PATH = str(test_db)
    await db.init_db()
    result = await tools.mark_watched("Nonexistent", DummyCtx())
    assert "Movie not found in watchlist" in result


@pytest.mark.asyncio
async def test_mark_watched_success(tmp_path):
    class DummyCtx:
        async def elicit(self, message, schema):
            return type("Dummy", (), {"action": "accept", "data": type("Data", (), {"rating": 8.0})()})()
    test_db = tmp_path / "test_watchlist.db"
    db.DB_PATH = str(test_db)
    await db.init_db()
    await tools.add_movie("WatchedMovie", 2023)
    result = await tools.mark_watched("WatchedMovie", DummyCtx())
    assert "Marked as watched: Title: WatchedMovie" in result and "Rating: 8.0" in result


@pytest.mark.asyncio
async def test_summarize_watchlist_empty(tmp_path):
    class DummyCtx:
        session = type("Session", (), {"create_message": staticmethod(lambda **kwargs: type("Msg", (), {"content": type("Content", (), {"type": "text", "text": "summary"})()})())})()
    test_db = tmp_path / "test_watchlist.db"
    db.DB_PATH = str(test_db)
    await db.init_db()
    # Patch get_all_movies to return empty (async)
    orig = tools.get_all_movies
    async def async_empty():
        return []
    tools.get_all_movies = staticmethod(async_empty)
    result = await tools.summarize_watchlist(DummyCtx())
    assert "watchlist is empty" in result.lower()
    tools.get_all_movies = orig


@pytest.mark.asyncio
async def test_summarize_watchlist_non_text(tmp_path):
    class DummyContent:
        type = "not_text"
        def __str__(self):
            return "[DummyContent]"
    class DummyMsg:
        content = DummyContent()
    class DummySession:
        @staticmethod
        async def create_message(*args, **kwargs):
            return DummyMsg()
    class DummyCtx:
        session = DummySession()
    test_db = tmp_path / "test_watchlist.db"
    db.DB_PATH = str(test_db)
    await db.init_db()
    orig = tools.get_all_movies
    async def async_movies():
        return ["Movie"]
    tools.get_all_movies = staticmethod(async_movies)
    result = await tools.summarize_watchlist(DummyCtx())
    assert "[Watchlist Summary]" in result and "[DummyContent]" in result
    tools.get_all_movies = orig


@pytest.mark.asyncio
async def test_summarize_watchlist_exception(tmp_path):
    class DummyCtx:
        session = type("Session", (), {"create_message": staticmethod(lambda **kwargs: (_ for _ in ()).throw(Exception("fail")))})()
    test_db = tmp_path / "test_watchlist.db"
    db.DB_PATH = str(test_db)
    await db.init_db()
    orig = tools.get_all_movies
    async def async_movies():
        return ["Movie"]
    tools.get_all_movies = staticmethod(async_movies)
    result = await tools.summarize_watchlist(DummyCtx())
    assert "Failed to generate a summary" in result
    tools.get_all_movies = orig
