"""Tests for tools.py in mcp_server_watchlist."""

import pytest
from mcp_server_watchlist import db, tools


@pytest.mark.asyncio
async def test_show_watchlist_returns_items(monkeypatch):
    """Test show_watchlist returns formatted movie entries from resources."""

    async def async_movies():
        return ["Title: Inception, Year: 2010, Watched: No, Rating: N/A"]

    monkeypatch.setattr(tools, "get_all_movies", async_movies)
    result = await tools.show_watchlist()

    assert len(result) == 1
    assert "Inception" in result[0]


@pytest.mark.asyncio
async def test_show_watchlist_empty(monkeypatch):
    """Test show_watchlist returns an empty list when the watchlist is empty."""

    async def async_movies():
        return []

    monkeypatch.setattr(tools, "get_all_movies", async_movies)
    result = await tools.show_watchlist()

    assert result == []


@pytest.mark.asyncio
async def test_summarize_watchlist_with_sampling_non_text(tmp_path):
    """Test summarize_watchlist_with_sampling with non-text content."""
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

    result = await tools.summarize_watchlist_with_sampling(DummyCtx())
    assert (
        "[Watchlist Summary]" in result and "[DummyContent]" in result
    )
    tools.get_all_movies = orig


@pytest.mark.asyncio
async def test_summarize_watchlist_with_sampling_text(tmp_path):
    """Test summarize_watchlist_with_sampling returns text content branch."""
    orig = tools.get_all_movies

    async def async_movies():
        return ["Movie1 (2020)"]

    tools.get_all_movies = staticmethod(async_movies)

    class DummyContent:
        """Dummy text content."""

        type = "text"
        text = "You like modern sci-fi thrillers."

    class DummyMsg:
        """Dummy message with text content."""

        content = DummyContent()

    class DummySession:
        """Dummy session for create_message."""

        @staticmethod
        async def create_message(*_args, **_kwargs):
            return DummyMsg()

    class DummyCtx:
        """Dummy context with session."""

        session = DummySession()

    result = await tools.summarize_watchlist_with_sampling(DummyCtx())
    assert "You like modern sci-fi thrillers." in result
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
    result = await tools.mark_watched_with_elicitation("Nonexistent", DummyCtx())
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
    result = await tools.mark_watched_with_elicitation("WatchedMovie", DummyCtx())
    assert "Marked as watched: Title: WatchedMovie" in result and "Rating: 8.0" in result


@pytest.mark.asyncio
async def test_mark_watched_with_rating_success(tmp_path):
    """Test mark_watched_with_rating updates a movie with direct rating input."""

    test_db = tmp_path / "test_watchlist.db"
    db.DB_PATH = str(test_db)
    await db.init_db()
    await tools.add_movie("NoPromptMovie", 2024)

    result = await tools.mark_watched_with_rating("NoPromptMovie", 7.5)
    assert "Marked as watched: Title: NoPromptMovie" in result
    assert "Rating: 7.5" in result


@pytest.mark.asyncio
async def test_mark_watched_with_rating_not_found(tmp_path):
    """Test mark_watched_with_rating returns not-found for missing movies."""

    test_db = tmp_path / "test_watchlist.db"
    db.DB_PATH = str(test_db)
    await db.init_db()
    result = await tools.mark_watched_with_rating("NoCtxMovie", 8.0)
    assert "Movie not found in watchlist" in result


@pytest.mark.asyncio
async def test_mark_watched_with_elicitation_rejects_direct_rating_arg(tmp_path):
    """Test elicitation variant rejects rating as unexpected direct input."""

    test_db = tmp_path / "test_watchlist.db"
    db.DB_PATH = str(test_db)
    await db.init_db()
    await tools.add_movie("StrictInputMovie", 2024)

    with pytest.raises(TypeError):
        await tools.mark_watched_with_elicitation("StrictInputMovie", rating=9.0)


@pytest.mark.asyncio
async def test_summarize_watchlist_with_sampling_empty(tmp_path):
    """Test summarize_watchlist_with_sampling with an empty watchlist."""
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
    result = await tools.summarize_watchlist_with_sampling(DummyCtx())
    assert "watchlist is empty" in result.lower()
    tools.get_all_movies = orig


@pytest.mark.asyncio
async def test_summarize_watchlist_with_sampling_non_text_2(tmp_path):
    """Test summarize_watchlist_with_sampling with non-text content (variant)."""
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
    result = await tools.summarize_watchlist_with_sampling(DummyCtx())
    assert (
        "[Watchlist Summary]" in result and "[DummyContent]" in result
    )
    tools.get_all_movies = orig


@pytest.mark.asyncio
async def test_summarize_watchlist_exception(tmp_path):
    """Test summarize_watchlist propagates sampling errors in strict mode."""
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
        return ["Title: Movie, Year: 2010, Watched: No, Rating: N/A"]
    tools.get_all_movies = staticmethod(async_movies)
    with pytest.raises(AttributeError):
        await tools.summarize_watchlist_with_sampling(DummyCtx())
    tools.get_all_movies = orig


@pytest.mark.asyncio
async def test_summarize_watchlist_runtime_error_fallback(tmp_path):
    """Test summarize_watchlist propagates runtime sampling errors."""

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
    with pytest.raises(RuntimeError):
        await tools.summarize_watchlist_with_sampling(DummyCtx())
    tools.get_all_movies = orig


@pytest.mark.asyncio
async def test_summarize_watchlist_without_sampling(tmp_path):
    """Test summarize_watchlist_without_sampling returns deterministic overview."""

    class DummySession:
        """Unused dummy session."""

        @staticmethod
        async def create_message(*_args, **_kwargs):
            raise AssertionError("create_message should not be called")

    class DummyCtx:
        """Unused dummy context with session."""

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
            "Title: One, Year: 1999, Watched: Yes, Rating: 9.0",
            "Title: Two, Year: 2015, Watched: No, Rating: N/A",
        ]

    tools.get_all_movies = staticmethod(async_movies)

    result = await tools.summarize_watchlist_without_sampling()
    assert "Sampling is disabled or unavailable" in result
    assert "Title: One" in result
    assert "Title: Two" in result
    tools.get_all_movies = orig


@pytest.mark.asyncio
async def test_summarize_watchlist_without_sampling_empty(tmp_path):
    """Test summarize_watchlist_without_sampling empty watchlist branch."""
    test_db = tmp_path / "test_watchlist.db"
    db.DB_PATH = str(test_db)
    await db.init_db()

    orig = tools.get_all_movies

    async def async_empty():
        return []

    tools.get_all_movies = staticmethod(async_empty)
    result = await tools.summarize_watchlist_without_sampling()
    assert "watchlist is empty" in result.lower()
    tools.get_all_movies = orig
