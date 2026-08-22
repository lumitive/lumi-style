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

# --- scripts path bootstrap (canonical; the bootstrap guard enforces this) ---
import pathlib as _bs_pathlib  # noqa: E402
import re
import sys as _bs_sys  # noqa: E402

_SCRIPTS_ROOT = next(p for p in _bs_pathlib.Path(__file__).resolve().parents
                     if p.name == "scripts")
for _sub in ("lib", "render", "check", "build", "ops", ""):
    _p = str(_SCRIPTS_ROOT / _sub) if _sub else str(_SCRIPTS_ROOT)
    if _p not in _bs_sys.path:
        _bs_sys.path.append(_p)
del _bs_pathlib, _bs_sys, _SCRIPTS_ROOT, _sub, _p

import pathlib  # noqa: E402

import gate_registry  # noqa: E402

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
    not demanded of a document that never had it.

    **BY NAME, NEVER BY PREFIX.** This read the id prefix — `D38_` — and
    inherited a whole family's classification onto every row in it. Two rows
    whose own targets say `reported` were counted as gates
    (`D37_caption_name_len`, `D38_agenda_run_echo`), and one row that gates was
    invisible because `M4zh_banned_hits` does not match the id pattern, which left
    the Chinese banned-phrase gate out of `run_conformance`'s `all-gating`
    require set entirely. A family is a family and a verdict is a verdict;
    `evals/gates.json` now carries both, and this asks it by name.
    """
    # NOT `except: return set()`. An empty gate set reads as "nothing gates" —
    # `run_conformance` builds its `all-gating` require set from this, so an
    # unreadable register silently stopped demanding every design and prose
    # verdict and scored a deck on the layout ones alone. Three functions in
    # this module had three different answers to the same broken file; they all
    # raise now, because a register nobody could read is a fact about the run,
    # not a verdict about the document.
    gate = gate_registry.gates(root)
    return {name for name in verdicts if name in gate}

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
    """-> everything the RULE REGISTER may cite as a gate.

    Metric IDS for design and prose (`D40`), verdict NAMES for layout
    (`collision`) — because that is how the two vocabularies are spelled: a
    rule cites the metric, and a layout verdict has no id to cite. `D38` is a
    gating id here even though `D38_agenda_run_echo` only reports, because the
    family does gate and a rule citing `D38` is citing that.

    The row-level question — *does THIS verdict fail a document* — is
    `gating_metrics`, and it works by name for the reason its docstring gives.
    Two questions, two functions; one union pretending to answer both is what
    made `check_rule_coverage` demand a rule for every row name.

    Sourced from `evals/gates.json`, held to the checkers by `check_repo`'s
    `gate declarations` guard.
    """
    return _ids_and_layout_names(gate_registry.gates(root))


# `M4zh` IS AN ID. The pattern this replaces was `([DM]\d+)_`, which cannot
# match `M4zh_banned_hits` — so the Chinese banned-phrase gate had no citable id
# and the rule register could not name it. Two rules quoting the Chinese list
# were filed under `M4`, the ENGLISH metric, and nothing could say so.
METRIC_ID = re.compile(r"([DM]\d+(?:zh)?)_")


def _ids_and_layout_names(names: set[str]) -> set[str]:
    """-> the vocabulary a rule may cite: metric ids for D/M, names for layout."""
    out = set()
    for n in names:
        m = METRIC_ID.match(n)
        out.add(m.group(1) if m else n)
    return out


def every_metric_name(root: pathlib.Path | None = None) -> set[str]:
    """-> everything the rule register may cite at all, gating or not.

    Raises rather than returning the empty set, for the reason above: an empty
    answer here reads as "no metric exists", and `check_rule_coverage` would
    then stop demanding a rule for any of them.
    """
    return _ids_and_layout_names(set(gate_registry.load(root)))
