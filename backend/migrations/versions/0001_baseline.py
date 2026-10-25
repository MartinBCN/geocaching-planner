"""Enable PostGIS.

Revision ID: 0001
Revises:
Create Date: 2025-01-01 00:00:00

"""

from collections.abc import Sequence

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")


def downgrade() -> None:
    # The extension is shared database state; dropping it could break unrelated objects.
    pass
