from uuid import uuid4
from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, Numeric, func, Index
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class AvatarStyle(Base):
    __tablename__ = "avatar_styles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False)
    name = Column(String(100), unique=True, nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    svg_template = Column(Text, nullable=False)
    animation_type = Column(String(50), nullable=False)
    animation_duration = Column(Numeric(5, 2), nullable=False, default=3.0)
    color_customizable = Column(Boolean, nullable=False, default=True)
    display_order = Column(Integer, nullable=False, default=0, index=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())

    __table_args__ = (
        Index("ix_avatar_styles_animation_type", "animation_type"),
    )
