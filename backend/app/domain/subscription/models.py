from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.base import Base, TimestampMixin
from app.core.types import SubscriptionID, UserID

if TYPE_CHECKING:
    from app.domain.user.models import User


class SubscriptionPlan(StrEnum):
    FREE = "free"
    PREMIUM = "premium"


class SubscriptionStatus(StrEnum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    TRIALING = "trialing"


class SubscriptionProvider(StrEnum):
    STRIPE = "stripe"
    APPLE = "apple"
    GOOGLE_PLAY = "google_play"


class Subscription(TimestampMixin, Base):
    """Tracks user plan, status, and billing data managed through RevenueCat."""

    __tablename__ = "subscriptions"

    id: Mapped[SubscriptionID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        server_default=text("uuid_generate_v4()"),
    )
    user_id: Mapped[UserID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    plan: Mapped[SubscriptionPlan] = mapped_column(
        SAEnum(SubscriptionPlan),
        nullable=False,
        server_default=text("'free'::subscriptionplan"),
    )
    status: Mapped[SubscriptionStatus] = mapped_column(
        SAEnum(SubscriptionStatus),
        nullable=False,
        server_default=text("'active'::subscriptionstatus"),
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )
    trial_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    current_period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    revenuecat_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider: Mapped[SubscriptionProvider | None] = mapped_column(
        SAEnum(SubscriptionProvider),
        nullable=True,
    )
    grace_period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    warning_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    user: Mapped[User] = relationship(
        "User",
        back_populates="subscription",
        lazy="selectin",
    )

