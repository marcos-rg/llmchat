---
id: LLMC-AXS-001
title: Accessibility pass across all four screens
area: AXS
phase: 5
layer: frontend
status: todo
review: none
depends_on:
  - LLMC-RUNS-005
docs:
  read:
    - docs/frontend/style-guide.md
    - docs/frontend/animations.md
    - docs/frontend/components.md
    - docs/frontend/run-frontend.md
    - docs/frontend/diff-frontend.md
  write:
    - docs/frontend/accessibility.md
---

# LLMC-AXS-001 - Accessibility pass across all four screens

## Objective

After this task the usability and accessibility NFR is real rather than aspirational: every screen is
operable by keyboard alone, status changes are announced instead of being conveyed only by motion,
`prefers-reduced-motion` is honoured as `docs/frontend/animations.md` requires, and the contrast of
every token pair actually in use has been measured.

## Scope

**In:**

- Keyboard operability across Login, Setup, Run and Settings: logical tab order, no focus traps, the
  `:focus-visible` accent outline reachable on every interactive element, and the horizontally
  scrolling card row reachable and scrollable by keyboard.
- Semantics for the components the mock fakes with CSS: `SegmentedControl` as a real
  `role="radiogroup"` with an accessible name and arrow-key navigation, status tags exposing their
  status as text and not by colour or icon alone, the prompt counter and warning associated with the
  textarea via `aria-describedby`, and the too-long warning announced politely.
- An `aria-live="polite"` region announcing per-response status transitions on the Run screen, so a
  screen-reader user learns a response finished without polling the DOM.
- `@media (prefers-reduced-motion: reduce)` disabling the spinner and shimmer per
  `docs/frontend/animations.md`, keeping the status tag label as the sole indicator.
- Automated checks: `vitest-axe` (or equivalent) assertions on each page's rendered output, and a
  contrast test over every token pair in use, extending the check added in `LLMC-DIFF-003`.
- Fixes for whatever those checks surface, and `docs/frontend/accessibility.md` recording the result,
  the manual screen-reader pass and any accepted gaps.

**Out:**

- Responsive/mobile breakpoints — `docs/frontend/layouts.md` records them as an open design gap, not an
  a11y fix, and the mock is desktop-only.
- A full WCAG AA certification or an external audit; the spec asks for standard practices.
- Redesigning the blueprint skin: contrast issues are fixed by adjusting token values or usage, not by
  abandoning the visual language.
- Backend changes.

## Outputs

- Accessibility fixes across `src/pages/`, `src/components/`, `src/layouts/`
- `src/styles/reduced-motion.css`, `src/components/StatusAnnouncer.tsx`
- `src/test/a11y.test.tsx`, extended `src/styles/contrast.test.ts`
- `docs/frontend/accessibility.md` — what was checked, what was fixed, what remains

## Acceptance criteria

- [ ] Automated a11y assertions run over all four pages and report no violations at the serious or
      critical level.
- [ ] Every interactive element on every page is reachable by Tab in DOM order and shows the
      `:focus-visible` outline; asserted in tests for the segmented controls, retry button and nav.
- [ ] The provider, run-count and diff controls expose `role="radiogroup"` with an accessible name, and
      arrow keys move the selection.
- [ ] Every token pair in use meets 4.5:1 for text (3:1 for large text), asserted in a test that fails
      if a token value changes to something insufficient.
- [ ] With `prefers-reduced-motion: reduce` emulated, no spinner or shimmer animation runs and the
      status tag label is still rendered.
- [ ] A response moving from `running` to `complete` updates a polite live region containing the run
      label and the new status.
- [ ] The prompt textarea is programmatically associated with its counter and, when over the limit,
      with the warning text.
- [ ] `npm run lint`, `npx tsc --noEmit` and `npm test` pass, and `docs/frontend/accessibility.md`
      records the manual keyboard and screen-reader pass.

## Verification

```bash
cd "$(git rev-parse --show-toplevel)"
docker compose run --rm frontend npm run lint
docker compose run --rm frontend npx tsc --noEmit
docker compose run --rm frontend npm test -- --run
grep -q 'prefers-reduced-motion' -r frontend/src
grep -qi 'screen reader\|screen-reader' docs/frontend/accessibility.md
```

## Evidence

_None recorded yet._
