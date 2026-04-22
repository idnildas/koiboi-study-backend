from uuid import uuid4
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, func, Index
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class PaletteColor(Base):
    __tablename__ = "palette_colors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False)
    palette_id = Column(UUID(as_uuid=True), ForeignKey("color_palette.id", ondelete="CASCADE"), nullable=False)
    hex_code = Column(String(7), nullable=False)
    hsl = Column(String(50), nullable=True)
    color_name = Column(String(100), nullable=True)
    display_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())

    # Indexes
    __table_args__ = (
        Index("ix_palette_colors_palette_id", "palette_id"),
        Index("ix_palette_colors_palette_id_display_order", "palette_id", "display_order"),
    )
