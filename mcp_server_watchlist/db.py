
"""Database logic for the watchlist MCP server."""

import aiosqlite

DB_PATH = "watchlist.db"

async def init_db():
    """Initialize the database and create the watchlist table if it does not exist."""
    async with aiosqlite.connect(DB_PATH) as conn:
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
        await conn.commit()
