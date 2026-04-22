from uuid import uuid4
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, func, Index
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class PlaygroundSnippet(Base):
    __tablename__ = "playground_snippets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    note_id = Column(UUID(as_uuid=True), ForeignKey("notes.id", ondelete="SET NULL"), nullable=True, index=True)
    language = Column(String(50), nullable=False)
    code = Column(Text, nullable=False)
    output = Column(Text, nullable=False, default="")
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

    __table_args__ = (
        # Composite index on user_id and created_at
        Index("ix_playground_snippets_user_id_created_at", "user_id", "created_at"),
    )
