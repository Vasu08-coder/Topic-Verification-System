-- Blockchain layer table. Run once in the Supabase SQL editor (or use: alembic upgrade head).
CREATE TABLE IF NOT EXISTS ledger_blocks (
    id SERIAL PRIMARY KEY,
    block_index INTEGER NOT NULL UNIQUE,
    submission_id INTEGER,
    timestamp VARCHAR(40) NOT NULL,
    data TEXT NOT NULL,
    previous_hash VARCHAR(64) NOT NULL,
    block_hash VARCHAR(64) NOT NULL UNIQUE
);
