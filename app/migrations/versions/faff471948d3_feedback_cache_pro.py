"""Revision ID: faff471948d3
Revises: 
Create Date: 2025-11-07 12:01:57.220831
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "faff471948d3"
down_revision = "0001_create_app_tables"
branch_labels = None
depends_on = None


def _table_exists(inspector: sa.engine.interfaces.Inspector, name: str) -> bool:
    return name in inspector.get_table_names()


def _column_exists(inspector: sa.engine.interfaces.Inspector, table: str, column: str) -> bool:
    return any(col["name"] == column for col in inspector.get_columns(table))


def _index_exists(inspector: sa.engine.interfaces.Inspector, table: str, name: str) -> bool:
    return any(idx["name"] == name for idx in inspector.get_indexes(table))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _table_exists(inspector, "feedbackcache"):
        op.create_table(
            "feedbackcache",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("key_hash", sa.String(length=64), nullable=False),
            sa.Column("model_used", sa.String(length=32), nullable=False),
            sa.Column("language", sa.String(length=8), nullable=False),
            sa.Column("persona", sa.String(length=32), nullable=False),
            sa.Column("topic", sa.String(length=255), nullable=True),
            sa.Column("feedback_text", sa.Text(), nullable=False),
            sa.Column("tokens_in", sa.Integer(), nullable=False),
            sa.Column("tokens_out", sa.Integer(), nullable=False),
            sa.Column("cost_eur", sa.Float(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )
        op.create_index("ix_feedbackcache_created_at", "feedbackcache", ["created_at"], unique=False)
        op.create_index("ux_feedbackcache_key_hash", "feedbackcache", ["key_hash"], unique=True)

    if not _table_exists(inspector, "feedbackevent"):
        op.create_table(
            "feedbackevent",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("user_id", sa.String(length=64), nullable=False),
            sa.Column("model_used", sa.String(length=32), nullable=False),
            sa.Column("tokens_in", sa.Integer(), nullable=False),
            sa.Column("tokens_out", sa.Integer(), nullable=False),
            sa.Column("cost_eur", sa.Float(), nullable=False),
            sa.Column("cached_hit", sa.Boolean(), nullable=False, server_default=sa.sql.expression.false()),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )
        op.create_index("ix_feedbackevent_user_id", "feedbackevent", ["user_id"], unique=False)
        op.create_index("ix_feedbackevent_created_at", "feedbackevent", ["created_at"], unique=False)

    if not _column_exists(inspector, "user", "is_pro"):
        op.add_column("user", sa.Column("is_pro", sa.Boolean(), nullable=False, server_default=sa.sql.expression.false()))
    if not _column_exists(inspector, "user", "pro_until"):
        op.add_column("user", sa.Column("pro_until", sa.DateTime(), nullable=True))

    if not _index_exists(inspector, "user", "ix_user_is_pro"):
        op.create_index("ix_user_is_pro", "user", ["is_pro"], unique=False)
    if not _index_exists(inspector, "user", "ix_user_pro_until"):
        op.create_index("ix_user_pro_until", "user", ["pro_until"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _index_exists(inspector, "user", "ix_user_pro_until"):
        op.drop_index("ix_user_pro_until", table_name="user")
    if _index_exists(inspector, "user", "ix_user_is_pro"):
        op.drop_index("ix_user_is_pro", table_name="user")
    if _column_exists(inspector, "user", "pro_until"):
        op.drop_column("user", "pro_until")
    if _column_exists(inspector, "user", "is_pro"):
        op.drop_column("user", "is_pro")

    if _table_exists(inspector, "feedbackevent"):
        if _index_exists(inspector, "feedbackevent", "ix_feedbackevent_created_at"):
            op.drop_index("ix_feedbackevent_created_at", table_name="feedbackevent")
        if _index_exists(inspector, "feedbackevent", "ix_feedbackevent_user_id"):
            op.drop_index("ix_feedbackevent_user_id", table_name="feedbackevent")
        op.drop_table("feedbackevent")

    if _table_exists(inspector, "feedbackcache"):
        if _index_exists(inspector, "feedbackcache", "ux_feedbackcache_key_hash"):
            op.drop_index("ux_feedbackcache_key_hash", table_name="feedbackcache")
        if _index_exists(inspector, "feedbackcache", "ix_feedbackcache_created_at"):
            op.drop_index("ix_feedbackcache_created_at", table_name="feedbackcache")
        op.drop_table("feedbackcache")
