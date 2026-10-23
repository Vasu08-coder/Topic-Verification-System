from __future__ import annotations

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SubmissionKeyword(Base):
    """Keyword extracted from a submission stored in the production submission_keywords table."""

    __tablename__ = "submission_keywords"

    id: Mapped[int] = mapped_column(primary_key=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.id"), nullable=False)
    keyword: Mapped[str] = mapped_column(String(255), nullable=False)
