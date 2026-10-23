from __future__ import annotations

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class LedgerBlock(Base):
    """One block of the approved-topics blockchain (table ledger_blocks). Only admin-approved topics are stored."""

    __tablename__ = "ledger_blocks"

    id: Mapped[int] = mapped_column(primary_key=True)
    block_index: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    submission_id: Mapped[int | None] = mapped_column(Integer, nullable=True)  # plain int: ledger must outlive DB rows
    timestamp: Mapped[str] = mapped_column(String(40), nullable=False)
    data: Mapped[str] = mapped_column(Text(), nullable=False)
    previous_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    block_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
