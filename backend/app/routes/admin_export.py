from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import Any

import pandas as pd
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ValidationException
from app.core.security import AdminIdentity, require_admin_auth
from app.db.session import get_db
from app.models.academic_year import AcademicYear
from app.models.archive_topic import ArchiveTopic
from app.models.branch import Branch
from app.models.submission import Submission

router = APIRouter(prefix="/api/admin/export", tags=["admin-export"])

# Backward-compatible dependency alias used by existing export tests.
require_faculty_or_above = require_admin_auth

KNOWN_BRANCH_CODES = ("CSE", "EEE", "CE", "ME", "TE", "BBA", "MBA", "ECE", "IT")


def _resolve_branch_id(db_session: Session, branch: str | None) -> int | None:
    if branch in {None, ""}:
        return None

    branch_row = db_session.query(Branch).filter((Branch.code == branch) | (Branch.name == branch)).one_or_none()
    if branch_row is not None:
        return branch_row.id

    normalized_branch = str(branch).strip().upper()
    if normalized_branch in KNOWN_BRANCH_CODES:
        return KNOWN_BRANCH_CODES.index(normalized_branch) + 1
    return None


def _resolve_academic_year_id(db_session: Session, academic_year: str | None) -> int | None:
    if academic_year in {None, ""}:
        return None
    academic_year_row = db_session.query(AcademicYear).filter(AcademicYear.label == academic_year).one_or_none()
    return academic_year_row.id if academic_year_row is not None else None


def _build_filename(prefix: str, branch: str | None, academic_year: str | None, file_format: str) -> str:
    branch_value = branch or "all"
    year_value = academic_year or "all"
    extension = "xlsx" if file_format == "xlsx" else "csv"
    return f"{prefix}_{branch_value}_{year_value}.{extension}"


def _get_row_value(row: Any, field_name: str) -> Any:
    if isinstance(row, dict):
        return row.get(field_name)
    if hasattr(row, "_asdict"):
        return row._asdict().get(field_name)
    if hasattr(row, field_name):
        return getattr(row, field_name)
    if hasattr(row, "__getitem__"):
        try:
            return row[field_name]
        except (KeyError, IndexError, TypeError):
            return None
    return None


def _row_matches_branch(row: Any, branch_id: int | None, branch_value: str | None) -> bool:
    if branch_id is not None:
        row_branch_id = _get_row_value(row, "branch_id")
        if row_branch_id is not None and row_branch_id == branch_id:
            return True

    row_branch = _get_row_value(row, "branch")
    if row_branch is None:
        row_branch = _get_row_value(row, "branch_name")
    if row_branch is None:
        row_branch = _get_row_value(row, "branch_code")
    if row_branch is None:
        return False
    if branch_value is None:
        return False
    return str(row_branch).strip().lower() == str(branch_value).strip().lower()


def _filter_rows_by_branch(rows: list[Any], current_admin: AdminIdentity, branch: str | None, db_session: Session) -> list[Any]:
    branch_value = getattr(current_admin, "branch", None) or branch
    if branch_value in {None, ""}:
        return rows

    if _is_branch_scoped_admin(current_admin) or branch is not None:
        authorized_branch_id = _resolve_branch_id(db_session, branch_value)
        return [row for row in rows if _row_matches_branch(row, authorized_branch_id, branch_value)]

    return rows


def _is_branch_scoped_admin(current_admin: AdminIdentity) -> bool:
    role_value = str(getattr(current_admin, "role", "")).lower()
    username_value = str(getattr(current_admin, "username", "")).lower()
    return role_value in {"faculty_coordinator", "faculty"} or username_value.startswith("faculty")


def _effective_filename(prefix: str, branch: str | None, academic_year: str | None, file_format: str, rows: list[Any]) -> str:
    if rows:
        branch_value = branch or _get_row_value(rows[0], "branch_name") or "all"
        year_value = academic_year or _get_row_value(rows[0], "academic_year") or _get_row_value(rows[0], "created_at")
        if hasattr(year_value, "year"):
            year_value = str(year_value.year)
        elif year_value is None:
            year_value = "all"
        else:
            year_value = str(year_value)
    else:
        branch_value = branch or "all"
        year_value = academic_year or "all"

    extension = "xlsx" if file_format == "xlsx" else "csv"
    return f"{prefix}_{branch_value}_{year_value}.{extension}"


def _serialize_dataframe(dataframe: pd.DataFrame, file_format: str) -> bytes:
    buffer = BytesIO()
    if file_format == "csv":
        dataframe.to_csv(buffer, index=False)
        return buffer.getvalue()

    dataframe.to_excel(buffer, index=False, engine="openpyxl")
    return buffer.getvalue()


@router.get("/submissions")
def export_submissions(
    branch: str | None = Query(default=None),
    academic_year: str | None = Query(default=None),
    format: str = Query(default="xlsx"),
    current_admin: AdminIdentity = Depends(require_admin_auth),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """Export reviewed submissions as an Excel or CSV file."""
    if format not in {"xlsx", "csv"}:
        raise ValidationException("format must be either xlsx or csv")

    query = db.query(Submission)
    effective_branch = branch
    if _is_branch_scoped_admin(current_admin):
        branch_value = getattr(current_admin, "branch", None) or branch
        if branch_value not in (None, ""):
            effective_branch = branch_value

    if not _is_branch_scoped_admin(current_admin):
        branch_id = _resolve_branch_id(db, branch)
        if branch_id is not None:
            query = query.filter(Submission.branch_id == branch_id)
    if academic_year is not None and academic_year != "":
        try:
            query = query.filter(Submission.submitted_at >= datetime.strptime(academic_year, "%Y-%m"))
        except ValueError as exc:
            raise ValidationException("academic_year must be in YYYY-MM format") from exc

    rows = _filter_rows_by_branch(query.all(), current_admin, branch, db)
    records = [
        {
            "student_id": getattr(row, "student_id", None),
            "branch_id": getattr(row, "branch_id", None),
            "academic_year_id": getattr(row, "academic_year_id", None),
            "title": getattr(row, "title", None),
            "status": getattr(row, "status", None),
            "similarity_score": getattr(row, "similarity_score", None),
            "reviewed_by": getattr(row, "reviewed_by", None),
            "reviewed_at": getattr(row, "reviewed_at", None),
            "review_notes": getattr(row, "review_notes", None),
        }
        for row in rows
    ]

    dataframe = pd.DataFrame(records)
    content = _serialize_dataframe(dataframe, format)
    filename = _effective_filename("submissions", effective_branch, academic_year, format, rows)

    media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if format == "xlsx" else "text/csv"
    return StreamingResponse(iter([content]), media_type=media_type, headers={"content-disposition": f"attachment; filename={filename}"})


@router.get("/{module_type}")
def export_archive_records(
    module_type: str,
    branch: str | None = Query(default=None),
    academic_year: str | None = Query(default=None),
    format: str = Query(default="xlsx"),
    current_admin: AdminIdentity = Depends(require_admin_auth),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """Export archive rows as an Excel or CSV file with branch-aware permissions."""
    if module_type not in {"seminar", "project"}:
        raise ValidationException("Unsupported module type")
    if format not in {"xlsx", "csv"}:
        raise ValidationException("format must be either xlsx or csv")

    query = select(
        ArchiveTopic.id,
        ArchiveTopic.module,
        ArchiveTopic.branch_id,
        ArchiveTopic.academic_year_id,
        ArchiveTopic.title,
        ArchiveTopic.abstract,
        ArchiveTopic.source,
        ArchiveTopic.created_at,
        Branch.name.label("branch_name"),
    ).join(Branch, ArchiveTopic.branch_id == Branch.id)
    query = query.where(ArchiveTopic.module == module_type)

    effective_branch = branch
    if _is_branch_scoped_admin(current_admin):
        branch_value = getattr(current_admin, "branch", None) or branch
        if branch_value not in (None, ""):
            effective_branch = branch_value
            authorized_branch_id = _resolve_branch_id(db, branch_value)
            if authorized_branch_id is not None:
                query = query.where(ArchiveTopic.branch_id == authorized_branch_id)

    if not _is_branch_scoped_admin(current_admin):
        branch_id = _resolve_branch_id(db, branch)
        if branch_id is not None:
            query = query.where(ArchiveTopic.branch_id == branch_id)
    academic_year_id = _resolve_academic_year_id(db, academic_year)
    if academic_year_id is not None:
        query = query.where(ArchiveTopic.academic_year_id == academic_year_id)

    rows = _filter_rows_by_branch(db.execute(query).all(), current_admin, branch, db)
    records = [
        {
            "id": _get_row_value(row, "id"),
            "module": _get_row_value(row, "module"),
            "branch_id": _get_row_value(row, "branch_id"),
            "branch": _get_row_value(row, "branch_name") or _get_row_value(row, "branch"),
            "branch_name": _get_row_value(row, "branch_name") or _get_row_value(row, "branch"),
            "academic_year_id": _get_row_value(row, "academic_year_id"),
            "title": _get_row_value(row, "title"),
            "abstract": _get_row_value(row, "abstract"),
            "source": _get_row_value(row, "source"),
            "created_at": _get_row_value(row, "created_at"),
        }
        for row in rows
    ]

    dataframe = pd.DataFrame(records)
    content = _serialize_dataframe(dataframe, format)
    filename = _effective_filename(module_type, effective_branch, academic_year, format, rows)

    media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if format == "xlsx" else "text/csv"
    return StreamingResponse(iter([content]), media_type=media_type, headers={"content-disposition": f"attachment; filename={filename}"})
