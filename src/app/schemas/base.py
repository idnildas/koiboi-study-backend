"""Base response schemas for API responses."""

from typing import Generic, Optional, TypeVar, Any
from pydantic import BaseModel, Field, field_validator

T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    """Generic success response schema.
    
    Used for all successful API responses with optional data, message, and total count.
    
    Attributes:
        success: Always True for success responses
        data: The response data (can be any type)
        message: Optional human-readable message
        total: Optional total count for list endpoints
    """

    success: bool = Field(default=True, description="Always True for success responses")
    data: T = Field(description="Response data")
    message: Optional[str] = Field(default=None, description="Optional success message")
    total: Optional[int] = Field(default=None, description="Total count for list endpoints")

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "data": {"id": "123", "name": "Example"},
                "message": "Operation successful",
                "total": 100,
            }
        }
    }


class ErrorResponse(BaseModel):
    """Error response schema.
    
    Used for all error responses with error code, message, and optional details.
    
    Attributes:
        success: Always False for error responses
        error: Error code (e.g., VALIDATION_ERROR, AUTHENTICATION_ERROR)
        message: Human-readable error message
        details: Optional dictionary with additional error details
    """

    success: bool = Field(default=False, description="Always False for error responses")
    error: str = Field(description="Error code")
    message: str = Field(description="Human-readable error message")
    details: Optional[dict[str, Any]] = Field(
        default=None, description="Optional error details"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": False,
                "error": "VALIDATION_ERROR",
                "message": "Invalid input provided",
                "details": {"field": "email", "reason": "Invalid email format"},
            }
        }
    }


class PaginationParams(BaseModel):
    """Pagination query parameters.
    
    Used for list endpoints to support limit and offset pagination.
    
    Attributes:
        limit: Maximum number of items to return (max 50)
        offset: Number of items to skip (must be >= 0)
    """

    limit: int = Field(default=50, ge=1, description="Max items to return (max 50)")
    offset: int = Field(default=0, ge=0, description="Items to skip (must be >= 0)")

    @field_validator("limit", mode="after")
    @classmethod
    def validate_limit(cls, v: int) -> int:
        """Ensure limit does not exceed maximum of 50."""
        if v > 50:
            return 50
        return v

    model_config = {
        "json_schema_extra": {
            "example": {"limit": 50, "offset": 0}
        }
    }
