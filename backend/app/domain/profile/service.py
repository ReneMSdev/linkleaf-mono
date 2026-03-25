"""Profile domain service — CRUD, slug handling, public view, soft delete.

All profile business logic lives in this module, with no FastAPI or HTTP concerns.
"""

from __future__ import annotations

import random
import re
import string
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, PermissionDeniedError, SlugMoved
from app.core.types import GRACE_PERIOD_DAYS, ProfileID, UserID
from app.domain.media.models import MediaType
from app.domain.profile.dto import (
    ContactPublic,
    LinkPublic,
    MediaPublic,
    ProfileCreate,
    ProfileInternal,
    ProfilePublic,
    ProfileUpdate,
    ThemePublic,
)
from app.domain.profile.models import Profile, SlugHistory
from app.domain.subscription.service import check_profile_limit

SLUG_MAX_BASE_LENGTH = 55
SLUG_SUFFIX_LENGTH = 4
SLUG_MAX_ATTEMPTS = 5


def _slugify(name: str) -> str:
    """Slugify name: lowercase, hyphens, truncate to 55 chars."""
    s = name.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s[:SLUG_MAX_BASE_LENGTH] if len(s) > SLUG_MAX_BASE_LENGTH else s


async def _slug_taken(slug: str, db: AsyncSession) -> bool:
    """Check if slug exists in profiles or slug_history."""
    stmt_profile = select(1).where(Profile.slug == slug)
    stmt_history = select(1).where(SlugHistory.old_slug == slug)
    result_p = await db.execute(stmt_profile)
    result_h = await db.execute(stmt_history)
    return result_p.scalar_one_or_none() is not None or result_h.scalar_one_or_none() is not None


# -----------------------------------------------------------------------------
# Generates a unique slug from name for new profiles.
# Called by create() before inserting a new profile.
# Returns unique slug string.
# Raises ConflictError after 5 failed attempts.
# -----------------------------------------------------------------------------
async def generate_slug(name: str, db: AsyncSession) -> str:
    base = _slugify(name)
    if not base:
        base = "profile"

    for _ in range(SLUG_MAX_ATTEMPTS):
        slug = base
        if await _slug_taken(slug, db):
            suffix = "".join(
                random.choices(string.ascii_lowercase + string.digits, k=SLUG_SUFFIX_LENGTH)
            )
            slug = f"{base}-{suffix}"

        if not await _slug_taken(slug, db):
            return slug

    raise ConflictError("Could not generate a unique slug. Please try again.")


# -----------------------------------------------------------------------------
# Fetches a profile by ID for the owning user.
# Called by update, set_default, soft_delete, restore to verify ownership.
# Returns ProfileInternal.
# Raises NotFoundError if not found.
# -----------------------------------------------------------------------------
async def get_by_id(
    profile_id: ProfileID,
    user_id: UserID,
    db: AsyncSession,
) -> ProfileInternal:
    statement = (
        select(Profile)
        .where(
            Profile.id == profile_id,
            Profile.user_id == user_id,
            Profile.deleted_at.is_(None),
        )
    )
    result = await db.execute(statement)
    profile = result.scalar_one_or_none()
    if profile is None:
        raise NotFoundError(f"Profile {profile_id} not found.")
    return ProfileInternal.model_validate(profile)


# -----------------------------------------------------------------------------
# Lists all active profiles for a user ordered by display_order.
# Called by API list endpoint.
# Returns list of ProfileInternal — empty list if none.
# -----------------------------------------------------------------------------
async def get_all(
    user_id: UserID,
    db: AsyncSession,
) -> list[ProfileInternal]:
    statement = (
        select(Profile)
        .where(Profile.user_id == user_id, Profile.deleted_at.is_(None))
        .order_by(Profile.display_order.asc())
    )
    result = await db.execute(statement)
    profiles = result.scalars().all()
    return [ProfileInternal.model_validate(p) for p in profiles]


# -----------------------------------------------------------------------------
# Fetches a public profile by slug for unauthenticated viewers.
# Called by GET /p/{slug}. Handles slug redirects via SlugHistory.
# Returns ProfilePublic with filtered links/media and computed has_sensitive_data.
# Raises SlugMoved when slug moved (API issues 301). Raises NotFoundError on miss.
# -----------------------------------------------------------------------------
async def get_public(
    slug: str,
    db: AsyncSession,
) -> ProfilePublic:
    statement = (
        select(Profile)
        .where(
            Profile.slug == slug,
            Profile.deleted_at.is_(None),
            Profile.is_active.is_(True),
        )
    )
    result = await db.execute(statement)
    profile = result.scalar_one_or_none()

    if profile is None:
        stmt_history = select(SlugHistory).where(SlugHistory.old_slug == slug)
        hist_result = await db.execute(stmt_history)
        hist = hist_result.scalar_one_or_none()
        if hist is not None:
            stmt_current = select(Profile.slug).where(
                Profile.id == hist.profile_id,
                Profile.deleted_at.is_(None),
            )
            curr_result = await db.execute(stmt_current)
            current_slug = curr_result.scalar_one_or_none()
            if current_slug is not None:
                raise SlugMoved(new_slug=current_slug)
        raise NotFoundError(f"Profile with slug '{slug}' not found.")

    filtered_links = [l for l in profile.links if l.is_active]
    filtered_media = [
        m for m in profile.media
        if m.deleted_at is None and m.is_public
    ]

    has_resume = any(m.media_type == MediaType.RESUME for m in filtered_media)
    contact = profile.contact
    has_sensitive_data = bool(
        has_resume
        or (
            contact
            and any(
                [
                    contact.phone,
                    contact.email,
                    contact.address_line_1,
                ]
            )
        )
    )

    theme_pub = ThemePublic.model_validate(profile.theme) if profile.theme else None
    links_pub = [LinkPublic.model_validate(l) for l in filtered_links]
    contact_pub = ContactPublic.model_validate(contact) if contact else None
    media_pub = [MediaPublic.model_validate(m) for m in filtered_media]

    return ProfilePublic(
        slug=profile.slug,
        name=profile.name,
        bio=profile.bio,
        avatar_url=profile.avatar_url,
        view_count=profile.view_count,
        has_sensitive_data=has_sensitive_data,
        theme=theme_pub,
        links=links_pub,
        contact=contact_pub,
        media=media_pub,
    )


# -----------------------------------------------------------------------------
# Increments view_count for a profile. Non-blocking, called as background task.
# Called from API layer for unauthenticated viewers only.
# Returns None.
# -----------------------------------------------------------------------------
async def increment_view_count(
    profile_id: ProfileID,
    db: AsyncSession,
) -> None:
    stmt = (
        update(Profile)
        .where(Profile.id == profile_id)
        .values(view_count=Profile.view_count + 1)
    )
    await db.execute(stmt)
    await db.commit()


# -----------------------------------------------------------------------------
# Creates a new profile for the user.
# Called by API POST /profiles. Enforces profile limit before create.
# Returns ProfileInternal.
# Raises PlanLimitError when limit exceeded. Raises ConflictError if slug gen fails.
# -----------------------------------------------------------------------------
async def create(
    user_id: UserID,
    dto: ProfileCreate,
    db: AsyncSession,
) -> ProfileInternal:
    await check_profile_limit(user_id, db)
    if dto.slug is not None:
        if await _slug_taken(dto.slug, db):
            raise ConflictError("Slug is already taken.")
        slug = dto.slug
    else:
        slug = await generate_slug(dto.name, db)

    count_stmt = (
        select(func.count())
        .select_from(Profile)
        .where(Profile.user_id == user_id, Profile.deleted_at.is_(None))
    )
    count_result = await db.execute(count_stmt)
    count = count_result.scalar_one()

    is_default = count == 0

    profile = Profile(
        user_id=user_id,
        slug=slug,
        name=dto.name.strip(),
        bio=dto.bio,
        theme_id=dto.theme_id,
        is_active=dto.is_active,
        display_order=dto.display_order,
        is_default=is_default,
    )
    db.add(profile)
    await db.flush()
    await db.commit()
    await db.refresh(profile)
    return ProfileInternal.model_validate(profile)


# -----------------------------------------------------------------------------
# Updates a profile. Handles slug change with SlugHistory for redirects.
# Called by API PATCH /profiles/{id}.
# Returns ProfileInternal.
# Raises NotFoundError, ConflictError if slug taken.
# -----------------------------------------------------------------------------
async def update_profile(
    profile_id: ProfileID,
    user_id: UserID,
    dto: ProfileUpdate,
    db: AsyncSession,
) -> ProfileInternal:
    statement = select(Profile).where(
        Profile.id == profile_id,
        Profile.user_id == user_id,
        Profile.deleted_at.is_(None),
    )
    result = await db.execute(statement)
    profile = result.scalar_one_or_none()
    if profile is None:
        raise NotFoundError(f"Profile {profile_id} not found.")

    if dto.slug is not None and dto.slug != profile.slug:
        stmt_taken_p = select(1).where(
            Profile.slug == dto.slug,
            Profile.id != profile_id,
        )
        stmt_taken_h = select(1).where(SlugHistory.old_slug == dto.slug)
        rp = await db.execute(stmt_taken_p)
        rh = await db.execute(stmt_taken_h)
        if rp.scalar_one_or_none() is not None or rh.scalar_one_or_none() is not None:
            raise ConflictError("Slug is already taken.")

        slug_history_entry = SlugHistory(
            profile_id=profile_id,
            old_slug=profile.slug,
        )
        db.add(slug_history_entry)
        profile.slug = dto.slug

    updates = dto.model_dump(exclude_unset=True, exclude={"slug"})
    for field_name, field_value in updates.items():
        setattr(profile, field_name, field_value)

    await db.commit()
    await db.refresh(profile)
    return ProfileInternal.model_validate(profile)


# -----------------------------------------------------------------------------
# Sets a profile as the user's default. Clears default on others first.
# Called by API POST /profiles/{id}/set-default.
# Returns ProfileInternal.
# Raises NotFoundError if profile not found.
# -----------------------------------------------------------------------------
async def set_default(
    profile_id: ProfileID,
    user_id: UserID,
    db: AsyncSession,
) -> ProfileInternal:
    await get_by_id(profile_id, user_id, db)

    await db.execute(
        update(Profile).where(Profile.user_id == user_id).values(is_default=False)
    )
    await db.execute(
        update(Profile).where(Profile.id == profile_id).values(is_default=True)
    )
    await db.commit()

    stmt = select(Profile).where(Profile.id == profile_id)
    res = await db.execute(stmt)
    profile = res.scalar_one_or_none()
    if profile is None:
        raise NotFoundError(f"Profile {profile_id} not found.")
    return ProfileInternal.model_validate(profile)


# -----------------------------------------------------------------------------
# Soft deletes a profile (sets deleted_at).
# Called by API DELETE /profiles/{id}.
# Returns None.
# Raises NotFoundError, PermissionDeniedError if default profile.
# -----------------------------------------------------------------------------
async def soft_delete(
    profile_id: ProfileID,
    user_id: UserID,
    db: AsyncSession,
) -> None:
    statement = select(Profile).where(
        Profile.id == profile_id,
        Profile.user_id == user_id,
        Profile.deleted_at.is_(None),
    )
    result = await db.execute(statement)
    profile = result.scalar_one_or_none()
    if profile is None:
        raise NotFoundError(f"Profile {profile_id} not found.")
    if profile.is_default:
        raise PermissionDeniedError("Cannot delete the default profile.")

    await db.execute(
        update(Profile)
        .where(Profile.id == profile_id)
        .values(deleted_at=datetime.now(timezone.utc))
    )
    await db.commit()


# -----------------------------------------------------------------------------
# Soft deletes all non-default profiles for a user.
# Called by webhook handler on subscription EXPIRATION.
# Returns None.
# -----------------------------------------------------------------------------
async def soft_delete_excess_profiles(
    user_id: UserID,
    db: AsyncSession,
) -> None:
    await db.execute(
        update(Profile)
        .where(
            Profile.user_id == user_id,
            Profile.deleted_at.is_(None),
            Profile.is_default.is_(False),
        )
        .values(deleted_at=datetime.now(timezone.utc))
    )
    await db.commit()


# -----------------------------------------------------------------------------
# Restores a soft-deleted profile within grace period.
# Called by API POST /profiles/{id}/restore.
# Returns ProfileInternal.
# Raises NotFoundError, PermissionDeniedError if outside grace period.
# -----------------------------------------------------------------------------
async def restore(
    profile_id: ProfileID,
    user_id: UserID,
    db: AsyncSession,
) -> ProfileInternal:
    statement = select(Profile).where(
        Profile.id == profile_id,
        Profile.user_id == user_id,
        Profile.deleted_at.isnot(None),
    )
    result = await db.execute(statement)
    profile = result.scalar_one_or_none()
    if profile is None:
        raise NotFoundError(f"Profile {profile_id} not found.")

    grace_cutoff = datetime.now(timezone.utc) - timedelta(days=GRACE_PERIOD_DAYS)
    if profile.deleted_at < grace_cutoff:
        raise PermissionDeniedError("Grace period has expired.")

    await db.execute(
        update(Profile)
        .where(Profile.id == profile_id)
        .values(
            deleted_at=None,
            restored_at=datetime.now(timezone.utc),
        )
    )
    await db.commit()

    # Re-fetch after update — previous ORM object is stale
    stmt = select(Profile).where(Profile.id == profile_id)
    res = await db.execute(stmt)
    profile = res.scalar_one_or_none()
    if profile is None:
        raise NotFoundError(f"Profile {profile_id} not found.")
    return ProfileInternal.model_validate(profile)
