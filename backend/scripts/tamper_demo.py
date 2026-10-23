"""Viva helper: simulate someone with database access editing an approved record directly.
  python scripts/tamper_demo.py tamper <block_index> "New Title"   -> then press Validate in the Blockchain Ledger page
  python scripts/tamper_demo.py restore                           -> puts the original data back"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.db.session import SessionLocal  # noqa: E402
from app.models.ledger_block import LedgerBlock  # noqa: E402

BACKUP = os.path.join(os.path.dirname(__file__), ".tamper_backup.json")
if len(sys.argv) < 2 or sys.argv[1] not in ("tamper", "restore"):
    sys.exit(__doc__)
with SessionLocal() as db:
    if sys.argv[1] == "tamper":
        idx, new_title = int(sys.argv[2]), sys.argv[3]
        row = db.query(LedgerBlock).filter(LedgerBlock.block_index == idx).one()
        json.dump({"block_index": idx, "data": row.data}, open(BACKUP, "w"))
        d = json.loads(row.data); d["topic_title"] = new_title
        row.data = json.dumps(d, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        print(f"Block {idx} title changed in the database. Now click Validate Chain.")
    else:
        b = json.load(open(BACKUP))
        db.query(LedgerBlock).filter(LedgerBlock.block_index == b["block_index"]).one().data = b["data"]
        print("Original block data restored.")
    db.commit()
