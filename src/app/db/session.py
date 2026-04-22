from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings


# Create async engine with connection pooling configuration
# pool_size: number of connections to keep in the pool
# max_overflow: maximum number of connections to create beyond pool_size
# pool_recycle: recycle connections after this many seconds (prevents stale connections)
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    future=True,
    echo=False,
    pool_size=20,
    max_overflow=40,
    pool_recycle=3600,
)

# Create async session factory with request-scoped sessions
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Async generator dependency that yields an `AsyncSession`.

    Provides request-scoped database sessions for FastAPI endpoints.
    Automatically handles transaction rollback on exceptions and commit on success.

    Use in FastAPI endpoints like: `async def endpoint(db: AsyncSession = Depends(get_session))`.
    """
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
