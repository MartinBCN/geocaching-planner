"""Add singleton planner settings.

Revision ID: 0003
Revises: 0002
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geography

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "settings",
        sa.Column("id", sa.SmallInteger(), primary_key=True),
        sa.Column("home_location", Geography("POINT", srid=4326, spatial_index=False)),
        sa.Column("avg_speed_kmh", sa.Float(), server_default="18", nullable=False),
        sa.Column("corridor_m_default", sa.Integer(), server_default="500", nullable=False),
        sa.Column("default_profile", sa.String(32), server_default="trekking", nullable=False),
        sa.Column("tile_url", sa.Text()),
        sa.Column(
            "tile_attribution",
            sa.Text(),
            server_default="© OpenStreetMap contributors, CyclOSM",
            nullable=False,
        ),
        sa.CheckConstraint("id = 1", name="ck_settings_singleton_id"),
    )


def downgrade() -> None:
    op.drop_table("settings")
