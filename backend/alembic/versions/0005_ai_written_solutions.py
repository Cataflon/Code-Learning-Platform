"""ai written solutions: who wrote the reference solution and the cross-check

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-18 18:00:00
"""

import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "generation_jobs",
        sa.Column("reference_by", sa.String(length=16), server_default="teacher", nullable=False),
    )
    op.add_column("generation_jobs", sa.Column("check_code", sa.Text(), nullable=True))
    op.add_column("test_cases", sa.Column("ai_check_output", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("test_cases", "ai_check_output")
    op.drop_column("generation_jobs", "check_code")
    op.drop_column("generation_jobs", "reference_by")
