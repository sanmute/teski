"""add institution report recipients

Revision ID: 3fb835f5ae71
Revises: 920a8b99a7c3
Create Date: 2025-11-16 14:45:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "3fb835f5ae71"
down_revision = "920a8b99a7c3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("institution", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "report_recipients",
                sa.JSON(),
                nullable=True,
                server_default=sa.text("'[]'"),
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("institution", schema=None) as batch_op:
        batch_op.drop_column("report_recipients")
