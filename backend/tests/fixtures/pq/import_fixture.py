"""Small synthetic PQ payloads used by import integration and E2E tests."""


def make_import_fixture() -> tuple[bytes, bytes]:
    caches = []
    for index, code in enumerate(("GC1001A", "GC1002B", "GC1003C"), start=1):
        logs = ""
        if index == 1:
            logs = (
                "<gs:logs>"
                '<gs:log id="9001"><gs:date>2026-01-01T10:00:00Z</gs:date>'
                "<gs:type>Found it</gs:type><gs:finder>Synthetic finder A</gs:finder>"
                "<gs:text>First synthetic log</gs:text></gs:log>"
                '<gs:log id="9002"><gs:date>2026-01-02T10:00:00Z</gs:date>'
                "<gs:type>Write note</gs:type><gs:finder>Synthetic finder B</gs:finder>"
                "<gs:text>Second synthetic log</gs:text></gs:log>"
                "</gs:logs>"
            )
        caches.append(
            f'<wpt lat="52.{index}" lon="4.{index}"><name>{code}</name>'
            "<sym>Geocache</sym><extensions>"
            f'<gs:cache id="{index}" available="True" archived="False">'
            f"<gs:name>Synthetic cache {index}</gs:name>"
            "<gs:owner>Synthetic owner</gs:owner>"
            "<gs:type>Traditional Cache</gs:type><gs:container>Small</gs:container>"
            "<gs:difficulty>1.5</gs:difficulty><gs:terrain>2</gs:terrain>"
            f"{logs}</gs:cache></extensions></wpt>"
        )
    cache_gpx = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<gpx xmlns="http://www.topografix.com/GPX/1/0" '
        'xmlns:gs="http://www.groundspeak.com/cache/1/0" version="1.0">'
        f"{''.join(caches)}</gpx>"
    ).encode()
    waypoint_gpx = (
        b'<?xml version="1.0" encoding="UTF-8"?>'
        b'<gpx xmlns="http://www.topografix.com/GPX/1/0" version="1.0">'
        b'<wpt lat="52.4" lon="4.4"><name>PK1001A</name><cmt>Parking</cmt>'
        b"<desc>Parking area</desc><type>Waypoint|Parking Area</type></wpt>"
        b'<wpt lat="52.5" lon="4.5"><name>FN1002B</name><cmt>Final</cmt>'
        b"<desc>Final location</desc><type>Waypoint|Final Location</type></wpt>"
        b"</gpx>"
    )
    return cache_gpx, waypoint_gpx
