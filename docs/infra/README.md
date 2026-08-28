# Infra & Project Setup

This folder documents how the system in [`docs/specs/specs.md`](../specs/specs.md),
[`docs/backend/`](../backend/README.md), and [`docs/frontend/`](../frontend/README.md) is packaged,
run, tested, and shipped through CI. It does not contain runnable tooling itself — it specifies what
the Makefile, Docker Compose setup, bash scripts, and CI workflow should look like once implemented.

Read in order:

1. [`architecture.md`](./architecture.md) — which processes/containers run, how they're connected,
   and how the non-functional requirements map onto that topology.
2. [`environment.md`](./environment.md) — every environment variable the system needs, grouped by
   service, with `.env.example` contents.
3. [`project-structure.md`](./project-structure.md) — the full repo layout (backend Django apps,
   frontend structure, Docker files, scripts) and the Makefile target reference.
4. [`setup.md`](./setup.md) — step-by-step first-time setup for a fresh clone, and the bash scripts
   that back it.
5. [`testing.md`](./testing.md) — test strategy per layer, how tests run against Dockerized
   dependencies, and how LLM calls are mocked.
6. [`ci.md`](./ci.md) — the GitHub Actions pipeline: jobs, triggers, service containers, required
   secrets (or lack thereof).

## Component map

| Component | Runs as | Responsibility |
|---|---|---|
| **frontend** | Docker service (Vite dev server in dev / static build in prod-like mode) | React SPA from `docs/frontend/` |
| **backend** | Docker service (Django + DRF via `manage.py runserver` / gunicorn) | API in `docs/backend/api-endpoints.md` |
| **worker** | Docker service (`manage.py qcluster`) | Executes queued LLM calls (Django-Q2) |
| **db** | Docker service (`postgres`) | Persists users, system prompts, app settings, active-session runs |
| **broker** | Docker service (`redis`) | Message broker between backend and worker |
| **LLM providers** | External (OpenAI, Anthropic) | Reached only from the worker, via LangChain |

See [`architecture.md`](./architecture.md) for the full diagram and how this satisfies the
[non-functional requirements](../specs/specs.md#non-functional-requirements).
