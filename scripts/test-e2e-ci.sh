#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export DB_PORT="${DB_PORT:-5432}"
export POSTGRES_USER="${POSTGRES_USER:-geocaching}"
export POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-geocaching}"
export POSTGRES_DB="${POSTGRES_DB:-geocaching}"
export GCP_HOST=127.0.0.1
export GCP_PORT=8000
export GCP_DATABASE_URL="${GCP_DATABASE_URL:-postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@127.0.0.1:${DB_PORT}/${POSTGRES_DB}}"
export VITE_API_TARGET=http://127.0.0.1:8000
export E2E_BASE_URL="${E2E_BASE_URL:-http://localhost:5173}"

BACKEND_LOG="$(mktemp)"
PREVIEW_LOG="$(mktemp)"
BACKEND_PID=""
PREVIEW_PID=""

cleanup() {
  local exit_code=$?
  if [[ -n "$PREVIEW_PID" ]]; then
    kill "$PREVIEW_PID" 2>/dev/null || true
    wait "$PREVIEW_PID" 2>/dev/null || true
  fi
  if [[ -n "$BACKEND_PID" ]]; then
    kill "$BACKEND_PID" 2>/dev/null || true
    wait "$BACKEND_PID" 2>/dev/null || true
  fi
  rm -f "$BACKEND_LOG" "$PREVIEW_LOG"
  exit "$exit_code"
}
trap cleanup EXIT

wait_for_url() {
  local url="$1"
  local pid="$2"
  local log="$3"
  for _ in $(seq 1 60); do
    if curl --fail --silent "$url" >/dev/null; then
      return 0
    fi
    if ! kill -0 "$pid" 2>/dev/null; then
      cat "$log" >&2
      echo "E2E service exited before becoming ready: $url" >&2
      return 1
    fi
    sleep 1
  done
  cat "$log" >&2
  echo "E2E service did not become ready: $url" >&2
  return 1
}

docker compose up -d --wait db
mise run db:migrate

mise exec -- uv run --locked --project backend python -m geocaching_planner >"$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!
wait_for_url "http://127.0.0.1:8000/api/v1/health" "$BACKEND_PID" "$BACKEND_LOG"

mise run build:frontend

mise exec -- pnpm --dir frontend exec vite preview --host 127.0.0.1 --port 5173 --strictPort \
  >"$PREVIEW_LOG" 2>&1 &
PREVIEW_PID=$!
wait_for_url "$E2E_BASE_URL" "$PREVIEW_PID" "$PREVIEW_LOG"

mise exec -- pnpm --dir frontend exec playwright test
