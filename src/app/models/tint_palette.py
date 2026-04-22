from uuid import uuid4
from sqlalchemy import Column, String, Integer, Boolean, DateTime, func, Index
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class TintPalette(Base):
    __tablename__ = "tint_palette"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False)
    name = Column(String(100), unique=True, nullable=False)
    hsl = Column(String(50), nullable=False)
    hex_code = Column(String(7), nullable=True)
    category = Column(String(50), nullable=True, index=True)
    display_order = Column(Integer, nullable=False, default=0, index=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
