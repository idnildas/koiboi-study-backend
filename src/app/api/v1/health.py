"""Health check endpoints."""

import platform
import sys
from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.db.session import get_session
from app.core.config import settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check():
    """Basic health check — returns 200 OK with version info."""
    return {
        "success": True,
        "status": "ok",
        "version": "1.0.0",
        "app": settings.APP_NAME,
    }


@router.get("/ready")
async def readiness_check(response: Response, db: AsyncSession = Depends(get_session)):
    """Readiness check — verifies database connectivity."""
    try:
        await db.execute(text("SELECT 1"))
        return {"success": True, "status": "ready", "database": "connected"}
    except Exception as exc:
        response.status_code = 503
        return {"success": False, "status": "not_ready", "database": "unavailable", "detail": str(exc)}


@router.get("/live")
async def liveness_check():
    """Liveness check — returns basic system status."""
    return {
        "success": True,
        "status": "alive",
        "python_version": sys.version,
        "platform": platform.system(),
    }
