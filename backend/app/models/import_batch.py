from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ImportBatch(Base):
    """Bulk import batch record stored in the production import_batches table."""

    __tablename__ = "import_batches"

    id: Mapped[int] = mapped_column(primary_key=True)
    module: Mapped[str] = mapped_column(String(50), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    uploaded_by: Mapped[int] = mapped_column(ForeignKey("admin_users.id"), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(), server_default=func.now(), nullable=False)
    total_records: Mapped[int] = mapped_column(Integer(), nullable=False)
    imported_count: Mapped[int] = mapped_column(Integer(), nullable=False)
    failed_count: Mapped[int] = mapped_column(Integer(), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
