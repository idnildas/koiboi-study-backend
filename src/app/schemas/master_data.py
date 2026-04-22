"""Master data response schemas for avatar styles, colors, and tints."""

from typing import Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class AvatarStyleResponse(BaseModel):
    """Schema for avatar style response.
    
    Attributes:
        id: Avatar style UUID
        name: Style name
        slug: URL-friendly slug
        description: Animation description
        svg_template: SVG with animations (only in detail view)
        animation_type: Type of animation
        animation_duration: Duration in seconds
        color_customizable: Whether color can be customized
        display_order: UI display order
        is_active: Whether style is available
        created_at: Creation timestamp
    """

    id: UUID = Field(..., description="Avatar style UUID")
    name: str = Field(..., description="Style name")
    slug: str = Field(..., description="URL-friendly slug")
    description: Optional[str] = Field(None, description="Animation description")
    svg_template: Optional[str] = Field(None, description="SVG with animations")
    animation_type: str = Field(..., description="Type of animation")
    animation_duration: Decimal = Field(..., description="Duration in seconds")
    color_customizable: bool = Field(..., description="Whether color can be customized")
    display_order: int = Field(..., description="UI display order")
    is_active: bool = Field(..., description="Whether style is available")
    created_at: datetime = Field(..., description="Creation timestamp")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Floating Bubble",
                "slug": "floating-bubble",
                "description": "A gentle floating animation",
                "svg_template": "<svg>...</svg>",
                "animation_type": "float",
                "animation_duration": 3.0,
                "color_customizable": True,
                "display_order": 1,
                "is_active": True,
                "created_at": "2026-04-21T10:00:00+00:00",
            }
        }
    }


class AvatarColorResponse(BaseModel):
    """Schema for avatar color response.
    
    Attributes:
        id: Avatar color UUID
        name: Color name
        hex_code: Hex color code
        rgb: RGB representation
        hsl: HSL representation
        display_order: UI display order
        is_active: Whether color is available
        created_at: Creation timestamp
    """

    id: UUID = Field(..., description="Avatar color UUID")
    name: str = Field(..., description="Color name")
    hex_code: str = Field(..., description="Hex color code")
    rgb: str = Field(..., description="RGB representation")
    hsl: str = Field(..., description="HSL representation")
    display_order: int = Field(..., description="UI display order")
    is_active: bool = Field(..., description="Whether color is available")
    created_at: datetime = Field(..., description="Creation timestamp")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Ocean Blue",
                "hex_code": "#0066CC",
                "rgb": "rgb(0, 102, 204)",
                "hsl": "hsl(210, 100%, 40%)",
                "display_order": 1,
                "is_active": True,
                "created_at": "2026-04-21T10:00:00+00:00",
            }
        }
    }


class TintPaletteResponse(BaseModel):
    """Schema for tint palette response.
    
    Attributes:
        id: Tint UUID
        name: Tint name
        hsl: HSL color triplet
        hex_code: Hex equivalent
        category: Color category (warm, cool, neutral)
        display_order: UI display order
        is_active: Whether tint is available
        created_at: Creation timestamp
    """

    id: UUID = Field(..., description="Tint UUID")
    name: str = Field(..., description="Tint name")
    hsl: str = Field(..., description="HSL color triplet")
    hex_code: str = Field(..., description="Hex equivalent")
    category: str = Field(..., description="Color category")
    display_order: int = Field(..., description="UI display order")
    is_active: bool = Field(..., description="Whether tint is available")
    created_at: datetime = Field(..., description="Creation timestamp")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Dusty Rose",
                "hsl": "hsl(350, 60%, 70%)",
                "hex_code": "#E8A0A0",
                "category": "warm",
                "display_order": 1,
                "is_active": True,
                "created_at": "2026-04-21T10:00:00+00:00",
            }
        }
    }
