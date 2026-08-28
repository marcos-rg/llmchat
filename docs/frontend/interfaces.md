# Interfaces

Source of truth: [`docs/backend/api-endpoints.md`](../backend/api-endpoints.md) and
[`docs/backend/db-schema.md`](../backend/db-schema.md) for the wire shapes; the mock's
`Component.state` / `renderVals()` in
[`mock/LLMChat Mockups.dc.html`](./mock/LLMChat%20Mockups.dc.html) for which view-model fields the UI
actually needs. These are TypeScript-flavored for readability; adjust to whatever the real frontend
stack uses, but keep field names aligned to the API so payloads can be passed through with minimal
mapping.

## API DTOs (mirror backend responses exactly)

```ts
interface User {
  id: number;
  email: string;
}

interface ProviderCatalogEntry {
  name: string;        // e.g. "OpenAI"
  models: string[];    // e.g. ["gpt-4o", "gpt-4o-mini", "gpt-4.1"]
}

interface SystemPrompt {
  id: number;
  name: string;
  text: string;
}

interface AppSettings {
  max_prompt_length: number;
}

type ResponseStatus = "queued" | "running" | "retrying" | "complete" | "failed";

interface ModelResponseDTO {
  id: number;
  index: number;
  is_baseline: boolean;
  status: ResponseStatus;
  response_text: string | null;
  diff_tokens: DiffToken[] | null;   // present only once complete and non-baseline
  error_message: string | null;
  retry_count: number;
}

type RunStatus = "queued" | "running" | "complete";

interface PromptRunDTO {
  id: number;
  provider: string;
  model: string;
  prompt: string;
  run_count: number;
  status?: RunStatus;                // present on GET /api/runs/{id}/, absent on the 201 create response
  responses: ModelResponseDTO[];
}

interface RunCreateRequest {
  provider: string;
  model: string;
  system_prompt: string;
  prompt: string;
  run_count: number;                 // 2–5
}
```

`DiffToken` shape is not specified in `api-endpoints.md` (the example response shows `diff_tokens:
null` only) — the mock's local token shape is the working assumption until the backend confirms the
real one:

```ts
interface DiffToken {
  text: string;   // includes trailing whitespace, e.g. "reliable, "
  hl: boolean;    // true = render as a highlighted diff span
}
```

## Frontend-only view models

These exist only in the UI layer — they're derived from the DTOs above plus local state, not sent to
or received from the API as-is.

```ts
type Screen = "login" | "setup" | "run" | "settings";

interface AppState {
  screen: Screen;
  user: User | null;

  // Setup form
  provider: string;
  model: string;
  systemPrompt: string;
  prompt: string;
  runCount: number;               // 2–5

  // App settings (from GET /api/settings/)
  maxPromptLength: number;

  // Active run being viewed
  activeRunId: number | null;

  // Run screen UI-only toggle — NOT part of any API payload
  diffOn: boolean;
}

// One entry per card rendered on the Run screen; computed from ModelResponseDTO + diffOn + baseline lookup
interface ResponseViewModel {
  id: number;
  label: string;              // "Run {index}"
  baseline: boolean;
  status: ResponseStatus;
  text: string | null;        // baseline's own response_text
  tokens: DiffToken[];        // non-baseline: diff_tokens if diffOn, else response_text re-wrapped as one plain token
  failReason: string | null;  // error_message, shown only when status === "failed"
  onRetry: () => void;        // bound to POST /api/responses/{id}/retry/
}
```

`promptTooLong` (`prompt.length > maxPromptLength`) and the counter color are pure derivations of
`AppState` — don't store them as separate state fields, compute them at render time (as the mock does
in `renderVals()`).

## Component prop boundaries

Keep these as the seams between pages and shared components, so any of the four pages can be reworked
independently (per the modular/incremental approach):

- `<SegmentedControl options, value, onChange, name, ariaLabelledBy>` — backs Provider, Run count, and
  (if kept) the diff toggle.
- `<ResponseCard viewModel: ResponseViewModel>` — owns rendering all five status layouts internally
  (see [`states.md`](./states.md)); pages never branch on status themselves.
- `<PromptField value, onChange, max, rows>` — owns its own counter/warning rendering.
