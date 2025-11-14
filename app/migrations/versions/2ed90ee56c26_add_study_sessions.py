"""add study sessions

Revision ID: 2ed90ee56c26
Revises: cc26e3b3f8fc
Create Date: 2025-11-14 11:11:57.401144
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "2ed90ee56c26"
down_revision = "cc26e3b3f8fc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "studysession",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("task_block_id", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.Column("planned_duration_minutes", sa.Integer(), nullable=False),
        sa.Column("actual_duration_minutes", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("goal_text", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["task_id"], ["learner_task.id"]),
        sa.ForeignKeyConstraint(["task_block_id"], ["learner_task_block.id"]),
    )
    op.create_index("ix_studysession_user_id", "studysession", ["user_id"])
    op.create_index("ix_studysession_task_id", "studysession", ["task_id"])
    op.create_index("ix_studysession_task_block_id", "studysession", ["task_block_id"])
    op.create_index("ix_studysession_started_at", "studysession", ["started_at"])
    op.create_index("ix_studysession_status", "studysession", ["status"])

    op.create_table(
        "studyreflection",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("goal_completed", sa.Boolean(), nullable=True),
        sa.Column("perceived_difficulty", sa.Integer(), nullable=True),
        sa.Column("time_feeling", sa.String(length=20), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["session_id"], ["studysession.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
    )
    op.create_index("ix_studyreflection_session_id", "studyreflection", ["session_id"])
    op.create_index("ix_studyreflection_user_id", "studyreflection", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_studyreflection_user_id", table_name="studyreflection")
    op.drop_index("ix_studyreflection_session_id", table_name="studyreflection")
    op.drop_table("studyreflection")
    op.drop_index("ix_studysession_status", table_name="studysession")
    op.drop_index("ix_studysession_started_at", table_name="studysession")
    op.drop_index("ix_studysession_task_block_id", table_name="studysession")
    op.drop_index("ix_studysession_task_id", table_name="studysession")
    op.drop_index("ix_studysession_user_id", table_name="studysession")
    op.drop_table("studysession")
