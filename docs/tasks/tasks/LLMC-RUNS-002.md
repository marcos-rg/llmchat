---
id: LLMC-RUNS-002
title: Verify the async generation pipeline on the running stack
area: RUNS
phase: 3
layer: verify
status: todo
review: none
depends_on:
  - LLMC-RUNS-001
  - LLMC-LLM-002
docs:
  read:
    - docs/backend/runs-backend.md
    - docs/backend/llm-worker.md
    - docs/infra/stack-runbook.md
  write:
    - docs/infra/verification-runs-pipeline.md
---

# LLMC-RUNS-002 - Verify the async generation pipeline on the running stack

## Objective

After this task the asynchronous pipeline is proven across real containers rather than in sync-mode
tests: a run submitted to the API is fanned out over Redis, executed by the `worker` process, and
observed transitioning to terminal states by polling — including the failure and retry path, and a
check that a configured API key never appears in any container's logs.

## Scope

**In:**

- `scripts/verify-pipeline.sh`, run against a stack started with `LLM_FAKE_PROVIDER=1`: log in, submit
  a `run_count: 3` run, poll `GET /api/runs/{id}/` until the run reports `complete`, and assert the
  per-response outcome; then submit a `FAIL:`-prefixed prompt, assert the responses end `failed` with a
  non-empty `error_message`, call the retry endpoint and assert the response returns to `queued` and is
  picked up again.
- A restart-resilience check, matching the spec's "failed background jobs should be recoverable by
  restarting the affected component": submit a run, `docker compose restart worker broker`, and assert
  the run still reaches a terminal state without data loss.
- A key-leak check: start the worker with a recognisable dummy key, run a generation, and assert the
  value appears in no container's logs.
- `docs/infra/verification-runs-pipeline.md` recording the procedure, the observed timings and the
  results.

**Out:**

- Any UI — the Setup and Run screens do not exist yet; this is an API-level verification.
- Diffing, which is not implemented yet (`LLMC-DIFF-002`).
- Load and concurrency measurement (`LLMC-PERF-001`).
- Calling real providers: verification runs against the fake provider so it costs nothing and is
  deterministic.

## Outputs

- `scripts/verify-pipeline.sh`
- `docs/infra/verification-runs-pipeline.md` (procedure + recorded run, including observed
  queued/running/complete timings)

## Acceptance criteria

- [ ] `bash scripts/verify-pipeline.sh` exits `0` against a stack running with `LLM_FAKE_PROVIDER=1`.
- [ ] The script asserts that a `run_count: 3` submission returns `201` in under two seconds and that
      all three responses are `queued` in that response — the API does not wait on generation.
- [ ] The script observes each response reach `complete` by polling, and asserts every completed
      response has non-empty `response_text` and a `completed_at`.
- [ ] The script asserts a `FAIL:` run ends with `failed` responses carrying an `error_message`, that
      `POST /api/responses/{id}/retry/` returns `202`, and that the response is re-processed to a
      terminal state afterwards.
- [ ] With `worker` and `broker` restarted mid-run, the run still reaches a terminal state and no
      response is left `running` indefinitely.
- [ ] A dummy key configured on the worker appears in no output of `docker compose logs` for any
      service.
- [ ] With the `worker` service stopped, a submitted run's responses stay `queued` and the run's status
      stays `queued` - proving the API never generates inline.

## Verification

```bash
cd "$(git rev-parse --show-toplevel)"
make up-d
timeout 120 bash -c 'until curl -fsS http://localhost:8000/api/health/ >/dev/null; do sleep 2; done'
bash scripts/verify-pipeline.sh
docker compose logs --no-color | grep -c 'sk-verify-dummy-key' | grep -q '^0$'
grep -qi 'restart' docs/infra/verification-runs-pipeline.md
```

## Evidence

_None recorded yet._
