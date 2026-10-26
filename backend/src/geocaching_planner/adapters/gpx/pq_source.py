"""Streaming, hardened Pocket Query GPX/ZIP parser."""

import re
import zipfile
import zlib
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime, time
from pathlib import PurePosixPath
from typing import IO, BinaryIO

from lxml import etree

from geocaching_planner.domain.cache import (
    Cache,
    CacheAttribute,
    CacheLog,
    CacheType,
    CacheWaypoint,
    ContainerSize,
    Coordinates,
    LogType,
    WaypointType,
)
from geocaching_planner.services.ports import (
    CacheParseResult,
    ParsedCache,
    ParseError,
    ParseIssue,
    ParseWarning,
)

_MAX_MEMBER_SIZE = 100 * 1024 * 1024
_MAX_ARCHIVE_GPX_SIZE = 500 * 1024 * 1024
_CHUNK_SIZE = 1024 * 1024
_GPX_NAMESPACES = {
    "http://www.topografix.com/GPX/1/0",
    "http://www.topografix.com/GPX/1/1",
}
_ENTITY_DECLARATION = re.compile(rb"<!\s*(?:DOCTYPE|ENTITY)\b", re.IGNORECASE)
_GC_CODE = re.compile(r"^GC([0-9A-Z]+)$", re.IGNORECASE)
_WAYPOINT_CODE = re.compile(r"^([0-9A-Z]{2})([0-9A-Z]+)$", re.IGNORECASE)

_CACHE_TYPES: dict[str, CacheType] = {
    "traditional cache": CacheType.TRADITIONAL,
    "multi-cache": CacheType.MULTI,
    "unknown cache": CacheType.MYSTERY,
    "letterbox hybrid": CacheType.LETTERBOX,
    "earthcache": CacheType.EARTHCACHE,
    "wherigo cache": CacheType.WHERIGO,
    "virtual cache": CacheType.VIRTUAL,
    "event cache": CacheType.EVENT,
    "cache in trash out event": CacheType.CITO,
    "mega-event cache": CacheType.MEGA,
    "giga-event cache": CacheType.GIGA,
    "webcam cache": CacheType.WEBCAM,
    "lab cache": CacheType.LAB,
}
_CONTAINERS: dict[str, ContainerSize] = {item.value.casefold(): item for item in ContainerSize}
_WAYPOINT_TYPES: dict[str, WaypointType] = {
    item.value.casefold(): item for item in WaypointType if item is not WaypointType.OTHER
}
_LOG_TYPES: dict[str, LogType] = {
    item.value.casefold(): item for item in LogType if item is not LogType.OTHER
}


@dataclass(frozen=True)
class SourceFile:
    filename: str
    stream: BinaryIO


@dataclass(frozen=True)
class _FilePlan:
    source: SourceFile
    is_zip: bool
    members: tuple[str | None, ...]

    @property
    def waypoint_members(self) -> tuple[str | None, ...]:
        return tuple(
            member
            for member in self.members
            if PurePosixPath(member or self.source.filename).name.casefold().endswith("-wpts.gpx")
        )

    @property
    def cache_members(self) -> tuple[str | None, ...]:
        return tuple(member for member in self.members if member not in self.waypoint_members)


@dataclass(frozen=True)
class _Waypoint:
    gc_code: str
    value: CacheWaypoint
    file: str


class _ForbiddenXmlDeclarationError(Exception):
    pass


class _DeclarationRejectingStream:
    """Detect declarations in bounded reads before the XML parser can consume them."""

    def __init__(self, stream: IO[bytes]) -> None:
        self._stream = stream
        self._tail = b""

    def read(self, size: int = -1) -> bytes:
        data = self._stream.read(size)
        if b"\x00" in data:
            raise _ForbiddenXmlDeclarationError
        candidate = self._tail + data
        if _ENTITY_DECLARATION.search(candidate):
            raise _ForbiddenXmlDeclarationError
        self._tail = candidate[-16:]
        return data


class PocketQuerySource:
    source_name = "pq"

    def __init__(self, files: Sequence[SourceFile]) -> None:
        self._files = tuple(files)

    def iter_caches(self) -> Iterator[CacheParseResult]:
        plans: list[_FilePlan] = []
        for source in self._files:
            plan, issue = self._inspect(source)
            if issue is not None:
                yield ParseError(issue=issue)
            elif plan is not None:
                plans.append(plan)

        indexed: dict[str, list[_Waypoint]] = {}
        waypoint_data_supplied = any(plan.waypoint_members for plan in plans)
        for plan in plans:
            for member in plan.waypoint_members:
                try:
                    for element, line in self._iter_waypoints(plan, member):
                        try:
                            parsed_waypoint = _parse_waypoint(element)
                        except ValueError, TypeError:
                            yield ParseError(
                                issue=self._issue(
                                    plan,
                                    member,
                                    "invalid_waypoint",
                                    "Waypoint entry has invalid fields.",
                                    line=line,
                                )
                            )
                            continue
                        if parsed_waypoint is None:
                            continue
                        indexed.setdefault(parsed_waypoint.cache_gc_code, []).append(
                            _Waypoint(
                                parsed_waypoint.cache_gc_code,
                                parsed_waypoint,
                                _display_file(plan.source.filename, member),
                            )
                        )
                except _GpxReadError as exc:
                    yield ParseError(
                        issue=self._issue(plan, member, exc.code, exc.message, line=exc.line)
                    )

        cache_codes: set[str] = set()
        for plan in plans:
            for member in plan.cache_members:
                try:
                    for element, line in self._iter_waypoints(plan, member):
                        extension = _cache_extension(element)
                        if extension is None:
                            continue
                        gc_code = _text(element, "name").upper()
                        try:
                            cache, warnings = _parse_cache(
                                element,
                                extension,
                                gc_code,
                                _display_file(plan.source.filename, member),
                            )
                        except ValueError, TypeError, OverflowError:
                            yield ParseError(
                                issue=self._issue(
                                    plan,
                                    member,
                                    "invalid_cache_entry",
                                    "Cache entry contains invalid or missing required fields.",
                                    gc_code=gc_code or None,
                                    line=line,
                                )
                            )
                            continue
                        cache_codes.add(cache.gc_code)
                        if waypoint_data_supplied:
                            cache = replace(
                                cache,
                                waypoints=tuple(
                                    record.value for record in indexed.get(cache.gc_code, ())
                                ),
                            )
                        yield ParsedCache(
                            cache=cache,
                            warnings=warnings,
                        )
                except _GpxReadError as exc:
                    yield ParseError(
                        issue=self._issue(plan, member, exc.code, exc.message, line=exc.line)
                    )

        for gc_code, orphaned_waypoints in indexed.items():
            if gc_code in cache_codes:
                continue
            for waypoint in orphaned_waypoints:
                yield ParseWarning(
                    issue=ParseIssue(
                        severity="warning",
                        file=waypoint.file,
                        gc_code=gc_code,
                        line=None,
                        code="orphan_waypoint",
                        message=(
                            f"Waypoint {waypoint.value.code} refers to {gc_code}, "
                            "but no matching cache was included in this import."
                        ),
                    )
                )

    def _inspect(self, source: SourceFile) -> tuple[_FilePlan | None, ParseIssue | None]:
        filename = source.filename
        suffix = PurePosixPath(filename).suffix.casefold()
        if suffix not in {".gpx", ".zip"}:
            return None, self._file_issue(
                filename, "unsupported_file", "Expected a .gpx or .zip input."
            )
        try:
            source.stream.seek(0)
            magic = source.stream.read(4)
            source.stream.seek(0)
        except OSError, ValueError, AttributeError:
            return None, self._file_issue(
                filename, "unreadable_file", "Input must be a readable, seekable binary stream."
            )
        is_zip = magic in {b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08"}
        if not is_zip:
            if suffix != ".gpx":
                return None, self._file_issue(
                    filename, "invalid_zip", "The .zip input does not contain a ZIP archive."
                )
            return _FilePlan(source, False, (None,)), None

        try:
            with zipfile.ZipFile(source.stream) as archive:
                infos = [info for info in archive.infolist() if not info.is_dir()]
                if any(info.filename.casefold().endswith(".zip") for info in infos):
                    raise _GpxReadError("nested_archive", "Nested ZIP archives are not supported.")
                gpx_infos = [
                    info
                    for info in infos
                    if PurePosixPath(info.filename).suffix.casefold() == ".gpx"
                ]
                if not gpx_infos:
                    raise _GpxReadError(
                        "no_gpx_members", "ZIP input does not contain any .gpx members."
                    )
                if any(info.file_size > _MAX_MEMBER_SIZE for info in gpx_infos):
                    raise _GpxReadError(
                        "zip_member_too_large",
                        "A GPX ZIP member exceeds the 100 MB uncompressed limit.",
                    )
                if sum(info.file_size for info in gpx_infos) > _MAX_ARCHIVE_GPX_SIZE:
                    raise _GpxReadError(
                        "zip_too_large",
                        "Combined uncompressed GPX members exceed the 500 MB limit.",
                    )

                actual_total = 0
                for info in gpx_infos:
                    member_size = 0
                    with archive.open(info) as member_stream:
                        first = member_stream.read(4)
                        if first in {b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08"}:
                            raise _GpxReadError(
                                "nested_archive",
                                "A ZIP archive was found inside a GPX ZIP member.",
                            )
                        member_size += len(first)
                        if actual_total + member_size > _MAX_ARCHIVE_GPX_SIZE:
                            raise _GpxReadError(
                                "zip_too_large",
                                "Combined uncompressed GPX members exceed the 500 MB limit.",
                            )
                        while chunk := member_stream.read(_CHUNK_SIZE):
                            member_size += len(chunk)
                            if member_size > _MAX_MEMBER_SIZE:
                                raise _GpxReadError(
                                    "zip_member_too_large",
                                    "A GPX ZIP member exceeds the 100 MB uncompressed limit.",
                                )
                            if actual_total + member_size > _MAX_ARCHIVE_GPX_SIZE:
                                raise _GpxReadError(
                                    "zip_too_large",
                                    "Combined uncompressed GPX members exceed the 500 MB limit.",
                                )
                    actual_total += member_size
                return _FilePlan(source, True, tuple(info.filename for info in gpx_infos)), None
        except _GpxReadError as exc:
            return None, self._file_issue(filename, exc.code, exc.message)
        except (
            EOFError,
            NotImplementedError,
            OSError,
            RuntimeError,
            zipfile.BadZipFile,
            zipfile.LargeZipFile,
            zlib.error,
        ):
            return None, self._file_issue(
                filename, "invalid_zip", "ZIP input is corrupt or unreadable."
            )

    @contextmanager
    def _open_member(self, plan: _FilePlan, member: str | None) -> Iterator[IO[bytes]]:
        if not plan.is_zip:
            plan.source.stream.seek(0)
            yield plan.source.stream
            return
        try:
            with zipfile.ZipFile(plan.source.stream) as archive:
                if member is None:
                    raise _GpxReadError("invalid_gpx", "Missing GPX member name.")
                with archive.open(member) as stream:
                    yield stream
        except (
            EOFError,
            KeyError,
            NotImplementedError,
            OSError,
            RuntimeError,
            zipfile.BadZipFile,
            zlib.error,
        ) as exc:
            raise _GpxReadError("invalid_zip_member", "Unable to read GPX ZIP member.") from exc

    def _iter_waypoints(
        self, plan: _FilePlan, member: str | None
    ) -> Iterator[tuple[etree._Element, int | None]]:
        try:
            with self._open_member(plan, member) as stream:
                parser = etree.iterparse(
                    _DeclarationRejectingStream(stream),
                    events=("start", "end"),
                    tag=("{*}gpx", "{*}wpt"),
                    resolve_entities=False,
                    no_network=True,
                    load_dtd=False,
                    huge_tree=False,
                    recover=False,
                    collect_ids=False,
                )
                root_seen = False
                for event, element in parser:
                    if not root_seen:
                        root_seen = True
                        _validate_root(element.getroottree().getroot())
                    if event != "end" or _local_name(element) != "wpt":
                        continue
                    line = element.sourceline
                    yield element, line
                    _clear_element(element)
                if not root_seen:
                    _validate_root(parser.root)
        except _ForbiddenXmlDeclarationError as exc:
            raise _GpxReadError(
                "xml_entities_rejected", "XML entity declarations are not allowed."
            ) from exc
        except etree.XMLSyntaxError as exc:
            raise _GpxReadError(
                "malformed_xml", "GPX XML is malformed.", line=exc.position[0] or None
            ) from exc
        except (_GpxReadError, LookupError, OSError, ValueError) as exc:
            if isinstance(exc, _GpxReadError):
                raise
            raise _GpxReadError("invalid_gpx", "Unable to read GPX input.") from exc

    def _issue(
        self,
        plan: _FilePlan,
        member: str | None,
        code: str,
        message: str,
        *,
        gc_code: str | None = None,
        line: int | None = None,
    ) -> ParseIssue:
        return ParseIssue(
            severity="error",
            file=_display_file(plan.source.filename, member),
            gc_code=gc_code,
            line=line,
            code=code,
            message=message,
        )

    @staticmethod
    def _file_issue(filename: str, code: str, message: str) -> ParseIssue:
        return ParseIssue(
            severity="error",
            file=filename,
            gc_code=None,
            line=None,
            code=code,
            message=message,
        )


class _GpxReadError(Exception):
    def __init__(self, code: str, message: str, *, line: int | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.line = line


def _display_file(filename: str, member: str | None) -> str:
    return filename if member is None else f"{filename}:{member}"


def _local_name(element: etree._Element) -> str:
    return etree.QName(element).localname


def _validate_root(element: etree._Element) -> None:
    root = etree.QName(element)
    if root.localname != "gpx" or root.namespace not in _GPX_NAMESPACES:
        raise _GpxReadError("not_gpx", "XML root is not a supported GPX 1.0 or 1.1 document.")


def _text(element: etree._Element, name: str, default: str = "") -> str:
    child = _child(element, name)
    return default if child is None else _joined_text(child).strip()


def _joined_text(element: etree._Element) -> str:
    if len(element) == 0:
        value = element.text
        if isinstance(value, bytes):
            return value.decode("utf-8")
        return value or ""
    return "".join(
        value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value
        for value in element.itertext()
    )


def _child(element: etree._Element, name: str) -> etree._Element | None:
    return element.find(f"{{*}}{name}")


def _cache_extension(wpt: etree._Element) -> etree._Element | None:
    for child in wpt:
        if _local_name(child) != "extensions":
            continue
        for extension in child.iter():
            if _local_name(extension) == "cache":
                return extension
    return None


def _parse_cache(
    wpt: etree._Element, extension: etree._Element, gc_code: str, source_file: str
) -> tuple[Cache, tuple[ParseIssue, ...]]:
    match = _GC_CODE.fullmatch(gc_code)
    if match is None:
        raise ValueError("Invalid GC code")
    gc_code = f"GC{match.group(1).upper()}"
    source_type = _text(extension, "type")
    source_container = _text(extension, "container")
    cache_type = _CACHE_TYPES.get(source_type.casefold(), CacheType.OTHER)
    container = _CONTAINERS.get(source_container.casefold(), ContainerSize.OTHER)
    warnings: list[ParseIssue] = []
    source_line = wpt.sourceline
    line = source_line if isinstance(source_line, int) else None
    if cache_type is CacheType.OTHER:
        warnings.append(
            ParseIssue(
                severity="warning",
                file=source_file,
                gc_code=gc_code,
                line=line,
                code="unknown_type",
                message=f"Unrecognized cache type {source_type!r}; mapped to Other.",
            )
        )
    if container is ContainerSize.OTHER:
        warnings.append(
            ParseIssue(
                severity="warning",
                file=source_file,
                gc_code=gc_code,
                line=line,
                code="unknown_container",
                message=f"Unrecognized container {source_container!r}; mapped to Other.",
            )
        )

    lat = float(wpt.attrib["lat"])
    lon = float(wpt.attrib["lon"])
    attributes: list[CacheAttribute] = []
    for item in _descendants(extension, "attribute"):
        attributes.append(
            CacheAttribute(
                id=int(item.attrib["id"]),
                included=item.attrib.get("inc", "1").casefold() in {"1", "true", "yes"},
                text=_joined_text(item).strip(),
            )
        )
    attributes.sort(key=lambda item: (item.id, item.included, item.text.casefold(), item.text))

    logs: list[CacheLog] = []
    for log in _descendants(extension, "log"):
        log_id = int(log.attrib["id"])
        source_log_type = _text(log, "type")
        log_type = _LOG_TYPES.get(source_log_type.casefold(), LogType.OTHER)
        logs.append(
            CacheLog(
                id=log_id,
                cache_gc_code=gc_code,
                type=log_type,
                source_type=source_log_type,
                finder=_text(log, "finder"),
                logged_at=_parse_datetime(_text(log, "date")),
                text=_text(log, "text"),
            )
        )
    logs.sort(key=lambda item: (item.logged_at, item.id, item.finder.casefold(), item.text))

    placed_by = _child(extension, "placed_by")
    placed_at = _parse_optional_date(
        placed_by.attrib.get("date") if placed_by is not None else None
    )
    description = _child(wpt, "desc")
    description_is_html = description is not None and description.attrib.get(
        "html", ""
    ).casefold() in {"true", "1", "yes"}
    long_description = _child(extension, "long_description")
    short_description = _child(extension, "short_description")
    description_is_html = description_is_html or any(
        item is not None and item.attrib.get("html", "").casefold() in {"true", "1", "yes"}
        for item in (short_description, long_description)
    )
    time_element = _text(wpt, "time")
    archived = _boolean(extension.attrib.get("archived"), default=False)
    available = _boolean(extension.attrib.get("available"), default=True)
    found_by_me = _text(wpt, "sym") == "Geocache Found"
    cache = Cache(
        gc_code=gc_code,
        name=_text(extension, "name"),
        type=cache_type,
        source_type=source_type,
        container=container,
        source_container=source_container,
        difficulty=float(_text(extension, "difficulty")),
        terrain=float(_text(extension, "terrain")),
        owner=_text(extension, "owner"),
        location=Coordinates(lat, lon),
        placed_at=placed_at,
        country=_text(extension, "country"),
        state=_text(extension, "state"),
        short_description=_text(extension, "short_description"),
        long_description=_text(extension, "long_description"),
        description_is_html=description_is_html,
        hint=_text(extension, "encoded_hints"),
        attributes=tuple(attributes),
        is_available=available,
        is_archived=archived,
        found_by_me=found_by_me,
        found_at=None,
        source="pq",
        source_updated_at=_parse_optional_datetime(time_element),
        waypoints=None,
        logs=tuple(logs),
    )
    return cache, tuple(warnings)


def _parse_waypoint(element: etree._Element) -> CacheWaypoint | None:
    source_code = _text(element, "name").upper()
    match = _WAYPOINT_CODE.fullmatch(source_code)
    if match is None:
        return None
    gc_code = f"GC{match.group(2)}"
    try:
        location = Coordinates(float(element.attrib["lat"]), float(element.attrib["lon"]))
    except KeyError, ValueError, TypeError:
        location = None
    source_type = _text(element, "type")
    normalized_type = source_type
    if "|" in normalized_type:
        normalized_type = normalized_type.split("|", maxsplit=1)[1].strip()
    if not normalized_type:
        normalized_type = _text(element, "desc")
    waypoint_type = _WAYPOINT_TYPES.get(normalized_type.casefold(), WaypointType.OTHER)
    waypoint = CacheWaypoint(
        cache_gc_code=gc_code,
        code=source_code,
        name=_text(element, "cmt") or _text(element, "desc"),
        type=waypoint_type,
        source_type=source_type,
        prefix=match.group(1).upper(),
        location=location,
        description=_text(element, "desc"),
    )
    return waypoint


def _descendants(element: etree._Element, name: str) -> Iterator[etree._Element]:
    return element.iterdescendants(f"{{*}}{name}")


def _parse_optional_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.combine(date.fromisoformat(value[:10]), time.min, tzinfo=UTC)
    except ValueError:
        return _parse_optional_datetime(value)


def _parse_optional_datetime(value: str) -> datetime | None:
    if not value:
        return None
    return _parse_datetime(value)


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed


def _boolean(value: str | None, *, default: bool) -> bool:
    if value is None:
        return default
    return value.casefold() in {"true", "1", "yes"}


def _clear_element(element: etree._Element) -> None:
    element.clear()
    parent = element.getparent()
    if parent is not None:
        while element.getprevious() is not None:
            del parent[0]
