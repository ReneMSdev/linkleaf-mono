from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum as SAEnum, ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.base import Base, TimestampMixin
from app.core.types import LinkID, ProfileID

if TYPE_CHECKING:
    from app.domain.profile.models import Profile


class LinkType(StrEnum):
    SOCIAL = "social"
    PORTFOLIO = "portfolio"
    CUSTOM = "custom"


class Link(TimestampMixin, Base):
    """External URLs shown on public profile pages, typed and display-ordered."""

    __tablename__ = "links"

    id: Mapped[LinkID] = mapped_column(
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
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    icon: Mapped[str | None] = mapped_column(String(100), nullable=True)
    link_type: Mapped[LinkType] = mapped_column(
        SAEnum(LinkType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        server_default=text("'custom'::linktype"),
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )
    display_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )
    click_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )

    profile: Mapped[Profile] = relationship(
        "Profile",
        back_populates="links",
        lazy="selectin",
    )

