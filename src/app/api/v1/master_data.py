"""Master data endpoints for avatar styles, colors, and tints."""

from typing import Optional
from uuid import UUID
from functools import lru_cache
import time

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.avatar_style import AvatarStyle
from app.models.avatar_color import AvatarColor
from app.models.tint_palette import TintPalette
from app.schemas.master_data import AvatarStyleResponse, AvatarColorResponse, TintPaletteResponse
from app.schemas.base import SuccessResponse, PaginationParams

router = APIRouter(prefix="/master", tags=["master-data"])

# In-memory cache configuration
_CACHE_TTL_SECONDS = 300  # 5 minutes
_avatar_styles_cache: dict = {"data": None, "timestamp": 0, "total": 0}
_avatar_style_detail_cache: dict = {}
_avatar_colors_cache: dict = {"data": None, "timestamp": 0, "total": 0}
_tint_palette_cache: dict = {"data": None, "timestamp": 0, "total": 0}


def _is_cache_valid() -> bool:
    """Check if the cache is still valid based on TTL."""
    if _avatar_styles_cache["data"] is None:
        return False
    return (time.time() - _avatar_styles_cache["timestamp"]) < _CACHE_TTL_SECONDS


def _invalidate_cache():
    """Invalidate the avatar styles cache."""
    global _avatar_styles_cache, _avatar_style_detail_cache, _avatar_colors_cache, _tint_palette_cache
    _avatar_styles_cache = {"data": None, "timestamp": 0, "total": 0}
    _avatar_style_detail_cache = {}
    _avatar_colors_cache = {"data": None, "timestamp": 0, "total": 0}
    _tint_palette_cache = {"data": None, "timestamp": 0, "total": 0}


@router.get("/avatar-styles", response_model=SuccessResponse[list[AvatarStyleResponse]])
async def list_avatar_styles(
    limit: int = Query(default=50, ge=1, le=50, description="Max items to return (max 50)"),
    offset: int = Query(default=0, ge=0, description="Items to skip"),
    db: AsyncSession = Depends(get_session),
):
    """
    List all active avatar styles with pagination.
    
    Returns avatar styles sorted by display_order in ascending order.
    Only returns active styles (is_active=True).
    Results are cached in memory for 5 minutes.
    
    **Validates: Requirements 5.1, 5.4, 5.5, 5.6**
    """
    # Check cache first
    if _is_cache_valid() and _avatar_styles_cache["data"] is not None:
        cached_data = _avatar_styles_cache["data"]
        total = _avatar_styles_cache["total"]
        # Apply pagination to cached data
        paginated_data = cached_data[offset:offset + limit]
        return SuccessResponse(
            success=True,
            data=paginated_data,
            total=total,
        )
    
    # Query database for active avatar styles
    count_query = select(func.count()).select_from(AvatarStyle).where(
        AvatarStyle.is_active == True
    )
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0
    
    query = (
        select(AvatarStyle)
        .where(AvatarStyle.is_active == True)
        .order_by(AvatarStyle.display_order.asc())
    )
    result = await db.execute(query)
    styles = result.scalars().all()
    
    # Convert to response models (without svg_template for list view)
    style_responses = [
        AvatarStyleResponse(
            id=style.id,
            name=style.name,
            slug=style.slug,
            description=style.description,
            svg_template=None,  # Exclude SVG template from list view
            animation_type=style.animation_type,
            animation_duration=style.animation_duration,
            color_customizable=style.color_customizable,
            display_order=style.display_order,
            is_active=style.is_active,
            created_at=style.created_at,
        )
        for style in styles
    ]
    
    # Update cache
    _avatar_styles_cache["data"] = style_responses
    _avatar_styles_cache["timestamp"] = time.time()
    _avatar_styles_cache["total"] = total
    
    # Apply pagination
    paginated_data = style_responses[offset:offset + limit]
    
    return SuccessResponse(
        success=True,
        data=paginated_data,
        total=total,
    )


@router.get("/avatar-styles/{style_id}", response_model=SuccessResponse[AvatarStyleResponse])
async def get_avatar_style(
    style_id: UUID,
    db: AsyncSession = Depends(get_session),
):
    """
    Get a specific avatar style by ID.
    
    Returns the complete style including the SVG template.
    Results are cached in memory for 5 minutes.
    
    **Validates: Requirements 5.3**
    """
    # Check cache first
    cache_key = str(style_id)
    if cache_key in _avatar_style_detail_cache:
        cached_entry = _avatar_style_detail_cache[cache_key]
        if (time.time() - cached_entry["timestamp"]) < _CACHE_TTL_SECONDS:
            return SuccessResponse(
                success=True,
                data=cached_entry["data"],
            )
    
    # Query database for the specific avatar style
    query = select(AvatarStyle).where(AvatarStyle.id == style_id)
    result = await db.execute(query)
    style = result.scalar_one_or_none()
    
    if style is None:
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "error": "RESOURCE_NOT_FOUND",
                "message": f"Avatar style with id {style_id} not found",
            }
        )
    
    # Convert to response model (include svg_template for detail view)
    style_response = AvatarStyleResponse(
        id=style.id,
        name=style.name,
        slug=style.slug,
        description=style.description,
        svg_template=style.svg_template,  # Include SVG template in detail view
        animation_type=style.animation_type,
        animation_duration=style.animation_duration,
        color_customizable=style.color_customizable,
        display_order=style.display_order,
        is_active=style.is_active,
        created_at=style.created_at,
    )
    
    # Update cache
    _avatar_style_detail_cache[cache_key] = {
        "data": style_response,
        "timestamp": time.time(),
    }
    
    return SuccessResponse(
        success=True,
        data=style_response,
    )


@router.get("/avatar-colors", response_model=SuccessResponse[list[AvatarColorResponse]])
async def list_avatar_colors(
    limit: int = Query(default=50, ge=1, le=50, description="Max items to return (max 50)"),
    offset: int = Query(default=0, ge=0, description="Items to skip"),
    db: AsyncSession = Depends(get_session),
):
    """
    List all active avatar colors with pagination.
    
    Returns avatar colors sorted by display_order in ascending order.
    Only returns active colors (is_active=True).
    Results are cached in memory for 5 minutes.
    
    **Validates: Requirements 6.1, 6.2, 6.3**
    """
    # Check cache first
    if _avatar_colors_cache["data"] is not None:
        cache_age = time.time() - _avatar_colors_cache["timestamp"]
        if cache_age < _CACHE_TTL_SECONDS:
            cached_data = _avatar_colors_cache["data"]
            total = _avatar_colors_cache["total"]
            # Apply pagination to cached data
            paginated_data = cached_data[offset:offset + limit]
            return SuccessResponse(
                success=True,
                data=paginated_data,
                total=total,
            )
    
    # Query database for active avatar colors
    count_query = select(func.count()).select_from(AvatarColor).where(
        AvatarColor.is_active == True
    )
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0
    
    query = (
        select(AvatarColor)
        .where(AvatarColor.is_active == True)
        .order_by(AvatarColor.display_order.asc())
    )
    result = await db.execute(query)
    colors = result.scalars().all()
    
    # Convert to response models
    color_responses = [
        AvatarColorResponse(
            id=color.id,
            name=color.name,
            hex_code=color.hex_code,
            rgb=color.rgb or "",
            hsl=color.hsl or "",
            display_order=color.display_order,
            is_active=color.is_active,
            created_at=color.created_at,
        )
        for color in colors
    ]
    
    # Update cache
    _avatar_colors_cache["data"] = color_responses
    _avatar_colors_cache["timestamp"] = time.time()
    _avatar_colors_cache["total"] = total
    
    # Apply pagination
    paginated_data = color_responses[offset:offset + limit]
    
    return SuccessResponse(
        success=True,
        data=paginated_data,
        total=total,
    )


@router.get("/tint-palette", response_model=SuccessResponse[list[TintPaletteResponse]])
async def list_tint_palette(
    limit: int = Query(default=50, ge=1, le=50, description="Max items to return (max 50)"),
    offset: int = Query(default=0, ge=0, description="Items to skip"),
    db: AsyncSession = Depends(get_session),
):
    """
    List all active tints with pagination.
    
    Returns tints sorted by display_order in ascending order.
    Only returns active tints (is_active=True).
    Results are cached in memory for 5 minutes.
    
    **Validates: Requirements 7.1, 7.2, 7.4**
    """
    # Check cache first
    if _tint_palette_cache["data"] is not None:
        cache_age = time.time() - _tint_palette_cache["timestamp"]
        if cache_age < _CACHE_TTL_SECONDS:
            cached_data = _tint_palette_cache["data"]
            total = _tint_palette_cache["total"]
            # Apply pagination to cached data
            paginated_data = cached_data[offset:offset + limit]
            return SuccessResponse(
                success=True,
                data=paginated_data,
                total=total,
            )
    
    # Query database for active tints
    count_query = select(func.count()).select_from(TintPalette).where(
        TintPalette.is_active == True
    )
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0
    
    query = (
        select(TintPalette)
        .where(TintPalette.is_active == True)
        .order_by(TintPalette.display_order.asc())
    )
    result = await db.execute(query)
    tints = result.scalars().all()
    
    # Convert to response models
    tint_responses = [
        TintPaletteResponse(
            id=tint.id,
            name=tint.name,
            hsl=tint.hsl,
            hex_code=tint.hex_code or "",
            category=tint.category or "",
            display_order=tint.display_order,
            is_active=tint.is_active,
            created_at=tint.created_at,
        )
        for tint in tints
    ]
    
    # Update cache
    _tint_palette_cache["data"] = tint_responses
    _tint_palette_cache["timestamp"] = time.time()
    _tint_palette_cache["total"] = total
    
    # Apply pagination
    paginated_data = tint_responses[offset:offset + limit]
    
    return SuccessResponse(
        success=True,
        data=paginated_data,
        total=total,
    )
