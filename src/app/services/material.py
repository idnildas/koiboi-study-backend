"""Material service for CRUD operations on materials."""

from typing import List, Optional, Tuple
from uuid import UUID, uuid4

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.material import Material
from app.models.subject import Subject
from app.services.storage import StorageService


class MaterialService:
    """Service for material CRUD operations."""

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
        result = await db.execute(select(Subject).where(Subject.id == subject_id))
        subject = result.scalar_one_or_none()
        if subject is None:
            return None
        if subject.user_id != user_id:
            return None
        return subject

    @staticmethod
    async def get_material(
        db: AsyncSession,
        material_id: UUID,
    ) -> Optional[Material]:
        """Retrieve a material by ID."""
        result = await db.execute(select(Material).where(Material.id == material_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_material_for_user(
        db: AsyncSession,
        material_id: UUID,
        user_id: UUID,
    ) -> Optional[Material]:
        """
        Retrieve a material by ID and verify ownership via subject.

        Returns the Material if found and owned by user_id, else None.
        """
        material = await MaterialService.get_material(db=db, material_id=material_id)
        if material is None:
            return None

        subject = await MaterialService.get_subject_for_user(
            db=db, subject_id=material.subject_id, user_id=user_id
        )
        if subject is None:
            return None
        return material

    @staticmethod
    async def create_material(
        db: AsyncSession,
        subject_id: UUID,
        user_id: UUID,
        title: str,
        file_name: str,
        file_content: bytes,
        mime_type: str = "application/pdf",
    ) -> Material:
        """
        Create a new material record and persist the file to storage.

        Args:
            db: Database session
            subject_id: UUID of the parent subject
            user_id: UUID of the owning user (used for storage_key)
            title: Material title
            file_name: Original filename
            file_content: Raw file bytes
            mime_type: MIME type (default application/pdf)

        Returns:
            Created Material object
        """
        material_id = uuid4()
        storage_key = f"materials/{user_id}/{material_id}/{file_name}"

        # Persist file to storage first
        StorageService.save_file(content=file_content, storage_key=storage_key)

        material = Material(
            id=material_id,
            subject_id=subject_id,
            title=title,
            file_name=file_name,
            mime_type=mime_type,
            file_size=len(file_content),
            storage_key=storage_key,
        )
        db.add(material)
        await db.flush()
        await db.refresh(material)
        return material

    @staticmethod
    async def list_materials(
        db: AsyncSession,
        subject_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[Material], int]:
        """
        List all materials for a subject with pagination.

        Args:
            db: Database session
            subject_id: UUID of the parent subject
            limit: Max items to return
            offset: Items to skip

        Returns:
            Tuple of (materials list, total count)
        """
        count_result = await db.execute(
            select(func.count()).select_from(Material).where(Material.subject_id == subject_id)
        )
        total = count_result.scalar() or 0

        query = (
            select(Material)
            .where(Material.subject_id == subject_id)
            .order_by(Material.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await db.execute(query)
        materials = list(result.scalars().all())

        return materials, total

    @staticmethod
    async def update_material(
        db: AsyncSession,
        material: Material,
        title: Optional[str] = None,
        page_count: Optional[int] = None,
    ) -> Material:
        """
        Update a material's metadata fields.

        Args:
            db: Database session
            material: Material object to update
            title: New title (optional)
            page_count: New page count (optional)

        Returns:
            Updated Material object
        """
        if title is not None:
            material.title = title
        if page_count is not None:
            material.page_count = page_count

        await db.flush()
        await db.refresh(material)
        return material

    @staticmethod
    async def delete_material(
        db: AsyncSession,
        material: Material,
    ) -> None:
        """
        Delete a material record and its associated file from storage.

        Args:
            db: Database session
            material: Material object to delete
        """
        # Remove file from storage first (best-effort)
        StorageService.delete_file(material.storage_key)

        await db.delete(material)
        await db.flush()
