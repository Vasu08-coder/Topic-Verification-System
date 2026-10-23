from __future__ import annotations

from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict, Field


class SeminarArchiveBase(BaseModel):
    academic_year: str = Field(..., min_length=1, max_length=50)
    branch: str = Field(..., min_length=1, max_length=255)
    title: str = Field(..., min_length=1, max_length=500)
    abstract: str = Field(..., min_length=1)
    embedding: List[float] = Field(..., min_length=384, max_length=384)
    status: str = Field(default="Approved", max_length=50)


class SeminarArchiveCreate(SeminarArchiveBase):
    pass


class SeminarArchiveResponse(SeminarArchiveBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
