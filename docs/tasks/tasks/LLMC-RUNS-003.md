---
id: LLMC-RUNS-003
title: Setup page: run configuration form and submission
area: RUNS
phase: 4
layer: frontend
status: todo
review: none
depends_on:
  - LLMC-RUNS-001
  - LLMC-CFG-002
docs:
  read:
    - docs/frontend/pages.md
    - docs/frontend/interfaces.md
    - docs/frontend/components.md
    - docs/backend/runs-backend.md
    - docs/backend/config-backend.md
  write:
    - docs/frontend/setup-frontend.md
---

# LLMC-RUNS-003 - Setup page: run configuration form and submission

## Objective

After this task a user can actually start a run from the browser: the "New run" screen from
`docs/frontend/pages.md` loads the catalog, library and limit, warns before the prompt gets too long,
and submits `POST /api/runs/` before handing off to the Run screen.

## Scope

**In:**

- `src/pages/Setup.tsx` in the authenticated shell, centred narrow column: eyebrow tag, `h1`, subtitle,
  and the field order from `docs/frontend/pages.md`.
- Provider/Model row as a CSS grid: provider `SegmentedControl` (OpenAI/Anthropic) and a model
  `<select>` repopulated from the selected provider's list, both from `GET /api/providers/`.
- System-prompt field with the "Manage library →" link to `/settings`, seeded from the shared draft
  state written by `LLMC-CFG-002`'s "Use" action, falling back to the first library prompt.
- `PromptField` component owning its own `N / max` counter (`max` from `GET /api/settings/`), the
  warning-accent colour flip past the limit, and the conditional blueprint warning block.
- Run-count `SegmentedControl` (2/3/4/5) and the `.btn-primary.btn-block` submit labelled
  "Run prompt {runCount} times", disabled while the prompt is too long or empty.
- `src/api/runs.ts` (`createRun`) and navigation to `/runs/{id}` on `201`; server-side `400` errors
  surfaced inline using the same warning language.
- Reusable `SegmentedControl` and `PromptField` components with the prop boundaries from
  `docs/frontend/interfaces.md`, plus their own component tests.

**Out:**

- The Run screen itself (`LLMC-RUNS-004`) and diff rendering (`LLMC-DIFF-003`).
- Persisting the draft across reloads or sessions — data is ephemeral by spec; in-memory state only.
- Editing the system-prompt library (read-only API) and any per-run advanced options such as
  temperature, which the spec does not include.
- The accessibility audit (`LLMC-AXS-001`).

## Outputs

- `src/pages/Setup.tsx`, `src/components/SegmentedControl.tsx`, `src/components/PromptField.tsx`,
  `src/api/runs.ts`
- `src/pages/Setup.test.tsx`, `src/components/{SegmentedControl,PromptField}.test.tsx`
- `docs/frontend/setup-frontend.md` — shipped form behaviour, validation mirroring and the draft handoff

## Acceptance criteria

- [ ] With a mocked catalog, selecting Anthropic replaces the model options with Anthropic's models and
      resets the selected model to that provider's first entry.
- [ ] The counter renders `{length} / {max}` using `max_prompt_length` from the mocked settings
      endpoint, updating as the user types.
- [ ] Typing one character past the limit shows the warning block naming the limit, applies the warning
      colour class to the counter, and disables the submit button; deleting a character re-enables it.
- [ ] The submit button is disabled while the prompt is empty.
- [ ] The button label reflects the selected run count (`"Run prompt 5 times"` after choosing 5).
- [ ] Submitting posts exactly `{provider, model, system_prompt, prompt, run_count}` to `/api/runs/`
      and, on a mocked `201`, navigates to `/runs/{id}`.
- [ ] A mocked `400` with `{"error": "prompt_too_long"}` renders its `detail` and stays on the page.
- [ ] Arriving from Settings' "Use" action pre-fills the system-prompt field with the chosen text.
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
