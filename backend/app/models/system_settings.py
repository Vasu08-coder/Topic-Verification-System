from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SystemSettings(Base):
    """System settings record stored in the production system_settings table."""

    __tablename__ = "system_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    similarity_threshold: Mapped[float | None] = mapped_column(Numeric(), nullable=True)
    flagged_threshold: Mapped[float | None] = mapped_column(Numeric(), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(), server_default=func.now(), nullable=False)
