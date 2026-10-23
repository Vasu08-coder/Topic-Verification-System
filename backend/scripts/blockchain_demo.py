"""Offline demo for the viva: no database, no internet needed.   Run:  python scripts/blockchain_demo.py
Uses SAMPLE topics (not real students) to show: build chain -> validate -> tamper -> detect."""
import copy
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.blockchain.chain import compute_hash, genesis_block, make_block, validate_chain  # noqa: E402

SAMPLES = [("Blockchain for Land Records", "Student A", 0.12), ("AI-Based Crop Disease Detection", "Student B", 0.08),
           ("IoT Smart Irrigation System", "Student C", 0.21)]


def show(blocks):
    for b in blocks:
        d = json.loads(b["data"])
        print(f"  Block {b['block_index']}: {d.get('topic_title', 'GENESIS'):<34} hash={b['block_hash'][:12]}.. prev={b['previous_hash'][:12]}..")


def verdict(title, blocks):
    r = validate_chain(blocks)
    print(f"{title}\n  -> {'VALID' if r['valid'] else 'INVALID at block ' + str(r['broken_at_index']) + ' (' + r['reason'] + ')'}\n")


chain = [genesis_block()]
for title, student, score in SAMPLES:  # an admin approved each topic after the AI similarity check
    chain.append(make_block(len(chain), chain[-1]["block_hash"],
                            {"type": "approved_topic", "topic_title": title, "student_name": student, "similarity_score": score, "admin_id": 1}))
print("STEP 1: Approved topics recorded as blocks (each hash includes the previous hash)")
show(chain)
verdict("STEP 2: Validate the untouched chain", chain)

t1 = copy.deepcopy(chain)
d = json.loads(t1[2]["data"]); d["topic_title"] = "Some Other Topic"; t1[2]["data"] = json.dumps(d, sort_keys=True, separators=(",", ":"))
verdict("STEP 3: Someone edits the title of Block 2 in the database", t1)

t2 = copy.deepcopy(t1)
b = t2[2]; b["block_hash"] = compute_hash(b["block_index"], b["timestamp"], b["data"], b["previous_hash"])
verdict("STEP 4: Attacker also recomputes Block 2's hash to hide the edit (the NEXT link breaks)", t2)

t3 = copy.deepcopy(chain); del t3[1]
verdict("STEP 5: Someone deletes Block 1", t3)
