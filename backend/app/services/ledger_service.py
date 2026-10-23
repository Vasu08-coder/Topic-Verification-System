"""Database side of the blockchain layer. Block logic itself lives in app.blockchain.chain."""
from __future__ import annotations

import hashlib
import json
from typing import Any

from sqlalchemy.orm import Session

from app.blockchain import chain
from app.models.activity_log import ActivityLog
from app.models.ledger_block import LedgerBlock


def _as_dict(row: LedgerBlock) -> dict[str, Any]:
    return {"block_index": row.block_index, "submission_id": row.submission_id, "timestamp": row.timestamp,
            "data": row.data, "previous_hash": row.previous_hash, "block_hash": row.block_hash}


def _last_block(db: Session) -> LedgerBlock | None:
    return db.query(LedgerBlock).order_by(LedgerBlock.block_index.desc()).with_for_update().first()


def append_approval(db: Session, submission: Any, student: Any, admin_id: int | None) -> LedgerBlock:
    """Record an admin approval as a new block. Same DB transaction as the approval (caller commits).
    Only approved topics reach this function: rejected topics are never added to the chain."""
    existing = db.query(LedgerBlock).filter(LedgerBlock.submission_id == submission.id).first()
    if existing is not None:
        return existing
    last = _last_block(db)
    if last is None:
        g = chain.genesis_block()
        last = LedgerBlock(submission_id=None, **g)
        db.add(last)
        db.flush()
    data = {
        "type": "approved_topic",
        "topic_title": submission.title,
        "abstract_sha256": hashlib.sha256((submission.abstract or "").encode("utf-8")).hexdigest(),
        "module": submission.module,
        "student_name": getattr(student, "full_name", None),
        "student_sis_id": getattr(student, "sis_id", None),
        "similarity_score": round(float(submission.similarity_score or 0.0), 4),  # from the AI layer
        "admin_id": admin_id,
    }
    block = chain.make_block(last.block_index + 1, last.block_hash, data)
    row = LedgerBlock(submission_id=submission.id, **block)
    db.add(row)
    db.flush()
    return row


def list_blocks(db: Session, limit: int = 50, offset: int = 0) -> dict[str, Any]:
    total = db.query(LedgerBlock).count()
    rows = db.query(LedgerBlock).order_by(LedgerBlock.block_index.desc()).offset(offset).limit(limit).all()
    blocks = []
    for r in rows:
        d = _as_dict(r)
        try:
            d["data"] = json.loads(r.data)
        except ValueError:
            d["data"] = {"unreadable": True}
        blocks.append(d)
    rejected = db.query(ActivityLog).filter(ActivityLog.action_type == "rejected").count()
    return {"total_blocks": total, "rejected_logged_off_chain": rejected, "blocks": blocks}


def validate(db: Session) -> dict[str, Any]:
    rows = db.query(LedgerBlock).order_by(LedgerBlock.block_index.asc()).all()
    return chain.validate_chain([_as_dict(r) for r in rows])
