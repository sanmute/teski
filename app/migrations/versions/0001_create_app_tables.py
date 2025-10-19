"""Create app tables"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0001_create_app_tables"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user",
        sa.Column("id", sa.CHAR(32), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, index=True),
        sa.Column("timezone", sa.String(), nullable=False),
        sa.Column("display_name", sa.String(), nullable=True),
        sa.Column("streak_days", sa.Integer(), nullable=False, default=0),
        sa.Column("persona", sa.String(), nullable=True),
    )
    op.create_table(
        "task",
        sa.Column("id", sa.CHAR(32), primary_key=True),
        sa.Column("user_id", sa.CHAR(32), sa.ForeignKey("user.id"), nullable=False, index=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("course", sa.String(), nullable=True, index=True),
        sa.Column("due_at", sa.DateTime(), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, index=True),
    )
    op.create_table(
        "legacy_user_map",
        sa.Column("legacy_user_id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.CHAR(32), sa.ForeignKey("user.id"), nullable=False, index=True),
    )
    op.create_table(
        "legacy_task_map",
        sa.Column("legacy_task_id", sa.String(), primary_key=True),
        sa.Column("task_id", sa.CHAR(32), sa.ForeignKey("task.id"), nullable=False, index=True),
    )
    op.create_table(
        "memoryitem",
        sa.Column("id", sa.CHAR(32), primary_key=True),
        sa.Column("user_id", sa.CHAR(32), sa.ForeignKey("user.id"), nullable=False, index=True),
        sa.Column("task_id", sa.CHAR(32), sa.ForeignKey("task.id"), nullable=True, index=True),
        sa.Column("concept", sa.String(), nullable=False, index=True),
        sa.Column("ease", sa.Float(), nullable=False, default=2.5),
        sa.Column("interval", sa.Integer(), nullable=False, default=1),
        sa.Column("due_at", sa.DateTime(), nullable=False, index=True),
        sa.Column("stability", sa.Float(), nullable=False, default=0.0),
        sa.Column("difficulty", sa.Float(), nullable=False, default=0.3),
        sa.Column("lapses", sa.Integer(), nullable=False, default=0),
    )
    op.create_table(
        "mistake",
        sa.Column("id", sa.CHAR(32), primary_key=True),
        sa.Column("user_id", sa.CHAR(32), sa.ForeignKey("user.id"), nullable=False, index=True),
        sa.Column("task_id", sa.CHAR(32), sa.ForeignKey("task.id"), nullable=True, index=True),
        sa.Column("concept", sa.String(), nullable=False, index=True),
        sa.Column("subtype", sa.String(length=10), nullable=False, index=True),
        sa.Column("raw", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, index=True),
    )
    op.create_table(
        "reviewlog",
        sa.Column("id", sa.CHAR(32), primary_key=True),
        sa.Column("user_id", sa.CHAR(32), sa.ForeignKey("user.id"), nullable=False, index=True),
        sa.Column("memory_id", sa.CHAR(32), sa.ForeignKey("memoryitem.id"), nullable=False, index=True),
        sa.Column("grade", sa.Integer(), nullable=False),
        sa.Column("scheduled_for", sa.DateTime(), nullable=False, index=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=False, index=True),
        sa.Column("next_due_at", sa.DateTime(), nullable=False, index=True),
        sa.Column("delta_seconds", sa.Integer(), nullable=False, default=0),
    )
    op.create_table(
        "personastate",
        sa.Column("id", sa.CHAR(32), primary_key=True),
        sa.Column("user_id", sa.CHAR(32), sa.ForeignKey("user.id"), nullable=False, index=True),
        sa.Column("persona", sa.String(), nullable=False, index=True),
        sa.Column("warmup_ts", sa.DateTime(), nullable=True, index=True),
    )
    op.create_table(
        "badge",
        sa.Column("id", sa.CHAR(32), primary_key=True),
        sa.Column("user_id", sa.CHAR(32), sa.ForeignKey("user.id"), nullable=False, index=True),
        sa.Column("kind", sa.String(), nullable=False, index=True),
        sa.Column("acquired_at", sa.DateTime(), nullable=False, index=True),
    )
    op.create_table(
        "abtestassignment",
        sa.Column("id", sa.CHAR(32), primary_key=True),
        sa.Column("user_id", sa.CHAR(32), sa.ForeignKey("user.id"), nullable=False, index=True),
        sa.Column("experiment", sa.String(), nullable=False, index=True),
        sa.Column("bucket", sa.String(), nullable=False, index=True),
        sa.Column("assigned_at", sa.DateTime(), nullable=False, index=True),
    )
    op.create_table(
        "analyticsevent",
        sa.Column("id", sa.CHAR(32), primary_key=True),
        sa.Column("user_id", sa.CHAR(32), sa.ForeignKey("user.id"), nullable=True, index=True),
        sa.Column("kind", sa.String(), nullable=False, index=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("ts", sa.DateTime(), nullable=False, index=True),
    )
    op.create_table(
        "xpevent",
        sa.Column("id", sa.CHAR(32), primary_key=True),
        sa.Column("user_id", sa.CHAR(32), sa.ForeignKey("user.id"), nullable=False, index=True),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(), nullable=False, index=True),
        sa.Column("ts", sa.DateTime(), nullable=False, index=True),
    )


def downgrade() -> None:
    op.drop_table("xpevent")
    op.drop_table("analyticsevent")
    op.drop_table("abtestassignment")
    op.drop_table("badge")
    op.drop_table("personastate")
    op.drop_table("reviewlog")
    op.drop_table("mistake")
    op.drop_table("memoryitem")
    op.drop_table("legacy_task_map")
    op.drop_table("legacy_user_map")
    op.drop_table("task")
    op.drop_table("user")
