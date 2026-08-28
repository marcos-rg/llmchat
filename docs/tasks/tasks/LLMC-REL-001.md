---
id: LLMC-REL-001
title: Release: clean-clone setup, docs index and handover
area: REL
phase: 5
layer: release
status: todo
review: human
depends_on:
  - LLMC-SEC-001
  - LLMC-AXS-001
  - LLMC-PERF-001
  - LLMC-AUTH-004
  - LLMC-CFG-003
docs:
  read:
    - docs/infra/setup.md
    - docs/infra/stack-runbook.md
    - docs/infra/ci-pipeline.md
    - docs/infra/security-review.md
    - docs/infra/performance.md
  write:
    - docs/infra/release.md
---

# LLMC-REL-001 - Release: clean-clone setup, docs index and handover

## Objective

After this task the project is handed over: someone who has never seen it clones the repository, runs
two commands, and has the working system in front of them — with a README that matches reality, a
documentation set that describes what shipped rather than what was planned, and an explicit list of
known gaps.

## Scope

**In:**

- A clean-clone rehearsal: clone into an empty directory, `make setup` then `make up`, create a user,
  and walk the whole journey. Every step that needed knowledge not in the docs is a defect fixed here.
- README rewrite: what the project is, the two-command quickstart, the four screens, where the docs
  live, and how to run the tests.
- `.env.example` final pass: every variable the code reads is present with a safe default, nothing
  unused remains, and every LLM key stays empty with a note that the fake provider covers offline use.
- Documentation reconciliation: each doc under `docs/frontend/`, `docs/backend/` and `docs/infra/`
  updated where implementation diverged, as `docs/frontend/README.md` instructs, and each living doc
  linked from its section README.
- `docs/infra/release.md`: the release checklist, the verified state of every functional and
  non-functional requirement (drawing on the verification and review docs), and the known-gaps list
  (no responsive layout, no run history, no rate limiting, no cloud deployment, unused `.table` and
  `.dialog` components).
- Tagging the release and confirming CI is green on `main`.

**Out:**

- New features or new screens.
- Cloud/production deployment, gunicorn/static-build packaging, and any deploy job in CI — the spec's
  hosting target is local Compose only.
- Any fix that requires design judgement or new scope; those are recorded as known gaps or proposed
  follow-up tasks rather than absorbed here.

## Outputs

- Rewritten `README.md`, final `.env.example`
- Reconciled docs across `docs/backend/`, `docs/frontend/`, `docs/infra/`, with living docs linked from
  each section README
- `docs/infra/release.md` — release checklist, requirement verification summary, known gaps
- A git tag for the release

## Acceptance criteria

- [ ] In a fresh clone at a clean temporary path, `make setup` (non-interactive) followed by `make up`
      brings the whole stack healthy with no manual step beyond what the README states.
- [ ] In that fresh clone, `GET /api/health/` returns `200` and the SPA serves at `http://localhost:5173`.
- [ ] `make test` and `make lint` pass in the fresh clone.
- [ ] Every variable in `.env.example` is read somewhere in the codebase, and every variable the code
      reads is in `.env.example`; both provider keys are empty.
- [ ] `docs/infra/release.md` lists every functional requirement from `docs/specs/specs.md` with the
      verification doc that demonstrates it, and every non-functional requirement with its verdict.
- [ ] Every living doc named by a task's `docs.write` exists and is linked from its section README.
- [ ] `python3 scripts/tasks.py validate` passes and every other task is `done`.
- [ ] CI is green on `main` and the release tag points at that commit.
- [ ] A human has approved the release and the known-gaps list.

## Verification

```bash
cd "$(git rev-parse --show-toplevel)"
python3 scripts/tasks.py validate
python3 scripts/tasks.py list --status todo
T=$(mktemp -d)
git clone "$(git rev-parse --show-toplevel)" "$T/llmchat"
cd "$T/llmchat"
bash scripts/init.sh --no-superuser
make up-d
timeout 180 bash -c 'until curl -fsS http://localhost:8000/api/health/ >/dev/null; do sleep 2; done'
curl -fsS -o /dev/null -w '%{http_code}\n' http://localhost:5173/ | grep -q 200
make lint
make test
make down
cd "$(git rev-parse --show-toplevel)" 2>/dev/null || true
grep -q '^OPENAI_API_KEY=$' .env.example
grep -q '^ANTHROPIC_API_KEY=$' .env.example
gh run list --branch main --limit 3 || echo "no gh CLI: record the main CI result in evidence"
```

## Evidence

_None recorded yet._
