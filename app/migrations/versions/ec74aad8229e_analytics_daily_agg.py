"""Revision ID: ec74aad8229e
Revises: faff471948d3
Create Date: 2025-11-07 12:49:22.219233
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.sqlite import JSON


revision = "ec74aad8229e"
down_revision = "faff471948d3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "analyticsdailyagg",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("counts", JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("sessions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reviews", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("minutes_active", sa.Float(), nullable=False, server_default="0"),
        sa.Column("last_recomputed_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.UniqueConstraint("user_id", "day", name="uq_analytics_daily_user_day"),
    )
    op.create_index("ix_analyticsdailyagg_user_id", "analyticsdailyagg", ["user_id"])
    op.create_index("ix_analyticsdailyagg_day", "analyticsdailyagg", ["day"])
    op.create_index("ix_analyticsdailyagg_sessions", "analyticsdailyagg", ["sessions"])
    op.create_index("ix_analyticsdailyagg_reviews", "analyticsdailyagg", ["reviews"])
    op.create_index(
        "ix_analyticsdailyagg_last_recomputed_at",
        "analyticsdailyagg",
        ["last_recomputed_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_analyticsdailyagg_last_recomputed_at", table_name="analyticsdailyagg")
    op.drop_index("ix_analyticsdailyagg_reviews", table_name="analyticsdailyagg")
    op.drop_index("ix_analyticsdailyagg_sessions", table_name="analyticsdailyagg")
    op.drop_index("ix_analyticsdailyagg_day", table_name="analyticsdailyagg")
    op.drop_index("ix_analyticsdailyagg_user_id", table_name="analyticsdailyagg")
    op.drop_table("analyticsdailyagg")
