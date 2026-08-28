# Stack Runbook

How the local Compose stack is actually composed, which environment variable each container
gets and why, and how to recover each service. This is the living record for
[`LLMC-CORE-001`](../tasks/tasks/LLMC-CORE-001.md); the contracts it implements are
[`architecture.md`](./architecture.md), [`environment.md`](./environment.md),
[`project-structure.md`](./project-structure.md) and [`setup.md`](./setup.md).

At this stage the stack is the **backend half of the walking skeleton**: four services, one
HTTP endpoint, one no-op background task. There are no application features on it yet.

## Services

| Service | Image | Command | Healthcheck | Exposed |
|---|---|---|---|---|
| `db` | `postgres:16-alpine` | default | `pg_isready -U $POSTGRES_USER -d $POSTGRES_DB` | — |
| `broker` | `redis:7-alpine` | default | `redis-cli ping` | — |
| `backend` | built from `backend/Dockerfile` | `manage.py runserver 0.0.0.0:8000` | `curl -fsS localhost:8000/api/health/` | `8000` |
| `worker` | **same image** | `manage.py qcluster` | `pgrep -f 'manage.py qcluster'` | — |

`backend` and `worker` share one image (`llmchat-backend:local`) and one settings module.
Only the command differs — that is the whole mechanism behind "a slow LLM call never blocks
the API". The `frontend` service arrives in `LLMC-CORE-002`.

Startup order is expressed with `depends_on: {condition: service_healthy}` on `db` and
`broker`, so no wait logic is needed in Compose itself. The entrypoint still runs
`scripts/wait-for.sh` for both: `docker compose run` and post-restart windows can hand a
container a healthy-but-not-yet-accepting socket.

## Build context is the repo root

`docker-compose.yml` builds with `context: .` and `dockerfile: backend/Dockerfile`, not
`context: ./backend`. This looks wrong at a glance and is deliberate:
`scripts/wait-for.sh` is a repo-level shared script (per `project-structure.md`) and must be
copied into the image, which a `./backend` context cannot reach. `.dockerignore` at the root
keeps `docs/`, `.git/` and `frontend/` out of the build context so this costs nothing.

## Environment ownership

Compose reads `./.env` for `${...}` interpolation, but **no service uses `env_file:`**. Each
service gets an explicit `environment:` block instead. This is the enforcement point for the
spec's "API keys are stored server-side only": `env_file: .env` would inject
`OPENAI_API_KEY`/`ANTHROPIC_API_KEY` into *every* service, and nothing downstream would
catch it.

| Variable | `db` | `backend` | `worker` |
|---|:--:|:--:|:--:|
| `POSTGRES_DB/USER/PASSWORD` | ✅ | ✅ | ✅ |
| `POSTGRES_HOST`, `POSTGRES_PORT` | — | ✅ | ✅ |
| `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CORS_ALLOWED_ORIGINS` | — | ✅ | ✅ |
| `REDIS_HOST`, `REDIS_PORT` | — | ✅ | ✅ |
| `Q_CLUSTER_WORKERS` | — | — | ✅ |
| `APP_MAX_PROMPT_LENGTH` | — | ✅ | ✅ |
| `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` | — | ❌ **never** | ✅ **only here** |

The "backend has no keys" rule is checked by this task's verification block, so a future
refactor to `env_file:` fails the task's own acceptance criteria rather than silently
leaking.

## The health endpoint

`GET /api/health/` returns:

```json
{"status": "ok", "db": "ok", "broker": "ok", "max_prompt_length": 600}
```

It is not a static payload. `db` comes from a real `SELECT 1` on a real cursor, `broker`
from a live `redis.Redis(...).ping()`, and `max_prompt_length` from the seeded `AppSettings`
row — a database read, not the `APP_MAX_PROMPT_LENGTH` setting. That distinction is the
point: the endpoint doubles as the Compose healthcheck, so if it could pass without touching
Postgres and Redis, a "healthy" backend would prove nothing.

When a dependency is down the endpoint returns **503** with the failing key set to `"error"`
and `max_prompt_length: null`. It deliberately does *not* fall back to the setting value —
reporting a stale constant as live configuration is worse than reporting nothing.

## `AppSettings` and the seed

`AppSettings` lives in `backend/prompts/models.py`, following
[`docs/backend/db-schema.md`](../backend/db-schema.md). Note that
`project-structure.md`'s directory listing files it under `runs/`; db-schema.md is the
authority for model placement and the two should be reconciled when `runs/` is created.

It is a singleton: `save()` pins `pk = 1`, `delete()` raises, and migration
`0002_seed_appsettings` creates row 1 from `APP_MAX_PROMPT_LENGTH`.

**`APP_MAX_PROMPT_LENGTH` is a seed, not a live setting.** It is read exactly once, when the
row does not yet exist. After that, changing it in `.env` and restarting does nothing —
runtime changes go through the admin or `PATCH /api/settings/`. This surprises people; it is
intentional, so that an admin's runtime change is not silently reverted by a container
restart.

## The queue path

`core/tasks.py::ping` is a no-op that returns `pong:<token>`. It has no application logic on
purpose: `manage.py check_queue` uses it as a liveness probe, so anything that could fail
for an app-level reason would make the probe ambiguous.

`check_queue` enqueues `ping` with a fresh UUID token and blocks on `django_q.tasks.fetch`
until a result appears. It fails if the broker is unreachable, if nothing is consuming, or
if the worker returns the wrong token (which means the worker is running stale code).

The cross-container mechanic worth knowing: **Redis is the broker only; task state lives in
Postgres**, in django-q2's ORM tables. That is why `check_queue` can run in a throwaway
`docker compose run backend` container and still read a result produced inside `worker` —
they meet in the database, not in Redis. It is also why polling reads in later tasks always
hit Postgres.

## Migrations run in the entrypoint, under an advisory lock

`backend/entrypoint.sh` runs `manage.py migrate_locked` before `exec "$@"`, in every
container built from this image. The upside is that `docker compose run --rm backend ...`
is always against a migrated schema, with no separate one-shot migration service to keep in
sync.

**`migrate_locked`, not `migrate`, and this matters.** `backend` and `worker` start
simultaneously and both migrate. Django does *not* serialize that for you: the first thing
`migrate` does is `MigrationRecorder.ensure_schema()`, a bare `CREATE TABLE
django_migrations`, and on a cold database the loser of the race dies with

```
MigrationSchemaMissing: Unable to create the django_migrations table
(duplicate key value violates unique constraint "pg_type_typname_nsp_index")
```

which is a container crash loop on first boot, not a transient warning. This was observed
during LLMC-CORE-001, not predicted.

`core/management/commands/migrate_locked.py` wraps the migration in a Postgres session-level
advisory lock (`pg_advisory_lock(4919570)`). One subtlety worth not re-discovering: the lock
is taken on one connection and `migrate` runs in a **subprocess** with its own connection.
That is required, not incidental — Django closes and reopens connections around schema
operations, and a session-level advisory lock dies with its session, so locking and
migrating on the same connection would silently drop the lock partway through.

## Recovery

| Symptom | Fix |
|---|---|
| Tasks queued but never run | `docker compose restart worker` — no data loss; state is in Postgres. |
| `"broker": "error"` in health | `docker compose restart broker worker`; the worker reconnects on restart. |
| `"db": "error"` in health | `docker compose logs db`; if the volume itself is corrupt, `make clean && make setup` (destroys data). |
| `backend` never becomes healthy | `docker compose logs backend` — usually a migration failure in the entrypoint, which exits before `runserver`. |
| Model/migration drift | `make makemigrations && make migrate`; `manage.py migrate --check` exits non-zero whenever this is pending. |
| Stale image after a dependency change | `docker compose build backend` (the `./backend:/app` mount covers *code* changes without a rebuild, but not `requirements/base.txt`). |

`make clean` is the only destructive target — it drops the `pgdata` volume. It is
deliberately not part of `make down` or `make setup`.

## Verifying the whole thing

```bash
make setup           # or: bash scripts/init.sh --no-superuser
make up-d
curl -fsS http://localhost:8000/api/health/
docker compose run --rm backend python manage.py check_queue
```
