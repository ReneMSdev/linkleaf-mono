from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.core.types import ContactID, ProfileID


class ContactBase(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    company: str | None = None
    job_title: str | None = None
    email: str | None = None
    phone: str | None = None
    whatsapp: str | None = None
    website: str | None = None
    address_line_1: str | None = None
    address_line_2: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    postal_code: str | None = None

    @field_validator("website")
    @classmethod
    def validate_website(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            if not v.startswith(("http://", "https://")):
                raise ValueError("Website must start with http:// or https://")
            if len(v) > 2048:
                raise ValueError("Website URL cannot exceed 2048 characters.")
        return v

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            if "@" not in v:
                raise ValueError("Invalid email address.")
            if len(v) > 255:
                raise ValueError("Email cannot exceed 255 characters.")
        return v


class ContactCreate(ContactBase):
    profile_id: ProfileID


class ContactUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    company: str | None = None
    job_title: str | None = None
    email: str | None = None
    phone: str | None = None
    whatsapp: str | None = None
    website: str | None = None
    address_line_1: str | None = None
    address_line_2: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    postal_code: str | None = None

    @field_validator("website")
    @classmethod
    def validate_website(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            if not v.startswith(("http://", "https://")):
                raise ValueError("Website must start with http:// or https://")
            if len(v) > 2048:
                raise ValueError("Website URL cannot exceed 2048 characters.")
        return v

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            if "@" not in v:
                raise ValueError("Invalid email address.")
            if len(v) > 255:
                raise ValueError("Email cannot exceed 255 characters.")
        return v


class ContactResponse(ContactBase):
    id: ContactID
    profile_id: ProfileID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ContactInternal(ContactBase):
    id: ContactID
    profile_id: ProfileID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
