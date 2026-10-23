"""Pure blockchain logic (no database, no web framework) so it can be tested and demonstrated anywhere.

Each block stores: index, timestamp, data (topic title, student, similarity score, admin, ...),
previous_hash and its own block_hash = SHA-256(index | timestamp | data | previous_hash).
Changing ANY past block changes its hash and breaks every later link, so tampering is detectable.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

GENESIS_PREVIOUS_HASH = "0" * 64


def canonical_json(data: dict[str, Any]) -> str:
    """Stable JSON text, so the same data always produces the same hash."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_hash(index: int, timestamp: str, data_json: str, previous_hash: str) -> str:
    return hashlib.sha256(f"{index}|{timestamp}|{data_json}|{previous_hash}".encode("utf-8")).hexdigest()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def make_block(index: int, previous_hash: str, data: dict[str, Any], timestamp: str | None = None) -> dict[str, Any]:
    ts = timestamp or utc_now_iso()
    data_json = canonical_json(data)
    return {
        "block_index": index,
        "timestamp": ts,
        "data": data_json,
        "previous_hash": previous_hash,
        "block_hash": compute_hash(index, ts, data_json, previous_hash),
    }


def genesis_block() -> dict[str, Any]:
    return make_block(0, GENESIS_PREVIOUS_HASH, {"type": "genesis", "note": "Seminar topic ledger start"})


def validate_chain(blocks: list[dict[str, Any]]) -> dict[str, Any]:
    """Re-check every block. Returns {valid, total_blocks, broken_at_index, reason}."""
    for position, block in enumerate(blocks):
        index = block["block_index"]
        if index != position:
            return _bad(blocks, index, "index_gap: a block is missing or out of order")
        expected_prev = GENESIS_PREVIOUS_HASH if position == 0 else blocks[position - 1]["block_hash"]
        if block["previous_hash"] != expected_prev:
            return _bad(blocks, index, "link_broken: previous_hash does not match the earlier block")
        if compute_hash(index, block["timestamp"], block["data"], block["previous_hash"]) != block["block_hash"]:
            return _bad(blocks, index, "hash_mismatch: block data was modified after it was recorded")
    return {"valid": True, "total_blocks": len(blocks), "broken_at_index": None, "reason": None}


def _bad(blocks: list[dict[str, Any]], index: int, reason: str) -> dict[str, Any]:
    return {"valid": False, "total_blocks": len(blocks), "broken_at_index": index, "reason": reason}
