"""Tests for link API routes — CRUD, reorder, click tracking."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator, AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, get_optional_user
from app.core.db.session import get_db
from app.domain.user.dto import UserInternal
from app.main import app
from tests.conftest import (
    TEST_USER_EMAIL,
    TEST_USER_ID,
    make_user_internal,
)
import uuid
from app.domain.link.models import Link


@pytest_asyncio.fixture(scope="module", loop_scope="session")
async def profile(db: AsyncSession, seed_free_user) -> AsyncIterator[dict]:
    """Get or create a free-tier profile for link tests."""
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
                r = await ac.post(
                    "/v1/profiles",
                    json={"name": "Link Test Profile"},
                )
                assert r.status_code == 201
                data = r.json()
            yield data
    finally:
        app.dependency_overrides.clear()


def _links_url(profile_id: str) -> str:
    return f"/v1/links?profile_id={profile_id}"


class TestCreateLink:
    """POST /v1/links"""

    async def test_create_link(
        self,
        client: AsyncClient,
        seed_free_user,
        profile,
    ) -> None:
        response = await client.post(
            "/v1/links",
            json={
                "profile_id": profile["id"],
                "title": "My Website",
                "url": "https://example.com",
                "link_type": "custom",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "My Website"
        assert data["url"] == "https://example.com"
        assert data["is_active"] is True
        assert data["display_order"] == 0
        assert data["click_count"] == 0

    async def test_create_second_link_increments_display_order(
        self,
        client: AsyncClient,
        seed_free_user,
        profile,
    ) -> None:
        response = await client.post(
            "/v1/links",
            json={
                "profile_id": profile["id"],
                "title": "My GitHub",
                "url": "https://github.com/example",
                "link_type": "social",
            },
        )
        assert response.status_code == 201
        assert response.json()["display_order"] == 1

    async def test_create_link_invalid_url(
        self,
        client: AsyncClient,
        seed_free_user,
        profile,
    ) -> None:
        response = await client.post(
            "/v1/links",
            json={
                "profile_id": profile["id"],
                "title": "Bad Link",
                "url": "not-a-url",
                "link_type": "custom",
            },
        )
        assert response.status_code == 422

    async def test_create_link_wrong_profile(
        self,
        client: AsyncClient,
        seed_free_user,
    ) -> None:
        response = await client.post(
            "/v1/links",
            json={
                "profile_id": "00000000-0000-0000-0000-000000000000",
                "title": "Wrong Profile",
                "url": "https://example.com",
                "link_type": "custom",
            },
        )
        assert response.status_code == 404

    async def test_create_link_missing_title(
        self,
        client: AsyncClient,
        seed_free_user,
        profile,
    ) -> None:
        response = await client.post(
            "/v1/links",
            json={
                "profile_id": profile["id"],
                "url": "https://example.com",
                "link_type": "custom",
            },
        )
        assert response.status_code == 422


class TestListLinks:
    """GET /v1/links?profile_id=..."""

    async def test_list_links(
        self,
        client: AsyncClient,
        seed_free_user,
        profile,
    ) -> None:
        response = await client.get(_links_url(profile["id"]))
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    async def test_list_links_ordered_by_display_order(
        self,
        client: AsyncClient,
        seed_free_user,
        profile,
    ) -> None:
        response = await client.get(_links_url(profile["id"]))
        assert response.status_code == 200
        data = response.json()
        orders = [l["display_order"] for l in data]
        assert orders == sorted(orders)

    async def test_list_links_has_required_fields(
        self,
        client: AsyncClient,
        seed_free_user,
        profile,
    ) -> None:
        response = await client.get(_links_url(profile["id"]))
        assert response.status_code == 200
        link = response.json()[0]
        assert "id" in link
        assert "title" in link
        assert "url" in link
        assert "link_type" in link
        assert "display_order" in link
        assert "is_active" in link
        assert "click_count" in link


class TestGetLink:
    """GET /v1/links/{link_id}"""

    async def test_get_link_by_id(
        self,
        client: AsyncClient,
        seed_free_user,
        profile,
    ) -> None:
        links = (await client.get(_links_url(profile["id"]))).json()
        link_id = links[0]["id"]
        response = await client.get(f"/v1/links/{link_id}")
        assert response.status_code == 200
        assert response.json()["id"] == link_id

    async def test_get_link_not_found(
        self,
        client: AsyncClient,
        seed_free_user,
        profile,
    ) -> None:
        response = await client.get(
            "/v1/links/00000000-0000-0000-0000-000000000000"
        )
        assert response.status_code == 404


class TestUpdateLink:
    """PATCH /v1/links/{link_id}"""

    async def test_update_link_title(
        self,
        client: AsyncClient,
        seed_free_user,
        profile,
    ) -> None:
        links = (await client.get(_links_url(profile["id"]))).json()
        link_id = links[0]["id"]
        response = await client.patch(
            f"/v1/links/{link_id}",
            json={"title": "Updated Title"},
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Updated Title"

    async def test_update_link_toggle_active(
        self,
        client: AsyncClient,
        seed_free_user,
        profile,
    ) -> None:
        links = (await client.get(_links_url(profile["id"]))).json()
        link_id = links[0]["id"]
        original_active = links[0]["is_active"]
        response = await client.patch(
            f"/v1/links/{link_id}",
            json={"is_active": not original_active},
        )
        assert response.status_code == 200
        assert response.json()["is_active"] is not original_active

    async def test_update_link_not_found(
        self,
        client: AsyncClient,
        seed_free_user,
        profile,
    ) -> None:
        response = await client.patch(
            "/v1/links/00000000-0000-0000-0000-000000000000",
            json={"title": "Ghost"},
        )
        assert response.status_code == 404


class TestReorderLinks:
    """POST /v1/links/reorder"""

    async def test_reorder_links(
        self,
        client: AsyncClient,
        seed_free_user,
        profile,
    ) -> None:
        links = (await client.get(_links_url(profile["id"]))).json()
        assert len(links) >= 2

        reversed_ids = [links[1]["id"], links[0]["id"]]
        response = await client.post(
            "/v1/links/reorder",
            json={
                "profile_id": profile["id"],
                "link_ids": reversed_ids,
            },
        )
        assert response.status_code == 200
        data = response.json()
        orders = [l["display_order"] for l in data]
        assert orders == sorted(orders)

    async def test_reorder_links_wrong_profile(
        self,
        client: AsyncClient,
        seed_free_user,
    ) -> None:
        response = await client.post(
            "/v1/links/reorder",
            json={
                "profile_id": "00000000-0000-0000-0000-000000000000",
                "link_ids": [],
            },
        )
        assert response.status_code == 404


class TestClickTracking:
    """POST /v1/links/{link_id}/click — public, optional auth"""

    async def test_click_returns_204(
        self,
        client: AsyncClient,
        seed_free_user,
        profile,
    ) -> None:
        # Get first link via API
        links = (await client.get(_links_url(profile["id"]))).json()
        if not links:
            r = await client.post(
                "/v1/links",
                json={
                    "profile_id": profile["id"],
                    "title": "Click Test Link",
                    "url": "https://click-test.com",
                    "link_type": "custom",
                },
            )
            assert r.status_code == 201
            link_id = r.json()["id"]
        else:
            link_id = links[0]["id"]

        response = await client.post(f"/v1/links/{link_id}/click")
        assert response.status_code == 204

    async def test_click_invalid_link(
        self,
        anon_client: AsyncClient,
        seed_free_user,
        profile,
    ) -> None:
        response = await anon_client.post(
            "/v1/links/00000000-0000-0000-0000-000000000000/click"
        )
        assert response.status_code == 404

    async def test_click_increments_count_via_service(
        self,
        db,
        seed_free_user,
        profile,
    ) -> None:
        # Test the service layer directly — bypass background task timing issue
        from app.domain.link import service as link_service
        import uuid

        result = await db.execute(
            select(Link)
            .where(Link.profile_id == uuid.UUID(str(profile["id"])))
            .limit(1)
        )
        link = result.scalar_one_or_none()
        if link is None:
            return  # no links to test

        original_count = link.click_count
        link_id = link.id

        await link_service.increment_click_count(link_id, db)

        db.expire_all()
        result = await db.execute(select(Link).where(Link.id == link_id))
        updated = result.scalar_one()
        assert updated.click_count == original_count + 1


class TestDeleteLink:
    """DELETE /v1/links/{link_id}"""

    async def test_delete_link(
        self,
        client: AsyncClient,
        seed_free_user,
        profile,
    ) -> None:
        r = await client.post(
            "/v1/links",
            json={
                "profile_id": profile["id"],
                "title": "To Delete",
                "url": "https://delete-me.com",
                "link_type": "custom",
            },
        )
        assert r.status_code == 201
        link_id = r.json()["id"]

        response = await client.delete(f"/v1/links/{link_id}")
        assert response.status_code == 204

    async def test_deleted_link_not_in_list(
        self,
        client: AsyncClient,
        seed_free_user,
        profile,
    ) -> None:
        r = await client.post(
            "/v1/links",
            json={
                "profile_id": profile["id"],
                "title": "Also Delete",
                "url": "https://also-delete.com",
                "link_type": "custom",
            },
        )
        assert r.status_code == 201
        link_id = r.json()["id"]
        await client.delete(f"/v1/links/{link_id}")

        links = (await client.get(_links_url(profile["id"]))).json()
        assert all(l["id"] != link_id for l in links)

    async def test_delete_link_not_found(
        self,
        client: AsyncClient,
        seed_free_user,
        profile,
    ) -> None:
        response = await client.delete(
            "/v1/links/00000000-0000-0000-0000-000000000000"
        )
        assert response.status_code == 404
