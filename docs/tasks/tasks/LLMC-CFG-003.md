---
id: LLMC-CFG-003
title: Verify the configuration slice and its staff gate
area: CFG
phase: 2
layer: verify
status: todo
review: none
depends_on:
  - LLMC-CFG-001
  - LLMC-CFG-002
docs:
  read:
    - docs/backend/config-backend.md
    - docs/frontend/settings-frontend.md
  write:
    - docs/infra/verification-config.md
---

# LLMC-CFG-003 - Verify the configuration slice and its staff gate

## Objective

After this task the configuration slice is proven on the real stack with two real users — one staff,
one not — confirming that the privilege boundary the Settings page draws in the UI is actually
enforced by the server, and that a limit changed through the UI is the limit the rest of the system
reads.

## Scope

**In:**

- `scripts/verify-config.sh`: creates a staff and a non-staff user, logs each in with its own cookie
  jar, and asserts the full permission matrix over `/api/providers/`, `/api/settings/` and
  `/api/system-prompts/`, including the out-of-range `PATCH` bounds; restores the original
  `max_prompt_length` and deletes both users on exit.
- Cross-check that a `PATCH`ed limit is visible to other readers of the same singleton row
  (`GET /api/settings/` and `GET /api/health/`).
- Manual browser pass over `http://localhost:5173/settings` as both users, recorded in the living doc:
  library renders, "Use" navigates with the prompt carried over, the limit control is enabled for
  staff and disabled for the other user.
- `docs/infra/verification-config.md`.

**Out:**

- The overall security review (`LLMC-SEC-001`), which revisits this boundary alongside key handling and
  run ownership.
- Anything about prompt runs — no run endpoints exist yet.
- Adding these checks to CI.

## Outputs

- `scripts/verify-config.sh`
- `docs/infra/verification-config.md` (procedure + recorded run, including the two manual passes)

## Acceptance criteria

- [ ] `bash scripts/verify-config.sh` exits `0` against a `make up-d` stack and leaves
      `max_prompt_length` at its pre-run value.
- [ ] The script asserts `403` for a non-staff `PATCH /api/settings/` and `200` for a staff one.
- [ ] The script asserts `400` for `PATCH` values `50` and `5000`, and that neither changed the stored
      value.
- [ ] The script asserts that a staff `PATCH` to `850` is subsequently reported by both
      `GET /api/settings/` and `GET /api/health/`.
- [ ] The script asserts all three endpoints return `401` with no cookie jar.
- [ ] `docs/infra/verification-config.md` records the manual staff and non-staff browser passes with
      their outcome.

## Verification

```bash
cd "$(git rev-parse --show-toplevel)"
make up-d
timeout 120 bash -c 'until curl -fsS http://localhost:8000/api/health/ >/dev/null; do sleep 2; done'
BEFORE=$(curl -fsS http://localhost:8000/api/health/ | grep -o '"max_prompt_length": *[0-9]*')
bash scripts/verify-config.sh
AFTER=$(curl -fsS http://localhost:8000/api/health/ | grep -o '"max_prompt_length": *[0-9]*')
test "$BEFORE" = "$AFTER"
grep -qi 'manual' docs/infra/verification-config.md
```

## Evidence

_None recorded yet._
