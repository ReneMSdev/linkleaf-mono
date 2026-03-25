"""Profile API routes — public QR/slug endpoints and authenticated CRUD.

Thin route handlers only; domain logic lives in profile/service.py.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, get_optional_user
from app.core.db.session import AsyncSessionLocal, get_db
from app.core.exceptions import (
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    PlanLimitError,
    SlugMoved,
)
from app.core.types import ProfileID
from app.domain.profile import service as profile_service
from app.domain.profile.dto import (
    ProfileCreate,
    ProfilePublic,
    ProfileResponse,
    ProfileUpdate,
)
from app.domain.profile.models import Profile
from app.domain.user.dto import UserInternal

# Public endpoints — no auth, no prefix
public_router = APIRouter(tags=["profiles"])

# Authenticated endpoints (mounted under /v1)
router = APIRouter(prefix="/profiles", tags=["profiles"])


# -----------------------------------------------------------------------------
# QR scan redirect — public, no auth. 302 to current profile slug path.
# -----------------------------------------------------------------------------
@public_router.get("/q/{qr_token}", tags=["qr"])
async def qr_redirect(
    qr_token: UUID,
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    stmt = select(Profile).where(
        Profile.qr_token == qr_token,
        Profile.qr_active.is_(True),
        Profile.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found.")
    return RedirectResponse(url=f"/p/{profile.slug}", status_code=302)


# -----------------------------------------------------------------------------
# Public profile page payload — optional auth; 301 if slug moved; view count for non-owners.
# -----------------------------------------------------------------------------
@public_router.get("/p/{slug}", response_model=ProfilePublic)
async def get_public_profile(
    slug: str,
    background_tasks: BackgroundTasks,
    current_user: UserInternal | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
) -> ProfilePublic:
    try:
        profile_public = await profile_service.get_public(slug, db)
    except SlugMoved as e:
        return RedirectResponse(url=f"/p/{e.new_slug}", status_code=301)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    stmt = select(Profile.id, Profile.user_id).where(
        Profile.slug == slug,
        Profile.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    row = result.first()
    if row is not None and (
        current_user is None or current_user.id != row[1]
    ):
        background_tasks.add_task(_increment_view_count_background, row[0])

    return profile_public


# -----------------------------------------------------------------------------
# List profiles for the authenticated user.
# -----------------------------------------------------------------------------
@router.get("", response_model=list[ProfileResponse])
async def list_profiles(
    current_user: UserInternal = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ProfileResponse]:
    profiles = await profile_service.get_all(current_user.id, db)
    return [ProfileResponse.model_validate(p) for p in profiles]


# -----------------------------------------------------------------------------
# Create profile — enforces plan limits and slug rules.
# -----------------------------------------------------------------------------
@router.post("", response_model=ProfileResponse, status_code=201)
async def create_profile(
    dto: ProfileCreate,
    current_user: UserInternal = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileResponse:
    try:
        result = await profile_service.create(current_user.id, dto, db)
    except PlanLimitError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    return ProfileResponse.model_validate(result)


# -----------------------------------------------------------------------------
# Get one profile by id — owner only.
# -----------------------------------------------------------------------------
@router.get("/{profile_id}", response_model=ProfileResponse)
async def get_profile(
    profile_id: ProfileID,
    current_user: UserInternal = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileResponse:
    try:
        result = await profile_service.get_by_id(profile_id, current_user.id, db)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return ProfileResponse.model_validate(result)


# -----------------------------------------------------------------------------
# Partial update — owner only; slug changes recorded in slug_history.
# -----------------------------------------------------------------------------
@router.patch("/{profile_id}", response_model=ProfileResponse)
async def update_profile(
    profile_id: ProfileID,
    dto: ProfileUpdate,
    current_user: UserInternal = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileResponse:
    try:
        result = await profile_service.update_profile(profile_id, current_user.id, dto, db)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    return ProfileResponse.model_validate(result)


# -----------------------------------------------------------------------------
# Soft delete — not allowed for default profile.
# -----------------------------------------------------------------------------
@router.delete("/{profile_id}", status_code=204)
async def delete_profile(
    profile_id: ProfileID,
    current_user: UserInternal = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    try:
        await profile_service.soft_delete(profile_id, current_user.id, db)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    return Response(status_code=204)


# -----------------------------------------------------------------------------
# Mark profile as default for the user.
# -----------------------------------------------------------------------------
@router.post("/{profile_id}/set-default", response_model=ProfileResponse)
async def set_default_profile(
    profile_id: ProfileID,
    current_user: UserInternal = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileResponse:
    try:
        result = await profile_service.set_default(profile_id, current_user.id, db)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return ProfileResponse.model_validate(result)


# -----------------------------------------------------------------------------
# Restore soft-deleted profile within grace period.
# -----------------------------------------------------------------------------
@router.post("/{profile_id}/restore", response_model=ProfileResponse)
async def restore_profile(
    profile_id: ProfileID,
    current_user: UserInternal = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileResponse:
    try:
        result = await profile_service.restore(profile_id, current_user.id, db)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    return ProfileResponse.model_validate(result)


async def _increment_view_count_background(profile_id: ProfileID) -> None:
    """Opens its own session for background view count increment."""
    db = AsyncSessionLocal()
    try:
        await profile_service.increment_view_count(profile_id, db)
    finally:
        await db.close()
