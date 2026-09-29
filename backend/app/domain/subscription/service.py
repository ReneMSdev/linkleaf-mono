"""Subscription domain service — plan limit enforcement and webhook updates.

Pure business rule enforcement — no FastAPI imports, no HTTP concerns.
"""

from __future__ import annotations

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, PlanLimitError
from app.core.types import ProfileID, UserID
from app.domain.media.models import Media, MediaType
from app.domain.profile.models import Profile
from app.domain.subscription.dto import SubscriptionInternal
from app.domain.subscription.enums import SubscriptionPlan, SubscriptionStatus
from app.domain.subscription.models import Subscription

FREE_PROFILE_LIMIT = 1
PREMIUM_PROFILE_LIMIT = 5
PREMIUM_PORTFOLIO_LIMIT = 100


# -----------------------------------------------------------------------------
# Fetches the subscription for a user.
# Called by check_profile_limit, check_portfolio_limit, check_resume_allowed, and webhook handlers.
# Returns SubscriptionInternal.
# Raises NotFoundError if subscription does not exist.
# -----------------------------------------------------------------------------
async def get_subscription(
    user_id: UserID,
    db: AsyncSession,
) -> SubscriptionInternal:
    statement = select(Subscription).where(Subscription.user_id == user_id)
    result = await db.execute(statement)
    subscription = result.scalar_one_or_none()
    if subscription is None:
        raise NotFoundError(f"Subscription for user {user_id} not found.")
    return SubscriptionInternal.model_validate(subscription)


# -----------------------------------------------------------------------------
# Enforces profile count limit before creating a new profile.
# Called by profile/service.create before writing.
# Raises PlanLimitError when limit would be exceeded.
# -----------------------------------------------------------------------------
async def check_profile_limit(
    user_id: UserID,
    db: AsyncSession,
) -> None:
    subscription = await get_subscription(user_id, db)

    count_stmt = (
        select(func.count())
        .select_from(Profile)
        .where(Profile.user_id == user_id, Profile.deleted_at.is_(None))
    )
    result = await db.execute(count_stmt)
    count = result.scalar_one()

    if "premium" in subscription.entitlements:
        if count >= PREMIUM_PROFILE_LIMIT:
            raise PlanLimitError(
                f"Premium accounts are limited to {PREMIUM_PROFILE_LIMIT} profiles."
            )
    else:
        if count >= FREE_PROFILE_LIMIT:
            raise PlanLimitError(
                f"Free accounts are limited to {FREE_PROFILE_LIMIT} profile."
            )


# -----------------------------------------------------------------------------
# Enforces portfolio image count limit before uploading.
# Called by media/service before writing a portfolio image.
# Raises PlanLimitError when user is free or when premium limit would be exceeded.
# -----------------------------------------------------------------------------
async def check_portfolio_limit(
    profile_id: ProfileID,
    user_id: UserID,
    db: AsyncSession,
) -> None:
    subscription = await get_subscription(user_id, db)

    if "premium" not in subscription.entitlements:
        raise PlanLimitError("Portfolio images require a premium subscription.")

    count_stmt = (
        select(func.count())
        .select_from(Media)
        .where(
            Media.profile_id == profile_id,
            Media.media_type == MediaType.IMAGE,
            Media.deleted_at.is_(None),
        )
    )
    result = await db.execute(count_stmt)
    count = result.scalar_one()

    if count >= PREMIUM_PORTFOLIO_LIMIT:
        raise PlanLimitError(
            f"Portfolio is limited to {PREMIUM_PORTFOLIO_LIMIT} images."
        )


# -----------------------------------------------------------------------------
# Enforces that resume upload is allowed (premium only).
# Called by media/service before writing a resume.
# Raises PlanLimitError when user is not premium.
# -----------------------------------------------------------------------------
async def check_resume_allowed(
    user_id: UserID,
    db: AsyncSession,
) -> None:
    subscription = await get_subscription(user_id, db)
    if "premium" not in subscription.entitlements:
        raise PlanLimitError("Resume upload requires a premium subscription.")


# -----------------------------------------------------------------------------
# Updates subscription from RevenueCat webhook payload.
# Called by webhook handler when plan, status, or entitlements change.
# Returns updated SubscriptionInternal.
# Raises NotFoundError if subscription does not exist.
# -----------------------------------------------------------------------------
async def update_from_webhook(
    user_id: UserID,
    plan: SubscriptionPlan,
    status: SubscriptionStatus,
    entitlements: list[str],
    db: AsyncSession,
) -> SubscriptionInternal:
    statement = (
        update(Subscription)
        .where(Subscription.user_id == user_id)
        .values(plan=plan, status=status, entitlements=entitlements)
    )
    await db.execute(statement)
    await db.commit()

    fetch_stmt = select(Subscription).where(Subscription.user_id == user_id)
    result = await db.execute(fetch_stmt)
    subscription = result.scalar_one_or_none()
    if subscription is None:
        raise NotFoundError(f"Subscription for user {user_id} not found.")
    return SubscriptionInternal.model_validate(subscription)
