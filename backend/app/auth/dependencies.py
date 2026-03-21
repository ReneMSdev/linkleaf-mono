"""FastAPI dependencies for authentication and authorization.

This module provides dependency functions used to resolve the current user
from the Authorization header, provision users on first login, and enforce
premium subscription requirements.
"""

from __future__ import annotations

from fastapi import BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.exceptions import AuthException, InvalidTokenError, MissingTokenError, TokenExpiredError
from app.auth.firebase_client import verify_token
from app.core.db.session import AsyncSessionLocal, get_db
from app.core.types import UserID
from app.domain.user.dto import UserInternal
from app.domain.user.service import (
    create_from_firebase,
    get_by_firebase_uid,
    sync_email,
    update_last_login,
)


# -----------------------------------------------------------------------------
# Resolves the authenticated user from the Authorization header.
# Used on protected routes that require a valid Firebase token.
# Returns UserInternal with subscription loaded.
# Raises HTTPException(401) when token is missing, invalid, or expired.
# -----------------------------------------------------------------------------
async def get_current_user(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> UserInternal:
    try:
        auth = request.headers.get("Authorization")
        if not auth or not auth.startswith("Bearer "):
            raise MissingTokenError()
        token = auth[7:]
        decoded_token = verify_token(token)
    except AuthException as e:
        raise HTTPException(status_code=401, detail=str(e)) from e

    firebase_uid = decoded_token["uid"]
    user = await get_by_firebase_uid(firebase_uid, db)
    if user is None:
        user = await create_from_firebase(decoded_token, db)
    else:
        if decoded_token.get("email") and decoded_token["email"] != user.email:
            user = await sync_email(user.id, decoded_token["email"], db)

    background_tasks.add_task(_update_last_login_background, user.id)
    return user


# -----------------------------------------------------------------------------
# Same as get_current_user but returns None when no token or invalid token.
# Used on routes that optionally use user context (e.g. personalized defaults).
# When token is present and valid, full provisioning + background task runs.
# Returns UserInternal when authenticated, None otherwise.
# -----------------------------------------------------------------------------
async def get_optional_user(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> UserInternal | None:
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        return None

    try:
        token = auth[7:]
        decoded_token = verify_token(token)
    except (InvalidTokenError, TokenExpiredError):
        return None

    firebase_uid = decoded_token["uid"]
    user = await get_by_firebase_uid(firebase_uid, db)
    if user is None:
        user = await create_from_firebase(decoded_token, db)
    else:
        if decoded_token.get("email") and decoded_token["email"] != user.email:
            user = await sync_email(user.id, decoded_token["email"], db)

    background_tasks.add_task(_update_last_login_background, user.id)
    return user


# -----------------------------------------------------------------------------
# Requires the current user to have a premium entitlement.
# Used on premium-only endpoints (e.g. advanced features, higher limits).
# Returns UserInternal when premium.
# Raises HTTPException(403) when subscription lacks "premium" entitlement.
# -----------------------------------------------------------------------------
def require_premium(
    current_user: UserInternal = Depends(get_current_user),
) -> UserInternal:
    entitlements = (
        current_user.subscription.entitlements
        if current_user.subscription
        else []
    )
    if "premium" not in entitlements:
        raise HTTPException(
            status_code=403,
            detail="Premium subscription required",
        )
    return current_user


async def _update_last_login_background(user_id: UserID) -> None:
    """Creates a fresh DB session and updates last_login_at. Used in background tasks."""
    db = AsyncSessionLocal()
    try:
        await update_last_login(user_id, db)
    finally:
        await db.close()
