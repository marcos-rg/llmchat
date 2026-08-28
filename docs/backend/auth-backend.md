# Auth Backend (shipped)

What `LLMC-AUTH-002` actually built, for anyone who needs to run, extend, or debug it. The
binding wire-format decisions live in [`auth-contract.md`](./auth-contract.md); this doc is the
implementation record — where things live, what settings matter, and how to create a user.
The model shape comes from [`db-schema.md`](./db-schema.md).

## Where things live

- `backend/accounts/` — the app. `models.py` (`User`), `serializers.py` (`UserSerializer`, the
  shared `{id, email, is_staff}` DTO), `views.py` (`LoginView`, `LogoutView`, `SessionView`),
  `urls.py`, `admin.py`, `authentication.py` (`CsrfSessionAuthentication`), `migrations/`.
- `backend/core/exceptions.py` — the DRF `EXCEPTION_HANDLER` that renders every error (except
  CSRF failures) as `{"error": "<code>", "detail": "<message>"}`.
- `backend/config/settings/base.py` — `AUTH_USER_MODEL`, the CSRF/session cookie settings, and
  the `REST_FRAMEWORK` block (`DEFAULT_AUTHENTICATION_CLASSES`, `DEFAULT_PERMISSION_CLASSES`,
  `EXCEPTION_HANDLER`).
- `backend/config/urls.py` — mounts `accounts.urls` at `/api/auth/`.

## Why CSRF needed a custom authenticator

DRF's stock `SessionAuthentication.enforce_csrf()` only runs once a session user has already
been found — an anonymous unsafe request (login itself, or a login-CSRF attack) sails through
unchecked. `accounts/authentication.py:CsrfSessionAuthentication` runs `enforce_csrf()`
unconditionally, before it even knows whether a session user exists, so `POST
/api/auth/login/` is CSRF-protected exactly like every other unsafe endpoint per
`auth-contract.md#csrf`. A CSRF failure raises `CsrfFailed`, a `PermissionDenied` subclass
that `core.exceptions.exception_handler` special-cases to keep Django's own
`{"detail": "CSRF Failed: ..."}` body (no `error` key) — the one place the app doesn't use the
common envelope, because the contract pins it to Django's default shape.

## Session probe never 401s

`GET /api/auth/session/` always returns `200` — `{"user": {...}}` when a session is live,
`{"user": null}` when it isn't. This was a discrepancy between this task's original
acceptance criteria/verification block (which asserted `401` for "no session") and
`auth-contract.md#unauthenticated-response-shape`, which is explicit that this endpoint
"never returns 401" because the SPA calls it unconditionally on boot before it knows whether
a session exists — a `401` there would make "never logged in" look like an error. The
contract is the binding decision (`auth-contract.md`'s own header: "implementation
(`LLMC-AUTH-002`) must match it exactly"), so the task file's acceptance criteria and
verification block were corrected to match the shipped, contract-compliant behavior rather
than the other way around. Every other authenticated endpoint (`logout`, and everything that
lands in later tasks) keeps the normal `401 {"error": "not_authenticated", ...}` behavior.

## Settings that matter

| Setting | Value | Why |
|---|---|---|
| `AUTH_USER_MODEL` | `accounts.User` | Must be set before the first migration; email-only login, no username field. |
| `CSRF_TRUSTED_ORIGINS` | `http://localhost:5173` (env-overridable) | The SPA's origin; required for cross-origin CSRF-protected POSTs. |
| `CSRF_COOKIE_HTTPONLY` | `False` | The SPA must read `csrftoken` from JS to echo it in `X-CSRFToken`. |
| `SESSION_COOKIE_HTTPONLY` | `True` | `sessionid` is never JS-readable. |
| `CSRF_COOKIE_SAMESITE` / `SESSION_COOKIE_SAMESITE` | `Lax` | Sufficient because `5173` and `8000` are both `localhost` in dev; see `auth-contract.md` for the HTTPS-deployment note on what changes off `localhost`. |
| `SESSION_COOKIE_AGE` | `1209600` (2 weeks, Django's default) | Spelled out explicitly as a deliberate choice, not left implicit. |
| `REST_FRAMEWORK.DEFAULT_AUTHENTICATION_CLASSES` | `["accounts.authentication.CsrfSessionAuthentication"]` | See above. |
| `REST_FRAMEWORK.DEFAULT_PERMISSION_CLASSES` | `["rest_framework.permissions.IsAuthenticated"]` | Every future endpoint is auth-gated unless it opts out with `AllowAny`. |
| `REST_FRAMEWORK.EXCEPTION_HANDLER` | `"core.exceptions.exception_handler"` | The `{error, detail}` envelope. |

`LoginView` and `SessionView` are the only two views with `permission_classes = [AllowAny]`,
per `auth-contract.md#permissions`.

## Creating a user

No signup endpoint exists (by design — see `auth-contract.md`'s user-model section). Two ways:

```bash
# First admin/staff account
docker compose run --rm backend python manage.py createsuperuser
# prompts for email + password only; there is no username prompt

# Any subsequent user, via the Django admin
# visit http://localhost:8000/admin/ as a staff user and use the Users section
```

Programmatically (e.g. for a fixture or a one-off dev user):

```python
from django.contrib.auth import get_user_model
get_user_model().objects.create_user(email="dev@example.com", password="devpass123")
```

## Logout and future work

`POST /api/auth/logout/` today only destroys the Django session. The
`PromptRun`/`ModelResponse` purge described in `auth-contract.md#logout-and-session-scoped-data-purge`
is explicitly out of scope here — those models don't exist until `LLMC-RUNS-001`, which will add
a `DELETE ... WHERE session_key = request.session.session_key` step to `LogoutView.post`
before it calls `django_logout`, not a new endpoint.

## Tests

`backend/accounts/tests/test_auth.py` covers, per the task's acceptance criteria:

- Login: success (200 + user body + `sessionid` cookie), wrong password and unknown email
  (identical `401 invalid_credentials`), missing password/email (`400 invalid_request`).
- Session probe: authenticated (`200` + user), anonymous (`200` + `{"user": null}`, never
  `401`), and that the `csrftoken` cookie is set in both states.
- Logout: success (`204`, session destroyed, a later probe returns `{"user": null}`),
  unauthenticated (`401 not_authenticated`).
- CSRF: an unsafe request with a session cookie but no `X-CSRFToken` header is rejected `403`
  with a body that has `detail` but no `error` key; login itself is also CSRF-protected despite
  being `AllowAny`.
- Permissions: `/api/health/` stays public; `/api/auth/logout/` (representative of the default)
  requires authentication.

Run with `docker compose run --rm backend pytest accounts -q`.
