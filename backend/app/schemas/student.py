from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class StudentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    sis_id: str = Field(..., min_length=1, max_length=255)
    branch: str = Field(..., min_length=1, max_length=255)
    email: Optional[str] = Field(default=None, max_length=255)


class StudentCreate(StudentBase):
    pass


class StudentOut(StudentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


StudentResponse = StudentOut
