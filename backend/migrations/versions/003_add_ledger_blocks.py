"""Add ledger_blocks table (blockchain layer).

Revision ID: 003
Revises: 002
"""

from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ledger_blocks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("block_index", sa.Integer(), nullable=False, unique=True),
        sa.Column("submission_id", sa.Integer(), nullable=True),
        sa.Column("timestamp", sa.String(40), nullable=False),
        sa.Column("data", sa.Text(), nullable=False),
        sa.Column("previous_hash", sa.String(64), nullable=False),
        sa.Column("block_hash", sa.String(64), nullable=False, unique=True),
    )


def downgrade() -> None:
    op.drop_table("ledger_blocks")
