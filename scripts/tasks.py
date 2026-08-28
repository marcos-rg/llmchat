#!/usr/bin/env python3
"""Task tracker for docs/tasks/tasks/*.md (task framework v2).

Each task is one file, `docs/tasks/tasks/<ID>.md`, with YAML frontmatter for
machine-owned fields and markdown for human-owned prose. This script is the ONLY
writer of status and evidence; `docs/tasks/tasks.md` is a generated index.

Subcommands:
  next                       Print the next actionable task.
  list [--status S] [--json] List tasks with status, phase, and dependencies.
  show <ID>                  Print a task file.
  new <ID> <title> [opts]    Scaffold a schema-correct task file.
  status <ID> <STATUS>       Move a task between statuses (guards enforced).
  evidence <ID> <text>       Append a timestamped evidence line to a task.
  link <ID> <url>            Record the GitHub issue URL for a task.
  verify <ID> [--run]        Print (or run) the task's verification commands.
  validate                   Check the whole graph; exit 1 on problems.
  index                      Regenerate docs/tasks/tasks.md.
  graph                      Print the dependency graph as mermaid.

Statuses: todo, in-progress, needs-review, blocked, done
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TASKS_DIR = REPO_ROOT / "docs" / "tasks" / "tasks"
INDEX_FILE = REPO_ROOT / "docs" / "tasks" / "tasks.md"

STATUSES = ("todo", "in-progress", "needs-review", "blocked", "done")
ACTIONABLE = ("todo", "in-progress")
LAYERS = ("infra", "contract", "backend", "frontend", "verify", "docs", "release")
REVIEWS = ("none", "human")
ID_RE = re.compile(r"^[A-Z]{2,5}-[A-Z]+-\d{3}$")

SECTIONS = ("Objective", "Scope", "Outputs", "Acceptance criteria", "Verification", "Evidence")


# --------------------------------------------------------------------------- #
# Minimal frontmatter parser.
#
# Deliberately not PyYAML: no third-party dependency, and a strict subset with
# loud errors beats a permissive parser that silently accepts a malformed graph.
# Supports: `key: scalar`, `key: [a, b]`, block lists, and one level of nesting.
# --------------------------------------------------------------------------- #

class ParseError(Exception):
    pass


def _scalar(raw: str):
    v = raw.strip()
    if not v.startswith(("'", '"')) and " #" in v:
        v = v.split(" #", 1)[0].strip()      # trailing inline comment
    if v.startswith(("'", '"')) and v.endswith(("'", '"')) and len(v) >= 2:
        return v[1:-1]
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1].strip()
        return [_scalar(p) for p in inner.split(",") if p.strip()] if inner else []
    if v.isdigit():
        return int(v)
    return v


def parse_frontmatter(text: str, where: str) -> tuple[dict, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ParseError(f"{where}: file must start with a '---' frontmatter fence")
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        raise ParseError(f"{where}: frontmatter fence is never closed") from None

    data: dict = {}
    cur_key: str | None = None      # key currently collecting a block list
    cur_map: str | None = None      # key currently collecting a nested map
    for n, line in enumerate(lines[1:end], start=2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        stripped = line.strip()

        if stripped.startswith("- "):
            item = _scalar(stripped[2:])
            target = data[cur_map][cur_key] if cur_map else data.get(cur_key)
            if not isinstance(target, list):
                raise ParseError(f"{where}:{n}: list item with no list key above it")
            target.append(item)
            continue

        if ":" not in stripped:
            raise ParseError(f"{where}:{n}: expected 'key: value', got {stripped!r}")
        key, _, rest = stripped.partition(":")
        key, rest = key.strip(), rest.strip()

        if indent == 0:
            cur_map = None
            if rest == "":
                data[key] = []          # block list or nested map; decided by next line
                cur_key = key
            else:
                data[key] = _scalar(rest)
                cur_key = key
        else:
            # Nested under the most recent empty key -> promote it to a map.
            parent = cur_map or cur_key
            if parent is None:
                raise ParseError(f"{where}:{n}: indented key with no parent")
            if not isinstance(data.get(parent), dict):
                if data.get(parent):
                    raise ParseError(f"{where}:{n}: {parent!r} is both a list and a map")
                data[parent] = {}
            cur_map = parent
            data[parent][key] = [] if rest == "" else _scalar(rest)
            cur_key = key
    return data, "\n".join(lines[end + 1:])


# --------------------------------------------------------------------------- #
# Task model
# --------------------------------------------------------------------------- #

@dataclass
class Task:
    id: str
    path: Path
    meta: dict
    body: str
    errors: list[str] = field(default_factory=list)

    @property
    def title(self) -> str:
        return str(self.meta.get("title", ""))

    @property
    def status(self) -> str:
        return str(self.meta.get("status", ""))

    @property
    def phase(self) -> int:
        p = self.meta.get("phase", 99)
        return p if isinstance(p, int) else 99

    @property
    def deps(self) -> list[str]:
        d = self.meta.get("depends_on") or []
        return [d] if isinstance(d, str) else list(d)

    @property
    def review(self) -> str:
        return str(self.meta.get("review", "none"))

    def docs(self, kind: str) -> list[str]:
        d = self.meta.get("docs") or {}
        if not isinstance(d, dict):
            return []
        v = d.get(kind) or []
        return [v] if isinstance(v, str) else list(v)

    def section(self, name: str) -> str:
        m = re.search(rf"^## {re.escape(name)}\s*$(.*?)(?=^## |\Z)", self.body,
                      re.MULTILINE | re.DOTALL)
        return m.group(1).strip() if m else ""

    def has_evidence(self) -> bool:
        body = self.section("Evidence")
        real = [ln for ln in body.splitlines()
                if ln.strip() and not ln.strip().startswith(("_", "<!--"))]
        return bool(real)


def load_tasks() -> list[Task]:
    if not TASKS_DIR.is_dir():
        return []
    tasks: list[Task] = []
    for path in sorted(TASKS_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        try:
            meta, body = parse_frontmatter(text, path.name)
        except ParseError as e:
            t = Task(id=path.stem, path=path, meta={}, body="")
            t.errors.append(str(e))
            tasks.append(t)
            continue
        tasks.append(Task(id=str(meta.get("id", path.stem)), path=path, meta=meta, body=body))
    return sorted(tasks, key=lambda t: (t.phase, t.id))


def index_by_id(tasks: list[Task]) -> dict[str, Task]:
    return {t.id: t for t in tasks}


def write_task(t: Task) -> None:
    """Rewrite a task file, preserving frontmatter key order and formatting."""
    text = t.path.read_text(encoding="utf-8")
    lines = text.splitlines()
    end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    status_at = -1
    for i in range(1, end):
        if lines[i].startswith("status:"):
            lines[i] = f"status: {t.meta['status']}"
            status_at = i
        elif lines[i].startswith("issue:") and t.meta.get("issue"):
            lines[i] = f"issue: {t.meta['issue']}"
    if t.meta.get("issue") and not any(l.startswith("issue:") for l in lines[1:end]):
        lines.insert(status_at + 1, f"issue: {t.meta['issue']}")
        end += 1
    t.path.write_text("\n".join(lines[: end + 1]) + "\n\n" + t.body.strip() + "\n",
                      encoding="utf-8")


# --------------------------------------------------------------------------- #
# Validation
# --------------------------------------------------------------------------- #

def find_cycles(tasks: list[Task]) -> list[list[str]]:
    idx = index_by_id(tasks)
    cycles: list[list[str]] = []
    WHITE, GREY, BLACK = 0, 1, 2
    color = {t.id: WHITE for t in tasks}

    def walk(node: str, stack: list[str]) -> None:
        color[node] = GREY
        stack.append(node)
        for dep in idx[node].deps if node in idx else []:
            if dep not in idx:
                continue
            if color[dep] == GREY:
                cycles.append(stack[stack.index(dep):] + [dep])
            elif color[dep] == WHITE:
                walk(dep, stack)
        stack.pop()
        color[node] = BLACK

    for t in tasks:
        if color[t.id] == WHITE:
            walk(t.id, [])
    return cycles


def validate(tasks: list[Task]) -> list[str]:
    errors: list[str] = []
    seen: dict[str, Task] = {}

    for t in tasks:
        errors.extend(f"{t.path.name}: {e}" for e in t.errors)
        if t.errors:
            continue
        if not ID_RE.match(t.id):
            errors.append(f"{t.path.name}: id {t.id!r} must look like TSC-AUTH-001")
        if t.path.stem != t.id:
            errors.append(f"{t.path.name}: filename must match id {t.id}")
        if t.id in seen:
            errors.append(f"Duplicate task id {t.id}")
        seen[t.id] = t
        if not t.title:
            errors.append(f"{t.id}: missing title")
        if t.status not in STATUSES:
            errors.append(f"{t.id}: invalid status {t.status!r} (use {', '.join(STATUSES)})")
        if t.review not in REVIEWS:
            errors.append(f"{t.id}: invalid review {t.review!r} (use {', '.join(REVIEWS)})")
        layer = str(t.meta.get("layer", ""))
        if layer and layer not in LAYERS:
            errors.append(f"{t.id}: invalid layer {layer!r} (use {', '.join(LAYERS)})")
        if not isinstance(t.meta.get("phase"), int):
            errors.append(f"{t.id}: phase must be an integer")
        for name in SECTIONS:
            if not re.search(rf"^## {re.escape(name)}\s*$", t.body, re.MULTILINE):
                errors.append(f"{t.id}: missing '## {name}' section")
        if not t.docs("write"):
            errors.append(f"{t.id}: docs.write must name at least one living doc")

    idx = seen
    for t in idx.values():
        for d in t.deps:
            if d not in idx:
                errors.append(f"{t.id}: unknown dependency {d}")
            elif t.status == "done" and idx[d].status != "done":
                errors.append(f"{t.id} is done but dependency {d} is {idx[d].status!r}")
        if t.status == "done":
            if not t.has_evidence():
                errors.append(f"{t.id} is done but its Evidence section is empty")
            for doc in t.docs("write"):
                if not (REPO_ROOT / doc).exists():
                    errors.append(f"{t.id} is done but declared doc {doc} does not exist")

    for cyc in find_cycles(list(idx.values())):
        errors.append("Dependency cycle: " + " -> ".join(cyc))

    in_progress = [t.id for t in idx.values() if t.status == "in-progress"]
    if len(in_progress) > 1:
        errors.append(f"More than one task in-progress: {', '.join(in_progress)}")

    return errors


# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #

def blockers_for(t: Task, idx: dict[str, Task]) -> list[str]:
    out = []
    for d in t.deps:
        dep = idx.get(d)
        if dep is None:
            out.append(f"{d} (unknown)")
        elif dep.status != "done":
            out.append(f"{d} ({dep.status})")
    for doc in t.docs("read"):
        if not (REPO_ROOT / doc).exists():
            out.append(f"missing contract doc {doc}")
    return out


def cmd_next(_a) -> int:
    tasks = load_tasks()
    idx = index_by_id(tasks)

    for t in tasks:
        if t.status == "in-progress":
            print(f"{t.id} - {t.title}\nStatus: in-progress\nAction: resume (work already started)")
            return 0

    for t in tasks:
        if t.status != "todo":
            continue
        if not blockers_for(t, idx):
            print(f"{t.id} - {t.title}")
            print(f"Status: todo\nAction: start\nPhase: {t.phase}  Layer: {t.meta.get('layer','-')}")
            print(f"Review gate: {t.review}")
            if t.meta.get("issue"):
                print(f"Issue: {t.meta['issue']}")
            print(f"Read first: {', '.join(t.docs('read')) or 'none'}")
            print(f"Must update: {', '.join(t.docs('write'))}")
            return 0

    review = [t.id for t in tasks if t.status == "needs-review"]
    blocked = [t for t in tasks if t.status in ("todo", "blocked")]
    if not blocked and not review:
        print("All tasks are done. Project complete.")
        return 0
    print("No task is actionable right now.")
    if review:
        print(f"  Waiting on human review: {', '.join(review)}")
    for t in blocked:
        print(f"  {t.id} [{t.status}] blocked by: {', '.join(blockers_for(t, idx)) or 'nothing'}")
    return 1


def cmd_list(a) -> int:
    tasks = load_tasks()
    if a.status:
        tasks = [t for t in tasks if t.status == a.status]
    if a.json:
        import json
        print(json.dumps([
            {"id": t.id, "title": t.title, "status": t.status, "phase": t.phase,
             "layer": t.meta.get("layer"), "depends_on": t.deps, "review": t.review,
             "docs_read": t.docs("read"), "docs_write": t.docs("write")}
            for t in tasks], indent=2))
        return 0
    for t in tasks:
        print(f"P{t.phase} {t.id:<16} {t.status:<13} {t.title[:44]:<44} "
              f"deps: {', '.join(t.deps) or 'none'}")
    return 0


def cmd_show(a) -> int:
    path = TASKS_DIR / f"{a.id}.md"
    if not path.exists():
        print(f"Unknown task: {a.id}", file=sys.stderr)
        return 1
    print(path.read_text(encoding="utf-8").rstrip())
    return 0


TEMPLATE = """---
id: {id}
title: {title}
area: {area}
phase: {phase}
layer: {layer}
status: todo
review: {review}
depends_on:{deps}
docs:
  read:{read}
  write:{write}
---

# {id} - {title}

## Objective

<!-- One paragraph: what capability exists after this task that did not before. -->

## Scope

**In:**

**Out:**

## Outputs

<!-- Concrete artifacts: files, endpoints, components, migrations. -->

## Acceptance criteria

<!-- Each line must be checkable by running something. Existence of a file is never
     sufficient on its own. -->

- [ ]

## Verification

```bash
# Exact commands the executor runs. Every one must pass before status -> done.
```

## Evidence

_None recorded yet._
"""


def _yaml_list(items: list[str]) -> str:
    return "".join(f"\n  - {i}" for i in items) if items else " []"


def _yaml_sublist(items: list[str]) -> str:
    return "".join(f"\n    - {i}" for i in items) if items else " []"


def cmd_new(a) -> int:
    if not ID_RE.match(a.id):
        print(f"Invalid id {a.id!r}; expected e.g. TSC-AUTH-001", file=sys.stderr)
        return 1
    path = TASKS_DIR / f"{a.id}.md"
    if path.exists():
        print(f"Refusing to overwrite existing task {a.id}", file=sys.stderr)
        return 1
    TASKS_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(TEMPLATE.format(
        id=a.id, title=a.title, area=a.id.split("-")[1], phase=a.phase, layer=a.layer,
        review=a.review, deps=_yaml_list(a.depends_on or []),
        read=_yaml_sublist(a.read or []), write=_yaml_sublist(a.write or []),
    ), encoding="utf-8")
    print(f"Created {path.relative_to(REPO_ROOT)} — fill in the prose sections, then run "
          f"'tasks.py validate'.")
    return 0


def cmd_status(a) -> int:
    tasks = load_tasks()
    idx = index_by_id(tasks)
    t = idx.get(a.id)
    if t is None:
        print(f"Unknown task: {a.id}", file=sys.stderr)
        return 1
    new = a.status
    if new not in STATUSES:
        print(f"Invalid status {new!r}; use {', '.join(STATUSES)}", file=sys.stderr)
        return 1

    if new == "in-progress":
        others = [o.id for o in tasks if o.status == "in-progress" and o.id != t.id]
        if others:
            print(f"Refusing: {', '.join(others)} already in-progress. One task at a time.",
                  file=sys.stderr)
            return 1
        blockers = blockers_for(t, idx)
        if blockers:
            print(f"Refusing to start {t.id}: {', '.join(blockers)}", file=sys.stderr)
            return 1

    if new == "done":
        blockers = [d for d in t.deps if idx.get(d) is None or idx[d].status != "done"]
        if blockers:
            print(f"Refusing: dependencies not done: {', '.join(blockers)}", file=sys.stderr)
            return 1
        if not t.has_evidence():
            print(f"Refusing: {t.id} has no evidence. Record it with "
                  f"'tasks.py evidence {t.id} \"...\"' first.", file=sys.stderr)
            return 1
        missing = [d for d in t.docs("write") if not (REPO_ROOT / d).exists()]
        if missing:
            print(f"Refusing: declared living docs not written: {', '.join(missing)}",
                  file=sys.stderr)
            return 1
        if t.review == "human" and t.status != "needs-review" and not a.approved:
            print(f"Refusing: {t.id} has a human review gate. Move it to 'needs-review', "
                  f"and re-run with --approved once a human has confirmed.", file=sys.stderr)
            return 1

    old = t.status
    t.meta["status"] = new
    write_task(t)
    cmd_index(None)
    print(f"{t.id}: {old} -> {new}")
    return 0


def cmd_evidence(a) -> int:
    t = index_by_id(load_tasks()).get(a.id)
    if t is None:
        print(f"Unknown task: {a.id}", file=sys.stderr)
        return 1
    stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    body = t.body
    if "_None recorded yet._" in body:
        body = body.replace("_None recorded yet._", "")
    body = body.rstrip() + f"\n\n- `{stamp}` {a.text}\n"
    t.body = body
    write_task(t)
    print(f"{t.id}: evidence recorded.")
    return 0


def cmd_link(a) -> int:
    t = index_by_id(load_tasks()).get(a.id)
    if t is None:
        print(f"Unknown task: {a.id}", file=sys.stderr)
        return 1
    t.meta["issue"] = a.url
    write_task(t)
    cmd_index(None)
    print(f"{t.id}: linked to {a.url}")
    return 0


def cmd_verify(a) -> int:
    t = index_by_id(load_tasks()).get(a.id)
    if t is None:
        print(f"Unknown task: {a.id}", file=sys.stderr)
        return 1
    block = re.search(r"```(?:bash|sh)\n(.*?)```", t.section("Verification"), re.DOTALL)
    if not block:
        print(f"{t.id}: no fenced command block in ## Verification", file=sys.stderr)
        return 1
    script = block.group(1)
    if not a.run:
        print(script.rstrip())
        return 0
    print(f"--- running verification for {t.id} ---")
    return subprocess.run(["bash", "-e", "-c", script], cwd=REPO_ROOT).returncode


def cmd_validate(_a) -> int:
    errors = validate(load_tasks())
    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1
    tasks = load_tasks()
    counts = {s: sum(1 for t in tasks if t.status == s) for s in STATUSES}
    print("tasks OK: " + ", ".join(f"{v} {k}" for k, v in counts.items() if v))
    return 0


def issue_cell(t: Task) -> str:
    url = str(t.meta.get("issue", ""))
    return f"[#{url.rstrip('/').rsplit('/', 1)[-1]}]({url})" if url else "—"


def cmd_index(_a) -> int:
    tasks = load_tasks()
    counts = {s: sum(1 for t in tasks if t.status == s) for s in STATUSES}
    total = len(tasks) or 1
    mark = {"done": "x", "in-progress": "~", "needs-review": "?", "blocked": "!", "todo": " "}
    out = [
        "<!-- GENERATED by scripts/tasks.py index. Do not edit by hand. -->",
        "",
        "# Implementation tasks",
        "",
        f"{counts['done']}/{len(tasks)} done ({100 * counts['done'] // total}%) — "
        + ", ".join(f"{v} {k}" for k, v in counts.items() if v),
        "",
        "Each task lives in [`docs/tasks/tasks/`](./tasks/). Statuses and evidence are",
        "written only by `scripts/tasks.py`; the format is defined in",
        "`.claude/skills/task-framework/SKILL.md`.",
        "",
    ]
    for phase in sorted({t.phase for t in tasks}):
        out += [f"## Phase {phase}", "",
                "| | Task | Title | Layer | Depends on | Living doc | Issue |",
                "|---|---|---|---|---|---|---|"]
        for t in [t for t in tasks if t.phase == phase]:
            docs = ", ".join(f"[{Path(d).name}](../../{d})" for d in t.docs("write")) or "—"
            out.append(
                f"| `{mark.get(t.status, '?')}` | [{t.id}](./tasks/{t.id}.md) | {t.title} "
                f"| {t.meta.get('layer', '—')} | {', '.join(t.deps) or '—'} | {docs} "
                f"| {issue_cell(t)} |")
        out.append("")
    INDEX_FILE.write_text("\n".join(out), encoding="utf-8")
    return 0


def cmd_graph(_a) -> int:
    tasks = load_tasks()
    print("```mermaid\ngraph TD")
    for t in tasks:
        print(f'  {t.id.replace("-", "_")}["{t.id}<br/>{t.title[:30]}"]')
        for d in t.deps:
            print(f'  {d.replace("-", "_")} --> {t.id.replace("-", "_")}')
    print("```")
    return 0


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("next").set_defaults(fn=cmd_next)

    pl = sub.add_parser("list"); pl.add_argument("--status", choices=STATUSES)
    pl.add_argument("--json", action="store_true"); pl.set_defaults(fn=cmd_list)

    ps = sub.add_parser("show"); ps.add_argument("id"); ps.set_defaults(fn=cmd_show)

    pn = sub.add_parser("new")
    pn.add_argument("id"); pn.add_argument("title")
    pn.add_argument("--phase", type=int, required=True)
    pn.add_argument("--layer", choices=LAYERS, required=True)
    pn.add_argument("--review", choices=REVIEWS, default="none")
    pn.add_argument("--depends-on", nargs="*", dest="depends_on")
    pn.add_argument("--read", nargs="*"); pn.add_argument("--write", nargs="*")
    pn.set_defaults(fn=cmd_new)

    pt = sub.add_parser("status"); pt.add_argument("id"); pt.add_argument("status")
    pt.add_argument("--approved", action="store_true",
                    help="human review gate has been approved")
    pt.set_defaults(fn=cmd_status)

    pe = sub.add_parser("evidence"); pe.add_argument("id"); pe.add_argument("text")
    pe.set_defaults(fn=cmd_evidence)

    pk = sub.add_parser("link"); pk.add_argument("id"); pk.add_argument("url")
    pk.set_defaults(fn=cmd_link)

    pv = sub.add_parser("verify"); pv.add_argument("id")
    pv.add_argument("--run", action="store_true"); pv.set_defaults(fn=cmd_verify)

    sub.add_parser("validate").set_defaults(fn=cmd_validate)
    sub.add_parser("index").set_defaults(fn=cmd_index)
    sub.add_parser("graph").set_defaults(fn=cmd_graph)

    a = p.parse_args(argv[1:])
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
