from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, timezone

import pytest

from geocaching_planner.domain.cache import (
    Cache,
    CacheAttribute,
    CacheType,
    ContainerSize,
    Coordinates,
    ImportIssue,
    ImportRun,
    UserCacheData,
    content_hash,
)


def test_hash_is_independent_of_collection_order(cache: Cache) -> None:
    assert cache.waypoints is not None
    reordered = replace(
        cache,
        attributes=cache.attributes[::-1],
        logs=cache.logs[::-1],
        waypoints=cache.waypoints[::-1],
    )
    assert content_hash(cache) == content_hash(reordered) == cache.source_hash
    assert len(cache.source_hash) == 64


def test_every_source_field_contributes_to_hash(cache: Cache) -> None:
    changed = [
        replace(cache, gc_code="GC0002B"),
        replace(cache, name="Other"),
        replace(cache, type=CacheType.MYSTERY),
        replace(cache, container=ContainerSize.LARGE),
        replace(cache, difficulty=3),
        replace(cache, terrain=3),
        replace(cache, owner="Other"),
        replace(cache, location=Coordinates(51, 3)),
        replace(cache, source_type="Unknown Cache"),
        replace(cache, source_container="Large"),
        replace(cache, placed_at=datetime(2026, 1, 1, tzinfo=UTC)),
        replace(cache, country="NL"),
        replace(cache, state="State"),
        replace(cache, short_description="Short"),
        replace(cache, long_description="<b>Long</b>"),
        replace(cache, description_is_html=True),
        replace(cache, hint="Hint"),
        replace(cache, attributes=(CacheAttribute(1, False),)),
        replace(cache, is_available=False),
        replace(cache, is_archived=True),
        replace(cache, found_by_me=True),
        replace(cache, found_at=datetime(2026, 1, 1, tzinfo=UTC)),
        replace(cache, source="other"),
        replace(cache, source_updated_at=datetime(2026, 1, 1, tzinfo=UTC)),
        replace(cache, logs=(replace(cache.logs[0], text="Changed log"),)),
    ]
    assert all(content_hash(value) != content_hash(cache) for value in changed)
    assert cache.waypoints is not None
    waypoint_change = replace(cache, waypoints=(replace(cache.waypoints[0], name="Changed"),))
    assert content_hash(waypoint_change) != content_hash(cache)
    assert content_hash(replace(cache, waypoints=None)) != content_hash(
        replace(cache, waypoints=())
    )


def test_persistence_metadata_does_not_change_hash(cache: Cache) -> None:
    assert cache.waypoints is not None
    persisted = replace(
        cache,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        updated_at=datetime(2026, 1, 2, tzinfo=UTC),
        waypoints=tuple(
            replace(waypoint, id=index) for index, waypoint in enumerate(cache.waypoints)
        ),
    )
    assert content_hash(persisted) == content_hash(cache)
    assert not {"note", "corrected_location", "user_data"} & {field.name for field in fields(cache)}
    user = UserCacheData(cache_gc_code=cache.gc_code, note="Private note")
    assert replace(user, corrected_location=Coordinates(53, 5)).note == "Private note"
    assert content_hash(cache) == content_hash(persisted)


def test_equivalent_numeric_and_datetime_representations_hash_equally(cache: Cache) -> None:
    utc = datetime(2026, 1, 1, tzinfo=UTC)
    offset = utc.astimezone(timezone(timedelta(hours=2)))
    assert content_hash(replace(cache, placed_at=utc)) == content_hash(
        replace(cache, placed_at=offset)
    )
    assert content_hash(
        replace(cache, difficulty=2, location=Coordinates(-0.0, 0))
    ) == content_hash(replace(cache, difficulty=2.0, location=Coordinates(0, 0.0)))
    assert content_hash(replace(cache, placed_at=datetime(2026, 1, 1)))


def test_domain_aggregates_and_import_errors_are_frozen(cache: Cache) -> None:
    issue = ImportIssue(
        severity="warning",
        file="synthetic.gpx",
        gc_code=cache.gc_code,
        line=42,
        code="unknown_type",
        message="Unrecognized source type",
    )
    run = ImportRun(
        started_at=datetime(2026, 1, 1, tzinfo=UTC),
        source="pq",
        filenames=("synthetic.gpx",),
        waypoints=2,
        errors=(issue,),
    )
    for value in (cache, cache.logs[0], run, issue, UserCacheData(cache_gc_code=cache.gc_code)):
        with pytest.raises(FrozenInstanceError):
            setattr(value, fields(value)[0].name, "Changed")
    assert run.errors[0].severity == "warning"
    assert run.errors[0].line == 42
