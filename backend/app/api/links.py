"""Link API routes — profile-scoped link CRUD, reorder, and public click tracking.

Thin route handlers only; domain logic lives in link/service.py.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, get_optional_user
from app.core.db.session import AsyncSessionLocal, get_db
from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.core.types import LinkID, ProfileID
from app.domain.link import service as link_service
from app.domain.link.dto import LinkCreate, LinkResponse, LinkUpdate
from app.domain.link.models import Link
from app.domain.profile.models import Profile
from app.domain.user.dto import UserInternal

router = APIRouter(prefix="/links", tags=["links"])


async def _increment_click_count_background(link_id: LinkID) -> None:
    """Opens its own session for background click count increment."""
    db = AsyncSessionLocal()
    try:
        await link_service.increment_click_count(link_id, db)
    finally:
        await db.close()


async def _get_link_with_ownership(
    link_id: LinkID,
    user_id: UUID,
    db: AsyncSession,
) -> Link:
    """Fetch link and verify profile ownership in one JOIN query.

    Raises HTTPException(404) if link not found or profile not owned by user.
    """
    stmt = (
        select(Link)
        .join(Profile, Profile.id == Link.profile_id)
        .where(
            Link.id == link_id,
            Profile.user_id == user_id,
            Profile.deleted_at.is_(None),
        )
    )
    result = await db.execute(stmt)
    link = result.scalar_one_or_none()
    if link is None:
        raise HTTPException(status_code=404, detail="Link not found.")
    return link


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


class ReorderRequest(BaseModel):
    profile_id: ProfileID
    link_ids: list[LinkID]


# -----------------------------------------------------------------------------
# List links for a profile — owner only.
# -----------------------------------------------------------------------------
@router.get("", response_model=list[LinkResponse])
async def list_links(
    profile_id: ProfileID,
    current_user: UserInternal = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[LinkResponse]:
    await _verify_profile_ownership(profile_id, current_user.id, db)
    links = await link_service.get_all(profile_id, db)
    return [LinkResponse.model_validate(l) for l in links]


# -----------------------------------------------------------------------------
# Create a link under an owned profile.
# -----------------------------------------------------------------------------
@router.post("", response_model=LinkResponse, status_code=201)
async def create_link(
    dto: LinkCreate,
    current_user: UserInternal = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LinkResponse:
    await _verify_profile_ownership(dto.profile_id, current_user.id, db)
    result = await link_service.create(dto, db)
    return LinkResponse.model_validate(result)


# -----------------------------------------------------------------------------
# Get a single link — owner only.
# -----------------------------------------------------------------------------
@router.get("/{link_id}", response_model=LinkResponse)
async def get_link(
    link_id: LinkID,
    current_user: UserInternal = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LinkResponse:
    link = await _get_link_with_ownership(link_id, current_user.id, db)
    return LinkResponse.model_validate(link)


# -----------------------------------------------------------------------------
# Partial update — owner only.
# -----------------------------------------------------------------------------
@router.patch("/{link_id}", response_model=LinkResponse)
async def update_link(
    link_id: LinkID,
    dto: LinkUpdate,
    current_user: UserInternal = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LinkResponse:
    link = await _get_link_with_ownership(link_id, current_user.id, db)
    try:
        updated = await link_service.update_link(link_id, link.profile_id, dto, db)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return LinkResponse.model_validate(updated)


# -----------------------------------------------------------------------------
# Delete a link — owner only.
# -----------------------------------------------------------------------------
@router.delete("/{link_id}", status_code=204)
async def delete_link(
    link_id: LinkID,
    current_user: UserInternal = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    link = await _get_link_with_ownership(link_id, current_user.id, db)
    try:
        await link_service.delete_link(link_id, link.profile_id, db)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return Response(status_code=204)


# -----------------------------------------------------------------------------
# Reorder links — static /reorder path before POST /{link_id}/click.
# -----------------------------------------------------------------------------
@router.post("/reorder", response_model=list[LinkResponse])
async def reorder_links(
    body: ReorderRequest,
    current_user: UserInternal = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[LinkResponse]:
    await _verify_profile_ownership(body.profile_id, current_user.id, db)
    try:
        result = await link_service.reorder(body.profile_id, body.link_ids, db)
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    return [LinkResponse.model_validate(l) for l in result]


# -----------------------------------------------------------------------------
# Record a public link tap — increments click count unless the viewer is the owner.
# -----------------------------------------------------------------------------
@router.post("/{link_id}/click", status_code=204)
async def record_link_click(
    link_id: LinkID,
    background_tasks: BackgroundTasks,
    current_user: UserInternal | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    stmt = (
        select(Link, Profile.user_id)
        .join(Profile, Profile.id == Link.profile_id)
        .where(
            Link.id == link_id,
            Profile.deleted_at.is_(None),
        )
    )
    result = await db.execute(stmt)
    row = result.first()
    if row is None:
        raise HTTPException(status_code=404, detail="Link not found.")
    link, profile_user_id = row

    if current_user is not None and current_user.id == profile_user_id:
        return Response(status_code=204)

    background_tasks.add_task(_increment_click_count_background, link_id)
    return Response(status_code=204)
