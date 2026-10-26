"""Create cache aggregates, separate user data, and import history.

Revision ID: 0002
Revises: 0001
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geography
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "caches",
        sa.Column("gc_code", sa.String(32), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("type", sa.String(40), nullable=False),
        sa.Column("source_type", sa.Text(), nullable=False),
        sa.Column("container", sa.String(40), nullable=False),
        sa.Column("source_container", sa.Text(), nullable=False),
        sa.Column("difficulty", sa.Float(), nullable=False),
        sa.Column("terrain", sa.Float(), nullable=False),
        sa.Column("owner", sa.Text(), nullable=False),
        sa.Column("placed_at", sa.DateTime(timezone=True)),
        sa.Column("location", Geography("POINT", srid=4326, spatial_index=False), nullable=False),
        sa.Column("country", sa.Text(), nullable=False),
        sa.Column("state", sa.Text(), nullable=False),
        sa.Column("short_description", sa.Text(), nullable=False),
        sa.Column("long_description", sa.Text(), nullable=False),
        sa.Column("description_is_html", sa.Boolean(), nullable=False),
        sa.Column("hint", sa.Text(), nullable=False),
        sa.Column("attributes", postgresql.JSONB(), nullable=False),
        sa.Column("is_available", sa.Boolean(), nullable=False),
        sa.Column("is_archived", sa.Boolean(), nullable=False),
        sa.Column("found_by_me", sa.Boolean(), nullable=False),
        sa.Column("found_at", sa.DateTime(timezone=True)),
        sa.Column("source", sa.String(40), nullable=False),
        sa.Column("source_updated_at", sa.DateTime(timezone=True)),
        sa.Column("source_hash", sa.String(64), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "difficulty BETWEEN 1 AND 5 AND difficulty * 2 = floor(difficulty * 2)",
            name="difficulty_range",
        ),
        sa.CheckConstraint(
            "terrain BETWEEN 1 AND 5 AND terrain * 2 = floor(terrain * 2)",
            name="terrain_range",
        ),
    )
    op.create_index("ix_caches_location_gist", "caches", ["location"], postgresql_using="gist")
    for column in ("type", "difficulty", "terrain", "found_by_me", "is_archived"):
        op.create_index(f"ix_caches_{column}", "caches", [column])

    op.create_table(
        "cache_waypoints",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "cache_gc_code",
            sa.String(32),
            sa.ForeignKey("caches.gc_code", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("prefix", sa.String(16), nullable=False),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("type", sa.String(40), nullable=False),
        sa.Column("source_type", sa.Text(), nullable=False),
        sa.Column("location", Geography("POINT", srid=4326, spatial_index=False)),
        sa.Column("description", sa.Text(), nullable=False),
        sa.UniqueConstraint("cache_gc_code", "code"),
    )
    op.create_index("ix_cache_waypoints_cache_gc_code", "cache_waypoints", ["cache_gc_code"])

    op.create_table(
        "cache_logs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=False),
        sa.Column(
            "cache_gc_code",
            sa.String(32),
            sa.ForeignKey("caches.gc_code", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("type", sa.String(40), nullable=False),
        sa.Column("source_type", sa.Text(), nullable=False),
        sa.Column("finder", sa.Text(), nullable=False),
        sa.Column("logged_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
    )
    op.create_index("ix_cache_logs_cache_gc_code", "cache_logs", ["cache_gc_code"])

    op.create_table(
        "user_cache_data",
        sa.Column(
            "cache_gc_code",
            sa.String(32),
            sa.ForeignKey("caches.gc_code", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("corrected_location", Geography("POINT", srid=4326, spatial_index=False)),
    )
    op.create_index(
        "ix_user_cache_data_corrected_location_gist",
        "user_cache_data",
        ["corrected_location"],
        postgresql_using="gist",
    )
    op.create_table(
        "import_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("source", sa.String(40), nullable=False),
        sa.Column("filenames", postgresql.JSONB(), nullable=False),
        sa.Column("created", sa.Integer(), nullable=False),
        sa.Column("updated", sa.Integer(), nullable=False),
        sa.Column("unchanged", sa.Integer(), nullable=False),
        sa.Column("waypoints", sa.Integer(), nullable=False),
        sa.Column("errors", postgresql.JSONB(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("import_runs")
    op.drop_table("user_cache_data")
    op.drop_table("cache_logs")
    op.drop_table("cache_waypoints")
    op.drop_table("caches")
