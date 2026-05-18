"""Tests for tools.py in mcp_server_watchlist."""

import pytest

from mcp_server_watchlist import db, tools


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


async def _setup_watchlist(tmp_path, watchlist_key: str = "alpha-list") -> None:
    """Initialize DB and create a watchlist with the provided key."""
    db.DB_PATH = str(tmp_path / "test_watchlist.db")
    await db.init_db()
    session = await db.get_session()
    async with session:
        watchlist = db.Watchlist(coolname=watchlist_key)
        session.add(watchlist)
        await session.commit()


@pytest.mark.asyncio
async def test_create_watchlist_generates_and_persists(
    monkeypatch, tmp_path, reset_db_engine
):
    """Test create_watchlist generates a key and writes it to DB."""
    db.DB_PATH = str(tmp_path / "test_watchlist.db")
    await db.init_db()
    monkeypatch.setattr(tools, "generate_slug", lambda: "quiet-blue-panda")

    created = await tools.create_watchlist()

    assert created == "quiet-blue-panda"
    session = await db.get_session()
    async with session:
        wid = await db.get_watchlist_id(session, "quiet-blue-panda")
        assert wid is not None


@pytest.mark.asyncio
async def test_create_watchlist_retries_on_collision(
    monkeypatch, tmp_path, reset_db_engine
):
    """Test create_watchlist retries when generated key already exists."""
    db.DB_PATH = str(tmp_path / "test_watchlist.db")
    await db.init_db()
    session = await db.get_session()
    async with session:
        watchlist = db.Watchlist(coolname="taken-key")
        session.add(watchlist)
        await session.commit()

    calls = iter(["taken-key", "fresh-key"])
    monkeypatch.setattr(tools, "generate_slug", lambda: next(calls))

    created = await tools.create_watchlist()

    assert created == "fresh-key"
    async with session:
        wid = await db.get_watchlist_id(session, "fresh-key")
        assert wid is not None


@pytest.mark.asyncio
async def test_create_watchlist_returns_db_error_when_insert_fails(
    monkeypatch, reset_db_engine
):
    """Test create_watchlist returns DB error when insert fails."""

    async def fake_get_watchlist_id(*_args, **_kwargs):
        return None

    async def fake_commit():
        raise Exception("Database error")

    monkeypatch.setattr(tools, "generate_slug", lambda: "quiet-blue-panda")
    monkeypatch.setattr(tools, "get_watchlist_id", fake_get_watchlist_id)

    # Mock the session's commit to raise an exception
    from unittest.mock import AsyncMock

    original_get_session = tools.get_session

    async def mock_get_session():
        session = await original_get_session()
        session.commit = AsyncMock(side_effect=Exception("Database error"))
        return session

    monkeypatch.setattr(tools, "get_session", mock_get_session)

    created = await tools.create_watchlist()

    assert created == tools.DB_ERROR_MESSAGE


@pytest.mark.asyncio
async def test_show_watchlist_returns_items(monkeypatch, reset_db_engine):
    """Test show_watchlist returns formatted movie entries from resources."""

    async def async_movies(watchlist_key):
        return ["Title: Inception, Year: 2010, Watched: No, Rating: N/A"]

    monkeypatch.setattr(tools, "get_all_movies", async_movies)
    result = await tools.show_watchlist("alpha-list")

    assert len(result) == 1
    assert "Inception" in result[0]


@pytest.mark.asyncio
async def test_show_watchlist_empty(monkeypatch, reset_db_engine):
    """Test show_watchlist returns an empty list when the watchlist is empty."""

    async def async_movies(watchlist_key):
        return []

    monkeypatch.setattr(tools, "get_all_movies", async_movies)
    result = await tools.show_watchlist("alpha-list")

    assert result == []


@pytest.mark.asyncio
async def test_summarize_watchlist_with_sampling_text(monkeypatch, reset_db_engine):
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
async def test_summarize_watchlist_with_sampling_empty(monkeypatch, reset_db_engine):
    """Test summarize_watchlist_with_sampling with an empty watchlist."""

    async def async_empty(watchlist_key):
        return []

    monkeypatch.setattr(tools, "get_all_movies", async_empty)

    class DummyCtx:
        pass

    result = await tools.summarize_watchlist_with_sampling("alpha-list", DummyCtx())
    assert "is empty" in result.lower()


@pytest.mark.asyncio
async def test_summarize_watchlist_with_sampling_not_found(
    monkeypatch, reset_db_engine
):
    """Test summarize_watchlist_with_sampling returns not-found response."""

    async def async_not_found(watchlist_key):
        return [f"Watchlist not found: '{watchlist_key}'."]

    monkeypatch.setattr(tools, "get_all_movies", async_not_found)

    class DummyCtx:
        pass

    result = await tools.summarize_watchlist_with_sampling("missing-list", DummyCtx())
    assert result == "Watchlist not found: 'missing-list'."


@pytest.mark.asyncio
async def test_summarize_watchlist_with_sampling_non_text(monkeypatch, reset_db_engine):
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
async def test_summarize_watchlist_without_sampling(monkeypatch, reset_db_engine):
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
async def test_summarize_watchlist_without_sampling_empty(monkeypatch, reset_db_engine):
    """Test summarize_watchlist_without_sampling empty watchlist branch."""

    async def async_empty(watchlist_key):
        return []

    monkeypatch.setattr(tools, "get_all_movies", async_empty)
    result = await tools.summarize_watchlist_without_sampling("alpha-list")
    assert "is empty" in result.lower()


@pytest.mark.asyncio
async def test_summarize_watchlist_without_sampling_not_found(
    monkeypatch, reset_db_engine
):
    """Test summarize_watchlist_without_sampling returns not-found response."""

    async def async_not_found(watchlist_key):
        return [f"Watchlist not found: '{watchlist_key}'."]

    monkeypatch.setattr(tools, "get_all_movies", async_not_found)
    result = await tools.summarize_watchlist_without_sampling("missing-list")

    assert result == "Watchlist not found: 'missing-list'."


@pytest.mark.asyncio
async def test_add_and_delete_movie(tmp_path, reset_db_engine):
    """Test adding and deleting a movie."""
    await _setup_watchlist(tmp_path, "alpha-list")

    add_result = await tools.add_movie("alpha-list", "Inception", 2010)
    assert "Added: Title: Inception" in add_result

    del_result = await tools.delete_movie("alpha-list", "Inception")
    assert "Deleted: Title: Inception" in del_result


@pytest.mark.asyncio
async def test_add_movie_unknown_watchlist(tmp_path, reset_db_engine):
    """Test add_movie returns watchlist-not-found for unknown keys."""
    db.DB_PATH = str(tmp_path / "test_watchlist.db")
    await db.init_db()

    result = await tools.add_movie("missing-list", "Inception", 2010)

    assert "Watchlist not found" in result


@pytest.mark.asyncio
async def test_add_movie_returns_db_error_when_insert_fails(
    monkeypatch, reset_db_engine
):
    """Test add_movie returns DB error when insert fails."""

    async def fake_get_watchlist_id(*_args, **_kwargs):
        return 123

    monkeypatch.setattr(tools, "get_watchlist_id", fake_get_watchlist_id)

    # Mock the session's commit to raise an exception
    from unittest.mock import AsyncMock

    original_get_session = tools.get_session

    async def mock_get_session():
        session = await original_get_session()
        session.commit = AsyncMock(side_effect=Exception("Database error"))
        return session

    monkeypatch.setattr(tools, "get_session", mock_get_session)

    result = await tools.add_movie("alpha-list", "Inception", 2010)

    assert result == tools.DB_ERROR_MESSAGE


@pytest.mark.asyncio
async def test_unwatch_movie(tmp_path, reset_db_engine):
    """Test unwatching a movie."""
    await _setup_watchlist(tmp_path, "alpha-list")
    await tools.add_movie("alpha-list", "TestMovie", 2022)

    result = await tools.unwatch_movie("alpha-list", "TestMovie")

    assert "Marked as unwatched: Title: TestMovie" in result


@pytest.mark.asyncio
async def test_mark_watched_with_elicitation_success(tmp_path, reset_db_engine):
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

    result = await tools.mark_watched_with_elicitation(
        "alpha-list", "WatchedMovie", DummyCtx()
    )

    assert "Marked as watched: Title: WatchedMovie" in result
    assert "Rating: 8.0" in result


@pytest.mark.asyncio
async def test_mark_watched_with_rating_success(tmp_path, reset_db_engine):
    """Test mark_watched_with_rating updates a movie with direct rating input."""
    await _setup_watchlist(tmp_path, "alpha-list")
    await tools.add_movie("alpha-list", "NoPromptMovie", 2024)

    result = await tools.mark_watched_with_rating("alpha-list", "NoPromptMovie", 7.5)

    assert "Marked as watched: Title: NoPromptMovie" in result
    assert "Rating: 7.5" in result


@pytest.mark.asyncio
async def test_mark_watched_with_rating_not_found(tmp_path, reset_db_engine):
    """Test mark_watched_with_rating returns not-found for missing movies."""
    await _setup_watchlist(tmp_path, "alpha-list")

    result = await tools.mark_watched_with_rating("alpha-list", "NoCtxMovie", 8.0)

    assert "Movie not found in watchlist" in result


@pytest.mark.asyncio
async def test_mark_watched_with_rating_unknown_watchlist(monkeypatch, reset_db_engine):
    """Test mark_watched_with_rating returns watchlist-not-found for unknown keys."""

    async def fake_get_watchlist_id(*_args, **_kwargs):
        return None

    monkeypatch.setattr(db, "get_watchlist_id", fake_get_watchlist_id)

    result = await tools.mark_watched_with_rating("missing-list", "NoCtxMovie", 8.0)

    assert result == "Watchlist not found: 'missing-list'."


@pytest.mark.asyncio
async def test_mark_watched_with_elicitation_unknown_watchlist(
    monkeypatch, reset_db_engine
):
    """Test elicitation variant returns not-found for unknown watchlists."""

    async def fake_get_watchlist_id(*_args, **_kwargs):
        return None

    monkeypatch.setattr(db, "get_watchlist_id", fake_get_watchlist_id)

    class DummyCtx:
        async def elicit(self, *_args, **_kwargs):
            return None

    result = await tools.mark_watched_with_elicitation(
        "missing-list", "Movie", DummyCtx()
    )

    assert result == "Watchlist not found: 'missing-list'."


@pytest.mark.asyncio
async def test_mark_watched_with_elicitation_movie_not_found(
    monkeypatch, reset_db_engine
):
    """Test elicitation variant returns not-found when movie is missing."""

    async def fake_get_watchlist_id(*_args, **_kwargs):
        return 1

    monkeypatch.setattr(db, "get_watchlist_id", fake_get_watchlist_id)

    class DummyCtx:
        async def elicit(self, *_args, **_kwargs):
            return None

    result = await tools.mark_watched_with_elicitation(
        "alpha-list", "Missing", DummyCtx()
    )

    assert result == "Movie not found in watchlist: Title: Missing"


@pytest.mark.asyncio
async def test_unwatch_movie_unknown_watchlist(monkeypatch, reset_db_engine):
    """Test unwatch_movie returns not-found for unknown watchlists."""

    async def fake_get_watchlist_id(*_args, **_kwargs):
        return None

    monkeypatch.setattr(db, "get_watchlist_id", fake_get_watchlist_id)

    result = await tools.unwatch_movie("missing-list", "Inception")

    assert result == "Watchlist not found: 'missing-list'."


@pytest.mark.asyncio
async def test_unwatch_movie_not_found(monkeypatch, reset_db_engine):
    """Test unwatch_movie returns movie-not-found when movie is missing."""

    async def fake_get_watchlist_id(*_args, **_kwargs):
        return 1

    monkeypatch.setattr(db, "get_watchlist_id", fake_get_watchlist_id)

    result = await tools.unwatch_movie("alpha-list", "Missing")

    assert result == "Movie not found in watchlist: Title: Missing"


@pytest.mark.asyncio
async def test_delete_movie_unknown_watchlist(monkeypatch, reset_db_engine):
    """Test delete_movie returns not-found for unknown watchlists."""

    async def fake_get_watchlist_id(*_args, **_kwargs):
        return None

    monkeypatch.setattr(db, "get_watchlist_id", fake_get_watchlist_id)

    result = await tools.delete_movie("missing-list", "Inception")

    assert result == "Watchlist not found: 'missing-list'."


@pytest.mark.asyncio
async def test_delete_movie_not_found(monkeypatch, reset_db_engine):
    """Test delete_movie returns movie-not-found when movie is missing."""

    async def fake_get_watchlist_id(*_args, **_kwargs):
        return 1

    monkeypatch.setattr(db, "get_watchlist_id", fake_get_watchlist_id)

    result = await tools.delete_movie("alpha-list", "Missing")

    assert result == "Movie not found in watchlist: Title: Missing"


@pytest.mark.asyncio
async def test_mark_watched_with_elicitation_no_rating(tmp_path, reset_db_engine):
    """Test mark_watched_with_elicitation when no rating is provided."""

    class DummyCtx:
        async def elicit(self, *_args, **_kwargs):
            return type(
                "Dummy",
                (),
                {"action": "accept", "data": type("Data", (), {"rating": None})()},
            )()

    await _setup_watchlist(tmp_path, "alpha-list")
    await tools.add_movie("alpha-list", "NoRatingMovie", 2023)

    result = await tools.mark_watched_with_elicitation(
        "alpha-list", "NoRatingMovie", DummyCtx()
    )

    assert "Marked as watched: Title: NoRatingMovie" in result
    assert "Rating: N/A" in result


@pytest.mark.asyncio
async def test_mark_watched_with_elicitation_no_elicit_response(
    tmp_path, reset_db_engine
):
    """Test mark_watched_with_elicitation when elicitation returns None."""

    class DummyCtx:
        async def elicit(self, *_args, **_kwargs):
            return None

    await _setup_watchlist(tmp_path, "alpha-list")
    await tools.add_movie("alpha-list", "NoResponseMovie", 2023)

    result = await tools.mark_watched_with_elicitation(
        "alpha-list", "NoResponseMovie", DummyCtx()
    )

    assert "Marked as watched: Title: NoResponseMovie" in result
    assert "Rating: N/A" in result


@pytest.mark.asyncio
async def test_delete_movie_success(tmp_path, reset_db_engine):
    """Test delete_movie successfully deletes a movie."""
    await _setup_watchlist(tmp_path, "alpha-list")
    await tools.add_movie("alpha-list", "ToDelete", 2020)

    result = await tools.delete_movie("alpha-list", "ToDelete")

    assert "Deleted: Title: ToDelete" in result
    assert "Year: 2020" in result
    assert "watchlist 'alpha-list'" in result


@pytest.mark.asyncio
async def test_delete_movie_with_rating(tmp_path, reset_db_engine):
    """Test delete_movie shows rating when movie has been rated."""
    await _setup_watchlist(tmp_path, "alpha-list")
    await tools.add_movie("alpha-list", "RatedMovie", 2019)
    await tools.mark_watched_with_rating("alpha-list", "RatedMovie", 7.5)

    result = await tools.delete_movie("alpha-list", "RatedMovie")

    assert "Deleted: Title: RatedMovie" in result
    assert "Rating: 7.5" in result


@pytest.mark.asyncio
async def test_unwatch_movie_success(tmp_path, reset_db_engine):
    """Test unwatch_movie successfully unmarks a watched movie."""
    await _setup_watchlist(tmp_path, "alpha-list")
    await tools.add_movie("alpha-list", "WatchedForUnwatch", 2021)
    await tools.mark_watched_with_rating("alpha-list", "WatchedForUnwatch", 8.5)

    result = await tools.unwatch_movie("alpha-list", "WatchedForUnwatch")

    assert "Marked as unwatched: Title: WatchedForUnwatch" in result
    assert "Year: 2021" in result
    assert "Rating: N/A" in result


@pytest.mark.asyncio
async def test_unwatch_movie_returns_db_error_when_update_fails(
    monkeypatch, reset_db_engine
):
    """Test unwatch_movie returns DB error when commit fails."""

    async def fake_get_watchlist_id(*_args, **_kwargs):
        return 1

    monkeypatch.setattr(tools, "get_watchlist_id", fake_get_watchlist_id)

    # Mock the session to return a movie object and fail on commit
    from unittest.mock import AsyncMock, MagicMock

    original_get_session = tools.get_session

    async def mock_get_session():
        session = await original_get_session()
        # Mock execute to return a movie object
        mock_result = MagicMock()
        mock_movie = MagicMock()
        mock_movie.watched = 1
        mock_movie.rating = 8.5
        mock_result.scalars.return_value.first.return_value = mock_movie
        session.execute = AsyncMock(return_value=mock_result)
        session.commit = AsyncMock(side_effect=Exception("Database error"))
        session.rollback = AsyncMock()
        return session

    monkeypatch.setattr(tools, "get_session", mock_get_session)

    result = await tools.unwatch_movie("alpha-list", "TestMovie")

    assert result == tools.DB_ERROR_MESSAGE


@pytest.mark.asyncio
async def test_delete_movie_returns_db_error_when_delete_fails(
    monkeypatch, reset_db_engine
):
    """Test delete_movie returns DB error when commit fails."""

    async def fake_get_watchlist_id(*_args, **_kwargs):
        return 1

    monkeypatch.setattr(tools, "get_watchlist_id", fake_get_watchlist_id)

    # Mock the session to return a movie object and fail on commit
    from unittest.mock import AsyncMock, MagicMock

    original_get_session = tools.get_session

    async def mock_get_session():
        session = await original_get_session()
        # Mock execute to return a movie object
        mock_result = MagicMock()
        mock_movie = MagicMock()
        mock_movie.year = 2020
        mock_movie.rating = 7.5
        mock_result.scalars.return_value.first.return_value = mock_movie
        session.execute = AsyncMock(return_value=mock_result)
        session.delete = MagicMock()
        session.commit = AsyncMock(side_effect=Exception("Database error"))
        session.rollback = AsyncMock()
        return session

    monkeypatch.setattr(tools, "get_session", mock_get_session)

    result = await tools.delete_movie("alpha-list", "TestMovie")

    assert result == tools.DB_ERROR_MESSAGE
