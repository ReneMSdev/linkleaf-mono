from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum as SAEnum, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.base import Base, TimestampMixin
from app.core.types import ThemeID

if TYPE_CHECKING:
    from app.domain.profile.models import Profile


class ThemeTier(StrEnum):
    FREE = "free"
    PREMIUM = "premium"


class Theme(TimestampMixin, Base):
    """System-seeded theme that controls public profile visual appearance."""

    __tablename__ = "themes"

    id: Mapped[ThemeID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        server_default=text("uuid_generate_v4()"),
    )
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(
        String(60),
        unique=True,
        nullable=False,
        index=True,
    )
    tier: Mapped[ThemeTier] = mapped_column(
        SAEnum(ThemeTier, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        server_default=text(f"'{ThemeTier.FREE.value}'::themetier"),
    )
    preview_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    config: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )
    is_featured: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )

    profiles: Mapped[list[Profile]] = relationship(
        "Profile",
        back_populates="theme",
        lazy="selectin",
    )

