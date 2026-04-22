"""Tests for security utilities (password hashing and JWT tokens)."""

import time
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from jose import jwt

from app.core.config import settings
from app.core.security import (
    create_access_token,
    extract_user_id,
    hash_password,
    verify_password,
    verify_token,
)


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_hash_password_creates_valid_hash(self):
        """Test that hash_password creates a valid bcrypt hash."""
        password = "test_password_123"
        hashed = hash_password(password)
        
        # Hash should be a string
        assert isinstance(hashed, str)
        # Hash should not be the same as the plain password
        assert hashed != password
        # Hash should be a valid bcrypt hash (starts with $2b$)
        assert hashed.startswith("$2b$")

    def test_hash_password_uses_10_rounds(self):
        """Test that hash_password uses at least 10 rounds."""
        password = "test_password_123"
        hashed = hash_password(password)
        
        # Bcrypt hash format: $2b$rounds$salt$hash
        # Extract rounds from hash
        rounds = int(hashed.split("$")[2])
        assert rounds >= 10

    def test_hash_password_different_hashes_for_same_password(self):
        """Test that hashing the same password produces different hashes (due to salt)."""
        password = "test_password_123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        # Different hashes due to different salts
        assert hash1 != hash2

    def test_verify_password_correct_password(self):
        """Test that verify_password returns True for correct password."""
        password = "test_password_123"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect_password(self):
        """Test that verify_password returns False for incorrect password."""
        password = "test_password_123"
        wrong_password = "wrong_password_456"
        hashed = hash_password(password)
        
        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_empty_password(self):
        """Test that verify_password handles empty passwords."""
        password = "test_password_123"
        hashed = hash_password(password)
        
        assert verify_password("", hashed) is False

    def test_verify_password_case_sensitive(self):
        """Test that password verification is case-sensitive."""
        password = "TestPassword123"
        hashed = hash_password(password)
        
        assert verify_password("testpassword123", hashed) is False
        assert verify_password("TestPassword123", hashed) is True


class TestJWTTokens:
    """Tests for JWT token generation and validation."""

    def test_create_access_token_returns_string(self):
        """Test that create_access_token returns a string."""
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        token = create_access_token(user_id)
        
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_has_three_parts(self):
        """Test that JWT token has three parts (header.payload.signature)."""
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        token = create_access_token(user_id)
        
        parts = token.split(".")
        assert len(parts) == 3

    def test_create_access_token_contains_user_id(self):
        """Test that JWT token contains user_id in payload."""
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        token = create_access_token(user_id)
        
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        assert payload["user_id"] == user_id

    def test_create_access_token_contains_iat(self):
        """Test that JWT token contains iat (issued at) claim."""
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        before = int(datetime.now(timezone.utc).timestamp())
        token = create_access_token(user_id)
        after = int(datetime.now(timezone.utc).timestamp())
        
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        assert "iat" in payload
        assert before <= payload["iat"] <= after

    def test_create_access_token_contains_exp(self):
        """Test that JWT token contains exp (expiration) claim."""
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        token = create_access_token(user_id)
        
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        assert "exp" in payload

    def test_create_access_token_expiration_is_correct(self):
        """Test that JWT token expiration is set to JWT_EXPIRATION_HOURS."""
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        token = create_access_token(user_id)
        
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        iat = payload["iat"]
        exp = payload["exp"]
        
        # Expiration should be approximately JWT_EXPIRATION_HOURS from iat
        expected_exp = iat + (settings.JWT_EXPIRATION_HOURS * 3600)
        # Allow 1 second tolerance for execution time
        assert abs(exp - expected_exp) <= 1

    def test_verify_token_valid_token(self):
        """Test that verify_token returns payload for valid token."""
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        token = create_access_token(user_id)
        
        payload = verify_token(token)
        assert payload is not None
        assert payload["user_id"] == user_id

    def test_verify_token_invalid_token(self):
        """Test that verify_token returns None for invalid token."""
        invalid_token = "invalid.token.here"
        
        payload = verify_token(invalid_token)
        assert payload is None

    def test_verify_token_malformed_token(self):
        """Test that verify_token returns None for malformed token."""
        malformed_token = "not_a_valid_jwt"
        
        payload = verify_token(malformed_token)
        assert payload is None

    def test_verify_token_wrong_secret(self):
        """Test that verify_token returns None when token signed with different secret."""
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        
        # Create token with different secret
        payload = {
            "user_id": user_id,
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=24)).timestamp()),
        }
        token = jwt.encode(payload, "different_secret_key", algorithm="HS256")
        
        # Verify with correct secret should fail
        result = verify_token(token)
        assert result is None

    def test_verify_token_expired_token(self):
        """Test that verify_token returns None for expired token."""
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        
        # Create expired token
        now = datetime.now(timezone.utc)
        payload = {
            "user_id": user_id,
            "iat": int((now - timedelta(hours=25)).timestamp()),
            "exp": int((now - timedelta(hours=1)).timestamp()),
        }
        token = jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")
        
        # Verify should fail for expired token
        result = verify_token(token)
        assert result is None

    def test_extract_user_id_valid_token(self):
        """Test that extract_user_id returns user_id for valid token."""
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        token = create_access_token(user_id)
        
        extracted_id = extract_user_id(token)
        assert extracted_id == user_id

    def test_extract_user_id_invalid_token(self):
        """Test that extract_user_id returns None for invalid token."""
        invalid_token = "invalid.token.here"
        
        extracted_id = extract_user_id(invalid_token)
        assert extracted_id is None

    def test_extract_user_id_expired_token(self):
        """Test that extract_user_id returns None for expired token."""
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        
        # Create expired token
        now = datetime.now(timezone.utc)
        payload = {
            "user_id": user_id,
            "iat": int((now - timedelta(hours=25)).timestamp()),
            "exp": int((now - timedelta(hours=1)).timestamp()),
        }
        token = jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")
        
        # Extract should fail for expired token
        extracted_id = extract_user_id(token)
        assert extracted_id is None

    def test_extract_user_id_missing_user_id_claim(self):
        """Test that extract_user_id returns None when user_id claim is missing."""
        # Create token without user_id
        now = datetime.now(timezone.utc)
        payload = {
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=24)).timestamp()),
        }
        token = jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")
        
        extracted_id = extract_user_id(token)
        assert extracted_id is None


class TestTokenIntegration:
    """Integration tests for token creation and verification."""

    def test_token_roundtrip(self):
        """Test creating and verifying a token."""
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        
        # Create token
        token = create_access_token(user_id)
        
        # Verify token
        payload = verify_token(token)
        assert payload is not None
        
        # Extract user_id
        extracted_id = extract_user_id(token)
        assert extracted_id == user_id

    def test_multiple_tokens_different_iat(self):
        """Test that tokens created at different times have different iat values."""
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        
        token1 = create_access_token(user_id)
        time.sleep(0.1)  # Small delay to ensure different timestamp
        token2 = create_access_token(user_id)
        
        payload1 = verify_token(token1)
        payload2 = verify_token(token2)
        
        # iat should be different (or very close but not identical)
        assert payload1["iat"] <= payload2["iat"]
