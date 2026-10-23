from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class SubmissionCreate(BaseModel):
    branch: str = Field(..., min_length=1, max_length=255)
    module_type: Literal["seminar", "project"]
    title: str = Field(..., min_length=1, max_length=500)
    abstract: str = Field(..., min_length=1)



class SubmissionMatch(BaseModel):
    archive_id: int
    year: Optional[str] = None
    title: str
    similarity: float



class SubmissionCheckResponse(BaseModel):
    submission_id: int
    status: str = Field(..., min_length=1)
    best_similarity: Optional[float] = None
    matches: List[SubmissionMatch] = Field(default_factory=list)
    can_upload_abstract: bool
    message: str


class SubmissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    student_full_name: Optional[str] = None
    student_sis_id: Optional[str] = None
    module: str
    branch_id: int
    branch_name: Optional[str] = None
    academic_year_id: int
    title: str
    abstract: str
    similarity_score: Optional[float] = None
    status: str = Field(..., pattern=r"^(pending|flagged|approved|rejected|needs_modification)$")
    ai_recommendation: Optional[str] = None
    document_filename: Optional[str] = None
    document_path: Optional[str] = None
    submitted_at: datetime
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[int] = None
    review_notes: Optional[str] = None


class SubmissionDecision(BaseModel):
    action: Literal["approve", "reject", "needs_modification"]
    notes: Optional[str] = None


class SubmissionUpdate(BaseModel):
    status: str = Field(..., pattern=r"^(pending|flagged|approved|rejected|needs_modification)$")
    admin_notes: Optional[str] = None
    reviewed_by: Optional[int] = None


SubmissionResponse = SubmissionOut
