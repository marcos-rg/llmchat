---
id: LLMC-AUTH-003
title: Login page, auth state and protected routing
area: AUTH
phase: 1
layer: frontend
status: todo
review: none
depends_on:
  - LLMC-AUTH-002
  - LLMC-CORE-002
docs:
  read:
    - docs/backend/auth-contract.md
    - docs/frontend/pages.md
    - docs/frontend/states.md
    - docs/frontend/app-shell.md
  write:
    - docs/frontend/auth-frontend.md
---

# LLMC-AUTH-003 - Login page, auth state and protected routing

## Objective

After this task the SPA has a real front door: the Login screen from `docs/frontend/pages.md` submits
to the API, a live session survives a page refresh, unauthenticated visitors are bounced to `/login`,
and the authenticated shell shows the logged-in email with a working Log out. It also closes the gap
`docs/frontend/states.md` flags — the mock has no login failure state.

## Scope

**In:**

- `src/pages/Login.tsx` per `docs/frontend/pages.md`: brand mark, pitch line, email and password
  `.input` fields, `.btn-primary.btn-block` CTA inside a `.card.blueprint`, and the admin-managed-keys
  footnote.
- Login state machine `idle -> submitting -> error -> success` from `docs/frontend/states.md`, with the
  `401` `detail` rendered inline near the password field in the warning visual language.
- `src/auth/AuthProvider.tsx`: session bootstrap via `GET /api/auth/session/` on mount, `user` (with
  `is_staff`), `login()`, `logout()`, and a loading state so protected routes do not flash the login
  screen during bootstrap.
- `RequireAuth` route wrapper: redirects to `/login` when unauthenticated, and back to the originally
  requested route after a successful login.
- CSRF wiring in `src/api/client.ts`: read the `csrftoken` cookie, send `X-CSRFToken` on unsafe
  requests, per `docs/backend/auth-contract.md`.
- Authenticated nav: brand, "New run", "Settings", the user's email, and a "Log out" `.btn-ghost` that
  calls the API, clears client state and navigates to `/login`.
- Update `docs/frontend/interfaces.md` so the `User` DTO includes `is_staff`.
- Vitest/RTL tests with msw for every criterion below.

**Out:**

- Setup, Run and Settings page content (`LLMC-RUNS-003`, `LLMC-RUNS-004`, `LLMC-CFG-002`).
- Signup, password reset, "remember me".
- The keyboard-navigation and contrast audit (`LLMC-AXS-001`) — this task follows the token/focus rules
  but is not where the audit happens.
- Any confirmation dialog on logout while a run is in flight (`docs/frontend/components.md` reserves
  `.dialog` for later).

## Outputs

- `src/pages/Login.tsx`, `src/auth/AuthProvider.tsx`, `src/auth/RequireAuth.tsx`
- `src/api/auth.ts`, CSRF handling in `src/api/client.ts`, nav in `src/layouts/AppShell.tsx`
- `src/pages/Login.test.tsx`, `src/auth/RequireAuth.test.tsx`
- Updated `docs/frontend/interfaces.md`
- `docs/frontend/auth-frontend.md` — shipped login/auth-state behaviour and the login-failure state the
  mock lacked

## Acceptance criteria

- [ ] Submitting the login form posts `{email, password}` to `/api/auth/login/` with the `X-CSRFToken`
      header and, on `201`/`200`, navigates to `/`.
- [ ] A mocked `401` renders the response's `detail` text on the page and leaves the user on `/login`;
      the password field is not cleared of focus affordance and the form stays submittable.
- [ ] The CTA is disabled and shows the submitting state while the request is in flight, so a double
      click issues only one request.
- [ ] Visiting `/settings` while the mocked session endpoint returns `401` redirects to `/login`; after
      a successful login the user lands back on `/settings`.
- [ ] With the session endpoint mocked to `200`, a reload of `/` keeps the user signed in and renders
      their email in the nav.
- [ ] Clicking "Log out" posts to `/api/auth/logout/`, and the app then renders `/login` with no email
      in the nav.
- [ ] `npm run lint`, `npx tsc --noEmit` and `npm test` all pass.

## Verification

```bash
cd "$(git rev-parse --show-toplevel)"
docker compose run --rm frontend npm run lint
docker compose run --rm frontend npx tsc --noEmit
docker compose run --rm frontend npm test -- --run
grep -q 'is_staff' docs/frontend/interfaces.md
```

## Evidence

_None recorded yet._
