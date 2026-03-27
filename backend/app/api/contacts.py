"""Contact API routes — authenticated contact CRUD and public vCard download.

Thin route handlers only; domain logic lives in contact/service.py.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.db.session import get_db
from app.core.exceptions import NotFoundError
from app.core.types import ProfileID
from app.domain.contact import service as contact_service
from app.domain.contact.dto import ContactCreate, ContactResponse
from app.domain.profile.models import Profile
from app.domain.user.dto import UserInternal

# Public endpoints — no auth
public_router = APIRouter(tags=["contacts"])

# Authenticated endpoints
router = APIRouter(prefix="/contacts", tags=["contacts"])


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


# -----------------------------------------------------------------------------
# Public vCard download endpoint for a profile.
# Returns a .vcf attachment named from profile slug.
# -----------------------------------------------------------------------------
@public_router.get("/contacts/{profile_id}/vcard")
async def download_vcard(
    profile_id: ProfileID,
    db: AsyncSession = Depends(get_db),
) -> Response:
    try:
        vcard_string = await contact_service.generate_vcard(profile_id, db)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    stmt = select(Profile.slug).where(
        Profile.id == profile_id,
        Profile.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    slug = result.scalar_one_or_none()
    if slug is None:
        raise HTTPException(status_code=404, detail="Profile not found.")

    return Response(
        content=vcard_string,
        media_type="text/vcard",
        headers={"Content-Disposition": f'attachment; filename="{slug}.vcf"'},
    )


# -----------------------------------------------------------------------------
# Fetches contact for an owned profile.
# -----------------------------------------------------------------------------
@router.get("/{profile_id}", response_model=ContactResponse)
async def get_contact(
    profile_id: ProfileID,
    current_user: UserInternal = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ContactResponse:
    await _verify_profile_ownership(profile_id, current_user.id, db)
    result = await contact_service.get_by_profile_id(profile_id, db)
    if result is None:
        raise HTTPException(status_code=404, detail="Contact not found.")
    return ContactResponse.model_validate(result)


# -----------------------------------------------------------------------------
# Creates or updates contact for an owned profile.
# -----------------------------------------------------------------------------
@router.post("", response_model=ContactResponse)
async def upsert_contact(
    dto: ContactCreate,
    current_user: UserInternal = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ContactResponse:
    await _verify_profile_ownership(dto.profile_id, current_user.id, db)
    result = await contact_service.upsert(dto, db)
    return ContactResponse.model_validate(result)


# -----------------------------------------------------------------------------
# Hard deletes contact for an owned profile.
# -----------------------------------------------------------------------------
@router.delete("/{profile_id}", status_code=204)
async def delete_contact(
    profile_id: ProfileID,
    current_user: UserInternal = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    await _verify_profile_ownership(profile_id, current_user.id, db)
    try:
        await contact_service.delete_contact(profile_id, db)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return Response(status_code=204)
