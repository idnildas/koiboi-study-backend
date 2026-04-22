"""Tests for topic management endpoints (tasks 27, 28, 29)."""

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

    email = f"topic_{uuid4().hex[:8]}{suffix}@example.com"
    payload = {
        "name": "Topic Test User",
        "email": email,
        "password": "securepass123",
        "avatar_style_id": styles[0]["id"],
        "avatar_color_id": colors[0]["id"],
    }
    resp = await client.post("/api/v1/auth/sign-up", json=payload)
    assert resp.status_code == 201
    return resp.json()["data"]["token"]


async def _create_subject(client: AsyncClient, token: str, name: str = "Test Subject") -> str:
    """Helper to create a subject and return its ID."""
    resp = await client.post(
        "/api/v1/subjects",
        json={"name": name},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    return resp.json()["data"]["id"]


@pytest.mark.asyncio
class TestCreateTopic:
    """Tests for POST /subjects/{subjectId}/topics."""

    async def test_create_topic_success(self, client):
        """Test creating a topic returns 201 with topic data."""
        token = await _register_and_login(client)
        subject_id = await _create_subject(client, token)

        response = await client.post(
            f"/api/v1/subjects/{subject_id}/topics",
            json={"name": "Graph Algorithms"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "Graph Algorithms"
        assert data["data"]["subject_id"] == subject_id
        assert data["data"]["status"] == "not-started"
        assert data["data"]["confidence"] == 0
        assert "id" in data["data"]
        assert "created_at" in data["data"]

    async def test_create_topic_with_tint_id(self, client):
        """Test creating a topic with an explicit tint_id."""
        token = await _register_and_login(client)
        subject_id = await _create_subject(client, token)

        tints_resp = await client.get("/api/v1/master/tint-palette")
        tints = tints_resp.json()["data"]
        if not tints:
            pytest.skip("No tints seeded in database")
        tint_id = tints[0]["id"]

        response = await client.post(
            f"/api/v1/subjects/{subject_id}/topics",
            json={"name": "Sorting Algorithms", "tint_id": tint_id},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["data"]["tint_id"] == tint_id

    async def test_create_topic_assigns_random_tint_when_not_provided(self, client):
        """Test that a tint is assigned automatically when not provided."""
        token = await _register_and_login(client)
        subject_id = await _create_subject(client, token)

        response = await client.post(
            f"/api/v1/subjects/{subject_id}/topics",
            json={"name": "Dynamic Programming"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 201
        # tint_id may be None if no tints seeded, but should not error
        data = response.json()
        assert data["success"] is True

    async def test_create_topic_no_auth_returns_401(self, client):
        """Test that creating a topic without auth returns 401."""
        response = await client.post(
            f"/api/v1/subjects/{uuid4()}/topics",
            json={"name": "Test"},
        )
        assert response.status_code == 401

    async def test_create_topic_nonexistent_subject_returns_404(self, client):
        """Test that creating a topic for a non-existent subject returns 404."""
        token = await _register_and_login(client)

        response = await client.post(
            f"/api/v1/subjects/{uuid4()}/topics",
            json={"name": "Test Topic"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404

    async def test_create_topic_wrong_user_returns_403(self, client):
        """Test that creating a topic in another user's subject returns 403."""
        token1 = await _register_and_login(client, "_a")
        token2 = await _register_and_login(client, "_b")

        subject_id = await _create_subject(client, token1)

        response = await client.post(
            f"/api/v1/subjects/{subject_id}/topics",
            json={"name": "Hijacked Topic"},
            headers={"Authorization": f"Bearer {token2}"},
        )

        assert response.status_code == 403
        data = response.json()
        assert data["detail"]["error"] == "FORBIDDEN"

    async def test_create_topic_empty_name_returns_422(self, client):
        """Test that empty name returns 422."""
        token = await _register_and_login(client)
        subject_id = await _create_subject(client, token)

        response = await client.post(
            f"/api/v1/subjects/{subject_id}/topics",
            json={"name": ""},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 422

    async def test_create_topic_name_too_long_returns_422(self, client):
        """Test that name exceeding 255 chars returns 422."""
        token = await _register_and_login(client)
        subject_id = await _create_subject(client, token)

        response = await client.post(
            f"/api/v1/subjects/{subject_id}/topics",
            json={"name": "x" * 256},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 422

    async def test_create_topic_invalid_tint_id_returns_400(self, client):
        """Test that a non-existent tint_id returns 400."""
        token = await _register_and_login(client)
        subject_id = await _create_subject(client, token)

        response = await client.post(
            f"/api/v1/subjects/{subject_id}/topics",
            json={"name": "Valid Name", "tint_id": str(uuid4())},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
class TestListTopics:
    """Tests for GET /subjects/{subjectId}/topics."""

    async def test_list_topics_returns_success(self, client):
        """Test listing topics returns success response."""
        token = await _register_and_login(client)
        subject_id = await _create_subject(client, token)

        response = await client.get(
            f"/api/v1/subjects/{subject_id}/topics",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert "total" in data

    async def test_list_topics_returns_created_topics(self, client):
        """Test that created topics appear in the list."""
        token = await _register_and_login(client)
        subject_id = await _create_subject(client, token)

        await client.post(
            f"/api/v1/subjects/{subject_id}/topics",
            json={"name": "Topic A"},
            headers={"Authorization": f"Bearer {token}"},
        )
        await client.post(
            f"/api/v1/subjects/{subject_id}/topics",
            json={"name": "Topic B"},
            headers={"Authorization": f"Bearer {token}"},
        )

        response = await client.get(
            f"/api/v1/subjects/{subject_id}/topics",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        names = [t["name"] for t in data["data"]]
        assert "Topic A" in names
        assert "Topic B" in names

    async def test_list_topics_sorted_by_created_at_asc(self, client):
        """Test that topics are sorted by created_at ascending."""
        token = await _register_and_login(client)
        subject_id = await _create_subject(client, token)

        for name in ["First", "Second", "Third"]:
            await client.post(
                f"/api/v1/subjects/{subject_id}/topics",
                json={"name": name},
                headers={"Authorization": f"Bearer {token}"},
            )

        response = await client.get(
            f"/api/v1/subjects/{subject_id}/topics",
            headers={"Authorization": f"Bearer {token}"},
        )

        data = response.json()
        created_ats = [t["created_at"] for t in data["data"]]
        assert created_ats == sorted(created_ats)

    async def test_list_topics_pagination(self, client):
        """Test pagination parameters work correctly."""
        token = await _register_and_login(client)
        subject_id = await _create_subject(client, token)

        for i in range(4):
            await client.post(
                f"/api/v1/subjects/{subject_id}/topics",
                json={"name": f"Topic {i}"},
                headers={"Authorization": f"Bearer {token}"},
            )

        response = await client.get(
            f"/api/v1/subjects/{subject_id}/topics?limit=2&offset=0",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2
        assert data["total"] == 4

    async def test_list_topics_status_filter(self, client):
        """Test filtering topics by status."""
        token = await _register_and_login(client)
        subject_id = await _create_subject(client, token)

        # Create a topic and update it to in-progress
        create_resp = await client.post(
            f"/api/v1/subjects/{subject_id}/topics",
            json={"name": "In Progress Topic"},
            headers={"Authorization": f"Bearer {token}"},
        )
        topic_id = create_resp.json()["data"]["id"]
        await client.patch(
            f"/api/v1/topics/{topic_id}",
            json={"status": "in-progress"},
            headers={"Authorization": f"Bearer {token}"},
        )

        # Create another topic (stays not-started)
        await client.post(
            f"/api/v1/subjects/{subject_id}/topics",
            json={"name": "Not Started Topic"},
            headers={"Authorization": f"Bearer {token}"},
        )

        response = await client.get(
            f"/api/v1/subjects/{subject_id}/topics?status=in-progress",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["data"][0]["status"] == "in-progress"

    async def test_list_topics_no_auth_returns_401(self, client):
        """Test that listing topics without auth returns 401."""
        response = await client.get(f"/api/v1/subjects/{uuid4()}/topics")
        assert response.status_code == 401

    async def test_list_topics_wrong_user_returns_403(self, client):
        """Test that listing topics in another user's subject returns 403."""
        token1 = await _register_and_login(client, "_c")
        token2 = await _register_and_login(client, "_d")

        subject_id = await _create_subject(client, token1)

        response = await client.get(
            f"/api/v1/subjects/{subject_id}/topics",
            headers={"Authorization": f"Bearer {token2}"},
        )

        assert response.status_code == 403
        data = response.json()
        assert data["detail"]["error"] == "FORBIDDEN"

    async def test_list_topics_nonexistent_subject_returns_404(self, client):
        """Test that listing topics for a non-existent subject returns 404."""
        token = await _register_and_login(client)

        response = await client.get(
            f"/api/v1/subjects/{uuid4()}/topics",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404


@pytest.mark.asyncio
class TestUpdateTopic:
    """Tests for PATCH /topics/{id}."""

    async def test_update_topic_name(self, client):
        """Test updating a topic name returns updated data."""
        token = await _register_and_login(client)
        subject_id = await _create_subject(client, token)

        create_resp = await client.post(
            f"/api/v1/subjects/{subject_id}/topics",
            json={"name": "Original Name"},
            headers={"Authorization": f"Bearer {token}"},
        )
        topic_id = create_resp.json()["data"]["id"]

        response = await client.patch(
            f"/api/v1/topics/{topic_id}",
            json={"name": "Updated Name"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "Updated Name"

    async def test_update_topic_status(self, client):
        """Test updating topic status."""
        token = await _register_and_login(client)
        subject_id = await _create_subject(client, token)

        create_resp = await client.post(
            f"/api/v1/subjects/{subject_id}/topics",
            json={"name": "Status Test"},
            headers={"Authorization": f"Bearer {token}"},
        )
        topic_id = create_resp.json()["data"]["id"]

        for new_status in ["in-progress", "revising", "completed", "not-started"]:
            response = await client.patch(
                f"/api/v1/topics/{topic_id}",
                json={"status": new_status},
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 200
            assert response.json()["data"]["status"] == new_status

    async def test_update_topic_confidence(self, client):
        """Test updating topic confidence."""
        token = await _register_and_login(client)
        subject_id = await _create_subject(client, token)

        create_resp = await client.post(
            f"/api/v1/subjects/{subject_id}/topics",
            json={"name": "Confidence Test"},
            headers={"Authorization": f"Bearer {token}"},
        )
        topic_id = create_resp.json()["data"]["id"]

        response = await client.patch(
            f"/api/v1/topics/{topic_id}",
            json={"confidence": 4},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.json()["data"]["confidence"] == 4

    async def test_update_topic_invalid_confidence_returns_422(self, client):
        """Test that confidence outside 0-5 returns 422."""
        token = await _register_and_login(client)
        subject_id = await _create_subject(client, token)

        create_resp = await client.post(
            f"/api/v1/subjects/{subject_id}/topics",
            json={"name": "Confidence Test"},
            headers={"Authorization": f"Bearer {token}"},
        )
        topic_id = create_resp.json()["data"]["id"]

        response = await client.patch(
            f"/api/v1/topics/{topic_id}",
            json={"confidence": 6},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 422

    async def test_update_topic_invalid_status_returns_422(self, client):
        """Test that invalid status returns 422."""
        token = await _register_and_login(client)
        subject_id = await _create_subject(client, token)

        create_resp = await client.post(
            f"/api/v1/subjects/{subject_id}/topics",
            json={"name": "Status Test"},
            headers={"Authorization": f"Bearer {token}"},
        )
        topic_id = create_resp.json()["data"]["id"]

        response = await client.patch(
            f"/api/v1/topics/{topic_id}",
            json={"status": "invalid-status"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 422

    async def test_update_topic_not_found_returns_404(self, client):
        """Test updating a non-existent topic returns 404."""
        token = await _register_and_login(client)

        response = await client.patch(
            f"/api/v1/topics/{uuid4()}",
            json={"name": "New Name"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404

    async def test_update_topic_wrong_user_returns_403(self, client):
        """Test that updating another user's topic returns 403."""
        token1 = await _register_and_login(client, "_e")
        token2 = await _register_and_login(client, "_f")

        subject_id = await _create_subject(client, token1)
        create_resp = await client.post(
            f"/api/v1/subjects/{subject_id}/topics",
            json={"name": "User1 Topic"},
            headers={"Authorization": f"Bearer {token1}"},
        )
        topic_id = create_resp.json()["data"]["id"]

        response = await client.patch(
            f"/api/v1/topics/{topic_id}",
            json={"name": "Hijacked"},
            headers={"Authorization": f"Bearer {token2}"},
        )

        assert response.status_code == 403
        data = response.json()
        assert data["detail"]["error"] == "FORBIDDEN"

    async def test_update_topic_no_auth_returns_401(self, client):
        """Test that updating without auth returns 401."""
        response = await client.patch(
            f"/api/v1/topics/{uuid4()}",
            json={"name": "New Name"},
        )
        assert response.status_code == 401


@pytest.mark.asyncio
class TestDeleteTopic:
    """Tests for DELETE /topics/{id}."""

    async def test_delete_topic_success(self, client):
        """Test deleting a topic returns 200 with success message."""
        token = await _register_and_login(client)
        subject_id = await _create_subject(client, token)

        create_resp = await client.post(
            f"/api/v1/subjects/{subject_id}/topics",
            json={"name": "To Delete"},
            headers={"Authorization": f"Bearer {token}"},
        )
        topic_id = create_resp.json()["data"]["id"]

        response = await client.delete(
            f"/api/v1/topics/{topic_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    async def test_delete_topic_removes_from_list(self, client):
        """Test that deleted topic no longer appears in list."""
        token = await _register_and_login(client)
        subject_id = await _create_subject(client, token)

        create_resp = await client.post(
            f"/api/v1/subjects/{subject_id}/topics",
            json={"name": "Will Be Deleted"},
            headers={"Authorization": f"Bearer {token}"},
        )
        topic_id = create_resp.json()["data"]["id"]

        await client.delete(
            f"/api/v1/topics/{topic_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        list_resp = await client.get(
            f"/api/v1/subjects/{subject_id}/topics",
            headers={"Authorization": f"Bearer {token}"},
        )
        ids = [t["id"] for t in list_resp.json()["data"]]
        assert topic_id not in ids

    async def test_delete_topic_not_found_returns_404(self, client):
        """Test deleting a non-existent topic returns 404."""
        token = await _register_and_login(client)

        response = await client.delete(
            f"/api/v1/topics/{uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404

    async def test_delete_topic_wrong_user_returns_403(self, client):
        """Test that deleting another user's topic returns 403."""
        token1 = await _register_and_login(client, "_g")
        token2 = await _register_and_login(client, "_h")

        subject_id = await _create_subject(client, token1)
        create_resp = await client.post(
            f"/api/v1/subjects/{subject_id}/topics",
            json={"name": "User1 Topic"},
            headers={"Authorization": f"Bearer {token1}"},
        )
        topic_id = create_resp.json()["data"]["id"]

        response = await client.delete(
            f"/api/v1/topics/{topic_id}",
            headers={"Authorization": f"Bearer {token2}"},
        )

        assert response.status_code == 403
        data = response.json()
        assert data["detail"]["error"] == "FORBIDDEN"

    async def test_delete_topic_no_auth_returns_401(self, client):
        """Test that deleting without auth returns 401."""
        response = await client.delete(f"/api/v1/topics/{uuid4()}")
        assert response.status_code == 401
