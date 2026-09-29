"""Media domain service — uploads, URLs, soft delete, restore.

Business rules only; no FastAPI or HTTP concerns.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.core import image_processing
from app.core import storage
from app.core.exceptions import NotFoundError, PermissionDeniedError, ValidationError
from app.core.types import GRACE_PERIOD_DAYS, MediaID, ProfileID, UserID
from app.domain.media.dto import AvatarUploadResponse, MediaInternal, MediaUploadResponse
from app.domain.media.models import Media, MediaType
from app.domain.profile.models import Profile
from app.domain.subscription.service import check_portfolio_limit, check_resume_allowed

MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB
MAX_RESUME_SIZE_BYTES = 5 * 1024 * 1024  # 5MB
SIGNED_URL_EXPIRY_MINUTES = 60


# -----------------------------------------------------------------------------
# Lists active media for a profile ordered by type then display order.
# -----------------------------------------------------------------------------
async def get_all(
    profile_id: ProfileID,
    db: AsyncSession,
) -> list[MediaInternal]:
    statement = (
        select(Media)
        .where(
            Media.profile_id == profile_id,
            Media.deleted_at.is_(None),
        )
        .order_by(Media.media_type.asc(), Media.display_order.asc())
    )
    result = await db.execute(statement)
    rows = result.scalars().all()
    return [MediaInternal.model_validate(m) for m in rows]


# -----------------------------------------------------------------------------
# Fetches one media row scoped to profile when not soft-deleted.
# -----------------------------------------------------------------------------
async def get_by_id(
    media_id: MediaID,
    profile_id: ProfileID,
    db: AsyncSession,
) -> MediaInternal:
    statement = select(Media).where(
        Media.id == media_id,
        Media.profile_id == profile_id,
        Media.deleted_at.is_(None),
    )
    result = await db.execute(statement)
    media = result.scalar_one_or_none()
    if media is None:
        raise NotFoundError(f"Media {media_id} not found.")
    return MediaInternal.model_validate(media)


# -----------------------------------------------------------------------------
# Resolves a public or signed download URL for a media row.
# -----------------------------------------------------------------------------
async def get_url(
    media: MediaInternal,
    db: AsyncSession,
) -> str:
    _ = db
    settings = get_settings()
    if media.media_type == MediaType.IMAGE:
        return storage.get_public_url(media.gcs_path, settings.GCS_PUBLIC_BUCKET_NAME)
    if media.media_type == MediaType.RESUME:
        return await storage.get_signed_url(
            media.gcs_path,
            settings.GCS_PRIVATE_BUCKET_NAME,
            expiry_minutes=SIGNED_URL_EXPIRY_MINUTES,
        )
    raise ValidationError(f"Unsupported media type for URL resolution: {media.media_type!r}")


# -----------------------------------------------------------------------------
# Processes and stores an avatar on the public bucket; updates profile.avatar_url.
# -----------------------------------------------------------------------------
async def upload_avatar(
    profile_id: ProfileID,
    file_bytes: bytes,
    file_name: str,
    db: AsyncSession,
) -> AvatarUploadResponse:
    loop = asyncio.get_event_loop()
    processed_bytes = await loop.run_in_executor(
        None,
        image_processing.process_avatar,
        file_bytes,
    )
    settings = get_settings()
    ext = "webp"
    gcs_path = storage.generate_upload_path(str(profile_id), "avatar", ext)
    await storage.upload_file(
        processed_bytes,
        gcs_path,
        "image/webp",
        settings.GCS_PUBLIC_BUCKET_NAME,
    )
    public_url = storage.get_public_url(gcs_path, settings.GCS_PUBLIC_BUCKET_NAME)
    await db.execute(
        update(Profile)
        .where(Profile.id == profile_id)
        .values(avatar_url=public_url)
    )
    await db.commit()
    return AvatarUploadResponse(avatar_url=public_url)


# -----------------------------------------------------------------------------
# Uploads a portfolio image or resume after validation, limits, and storage writes.
# -----------------------------------------------------------------------------
async def upload_media(
    profile_id: ProfileID,
    user_id: UserID,
    file_bytes: bytes,
    file_name: str,
    media_type: MediaType,
    db: AsyncSession,
) -> MediaUploadResponse:
    settings = get_settings()
    loop = asyncio.get_event_loop()
    safe_name = file_name.strip()

    if media_type == MediaType.IMAGE:
        await check_portfolio_limit(profile_id, user_id, db)
        processed_bytes = await loop.run_in_executor(
            None,
            image_processing.process_profile_image,
            file_bytes,
        )
        mime_type = "image/webp"
        gcs_path = storage.generate_upload_path(str(profile_id), "image", "webp")
        await storage.upload_file(
            processed_bytes,
            gcs_path,
            mime_type,
            settings.GCS_PUBLIC_BUCKET_NAME,
        )
        public_url = storage.get_public_url(gcs_path, settings.GCS_PUBLIC_BUCKET_NAME)

        max_stmt = select(func.coalesce(func.max(Media.display_order), -1)).where(
            Media.profile_id == profile_id,
            Media.media_type == MediaType.IMAGE,
            Media.deleted_at.is_(None),
        )
        max_result = await db.execute(max_stmt)
        next_order = int(max_result.scalar_one()) + 1

        media = Media(
            profile_id=profile_id,
            media_type=MediaType.IMAGE,
            file_name=safe_name,
            gcs_path=gcs_path,
            mime_type=mime_type,
            file_size=len(processed_bytes),
            display_order=next_order,
            is_public=True,
        )
        db.add(media)
        await db.flush()
        await db.commit()
        await db.refresh(media)

        return MediaUploadResponse(
            id=media.id,
            profile_id=media.profile_id,
            media_type=media.media_type,
            file_name=media.file_name,
            mime_type=media.mime_type,
            file_size=media.file_size,
            display_order=media.display_order,
            url=public_url,
            created_at=media.created_at,
            updated_at=media.updated_at,
        )

    if media_type == MediaType.RESUME:
        await check_resume_allowed(user_id, db)
        validated_mime = image_processing.validate_resume(file_bytes)
        ext = "pdf" if validated_mime == "application/pdf" else "docx"
        gcs_path = storage.generate_upload_path(str(profile_id), "resume", ext)

        existing_stmt = select(Media).where(
            Media.profile_id == profile_id,
            Media.media_type == MediaType.RESUME,
            Media.deleted_at.is_(None),
        )
        existing_result = await db.execute(existing_stmt)
        old_resume = existing_result.scalar_one_or_none()
        if old_resume is not None:
            await db.execute(
                update(Media)
                .where(Media.id == old_resume.id)
                .values(deleted_at=datetime.now(timezone.utc))
            )
            await db.flush()

        await storage.upload_file(
            file_bytes,
            gcs_path,
            validated_mime,
            settings.GCS_PRIVATE_BUCKET_NAME,
        )

        media = Media(
            profile_id=profile_id,
            media_type=MediaType.RESUME,
            file_name=safe_name,
            gcs_path=gcs_path,
            mime_type=validated_mime,
            file_size=len(file_bytes),
            display_order=None,
            is_public=False,
        )
        db.add(media)
        await db.flush()
        await db.commit()
        await db.refresh(media)

        signed_url = await storage.get_signed_url(
            gcs_path,
            settings.GCS_PRIVATE_BUCKET_NAME,
            expiry_minutes=SIGNED_URL_EXPIRY_MINUTES,
        )

        return MediaUploadResponse(
            id=media.id,
            profile_id=media.profile_id,
            media_type=media.media_type,
            file_name=media.file_name,
            mime_type=media.mime_type,
            file_size=media.file_size,
            display_order=media.display_order,
            url=signed_url,
            created_at=media.created_at,
            updated_at=media.updated_at,
        )

    raise ValidationError(f"Unsupported media_type for upload: {media_type!r}")


# -----------------------------------------------------------------------------
# Soft-deletes a media row by setting deleted_at.
# -----------------------------------------------------------------------------
async def soft_delete_media(
    media_id: MediaID,
    profile_id: ProfileID,
    db: AsyncSession,
) -> None:
    statement = select(Media).where(
        Media.id == media_id,
        Media.profile_id == profile_id,
        Media.deleted_at.is_(None),
    )
    result = await db.execute(statement)
    media = result.scalar_one_or_none()
    if media is None:
        raise NotFoundError(f"Media {media_id} not found.")

    await db.execute(
        update(Media)
        .where(Media.id == media_id)
        .values(deleted_at=datetime.now(timezone.utc))
    )
    await db.commit()


# -----------------------------------------------------------------------------
# Restores a soft-deleted media row within the grace period.
# -----------------------------------------------------------------------------
async def restore_media(
    media_id: MediaID,
    profile_id: ProfileID,
    db: AsyncSession,
) -> MediaInternal:
    statement = select(Media).where(
        Media.id == media_id,
        Media.profile_id == profile_id,
        Media.deleted_at.isnot(None),
    )
    result = await db.execute(statement)
    media = result.scalar_one_or_none()
    if media is None:
        raise NotFoundError(f"Media {media_id} not found.")

    grace_cutoff = datetime.now(timezone.utc) - timedelta(days=GRACE_PERIOD_DAYS)
    if media.deleted_at is not None and media.deleted_at < grace_cutoff:
        raise PermissionDeniedError("Grace period has expired.")

    await db.execute(
        update(Media)
        .where(Media.id == media_id)
        .values(
            deleted_at=None,
            restored_at=datetime.now(timezone.utc),
        )
    )
    await db.commit()

    stmt = select(Media).where(Media.id == media_id)
    res = await db.execute(stmt)
    refreshed = res.scalar_one_or_none()
    if refreshed is None:
        raise NotFoundError(f"Media {media_id} not found.")
    return MediaInternal.model_validate(refreshed)


# -----------------------------------------------------------------------------
# Soft-deletes all images and resume for a profile (subscription expiration).
# -----------------------------------------------------------------------------
async def soft_delete_excess_media(
    profile_id: ProfileID,
    db: AsyncSession,
) -> None:
    now = datetime.now(timezone.utc)
    await db.execute(
        update(Media)
        .where(
            Media.profile_id == profile_id,
            Media.media_type == MediaType.IMAGE,
            Media.deleted_at.is_(None),
        )
        .values(deleted_at=now)
    )
    await db.execute(
        update(Media)
        .where(
            Media.profile_id == profile_id,
            Media.media_type == MediaType.RESUME,
            Media.deleted_at.is_(None),
        )
        .values(deleted_at=now)
    )
    await db.commit()
