---
id: LLMC-LLM-002
title: LangChain provider adapters and generate_response worker task
area: LLM
phase: 3
layer: backend
status: todo
review: none
depends_on:
  - LLMC-LLM-001
  - LLMC-RUNS-001
docs:
  read:
    - docs/backend/llm-contract.md
    - docs/backend/runs-backend.md
    - docs/infra/testing.md
  write:
    - docs/backend/llm-worker.md
---

# LLMC-LLM-002 - LangChain provider adapters and generate_response worker task

## Objective

After this task queued responses actually get generated: the `worker` container picks up each task,
calls OpenAI or Anthropic through a uniform LangChain adapter (or the offline fake provider), and
writes the result or a scrubbed error back to PostgreSQL with the status transitions the contract
specifies. This closes the async pipeline — the backend half of the product's core feature.

## Scope

**In:**

- `backend/llm/client.py` implementing `generate(...)` per `docs/backend/llm-contract.md`, with
  `backend/llm/providers/{openai,anthropic,fake}.py` adapters and the documented error taxonomy
  mapping SDK/LangChain exceptions onto typed errors.
- `LLM_FAKE_PROVIDER`, `LLM_TIMEOUT_SECONDS`, `LLM_MAX_ATTEMPTS` wired into settings, `.env.example`
  and the `worker` service's Compose environment (never the `backend` or `frontend` service).
- Key-masking log filter applied to the worker's logging configuration, covering exception messages.
- `backend/runs/tasks.py::generate_response(response_id)`: the transitions, timestamps, `retry_count`
  handling, retryable-vs-fatal behaviour and duplicate-delivery guard from the contract.
- Django-Q2 `Q_CLUSTER` timeout/retry/max-attempts values consistent with the contract.
- `llm/tests/` with the provider clients mocked at the contract's patch point (success, each error
  class, timeout, empty key) and `runs/tests/test_task.py` asserting the DB effects; one sync-mode
  integration test that `POST /api/runs/` with the fake provider yields `run_count` complete responses.

**Out:**

- Streaming, token accounting, cost tracking, model fallback and LangGraph multi-step flows.
- Diffing (`LLMC-DIFF-002`) and any UI.
- Real-provider integration tests — `docs/infra/testing.md` rules them out; adapters are exercised
  against mocks and the fake provider only.
- Changing the run API surface (`LLMC-RUNS-001` owns it).

## Outputs

- `backend/llm/client.py`, `backend/llm/providers/{openai,anthropic,fake}.py`,
  `backend/llm/errors.py`, `backend/core/logging.py` (masking filter)
- `backend/runs/tasks.py`
- `.env.example` and `docker-compose.yml` updates for the three LLM variables
- `backend/llm/tests/`, `backend/runs/tests/test_task.py`
- `docs/backend/llm-worker.md` — shipped adapter behaviour, retry/timeout values, fake-provider usage
  and how to add a provider

## Acceptance criteria

- [ ] With the provider client mocked to succeed, `generate_response(id)` moves the row
      `queued -> running -> complete`, stores `response_text`, and sets both `started_at` and
      `completed_at`.
- [ ] With the client mocked to raise a retryable error every time, the row ends `failed` after exactly
      `LLM_MAX_ATTEMPTS` attempts with `retry_count` equal to the attempts made, and `error_message` set.
- [ ] With the client mocked to raise a fatal error (auth/bad request), exactly one attempt is made.
- [ ] An empty API key produces `ProviderNotConfigured`, a `failed` row and no network call.
- [ ] `error_message` never contains the API key, and a key value passed through a raised exception
      does not appear in captured log output.
- [ ] Delivering the same task twice for a `complete` response does not overwrite `response_text` or
      re-issue a provider call.
- [ ] In sync test mode with `LLM_FAKE_PROVIDER=1`, `POST /api/runs/` with `run_count: 3` leaves three
      `complete` responses whose texts are not all identical, and a prompt starting with `FAIL:` leaves
      them `failed`.
- [ ] No test performs a network call (asserted by patching the transport to raise).
- [ ] `pytest llm runs` passes with both provider keys set to empty strings.

## Verification

```bash
cd "$(git rev-parse --show-toplevel)"
docker compose up -d db broker
docker compose run --rm -e OPENAI_API_KEY= -e ANTHROPIC_API_KEY= backend pytest llm runs -q --cov=llm --cov=runs
docker compose run --rm backend ruff check .
docker compose run --rm backend python -c "import os,sys; sys.exit(1 if os.environ.get('OPENAI_API_KEY') or os.environ.get('ANTHROPIC_API_KEY') else 0)"
docker compose config | grep -A40 'worker:' | grep -q 'LLM_FAKE_PROVIDER'
grep -q 'LLM_FAKE_PROVIDER' .env.example
```

## Evidence

_None recorded yet._
