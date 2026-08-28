---
id: LLMC-PERF-001
title: Concurrency check for 10 simultaneous users
area: PERF
phase: 5
layer: verify
status: todo
review: none
depends_on:
  - LLMC-RUNS-005
docs:
  read:
    - docs/specs/specs.md
    - docs/infra/architecture.md
    - docs/backend/llm-worker.md
    - docs/infra/environment.md
  write:
    - docs/infra/performance.md
---

# LLMC-PERF-001 - Concurrency check for 10 simultaneous users

## Objective

After this task the one quantified non-functional requirement in `docs/specs/specs.md` — "at least 10
concurrent users without noticeable degradation" — has a measurement behind it, and `Q_CLUSTER_WORKERS`
has a value chosen from evidence rather than from the `.env.example` default.

## Scope

**In:**

- `scripts/verify-load.sh`: with `LLM_FAKE_PROVIDER=1` and a configured fake delay, log in 10 distinct
  users, have each submit a `run_count: 5` run at the same time (50 queued generations), and poll all
  ten runs to terminal while recording API latency percentiles for `POST /api/runs/` and
  `GET /api/runs/{id}/`, plus total drain time for the queue.
- A short sweep over `Q_CLUSTER_WORKERS` (for example 2 / 4 / 8) recording drain time and worker
  container CPU/memory, ending in a recommended default written into `.env.example` and
  `docs/infra/environment.md`.
- Confirming the requirement's real content: the API stays responsive while the queue is saturated —
  submitting an eleventh run during the load returns `201` quickly rather than blocking behind
  generation.
- `docs/infra/performance.md`: method, raw numbers, the chosen worker count and its rationale, plus the
  limits deliberately not addressed.

**Out:**

- Performance optimisation work: the spec explicitly requires no optimisation at this stage. Findings
  become recorded facts or follow-up tasks, not refactors here.
- Load against real providers (cost and rate limits make it meaningless as a system measurement).
- Horizontal scaling, autoscaling, connection pooling and caching — all out of scope per the spec.
- Frontend rendering performance.

## Outputs

- `scripts/verify-load.sh`
- Updated `Q_CLUSTER_WORKERS` default in `.env.example` and `docs/infra/environment.md`
- `docs/infra/performance.md` — method, measurements, chosen configuration, known limits

## Acceptance criteria

- [ ] `bash scripts/verify-load.sh` exits `0`: all 10 concurrent runs reach terminal status with no
      response left non-terminal and no task lost.
- [ ] `POST /api/runs/` p95 stays under 1s and `GET /api/runs/{id}/` p95 under 500ms while the queue is
      saturated, with the measured values recorded.
- [ ] A run submitted while the queue is saturated still returns `201` within the same latency bound,
      proving the API path is never blocked by generation.
- [ ] No `ModelResponse` is left `running` after the queue drains, and no duplicate generation occurs
      (each completed response has exactly one `completed_at` and its `retry_count` is unchanged).
- [ ] `docs/infra/performance.md` records drain time for at least three `Q_CLUSTER_WORKERS` values and
      names the chosen default.
- [ ] `.env.example` and `docs/infra/environment.md` carry that chosen default.

## Verification

```bash
cd "$(git rev-parse --show-toplevel)"
make up-d
timeout 120 bash -c 'until curl -fsS http://localhost:8000/api/health/ >/dev/null; do sleep 2; done'
bash scripts/verify-load.sh
docker compose run --rm backend python manage.py shell -c \
  "from runs.models import ModelResponse as M; assert not M.objects.filter(status='running').exists()"
P=docs/infra/performance.md
grep -qi 'p95' "$P"
grep -q 'Q_CLUSTER_WORKERS' "$P"
grep -q 'Q_CLUSTER_WORKERS' .env.example
```

## Evidence

_None recorded yet._
