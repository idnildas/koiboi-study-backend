"""Authentication service for user sign-up, sign-in, password management."""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.models.session import UserSession
from app.models.reset_token import PasswordResetToken
from app.models.avatar_style import AvatarStyle
from app.models.avatar_color import AvatarColor


class AuthService:
    """Service for authentication operations including sign-up, sign-in, and password management."""

    @staticmethod
    async def sign_up(
        db: AsyncSession,
        name: str,
        email: str,
        password: str,
        avatar_style_id: UUID,
        avatar_color_id: UUID,
    ) -> Tuple[User, str]:
        """
        Create a new user account with provided credentials and avatar selection.

        Args:
            db: Database session
            name: User's display name (2-100 characters)
            email: User's email address (must be unique)
            password: User's password (6-128 characters)
            avatar_style_id: UUID of selected avatar style
            avatar_color_id: UUID of selected avatar color

        Returns:
            Tuple of (User object, JWT token)

        Raises:
            ValueError: If validation fails (invalid inputs, email exists, avatar IDs invalid)
        """
        # Validate inputs
        if not name or len(name) < 2 or len(name) > 100:
            raise ValueError("Name must be between 2 and 100 characters")

        if not email or "@" not in email or "." not in email.split("@")[1]:
            raise ValueError("Invalid email format")

        if not password or len(password) < 6 or len(password) > 128:
            raise ValueError("Password must be between 6 and 128 characters")

        # Check if email already exists
        existing_user = await db.execute(
            select(User).where(User.email == email)
        )
        if existing_user.scalar_one_or_none() is not None:
            raise ValueError("Email already registered")

        # Verify avatar_style_id exists
        avatar_style = await db.execute(
            select(AvatarStyle).where(AvatarStyle.id == avatar_style_id)
        )
        if avatar_style.scalar_one_or_none() is None:
            raise ValueError("Invalid avatar_style_id")

        # Verify avatar_color_id exists
        avatar_color = await db.execute(
            select(AvatarColor).where(AvatarColor.id == avatar_color_id)
        )
        if avatar_color.scalar_one_or_none() is None:
            raise ValueError("Invalid avatar_color_id")

        # Hash password and create user
        password_hash = hash_password(password)
        user = User(
            name=name,
            email=email,
            password_hash=password_hash,
            avatar_style_id=avatar_style_id,
            avatar_color_id=avatar_color_id,
        )
        db.add(user)
        await db.flush()

        # Create JWT token
        token = create_access_token(str(user.id))

        return user, token

    @staticmethod
    async def sign_in(
        db: AsyncSession,
        email: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Tuple[User, str]:
        """
        Authenticate user with email and password, create session.

        Args:
            db: Database session
            email: User's email address
            password: User's password
            ip_address: Client IP address (optional)
            user_agent: Client user agent (optional)

        Returns:
            Tuple of (User object, JWT token)

        Raises:
            ValueError: If credentials are invalid
        """
        # Find user by email
        result = await db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()

        if user is None or not verify_password(password, user.password_hash):
            raise ValueError("Invalid credentials")

        # Create JWT token
        token = create_access_token(str(user.id))

        # Create session record
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=24)

        session = UserSession(
            user_id=user.id,
            token=token,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.add(session)
        await db.flush()

        # Update last_login_at
        user.last_login_at = now
        await db.flush()

        return user, token

    @staticmethod
    async def sign_out(
        db: AsyncSession,
        user_id: UUID,
        token: str,
    ) -> None:
        """
        Sign out user by deleting their session.

        Args:
            db: Database session
            user_id: UUID of user signing out
            token: JWT token to invalidate

        Raises:
            ValueError: If session not found
        """
        result = await db.execute(
            select(UserSession).where(
                (UserSession.user_id == user_id) & (UserSession.token == token)
            )
        )
        session = result.scalar_one_or_none()

        if session is None:
            raise ValueError("Session not found")

        await db.delete(session)
        await db.flush()

    @staticmethod
    async def forgot_password(
        db: AsyncSession,
        email: str,
    ) -> Optional[PasswordResetToken]:
        """
        Generate password reset token for user email.

        Returns 200 OK regardless of whether email exists (security best practice).
        If email exists, creates and returns reset token. If not, returns None.

        Args:
            db: Database session
            email: User's email address

        Returns:
            PasswordResetToken if email exists, None otherwise
        """
        result = await db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()

        if user is None:
            return None

        # Generate cryptographically secure reset token
        reset_token = secrets.token_urlsafe(32)
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=1)

        token_record = PasswordResetToken(
            user_id=user.id,
            token=reset_token,
            expires_at=expires_at,
        )
        db.add(token_record)
        await db.flush()

        return token_record

    @staticmethod
    async def reset_password(
        db: AsyncSession,
        email: str,
        token: str,
        new_password: str,
    ) -> User:
        """
        Reset user password using reset token.

        Args:
            db: Database session
            email: User's email address
            token: Password reset token
            new_password: New password (6-128 characters)

        Returns:
            Updated User object

        Raises:
            ValueError: If token invalid/expired, password invalid, or email not found
        """
        # Validate new password
        if not new_password or len(new_password) < 6 or len(new_password) > 128:
            raise ValueError("Password must be between 6 and 128 characters")

        # Find user by email
        result = await db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()

        if user is None:
            raise ValueError("User not found")

        # Find and validate reset token
        now = datetime.now(timezone.utc)
        result = await db.execute(
            select(PasswordResetToken).where(
                (PasswordResetToken.user_id == user.id)
                & (PasswordResetToken.token == token)
            )
        )
        reset_token = result.scalar_one_or_none()

        if reset_token is None:
            raise ValueError("Invalid or expired reset token")

        if reset_token.expires_at < now:
            raise ValueError("Invalid or expired reset token")

        if reset_token.used_at is not None:
            raise ValueError("Invalid or expired reset token")

        # Update password
        user.password_hash = hash_password(new_password)

        # Mark token as used
        reset_token.used_at = now

        # Invalidate all existing sessions
        await db.execute(
            select(UserSession).where(UserSession.user_id == user.id)
        )
        sessions = (
            await db.execute(
                select(UserSession).where(UserSession.user_id == user.id)
            )
        ).scalars().all()
        for session in sessions:
            await db.delete(session)

        await db.flush()

        return user

    @staticmethod
    async def change_password(
        db: AsyncSession,
        user_id: UUID,
        current_password: str,
        new_password: str,
    ) -> User:
        """
        Change user password after verifying current password.

        Args:
            db: Database session
            user_id: UUID of user changing password
            current_password: User's current password
            new_password: New password (6-128 characters)

        Returns:
            Updated User object

        Raises:
            ValueError: If current password incorrect, new password invalid, or user not found
        """
        # Find user
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if user is None:
            raise ValueError("User not found")

        # Verify current password
        if not verify_password(current_password, user.password_hash):
            raise ValueError("Current password is incorrect")

        # Validate new password
        if not new_password or len(new_password) < 6 or len(new_password) > 128:
            raise ValueError("Password must be between 6 and 128 characters")

        # Update password
        user.password_hash = hash_password(new_password)
        await db.flush()

        return user
