#!/usr/bin/env python3
"""The trace schema — one definition, imported by both the writer and the guard.

It lives in scripts/lib/ rather than beside the CLI for a specific reason: the
emergency-merge path runs a trusted closure of checker code, and a guard that
reached into scripts/ops/ would make the emergency run execute the pull
request's own copy of the thing it is checking. A shared definition also keeps
this repository's `no shadow math` rule — a second copy of a field list is the
defect most of its releases exist to fix.
"""
from __future__ import annotations

# --- scripts path bootstrap (canonical; the bootstrap guard enforces this) ---
# Bare-name sibling imports must resolve from any drawer depth: walk up to
# the scripts/ root and APPEND it and its drawers to sys.path — append,
# never insert(0), so the standard library and the caller's environment
# always win. Drawer order is lib-first and the scripts ROOT LAST on
# purpose: the emergency path overwrites a PR's lib/ files with trusted
# copies, and lib-first means a file PLANTED at the scripts root can never
# outrank them (the shadowing the PR #92 review demonstrated).
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

from deliverable_registry import (  # noqa: E402 — after the bootstrap
    GENRES,  # one axis, one definition
    STAGE_OF,  # composition -> stage, so a trace cannot contradict a body
    STORYLINES,  # the other axis, one definition
)

ENUMS = {
    "source": ("build", "conformance", "fixture"),
    "storyline": STORYLINES,
    # IMPORTED, not retyped. This was a sixth literal copy of the genre
    # vocabulary and `check_genre_vocabulary` inspected a fixed seven-file list
    # that did not include this one — so adding a genre would have left the
    # newest genre the only one that could not be traced. Sharing the tuple
    # makes the drift impossible instead of checked.
    "genre": GENRES,
    "entry_path": ("A", "B"),
    "stage": ("discussion", "outline", "build", "checks"),
    # Every stage a composition maps to, plus the ones that belong to no
    # composition. Derived, so a new composition cannot become untraceable.
    "geometry": tuple(dict.fromkeys((*STAGE_OF.values(), "laptop"))),
}
PHASES = ENUMS["stage"]
CLAUSE = re.compile(r"^P-[1-9]\d*$")
ID = re.compile(r"^t-[0-9a-f]{12}$")

FIELDS: dict[str, object] = {
    "trace_id": str, "opened_at": str, "closed_at": (str, type(None)),
    "source": str, "skill_version": str, "genre": str, "storyline": str,
    "entry_path": str, "outline_reviewed": bool,
    "titles_changed_after_approval": int, "geometry": (str, type(None)),
    "model": (str, type(None)), "effort": (str, type(None)),
    "agent": (str, type(None)), "pages": int, "content_pages": int,
    "phase_seconds": dict, "input_tokens": (int, type(None)),
    "output_tokens": (int, type(None)), "cost_usd": (float, int, type(None)),
    "gates": dict, "graded": dict, "thresholds": dict,
    "principle_yields": list, "refused_to_emit": (dict, type(None)),
    "corpus_id": (str, type(None)), "review_ref": (str, type(None)),
}


def validate(rec):
    """Return a list of reasons this record is not a legal trace."""
    errors = []
    unknown = sorted(set(rec) - set(FIELDS))
    if unknown:
        errors.append(f"unknown field(s) {unknown} — the schema is closed; a trace "
                      f"carries no free-form data")
    for key, typ in FIELDS.items():
        if key not in rec:
            errors.append(f"missing field {key}")
        elif not isinstance(rec[key], typ):  # type: ignore[arg-type]
            errors.append(f"{key}: expected {typ}, got {type(rec[key]).__name__}")
    for key, allowed in ENUMS.items():
        if key in rec and rec[key] is not None and key != "stage" and rec[key] not in allowed:
            errors.append(f"{key}={rec[key]!r} is outside the vocabulary {allowed}")
    if "trace_id" in rec and not ID.match(str(rec["trace_id"])):
        errors.append(f"trace_id {rec['trace_id']!r} is not t-<12 hex>")
    for phase in rec.get("phase_seconds", {}):
        if phase not in PHASES:
            errors.append(f"phase_seconds has phase {phase!r}, not one of {PHASES}")
    for y in rec.get("principle_yields", []):
        if not isinstance(y, dict) or set(y) != {"yielded", "for", "stage"}:
            errors.append(f"principle_yields entry {y!r} must be "
                          f"{{yielded, for, stage}} and nothing else")
            continue
        if not CLAUSE.match(y["yielded"]) or not CLAUSE.match(y["for"]):
            errors.append(f"principle_yields entry {y!r} names a non-clause")
        if y["stage"] not in PHASES:
            errors.append(f"principle_yields entry {y!r} names an unknown stage")
    r = rec.get("refused_to_emit")
    if r is not None:
        if set(r) != {"clauses", "stage"}:
            errors.append("refused_to_emit carries {clauses, stage} and nothing else — "
                          "the reasoning goes to the debug log, never here")
        else:
            if not all(CLAUSE.match(c) for c in r["clauses"]):
                errors.append(f"refused_to_emit names a non-clause: {r['clauses']}")
            if r["stage"] not in PHASES:
                errors.append(f"refused_to_emit stage {r['stage']!r} is unknown")
    return errors
