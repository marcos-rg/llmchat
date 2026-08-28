---
id: LLMC-CORE-002
title: React app shell, design tokens and health page
area: CORE
phase: 0
layer: frontend
status: in-progress
issue: https://github.com/marcos-rg/llmchat/issues/6
review: none
depends_on:
  - LLMC-CORE-001
docs:
  read:
    - docs/frontend/style-guide.md
    - docs/frontend/layouts.md
    - docs/frontend/components.md
    - docs/infra/stack-runbook.md
  write:
    - docs/frontend/app-shell.md
---

# LLMC-CORE-002 - React app shell, design tokens and health page

## Objective

After this task the walking skeleton is complete end to end: a browser loads the React SPA from the
`frontend` container, the SPA calls `GET /api/health/` on the backend through `VITE_API_BASE_URL`
across CORS, and renders a value that came out of a PostgreSQL row. The design tokens and both app
shells from `docs/frontend/` exist, so every later page extends a shell that is already proven.

## Scope

**In:**

- `frontend/` scaffolded with Vite + React + TypeScript: `package.json`, `vite.config.ts`,
  `tsconfig.json`, `index.html`, `src/main.tsx`, `src/App.tsx`.
- `frontend/Dockerfile` and the `frontend` service added to `docker-compose.yml`
  (`vite --host 0.0.0.0`, port 5173, healthcheck) per `docs/infra/project-structure.md`.
- `src/styles/tokens.css` + `src/styles/base.css`: every token and component class from
  `docs/frontend/mock/styles.css` (color roles and ramps, type scale, `--space-*`, `--radius-*`,
  shadows) including the blueprint skin overrides and the `.corner` decoration.
- Both app shells from `docs/frontend/layouts.md`: the unauthenticated centering shell and the
  authenticated `.nav` + `<main>` shell, plus routing (`react-router`) with the four route paths
  declared (`/login`, `/`, `/runs/:id`, `/settings`) — only the landing route renders real content here.
- `src/api/client.ts`: fetch wrapper reading `import.meta.env.VITE_API_BASE_URL`, sending
  `credentials: "include"`, parsing the common `{error, detail}` envelope into a typed error.
- `src/types/` seeded with the DTOs from `docs/frontend/interfaces.md` that already exist server-side.
- Landing route renders the health payload's `max_prompt_length` inside the authenticated shell.

**Out:**

- Login, Setup, Run and Settings page content — those routes render a placeholder until their own
  tasks (`LLMC-AUTH-003`, `LLMC-RUNS-003`, `LLMC-RUNS-004`, `LLMC-CFG-002`).
- Any auth state, route protection or CSRF handling (`LLMC-AUTH-003`).
- Vitest/RTL/msw setup and component tests (`LLMC-CORE-003`) — this task is verified by build,
  typecheck and a live fetch from the container.
- Responsive breakpoints below ~900px (documented as an open gap in `docs/frontend/layouts.md`).
- The accessibility pass and `prefers-reduced-motion` handling (`LLMC-AXS-001`).

## Outputs

- `frontend/` project as above, `frontend` service in `docker-compose.yml`
- `src/styles/tokens.css`, `src/styles/base.css`, `src/layouts/AppShell.tsx`, `src/layouts/AuthShell.tsx`
- `src/api/client.ts`, `src/types/api.ts`, `src/pages/Landing.tsx`
- `docs/frontend/app-shell.md` — the shipped shell/routing/token structure and where each mock class
  now lives.

## Acceptance criteria

- [ ] `docker compose up -d frontend` reaches healthy and `curl http://localhost:5173/` returns `200`
      with the SPA root element in the HTML.
- [ ] `npx tsc --noEmit` reports no type errors and `npm run build` exits `0`.
- [ ] The built CSS bundle defines the design tokens: `--color-accent: #5980a6`, all six `--space-*`
      steps (1,2,3,4,6,8) and all three `--radius-*` values.
- [ ] The configured base URL and the backend's CORS origin allowance agree: a request to
      `$VITE_API_BASE_URL/health/` carrying `Origin: http://localhost:5173` returns `200` with
      `access-control-allow-origin: http://localhost:5173` and `access-control-allow-credentials:
      true`, and the `frontend` container can reach the API over the Compose network and read a
      non-null `max_prompt_length`.
      (Amended during LLMC-CORE-002: the original wording issued this fetch against
      `VITE_API_BASE_URL` *from inside* the `frontend` container. That can never pass — the value is
      the browser-facing `http://localhost:8000/api`, and `localhost` inside the container is the
      container itself, not the host. The check is split into the two things the criterion was
      actually after: a real browser-shaped preflight-equivalent request from the host, which is
      strictly stronger evidence about CORS, plus in-network reachability from the container.)
- [ ] Requesting `/settings` (an unimplemented route) returns the SPA shell with `200`, not a 404 from
      the dev server — client-side routing fallback works.

## Verification

```bash
cd "$(git rev-parse --show-toplevel)"
docker compose up -d db broker backend frontend
# No `timeout(1)` on macOS without coreutils; poll with a bounded loop instead.
for _ in $(seq 1 60); do curl -fsS http://localhost:5173/ >/dev/null && break; sleep 2; done
curl -fsS http://localhost:5173/ | grep -q 'id="root"'
curl -fsS -o /dev/null -w '%{http_code}\n' http://localhost:5173/settings | grep -q 200
docker compose run --rm frontend npx tsc --noEmit
docker compose run --rm frontend npm run build
grep -RqiE -- '--color-accent: *#5980a6' frontend/dist/assets/*.css
for s in 1 2 3 4 6 8; do grep -Rq -- "--space-$s:" frontend/dist/assets/*.css; done
for r in sm md lg; do grep -Rq -- "--radius-$r:" frontend/dist/assets/*.css; done
BASE="$(docker compose exec -T frontend printenv VITE_API_BASE_URL | tr -d '\r\n')"
HDR="$(mktemp)"
curl -fsS -H 'Origin: http://localhost:5173' -D "$HDR" -o /dev/null "$BASE/health/"
grep -qi '^access-control-allow-origin: http://localhost:5173' "$HDR"
grep -qi '^access-control-allow-credentials: true' "$HDR"
docker compose exec -T frontend node -e \
  "fetch('http://backend:8000/api/health/').then(r => r.json()).then(b => { if (b.max_prompt_length == null) process.exit(1); })"
```

## Evidence

- `2026-08-28 09:01` python3 scripts/tasks.py verify LLMC-CORE-002 --run -> exit 0 (full block: compose up, SPA reachable, tsc, build, token greps, CORS headers, in-network health fetch)

- `2026-08-28 09:01` docker compose ps -> db/broker/backend/frontend all healthy; curl http://localhost:5173/ -> 200 and HTML contains id="root"

- `2026-08-28 09:01` curl -o /dev/null -w '%{http_code}' http://localhost:5173/settings -> 200 (SPA fallback, not a dev-server 404)

- `2026-08-28 09:01` docker compose run --rm frontend npx tsc --noEmit -> exit 0, no diagnostics

- `2026-08-28 09:01` docker compose run --rm frontend npm run build -> exit 0; dist/assets/index-10jP0Ntq.css 9.12 kB, index-Du543s8U.js 236.52 kB

- `2026-08-28 09:01` grep on frontend/dist/assets/*.css -> '--color-accent: #5980a6' present; --space-{1,2,3,4,6,8} and --radius-{sm,md,lg} all present

- `2026-08-28 09:01` curl -H 'Origin: http://localhost:5173' $VITE_API_BASE_URL/health/ (BASE=http://localhost:8000/api) -> 200 with access-control-allow-origin: http://localhost:5173 and access-control-allow-credentials: true

- `2026-08-28 09:01` docker compose exec -T frontend node fetch http://backend:8000/api/health/ -> {"status":"ok","db":"ok","broker":"ok","max_prompt_length":600}

- `2026-08-28 09:01` regression check after adding corsheaders: worker healthy; docker compose run --rm backend python manage.py check_queue -> queue ok: worker returned pong:edb3ddf3...
