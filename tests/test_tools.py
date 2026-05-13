"""Tests for tools.py in mcp_server_watchlist."""

import asyncio
import pytest
from mcp_server_watchlist import db, tools


@pytest.mark.asyncio
async def test_summarize_watchlist_non_text(tmp_path):
    """Test summarize_watchlist with non-text content."""
    orig = tools.get_all_movies

    async def async_movies():
        return ["Movie1 (2020)"]

    tools.get_all_movies = staticmethod(async_movies)

    class DummyContent:
        """Dummy content with non-text type."""

        type = "not_text"

        def __str__(self):
            return "[DummyContent]"

    class DummyMsg:
        """Dummy message with content."""

        content = DummyContent()

    class DummySession:
        """Dummy session for create_message."""

        @staticmethod
        async def create_message(*_args, **_kwargs):
            """Create a dummy message."""
            return DummyMsg()

        def dummy_method(self):
            """Dummy method to avoid too-few-public-methods warning."""
            return None

    class DummyCtx:
        """Dummy context with session."""

        session = DummySession()

        def dummy_method(self):
            """Dummy method to avoid too-few-public-methods warning."""
            return None

    result = await tools.summarize_watchlist(DummyCtx())
    assert (
        "[Watchlist Summary]" in result and "[DummyContent]" in result
    )
    tools.get_all_movies = orig


@pytest.mark.asyncio
async def test_add_and_delete_movie(tmp_path):
    """Test adding and deleting a movie."""
    test_db = tmp_path / "test_watchlist.db"
    orig_path = db.DB_PATH
    db.DB_PATH = str(test_db)
    await db.init_db()
    result = await tools.add_movie("Inception", 2010)
    assert "Added: Title: Inception" in result
    del_result = await tools.delete_movie("Inception")
    assert "Deleted: Title: Inception" in del_result
    db.DB_PATH = orig_path


@pytest.mark.asyncio
async def test_delete_movie_not_found(tmp_path):
    """Test deleting a movie that does not exist."""
    test_db = tmp_path / "test_watchlist.db"
    orig_path = db.DB_PATH
    db.DB_PATH = str(test_db)
    await db.init_db()
    result = await tools.delete_movie("Nonexistent")
    assert "Movie not found in watchlist" in result
    db.DB_PATH = orig_path


@pytest.mark.asyncio
async def test_unwatch_movie(tmp_path):
    """Test unwatching a movie."""
    test_db = tmp_path / "test_watchlist.db"
    orig_path = db.DB_PATH
    db.DB_PATH = str(test_db)
    await db.init_db()
    await tools.add_movie("TestMovie", 2022)
    result = await tools.unwatch_movie("TestMovie")
    assert "Marked as unwatched: Title: TestMovie" in result
    db.DB_PATH = orig_path


@pytest.mark.asyncio
async def test_unwatch_movie_not_found(tmp_path):
    """Test unwatching a movie that does not exist."""
    test_db = tmp_path / "test_watchlist.db"
    db.DB_PATH = str(test_db)
    await db.init_db()
    result = await tools.unwatch_movie("Nonexistent")
    assert "Movie not found in watchlist" in result


@pytest.mark.asyncio
async def test_mark_watched_not_found(tmp_path):
    """Test marking as watched a movie that does not exist."""
    class DummyCtx:
        """Dummy context for elicit."""
        async def elicit(self, _message, _schema):
            """Dummy elicit method."""
            return type("Dummy", (), {"action": "accept", "data": type("Data", (), {"rating": 9.0})()})()

        def dummy_method(self):
            """Dummy method to avoid too-few-public-methods warning."""
            return None

    test_db = tmp_path / "test_watchlist.db"
    db.DB_PATH = str(test_db)
    await db.init_db()
    result = await tools.mark_watched("Nonexistent", DummyCtx())
    assert "Movie not found in watchlist" in result


@pytest.mark.asyncio
async def test_mark_watched_success(tmp_path):
    """Test successfully marking a movie as watched."""
    class DummyCtx:
        """Dummy context for elicit."""
        async def elicit(self, *args, **kwargs):
            """Dummy elicit method."""
            return type("Dummy", (), {"action": "accept", "data": type("Data", (), {"rating": 8.0})()})()

        def dummy_method(self):
            """Dummy method to avoid too-few-public-methods warning."""
            return None

    test_db = tmp_path / "test_watchlist.db"
    db.DB_PATH = str(test_db)
    await db.init_db()
    await tools.add_movie("WatchedMovie", 2023)
    result = await tools.mark_watched("WatchedMovie", DummyCtx())
    assert "Marked as watched: Title: WatchedMovie" in result and "Rating: 8.0" in result


@pytest.mark.asyncio
async def test_summarize_watchlist_empty(tmp_path):
    """Test summarize_watchlist with an empty watchlist."""
    class DummyCtx:
        """Dummy context for session."""
        session = type("Session", (), {"create_message": staticmethod(lambda **_kwargs: type("Msg", (), {"content": type("Content", (), {"type": "text", "text": "summary"})()})())})()

        def dummy_method(self):
            """Dummy method to avoid too-few-public-methods warning."""
            return None

    test_db = tmp_path / "test_watchlist.db"
    db.DB_PATH = str(test_db)
    await db.init_db()
    orig = tools.get_all_movies
    async def async_empty():
        return []
    tools.get_all_movies = staticmethod(async_empty)
    result = await tools.summarize_watchlist(DummyCtx())
    assert "watchlist is empty" in result.lower()
    tools.get_all_movies = orig


@pytest.mark.asyncio
async def test_summarize_watchlist_non_text_2(tmp_path):
    """Test summarize_watchlist with non-text content (variant)."""
    class DummyContent:
        """Dummy content with non-text type."""
        type = "not_text"
        def __str__(self):
            return "[DummyContent]"
    class DummyMsg:
        """Dummy message with content."""
        content = DummyContent()
    class DummySession:
        """Dummy session for create_message."""
        @staticmethod
        async def create_message(*_args, **_kwargs):
            """Create a dummy message."""
            return DummyMsg()
        def dummy_method(self):
            """Dummy method to avoid too-few-public-methods warning."""
            return None
    class DummyCtx:
        """Dummy context with session."""
        session = DummySession()
        def dummy_method(self):
            """Dummy method to avoid too-few-public-methods warning."""
            return None
    test_db = tmp_path / "test_watchlist.db"
    db.DB_PATH = str(test_db)
    await db.init_db()
    orig = tools.get_all_movies
    async def async_movies():
        return ["Movie"]
    tools.get_all_movies = staticmethod(async_movies)
    result = await tools.summarize_watchlist(DummyCtx())
    assert (
        "[Watchlist Summary]" in result and "[DummyContent]" in result
    )
    tools.get_all_movies = orig


@pytest.mark.asyncio
async def test_summarize_watchlist_exception(tmp_path):
    """Test summarize_watchlist falls back to local summary on exception."""
    class DummyCtx:
        """Dummy context for session."""
        session = type(
            "Session",
            (),
            {
                "create_message": staticmethod(
                    lambda **_kwargs: (_ for _ in ()).throw(AttributeError("fail"))
                )
            },
        )()
        def dummy_method(self):
            """Dummy method to avoid too-few-public-methods warning."""
            return None
    test_db = tmp_path / "test_watchlist.db"
    db.DB_PATH = str(test_db)
    await db.init_db()
    orig = tools.get_all_movies
    async def async_movies():
        return ["Movie"]
    tools.get_all_movies = staticmethod(async_movies)
    result = await tools.summarize_watchlist(DummyCtx())
    assert "[Watchlist Summary]" in result
    assert "You have 1 movie(s)" in result
    tools.get_all_movies = orig


@pytest.mark.asyncio
async def test_summarize_watchlist_runtime_error_fallback(tmp_path):
    """Test summarize_watchlist handles non-attribute runtime errors too."""

    class DummySession:
        """Dummy session that raises a generic runtime error."""

        @staticmethod
        async def create_message(*_args, **_kwargs):
            raise RuntimeError("sampling backend unavailable")

    class DummyCtx:
        """Dummy context with session."""

        session = DummySession()

        def dummy_method(self):
            """Dummy method to avoid too-few-public-methods warning."""
            return None

    test_db = tmp_path / "test_watchlist.db"
    db.DB_PATH = str(test_db)
    await db.init_db()

    orig = tools.get_all_movies

    async def async_movies():
        return [
            "Title: A, Year: 2000, Watched: Yes, Rating: 8.5",
            "Title: B, Year: 2020, Watched: No, Rating: N/A",
        ]

    tools.get_all_movies = staticmethod(async_movies)
    result = await tools.summarize_watchlist(DummyCtx())
    assert "[Watchlist Summary]" in result
    assert "2 movie(s): 1 watched and 1 unwatched" in result
    assert "span from 2000 to 2020" in result
    tools.get_all_movies = orig


@pytest.mark.asyncio
async def test_summarize_watchlist_timeout_fallback(tmp_path, monkeypatch):
    """Test summarize_watchlist falls back when sampling stalls."""

    class DummySession:
        """Dummy session that blocks long enough to trigger timeout."""

        @staticmethod
        async def create_message(*_args, **_kwargs):
            await asyncio.sleep(0.2)
            return None

    class DummyCtx:
        """Dummy context with session."""

        session = DummySession()

        def dummy_method(self):
            """Dummy method to avoid too-few-public-methods warning."""
            return None

    test_db = tmp_path / "test_watchlist.db"
    db.DB_PATH = str(test_db)
    await db.init_db()

    orig_movies = tools.get_all_movies
    async def async_movies():
        return ["Title: A, Year: 2021, Watched: No, Rating: N/A"]

    monkeypatch.setattr(tools, "SAMPLING_TIMEOUT_SECONDS", 0.05)
    tools.get_all_movies = staticmethod(async_movies)

    result = await tools.summarize_watchlist(DummyCtx())
    assert "[Watchlist Summary]" in result
    assert "You have 1 movie(s): 0 watched and 1 unwatched" in result
    tools.get_all_movies = orig_movies
