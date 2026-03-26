from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, PlanLimitError
from app.core.types import ThemeID, UserID
from app.domain.subscription.service import get_subscription
from app.domain.theme.dto import ThemeInternal, ThemeResponse
from app.domain.theme.models import Theme, ThemeTier


# -----------------------------------------------------------------------------
# Lists all active themes for a user with per-theme lock state from subscription.
# Fetches subscription to set is_locked on premium rows for non-premium users.
# Free users see every theme; premium-only themes have is_locked True until upgraded.
# -----------------------------------------------------------------------------
async def get_all(
    user_id: UserID,
    db: AsyncSession,
) -> list[ThemeResponse]:
    subscription = await get_subscription(user_id, db)
    is_premium = "premium" in subscription.entitlements

    statement = (
        select(Theme)
        .where(Theme.is_active.is_(True))
        .order_by(Theme.tier.asc(), Theme.name.asc())
    )
    result = await db.execute(statement)
    themes = result.scalars().all()

    out: list[ThemeResponse] = []
    for theme in themes:
        is_locked = theme.tier == ThemeTier.PREMIUM and not is_premium
        base = ThemeResponse.model_validate(theme)
        out.append(base.model_copy(update={"is_locked": is_locked}))
    return out


# -----------------------------------------------------------------------------
# Loads one active theme by id for internal/domain use.
# Raises NotFoundError when missing or inactive.
# -----------------------------------------------------------------------------
async def get_by_id(
    theme_id: ThemeID,
    db: AsyncSession,
) -> ThemeInternal:
    statement = select(Theme).where(
        Theme.id == theme_id,
        Theme.is_active.is_(True),
    )
    result = await db.execute(statement)
    theme = result.scalar_one_or_none()
    if theme is None:
        raise NotFoundError(f"Theme {theme_id} not found.")
    return ThemeInternal.model_validate(theme)


# -----------------------------------------------------------------------------
# Ensures the user may apply the theme (premium themes require premium entitlement).
# Raises PlanLimitError when the theme is premium and the user lacks premium.
# -----------------------------------------------------------------------------
async def check_theme_allowed(
    theme_id: ThemeID,
    user_id: UserID,
    db: AsyncSession,
) -> None:
    theme = await get_by_id(theme_id, db)
    subscription = await get_subscription(user_id, db)
    if (
        ThemeTier(theme.tier) == ThemeTier.PREMIUM
        and "premium" not in subscription.entitlements
    ):
        raise PlanLimitError("This theme requires a premium subscription.")
