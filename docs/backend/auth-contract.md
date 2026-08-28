# Auth Contract

This document fixes the part [`api-endpoints.md`](./api-endpoints.md) leaves open: how the React SPA
on `localhost:5173` authenticates against the Django API on `localhost:8000` using session cookies,
across two different origins/ports. It is the binding decision — implementation
(`LLMC-AUTH-002`) must match it exactly.

Read alongside [`db-schema.md`](./db-schema.md) (the `User` model) and
[`sequence-diagrams.md`](./sequence-diagrams.md) (diagrams 1–2, login/logout).

## User model and account creation

Per `db-schema.md`, `User` extends `AbstractUser` with the inherited login-name field set to `None`,
a unique `email`, and `USERNAME_FIELD = "email"` — `email` is the sole login identifier, and no other
identifier field exists on the model. There is **no self-service signup endpoint** anywhere in the
spec or the UI mockups — the login screen has no "create account" link. Consequently:

- Accounts are provisioned out-of-band by an admin, via `python manage.py createsuperuser` (for the
  first admin/staff account) or the Django admin site (`/admin/`) for subsequent users.
- `is_staff` is set the same way, by an admin, at account-creation time or later via the Django
  admin. There is no API endpoint that changes it.
- The API surface in this contract therefore has exactly three endpoints: login, logout, and session
  probe. No register/forgot-password/change-password endpoints exist.

## Endpoints

### `POST /api/auth/login/`

Authenticates with email + password and starts a session. Matches diagram 1 in
`sequence-diagrams.md`.

- **Auth required:** No
- **Request**
  ```json
  { "email": "you@company.com", "password": "••••••••" }
  ```
- **Success:** `200 OK` — sets the `sessionid` cookie (see [Cookies](#cookies-local-http-development))
  and, because this is the first response of the session, also sets the `csrftoken` cookie (Django's
  `CsrfViewMiddleware` sets it on any response once `get_token()` has been called; the login view
  calls it explicitly so the very next request already has a token to send).
  ```json
  { "user": { "id": 1, "email": "you@company.com", "is_staff": false } }
  ```
- **Error:**
  - `400 Bad Request` — missing/malformed `email` or `password`
    ```json
    { "error": "invalid_request", "detail": "Email and password are required." }
    ```
  - `401 Unauthorized` — credentials don't match an active user
    ```json
    { "error": "invalid_credentials", "detail": "Email or password is incorrect." }
    ```
  - `403 Forbidden` — CSRF header missing/invalid (see [CSRF](#csrf)); DRF/Django's standard CSRF
    failure response, `{ "detail": "CSRF Failed: ..." }`

### `POST /api/auth/logout/`

Ends the session. Matches diagram 2. Purging the session's `PromptRun`/`ModelResponse` rows
(`db-schema.md`'s ephemeral-data cascade) is this endpoint's responsibility once those models exist;
today there is nothing to purge because `LLMC-RUNS-001` (which defines `PromptRun`/`ModelResponse`)
has not landed yet. This contract fixes the interface now so `LLMC-RUNS-001` only has to add the
`DELETE ... WHERE session_key = request.session.session_key` step inside the existing view, not
design a new endpoint.

- **Auth required:** Yes
- **Request:** none
- **Success:** `204 No Content` — session destroyed, `sessionid` cookie cleared
- **Error:**
  - `401 Unauthorized` — no active session
    ```json
    { "error": "not_authenticated", "detail": "Authentication credentials were not provided." }
    ```
  - `403 Forbidden` — CSRF header missing/invalid (logout is an unsafe method; see [CSRF](#csrf))

### `GET /api/auth/session/`

New endpoint, not in the original `api-endpoints.md`. Lets the SPA learn whether it already has a
valid session after a hard refresh or a fresh tab open — the browser sends the `sessionid` cookie
automatically, but JavaScript has no other way to read it (it's `HttpOnly`). This is also the
endpoint that issues the CSRF cookie for anonymous visitors (see [CSRF](#csrf)), so the SPA calls it
once on boot before rendering the login screen, unconditionally.

- **Auth required:** No (the endpoint itself is public; its response shape differs by auth state)
- **Request:** none
- **Success:**
  - `200 OK` — an active session exists
    ```json
    { "user": { "id": 1, "email": "you@company.com", "is_staff": false } }
    ```
  - `200 OK` — no active session (**not** `401`; this is a normal, expected boot-time state, not an
    auth failure — see [Unauthenticated response shape](#unauthenticated-response-shape))
    ```json
    { "user": null }
    ```
- **Error:** none beyond the standard `5xx` server-error case; this endpoint never returns `401`.

## Unauthenticated response shape

Two distinct situations must not be confused:

1. **Boot-time session probe** (`GET /api/auth/session/`) — "does a session exist" is a yes/no
   question the SPA asks before it knows anything. The answer is always `200 OK` with
   `{ "user": null }` for "no", never `401`. A `401` here would make the SPA's boot sequence treat
   "never logged in" as an error to display, which it isn't.
2. **Every other authenticated endpoint** (`logout`, `providers`, `system-prompts`, `settings`,
   `runs`, `responses/*/retry`) — per `api-endpoints.md`, these require `IsAuthenticated`. Missing or
   expired session on these returns `401 Unauthorized`:
   ```json
   { "error": "not_authenticated", "detail": "Authentication credentials were not provided." }
   ```
   The SPA's shared fetch wrapper treats any `401` from these endpoints as "session expired," clears
   local auth state, and redirects to the Login screen (see
   [`docs/frontend/states.md`](../frontend/states.md#login--auth-states) for the login-screen state
   machine this feeds).

## User DTO

Both `POST /api/auth/login/` and `GET /api/auth/session/` return the same shape:

```json
{ "id": 1, "email": "you@company.com", "is_staff": false }
```

`is_staff` is included on both — not just login — because a refreshed page re-derives its auth state
from `GET /api/auth/session/` alone, and the Settings page
([`docs/frontend/pages.md`](../frontend/pages.md)) needs `is_staff` to decide whether to render the
"Prompt limits" `PATCH /api/settings/` control, or show it disabled, without a second round trip.

`request.session.session_key` (the server-side value `db-schema.md`'s `PromptRun.session_key` scopes
on) is **never** part of this DTO or any other client-visible payload. It's a server-side scoping key
only — the client identifies "my session" implicitly via the `sessionid` cookie, never by value.

## CSRF

Django's session auth is cookie-based, and the SPA is cross-origin from the API in local dev
(`localhost:5173` vs `localhost:8000`), so CSRF must be handled explicitly — a browser will send the
`sessionid` cookie on any request to `localhost:8000` regardless of which origin issued it, so the
`sessionid` cookie alone cannot prove the request came from the SPA.

- **Mechanism:** Django's built-in double-submit-cookie CSRF protection (`CsrfViewMiddleware`), not a
  custom token scheme.
- **Cookie:** `csrftoken` — readable by JavaScript (`Secure`/`SameSite` per
  [Cookies](#cookies-local-http-development), but **not** `HttpOnly`, since the SPA must read its
  value to echo it back in the header).
- **Header:** `X-CSRFToken` — required on every unsafe request (`POST`, `PATCH`, `PUT`, `DELETE`) to
  every endpoint. `GET`/`HEAD`/`OPTIONS` never require it.
- **Cookie issuance:** `GET /api/auth/session/` is decorated with `@ensure_csrf_cookie`, so calling it
  guarantees a fresh `csrftoken` cookie exists — including for a visitor who has never logged in. This
  is why the SPA calls `GET /api/auth/session/` unconditionally on boot: it doubles as "am I logged
  in" and "give me a CSRF token" in one request. `POST /api/auth/login/` also refreshes the cookie on
  success (Django rotates the CSRF token on login by default, `CSRF_COOKIE_AGE`/rotation aside — the
  SPA must re-read `document.cookie` after login rather than reusing the pre-login token).
- **Missing/invalid header on an unsafe request:** `403 Forbidden`,
  `{ "detail": "CSRF Failed: CSRF token missing." }` (Django's default `CsrfViewMiddleware` body, not
  the `{error, detail}` shape used elsewhere — the SPA's fetch wrapper must special-case `403` with a
  body that has `detail` but no `error` key as "CSRF failure, retry after re-fetching the cookie" one
  time before surfacing an error to the user).
- **Django settings implied by this decision:**
  - `CSRF_TRUSTED_ORIGINS = ["http://localhost:5173"]` (dev; production equivalent added when a real
    origin exists — out of scope here, no production origin is defined in the spec)
  - `CORS_ALLOW_CREDENTIALS = True` and `CORS_ALLOWED_ORIGINS = ["http://localhost:5173"]` (via
    `django-cors-headers`) — required so the browser attaches cookies to cross-origin fetches at all
    (`fetch(..., { credentials: "include" })` on the SPA side)
  - `CSRF_HEADER_NAME` stays Django's default (`HTTP_X_CSRFTOKEN`, i.e. the `X-CSRFToken` header) —
    no rename

## Cookies (local HTTP development)

Both cookies are scoped to `localhost:8000` (the API's own origin — a cookie's origin is where it was
*set*, not where the request that reads it originates; cross-origin `fetch` with `credentials:
"include"` still attaches it).

| Cookie | `HttpOnly` | `Secure` | `SameSite` | Notes |
|---|---|---|---|---|
| `sessionid` | `True` | `False` | `Lax` | Django's default session cookie; never readable by JS. |
| `csrftoken` | `False` | `False` | `Lax` | Must be JS-readable so the SPA can echo it in `X-CSRFToken`. |

- **`Secure=False`:** both origins are plain `http://localhost` in dev; a `Secure` cookie would
  silently not be sent over HTTP and break every request. This is a deliberate dev-only relaxation.
- **`SameSite=Lax`** (not `None`) is sufficient here specifically because `5173` and `8000` are both
  `localhost` — modern browsers treat same-site-different-port as same-site for `SameSite` purposes,
  so `Lax` still allows the cross-port `fetch`. This is a `localhost`-specific property, not a general
  cross-origin one.
- **What changes for a real cross-origin HTTPS deployment** (SPA and API on different registrable
  domains, e.g. `app.example.com` and `api.example.com`): `Secure` must become `True` on both cookies
  (required for `SameSite=None` and good practice regardless), and `SameSite` must become `None` on
  both — true cross-site requests are not covered by the `Lax` same-site carve-out. `CSRF_TRUSTED_ORIGINS`
  and `CORS_ALLOWED_ORIGINS` must be updated to the real origin. No other part of this contract
  changes; the endpoint shapes, the CSRF mechanism, and the DTO are unaffected. This is documented
  here, not implemented — the spec's only deployment target is local Docker Compose
  (`docs/specs/specs.md`).

## Permissions

- **Default DRF permission:** `IsAuthenticated`, set globally via
  `REST_FRAMEWORK["DEFAULT_PERMISSION_CLASSES"]`.
- **Exempt (public) endpoints**, overridden per-view with `AllowAny`:
  - `GET /api/health/`
  - `POST /api/auth/login/`
  - `GET /api/auth/session/`
- Every other endpoint in `api-endpoints.md` — `POST /api/auth/logout/`, `GET /api/providers/`,
  `GET /api/system-prompts/`, `GET`/`PATCH /api/settings/`, `POST /api/runs/`,
  `GET /api/runs/{id}/`, `POST /api/responses/{id}/retry/` — inherits `IsAuthenticated` and needs no
  per-view override for auth (`PATCH /api/settings/` additionally needs a staff check, already
  specified in `api-endpoints.md`).

## Session lifetime

- `SESSION_COOKIE_AGE` uses Django's default of `1209600` seconds (2 weeks) — the spec sets no
  explicit session-timeout requirement, and a short-lived session would fight the "ephemeral data
  survives a refresh" requirement in `db-schema.md` (a refresh must not force a re-login).
  `SESSION_EXPIRE_AT_BROWSER_CLOSE = False` for the same reason: closing the tab must not lose the
  session, only an explicit logout or the 2-week expiry does.
  - `request.session.session_key` is not returned to the client in any endpoint response — see
    [User DTO](#user-dto) above. It is used server-side only, to scope `PromptRun.session_key`
    lookups (`db-schema.md`) once that model exists.
- Rate limiting, lockout after repeated failed logins, and any other abuse-mitigation policy are
  explicitly out of scope for this contract — deferred to `LLMC-SEC-001`, which decides whether the
  hackathon scope needs them at all.

## Logout and session-scoped data purge

`POST /api/auth/logout/` is the single component responsible for purging session-scoped data — no
other endpoint deletes `PromptRun`/`ModelResponse` rows. Per diagram 2 in `sequence-diagrams.md` and
the ephemeral-data note in `db-schema.md`, the logout view must, before destroying the session:

```
DELETE FROM prompt_run WHERE session_key = request.session.session_key
```

which cascades to `ModelResponse` via `on_delete=CASCADE`. **This step does not exist yet** — no run
models exist until `LLMC-RUNS-001` lands. Until then, `POST /api/auth/logout/` (built in
`LLMC-AUTH-002`) only destroys the session; the purge query is added by `LLMC-RUNS-001` as a change to
that same view, not a new endpoint. A scheduled Django-Q2 task also purges `PromptRun` rows past a
short TTL as a safety net for sessions that expire without an explicit logout (`db-schema.md`) — also
`LLMC-RUNS-001` scope.

## Out of scope

- Token/JWT auth, OAuth, SSO — session cookies only, per the decisions above.
- Password reset, "remember me", self-service registration — none are in the spec; accounts are
  admin-provisioned only (see [User model](#user-model-and-account-creation)).
- Rate limiting / lockout policy — deferred to `LLMC-SEC-001`.
- Frontend state modelling of the login screen (loading/submitting/error/success transitions) —
  `LLMC-AUTH-003`; this contract only fixes the wire format those states react to.
- Any implementation (models, views, settings, tests) — `LLMC-AUTH-002`.
