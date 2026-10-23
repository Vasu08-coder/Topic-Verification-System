from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ImportErrorRecord(Base):
    """Import error record stored in the production import_errors table."""

    __tablename__ = "import_errors"

    id: Mapped[int] = mapped_column(primary_key=True)
    import_batch_id: Mapped[int] = mapped_column(ForeignKey("import_batches.id"), nullable=False)
    row_number: Mapped[int] = mapped_column(Integer(), nullable=False)
    error_message: Mapped[str] = mapped_column(String(500), nullable=False)
    raw_data: Mapped[dict | None] = mapped_column(postgresql.JSONB(astext_type=String()), nullable=True)
