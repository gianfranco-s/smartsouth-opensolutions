#!/usr/bin/env python3
"""Collapse manual line-wraps in markdown to one line per paragraph/bullet.

Fenced code blocks (```...```, including Mermaid diagrams) and table rows
(lines starting with |) are left untouched. Headings and list items each
start a new line; any plain text immediately following gets folded into
that line with a single space, so a paragraph hand-wrapped across several
source lines becomes one long line.

Usage:
    unwrap_md.py file1.md [file2.md ...]

Edits files in place.
"""
import re, sys

def unwrap(text):
    lines = text.split("\n")
    out = []
    buf = None  # current paragraph/list-item buffer
    in_fence = False

    def flush():
        nonlocal buf
        if buf is not None:
            out.append(buf)
            buf = None

    for line in lines:
        stripped = line.rstrip("\n")

        # fenced code block toggle (```...```)
        if re.match(r'^\s*```', stripped):
            flush()
            out.append(stripped)
            in_fence = not in_fence
            continue

        if in_fence:
            out.append(stripped)
            continue

        if stripped.strip() == "":
            flush()
            out.append("")
            continue

        # table row - passthrough as its own line, never buffered/merged
        if stripped.lstrip().startswith("|"):
            flush()
            out.append(stripped)
            continue

        # heading
        if re.match(r'^#{1,6}\s', stripped):
            flush()
            out.append(stripped)
            continue

        # list item start (bullet or numbered), any indent level
        if re.match(r'^\s*([-*]|\d+\.)\s', stripped):
            flush()
            buf = stripped
            continue

        # continuation line -> merge into current buffer with a space
        if buf is not None:
            buf = buf.rstrip() + " " + stripped.strip()
        else:
            buf = stripped.strip()

    flush()
    return "\n".join(out)

if len(sys.argv) < 2:
    print(__doc__)
    sys.exit(1)

for path in sys.argv[1:]:
    with open(path, encoding="utf-8") as f:
        content = f.read()
    result = unwrap(content)
    with open(path, "w", encoding="utf-8") as f:
        f.write(result)
    print(f"unwrapped {path}")
