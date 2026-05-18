"""Tests for the db module in mcp_server_watchlist."""

import pytest

from mcp_server_watchlist import db


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


@pytest.mark.asyncio
async def test_init_db_creates_tables(tmp_path, reset_db_engine):
    """Test that init_db creates watchlists and watchlist tables."""
    orig_path = db.DB_PATH
    db.DB_PATH = str(tmp_path / "test_watchlist.db")
    result = await db.init_db()
    assert result is True
    db.DB_PATH = orig_path


@pytest.mark.asyncio
async def test_get_watchlist_id_returns_expected_value(tmp_path, reset_db_engine):
    """Test get_watchlist_id returns the created row id for an existing key."""
    orig_path = db.DB_PATH
    db.DB_PATH = str(tmp_path / "test_watchlist.db")
    await db.init_db()
    session = await db.get_session()
    async with session:
        watchlist = db.Watchlist(coolname="alpha-list")
        session.add(watchlist)
        await session.commit()
        wid = await db.get_watchlist_id(session, "alpha-list")
        assert isinstance(wid, int)
        assert wid > 0
    db.DB_PATH = orig_path


@pytest.mark.asyncio
async def test_get_watchlist_id_missing_returns_none(tmp_path, reset_db_engine):
    """Test get_watchlist_id returns None for unknown keys."""
    orig_path = db.DB_PATH
    db.DB_PATH = str(tmp_path / "test_watchlist.db")
    await db.init_db()
    session = await db.get_session()
    async with session:
        wid = await db.get_watchlist_id(session, "missing-list")
        assert wid is None
    db.DB_PATH = orig_path


def test_get_database_url_defaults_to_sqlite(monkeypatch):
    """Test default DB URL uses local SQLite when DATABASE_URL is unset."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("DB_URL", raising=False)
    db.DB_PATH = "watchlist.db"
    assert db.get_database_url() == "sqlite+aiosqlite:///watchlist.db"


def test_get_database_url_uses_db_url_alias(monkeypatch):
    """Test DB_URL is accepted when DATABASE_URL is not set."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("DB_URL", "sqlite:///tmp/watchlist.db")
    assert db.get_database_url() == "sqlite+aiosqlite:///tmp/watchlist.db"


def test_get_database_url_prefers_database_url_over_db_url(monkeypatch):
    """Test DATABASE_URL has precedence when both env vars are set."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@h:5432/watchlist")
    monkeypatch.setenv("DB_URL", "sqlite:///tmp/watchlist.db")
    assert db.get_database_url().startswith("postgresql+asyncpg://")


def test_get_database_url_invalid_db_url_falls_back_to_sqlite(monkeypatch):
    """Test invalid DB_URL values are ignored in favor of default SQLite."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("DB_URL", "watchlist.db")
    db.DB_PATH = "watchlist.db"
    assert db.get_database_url() == "sqlite+aiosqlite:///watchlist.db"


def test_get_database_url_invalid_database_url_falls_back_to_sqlite(monkeypatch):
    """Test invalid DATABASE_URL values are ignored in favor of default SQLite."""
    monkeypatch.setenv("DATABASE_URL", "not-a-valid-db-url")
    monkeypatch.delenv("DB_URL", raising=False)
    db.DB_PATH = "watchlist.db"
    assert db.get_database_url() == "sqlite+aiosqlite:///watchlist.db"


def test_get_database_url_normalizes_postgres(monkeypatch):
    """Test PostgreSQL URLs are normalized to asyncpg driver."""
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://user:[REDACTED_SQL_PASSWORD_1]@db.example.com:5432/watchlist",
    )
    assert db.get_database_url().startswith("postgresql+asyncpg://")


def test_normalize_database_url_supports_all_prefixes():
    """Test URL normalization for sqlite, postgres shorthand, mysql, and passthrough."""
    assert db._normalize_database_url("sqlite:///tmp/test.db").startswith(
        "sqlite+aiosqlite:///"
    )
    assert db._normalize_database_url("postgres://u:p@h:5432/db").startswith(
        "postgresql+asyncpg://"
    )
    assert db._normalize_database_url("mysql://u:p@h:3306/db").startswith(
        "mysql+aiomysql://"
    )
    assert (
        db._normalize_database_url("oracle://u:p@h:1521/db") == "oracle://u:p@h:1521/db"
    )


def test_make_engine_strips_sslmode_and_sets_ssl(monkeypatch):
    """Test _make_engine maps sslmode to connect_args and removes sslmode query param."""
    captured = {}

    def fake_create_async_engine(url, connect_args=None):
        captured["url"] = url
        captured["connect_args"] = connect_args

        class DummyEngine:
            pass

        return DummyEngine()

    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://u:p@h:5432/watchlist?sslmode=require&application_name=watchlist",
    )
    monkeypatch.setattr(db, "create_async_engine", fake_create_async_engine)

    db._make_engine()

    assert "sslmode=require" not in captured["url"]
    assert "application_name=watchlist" in captured["url"]
    assert captured["connect_args"] == {"ssl": True}


def test_make_engine_without_sslmode_does_not_set_ssl(monkeypatch, reset_db_engine):
    """Test _make_engine leaves connect_args empty when sslmode is not present."""
    captured = {}

    def fake_create_async_engine(url, connect_args=None):
        captured["url"] = url
        captured["connect_args"] = connect_args

        class DummyEngine:
            pass

        return DummyEngine()

    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@h:5432/watchlist")
    monkeypatch.setattr(db, "create_async_engine", fake_create_async_engine)

    db._make_engine()

    assert captured["url"].startswith("postgresql+asyncpg://")
    assert captured["connect_args"] == {}


def test_make_engine_invalid_configured_url_falls_back_to_sqlite(
    monkeypatch, reset_db_engine
):
    """Test _make_engine uses local SQLite when configured URL is invalid."""
    captured = {}

    def fake_create_async_engine(url, connect_args=None):
        captured["url"] = url
        captured["connect_args"] = connect_args

        class DummyEngine:
            pass

        return DummyEngine()

    monkeypatch.setenv("DATABASE_URL", "watchlist.db")
    monkeypatch.delenv("DB_URL", raising=False)
    monkeypatch.setattr(db, "create_async_engine", fake_create_async_engine)

    db._make_engine()

    assert captured["url"] == "sqlite+aiosqlite:///watchlist.db"
    assert captured["connect_args"] == {}


@pytest.mark.asyncio
async def test_init_db_returns_false_on_exception(monkeypatch, reset_db_engine):
    """Test that init_db returns False when database initialization fails."""

    class FakeAsyncContextManager:
        async def __aenter__(self):
            raise RuntimeError("Simulated engine error")

        async def __aexit__(self, *args):
            pass

    class FakeEngine:
        def begin(self):
            return FakeAsyncContextManager()

    def fake_get_engine():
        return FakeEngine()

    monkeypatch.setattr(db, "get_engine", fake_get_engine)
    result = await db.init_db()
    assert result is False


@pytest.mark.asyncio
async def test_check_database_connection_success(tmp_path, reset_db_engine):
    """Test that check_database_connection returns True on successful read."""
    orig_path = db.DB_PATH
    db.DB_PATH = str(tmp_path / "test_watchlist.db")
    await db.init_db()
    result = await db.check_database_connection()
    assert result is True
    db.DB_PATH = orig_path


@pytest.mark.asyncio
async def test_check_database_connection_failure(monkeypatch, reset_db_engine):
    """Test that check_database_connection returns False on exception."""

    async def fake_get_session():
        raise Exception("Database connection error")

    monkeypatch.setattr(db, "get_session", fake_get_session)
    result = await db.check_database_connection()
    assert result is False
