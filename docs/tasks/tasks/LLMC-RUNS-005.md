---
id: LLMC-RUNS-005
title: Verify the full compare-responses slice end to end
area: RUNS
phase: 4
layer: verify
status: todo
review: none
depends_on:
  - LLMC-RUNS-004
  - LLMC-DIFF-003
docs:
  read:
    - docs/frontend/run-frontend.md
    - docs/frontend/diff-frontend.md
    - docs/backend/runs-backend.md
    - docs/infra/stack-runbook.md
  write:
    - docs/infra/verification-run-slice.md
---

# LLMC-RUNS-005 - Verify the full compare-responses slice end to end

## Objective

After this task the product's main journey is proven on the real stack from the browser's point of
view: log in, configure a run, watch statuses arrive by polling, compare highlighted responses, toggle
the highlighting off, retry a failure, and log out to find nothing left behind. This is the slice that
makes every functional requirement in `docs/specs/specs.md` demonstrable.

## Scope

**In:**

- `scripts/verify-run-slice.sh`: an API-level walk of the whole journey against a stack running with
  `LLM_FAKE_PROVIDER=1` — login, `POST /api/runs/` with `run_count: 5`, poll to terminal, assert the
  baseline has `diff_tokens: null` while the others are populated, assert every token concatenation
  reconstructs its `response_text`, force a failure and retry it, then log out and assert the run is
  gone (`404`).
- A recorded manual browser walkthrough of the same journey with screenshots or notes per step,
  including the diff toggle on and off and the prompt-too-long warning.
- A requirements trace table in the living doc mapping each functional requirement in
  `docs/specs/specs.md` to the step that demonstrates it, so any gap becomes visible now rather than at
  release.
- `docs/infra/verification-run-slice.md`.

**Out:**

- Adding a browser E2E framework or putting this in CI (`docs/infra/testing.md` rules it out).
- Load/concurrency measurement (`LLMC-PERF-001`), the security audit (`LLMC-SEC-001`) and the
  accessibility audit (`LLMC-AXS-001`) — each has its own task in phase 5.
- Calling real providers.

## Outputs

- `scripts/verify-run-slice.sh`
- `docs/infra/verification-run-slice.md` (procedure, recorded walkthrough, requirements trace table)

## Acceptance criteria

- [ ] `bash scripts/verify-run-slice.sh` exits `0` against a `make up-d` stack with
      `LLM_FAKE_PROVIDER=1`.
- [ ] The script asserts a five-response run reaches run status `complete` by polling alone, with all
      five responses terminal.
- [ ] It asserts `diff_tokens` is `null` on the baseline and non-null on every other complete response,
      and that at least one token has `hl: true` (the fake provider varies its output).
- [ ] It asserts, for each non-baseline complete response, that joining its token texts equals its
      `response_text`.
- [ ] It exercises the failure path: a `FAIL:` run ends `failed`, `POST /api/responses/{id}/retry/`
      returns `202`, and the response reaches a terminal state again.
- [ ] It asserts that after `POST /api/auth/logout/`, re-logging in and requesting the same run returns
      `404`.
- [ ] The living doc's trace table has a row for every functional requirement in
      `docs/specs/specs.md`, each marked demonstrated or flagged as a gap.

## Verification

```bash
cd "$(git rev-parse --show-toplevel)"
make up-d
timeout 120 bash -c 'until curl -fsS http://localhost:8000/api/health/ >/dev/null; do sleep 2; done'
bash scripts/verify-run-slice.sh
D=docs/infra/verification-run-slice.md
grep -qi 'trace' "$D"
test "$(grep -c '^| ' "$D")" -ge 11
grep -qi 'toggle' "$D"
```

## Evidence

_None recorded yet._
