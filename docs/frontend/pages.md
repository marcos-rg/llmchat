# Pages

Source of truth: the four `<sc-if>`-gated screens in
[`mock/LLMChat Mockups.dc.html`](./mock/LLMChat%20Mockups.dc.html) (`screen` state: `login`, `setup`,
`run`, `settings`). Each page below lists its purpose, layout, fields/elements, and the backend
endpoint(s) from [`docs/backend/api-endpoints.md`](../backend/api-endpoints.md) it's wired to.

## Login

**Route intent:** `/login`. **Layout:** unauthenticated shell, centered card (see
[`layouts.md`](./layouts.md)).

- Brand mark (small bordered icon square + "LLMChat" heading) and one-line pitch text.
- Fields: Email (`.input[type=email]`), Password (`.input[type=password]`).
- Primary CTA: "Log in" (`.btn-primary.btn-block`).
- Footnote: "Provider API keys are configured by your admin — you never enter or see them here."
  (reflects the spec's admin-managed-keys assumption; keep this copy or equivalent wherever key
  handling could otherwise be assumed to be per-user).
- **API:** `POST /api/auth/login/`. On `401`, surface `detail` inline (not modeled in the mock, which
  has no failure state for login — add one when wiring real auth).

## Setup ("New run")

**Route intent:** `/` or `/new`. **Layout:** authenticated shell, centered narrow column.

- Eyebrow tag "New run", `h1` "Compare model consistency", subtitle.
- Provider/Model row (grid): Provider as a 2-option `.seg` (OpenAI/Anthropic); Model as a `.input`
  `<select>` whose options repopulate from the chosen provider's model list. **API:** both driven by
  `GET /api/providers/`.
- System prompt: `.field` with a "Manage library →" link to Settings, and a 2-row textarea seeded from
  the last-used/default system prompt. **API:** options sourced from `GET /api/system-prompts/`.
- Prompt: `.field` with a live `N / max` character counter (color flips to the warning accent past the
  limit) and a 5-row textarea. **API:** `max` comes from `GET /api/settings/` (`max_prompt_length`).
- Conditional warning block (blueprint-bordered, accent-colored icon + text) shown only when the prompt
  exceeds `maxLen`: "Prompt exceeds {maxLen} characters. Shorten it before running…".
- Number of runs: a 4-option `.seg` (2/3/4/5), maps to `run_count`.
- Submit: "Run prompt {runCount} times" (`.btn-primary.btn-block`), `disabled` while `promptTooLong`.
- **API:** submit calls `POST /api/runs/`; on `201`, navigate to Run with the returned `id`.

## Run (results comparison)

**Route intent:** `/runs/:id`. **Layout:** authenticated shell, full-width with horizontal scroll (see
[`layouts.md`](./layouts.md)).

- Header row: left side shows a `tag-accent` "{provider} · {model}" badge and the prompt text (muted
  "Prompt —" label prefix); right side holds two demo-only `.seg` controls in the mock (**"Demo:
  phase"** and **"Diff highlighting"**) — in the real app, **phase is not user-selectable**, it's
  driven by polling `GET /api/runs/{run_id}/`; only the **diff on/off** toggle is real UI.
- Body: a horizontally-scrolling row of response cards, one per `run_count`, each rendering per its
  current status — see [`states.md`](./states.md) for the full per-status layout (queued/running/
  retrying/failed/complete) and the diff-token rendering rule.
- The baseline response (`index === 1`) is visually pinned first and marked with an outline "Baseline"
  tag; every other response's diff is computed against it.
- **API:** poll `GET /api/runs/{run_id}/` on an interval until every response reaches a terminal status
  (`complete` or `failed`); `POST /api/responses/{response_id}/retry/` for the retry button on a failed
  card.

## Settings

**Route intent:** `/settings`. **Layout:** authenticated shell, centered narrow column.

- Eyebrow tag "Settings", `h1` "System prompt library & limits".
- **Saved system prompts** (`h3` + list): one `.card.blueprint` row per saved prompt (name + text +
  "Use" button that copies the prompt into Setup's system-prompt field and navigates there). **API:**
  `GET /api/system-prompts/`.
- **Prompt limits** (`h3`): a single numeric `.input` for "Maximum prompt length (characters)"
  (`min=100 max=4000 step=50`, matching the `[100, 4000]` server-side validation range). **API:**
  `GET`/`PATCH /api/settings/` — `PATCH` is staff/admin-only server-side, so the real page must hide or
  disable this control for non-staff users (the mock has no role check since it has no real auth).
- **Provider connections** (`h3`): static-looking `tag-accent` badges ("OpenAI · connected (admin
  key)", "Anthropic · connected (admin key)") plus explanatory copy. Read-only display; there is no
  corresponding write endpoint since keys are env-configured, not user-managed. Source list from
  `GET /api/providers/` rather than hardcoding the two names.
