from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.domain.subscription.enums import SubscriptionPlan, SubscriptionStatus


class SubscriptionInternal(BaseModel):
    """Cross-domain DTO for subscription context passed via UserInternal."""

    plan: SubscriptionPlan
    status: SubscriptionStatus
    is_active: bool
    trial_end: datetime | None = None
    current_period_end: datetime | None = None
    grace_period_end: datetime | None = None
    entitlements: list[str] = []

    model_config = ConfigDict(from_attributes=True)

