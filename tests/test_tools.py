"""Tests for tools.py in mcp_server_watchlist."""

import pytest
from mcp_server_watchlist import db, tools


async def _setup_watchlist(tmp_path, watchlist_key: str = "alpha-list") -> None:
    """Initialize DB and create a watchlist with the provided key."""
    db.DB_PATH = str(tmp_path / "test_watchlist.db")
    await db.init_db()
    await db.execute(
        "INSERT INTO watchlists (coolname) VALUES (:coolname)",
        {"coolname": watchlist_key},
    )


@pytest.mark.asyncio
async def test_create_watchlist_generates_and_persists(monkeypatch, tmp_path):
    """Test create_watchlist generates a key and writes it to DB."""
    db.DB_PATH = str(tmp_path / "test_watchlist.db")
    await db.init_db()
    monkeypatch.setattr(tools, "generate_slug", lambda: "quiet-blue-panda")

    created = await tools.create_watchlist()

    assert created == "quiet-blue-panda"
    wid = await db.get_watchlist_id("quiet-blue-panda")
    assert wid is not None


@pytest.mark.asyncio
async def test_create_watchlist_retries_on_collision(monkeypatch, tmp_path):
    """Test create_watchlist retries when generated key already exists."""
    db.DB_PATH = str(tmp_path / "test_watchlist.db")
    await db.init_db()
    await db.execute(
        "INSERT INTO watchlists (coolname) VALUES (:coolname)",
        {"coolname": "taken-key"},
    )

    calls = iter(["taken-key", "fresh-key"])
    monkeypatch.setattr(tools, "generate_slug", lambda: next(calls))

    created = await tools.create_watchlist()

    assert created == "fresh-key"
    wid = await db.get_watchlist_id("fresh-key")
    assert wid is not None


@pytest.mark.asyncio
async def test_show_watchlist_returns_items(monkeypatch):
    """Test show_watchlist returns formatted movie entries from resources."""

    async def async_movies(watchlist_key):
        return ["Title: Inception, Year: 2010, Watched: No, Rating: N/A"]

    monkeypatch.setattr(tools, "get_all_movies", async_movies)
    result = await tools.show_watchlist("alpha-list")

    assert len(result) == 1
    assert "Inception" in result[0]


@pytest.mark.asyncio
async def test_show_watchlist_empty(monkeypatch):
    """Test show_watchlist returns an empty list when the watchlist is empty."""

    async def async_movies(watchlist_key):
        return []

    monkeypatch.setattr(tools, "get_all_movies", async_movies)
    result = await tools.show_watchlist("alpha-list")

    assert result == []


@pytest.mark.asyncio
async def test_summarize_watchlist_with_sampling_text(monkeypatch):
    """Test summarize_watchlist_with_sampling returns text content branch."""

    async def async_movies(watchlist_key):
        return ["Movie1 (2020)"]

    monkeypatch.setattr(tools, "get_all_movies", async_movies)

    class DummyContent:
        type = "text"
        text = "You like modern sci-fi thrillers."

    class DummyMsg:
        content = DummyContent()

    class DummySession:
        @staticmethod
        async def create_message(*_args, **_kwargs):
            return DummyMsg()

    class DummyCtx:
        session = DummySession()

    result = await tools.summarize_watchlist_with_sampling("alpha-list", DummyCtx())
    assert "You like modern sci-fi thrillers." in result


@pytest.mark.asyncio
async def test_summarize_watchlist_with_sampling_empty(monkeypatch):
    """Test summarize_watchlist_with_sampling with an empty watchlist."""

    async def async_empty(watchlist_key):
        return []

    monkeypatch.setattr(tools, "get_all_movies", async_empty)

    class DummyCtx:
        pass

    result = await tools.summarize_watchlist_with_sampling("alpha-list", DummyCtx())
    assert "is empty" in result.lower()


@pytest.mark.asyncio
async def test_summarize_watchlist_with_sampling_non_text(monkeypatch):
    """Test summarize_watchlist_with_sampling with non-text response content."""

    async def async_movies(watchlist_key):
        return ["Movie1 (2020)"]

    monkeypatch.setattr(tools, "get_all_movies", async_movies)

    class DummyContent:
        type = "not_text"

        def __str__(self):
            return "[DummyContent]"

    class DummyMsg:
        content = DummyContent()

    class DummySession:
        @staticmethod
        async def create_message(*_args, **_kwargs):
            return DummyMsg()

    class DummyCtx:
        session = DummySession()

    result = await tools.summarize_watchlist_with_sampling("alpha-list", DummyCtx())
    assert "[Watchlist Summary]" in result and "[DummyContent]" in result


@pytest.mark.asyncio
async def test_summarize_watchlist_without_sampling(monkeypatch):
    """Test summarize_watchlist_without_sampling returns deterministic overview."""

    async def async_movies(watchlist_key):
        return [
            "Title: One, Year: 1999, Watched: Yes, Rating: 9.0",
            "Title: Two, Year: 2015, Watched: No, Rating: N/A",
        ]

    monkeypatch.setattr(tools, "get_all_movies", async_movies)

    result = await tools.summarize_watchlist_without_sampling("alpha-list")
    assert "Sampling is disabled or unavailable" in result
    assert "Title: One" in result
    assert "Title: Two" in result


@pytest.mark.asyncio
async def test_summarize_watchlist_without_sampling_empty(monkeypatch):
    """Test summarize_watchlist_without_sampling empty watchlist branch."""

    async def async_empty(watchlist_key):
        return []

    monkeypatch.setattr(tools, "get_all_movies", async_empty)
    result = await tools.summarize_watchlist_without_sampling("alpha-list")
    assert "is empty" in result.lower()


@pytest.mark.asyncio
async def test_add_and_delete_movie(tmp_path):
    """Test adding and deleting a movie."""
    await _setup_watchlist(tmp_path, "alpha-list")

    add_result = await tools.add_movie("alpha-list", "Inception", 2010)
    assert "Added: Title: Inception" in add_result

    del_result = await tools.delete_movie("alpha-list", "Inception")
    assert "Deleted: Title: Inception" in del_result


@pytest.mark.asyncio
async def test_add_movie_unknown_watchlist(tmp_path):
    """Test add_movie returns watchlist-not-found for unknown keys."""
    db.DB_PATH = str(tmp_path / "test_watchlist.db")
    await db.init_db()

    result = await tools.add_movie("missing-list", "Inception", 2010)

    assert "Watchlist not found" in result


@pytest.mark.asyncio
async def test_unwatch_movie(tmp_path):
    """Test unwatching a movie."""
    await _setup_watchlist(tmp_path, "alpha-list")
    await tools.add_movie("alpha-list", "TestMovie", 2022)

    result = await tools.unwatch_movie("alpha-list", "TestMovie")

    assert "Marked as unwatched: Title: TestMovie" in result


@pytest.mark.asyncio
async def test_mark_watched_with_elicitation_success(tmp_path):
    """Test successfully marking a movie as watched via elicitation."""

    class DummyCtx:
        async def elicit(self, *_args, **_kwargs):
            return type(
                "Dummy",
                (),
                {"action": "accept", "data": type("Data", (), {"rating": 8.0})()},
            )()

    await _setup_watchlist(tmp_path, "alpha-list")
    await tools.add_movie("alpha-list", "WatchedMovie", 2023)

    result = await tools.mark_watched_with_elicitation("alpha-list", "WatchedMovie", DummyCtx())

    assert "Marked as watched: Title: WatchedMovie" in result
    assert "Rating: 8.0" in result


@pytest.mark.asyncio
async def test_mark_watched_with_rating_success(tmp_path):
    """Test mark_watched_with_rating updates a movie with direct rating input."""
    await _setup_watchlist(tmp_path, "alpha-list")
    await tools.add_movie("alpha-list", "NoPromptMovie", 2024)

    result = await tools.mark_watched_with_rating("alpha-list", "NoPromptMovie", 7.5)

    assert "Marked as watched: Title: NoPromptMovie" in result
    assert "Rating: 7.5" in result


@pytest.mark.asyncio
async def test_mark_watched_with_rating_not_found(tmp_path):
    """Test mark_watched_with_rating returns not-found for missing movies."""
    await _setup_watchlist(tmp_path, "alpha-list")

    result = await tools.mark_watched_with_rating("alpha-list", "NoCtxMovie", 8.0)

    assert "Movie not found in watchlist" in result
