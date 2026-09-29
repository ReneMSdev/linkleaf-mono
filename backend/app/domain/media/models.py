from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.base import Base, TimestampMixin
from app.core.types import MediaID, ProfileID

if TYPE_CHECKING:
    from app.domain.profile.models import Profile


class MediaType(StrEnum):
    IMAGE = "image"
    RESUME = "resume"


class Media(TimestampMixin, Base):
    """Metadata for uploaded profile files stored in GCS.

    This table stores only file metadata and GCS object paths for images
    and resumes. `deleted_at` and `restored_at` support the
    premium soft-delete grace period flow.
    """

    __tablename__ = "media"

    id: Mapped[MediaID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        server_default=text("uuid_generate_v4()"),
    )
    profile_id: Mapped[ProfileID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    media_type: Mapped[MediaType] = mapped_column(
        SAEnum(MediaType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    gcs_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(127), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    display_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_public: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )
    click_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    restored_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    profile: Mapped[Profile] = relationship(
        "Profile",
        back_populates="media",
        lazy="selectin",
    )

