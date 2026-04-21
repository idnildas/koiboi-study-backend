from fastapi import FastAPI
from app.api.v1.routes import router as v1_router
from app.core.config import settings

# DB imports for creating tables on startup (development convenience)
from app.db.session import engine
from app.db.base import Base
from sqlalchemy import text
import logging

logger = logging.getLogger("uvicorn.error")


def create_app() -> FastAPI:
    app = FastAPI(title=settings.APP_NAME)
    app.include_router(v1_router, prefix="/api/v1")

    @app.on_event("startup")
    async def on_startup():
        try:
            # Create DB tables automatically in development (uses SQLAlchemy run_sync)
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            # Quick connection check: run a simple SELECT 1
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))

            logger.info("Database connection successful")
        except Exception as exc:
            logger.exception("Database connection check failed: %s", exc)

    return app


app = create_app()


@app.get("/")
async def root():
    return {"message": f"{settings.APP_NAME} is running"}
