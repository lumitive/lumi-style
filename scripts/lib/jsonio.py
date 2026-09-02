#!/usr/bin/env python3
"""Writing a JSON file this repository tracks: the way the file already is.

WHY THIS EXISTS. Twenty-six `json.dump` sites, `indent=1` at twelve of them
and `indent=2` at fourteen, and no shared writer — so whichever a script or a
one-off heredoc happened to pick, the file came back re-indented if it had
been the other. Four times in three releases (see `check/surgical_diff.py`'s
docstring for the numbers) a commit carried thousands of changed lines of
which a handful were the change, and one of the four put the previous one
back. `surgical_diff.py` catches the commit; this removes the cause for
anything that writes through it.

ONE RULE. `dump_json` reads the indent the file already has and writes with
it. A new file gets 1 — the indent fourteen of the twenty-two hand-written
JSON files in this tree use, chosen because it is the majority and not because
it is better. An explicit `indent=` wins, for the caller that knows.

Not a formatter: nothing here rewrites a file that is not being written anyway,
which is what AG-4 refused.
"""
from __future__ import annotations

import json
import os
import pathlib
from typing import Any

DEFAULT_INDENT = 1


def detect_indent(text: str) -> int | None:
    """-> the indent width of a pretty-printed JSON text, or None for compact.

    The first line after the opening one that carries content says it: its
    leading spaces are the unit. A single-line document has no indented line
    and is compact.
    """
    for line in text.split("\n")[1:]:
        if line.strip():
            return len(line) - len(line.lstrip(" "))
    return None


def load_json(path: pathlib.Path | str) -> Any:
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def dump_json(path: pathlib.Path | str, obj: Any, *, indent: int | None = None,
              ensure_ascii: bool = False, sort_keys: bool = False,
              atomic: bool = False) -> int:
    """Write `obj` to `path` with the indent `path` already has. -> the indent used.

    `indent=None` (the default) means "look at the file"; a file that does not
    exist yet gets DEFAULT_INDENT. Pass an int to override, or 0 for compact.
    The file ends in one newline, which is what every tracked JSON here does.

    `atomic=True` writes a sibling temp file and `os.replace`s it into place —
    the shape `trace.py` needed for a record that is rewritten whole on every
    phase stop, where a crash mid-write used to leave a truncated file that
    every later command died on. The indent is still read from `path`, never
    from the temp file, which does not exist yet.
    """
    path = pathlib.Path(path)
    if indent is None:
        indent = DEFAULT_INDENT
        if path.exists():
            found = detect_indent(path.read_text(encoding="utf-8"))
            indent = found if found is not None else 0
    if indent == 0:
        text = json.dumps(obj, ensure_ascii=ensure_ascii, sort_keys=sort_keys,
                          separators=(",", ":"))
    else:
        text = json.dumps(obj, indent=indent, ensure_ascii=ensure_ascii,
                          sort_keys=sort_keys)
    path.parent.mkdir(parents=True, exist_ok=True)
    if atomic:
        tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
        tmp.write_text(text + "\n", encoding="utf-8")
        os.replace(tmp, path)
    else:
        path.write_text(text + "\n", encoding="utf-8")
    return indent
