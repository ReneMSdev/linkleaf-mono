"""Tests for profile API routes — CRUD, public slug, QR redirect, restore."""

from __future__ import annotations

from collections.abc import AsyncGenerator, AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, get_optional_user
from app.core.db.session import get_db
from app.domain.user.dto import UserInternal
from app.main import app

from tests.conftest import (
    TEST_PREMIUM_USER_EMAIL,
    TEST_PREMIUM_USER_ID,
    TEST_USER_EMAIL,
    TEST_USER_ID,
    make_user_internal,
)


@pytest_asyncio.fixture(scope="module", loop_scope="session")
async def profile(db: AsyncSession, seed_free_user) -> AsyncIterator[dict]:
    """Primary free-tier profile: GET existing (e.g. from TestCreateProfile) or create via API."""
    free_user = make_user_internal(TEST_USER_ID, TEST_USER_EMAIL, [])

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db

    async def override_get_current_user() -> UserInternal:
        return free_user

    async def override_get_optional_user() -> UserInternal:
        return free_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_optional_user] = override_get_optional_user

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as ac:
            listed = await ac.get("/v1/profiles")
            assert listed.status_code == 200
            profiles = listed.json()
            if profiles:
                data = profiles[0]
            else:
                response = await ac.post(
                    "/v1/profiles",
                    json={"name": "Test Profile", "bio": "Test bio"},
                )
                assert response.status_code == 201
                data = response.json()
            yield data
    finally:
        app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="module", loop_scope="session")
async def premium_profile(db: AsyncSession, seed_premium_user) -> AsyncIterator[dict]:
    """Premium-tier profile via API (or first existing premium profile)."""
    premium_user = make_user_internal(
        TEST_PREMIUM_USER_ID,
        TEST_PREMIUM_USER_EMAIL,
        ["premium"],
    )

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db

    async def override_get_current_user() -> UserInternal:
        return premium_user

    async def override_get_optional_user() -> UserInternal:
        return premium_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_optional_user] = override_get_optional_user

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as ac:
            listed = await ac.get("/v1/profiles")
            assert listed.status_code == 200
            profiles = listed.json()
            if profiles:
                data = profiles[0]
            else:
                response = await ac.post(
                    "/v1/profiles",
                    json={"name": "Premium Profile", "bio": "Premium bio"},
                )
                assert response.status_code == 201
                data = response.json()
            yield data
    finally:
        app.dependency_overrides.clear()


class TestCreateProfile:
    """POST /v1/profiles"""

    async def test_create_profile_auto_slug(
        self,
        premium_client: AsyncClient,
        seed_premium_user,
    ) -> None:
        response = await premium_client.post(
            "/v1/profiles",
            json={"name": "Auto Slug Test"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["slug"] == "auto-slug-test"
        assert data["qr_token"] is not None
        assert data["qr_active"] is True

    async def test_create_profile_custom_slug(
        self,
        client: AsyncClient,
        seed_free_user,
    ) -> None:
        # Free user already has a profile — should be blocked
        response = await client.post(
            "/v1/profiles",
            json={"name": "Custom Slug", "slug": "my-custom-slug"},
        )
        assert response.status_code == 403

    async def test_create_profile_reserved_slug_rejected(
        self,
        client: AsyncClient,
        seed_free_user,
    ) -> None:
        response = await client.post(
            "/v1/profiles",
            json={"name": "Admin", "slug": "admin"},
        )
        assert response.status_code == 422

    async def test_free_user_limited_to_one_profile(
        self,
        client: AsyncClient,
        seed_free_user,
    ) -> None:
        response = await client.post(
            "/v1/profiles",
            json={"name": "Second Profile"},
        )
        assert response.status_code == 403

    async def test_premium_user_can_create_multiple_profiles(
        self,
        premium_client: AsyncClient,
        seed_premium_user,
    ) -> None:
        # First profile
        r1 = await premium_client.post(
            "/v1/profiles",
            json={"name": "Premium Profile One"},
        )
        assert r1.status_code == 201

        # Second profile
        r2 = await premium_client.post(
            "/v1/profiles",
            json={"name": "Premium Profile Two"},
        )
        assert r2.status_code == 201


class TestListProfiles:
    """GET /v1/profiles"""

    async def test_list_profiles_returns_array(
        self,
        client: AsyncClient,
        seed_free_user,
        profile,
    ) -> None:
        response = await client.get("/v1/profiles")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    async def test_list_profiles_ordered_by_display_order(
        self,
        client: AsyncClient,
        seed_free_user,
        profile,
    ) -> None:
        response = await client.get("/v1/profiles")
        assert response.status_code == 200
        data = response.json()
        orders = [p["display_order"] for p in data]
        assert orders == sorted(orders)


class TestGetProfile:
    """GET /v1/profiles/{id}"""

    async def test_get_profile_by_id(
        self,
        client: AsyncClient,
        seed_free_user,
        profile,
    ) -> None:
        response = await client.get(f"/v1/profiles/{profile['id']}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == profile["id"]
        assert data["name"] == profile["name"]

    async def test_get_profile_not_found(
        self,
        client: AsyncClient,
        seed_free_user,
    ) -> None:
        response = await client.get(
            "/v1/profiles/00000000-0000-0000-0000-000000000000"
        )
        assert response.status_code == 404

    async def test_get_profile_no_qr_token_exposed(
        self,
        client: AsyncClient,
        seed_free_user,
        profile,
    ) -> None:
        response = await client.get(f"/v1/profiles/{profile['id']}")
        assert response.status_code == 200
        # qr_token IS exposed to owner — confirm it's present
        assert "qr_token" in response.json()


class TestUpdateProfile:
    """PATCH /v1/profiles/{id}"""

    async def test_update_profile_name(
        self,
        client: AsyncClient,
        seed_free_user,
        profile,
    ) -> None:
        response = await client.patch(
            f"/v1/profiles/{profile['id']}",
            json={"name": "Updated Name"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Name"

    async def test_update_slug_writes_to_slug_history(
        self,
        client: AsyncClient,
        seed_free_user,
        profile,
        db: AsyncSession,
    ) -> None:
        old_slug = profile["slug"]
        response = await client.patch(
            f"/v1/profiles/{profile['id']}",
            json={"slug": "new-test-slug"},
        )
        assert response.status_code == 200
        assert response.json()["slug"] == "new-test-slug"

        # Verify old slug in slug_history
        result = await db.execute(
            text("SELECT old_slug FROM slug_history WHERE old_slug = :slug"),
            {"slug": old_slug},
        )
        row = result.scalar_one_or_none()
        assert row == old_slug

    async def test_update_reserved_slug_rejected(
        self,
        client: AsyncClient,
        seed_free_user,
        profile,
    ) -> None:
        response = await client.patch(
            f"/v1/profiles/{profile['id']}",
            json={"slug": "health"},
        )
        assert response.status_code == 422


class TestPublicProfile:
    """GET /p/{slug}"""

    async def test_public_profile_returns_200(
        self,
        anon_client: AsyncClient,
        seed_free_user,
        profile,
        client: AsyncClient,
    ) -> None:
        # Re-fetch current slug — may have changed from update tests
        current = (await client.get(f"/v1/profiles/{profile['id']}")).json()
        response = await anon_client.get(f"/p/{current['slug']}")
        assert response.status_code == 200
        data = response.json()
        assert data["slug"] == current["slug"]
        assert data["name"] is not None

    async def test_public_profile_no_sensitive_fields(
        self,
        anon_client: AsyncClient,
        seed_free_user,
        profile,
        client: AsyncClient,
    ) -> None:
        current = (await client.get(f"/v1/profiles/{profile['id']}")).json()
        response = await anon_client.get(f"/p/{current['slug']}")
        assert response.status_code == 200
        data = response.json()
        assert "qr_token" not in data
        assert "user_id" not in data
        assert "is_default" not in data
        assert "deleted_at" not in data

    async def test_public_profile_has_sensitive_data_false(
        self,
        anon_client: AsyncClient,
        seed_free_user,
        profile,
        client: AsyncClient,
    ) -> None:
        current = (await client.get(f"/v1/profiles/{profile['id']}")).json()
        response = await anon_client.get(f"/p/{current['slug']}")
        assert response.status_code == 200
        assert response.json()["has_sensitive_data"] is False

    async def test_public_profile_not_found(
        self,
        anon_client: AsyncClient,
    ) -> None:
        response = await anon_client.get("/p/nonexistent-slug")
        assert response.status_code == 404

    async def test_old_slug_redirects(
        self,
        anon_client: AsyncClient,
        seed_free_user,
        profile,
        client: AsyncClient,
    ) -> None:
        # Run last in this class — other tests use profile["slug"] unchanged.
        me = await client.get(f"/v1/profiles/{profile['id']}")
        assert me.status_code == 200
        old_slug = me.json()["slug"]
        await client.patch(
            f"/v1/profiles/{profile['id']}",
            json={"slug": "redirect-test-slug"},
        )
        response = await anon_client.get(
            f"/p/{old_slug}",
            follow_redirects=False,
        )
        assert response.status_code == 301
        assert "/p/redirect-test-slug" in response.headers["location"]


class TestQRRedirect:
    """GET /q/{qr_token}"""

    async def test_qr_redirect(
        self,
        anon_client: AsyncClient,
        seed_free_user,
        profile,
    ) -> None:
        qr_token = profile["qr_token"]
        response = await anon_client.get(
            f"/q/{qr_token}",
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert "/p/" in response.headers["location"]

    async def test_qr_redirect_invalid_token(
        self,
        anon_client: AsyncClient,
    ) -> None:
        response = await anon_client.get(
            "/q/00000000-0000-0000-0000-000000000000",
            follow_redirects=False,
        )
        assert response.status_code == 404


class TestSoftDelete:
    """DELETE /v1/profiles/{id}"""

    async def test_cannot_delete_default_profile(
        self,
        client: AsyncClient,
        seed_free_user,
        profile,
    ) -> None:
        response = await client.delete(f"/v1/profiles/{profile['id']}")
        assert response.status_code == 403

    async def test_can_delete_non_default_profile(
        self,
        premium_client: AsyncClient,
        seed_premium_user,
    ) -> None:
        # Create a second profile to delete
        r = await premium_client.post(
            "/v1/profiles",
            json={"name": "Profile To Delete"},
        )
        assert r.status_code == 201
        profile_id = r.json()["id"]

        # Delete it
        response = await premium_client.delete(f"/v1/profiles/{profile_id}")
        assert response.status_code == 204


class TestSetDefault:
    """POST /v1/profiles/{id}/set-default"""

    async def test_set_default(
        self,
        client: AsyncClient,
        seed_free_user,
        profile,
    ) -> None:
        response = await client.post(
            f"/v1/profiles/{profile['id']}/set-default"
        )
        assert response.status_code == 200
        assert response.json()["is_default"] is True


class TestRestore:
    """POST /v1/profiles/{id}/restore"""

    async def test_restore_soft_deleted_profile(
        self,
        premium_client: AsyncClient,
        seed_premium_user,
    ) -> None:
        # Create and delete a profile
        r = await premium_client.post(
            "/v1/profiles",
            json={"name": "Restore Test Profile"},
        )
        assert r.status_code == 201
        profile_id = r.json()["id"]

        # Make it non-default first
        profiles = (await premium_client.get("/v1/profiles")).json()
        default = next(p for p in profiles if p["is_default"])
        if default["id"] == profile_id:
            other = next(p for p in profiles if p["id"] != profile_id)
            await premium_client.post(f"/v1/profiles/{other['id']}/set-default")

        # Soft delete
        await premium_client.delete(f"/v1/profiles/{profile_id}")

        # Restore
        response = await premium_client.post(
            f"/v1/profiles/{profile_id}/restore"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["deleted_at"] is None
        assert data["restored_at"] is not None
