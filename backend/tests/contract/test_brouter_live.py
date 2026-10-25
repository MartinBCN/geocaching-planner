import os
from pathlib import Path

import httpx
import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SEGMENTS_DIR = Path(
    os.environ.get("BROUTER_SEGMENTS_DIR", REPO_ROOT / "infra" / "brouter" / "segments")
)
BROUTER_URL = os.environ.get("BROUTER_URL", "http://127.0.0.1:17777")

pytestmark = [
    pytest.mark.brouter,
    pytest.mark.enable_socket,
    pytest.mark.skipif(
        not (SEGMENTS_DIR / "E5_N50.rd5").exists(),
        reason="requires E5_N50.rd5 (run `mise run brouter:segments`)",
    ),
]


def test_short_route_within_segment_coverage() -> None:
    """AC2: a short route inside E5_N50 returns a GeoJSON LineString with elevation."""
    params = {
        "lonlats": "6.00,51.00|6.02,51.01",
        "profile": "trekking",
        "alternativeidx": "0",
        "format": "geojson",
    }
    response = httpx.get(f"{BROUTER_URL}/brouter", params=params, timeout=30.0)

    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "FeatureCollection"
    geometry = body["features"][0]["geometry"]
    assert geometry["type"] == "LineString"
    assert len(geometry["coordinates"]) >= 2
    assert all(len(coord) >= 3 for coord in geometry["coordinates"])
