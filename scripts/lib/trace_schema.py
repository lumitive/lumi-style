#!/usr/bin/env python3
"""The trace schema — one definition, imported by both the writer and the guard.

It lives in scripts/lib/ rather than beside the CLI for a specific reason: the
emergency-merge path runs a trusted closure of checker code, and a guard that
reached into scripts/ops/ would make the emergency run execute the pull
request's own copy of the thing it is checking. A shared definition also keeps
this repository's `one home` rule — a second copy of a field list is the
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
#
# Membership here also PERMANENTLY withdraws a field from
# check_trace_field_writers' fill-rate guard (it skips `f in ADDED_LATER`).
# That is deliberate — an honest late arrival must not redden as "never
# recorded" — but note the asymmetry with WRITER_WAIVERS: a waiver carries a
# dead-waiver reverse check (a waived-but-filled field is itself a finding),
# ADDED_LATER does not. So if a field here regressed to recording nothing on
# every trace, the guard would stay green. The exposure is bounded: these are
# absence-heavy by nature (cache counts: "None is the answer, zero would be a
# claim"), and a field that becomes reliably filled is a candidate to move OUT
# of ADDED_LATER into a plain declaration, where the guard covers it again.
ADDED_LATER = frozenset({"shape", "cli_version",
                         # 0.1.648. Every trace closed before it has neither,
                         # and that is an honest absence rather than a zero:
                         # the counts were being read off the transcript and
                         # thrown away, not reported as nothing.
                         "cache_read_tokens", "cache_write_tokens",
                         # 0.1.655. A --fast round marks it; every trace closed
                         # before it is a full delivery whose absence reads False.
                         "partial"})

# WHY A DECLARED FIELD MAY BE EMPTY ON EVERY TRACE, stated rather than left to
# rot. `check_trace_field_writers` (check_repo) holds every declared field to
# recording SOMETHING across the stored traces — the mirror of
# `check_trace_field_readers`, which caught a field nobody read. The disease it
# guards against is FM-24's exact shape one field over: a column with a
# validator and no data prints what a clean tree prints (empty on every trace)
# while looking like coverage. `principle_yields`/`refused_to_emit` were
# 0-of-96 for 187 releases for exactly this reason — their writers `trace.py
# yield`/`refuse` are subcommands no build or conformance pipeline ever invokes.
# Their authority is PRINCIPLES.md §3 (the constitution's collide-and-exit
# clause), which `cmd_refuse`'s own help string cites.
#
# A waiver here is the ADDED_LATER move applied to fill rate rather than to
# vintage: a field may be empty on every trace ONLY with a reason that names
# what would fill it. No waiver, no data -> the guard is red. And the reverse is
# held (convention 19): a waiver for a field that IS now filled, or no longer
# exists, is a dead waiver and fails — an approved silence over a hole that
# closed is the same "looks like coverage" defect. This is not a place to
# silence the guard; it is the ledger that turns an invisible hole into a
# tracked debt with a named trigger.
WRITER_WAIVERS: dict[str, str] = {
    "principle_yields":
        "The data-layer home of PRINCIPLES.md §3 (record which principle was "
        "yielded, per build). Its writer `trace.py yield` is invoked by no "
        "pipeline, so it is empty until an explicit-yield event in the build "
        "tool is wired to call it (the `--assess` family is the natural hook). "
        "Not deleted — deleting it removes the only place a constitutional "
        "yield can be counted; kept as a debt with this trigger.",
    "refused_to_emit":
        "PRINCIPLES.md §3's other half: the clauses that collided and the "
        "stage, when a build refuses to emit rather than break a rule. Writer "
        "`trace.py refuse` is invoked by no pipeline. Activates when the "
        "renderer/build tool machine-writes a refusal — the same 'a verdict is "
        "transcribed, never typed' philosophy the shape readings follow. Kept "
        "for the reason above.",
}

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
    # A --fast (iteration) round MARKS the trace partial rather than closing it:
    # True = a fast-loop record (clock stopped, no closed_at, no verdicts, no
    # shape — it measured one geometry and reviewed no storyline); False = a full
    # delivery close set it; None = a trace from before the field existed.
    "partial": (bool, type(None)),
    "model": (str, type(None)), "effort": (str, type(None)),
    # WHICH BUILD OF THE AGENT. `agent` names a platform and `model` names what
    # it was pointed at; neither says which version of the CLI did the work,
    # and a CLI updates on its own schedule. Two rounds of one configuration
    # measured a week apart were driven by `2026.08.11-e8db854` and
    # `2026.08.25-3e8eec8`, so any difference between them has a third possible
    # cause that nothing recorded. Free text for the same reason `model` is:
    # every vendor spells a build differently and an enum of them would be a
    # maintenance tax with no defect behind it.
    "cli_version": (str, type(None)),
    "agent": (str, type(None)), "pages": int, "content_pages": int,
    "phase_seconds": dict, "input_tokens": (int, type(None)),
    # `cost_usd` was here and is gone. It is tokens times a price, and a
    # stored derivation goes stale the day the price does — while the tokens
    # it derives from are right there. Prefer deleting the number: the board
    # computes cost at report time from a dated price table when one exists.
    "output_tokens": (int, type(None)),
    # THE OTHER HALF OF THE BILL. Optional where the two above are not: a CLI
    # that reports no cache line is one that does not SAY, not one that read
    # nothing, and `None` is that answer. Recorded rather than ordered on —
    # the cost axis is output tokens per page by the owner's ruling, and these
    # exist so a later change of that ruling has data to change to.
    "cache_read_tokens": (int, type(None)),
    "cache_write_tokens": (int, type(None)),
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


# WHOSE FACT IS IT. One flat record holds three populations — the document's,
# the producer's, and the run's own — and until this partition existed nothing
# said which was which. Declared as a PARTITION rather than as lists, because a
# list can omit a member in silence and a partition cannot: `check_trace_schema`
# asserts the three are disjoint and together exhaust FIELDS, so a field added
# to the schema must be assigned a side or CI goes red.
#
# **What a reader may do with the other side's fields.** The first draft of this
# comment allowed two uses and a review found both of its own examples breaking
# them, in the two files it named. The honest list is three:
#
#   * QUALIFY — `agent_runs.board()` reads `gates`, a document field, to decide
#     whether a run is admitted at all. A failing gate keeps a cheap thin deck
#     off the cost board, which is the one thing stopping the board from
#     rewarding thinner decks.
#   * NORMALIZE — `agent_runs.board()` divides by `content_pages`, a document
#     field, because a rate needs a denominator. `tokens_per_page` is a fact
#     about the producer expressed per unit of document, and calling that
#     forbidden would forbid the board's headline number.
#   * REPORT — `ledger.ledger_signals()` reads `refused_to_emit` and
#     `principle_yields`, producer fields, and prints them under its own
#     heading. It neither groups nor grades: a refusal to emit is a fact about
#     the run that the document tool is the place to notice.
#
# What no reader may do is GRADE across the line: a document's verdict may not
# depend on which model wrote it, and an agent's standing may not be read off
# one document's quality. That is the sentence with teeth, and it is the one
# `run_conformance.py` states as the product claim — a deliverable is held to
# one bar whichever model wrote it.
#
# None of this is mechanical, and a tighter check would be FM-01 pretending to
# judge intent. What IS mechanical is that every field has a side.
DOCUMENT_FIELDS = frozenset({
    "genre", "storyline", "geometry", "pages", "content_pages",
    "gates", "graded", "thresholds", "shape", "corpus_id", "review_ref",
    "outline_reviewed", "titles_changed_after_approval",
})
PRODUCER_FIELDS = frozenset({
    "agent", "model", "effort", "cli_version", "input_tokens", "output_tokens",
    "cache_read_tokens", "cache_write_tokens",
    "phase_seconds", "refused_to_emit", "principle_yields",
})
# The run itself: neither the document's nor the producer's, and naming them
# keeps the two sets above honest instead of letting provenance drift into
# whichever half a reader reached for first.
RUN_FIELDS = frozenset({
    "trace_id", "opened_at", "closed_at", "source", "skill_version",
    "recipe_hash", "recipe_version", "entry_path", "partial",
})


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
