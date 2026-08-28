---
name: task-framework
description: The task ledger format and rules for this project - task file schema, statuses, dependency and docs conventions, and the tasks.py commands that own them. Load this before creating, editing, selecting, or completing any task in docs/tasks/tasks/.
---

# Task framework

This is the **single definition** of the task format. The generator writes it, the
executor reads it, `scripts/tasks.py` enforces it. Nothing else may restate these rules —
if a rule needs to change, it changes here.

## Where things live

| Path | Owner | Editable by hand |
|---|---|---|
| `docs/specs/specs.md` | human | yes — source of truth for scope |
| `docs/**` | whoever does the task | yes — the contract and the living record |
| `docs/tasks/tasks/<ID>.md` | generator (prose), `tasks.py` (status/evidence) | prose yes, `status:` **never** |
| `docs/tasks/tasks.md` | `tasks.py index` | **never** — generated |

## Task file schema

```yaml
---
id: TSC-AUTH-001            # <PREFIX>-<AREA>-<NNN>. Never changes, never reused.
title: Implement backend authentication
area: AUTH
phase: 1                    # integer; phase 0 is the walking skeleton
layer: backend              # infra | contract | backend | frontend | verify | docs | release
status: todo                # todo | in-progress | needs-review | blocked | done
issue: https://...          # optional; written by `tasks.py link`, not by hand
review: none                # none | human
depends_on:
  - TSC-CORE-001
docs:
  read:                     # contracts this task implements — must exist BEFORE it starts
    - docs/backend/auth-contract.md
  write:                    # living docs this task must produce — checked before `done`
    - docs/auth-backend.md
---
```

Then six required markdown sections, in this order:

- `## Objective` — one paragraph: what capability exists after this task that did not before.
- `## Scope` — explicit **In:** and **Out:** lists. "Out" is what stops scope creep.
- `## Outputs` — concrete artifacts: files, endpoints, components, migrations.
- `## Acceptance criteria` — a checkbox list where **every line is checkable by running
  something**. The existence of a file is never a criterion.
- `## Verification` — one fenced ` ```bash ` block of the exact commands that prove the
  criteria. `tasks.py verify <ID> --run` executes this block.
- `## Evidence` — append-only, written by `tasks.py evidence`. Never edit by hand.

## Statuses

| Status | Meaning | `next` picks it? |
|---|---|---|
| `todo` | not started | yes, once dependencies are `done` and `docs.read` exist |
| `in-progress` | actively being worked; at most one at a time | yes (resume) |
| `needs-review` | work complete and committed, waiting on a human | **no** |
| `blocked` | cannot proceed for a reason outside the graph | **no** |
| `done` | every criterion verified, evidence recorded, living doc written | — |

`needs-review` exists so a task waiting on a human does not jam the queue. This is the
whole reason the loop keeps moving: park it and the next independent task becomes eligible.

## Docs before artifacts

The direction is **docs → code**, never code → docs.

- A task's `docs.read` entries are the contract it implements. They must exist before the
  task can start; `tasks.py status <ID> in-progress` refuses otherwise. If the contract is
  missing, the fix is a `layer: contract` task that writes it — not to start coding.
- A task's `docs.write` entries are the living record it must produce. `tasks.py status
  <ID> done` refuses if the file does not exist.
- Write or update the `docs.write` doc **as you design, before or alongside the code** —
  not as a closing chore. A doc written after the tests pass only ever describes what
  happened to get built.

## Review gates

`review: human` is for decisions a machine cannot settle: scope and architecture sign-off,
security posture, visual/UX judgment, production release. **Not** for routine
implementation. If most tasks carry a gate, the gate means nothing and the loop stalls.

Gated flow: implement → commit → `status <ID> needs-review` → stop and ask the human →
(later invocation, after they confirm) `status <ID> done --approved`.

## Commands

```bash
python3 scripts/tasks.py next                       # what to work on
python3 scripts/tasks.py show TSC-AUTH-001
python3 scripts/tasks.py list [--status todo] [--json]
python3 scripts/tasks.py new TSC-AUTH-001 "Title" \
    --phase 1 --layer backend --review none \
    --depends-on TSC-CORE-001 --read docs/backend/auth-contract.md --write docs/backend/auth-backend.md
python3 scripts/tasks.py status TSC-AUTH-001 in-progress
python3 scripts/tasks.py evidence TSC-AUTH-001 "pytest -q tests/auth -> 34 passed"
python3 scripts/tasks.py link TSC-AUTH-001 https://github.com/acme/app/issues/42
python3 scripts/tasks.py verify TSC-AUTH-001 --run
python3 scripts/tasks.py status TSC-AUTH-001 done
python3 scripts/tasks.py validate                   # graph integrity; hooks run this
python3 scripts/tasks.py index                      # regenerate docs/tasks/tasks.md
```

`status` regenerates the index automatically. Never edit a `status:` line, and never edit
`docs/tasks/tasks.md`, by hand — a hook will reject it.

## Invariants `validate` enforces

Schema and section completeness; id/filename agreement; unknown dependencies; **dependency
cycles**; more than one task `in-progress`; a `done` task with a non-`done` dependency,
with an empty Evidence section, or with a `docs.write` file that does not exist.
