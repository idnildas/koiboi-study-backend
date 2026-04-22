"""Topic request and response schemas."""

from typing import Optional, Literal
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class TopicCreate(BaseModel):
    """Schema for creating a new topic.
    
    Attributes:
        name: Topic name (1-255 characters)
        tint_id: Optional UUID of tint palette color
    """

    name: str = Field(..., min_length=1, max_length=255, description="Topic name")
    tint_id: Optional[UUID] = Field(None, description="Tint palette color UUID")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name is not empty after stripping whitespace."""
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Graph Algorithms",
                "tint_id": "550e8400-e29b-41d4-a716-446655440000",
            }
        }
    }


class TopicUpdate(BaseModel):
    """Schema for updating a topic.
    
    Attributes:
        name: Updated topic name (optional)
        status: Updated status (optional)
        confidence: Updated confidence level 0-5 (optional)
        tint_id: Updated tint palette color UUID (optional)
    """

    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Updated topic name")
    status: Optional[Literal["not-started", "in-progress", "revising", "completed"]] = Field(
        None, description="Topic status"
    )
    confidence: Optional[int] = Field(None, ge=0, le=5, description="Confidence level 0-5")
    tint_id: Optional[UUID] = Field(None, description="Updated tint palette color UUID")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate name if provided."""
        if v is not None:
            if not v or not v.strip():
                raise ValueError("Name cannot be empty")
            return v.strip()
        return v

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: Optional[int]) -> Optional[int]:
        """Validate confidence is in valid range."""
        if v is not None and (v < 0 or v > 5):
            raise ValueError("Confidence must be between 0 and 5")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Advanced Graph Algorithms",
                "status": "in-progress",
                "confidence": 3,
            }
        }
    }


class TopicResponse(BaseModel):
    """Schema for topic response.
    
    Attributes:
        id: Topic UUID
        subject_id: Parent subject UUID
        name: Topic name
        status: Topic status (not-started, in-progress, revising, completed)
        confidence: Confidence level 0-5
        tint_id: Tint palette color UUID
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    id: UUID = Field(..., description="Topic UUID")
    subject_id: UUID = Field(..., description="Parent subject UUID")
    name: str = Field(..., description="Topic name")
    status: str = Field(..., description="Topic status")
    confidence: int = Field(..., ge=0, le=5, description="Confidence level 0-5")
    tint_id: Optional[UUID] = Field(None, description="Tint palette color UUID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "subject_id": "550e8400-e29b-41d4-a716-446655440001",
                "name": "Graph Algorithms",
                "status": "in-progress",
                "confidence": 3,
                "tint_id": "550e8400-e29b-41d4-a716-446655440002",
                "created_at": "2026-04-21T10:00:00+00:00",
                "updated_at": "2026-04-21T10:00:00+00:00",
            }
        }
    }
