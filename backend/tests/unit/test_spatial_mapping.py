import struct

import pytest
from geoalchemy2.elements import WKBElement

from geocaching_planner.adapters.db.spatial import coordinates_to_point, point_to_coordinates
from geocaching_planner.domain.cache import Coordinates


@pytest.mark.parametrize("byte_order", ["<", ">"])
@pytest.mark.parametrize("hex_encoding", [False, True])
def test_point_wkb_decodes_both_endian_formats(byte_order: str, hex_encoding: bool) -> None:
    data = struct.pack(f"{byte_order}BIdd", byte_order == "<", 1, 4.3, 52.1)
    point = WKBElement(data.hex() if hex_encoding else data, srid=4326, extended=False)
    assert point_to_coordinates(point) == Coordinates(52.1, 4.3)
    assert coordinates_to_point(Coordinates(52.1, 4.3)).data == "POINT(4.3 52.1)"


@pytest.mark.parametrize(
    "data",
    [b"", b"\x01", struct.pack("<BIdd", 1, 2, 4.3, 52.1), struct.pack("<BIdd", 2, 1, 4.3, 52.1)],
)
def test_non_point_wkb_is_rejected(data: bytes) -> None:
    point = WKBElement(data, srid=4326, extended=False)
    with pytest.raises(ValueError, match="Point WKB"):
        point_to_coordinates(point)


@pytest.mark.parametrize("byte_order", ["<", ">"])
def test_extended_point_wkb_preserves_coordinate_order(byte_order: str) -> None:
    data = struct.pack(f"{byte_order}BIIdd", byte_order == "<", 0x20000001, 4326, 4.3, 52.1)
    point = WKBElement(data, srid=4326, extended=True)
    assert point_to_coordinates(point) == Coordinates(52.1, 4.3)


def test_extended_point_wkb_rejects_wrong_srid() -> None:
    data = struct.pack("<BIIdd", 1, 0x20000001, 3857, 4.3, 52.1)
    with pytest.raises(ValueError, match="SRID 4326"):
        point_to_coordinates(WKBElement(data, srid=3857, extended=True))
