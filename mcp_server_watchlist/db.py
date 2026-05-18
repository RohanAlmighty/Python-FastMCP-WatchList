"""Database logic for the watchlist MCP server."""

import logging
import os
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from sqlalchemy import Column, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.engine.url import make_url
from sqlalchemy.exc import ArgumentError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.future import select
from sqlalchemy.orm import declarative_base

DB_PATH = "watchlist.db"
logger = logging.getLogger(__name__)

_engine = None
_session_factory = None


def get_engine():
    """
    Get or create the async engine (singleton).

    Note:
        Caches engine in module-level _engine variable.
    """
    global _engine
    if _engine is None:
        url = _resolve_database_url()
        if url.startswith("sqlite+"):
            _engine = create_async_engine(
                url,
                connect_args={},
                pool_size=1,
                max_overflow=0,
                echo=False,
            )
        else:
            parsed = urlparse(url)
            params = parse_qs(parsed.query, keep_blank_values=True)
            sslmode = params.pop("sslmode", [None])[0]
            new_query = urlencode({k: v[0] for k, v in params.items()})
            if parsed.query:
                url = urlunparse(parsed._replace(query=new_query))
            connect_args: dict[str, Any] = {}
            if sslmode in ("require", "verify-ca", "verify-full"):
                connect_args["ssl"] = True
            _engine = create_async_engine(
                url,
                connect_args=connect_args,
                pool_size=10,
                max_overflow=20,
                echo=False,
                pool_pre_ping=True,
            )
    return _engine


def get_session_factory():
    """
    Get or create the async session factory (singleton).

    Note:
        Caches factory in module-level _session_factory variable.
    """
    global _session_factory
    if _session_factory is None:
        engine = get_engine()
        _session_factory = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
    return _session_factory


async def get_session() -> AsyncSession:
    """
    Get an async session for database operations.

    Note:
        Uses connection pooling via session factory for efficiency.
    """
    session_factory = get_session_factory()
    return session_factory()


def _normalize_database_url(database_url: str) -> str:
    """
    Normalize common SQLAlchemy URLs to async driver variants.

    Args:
        database_url: The database URL to normalize.

    Note:
        Supports sqlite, postgres, postgresql, and mysql databases.
    """
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
    """
    Return a configured DB URL from env vars, preferring DATABASE_URL over DB_URL.

    Note:
        Checks DATABASE_URL first, then DB_URL as fallback.
    """
    database_url = os.environ.get("DATABASE_URL", "").strip()
    if database_url:
        return database_url

    db_url = os.environ.get("DB_URL", "").strip()
    if db_url:
        return db_url

    return ""


def _default_database_url() -> str:
    """
    Return the local SQLite default URL.

    Note:
        Defaults to watchlist.db in the current directory.
    """
    return f"sqlite+aiosqlite:///{DB_PATH}"


def _resolve_database_url() -> str:
    """
    Resolve configured DB URL and fallback to default if missing or invalid.

    Note:
        Uses environment variables for configuration; falls back to SQLite.
    """
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
    """
    Return the resolved database URL used by the application.

    Note:
        Falls back to SQLite default if configured URL is invalid.
    """
    return _resolve_database_url()


def _make_engine():
    """
    Build an async engine, converting sslmode query params to connect_args.

    Note:
        Internal helper that wraps get_engine().
    """
    return get_engine()


# ORM Models
Base = declarative_base()


class Watchlist(Base):
    __tablename__ = "watchlists"

    id = Column(Integer, primary_key=True, autoincrement=True)
    coolname = Column(String, nullable=False, unique=True)


class WatchlistItem(Base):
    __tablename__ = "watchlist"

    id = Column(Integer, primary_key=True, autoincrement=True)
    watchlist_id = Column(Integer, ForeignKey("watchlists.id"), nullable=False)
    title = Column(String, nullable=False)
    year = Column(Integer)
    watched = Column(Integer, default=0)
    rating = Column(Float)

    __table_args__ = (UniqueConstraint("watchlist_id", "title"),)


async def init_db():
    """
    Initialize the database and create all tables if they do not exist.

    Note:
        Idempotent; safe to call multiple times.
    """
    engine = get_engine()
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        return True
    except (SQLAlchemyError, OSError, RuntimeError):
        logger.exception("Database initialization failed")
        return False


async def check_database_connection() -> bool:
    """
    Return True when a simple DB read succeeds using ORM.

    Note:
        Used for health checks; returns False on any exception.
    """
    session = None
    try:
        session = await get_session()
        result = await session.execute(select(1))
        return result.scalar() == 1
    except Exception:
        logger.exception("Database read failed (check_database_connection)")
        return False
    finally:
        if session is not None:
            await session.close()


async def get_watchlist_id(session: AsyncSession, coolname: str) -> int | None:
    """
    Return the watchlist id for the given coolname, or None if not found.

    Args:
        session: AsyncSession for database operations.
        coolname: The coolname to look up.

    Note:
        Returns None if the watchlist does not exist.
    """
    result = await session.execute(select(Watchlist).filter_by(coolname=coolname))
    watchlist = result.scalars().first()
    return watchlist.id if watchlist else None
