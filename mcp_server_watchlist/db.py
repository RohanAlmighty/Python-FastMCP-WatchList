
"""Database logic for the watchlist MCP server."""

import os
import logging
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from sqlalchemy import Column, Float, ForeignKey, Integer, MetaData, String, Table, UniqueConstraint, text
from sqlalchemy.engine.url import make_url
from sqlalchemy.exc import ArgumentError, SQLAlchemyError
from sqlalchemy.ext.asyncio import create_async_engine

DB_PATH = "watchlist.db"
logger = logging.getLogger(__name__)


metadata = MetaData()
watchlists = Table(
    "watchlists",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("coolname", String, nullable=False, unique=True),
)
watchlist = Table(
    "watchlist",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("watchlist_id", Integer, ForeignKey("watchlists.id"), nullable=False),
    Column("title", String, nullable=False),
    Column("year", Integer),
    Column("watched", Integer, default=0),
    Column("rating", Float),
    UniqueConstraint("watchlist_id", "title"),
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


def _get_configured_database_url() -> str:
    """Return a configured DB URL from env vars, preferring DATABASE_URL over DB_URL."""
    database_url = os.environ.get("DATABASE_URL", "").strip()
    if database_url:
        return database_url

    db_url = os.environ.get("DB_URL", "").strip()
    if db_url:
        return db_url

    return ""


def _default_database_url() -> str:
    """Return the local SQLite default URL."""
    return f"sqlite+aiosqlite:///{DB_PATH}"


def _resolve_database_url() -> str:
    """Resolve configured DB URL and fallback to default if missing or invalid."""
    configured_url = _get_configured_database_url()
    if not configured_url:
        return _default_database_url()

    normalized_url = _normalize_database_url(configured_url)
    try:
        make_url(normalized_url)
    except ArgumentError:
        return _default_database_url()

    return normalized_url


def get_database_url() -> str:
    """Return the resolved database URL used by the application."""
    return _resolve_database_url()


def _make_engine():
    """Build an async engine, converting sslmode query params to connect_args."""
    url = _resolve_database_url()

    # Keep sqlite URL shape intact (sqlite+aiosqlite:///path) to avoid path corruption.
    if url.startswith("sqlite+"):
        return create_async_engine(url, connect_args={})

    parsed = urlparse(url)
    params = parse_qs(parsed.query, keep_blank_values=True)
    sslmode = params.pop("sslmode", [None])[0]
    new_query = urlencode({k: v[0] for k, v in params.items()})
    if parsed.query:
        url = urlunparse(parsed._replace(query=new_query))

    connect_args: dict[str, Any] = {}
    if sslmode in ("require", "verify-ca", "verify-full"):
        connect_args["ssl"] = True

    return create_async_engine(url, connect_args=connect_args)


async def _execute_with_engine(query: str, params: dict[str, Any] | None = None) -> bool:
    """Execute a statement inside a transaction."""
    engine = _make_engine()
    try:
        async with engine.begin() as conn:
            await conn.execute(text(query), params or {})
            return True
    except (SQLAlchemyError, OSError, RuntimeError):
        logger.exception("Database write failed")
        return False
    finally:
        await engine.dispose()


async def fetch_one(query: str, params: dict[str, Any] | None = None):
    """Fetch a single row for the given query."""
    engine = _make_engine()
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text(query), params or {})
            return result.fetchone()
    except (SQLAlchemyError, OSError, RuntimeError):
        logger.exception("Database read failed (fetch_one)")
        return None
    finally:
        await engine.dispose()


async def fetch_all(query: str, params: dict[str, Any] | None = None):
    """Fetch all rows for the given query."""
    engine = _make_engine()
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text(query), params or {})
            return result.fetchall()
    except (SQLAlchemyError, OSError, RuntimeError):
        logger.exception("Database read failed (fetch_all)")
        return []
    finally:
        await engine.dispose()


async def execute(query: str, params: dict[str, Any] | None = None) -> bool:
    """Execute a write statement and commit."""
    return await _execute_with_engine(query, params)

async def init_db():
    """Initialize the database and create all tables if they do not exist."""
    engine = _make_engine()
    try:
        async with engine.begin() as conn:
            await conn.run_sync(metadata.create_all)
            return True
    except (SQLAlchemyError, OSError, RuntimeError):
        logger.exception("Database initialization failed")
        return False
    finally:
        await engine.dispose()


async def check_database_connection() -> bool:
    """Return True when a simple DB read succeeds."""
    row = await fetch_one("SELECT 1")
    return row is not None


async def get_watchlist_id(coolname: str) -> int | None:
    """Return the watchlist id for the given coolname, or None if not found."""
    row = await fetch_one(
        "SELECT id FROM watchlists WHERE coolname = :coolname",
        {"coolname": coolname},
    )
    return row[0] if row else None
