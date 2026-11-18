"""admin role and invite codes

Revision ID: 0006
Revises: 0005
Create Date: 2026-11-19 00:09:06.889856
"""

import sqlalchemy as sa
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "invite_codes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("note", sa.String(length=200), nullable=False),
        sa.Column("max_uses", sa.Integer(), nullable=False),
        sa.Column("uses", sa.Integer(), server_default="0", nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name="invite_codes_created_by_fkey",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_invite_codes_code"), "invite_codes", ["code"], unique=True)
    # The role column is a plain string (native_enum=False, no CHECK), so "admin" needs no change.
    op.add_column(
        "users",
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
    )
    op.add_column("users", sa.Column("invite_code_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "users_invite_code_id_fkey",
        "users",
        "invite_codes",
        ["invite_code_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.execute("UPDATE users SET role = 'teacher' WHERE role = 'admin'")
    op.drop_constraint("users_invite_code_id_fkey", "users", type_="foreignkey")
    op.drop_column("users", "invite_code_id")
    op.drop_column("users", "is_active")
    op.drop_index(op.f("ix_invite_codes_code"), table_name="invite_codes")
    op.drop_table("invite_codes")
