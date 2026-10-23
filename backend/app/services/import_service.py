from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pandas as pd

from app.core.config import settings
from app.core.exceptions import FileTypeException, ValidationException
from app.models.archive_topic import ArchiveTopic
from app.services import similarity_service

ALLOWED_BRANCHES = {
    "CSE",
    "EEE",
    "CE",
    "ME",
    "TE",
    "BBA",
    "MBA",
    "ECE",
    "IT",
}


def parse_excel(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """Load an Excel file into a pandas DataFrame and validate the expected columns."""
    suffix = Path(filename).suffix.lower()
    if suffix not in {".xlsx", ".xls"}:
        raise FileTypeException("Only XLSX and XLS files are supported")

    try:
        dataframe = pd.read_excel(file_bytes) if hasattr(pd, "read_excel") else pd.read_excel(file_bytes)
    except Exception as exc:  # pragma: no cover - depends on pandas engine availability
        raise ValidationException("Unable to read Excel file") from exc

    required_columns = {"academic_year", "branch", "title"}
    missing_columns = required_columns.difference(set(dataframe.columns))
    if missing_columns:
        raise ValidationException(f"Missing required columns: {', '.join(sorted(missing_columns))}")

    if "abstract" not in set(dataframe.columns):
        dataframe["abstract"] = ""

    return dataframe


def validate_row(row: dict[str, Any]) -> tuple[bool, str | None]:
    """Validate a single import row; return (is_valid, error_reason)."""
    title = row.get("title")
    if title is None or (isinstance(title, float) and pd.isna(title)) or str(title).strip() == "":
        return False, "title is empty"

    branch = row.get("branch")
    branch_value = str(branch).strip() if branch is not None else ""
    if branch_value.upper() not in ALLOWED_BRANCHES:
        return False, "branch is invalid"

    academic_year = row.get("academic_year")
    academic_year_value = str(academic_year).strip() if academic_year is not None else ""
    if not re.fullmatch(r"\d{4}(-\d{4})?", academic_year_value):
        return False, "academic_year format is invalid"

    return True, None


def import_rows(
    db_session: Any,
    module_type: str,
    dataframe: pd.DataFrame,
    filename: str,
) -> dict[str, Any]:
    """Import validated rows into the requested archive table and collect failures."""
    if module_type not in {"seminar", "project"}:
        raise ValidationException("Unsupported module type")

    failure_details: list[dict[str, Any]] = []
    imported = 0

    for row_number, row in dataframe.iterrows():
        row_data = row.to_dict()
        is_valid, error_reason = validate_row(row_data)
        if not is_valid:
            failure_details.append({"row_number": int(row_number) + 2, "error_message": error_reason})
            continue

        title = str(row_data.get("title", "")).strip()
        branch = str(row_data.get("branch", "")).strip().upper()
        academic_year = str(row_data.get("academic_year", "")).strip()
        abstract = str(row_data.get("abstract", "") or "")

        existing = db_session.query(ArchiveTopic).filter(ArchiveTopic.module == module_type, ArchiveTopic.title == title).one_or_none()
        if existing is not None:
            failure_details.append({"row_number": int(row_number) + 2, "error_message": "duplicate title in archive"})
            continue

        embedding = similarity_service.embed_text(title, abstract)
        archive_entry = ArchiveTopic(
            module=module_type,
            title=title,
            abstract=abstract,
            branch_id=1,
            academic_year_id=1,
            embedding=embedding,
            source=None,
        )
        db_session.add(archive_entry)
        imported += 1

    db_session.flush()

    return {
        "total_records": len(dataframe),
        "imported": imported,
        "failed": len(failure_details),
        "failure_details": failure_details,
        "filename": filename,
        "module_type": module_type,
    }
