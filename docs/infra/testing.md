# Testing Strategy

Scope follows the spec's Maintainability & Testability NFR: *"Core business logic (prompt fan-out,
LLM orchestration, diffing) should have basic unit test coverage"* — this is a hackathon project, not
a target for exhaustive E2E coverage. No E2E/browser test suite is planned; polling and diff-rendering
correctness are covered at the unit/component level instead.

## Backend (`pytest` + `pytest-django`)

Runs inside the `backend` image against `config.settings.test`, which:

- Uses the SQLite in-memory DB is **not** used — Postgres parity matters for JSON fields / constraints,
  so tests run against the same `db` service as dev, on a Django-managed test database
  (`test_<POSTGRES_DB>`), created/destroyed automatically by `pytest-django`.
- Sets Django-Q2 to synchronous mode (`Q_CLUSTER["sync"] = True`) so enqueued tasks execute inline
  during tests — no real `worker` container or `broker` needed for backend tests.
- Uses `django.contrib.auth.hashers.MD5PasswordHasher` (fast, insecure-by-design for tests only) to
  keep auth-flow tests fast.

Per-app `tests/` packages (see [`project-structure.md`](./project-structure.md)):

| App | What's tested |
|---|---|
| `accounts` | Login/logout flows, session-cookie auth, password validation. |
| `prompts` | System-prompt library CRUD/listing. |
| `runs` | `run_count` fan-out (2–5 `ModelResponse` rows created), prompt-length validation against `AppSettings`, status transitions (`queued→running→complete/failed`), retry endpoint, session-scoped ownership (`404` for another user's run), logout purge cascade. |
| `llm` | LangChain adapter contract — **mocked** provider calls (see below), diff-token generation logic. |
| `core` | Shared test fixtures/utilities only; no independent test target. |

**LLM calls are always mocked in tests.** `llm/tests/` stubs the OpenAI/Anthropic clients (e.g. via
`unittest.mock.patch` on the LangChain chat-model classes) so:
- Tests never make network calls or spend API credits.
- Tests never require real `OPENAI_API_KEY`/`ANTHROPIC_API_KEY` values (CI can run with empty keys).
- Failure/retry paths are testable deterministically (mock raises, assert `ModelResponse.status ==
  "failed"` and `retry_count` behavior).

Run locally: `make test-backend` → `docker compose run --rm backend pytest --cov`.

## Frontend (Vitest + React Testing Library)

- **Component tests** — per component in `docs/frontend/components.md` (buttons, fields, diff view,
  status badges): render + interaction assertions, not snapshot-only.
- **Page-level tests** — `pages/` per `docs/frontend/pages.md`, with `api/` calls mocked (e.g.
  `msw` — Mock Service Worker — intercepting the endpoints in
  `docs/backend/api-endpoints.md`), covering: prompt-length warning threshold, run submission,
  polling-driven status updates, diff-toggle on/off.
- **State-machine tests** — the per-response status logic in `docs/frontend/states.md` tested as
  plain unit functions where possible, independent of rendering.

Run locally: `make test-frontend` → `docker compose run --rm frontend npm test`.

## What's explicitly out of scope

- End-to-end browser tests (Playwright/Cypress) — not required by the NFR and adds CI time/flakiness
  disproportionate to a hackathon scope.
- Load/performance testing beyond the "10 concurrent users" NFR, which is a design constraint
  ([`architecture.md`](./architecture.md)) rather than something to load-test in CI.
- Real LLM provider integration tests — would require live API keys in CI and introduce
  non-determinism; provider adapters are tested against mocks only.

## Running everything the way CI does

`scripts/ci-test.sh` runs backend and frontend suites with the same invocations CI uses, so
`make test` locally and the CI job never drift:

```bash
#!/usr/bin/env bash
set -euo pipefail

docker compose run --rm backend ruff check .
docker compose run --rm backend pytest --cov --cov-report=term-missing

docker compose run --rm frontend npm run lint
docker compose run --rm frontend npm test -- --run
```
