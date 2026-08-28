# Response & Run States

Source of truth: `ModelResponse.Status` / `PromptRun.status` in
[`docs/backend/db-schema.md`](../backend/db-schema.md), rendered by the `showQueued`/`showRunning`/
`showFailed`/`showRetrying`/`showComplete` branches in
[`mock/LLMChat Mockups.dc.html`](./mock/LLMChat%20Mockups.dc.html).

## Per-response status machine

```
queued → running → complete
                 → failed → (user clicks Retry) → retrying → complete
                                                            → failed (repeat)
```

| Status | Tag | Icon | Body content |
|---|---|---|---|
| `queued` | `.tag-neutral` "Queued" | clock (static) | 3 shimmer bars (92% / 78% / 85% width) |
| `running` | `.tag-outline` "Running" | spinner (`.llm-spin`) | 2 shimmer bars (96% / 64% width) |
| `retrying` | `.tag-outline` "Retrying" | spinner (`.llm-spin`) | 2 shimmer bars (90% / 70% width) — visually identical treatment to `running`, distinguished only by the tag label |
| `failed` | `.tag-neutral` "Failed" | warning triangle (static) | `error_message` text + a "Retry" button (`.btn-secondary`) |
| `complete` | `.tag-accent` "Complete" | check (static) | Response text — baseline renders `response_text` plain; non-baseline renders `diff_tokens`, each wrapped in `<mark>` when `hl: true` else plain `<span>` |

Only one of these five blocks is shown at a time — implement as a single `switch`/lookup on `status`,
not independent booleans (the mock's `showX` flags are a template-engine limitation, not a pattern to
copy).

## Diff toggle interaction

`diffOn` only affects **complete, non-baseline** cards: when off, render every token as plain text
(`hl` ignored) instead of hiding the response — the raw text must stay fully readable, matching the
"toggle diff highlighting on/off to view raw responses" functional requirement. The baseline card is
never diffed against itself, so the toggle has no visual effect on it.

## Run-level status & polling contract

`PromptRun.status` is a derived property (see `db-schema.md`), not a stored field:

- `queued` — every response is still `queued`
- `running` — at least one response is `running` or `retrying`
- `complete` — every response has reached a terminal status (`complete` or `failed`)

The Run page should poll `GET /api/runs/{run_id}/` on an interval and stop polling once the top-level
`status` is `complete` — a `failed` response does not block the run from being considered finished;
the user resolves it manually via the per-card Retry button, which re-queues just that one response
(`POST /api/responses/{response_id}/retry/`, `202 Accepted`) and should resume/extend polling since
that response goes back to `queued`.

## Login / auth states

Not modeled in the mock (no failure state exists for the Login screen). When wiring real auth, add at
least: idle → submitting → error (`401` → inline message near the password field, using the same
warning visual language as the prompt-too-long block in [`components.md`](./components.md)) → success
(navigate to Setup).
