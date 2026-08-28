---
id: LLMC-DIFF-002
title: Server-side diff computation on the run poll endpoint
area: DIFF
phase: 4
layer: backend
status: todo
review: none
depends_on:
  - LLMC-DIFF-001
  - LLMC-RUNS-001
docs:
  read:
    - docs/backend/diff-contract.md
    - docs/backend/runs-backend.md
  write:
    - docs/backend/diff-backend.md
---

# LLMC-DIFF-002 - Server-side diff computation on the run poll endpoint

## Objective

After this task `GET /api/runs/{id}/` returns real diff tokens: every complete non-baseline response
carries a word-level comparison against the baseline, computed on read exactly as
`docs/backend/diff-contract.md` specifies, so the Run screen only ever has to toggle their rendering.

## Scope

**In:**

- `backend/runs/diff.py`: tokenisation and `SequenceMatcher`-based token building per the contract,
  including the concatenation invariant and the size bound.
- Wiring it into the run serializer so `diff_tokens` is populated only under the contract's conditions
  and `null` in every other case, without extra queries per response (baseline fetched once).
- `runs/tests/test_diff.py`: the contract's worked example asserted literally, the identical-text case,
  the fully-different case, the unfinished/failed-baseline cases, and the invariant checked as a
  property over generated pairs.
- Update `docs/backend/runs-backend.md`'s description of the poll payload to point at the new behaviour.

**Out:**

- Persisting diffs to the database (the contract rules it out).
- Any rendering, toggle or markup (`LLMC-DIFF-003`).
- Diffing against anything other than `index=1`, and any similarity metric or score.
- Changing the status semantics or any other part of the run API (`LLMC-RUNS-001` owns it).

## Outputs

- `backend/runs/diff.py`, updated `backend/runs/serializers.py`
- `backend/runs/tests/test_diff.py`
- `docs/backend/diff-backend.md` — the shipped implementation, its complexity/size bound and how it is
  exercised

## Acceptance criteria

- [ ] For the worked example in `docs/backend/diff-contract.md`, the produced token list matches the
      documented one exactly.
- [ ] For every response, joining `token["text"]` in order equals `response_text` character for
      character, including whitespace.
- [ ] Two identical responses produce tokens with `hl: false` throughout.
- [ ] The baseline response always has `diff_tokens: null`, whatever its status.
- [ ] A `complete` non-baseline response has `diff_tokens: null` while the baseline is not yet
      `complete`, and is populated on the next poll once the baseline completes.
- [ ] A `failed` response has `diff_tokens: null` and a non-null `error_message`.
- [ ] `GET /api/runs/{id}/` for a five-response run issues no more database queries than it did before
      this task plus one (asserted with `assertNumQueries`).
- [ ] `pytest runs` passes.

## Verification

```bash
cd "$(git rev-parse --show-toplevel)"
docker compose up -d db broker
docker compose run --rm backend pytest runs -q
docker compose run --rm backend ruff check .
```

## Evidence

_None recorded yet._
