"""Dependency injection for authentication and authorization."""

from typing import Optional
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import extract_user_id
from app.db.session import get_session
from app.models.user import User


async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_session),
) -> User:
    """
    Dependency to extract and validate JWT token from Authorization header.
    
    Extracts the JWT token from the Authorization header (Bearer scheme),
    validates the token, extracts the user_id, and queries the database
    to return the User object.
    
    Args:
        authorization: Authorization header value (e.g., "Bearer <token>")
        db: Database session
        
    Returns:
        User object if token is valid
        
    Raises:
        HTTPException: 401 Unauthorized if token is missing, invalid, or expired
    """
    # Check if Authorization header is present
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
        )
    
    # Extract token from "Bearer <token>" format
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
        )
    
    token = parts[1]
    
    # Extract user_id from token
    user_id = extract_user_id(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    
    # Query database to get User object
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    
    result = await db.execute(
        select(User).where(User.id == user_uuid)
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    return user


async def optional_current_user(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_session),
) -> Optional[User]:
    """
    Dependency for optional authentication on public endpoints.
    
    Attempts to extract and validate JWT token from Authorization header.
    Returns the User object if token is valid, or None if token is missing.
    Raises 401 Unauthorized only if token is present but invalid/expired.
    
    Args:
        authorization: Authorization header value (e.g., "Bearer <token>")
        db: Database session
        
    Returns:
        User object if token is valid, None if token is missing
        
    Raises:
        HTTPException: 401 Unauthorized if token is present but invalid/expired
    """
    # If no authorization header, return None (public access allowed)
    if not authorization:
        return None
    
    # Extract token from "Bearer <token>" format
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
        )
    
    token = parts[1]
    
    # Extract user_id from token
    user_id = extract_user_id(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    
    # Query database to get User object
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    
    result = await db.execute(
        select(User).where(User.id == user_uuid)
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    return user
