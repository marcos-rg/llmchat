# Environment Variables

One `.env` file at the repo root, consumed by `docker-compose.yml` and passed into whichever
containers need each variable. Committed as `.env.example` with safe placeholder/default values;
`.env` itself is gitignored.

## `.env.example` (reference contents)

```dotenv
# --- Django ---
DJANGO_SECRET_KEY=change-me-in-local-env
DJANGO_DEBUG=1
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,backend
DJANGO_CORS_ALLOWED_ORIGINS=http://localhost:5173

# --- Database (backend, worker) ---
POSTGRES_DB=llmchat
POSTGRES_USER=llmchat
POSTGRES_PASSWORD=llmchat
POSTGRES_HOST=db
POSTGRES_PORT=5432

# --- Redis / Django-Q2 (backend, worker) ---
REDIS_HOST=broker
REDIS_PORT=6379
Q_CLUSTER_WORKERS=4

# --- LLM providers (worker only) ---
OPENAI_API_KEY=
ANTHROPIC_API_KEY=

# --- App settings defaults (backend) ---
APP_MAX_PROMPT_LENGTH=600

# --- Frontend (build-time, exposed to browser) ---
VITE_API_BASE_URL=http://localhost:8000/api
```

## Ownership by container

| Variable(s) | Consumed by | Notes |
|---|---|---|
| `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CORS_ALLOWED_ORIGINS` | `backend` | `worker` also loads Django settings but doesn't serve HTTP, so CORS/allowed-hosts are irrelevant there. |
| `POSTGRES_*` | `db`, `backend`, `worker` | `db` uses them to initialize the instance; `backend`/`worker` use them to build `DATABASES["default"]`. |
| `REDIS_HOST`, `REDIS_PORT`, `Q_CLUSTER_WORKERS` | `backend` (enqueue), `worker` (`Q_CLUSTER` setting) | `backend` only needs host/port to enqueue; worker concurrency (`Q_CLUSTER_WORKERS`) is worker-only. |
| `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` | `worker` only | Never mounted into `backend` or `frontend` — see [`architecture.md`](./architecture.md#why-this-shape). Never logged (mask in worker logging config). |
| `APP_MAX_PROMPT_LENGTH` | `backend` | Seeds the singleton `AppSettings` row on first migrate; overridable at runtime via `PATCH /api/settings/` (staff-only), not by re-reading the env var. |
| `VITE_API_BASE_URL` | `frontend` | Build-time only (Vite inlines `VITE_*` vars); requires an image rebuild to change, not just a container restart. |

## Rules

- **No API keys in the frontend or backend containers.** Only `worker` gets
  `OPENAI_API_KEY`/`ANTHROPIC_API_KEY` in its Compose `environment:` block.
- **No secrets committed.** `.env` is gitignored; `.env.example` holds placeholders only, never real
  keys.
- **CI never needs real LLM keys.** Test runs mock the LangChain/provider layer (see
  [`testing.md`](./testing.md)), so `OPENAI_API_KEY`/`ANTHROPIC_API_KEY` can stay empty in CI.
