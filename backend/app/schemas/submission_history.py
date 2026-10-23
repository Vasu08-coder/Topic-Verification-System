from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SubmissionHistoryBase(BaseModel):
    submission_id: int
    changed_by: int
    old_status: Optional[str] = None
    new_status: str = Field(..., min_length=1, max_length=50)
    notes: Optional[str] = None


class SubmissionHistoryCreate(SubmissionHistoryBase):
    pass


class SubmissionHistoryResponse(SubmissionHistoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    changed_at: datetime
