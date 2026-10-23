from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class ImportErrorDetailResponse(BaseModel):
    row_number: int
    error_message: str


class ImportHistoryBase(BaseModel):
    file_name: str = Field(..., min_length=1, max_length=500)
    module: str = Field(..., pattern=r"^(seminar|project)$")
    total_records: int
    imported_count: int
    failed_count: int
    status: str = Field(..., min_length=1, max_length=50)
    uploaded_by: int


class ImportHistoryCreate(ImportHistoryBase):
    pass


class ImportHistoryResponse(ImportHistoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    uploaded_at: datetime
    failure_details: list[ImportErrorDetailResponse] = Field(default_factory=list)
