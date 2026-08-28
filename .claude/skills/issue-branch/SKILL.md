---
name: issue-branch
description: Create a GitHub issue and a linked working branch for it using the gh CLI. Use when the user asks to open an issue, start work on a new task, create a ticket and branch, or "abrir un issue y una rama".
allowed-tools: Bash(./.claude/skills/issue-branch/scripts/new-issue-branch.sh:*), Bash(gh issue:*), Bash(git status:*), Bash(git branch:*)
---

# Issue + branch

Creates a GitHub issue and the branch linked to it (via `gh issue develop`, so GitHub
records the issue↔branch relationship) in a single step.

## Usage

```bash
./.claude/skills/issue-branch/scripts/new-issue-branch.sh \
  --title "Define requirements" \
  --body "Full requirements list for this repo"
```

Options:

| Flag | Description |
| --- | --- |
| `--title <text>` | Issue title (required) |
| `--body <text>` | Issue body |
| `--body-file <path>` | Read body from a file, or `-` for stdin (use for multi-line bodies) |
| `--branch <name>` | Branch name. Default: `feature/<slug-of-title>` |
| `--label <name>` | Label to add (repeatable) |
| `--assignee <user>` | Default `@me` |
| `--base <branch>` | Base branch |
| `--no-checkout` | Create the branch without switching to it |

Output on success:

```
issue: https://github.com/<owner>/<repo>/issues/42
branch: feature/define-requirements
```

## Guidelines

- Write the title as a short imperative phrase; put context, acceptance criteria and
  scope in the body.
- A body that starts with YAML frontmatter (any task file) is reformatted automatically:
  the frontmatter becomes a one-line metadata header plus `Depends on` / `Docs` lines, and
  the duplicated `# <ID> - <title>` heading is dropped. Pass the task file through as-is;
  do not hand-strip it.
- For multi-line bodies, write the markdown to a temp file and pass `--body-file`.
- The script refuses to run with a dirty working tree unless `--no-checkout` is passed;
  ask the user to commit or stash first.
- Prefer this skill over calling `gh issue create` + `git checkout -b` separately, so the
  branch stays linked to the issue.

## Use inside the task workflow

When starting a task from `docs/tasks/tasks/`, run this **before**
`tasks.py status <ID> in-progress` — that command rewrites the task file and the
generated index, which dirties the tree and makes this script refuse to check out.

```bash
python3 scripts/tasks.py show TSC-AUTH-002 > /tmp/issue-body.md
./.claude/skills/issue-branch/scripts/new-issue-branch.sh \
  --title "[TSC-AUTH-002] Implement the authentication backend" \
  --body-file /tmp/issue-body.md \
  --branch "task/TSC-AUTH-002-auth-backend" \
  --label task
python3 scripts/tasks.py link TSC-AUTH-002 https://github.com/<owner>/<repo>/issues/42
```

The frontmatter in that `show` output is rendered as the issue's metadata header, so the
issue reads as prose rather than raw YAML.

`tasks.py link` records the issue URL in the task's frontmatter, so the link is
bidirectional: the issue body carries the task, and the task carries the issue.

Branch naming for tasks: `task/<TASK-ID>-<short-slug>`. The ID leads so branches sort and
grep by task, and so a stale branch is traceable to its ledger entry.

## Failure modes worth knowing

- **No GitHub remote / not authenticated / not a git repo** — the script exits before
  creating anything. In a project not hosted on GitHub, skip this skill entirely and use a
  plain `git switch -c task/<ID>-<slug>`; nothing else in the workflow depends on issues.
- **Issue created but branch failed** — the script says so and prints the exact
  `gh issue develop` command to finish the job. Do not create a second issue.

## Equivalent manual commands

```bash
gh issue create --title "Define requirements" --body "..." --assignee "@me"
gh issue develop 42 --name "feature/mi-nueva-rama" --checkout
```
