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
- For multi-line bodies, write the markdown to a temp file and pass `--body-file`.
- The script refuses to run with a dirty working tree unless `--no-checkout` is passed;
  ask the user to commit or stash first.
- Prefer this skill over calling `gh issue create` + `git checkout -b` separately, so the
  branch stays linked to the issue.

## Equivalent manual commands

```bash
gh issue create --title "Define requirements" --body "..." --assignee "@me"
gh issue develop 42 --name "feature/mi-nueva-rama" --checkout
```
