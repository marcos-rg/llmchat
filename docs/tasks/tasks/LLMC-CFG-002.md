---
id: LLMC-CFG-002
title: Settings page: prompt library, limits and provider status
area: CFG
phase: 2
layer: frontend
status: todo
review: none
depends_on:
  - LLMC-CFG-001
  - LLMC-AUTH-003
docs:
  read:
    - docs/backend/config-backend.md
    - docs/frontend/pages.md
    - docs/frontend/interfaces.md
    - docs/frontend/components.md
    - docs/frontend/auth-frontend.md
  write:
    - docs/frontend/settings-frontend.md
---

# LLMC-CFG-002 - Settings page: prompt library, limits and provider status

## Objective

After this task the Settings screen from `docs/frontend/pages.md` is real: it lists the saved system
prompts with a "Use" action, lets a staff user change the maximum prompt length (and visibly refuses
to offer that control to everyone else), and shows provider connection status sourced from the API
rather than hardcoded names.

## Scope

**In:**

- `src/pages/Settings.tsx` inside the authenticated shell, centred narrow column per
  `docs/frontend/layouts.md`: eyebrow tag, `h1`, and the three sections from `docs/frontend/pages.md`.
- Saved system prompts: one `.card.blueprint` per prompt (name, text, "Use" button) loaded from
  `GET /api/system-prompts/`.
- "Use" writes the chosen prompt text into shared app state and navigates to `/`. Consuming that value
  in the run configuration form belongs to `LLMC-RUNS-003`; this task only owns storing it and the
  navigation.
- Prompt limits: numeric `.input` (`min=100 max=4000 step=50`) loaded from `GET /api/settings/`,
  `PATCH`ed on blur when changed, gated on `user.is_staff` — non-staff see it disabled with an
  explanatory line, never a control that produces a `403` on use.
- Provider connections: `tag-accent` badges built from `GET /api/providers/`, plus the "keys are
  configured by your admin" copy.
- `src/api/{settings,systemPrompts,providers}.ts` typed clients matching
  `docs/frontend/interfaces.md`.
- Vitest/RTL + msw tests for every criterion below.

**Out:**

- Creating, editing or deleting saved prompts — the API is read-only (`LLMC-CFG-001`).
- The Setup and Run screens (`LLMC-RUNS-003`, `LLMC-RUNS-004`).
- Any display or entry of provider API keys anywhere in the UI — forbidden by the spec.
- The accessibility audit (`LLMC-AXS-001`).

## Outputs

- `src/pages/Settings.tsx`, `src/state/runDraft.ts` (shared setup draft state), `src/api/settings.ts`,
  `src/api/systemPrompts.ts`, `src/api/providers.ts`
- `src/pages/Settings.test.tsx`
- `docs/frontend/settings-frontend.md` — shipped Settings behaviour, the staff gate, and the
  draft-state handoff to the run configuration form

## Acceptance criteria

- [ ] With three prompts mocked, the page renders three prompt cards showing each prompt's name and
      text.
- [ ] Clicking "Use" on the second prompt stores that prompt's text in the shared draft state and
      navigates to `/`.
- [ ] For a mocked user with `is_staff: true`, the max-length input is enabled and pre-filled with the
      value from `GET /api/settings/`.
- [ ] For a mocked user with `is_staff: false`, the input is disabled (or absent) and no `PATCH` is
      issued by any interaction on the page.
- [ ] Changing the value and blurring issues exactly one `PATCH /api/settings/` with the new number;
      blurring without a change issues none.
- [ ] A mocked `400` from `PATCH` renders the response `detail` next to the field and restores the last
      known good value.
- [ ] Provider badges come from the API: a mocked catalog containing a third provider renders three
      badges.
- [ ] `npm run lint`, `npx tsc --noEmit` and `npm test` pass.

## Verification

```bash
cd "$(git rev-parse --show-toplevel)"
docker compose run --rm frontend npm run lint
docker compose run --rm frontend npx tsc --noEmit
docker compose run --rm frontend npm test -- --run
! grep -rniE 'sk-[a-z0-9]|api[_-]?key *[:=] *["'"'"']' frontend/src
```

## Evidence

_None recorded yet._
