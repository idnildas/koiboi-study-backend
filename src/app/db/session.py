from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


engine: AsyncEngine = create_async_engine(settings.DATABASE_URL, future=True, echo=False)

async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Async generator dependency that yields an `AsyncSession`.

    Use in FastAPI endpoints like: `async def endpoint(db: AsyncSession = Depends(get_session))`.
    """
    async with async_session() as session:
        yield session
