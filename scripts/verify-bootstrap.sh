#!/usr/bin/env bash
# Automated checks for the tooling bootstrap (T-001).
# Usage: scripts/verify-bootstrap.sh [all|<function-name>]
# Each verify_* function maps to one acceptance criterion (see T-001 test plan).
# This script must never call `mise run check`, which runs it (no recursion).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

TMP_DIRS=()
trap 'rm -rf ${TMP_DIRS[@]+"${TMP_DIRS[@]}"}' EXIT

STUB_TASKS=(test:frontend test:e2e db:migrate db:revision api:gen brouter:segments)
REQUIRED_TASKS=(setup dev check lint fmt test test:bootstrap test:backend test:frontend test:e2e db:migrate db:revision api:gen brouter:segments check:pre-commit lint:backend fmt:backend typecheck:backend check:backend verify:python:314)

fail() { echo "FAIL: $*" >&2; exit 1; }
pass() { echo "PASS: $1"; }

# AC2: every task in Scope exists, and check/lint depend on the real tasks only.
verify_task_inventory() {
  local json
  json="$(mise tasks --json)"
  JSON="$json" REQUIRED="${REQUIRED_TASKS[*]}" STUBS="${STUB_TASKS[*]}" python3 - <<'PY' || exit 1
import json, os, sys
tasks = {t["name"]: t for t in json.loads(os.environ["JSON"])}
required = os.environ["REQUIRED"].split()
stubs = set(os.environ["STUBS"].split())
missing = [n for n in required if n not in tasks]
if missing:
    sys.exit(f"FAIL: missing tasks: {missing}")

def closure(name, seen=None):
    seen = set() if seen is None else seen
    for dep in tasks[name]["depends"]:
        if dep not in seen:
            seen.add(dep)
            closure(dep, seen)
    return seen

for gate in ("check", "lint"):
    deps = closure(gate)
    hit = sorted(deps & stubs)
    if hit:
        sys.exit(f"FAIL: '{gate}' invokes stub tasks: {hit}")
    for needed in ("check:pre-commit", "test:bootstrap"):
        if needed not in deps:
            sys.exit(f"FAIL: '{gate}' does not depend on '{needed}'")
print("PASS: task inventory and gate dependencies")
PY
}

# AC3: pre-commit hooks are installed by setup, and setup keeps an existing .env byte-for-byte.
verify_hooks_and_setup_idempotence() {
  [ -f .git/hooks/pre-commit ] || fail "setup did not install .git/hooks/pre-commit"
  local tmp before after
  tmp="$(mktemp -d)"
  TMP_DIRS+=("$tmp")
  git ls-files -z -co --exclude-standard | tar --null -T - -cf - | (cd "$tmp" && tar xf -)
  (
    cd "$tmp"
    git init -q
    rm -f .env
    mise run setup >/dev/null
    printf 'USER_VALUE=1\n' >> .env
    before="$(shasum -a 256 .env | cut -d' ' -f1)"
    mise run setup >/dev/null
    after="$(shasum -a 256 .env | cut -d' ' -f1)"
    [ "$before" = "$after" ] || exit 1
  ) || fail "re-running setup changed an existing .env"
  pass "hooks installed; setup leaves existing .env unchanged"
}

# AC4: root Python project files are untracked, root .venv absent, ignore rules behave.
verify_layout_and_ignore_rules() {
  for f in pyproject.toml uv.lock; do
    if git ls-files --error-unmatch "$f" >/dev/null 2>&1; then fail "root $f is tracked"; fi
  done
  [ ! -e .venv ] || fail "root .venv exists"
  git check-ignore -q .env || fail ".env is not ignored"
  git check-ignore -q infra/brouter/segments/example.rd5 || fail "segment .rd5 is not ignored"
  git check-ignore -q data/personal.gpx || fail "root *.gpx is not ignored"
  git check-ignore -q backend/tests/fixtures/sample.gpx && fail "fixture gpx is ignored"
  git check-ignore -q .env.example && fail ".env.example is ignored"
  git check-ignore -q infra/brouter/segments/.gitkeep && fail "segments/.gitkeep is ignored"
  pass "layout and ignore rules"
}

# AC5: each stub exits non-zero and names its owning ticket.
verify_stub_failures_and_check_is_real() {
  local task out rc
  for task in "${STUB_TASKS[@]}"; do
    set +e
    out="$(mise run "$task" 2>&1)"
    rc=$?
    set -e
    [ "$rc" -ne 0 ] || fail "stub '$task' exited 0"
    grep -Eq "T-[0-9]{3}" <<<"$out" || fail "stub '$task' does not name an owning ticket"
  done
  pass "stub tasks exit non-zero and name owning tickets"
}

# AC6: required scaffold is tracked (or staged, since git ls-files reads the index).
verify_required_scaffold_is_tracked() {
  local f
  for f in backend/pyproject.toml frontend/.gitkeep infra/brouter/profiles/.gitkeep \
           infra/brouter/segments/.gitkeep .editorconfig .env.example; do
    git ls-files --error-unmatch "$f" >/dev/null 2>&1 || fail "$f is not tracked (git add it)"
  done
  pass "required scaffold is tracked"
}

# AC1: a clean clone without .env runs setup non-interactively and creates the hook and .env.
verify_clean_clone_setup() {
  local tmp
  tmp="$(mktemp -d)"
  TMP_DIRS+=("$tmp")
  git ls-files -z -co --exclude-standard | tar --null -T - -cf - | (cd "$tmp" && tar xf -)
  (
    cd "$tmp"
    git init -q
    rm -f .env
    mise trust -q
    mise install -q
    mise run setup
  ) || fail "clean-clone 'mise run setup' failed"
  [ -f "$tmp/.git/hooks/pre-commit" ] || fail "clean clone has no pre-commit hook"
  [ -f "$tmp/.env" ] || fail "clean clone did not create .env"
  cmp -s "$tmp/.env" "$tmp/.env.example" || fail "clean clone .env differs from .env.example"
  pass "clean clone setup"
}

run_all() {
  verify_task_inventory
  verify_layout_and_ignore_rules
  verify_required_scaffold_is_tracked
  verify_hooks_and_setup_idempotence
  verify_stub_failures_and_check_is_real
  verify_clean_clone_setup
  echo "All bootstrap checks passed."
}

if [ "${1:-all}" = "all" ]; then run_all; else "$1"; fi
