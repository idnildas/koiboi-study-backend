"""Subject service for CRUD operations on subjects."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subject import Subject
from app.models.palette_color import PaletteColor


class SubjectService:
    """Service for subject CRUD operations."""

    @staticmethod
    async def create_subject(
        db: AsyncSession,
        user_id: UUID,
        name: str,
        color_id: Optional[UUID] = None,
        description: Optional[str] = None,
    ) -> Subject:
        """
        Create a new subject for the given user.

        Args:
            db: Database session
            user_id: UUID of the owning user
            name: Subject name (1-255 chars)
            color_id: Optional palette color UUID
            description: Optional description (max 1000 chars)

        Returns:
            Created Subject object

        Raises:
            ValueError: If color_id does not exist in palette_colors
        """
        if color_id is not None:
            result = await db.execute(
                select(PaletteColor).where(PaletteColor.id == color_id)
            )
            if result.scalar_one_or_none() is None:
                raise ValueError("Invalid color_id: palette color not found")

        subject = Subject(
            user_id=user_id,
            name=name,
            color_id=color_id,
            description=description,
        )
        db.add(subject)
        await db.flush()
        await db.refresh(subject)
        return subject

    @staticmethod
    async def list_subjects(
        db: AsyncSession,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
        sort: str = "created_at",
    ) -> tuple[List[Subject], int]:
        """
        List all subjects owned by the user with pagination.

        Args:
            db: Database session
            user_id: UUID of the owning user
            limit: Max items to return
            offset: Items to skip
            sort: Sort field ("created_at" or "name")

        Returns:
            Tuple of (subjects list, total count)
        """
        base_query = select(Subject).where(Subject.user_id == user_id)

        # Count total
        count_result = await db.execute(
            select(func.count()).select_from(Subject).where(Subject.user_id == user_id)
        )
        total = count_result.scalar() or 0

        # Apply sort
        if sort == "name":
            base_query = base_query.order_by(Subject.name.asc())
        else:
            base_query = base_query.order_by(Subject.created_at.desc())

        base_query = base_query.limit(limit).offset(offset)
        result = await db.execute(base_query)
        subjects = list(result.scalars().all())

        return subjects, total

    @staticmethod
    async def get_subject(
        db: AsyncSession,
        subject_id: UUID,
    ) -> Optional[Subject]:
        """
        Retrieve a subject by ID.

        Args:
            db: Database session
            subject_id: UUID of the subject

        Returns:
            Subject object or None if not found
        """
        result = await db.execute(
            select(Subject).where(Subject.id == subject_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_subject(
        db: AsyncSession,
        subject: Subject,
        name: Optional[str] = None,
        color_id: Optional[UUID] = None,
        description: Optional[str] = None,
    ) -> Subject:
        """
        Update a subject's fields.

        Args:
            db: Database session
            subject: Subject object to update
            name: New name (optional)
            color_id: New palette color UUID (optional)
            description: New description (optional)

        Returns:
            Updated Subject object

        Raises:
            ValueError: If color_id does not exist in palette_colors
        """
        if color_id is not None:
            result = await db.execute(
                select(PaletteColor).where(PaletteColor.id == color_id)
            )
            if result.scalar_one_or_none() is None:
                raise ValueError("Invalid color_id: palette color not found")

        if name is not None:
            subject.name = name
        if color_id is not None:
            subject.color_id = color_id
        if description is not None:
            subject.description = description

        await db.flush()
        await db.refresh(subject)
        return subject

    @staticmethod
    async def delete_subject(
        db: AsyncSession,
        subject: Subject,
    ) -> None:
        """
        Delete a subject (cascade deletes topics, notes, materials via DB).

        Args:
            db: Database session
            subject: Subject object to delete
        """
        await db.delete(subject)
        await db.flush()
