from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.core.exceptions import NotFoundError
from app.core.types import ProfileID
from app.domain.contact.dto import ContactCreate, ContactInternal, ContactUpdate
from app.domain.contact.models import Contact
from app.domain.profile.models import Profile
from app.domain.subscription.service import get_subscription


# -----------------------------------------------------------------------------
# Fetches optional contact card for a profile.
# Returns None when there is no contact record.
# -----------------------------------------------------------------------------
async def get_by_profile_id(
    profile_id: ProfileID,
    db: AsyncSession,
) -> ContactInternal | None:
    statement = select(Contact).where(Contact.profile_id == profile_id)
    result = await db.execute(statement)
    contact = result.scalar_one_or_none()
    if contact is None:
        return None
    return ContactInternal.model_validate(contact)


# -----------------------------------------------------------------------------
# Creates or updates contact data for a profile in one upsert-like operation.
# Existing rows are fully overwritten field-by-field, including explicit nulls.
# -----------------------------------------------------------------------------
async def upsert(
    dto: ContactCreate,
    db: AsyncSession,
) -> ContactInternal:
    statement = select(Contact).where(Contact.profile_id == dto.profile_id)
    result = await db.execute(statement)
    contact = result.scalar_one_or_none()

    payload = dto.model_dump(exclude={"profile_id"}, exclude_none=False)

    if contact is not None:
        for field_name, field_value in payload.items():
            setattr(contact, field_name, field_value)
        await db.commit()
        await db.refresh(contact)
        return ContactInternal.model_validate(contact)

    contact = Contact(profile_id=dto.profile_id, **payload)
    db.add(contact)
    await db.flush()
    await db.commit()
    await db.refresh(contact)
    return ContactInternal.model_validate(contact)


# -----------------------------------------------------------------------------
# Hard deletes the contact row for a profile.
# Raises NotFoundError when no contact exists for the profile.
# -----------------------------------------------------------------------------
async def delete_contact(
    profile_id: ProfileID,
    db: AsyncSession,
) -> None:
    statement = select(Contact).where(Contact.profile_id == profile_id)
    result = await db.execute(statement)
    contact = result.scalar_one_or_none()
    if contact is None:
        raise NotFoundError(f"Contact for profile {profile_id} not found.")

    await db.execute(delete(Contact).where(Contact.profile_id == profile_id))
    await db.commit()


# -----------------------------------------------------------------------------
# Builds a vCard 3.0 string for contact download with plan-based branding.
# Free users include branding note; premium users omit branding line.
# -----------------------------------------------------------------------------
async def generate_vcard(
    profile_id: ProfileID,
    db: AsyncSession,
) -> str:
    settings = get_settings()
    contact = await get_by_profile_id(profile_id, db)
    if contact is None:
        raise NotFoundError(f"Contact for profile {profile_id} not found.")

    statement = select(Profile).where(
        Profile.id == profile_id,
        Profile.deleted_at.is_(None),
    )
    result = await db.execute(statement)
    profile = result.scalar_one_or_none()
    if profile is None:
        raise NotFoundError(f"Profile {profile_id} not found.")

    subscription = await get_subscription(profile.user_id, db)
    is_premium = "premium" in subscription.entitlements

    lines: list[str] = []
    lines.append("BEGIN:VCARD")
    lines.append("VERSION:3.0")

    full_name = " ".join(filter(None, [contact.first_name, contact.last_name]))
    if full_name:
        lines.append(f"FN:{full_name}")

    n_last = contact.last_name or ""
    n_first = contact.first_name or ""
    lines.append(f"N:{n_last};{n_first};;;")

    if contact.company:
        lines.append(f"ORG:{contact.company}")

    if contact.job_title:
        lines.append(f"TITLE:{contact.job_title}")

    if contact.email:
        lines.append(f"EMAIL;TYPE=INTERNET:{contact.email}")

    if contact.phone:
        lines.append(f"TEL;TYPE=CELL:{contact.phone}")

    if contact.whatsapp:
        lines.append(f"TEL;TYPE=CELL;X-SERVICE=WhatsApp:{contact.whatsapp}")

    address_parts = [
        "",
        "",
        contact.address_line_1 or "",
        contact.city or "",
        contact.state or "",
        contact.postal_code or "",
        contact.country or "",
    ]
    if any([contact.address_line_1, contact.city, contact.state, contact.country]):
        lines.append(f"ADR;TYPE=WORK:{';'.join(address_parts)}")

    lines.append(f"URL:{settings.PUBLIC_BASE_URL}/p/{profile.slug}")

    if not is_premium:
        lines.append(f"NOTE:{settings.VCARD_BRANDING_NOTE}")

    lines.append("END:VCARD")

    return "\r\n".join(lines) + "\r\n"
