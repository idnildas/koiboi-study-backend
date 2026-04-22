"""Tests for authentication endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient
from uuid import uuid4

from app.main import app


@pytest.fixture
async def client():
    """Create an async HTTP client for testing."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


async def _get_avatar_ids(client: AsyncClient):
    """Helper to fetch valid avatar style and color IDs from master data."""
    styles_resp = await client.get("/api/v1/master/avatar-styles")
    colors_resp = await client.get("/api/v1/master/avatar-colors")

    styles = styles_resp.json()["data"]
    colors = colors_resp.json()["data"]

    if not styles or not colors:
        pytest.skip("No avatar styles/colors seeded in database")

    return styles[0]["id"], colors[0]["id"]


@pytest.mark.asyncio
class TestSignUpEndpoint:
    """Tests for POST /auth/sign-up."""

    async def test_sign_up_success(self, client):
        """Test successful user registration returns 201 with token and user profile."""
        style_id, color_id = await _get_avatar_ids(client)

        payload = {
            "name": "Test User",
            "email": f"testuser_{uuid4().hex[:8]}@example.com",
            "password": "securepass123",
            "avatar_style_id": style_id,
            "avatar_color_id": color_id,
        }

        response = await client.post("/api/v1/auth/sign-up", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "token" in data["data"]
        assert "user" in data["data"]
        user = data["data"]["user"]
        assert user["email"] == payload["email"]
        assert user["name"] == payload["name"]
        assert "password" not in user
        assert "password_hash" not in user

    async def test_sign_up_duplicate_email_returns_409(self, client):
        """Test that registering with an existing email returns 409 Conflict."""
        style_id, color_id = await _get_avatar_ids(client)
        email = f"dup_{uuid4().hex[:8]}@example.com"

        payload = {
            "name": "First User",
            "email": email,
            "password": "securepass123",
            "avatar_style_id": style_id,
            "avatar_color_id": color_id,
        }

        await client.post("/api/v1/auth/sign-up", json=payload)
        response = await client.post("/api/v1/auth/sign-up", json=payload)

        assert response.status_code == 409
        data = response.json()
        assert data["detail"]["error"] == "EMAIL_CONFLICT"

    async def test_sign_up_invalid_email_returns_422(self, client):
        """Test that an invalid email format returns 422 Unprocessable Entity."""
        style_id, color_id = await _get_avatar_ids(client)

        payload = {
            "name": "Test User",
            "email": "not-an-email",
            "password": "securepass123",
            "avatar_style_id": style_id,
            "avatar_color_id": color_id,
        }

        response = await client.post("/api/v1/auth/sign-up", json=payload)

        assert response.status_code == 422

    async def test_sign_up_short_name_returns_422(self, client):
        """Test that a name shorter than 2 characters returns 422."""
        style_id, color_id = await _get_avatar_ids(client)

        payload = {
            "name": "A",
            "email": f"user_{uuid4().hex[:8]}@example.com",
            "password": "securepass123",
            "avatar_style_id": style_id,
            "avatar_color_id": color_id,
        }

        response = await client.post("/api/v1/auth/sign-up", json=payload)

        assert response.status_code == 422

    async def test_sign_up_short_password_returns_422(self, client):
        """Test that a password shorter than 6 characters returns 422."""
        style_id, color_id = await _get_avatar_ids(client)

        payload = {
            "name": "Test User",
            "email": f"user_{uuid4().hex[:8]}@example.com",
            "password": "abc",
            "avatar_style_id": style_id,
            "avatar_color_id": color_id,
        }

        response = await client.post("/api/v1/auth/sign-up", json=payload)

        assert response.status_code == 422

    async def test_sign_up_invalid_avatar_style_id_returns_400(self, client):
        """Test that a non-existent avatar_style_id returns 400."""
        _, color_id = await _get_avatar_ids(client)

        payload = {
            "name": "Test User",
            "email": f"user_{uuid4().hex[:8]}@example.com",
            "password": "securepass123",
            "avatar_style_id": str(uuid4()),
            "avatar_color_id": color_id,
        }

        response = await client.post("/api/v1/auth/sign-up", json=payload)

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error"] == "VALIDATION_ERROR"

    async def test_sign_up_invalid_avatar_color_id_returns_400(self, client):
        """Test that a non-existent avatar_color_id returns 400."""
        style_id, _ = await _get_avatar_ids(client)

        payload = {
            "name": "Test User",
            "email": f"user_{uuid4().hex[:8]}@example.com",
            "password": "securepass123",
            "avatar_style_id": style_id,
            "avatar_color_id": str(uuid4()),
        }

        response = await client.post("/api/v1/auth/sign-up", json=payload)

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error"] == "VALIDATION_ERROR"

    async def test_sign_up_missing_fields_returns_422(self, client):
        """Test that missing required fields returns 422."""
        response = await client.post("/api/v1/auth/sign-up", json={"name": "Test"})

        assert response.status_code == 422

    async def test_sign_up_no_auth_required(self, client):
        """Test that sign-up endpoint is public (no auth header needed)."""
        style_id, color_id = await _get_avatar_ids(client)

        payload = {
            "name": "Public User",
            "email": f"public_{uuid4().hex[:8]}@example.com",
            "password": "securepass123",
            "avatar_style_id": style_id,
            "avatar_color_id": color_id,
        }

        response = await client.post("/api/v1/auth/sign-up", json=payload)

        assert response.status_code == 201
