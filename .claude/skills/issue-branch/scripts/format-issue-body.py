#!/usr/bin/env python3
"""Render leading YAML frontmatter in an issue body as a compact markdown header.

Read on stdin, written on stdout. A body without frontmatter passes through
unchanged. Only the flat subset the task ledger uses is understood (scalars,
lists of scalars, one level of nesting); anything else is left as a plain
`key: value` line rather than dropped.
"""
import re
import sys

SKIP = {"title", "issue"}  # the issue title and URL are already on the issue itself


def split_frontmatter(text):
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---", 3)
    if end == -1:
        return None, text
    nl = text.find("\n", end + 1)
    body = text[nl + 1:] if nl != -1 else ""
    return text[4:end], body.lstrip("\n")


def parse(fm):
    """Return [(key, value)] where value is str | list[str] | list[(k, list[str])]."""
    items, stack = [], []
    for raw in fm.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        line = raw.strip()
        if line.startswith("- "):
            target = stack[-1][1] if stack else (items[-1][1] if items else None)
            if isinstance(target, list):
                target.append(line[2:].strip())
            continue
        while stack and indent <= stack[-1][0]:
            stack.pop()
        key, _, value = line.partition(":")
        key, value = key.strip(), value.strip()
        entry = (key, value if value else [])
        if stack:
            stack[-1][1].append(entry) if isinstance(stack[-1][1], list) else None
        else:
            items.append(entry)
        if not value:
            stack.append((indent, entry[1]))
    return items


def fmt_list(values):
    return ", ".join(f"`{v}`" for v in values)


def render(items):
    inline, blocks = [], []
    for key, value in items:
        if key in SKIP:
            continue
        label = key.replace("_", " ").capitalize()
        if isinstance(value, str):
            inline.append(f"**{label}:** {value}")
        elif value and all(isinstance(v, tuple) for v in value):
            for sub, subvals in value:
                if subvals:
                    blocks.append(f"**{label} to {sub}:** {fmt_list(subvals)}")
        elif value:
            blocks.append(f"**{label}:** {fmt_list(value)}")
    out = []
    if inline:
        out.append(" · ".join(inline))
    out.extend(blocks)
    return "\n\n".join(out)


def main():
    text = sys.stdin.read()
    fm, body = split_frontmatter(text)
    if fm is None:
        sys.stdout.write(text)
        return
    # The H1 repeats the issue title on the issue page.
    body = re.sub(r"\A#\s+[^\n]*\n+", "", body)
    header = render(parse(fm))
    sys.stdout.write(f"{header}\n\n---\n\n{body}" if header else body)


if __name__ == "__main__":
    main()
