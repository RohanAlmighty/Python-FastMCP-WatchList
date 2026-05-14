
"""Database logic for the watchlist MCP server."""

import os
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from sqlalchemy import Column, Float, Integer, MetaData, String, Table, text
from sqlalchemy.ext.asyncio import create_async_engine

DB_PATH = "watchlist.db"


metadata = MetaData()
watchlist = Table(
    "watchlist",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("title", String, nullable=False),
    Column("year", Integer),
    Column("watched", Integer, default=0),
    Column("rating", Float),
)


def _normalize_database_url(database_url: str) -> str:
    """Normalize common SQLAlchemy URLs to async driver variants."""
    if database_url.startswith("sqlite:///"):
        return database_url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if database_url.startswith("mysql://"):
        return database_url.replace("mysql://", "mysql+aiomysql://", 1)
    return database_url


def get_database_url() -> str:
    """Return the configured database URL, defaulting to local SQLite."""
    configured_url = os.environ.get("DATABASE_URL", "").strip()
    if configured_url:
        return _normalize_database_url(configured_url)
    return f"sqlite+aiosqlite:///{DB_PATH}"


def _make_engine():
    """Build an async engine, converting sslmode query params to connect_args."""
    raw_url = os.environ.get("DATABASE_URL", "").strip()
    url = _normalize_database_url(raw_url) if raw_url else f"sqlite+aiosqlite:///{DB_PATH}"

    parsed = urlparse(url)
    params = parse_qs(parsed.query, keep_blank_values=True)
    sslmode = params.pop("sslmode", [None])[0]
    new_query = urlencode({k: v[0] for k, v in params.items()})
    url = urlunparse(parsed._replace(query=new_query))

    connect_args: dict[str, Any] = {}
    if sslmode in ("require", "verify-ca", "verify-full"):
        connect_args["ssl"] = True

    return create_async_engine(url, connect_args=connect_args)


async def _execute_with_engine(query: str, params: dict[str, Any] | None = None):
    """Execute a statement inside a transaction."""
    engine = _make_engine()
    try:
        async with engine.begin() as conn:
            return await conn.execute(text(query), params or {})
    finally:
        await engine.dispose()


async def fetch_one(query: str, params: dict[str, Any] | None = None):
    """Fetch a single row for the given query."""
    engine = _make_engine()
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text(query), params or {})
            return result.fetchone()
    finally:
        await engine.dispose()


async def fetch_all(query: str, params: dict[str, Any] | None = None):
    """Fetch all rows for the given query."""
    engine = _make_engine()
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text(query), params or {})
            return result.fetchall()
    finally:
        await engine.dispose()


async def execute(query: str, params: dict[str, Any] | None = None):
    """Execute a write statement and commit."""
    await _execute_with_engine(query, params)

async def init_db():
    """Initialize the database and create the watchlist table if it does not exist."""
    engine = _make_engine()
    try:
        async with engine.begin() as conn:
            await conn.run_sync(metadata.create_all)
    finally:
        await engine.dispose()
