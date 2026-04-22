"""Tests for master data endpoints (avatar styles, colors, tints)."""

import pytest
from httpx import ASGITransport, AsyncClient
from uuid import uuid4

from app.main import app


@pytest.fixture
async def client():
    """Create an async HTTP client for testing."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


@pytest.mark.asyncio
class TestAvatarStylesEndpoints:
    """Tests for avatar styles endpoints."""

    async def test_list_avatar_styles_returns_success(self, client):
        """Test that list avatar styles endpoint returns success response."""
        response = await client.get("/api/v1/master/avatar-styles")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "total" in data
        assert isinstance(data["data"], list)

    async def test_list_avatar_styles_pagination_default(self, client):
        """Test that default pagination parameters work correctly."""
        response = await client.get("/api/v1/master/avatar-styles")

        assert response.status_code == 200
        data = response.json()
        # Default limit is 50, offset is 0
        assert data["total"] >= 0

    async def test_list_avatar_styles_pagination_custom(self, client):
        """Test that custom pagination parameters work correctly."""
        response = await client.get("/api/v1/master/avatar-styles?limit=5&offset=0")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) <= 5

    async def test_list_avatar_styles_excludes_svg_template(self, client):
        """Test that list endpoint excludes SVG template from response."""
        response = await client.get("/api/v1/master/avatar-styles")

        assert response.status_code == 200
        data = response.json()

        if data["data"]:
            # SVG template should be None in list view
            assert data["data"][0]["svg_template"] is None

    async def test_list_avatar_styles_invalid_offset(self, client):
        """Test that invalid offset parameter returns validation error."""
        response = await client.get("/api/v1/master/avatar-styles?offset=-1")

        assert response.status_code == 422  # Validation error

    async def test_avatar_styles_sorted_by_display_order(self, client):
        """Test that avatar styles are sorted by display_order ascending."""
        response = await client.get("/api/v1/master/avatar-styles")

        assert response.status_code == 200
        data = response.json()

        if len(data["data"]) > 1:
            display_orders = [item["display_order"] for item in data["data"]]
            assert display_orders == sorted(display_orders)

    async def test_avatar_styles_no_auth_required(self, client):
        """Test that avatar styles endpoints are public (no auth required)."""
        # No Authorization header should work
        response = await client.get("/api/v1/master/avatar-styles")

        assert response.status_code == 200


@pytest.mark.asyncio
class TestAvatarColorsEndpoints:
    """Tests for avatar colors endpoints."""

    async def test_list_avatar_colors_returns_success(self, client):
        """Test that list avatar colors endpoint returns success response."""
        response = await client.get("/api/v1/master/avatar-colors")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "total" in data
        assert isinstance(data["data"], list)

    async def test_list_avatar_colors_pagination_default(self, client):
        """Test that default pagination parameters work correctly."""
        response = await client.get("/api/v1/master/avatar-colors")

        assert response.status_code == 200
        data = response.json()
        # Default limit is 50, offset is 0
        assert data["total"] >= 0

    async def test_list_avatar_colors_pagination_custom(self, client):
        """Test that custom pagination parameters work correctly."""
        response = await client.get("/api/v1/master/avatar-colors?limit=5&offset=0")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) <= 5

    async def test_list_avatar_colors_includes_color_representations(self, client):
        """Test that list endpoint includes hex, RGB, and HSL representations."""
        response = await client.get("/api/v1/master/avatar-colors")

        assert response.status_code == 200
        data = response.json()

        if data["data"]:
            color = data["data"][0]
            assert "hex_code" in color
            assert "rgb" in color
            assert "hsl" in color
            # Hex code should start with #
            assert color["hex_code"].startswith("#")

    async def test_list_avatar_colors_invalid_offset(self, client):
        """Test that invalid offset parameter returns validation error."""
        response = await client.get("/api/v1/master/avatar-colors?offset=-1")

        assert response.status_code == 422  # Validation error

    async def test_avatar_colors_sorted_by_display_order(self, client):
        """Test that avatar colors are sorted by display_order ascending."""
        response = await client.get("/api/v1/master/avatar-colors")

        assert response.status_code == 200
        data = response.json()

        if len(data["data"]) > 1:
            display_orders = [item["display_order"] for item in data["data"]]
            assert display_orders == sorted(display_orders)

    async def test_avatar_colors_no_auth_required(self, client):
        """Test that avatar colors endpoints are public (no auth required)."""
        # No Authorization header should work
        response = await client.get("/api/v1/master/avatar-colors")

        assert response.status_code == 200


@pytest.mark.asyncio
class TestTintPaletteEndpoints:
    """Tests for tint palette endpoints."""

    async def test_list_tint_palette_returns_success(self, client):
        """Test that list tint palette endpoint returns success response."""
        response = await client.get("/api/v1/master/tint-palette")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "total" in data
        assert isinstance(data["data"], list)

    async def test_list_tint_palette_pagination_default(self, client):
        """Test that default pagination parameters work correctly."""
        response = await client.get("/api/v1/master/tint-palette")

        assert response.status_code == 200
        data = response.json()
        # Default limit is 50, offset is 0
        assert data["total"] >= 0

    async def test_list_tint_palette_pagination_custom(self, client):
        """Test that custom pagination parameters work correctly."""
        response = await client.get("/api/v1/master/tint-palette?limit=5&offset=0")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) <= 5

    async def test_list_tint_palette_includes_required_fields(self, client):
        """Test that list endpoint includes name, HSL, hex code, and category."""
        response = await client.get("/api/v1/master/tint-palette")

        assert response.status_code == 200
        data = response.json()

        if data["data"]:
            tint = data["data"][0]
            assert "name" in tint
            assert "hsl" in tint
            assert "hex_code" in tint
            assert "category" in tint

    async def test_list_tint_palette_invalid_offset(self, client):
        """Test that invalid offset parameter returns validation error."""
        response = await client.get("/api/v1/master/tint-palette?offset=-1")

        assert response.status_code == 422  # Validation error

    async def test_tint_palette_sorted_by_display_order(self, client):
        """Test that tints are sorted by display_order ascending."""
        response = await client.get("/api/v1/master/tint-palette")

        assert response.status_code == 200
        data = response.json()

        if len(data["data"]) > 1:
            display_orders = [item["display_order"] for item in data["data"]]
            assert display_orders == sorted(display_orders)

    async def test_tint_palette_no_auth_required(self, client):
        """Test that tint palette endpoints are public (no auth required)."""
        # No Authorization header should work
        response = await client.get("/api/v1/master/tint-palette")

        assert response.status_code == 200
