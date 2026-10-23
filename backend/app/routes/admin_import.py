from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, Request, UploadFile, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import FileTypeException, NotFoundException, ValidationException
from app.core.file_validation import enforce_max_size, sanitize_filename, validate_file_signature
from app.core.security import AdminIdentity, require_admin_auth
from app.db.session import get_db
from app.models.import_batch import ImportBatch
from app.models.import_error import ImportErrorRecord
from app.schemas.import_history import ImportErrorDetailResponse, ImportHistoryResponse
from app.services import import_service

router = APIRouter(prefix="/api/admin/import", tags=["admin-import"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/{module_type}", response_model=ImportHistoryResponse)
@limiter.limit("10/hour")
async def import_archive_records(
    request: Request,
    module_type: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin=Depends(require_admin_auth),

) -> ImportHistoryResponse:
    """Bulk import historical seminar or project topics from Excel."""
    if module_type not in {"seminar", "project"}:
        raise ValidationException("Unsupported module type")

    if file.filename is None:
        raise ValidationException("A file is required")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in {".xlsx", ".xls"}:
        raise FileTypeException("Only XLSX and XLS files are supported")

    enforce_max_size(file.file, settings.MAX_UPLOAD_SIZE_BYTES)
    content = file.file.read()

    if not validate_file_signature(content, "xlsx"):
        raise FileTypeException("Uploaded file signature does not match an XLSX file")

    safe_name = sanitize_filename(file.filename)
    dataframe = import_service.parse_excel(content, safe_name)
    summary = import_service.import_rows(db, module_type, dataframe, file.filename)

    import_record = ImportBatch(
        module=summary["module_type"],
        file_name=summary["filename"],
        uploaded_by=admin.id,
        total_records=summary["total_records"],
        imported_count=summary["imported"],
        failed_count=summary["failed"],
        status="completed" if summary["failed"] == 0 else "completed_with_errors",
    )
    db.add(import_record)
    db.flush()

    for error_detail in summary.get("failure_details", []):
        db.add(
            ImportErrorRecord(
                import_batch_id=import_record.id,
                row_number=error_detail["row_number"],
                error_message=error_detail["error_message"],
                raw_data=None,
            )
        )

    db.commit()
    db.refresh(import_record)

    response = ImportHistoryResponse.model_validate(import_record)
    failure_rows = (
        db.query(ImportErrorRecord)
        .filter(ImportErrorRecord.import_batch_id == import_record.id)
        .order_by(ImportErrorRecord.row_number)
        .all()
    )
    response.failure_details = [
        ImportErrorDetailResponse(row_number=error.row_number, error_message=error.error_message)
        for error in failure_rows
    ]
    return response


@router.get("/history", response_model=list[ImportHistoryResponse])
def import_history(
    current_admin: AdminIdentity = Depends(require_admin_auth),
    db: Session = Depends(get_db),
) -> list[ImportHistoryResponse]:
    """Return the import history for super admins, newest first."""
    records = db.query(ImportBatch).order_by(ImportBatch.uploaded_at.desc()).all()
    return [ImportHistoryResponse.model_validate(record) for record in records]
