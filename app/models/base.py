from sqlalchemy import Column, Integer, DateTime, func
from sqlalchemy.orm import declarative_mixin


@declarative_mixin
class BaseModelMixin:
    """Базовый миксин для моделей: id, created_at, updated_at."""

    id = Column(Integer, primary_key=True, index=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
