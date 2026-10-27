"""Add expression GiST indexes for bbox predicates on geometry casts.

Revision ID: 0004
Revises: 0003
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_caches_location_geometry_gist",
        "caches",
        [sa.text("CAST(location AS geometry(GEOMETRY))")],
        postgresql_using="gist",
    )
    op.create_index(
        "ix_user_cache_data_corrected_geometry_gist",
        "user_cache_data",
        [sa.text("CAST(corrected_location AS geometry(GEOMETRY))")],
        postgresql_using="gist",
    )


def downgrade() -> None:
    op.drop_index("ix_user_cache_data_corrected_geometry_gist", table_name="user_cache_data")
    op.drop_index("ix_caches_location_geometry_gist", table_name="caches")
