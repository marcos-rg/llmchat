#!/usr/bin/env bash
# First-time setup on a fresh clone. See docs/infra/setup.md.
#
# Idempotent: never overwrites an existing .env, and `migrate` is a no-op on an
# already-migrated database, so re-running is always safe.
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

create_superuser=1
for arg in "$@"; do
  case "$arg" in
    --no-superuser) create_superuser=0 ;;
    -h|--help) echo "Usage: scripts/init.sh [--no-superuser]"; exit 0 ;;
    *) echo "Unknown option: $arg" >&2; exit 2 ;;
  esac
done

if [ -f .env ]; then
  echo "==> .env already exists, leaving it untouched"
else
  echo "==> Creating .env from .env.example"
  cp .env.example .env
fi

echo "==> Building images"
docker compose build

echo "==> Starting db and broker"
docker compose up -d db broker

echo "==> Waiting for db and broker to report healthy"
POSTGRES_USER="$(grep -E '^POSTGRES_USER=' .env | cut -d= -f2-)"
until docker compose exec -T db pg_isready -U "${POSTGRES_USER:-llmchat}" >/dev/null 2>&1; do sleep 1; done
until docker compose exec -T broker redis-cli ping >/dev/null 2>&1; do sleep 1; done

echo "==> Running migrations (this also seeds the AppSettings singleton)"
docker compose run --rm backend python manage.py migrate

if [ "$create_superuser" -eq 1 ]; then
  echo "==> Creating a Django superuser (Ctrl-C to skip)"
  docker compose run --rm backend python manage.py createsuperuser
else
  echo "==> Skipping superuser creation (--no-superuser)"
fi

cat <<'MSG'

Setup complete.
  API:    http://localhost:8000/api/
  Health: http://localhost:8000/api/health/

Run `make up` to start the stack, `make logs` to follow it.
MSG
