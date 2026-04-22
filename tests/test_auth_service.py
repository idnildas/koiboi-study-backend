"""Tests for AuthService authentication operations."""

import pytest
import pytest_asyncio
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.user import User
from app.models.session import UserSession
from app.models.reset_token import PasswordResetToken
from app.models.avatar_style import AvatarStyle
from app.models.avatar_color import AvatarColor
from app.services.auth import AuthService
from app.core.security import verify_password


# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def db_session():
    """Create an in-memory test database session."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        # Only create the tables needed for auth tests
        await conn.run_sync(Base.metadata.tables['users'].create, checkfirst=True)
        await conn.run_sync(Base.metadata.tables['user_sessions'].create, checkfirst=True)
        await conn.run_sync(Base.metadata.tables['password_reset_tokens'].create, checkfirst=True)
        await conn.run_sync(Base.metadata.tables['avatar_styles'].create, checkfirst=True)
        await conn.run_sync(Base.metadata.tables['avatar_colors'].create, checkfirst=True)
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture
async def avatar_style(db_session: AsyncSession):
    """Create a test avatar style."""
    style = AvatarStyle(
        name="Test Style",
        slug="test-style",
        description="Test avatar style",
        svg_template="<svg></svg>",
        animation_type="float",
        animation_duration=3.0,
        color_customizable=True,
        display_order=1,
        is_active=True,
    )
    db_session.add(style)
    await db_session.flush()
    return style


@pytest_asyncio.fixture
async def avatar_color(db_session: AsyncSession):
    """Create a test avatar color."""
    color = AvatarColor(
        name="Test Color",
        hex_code="#FF0000",
        rgb="rgb(255, 0, 0)",
        hsl="hsl(0, 100%, 50%)",
        display_order=1,
        is_active=True,
    )
    db_session.add(color)
    await db_session.flush()
    return color


class TestSignUp:
    """Tests for AuthService.sign_up method."""

    @pytest.mark.asyncio
    async def test_sign_up_success(self, db_session: AsyncSession, avatar_style, avatar_color):
        """Test successful user sign-up."""
        user, token = await AuthService.sign_up(
            db_session,
            name="John Doe",
            email="john@example.com",
            password="password123",
            avatar_style_id=avatar_style.id,
            avatar_color_id=avatar_color.id,
        )
        
        assert user.name == "John Doe"
        assert user.email == "john@example.com"
        assert user.avatar_style_id == avatar_style.id
        assert user.avatar_color_id == avatar_color.id
        assert user.is_active is True
        assert token is not None
        assert len(token) > 0
        # Password should be hashed, not plain text
        assert user.password_hash != "password123"
        assert verify_password("password123", user.password_hash)

    @pytest.mark.asyncio
    async def test_sign_up_name_too_short(self, db_session: AsyncSession, avatar_style, avatar_color):
        """Test sign-up fails with name too short."""
        with pytest.raises(ValueError, match="Name must be between 2 and 100 characters"):
            await AuthService.sign_up(
                db_session,
                name="J",
                email="john@example.com",
                password="password123",
                avatar_style_id=avatar_style.id,
                avatar_color_id=avatar_color.id,
            )

    @pytest.mark.asyncio
    async def test_sign_up_name_too_long(self, db_session: AsyncSession, avatar_style, avatar_color):
        """Test sign-up fails with name too long."""
        with pytest.raises(ValueError, match="Name must be between 2 and 100 characters"):
            await AuthService.sign_up(
                db_session,
                name="A" * 101,
                email="john@example.com",
                password="password123",
                avatar_style_id=avatar_style.id,
                avatar_color_id=avatar_color.id,
            )

    @pytest.mark.asyncio
    async def test_sign_up_name_empty(self, db_session: AsyncSession, avatar_style, avatar_color):
        """Test sign-up fails with empty name."""
        with pytest.raises(ValueError, match="Name must be between 2 and 100 characters"):
            await AuthService.sign_up(
                db_session,
                name="",
                email="john@example.com",
                password="password123",
                avatar_style_id=avatar_style.id,
                avatar_color_id=avatar_color.id,
            )

    @pytest.mark.asyncio
    async def test_sign_up_invalid_email(self, db_session: AsyncSession, avatar_style, avatar_color):
        """Test sign-up fails with invalid email."""
        with pytest.raises(ValueError, match="Invalid email format"):
            await AuthService.sign_up(
                db_session,
                name="John Doe",
                email="invalid-email",
                password="password123",
                avatar_style_id=avatar_style.id,
                avatar_color_id=avatar_color.id,
            )

    @pytest.mark.asyncio
    async def test_sign_up_empty_email(self, db_session: AsyncSession, avatar_style, avatar_color):
        """Test sign-up fails with empty email."""
        with pytest.raises(ValueError, match="Invalid email format"):
            await AuthService.sign_up(
                db_session,
                name="John Doe",
                email="",
                password="password123",
                avatar_style_id=avatar_style.id,
                avatar_color_id=avatar_color.id,
            )

    @pytest.mark.asyncio
    async def test_sign_up_password_too_short(self, db_session: AsyncSession, avatar_style, avatar_color):
        """Test sign-up fails with password too short."""
        with pytest.raises(ValueError, match="Password must be between 6 and 128 characters"):
            await AuthService.sign_up(
                db_session,
                name="John Doe",
                email="john@example.com",
                password="pass",
                avatar_style_id=avatar_style.id,
                avatar_color_id=avatar_color.id,
            )

    @pytest.mark.asyncio
    async def test_sign_up_password_too_long(self, db_session: AsyncSession, avatar_style, avatar_color):
        """Test sign-up fails with password too long."""
        with pytest.raises(ValueError, match="Password must be between 6 and 128 characters"):
            await AuthService.sign_up(
                db_session,
                name="John Doe",
                email="john@example.com",
                password="A" * 129,
                avatar_style_id=avatar_style.id,
                avatar_color_id=avatar_color.id,
            )

    @pytest.mark.asyncio
    async def test_sign_up_password_empty(self, db_session: AsyncSession, avatar_style, avatar_color):
        """Test sign-up fails with empty password."""
        with pytest.raises(ValueError, match="Password must be between 6 and 128 characters"):
            await AuthService.sign_up(
                db_session,
                name="John Doe",
                email="john@example.com",
                password="",
                avatar_style_id=avatar_style.id,
                avatar_color_id=avatar_color.id,
            )

    @pytest.mark.asyncio
    async def test_sign_up_duplicate_email(self, db_session: AsyncSession, avatar_style, avatar_color):
        """Test sign-up fails with duplicate email."""
        # Create first user
        await AuthService.sign_up(
            db_session,
            name="John Doe",
            email="john@example.com",
            password="password123",
            avatar_style_id=avatar_style.id,
            avatar_color_id=avatar_color.id,
        )
        
        # Try to create second user with same email
        with pytest.raises(ValueError, match="Email already registered"):
            await AuthService.sign_up(
                db_session,
                name="Jane Doe",
                email="john@example.com",
                password="password456",
                avatar_style_id=avatar_style.id,
                avatar_color_id=avatar_color.id,
            )

    @pytest.mark.asyncio
    async def test_sign_up_invalid_avatar_style_id(self, db_session: AsyncSession, avatar_color):
        """Test sign-up fails with invalid avatar_style_id."""
        with pytest.raises(ValueError, match="Invalid avatar_style_id"):
            await AuthService.sign_up(
                db_session,
                name="John Doe",
                email="john@example.com",
                password="password123",
                avatar_style_id=uuid4(),
                avatar_color_id=avatar_color.id,
            )

    @pytest.mark.asyncio
    async def test_sign_up_invalid_avatar_color_id(self, db_session: AsyncSession, avatar_style):
        """Test sign-up fails with invalid avatar_color_id."""
        with pytest.raises(ValueError, match="Invalid avatar_color_id"):
            await AuthService.sign_up(
                db_session,
                name="John Doe",
                email="john@example.com",
                password="password123",
                avatar_style_id=avatar_style.id,
                avatar_color_id=uuid4(),
            )


class TestSignIn:
    """Tests for AuthService.sign_in method."""

    @pytest.mark.asyncio
    async def test_sign_in_success(self, db_session: AsyncSession, avatar_style, avatar_color):
        """Test successful user sign-in."""
        # Create user
        created_user, _ = await AuthService.sign_up(
            db_session,
            name="John Doe",
            email="john@example.com",
            password="password123",
            avatar_style_id=avatar_style.id,
            avatar_color_id=avatar_color.id,
        )
        
        # Sign in
        user, token = await AuthService.sign_in(
            db_session,
            email="john@example.com",
            password="password123",
            ip_address="127.0.0.1",
            user_agent="Mozilla/5.0",
        )
        
        assert user.id == created_user.id
        assert user.email == "john@example.com"
        assert token is not None
        assert len(token) > 0
        assert user.last_login_at is not None

    @pytest.mark.asyncio
    async def test_sign_in_invalid_email(self, db_session: AsyncSession):
        """Test sign-in fails with non-existent email."""
        with pytest.raises(ValueError, match="Invalid credentials"):
            await AuthService.sign_in(
                db_session,
                email="nonexistent@example.com",
                password="password123",
            )

    @pytest.mark.asyncio
    async def test_sign_in_wrong_password(self, db_session: AsyncSession, avatar_style, avatar_color):
        """Test sign-in fails with wrong password."""
        # Create user
        await AuthService.sign_up(
            db_session,
            name="John Doe",
            email="john@example.com",
            password="password123",
            avatar_style_id=avatar_style.id,
            avatar_color_id=avatar_color.id,
        )
        
        # Try to sign in with wrong password
        with pytest.raises(ValueError, match="Invalid credentials"):
            await AuthService.sign_in(
                db_session,
                email="john@example.com",
                password="wrongpassword",
            )

    @pytest.mark.asyncio
    async def test_sign_in_creates_session(self, db_session: AsyncSession, avatar_style, avatar_color):
        """Test that sign-in creates a session record."""
        # Create user
        created_user, _ = await AuthService.sign_up(
            db_session,
            name="John Doe",
            email="john@example.com",
            password="password123",
            avatar_style_id=avatar_style.id,
            avatar_color_id=avatar_color.id,
        )
        
        # Sign in
        user, token = await AuthService.sign_in(
            db_session,
            email="john@example.com",
            password="password123",
            ip_address="127.0.0.1",
            user_agent="Mozilla/5.0",
        )
        
        # Verify session was created
        from sqlalchemy import select
        result = await db_session.execute(
            select(UserSession).where(UserSession.user_id == created_user.id)
        )
        session = result.scalar_one_or_none()
        
        assert session is not None
        assert session.token == token
        assert session.ip_address == "127.0.0.1"
        assert session.user_agent == "Mozilla/5.0"


class TestSignOut:
    """Tests for AuthService.sign_out method."""

    @pytest.mark.asyncio
    async def test_sign_out_success(self, db_session: AsyncSession, avatar_style, avatar_color):
        """Test successful user sign-out."""
        # Create and sign in user
        created_user, _ = await AuthService.sign_up(
            db_session,
            name="John Doe",
            email="john@example.com",
            password="password123",
            avatar_style_id=avatar_style.id,
            avatar_color_id=avatar_color.id,
        )
        
        user, token = await AuthService.sign_in(
            db_session,
            email="john@example.com",
            password="password123",
        )
        
        # Sign out
        await AuthService.sign_out(db_session, user.id, token)
        
        # Verify session was deleted
        from sqlalchemy import select
        result = await db_session.execute(
            select(UserSession).where(UserSession.user_id == user.id)
        )
        session = result.scalar_one_or_none()
        
        assert session is None

    @pytest.mark.asyncio
    async def test_sign_out_invalid_session(self, db_session: AsyncSession):
        """Test sign-out fails with invalid session."""
        with pytest.raises(ValueError, match="Session not found"):
            await AuthService.sign_out(
                db_session,
                user_id=uuid4(),
                token="invalid_token",
            )


class TestForgotPassword:
    """Tests for AuthService.forgot_password method."""

    @pytest.mark.asyncio
    async def test_forgot_password_existing_email(self, db_session: AsyncSession, avatar_style, avatar_color):
        """Test forgot_password with existing email."""
        # Create user
        created_user, _ = await AuthService.sign_up(
            db_session,
            name="John Doe",
            email="john@example.com",
            password="password123",
            avatar_style_id=avatar_style.id,
            avatar_color_id=avatar_color.id,
        )
        
        # Request password reset
        reset_token = await AuthService.forgot_password(
            db_session,
            email="john@example.com",
        )
        
        assert reset_token is not None
        assert reset_token.user_id == created_user.id
        assert reset_token.token is not None
        assert len(reset_token.token) > 0
        assert reset_token.expires_at is not None
        assert reset_token.used_at is None

    @pytest.mark.asyncio
    async def test_forgot_password_nonexistent_email(self, db_session: AsyncSession):
        """Test forgot_password with non-existent email returns None."""
        reset_token = await AuthService.forgot_password(
            db_session,
            email="nonexistent@example.com",
        )
        
        assert reset_token is None


class TestResetPassword:
    """Tests for AuthService.reset_password method."""

    @pytest.mark.asyncio
    async def test_reset_password_success(self, db_session: AsyncSession, avatar_style, avatar_color):
        """Test successful password reset."""
        # Create user
        created_user, _ = await AuthService.sign_up(
            db_session,
            name="John Doe",
            email="john@example.com",
            password="password123",
            avatar_style_id=avatar_style.id,
            avatar_color_id=avatar_color.id,
        )
        
        # Request password reset
        reset_token = await AuthService.forgot_password(
            db_session,
            email="john@example.com",
        )
        
        # Reset password
        user = await AuthService.reset_password(
            db_session,
            email="john@example.com",
            token=reset_token.token,
            new_password="newpassword456",
        )
        
        assert user.id == created_user.id
        assert verify_password("newpassword456", user.password_hash)
        assert not verify_password("password123", user.password_hash)

    @pytest.mark.asyncio
    async def test_reset_password_invalid_token(self, db_session: AsyncSession, avatar_style, avatar_color):
        """Test reset_password fails with invalid token."""
        # Create user
        await AuthService.sign_up(
            db_session,
            name="John Doe",
            email="john@example.com",
            password="password123",
            avatar_style_id=avatar_style.id,
            avatar_color_id=avatar_color.id,
        )
        
        # Try to reset with invalid token
        with pytest.raises(ValueError, match="Invalid or expired reset token"):
            await AuthService.reset_password(
                db_session,
                email="john@example.com",
                token="invalid_token",
                new_password="newpassword456",
            )

    @pytest.mark.asyncio
    async def test_reset_password_invalid_password(self, db_session: AsyncSession, avatar_style, avatar_color):
        """Test reset_password fails with invalid new password."""
        # Create user
        await AuthService.sign_up(
            db_session,
            name="John Doe",
            email="john@example.com",
            password="password123",
            avatar_style_id=avatar_style.id,
            avatar_color_id=avatar_color.id,
        )
        
        # Request password reset
        reset_token = await AuthService.forgot_password(
            db_session,
            email="john@example.com",
        )
        
        # Try to reset with invalid password
        with pytest.raises(ValueError, match="Password must be between 6 and 128 characters"):
            await AuthService.reset_password(
                db_session,
                email="john@example.com",
                token=reset_token.token,
                new_password="short",
            )

    @pytest.mark.asyncio
    async def test_reset_password_nonexistent_user(self, db_session: AsyncSession):
        """Test reset_password fails with non-existent user."""
        with pytest.raises(ValueError, match="User not found"):
            await AuthService.reset_password(
                db_session,
                email="nonexistent@example.com",
                token="some_token",
                new_password="newpassword456",
            )

    @pytest.mark.asyncio
    async def test_reset_password_invalidates_sessions(self, db_session: AsyncSession, avatar_style, avatar_color):
        """Test that reset_password invalidates all existing sessions."""
        # Create user
        created_user, _ = await AuthService.sign_up(
            db_session,
            name="John Doe",
            email="john@example.com",
            password="password123",
            avatar_style_id=avatar_style.id,
            avatar_color_id=avatar_color.id,
        )
        
        # Sign in to create session
        user, token = await AuthService.sign_in(
            db_session,
            email="john@example.com",
            password="password123",
        )
        
        # Request password reset
        reset_token = await AuthService.forgot_password(
            db_session,
            email="john@example.com",
        )
        
        # Reset password
        await AuthService.reset_password(
            db_session,
            email="john@example.com",
            token=reset_token.token,
            new_password="newpassword456",
        )
        
        # Verify session was deleted
        from sqlalchemy import select
        result = await db_session.execute(
            select(UserSession).where(UserSession.user_id == created_user.id)
        )
        session = result.scalar_one_or_none()
        
        assert session is None


class TestChangePassword:
    """Tests for AuthService.change_password method."""

    @pytest.mark.asyncio
    async def test_change_password_success(self, db_session: AsyncSession, avatar_style, avatar_color):
        """Test successful password change."""
        # Create user
        created_user, _ = await AuthService.sign_up(
            db_session,
            name="John Doe",
            email="john@example.com",
            password="password123",
            avatar_style_id=avatar_style.id,
            avatar_color_id=avatar_color.id,
        )
        
        # Change password
        user = await AuthService.change_password(
            db_session,
            user_id=created_user.id,
            current_password="password123",
            new_password="newpassword456",
        )
        
        assert user.id == created_user.id
        assert verify_password("newpassword456", user.password_hash)
        assert not verify_password("password123", user.password_hash)

    @pytest.mark.asyncio
    async def test_change_password_wrong_current_password(self, db_session: AsyncSession, avatar_style, avatar_color):
        """Test change_password fails with wrong current password."""
        # Create user
        created_user, _ = await AuthService.sign_up(
            db_session,
            name="John Doe",
            email="john@example.com",
            password="password123",
            avatar_style_id=avatar_style.id,
            avatar_color_id=avatar_color.id,
        )
        
        # Try to change password with wrong current password
        with pytest.raises(ValueError, match="Current password is incorrect"):
            await AuthService.change_password(
                db_session,
                user_id=created_user.id,
                current_password="wrongpassword",
                new_password="newpassword456",
            )

    @pytest.mark.asyncio
    async def test_change_password_invalid_new_password(self, db_session: AsyncSession, avatar_style, avatar_color):
        """Test change_password fails with invalid new password."""
        # Create user
        created_user, _ = await AuthService.sign_up(
            db_session,
            name="John Doe",
            email="john@example.com",
            password="password123",
            avatar_style_id=avatar_style.id,
            avatar_color_id=avatar_color.id,
        )
        
        # Try to change password with invalid new password
        with pytest.raises(ValueError, match="Password must be between 6 and 128 characters"):
            await AuthService.change_password(
                db_session,
                user_id=created_user.id,
                current_password="password123",
                new_password="short",
            )

    @pytest.mark.asyncio
    async def test_change_password_nonexistent_user(self, db_session: AsyncSession):
        """Test change_password fails with non-existent user."""
        with pytest.raises(ValueError, match="User not found"):
            await AuthService.change_password(
                db_session,
                user_id=uuid4(),
                current_password="password123",
                new_password="newpassword456",
            )
