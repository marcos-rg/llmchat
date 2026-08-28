---
id: LLMC-RUNS-004
title: Run page: response cards, polling and retry
area: RUNS
phase: 4
layer: frontend
status: todo
review: human
depends_on:
  - LLMC-RUNS-003
  - LLMC-RUNS-002
docs:
  read:
    - docs/frontend/pages.md
    - docs/frontend/states.md
    - docs/frontend/layouts.md
    - docs/frontend/animations.md
    - docs/frontend/interfaces.md
    - docs/backend/runs-backend.md
  write:
    - docs/frontend/run-frontend.md
---

# LLMC-RUNS-004 - Run page: response cards, polling and retry

## Objective

After this task the comparison screen is live: responses appear side by side as a horizontally
scrolling row with the baseline pinned, each card renders the right one of the five states from
`docs/frontend/states.md`, polling drives those states without a manual refresh, and a failed response
can be retried from its own card. This is the screen the whole product exists to show, so it carries a
human visual/UX review.

## Scope

**In:**

- `src/pages/Run.tsx`: header row with the `tag-accent` "{provider} · {model}" badge and the prompt
  text, and the full-width body from `docs/frontend/layouts.md` (`display:flex; overflow-x:auto`,
  340px fixed-width cards, baseline card `position: sticky; left: 0` with its own surface background
  and directional shadow).
- `src/components/ResponseCard.tsx` owning all five status layouts internally as a single lookup on
  `status` (never independent booleans), with the tag variant, icon and body content from
  `docs/frontend/states.md`, the "Baseline" outline tag on `index=1`, and blueprint corner ticks.
- `src/components/Shimmer.tsx` and the `spin`/`shimmer` keyframes from `docs/frontend/animations.md`,
  with the documented bar counts and widths per status.
- `src/hooks/usePolling.ts`: polls `GET /api/runs/{id}/` about every 2s, stops when the run-level
  status is `complete`, resumes after a retry, stops on unmount, and never overlaps requests.
- Retry: the failed card's `.btn-secondary` posts `POST /api/responses/{id}/retry/`, moves the card to
  `retrying` and resumes polling.
- Error and edge handling: a `404` from the poll (run purged or not owned) renders a clear empty state
  with a link back to New run, rather than polling forever.
- Vitest/RTL + msw tests for every criterion below.

**Out:**

- Diff token rendering and the diff on/off toggle (`LLMC-DIFF-003`) — cards render `response_text`
  plainly for now.
- The mock's "Demo: phase" control, which is a prototype affordance and must not ship.
- `prefers-reduced-motion` handling and the a11y audit (`LLMC-AXS-001`).
- Websockets or server-sent events: the spec calls for periodic polling.
- Any run history, sharing or export.

## Outputs

- `src/pages/Run.tsx`, `src/components/ResponseCard.tsx`, `src/components/Shimmer.tsx`,
  `src/hooks/usePolling.ts`, `src/api/runs.ts` (`getRun`, `retryResponse`)
- `src/pages/Run.test.tsx`, `src/components/ResponseCard.test.tsx`, `src/hooks/usePolling.test.ts`
- `docs/frontend/run-frontend.md` — shipped Run screen behaviour, the polling contract as implemented,
  and the demo-only controls that were dropped

## Acceptance criteria

- [ ] For a run with five responses, five cards render in a container with `overflow-x: auto`, and the
      `index=1` card carries the "Baseline" tag and sticky positioning.
- [ ] Each status renders its documented treatment: `queued` shows three shimmer bars and the Queued
      tag, `running` and `retrying` show two bars and a spinning icon with their own tag labels,
      `complete` shows the response text with the Complete tag, `failed` shows `error_message` and a
      Retry button.
- [ ] Given a mocked poll sequence (all queued → one running → all complete), the cards update without
      user interaction and no further poll is issued after the run reports `complete`.
- [ ] Only one poll request is in flight at a time, and polling stops when the component unmounts.
- [ ] Clicking Retry on a failed card posts to `/api/responses/{id}/retry/`, switches that card to
      `retrying`, and resumes polling for a run that had already stopped.
- [ ] A `404` from the poll endpoint renders the empty state and issues no further polls.
- [ ] Nothing in the shipped page exposes a manual status/phase control.
- [ ] `npm run lint`, `npx tsc --noEmit` and `npm test` pass.
- [ ] A human has reviewed the screen against `docs/frontend/mock/LLMChat Mockups.dc.html` and approved
      the visual result.

## Verification

```bash
cd "$(git rev-parse --show-toplevel)"
docker compose run --rm frontend npm run lint
docker compose run --rm frontend npx tsc --noEmit
docker compose run --rm frontend npm test -- --run
! grep -rniE 'demo.?phase' frontend/src
make up-d
timeout 120 bash -c 'until curl -fsS http://localhost:5173/ >/dev/null; do sleep 2; done'
echo "Open http://localhost:5173 , start a run, and screenshot the Run screen for the review gate."
```

## Evidence

_None recorded yet._
