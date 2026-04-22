"""Tests for snippet endpoints (tasks 37, 38, 39)."""

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

    email = f"snip_{uuid4().hex[:8]}{suffix}@example.com"
    payload = {
        "name": "Snippet Test User",
        "email": email,
        "password": "securepass123",
        "avatar_style_id": styles[0]["id"],
        "avatar_color_id": colors[0]["id"],
    }
    resp = await client.post("/api/v1/auth/sign-up", json=payload)
    assert resp.status_code == 201
    return resp.json()["data"]["token"]


async def _create_subject(client: AsyncClient, token: str) -> str:
    resp = await client.post(
        "/api/v1/subjects",
        json={"name": f"Subject {uuid4().hex[:6]}"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    return resp.json()["data"]["id"]


async def _create_topic(client: AsyncClient, token: str, subject_id: str) -> str:
    resp = await client.post(
        f"/api/v1/subjects/{subject_id}/topics",
        json={"name": f"Topic {uuid4().hex[:6]}"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    return resp.json()["data"]["id"]


async def _create_note(client: AsyncClient, token: str, topic_id: str) -> str:
    resp = await client.post(
        f"/api/v1/topics/{topic_id}/notes",
        json={"title": f"Note {uuid4().hex[:6]}"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    return resp.json()["data"]["id"]


@pytest.mark.asyncio
class TestCreateSnippet:
    """Tests for POST /snippets."""

    async def test_create_snippet_success(self, client):
        """Test creating a snippet returns 201 with snippet data."""
        token = await _register_and_login(client)

        response = await client.post(
            "/api/v1/snippets",
            json={"language": "python", "code": "print('hello')"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["language"] == "python"
        assert data["data"]["code"] == "print('hello')"
        assert data["data"]["output"] == ""
        assert data["data"]["note_id"] is None
        assert "id" in data["data"]
        assert "user_id" in data["data"]
        assert "created_at" in data["data"]
        assert "updated_at" in data["data"]

    async def test_create_snippet_with_note_id(self, client):
        """Test creating a snippet linked to a note."""
        token = await _register_and_login(client)
        subject_id = await _create_subject(client, token)
        topic_id = await _create_topic(client, token, subject_id)
        note_id = await _create_note(client, token, topic_id)

        response = await client.post(
            "/api/v1/snippets",
            json={"language": "javascript", "code": "console.log('hi')", "note_id": note_id},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["data"]["note_id"] == note_id

    async def test_create_snippet_no_auth_returns_401(self, client):
        """Test that creating a snippet without auth returns 401."""
        response = await client.post(
            "/api/v1/snippets",
            json={"language": "python", "code": "print('hello')"},
        )
        assert response.status_code == 401

    async def test_create_snippet_empty_language_returns_422(self, client):
        """Test that empty language returns 422."""
        token = await _register_and_login(client)

        response = await client.post(
            "/api/v1/snippets",
            json={"language": "   ", "code": "print('hello')"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_create_snippet_empty_code_returns_422(self, client):
        """Test that empty code returns 422."""
        token = await _register_and_login(client)

        response = await client.post(
            "/api/v1/snippets",
            json={"language": "python", "code": "   "},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422

    async def test_create_snippet_nonexistent_note_returns_404(self, client):
        """Test that a non-existent note_id returns 404."""
        token = await _register_and_login(client)

        response = await client.post(
            "/api/v1/snippets",
            json={"language": "python", "code": "print('hi')", "note_id": str(uuid4())},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    async def test_create_snippet_other_users_note_returns_403(self, client):
        """Test that using another user's note_id returns 403."""
        token1 = await _register_and_login(client, "_a")
        token2 = await _register_and_login(client, "_b")

        subject_id = await _create_subject(client, token1)
        topic_id = await _create_topic(client, token1, subject_id)
        note_id = await _create_note(client, token1, topic_id)

        response = await client.post(
            "/api/v1/snippets",
            json={"language": "python", "code": "print('hi')", "note_id": note_id},
            headers={"Authorization": f"Bearer {token2}"},
        )
        assert response.status_code == 403
        assert response.json()["detail"]["error"] == "FORBIDDEN"


@pytest.mark.asyncio
class TestListSnippets:
    """Tests for GET /snippets."""

    async def test_list_snippets_returns_success(self, client):
        """Test listing snippets returns success response."""
        token = await _register_and_login(client)

        response = await client.get(
            "/api/v1/snippets",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert "total" in data

    async def test_list_snippets_returns_own_snippets(self, client):
        """Test that only the user's own snippets are returned."""
        token = await _register_and_login(client)

        for lang in ["python", "javascript"]:
            await client.post(
                "/api/v1/snippets",
                json={"language": lang, "code": f"// {lang}"},
                headers={"Authorization": f"Bearer {token}"},
            )

        response = await client.get(
            "/api/v1/snippets",
            headers={"Authorization": f"Bearer {token}"},
        )

        data = response.json()
        assert data["total"] >= 2
        langs = [s["language"] for s in data["data"]]
        assert "python" in langs
        assert "javascript" in langs

    async def test_list_snippets_sorted_by_created_at_desc(self, client):
        """Test that snippets are sorted by created_at descending."""
        token = await _register_and_login(client)

        for i in range(3):
            await client.post(
                "/api/v1/snippets",
                json={"language": "python", "code": f"# snippet {i}"},
                headers={"Authorization": f"Bearer {token}"},
            )

        response = await client.get(
            "/api/v1/snippets",
            headers={"Authorization": f"Bearer {token}"},
        )

        data = response.json()
        created_ats = [s["created_at"] for s in data["data"]]
        assert created_ats == sorted(created_ats, reverse=True)

    async def test_list_snippets_pagination(self, client):
        """Test pagination parameters work correctly."""
        token = await _register_and_login(client)

        for i in range(4):
            await client.post(
                "/api/v1/snippets",
                json={"language": "go", "code": f"// go {i}"},
                headers={"Authorization": f"Bearer {token}"},
            )

        response = await client.get(
            "/api/v1/snippets?limit=2&offset=0",
            headers={"Authorization": f"Bearer {token}"},
        )

        data = response.json()
        assert len(data["data"]) == 2
        assert data["total"] >= 4

    async def test_list_snippets_language_filter(self, client):
        """Test filtering snippets by language."""
        token = await _register_and_login(client)

        await client.post(
            "/api/v1/snippets",
            json={"language": "rust", "code": "fn main() {}"},
            headers={"Authorization": f"Bearer {token}"},
        )
        await client.post(
            "/api/v1/snippets",
            json={"language": "typescript", "code": "const x: number = 1"},
            headers={"Authorization": f"Bearer {token}"},
        )

        response = await client.get(
            "/api/v1/snippets?language=rust",
            headers={"Authorization": f"Bearer {token}"},
        )

        data = response.json()
        assert all(s["language"] == "rust" for s in data["data"])

    async def test_list_snippets_no_auth_returns_401(self, client):
        """Test that listing snippets without auth returns 401."""
        response = await client.get("/api/v1/snippets")
        assert response.status_code == 401

    async def test_list_snippets_does_not_return_other_users(self, client):
        """Test that snippets from other users are not returned."""
        token1 = await _register_and_login(client, "_c")
        token2 = await _register_and_login(client, "_d")

        await client.post(
            "/api/v1/snippets",
            json={"language": "python", "code": "# user1 snippet"},
            headers={"Authorization": f"Bearer {token1}"},
        )

        response = await client.get(
            "/api/v1/snippets",
            headers={"Authorization": f"Bearer {token2}"},
        )

        data = response.json()
        # user2 should have 0 snippets (they haven't created any)
        assert data["total"] == 0


@pytest.mark.asyncio
class TestUpdateSnippet:
    """Tests for PATCH /snippets/{id}."""

    async def test_update_snippet_code(self, client):
        """Test updating snippet code."""
        token = await _register_and_login(client)

        create_resp = await client.post(
            "/api/v1/snippets",
            json={"language": "python", "code": "print('old')"},
            headers={"Authorization": f"Bearer {token}"},
        )
        snippet_id = create_resp.json()["data"]["id"]

        response = await client.patch(
            f"/api/v1/snippets/{snippet_id}",
            json={"code": "print('new')"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["code"] == "print('new')"

    async def test_update_snippet_output(self, client):
        """Test updating snippet output."""
        token = await _register_and_login(client)

        create_resp = await client.post(
            "/api/v1/snippets",
            json={"language": "python", "code": "print('hello')"},
            headers={"Authorization": f"Bearer {token}"},
        )
        snippet_id = create_resp.json()["data"]["id"]

        response = await client.patch(
            f"/api/v1/snippets/{snippet_id}",
            json={"output": "hello\n"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.json()["data"]["output"] == "hello\n"

    async def test_update_snippet_not_found_returns_404(self, client):
        """Test updating a non-existent snippet returns 404."""
        token = await _register_and_login(client)

        response = await client.patch(
            f"/api/v1/snippets/{uuid4()}",
            json={"code": "print('hi')"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    async def test_update_snippet_wrong_user_returns_403(self, client):
        """Test that updating another user's snippet returns 403."""
        token1 = await _register_and_login(client, "_e")
        token2 = await _register_and_login(client, "_f")

        create_resp = await client.post(
            "/api/v1/snippets",
            json={"language": "python", "code": "# user1"},
            headers={"Authorization": f"Bearer {token1}"},
        )
        snippet_id = create_resp.json()["data"]["id"]

        response = await client.patch(
            f"/api/v1/snippets/{snippet_id}",
            json={"code": "# hijacked"},
            headers={"Authorization": f"Bearer {token2}"},
        )

        assert response.status_code == 403
        assert response.json()["detail"]["error"] == "FORBIDDEN"

    async def test_update_snippet_no_auth_returns_401(self, client):
        """Test that updating without auth returns 401."""
        response = await client.patch(
            f"/api/v1/snippets/{uuid4()}",
            json={"code": "print('hi')"},
        )
        assert response.status_code == 401


@pytest.mark.asyncio
class TestDeleteSnippet:
    """Tests for DELETE /snippets/{id}."""

    async def test_delete_snippet_success(self, client):
        """Test deleting a snippet returns 200 with success message."""
        token = await _register_and_login(client)

        create_resp = await client.post(
            "/api/v1/snippets",
            json={"language": "python", "code": "# to delete"},
            headers={"Authorization": f"Bearer {token}"},
        )
        snippet_id = create_resp.json()["data"]["id"]

        response = await client.delete(
            f"/api/v1/snippets/{snippet_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.json()["success"] is True

    async def test_delete_snippet_removes_from_list(self, client):
        """Test that deleted snippet no longer appears in list."""
        token = await _register_and_login(client)

        create_resp = await client.post(
            "/api/v1/snippets",
            json={"language": "python", "code": "# will be deleted"},
            headers={"Authorization": f"Bearer {token}"},
        )
        snippet_id = create_resp.json()["data"]["id"]

        await client.delete(
            f"/api/v1/snippets/{snippet_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        list_resp = await client.get(
            "/api/v1/snippets",
            headers={"Authorization": f"Bearer {token}"},
        )
        ids = [s["id"] for s in list_resp.json()["data"]]
        assert snippet_id not in ids

    async def test_delete_snippet_not_found_returns_404(self, client):
        """Test deleting a non-existent snippet returns 404."""
        token = await _register_and_login(client)

        response = await client.delete(
            f"/api/v1/snippets/{uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404

    async def test_delete_snippet_wrong_user_returns_403(self, client):
        """Test that deleting another user's snippet returns 403."""
        token1 = await _register_and_login(client, "_g")
        token2 = await _register_and_login(client, "_h")

        create_resp = await client.post(
            "/api/v1/snippets",
            json={"language": "python", "code": "# user1"},
            headers={"Authorization": f"Bearer {token1}"},
        )
        snippet_id = create_resp.json()["data"]["id"]

        response = await client.delete(
            f"/api/v1/snippets/{snippet_id}",
            headers={"Authorization": f"Bearer {token2}"},
        )

        assert response.status_code == 403
        assert response.json()["detail"]["error"] == "FORBIDDEN"

    async def test_delete_snippet_no_auth_returns_401(self, client):
        """Test that deleting without auth returns 401."""
        response = await client.delete(f"/api/v1/snippets/{uuid4()}")
        assert response.status_code == 401
