---
id: LLMC-RUNS-001
title: Prompt run models, fan-out API and ephemeral purge
area: RUNS
phase: 3
layer: backend
status: todo
review: none
depends_on:
  - LLMC-AUTH-002
  - LLMC-CFG-001
  - LLMC-LLM-001
docs:
  read:
    - docs/backend/api-endpoints.md
    - docs/backend/db-schema.md
    - docs/backend/auth-contract.md
    - docs/backend/llm-contract.md
  write:
    - docs/backend/runs-backend.md
---

# LLMC-RUNS-001 - Prompt run models, fan-out API and ephemeral purge

## Objective

After this task the core of the product exists server-side: submitting a prompt with a run count of
2-5 persists a `PromptRun` and its `ModelResponse` rows and enqueues one generation task per response,
the run is pollable by its owner only, a failed response can be re-queued, and nothing survives logout
- the ephemeral-data rule from the spec is enforced in the database, not just described.

## Scope

**In:**

- `backend/runs/` app: `PromptRun` and `ModelResponse` exactly as in `docs/backend/db-schema.md`
  (check constraint `run_count` 2-5, `unique_together (run, index)`, `is_baseline` on `index == 1`,
  the derived `PromptRun.status` property) plus migrations.
- `POST /api/runs/`: validates the provider/model pair against `LLM_PROVIDERS` (via the helper from
  `LLMC-CFG-001`), `run_count` in `[2, 5]`, non-empty prompt, and `len(prompt) <= max_prompt_length`
  read live from `AppSettings`; creates the run and its `run_count` responses in one transaction; then
  enqueues one `runs.tasks.generate_response(response_id)` task per response at the dotted path fixed
  by `docs/backend/llm-contract.md`; returns `201` with the payload from
  `docs/backend/api-endpoints.md`.
- `GET /api/runs/{run_id}/`: owner-and-session scoped (`404`, never `403`, for anyone else), returning
  the run plus every response with `diff_tokens: null` for now.
- `POST /api/responses/{response_id}/retry/`: `404` unless the caller owns the parent run and the
  response is `failed`; otherwise clears `error_message`, sets `queued`, re-enqueues, returns `202`.
- Extending the logout view from `LLMC-AUTH-002` to delete every `PromptRun` with the session's
  `session_key` (cascading to responses) before the session is destroyed.
- A Django-Q2 scheduled task purging `PromptRun` rows older than `RUN_TTL_HOURS` (default 24), for
  sessions that expire without an explicit logout, registered idempotently on migrate.
- `runs/tests/` covering fan-out, validation, scoping, retry eligibility, purge and enqueue arguments
  (enqueue is patched — the task body itself lands in `LLMC-LLM-002`).

**Out:**

- The worker task implementation and any provider call (`LLMC-LLM-002`).
- Diff computation — `diff_tokens` stays `null` here (`LLMC-DIFF-002`).
- Any UI (`LLMC-RUNS-003`, `LLMC-RUNS-004`).
- A run history or list endpoint: the spec has no history page and data is ephemeral, so no
  `GET /api/runs/` collection route is added.
- Editing or deleting a run through the API.

## Outputs

- `backend/runs/{models,serializers,views,urls}.py` + migrations, `backend/runs/purge.py` (TTL task)
- Endpoints: `POST /api/runs/`, `GET /api/runs/{run_id}/`, `POST /api/responses/{response_id}/retry/`
- Logout purge in `backend/accounts/views.py`
- `backend/runs/tests/{test_create.py,test_poll.py,test_retry.py,test_purge.py}`
- `docs/backend/runs-backend.md` — shipped run lifecycle, validation rules, scoping and purge behaviour

## Acceptance criteria

- [ ] `POST /api/runs/` with `run_count: 4` returns `201` and creates exactly four `ModelResponse` rows
      with `index` 1-4, all `queued`, and only `index=1` flagged `is_baseline`.
- [ ] It enqueues exactly `run_count` tasks, each with the dotted path and single `response_id`
      argument named in `docs/backend/llm-contract.md`.
- [ ] `run_count` of `1` and of `6` are both rejected with `400`, and no rows are created.
- [ ] A prompt one character longer than the current `max_prompt_length` is rejected with `400` and
      `{"error": "prompt_too_long"}`; raising the limit via `PATCH /api/settings/` makes the same
      prompt succeed, proving the limit is read live rather than at import time.
- [ ] An unknown provider, or a model that belongs to the other provider, is rejected with `400`.
- [ ] `GET /api/runs/{id}/` returns the run for its owner and `404` for a second authenticated user.
- [ ] The run's top-level `status` is `queued` with all responses queued, `running` when one is
      `running` or `retrying`, and `complete` once every response is `complete` or `failed`.
- [ ] `POST /api/responses/{id}/retry/` returns `404` for a `complete` response and `202` for a `failed`
      one, resetting it to `queued` with `error_message` cleared and one new task enqueued.
- [ ] `POST /api/auth/logout/` deletes the session's runs and their responses; a subsequent
      `GET /api/runs/{id}/` after logging back in returns `404`.
- [ ] A `PromptRun` older than `RUN_TTL_HOURS` is removed when the purge task runs; a newer one is not.
- [ ] `pytest runs` passes and `manage.py migrate --check` exits `0`.

## Verification

```bash
cd "$(git rev-parse --show-toplevel)"
docker compose up -d db broker backend
docker compose run --rm backend pytest runs accounts -q
docker compose run --rm backend python manage.py migrate --check
docker compose run --rm backend python manage.py shell -c \
  "from django.db import connection as c; print([t for t in c.introspection.table_names() if 'run' in t or 'response' in t])"
```

## Evidence

_None recorded yet._
