---
id: LLMC-AUTH-002
title: Email/password auth endpoints and session scoping
area: AUTH
phase: 1
layer: backend
status: done
issue: https://github.com/marcos-rg/llmchat/issues/12
review: none
depends_on:
  - LLMC-AUTH-001
  - LLMC-CORE-003
docs:
  read:
    - docs/backend/auth-contract.md
    - docs/backend/db-schema.md
  write:
    - docs/backend/auth-backend.md
---

# LLMC-AUTH-002 - Email/password auth endpoints and session scoping

## Objective

After this task the API has real users and real sessions: a user can log in with email and password,
the SPA can ask whether a session is still live, logging out destroys it, and every other `/api/`
endpoint refuses unauthenticated callers. This is the gate every later feature sits behind.

## Scope

**In:**

- `backend/accounts/` app: the custom `User` model from `docs/backend/db-schema.md`, `AUTH_USER_MODEL`
  wiring, initial migration, and admin registration.
- `POST /api/auth/login/`, `POST /api/auth/logout/`, `GET /api/auth/session/` exactly as specified in
  `docs/backend/auth-contract.md`, including the `{error, detail}` envelope and `is_staff` in the user
  object.
- DRF configuration: `SessionAuthentication`, `DEFAULT_PERMISSION_CLASSES = [IsAuthenticated]`, and the
  documented exempt endpoints.
- CSRF and CORS settings per the contract (`CSRF_TRUSTED_ORIGINS`, `CORS_ALLOW_CREDENTIALS`, cookie
  attributes), and the `ensure_csrf_cookie` on the session endpoint.
- A DRF exception handler that renders every error as the common `{error, detail}` shape.
- `accounts/tests/` covering the success, failure, validation, CSRF and permission paths below.

**Out:**

- Purging `PromptRun` rows at logout — the models do not exist yet; `LLMC-RUNS-001` extends the logout
  view and adds that test.
- Signup, password reset/change, email verification, "remember me", rate limiting.
- Any frontend work (`LLMC-AUTH-003`).
- The system-prompt, settings and providers endpoints (`LLMC-CFG-001`), which will inherit the default
  `IsAuthenticated` permission set here.

## Outputs

- `backend/accounts/{models,views,urls,serializers,admin}.py` + `0001_initial` migration
- `backend/core/exceptions.py` (error-envelope handler)
- Endpoints: `POST /api/auth/login/`, `POST /api/auth/logout/`, `GET /api/auth/session/`
- `backend/accounts/tests/test_auth.py`
- `docs/backend/auth-backend.md` — the shipped auth behaviour, settings that matter, and how to create
  a user

## Acceptance criteria

- [ ] `POST /api/auth/login/` with valid credentials returns `200`, a body containing `id`, `email` and
      `is_staff`, and sets a `sessionid` cookie.
- [ ] `POST /api/auth/login/` with a wrong password returns `401` and
      `{"error": "invalid_credentials", ...}`; the body never reveals whether the email exists.
- [ ] `POST /api/auth/login/` with a missing `password` field returns `400`.
- [ ] `GET /api/auth/session/` returns `200` with the user object when a session cookie is present, and
      `200` with `{"user": null}` when it is not (never `401` — see
      `docs/backend/auth-contract.md#unauthenticated-response-shape`); it sets the `csrftoken` cookie in
      both cases.
- [ ] `POST /api/auth/logout/` returns `204` with a session, `401` without, and a subsequent
      `GET /api/auth/session/` with the old cookie returns `200` with `{"user": null}`.
- [ ] An unsafe request with a session cookie but no `X-CSRFToken` header is rejected with the status
      the contract specifies.
- [ ] `GET /api/health/` still returns `200` without authentication, while every other `/api/` route
      requires it.
- [ ] `manage.py createsuperuser` works with an email and no username, and the resulting user can log in.
- [ ] `pytest accounts` passes and `manage.py migrate --check` exits `0`.

## Verification

```bash
cd "$(git rev-parse --show-toplevel)"
docker compose up -d db broker backend
docker compose run --rm backend pytest accounts -q
docker compose run --rm backend python manage.py migrate --check
docker compose run --rm backend python manage.py shell -c \
  "from django.contrib.auth import get_user_model as G; U=G(); U.objects.filter(email='dev@example.com').delete(); U.objects.create_user(email='dev@example.com', password='devpass123')"
J=$(mktemp)
curl -fsS -c "$J" http://localhost:8000/api/auth/session/ -o /dev/null -w '%{http_code}\n' | grep -q 200
grep -q csrftoken "$J"
TOKEN=$(awk '/csrftoken/{print $7}' "$J")
curl -fsS -b "$J" -c "$J" -X POST http://localhost:8000/api/auth/login/ \
  -H 'Content-Type: application/json' -H "X-CSRFToken: $TOKEN" \
  -d '{"email":"dev@example.com","password":"devpass123"}' | grep -q '"is_staff"'
grep -q sessionid "$J"
curl -fsS -b "$J" http://localhost:8000/api/auth/session/ | grep -q 'dev@example.com'
# Django rotates the CSRF token on login (auth-contract.md#csrf) -- re-read it
# from the jar, the same way the SPA must re-read document.cookie post-login.
TOKEN=$(awk '/csrftoken/{print $7}' "$J")
curl -s -o /dev/null -w '%{http_code}\n' -b "$J" -X POST http://localhost:8000/api/auth/login/ \
  -H 'Content-Type: application/json' -H "X-CSRFToken: $TOKEN" \
  -d '{"email":"dev@example.com","password":"wrong"}' | grep -q 401
curl -s -o /dev/null -w '%{http_code}\n' -b "$J" -X POST http://localhost:8000/api/auth/logout/ \
  -H "X-CSRFToken: $TOKEN" | grep -q 204
curl -s -b "$J" http://localhost:8000/api/auth/session/ | grep -q '"user": *null'
curl -fsS -o /dev/null -w '%{http_code}\n' http://localhost:8000/api/health/ | grep -q 200
```

## Evidence

- `2026-08-28 10:09` docker compose run --rm backend pytest accounts -q -> 16 passed

- `2026-08-28 10:09` docker compose run --rm backend python manage.py migrate --check -> exit 0, no migrations to apply

- `2026-08-28 10:09` bash scripts/ci-test.sh --backend -> 18 passed, ruff clean, 95% coverage

- `2026-08-28 10:09` python3 scripts/tasks.py verify LLMC-AUTH-002 --run -> full curl-based verification script (login/logout/session/csrf/health) passed, exit 0

- `2026-08-28 10:09` manage.py createsuperuser --noinput --email admin@example.com -> superuser created, is_staff/is_superuser True, password verified
