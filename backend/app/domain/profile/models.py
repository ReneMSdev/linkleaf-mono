from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.base import Base, TimestampMixin
from app.core.types import ProfileID, ThemeID, UserID

if TYPE_CHECKING:
    from app.domain.contact.models import Contact
    from app.domain.link.models import Link
    from app.domain.media.models import Media
    from app.domain.theme.models import Theme
    from app.domain.user.models import User


class Profile(TimestampMixin, Base):
    """Public-facing identity profile that powers slug and QR-based sharing."""

    __tablename__ = "profiles"

    id: Mapped[ProfileID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        server_default=text("uuid_generate_v4()"),
    )
    user_id: Mapped[UserID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    slug: Mapped[str] = mapped_column(
        String(60),
        unique=True,
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    bio: Mapped[str | None] = mapped_column(String(500), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    qr_token: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        unique=True,
        nullable=False,
        index=True,
        server_default=text("uuid_generate_v4()"),
    )
    qr_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )
    theme_id: Mapped[ThemeID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("themes.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )
    display_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )
    view_count: Mapped[int] = mapped_column(
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

    user: Mapped[User] = relationship("User", back_populates="profiles")
    theme: Mapped[Theme | None] = relationship(
        "Theme",
        back_populates="profiles",
        lazy="selectin",
    )
    links: Mapped[list[Link]] = relationship(
        "Link",
        back_populates="profile",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    contact: Mapped[Contact | None] = relationship(
        "Contact",
        back_populates="profile",
        cascade="all, delete-orphan",
        uselist=False,
        lazy="selectin",
    )
    media: Mapped[list[Media]] = relationship(
        "Media",
        back_populates="profile",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

