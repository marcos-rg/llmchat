#!/usr/bin/env bash
# Wait for the datastores, apply migrations, then hand off to the container command.
#
# Migrations run here rather than in a separate one-shot service so that `backend`,
# `worker` and any `docker compose run` all start against a migrated schema.
# `migrate_locked` (not plain `migrate`) because backend and worker start at the
# same time and Django does not serialize the creation of django_migrations - see
# core/management/commands/migrate_locked.py.
set -euo pipefail

wait-for.sh "${POSTGRES_HOST:-db}" "${POSTGRES_PORT:-5432}" 60
wait-for.sh "${REDIS_HOST:-broker}" "${REDIS_PORT:-6379}" 60

python manage.py migrate_locked

exec "$@"
