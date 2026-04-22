from fastapi import FastAPI
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse
from scalar_fastapi import get_scalar_api_reference
from sqlalchemy import text

from app.api.v1.routes import router as v1_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.middleware.logging import RequestLoggingMiddleware

import logging

logger = logging.getLogger("uvicorn.error")

_DESCRIPTION = """
Koiboi is a personal study workspace and note-taking backend.

## Features
- **Auth** — sign-up, sign-in, JWT sessions, password reset
- **Subjects** — top-level study areas with colour customisation
- **Topics** — subtopics with status and confidence tracking
- **Notes** — markdown notes with hand-drawn scribble annotations
- **Materials** — PDF upload, download, and management
- **Snippets** — playground code snippets in any language
- **Master Data** — avatar styles, avatar colours, tint palette

## Authentication
Protected endpoints require a Bearer token in the `Authorization` header:
```
Authorization: Bearer <token>
```
Obtain a token via `POST /api/v1/auth/sign-in` or `POST /api/v1/auth/sign-up`.
"""


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        description=_DESCRIPTION,
        version="1.0.0",
        contact={"name": "Koiboi API"},
        license_info={"name": "MIT"},
        # Disable the default docs so we can serve custom ones
        docs_url=None,
        redoc_url=None,
        openapi_url="/api/v1/openapi.json",
    )

    app.add_middleware(RequestLoggingMiddleware)
    app.include_router(v1_router, prefix="/api/v1")

    # ── Scalar (primary — best UX) ────────────────────────────────────────
    @app.get("/docs", include_in_schema=False)
    async def scalar_docs() -> HTMLResponse:
        return get_scalar_api_reference(
            openapi_url="/api/v1/openapi.json",
            title=f"{settings.APP_NAME} — API Reference",
        )

    # ── Swagger UI (fallback) ─────────────────────────────────────────────
    @app.get("/swagger", include_in_schema=False)
    async def swagger_docs() -> HTMLResponse:
        return get_swagger_ui_html(
            openapi_url="/api/v1/openapi.json",
            title=f"{settings.APP_NAME} — Swagger UI",
            swagger_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
        )

    # ── ReDoc (fallback) ──────────────────────────────────────────────────
    @app.get("/redoc", include_in_schema=False)
    async def redoc_docs() -> HTMLResponse:
        return get_redoc_html(
            openapi_url="/api/v1/openapi.json",
            title=f"{settings.APP_NAME} — ReDoc",
        )

    @app.on_event("startup")
    async def on_startup():
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            logger.info("Database connection successful")
        except Exception as exc:
            logger.exception("Database connection check failed: %s", exc)

    return app


app = create_app()


@app.get("/", include_in_schema=False)
async def root():
    return {
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "docs": {
            "scalar": "/docs",
            "swagger": "/swagger",
            "redoc": "/redoc",
            "openapi_json": "/api/v1/openapi.json",
        },
    }
