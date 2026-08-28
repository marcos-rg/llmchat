---
id: LLMC-AUTH-004
title: Verify the auth slice on the running stack
area: AUTH
phase: 1
layer: verify
status: todo
review: none
depends_on:
  - LLMC-AUTH-002
  - LLMC-AUTH-003
docs:
  read:
    - docs/backend/auth-contract.md
    - docs/backend/auth-backend.md
    - docs/frontend/auth-frontend.md
  write:
    - docs/infra/verification-auth.md
---

# LLMC-AUTH-004 - Verify the auth slice on the running stack

## Objective

After this task the auth slice is proven against the real containers rather than against mocks: a
repeatable script drives a browser-equivalent cookie flow through the running `frontend` and `backend`
services, and the result — including a manual pass over the Login screen — is recorded as the slice's
verification evidence.

## Scope

**In:**

- `scripts/verify-auth.sh`: brings the stack up, creates a disposable test user, then exercises with a
  cookie jar — session bootstrap while anonymous, CSRF token acquisition, login, authenticated session
  read, cross-origin request with the SPA's `Origin` header, logout, and post-logout rejection. Exits
  non-zero on the first mismatch and cleans up the test user.
- Assertions on real cookie attributes as sent by the running server (names, `HttpOnly`, `SameSite`,
  `Path`), which unit tests do not observe.
- A manual pass over `http://localhost:5173/login` in a browser: successful login, wrong password
  error text, refresh keeps the session, log out returns to the login screen — recorded with findings
  in the living doc.
- `docs/infra/verification-auth.md`: how to run the script, what it asserts, and the recorded result.

**Out:**

- Adding an E2E browser framework or wiring this script into CI — `docs/infra/testing.md` rules both
  out; the script is a developer/verification tool run against a local stack.
- Load or concurrency testing (`LLMC-PERF-001`).
- The security audit of key handling and scoping (`LLMC-SEC-001`) — this task only proves the auth flow
  behaves as contracted.
- Anything about runs, settings or the prompt library — those endpoints do not exist yet.

## Outputs

- `scripts/verify-auth.sh`
- `docs/infra/verification-auth.md` (procedure + recorded run)

## Acceptance criteria

- [ ] `bash scripts/verify-auth.sh` exits `0` against a stack started with `make up-d`, and exits
      non-zero if the backend is stopped mid-run.
- [ ] The script asserts a `401` from `GET /api/auth/session/` before login and a `200` with the user's
      email after it.
- [ ] The script asserts that an unsafe request carrying the session cookie but no `X-CSRFToken` is
      rejected with the status in `docs/backend/auth-contract.md`.
- [ ] The script asserts the `sessionid` cookie is `HttpOnly` and carries the `SameSite` value the
      contract specifies.
- [ ] After logout, both `GET /api/auth/session/` and a second `POST /api/auth/logout/` return `401`.
- [ ] A request to `/api/auth/login/` with `Origin: http://localhost:5173` succeeds and returns the
      `Access-Control-Allow-Credentials: true` header; the same request from an unlisted origin does not
      receive an allow-origin header for that origin.
- [ ] `docs/infra/verification-auth.md` records the four manual browser checks with their outcome.

## Verification

```bash
cd "$(git rev-parse --show-toplevel)"
make up-d
timeout 120 bash -c 'until curl -fsS http://localhost:8000/api/health/ >/dev/null; do sleep 2; done'
bash scripts/verify-auth.sh
docker compose stop backend
! bash scripts/verify-auth.sh
docker compose start backend
grep -qi 'manual' docs/infra/verification-auth.md
```

## Evidence

_None recorded yet._
