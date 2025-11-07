"""Initial placeholder revision to anchor legacy DB state.

The Teski app historically relied on SQLModel.create_all at runtime to
materialize tables, so this migration intentionally does nothing. It
exists solely to give Alembic a stable base revision that matches the
current production schema.
"""

from __future__ import annotations

from alembic import op  # noqa: F401
import sqlalchemy as sa  # noqa: F401

revision = "0001_create_app_tables"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
