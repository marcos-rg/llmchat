---
id: LLMC-DIFF-003
title: Diff rendering and on/off toggle on the Run page
area: DIFF
phase: 4
layer: frontend
status: todo
review: none
depends_on:
  - LLMC-RUNS-004
  - LLMC-DIFF-002
docs:
  read:
    - docs/backend/diff-contract.md
    - docs/backend/diff-backend.md
    - docs/frontend/states.md
    - docs/frontend/run-frontend.md
    - docs/frontend/style-guide.md
  write:
    - docs/frontend/diff-frontend.md
---

# LLMC-DIFF-003 - Diff rendering and on/off toggle on the Run page

## Objective

After this task the product's headline feature is complete in the UI: differences between each
response and the baseline are highlighted automatically, and one toggle turns the highlighting off
without hiding a single character of the response — the last two functional requirements in
`docs/specs/specs.md`.

## Scope

**In:**

- Rendering `diff_tokens` in `ResponseCard`: each token as `<mark>` when `hl` is true and the toggle is
  on, otherwise a plain span, per `docs/frontend/states.md` and `docs/backend/diff-contract.md`.
- The "Diff highlighting" `SegmentedControl` (On/Off) in the Run header, holding UI-only state that is
  never sent to the API.
- The rule that the toggle affects only `complete`, non-baseline cards: the baseline renders its own
  `response_text` plain, and a card whose `diff_tokens` are `null` (baseline unfinished or response
  failed) renders plain text rather than an empty body.
- `<mark>` styling from `docs/frontend/style-guide.md` (`--color-accent-200` background,
  `--color-accent-800` text) and a unit-tested contrast check of that pair against the WCAG AA
  threshold.
- Update `docs/frontend/run-frontend.md` to point at the new diff behaviour, and record the shipped
  rendering rules in the new living doc.

**Out:**

- Any client-side diff computation — tokens come from the API (`LLMC-DIFF-002`).
- Per-card toggles, diff modes (word/character/semantic), or choosing a different baseline.
- The broader accessibility audit (`LLMC-AXS-001`); this task owns only the contrast of the diff mark.

## Outputs

- Diff rendering in `src/components/ResponseCard.tsx`, `src/components/DiffText.tsx`, toggle state in
  `src/pages/Run.tsx`
- `src/components/DiffText.test.tsx`, contrast test in `src/styles/contrast.test.ts`
- `docs/frontend/diff-frontend.md` — shipped diff rendering, toggle semantics and the contrast result

## Acceptance criteria

- [ ] With the toggle on, a non-baseline complete card renders a `<mark>` for every token with
      `hl: true` and no `<mark>` for the others.
- [ ] With the toggle off, the same card renders no `<mark>` elements at all, and its visible text is
      still character-for-character equal to the response text.
- [ ] In both toggle states, the card's text content equals the concatenation of the token texts.
- [ ] The baseline card renders identically whatever the toggle state, and contains no `<mark>`.
- [ ] A complete card whose `diff_tokens` are `null` renders its full `response_text` as plain text.
- [ ] Toggling issues no network request.
- [ ] The `--color-accent-200` / `--color-accent-800` pair used by `<mark>` meets a contrast ratio of at
      least 4.5:1, asserted in a test rather than by inspection.
- [ ] `npm run lint`, `npx tsc --noEmit` and `npm test` pass.

## Verification

```bash
cd "$(git rev-parse --show-toplevel)"
docker compose run --rm frontend npm run lint
docker compose run --rm frontend npx tsc --noEmit
docker compose run --rm frontend npm test -- --run
```

## Evidence

_None recorded yet._
