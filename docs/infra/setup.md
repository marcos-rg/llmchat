# First-Time Setup (Fresh Clone)

Target: a new contributor runs one command after cloning and has a working local stack. Matches the
spec's Portability requirement — "run via `docker compose up` with minimal manual configuration."

## Prerequisites

- Docker + Docker Compose v2 (`docker compose`, not the standalone `docker-compose`).
- `make`.
- Nothing else — Python, Node, Postgres, and Redis all run inside containers; no local interpreter
  versions to manage.

## Steps

```bash
git clone <repo-url>
cd llmchat
make setup
make up
```

That's it — `make setup` handles environment file creation, image builds, and migrations; `make up`
starts the stack. Frontend at `http://localhost:5173`, API at `http://localhost:8000/api/`.

## What `make setup` does (`scripts/init.sh`)

1. **Copy env file** — if `.env` doesn't exist, copy `.env.example` → `.env` (never overwrites an
   existing `.env`, so re-running `make setup` is safe).
2. **Build images** — `docker compose build`.
3. **Start dependencies only** — `docker compose up -d db broker`, then wait for both healthchecks
   (`docker compose wait` or a poll loop against `pg_isready`/`redis-cli ping`) before continuing, so
   migrations don't race a not-yet-ready Postgres.
4. **Run migrations** — `docker compose run --rm backend python manage.py migrate`.
5. **Seed `AppSettings`** — a data migration (or `manage.py` one-off command) creates the singleton
   `AppSettings` row from `APP_MAX_PROMPT_LENGTH` if it doesn't already exist, so `GET /api/settings/`
   never 500s on a fresh DB.
6. **Offer to create a superuser** — interactive prompt; skippable with a flag
   (`scripts/init.sh --no-superuser`) for non-interactive/CI use, since a superuser is only needed to
   reach `PATCH /api/settings/` and the Django admin, not to use the app as a regular user.
7. **Print next steps** — the URLs above and `make logs` for troubleshooting.

Script sketch (reference, not implemented):

```bash
#!/usr/bin/env bash
set -euo pipefail

[ -f .env ] || cp .env.example .env

docker compose build
docker compose up -d db broker

echo "Waiting for db and broker..."
until docker compose exec -T db pg_isready -U "${POSTGRES_USER:-llmchat}" >/dev/null 2>&1; do sleep 1; done
until docker compose exec -T broker redis-cli ping >/dev/null 2>&1; do sleep 1; done

docker compose run --rm backend python manage.py migrate

if [[ "${1:-}" != "--no-superuser" ]]; then
  docker compose run --rm backend python manage.py createsuperuser
fi

cat <<'EOF'

Setup complete.
  Frontend: http://localhost:5173
  API:      http://localhost:8000/api/

Run `make up` to start the stack.
EOF
```

## Everyday commands after setup

| I want to... | Run |
|---|---|
| Start the stack | `make up` (or `make up-d` to run detached) |
| Stop the stack | `make down` |
| Tail logs | `make logs` |
| Add a new model / regenerate migrations | `make makemigrations` then `make migrate` |
| Run the test suites | `make test` |
| Reset everything, including the DB volume | `make clean` then `make setup` |

## Resetting a broken local environment

If the worker or broker gets into a bad state (per the spec's "failed background jobs should be
recoverable by restarting the affected component"), restarting just those services is enough — no
data loss:

```bash
docker compose restart worker broker
```

Only use `make clean` (drops volumes) when the Postgres data itself is the problem.
