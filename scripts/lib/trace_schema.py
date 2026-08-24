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
    # The reasoning tier a build ran at. Closed, because K1's model matrix is
    # model tiers by effort levels and a free-string column cannot be grouped.
    # `model` deliberately stays free text one line up: model names rot, and an
    # enum of them is a maintenance tax with no defect behind it.
    #
    # **The levels are the CLIs', not this repository's, and they grew.**
    # `claude --effort` documents low|medium|high|xhigh|max; Cursor spells its
    # top level `xhigh` inside the model id; `hermes --reasoning` adds none,
    # minimal and ultra beyond these. 0.1.554 widened the harness to match and
    # did not sweep here, so this tuple stayed three long — and the cost of
    # that is measured: on 2026-08-22 the only agent that passed all three
    # conformance tasks tried to close its trace with `--effort xhigh`,
    # argparse rejected the value, and the run contributed no row to the cost
    # board it was driven to fill. This is the ONE definition; `run_conformance`
    # imports it rather than retyping it, on the reasoning the `genre` note
    # above gives — a shared tuple makes the drift impossible instead of
    # checked.
    "effort": ("low", "medium", "high", "xhigh", "max"),
    "stage": ("discussion", "outline", "build", "checks"),
    # Every stage a composition maps to, plus the ones that belong to no
    # composition. Derived, so a new composition cannot become untraceable.
    "geometry": tuple(dict.fromkeys((*STAGE_OF.values(), "laptop"))),
}
PHASES = ENUMS["stage"]
CLAUSE = re.compile(r"^P-[1-9]\d*$")
ID = re.compile(r"^t-[0-9a-f]{12}$")

# What a `shape` reading may name. A closed vocabulary for the same reason the
# trace's own field list is closed: a store anyone can add a key to is a store
# nobody can read across.
SHAPE_KEYS = ("layout_top_share", "layout_kinds", "visual_share_median",
              "repeated_skeleton_pages", "figures",
              "move_skeleton_clashes", "text_only_figures")
# A shape reading is a number; `geometry` says which rendering the rendered
# ones came from, and a median with no geometry beside it is not comparable
# across documents.
SHAPE_TEXT_KEYS = ("geometry",)

# Fields introduced after traces were already being stored. Absent is legal;
# present must still be the declared type.
ADDED_LATER = frozenset({"shape"})

FIELDS: dict[str, object] = {
    "trace_id": str, "opened_at": str, "closed_at": (str, type(None)),
    "source": str, "skill_version": str, "genre": str, "storyline": str,
    "entry_path": str, "outline_reviewed": bool,
    # WHAT THE BUILD WAS DRIVEN BY, and what version that thing was written
    # against. `skill_version` is read from SKILL.md at open, so it always
    # equals HEAD and can never be stale — which is why a replay of a frozen
    # recipe used to produce a record indistinguishable from a current build.
    # Both are None on a build with no recipe to point at (a path-A document
    # composed from a conversation), and None is not "current".
    "recipe_hash": (str, type(None)), "recipe_version": (str, type(None)),
    "titles_changed_after_approval": int, "geometry": (str, type(None)),
    "model": (str, type(None)), "effort": (str, type(None)),
    "agent": (str, type(None)), "pages": int, "content_pages": int,
    "phase_seconds": dict, "input_tokens": (int, type(None)),
    # `cost_usd` was here and is gone. It is tokens times a price, and a
    # stored derivation goes stale the day the price does — while the tokens
    # it derives from are right there. Prefer deleting the number: the board
    # computes cost at report time from a dated price table when one exists.
    "output_tokens": (int, type(None)),
    "gates": dict, "graded": dict, "thresholds": dict,
    # THE DOCUMENT'S SHAPE, so the corpus can grow its own baseline.
    #
    # `gates` and `graded` record whether each metric passed; none of them
    # records what the document LOOKED like. GAP-024 and GAP-025 have both been
    # open since 0.1.543 for want of a second measured document, and the reason
    # a second one was never to hand is that no build kept its numbers — every
    # comparison had to be re-measured by opening old files, which is why the
    # one attempt at a bar (0.1.592) was drafted from five documents found by
    # hand and refuted by a sixth.
    #
    # Descriptive, never a threshold. A reading here says what this build was,
    # not whether it was good; `ledger.py` reports the distribution and a person
    # reads it. That is the whole difference between a corpus that grows and a
    # number somebody invented.
    "shape": dict,
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
            # A FIELD ADDED AFTER RECORDS EXISTED IS OPTIONAL. `shape` arrived
            # at 0.1.595 with 135 traces already stored; requiring it would
            # redden every one of them for having been written before it
            # existed, which teaches nothing and trains people to ignore the
            # guard. New records get it from `cmd_open`; old ones stay as they
            # were written, which is what a record is for.
            if key in ADDED_LATER:
                continue
            errors.append(f"missing field {key}")
        elif rec[key] is None and key in ADDED_LATER:
            # For a field added after records existed, a null says exactly what
            # an absent key says: not recorded. Refusing one while allowing the
            # other would fail a record for how its writer spelled "nothing".
            continue
        elif not isinstance(rec[key], typ):  # type: ignore[arg-type]
            errors.append(f"{key}: expected {typ}, got {type(rec[key]).__name__}")
    for key, allowed in ENUMS.items():
        if key in rec and rec[key] is not None and key != "stage" and rec[key] not in allowed:
            errors.append(f"{key}={rec[key]!r} is outside the vocabulary {allowed}")
    if "trace_id" in rec and not ID.match(str(rec["trace_id"])):
        errors.append(f"trace_id {rec['trace_id']!r} is not t-<12 hex>")
    # ONLY WHEN IT IS A DICT. The type check above APPENDS an error and does
    # not return, so a truthy non-dict fell through to `.items()` and raised —
    # `[]` reported cleanly while `[1, 2]` crashed, and the crash took
    # `check_repo`'s guard with it, so the tree could not be checked at all.
    # A validator that raises instead of reporting cannot name the bad record.
    for key, value in (rec.get("shape") if isinstance(rec.get("shape"), dict)
                       else {}).items():
        if key in SHAPE_TEXT_KEYS:
            if not isinstance(value, str) or not value:
                errors.append(f"shape.{key} is {value!r}; expected a name")
            continue
        if key not in SHAPE_KEYS:
            errors.append(f"shape.{key} is not one of "
                          f"{', '.join(SHAPE_KEYS + SHAPE_TEXT_KEYS)}")
        elif isinstance(value, bool) or not isinstance(value, (int, float)):
            errors.append(f"shape.{key} is {value!r}; a shape reading is a "
                          f"number or the key is absent — there is no field "
                          f"for 'not measured' because an absent key IS that")
    for phase, seconds in rec.get("phase_seconds", {}).items():
        if phase not in PHASES:
            errors.append(f"phase_seconds has phase {phase!r}, not one of {PHASES}")
        # The VALUE is typed too. A string here validated until 0.1.524, and
        # ledger.py sums these.
        if isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or seconds < 0:
            errors.append(f"phase_seconds[{phase!r}] must be a non-negative number, "
                          f"got {seconds!r}")
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
