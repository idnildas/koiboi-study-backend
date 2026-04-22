"""Snippet service for CRUD operations on playground snippets."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.note import Note
from app.models.snippet import PlaygroundSnippet
from app.models.subject import Subject
from app.models.topic import Topic


class SnippetService:
    """Service for playground snippet CRUD operations."""

    @staticmethod
    async def _verify_note_ownership(
        db: AsyncSession,
        note_id: UUID,
        user_id: UUID,
    ) -> bool:
        """
        Verify that a note exists and is owned by the user via note → topic → subject chain.

        Returns True if note exists and user owns it, False otherwise.
        """
        result = await db.execute(select(Note).where(Note.id == note_id))
        note = result.scalar_one_or_none()
        if note is None:
            return False

        topic_result = await db.execute(select(Topic).where(Topic.id == note.topic_id))
        topic = topic_result.scalar_one_or_none()
        if topic is None:
            return False

        subj_result = await db.execute(select(Subject).where(Subject.id == topic.subject_id))
        subject = subj_result.scalar_one_or_none()
        if subject is None or subject.user_id != user_id:
            return False

        return True

    @staticmethod
    async def create_snippet(
        db: AsyncSession,
        user_id: UUID,
        language: str,
        code: str,
        note_id: Optional[UUID] = None,
    ) -> PlaygroundSnippet:
        """
        Create a new playground snippet.

        Args:
            db: Database session
            user_id: Owner user UUID
            language: Programming language
            code: Source code
            note_id: Optional associated note UUID

        Returns:
            Created PlaygroundSnippet object

        Raises:
            ValueError: If note_id is provided but note doesn't exist or user doesn't own it
        """
        if note_id is not None:
            note_result = await db.execute(select(Note).where(Note.id == note_id))
            note = note_result.scalar_one_or_none()
            if note is None:
                raise ValueError("note_not_found")

            owns = await SnippetService._verify_note_ownership(db, note_id, user_id)
            if not owns:
                raise PermissionError("note_forbidden")

        snippet = PlaygroundSnippet(
            user_id=user_id,
            note_id=note_id,
            language=language,
            code=code,
            output="",
        )
        db.add(snippet)
        await db.flush()
        await db.refresh(snippet)
        return snippet

    @staticmethod
    async def list_snippets(
        db: AsyncSession,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
        language: Optional[str] = None,
    ) -> tuple[List[PlaygroundSnippet], int]:
        """
        List all snippets owned by a user with pagination and optional language filter.

        Args:
            db: Database session
            user_id: Owner user UUID
            limit: Max items to return
            offset: Items to skip
            language: Optional language filter

        Returns:
            Tuple of (snippets list, total count)
        """
        filters = [PlaygroundSnippet.user_id == user_id]
        if language:
            filters.append(PlaygroundSnippet.language == language)

        count_result = await db.execute(
            select(func.count()).select_from(PlaygroundSnippet).where(*filters)
        )
        total = count_result.scalar() or 0

        query = (
            select(PlaygroundSnippet)
            .where(*filters)
            .order_by(PlaygroundSnippet.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await db.execute(query)
        snippets = list(result.scalars().all())

        return snippets, total

    @staticmethod
    async def get_snippet(
        db: AsyncSession,
        snippet_id: UUID,
    ) -> Optional[PlaygroundSnippet]:
        """Retrieve a snippet by ID."""
        result = await db.execute(
            select(PlaygroundSnippet).where(PlaygroundSnippet.id == snippet_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_snippet(
        db: AsyncSession,
        snippet: PlaygroundSnippet,
        code: Optional[str] = None,
        output: Optional[str] = None,
    ) -> PlaygroundSnippet:
        """
        Update a snippet's code and/or output.

        Args:
            db: Database session
            snippet: PlaygroundSnippet object to update
            code: New source code (optional)
            output: New execution output (optional)

        Returns:
            Updated PlaygroundSnippet object
        """
        if code is not None:
            snippet.code = code
        if output is not None:
            snippet.output = output

        await db.flush()
        await db.refresh(snippet)
        return snippet

    @staticmethod
    async def delete_snippet(
        db: AsyncSession,
        snippet: PlaygroundSnippet,
    ) -> None:
        """
        Delete a snippet.

        Args:
            db: Database session
            snippet: PlaygroundSnippet object to delete
        """
        await db.delete(snippet)
        await db.flush()
