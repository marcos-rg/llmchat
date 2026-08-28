#!/bin/bash
# Stop: refuse to finish while the task graph is inconsistent (exit 2 = block).

set -uo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
INPUT="$(cat)"

# Already blocked once this turn: let the agent stop rather than loop forever.
printf '%s' "$INPUT" | grep -q '"stop_hook_active"[[:space:]]*:[[:space:]]*true' && exit 0

if ! OUTPUT="$(python3 "$REPO_ROOT/scripts/tasks.py" validate 2>&1)"; then
  echo "Cannot finish: the task graph is inconsistent:" >&2
  echo "$OUTPUT" >&2
  echo "Fix it with 'python3 scripts/tasks.py status|evidence|index' before finishing." >&2
  exit 2
fi
exit 0
