"""User profile service for retrieving and updating user profiles."""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.avatar_style import AvatarStyle
from app.models.avatar_color import AvatarColor


class UserService:
    """Service for user profile operations."""

    @staticmethod
    async def get_profile(db: AsyncSession, user_id: UUID) -> User:
        """
        Retrieve user profile by user ID.

        Args:
            db: Database session
            user_id: UUID of the user

        Returns:
            User object

        Raises:
            ValueError: If user not found
        """
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if user is None:
            raise ValueError("User not found")

        return user

    @staticmethod
    async def update_profile(
        db: AsyncSession,
        user_id: UUID,
        name: Optional[str] = None,
        avatar_style_id: Optional[UUID] = None,
        avatar_color_id: Optional[UUID] = None,
    ) -> User:
        """
        Update user profile fields.

        Args:
            db: Database session
            user_id: UUID of the user to update
            name: New display name (optional)
            avatar_style_id: New avatar style UUID (optional)
            avatar_color_id: New avatar color UUID (optional)

        Returns:
            Updated User object

        Raises:
            ValueError: If user not found or avatar IDs are invalid
        """
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if user is None:
            raise ValueError("User not found")

        if avatar_style_id is not None:
            style_result = await db.execute(
                select(AvatarStyle).where(AvatarStyle.id == avatar_style_id)
            )
            if style_result.scalar_one_or_none() is None:
                raise ValueError("Invalid avatar_style_id")

        if avatar_color_id is not None:
            color_result = await db.execute(
                select(AvatarColor).where(AvatarColor.id == avatar_color_id)
            )
            if color_result.scalar_one_or_none() is None:
                raise ValueError("Invalid avatar_color_id")

        if name is not None:
            user.name = name
        if avatar_style_id is not None:
            user.avatar_style_id = avatar_style_id
        if avatar_color_id is not None:
            user.avatar_color_id = avatar_color_id

        await db.flush()

        return user
