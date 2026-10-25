#!/bin/sh
# Starts the BRouter RouteServer. Missing segments are reported but do not stop the service:
# requests outside downloaded coverage fail individually instead.
set -eu

SEGMENTS=/data/segments
PROFILES=/data/profiles

if ! ls "$SEGMENTS"/*.rd5 >/dev/null 2>&1; then
  echo 'No routing data found — run `mise run brouter:segments`' >&2
fi

exec java -Xms128m -Xmx256m -cp /opt/brouter/brouter.jar btools.server.RouteServer \
  "$SEGMENTS" "$PROFILES" "$PROFILES" 17777 2 0.0.0.0
