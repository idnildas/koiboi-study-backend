from uuid import uuid4
from enum import Enum
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, func, CheckConstraint, Enum as SQLEnum, Index
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class TopicStatus(str, Enum):
    """Enum for topic learning status."""
    NOT_STARTED = "not-started"
    IN_PROGRESS = "in-progress"
    REVISING = "revising"
    COMPLETED = "completed"


class Topic(Base):
    __tablename__ = "topics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    status = Column(SQLEnum(TopicStatus), nullable=False, default=TopicStatus.NOT_STARTED, index=True)
    confidence = Column(Integer, nullable=False, default=0)
    tint_id = Column(UUID(as_uuid=True), ForeignKey("tint_palette.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

    __table_args__ = (
        # Check constraint for confidence range (0-5)
        CheckConstraint("confidence >= 0 AND confidence <= 5", name="confidence_range_check"),
        # Composite index on subject_id and name
        Index("ix_topics_subject_id_name", "subject_id", "name"),
    )
