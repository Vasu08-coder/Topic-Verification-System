from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, Numeric, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SubmissionMatch(Base):
    """Submission-to-archive match record stored in the production submission_matches table."""

    __tablename__ = "submission_matches"

    id: Mapped[int] = mapped_column(primary_key=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.id"), nullable=False)
    archive_topic_id: Mapped[int] = mapped_column(ForeignKey("archive_topics.id"), nullable=False)
    similarity_pct: Mapped[float | None] = mapped_column(Numeric(), nullable=True)
    match_rank: Mapped[int | None] = mapped_column(SmallInteger(), nullable=True)
