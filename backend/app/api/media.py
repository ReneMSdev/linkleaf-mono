"""Media API routes — avatar, portfolio image, and resume uploads.

Thin route handlers only; domain logic lives in media/service.py.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.db.session import get_db
from app.core.exceptions import (
    NotFoundError,
    PermissionDeniedError,
    PlanLimitError,
    ValidationError,
)
from app.core.types import MediaID, ProfileID
from app.domain.media import service as media_service
from app.domain.media.dto import (
    AvatarUploadResponse,
    MediaInternal,
    MediaResponse,
    MediaUploadResponse,
)
from app.domain.media.models import MediaType
from app.domain.profile.models import Profile
from app.domain.user.dto import UserInternal

router = APIRouter(prefix="/media", tags=["media"])


async def _verify_profile_ownership(
    profile_id: ProfileID,
    user_id: UUID,
    db: AsyncSession,
) -> None:
    stmt = select(Profile).where(
        Profile.id == profile_id,
        Profile.user_id == user_id,
        Profile.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Profile not found.")


def _media_response_from_internal(item: MediaInternal, url: str) -> MediaResponse:
    data = item.model_dump(exclude={"gcs_path"})
    return MediaResponse(**data, url=url)


# -----------------------------------------------------------------------------
# Upload avatar image — processed server-side, stored on public bucket.
# -----------------------------------------------------------------------------
@router.post("/avatar/{profile_id}", response_model=AvatarUploadResponse)
async def upload_avatar(
    profile_id: ProfileID,
    file: UploadFile = File(...),
    current_user: UserInternal = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AvatarUploadResponse:
    await _verify_profile_ownership(profile_id, current_user.id, db)
    file_bytes = await file.read()
    try:
        return await media_service.upload_avatar(
            profile_id,
            file_bytes,
            file.filename or "",
            db,
        )
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e


# -----------------------------------------------------------------------------
# Upload portfolio image or resume — query param media_type (image | resume).
# -----------------------------------------------------------------------------
@router.post("/upload/{profile_id}", response_model=MediaUploadResponse)
async def upload_media(
    profile_id: ProfileID,
    media_type: MediaType,
    file: UploadFile = File(...),
    current_user: UserInternal = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MediaUploadResponse:
    await _verify_profile_ownership(profile_id, current_user.id, db)
    file_bytes = await file.read()
    try:
        return await media_service.upload_media(
            profile_id,
            current_user.id,
            file_bytes,
            file.filename or "",
            media_type,
            db,
        )
    except PlanLimitError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e


# -----------------------------------------------------------------------------
# List all active media for a profile with resolved URLs.
# -----------------------------------------------------------------------------
@router.get("/{profile_id}", response_model=list[MediaResponse])
async def list_media(
    profile_id: ProfileID,
    current_user: UserInternal = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[MediaResponse]:
    await _verify_profile_ownership(profile_id, current_user.id, db)
    media_list = await media_service.get_all(profile_id, db)
    responses: list[MediaResponse] = []
    for item in media_list:
        url = await media_service.get_url(item, db)
        responses.append(_media_response_from_internal(item, url))
    return responses


# -----------------------------------------------------------------------------
# Get one media item with resolved URL.
# -----------------------------------------------------------------------------
@router.get("/{profile_id}/{media_id}", response_model=MediaResponse)
async def get_media(
    profile_id: ProfileID,
    media_id: MediaID,
    current_user: UserInternal = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MediaResponse:
    await _verify_profile_ownership(profile_id, current_user.id, db)
    try:
        result = await media_service.get_by_id(media_id, profile_id, db)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    url = await media_service.get_url(result, db)
    return _media_response_from_internal(result, url)


# -----------------------------------------------------------------------------
# Soft-delete media within grace period flow.
# -----------------------------------------------------------------------------
@router.delete("/{profile_id}/{media_id}", status_code=204)
async def delete_media(
    profile_id: ProfileID,
    media_id: MediaID,
    current_user: UserInternal = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    await _verify_profile_ownership(profile_id, current_user.id, db)
    try:
        await media_service.soft_delete_media(media_id, profile_id, db)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return Response(status_code=204)


# -----------------------------------------------------------------------------
# Restore soft-deleted media within grace period.
# -----------------------------------------------------------------------------
@router.post("/{profile_id}/{media_id}/restore", response_model=MediaResponse)
async def restore_media(
    profile_id: ProfileID,
    media_id: MediaID,
    current_user: UserInternal = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MediaResponse:
    await _verify_profile_ownership(profile_id, current_user.id, db)
    try:
        result = await media_service.restore_media(media_id, profile_id, db)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    url = await media_service.get_url(result, db)
    return _media_response_from_internal(result, url)
