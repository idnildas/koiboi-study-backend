"""Tests for authentication dependencies."""

import pytest
import pytest_asyncio
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException

from app.db.base import Base
from app.models.user import User
from app.models.avatar_style import AvatarStyle
from app.models.avatar_color import AvatarColor
from app.api.dependencies import get_current_user, optional_current_user
from app.core.security import create_access_token


# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def db_session():
    """Create an in-memory test database session."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        # Create only the tables needed for dependency tests
        await conn.run_sync(Base.metadata.tables['users'].create, checkfirst=True)
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


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession, avatar_style, avatar_color):
    """Create a test user."""
    user = User(
        name="Test User",
        email="test@example.com",
        password_hash="hashed_password",
        avatar_style_id=avatar_style.id,
        avatar_color_id=avatar_color.id,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    return user


class TestGetCurrentUser:
    """Tests for get_current_user dependency."""

    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(self, db_session: AsyncSession, test_user):
        """Test get_current_user with valid token."""
        token = create_access_token(str(test_user.id))
        authorization = f"Bearer {token}"
        
        user = await get_current_user(authorization=authorization, db=db_session)
        
        assert user.id == test_user.id
        assert user.email == "test@example.com"
        assert user.name == "Test User"

    @pytest.mark.asyncio
    async def test_get_current_user_missing_authorization_header(self, db_session: AsyncSession):
        """Test get_current_user with missing authorization header."""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(authorization=None, db=db_session)
        
        assert exc_info.value.status_code == 401
        assert "Missing authorization header" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_header_format(self, db_session: AsyncSession):
        """Test get_current_user with invalid header format."""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(authorization="InvalidFormat", db=db_session)
        
        assert exc_info.value.status_code == 401
        assert "Invalid authorization header format" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_missing_bearer_prefix(self, db_session: AsyncSession):
        """Test get_current_user without Bearer prefix."""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(authorization="token123", db=db_session)
        
        assert exc_info.value.status_code == 401
        assert "Invalid authorization header format" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, db_session: AsyncSession):
        """Test get_current_user with invalid token."""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(authorization="Bearer invalid_token", db=db_session)
        
        assert exc_info.value.status_code == 401
        assert "Invalid or expired token" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_expired_token(self, db_session: AsyncSession, test_user):
        """Test get_current_user with expired token."""
        # Create an expired token by manipulating the expiration
        from app.core.config import settings
        from datetime import datetime, timedelta, timezone
        from jose import jwt
        
        now = datetime.now(timezone.utc)
        expired_time = now - timedelta(hours=1)
        
        payload = {
            "user_id": str(test_user.id),
            "iat": int(now.timestamp()),
            "exp": int(expired_time.timestamp()),
        }
        
        token = jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(authorization=f"Bearer {token}", db=db_session)
        
        assert exc_info.value.status_code == 401
        assert "Invalid or expired token" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_user_not_found(self, db_session: AsyncSession):
        """Test get_current_user when user doesn't exist in database."""
        non_existent_user_id = uuid4()
        token = create_access_token(str(non_existent_user_id))
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(authorization=f"Bearer {token}", db=db_session)
        
        assert exc_info.value.status_code == 401
        assert "User not found" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_case_insensitive_bearer(self, db_session: AsyncSession, test_user):
        """Test get_current_user with lowercase bearer prefix."""
        token = create_access_token(str(test_user.id))
        authorization = f"bearer {token}"
        
        user = await get_current_user(authorization=authorization, db=db_session)
        
        assert user.id == test_user.id

    @pytest.mark.asyncio
    async def test_get_current_user_uppercase_bearer(self, db_session: AsyncSession, test_user):
        """Test get_current_user with uppercase BEARER prefix."""
        token = create_access_token(str(test_user.id))
        authorization = f"BEARER {token}"
        
        user = await get_current_user(authorization=authorization, db=db_session)
        
        assert user.id == test_user.id


class TestOptionalCurrentUser:
    """Tests for optional_current_user dependency."""

    @pytest.mark.asyncio
    async def test_optional_current_user_valid_token(self, db_session: AsyncSession, test_user):
        """Test optional_current_user with valid token."""
        token = create_access_token(str(test_user.id))
        authorization = f"Bearer {token}"
        
        user = await optional_current_user(authorization=authorization, db=db_session)
        
        assert user is not None
        assert user.id == test_user.id
        assert user.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_optional_current_user_missing_authorization_header(self, db_session: AsyncSession):
        """Test optional_current_user with missing authorization header returns None."""
        user = await optional_current_user(authorization=None, db=db_session)
        
        assert user is None

    @pytest.mark.asyncio
    async def test_optional_current_user_invalid_header_format(self, db_session: AsyncSession):
        """Test optional_current_user with invalid header format raises 401."""
        with pytest.raises(HTTPException) as exc_info:
            await optional_current_user(authorization="InvalidFormat", db=db_session)
        
        assert exc_info.value.status_code == 401
        assert "Invalid authorization header format" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_optional_current_user_invalid_token(self, db_session: AsyncSession):
        """Test optional_current_user with invalid token raises 401."""
        with pytest.raises(HTTPException) as exc_info:
            await optional_current_user(authorization="Bearer invalid_token", db=db_session)
        
        assert exc_info.value.status_code == 401
        assert "Invalid or expired token" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_optional_current_user_expired_token(self, db_session: AsyncSession, test_user):
        """Test optional_current_user with expired token raises 401."""
        from app.core.config import settings
        from datetime import datetime, timedelta, timezone
        from jose import jwt
        
        now = datetime.now(timezone.utc)
        expired_time = now - timedelta(hours=1)
        
        payload = {
            "user_id": str(test_user.id),
            "iat": int(now.timestamp()),
            "exp": int(expired_time.timestamp()),
        }
        
        token = jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")
        
        with pytest.raises(HTTPException) as exc_info:
            await optional_current_user(authorization=f"Bearer {token}", db=db_session)
        
        assert exc_info.value.status_code == 401
        assert "Invalid or expired token" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_optional_current_user_user_not_found(self, db_session: AsyncSession):
        """Test optional_current_user when user doesn't exist in database."""
        non_existent_user_id = uuid4()
        token = create_access_token(str(non_existent_user_id))
        
        with pytest.raises(HTTPException) as exc_info:
            await optional_current_user(authorization=f"Bearer {token}", db=db_session)
        
        assert exc_info.value.status_code == 401
        assert "User not found" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_optional_current_user_case_insensitive_bearer(self, db_session: AsyncSession, test_user):
        """Test optional_current_user with lowercase bearer prefix."""
        token = create_access_token(str(test_user.id))
        authorization = f"bearer {token}"
        
        user = await optional_current_user(authorization=authorization, db=db_session)
        
        assert user is not None
        assert user.id == test_user.id
