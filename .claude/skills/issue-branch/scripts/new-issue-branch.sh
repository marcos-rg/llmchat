#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: new-issue-branch.sh --title "<title>" [options]

Creates a GitHub issue and a linked branch for it.

Options:
  --title <text>        Issue title (required)
  --body <text>         Issue body
  --body-file <path>    Read the issue body from a file ("-" for stdin)
  --branch <name>       Branch name (default: feature/<slug-of-title>)
  --label <name>        Label to add (repeatable)
  --assignee <user>     Assignee (default: @me)
  --base <branch>       Base branch for the new branch
  --no-checkout         Create the branch without checking it out
  -h, --help            Show this help
EOF
}

title=""
body=""
body_file=""
branch=""
base=""
assignee="@me"
labels=()
checkout=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    --title)      title="${2:?--title requires a value}"; shift 2 ;;
    --body)       body="${2:?--body requires a value}"; shift 2 ;;
    --body-file)  body_file="${2:?--body-file requires a value}"; shift 2 ;;
    --branch)     branch="${2:?--branch requires a value}"; shift 2 ;;
    --base)       base="${2:?--base requires a value}"; shift 2 ;;
    --assignee)   assignee="${2:?--assignee requires a value}"; shift 2 ;;
    --label)      labels+=("${2:?--label requires a value}"); shift 2 ;;
    --no-checkout) checkout=0; shift ;;
    -h|--help)    usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ -z "$title" ]]; then
  echo "Error: --title is required" >&2
  exit 2
fi

command -v gh >/dev/null 2>&1 || { echo "Error: gh CLI is not installed" >&2; exit 1; }
gh auth status >/dev/null 2>&1 || { echo "Error: gh is not authenticated (run 'gh auth login')" >&2; exit 1; }
git rev-parse --git-dir >/dev/null 2>&1 || { echo "Error: not inside a git repository" >&2; exit 1; }
gh repo view --json name >/dev/null 2>&1 || {
  echo "Error: no GitHub repository for this checkout (add a remote, or skip this step)" >&2
  exit 1
}

if [[ -n "$body_file" ]]; then
  if [[ "$body_file" == "-" ]]; then
    body="$(cat)"
  else
    body="$(cat -- "$body_file")"
  fi
fi

# -E, not \+: BSD sed (macOS) does not treat \+ as a quantifier, which would leave
# spaces in the slug and produce an invalid git ref.
slugify() {
  printf '%s' "$1" \
    | tr '[:upper:]' '[:lower:]' \
    | sed -E -e 's/[^a-z0-9]+/-/g' -e 's/^-+//' -e 's/-+$//' \
    | cut -c1-50 \
    | sed -E 's/-+$//'
}

if [[ -z "$branch" ]]; then
  slug="$(slugify "$title")"
  [[ -n "$slug" ]] || slug="issue"
  branch="feature/${slug}"
fi

git check-ref-format --branch "$branch" >/dev/null 2>&1 || {
  echo "Error: '$branch' is not a valid branch name" >&2
  exit 1
}

# Uncommitted changes would be carried into the new branch on checkout.
if (( checkout )) && [[ -n "$(git status --porcelain)" ]]; then
  echo "Error: working tree is dirty; commit/stash first or use --no-checkout" >&2
  exit 1
fi

create_args=(issue create --title "$title" --body "${body:-}")
[[ -n "$assignee" ]] && create_args+=(--assignee "$assignee")
for label in "${labels[@]:-}"; do
  [[ -n "$label" ]] && create_args+=(--label "$label")
done

# gh may print progress lines before the URL; the URL is always the last line.
issue_url="$(gh "${create_args[@]}" | tail -n 1)"
issue_number="${issue_url##*/}"

if ! [[ "$issue_number" =~ ^[0-9]+$ ]]; then
  echo "Error: could not parse issue number from '$issue_url'" >&2
  exit 1
fi

develop_args=(issue develop "$issue_number" --name "$branch")
[[ -n "$base" ]] && develop_args+=(--base "$base")
(( checkout )) && develop_args+=(--checkout)

if ! gh "${develop_args[@]}"; then
  echo "Error: issue $issue_number was created ($issue_url) but the branch was not." >&2
  echo "Fix the cause, then link a branch with: gh issue develop $issue_number --name $branch --checkout" >&2
  exit 1
fi

echo "issue: $issue_url"
echo "branch: $branch"
