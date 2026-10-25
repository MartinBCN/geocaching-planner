"""Download BRouter routing segments (`.rd5`) for the configured tiles.

Run through `mise run brouter:segments`. Tiles come from BROUTER_SEGMENTS (comma-separated,
default E0_N50,E5_N50). Complete files already on disk are skipped without a request; each download
goes to a `.part` file that is renamed only once it is complete. Exits 1 when any tile fails.
"""

import os
import re
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import httpx

BASE_URL = "https://brouter.de/brouter/segments4/"
DEFAULT_TILES = ("E0_N50", "E5_N50")
# Tile names such as E5_N50; the strict pattern rejects anything that could escape the directory.
TILE_PATTERN = re.compile(r"^[EW]\d{1,3}_[NS]\d{1,2}$")
# .../backend/scripts/brouter_segments.py -> repository root
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SEGMENTS_DIR = REPO_ROOT / "infra" / "brouter" / "segments"

Status = Literal["downloaded", "skipped", "failed"]


@dataclass(frozen=True)
class TileResult:
    tile: str
    status: Status
    message: str


def parse_tiles(value: str | None) -> tuple[str, ...]:
    """Parse BROUTER_SEGMENTS; fall back to the defaults when unset or empty."""
    if value is None or not value.strip():
        return DEFAULT_TILES
    tiles = tuple(part.strip() for part in value.split(",") if part.strip())
    invalid = [tile for tile in tiles if not TILE_PATTERN.match(tile)]
    if invalid:
        raise ValueError(f"invalid BROUTER_SEGMENTS tile name(s): {', '.join(invalid)}")
    return tiles


def download_tile(client: httpx.Client, tile: str, dest_dir: Path) -> TileResult:
    """Fetch one `<tile>.rd5`, skipping it when it is already complete on disk."""
    final = dest_dir / f"{tile}.rd5"
    if final.exists():
        return TileResult(tile, "skipped", "already present")

    part = dest_dir / f"{tile}.rd5.part"
    try:
        size = 0
        with client.stream("GET", f"{BASE_URL}{tile}.rd5", follow_redirects=True) as response:
            response.raise_for_status()
            with part.open("wb") as handle:
                for chunk in response.iter_bytes():
                    handle.write(chunk)
                    size += len(chunk)
        os.replace(part, final)
    except (httpx.HTTPError, OSError) as exc:
        part.unlink(missing_ok=True)
        return TileResult(tile, "failed", str(exc))
    return TileResult(tile, "downloaded", f"{size / 1_000_000:.1f} MB")


def run(tiles: Sequence[str], dest_dir: Path, client: httpx.Client) -> list[TileResult]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    results: list[TileResult] = []
    for index, tile in enumerate(tiles, start=1):
        print(f"[{index}/{len(tiles)}] {tile}.rd5 ...", flush=True)
        result = download_tile(client, tile, dest_dir)
        print(f"    {result.status}: {result.message}", flush=True)
        results.append(result)
    return results


def main() -> int:
    try:
        tiles = parse_tiles(os.environ.get("BROUTER_SEGMENTS"))
    except ValueError as exc:
        print(f"brouter:segments: {exc}", file=sys.stderr)
        return 2

    dest_dir = Path(os.environ.get("BROUTER_SEGMENTS_DIR", DEFAULT_SEGMENTS_DIR))
    with httpx.Client(timeout=httpx.Timeout(60.0)) as client:
        results = run(tiles, dest_dir, client)

    downloaded = sum(r.status == "downloaded" for r in results)
    skipped = sum(r.status == "skipped" for r in results)
    failed = [r for r in results if r.status == "failed"]
    print(f"Summary: {downloaded} downloaded, {skipped} skipped, {len(failed)} failed")
    for result in failed:
        print(f"FAILED {result.tile}.rd5: {result.message}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
