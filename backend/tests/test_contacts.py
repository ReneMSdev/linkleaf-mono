"""Tests for contact API routes — upsert, vCard download."""

from __future__ import annotations

from collections.abc import AsyncGenerator, AsyncIterator

import pytest_asyncio
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, get_optional_user
from app.core.db.session import get_db
from app.domain.user.dto import UserInternal
from app.main import app
from tests.conftest import (
    TEST_USER_EMAIL,
    TEST_USER_ID,
    TestSessionLocal,
    make_user_internal,
)


async def _fetch_vcard_public(profile_id: str) -> Response:
    """GET vCard with a clean DB session and public-style auth overrides."""
    from httpx import AsyncClient as HttpxClient

    from app.main import app as fastapi_app

    async def _get_db() -> AsyncGenerator[AsyncSession, None]:
        async with TestSessionLocal() as session:
            yield session

    async def _anon_current_user() -> UserInternal:
        raise HTTPException(status_code=401, detail="Authentication token is missing.")

    async def _anon_optional_user() -> UserInternal | None:
        return None

    fastapi_app.dependency_overrides[get_db] = _get_db
    fastapi_app.dependency_overrides[get_current_user] = _anon_current_user
    fastapi_app.dependency_overrides[get_optional_user] = _anon_optional_user

    try:
        async with HttpxClient(
            transport=ASGITransport(app=fastapi_app),
            base_url="http://test",
        ) as ac:
            return await ac.get(f"/contacts/{profile_id}/vcard")
    finally:
        fastapi_app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="module", loop_scope="session")
async def profile(db: AsyncSession, seed_free_user) -> AsyncIterator[dict]:
    """Get or create a free-tier profile for contact tests."""
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
                    json={"name": "Contact Test Profile"},
                )
                assert r.status_code == 201
                data = r.json()
            yield data
    finally:
        app.dependency_overrides.clear()


class TestContactMutations:
    """POST /v1/contacts — upsert with profile_id in body"""

    async def test_create_contact(
        self,
        client: AsyncClient,
        seed_free_user,
        profile,
    ) -> None:
        response = await client.post(
            "/v1/contacts",
            json={
                "profile_id": profile["id"],
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
                "phone": "+1234567890",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "John"
        assert data["last_name"] == "Doe"
        assert data["email"] == "john@example.com"
        assert data["phone"] == "+1234567890"

    async def test_update_contact(
        self,
        client: AsyncClient,
        seed_free_user,
        profile,
    ) -> None:
        response = await client.post(
            "/v1/contacts",
            json={
                "profile_id": profile["id"],
                "first_name": "Jane",
                "last_name": "Doe",
                "email": "jane@example.com",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Jane"
        assert data["email"] == "jane@example.com"

    async def test_contact_has_required_fields(
        self,
        client: AsyncClient,
        seed_free_user,
        profile,
    ) -> None:
        response = await client.post(
            "/v1/contacts",
            json={
                "profile_id": profile["id"],
                "first_name": "Field Test",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "profile_id" in data
        assert "first_name" in data
        assert "created_at" in data
        assert "updated_at" in data

    async def test_upsert_contact_wrong_profile(
        self,
        client: AsyncClient,
        seed_free_user,
    ) -> None:
        response = await client.post(
            "/v1/contacts",
            json={
                "profile_id": "00000000-0000-0000-0000-000000000000",
                "first_name": "Ghost",
            },
        )
        assert response.status_code == 404

    async def test_upsert_contact_unauthenticated(
        self,
        anon_client: AsyncClient,
        profile,
    ) -> None:
        response = await anon_client.post(
            "/v1/contacts",
            json={
                "profile_id": profile["id"],
                "first_name": "Anon",
            },
        )
        assert response.status_code == 401

    async def test_contact_empty_body_allowed(
        self,
        client: AsyncClient,
        seed_free_user,
        profile,
    ) -> None:
        # profile_id required; other fields optional
        response = await client.post(
            "/v1/contacts",
            json={"profile_id": profile["id"]},
        )
        assert response.status_code == 200

    async def test_contact_with_address(
        self,
        client: AsyncClient,
        seed_free_user,
        profile,
    ) -> None:
        response = await client.post(
            "/v1/contacts",
            json={
                "profile_id": profile["id"],
                "first_name": "Address",
                "last_name": "Test",
                "address_line_1": "123 Main St",
                "city": "Austin",
                "state": "TX",
                "country": "US",
                "postal_code": "78701",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["address_line_1"] == "123 Main St"
        assert data["city"] == "Austin"

    async def test_contact_with_company(
        self,
        client: AsyncClient,
        seed_free_user,
        profile,
    ) -> None:
        response = await client.post(
            "/v1/contacts",
            json={
                "profile_id": profile["id"],
                "first_name": "Company",
                "last_name": "Test",
                "company": "Acme Corp",
                "job_title": "Engineer",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["company"] == "Acme Corp"
        assert data["job_title"] == "Engineer"


class TestContactQueries:
    """GET /v1/contacts/{profile_id}"""

    async def test_get_contact(
        self,
        client: AsyncClient,
        seed_free_user,
        profile,
    ) -> None:
        response = await client.get(f"/v1/contacts/{profile['id']}")
        assert response.status_code == 200
        data = response.json()
        assert data["profile_id"] == profile["id"]

    async def test_get_contact_not_found(
        self,
        client: AsyncClient,
        seed_free_user,
    ) -> None:
        response = await client.get(
            "/v1/contacts/00000000-0000-0000-0000-000000000000"
        )
        assert response.status_code == 404

    async def test_get_contact_unauthenticated(
        self,
        anon_client: AsyncClient,
        profile,
    ) -> None:
        response = await anon_client.get(f"/v1/contacts/{profile['id']}")
        assert response.status_code == 401


class TestVCard:
    """GET /contacts/{profile_id}/vcard — public, no auth"""

    async def test_vcard_download(
        self,
        anon_client: AsyncClient,
        seed_free_user,
        profile,
        client: AsyncClient,
    ) -> None:
        await client.post(
            "/v1/contacts",
            json={
                "profile_id": profile["id"],
                "first_name": "vCard",
                "last_name": "Test",
                "email": "vcard@example.com",
                "phone": "+1234567890",
            },
        )

        response = await _fetch_vcard_public(profile["id"])

        assert response.status_code == 200
        assert "text/vcard" in response.headers["content-type"]
        content = response.text
        assert "BEGIN:VCARD" in content
        assert "END:VCARD" in content
        assert "vCard Test" in content

    async def test_vcard_not_found(
        self,
        anon_client: AsyncClient,
    ) -> None:
        response = await anon_client.get(
            "/contacts/00000000-0000-0000-0000-000000000000/vcard"
        )
        assert response.status_code == 404

    async def test_vcard_contains_email(
        self,
        seed_free_user,
        profile,
        client: AsyncClient,
    ) -> None:
        await client.post(
            "/v1/contacts",
            json={
                "profile_id": profile["id"],
                "first_name": "Email",
                "last_name": "Check",
                "email": "vcard@example.com",
            },
        )

        response = await _fetch_vcard_public(profile["id"])

        assert response.status_code == 200
        assert "vcard@example.com" in response.text

    async def test_vcard_free_user_has_branding(
        self,
        seed_free_user,
        profile,
        client: AsyncClient,
    ) -> None:
        await client.post(
            "/v1/contacts",
            json={
                "profile_id": profile["id"],
                "first_name": "Brand",
                "last_name": "Test",
            },
        )

        response = await _fetch_vcard_public(profile["id"])

        assert response.status_code == 200
        assert "LinkLeaf" in response.text
