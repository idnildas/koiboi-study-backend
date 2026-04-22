"""Tests for note management endpoints (tasks 30, 31, 32)."""

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

    email = f"note_{uuid4().hex[:8]}{suffix}@example.com"
    payload = {
        "name": "Note Test User",
        "email": email,
        "password": "securepass123",
        "avatar_style_id": styles[0]["id"],
        "avatar_color_id": colors[0]["id"],
    }
    resp = await client.post("/api/v1/auth/sign-up", json=payload)
    assert resp.status_code == 201
    return resp.json()["data"]["token"]


async def _create_subject(client: AsyncClient, token: str, name: str = "Test Subject") -> str:
    resp = await client.post(
        "/api/v1/subjects",
        json={"name": name},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    return resp.json()["data"]["id"]


async def _create_topic(client: AsyncClient, token: str, subject_id: str, name: str = "Test Topic") -> str:
    resp = await client.post(
        f"/api/v1/subjects/{subject_id}/topics",
        json={"name": name},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    return resp.json()["data"]["id"]


@pytest.mark.asyncio
class TestCreateNote:
    """Tests for POST /topics/{topicId}/notes."""

    async def test_create_note_success(self, client):
        """Test creating a note returns 201 with note data."""
        token = await _register_and_login(client)
        subject_id = await _create_subject(client, token)
        topic_id = await _create_topic(client, token, subject_id)

        response = await client.post(
            f"/api/v1/topics/{topic_id}/notes",
            json={"title": "My First Note"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["title"] == "My First Note"
        assert data["data"]["topic_id"] == topic_id
        assert data["data"]["scribbles"] == []
        assert "id" in data["data"]
        assert "created_at" in data["data"]
        assert "updated_at" in data["data"]

    async def test_create_note_with_body(self, client):
        """Test creating a note with optional body."""
        token = await _register_and_login(client)
        subject_id = await _create_subject(client, token)
        topic_id = await _create_topic(client, token, subject_id)

        response = await client.post(
            f"/api/v1/topics/{topic_id}/notes",
            json={"title": "Note With Body", "body": "# Heading\n\nSome content"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["data"]["body"] == "# Heading\n\nSome content"

    async def test_create_note_with_tint_id(self, client):
        """Test creating a note with an explicit tint_id."""
        token = await _register_and_login(client)
        subject_id = await _create_subject(client, token)
        topic_id = await _create_topic(client, token, subject_id)

        tints_resp = await client.get("/api/v1/master/tint-palette")
        tints = tints_resp.json()["data"]
        if not tints:
            pytest.skip("No tints seeded in database")
        tint_id = tints[0]["id"]

        response = await client.post(
            f"/api/v1/topics/{topic_id}/notes",
            json={"title": "Tinted Note", "tint_id": tint_id},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 201
        assert response.json()["data"]["tint_id"] == tint_id

    async def test_create_note_assigns_random_tint(self, client):
        """Test that a tint is assigned automatically when not provided."""
        token = await _register_and_login(client)
        subject_id = await _create_subject(client, token)
        topic_id = await _create_topic(client, token, subject_id)

        response = await client.post(
            f"/api/v1/topics/{topic_id}/notes",
            json={"title": "Auto Tint Note"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 201
        assert response.json()["success"] is True

    async def test_create_note_no_auth_returns_401(self, client):
        """Test that creating a note without auth returns 401."""
        response = await client.post(
            f"/api/v1/topics/{uuid4()}/notes",
            json={"title": "Test"},
        )
        assert response.status_code == 401

    async def test_create_note_nonexistent_topic_returns_404(self, client):
        """Test that creating a note for a non-existent topic returns 404."""
        token = await _register_and_login(client)

        response = await client.post(
            f"/api/v1/topics/{uuid4()}/notes",
            json={"title": "Test Note"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404

    async def test_create_note_wrong_user_returns_403(self, client):
        """Test that creating a note in another user's topic returns 403."""
        token1 = await _register_and_login(client, "_a")
        token2 = await _register_and_login(client, "_b")

        subject_id = await _create_subject(client, token1)
        topic_id = await _create_topic(client, token1, subject_id)

        response = await client.post(
            f"/api/v1/topics/{topic_id}/notes",
            json={"title": "Hijacked Note"},
            headers={"Authorization": f"Bearer {token2}"},
        )

        assert response.status_code == 403
        assert response.json()["detail"]["error"] == "FORBIDDEN"

    async def test_create_note_empty_title_returns_422(self, client):
        """Test that empty title returns 422."""
        token = await _register_and_login(client)
        subject_id = await _create_subject(client, token)
        topic_id = await _create_topic(client, token, subject_id)

        response = await client.post(
            f"/api/v1/topics/{topic_id}/notes",
            json={"title": ""},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 422

    async def test_create_note_title_too_long_returns_422(self, client):
        """Test that title exceeding 255 chars returns 422."""
        token = await _register_and_login(client)
        subject_id = await _create_subject(client, token)
        topic_id = await _create_topic(client, token, subject_id)

        response = await client.post(
            f"/api/v1/topics/{topic_id}/notes",
            json={"title": "x" * 256},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 422

    async def test_create_note_invalid_tint_id_returns_400(self, client):
        """Test that a non-existent tint_id returns 400."""
        token = await _register_and_login(client)
        subject_id = await _create_subject(client, token)
        topic_id = await _create_topic(client, token, subject_id)

        response = await client.post(
            f"/api/v1/topics/{topic_id}/notes",
            json={"title": "Valid Title", "tint_id": str(uuid4())},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 400
        assert response.json()["detail"]["error"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
class TestListNotes:
    """Tests for GET /topics/{topicId}/notes."""

    async def test_list_notes_returns_success(self, client):
        """Test listing notes returns success response."""
        token = await _register_and_login(client)
        subject_id = await _create_subject(client, token)
        topic_id = await _create_topic(client, token, subject_id)

        response = await client.get(
            f"/api/v1/topics/{topic_id}/notes",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert "total" in data

    async def test_list_notes_returns_created_notes(self, client):
        """Test that created notes appear in the list."""
        token = await _register_and_login(client)
        subject_id = await _create_subject(client, token)
        topic_id = await _create_topic(client, token, subject_id)

        for title in ["Note A", "Note B"]:
            await client.post(
                f"/api/v1/topics/{topic_id}/notes",
                json={"title": title},
                headers={"Authorization": f"Bearer {token}"},
            )

        response = await client.get(
            f"/api/v1/topics/{topic_id}/notes",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        titles = [n["title"] for n in data["data"]]
        assert "Note A" in titles
        assert "Note B" in titles

    async def test_list_notes_pagination(self, client):
        """Test pagination parameters work correctly."""
        token = await _register_and_login(client)
        subject_id = await _create_subject(client, token)
        topic_id = await _create_topic(client, token, subject_id)

        for i in range(4):
            await client.post(
                f"/api/v1/topics/{topic_id}/notes",
                json={"title": f"Note {i}"},
                headers={"Authorization": f"Bearer {token}"},
            )

        response = await client.get(
            f"/api/v1/topics/{topic_id}/notes?limit=2&offset=0",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2
        assert data["total"] == 4

    async def test_list_notes_sorted_by_created_at_asc(self, client):
        """Test that notes are sorted by created_at ascending by default."""
        token = await _register_and_login(client)
        subject_id = await _create_subject(client, token)
        topic_id = await _create_topic(client, token, subject_id)

        for title in ["First", "Second", "Third"]:
            await client.post(
                f"/api/v1/topics/{topic_id}/notes",
                json={"title": title},
                headers={"Authorization": f"Bearer {token}"},
            )

        response = await client.get(
            f"/api/v1/topics/{topic_id}/notes",
            headers={"Authorization": f"Bearer {token}"},
        )

        data = response.json()
        created_ats = [n["created_at"] for n in data["data"]]
        assert created_ats == sorted(created_ats)

    async def test_list_notes_no_auth_returns_401(self, client):
        """Test that listing notes without auth returns 401."""
        response = await client.get(f"/api/v1/topics/{uuid4()}/notes")
        assert response.status_code == 401

    async def test_list_notes_wrong_user_returns_403(self, client):
        """Test that listing notes in another user's topic returns 403."""
        token1 = await _register_and_login(client, "_c")
        token2 = await _register_and_login(client, "_d")

        subject_id = await _create_subject(client, token1)
        topic_id = await _create_topic(client, token1, subject_id)

        response = await client.get(
            f"/api/v1/topics/{topic_id}/notes",
            headers={"Authorization": f"Bearer {token2}"},
        )

        assert response.status_code == 403
        assert response.json()["detail"]["error"] == "FORBIDDEN"

    async def test_list_notes_nonexistent_topic_returns_404(self, client):
        """Test that listing notes for a non-existent topic returns 404."""
        token = await _register_and_login(client)

        response = await client.get(
            f"/api/v1/topics/{uuid4()}/notes",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404


@pytest.mark.asyncio
class TestGetNote:
    """Tests for GET /notes/{id}."""

    async def test_get_note_success(self, client):
        """Test getting a note returns complete note data."""
        token = await _register_and_login(client)
        subject_id = await _create_subject(client, token)
        topic_id = await _create_topic(client, token, subject_id)

        create_resp = await client.post(
            f"/api/v1/topics/{topic_id}/notes",
            json={"title": "Fetch Me", "body": "Some content"},
            headers={"Authorization": f"Bearer {token}"},
        )
        note_id = create_resp.json()["data"]["id"]

        response = await client.get(
            f"/api/v1/notes/{note_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == note_id
        assert data["data"]["title"] == "Fetch Me"
        assert "scribbles" in data["data"]

    async def test_get_note_not_found_returns_404(self, client):
        """Test getting a non-existent note returns 404."""
        token = await _register_and_login(client)

        response = await client.get(
            f"/api/v1/notes/{uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404

    async def test_get_note_wrong_user_returns_403(self, client):
        """Test that getting another user's note returns 403."""
        token1 = await _register_and_login(client, "_e")
        token2 = await _register_and_login(client, "_f")

        subject_id = await _create_subject(client, token1)
        topic_id = await _create_topic(client, token1, subject_id)
        create_resp = await client.post(
            f"/api/v1/topics/{topic_id}/notes",
            json={"title": "Private Note"},
            headers={"Authorization": f"Bearer {token1}"},
        )
        note_id = create_resp.json()["data"]["id"]

        response = await client.get(
            f"/api/v1/notes/{note_id}",
            headers={"Authorization": f"Bearer {token2}"},
        )

        assert response.status_code == 403
        assert response.json()["detail"]["error"] == "FORBIDDEN"

    async def test_get_note_no_auth_returns_401(self, client):
        """Test that getting a note without auth returns 401."""
        response = await client.get(f"/api/v1/notes/{uuid4()}")
        assert response.status_code == 401


@pytest.mark.asyncio
class TestUpdateNote:
    """Tests for PATCH /notes/{id}."""

    async def test_update_note_title(self, client):
        """Test updating a note title."""
        token = await _register_and_login(client)
        subject_id = await _create_subject(client, token)
        topic_id = await _create_topic(client, token, subject_id)

        create_resp = await client.post(
            f"/api/v1/topics/{topic_id}/notes",
            json={"title": "Original Title"},
            headers={"Authorization": f"Bearer {token}"},
        )
        note_id = create_resp.json()["data"]["id"]

        response = await client.patch(
            f"/api/v1/notes/{note_id}",
            json={"title": "Updated Title"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["title"] == "Updated Title"

    async def test_update_note_scribbles(self, client):
        """Test updating a note with scribbles."""
        token = await _register_and_login(client)
        subject_id = await _create_subject(client, token)
        topic_id = await _create_topic(client, token, subject_id)

        create_resp = await client.post(
            f"/api/v1/topics/{topic_id}/notes",
            json={"title": "Scribble Note"},
            headers={"Authorization": f"Bearer {token}"},
        )
        note_id = create_resp.json()["data"]["id"]

        scribbles = [
            {
                "id": str(uuid4()),
                "tool": "brush",
                "color": "#FF0000",
                "width": 2.5,
                "opacity": 0.8,
                "points": [{"x": 10.0, "y": 20.0}, {"x": 30.0, "y": 40.0}],
            }
        ]

        response = await client.patch(
            f"/api/v1/notes/{note_id}",
            json={"scribbles": scribbles},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["scribbles"]) == 1
        assert data["data"]["scribbles"][0]["tool"] == "brush"

    async def test_update_note_invalid_scribble_color_returns_422(self, client):
        """Test that invalid scribble color returns 422."""
        token = await _register_and_login(client)
        subject_id = await _create_subject(client, token)
        topic_id = await _create_topic(client, token, subject_id)

        create_resp = await client.post(
            f"/api/v1/topics/{topic_id}/notes",
            json={"title": "Note"},
            headers={"Authorization": f"Bearer {token}"},
        )
        note_id = create_resp.json()["data"]["id"]

        response = await client.patch(
            f"/api/v1/notes/{note_id}",
            json={
                "scribbles": [
                    {
                        "id": str(uuid4()),
                        "tool": "brush",
                        "color": "not-a-color",
                        "width": 2.0,
                        "opacity": 0.5,
                        "points": [{"x": 1.0, "y": 2.0}],
                    }
                ]
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 422

    async def test_update_note_not_found_returns_404(self, client):
        """Test updating a non-existent note returns 404."""
        token = await _register_and_login(client)

        response = await client.patch(
            f"/api/v1/notes/{uuid4()}",
            json={"title": "New Title"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404

    async def test_update_note_wrong_user_returns_403(self, client):
        """Test that updating another user's note returns 403."""
        token1 = await _register_and_login(client, "_g")
        token2 = await _register_and_login(client, "_h")

        subject_id = await _create_subject(client, token1)
        topic_id = await _create_topic(client, token1, subject_id)
        create_resp = await client.post(
            f"/api/v1/topics/{topic_id}/notes",
            json={"title": "User1 Note"},
            headers={"Authorization": f"Bearer {token1}"},
        )
        note_id = create_resp.json()["data"]["id"]

        response = await client.patch(
            f"/api/v1/notes/{note_id}",
            json={"title": "Hijacked"},
            headers={"Authorization": f"Bearer {token2}"},
        )

        assert response.status_code == 403
        assert response.json()["detail"]["error"] == "FORBIDDEN"

    async def test_update_note_no_auth_returns_401(self, client):
        """Test that updating without auth returns 401."""
        response = await client.patch(
            f"/api/v1/notes/{uuid4()}",
            json={"title": "New Title"},
        )
        assert response.status_code == 401


@pytest.mark.asyncio
class TestDeleteNote:
    """Tests for DELETE /notes/{id}."""

    async def test_delete_note_success(self, client):
        """Test deleting a note returns 200 with success message."""
        token = await _register_and_login(client)
        subject_id = await _create_subject(client, token)
        topic_id = await _create_topic(client, token, subject_id)

        create_resp = await client.post(
            f"/api/v1/topics/{topic_id}/notes",
            json={"title": "To Delete"},
            headers={"Authorization": f"Bearer {token}"},
        )
        note_id = create_resp.json()["data"]["id"]

        response = await client.delete(
            f"/api/v1/notes/{note_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.json()["success"] is True

    async def test_delete_note_removes_from_list(self, client):
        """Test that deleted note no longer appears in list."""
        token = await _register_and_login(client)
        subject_id = await _create_subject(client, token)
        topic_id = await _create_topic(client, token, subject_id)

        create_resp = await client.post(
            f"/api/v1/topics/{topic_id}/notes",
            json={"title": "Will Be Deleted"},
            headers={"Authorization": f"Bearer {token}"},
        )
        note_id = create_resp.json()["data"]["id"]

        await client.delete(
            f"/api/v1/notes/{note_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        list_resp = await client.get(
            f"/api/v1/topics/{topic_id}/notes",
            headers={"Authorization": f"Bearer {token}"},
        )
        ids = [n["id"] for n in list_resp.json()["data"]]
        assert note_id not in ids

    async def test_delete_note_not_found_returns_404(self, client):
        """Test deleting a non-existent note returns 404."""
        token = await _register_and_login(client)

        response = await client.delete(
            f"/api/v1/notes/{uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404

    async def test_delete_note_wrong_user_returns_403(self, client):
        """Test that deleting another user's note returns 403."""
        token1 = await _register_and_login(client, "_i")
        token2 = await _register_and_login(client, "_j")

        subject_id = await _create_subject(client, token1)
        topic_id = await _create_topic(client, token1, subject_id)
        create_resp = await client.post(
            f"/api/v1/topics/{topic_id}/notes",
            json={"title": "User1 Note"},
            headers={"Authorization": f"Bearer {token1}"},
        )
        note_id = create_resp.json()["data"]["id"]

        response = await client.delete(
            f"/api/v1/notes/{note_id}",
            headers={"Authorization": f"Bearer {token2}"},
        )

        assert response.status_code == 403
        assert response.json()["detail"]["error"] == "FORBIDDEN"

    async def test_delete_note_no_auth_returns_401(self, client):
        """Test that deleting without auth returns 401."""
        response = await client.delete(f"/api/v1/notes/{uuid4()}")
        assert response.status_code == 401
