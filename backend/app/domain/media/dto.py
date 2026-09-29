from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.core.types import MediaID, ProfileID
from app.domain.media.models import MediaType


class MediaBase(BaseModel):
    profile_id: ProfileID
    media_type: MediaType
    file_name: str
    mime_type: str
    file_size: int
    display_order: int | None = None
    is_public: bool = True

    @field_validator("file_name")
    @classmethod
    def validate_file_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("File name cannot be empty.")
        if len(v) > 255:
            raise ValueError("File name cannot exceed 255 characters.")
        return v


class MediaResponse(BaseModel):
    id: MediaID
    profile_id: ProfileID
    media_type: MediaType
    file_name: str
    mime_type: str
    file_size: int
    display_order: int | None
    is_public: bool
    click_count: int
    url: str | None = None  # populated at service layer — never stored
    deleted_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MediaInternal(BaseModel):
    id: MediaID
    profile_id: ProfileID
    media_type: MediaType
    file_name: str
    gcs_path: str  # internal only — never exposed to API clients
    mime_type: str
    file_size: int
    display_order: int | None
    is_public: bool
    click_count: int
    deleted_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AvatarUploadResponse(BaseModel):
    avatar_url: str  # public GCS URL — stored on profile.avatar_url


class MediaUploadResponse(BaseModel):
    id: MediaID
    profile_id: ProfileID
    media_type: MediaType
    file_name: str
    mime_type: str
    file_size: int
    display_order: int | None
    url: str  # public URL for images, signed URL for resume
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
