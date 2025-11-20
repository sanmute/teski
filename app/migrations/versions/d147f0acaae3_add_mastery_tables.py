"""add mastery tables

Revision ID: d147f0acaae3
Revises: 3fb835f5ae71
Create Date: 2025-11-19 13:26:14.670346
"""

from alembic import op
import sqlalchemy as sa


revision = "d147f0acaae3"
down_revision = "3fb835f5ae71"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "skill",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_skill_name"),
        sa.UniqueConstraint("slug", name="uq_skill_slug"),
    )
    op.create_index("ix_skill_name", "skill", ["name"])
    op.create_index("ix_skill_slug", "skill", ["slug"])

    op.create_table(
        "user_skill_mastery",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("skill_id", sa.String(length=36), nullable=False),
        sa.Column("mastery", sa.Float(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["skill_id"], ["skill.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "skill_id", name="uq_user_skill_mastery"),
    )
    op.create_index("ix_user_skill_mastery_user_id", "user_skill_mastery", ["user_id"])
    op.create_index("ix_user_skill_mastery_skill_id", "user_skill_mastery", ["skill_id"])


def downgrade():
    op.drop_index("ix_user_skill_mastery_skill_id", table_name="user_skill_mastery")
    op.drop_index("ix_user_skill_mastery_user_id", table_name="user_skill_mastery")
    op.drop_table("user_skill_mastery")
    op.drop_index("ix_skill_slug", table_name="skill")
    op.drop_index("ix_skill_name", table_name="skill")
    op.drop_table("skill")
