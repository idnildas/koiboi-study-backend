from uuid import uuid4
from enum import Enum
from sqlalchemy import Column, String, Text, Boolean, DateTime, func, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class PaletteType(str, Enum):
    """Enum for palette type."""
    SUBJECT = "subject"
    NOTE = "note"
    BOTH = "both"


class ColorPalette(Base):
    __tablename__ = "color_palette"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    palette_type = Column(SQLEnum(PaletteType), nullable=False, default=PaletteType.BOTH)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
