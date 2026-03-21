"""Data transfer objects for the user domain.

These DTOs define the data shapes that cross API, service, and cross-domain
boundaries for user-related operations.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.types import UserID

from app.domain.subscription.dto import SubscriptionInternal


class UserBase(BaseModel):
    """Shared user fields reused by internal and outbound user DTOs."""

    email: str = Field(max_length=255)
    display_name: str | None = Field(default=None, max_length=100)
    avatar_url: str | None = Field(default=None, max_length=1024)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_and_validate_email(cls, value: str) -> str:
        """Normalize email and enforce basic domain rule requirements."""
        normalized = value.strip().lower()
        if "@" not in normalized:
            raise ValueError("Email must contain '@'.")
        return normalized


class UserCreate(UserBase):
    """Internal inbound DTO for auto-provisioning a user after Firebase login."""

    firebase_uid: str = Field(max_length=128)
    is_verified: bool = False


class UserUpdate(BaseModel):
    """Inbound DTO for PATCH updates from the authenticated user boundary."""

    display_name: str | None = Field(default=None, max_length=100)
    avatar_url: str | None = Field(default=None, max_length=1024)


class UserResponse(UserBase):
    """Outbound DTO returned to authenticated API clients."""

    id: UserID
    is_active: bool
    is_verified: bool
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserInternal(UserBase):
    """Cross-domain DTO used for service-to-service user context transfer."""

    id: UserID
    firebase_uid: str
    is_active: bool
    is_verified: bool
    last_login_at: datetime | None
    subscription: SubscriptionInternal | None = None

    model_config = ConfigDict(from_attributes=True)


class UserPublic(BaseModel):
    """Minimal outbound DTO for public/connection-facing user display data."""

    display_name: str | None
    avatar_url: str | None

    model_config = ConfigDict(from_attributes=True)

UserInternal.model_rebuild()