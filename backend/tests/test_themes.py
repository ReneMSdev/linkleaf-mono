"""Tests for theme API routes — marketplace, lock state, featured preview."""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import AsyncClient

from tests.conftest import TEST_PREMIUM_USER_ID, TEST_USER_ID  # noqa: F401


class TestListThemes:
    """GET /v1/themes"""

    async def test_list_themes_returns_all(
        self,
        client: AsyncClient,
        seed_free_user,
    ) -> None:
        response = await client.get("/v1/themes")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    async def test_list_themes_free_user_sees_all(
        self,
        client: AsyncClient,
        seed_free_user,
    ) -> None:
        # Free users see all themes — premium ones are locked not hidden
        response = await client.get("/v1/themes")
        assert response.status_code == 200
        data = response.json()
        tiers = {t["tier"] for t in data}
        assert "free" in tiers
        assert "premium" in tiers

    async def test_list_themes_free_user_premium_locked(
        self,
        client: AsyncClient,
        seed_free_user,
    ) -> None:
        response = await client.get("/v1/themes")
        assert response.status_code == 200
        data = response.json()
        for theme in data:
            if theme["tier"] == "premium":
                assert theme["is_locked"] is True
            else:
                assert theme["is_locked"] is False

    async def test_list_themes_premium_user_all_unlocked(
        self,
        premium_client: AsyncClient,
        seed_premium_user,
    ) -> None:
        response = await premium_client.get("/v1/themes")
        assert response.status_code == 200
        data = response.json()
        for theme in data:
            assert theme["is_locked"] is False

    async def test_list_themes_has_required_fields(
        self,
        client: AsyncClient,
        seed_free_user,
    ) -> None:
        response = await client.get("/v1/themes")
        assert response.status_code == 200
        theme = response.json()[0]
        assert "id" in theme
        assert "name" in theme
        assert "slug" in theme
        assert "tier" in theme
        assert "config" in theme
        assert "is_locked" in theme
        assert "is_featured" in theme

    async def test_list_themes_ordered_free_first(
        self,
        client: AsyncClient,
        seed_free_user,
    ) -> None:
        response = await client.get("/v1/themes")
        assert response.status_code == 200
        data = response.json()
        tiers = [t["tier"] for t in data]
        # free themes come before premium (ordered by tier asc)
        last_free = max(
            (i for i, t in enumerate(tiers) if t == "free"),
            default=-1,
        )
        first_premium = min(
            (i for i, t in enumerate(tiers) if t == "premium"),
            default=len(tiers),
        )
        assert last_free < first_premium

    async def test_list_themes_unauthenticated(
        self,
        anon_client: AsyncClient,
    ) -> None:
        response = await anon_client.get("/v1/themes")
        assert response.status_code == 401


class TestGetTheme:
    """GET /v1/themes/{id}"""

    async def test_get_free_theme(
        self,
        client: AsyncClient,
        seed_free_user,
    ) -> None:
        # Get a free theme ID from list
        themes = (await client.get("/v1/themes")).json()
        free_theme = next(t for t in themes if t["tier"] == "free")
        response = await client.get(f"/v1/themes/{free_theme['id']}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == free_theme["id"]
        assert data["is_locked"] is False

    async def test_get_premium_theme_locked_for_free_user(
        self,
        client: AsyncClient,
        seed_free_user,
    ) -> None:
        themes = (await client.get("/v1/themes")).json()
        premium_theme = next(t for t in themes if t["tier"] == "premium")
        response = await client.get(f"/v1/themes/{premium_theme['id']}")
        assert response.status_code == 200
        assert response.json()["is_locked"] is True

    async def test_get_premium_theme_unlocked_for_premium_user(
        self,
        premium_client: AsyncClient,
        seed_premium_user,
    ) -> None:
        themes = (await premium_client.get("/v1/themes")).json()
        premium_theme = next(t for t in themes if t["tier"] == "premium")
        response = await premium_client.get(f"/v1/themes/{premium_theme['id']}")
        assert response.status_code == 200
        assert response.json()["is_locked"] is False

    async def test_get_theme_not_found(
        self,
        client: AsyncClient,
        seed_free_user,
    ) -> None:
        response = await client.get(
            "/v1/themes/00000000-0000-0000-0000-000000000000"
        )
        assert response.status_code == 404

    async def test_get_theme_unauthenticated(
        self,
        anon_client: AsyncClient,
    ) -> None:
        # Auth check happens before theme lookup — any UUID triggers 401
        response = await anon_client.get(
            "/v1/themes/00000000-0000-0000-0000-000000000001"
        )
        assert response.status_code == 401


class TestFeaturedThemes:
    """GET /themes/preview — public, no auth"""

    async def test_featured_themes_public(
        self,
        anon_client: AsyncClient,
    ) -> None:
        response = await anon_client.get("/themes/preview")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    async def test_featured_themes_all_have_is_featured_true(
        self,
        anon_client: AsyncClient,
    ) -> None:
        response = await anon_client.get("/themes/preview")
        assert response.status_code == 200
        for theme in response.json():
            assert theme["is_featured"] is True

    async def test_featured_themes_is_locked_always_false(
        self,
        anon_client: AsyncClient,
    ) -> None:
        # Public endpoint — no user context, is_locked always False
        response = await anon_client.get("/themes/preview")
        assert response.status_code == 200
        for theme in response.json():
            assert theme["is_locked"] is False

    async def test_featured_themes_includes_both_tiers(
        self,
        anon_client: AsyncClient,
    ) -> None:
        response = await anon_client.get("/themes/preview")
        assert response.status_code == 200
        tiers = {t["tier"] for t in response.json()}
        assert "free" in tiers
        assert "premium" in tiers

    async def test_featured_themes_has_config(
        self,
        anon_client: AsyncClient,
    ) -> None:
        response = await anon_client.get("/themes/preview")
        assert response.status_code == 200
        for theme in response.json():
            assert "config" in theme
            assert isinstance(theme["config"], dict)


class TestApplyTheme:
    """PATCH /v1/profiles/{id} with theme_id — theme gate enforcement"""

    async def test_free_user_cannot_apply_premium_theme(
        self,
        client: AsyncClient,
        seed_free_user,
    ) -> None:
        # Get a profile
        profiles = (await client.get("/v1/profiles")).json()
        if not profiles:
            r = await client.post(
                "/v1/profiles",
                json={"name": "Theme Test Profile"},
            )
            profile_id = r.json()["id"]
        else:
            profile_id = profiles[0]["id"]

        # Get a premium theme
        themes = (await client.get("/v1/themes")).json()
        premium_theme = next(t for t in themes if t["tier"] == "premium")

        # Try to apply premium theme as free user
        response = await client.patch(
            f"/v1/profiles/{profile_id}",
            json={"theme_id": premium_theme["id"]},
        )
        assert response.status_code == 403

    async def test_premium_user_can_apply_premium_theme(
        self,
        premium_client: AsyncClient,
        seed_premium_user,
    ) -> None:
        profiles = (await premium_client.get("/v1/profiles")).json()
        if not profiles:
            r = await premium_client.post(
                "/v1/profiles",
                json={"name": "Premium Theme Test"},
            )
            profile_id = r.json()["id"]
        else:
            profile_id = profiles[0]["id"]

        themes = (await premium_client.get("/v1/themes")).json()
        premium_theme = next(t for t in themes if t["tier"] == "premium")

        response = await premium_client.patch(
            f"/v1/profiles/{profile_id}",
            json={"theme_id": premium_theme["id"]},
        )
        assert response.status_code == 200
        assert response.json()["theme_id"] == premium_theme["id"]

    async def test_free_user_can_apply_free_theme(
        self,
        client: AsyncClient,
        seed_free_user,
    ) -> None:
        profiles = (await client.get("/v1/profiles")).json()
        if not profiles:
            r = await client.post(
                "/v1/profiles",
                json={"name": "Free Theme Test"},
            )
            profile_id = r.json()["id"]
        else:
            profile_id = profiles[0]["id"]

        themes = (await client.get("/v1/themes")).json()
        free_theme = next(t for t in themes if t["tier"] == "free")

        response = await client.patch(
            f"/v1/profiles/{profile_id}",
            json={"theme_id": free_theme["id"]},
        )
        assert response.status_code == 200
        assert response.json()["theme_id"] == free_theme["id"]
