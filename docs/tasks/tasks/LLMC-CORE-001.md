---
id: LLMC-CORE-001
title: Container stack and Django skeleton with health endpoint
area: CORE
phase: 0
layer: infra
status: in-progress
issue: https://github.com/marcos-rg/llmchat/issues/4
review: human
depends_on: []
docs:
  read:
    - docs/specs/specs.md
    - docs/infra/architecture.md
    - docs/infra/environment.md
    - docs/infra/project-structure.md
    - docs/infra/setup.md
  write:
    - docs/infra/stack-runbook.md
---

# LLMC-CORE-001 - Container stack and Django skeleton with health endpoint

## Objective

After this task a fresh clone can run `make setup && make up` and get four healthy containers
(`db`, `broker`, `backend`, `worker`) in which a real HTTP request reaches a real Django view, which
reads a real row from PostgreSQL and confirms a task can be pushed through Redis to the Django-Q2
worker. This is the backend half of the walking skeleton: one thin, working line through every
backend layer, with no application features on it.

## Scope

**In:**

- `docker-compose.yml` with `db` (postgres:16-alpine), `broker` (redis:7-alpine), `backend`, and
  `worker`, healthchecks (`pg_isready`, `redis-cli ping`, `curl /api/health/`) and
  `depends_on: {condition: service_healthy}` ordering per `docs/infra/architecture.md`.
- `backend/Dockerfile`, `backend/entrypoint.sh` (migrate, then exec CMD), `backend/requirements/base.txt`.
- Django project `backend/config` with `settings/base.py` + `settings/local.py`, `urls.py`, `wsgi.py`,
  `asgi.py`, `manage.py`; DB, Redis and `Q_CLUSTER` configuration read from the environment.
- `backend/core/` (shared, model-less app) and `backend/prompts/` holding the `AppSettings` singleton
  model, its migration, and a data migration that seeds row `pk=1` from `APP_MAX_PROMPT_LENGTH`.
- `GET /api/health/` returning `{"status", "db", "broker", "max_prompt_length"}` where
  `max_prompt_length` is read from the seeded `AppSettings` row and `broker` reflects a live Redis ping.
- `core/tasks.py::ping` plus `manage.py check_queue`, which enqueues `ping` through Redis and waits for
  the worker to return its result — the skeleton's proof that the queue path works.
- Root `Makefile` (`setup`, `up`, `up-d`, `down`, `logs`, `migrate`, `makemigrations`, `superuser`,
  `shell-backend`, `clean`), `scripts/init.sh` (with `--no-superuser`), `scripts/wait-for.sh`,
  `.env.example`, `.gitignore` entry for `.env`.

**Out:**

- Any authentication, user model, or DRF permission wiring (`LLMC-AUTH-002`).
- `PromptRun`/`ModelResponse` models, run endpoints, LangChain, provider adapters or API keys reaching
  application code (`LLMC-RUNS-001`, `LLMC-LLM-002`) — this task only proves the queue transports a
  no-op task.
- The `frontend` Compose service and any React code (`LLMC-CORE-002`).
- `config/settings/test.py`, pytest, ruff, and CI (`LLMC-CORE-003`) — the Makefile's `test`/`lint`
  targets are added there, not here.
- Production/gunicorn packaging; the spec's hosting target is local Compose only.

## Outputs

- `docker-compose.yml`, `.env.example`, `Makefile`, `.gitignore`
- `scripts/init.sh`, `scripts/wait-for.sh`
- `backend/Dockerfile`, `backend/entrypoint.sh`, `backend/manage.py`, `backend/requirements/base.txt`
- `backend/config/settings/{base,local}.py`, `backend/config/urls.py`
- `backend/core/{views,tasks}.py`, `backend/core/management/commands/check_queue.py`
- `backend/prompts/models.py` + `0001_initial` + `0002_seed_appsettings` migrations
- Endpoint: `GET /api/health/`
- `docs/infra/stack-runbook.md` — how the stack is composed, which variable each container gets, and
  how to recover each service.

## Acceptance criteria

- [ ] `docker compose up -d db broker backend worker` reaches `healthy` for `db`, `broker` and
      `backend` within 120s, with `worker` running.
- [ ] `GET /api/health/` returns `200` with `"status": "ok"`, `"db": "ok"` and `"broker": "ok"`.
- [ ] `max_prompt_length` in the health payload comes from the database, not a constant: updating
      `AppSettings.max_prompt_length` to `777` changes the next response to `777`.
- [ ] `manage.py migrate --check` exits `0` on a migrated database (no model/migration drift).
- [ ] `manage.py check_queue` exits `0`, proving a task enqueued by the backend was executed by the
      `worker` container via Redis.
- [ ] The `backend` container's environment contains neither `OPENAI_API_KEY` nor `ANTHROPIC_API_KEY`;
      the `worker` container's environment contains both.
- [ ] `scripts/init.sh --no-superuser` completes non-interactively on a tree with no `.env`, creates
      `.env` from `.env.example`, and leaves an existing `.env` untouched on a second run.

## Verification

```bash
cd "$(git rev-parse --show-toplevel)"
rm -f .env && bash scripts/init.sh --no-superuser
echo "# sentinel" >> .env && bash scripts/init.sh --no-superuser && grep -q '# sentinel' .env
docker compose up -d db broker backend worker
# portable 120s poll (GNU `timeout` is not present on macOS)
for i in $(seq 1 60); do curl -fsS http://localhost:8000/api/health/ >/dev/null 2>&1 && break; sleep 2; done
curl -fsS http://localhost:8000/api/health/ >/dev/null
docker compose ps
curl -fsS http://localhost:8000/api/health/ | tee /dev/stderr | grep -q '"status": *"ok"'
curl -fsS http://localhost:8000/api/health/ | grep -q '"db": *"ok"'
curl -fsS http://localhost:8000/api/health/ | grep -q '"broker": *"ok"'
docker compose exec -T backend python manage.py shell -c \
  "from prompts.models import AppSettings; s=AppSettings.load(); s.max_prompt_length=777; s.save()"
curl -fsS http://localhost:8000/api/health/ | grep -q '"max_prompt_length": *777'
docker compose exec -T backend python manage.py shell -c \
  "from prompts.models import AppSettings; s=AppSettings.load(); s.max_prompt_length=600; s.save()"
docker compose run --rm backend python manage.py migrate --check
docker compose run --rm backend python manage.py makemigrations --check --dry-run
docker compose run --rm backend python manage.py check_queue
! docker compose exec -T backend env | grep -qE '^(OPENAI|ANTHROPIC)_API_KEY='
docker compose exec -T worker env | grep -q '^OPENAI_API_KEY='
docker compose exec -T worker env | grep -q '^ANTHROPIC_API_KEY='
```

## Evidence

_None recorded yet._
