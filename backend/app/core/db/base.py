from datetime import datetime

from sqlalchemy import DateTime, func, inspect
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""

    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        mapper = inspect(self.__class__)
        primary_key_columns = mapper.primary_key

        if len(primary_key_columns) == 1:
            pk_attr = primary_key_columns[0].key
            pk_value = getattr(self, pk_attr, None)
            return f"<{class_name} {pk_attr}={pk_value}>"

        pk_parts = ", ".join(
            f"{column.key}={getattr(self, column.key, None)}"
            for column in primary_key_columns
        )
        return f"<{class_name} {pk_parts}>"


class TimestampMixin:
    """Shared timestamp columns for domain models."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
