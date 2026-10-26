from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest

from geocaching_planner.adapters.gpx.pq_source import (
    PocketQuerySource,
    SourceFile,
)
from geocaching_planner.domain.cache import CacheType, ContainerSize, LogType, WaypointType
from geocaching_planner.services.ports import ParsedCache, ParseError, ParseWarning

FIXTURES = Path(__file__).parents[2] / "fixtures" / "pq"


def _source(name: str, content: bytes | None = None) -> SourceFile:
    data = content if content is not None else (FIXTURES / name).read_bytes()
    return SourceFile(name, io.BytesIO(data))


def _zip_file(files: dict[str, bytes]) -> bytes:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in files.items():
            archive.writestr(name, data)
    return stream.getvalue()


def _one_cache(source: SourceFile) -> ParsedCache:
    results = list(PocketQuerySource([source]).iter_caches())
    assert len(results) == 1
    assert isinstance(results[0], ParsedCache)
    return results[0]


def test_namespace_and_schema_versions_are_equivalent() -> None:
    old = _one_cache(_source("gpx10-gs10.gpx"))
    new = _one_cache(_source("gpx11-gs101.gpx"))

    assert old.cache == new.cache
    assert old.warnings == new.warnings == ()


def test_links_separate_waypoint_files_and_reports_orphans() -> None:
    cache = (FIXTURES / "cache.gpx").read_bytes()
    waypoints = (FIXTURES / "cache-wpts.gpx").read_bytes()
    results = list(
        PocketQuerySource(
            [_source("pq.gpx", cache), _source("pq-wpts.gpx", waypoints)]
        ).iter_caches()
    )

    assert len(results) == 2
    assert isinstance(results[0], ParsedCache)
    assert results[0].cache.waypoints is not None
    assert len(results[0].cache.waypoints) == 2
    point = results[0].cache.waypoints[0]
    assert point.code == "PK0001A"
    assert point.cache_gc_code == "GC0001A"
    assert point.type is WaypointType.PARKING_AREA
    assert point.source_type == "Waypoint|Parking Area"
    assert point.location is not None
    assert (point.location.lat, point.location.lon) == (52.2, 4.4)
    unknown_waypoint = results[0].cache.waypoints[1]
    assert unknown_waypoint.type is WaypointType.OTHER
    assert unknown_waypoint.source_type == "Waypoint|Unknown kind"
    assert isinstance(results[1], ParseWarning)
    assert results[1].issue.file == "pq-wpts.gpx"
    assert results[1].issue.gc_code == "GC9999Z"
    assert results[1].issue.code == "orphan_waypoint"

    zipped = _source(
        "input.zip",
        _zip_file({"pq.gpx": cache, "pq-wpts.gpx": waypoints}),
    )
    zipped_results = list(PocketQuerySource([zipped]).iter_caches())
    assert isinstance(zipped_results[0], ParsedCache)
    assert len(zipped_results[0].cache.waypoints or ()) == 2
    assert isinstance(zipped_results[1], ParseWarning)


def test_recovers_after_corrupt_cache_entry() -> None:
    results = list(PocketQuerySource([_source("three_caches_one_corrupt_entry.gpx")]).iter_caches())

    assert len(results) == 3
    assert isinstance(results[0], ParsedCache)
    assert results[0].cache.gc_code == "GC0001A"
    assert isinstance(results[1], ParseError)
    assert results[1].issue.gc_code == "GC0002B"
    assert results[1].issue.line == 4
    assert isinstance(results[2], ParsedCache)
    assert results[2].cache.gc_code == "GC0003C"


def test_non_gpx_and_zip_without_gpx_return_file_error() -> None:
    results = list(
        PocketQuerySource(
            [
                _source("plain.gpx", b"this is not XML"),
                _source("xml-not-gpx.gpx", b"<not-gpx />"),
                _source("corrupt.zip", b"PK\x03\x04broken"),
                _source("empty.zip", _zip_file({"readme.txt": b"not GPX"})),
                _source("not_gpx.txt"),
            ]
        ).iter_caches()
    )

    assert len(results) == 5
    assert all(isinstance(result, ParseError) for result in results)
    assert all(result.issue.gc_code is None for result in results if isinstance(result, ParseError))


def test_xxe_content_is_never_resolved(tmp_path: Path) -> None:
    secret = tmp_path / "secret.txt"
    secret.write_text("synthetic secret", encoding="utf-8")
    payload = (
        (FIXTURES / "xxe.gpx").read_bytes().replace(b"/tmp/PQ_SECRET_FILE", str(secret).encode())
    )

    for filename in ("xxe.gpx", "billion_laughs.gpx"):
        content = payload if filename == "xxe.gpx" else (FIXTURES / filename).read_bytes()
        results = list(PocketQuerySource([_source(filename, content)]).iter_caches())
        assert len(results) == 1
        assert isinstance(results[0], ParseError)
        assert "synthetic secret" not in repr(results)


def test_unicode_html_description_is_decoded_and_flagged() -> None:
    parsed = _one_cache(_source("unicode_html.gpx"))

    expected = (
        (FIXTURES / "unicode_html.expected.txt").read_text(encoding="utf-8").removesuffix("\n")
    )
    assert parsed.cache.long_description == expected
    assert parsed.cache.description_is_html is True


def test_cache_status_mapping() -> None:
    content = (FIXTURES / "all_fields.gpx").read_bytes()
    found = _one_cache(
        _source(
            "found.gpx",
            content.replace(b"<sym>Geocache</sym>", b"<sym>Geocache Found</sym>"),
        )
    ).cache
    not_found = _one_cache(_source("not-found.gpx", content)).cache
    disabled = _one_cache(
        _source("disabled.gpx", content.replace(b'available="True"', b'available="False"'))
    ).cache
    archived = _one_cache(
        _source("archived.gpx", content.replace(b'archived="False"', b'archived="True"'))
    ).cache

    assert found.found_by_me is True
    assert found.found_at is None
    assert not_found.found_by_me is False
    assert not_found.found_at is None
    assert disabled.is_available is False
    assert disabled.is_archived is False
    assert archived.is_available is True
    assert archived.is_archived is True


def test_all_fields_and_optional_defaults() -> None:
    cache = _one_cache(_source("all_fields.gpx")).cache

    assert cache.type is CacheType.MULTI
    assert cache.name == "All fields cache"
    assert cache.container is ContainerSize.REGULAR
    assert cache.difficulty == 3.5
    assert cache.terrain == 4
    assert cache.source_type == "Multi-cache"
    assert cache.source_container == "Regular"
    assert cache.owner == "Synthetic owner"
    assert cache.placed_at is not None
    assert cache.placed_at.isoformat() == "2024-05-06T00:00:00+00:00"
    assert [(item.id, item.included) for item in cache.attributes] == [(2, False), (13, True)]
    assert [item.id for item in cache.logs] == [10, 20]
    assert cache.logs[0].type is LogType.FOUND_IT
    assert cache.logs[0].source_type == "Found it"
    assert cache.source == "pq"
    assert cache.source_updated_at is not None
    assert cache.source_updated_at.isoformat() == "2026-01-01T12:00:00+00:00"
    assert cache.description_is_html is True

    minimal = _one_cache(_source("missing_optional.gpx")).cache
    assert minimal.country == ""
    assert minimal.state == ""
    assert minimal.hint == ""
    assert minimal.attributes == ()
    assert minimal.logs == ()
    assert minimal.waypoints is None
    assert minimal.placed_at is None
    assert minimal.source_updated_at is None
    assert minimal.container is ContainerSize.NOT_CHOSEN


def test_unknown_values_report_warnings() -> None:
    parsed = _one_cache(_source("unknown_enums.gpx"))

    assert parsed.cache.type is CacheType.OTHER
    assert parsed.cache.container is ContainerSize.OTHER
    assert parsed.cache.logs[0].type is LogType.OTHER
    assert parsed.cache.logs[0].source_type == "Imaginary log"
    assert [issue.code for issue in parsed.warnings] == ["unknown_type", "unknown_container"]
    assert all(issue.gc_code == "GC9999Z" for issue in parsed.warnings)
    assert all(issue.file == "unknown_enums.gpx" for issue in parsed.warnings)


def test_waypoint_without_coordinates_is_linked() -> None:
    cache = (FIXTURES / "gpx10-gs10.gpx").read_bytes()
    waypoints = (
        b'<gpx xmlns="http://www.topografix.com/GPX/1/1" version="1.1">'
        b"<wpt><name>PK0001A</name><desc>Parking</desc>"
        b"<type>Waypoint|Parking Area</type></wpt></gpx>"
    )
    results = list(
        PocketQuerySource(
            [_source("pq.gpx", cache), _source("pq-wpts.gpx", waypoints)]
        ).iter_caches()
    )

    assert isinstance(results[0], ParsedCache)
    assert results[0].cache.waypoints is not None
    assert results[0].cache.waypoints[0].location is None


def test_zip_limits_and_nested_archives_are_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    import geocaching_planner.adapters.gpx.pq_source as pq_source

    nested = _zip_file({"inner.zip": b"PK\x03\x04"})
    nested_result = list(PocketQuerySource([_source("nested.zip", nested)]).iter_caches())
    assert len(nested_result) == 1
    assert isinstance(nested_result[0], ParseError)

    monkeypatch.setattr(pq_source, "_MAX_MEMBER_SIZE", 8)
    oversized = _zip_file({"large.gpx": b"<gpx>content</gpx>"})
    oversized_result = list(PocketQuerySource([_source("oversized.zip", oversized)]).iter_caches())
    assert len(oversized_result) == 1
    assert isinstance(oversized_result[0], ParseError)
    assert oversized_result[0].issue.code == "zip_member_too_large"

    monkeypatch.setattr(pq_source, "_MAX_MEMBER_SIZE", 1024)
    monkeypatch.setattr(pq_source, "_MAX_ARCHIVE_GPX_SIZE", 10)
    total_oversized = _zip_file({"one.gpx": b"123456", "two.gpx": b"abcdef"})
    total_result = list(
        PocketQuerySource([_source("total-oversized.zip", total_oversized)]).iter_caches()
    )
    assert len(total_result) == 1
    assert isinstance(total_result[0], ParseError)
    assert total_result[0].issue.code == "zip_too_large"


def test_waypoint_only_import_reports_orphans() -> None:
    content = (
        b'<gpx xmlns="http://www.topografix.com/GPX/1/1" version="1.1">'
        b'<wpt lat="52" lon="4"><name>PK1234X</name><desc>Parking</desc>'
        b"<type>Waypoint|Parking Area</type></wpt></gpx>"
    )
    results = list(PocketQuerySource([_source("only-wpts.gpx", content)]).iter_caches())

    assert len(results) == 1
    assert isinstance(results[0], ParseWarning)
    assert results[0].issue.gc_code == "GC1234X"
    assert results[0].issue.file == "only-wpts.gpx"
