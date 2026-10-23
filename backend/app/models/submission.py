from __future__ import annotations

from datetime import datetime

from pgvector.sqlalchemy import Vector
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.branch import Branch
    from app.models.student import Student


class Submission(Base):
    """Submission record stored in the production submissions table."""

    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    module: Mapped[str] = mapped_column(String(50), nullable=False)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.id"), nullable=False)
    academic_year_id: Mapped[int] = mapped_column(ForeignKey("academic_years.id"), nullable=False)
    title: Mapped[str] = mapped_column(Text(), nullable=False)
    abstract: Mapped[str] = mapped_column(Text(), nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(384), nullable=False)
    similarity_score: Mapped[float | None] = mapped_column(Float(), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    ai_recommendation: Mapped[str | None] = mapped_column(Text(), nullable=True)
    document_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    document_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(), server_default=func.now(), nullable=False)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("admin_users.id"), nullable=True)
    review_notes: Mapped[str | None] = mapped_column(Text(), nullable=True)

    student: Mapped["Student"] = relationship("Student", foreign_keys=[student_id], lazy="joined")
    branch: Mapped["Branch"] = relationship("Branch", foreign_keys=[branch_id], lazy="joined")
