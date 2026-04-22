"""User request and response schemas."""

from typing import Optional
from uuid import UUID
from datetime import datetime
import re
from pydantic import BaseModel, Field, field_validator


class UserCreate(BaseModel):
    """Schema for creating a new user during sign-up.
    
    Attributes:
        name: User's display name (2-100 characters)
        email: User's email address (must be valid email format)
        password: User's password (6-128 characters)
        avatar_style_id: UUID of selected avatar style
        avatar_color_id: UUID of selected avatar color
    """

    name: str = Field(..., min_length=2, max_length=100, description="User display name")
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=6, max_length=128, description="User password")
    avatar_style_id: UUID = Field(..., description="Avatar style UUID")
    avatar_color_id: UUID = Field(..., description="Avatar color UUID")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, v):
            raise ValueError("Invalid email format")
        return v.lower()

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name is not empty after stripping whitespace."""
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password is not empty after stripping whitespace."""
        if not v or not v.strip():
            raise ValueError("Password cannot be empty")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "John Doe",
                "email": "john@example.com",
                "password": "secure_password_123",
                "avatar_style_id": "550e8400-e29b-41d4-a716-446655440000",
                "avatar_color_id": "550e8400-e29b-41d4-a716-446655440001",
            }
        }
    }


class UserUpdate(BaseModel):
    """Schema for updating user profile.
    
    Attributes:
        name: Updated display name (optional)
        avatar_style_id: Updated avatar style UUID (optional)
        avatar_color_id: Updated avatar color UUID (optional)
    """

    name: Optional[str] = Field(None, min_length=2, max_length=100, description="Updated display name")
    avatar_style_id: Optional[UUID] = Field(None, description="Updated avatar style UUID")
    avatar_color_id: Optional[UUID] = Field(None, description="Updated avatar color UUID")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate name is not empty after stripping whitespace."""
        if v is not None:
            if not v or not v.strip():
                raise ValueError("Name cannot be empty")
            return v.strip()
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Jane Doe",
                "avatar_style_id": "550e8400-e29b-41d4-a716-446655440000",
                "avatar_color_id": "550e8400-e29b-41d4-a716-446655440001",
            }
        }
    }


class UserResponse(BaseModel):
    """Schema for user profile response.
    
    Attributes:
        id: User UUID
        name: User's display name
        email: User's email address
        avatar_style_id: UUID of selected avatar style
        avatar_color_id: UUID of selected avatar color
        created_at: Account creation timestamp
        updated_at: Last profile update timestamp
        last_login_at: Last successful login timestamp
        is_active: Account status
    """

    id: UUID = Field(..., description="User UUID")
    name: str = Field(..., description="User display name")
    email: str = Field(..., description="User email address")
    avatar_style_id: UUID = Field(..., description="Avatar style UUID")
    avatar_color_id: UUID = Field(..., description="Avatar color UUID")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last profile update timestamp")
    last_login_at: Optional[datetime] = Field(None, description="Last successful login timestamp")
    is_active: bool = Field(..., description="Account status")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "John Doe",
                "email": "john@example.com",
                "avatar_style_id": "550e8400-e29b-41d4-a716-446655440000",
                "avatar_color_id": "550e8400-e29b-41d4-a716-446655440001",
                "created_at": "2026-04-21T10:00:00+00:00",
                "updated_at": "2026-04-21T10:00:00+00:00",
                "last_login_at": "2026-04-21T10:00:00+00:00",
                "is_active": True,
            }
        }
    }


class ChangePasswordRequest(BaseModel):
    """Schema for password change request.
    
    Attributes:
        current_password: Current password for verification
        new_password: New password (6-128 characters)
    """

    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=6, max_length=128, description="New password")

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password is not empty after stripping whitespace."""
        if not v or not v.strip():
            raise ValueError("Password cannot be empty")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "current_password": "old_password_123",
                "new_password": "new_password_456",
            }
        }
    }
