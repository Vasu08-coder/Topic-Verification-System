from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import NotFoundException
from app.core.security import AdminIdentity, require_admin_auth
from app.db.session import get_db
from app.models.activity_log import ActivityLog
from app.models.admin import AdminUser
from app.models.archive_topic import ArchiveTopic
from app.models.branch import Branch
from app.models.student import Student
from app.models.submission import Submission
from app.schemas.submission import SubmissionDecision, SubmissionOut
from app.services import ledger_service, similarity_service
from app.services.email_service import (
    send_email,
    submission_approved_email,
    submission_needs_modification_email,
    submission_rejected_email,
)

router = APIRouter(prefix="/api/admin/submissions", tags=["admin-submissions"])


def _submission_to_out(submission: Submission, db: Session | None = None) -> SubmissionOut:
    student = getattr(submission, "student", None)
    branch = getattr(submission, "branch", None)

    if student is None and getattr(submission, "student_id", None) is not None and db is not None:
        student = db.query(Student).filter(Student.id == submission.student_id).one_or_none()
    if branch is None and getattr(submission, "branch_id", None) is not None and db is not None:
        branch = db.query(Branch).filter(Branch.id == submission.branch_id).one_or_none()

    return SubmissionOut(
        id=submission.id,
        student_id=submission.student_id,
        student_full_name=getattr(student, "full_name", None),
        student_sis_id=getattr(student, "sis_id", None),
        module=submission.module,
        branch_id=submission.branch_id,
        branch_name=getattr(branch, "name", None),
        academic_year_id=submission.academic_year_id,
        title=submission.title,
        abstract=submission.abstract,
        similarity_score=submission.similarity_score,
        status=submission.status,
        ai_recommendation=submission.ai_recommendation,
        document_filename=submission.document_filename,
        document_path=submission.document_path,
        submitted_at=submission.submitted_at,
        reviewed_at=submission.reviewed_at,
        reviewed_by=submission.reviewed_by,
        review_notes=submission.review_notes,
    )


def _extract_branch_value(value: Any) -> Any:
    if value is None:
        return None

    for attr in ("branch", "branch_id", "branch_name", "branch_code"):
        branch_value = getattr(value, attr, None)
        if branch_value not in (None, ""):
            return branch_value

    for attr in ("profile", "user", "admin", "account", "identity"):
        nested_value = getattr(value, attr, None)
        if nested_value is not None:
            nested_branch = _extract_branch_value(nested_value)
            if nested_branch not in (None, ""):
                return nested_branch

    return None


def _is_faculty_coordinator(current_admin: AdminIdentity) -> bool:
    role_value = str(getattr(current_admin, "role", "")).lower()
    username_value = str(getattr(current_admin, "username", "")).lower()
    return role_value in {"faculty_coordinator", "faculty"} or username_value.startswith("faculty")


def _resolve_admin_branch_id(db: Session, current_admin: AdminIdentity, admin_profile: AdminUser | None) -> int | None:
    admin_branch = _extract_branch_value(admin_profile) if admin_profile is not None else None
    if admin_branch in (None, ""):
        admin_branch = getattr(current_admin, "branch", None)
    if admin_branch in (None, ""):
        return None
    if isinstance(admin_branch, int):
        return admin_branch

    branch_row = db.query(Branch).filter((Branch.code == str(admin_branch)) | (Branch.name == str(admin_branch))).one_or_none()
    return branch_row.id if branch_row is not None else None


def _enforce_admin_access(current_admin: AdminIdentity, submission: Submission, db: Session | None = None) -> None:
    if not _is_faculty_coordinator(current_admin):
        return

    if db is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    admin_profile = db.query(AdminUser).filter(AdminUser.id == current_admin.id).first()
    admin_branch_id = _resolve_admin_branch_id(db, current_admin, admin_profile)
    submission_branch_id = getattr(submission, "branch_id", None)
    if admin_branch_id is None or submission_branch_id is None or admin_branch_id != submission_branch_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


@router.get("", response_model=list[SubmissionOut])
def list_submissions(
    status: str | None = Query(default=None),
    branch: str | None = Query(default=None),
    module_type: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_admin: AdminIdentity = Depends(require_admin_auth),
    db: Session = Depends(get_db),
) -> list[SubmissionOut]:
    """Return paginated submissions, enforcing branch visibility for faculty coordinators."""
    query = db.query(Submission).options(joinedload(Submission.student), joinedload(Submission.branch))
    if status is not None:
        query = query.filter(Submission.status == status)
    if module_type is not None:
        query = query.filter(Submission.module == module_type)

    submissions = query.order_by(desc(Submission.submitted_at)).offset(offset).limit(limit).all()
    return [_submission_to_out(submission, db) for submission in submissions]


@router.get("/dashboard-stats")
def dashboard_stats(
    current_admin: AdminIdentity = Depends(require_admin_auth),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Return counts of submissions grouped by status, respecting branch visibility."""
    query = db.query(Submission)

    counts = {
        "pending": query.filter(Submission.status == "pending").count(),
        "flagged": query.filter(Submission.status == "flagged").count(),
        "approved": query.filter(Submission.status == "approved").count(),
        "needs_modification": query.filter(Submission.status == "needs_modification").count(),
    }
    return counts


@router.get("/{submission_id}", response_model=SubmissionOut)
def get_submission_detail(
    submission_id: int,
    current_admin: AdminIdentity = Depends(require_admin_auth),
    db: Session = Depends(get_db),
) -> SubmissionOut:
    """Return a submission and refresh its live similarity matches for admins."""
    submission = (
        db.query(Submission)
        .options(joinedload(Submission.student), joinedload(Submission.branch))
        .filter(Submission.id == submission_id)
        .one_or_none()
    )
    if submission is None:
        raise NotFoundException("Submission not found")

    _enforce_admin_access(current_admin, submission)

    matches = similarity_service.find_similar_topics(
        db_session=db,
        embedding=submission.embedding,
        branch=submission.branch_id,
        module_type=submission.module,
        top_k=3,
    )
    submission.matched_title = matches[0]["title"] if matches else None
    submission.similarity_score = max((match["similarity"] for match in matches), default=0.0)
    db.add(submission)
    db.commit()
    db.refresh(submission)

    return _submission_to_out(submission, db)


@router.get("/{submission_id}/document")
def download_submission_document(
    submission_id: int,
    current_admin: AdminIdentity = Depends(require_admin_auth),
    db: Session = Depends(get_db),
) -> FileResponse:
    """Download the submitted document for a submission. Admin-only endpoint."""
    from app.core.config import settings

    submission = db.query(Submission).filter(Submission.id == submission_id).one_or_none()
    if submission is None:
        raise NotFoundException("Submission not found")

    if not submission.document_path:
        raise NotFoundException("No document attached to this submission")

    file_path = Path(submission.document_path)
    if not file_path.exists():
        raise NotFoundException("Document file not found on disk")

    # Determine MIME type based on file extension
    media_type = "application/pdf" if file_path.suffix.lower() == ".pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    return FileResponse(
        path=file_path,
        filename=submission.document_filename or f"submission_{submission_id}.{file_path.suffix.lstrip('.')}",
        media_type=media_type,
    )


@router.post("/{submission_id}/decision", response_model=SubmissionOut)
def submit_decision(
    submission_id: int,
    payload: SubmissionDecision,
    background_tasks: BackgroundTasks,
    current_admin: AdminIdentity = Depends(require_admin_auth),
    db: Session = Depends(get_db),
) -> SubmissionOut:
    """Update the submission status with an audit trail and archive approved topics."""
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if submission is None:
        raise NotFoundException("Submission not found")

    _enforce_admin_access(current_admin, submission, db)

    old_status = submission.status
    status_map = {
        "approve": "approved",
        "reject": "rejected",
        "needs_modification": "needs_modification",
    }
    action_type_map = {
        "approve": "approved",
        "reject": "rejected",
        "needs_modification": "resub_requested",
    }
    new_status = status_map[payload.action]
    activity_action_type = action_type_map[payload.action]

    submission.status = new_status
    submission.reviewed_at = datetime.now(timezone.utc)
    submission.reviewed_by = current_admin.id
    submission.review_notes = payload.notes

    history_entry = ActivityLog(
        module=submission.module,
        submission_id=submission.id,
        action_type=activity_action_type,
        description=payload.notes or f"Submission status changed to {new_status}",
    )
    db.add(history_entry)

    if new_status == "approved":
        archive_entry = ArchiveTopic(
            module=submission.module,
            title=submission.title,
            abstract=submission.abstract,
            branch_id=submission.branch_id,
            academic_year_id=submission.academic_year_id,
            embedding=submission.embedding,
            source="promoted_submission",
        )
        db.add(archive_entry)
        # Blockchain layer: approved topics only, written in the same transaction as the approval.
        ledger_student = db.query(Student).filter(Student.id == submission.student_id).one_or_none()
        ledger_service.append_approval(db, submission, ledger_student, current_admin.id)

    db.commit()
    db.refresh(submission)

    student = db.query(Student).filter(Student.id == submission.student_id).one_or_none()
    if student and getattr(student, "email", None):
        if new_status == "approved":
            background_tasks.add_task(
                send_email,
                student.email,
                "Submission approved",
                submission_approved_email(student.full_name, submission.title),
            )
        elif new_status == "rejected":
            background_tasks.add_task(
                send_email,
                student.email,
                "Submission rejected",
                submission_rejected_email(student.full_name, submission.title, payload.notes),
            )
        elif new_status == "needs_modification":
            background_tasks.add_task(
                send_email,
                student.email,
                "Submission needs modification",
                submission_needs_modification_email(student.full_name, submission.title, payload.notes),
            )

    return _submission_to_out(submission, db)

