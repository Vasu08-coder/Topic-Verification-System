"""Initial baseline for existing Supabase schema.

Revision ID: 001
Revises: 
Create Date: 2026-07-28 00:00:00.000000

This migration is intentionally empty because the real Supabase database
already contains the production tables. It serves as a clean starting point
for future schema changes.
"""

from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """No-op baseline migration for the existing Supabase schema."""
    pass


def downgrade() -> None:
    """No-op downgrade for the baseline migration."""
    pass
