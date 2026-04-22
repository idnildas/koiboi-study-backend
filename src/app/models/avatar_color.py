from uuid import uuid4
from sqlalchemy import Column, String, Integer, Boolean, DateTime, func, Index
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class AvatarColor(Base):
    __tablename__ = "avatar_colors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False)
    name = Column(String(100), unique=True, nullable=False)
    hex_code = Column(String(7), unique=True, nullable=False, index=True)
    rgb = Column(String(20), nullable=True)
    hsl = Column(String(50), nullable=True)
    display_order = Column(Integer, nullable=False, default=0, index=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
