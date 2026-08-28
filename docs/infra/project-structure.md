# Project Structure

This is the target repo layout implied by [`architecture.md`](./architecture.md) and the existing
`docs/backend/db-schema.md` model paths (`accounts/models.py`, `prompts/models.py`). Nothing below is
implemented yet — `backend/config`, `backend/core`, `backend/core/tests`, and `frontend/src` currently
exist as empty placeholders; this doc is the plan for filling them in.

## Repo layout

```
llmchat/
├── Makefile
├── docker-compose.yml
├── .env.example
├── .github/
│   └── workflows/
│       └── ci.yml
├── scripts/
│   ├── init.sh              # first-time setup on a fresh clone
│   ├── wait-for.sh           # generic "wait for tcp host:port" helper for entrypoints
│   └── ci-test.sh            # runs backend + frontend test suites the same way CI does
├── backend/
│   ├── Dockerfile
│   ├── entrypoint.sh          # migrate --check / migrate, then exec CMD (runserver or qcluster)
│   ├── manage.py
│   ├── requirements/
│   │   ├── base.txt
│   │   └── dev.txt            # base + pytest, ruff, factory_boy, etc.
│   ├── config/                # Django project package
│   │   ├── settings/
│   │   │   ├── base.py
│   │   │   ├── local.py       # DEBUG on, permissive CORS
│   │   │   └── test.py        # fast password hasher, in-memory-friendly Q_CLUSTER sync mode
│   │   ├── urls.py
│   │   ├── asgi.py
│   │   └── wsgi.py
│   ├── core/                  # cross-app shared code, no models of its own
│   │   └── tests/             # shared test utilities/fixtures (e.g. authenticated client factory)
│   ├── accounts/              # User model + auth endpoints
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── tests/
│   ├── prompts/                # SystemPrompt model + library endpoints
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── tests/
│   ├── runs/                  # PromptRun, ModelResponse, AppSettings, run/response endpoints, tasks.py (Django-Q2 hooks)
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── tasks.py
│   │   ├── urls.py
│   │   └── tests/
│   └── llm/                    # LangChain orchestration layer, one adapter per provider
│       ├── client.py
│       ├── providers/
│       │   ├── openai.py
│       │   └── anthropic.py
│       └── tests/
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts
│   ├── index.html
│   └── src/
│       ├── api/                # thin fetch wrappers matching docs/backend/api-endpoints.md
│       ├── components/         # per docs/frontend/components.md
│       ├── pages/               # Login, Setup, Run, Settings — per docs/frontend/pages.md
│       ├── hooks/               # e.g. usePolling for run status
│       ├── styles/               # design tokens per docs/frontend/style-guide.md
│       └── types/                # DTOs per docs/frontend/interfaces.md
└── docs/                        # this doc set + backend/frontend/specs docs (already present)
```

## Docker Compose services

`docker-compose.yml` defines six services matching the [architecture](./architecture.md#topology):

| Service | Image / build | Command | Healthcheck |
|---|---|---|---|
| `db` | `postgres:16-alpine` | default | `pg_isready -U $POSTGRES_USER` |
| `broker` | `redis:7-alpine` | default | `redis-cli ping` |
| `backend` | build `./backend` | `entrypoint.sh` → `manage.py runserver 0.0.0.0:8000` | `curl -f localhost:8000/api/health/` |
| `worker` | build `./backend` (same image, different command) | `entrypoint.sh` → `manage.py qcluster` | process-based (no HTTP endpoint) |
| `frontend` | build `./frontend` | `vite --host 0.0.0.0` | `curl -f localhost:5173` |

`backend` and `worker` reuse the same image to avoid duplicated dependency installs and keep
migrations/model code in one place; only the container command differs.

## Makefile target reference

The root `Makefile` is the single entry point for setup and day-to-day commands — see
[`setup.md`](./setup.md) for first-run usage and [`testing.md`](./testing.md) for the test targets.

| Target | Purpose |
|---|---|
| `make setup` | Runs `scripts/init.sh`: copies `.env.example` → `.env` (if missing), builds images, runs migrations, prompts to create a Django superuser. |
| `make up` | `docker compose up` (foreground, all services). |
| `make up-d` | `docker compose up -d` (detached). |
| `make down` | `docker compose down`. |
| `make logs` | `docker compose logs -f`. |
| `make migrate` | `docker compose run --rm backend python manage.py migrate`. |
| `make makemigrations` | `docker compose run --rm backend python manage.py makemigrations`. |
| `make superuser` | `docker compose run --rm backend python manage.py createsuperuser`. |
| `make shell-backend` | `docker compose run --rm backend python manage.py shell`. |
| `make test` | Runs backend and frontend suites (delegates to `scripts/ci-test.sh`) — same commands CI runs. |
| `make test-backend` | `docker compose run --rm backend pytest`. |
| `make test-frontend` | `docker compose run --rm frontend npm test`. |
| `make lint` | Backend (`ruff check`) + frontend (`eslint`) linting. |
| `make fmt` | Backend (`ruff format`) + frontend (`prettier --write`) formatting. |
| `make clean` | `docker compose down -v` — also drops the Postgres volume (destructive; documented, not silent). |

`make clean` is the only destructive target; it's intentionally not part of `make setup` or `make
down` so a stray `make clean` is always a deliberate choice.
