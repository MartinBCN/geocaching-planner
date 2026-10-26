"""Generate large synthetic Pocket Query fixtures for the parser performance test."""


def make_pq(cache_count: int) -> bytes:
    if cache_count < 0:
        raise ValueError("cache_count must not be negative")
    header = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<gpx xmlns="http://www.topografix.com/GPX/1/0" '
        'xmlns:gs="http://www.groundspeak.com/cache/1/0" '
        'version="1.0" creator="synthetic-perf-fixture">'
    )
    entries = []
    for index in range(cache_count):
        gc_code = f"GC{index:06d}"
        logs = "".join(
            f'<gs:log id="{index * 4 + log}"><gs:date>2026-01-01T00:00:00Z</gs:date>'
            f"<gs:type>Found it</gs:type><gs:finder>Synthetic {log}</gs:finder>"
            f"<gs:text>Log {log} for cache {index}</gs:text></gs:log>"
            for log in range(4)
        )
        entries.append(
            f'<wpt lat="52.1" lon="4.3"><time>2026-01-01T00:00:00Z</time><name>{gc_code}</name>'
            f'<sym>Geocache</sym><extensions><gs:cache id="{index}" '
            'available="True" archived="False">'
            f"<gs:name>Synthetic cache {index}</gs:name><gs:owner>Synthetic owner</gs:owner>"
            f"<gs:type>Traditional Cache</gs:type><gs:container>Small</gs:container>"
            f"<gs:difficulty>1.5</gs:difficulty><gs:terrain>2</gs:terrain>"
            f"<gs:logs>{logs}</gs:logs></gs:cache></extensions></wpt>"
        )
    return (header + "".join(entries) + "</gpx>").encode("utf-8")
