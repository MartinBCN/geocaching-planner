"""Preflight validation for staged Pocket Query uploads."""

import re
import zipfile
import zlib
from collections.abc import Sequence
from pathlib import Path, PurePosixPath
from typing import IO

from lxml import etree

MAX_MEMBER_SIZE = 100 * 1024 * 1024
MAX_EXPANDED_SIZE = 500 * 1024 * 1024
_CHUNK_SIZE = 1024 * 1024
_XML_DECLARATION = re.compile(rb"<!\s*(?:DOCTYPE|ENTITY)\b", re.IGNORECASE)
_ZIP_MAGIC = {b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08"}
_GPX_NAMESPACES = {
    "http://www.topografix.com/GPX/1/0",
    "http://www.topografix.com/GPX/1/1",
}


class UnsupportedInputError(ValueError):
    """The staged input is not a supported GPX or ZIP Pocket Query."""


class UploadTooLargeError(OverflowError):
    """A staged input exceeds a configured compressed or expanded-size limit."""


def validate_uploads(staged: Sequence[tuple[str, Path]]) -> None:
    expanded_size = 0
    for filename, path in staged:
        suffix = PurePosixPath(filename).suffix.casefold()
        with path.open("rb") as stream:
            magic = stream.read(4)
        is_zip = magic in _ZIP_MAGIC
        if suffix == ".zip":
            if not is_zip:
                raise UnsupportedInputError(f"{filename} is not a ZIP archive.")
            expanded_size = _validate_archive(filename, path, expanded_size)
        else:
            if is_zip:
                raise UnsupportedInputError(f"{filename} has ZIP content but a .gpx extension.")
            with path.open("rb") as stream:
                _validate_gpx_stream(stream, filename)


def _validate_archive(filename: str, path: Path, current_size: int) -> int:
    try:
        with zipfile.ZipFile(path) as archive:
            files = [member for member in archive.infolist() if not member.is_dir()]
            if any(member.filename.casefold().endswith(".zip") for member in files):
                raise UnsupportedInputError(f"{filename} contains a nested ZIP archive.")
            if current_size + sum(member.file_size for member in files) > MAX_EXPANDED_SIZE:
                raise UploadTooLargeError("Expanded archive content exceeds the 500 MB limit.")
            members = [
                member
                for member in files
                if PurePosixPath(member.filename).suffix.casefold() == ".gpx"
            ]
            if not members:
                raise UnsupportedInputError(f"{filename} does not contain any .gpx files.")
            for member in files:
                if PurePosixPath(member.filename).suffix.casefold() == ".gpx":
                    if member.file_size > MAX_MEMBER_SIZE:
                        raise UploadTooLargeError(f"{filename} contains a GPX member over 100 MB.")
                    with archive.open(member) as stream:
                        member_size = _validate_gpx_stream(
                            stream,
                            f"{filename}:{member.filename}",
                            current_size=current_size,
                        )
                    current_size += member_size
                else:
                    current_size += member.file_size
    except (
        EOFError,
        KeyError,
        NotImplementedError,
        OSError,
        RuntimeError,
        zipfile.BadZipFile,
        zipfile.LargeZipFile,
        zlib.error,
    ) as exc:
        raise UnsupportedInputError(f"{filename} is a corrupt or unreadable ZIP archive.") from exc
    return current_size


def _validate_gpx_stream(stream: IO[bytes], filename: str, *, current_size: int = 0) -> int:
    parser = etree.XMLPullParser(
        events=("start",),
        resolve_entities=False,
        no_network=True,
        load_dtd=False,
        huge_tree=False,
    )
    size = 0
    tail = b""
    root_valid = False
    try:
        while chunk := stream.read(_CHUNK_SIZE):
            size += len(chunk)
            if current_size + size > MAX_EXPANDED_SIZE:
                raise UploadTooLargeError("Expanded archive content exceeds the 500 MB limit.")
            if size == len(chunk) and chunk[:4] in _ZIP_MAGIC:
                raise UnsupportedInputError(f"{filename} contains a nested ZIP archive.")
            candidate = tail + chunk
            if _XML_DECLARATION.search(candidate):
                raise UnsupportedInputError(f"{filename} contains a forbidden XML declaration.")
            tail = candidate[-16:]
            parser.feed(chunk)
            for _, element in parser.read_events():
                if not root_valid and isinstance(element, etree._Element):
                    qname = etree.QName(element)
                    if qname.localname != "gpx" or qname.namespace not in _GPX_NAMESPACES:
                        raise UnsupportedInputError(
                            f"{filename} does not contain GPX 1.0 or 1.1 content."
                        )
                    root_valid = True
        parser.close()
    except etree.XMLSyntaxError as exc:
        raise UnsupportedInputError(f"{filename} is not a well-formed GPX document.") from exc
    if not root_valid:
        raise UnsupportedInputError(f"{filename} is empty or does not contain GPX content.")
    return size
