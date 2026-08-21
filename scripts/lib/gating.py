#!/usr/bin/env python3
"""Which metrics GATE — read from the checkers, never listed by hand.

A checker decides this in one place: the target string on a row carries
"(gates)" if and only if that metric fails the run. Two consumers need the
answer and neither may keep its own copy — `check_repo.check_gating_claims`
holds the package's prose to it, and `run_conformance` holds a conformance
deliverable to it.

**Why the second consumer exists.** T1's `require` block named six metrics by
hand: D12, D14, D15, M4, collision, content_hidden. Ten design metrics gate and
fifteen layout verdicts do, so a deck could fail D19, D1, D3, D4 and eleven
layout checks and still be scored `pass` — which is what the owner found by
opening one on 2026-08-21. A hand-written subset of a machine-readable set is
the drift this repository has fixed twenty-six times, and here it was not even
drift: the list was short the day it was written.

`ast`, never `import`: the authority is the source of the row table, and
importing a checker to ask it would run a checker. Both scripts spell the table
differently — one appends tuples, the other returns a list literal — so this
walks every tuple rather than keying on either shape.
"""
from __future__ import annotations

import ast
import pathlib
import re

ROOT = next(p for p in pathlib.Path(__file__).resolve().parents
            if (p / "SKILL.md").exists())

# One file per metric prefix. A prefix with no authority here cannot be asked
# about, which is better than an answer nobody can trace.
METRIC_AUTHORITIES = {
    "D": "scripts/check/check_design.py",
    "M": "scripts/check/check_prose.py",
}


def metric_ids(prefix: str, root: pathlib.Path | None = None
               ) -> tuple[set[str], set[str]]:
    """-> (every id that produces a verdict row, the subset whose target gates).

    `root` is the caller's, not this module's. check_repo's guard tests build a
    synthetic tree and point the guard at it; a module that resolved the path
    from its own location read the REAL checkers instead and the tests passed
    against the wrong files — a guard test that cannot control its input is
    testing the repository, not the guard.
    """
    path = (root or ROOT) / METRIC_AUTHORITIES[prefix]
    tree = ast.parse(path.read_text(encoding="utf-8"))
    ids: set[str] = set()
    gating: set[str] = set()
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Tuple) and len(node.elts) >= 3):
            continue
        name, target = node.elts[0], node.elts[2]
        if not (isinstance(name, ast.Constant) and isinstance(name.value, str)):
            continue
        match = re.match(rf"({prefix}\d+)_", name.value)
        if not match:
            continue
        ids.add(match.group(1))
        if isinstance(target, ast.Constant) and "gates" in str(target.value):
            gating.add(match.group(1))
    return ids, gating


def gating_metrics(verdicts: dict, root: pathlib.Path | None = None) -> set[str]:
    """-> the subset of `verdicts` this package gates a DELIVERABLE on.

    Keyed on what the report actually returned, so a metric that did not run is
    not demanded of a document that never had it. Three sources, one rule each:

    * design and prose — the id prefix carries "(gates)" in its row table.
    * layout — every key it returns under `--deliverable` is a gating verdict by
      construction; `inspect_layout` decides that in `deliverable_verdicts` and
      reports nothing else there.

    A verdict whose prefix has no authority (the layout names, which are words
    rather than ids) falls into the third case, which is why the layout report
    must be passed on its own rather than merged into one dict first.
    """
    gate: set[str] = set()
    for prefix in METRIC_AUTHORITIES:
        try:
            gate |= metric_ids(prefix, root)[1]
        except (OSError, SyntaxError):
            continue
    out = set()
    for name in verdicts:
        head = name.split("_", 1)[0]
        if head in gate:
            out.add(name)
    return out

def layout_verdicts(root: pathlib.Path | None = None) -> set[str]:
    """-> every verdict name `inspect_layout.deliverable_verdicts` emits.

    All of them gate: that function is the deliverable gate set by construction
    and reports nothing else. Read from its `add(...)` calls rather than listed
    here, for the reason the rest of this module exists — CLAUDE.md has counted
    this list wrong in four files at once.

    Walks only the body of that one function, so an `add(` elsewhere in the file
    cannot smuggle a name into the gate set.
    """
    path = (root or ROOT) / "scripts/check/inspect_layout.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not (isinstance(node, ast.FunctionDef)
                and node.name == "deliverable_verdicts"):
            continue
        names = {c.args[0].value for c in ast.walk(node)
                 if isinstance(c, ast.Call)
                 and isinstance(c.func, ast.Name) and c.func.id == "add"
                 and c.args and isinstance(c.args[0], ast.Constant)
                 and isinstance(c.args[0].value, str)}
        # TWO SPELLINGS, and reading only the first one lost a verdict. Most
        # findings go through `add(...)`; `datum` and `role_split` are written
        # straight into the dict because they come from the consistency audit
        # rather than from the page rows. A reader keyed on the common shape
        # reported 19 gates where there are 20 — the exact class of mistake
        # convention 15 is about, found by looking at the material.
        names |= {t.slice.value for a in ast.walk(node)
                  if isinstance(a, ast.Assign)
                  for t in a.targets
                  if isinstance(t, ast.Subscript)
                  and isinstance(t.value, ast.Name) and t.value.id == "out"
                  and isinstance(t.slice, ast.Constant)
                  and isinstance(t.slice.value, str)}
        return names
    return set()


def every_gating_name(root: pathlib.Path | None = None) -> set[str]:
    """-> every metric id and verdict name that can fail a deliverable.

    The union the rule register is held to: a gate absent from here cannot be
    cited, and a gate here that no rule cites is a threshold with no rule behind
    it, which `check_rule_coverage.py` reports as a finding in its own right.
    """
    names: set[str] = set()
    for prefix in METRIC_AUTHORITIES:
        names |= metric_ids(prefix, root)[1]
    return names | layout_verdicts(root)


def every_metric_name(root: pathlib.Path | None = None) -> set[str]:
    """-> every metric id and verdict name a checker can emit, gating or not."""
    names: set[str] = set()
    for prefix in METRIC_AUTHORITIES:
        names |= metric_ids(prefix, root)[0]
    return names | layout_verdicts(root)
