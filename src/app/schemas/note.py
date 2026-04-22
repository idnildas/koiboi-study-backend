"""Note request and response schemas."""

from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class Point(BaseModel):
    """Schema for a point in a scribble stroke.
    
    Attributes:
        x: X coordinate
        y: Y coordinate
    """

    x: float = Field(..., description="X coordinate")
    y: float = Field(..., description="Y coordinate")

    model_config = {
        "json_schema_extra": {
            "example": {"x": 100.5, "y": 200.3}
        }
    }


class ScribbleStroke(BaseModel):
    """Schema for a hand-drawn scribble stroke.
    
    Attributes:
        id: Stroke UUID
        tool: Drawing tool type
        color: Hex color code
        width: Stroke width (1-20)
        opacity: Stroke opacity (0-1)
        points: Array of points in the stroke
    """

    id: str = Field(..., description="Stroke UUID")
    tool: str = Field(..., description="Drawing tool type")
    color: str = Field(..., description="Hex color code")
    width: float = Field(..., ge=1, le=20, description="Stroke width")
    opacity: float = Field(..., ge=0, le=1, description="Stroke opacity")
    points: List[Point] = Field(..., description="Array of points in stroke")

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: str) -> str:
        """Validate hex color format."""
        import re
        if not re.match(r"^#[0-9a-fA-F]{6}$", v):
            raise ValueError("Invalid hex color format")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "tool": "brush",
                "color": "#FF0000",
                "width": 2.5,
                "opacity": 0.8,
                "points": [
                    {"x": 100, "y": 200},
                    {"x": 110, "y": 210},
                    {"x": 120, "y": 220},
                ],
            }
        }
    }


class NoteCreate(BaseModel):
    """Schema for creating a new note.
    
    Attributes:
        title: Note title (1-255 characters)
        body: Optional markdown content
        tint_id: Optional UUID of tint palette color
    """

    title: str = Field(..., min_length=1, max_length=255, description="Note title")
    body: Optional[str] = Field(None, description="Markdown content")
    tint_id: Optional[UUID] = Field(None, description="Tint palette color UUID")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Validate title is not empty after stripping whitespace."""
        if not v or not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()

    @field_validator("body")
    @classmethod
    def validate_body(cls, v: Optional[str]) -> Optional[str]:
        """Validate body if provided."""
        if v is not None and not v.strip():
            return None
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "Graph Traversal",
                "body": "# BFS and DFS algorithms\n\nBFS uses a queue...",
                "tint_id": "550e8400-e29b-41d4-a716-446655440000",
            }
        }
    }


class NoteUpdate(BaseModel):
    """Schema for updating a note.
    
    Attributes:
        title: Updated note title (optional)
        body: Updated markdown content (optional)
        tint_id: Updated tint palette color UUID (optional)
        scribbles: Updated array of scribble strokes (optional)
    """

    title: Optional[str] = Field(None, min_length=1, max_length=255, description="Updated note title")
    body: Optional[str] = Field(None, description="Updated markdown content")
    tint_id: Optional[UUID] = Field(None, description="Updated tint palette color UUID")
    scribbles: Optional[List[ScribbleStroke]] = Field(None, description="Array of scribble strokes")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        """Validate title if provided."""
        if v is not None:
            if not v or not v.strip():
                raise ValueError("Title cannot be empty")
            return v.strip()
        return v

    @field_validator("body")
    @classmethod
    def validate_body(cls, v: Optional[str]) -> Optional[str]:
        """Validate body if provided."""
        if v is not None and not v.strip():
            return None
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "Updated Graph Traversal",
                "body": "# BFS and DFS algorithms\n\nUpdated content...",
                "scribbles": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "tool": "brush",
                        "color": "#FF0000",
                        "width": 2.5,
                        "opacity": 0.8,
                        "points": [{"x": 100, "y": 200}],
                    }
                ],
            }
        }
    }


class NoteResponse(BaseModel):
    """Schema for note response.
    
    Attributes:
        id: Note UUID
        topic_id: Parent topic UUID
        title: Note title
        body: Markdown content
        tint_id: Tint palette color UUID
        scribbles: Array of scribble strokes
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    id: UUID = Field(..., description="Note UUID")
    topic_id: UUID = Field(..., description="Parent topic UUID")
    title: str = Field(..., description="Note title")
    body: Optional[str] = Field(None, description="Markdown content")
    tint_id: UUID = Field(..., description="Tint palette color UUID")
    scribbles: List[ScribbleStroke] = Field(default_factory=list, description="Array of scribble strokes")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "topic_id": "550e8400-e29b-41d4-a716-446655440001",
                "title": "Graph Traversal",
                "body": "# BFS and DFS algorithms\n\nBFS uses a queue...",
                "tint_id": "550e8400-e29b-41d4-a716-446655440002",
                "scribbles": [],
                "created_at": "2026-04-21T10:00:00+00:00",
                "updated_at": "2026-04-21T10:00:00+00:00",
            }
        }
    }
