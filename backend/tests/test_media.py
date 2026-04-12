"""Tests for media API routes — avatar, image, resume upload, soft delete, restore."""

from __future__ import annotations

import struct
import uuid
import zlib
from collections.abc import AsyncGenerator, AsyncIterator
from unittest.mock import AsyncMock, patch

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, get_optional_user
from app.core.db.session import get_db
from app.domain.media.models import Media, MediaType
from app.domain.user.dto import UserInternal
from app.main import app
from tests.conftest import (
    TEST_PREMIUM_USER_EMAIL,
    TEST_PREMIUM_USER_ID,
    TEST_USER_EMAIL,
    TEST_USER_ID,
    make_user_internal,
)


def _png_chunk(name: bytes, data: bytes) -> bytes:
    c = struct.pack(">I", len(data)) + name + data
    return c + struct.pack(">I", zlib.crc32(c[4:]) & 0xFFFFFFFF)


def _fake_image_bytes() -> bytes:
    """Minimal valid PNG bytes (passes Pillow / typical magic sniffing)."""
    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    idat = zlib.compress(b"\x00\xff\xff\xff")
    return (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"IDAT", idat)
        + _png_chunk(b"IEND", b"")
    )


def _fake_pdf_bytes() -> bytes:
    """Minimal PDF structure for resume path tests."""
    return (
        b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n"
        b"xref\n0 1\n0000000000 65535 f\ntrailer\n<< /Size 1 /Root 1 0 R >>\n"
        b"startxref\n9\n%%EOF"
    )


@pytest_asyncio.fixture(scope="module", loop_scope="session")
async def profile(db: AsyncSession, seed_free_user) -> AsyncIterator[dict]:
    """Get or create a free-tier profile for media tests."""
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
                    json={"name": "Media Test Profile"},
                )
                assert r.status_code == 201
                data = r.json()
            yield data
    finally:
        app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="module", loop_scope="session")
async def premium_profile(db: AsyncSession, seed_premium_user) -> AsyncIterator[dict]:
    """Get or create a premium profile for media tests."""
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
                r = await ac.post(
                    "/v1/profiles",
                    json={"name": "Premium Media Profile"},
                )
                assert r.status_code == 201
                data = r.json()
            yield data
    finally:
        app.dependency_overrides.clear()


def _mock_storage_upload() -> patch:
    return patch(
        "app.domain.media.service.storage.upload_file",
        new_callable=AsyncMock,
        return_value="profiles/test/images/fake.webp",
    )


def _mock_storage_public_url() -> patch:
    return patch(
        "app.domain.media.service.storage.get_public_url",
        return_value="https://storage.googleapis.com/bucket/profiles/test/images/fake.webp",
    )


def _mock_storage_signed_url() -> patch:
    return patch(
        "app.domain.media.service.storage.get_signed_url",
        new_callable=AsyncMock,
        return_value="https://storage.googleapis.com/bucket/profiles/test/resume.pdf?X-Goog-Signature=fake",
    )


def _mock_storage_generate_path() -> patch:
    return patch(
        "app.domain.media.service.storage.generate_upload_path",
        return_value="profiles/test/images/fake.webp",
    )


def _mock_process_avatar() -> patch:
    return patch(
        "app.domain.media.service.image_processing.process_avatar",
        return_value=b"fake_webp_bytes",
    )


def _mock_process_image() -> patch:
    return patch(
        "app.domain.media.service.image_processing.process_profile_image",
        return_value=b"fake_webp_bytes",
    )


def _mock_validate_resume() -> patch:
    return patch(
        "app.domain.media.service.image_processing.validate_resume",
        return_value="application/pdf",
    )


def _mock_list_urls() -> tuple[patch, patch]:
    """List/get_media may include images (public) and resumes (signed)."""
    return _mock_storage_public_url(), _mock_storage_signed_url()


class TestAvatarUpload:
    """POST /v1/media/avatar/{profile_id}"""

    async def test_upload_avatar(
        self,
        client: AsyncClient,
        seed_free_user,
        profile,
    ) -> None:
        with (
            _mock_process_avatar(),
            _mock_storage_upload(),
            _mock_storage_public_url(),
            _mock_storage_generate_path(),
        ):
            response = await client.post(
                f"/v1/media/avatar/{profile['id']}",
                files={"file": ("avatar.png", _fake_image_bytes(), "image/png")},
            )
        assert response.status_code == 200
        data = response.json()
        assert "avatar_url" in data
        assert data["avatar_url"].startswith("https://")

    async def test_upload_avatar_wrong_profile(
        self,
        client: AsyncClient,
        seed_free_user,
    ) -> None:
        response = await client.post(
            "/v1/media/avatar/00000000-0000-0000-0000-000000000000",
            files={"file": ("avatar.png", _fake_image_bytes(), "image/png")},
        )
        assert response.status_code == 404

    async def test_upload_avatar_unauthenticated(
        self,
        anon_client: AsyncClient,
        profile,
    ) -> None:
        response = await anon_client.post(
            f"/v1/media/avatar/{profile['id']}",
            files={"file": ("avatar.png", _fake_image_bytes(), "image/png")},
        )
        assert response.status_code == 401


class TestImageUpload:
    """POST /v1/media/upload/{profile_id}?media_type=image"""

    async def test_free_user_cannot_upload_image(
        self,
        client: AsyncClient,
        seed_free_user,
        profile,
    ) -> None:
        with (
            _mock_process_image(),
            _mock_storage_upload(),
            _mock_storage_public_url(),
            _mock_storage_generate_path(),
        ):
            response = await client.post(
                f"/v1/media/upload/{profile['id']}?media_type=image",
                files={"file": ("photo.png", _fake_image_bytes(), "image/png")},
            )
        assert response.status_code == 403

    async def test_premium_user_can_upload_image(
        self,
        premium_client: AsyncClient,
        seed_premium_user,
        premium_profile,
    ) -> None:
        with (
            _mock_process_image(),
            _mock_storage_upload(),
            _mock_storage_public_url(),
            _mock_storage_generate_path(),
        ):
            response = await premium_client.post(
                f"/v1/media/upload/{premium_profile['id']}?media_type=image",
                files={"file": ("photo.png", _fake_image_bytes(), "image/png")},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["media_type"] == "image"
        assert data["mime_type"] == "image/webp"
        assert "url" in data
        assert data["display_order"] == 0

    async def test_premium_second_image_increments_display_order(
        self,
        premium_client: AsyncClient,
        seed_premium_user,
        premium_profile,
    ) -> None:
        with (
            _mock_process_image(),
            _mock_storage_upload(),
            _mock_storage_public_url(),
            _mock_storage_generate_path(),
        ):
            response = await premium_client.post(
                f"/v1/media/upload/{premium_profile['id']}?media_type=image",
                files={"file": ("photo2.png", _fake_image_bytes(), "image/png")},
            )
        assert response.status_code == 200
        assert response.json()["display_order"] == 1

    async def test_upload_image_wrong_profile(
        self,
        premium_client: AsyncClient,
        seed_premium_user,
    ) -> None:
        response = await premium_client.post(
            "/v1/media/upload/00000000-0000-0000-0000-000000000000?media_type=image",
            files={"file": ("photo.png", _fake_image_bytes(), "image/png")},
        )
        assert response.status_code == 404


class TestListMedia:
    """GET /v1/media/{profile_id}"""

    async def test_list_media(
        self,
        premium_client: AsyncClient,
        seed_premium_user,
        premium_profile,
    ) -> None:
        pub, sig = _mock_list_urls()
        with pub, sig:
            response = await premium_client.get(
                f"/v1/media/{premium_profile['id']}"
            )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_list_media_no_gcs_path(
        self,
        premium_client: AsyncClient,
        seed_premium_user,
        premium_profile,
    ) -> None:
        pub, sig = _mock_list_urls()
        with pub, sig:
            response = await premium_client.get(
                f"/v1/media/{premium_profile['id']}"
            )
        assert response.status_code == 200
        for item in response.json():
            assert "gcs_path" not in item

    async def test_list_media_unauthenticated(
        self,
        anon_client: AsyncClient,
        premium_profile,
    ) -> None:
        response = await anon_client.get(f"/v1/media/{premium_profile['id']}")
        assert response.status_code == 401


class TestResumeUpload:
    """POST /v1/media/upload/{profile_id}?media_type=resume"""

    async def test_free_user_cannot_upload_resume(
        self,
        client: AsyncClient,
        seed_free_user,
        profile,
    ) -> None:
        with _mock_validate_resume():
            response = await client.post(
                f"/v1/media/upload/{profile['id']}?media_type=resume",
                files={"file": ("resume.pdf", _fake_pdf_bytes(), "application/pdf")},
            )
        assert response.status_code == 403

    async def test_premium_user_can_upload_resume(
        self,
        premium_client: AsyncClient,
        seed_premium_user,
        premium_profile,
    ) -> None:
        with (
            _mock_validate_resume(),
            _mock_storage_upload(),
            _mock_storage_signed_url(),
            patch(
                "app.domain.media.service.storage.generate_upload_path",
                return_value="profiles/test/resume.pdf",
            ),
        ):
            response = await premium_client.post(
                f"/v1/media/upload/{premium_profile['id']}?media_type=resume",
                files={"file": ("resume.pdf", _fake_pdf_bytes(), "application/pdf")},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["media_type"] == "resume"
        assert data["mime_type"] == "application/pdf"
        assert "url" in data
        assert data["display_order"] is None

    async def test_resume_replacement_soft_deletes_old(
        self,
        premium_client: AsyncClient,
        seed_premium_user,
        premium_profile,
        db: AsyncSession,
    ) -> None:
        with (
            _mock_validate_resume(),
            _mock_storage_upload(),
            _mock_storage_signed_url(),
            patch(
                "app.domain.media.service.storage.generate_upload_path",
                return_value="profiles/test/resume.pdf",
            ),
        ):
            response = await premium_client.post(
                f"/v1/media/upload/{premium_profile['id']}?media_type=resume",
                files={"file": ("resume2.pdf", _fake_pdf_bytes(), "application/pdf")},
            )
        assert response.status_code == 200

        result = await db.execute(
            select(Media).where(
                Media.profile_id == uuid.UUID(str(premium_profile["id"])),
                Media.media_type == MediaType.RESUME,
                Media.deleted_at.is_(None),
            )
        )
        active_resumes = result.scalars().all()
        assert len(active_resumes) == 1


class TestSoftDeleteMedia:
    """DELETE /v1/media/{profile_id}/{media_id}"""

    async def test_soft_delete_media(
        self,
        premium_client: AsyncClient,
        seed_premium_user,
        premium_profile,
    ) -> None:
        with (
            _mock_process_image(),
            _mock_storage_upload(),
            _mock_storage_public_url(),
            _mock_storage_generate_path(),
        ):
            r = await premium_client.post(
                f"/v1/media/upload/{premium_profile['id']}?media_type=image",
                files={"file": ("delete_me.png", _fake_image_bytes(), "image/png")},
            )
        assert r.status_code == 200
        media_id = r.json()["id"]

        response = await premium_client.delete(
            f"/v1/media/{premium_profile['id']}/{media_id}"
        )
        assert response.status_code == 204

    async def test_deleted_media_not_in_list(
        self,
        premium_client: AsyncClient,
        seed_premium_user,
        premium_profile,
    ) -> None:
        with (
            _mock_process_image(),
            _mock_storage_upload(),
            _mock_storage_public_url(),
            _mock_storage_generate_path(),
        ):
            r = await premium_client.post(
                f"/v1/media/upload/{premium_profile['id']}?media_type=image",
                files={"file": ("also_delete.png", _fake_image_bytes(), "image/png")},
            )
        assert r.status_code == 200
        media_id = r.json()["id"]

        await premium_client.delete(
            f"/v1/media/{premium_profile['id']}/{media_id}"
        )

        pub, sig = _mock_list_urls()
        with pub, sig:
            listed = (
                await premium_client.get(f"/v1/media/{premium_profile['id']}")
            ).json()
        assert all(m["id"] != media_id for m in listed)

    async def test_soft_delete_not_found(
        self,
        premium_client: AsyncClient,
        seed_premium_user,
        premium_profile,
    ) -> None:
        response = await premium_client.delete(
            f"/v1/media/{premium_profile['id']}/00000000-0000-0000-0000-000000000000"
        )
        assert response.status_code == 404


class TestRestoreMedia:
    """POST /v1/media/{profile_id}/{media_id}/restore"""

    async def test_restore_media(
        self,
        premium_client: AsyncClient,
        seed_premium_user,
        premium_profile,
    ) -> None:
        with (
            _mock_process_image(),
            _mock_storage_upload(),
            _mock_storage_public_url(),
            _mock_storage_generate_path(),
        ):
            r = await premium_client.post(
                f"/v1/media/upload/{premium_profile['id']}?media_type=image",
                files={"file": ("restore_me.png", _fake_image_bytes(), "image/png")},
            )
        assert r.status_code == 200
        media_id = r.json()["id"]

        await premium_client.delete(
            f"/v1/media/{premium_profile['id']}/{media_id}"
        )

        with _mock_storage_public_url():
            response = await premium_client.post(
                f"/v1/media/{premium_profile['id']}/{media_id}/restore"
            )
        assert response.status_code == 200
        data = response.json()
        assert data["deleted_at"] is None

    async def test_restore_not_found(
        self,
        premium_client: AsyncClient,
        seed_premium_user,
        premium_profile,
    ) -> None:
        response = await premium_client.post(
            f"/v1/media/{premium_profile['id']}/00000000-0000-0000-0000-000000000000/restore"
        )
        assert response.status_code == 404
