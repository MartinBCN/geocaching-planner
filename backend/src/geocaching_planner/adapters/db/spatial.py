import struct

from geoalchemy2.elements import WKBElement, WKTElement
from sqlalchemy import func
from sqlalchemy.sql.functions import coalesce

from geocaching_planner.adapters.db.models import CacheModel, UserCacheDataModel
from geocaching_planner.domain.cache import Coordinates


def coordinates_to_point(location: Coordinates) -> WKTElement:
    return WKTElement(f"POINT({location.lon} {location.lat})", srid=4326)


def point_to_coordinates(point: WKBElement) -> Coordinates:
    """Decode PostGIS's two-dimensional Point WKB without a geometry dependency."""
    wkb = point.data
    data = bytes.fromhex(wkb) if isinstance(wkb, str) else bytes(wkb)
    if len(data) not in (21, 25) or data[0] not in (0, 1):
        raise ValueError("Expected a two-dimensional Point WKB")
    byte_order = "<" if data[0] else ">"
    geometry_type = struct.unpack(f"{byte_order}I", data[1:5])[0]
    has_srid = geometry_type == 0x20000001
    if geometry_type not in (1, 0x20000001) or len(data) != (25 if has_srid else 21):
        raise ValueError("Expected a Point WKB")
    if has_srid and struct.unpack(f"{byte_order}I", data[5:9])[0] != 4326:
        raise ValueError("Expected SRID 4326")
    lon, lat = struct.unpack(f"{byte_order}dd", data[9:] if has_srid else data[5:])
    return Coordinates(lat=lat, lon=lon)


def effective_location() -> coalesce[WKBElement]:
    """Projection/order expression; spatial predicates must use indexed branches."""
    return func.coalesce(UserCacheDataModel.corrected_location, CacheModel.location)
