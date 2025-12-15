
# Tests for tools.py
import pytest
from mcp_server_watchlist import db, tools

@pytest.mark.asyncio
async def test_add_and_delete_movie(tmp_path):
    test_db = tmp_path / "test_watchlist.db"
    db.DB_PATH = str(test_db)
    await db.init_db()
    # Add movie
    result = await tools.add_movie("Inception", 2010)
    assert "Added: Title: Inception" in result
    # Delete movie
    del_result = await tools.delete_movie("Inception")
    assert "Deleted: Title: Inception" in del_result
