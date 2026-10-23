from __future__ import annotations

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AcademicYear(Base):
    """Academic year record stored in the production academic_years table."""

    __tablename__ = "academic_years"

    id: Mapped[int] = mapped_column(primary_key=True)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False)
