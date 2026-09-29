"""User API routes.

Thin route handlers — no business logic. Auth via get_current_user.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.db.session import get_db
from app.core.exceptions import ConflictError, NotFoundError
from app.domain.user import service as user_service
from app.domain.user.dto import UserInternal, UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


# -----------------------------------------------------------------------------
# Returns the authenticated user's profile. Requires valid JWT.
# Returns UserResponse with current user data. No DB call — current_user is hydrated.
# -----------------------------------------------------------------------------
@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: UserInternal = Depends(get_current_user),
) -> UserResponse:
    return UserResponse.model_validate(current_user)


# -----------------------------------------------------------------------------
# Updates the authenticated user's profile (display_name, avatar_url).
# Requires valid JWT. Returns UserResponse with persisted state.
# Raises 404 if user not found, 409 on conflict (e.g. email already in use).
# -----------------------------------------------------------------------------
@router.patch("/me", response_model=UserResponse)
async def update_me(
    dto: UserUpdate,
    current_user: UserInternal = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    try:
        return await user_service.update_user(current_user.id, dto, db)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
