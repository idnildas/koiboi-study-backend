"""Snippet request and response schemas."""

from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class SnippetCreate(BaseModel):
    """Schema for creating a new code snippet.
    
    Attributes:
        language: Programming language
        code: Source code
        note_id: Optional associated note UUID
    """

    language: str = Field(..., min_length=1, max_length=50, description="Programming language")
    code: str = Field(..., min_length=1, description="Source code")
    note_id: Optional[UUID] = Field(None, description="Associated note UUID")

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        """Validate language is not empty after stripping whitespace."""
        if not v or not v.strip():
            raise ValueError("Language cannot be empty")
        return v.strip()

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        """Validate code is not empty."""
        if not v or not v.strip():
            raise ValueError("Code cannot be empty")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "language": "python",
                "code": "def bfs(graph, start):\n    visited = set()\n    queue = [start]\n    while queue:\n        node = queue.pop(0)\n        if node not in visited:\n            visited.add(node)\n            queue.extend(graph[node])\n    return visited",
                "note_id": "550e8400-e29b-41d4-a716-446655440000",
            }
        }
    }


class SnippetUpdate(BaseModel):
    """Schema for updating a code snippet.
    
    Attributes:
        code: Updated source code (optional)
        output: Execution output (optional)
    """

    code: Optional[str] = Field(None, min_length=1, description="Updated source code")
    output: Optional[str] = Field(None, description="Execution output")

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: Optional[str]) -> Optional[str]:
        """Validate code if provided."""
        if v is not None:
            if not v or not v.strip():
                raise ValueError("Code cannot be empty")
            return v
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "code": "def bfs(graph, start):\n    # Updated implementation\n    pass",
                "output": "Execution result here",
            }
        }
    }


class SnippetResponse(BaseModel):
    """Schema for snippet response.
    
    Attributes:
        id: Snippet UUID
        user_id: Owner user UUID
        note_id: Associated note UUID
        language: Programming language
        code: Source code
        output: Execution output
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    id: UUID = Field(..., description="Snippet UUID")
    user_id: UUID = Field(..., description="Owner user UUID")
    note_id: Optional[UUID] = Field(None, description="Associated note UUID")
    language: str = Field(..., description="Programming language")
    code: str = Field(..., description="Source code")
    output: Optional[str] = Field(None, description="Execution output")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "550e8400-e29b-41d4-a716-446655440001",
                "note_id": "550e8400-e29b-41d4-a716-446655440002",
                "language": "python",
                "code": "def bfs(graph, start):\n    pass",
                "output": "Execution result",
                "created_at": "2026-04-21T10:00:00+00:00",
                "updated_at": "2026-04-21T10:00:00+00:00",
            }
        }
    }
