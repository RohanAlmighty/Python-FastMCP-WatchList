
"""Tests for the db module in mcp_server_watchlist."""

import pytest
import aiosqlite
from mcp_server_watchlist import db

@pytest.mark.asyncio
async def test_init_db_creates_table():
    """Test that init_db creates the watchlist table in the database."""
    orig_path = db.DB_PATH
    db.DB_PATH = ":memory:"
    await db.init_db()
    async with aiosqlite.connect(":memory:") as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                year INTEGER,
                watched INTEGER DEFAULT 0,
                rating REAL
            )
            """
        )
        async with conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='watchlist'"
        ) as cursor:
            row = await cursor.fetchone()
    assert row is not None
    db.DB_PATH = orig_path
