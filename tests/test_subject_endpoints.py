"""Tests for subject management endpoints."""

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


async def _register_and_login(client: AsyncClient, suffix: str = "") -> str:
    """Helper to register a user and return a JWT token."""
    styles_resp = await client.get("/api/v1/master/avatar-styles")
    colors_resp = await client.get("/api/v1/master/avatar-colors")
    styles = styles_resp.json()["data"]
    colors = colors_resp.json()["data"]
    if not styles or not colors:
        pytest.skip("No avatar styles/colors seeded in database")

    email = f"subj_{uuid4().hex[:8]}{suffix}@example.com"
    payload = {
        "name": "Subject Test User",
        "email": email,
        "password": "securepass123",
        "avatar_style_id": styles[0]["id"],
        "avatar_color_id": colors[0]["id"],
    }
    resp = await client.post("/api/v1/auth/sign-up", json=payload)
    assert resp.status_code == 201
    return resp.json()["data"]["token"]


@pytest.mark.asyncio
class TestCreateSubject:
    """Tests for POST /subjects."""

    async def test_create_subject_success(self, client):
        """Test creating a subject returns 201 with subject data."""
        token = await _register_and_login(client)
        payload = {"name": "Data Structures", "description": "DSA study materials"}

        response = await client.post(
            "/api/v1/subjects",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "Data Structures"
        assert data["data"]["description"] == "DSA study materials"
        assert "id" in data["data"]
        assert "user_id" in data["data"]
        assert "created_at" in data["data"]

    async def test_create_subject_minimal(self, client):
        """Test creating a subject with only name succeeds."""
        token = await _register_and_login(client)

        response = await client.post(
            "/api/v1/subjects",
            json={"name": "Minimal Subject"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["data"]["name"] == "Minimal Subject"
        assert data["data"]["color_id"] is None
        assert data["data"]["description"] is None

    async def test_create_subject_no_auth_returns_401(self, client):
        """Test that creating a subject without auth returns 401."""
        response = await client.post("/api/v1/subjects", json={"name": "Test"})
        assert response.status_code == 401

    async def test_create_subject_empty_name_returns_422(self, client):
        """Test that empty name returns 422."""
        token = await _register_and_login(client)

        response = await client.post(
            "/api/v1/subjects",
            json={"name": ""},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 422

    async def test_create_subject_name_too_long_returns_422(self, client):
        """Test that name exceeding 255 chars returns 422."""
        token = await _register_and_login(client)

        response = await client.post(
            "/api/v1/subjects",
            json={"name": "x" * 256},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 422

    async def test_create_subject_description_too_long_returns_422(self, client):
        """Test that description exceeding 1000 chars returns 422."""
        token = await _register_and_login(client)

        response = await client.post(
            "/api/v1/subjects",
            json={"name": "Valid Name", "description": "x" * 1001},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 422

    async def test_create_subject_invalid_color_id_returns_400(self, client):
        """Test that a non-existent color_id returns 400."""
        token = await _register_and_login(client)

        response = await client.post(
            "/api/v1/subjects",
            json={"name": "Valid Name", "color_id": str(uuid4())},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
class TestListSubjects:
    """Tests for GET /subjects."""

    async def test_list_subjects_returns_success(self, client):
        """Test listing subjects returns success response."""
        token = await _register_and_login(client)

        response = await client.get(
            "/api/v1/subjects",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert "total" in data

    async def test_list_subjects_only_returns_own(self, client):
        """Test that listing subjects only returns the user's own subjects."""
        token1 = await _register_and_login(client, "_a")
        token2 = await _register_and_login(client, "_b")

        # Create subject for user1
        await client.post(
            "/api/v1/subjects",
            json={"name": "User1 Subject"},
            headers={"Authorization": f"Bearer {token1}"},
        )

        # User2 should see 0 subjects
        response = await client.get(
            "/api/v1/subjects",
            headers={"Authorization": f"Bearer {token2}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["data"] == []

    async def test_list_subjects_pagination(self, client):
        """Test pagination parameters work correctly."""
        token = await _register_and_login(client)

        # Create 3 subjects
        for i in range(3):
            await client.post(
                "/api/v1/subjects",
                json={"name": f"Subject {i}"},
                headers={"Authorization": f"Bearer {token}"},
            )

        response = await client.get(
            "/api/v1/subjects?limit=2&offset=0",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2
        assert data["total"] == 3

    async def test_list_subjects_sort_by_name(self, client):
        """Test sorting subjects by name."""
        token = await _register_and_login(client)

        for name in ["Zebra", "Apple", "Mango"]:
            await client.post(
                "/api/v1/subjects",
                json={"name": name},
                headers={"Authorization": f"Bearer {token}"},
            )

        response = await client.get(
            "/api/v1/subjects?sort=name",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        names = [s["name"] for s in data["data"]]
        assert names == sorted(names)

    async def test_list_subjects_no_auth_returns_401(self, client):
        """Test that listing subjects without auth returns 401."""
        response = await client.get("/api/v1/subjects")
        assert response.status_code == 401


@pytest.mark.asyncio
class TestUpdateSubject:
    """Tests for PATCH /subjects/{id}."""

    async def test_update_subject_success(self, client):
        """Test updating a subject returns updated data."""
        token = await _register_and_login(client)

        create_resp = await client.post(
            "/api/v1/subjects",
            json={"name": "Original Name"},
            headers={"Authorization": f"Bearer {token}"},
        )
        subject_id = create_resp.json()["data"]["id"]

        response = await client.patch(
            f"/api/v1/subjects/{subject_id}",
            json={"name": "Updated Name", "description": "New description"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "Updated Name"
        assert data["data"]["description"] == "New description"

    async def test_update_subject_not_found_returns_404(self, client):
        """Test updating a non-existent subject returns 404."""
        token = await _register_and_login(client)

        response = await client.patch(
            f"/api/v1/subjects/{uuid4()}",
            json={"name": "New Name"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404

    async def test_update_subject_wrong_user_returns_403(self, client):
        """Test that updating another user's subject returns 403."""
        token1 = await _register_and_login(client, "_c")
        token2 = await _register_and_login(client, "_d")

        create_resp = await client.post(
            "/api/v1/subjects",
            json={"name": "User1 Subject"},
            headers={"Authorization": f"Bearer {token1}"},
        )
        subject_id = create_resp.json()["data"]["id"]

        response = await client.patch(
            f"/api/v1/subjects/{subject_id}",
            json={"name": "Hijacked"},
            headers={"Authorization": f"Bearer {token2}"},
        )

        assert response.status_code == 403
        data = response.json()
        assert data["detail"]["error"] == "FORBIDDEN"

    async def test_update_subject_no_auth_returns_401(self, client):
        """Test that updating without auth returns 401."""
        response = await client.patch(
            f"/api/v1/subjects/{uuid4()}",
            json={"name": "New Name"},
        )
        assert response.status_code == 401


@pytest.mark.asyncio
class TestDeleteSubject:
    """Tests for DELETE /subjects/{id}."""

    async def test_delete_subject_success(self, client):
        """Test deleting a subject returns 200 with success message."""
        token = await _register_and_login(client)

        create_resp = await client.post(
            "/api/v1/subjects",
            json={"name": "To Delete"},
            headers={"Authorization": f"Bearer {token}"},
        )
        subject_id = create_resp.json()["data"]["id"]

        response = await client.delete(
            f"/api/v1/subjects/{subject_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    async def test_delete_subject_removes_from_list(self, client):
        """Test that deleted subject no longer appears in list."""
        token = await _register_and_login(client)

        create_resp = await client.post(
            "/api/v1/subjects",
            json={"name": "Will Be Deleted"},
            headers={"Authorization": f"Bearer {token}"},
        )
        subject_id = create_resp.json()["data"]["id"]

        await client.delete(
            f"/api/v1/subjects/{subject_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        list_resp = await client.get(
            "/api/v1/subjects",
            headers={"Authorization": f"Bearer {token}"},
        )
        ids = [s["id"] for s in list_resp.json()["data"]]
        assert subject_id not in ids

    async def test_delete_subject_not_found_returns_404(self, client):
        """Test deleting a non-existent subject returns 404."""
        token = await _register_and_login(client)

        response = await client.delete(
            f"/api/v1/subjects/{uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404

    async def test_delete_subject_wrong_user_returns_403(self, client):
        """Test that deleting another user's subject returns 403."""
        token1 = await _register_and_login(client, "_e")
        token2 = await _register_and_login(client, "_f")

        create_resp = await client.post(
            "/api/v1/subjects",
            json={"name": "User1 Subject"},
            headers={"Authorization": f"Bearer {token1}"},
        )
        subject_id = create_resp.json()["data"]["id"]

        response = await client.delete(
            f"/api/v1/subjects/{subject_id}",
            headers={"Authorization": f"Bearer {token2}"},
        )

        assert response.status_code == 403
        data = response.json()
        assert data["detail"]["error"] == "FORBIDDEN"

    async def test_delete_subject_no_auth_returns_401(self, client):
        """Test that deleting without auth returns 401."""
        response = await client.delete(f"/api/v1/subjects/{uuid4()}")
        assert response.status_code == 401
