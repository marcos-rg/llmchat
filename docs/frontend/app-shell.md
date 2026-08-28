# App Shell

The living record for [`LLMC-CORE-002`](../tasks/tasks/LLMC-CORE-002.md): what the `frontend`
container actually is, how the token files and both shells are laid out, and where each class
from the mock now lives. The contracts it implements are
[`style-guide.md`](./style-guide.md), [`layouts.md`](./layouts.md),
[`components.md`](./components.md), [`interfaces.md`](./interfaces.md) and
[`../infra/stack-runbook.md`](../infra/stack-runbook.md).

At this stage the SPA is the **browser half of the walking skeleton**: four routes exist, one
of them renders real data. There is no auth, no run flow and no test suite yet.

## The `frontend` service

| | |
|---|---|
| Image | built from `frontend/Dockerfile` (`node:22-alpine`), tagged `llmchat-frontend:local` |
| Command | `npm run dev` → `vite --host 0.0.0.0` |
| Healthcheck | `curl -fsS http://localhost:5173/` |
| Exposed | `5173` |
| Mounts | `./frontend:/app` + an anonymous volume on `/app/node_modules` |

It is a **dev-server image, not a static build** — Vite serves modules straight off the bind
mount so an edit on the host is live without a rebuild. `npm run build` still works (and the
task's verification runs it), writing `frontend/dist/` through the same bind mount; nothing
serves that directory yet.

The anonymous `/app/node_modules` volume is the part worth understanding. `npm ci` runs in the
image, but `./frontend:/app` would mount the host directory — which has no `node_modules` — right
over it. Declaring a volume at the nested path makes Docker seed a fresh empty volume from the
image's contents at that path, so the installed packages win. It is also why
`docker compose run --rm frontend npx tsc --noEmit` works from a clean checkout: `run` creates a
new anonymous volume and Docker seeds that one too.

`frontend` deliberately has **no `depends_on`** on `backend`. The SPA renders its shell and an
error state when the API is unreachable, so coupling their startup would only make the frontend
slower to come up without making it more correct.

## `VITE_API_BASE_URL` is browser-facing, and that is the whole CORS story

`VITE_API_BASE_URL` is `http://localhost:8000/api`. Vite inlines `VITE_*` variables into the
bundle, so the value has to be the URL **the browser** will fetch — not `http://backend:8000`,
which only resolves inside the Compose network.

That makes every API call cross-origin (`:5173` → `:8000`), which is why this task added
`django-cors-headers` to the backend:

```python
CORS_ALLOWED_ORIGINS = env_list("DJANGO_CORS_ALLOWED_ORIGINS", "http://localhost:5173")
CORS_ALLOW_CREDENTIALS = True
```

`CORS_ALLOW_ALL_ORIGINS` is **not** used and must not be. The API authenticates with a session
cookie and `client.ts` sends `credentials: "include"`; browsers refuse to attach credentials to a
wildcard-origin response, so the permissive setting would break auth rather than loosen it. The
middleware sits above `CommonMiddleware` so preflight `OPTIONS` requests — which never reach a
view — still get their headers.

**The consequence to remember: `localhost` means two different things here.** From the browser it
is the host; from inside the `frontend` container it is the container. Any in-container check of
the API must use `http://backend:8000/api`, and any check of the browser's path must run from the
host. The task's original acceptance criterion conflated the two and was amended in place — see
its `## Acceptance criteria` note.

## Styles: two files, and the order matters

| File | Contents |
|---|---|
| `src/styles/tokens.css` | the Google-Fonts `@import` and the whole `:root` block — color roles, the three tonal ramps, fonts, `--space-*`, `--radius-*`, `--shadow-*` |
| `src/styles/base.css` | element defaults, `.blueprint`/`.corner`, and every component class, ending with the blueprint-frame override block |

Both are transcribed verbatim from [`mock/styles.css`](./mock/styles.css), which stays the source
of truth. `main.tsx` imports `tokens.css` first — custom properties are not hoisted, so a
component file that landed above it would resolve its `var()`s against nothing.

Inside `base.css` the final `/* blueprint frame */` block is **required to stay last**. It is what
squares the corners and empties the fills on `.card`, `.btn`, `.input`, `.tag`, `.seg` and
`.dialog`; a new component rule appended below it would silently keep the rounded/filled look and
read as a one-off styling bug rather than an ordering one.

Class → home mapping, for anything in the mock not yet used by a page: `.table`, `.dialog*`,
`.radio`, `.elev-*`, `.tag-accent-2` and `.duotone` are all present in `base.css` and unused —
they were transcribed rather than dropped so the reskin stays a single-file change. `.llm-shimmer`
is *not* here: the mock defines it inline as page-specific, and it belongs to the Run screen
(`LLMC-RUNS-004`).

## Shells

`src/layouts/AuthShell.tsx` — the unauthenticated shell. A full-viewport flex container centering
one child. No nav: there is nothing to navigate to before a session exists.

`src/layouts/AppShell.tsx` — the authenticated shell. Flex column with a `.nav` bar (hairline
bottom border, brand, "New run", "Settings", user email, "Log out") and a `<main>` with `flex: 1`.

Two decisions inside it:

- **`width` prop, `"narrow" | "wide"`.** `"narrow"` is the 760px centered column used by form and
  list pages; `"wide"` drops the max-width so the Run screen's response row can scroll
  horizontally edge to edge while its own header aligns to 1400px. This is the choice
  [`layouts.md`](./layouts.md) describes as "which container pattern", made explicit as one prop
  instead of two shell components.
- **Active-link marking is `NavLink`'s `aria-current`, not a class.** The CSS already keys off
  `.nav a[aria-current='page']`, so routing state and styling read the same attribute and cannot
  drift apart. The "New run" link carries `end` so `/` does not match `/runs/:id`.

`userEmail` is a prop defaulting to `null`, and its `<span>` renders even when empty so the nav
does not reflow once `LLMC-AUTH-003` supplies a session. "Log out" is rendered `disabled` for the
same reason — the button's place in the layout is proven now, its behavior arrives with auth.

## Routing

`src/App.tsx` declares all four paths from [`pages.md`](./pages.md) at once:

| Path | Element | Shell |
|---|---|---|
| `/login` | `Placeholder` → `LLMC-AUTH-003` | auth |
| `/` | `Landing` (real content) | app |
| `/runs/:id` | `Placeholder` → `LLMC-RUNS-004` | app |
| `/settings` | `Placeholder` → `LLMC-CFG-002` | app |

Declaring the empty routes now is deliberate: each later page task changes one `element=` and
nothing about the routing or shell seam, and the client-side fallback (a deep link to `/settings`
returning the SPA rather than a dev-server 404) is proven before anything depends on it.

**There is no route protection.** Every path renders for anyone. `LLMC-AUTH-003` wraps these
elements with the auth guard; it does not re-declare them.

## The API client

`src/api/client.ts` exports `API_BASE_URL` (trailing slashes stripped) and
`apiFetch<T>(path, init)`.

- `credentials: "include"` is unconditional, not per-call. The API is cookie-session
  authenticated on another origin, so a call that forgets it fails as an anonymous 401 — a
  confusing bug to chase for the sake of a flag nobody wants to set differently.
- Non-2xx responses become an `ApiError` carrying `status`, `code` and `message`, parsed from the
  common `{error, detail}` envelope. **Branch on `code`**, never on `message`: the code is the
  backend's stable machine-readable string, the message is human-facing prose.
- An empty body is parsed as `null` rather than fed to `JSON.parse`, because `POST
  /api/auth/logout/` returns `204`.

Note that `GET /api/health/`'s 503 does *not* use the error envelope, so a degraded backend
surfaces as `ApiError("http_error")`. That is accepted: health is a diagnostic endpoint, not part
of the app's error contract.

## Types

`src/types/api.ts` holds only the DTOs that exist server-side today — `HealthDTO`,
`AppSettingsDTO` and the `ApiErrorBody` envelope. The rest of
[`interfaces.md`](./interfaces.md) (`PromptRunDTO`, `ModelResponseDTO`, `DiffToken`, `User`,
`SystemPrompt`) is intentionally *not* pre-declared: a DTO written before its endpoint is a guess,
and a wrong guess in a shared types file is harder to notice than a missing one.

## The landing route

`src/pages/Landing.tsx` fetches `/health/` on mount and renders `max_prompt_length` in a
`.card.blueprint`. That field is the one worth showing: it is the only part of the payload that
must come out of a **database row** (the seeded `AppSettings` singleton) rather than a constant,
so a number on screen means browser → Vite → CORS → Django → Postgres is live all the way through.
`LLMC-RUNS-003` replaces this component on the same route.

## Verifying the whole thing

```bash
docker compose up -d db broker backend frontend
open http://localhost:5173/                       # a number under "max_prompt_length"
docker compose run --rm frontend npx tsc --noEmit
docker compose run --rm frontend npm run build
curl -fsS -i -H 'Origin: http://localhost:5173' http://localhost:8000/api/health/ | head -20
```
