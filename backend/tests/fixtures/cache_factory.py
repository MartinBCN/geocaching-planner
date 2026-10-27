"""Deterministic synthetic caches for repository and query tests."""

from datetime import UTC, datetime, timedelta

from geocaching_planner.domain.cache import Cache, CacheType, ContainerSize, Coordinates


def make_caches(n: int, seed: int = 0) -> tuple[Cache, ...]:
    if n < 0:
        raise ValueError("n must not be negative")
    caches: list[Cache] = []
    cache_types = tuple(CacheType)
    other_cache_types = tuple(
        cache_type
        for cache_type in cache_types
        if cache_type not in {CacheType.TRADITIONAL, CacheType.MYSTERY}
    )
    containers = tuple(ContainerSize)
    placed = datetime(2000, 1, 1, tzinfo=UTC)
    for index in range(n):
        if index < 10_000:
            lat = 51.75 + ((index * 37 + seed) % 50) / 100
            lon = 4.25 + ((index * 53 + seed) % 50) / 100
        else:
            outside_index = index - 10_000
            lat = 30 + ((outside_index * 37 + seed) % 1500) / 100
            lon = 0 + ((outside_index * 53 + seed) % 1000) / 100
        slot = index % 5
        if slot < 2:
            cache_type = CacheType.TRADITIONAL
        elif slot == 2:
            cache_type = CacheType.MYSTERY
        else:
            cache_type = other_cache_types[(index + seed) % len(other_cache_types)]
        caches.append(
            Cache(
                gc_code=f"GC{index:06d}",
                name=f"Synthetic cache {index:05d}",
                type=cache_type,
                source_type=cache_type.value,
                container=containers[(index + seed) % len(containers)],
                source_container="synthetic",
                difficulty=1 + (index % 9) / 2,
                terrain=1 + ((index + 2) % 9) / 2,
                owner="Synthetic owner",
                location=Coordinates(lat=lat, lon=lon),
                placed_at=placed + timedelta(days=index),
                is_available=index % 13 != 0,
                is_archived=index % 31 == 0,
                found_by_me=index % 2 == 0,
            )
        )
    return tuple(caches)
