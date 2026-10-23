from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.security import AdminIdentity, require_admin_auth
from app.db.session import get_db
from app.services import ledger_service

router = APIRouter(prefix="/api/admin/ledger", tags=["admin-ledger"])


@router.get("")
def get_ledger(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_admin: AdminIdentity = Depends(require_admin_auth),
    db: Session = Depends(get_db),
) -> dict:
    """Newest-first list of blocks plus counts. Read-only."""
    return ledger_service.list_blocks(db, limit=limit, offset=offset)


@router.get("/validate")
def validate_ledger(
    current_admin: AdminIdentity = Depends(require_admin_auth),
    db: Session = Depends(get_db),
) -> dict:
    """Recompute every hash and link; reports the first tampered block, if any."""
    result = ledger_service.validate(db)
    result["checked_at"] = datetime.now(timezone.utc).isoformat()
    return result
