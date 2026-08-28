---
id: LLMC-AUTH-001
title: Session auth and CSRF contract for the cross-origin SPA
area: AUTH
phase: 1
layer: contract
status: todo
review: none
depends_on:
  - LLMC-CORE-001
docs:
  read:
    - docs/specs/specs.md
    - docs/backend/api-endpoints.md
    - docs/backend/sequence-diagrams.md
    - docs/backend/db-schema.md
    - docs/frontend/states.md
  write:
    - docs/backend/auth-contract.md
---

# LLMC-AUTH-001 - Session auth and CSRF contract for the cross-origin SPA

## Objective

After this task there is a written, reviewed decision for how a React SPA on `localhost:5173`
authenticates against a Django API on `localhost:8000` using session cookies — the part
`docs/backend/api-endpoints.md` leaves open. It fixes the CSRF strategy, the cookie attributes, how
the SPA learns it already has a session after a refresh, the unauthenticated response shape, and the
user DTO — before any of it is implemented and defended in code.

## Scope

**In:**

- `docs/backend/auth-contract.md` covering:
  - The custom `User` model decision (`AbstractUser`, `username=None`, unique `email`,
    `USERNAME_FIELD="email"`) and the consequence that accounts are created by an admin
    (`createsuperuser` / Django admin) — there is no self-service signup endpoint in the spec.
  - `POST /api/auth/login/`, `POST /api/auth/logout/` and the new `GET /api/auth/session/`: method,
    path, auth rule, request body, success body, and every error status with its `{error, detail}` code.
  - The user DTO, including `is_staff` — the Settings page needs it to gate the prompt-limit control
    (`docs/frontend/pages.md`), so it must be on the login and session payloads.
  - CSRF: which requests require `X-CSRFToken`, how the `csrftoken` cookie is issued
    (`ensure_csrf_cookie` on `GET /api/auth/session/`), `CSRF_TRUSTED_ORIGINS`,
    `CORS_ALLOW_CREDENTIALS`, and the exact status returned when the header is missing.
  - Cookie attributes for local HTTP development (`SameSite`, `Secure`, `HttpOnly`) and what would
    have to change if the app were ever served over HTTPS from another origin.
  - The DRF default permission (`IsAuthenticated`) and the exempt list (`/api/health/`,
    `/api/auth/login/`, `/api/auth/session/`).
  - Session lifetime/expiry, and the rule that `request.session.session_key` is never returned to the
    client — it is a server-side scoping key only (`docs/backend/db-schema.md`).
  - Which component owns purging session-scoped data at logout, and the note that the purge itself
    lands in `LLMC-RUNS-001` because no run models exist yet.
- Amending `docs/backend/api-endpoints.md` with the `GET /api/auth/session/` section and the `is_staff`
  field, so the two documents do not disagree.

**Out:**

- Any implementation — no models, views, settings or tests (`LLMC-AUTH-002`).
- Token/JWT auth, OAuth, SSO, password reset, registration, or "remember me": none are in the spec.
- Rate limiting and lockout policy — deferred to the security review (`LLMC-SEC-001`), which decides
  whether the hackathon scope needs it.
- Frontend state modelling of the login screen (`LLMC-AUTH-003`).

## Outputs

- `docs/backend/auth-contract.md`
- Updated `docs/backend/api-endpoints.md` (new `GET /api/auth/session/` section; `is_staff` on the user
  object in the login response)

## Acceptance criteria

- [ ] The contract documents all three auth endpoints, and for each names the method, path, auth rule,
      request shape, success shape and every error code — checked by grepping each path plus the words
      `Auth required`, `Request`, `Success` and `Error` in its section.
- [ ] The contract states a single CSRF decision: it names the header, the cookie, the endpoint that
      issues the cookie, and the status code returned when the header is absent on an unsafe request.
- [ ] The contract and `docs/backend/api-endpoints.md` agree on the login failure envelope — both
      contain `invalid_credentials` and `401`.
- [ ] `is_staff` appears in the user object in both the contract and `docs/backend/api-endpoints.md`.
- [ ] Every relative markdown link in the contract resolves to a file that exists.
- [ ] The contract contradicts nothing in `docs/backend/db-schema.md`: it uses `email` as
      `USERNAME_FIELD` and does not introduce a `username` field.

## Verification

```bash
cd "$(git rev-parse --show-toplevel)"
C=docs/backend/auth-contract.md
test -f "$C"
for p in '/api/auth/login/' '/api/auth/logout/' '/api/auth/session/'; do grep -q -- "$p" "$C"; done
for w in 'Auth required' 'Request' 'Success' 'Error' 'X-CSRFToken' 'csrftoken' 'SameSite' 'is_staff' \
         'IsAuthenticated' 'USERNAME_FIELD' 'session_key'; do grep -q "$w" "$C"; done
grep -q 'invalid_credentials' "$C" && grep -q '401' "$C"
grep -q '/api/auth/session/' docs/backend/api-endpoints.md
grep -q 'is_staff' docs/backend/api-endpoints.md
grep -q 'invalid_credentials' docs/backend/api-endpoints.md
! grep -q 'username' "$C"
grep -o '](\.\./[^)#]*\|](\./[^)#]*' "$C" | sed 's/^](//' | while read -r l; do \
  test -e "docs/backend/$l" || { echo "broken link: $l"; exit 1; }; done
```

## Evidence

_None recorded yet._
