from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.core.types import LinkID, ProfileID
from app.domain.link.models import LinkType


class LinkBase(BaseModel):
    title: str
    url: str
    icon: str | None = None
    link_type: LinkType = LinkType.CUSTOM
    is_active: bool = True

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Title cannot be empty.")
        if len(v) > 100:
            raise ValueError("Title cannot exceed 100 characters.")
        return v

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("URL cannot be empty.")
        if len(v) > 2048:
            raise ValueError("URL cannot exceed 2048 characters.")
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v

    @field_validator("icon")
    @classmethod
    def validate_icon(cls, v: str | None) -> str | None:
        if v is not None and len(v) > 100:
            raise ValueError("Icon cannot exceed 100 characters.")
        return v


class LinkCreate(LinkBase):
    profile_id: ProfileID


class LinkUpdate(BaseModel):
    title: str | None = None
    url: str | None = None
    icon: str | None = None
    link_type: LinkType | None = None
    is_active: bool | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if not v:
            raise ValueError("Title cannot be empty.")
        if len(v) > 100:
            raise ValueError("Title cannot exceed 100 characters.")
        return v

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if not v:
            raise ValueError("URL cannot be empty.")
        if len(v) > 2048:
            raise ValueError("URL cannot exceed 2048 characters.")
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v

    @field_validator("icon")
    @classmethod
    def validate_icon(cls, v: str | None) -> str | None:
        if v is not None and len(v) > 100:
            raise ValueError("Icon cannot exceed 100 characters.")
        return v


class LinkResponse(LinkBase):
    id: LinkID
    profile_id: ProfileID
    display_order: int
    click_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LinkInternal(LinkBase):
    id: LinkID
    profile_id: ProfileID
    display_order: int
    click_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
