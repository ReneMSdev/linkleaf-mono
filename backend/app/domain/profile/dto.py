"""Data transfer objects for the profile domain.

Nested public DTOs (ThemePublic, LinkPublic, ContactPublic, MediaPublic) are
defined here so ProfilePublic is self-contained and we avoid circular imports
between profile, theme, link, contact, and media domain DTOs.
"""

from __future__ import annotations

import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from app.core.types import (
    ContactID,
    LinkID,
    MediaID,
    ProfileID,
    RESERVED_SLUGS,
    ThemeID,
    UserID,
)

SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{1,58}[a-z0-9]$")


def _validate_slug(v: str) -> str:
    if not SLUG_PATTERN.match(v):
        raise ValueError(
            "Slug must be 3-60 characters, lowercase letters, numbers and "
            "hyphens only, cannot start or end with a hyphen."
        )
    if v in RESERVED_SLUGS:
        raise ValueError(f'"{v}" is a reserved slug and cannot be used.')
    return v


# -----------------------------------------------------------------------------
# Nested public DTOs — used by ProfilePublic for public profile page response
# -----------------------------------------------------------------------------

class ThemePublic(BaseModel):
    id: ThemeID
    name: str
    slug: str
    config: dict
    preview_url: str | None
    model_config = ConfigDict(from_attributes=True)


class LinkPublic(BaseModel):
    id: LinkID
    title: str
    url: str
    icon: str | None
    link_type: str
    display_order: int
    click_count: int
    model_config = ConfigDict(from_attributes=True)


class ContactPublic(BaseModel):
    id: ContactID
    first_name: str | None
    last_name: str | None
    company: str | None
    job_title: str | None
    email: str | None
    phone: str | None
    whatsapp: str | None
    website: str | None
    address_line_1: str | None
    address_line_2: str | None
    city: str | None
    state: str | None
    country: str | None
    postal_code: str | None
    model_config = ConfigDict(from_attributes=True)


class MediaPublic(BaseModel):
    id: MediaID
    media_type: str
    file_name: str
    mime_type: str
    file_size: int
    display_order: int | None
    url: str | None = None  # public URL for images — populated at service layer, never stored
    model_config = ConfigDict(from_attributes=True)


# -----------------------------------------------------------------------------
# Profile DTOs
# -----------------------------------------------------------------------------

class ProfileBase(BaseModel):
    name: str
    bio: str | None = None
    theme_id: ThemeID | None = None
    is_active: bool = True
    display_order: int = 0


class ProfileCreate(ProfileBase):
    slug: str | None = None  # optional — backend generates if not provided

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return _validate_slug(v)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be empty.")
        if len(v) > 100:
            raise ValueError("Name cannot exceed 100 characters.")
        return v

    @field_validator("bio")
    @classmethod
    def validate_bio(cls, v: str | None) -> str | None:
        if v is not None and len(v) > 500:
            raise ValueError("Bio cannot exceed 500 characters.")
        return v


class ProfileUpdate(BaseModel):
    slug: str | None = None
    name: str | None = None
    bio: str | None = None
    theme_id: ThemeID | None = None
    is_active: bool | None = None
    display_order: int | None = None

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return _validate_slug(v)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be empty.")
        if len(v) > 100:
            raise ValueError("Name cannot exceed 100 characters.")
        return v

    @field_validator("bio")
    @classmethod
    def validate_bio(cls, v: str | None) -> str | None:
        if v is not None and len(v) > 500:
            raise ValueError("Bio cannot exceed 500 characters.")
        return v


class ProfileResponse(ProfileBase):
    id: ProfileID
    user_id: UserID
    slug: str
    qr_token: UUID
    qr_active: bool
    is_default: bool
    view_count: int
    deleted_at: datetime | None
    restored_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProfilePublic(BaseModel):
    slug: str
    name: str
    bio: str | None
    avatar_url: str | None
    view_count: int
    has_sensitive_data: bool = False
    is_premium: bool = False  # controls branding display on public page
    theme: ThemePublic | None
    links: list[LinkPublic]
    contact: ContactPublic | None
    media: list[MediaPublic]

    model_config = ConfigDict(from_attributes=True)


class ProfileInternal(ProfileBase):
    id: ProfileID
    user_id: UserID
    slug: str
    qr_token: UUID
    qr_active: bool
    is_default: bool
    is_active: bool
    display_order: int
    view_count: int
    deleted_at: datetime | None
    restored_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
