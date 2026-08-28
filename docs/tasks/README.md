# Task-driven agent workflow

This workflow is already wired up for this project: a human writes the spec,
`task-generator` turns it into a dependency-ordered task graph, and `task-executor`
builds it one verified task at a time.

## Setup

The spec already exists at [`docs/specs/specs.md`](../specs/specs.md) — that's what
`task-generator` decomposes. Nothing else to set up.

## Use

```
> use the task-generator agent to plan the project
> use the task-executor agent to do the next task     # repeat until done
```

The executor does exactly one task per invocation. That bound is deliberate: it keeps
context small, keeps each unit reviewable, and keeps a failure contained to one task.

## The three-part split

Each piece does the one job it is actually good at, which is the main structural lesson
from v1:

| Piece | Owns | Why not somewhere else |
|---|---|---|
| `scripts/tasks.py` | status, evidence, the index, all invariants | A program never miscounts or forgets a guard. Prose asks a model to be careful; code does not have to ask. |
| `scripts/hooks/*.sh` | blocking on an invalid graph | The harness enforces this, so it cannot be reasoned around mid-task. Hooks are for invariants, never for procedure. |
| `.claude/skills/task-framework` | the *definition* of the format | One shared copy. In v1 the rules lived in three places and had already drifted apart. |
| `.claude/agents/*` | the *procedure* — plan, or execute | Judgment belongs to the model; the rules it works under do not. |
| `.claude/skills/issue-branch` | one issue + one linked branch per task | A shell script gets `gh issue develop` right every time; an agent improvising `gh` calls does not. |

## What the tracker will refuse

Not suggestions in a prompt — enforced, with a non-zero exit:

- starting a task whose dependencies are not `done`, or whose contract doc is missing
- starting a second task while one is `in-progress`
- marking a task `done` with no recorded evidence
- marking a task `done` before the living doc it declared exists
- marking a gated task `done` without `--approved`
- any hand edit to a `status:` line or to the generated `docs/tasks/tasks.md`
- a dependency cycle, an unknown dependency, or a task section left out

## One task, one issue, one branch, one PR

The executor opens a GitHub issue and a linked branch before claiming a task, and a PR
when it finishes. The issue body *is* the task file, so scope and acceptance criteria are
reviewable on GitHub; `tasks.py link` writes the issue URL back into the task, so the
reference resolves both ways.

Ordering is not cosmetic: the issue and branch are created **before**
`tasks.py status ... in-progress`, because that command rewrites the task file and the
index, and `new-issue-branch.sh` refuses to check out onto a dirty tree.

Not on GitHub? The script exits without creating anything and the executor falls back to
`git switch -c task/<ID>-<slug>`. Nothing else in the workflow depends on issues.

## Docs before artifacts

The rule the whole layout exists to enforce.

```yaml
docs:
  read:  [docs/backend/auth-contract.md]   # the contract — must exist before the task starts
  write: [docs/backend/auth-backend.md]    # the living record — must exist before it is done
```

When the design is non-trivial, a `layer: contract` task writes `docs/<layer>/<x>-contract.md`
(alongside the existing `docs/backend/`, `docs/frontend/`, `docs/infra/` doc sets) *before* the
implementation task that reads it. The decision gets made and reviewed while it is still a
paragraph, not after it is a thousand lines of code defending itself.

## How the plan is shaped

Phase 0 ends with a deployable walking skeleton — one page, one endpoint, one row, in
containers, in CI. Not a folder tree: a thin working line through every layer.

Then one feature at a time, each a vertical slice of `contract → backend → frontend →
verify`, every phase leaving the system runnable. The system grows upward and is never
in a state where nothing works.
