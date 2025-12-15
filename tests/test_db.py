
# Tests for db.py
import pytest
import aiosqlite
from mcp_server_watchlist import db

DB_PATH = db.DB_PATH

@pytest.mark.asyncio
async def test_init_db_creates_table(tmp_path):
    test_db = tmp_path / "test_watchlist.db"
    # Patch DB_PATH for test
    db.DB_PATH = str(test_db)
    await db.init_db()
    async with aiosqlite.connect(str(test_db)) as conn:
        async with conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='watchlist'") as cursor:
            row = await cursor.fetchone()
    assert row is not None
    db.DB_PATH = DB_PATH  # Restore
