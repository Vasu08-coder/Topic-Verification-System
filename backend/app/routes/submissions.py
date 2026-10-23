from __future__ import annotations

from pathlib import Path
from typing import Any
from fastapi import Request

from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings
from app.core.exceptions import FileTypeException, NotFoundException, ValidationException
from app.core.file_validation import enforce_max_size, sanitize_filename, validate_file_signature
from app.core.security import require_student_auth, StudentIdentity
from app.db.session import get_db
from app.models.academic_year import AcademicYear
from app.models.branch import Branch
from app.models.student import Student
from app.models.submission import Submission
from app.models.activity_log import ActivityLog
from app.schemas.submission import SubmissionCheckResponse, SubmissionCreate
from app.services import similarity_service
from app.services.email_service import (
    send_email,
    submission_flagged_email,
)

router = APIRouter(prefix="/api/submissions", tags=["submissions"])
limiter = Limiter(key_func=get_remote_address)


def _resolve_branch_id(db_session: Session, branch_code: str) -> int:
    branch_row = db_session.query(Branch).filter((Branch.code == branch_code) | (Branch.name == branch_code)).one_or_none()
    if branch_row is None:
        return 1
    return branch_row.id


def _resolve_academic_year_id(db_session: Session) -> int:
    academic_year_row = db_session.query(AcademicYear).filter(AcademicYear.is_current.is_(True)).one_or_none()
    if academic_year_row is None:
        academic_year_row = db_session.query(AcademicYear).first()
    if academic_year_row is None:
        return 1
    return academic_year_row.id


def _validate_upload_content(filename: str, content: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        if content.startswith(b"%PDF"):
            return "pdf"
        raise FileTypeException("Uploaded file is not a valid PDF")

    if suffix == ".docx":
        if content.startswith(b"PK\x03\x04"):
            return "docx"
        raise FileTypeException("Uploaded file is not a valid DOCX")

    raise FileTypeException("Only PDF and DOCX files are supported")


@router.post("/check-similarity", response_model=SubmissionCheckResponse)
@limiter.limit("10/minute")
def check_similarity(
    request: Request,
    payload: SubmissionCreate,
    background_tasks: BackgroundTasks,
    current_student: StudentIdentity = Depends(require_student_auth),
    db: Session = Depends(get_db),
) -> SubmissionCheckResponse:
    """Create a student submission and compare it against the archive."""
    branch_id = _resolve_branch_id(db, payload.branch)
    academic_year_id = _resolve_academic_year_id(db)

    # Use authenticated student identity, not client-supplied data
    student = db.query(Student).filter(Student.id == current_student.id).one_or_none()
    if student is None:
        raise NotFoundException("Student not found")

    embedding = similarity_service.embed_text(payload.title, payload.abstract)
    matches = similarity_service.find_similar_topics(
        db_session=db,
        embedding=embedding,
        branch=branch_id,
        module_type=payload.module_type,
        top_k=3,
    )

    best_similarity = max((match["similarity"] for match in matches), default=0.0)
    status = "flagged" if best_similarity >= settings.SIMILARITY_THRESHOLD else "pending"

    matched_archive = matches[0] if matches else None
    submission = Submission(
        student_id=student.id,
        module=payload.module_type,
        branch_id=student.branch_id,
        academic_year_id=academic_year_id,
        title=payload.title,
        abstract=payload.abstract,
        embedding=embedding,
        similarity_score=best_similarity,
        status=status,
    )
    db.add(submission)
    db.flush()

    history_entry = ActivityLog(
        module=payload.module_type,
        submission_id=submission.id,
        action_type="submitted",
        description="Initial submission created",
    )
    db.add(history_entry)
    db.commit()
    db.refresh(submission)

    if status == "flagged" and getattr(student, "email", None):
        background_tasks.add_task(
            send_email,
            student.email,
            "Submission flagged for review",
            submission_flagged_email(student.full_name, payload.title),
        )

    return SubmissionCheckResponse(
        submission_id=submission.id,
        status=submission.status,
        best_similarity=best_similarity,
        matches=matches,
        can_upload_abstract=status == "pending",
        message="Submission was recorded successfully." if status == "pending" else "Submission matched an archived topic and was flagged for review.",
    )


@router.post("/{submission_id}/upload-abstract", status_code=status.HTTP_200_OK)
async def upload_abstract(
    submission_id: int,
    file: UploadFile = File(...),
    current_student: StudentIdentity = Depends(require_student_auth),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Upload a PDF or DOCX abstract for a non-flagged submission."""
    enforce_max_size(file.file, settings.MAX_UPLOAD_SIZE_BYTES)
    content = await file.read()

    if not validate_file_signature(content, "pdf") and not validate_file_signature(content, "docx"):
        raise FileTypeException("Uploaded file signature does not match a supported PDF or DOCX file")

    submission = db.query(Submission).filter(Submission.id == submission_id).one_or_none()
    if submission is None:
        raise NotFoundException("Submission not found")

    # Verify submission belongs to authenticated student
    if submission.student_id != current_student.id:
        raise NotFoundException("Submission not found")

    if submission.status == "flagged":
        raise ValidationException("Flagged submissions cannot upload an abstract")

    extension = "pdf" if validate_file_signature(content, "pdf") else "docx"
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_name = sanitize_filename(file.filename) or f"submission_{submission_id}"
    save_path = upload_dir / f"submission_{submission_id}_{safe_name}"
    save_path.write_bytes(content)

    submission.document_path = str(save_path.resolve())
    submission.document_filename = file.filename  # Store original filename for UI display
    db.add(submission)
    db.commit()
    db.refresh(submission)

    return {"message": "Abstract uploaded successfully", "file_path": submission.document_path}


@router.get("/{submission_id}/status")
@limiter.limit("10/minute")
async def get_submission_status(
    request: Request,
    submission_id: int,
    current_student: StudentIdentity = Depends(require_student_auth),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Return a minimal public status summary for a submission."""
    submission = db.query(Submission).filter(Submission.id == submission_id).one_or_none()
    if submission is None:
        raise NotFoundException("Submission not found")

    # Verify submission belongs to authenticated student
    if submission.student_id != current_student.id:
        raise NotFoundException("Submission not found")

    return {
        "submission_id": submission.id,
        "status": submission.status,
        "message": "Submission is pending review" if submission.status == "pending" else "Submission has been reviewed",
    }
