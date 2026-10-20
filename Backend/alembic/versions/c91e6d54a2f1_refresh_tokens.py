"""Persist hashed, rotating refresh tokens.

Revision ID: c91e6d54a2f1
Revises: 0a733eca1023
Create Date: 2026-10-20
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c91e6d54a2f1"
down_revision: Union[str, Sequence[str], None] = "0a733eca1023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "RefreshTokens",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("family_id", sa.String(length=36), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["usuario_id"], ["Usuarios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("ix_RefreshTokens_usuario_id", "RefreshTokens", ["usuario_id"])
    op.create_index("ix_RefreshTokens_family_id", "RefreshTokens", ["family_id"])


def downgrade() -> None:
    op.drop_index("ix_RefreshTokens_family_id", table_name="RefreshTokens")
    op.drop_index("ix_RefreshTokens_usuario_id", table_name="RefreshTokens")
    op.drop_table("RefreshTokens")
