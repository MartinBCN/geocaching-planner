#!/usr/bin/env bash
# AC1/AC8: `mise run dev` starts the stack and /api/v1/health reports db ok.
# Requires Docker. Stops the dev process it started.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PORT="${GCP_PORT:-8000}"
LOG="$(mktemp)"
trap 'if [ -n "${DEV_PID:-}" ]; then kill "$DEV_PID" 2>/dev/null || true; fi; rm -f "$LOG"' EXIT

mise run dev >"$LOG" 2>&1 &
DEV_PID=$!

for _ in $(seq 1 120); do
  if ! kill -0 "$DEV_PID" 2>/dev/null; then
    echo "FAIL: mise run dev exited early" >&2
    cat "$LOG" >&2
    exit 1
  fi
  body="$(curl -fsS "http://127.0.0.1:${PORT}/api/v1/health" 2>/dev/null || true)"
  # Any HTTP response (the root is 404) proves RouteServer is listening on the published port.
  brouter_code="$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:${BROUTER_PORT:-17777}/" 2>/dev/null || true)"
  if [ -n "$body" ] && echo "$body" | grep -q '"db":"ok"' && [ -n "$brouter_code" ] && [ "$brouter_code" != "000" ]; then
    echo "PASS: dev stack health reports db ok and BRouter is listening"
    exit 0
  fi
  sleep 2
done

echo "FAIL: /api/v1/health did not report db ok within 240s" >&2
cat "$LOG" >&2
exit 1
