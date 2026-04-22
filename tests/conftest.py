"""Test configuration for endpoint tests.

Overrides the database session dependency to use NullPool, which avoids
asyncpg connection pool issues when pytest-asyncio creates a new event loop
per test function.

IMPORTANT: The routes use `from app.db.session import get_session`, so we
must import from the same path to get the same function object for the override.
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

# Must import from app.* to match the function object used by the routes
from app.core.config import settings
from app.db.session import get_session
from app.main import app


@pytest.fixture(autouse=True)
def override_db_session():
    """Override get_session to use NullPool engine for each test.

    This prevents asyncpg 'attached to a different loop' errors that occur
    when the module-level connection pool is reused across different event loops.
    """
    async def _get_test_session():
        engine = create_async_engine(
            settings.DATABASE_URL,
            poolclass=NullPool,
        )
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        async with async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
        await engine.dispose()

    app.dependency_overrides[get_session] = _get_test_session
    yield
    app.dependency_overrides.pop(get_session, None)
