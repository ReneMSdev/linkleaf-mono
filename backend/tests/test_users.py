"""Tests for GET /v1/users/me and PATCH /v1/users/me."""

from __future__ import annotations

from httpx import AsyncClient

from tests.conftest import TEST_USER_ID


class TestGetMe:
    """GET /v1/users/me"""

    async def test_get_me_returns_user(
        self,
        client: AsyncClient,
        seed_free_user,
    ) -> None:
        response = await client.get("/v1/users/me")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(TEST_USER_ID)
        assert data["email"] == "test@linkleaf.co"
        assert data["is_active"] is True

    async def test_get_me_no_password_in_response(
        self,
        client: AsyncClient,
        seed_free_user,
    ) -> None:
        response = await client.get("/v1/users/me")
        assert response.status_code == 200
        data = response.json()
        assert "password" not in data
        assert "firebase_uid" not in data

    async def test_get_me_has_required_fields(
        self,
        client: AsyncClient,
        seed_free_user,
    ) -> None:
        response = await client.get("/v1/users/me")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "email" in data
        assert "display_name" in data
        assert "is_active" in data
        assert "created_at" in data
        assert "updated_at" in data


class TestPatchMe:
    """PATCH /v1/users/me"""

    async def test_update_display_name(
        self,
        client: AsyncClient,
        seed_free_user,
    ) -> None:
        response = await client.patch(
            "/v1/users/me",
            json={"display_name": "Updated Name"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["display_name"] == "Updated Name"

    async def test_partial_update_only_changes_provided_fields(
        self,
        client: AsyncClient,
        seed_free_user,
    ) -> None:
        # First get current state
        original = (await client.get("/v1/users/me")).json()

        # Update only display_name
        response = await client.patch(
            "/v1/users/me",
            json={"display_name": "Partial Update"},
        )
        assert response.status_code == 200
        data = response.json()

        # display_name changed
        assert data["display_name"] == "Partial Update"
        # email unchanged
        assert data["email"] == original["email"]
        # id unchanged
        assert data["id"] == original["id"]

    async def test_update_with_empty_body_returns_200(
        self,
        client: AsyncClient,
        seed_free_user,
    ) -> None:
        response = await client.patch("/v1/users/me", json={})
        assert response.status_code == 200

    async def test_update_returns_user_response_shape(
        self,
        client: AsyncClient,
        seed_free_user,
    ) -> None:
        response = await client.patch(
            "/v1/users/me",
            json={"display_name": "Shape Test"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "email" in data
        assert "display_name" in data
        assert "created_at" in data
        assert "updated_at" in data
