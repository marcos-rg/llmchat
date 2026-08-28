---
id: LLMC-SEC-001
title: Security posture review: keys, session scoping and staff gate
area: SEC
phase: 5
layer: verify
status: todo
review: human
depends_on:
  - LLMC-RUNS-005
  - LLMC-CFG-003
docs:
  read:
    - docs/specs/specs.md
    - docs/backend/auth-contract.md
    - docs/backend/llm-contract.md
    - docs/infra/environment.md
  write:
    - docs/infra/security-review.md
---

# LLMC-SEC-001 - Security posture review: keys, session scoping and staff gate

## Objective

After this task every security and privacy requirement in `docs/specs/specs.md` has been tested against
the assembled system rather than assumed from the design docs, and a human has signed off on the
result: API keys never leave the worker, one user can never reach another's run, the staff gate holds,
and logging out really does destroy the session's data.

## Scope

**In:**

- `scripts/verify-security.sh` asserting, against a running stack:
  - No provider key is present in the `backend` or `frontend` container environments, in the built
    frontend bundle, in any API response body, or in `docker compose logs` for any service — checked
    with a recognisable sentinel key value.
  - Cross-user isolation: user B receives `404` (not `403`) for user A's run and for
    `POST /api/responses/{id}/retry/` on A's response.
  - Cross-session isolation for the same user: a run created in session 1 is gone after logout, and the
    responses are gone with it (no orphan `ModelResponse` rows).
  - The staff gate on `PATCH /api/settings/` and the `IsAuthenticated` default on every `/api/` route
    except the documented exempt list.
  - CSRF enforcement on every unsafe method, and CORS rejecting an unlisted origin.
  - Input bounds that guard the queue: oversized prompt, out-of-range `run_count`, unknown
    provider/model.
- A written review in `docs/infra/security-review.md`: each spec Security & Privacy bullet with the
  check that covers it, the residual risks accepted for a local-only hackathon deployment (no rate
  limiting, `DEBUG=1` locally, shared admin keys), and what would have to change before any non-local
  deployment.
- A dependency check (`pip-audit` or equivalent, `npm audit`) with findings triaged in the doc.

**Out:**

- Implementing new security features — anything the review finds becomes its own task rather than
  scope creep here; only trivial configuration corrections are fixed in place, and each is recorded.
- Penetration testing, threat modelling beyond the spec's stated requirements, and any
  production/cloud hardening — the deployment target is local Compose only.
- Accessibility (`LLMC-AXS-001`) and performance (`LLMC-PERF-001`).

## Outputs

- `scripts/verify-security.sh`
- `docs/infra/security-review.md` — requirement-by-requirement result, accepted residual risks,
  dependency-audit triage, and any follow-up tasks proposed

## Acceptance criteria

- [ ] `bash scripts/verify-security.sh` exits `0` against a `make up-d` stack started with a sentinel
      key value.
- [ ] The sentinel key appears in no container log, no API response, and no file under
      `frontend/dist/`.
- [ ] User B gets `404` for user A's run and for a retry on A's response, and never `403` (which would
      confirm the run exists).
- [ ] After logout, the session's `PromptRun` rows and all their `ModelResponse` rows are gone —
      verified by row counts, not just by the API returning `404`.
- [ ] Every `/api/` route except `/api/health/`, `/api/auth/login/` and `/api/auth/session/` returns
      `401` without a session.
- [ ] Every unsafe method without `X-CSRFToken` is rejected, and a request from an unlisted origin
      receives no allow-origin header for it.
- [ ] `docs/infra/security-review.md` has a row for each Security & Privacy bullet in
      `docs/specs/specs.md` with a pass/fail/accepted-risk verdict.
- [ ] A human has reviewed and approved the posture, including the accepted residual risks.

## Verification

```bash
cd "$(git rev-parse --show-toplevel)"
make up-d
timeout 120 bash -c 'until curl -fsS http://localhost:8000/api/health/ >/dev/null; do sleep 2; done'
bash scripts/verify-security.sh
docker compose run --rm frontend npm run build
! grep -rq 'sk-sentinel' frontend/dist
docker compose logs --no-color | grep -c 'sk-sentinel' | grep -q '^0$'
D=docs/infra/security-review.md
for w in 'Authentication is required' 'API keys' 'own active session'; do grep -qi "$(echo "$w" | cut -c1-12)" "$D"; done
grep -qi 'residual' "$D"
```

## Evidence

_None recorded yet._
