---
id: LLMC-DIFF-001
title: Diff token wire format contract
area: DIFF
phase: 4
layer: contract
status: todo
review: none
depends_on:
  - LLMC-RUNS-001
docs:
  read:
    - docs/backend/api-endpoints.md
    - docs/frontend/interfaces.md
    - docs/frontend/states.md
    - docs/backend/runs-backend.md
  write:
    - docs/backend/diff-contract.md
---

# LLMC-DIFF-001 - Diff token wire format contract

## Objective

After this task the one shape the frontend is currently guessing at is decided and written down.
`docs/backend/api-endpoints.md` only ever shows `diff_tokens: null`, and
`docs/frontend/interfaces.md` flags its `{text, hl}` assumption as unconfirmed. This contract fixes
the token schema, the tokenisation rule, when the field is populated and when it is `null`, so the
backend and the Run screen can be built against the same definition.

## Scope

**In:** `docs/backend/diff-contract.md` covering:

- The token object: field names, types, and the invariant that concatenating every `text` in order
  reproduces the response's `response_text` exactly, whitespace included — this is what lets the UI
  render raw text with the toggle off without a second field.
- The tokenisation rule (word-level with trailing whitespace attached, per
  `docs/frontend/interfaces.md`), the algorithm (`difflib.SequenceMatcher` over the token lists) and
  which opcodes set `hl: true`.
- A worked example: two short response texts plus the exact token list the implementation must produce,
  reproduced literally so `LLMC-DIFF-002` can assert against it.
- Population rules: `diff_tokens` is non-null only for a `complete`, non-baseline response whose
  baseline (`index=1`) is also `complete`; it is `null` for the baseline, for any non-terminal or
  `failed` response, and while the baseline is unfinished or itself failed. What the UI shows in that
  last case (plain text, no highlighting) is stated explicitly.
- The decision not to persist the field (derived on read, per `docs/backend/db-schema.md`), plus the
  size and cost bound: the maximum tokens diffed per response and the behaviour beyond it.
- Amending `docs/backend/api-endpoints.md` so the `GET /api/runs/{id}/` example shows a populated
  `diff_tokens`, and confirming or correcting the assumption block in `docs/frontend/interfaces.md`.

**Out:**

- Implementation, backend (`LLMC-DIFF-002`) or frontend (`LLMC-DIFF-003`).
- Character-level or semantic/embedding-based diffing, similarity scores, and diffing responses against
  anything other than the baseline — the spec asks only for differences to be highlighted.
- Choosing the highlight colours; `docs/frontend/style-guide.md` already fixes them.

## Outputs

- `docs/backend/diff-contract.md`
- Updated `docs/backend/api-endpoints.md` (populated `diff_tokens` example)
- Updated `docs/frontend/interfaces.md` (assumption confirmed, marked as agreed)

## Acceptance criteria

- [ ] The contract defines the token object with every field name and type, and states the
      concatenation invariant.
- [ ] It names the tokenisation rule and the diff algorithm, and says which opcodes produce `hl: true`.
- [ ] It contains a worked example with two input texts and the exact expected token list.
- [ ] It enumerates every case in which `diff_tokens` is `null`, including the unfinished-baseline and
      failed-baseline cases.
- [ ] `docs/backend/api-endpoints.md` shows at least one non-null `diff_tokens` example under
      `GET /api/runs/{id}/`.
- [ ] `docs/frontend/interfaces.md` no longer describes the shape as an unconfirmed working assumption.
- [ ] The contract contradicts nothing in `docs/frontend/states.md`: both state that with the toggle
      off the full response text stays readable rather than hidden.
- [ ] Every relative markdown link in the contract resolves.

## Verification

```bash
cd "$(git rev-parse --show-toplevel)"
C=docs/backend/diff-contract.md
test -f "$C"
grep -q 'hl' "$C" && grep -q 'text' "$C"
grep -qi 'concaten' "$C"
grep -qi 'SequenceMatcher' "$C"
grep -qi 'baseline' "$C"
grep -qi 'null' "$C"
grep -A3 'diff_tokens' docs/backend/api-endpoints.md | grep -q '"hl"'
! grep -qi 'working assumption' docs/frontend/interfaces.md
grep -o '](\.\./[^)#]*\|](\./[^)#]*' "$C" | sed 's/^](//' | while read -r l; do \
  test -e "docs/backend/$l" || { echo "broken link: $l"; exit 1; }; done
```

## Evidence

_None recorded yet._
