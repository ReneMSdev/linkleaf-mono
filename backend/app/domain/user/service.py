"""User domain service functions.

All user business logic lives in this module, with no FastAPI or HTTP concerns.
Each operation is implemented as a standalone async function, not a class method.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictError, NotFoundError
from app.core.types import UserID
from app.domain.subscription.dto import SubscriptionInternal
from app.domain.subscription.enums import SubscriptionPlan, SubscriptionStatus
from app.domain.subscription.models import Subscription
from app.domain.user.dto import UserCreate, UserInternal, UserResponse, UserUpdate
from app.domain.user.models import User


# -----------------------------------------------------------------------------
# Looks up a user by Firebase UID during authentication.
# Called by auth/dependency flows to resolve an existing account.
# Returns UserInternal when found, or None when no matching user exists.
# Never raises on a miss.
# -----------------------------------------------------------------------------
async def get_by_firebase_uid(
    firebase_uid: str,
    db: AsyncSession,
) -> UserInternal | None:
    statement = (
        select(User)
        .options(selectinload(User.subscription))
        .where(User.firebase_uid == firebase_uid)
    )
    result = await db.execute(statement)
    user = result.scalar_one_or_none()
    if user is None:
        return None
    return UserInternal.model_validate(user)


# -----------------------------------------------------------------------------
# Fetches a user by internal user ID for service-level operations.
# Called when downstream domains need authoritative user context.
# Returns UserInternal when found.
# Raises NotFoundError when the user does not exist.
# -----------------------------------------------------------------------------
async def get_by_id(
    user_id: UserID,
    db: AsyncSession,
) -> UserInternal:
    statement = select(User).options(selectinload(User.subscription)).where(User.id == user_id)
    result = await db.execute(statement)
    user = result.scalar_one_or_none()
    if user is None:
        raise NotFoundError(f"User {user_id} not found.")
    return UserInternal.model_validate(user)


# -----------------------------------------------------------------------------
# Internal helper to detect duplicate emails before user provisioning.
# Called only by create_from_firebase().
# Returns the raw User ORM object when found, otherwise None.
# -----------------------------------------------------------------------------
async def _get_by_email(
    email: str,
    db: AsyncSession,
) -> User | None:
    statement = select(User).where(User.email == email)
    result = await db.execute(statement)
    return result.scalar_one_or_none()


# -----------------------------------------------------------------------------
# Creates a new local user from Firebase claims on first successful login.
# Called after get_by_firebase_uid() returns None.
# Returns the created user as UserInternal.
# Raises ConflictError when the email already exists.
# -----------------------------------------------------------------------------
async def create_from_firebase(
    claims: dict,
    db: AsyncSession,
) -> UserInternal:
    dto = UserCreate(
        firebase_uid=claims["uid"],
        email=claims["email"],
        display_name=claims.get("name"),
        is_verified=bool(claims.get("email_verified", False)),
    )

    existing_user = await _get_by_email(dto.email, db)
    if existing_user is not None:
        raise ConflictError(f"Email {dto.email} is already in use.")

    user = User(
        firebase_uid=dto.firebase_uid,
        email=dto.email,
        display_name=dto.display_name,
        is_verified=dto.is_verified,
    )
    db.add(user)
    await db.flush()

    subscription = Subscription(
        user_id=user.id,
        plan=SubscriptionPlan.FREE,
        status=SubscriptionStatus.ACTIVE,
        entitlements=[],
    )
    user.subscription = subscription
    db.add(subscription)

    await db.commit()
    await db.refresh(user)
    return UserInternal.model_validate(user)


# -----------------------------------------------------------------------------
# Applies profile-editable user fields from a PATCH payload.
# Called by authenticated user settings/profile endpoints.
# Returns UserResponse with persisted state.
# Raises NotFoundError when the user does not exist.
# -----------------------------------------------------------------------------
async def update_user(
    user_id: UserID,
    dto: UserUpdate,
    db: AsyncSession,
) -> UserResponse:
    statement = select(User).where(User.id == user_id)
    result = await db.execute(statement)
    user = result.scalar_one_or_none()
    if user is None:
        raise NotFoundError(f"User {user_id} not found.")

    updates = dto.model_dump(exclude_unset=True)
    for field_name, field_value in updates.items():
        setattr(user, field_name, field_value)

    await db.commit()
    await db.refresh(user)
    return UserResponse.model_validate(user)


# -----------------------------------------------------------------------------
# Synchronizes the local user email with Firebase claims when they differ.
# Called in auth flows after token verification if email drift is detected.
# Returns updated UserInternal.
# Raises NotFoundError when the user does not exist.
# -----------------------------------------------------------------------------
async def sync_email(
    user_id: UserID,
    new_email: str,
    db: AsyncSession,
) -> UserInternal:
    statement = select(User).options(selectinload(User.subscription)).where(User.id == user_id)
    result = await db.execute(statement)
    user = result.scalar_one_or_none()
    if user is None:
        raise NotFoundError(f"User {user_id} not found.")

    user.email = new_email
    await db.commit()
    await db.refresh(user)
    return UserInternal.model_validate(user)


# -----------------------------------------------------------------------------
# Updates the last successful-auth timestamp for audit and activity tracking.
# Called on every successful authentication event via background task.
# Returns None.
# -----------------------------------------------------------------------------
async def update_last_login(
    user_id: UserID,
    db: AsyncSession,
) -> None:
    statement = (
        update(User)
        .where(User.id == user_id)
        .values(last_login_at=datetime.now(timezone.utc))
    )
    await db.execute(statement)
    await db.commit()


# -----------------------------------------------------------------------------
# Deactivates a user account while preserving record history.
# Called by account lifecycle logic when access should be disabled.
# Returns None.
# Raises NotFoundError when the user does not exist.
# -----------------------------------------------------------------------------
async def deactivate(
    user_id: UserID,
    db: AsyncSession,
) -> None:
    statement = select(User.id).where(User.id == user_id)
    result = await db.execute(statement)
    user_exists = result.scalar_one_or_none()
    if user_exists is None:
        raise NotFoundError(f"User {user_id} not found.")

    deactivate_statement = (
        update(User)
        .where(User.id == user_id)
        .values(is_active=False)
    )
    await db.execute(deactivate_statement)
    await db.commit()

