"""add learner profile

Revision ID: 7c05582ce791
Revises: 1eab20931928
Create Date: 2025-11-13 12:32:05.641875
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.sqlite import JSON


revision = "7c05582ce791"
down_revision = "1eab20931928"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "learnerprofile",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("approach_new_topic", sa.String(length=50), nullable=True),
        sa.Column("stuck_strategy", sa.String(length=50), nullable=True),
        sa.Column("explanation_style", sa.String(length=50), nullable=True),
        sa.Column("confidence_baseline", sa.Integer(), nullable=True),
        sa.Column("long_assignment_reaction", sa.String(length=50), nullable=True),
        sa.Column("focus_time", sa.String(length=50), nullable=True),
        sa.Column("communication_style", sa.String(length=50), nullable=True),
        sa.Column("practice_style", sa.String(length=50), nullable=True),
        sa.Column("time_estimation_bias", sa.String(length=50), nullable=True),
        sa.Column("analytical_comfort", sa.Integer(), nullable=True),
        sa.Column("feedback_preference", sa.String(length=50), nullable=True),
        sa.Column("challenges", JSON(), nullable=True),
        sa.Column("primary_device", sa.String(length=50), nullable=True),
        sa.Column("proactivity_level", sa.String(length=50), nullable=True),
        sa.Column("semester_goal", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
    )
    op.create_index("ix_learnerprofile_user_id", "learnerprofile", ["user_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_learnerprofile_user_id", table_name="learnerprofile")
    op.drop_table("learnerprofile")
