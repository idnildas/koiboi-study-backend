"""Subject request and response schemas."""

from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class SubjectCreate(BaseModel):
    """Schema for creating a new subject.
    
    Attributes:
        name: Subject name (1-255 characters)
        color_id: Optional UUID of palette color
        description: Optional subject description (max 1000 characters)
    """

    name: str = Field(..., min_length=1, max_length=255, description="Subject name")
    color_id: Optional[UUID] = Field(None, description="Palette color UUID")
    description: Optional[str] = Field(None, max_length=1000, description="Subject description")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name is not empty after stripping whitespace."""
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        """Validate description if provided."""
        if v is not None:
            if not v.strip():
                return None
            return v.strip()
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Data Structures & Algorithms",
                "color_id": "550e8400-e29b-41d4-a716-446655440000",
                "description": "Study materials for DSA",
            }
        }
    }


class SubjectUpdate(BaseModel):
    """Schema for updating a subject.
    
    Attributes:
        name: Updated subject name (optional)
        color_id: Updated palette color UUID (optional)
        description: Updated subject description (optional)
    """

    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Updated subject name")
    color_id: Optional[UUID] = Field(None, description="Updated palette color UUID")
    description: Optional[str] = Field(None, max_length=1000, description="Updated subject description")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate name if provided."""
        if v is not None:
            if not v or not v.strip():
                raise ValueError("Name cannot be empty")
            return v.strip()
        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        """Validate description if provided."""
        if v is not None:
            if not v.strip():
                return None
            return v.strip()
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Advanced DSA",
                "description": "Advanced topics in data structures",
            }
        }
    }


class SubjectResponse(BaseModel):
    """Schema for subject response.
    
    Attributes:
        id: Subject UUID
        user_id: Owner user UUID
        name: Subject name
        color_id: Palette color UUID
        description: Subject description
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    id: UUID = Field(..., description="Subject UUID")
    user_id: UUID = Field(..., description="Owner user UUID")
    name: str = Field(..., description="Subject name")
    color_id: Optional[UUID] = Field(None, description="Palette color UUID")
    description: Optional[str] = Field(None, description="Subject description")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "550e8400-e29b-41d4-a716-446655440001",
                "name": "Data Structures & Algorithms",
                "color_id": "550e8400-e29b-41d4-a716-446655440002",
                "description": "Study materials for DSA",
                "created_at": "2026-04-21T10:00:00+00:00",
                "updated_at": "2026-04-21T10:00:00+00:00",
            }
        }
    }
