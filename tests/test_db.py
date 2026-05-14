
"""Tests for the db module in mcp_server_watchlist."""

import pytest
from mcp_server_watchlist import db

@pytest.mark.asyncio
async def test_init_db_creates_table(tmp_path):
    """Test that init_db creates the watchlist table in the database."""
    orig_path = db.DB_PATH
    db.DB_PATH = str(tmp_path / "test_watchlist.db")
    await db.init_db()
    row = await db.fetch_one(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='watchlist'"
    )
    assert row is not None
    db.DB_PATH = orig_path


def test_get_database_url_defaults_to_sqlite(monkeypatch):
    """Test default DB URL uses local SQLite when DATABASE_URL is unset."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    db.DB_PATH = "watchlist.db"
    assert db.get_database_url() == "sqlite+aiosqlite:///watchlist.db"


def test_get_database_url_normalizes_postgres(monkeypatch):
    """Test PostgreSQL URLs are normalized to asyncpg driver."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@db.example.com:5432/watchlist")
    assert db.get_database_url().startswith("postgresql+asyncpg://")
