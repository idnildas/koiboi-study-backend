"""Material request and response schemas."""

from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class MaterialCreate(BaseModel):
    """Schema for creating a new material (metadata only, file uploaded separately).
    
    Attributes:
        title: Material title (1-255 characters)
    """

    title: str = Field(..., min_length=1, max_length=255, description="Material title")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Validate title is not empty after stripping whitespace."""
        if not v or not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "Algorithm Design Manual",
            }
        }
    }


class MaterialUpdate(BaseModel):
    """Schema for updating material metadata.
    
    Attributes:
        title: Updated material title (optional)
        page_count: Updated page count (optional)
    """

    title: Optional[str] = Field(None, min_length=1, max_length=255, description="Updated material title")
    page_count: Optional[int] = Field(None, ge=1, description="Page count")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        """Validate title if provided."""
        if v is not None:
            if not v or not v.strip():
                raise ValueError("Title cannot be empty")
            return v.strip()
        return v

    @field_validator("page_count")
    @classmethod
    def validate_page_count(cls, v: Optional[int]) -> Optional[int]:
        """Validate page count is positive."""
        if v is not None and v < 1:
            raise ValueError("Page count must be a positive integer")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "Updated Algorithm Design Manual",
                "page_count": 350,
            }
        }
    }


class MaterialResponse(BaseModel):
    """Schema for material response.
    
    Attributes:
        id: Material UUID
        subject_id: Parent subject UUID
        title: Material title
        file_name: Original filename
        mime_type: MIME type (always application/pdf)
        file_size: File size in bytes
        page_count: Number of pages
        storage_key: Unique cloud storage key
        created_at: Upload timestamp
        updated_at: Last update timestamp
    """

    id: UUID = Field(..., description="Material UUID")
    subject_id: UUID = Field(..., description="Parent subject UUID")
    title: str = Field(..., description="Material title")
    file_name: str = Field(..., description="Original filename")
    mime_type: str = Field(..., description="MIME type")
    file_size: int = Field(..., ge=0, description="File size in bytes")
    page_count: Optional[int] = Field(None, description="Number of pages")
    storage_key: str = Field(..., description="Cloud storage key")
    created_at: datetime = Field(..., description="Upload timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "subject_id": "550e8400-e29b-41d4-a716-446655440001",
                "title": "Algorithm Design Manual",
                "file_name": "algorithm_design.pdf",
                "mime_type": "application/pdf",
                "file_size": 5242880,
                "page_count": 350,
                "storage_key": "materials/user123/material456/algorithm_design.pdf",
                "created_at": "2026-04-21T10:00:00+00:00",
                "updated_at": "2026-04-21T10:00:00+00:00",
            }
        }
    }
