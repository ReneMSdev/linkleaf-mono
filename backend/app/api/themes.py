"""Theme API routes — authenticated marketplace and public featured preview.

Thin route handlers only; domain logic lives in theme/service.py.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.db.session import get_db
from app.core.exceptions import NotFoundError
from app.core.types import ThemeID
from app.domain.theme import service as theme_service
from app.domain.theme.dto import ThemeResponse
from app.domain.user.dto import UserInternal

# Public endpoints — no auth
public_router = APIRouter(tags=["themes"])

# Authenticated endpoints
router = APIRouter(prefix="/themes", tags=["themes"])


# -----------------------------------------------------------------------------
# Public featured themes — no auth. Used by marketing page theme showcase.
# Returns curated selection of featured active themes, is_locked always False.
# -----------------------------------------------------------------------------
@public_router.get("/themes/preview", response_model=list[ThemeResponse])
async def get_featured_themes(
    db: AsyncSession = Depends(get_db),
) -> list[ThemeResponse]:
    return await theme_service.get_featured(db)


# -----------------------------------------------------------------------------
# List all themes for authenticated user with is_locked computed per subscription.
# Used by Flutter theme marketplace.
# -----------------------------------------------------------------------------
@router.get("", response_model=list[ThemeResponse])
async def list_themes(
    current_user: UserInternal = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ThemeResponse]:
    return await theme_service.get_all(current_user.id, db)


# -----------------------------------------------------------------------------
# Get single theme by ID with is_locked computed for the requesting user.
# -----------------------------------------------------------------------------
@router.get("/{theme_id}", response_model=ThemeResponse)
async def get_theme(
    theme_id: ThemeID,
    current_user: UserInternal = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ThemeResponse:
    try:
        return await theme_service.get_for_user(theme_id, current_user.id, db)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
