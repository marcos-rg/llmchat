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
- [ ] A fetch of `VITE_API_BASE_URL + "/health/"` issued from inside the `frontend` container returns
      `200` — the configured base URL and the backend's CORS origin allowance actually agree.
- [ ] Requesting `/settings` (an unimplemented route) returns the SPA shell with `200`, not a 404 from
      the dev server — client-side routing fallback works.

## Verification

```bash
cd "$(git rev-parse --show-toplevel)"
docker compose up -d db broker backend frontend
timeout 120 bash -c 'until curl -fsS http://localhost:5173/ >/dev/null; do sleep 2; done'
curl -fsS http://localhost:5173/ | grep -q 'id="root"'
curl -fsS -o /dev/null -w '%{http_code}\n' http://localhost:5173/settings | grep -q 200
docker compose run --rm frontend npx tsc --noEmit
docker compose run --rm frontend npm run build
grep -RqiE -- '--color-accent: *#5980a6' frontend/dist/assets/*.css
for s in 1 2 3 4 6 8; do grep -Rq -- "--space-$s:" frontend/dist/assets/*.css; done
for r in sm md lg; do grep -Rq -- "--radius-$r:" frontend/dist/assets/*.css; done
docker compose exec -T frontend node -e \
  "fetch(process.env.VITE_API_BASE_URL + '/health/').then(r => { if (r.status !== 200) process.exit(1); })"
```

## Evidence

_None recorded yet._
