#!/usr/bin/env bash
# The four commands CI runs, in the order CI runs them, against the Compose
# stack. Transcribed from docs/infra/testing.md.
#
# It exists so `make test` and the GitHub Actions workflow cannot drift: the
# workflow runs these same four invocations natively (no Docker), and this script
# is what a developer runs to reproduce a red CI job locally.
#
# Sub-suites: `--backend` or `--frontend` runs only that half; the Makefile's
# test-backend/test-frontend targets use those flags rather than duplicating the
# commands.
set -euo pipefail

cd "$(dirname "$0")/.."

run_backend=1
run_frontend=1
case "${1:-}" in
  --backend) run_frontend=0 ;;
  --frontend) run_backend=0 ;;
  "") ;;
  *)
    echo "usage: $0 [--backend|--frontend]" >&2
    exit 2
    ;;
esac

# The backend suite needs a reachable Postgres (pytest-django creates the
# test_<POSTGRES_DB> database on it) and Redis (the health endpoint pings it for
# real). No `worker` is needed: config.settings.test puts Django-Q2 in sync mode.
if [ "$run_backend" = 1 ]; then
  docker compose up -d db broker
  docker compose run --rm backend ruff check .
  docker compose run --rm backend pytest --cov --cov-report=term-missing
fi

if [ "$run_frontend" = 1 ]; then
  docker compose run --rm frontend npm run lint
  docker compose run --rm frontend npm test -- --run
fi
