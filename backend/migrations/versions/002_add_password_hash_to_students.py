"""Add password_hash column to students table.

Revision ID: 002
Revises: 001
Create Date: 2026-07-31 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add nullable password_hash column to students table."""
    op.add_column("students", sa.Column("password_hash", sa.String(255), nullable=True))


def downgrade() -> None:
    """Remove password_hash column from students table."""
    op.drop_column("students", "password_hash")
