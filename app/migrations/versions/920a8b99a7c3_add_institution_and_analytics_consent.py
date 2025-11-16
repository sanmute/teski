"""Revision ID: 920a8b99a7c3
Revises: 2ed90ee56c26
Create Date: 2025-11-16 14:26:57.504297
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '920a8b99a7c3'
down_revision = '2ed90ee56c26'
branch_labels = None
depends_on = None

def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    existing_tables = inspector.get_table_names()
    if "institution" not in existing_tables:
        op.create_table(
            "institution",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("domain", sa.String(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("domain", name="uq_institution_domain"),
        )
        op.create_index("ix_institution_name", "institution", ["name"])
        op.create_index("ix_institution_domain", "institution", ["domain"])
    else:
        inst_indexes = {idx["name"] for idx in inspector.get_indexes("institution")}
        if "ix_institution_name" not in inst_indexes:
            op.create_index("ix_institution_name", "institution", ["name"])
        if "ix_institution_domain" not in inst_indexes:
            op.create_index("ix_institution_domain", "institution", ["domain"])

    user_columns = {col["name"] for col in inspector.get_columns("user")}
    if "email" not in user_columns:
        op.add_column("user", sa.Column("email", sa.String(length=255), nullable=True))
    if "institution_id" not in user_columns:
        op.add_column("user", sa.Column("institution_id", sa.String(length=36), nullable=True))
    if "analytics_consent" not in user_columns:
        op.add_column(
            "user",
            sa.Column(
                "analytics_consent",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("1"),
            ),
        )
    if "is_institution_admin" not in user_columns:
        op.add_column(
            "user",
            sa.Column(
                "is_institution_admin",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("0"),
            ),
        )

    user_indexes = {idx["name"] for idx in inspector.get_indexes("user")}
    if "ix_user_email" not in user_indexes:
        op.create_index("ix_user_email", "user", ["email"])
    if "ix_user_institution_id" not in user_indexes:
        op.create_index("ix_user_institution_id", "user", ["institution_id"])
    if "ix_user_is_institution_admin" not in user_indexes:
        op.create_index("ix_user_is_institution_admin", "user", ["is_institution_admin"])


def downgrade() -> None:
    op.drop_index("ix_user_is_institution_admin", table_name="user")
    op.drop_index("ix_user_institution_id", table_name="user")
    op.drop_index("ix_user_email", table_name="user")
    op.drop_column("user", "is_institution_admin")
    op.drop_column("user", "analytics_consent")
    op.drop_column("user", "institution_id")
    op.drop_column("user", "email")

    op.drop_index("ix_institution_domain", table_name="institution")
    op.drop_index("ix_institution_name", table_name="institution")
    op.drop_table("institution")
