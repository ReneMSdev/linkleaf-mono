"""update mediatype enum remove avatar rename portfolio_image to image

Revision ID: f2a3b4c5d6e7
Revises: b7c8d9e0f1a2
Create Date: 2026-03-27

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "f2a3b4c5d6e7"
down_revision: Union[str, Sequence[str], None] = "b7c8d9e0f1a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new value
    op.execute("ALTER TYPE mediatype ADD VALUE IF NOT EXISTS 'image'")
    # Update existing rows
    op.execute("UPDATE media SET media_type = 'image' WHERE media_type = 'portfolio_image'")
    # Remove old values — PostgreSQL does not support DROP VALUE
    # portfolio_image and avatar will remain in the enum type but never used
    # Application layer enforces valid values via SQLAlchemy StrEnum


def downgrade() -> None:
    op.execute("UPDATE media SET media_type = 'portfolio_image' WHERE media_type = 'image'")
