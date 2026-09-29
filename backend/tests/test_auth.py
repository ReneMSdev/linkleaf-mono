"""Tests for the ALLOWED_FIREBASE_UIDS allowlist in app/auth/dependencies.py.

Unlike the other suites, these exercise the real get_current_user /
get_optional_user dependencies; only Firebase token verification is patched.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, AsyncIterator
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from fastapi import BackgroundTasks
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from app.auth.dependencies import get_optional_user
from app.config.settings import Settings, get_settings
from app.core.db.session import get_db
from app.main import app
from tests.conftest import TEST_USER_EMAIL, TEST_USER_ID

SEEDED_UID = f"firebase_{TEST_USER_ID.hex}"
STRANGER_UID = "stranger-uid"


def _token_for(uid: str) -> dict:
    return {"uid": uid, "email": TEST_USER_EMAIL}


def _request_with_bearer() -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": [(b"authorization", b"Bearer fake-token")],
        }
    )


@pytest.fixture
def allowlist(monkeypatch: pytest.MonkeyPatch):
    """Sets ALLOWED_FIREBASE_UIDS on the cached settings for one test."""

    def _set(uids: list[str]) -> None:
        monkeypatch.setattr(get_settings(), "ALLOWED_FIREBASE_UIDS", uids)

    return _set


@pytest_asyncio.fixture(loop_scope="session")
async def real_auth_client(db: AsyncSession) -> AsyncIterator[AsyncClient]:
    """Client that keeps the real auth dependencies; only the DB is overridden."""

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"Authorization": "Bearer fake-token"},
        ) as ac:
            yield ac
    finally:
        app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def _no_last_login_task():
    # The background task opens its own session from DATABASE_URL; keep it out of tests.
    with patch("app.auth.dependencies._update_last_login_background", new=AsyncMock()):
        yield


class TestRequiredAuthAllowlist:
    """get_current_user via GET /v1/users/me"""

    async def test_listed_uid_is_allowed(
        self,
        real_auth_client: AsyncClient,
        seed_free_user,
        allowlist,
    ) -> None:
        allowlist([SEEDED_UID])
        with patch("app.auth.dependencies.verify_token", return_value=_token_for(SEEDED_UID)):
            response = await real_auth_client.get("/v1/users/me")
        assert response.status_code == 200
        assert response.json()["id"] == str(TEST_USER_ID)

    async def test_unlisted_uid_is_forbidden_and_not_provisioned(
        self,
        real_auth_client: AsyncClient,
        allowlist,
    ) -> None:
        allowlist([SEEDED_UID])
        with (
            patch("app.auth.dependencies.verify_token", return_value=_token_for(STRANGER_UID)),
            patch(
                "app.auth.dependencies.get_by_firebase_uid",
                new=AsyncMock(return_value=None),
            ) as lookup,
            patch(
                "app.auth.dependencies.create_from_firebase",
                new=AsyncMock(side_effect=AssertionError("unlisted UID was provisioned")),
            ) as create,
        ):
            response = await real_auth_client.get("/v1/users/me")
        assert response.status_code == 403
        assert response.json()["detail"] == "Account not permitted."
        lookup.assert_not_called()
        create.assert_not_called()

    async def test_empty_allowlist_allows_any_uid(
        self,
        real_auth_client: AsyncClient,
        seed_free_user,
        allowlist,
    ) -> None:
        allowlist([])
        with patch("app.auth.dependencies.verify_token", return_value=_token_for(SEEDED_UID)):
            response = await real_auth_client.get("/v1/users/me")
        assert response.status_code == 200


class TestOptionalAuthAllowlist:
    """get_optional_user, called directly"""

    async def test_unlisted_uid_is_treated_as_anonymous(
        self,
        db: AsyncSession,
        allowlist,
    ) -> None:
        allowlist([SEEDED_UID])
        with (
            patch("app.auth.dependencies.verify_token", return_value=_token_for(STRANGER_UID)),
            patch("app.auth.dependencies.create_from_firebase", new=AsyncMock()) as create,
        ):
            user = await get_optional_user(_request_with_bearer(), BackgroundTasks(), db)
        assert user is None
        create.assert_not_called()

    async def test_listed_uid_resolves_user(
        self,
        db: AsyncSession,
        seed_free_user,
        allowlist,
    ) -> None:
        allowlist([SEEDED_UID])
        with patch("app.auth.dependencies.verify_token", return_value=_token_for(SEEDED_UID)):
            user = await get_optional_user(_request_with_bearer(), BackgroundTasks(), db)
        assert user is not None
        assert user.id == TEST_USER_ID


class TestAllowlistRequiredWhenDeployed:
    """Settings refuse an empty allowlist in staging and production."""

    @pytest.mark.parametrize("env", ["staging", "production"])
    def test_empty_allowlist_rejected(self, env: str) -> None:
        with pytest.raises(ValidationError, match="ALLOWED_FIREBASE_UIDS"):
            Settings(APP_ENV=env, ALLOWED_FIREBASE_UIDS=[])

    @pytest.mark.parametrize("env", ["staging", "production"])
    def test_non_empty_allowlist_accepted(self, env: str) -> None:
        settings = Settings(APP_ENV=env, ALLOWED_FIREBASE_UIDS=["some-uid"])
        assert settings.ALLOWED_FIREBASE_UIDS == ["some-uid"]

    @pytest.mark.parametrize("env", ["development", "test"])
    def test_empty_allowlist_fine_locally(self, env: str) -> None:
        assert Settings(APP_ENV=env, ALLOWED_FIREBASE_UIDS=[]).ALLOWED_FIREBASE_UIDS == []
