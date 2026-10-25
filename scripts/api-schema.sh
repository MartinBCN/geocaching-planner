#!/usr/bin/env bash
# Generates the frontend API types from the backend OpenAPI document (ADR-0005).
# Usage: scripts/api-schema.sh gen    rewrite frontend/src/api/schema.d.ts
#        scripts/api-schema.sh check  fail if the committed schema is out of date
# Only the generated schema file is compared, so unrelated changes never trip the check.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCHEMA="$ROOT/frontend/src/api/schema.d.ts"
mode="${1:?usage: api-schema.sh gen|check}"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

uv run --locked --project "$ROOT/backend" python "$ROOT/backend/scripts/export_openapi.py" "$tmp/openapi.json"

case "$mode" in
  gen)
    pnpm --dir "$ROOT/frontend" exec openapi-typescript "$tmp/openapi.json" -o "$SCHEMA"
    ;;
  check)
    pnpm --dir "$ROOT/frontend" exec openapi-typescript "$tmp/openapi.json" -o "$tmp/schema.d.ts"
    if ! cmp -s "$tmp/schema.d.ts" "$SCHEMA"; then
      echo "API schema out of date: run mise run api:gen" >&2
      exit 1
    fi
    echo "PASS: API schema is up to date"
    ;;
  *)
    echo "usage: api-schema.sh gen|check" >&2
    exit 2
    ;;
esac
