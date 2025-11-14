"""add tasks and notifications

Revision ID: cc26e3b3f8fc
Revises: 7c05582ce791
Create Date: 2025-11-13 13:00:42.630103
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "cc26e3b3f8fc"
down_revision = "7c05582ce791"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "learner_task",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("course", sa.String(), nullable=True),
        sa.Column("kind", sa.String(), nullable=True),
        sa.Column("due_at", sa.DateTime(), nullable=True),
        sa.Column("base_estimated_minutes", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
    )
    op.create_index("ix_learner_task_user_id", "learner_task", ["user_id"])
    op.create_index("ix_learner_task_due_at", "learner_task", ["due_at"])
    op.create_index("ix_learner_task_status", "learner_task", ["status"])

    op.create_table(
        "learner_task_block",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("start_at", sa.DateTime(), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["task_id"], ["learner_task.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
    )
    op.create_index("ix_learner_task_block_task_id", "learner_task_block", ["task_id"])
    op.create_index("ix_learner_task_block_user_id", "learner_task_block", ["user_id"])

    op.create_table(
        "notificationpreference",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("enable_task_reminders", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("enable_review_reminders", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("quiet_hours_start", sa.Integer(), nullable=True),
        sa.Column("quiet_hours_end", sa.Integer(), nullable=True),
        sa.Column("max_per_day", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
    )
    op.create_index("ix_notificationpreference_user_id", "notificationpreference", ["user_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_notificationpreference_user_id", table_name="notificationpreference")
    op.drop_table("notificationpreference")
    op.drop_index("ix_learner_task_block_user_id", table_name="learner_task_block")
    op.drop_index("ix_learner_task_block_task_id", table_name="learner_task_block")
    op.drop_table("learner_task_block")
    op.drop_index("ix_learner_task_status", table_name="learner_task")
    op.drop_index("ix_learner_task_due_at", table_name="learner_task")
    op.drop_index("ix_learner_task_user_id", table_name="learner_task")
    op.drop_table("learner_task")
