import os
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

DEFAULT_SQLITE_URL = "sqlite+aiosqlite:///./mplads.db"

# Local prototype defaults to SQLite. Set DATABASE_URL for PostgreSQL.
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_SQLITE_URL)

use_sqlite = DATABASE_URL.startswith("sqlite")
if not use_sqlite:
    try:
        import asyncpg
    except ImportError:
        use_sqlite = True
        DATABASE_URL = DEFAULT_SQLITE_URL

if use_sqlite:
    if not DATABASE_URL.startswith("sqlite"):
        DATABASE_URL = DEFAULT_SQLITE_URL
    engine = create_async_engine(DATABASE_URL, connect_args={"check_same_thread": False}, echo=False)
else:
    engine = create_async_engine(
        DATABASE_URL,
        connect_args={
            "statement_cache_size": 0,
            "prepared_statement_cache_size": 0
        },
        pool_pre_ping=True,
        echo=False
    )

def get_session_factory():
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )

AsyncSessionLocal = get_session_factory()
Base = declarative_base()

async def init_db():
    """Creates all database tables based on SQLAlchemy metadata, with automatic fallback if PostgreSQL database does not exist."""
    global engine, AsyncSessionLocal
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as err:
        if "mplads_db" in str(err) or "InvalidCatalogNameError" in str(err) or "ConnectionRefused" in str(err):
            print(f"[DB Notice] PostgreSQL connection notice ({err}). Auto-switching to SQLite local database.")
            engine = create_async_engine(DEFAULT_SQLITE_URL, connect_args={"check_same_thread": False}, echo=False)
            AsyncSessionLocal.configure(bind=engine)
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        else:
            raise err

async def get_db():
    """Dependency for providing async database sessions in FastAPI routes."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
