#!/usr/bin/env bash
# Reports a task that is not implemented yet and exits non-zero (AC5).
# Usage: scripts/not-implemented.sh <task-name> <owning-ticket>
set -euo pipefail

task="${1:?task name required}"
ticket="${2:?owning ticket required}"

echo "mise run ${task} is not implemented yet; it is owned by ${ticket}." >&2
exit 1
