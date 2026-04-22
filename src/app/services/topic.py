"""Topic service for CRUD operations on topics."""

import random
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subject import Subject
from app.models.topic import Topic, TopicStatus
from app.models.tint_palette import TintPalette


class TopicService:
    """Service for topic CRUD operations."""

    @staticmethod
    async def _get_random_active_tint(db: AsyncSession) -> Optional[UUID]:
        """Return a random active tint_palette id, or None if none exist."""
        result = await db.execute(
            select(TintPalette.id).where(TintPalette.is_active == True)
        )
        tint_ids = result.scalars().all()
        if not tint_ids:
            return None
        return random.choice(tint_ids)

    @staticmethod
    async def get_subject_for_user(
        db: AsyncSession,
        subject_id: UUID,
        user_id: UUID,
    ) -> Optional[Subject]:
        """
        Retrieve a subject by ID and verify ownership.

        Returns the Subject if found and owned by user_id, else None.
        """
        result = await db.execute(
            select(Subject).where(Subject.id == subject_id)
        )
        subject = result.scalar_one_or_none()
        if subject is None or subject.user_id != user_id:
            return None
        return subject

    @staticmethod
    async def create_topic(
        db: AsyncSession,
        subject_id: UUID,
        name: str,
        tint_id: Optional[UUID] = None,
    ) -> Topic:
        """
        Create a new topic under the given subject.

        Args:
            db: Database session
            subject_id: UUID of the parent subject
            name: Topic name (1-255 chars)
            tint_id: Optional tint palette UUID; random active tint assigned if None

        Returns:
            Created Topic object

        Raises:
            ValueError: If tint_id does not exist in tint_palette
        """
        if tint_id is not None:
            result = await db.execute(
                select(TintPalette).where(TintPalette.id == tint_id)
            )
            if result.scalar_one_or_none() is None:
                raise ValueError("Invalid tint_id: tint not found in tint_palette")
        else:
            tint_id = await TopicService._get_random_active_tint(db)

        topic = Topic(
            subject_id=subject_id,
            name=name,
            status=TopicStatus.NOT_STARTED,
            confidence=0,
            tint_id=tint_id,
        )
        db.add(topic)
        await db.flush()
        await db.refresh(topic)
        return topic

    @staticmethod
    async def list_topics(
        db: AsyncSession,
        subject_id: UUID,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None,
    ) -> tuple[List[Topic], int]:
        """
        List all topics for a subject with optional status filter and pagination.

        Args:
            db: Database session
            subject_id: UUID of the parent subject
            limit: Max items to return
            offset: Items to skip
            status: Optional status filter

        Returns:
            Tuple of (topics list, total count)
        """
        base_filter = [Topic.subject_id == subject_id]
        if status is not None:
            try:
                status_enum = TopicStatus(status)
                base_filter.append(Topic.status == status_enum)
            except ValueError:
                pass  # ignore invalid status filter

        count_result = await db.execute(
            select(func.count()).select_from(Topic).where(*base_filter)
        )
        total = count_result.scalar() or 0

        query = (
            select(Topic)
            .where(*base_filter)
            .order_by(Topic.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await db.execute(query)
        topics = list(result.scalars().all())

        return topics, total

    @staticmethod
    async def get_topic(
        db: AsyncSession,
        topic_id: UUID,
    ) -> Optional[Topic]:
        """Retrieve a topic by ID."""
        result = await db.execute(
            select(Topic).where(Topic.id == topic_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_topic_with_subject(
        db: AsyncSession,
        topic_id: UUID,
    ) -> Optional[tuple[Topic, Subject]]:
        """
        Retrieve a topic and its parent subject together.

        Returns:
            Tuple of (Topic, Subject) or None if topic not found
        """
        result = await db.execute(
            select(Topic).where(Topic.id == topic_id)
        )
        topic = result.scalar_one_or_none()
        if topic is None:
            return None

        subj_result = await db.execute(
            select(Subject).where(Subject.id == topic.subject_id)
        )
        subject = subj_result.scalar_one_or_none()
        return topic, subject

    @staticmethod
    async def update_topic(
        db: AsyncSession,
        topic: Topic,
        name: Optional[str] = None,
        status: Optional[str] = None,
        confidence: Optional[int] = None,
        tint_id: Optional[UUID] = None,
    ) -> Topic:
        """
        Update a topic's fields.

        Args:
            db: Database session
            topic: Topic object to update
            name: New name (optional)
            status: New status string (optional)
            confidence: New confidence 0-5 (optional)
            tint_id: New tint palette UUID (optional)

        Returns:
            Updated Topic object

        Raises:
            ValueError: If tint_id does not exist in tint_palette
        """
        if tint_id is not None:
            result = await db.execute(
                select(TintPalette).where(TintPalette.id == tint_id)
            )
            if result.scalar_one_or_none() is None:
                raise ValueError("Invalid tint_id: tint not found in tint_palette")

        if name is not None:
            topic.name = name
        if status is not None:
            topic.status = TopicStatus(status)
        if confidence is not None:
            topic.confidence = confidence
        if tint_id is not None:
            topic.tint_id = tint_id

        await db.flush()
        await db.refresh(topic)
        return topic

    @staticmethod
    async def delete_topic(
        db: AsyncSession,
        topic: Topic,
    ) -> None:
        """
        Delete a topic (cascade deletes notes via DB).

        Args:
            db: Database session
            topic: Topic object to delete
        """
        await db.delete(topic)
        await db.flush()
