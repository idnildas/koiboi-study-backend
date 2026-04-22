"""Tests for material management endpoints (tasks 33, 34, 35, 36)."""

import io
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

    email = f"mat_{uuid4().hex[:8]}{suffix}@example.com"
    payload = {
        "name": "Material Test User",
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


def _make_pdf_file(content: bytes = b"%PDF-1.4 fake pdf content") -> tuple:
    """Return (filename, file_obj, content_type) for a fake PDF upload."""
    return ("test.pdf", io.BytesIO(content), "application/pdf")


@pytest.mark.asyncio
class TestUploadMaterial:
    """Tests for POST /subjects/{subjectId}/materials."""

    async def test_upload_material_success(self, client):
        """Test uploading a PDF returns 201 with material data."""
        token = await _register_and_login(client)
        subject_id = await _create_subject(client, token)

        response = await client.post(
            f"/api/v1/subjects/{subject_id}/materials",
            data={"title": "My PDF"},
            files={"file": _make_pdf_file()},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["title"] == "My PDF"
        assert data["data"]["subject_id"] == subject_id
        assert data["data"]["mime_type"] == "application/pdf"
        assert data["data"]["file_name"] == "test.pdf"
        assert "storage_key" in data["data"]
        assert "id" in data["data"]
        assert "created_at" in data["data"]

    async def test_upload_material_no_auth_returns_401(self, client):
        """Test that uploading without auth returns 401."""
        response = await client.post(
            f"/api/v1/subjects/{uuid4()}/materials",
            data={"title": "Test"},
            files={"file": _make_pdf_file()},
        )
        assert response.status_code == 401

    async def test_upload_material_nonexistent_subject_returns_404(self, client):
        """Test that uploading to a non-existent subject returns 404."""
        token = await _register_and_login(client)

        response = await client.post(
            f"/api/v1/subjects/{uuid4()}/materials",
            data={"title": "Test"},
            files={"file": _make_pdf_file()},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404

    async def test_upload_material_wrong_user_returns_403(self, client):
        """Test that uploading to another user's subject returns 403."""
        token1 = await _register_and_login(client, "_a")
        token2 = await _register_and_login(client, "_b")

        subject_id = await _create_subject(client, token1)

        response = await client.post(
            f"/api/v1/subjects/{subject_id}/materials",
            data={"title": "Hijack"},
            files={"file": _make_pdf_file()},
            headers={"Authorization": f"Bearer {token2}"},
        )

        assert response.status_code == 403
        assert response.json()["detail"]["error"] == "FORBIDDEN"

    async def test_upload_material_non_pdf_returns_400(self, client):
        """Test that uploading a non-PDF file returns 400."""
        token = await _register_and_login(client)
        subject_id = await _create_subject(client, token)

        response = await client.post(
            f"/api/v1/subjects/{subject_id}/materials",
            data={"title": "Not a PDF"},
            files={"file": ("test.txt", io.BytesIO(b"plain text"), "text/plain")},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 400
        assert response.json()["detail"]["error"] == "VALIDATION_ERROR"

    async def test_upload_material_file_too_large_returns_413(self, client):
        """Test that uploading a file > 100 MB returns 413."""
        token = await _register_and_login(client)
        subject_id = await _create_subject(client, token)

        # Create a fake file slightly over 100 MB
        large_content = b"x" * (100 * 1024 * 1024 + 1)

        response = await client.post(
            f"/api/v1/subjects/{subject_id}/materials",
            data={"title": "Too Big"},
            files={"file": ("big.pdf", io.BytesIO(large_content), "application/pdf")},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 413

    async def test_upload_material_empty_title_returns_422(self, client):
        """Test that empty title returns 422."""
        token = await _register_and_login(client)
        subject_id = await _create_subject(client, token)

        response = await client.post(
            f"/api/v1/subjects/{subject_id}/materials",
            data={"title": "   "},
            files={"file": _make_pdf_file()},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 422

    async def test_upload_material_storage_key_format(self, client):
        """Test that storage_key follows the expected format."""
        token = await _register_and_login(client)
        subject_id = await _create_subject(client, token)

        response = await client.post(
            f"/api/v1/subjects/{subject_id}/materials",
            data={"title": "Key Format Test"},
            files={"file": _make_pdf_file()},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 201
        storage_key = response.json()["data"]["storage_key"]
        assert storage_key.startswith("materials/")
        assert "test.pdf" in storage_key


@pytest.mark.asyncio
class TestListMaterials:
    """Tests for GET /subjects/{subjectId}/materials."""

    async def test_list_materials_empty(self, client):
        """Test listing materials for a subject with no materials."""
        token = await _register_and_login(client)
        subject_id = await _create_subject(client, token)

        response = await client.get(
            f"/api/v1/subjects/{subject_id}/materials",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] == []
        assert data["total"] == 0

    async def test_list_materials_returns_uploaded(self, client):
        """Test that uploaded materials appear in the list."""
        token = await _register_and_login(client)
        subject_id = await _create_subject(client, token)

        for title in ["PDF One", "PDF Two"]:
            await client.post(
                f"/api/v1/subjects/{subject_id}/materials",
                data={"title": title},
                files={"file": _make_pdf_file()},
                headers={"Authorization": f"Bearer {token}"},
            )

        response = await client.get(
            f"/api/v1/subjects/{subject_id}/materials",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        titles = [m["title"] for m in data["data"]]
        assert "PDF One" in titles
        assert "PDF Two" in titles

    async def test_list_materials_pagination(self, client):
        """Test pagination parameters work correctly."""
        token = await _register_and_login(client)
        subject_id = await _create_subject(client, token)

        for i in range(3):
            await client.post(
                f"/api/v1/subjects/{subject_id}/materials",
                data={"title": f"PDF {i}"},
                files={"file": _make_pdf_file()},
                headers={"Authorization": f"Bearer {token}"},
            )

        response = await client.get(
            f"/api/v1/subjects/{subject_id}/materials?limit=2&offset=0",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2
        assert data["total"] == 3

    async def test_list_materials_no_auth_returns_401(self, client):
        """Test that listing without auth returns 401."""
        response = await client.get(f"/api/v1/subjects/{uuid4()}/materials")
        assert response.status_code == 401

    async def test_list_materials_wrong_user_returns_403(self, client):
        """Test that listing another user's materials returns 403."""
        token1 = await _register_and_login(client, "_c")
        token2 = await _register_and_login(client, "_d")

        subject_id = await _create_subject(client, token1)

        response = await client.get(
            f"/api/v1/subjects/{subject_id}/materials",
            headers={"Authorization": f"Bearer {token2}"},
        )

        assert response.status_code == 403
        assert response.json()["detail"]["error"] == "FORBIDDEN"

    async def test_list_materials_nonexistent_subject_returns_404(self, client):
        """Test that listing for a non-existent subject returns 404."""
        token = await _register_and_login(client)

        response = await client.get(
            f"/api/v1/subjects/{uuid4()}/materials",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404


@pytest.mark.asyncio
class TestUpdateMaterial:
    """Tests for PATCH /materials/{id}."""

    async def test_update_material_title(self, client):
        """Test updating a material title."""
        token = await _register_and_login(client)
        subject_id = await _create_subject(client, token)

        upload_resp = await client.post(
            f"/api/v1/subjects/{subject_id}/materials",
            data={"title": "Original Title"},
            files={"file": _make_pdf_file()},
            headers={"Authorization": f"Bearer {token}"},
        )
        material_id = upload_resp.json()["data"]["id"]

        response = await client.patch(
            f"/api/v1/materials/{material_id}",
            json={"title": "Updated Title"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["title"] == "Updated Title"

    async def test_update_material_page_count(self, client):
        """Test updating a material page count."""
        token = await _register_and_login(client)
        subject_id = await _create_subject(client, token)

        upload_resp = await client.post(
            f"/api/v1/subjects/{subject_id}/materials",
            data={"title": "Page Count Test"},
            files={"file": _make_pdf_file()},
            headers={"Authorization": f"Bearer {token}"},
        )
        material_id = upload_resp.json()["data"]["id"]

        response = await client.patch(
            f"/api/v1/materials/{material_id}",
            json={"page_count": 42},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.json()["data"]["page_count"] == 42

    async def test_update_material_invalid_page_count_returns_422(self, client):
        """Test that page_count of 0 returns 422."""
        token = await _register_and_login(client)
        subject_id = await _create_subject(client, token)

        upload_resp = await client.post(
            f"/api/v1/subjects/{subject_id}/materials",
            data={"title": "Test"},
            files={"file": _make_pdf_file()},
            headers={"Authorization": f"Bearer {token}"},
        )
        material_id = upload_resp.json()["data"]["id"]

        response = await client.patch(
            f"/api/v1/materials/{material_id}",
            json={"page_count": 0},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 422

    async def test_update_material_not_found_returns_404(self, client):
        """Test updating a non-existent material returns 404."""
        token = await _register_and_login(client)

        response = await client.patch(
            f"/api/v1/materials/{uuid4()}",
            json={"title": "New Title"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404

    async def test_update_material_wrong_user_returns_403(self, client):
        """Test that updating another user's material returns 403."""
        token1 = await _register_and_login(client, "_e")
        token2 = await _register_and_login(client, "_f")

        subject_id = await _create_subject(client, token1)
        upload_resp = await client.post(
            f"/api/v1/subjects/{subject_id}/materials",
            data={"title": "User1 Material"},
            files={"file": _make_pdf_file()},
            headers={"Authorization": f"Bearer {token1}"},
        )
        material_id = upload_resp.json()["data"]["id"]

        response = await client.patch(
            f"/api/v1/materials/{material_id}",
            json={"title": "Hijacked"},
            headers={"Authorization": f"Bearer {token2}"},
        )

        assert response.status_code == 403
        assert response.json()["detail"]["error"] == "FORBIDDEN"

    async def test_update_material_no_auth_returns_401(self, client):
        """Test that updating without auth returns 401."""
        response = await client.patch(
            f"/api/v1/materials/{uuid4()}",
            json={"title": "New Title"},
        )
        assert response.status_code == 401


@pytest.mark.asyncio
class TestDownloadMaterial:
    """Tests for GET /materials/{id}/download."""

    async def test_download_material_success(self, client):
        """Test downloading a material returns the file with correct headers."""
        token = await _register_and_login(client)
        subject_id = await _create_subject(client, token)

        pdf_content = b"%PDF-1.4 test content"
        upload_resp = await client.post(
            f"/api/v1/subjects/{subject_id}/materials",
            data={"title": "Download Test"},
            files={"file": ("download.pdf", io.BytesIO(pdf_content), "application/pdf")},
            headers={"Authorization": f"Bearer {token}"},
        )
        material_id = upload_resp.json()["data"]["id"]

        response = await client.get(
            f"/api/v1/materials/{material_id}/download",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.content == pdf_content
        assert response.headers["content-type"] == "application/pdf"
        assert "attachment" in response.headers["content-disposition"]
        assert "download.pdf" in response.headers["content-disposition"]

    async def test_download_material_no_auth_returns_401(self, client):
        """Test that downloading without auth returns 401."""
        response = await client.get(f"/api/v1/materials/{uuid4()}/download")
        assert response.status_code == 401

    async def test_download_material_not_found_returns_404(self, client):
        """Test downloading a non-existent material returns 404."""
        token = await _register_and_login(client)

        response = await client.get(
            f"/api/v1/materials/{uuid4()}/download",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404

    async def test_download_material_wrong_user_returns_403(self, client):
        """Test that downloading another user's material returns 403."""
        token1 = await _register_and_login(client, "_g")
        token2 = await _register_and_login(client, "_h")

        subject_id = await _create_subject(client, token1)
        upload_resp = await client.post(
            f"/api/v1/subjects/{subject_id}/materials",
            data={"title": "Private PDF"},
            files={"file": _make_pdf_file()},
            headers={"Authorization": f"Bearer {token1}"},
        )
        material_id = upload_resp.json()["data"]["id"]

        response = await client.get(
            f"/api/v1/materials/{material_id}/download",
            headers={"Authorization": f"Bearer {token2}"},
        )

        assert response.status_code == 403
        assert response.json()["detail"]["error"] == "FORBIDDEN"


@pytest.mark.asyncio
class TestDeleteMaterial:
    """Tests for DELETE /materials/{id}."""

    async def test_delete_material_success(self, client):
        """Test deleting a material returns 200 with success message."""
        token = await _register_and_login(client)
        subject_id = await _create_subject(client, token)

        upload_resp = await client.post(
            f"/api/v1/subjects/{subject_id}/materials",
            data={"title": "To Delete"},
            files={"file": _make_pdf_file()},
            headers={"Authorization": f"Bearer {token}"},
        )
        material_id = upload_resp.json()["data"]["id"]

        response = await client.delete(
            f"/api/v1/materials/{material_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.json()["success"] is True

    async def test_delete_material_removes_from_list(self, client):
        """Test that deleted material no longer appears in list."""
        token = await _register_and_login(client)
        subject_id = await _create_subject(client, token)

        upload_resp = await client.post(
            f"/api/v1/subjects/{subject_id}/materials",
            data={"title": "Will Be Deleted"},
            files={"file": _make_pdf_file()},
            headers={"Authorization": f"Bearer {token}"},
        )
        material_id = upload_resp.json()["data"]["id"]

        await client.delete(
            f"/api/v1/materials/{material_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        list_resp = await client.get(
            f"/api/v1/subjects/{subject_id}/materials",
            headers={"Authorization": f"Bearer {token}"},
        )
        ids = [m["id"] for m in list_resp.json()["data"]]
        assert material_id not in ids

    async def test_delete_material_not_found_returns_404(self, client):
        """Test deleting a non-existent material returns 404."""
        token = await _register_and_login(client)

        response = await client.delete(
            f"/api/v1/materials/{uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 404

    async def test_delete_material_wrong_user_returns_403(self, client):
        """Test that deleting another user's material returns 403."""
        token1 = await _register_and_login(client, "_i")
        token2 = await _register_and_login(client, "_j")

        subject_id = await _create_subject(client, token1)
        upload_resp = await client.post(
            f"/api/v1/subjects/{subject_id}/materials",
            data={"title": "User1 Material"},
            files={"file": _make_pdf_file()},
            headers={"Authorization": f"Bearer {token1}"},
        )
        material_id = upload_resp.json()["data"]["id"]

        response = await client.delete(
            f"/api/v1/materials/{material_id}",
            headers={"Authorization": f"Bearer {token2}"},
        )

        assert response.status_code == 403
        assert response.json()["detail"]["error"] == "FORBIDDEN"

    async def test_delete_material_no_auth_returns_401(self, client):
        """Test that deleting without auth returns 401."""
        response = await client.delete(f"/api/v1/materials/{uuid4()}")
        assert response.status_code == 401
