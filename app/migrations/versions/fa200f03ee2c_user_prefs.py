"""Revision ID: fa200f03ee2c
Revises: ec74aad8229e
Create Date: 2025-11-07 20:35:36.316804
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "fa200f03ee2c"
down_revision = "ec74aad8229e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "userprefs",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False, unique=True),
        sa.Column("allow_llm_feedback", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("allow_voice_stt", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("allow_elaboration_prompts", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("allow_concept_maps", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("allow_transfer_checks", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("store_self_explanations", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("store_concept_maps", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_userprefs_user_id", "userprefs", ["user_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_userprefs_user_id", table_name="userprefs")
    op.drop_table("userprefs")
