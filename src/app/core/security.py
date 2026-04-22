"""Security utilities for password hashing and JWT token management."""

from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings


# Password Hashing Functions
def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt with 10+ rounds.
    
    Args:
        password: Plain text password to hash
        
    Returns:
        Hashed password string
    """
    salt = bcrypt.gensalt(rounds=10)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a bcrypt hash.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Bcrypt hash to verify against
        
    Returns:
        True if password matches, False otherwise
    """
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


# JWT Token Functions
def create_access_token(user_id: str) -> str:
    """
    Create a JWT access token with user_id, exp, and iat claims.
    
    Args:
        user_id: UUID of the user
        
    Returns:
        JWT token string
    """
    now = datetime.now(timezone.utc)
    expiration = now + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    
    payload = {
        "user_id": user_id,
        "iat": int(now.timestamp()),
        "exp": int(expiration.timestamp()),
    }
    
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")
    return token


def verify_token(token: str) -> Optional[dict]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string to verify
        
    Returns:
        Decoded token payload if valid, None if invalid or expired
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        return payload
    except JWTError:
        return None


def extract_user_id(token: str) -> Optional[str]:
    """
    Extract user_id from a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        User ID if token is valid, None otherwise
    """
    payload = verify_token(token)
    if payload is None:
        return None
    return payload.get("user_id")
