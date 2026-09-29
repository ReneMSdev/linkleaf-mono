from __future__ import annotations

from sqlalchemy import case, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.core.types import LinkID, ProfileID
from app.domain.link.dto import LinkCreate, LinkInternal, LinkUpdate
from app.domain.link.models import Link


# -----------------------------------------------------------------------------
# Lists all links for a profile ordered by display_order (includes inactive).
# Owner sees every link; returns empty list when there are none.
# -----------------------------------------------------------------------------
async def get_all(
    profile_id: ProfileID,
    db: AsyncSession,
) -> list[LinkInternal]:
    statement = (
        select(Link)
        .where(Link.profile_id == profile_id)
        .order_by(Link.display_order.asc())
    )
    result = await db.execute(statement)
    links = result.scalars().all()
    return [LinkInternal.model_validate(link) for link in links]


# -----------------------------------------------------------------------------
# Fetches a single link scoped to the given profile.
# Raises NotFoundError when missing or wrong profile.
# -----------------------------------------------------------------------------
async def get_by_id(
    link_id: LinkID,
    profile_id: ProfileID,
    db: AsyncSession,
) -> LinkInternal:
    statement = select(Link).where(
        Link.id == link_id,
        Link.profile_id == profile_id,
    )
    result = await db.execute(statement)
    link = result.scalar_one_or_none()
    if link is None:
        raise NotFoundError(f"Link {link_id} not found.")
    return LinkInternal.model_validate(link)


# -----------------------------------------------------------------------------
# Creates a link with display_order appended after the current max for the profile.
# First link uses display_order 0.
# -----------------------------------------------------------------------------
async def create(
    dto: LinkCreate,
    db: AsyncSession,
) -> LinkInternal:
    max_stmt = select(func.coalesce(func.max(Link.display_order), -1)).where(
        Link.profile_id == dto.profile_id
    )
    max_result = await db.execute(max_stmt)
    next_order = int(max_result.scalar_one()) + 1

    link = Link(
        profile_id=dto.profile_id,
        title=dto.title,
        url=dto.url,
        icon=dto.icon,
        link_type=dto.link_type,
        is_active=dto.is_active,
        display_order=next_order,
    )
    db.add(link)
    await db.flush()
    await db.commit()
    await db.refresh(link)
    return LinkInternal.model_validate(link)


# -----------------------------------------------------------------------------
# Partially updates a link belonging to the profile.
# Raises NotFoundError if the link does not exist for this profile.
# -----------------------------------------------------------------------------
async def update_link(
    link_id: LinkID,
    profile_id: ProfileID,
    dto: LinkUpdate,
    db: AsyncSession,
) -> LinkInternal:
    statement = select(Link).where(
        Link.id == link_id,
        Link.profile_id == profile_id,
    )
    result = await db.execute(statement)
    link = result.scalar_one_or_none()
    if link is None:
        raise NotFoundError(f"Link {link_id} not found.")

    updates = dto.model_dump(exclude_unset=True)
    for field_name, field_value in updates.items():
        setattr(link, field_name, field_value)

    await db.commit()
    await db.refresh(link)
    return LinkInternal.model_validate(link)


# -----------------------------------------------------------------------------
# Reorders links by assigning display_order from each id's index in link_ids.
# Raises PermissionDeniedError if any id does not belong to the profile.
# -----------------------------------------------------------------------------
async def reorder(
    profile_id: ProfileID,
    link_ids: list[LinkID],
    db: AsyncSession,
) -> list[LinkInternal]:
    stmt_ids = select(Link.id).where(Link.profile_id == profile_id)
    result = await db.execute(stmt_ids)
    allowed = {row[0] for row in result.all()}

    for lid in link_ids:
        if lid not in allowed:
            raise PermissionDeniedError(
                "One or more links do not belong to this profile."
            )

    await db.execute(
        update(Link)
        .where(
            Link.profile_id == profile_id,
            Link.id.in_(link_ids),
        )
        .values(
            display_order=case(
                {lid: index for index, lid in enumerate(link_ids)},
                value=Link.id,
            )
        )
    )
    await db.commit()

    return await get_all(profile_id, db)


# -----------------------------------------------------------------------------
# Permanently deletes a link row for the given profile.
# Raises NotFoundError if missing or not owned by this profile.
# -----------------------------------------------------------------------------
async def delete_link(
    link_id: LinkID,
    profile_id: ProfileID,
    db: AsyncSession,
) -> None:
    statement = select(Link).where(
        Link.id == link_id,
        Link.profile_id == profile_id,
    )
    result = await db.execute(statement)
    link = result.scalar_one_or_none()
    if link is None:
        raise NotFoundError(f"Link {link_id} not found.")

    await db.execute(delete(Link).where(Link.id == link_id))
    await db.commit()


# -----------------------------------------------------------------------------
# Increments click_count by one for analytics (typically from a background task).
# -----------------------------------------------------------------------------
async def increment_click_count(
    link_id: LinkID,
    db: AsyncSession,
) -> None:
    await db.execute(
        update(Link)
        .where(Link.id == link_id)
        .values(click_count=Link.click_count + 1)
    )
    await db.commit()
