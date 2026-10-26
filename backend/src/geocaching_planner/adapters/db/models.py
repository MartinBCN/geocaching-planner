from datetime import datetime

from geoalchemy2 import Geography
from geoalchemy2.elements import WKBElement
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from geocaching_planner.adapters.db.base import Base


class CacheModel(Base):
    __tablename__ = "caches"
    __table_args__ = (
        Index("ix_caches_location_gist", "location", postgresql_using="gist"),
        Index("ix_caches_type", "type"),
        Index("ix_caches_difficulty", "difficulty"),
        Index("ix_caches_terrain", "terrain"),
        Index("ix_caches_found_by_me", "found_by_me"),
        Index("ix_caches_is_archived", "is_archived"),
        CheckConstraint(
            "difficulty BETWEEN 1 AND 5 AND difficulty * 2 = floor(difficulty * 2)",
            name="difficulty_range",
        ),
        CheckConstraint(
            "terrain BETWEEN 1 AND 5 AND terrain * 2 = floor(terrain * 2)",
            name="terrain_range",
        ),
    )

    gc_code: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    type: Mapped[str] = mapped_column(String(40))
    source_type: Mapped[str] = mapped_column(Text, default="")
    container: Mapped[str] = mapped_column(String(40))
    source_container: Mapped[str] = mapped_column(Text, default="")
    difficulty: Mapped[float] = mapped_column(Float)
    terrain: Mapped[float] = mapped_column(Float)
    owner: Mapped[str] = mapped_column(Text)
    placed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    location: Mapped[WKBElement] = mapped_column(Geography("POINT", srid=4326, spatial_index=False))
    country: Mapped[str] = mapped_column(Text, default="")
    state: Mapped[str] = mapped_column(Text, default="")
    short_description: Mapped[str] = mapped_column(Text, default="")
    long_description: Mapped[str] = mapped_column(Text, default="")
    description_is_html: Mapped[bool] = mapped_column(Boolean, default=False)
    hint: Mapped[str] = mapped_column(Text, default="")
    attributes: Mapped[list[dict[str, str | int | bool]]] = mapped_column(JSONB, default=list)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    found_by_me: Mapped[bool] = mapped_column(Boolean, default=False)
    found_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source: Mapped[str] = mapped_column(String(40))
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_hash: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    waypoints: Mapped[list[CacheWaypointModel]] = relationship(cascade="all, delete-orphan")
    logs: Mapped[list[CacheLogModel]] = relationship(cascade="all, delete-orphan")
    user_data: Mapped[UserCacheDataModel | None] = relationship(cascade="all, delete-orphan")


class CacheWaypointModel(Base):
    __tablename__ = "cache_waypoints"
    __table_args__ = (UniqueConstraint("cache_gc_code", "code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cache_gc_code: Mapped[str] = mapped_column(
        ForeignKey("caches.gc_code", ondelete="CASCADE"), index=True
    )
    prefix: Mapped[str] = mapped_column(String(16), default="")
    code: Mapped[str] = mapped_column(String(32))
    name: Mapped[str] = mapped_column(Text)
    type: Mapped[str] = mapped_column(String(40))
    source_type: Mapped[str] = mapped_column(Text, default="")
    location: Mapped[WKBElement | None] = mapped_column(
        Geography("POINT", srid=4326, spatial_index=False)
    )
    description: Mapped[str] = mapped_column(Text, default="")


class CacheLogModel(Base):
    __tablename__ = "cache_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    cache_gc_code: Mapped[str] = mapped_column(
        ForeignKey("caches.gc_code", ondelete="CASCADE"), index=True
    )
    type: Mapped[str] = mapped_column(String(40))
    source_type: Mapped[str] = mapped_column(Text, default="")
    finder: Mapped[str] = mapped_column(Text)
    logged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    text: Mapped[str] = mapped_column(Text, default="")


class UserCacheDataModel(Base):
    __tablename__ = "user_cache_data"
    __table_args__ = (
        Index(
            "ix_user_cache_data_corrected_location_gist",
            "corrected_location",
            postgresql_using="gist",
        ),
    )

    cache_gc_code: Mapped[str] = mapped_column(
        ForeignKey("caches.gc_code", ondelete="CASCADE"), primary_key=True
    )
    note: Mapped[str] = mapped_column(Text, default="")
    corrected_location: Mapped[WKBElement | None] = mapped_column(
        Geography("POINT", srid=4326, spatial_index=False)
    )


class ImportRunModel(Base):
    __tablename__ = "import_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source: Mapped[str] = mapped_column(String(40))
    filenames: Mapped[list[str]] = mapped_column(JSONB)
    created: Mapped[int] = mapped_column(Integer, default=0)
    updated: Mapped[int] = mapped_column(Integer, default=0)
    unchanged: Mapped[int] = mapped_column(Integer, default=0)
    waypoints: Mapped[int] = mapped_column(Integer, default=0)
    errors: Mapped[list[dict[str, str | int | None]]] = mapped_column(JSONB, default=list)
