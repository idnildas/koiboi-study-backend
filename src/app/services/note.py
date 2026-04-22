"""Note service for CRUD operations on notes."""

import random
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.note import Note
from app.models.subject import Subject
from app.models.tint_palette import TintPalette
from app.models.topic import Topic


class NoteService:
    """Service for note CRUD operations."""

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
    async def get_topic_for_user(
        db: AsyncSession,
        topic_id: UUID,
        user_id: UUID,
    ) -> Optional[Topic]:
        """
        Retrieve a topic by ID and verify ownership via subject.

        Returns the Topic if found and owned by user_id (via subject), else None.
        """
        result = await db.execute(select(Topic).where(Topic.id == topic_id))
        topic = result.scalar_one_or_none()
        if topic is None:
            return None

        subj_result = await db.execute(
            select(Subject).where(Subject.id == topic.subject_id)
        )
        subject = subj_result.scalar_one_or_none()
        if subject is None or subject.user_id != user_id:
            return None
        return topic

    @staticmethod
    async def get_note_for_user(
        db: AsyncSession,
        note_id: UUID,
        user_id: UUID,
    ) -> Optional[Note]:
        """
        Retrieve a note by ID and verify ownership via topic → subject chain.

        Returns the Note if found and owned by user_id, else None.
        """
        result = await db.execute(select(Note).where(Note.id == note_id))
        note = result.scalar_one_or_none()
        if note is None:
            return None

        topic = await NoteService.get_topic_for_user(
            db=db, topic_id=note.topic_id, user_id=user_id
        )
        if topic is None:
            return None
        return note

    @staticmethod
    async def create_note(
        db: AsyncSession,
        topic_id: UUID,
        title: str,
        body: Optional[str] = None,
        tint_id: Optional[UUID] = None,
    ) -> Note:
        """
        Create a new note under the given topic.

        Args:
            db: Database session
            topic_id: UUID of the parent topic
            title: Note title (1-255 chars)
            body: Optional markdown content
            tint_id: Optional tint palette UUID; random active tint assigned if None

        Returns:
            Created Note object

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
            tint_id = await NoteService._get_random_active_tint(db)

        note = Note(
            topic_id=topic_id,
            title=title,
            body=body or "",
            tint_id=tint_id,
            scribbles=[],
        )
        db.add(note)
        await db.flush()
        await db.refresh(note)
        return note

    @staticmethod
    async def list_notes(
        db: AsyncSession,
        topic_id: UUID,
        limit: int = 50,
        offset: int = 0,
        sort: str = "created_at",
    ) -> tuple[List[Note], int]:
        """
        List all notes for a topic with pagination and sorting.

        Args:
            db: Database session
            topic_id: UUID of the parent topic
            limit: Max items to return
            offset: Items to skip
            sort: Sort field (created_at or updated_at)

        Returns:
            Tuple of (notes list, total count)
        """
        base_filter = [Note.topic_id == topic_id]

        count_result = await db.execute(
            select(func.count()).select_from(Note).where(*base_filter)
        )
        total = count_result.scalar() or 0

        sort_col = Note.updated_at if sort == "updated_at" else Note.created_at

        query = (
            select(Note)
            .where(*base_filter)
            .order_by(sort_col.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await db.execute(query)
        notes = list(result.scalars().all())

        return notes, total

    @staticmethod
    async def get_note(
        db: AsyncSession,
        note_id: UUID,
    ) -> Optional[Note]:
        """Retrieve a note by ID."""
        result = await db.execute(select(Note).where(Note.id == note_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_note(
        db: AsyncSession,
        note: Note,
        title: Optional[str] = None,
        body: Optional[str] = None,
        tint_id: Optional[UUID] = None,
        scribbles: Optional[list] = None,
    ) -> Note:
        """
        Update a note's fields.

        Args:
            db: Database session
            note: Note object to update
            title: New title (optional)
            body: New body (optional)
            tint_id: New tint palette UUID (optional)
            scribbles: New scribbles array (optional)

        Returns:
            Updated Note object

        Raises:
            ValueError: If tint_id does not exist in tint_palette
        """
        if tint_id is not None:
            result = await db.execute(
                select(TintPalette).where(TintPalette.id == tint_id)
            )
            if result.scalar_one_or_none() is None:
                raise ValueError("Invalid tint_id: tint not found in tint_palette")

        if title is not None:
            note.title = title
        if body is not None:
            note.body = body
        if tint_id is not None:
            note.tint_id = tint_id
        if scribbles is not None:
            note.scribbles = scribbles

        await db.flush()
        await db.refresh(note)
        return note

    @staticmethod
    async def delete_note(
        db: AsyncSession,
        note: Note,
    ) -> None:
        """
        Delete a note. Associated snippets have note_id set to NULL via DB constraint.

        Args:
            db: Database session
            note: Note object to delete
        """
        await db.delete(note)
        await db.flush()
