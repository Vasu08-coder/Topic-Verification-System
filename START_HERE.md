# Blockchain-Based Duplicate Seminar Topic Detection and Registration System

Two layers (as in the seminar abstract):
1. **AI layer (existing):** semantic similarity (sentence-transformers + pgvector) flags duplicate topics before the admin sees them.
2. **Blockchain layer (new):** when the admin APPROVES a topic, a block {title, student, AI similarity score, admin id, timestamp} is created,
   hashed with SHA-256 and linked to the previous block. Rejected topics are logged separately (activity log) and never go on the chain.
   A validation function re-checks the whole chain and reports the first tampered block.

New files: `backend/app/blockchain/chain.py` (pure logic), `backend/app/services/ledger_service.py`, `backend/app/routes/admin_ledger.py`,
`backend/app/models/ledger_block.py`, `frontend-react/src/pages/admin/AdminLedger.jsx` (admin menu: "Blockchain Ledger").
Only small hooks were added to existing files: approval step in `admin_submissions.py`, router in `main.py`, menu item + route in the React app.

## 1. Run (Windows; first time)
```
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```
Open `backend\.env` and paste your own `DATABASE_URL` (the Supabase/Postgres URL you already use).
Create the ledger table ONCE: Supabase SQL editor -> run `backend\migrations\003_ledger_blocks.sql` (or `alembic upgrade head`).
```
uvicorn app.main:app --reload
```
New terminal:
```
cd frontend-react
npm install
npm run dev
```
Open http://localhost:5173 (admin login as before; `python seed_admin.py` if you need an admin).

## 2. Demo for the professor
1. Student logs in and submits a seminar topic -> AI similarity result is shown.
2. Admin opens the submission and clicks **Approve** -> a new block is created.
3. Admin menu -> **Blockchain Ledger** -> see blocks, hashes, previous hashes. Click **Validate Chain** -> "VALID".
4. Tamper test: `cd backend` then `python scripts/tamper_demo.py tamper 1 "Edited Title"` -> click **Validate Chain** -> "TAMPERED at block 1".
   Undo: `python scripts/tamper_demo.py restore`.
5. No database? `python scripts/blockchain_demo.py` shows build -> validate -> tamper -> detect with sample data (needs only Python).
Tests for the chain logic: `cd backend` then `python -m pytest tests/test_blockchain.py`.

## 3. Be honest in the viva
- This is a hash-chained, tamper-EVIDENT ledger stored in the project database. Editing or deleting a past record is detected, but there is
  one server and no consensus, so it is not decentralised. Multi-node copies, consensus and anchoring to a public chain are future work.
- Someone who rewrites the WHOLE chain consistently could avoid detection unless a copy of the latest hash is kept elsewhere.

## 4. Security notes
- `backend/.env` was reset: paste your own DATABASE_URL. Your old Supabase password was inside the zip you shared; change it in Supabase.
- Set a strong `JWT_SECRET` in `backend/.env` before any real use.
