from uuid import uuid4
from sqlalchemy import Column, String, DateTime, ForeignKey, func, BigInteger, Integer, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class Material(Base):
    __tablename__ = "materials"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    file_name = Column(String(255), nullable=False)
    mime_type = Column(String(50), nullable=False, default="application/pdf")
    file_size = Column(BigInteger, nullable=False)
    page_count = Column(Integer, nullable=True)
    storage_key = Column(String(255), nullable=False, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

    __table_args__ = (
        # Composite index on subject_id and created_at
        Index("ix_materials_subject_id_created_at", "subject_id", "created_at"),
    )
