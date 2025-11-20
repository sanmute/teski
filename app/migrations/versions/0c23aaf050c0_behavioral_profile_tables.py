"""add practice sessions and behavioral profile tables

Revision ID: 0c23aaf050c0
Revises: faff471948d3
Create Date: 2023-11-19 18:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0c23aaf050c0"
down_revision = "faff471948d3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "practice_session",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("skill_id", sa.String(length=36), nullable=True),
        sa.Column("length", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("correct_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("incorrect_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avg_difficulty", sa.Float(), nullable=False, server_default="0"),
        sa.Column("fraction_review", sa.Float(), nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("abandoned", sa.Boolean(), nullable=False, server_default=sa.text("0")),
    )
    op.create_index("ix_practice_session_user_id", "practice_session", ["user_id"])
    op.create_index("ix_practice_session_skill_id", "practice_session", ["skill_id"])
    op.create_index("ix_practice_session_started_at", "practice_session", ["started_at"])
    op.create_index("ix_practice_session_finished_at", "practice_session", ["finished_at"])
    op.create_index("ix_practice_session_abandoned", "practice_session", ["abandoned"])

    op.create_table(
        "behavioral_profile",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("engagement_level", sa.Float(), nullable=False, server_default="0"),
        sa.Column("consistency_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("challenge_preference", sa.Float(), nullable=False, server_default="50"),
        sa.Column("review_vs_new_bias", sa.Float(), nullable=False, server_default="50"),
        sa.Column("session_length_preference", sa.Float(), nullable=False, server_default="50"),
        sa.Column("fatigue_risk", sa.Float(), nullable=False, server_default="10"),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_behavioral_profile_user_id", "behavioral_profile", ["user_id"], unique=True)
    op.create_index("ix_behavioral_profile_updated_at", "behavioral_profile", ["updated_at"])


def downgrade() -> None:
    op.drop_index("ix_behavioral_profile_updated_at", table_name="behavioral_profile")
    op.drop_index("ix_behavioral_profile_user_id", table_name="behavioral_profile")
    op.drop_table("behavioral_profile")

    op.drop_index("ix_practice_session_abandoned", table_name="practice_session")
    op.drop_index("ix_practice_session_finished_at", table_name="practice_session")
    op.drop_index("ix_practice_session_started_at", table_name="practice_session")
    op.drop_index("ix_practice_session_skill_id", table_name="practice_session")
    op.drop_index("ix_practice_session_user_id", table_name="practice_session")
    op.drop_table("practice_session")
