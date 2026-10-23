from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.security import AdminIdentity, get_current_admin
from app.db.session import get_db
from app.models.archive_topic import ArchiveTopic

router = APIRouter(prefix="/api", tags=["archive"])
public_limiter = Limiter(key_func=get_remote_address)


def _build_archive_query(model: type[Any], branch: str | None, academic_year: str | None, search: str | None):
    query = model.query if hasattr(model, "query") else None
    if query is None:
        query = None
    return query


@router.get("/admin/archive/{module_type}")
def list_admin_archive(
    module_type: str,
    branch: str | None = Query(default=None),
    academic_year: str | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_admin: AdminIdentity = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Browse the approved archive for admins with pagination and text search."""
    if module_type not in {"seminar", "project"}:
        raise ValueError("Unsupported module type")

    query = db.query(ArchiveTopic)
    query = query.filter(ArchiveTopic.module == module_type)

    if branch is not None and branch != "":
        query = query.filter(ArchiveTopic.branch_id == branch)
    if academic_year is not None and academic_year != "":
        query = query.filter(ArchiveTopic.academic_year_id == academic_year)
    if search is not None and search != "":
        query = query.filter(ArchiveTopic.title.ilike(f"%{search}%"))

    total = query.count()
    rows = query.order_by(desc(ArchiveTopic.created_at)).offset(offset).limit(limit).all()

    results = [
        {
            "id": row.id,
            "module": row.module,
            "title": row.title,
            "created_at": row.created_at,
        }
        for row in rows
    ]

    return {"module_type": module_type, "items": results, "limit": limit, "offset": offset, "total": total}


@router.get("/public/archive/{module_type}")
@public_limiter.limit("20/minute")
def list_public_archive(
    request: Request,
    module_type: str,
    branch: str | None = Query(default=None),
    academic_year: str | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Expose a safe, public archive view for students browsing approved topics."""
    if module_type not in {"seminar", "project"}:
        raise ValueError("Unsupported module type")

    query = db.query(ArchiveTopic)
    query = query.filter(ArchiveTopic.module == module_type)

    if branch is not None and branch != "":
        query = query.filter(ArchiveTopic.branch_id == branch)
    if academic_year is not None and academic_year != "":
        query = query.filter(ArchiveTopic.academic_year_id == academic_year)
    if search is not None and search != "":
        query = query.filter(ArchiveTopic.title.ilike(f"%{search}%"))

    total = query.count()
    rows = query.order_by(desc(ArchiveTopic.created_at)).offset(offset).limit(limit).all()

    results = [
        {
            "module": row.module,
            "title": row.title,
        }
        for row in rows
    ]

    return {"module_type": module_type, "items": results, "limit": limit, "offset": offset, "total": total}
