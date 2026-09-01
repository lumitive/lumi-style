#!/usr/bin/env python3
"""The figure data contract: what a reader needs before they can read a drawing.

**Why this exists.** Measured across three shipped deliverables: 58 business
figures, **1** declaring the data it draws. Nothing in this package held a
figure's numbers, so there was nothing for a rebuild to inherit, nothing for a
translation to redraw from, nothing for the fact contract to compare against,
and nothing to call a renderer with. One absence produced nine broken links in
the chain a figure travels (`specs/2026-09-01-figure-data-contract-design.md`
§4). This is the artefact that closes them.

One file per figure, JSON, beside the deck. It holds two halves.

**The universal half** is what `references/design-rules.md` DR-20 and
`references/writing-rules.md` WR-5 already demand of any figure carrying a
number: the period it covers, the direction stated in words, whether cause is
claimed, where the observations came from, the analytical move that produced
it — and **the measures, named with units**.

    {
      "period":  "the fiscal year or window the numbers cover",
      "reading": "the direction, in words",
      "cause":   "direction not tested",
      "source":  "where these observations came from",
      "move":    "compare",
      "measure": {"name": "...", "unit": "..."}
    }

**Where the measures live is the move's business, and that is a deliberate
departure from the design record.** The spec wrote `measure` as a flat
universal field. A `correlate` figure's measures are its two axes and a
`position` figure's are its two dimensions — both already named with units in
the move half — so demanding a *separate* `measure` object of them asks the
author to invent a third quantity that does not exist. That is AG-10's shape:
a gate no correct answer can satisfy. So the requirement is stated as **"the
figure names at least one measure, with a unit"**, and `measures_of` says where
that lives for each move. The rule is unchanged; only the place it is read from
moves. (Convention 2's documented case; recorded in the CHANGELOG.)

**The move half** is AR-1's input shape, made readable:

    compare    subject: {label, value}   references: [{label, value}]
    decompose  total:   {label, value}   parts:      [{label, value}]
    position   axes:    {x, y}           items:      [{label, x, y}]
    correlate  x, y:    {name, unit}     points:     [{x, y, size?, series?}]
    bridge     before/after: {label, value}          pieces: [{label, delta}]

`f-data`'s `{"series": [{"label", "value"}]}` can express **none** of the five,
which is why this is a new artefact rather than a revision of that one.

**Nothing here mandates that a figure have a spec.** A schematic, a 2x2, the
globe and an icon row are correct answers that cannot satisfy such a demand —
AG-10 again, which this package declined after shipping it for one commit and
watching its author bind a wrong shape to satisfy his own guard. What is graded
is the contradiction class only, target zero: a page that DECLARES a spec whose
file is missing or does not hold what it says it holds.

**And a spec may never double as the `--facts` contract.**
`check_facts.compare` computes `unsourced = document quantities − contract
quantities`; one source makes that set empty forever and red line 1's only
instrument goes blind. The contract is written from the engagement, the spec is
written for a figure, and the check is that they agree.

Standard library only.
"""
from __future__ import annotations

import json
import pathlib

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

import figure_scale  # noqa: E402

num = figure_scale.num

# What an unfilled slot looks like. It is the SAME marker `check_design`'s D14
# refuses in a rendered document, so a skeleton that reaches a reader is caught
# by a gate that already exists rather than by a new one.
TO_FILL = "[TO FILL: {}]"
TO_FILL_RE = re.compile(r"\[TO FILL[^\]]*\]|\[TBD[^\]]*\]|\{\{[^}]*\}\}")

# The five moves are `check_outline.ANALYTICAL_MOVES`' business; this module
# holds the SHAPES, and `figure spec moves` in check_repo.py holds the two
# lists together so a sixth move cannot be added to one and not the other.
MOVE_FIELDS: dict[str, tuple[str, ...]] = {
    "compare": ("subject", "references"),
    "decompose": ("total", "parts"),
    "position": ("axes", "items"),
    "correlate": ("x", "y", "points"),
    "bridge": ("before", "after", "pieces"),
}

# The collection each move's OPTIONAL refinement keeps, so the shape check runs
# over it too. `criteria` turns a compare into a radar, `lanes` turns it into a
# layer map, and `stages` turns a bridge into a named path.
#
# READ BY NOTHING, and kept as the register of what the refinements are —
# `_COLLECTIONS` below is what the shape check iterates, and the two are
# extended together. An entry that guards nothing reads as coverage
# (convention 19), so this says which of the two does the work.
_COLLECTION_EXTRAS = {"compare": ("criteria", "lanes"), "bridge": ("stages",)}

# The field of each move that holds MANY things. Named rather than discovered
# because the shape check has to run before anything iterates them.
_COLLECTIONS: dict[str, tuple[str, ...]] = {
    "compare": ("references", "criteria", "lanes"),
    "decompose": ("parts",),
    "position": ("items",),
    "correlate": ("points",),
    "bridge": ("pieces", "stages"),
}

# Everything but the measures, which move (see the module docstring).
UNIVERSAL_FIELDS: tuple[str, ...] = ("period", "reading", "cause", "source",
                                     "move")


# **A CEILING, not a target.** Parts stated to one decimal do not sum to a total
# stated to the same precision, and refusing that would fail correct data — so
# the residual is allowed to be this share of the total and no more. It is
# deliberately tight: at 0.5% a genuine missing part shows up in any figure
# whose smallest slice a reader can see, and the cheap way to satisfy it is to
# name the remainder as its own part, which is what a reader needed anyway.
RESIDUAL_CEILING = 0.005

# Below this the relative test is meaningless, so an absolute one takes over.
# A total of 0.4 with parts of 0.1 and 0.2 is 25% out and must not pass because
# the numbers are small.
RESIDUAL_FLOOR = 1e-9


def _reconciles(total, pieces) -> tuple[bool, float]:
    """-> (whether the pieces account for the total, the residual)."""
    residual = total - sum(pieces)
    allowed = max(abs(total) * RESIDUAL_CEILING, RESIDUAL_FLOOR)
    return abs(residual) <= allowed, residual


def measures_of(spec: dict) -> list[tuple[str, dict]]:
    """-> [(where, {name, unit})] the measures this spec's move declares.

    The list is empty when the move is unknown, which the caller reports as a
    move problem rather than as a missing measure — two findings for one cause
    reads as two defects.
    """
    move = str(spec.get("move") or "").strip().lower()
    if move == "correlate":
        return [(k, spec.get(k) or {}) for k in ("x", "y")]
    if move == "position":
        axes = spec.get("axes")
        if not isinstance(axes, dict):
            # `[]` and `{}` both reach here, and `axes.get` on a list raised
            # AttributeError that propagated out of `check_design.measure` and
            # aborted every metric on the document with a traceback. A caller
            # asking "what does this spec measure" gets an answer or an empty
            # list, never an exception.
            return [("axes.x", {}), ("axes.y", {})]
        out: list[tuple[str, dict]] = []
        for k in ("x", "y"):
            got = axes.get(k)
            out.append((f"axes.{k}", got if isinstance(got, dict) else {}))
        return out
    if move in MOVE_FIELDS:
        return [("measure", spec.get("measure") or {})]
    return []


def _filled(value) -> bool:
    """-> whether a field holds an answer rather than a slot or a blank."""
    if value is None or isinstance(value, bool):
        return False
    if isinstance(value, str):
        return bool(value.strip()) and not TO_FILL_RE.search(value)
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


def is_skeleton(spec: dict) -> bool:
    """-> whether any value anywhere is still an unfilled slot.

    A skeleton that renders is a slot no gate can refuse: the drawing would go
    on the page, look finished, and carry nobody's numbers. So the renderers
    refuse it, and this is what they ask.
    """
    return bool(TO_FILL_RE.search(json.dumps(spec, ensure_ascii=False)))


# The keys that carry a QUANTITY. A label may be any words; a value may not.
# Found by writing the test for the arithmetic: `{"label": "a", "value": "lots"}`
# satisfied "is filled", so the contract accepted it and only the renderer — one
# layer later, and only for the moves that have one — refused to draw it.
NUMERIC_KEYS = frozenset({"value", "delta", "x", "y"})


def _pair_problems(where: str, obj, keys: tuple[str, ...], rule: str) -> list[str]:
    if not isinstance(obj, dict):
        return [f"`{where}` is {type(obj).__name__}, not an object with "
                f"{' and '.join(keys)} ({rule})"]
    out = []
    for k in keys:
        if not _filled(obj.get(k)):
            out.append(f"`{where}` does not give its {k} ({rule})")
        elif k in NUMERIC_KEYS and num(obj.get(k)) is None:
            out.append(f"`{where}`'s {k} is {obj[k]!r}, which is not a number. "
                       f"A mark's length, position or area IS its value, so a "
                       f"value nothing can read has no honest drawing ({rule})")
        elif k == "values":
            bad = [i for i, v in enumerate(obj[k] or []) if num(v) is None]
            if bad:
                out.append(f"`{where}`'s values are not all numbers "
                           f"(positions {bad}) ({rule})")
    return out


def problems(spec) -> list[str]:
    """-> everything wrong with this spec, each finding naming the rule it breaks.

    Returns `[]` for a spec that can be drawn. It never returns `[]` for a
    spec it could not read: an unreadable spec is reported, because "nothing
    wrong" and "nothing looked at" printing the same empty list is FM-24.
    """
    if not isinstance(spec, dict):
        return [f"the spec is {type(spec).__name__}, not an object"]
    out: list[str] = []

    for field in UNIVERSAL_FIELDS:
        if not _filled(spec.get(field)):
            out.append(
                f"`{field}` is missing or unfilled. Every figure carrying a "
                f"number states its period, its direction in words, whether "
                f"cause is claimed, its source and the move that produced it "
                f"(design-rules.md DR-20, writing-rules.md WR-5)")

    raw_move = spec.get("move")
    if raw_move is not None and not isinstance(raw_move, str):
        # `move: 0` was "filled" (a non-bool scalar), and `str(x or "")`
        # collapsed it to "", which gated OFF the entire move half — so a spec
        # with no shape at all came back clean. Realistic when a generator
        # emits the move as an index rather than a name.
        return [f"`move` is {type(raw_move).__name__} {raw_move!r}, not one of "
                f"{', '.join(sorted(MOVE_FIELDS))}. Nothing in the move half of "
                f"this spec was checked (analysis-rules.md AR-1)"]
    move = str(raw_move or "").strip().lower()
    if move and move not in MOVE_FIELDS:
        out.append(f"`move` is {move!r}, which is not one of "
                   f"{', '.join(sorted(MOVE_FIELDS))} (analysis-rules.md AR-1)")
        return out

    named = measures_of(spec)
    if move:
        if not named:
            out.append("no measure is named anywhere — a figure whose reader "
                       "cannot say what is being counted, in what unit, is a "
                       "figure of unknown meaning (DR-20)")
        for where, obj in named:
            out += _pair_problems(where, obj, ("name", "unit"),
                                  "DR-20: name the measure and its unit")

        # THE CONTAINER'S SHAPE FIRST. Every per-datum check below is either
        # `isinstance(x, list) and not x` or `for i, y in enumerate(x or [])`,
        # and a dict satisfies neither: `{}` is not a list and is falsy, so on
        # `"parts": {}` the emptiness finding was skipped, the per-datum loop
        # ran zero times, the arithmetic returned early — and `problems()` came
        # back clean for all five moves. Measured. An author keying items by
        # label instead of writing an array is the commonest JSON mistake
        # there is, and the renderers then drew a titled, sourced figure with
        # no marks in it.
        for field in _COLLECTIONS.get(move, ()):
            coll = spec.get(field)
            if coll is not None and not isinstance(coll, list):
                out.append(
                    f"`{field}` is {type(coll).__name__}, not a list. AR-1's "
                    f"input shape for {move} wants a list here, so nothing "
                    f"inside it was read — this is not a spec that passed")
                return out

        required = MOVE_FIELDS[move]
        if move == "bridge" and spec.get("stages") is not None:
            required = ("stages",)
        for field in required:
            # ABSENT, not merely empty. An empty `references` list is a
            # different finding from a missing one and `_move_problems` says
            # what it is — the judgment anchor, in WR-5's own words. Testing
            # `_filled` here reported both, and the one a reader saw first was
            # the wrong one.
            if spec.get(field) is None:
                out.append(
                    f"a `{move}` figure needs `{field}`, and this spec does "
                    f"not carry it. AR-1's input shape for {move} is "
                    f"{' + '.join(required)}")
        out += _move_problems(move, spec)
    return out


def _move_problems(move: str, spec: dict) -> list[str]:
    """-> the findings only that move can produce. Its own function because the
    universal half is one rule and each move's shape is a different one."""
    out: list[str] = []
    if move == "compare":
        refs = spec.get("references")
        if isinstance(refs, list) and not refs:
            # WR-5 rule 0 — "a key number carries its judgment anchor" — was
            # unchecked prose with no candidate metric. Here it is not a gate
            # at all: it is an INPUT SHAPE. A compare figure with nothing to
            # compare against cannot be drawn, so the anchor exists or the
            # figure does not.
            out.append(
                "a `compare` figure carries one value and AT LEAST ONE "
                "reference value, and this spec's `references` is empty. A "
                "number standing alone with no reader able to say whether it "
                "is good is the tell that the move is missing (AR-1; "
                "writing-rules.md WR-5 rule 0, the judgment anchor)")
        # `criteria` is compare's OPTIONAL refinement, and it is what a radar
        # draws: the same move across several criteria at once rather than on
        # one measure. It is an extension rather than a sixth move because the
        # question is AR-1's compare question — "where is this strong and where
        # is it thin" is still setting a value against a reference — and adding
        # a move to the five would put this module and
        # `check_outline.ANALYTICAL_MOVES` out of step.
        # `lanes` is compare's OTHER refinement, and it is exclusive with
        # `criteria` for the same reason `stages` and `pieces` are exclusive on
        # a bridge: the two answer different questions about the same move and
        # a spec carrying both has not decided which figure it is. A radar
        # compares one subject across several criteria; a lane figure compares
        # several subjects that sit in different LAYERS, and the layer is the
        # argument. Adding it here rather than as a sixth move is AR-1's rule:
        # "where does each of these sit, and how do they differ" is still
        # setting a value against a reference.
        lanes = spec.get("lanes")
        crit = spec.get("criteria")
        if lanes is not None and crit is not None:
            out.append(
                "a compare declares `criteria` (a radar: one subject across "
                "several axes) or `lanes` (layers: several subjects in "
                "different bands), never both — they are different figures of "
                "the same move, and a spec carrying both has not chosen (AR-1)")
        if lanes is not None:
            if not isinstance(lanes, list) or len(lanes) < 2:
                out.append(
                    "`lanes` names the layers the items are split across, and "
                    "a split needs at least two: with one lane there is "
                    "nothing for the split to say and the figure is a row of "
                    "chips (AR-1)")
            else:
                for i, lane in enumerate(lanes):
                    out += _pair_problems(f"lanes[{i}]", lane, ("name",),
                                          "AR-1: compare across lanes")
                named = {str((lane or {}).get("name") or "").strip()
                         for lane in lanes if isinstance(lane, dict)}
                for who, obj in ([("subject", spec.get("subject"))]
                                 + [(f"references[{i}]", r)
                                    for i, r in enumerate(refs or [])]):
                    got = str((obj or {}).get("lane") or "").strip() \
                        if isinstance(obj, dict) else ""
                    if got not in named:
                        # NEVER A DEFAULT LANE. Dropping an item into the first
                        # band draws a claim the spec does not make, and the
                        # reader cannot see that it was a guess.
                        out.append(
                            f"`{who}` declares lane {got!r}, which is not one "
                            f"of {', '.join(sorted(named))}. The lane is the "
                            f"figure's whole argument, so it is stated rather "
                            f"than defaulted (AR-1)")
        if crit is not None:
            if not isinstance(crit, list) or len(crit) < 3:
                out.append(
                    "`criteria` names the axes a radar compares across, and a "
                    "radar needs at least three: two criteria are a pair of "
                    "bars drawn as a triangle (AR-1)")
            else:
                for i, c in enumerate(crit):
                    out += _pair_problems(f"criteria[{i}]", c, ("name",),
                                          "AR-1: compare across criteria")
                for who, obj in ([("subject", spec.get("subject"))]
                                 + [(f"references[{i}]", r)
                                    for i, r in enumerate(refs or [])]):
                    vals = (obj or {}).get("values") if isinstance(obj, dict) else None
                    if not isinstance(vals, list) or len(vals) != len(crit):
                        out.append(
                            f"`{who}` must carry one value per criterion — "
                            f"{len(crit)} of them — because a radar with a "
                            f"missing spoke draws a shape the data does not "
                            f"have (AR-1)")
        # A LAYER MAP CARRIES NO VALUE, and demanding one is AG-10 exactly.
        # `lanes_svg` draws a name, a lane and a chip; it reads no `value` at
        # all. Held to the plain compare shape, a correct six-item layer map
        # was refused with eight problems until fake numbers were invented —
        # and `check_facts` then collected those inventions and required the
        # author to write them into the fact contract as well. The only ways
        # out were to invent facts or delete the figure, which is the sentence
        # 0.1.676 wrote about `position` while shipping the same trap one
        # refinement over.
        if lanes is not None:
            value_key: tuple[str, ...] = ()
        elif crit is not None:
            value_key = ("values",)
        else:
            value_key = ("value",)
        out += _pair_problems("subject", spec.get("subject"),
                              ("label",) + value_key, "AR-1: compare")
        for i, ref in enumerate(refs or []):
            out += _pair_problems(f"references[{i}]", ref,
                                  ("label",) + value_key, "AR-1: compare")
    elif move == "decompose":
        if isinstance(spec.get("parts"), list) and not spec["parts"]:
            out.append(
                "a `decompose` figure breaks a whole into parts, and this "
                "spec's `parts` is empty. A total discussed as a total is the "
                "tell that the move is missing (AR-1)")
        out += _pair_problems("total", spec.get("total"), ("label", "value"),
                              "AR-1: decompose")
        for i, part in enumerate(spec.get("parts") or []):
            out += _pair_problems(f"parts[{i}]", part, ("label", "value"),
                                  "AR-1: decompose")
        out += _arithmetic(spec, "decompose")
    elif move == "bridge":
        # `stages` is bridge's OPTIONAL refinement, the way `criteria` refines
        # compare: a path whose steps are NAMED rather than numeric. A version
        # history — announced, stable, current, candidate — is a bridge whose
        # pieces do not add up to anything, because the change it attributes is
        # capability rather than quantity. It is an extension rather than a
        # sixth move because AR-1 declares five and `figure spec moves` holds
        # this module to `check_outline.ANALYTICAL_MOVES`; a sixth would need
        # convention 2's documented case for a rule revision, and a timeline
        # does not earn one.
        stages, pieces = spec.get("stages"), spec.get("pieces")
        if stages is not None and pieces is not None:
            out.append(
                "a `bridge` figure carries EITHER `pieces`, which must "
                "reconcile the change arithmetically, OR `stages`, which name "
                "a path the numbers do not add up along. Carrying both leaves "
                "the reader unable to say which one the drawing is (AR-1)")
            return out
        if stages is not None:
            if not isinstance(stages, list) or len(stages) < 2:
                out.append(
                    "a `bridge` drawn as a path needs at least two `stages`. "
                    "One point in time is a date, not a path (AR-1)")
                return out
            for i, st in enumerate(stages):
                out += _pair_problems(f"stages[{i}]", st, ("date", "name"),
                                      "AR-1: bridge as a named path")
            return out
        if isinstance(spec.get("pieces"), list) and not spec["pieces"]:
            out.append(
                "a `bridge` figure attributes a change to pieces, and this "
                "spec's `pieces` is empty. A before and an after with nothing "
                "between them is a comparison, not a bridge (AR-1)")
        for end in ("before", "after"):
            out += _pair_problems(end, spec.get(end), ("label", "value"),
                                  "AR-1: bridge")
        for i, piece in enumerate(spec.get("pieces") or []):
            out += _pair_problems(f"pieces[{i}]", piece, ("label", "delta"),
                                  "AR-1: bridge")
        out += _arithmetic(spec, "bridge")
    elif move == "position":
        if isinstance(spec.get("items"), list) and len(spec["items"]) < 2:
            out.append(
                "a `position` figure places ITEMS on two axes, and this spec "
                "carries fewer than two. One item on a map is a point, not a "
                "position (AR-1)")
        for i, item in enumerate(spec.get("items") or []):
            out += _pair_problems(f"items[{i}]", item, ("label", "x", "y"),
                                  "AR-1: position")
    elif move == "correlate":
        pts = spec.get("points")
        if isinstance(pts, list):
            # EVERY POINT IS READ, the way every other move's data is. This
            # counted drawable points and nothing else until 0.1.671, so a
            # point whose x was the string "TBD" satisfied "is filled", passed
            # the contract, and was then silently dropped by the renderer's
            # `continue`. Measured on a 40-point spec with 38 such points: the
            # contract reported nothing, the drawing carried two marks, and its
            # own alt text said "2 points". Thirty-eight observations
            # disappeared with nobody counting them.
            unreadable = []
            for i, p in enumerate(pts):
                if not isinstance(p, dict):
                    out.append(f"`points[{i}]` is {type(p).__name__}, not an "
                               f"observation with an x and a y (AR-1)")
                    continue
                bad = _pair_problems(f"points[{i}]", p, ("x", "y"),
                                     "AR-1: correlate")
                if bad:
                    unreadable.append(i)
                    out += bad[:1]
            if len(unreadable) > 3:
                out.append(
                    f"{len(unreadable)} of {len(pts)} observations carry an x "
                    f"or a y this contract cannot read. A discarded "
                    f"observation is a datum the reader never learns was "
                    f"collected")
            drawable = [p for p in pts
                        if isinstance(p, dict)
                        and num(p.get("x")) is not None
                        and num(p.get("y")) is not None]
            if len(drawable) < 2:
                out.append(
                    "a `correlate` figure shows PAIRED observations, and this "
                    "spec carries fewer than two points with both an x and a "
                    "y. One point is not a relation (AR-1)")
    return out


def _arithmetic(spec: dict, move: str) -> list[str]:
    """-> the finding when the numbers do not add up. **The prize.**

    Every other check in this package is about the DOCUMENT: whether a class is
    declared, a reference resolves, a mark is drawn in proportion. This is an
    assertion about the author's DATA, and no existing check could make it,
    because before this artefact nothing held both the total and its parts.

    It is silent when a value cannot be read as a number — `problems` has
    already said so in its own words, and two findings for one cause reads as
    two defects.
    """
    def _n(obj, key):
        return num(obj.get(key)) if isinstance(obj, dict) else None

    if move == "decompose":
        total = _n(spec.get("total"), "value")
        parts = [_n(p, "value") for p in spec.get("parts") or []]
        if total is None or not parts or any(v is None for v in parts):
            return []
        ok, residual = _reconciles(total, parts)
        if ok:
            return []
        return [
            f"the parts do not account for the total: they sum to "
            f"{sum(parts):g} against a total of {total:g}, leaving {residual:g} "
            f"unaccounted for. A decompose is MECE (AR-1) — mutually exclusive "
            f"and collectively exhaustive — so either a part is missing, a "
            f"value is wrong, or the remainder is real and belongs on the "
            f"figure as its own named part rather than as a gap the reader "
            f"cannot see"]

    before = _n(spec.get("before"), "value")
    after = _n(spec.get("after"), "value")
    deltas = [_n(p, "delta") for p in spec.get("pieces") or []]
    if before is None or after is None or not deltas or any(d is None for d in deltas):
        return []
    ok, residual = _reconciles(after - before, deltas)
    if ok:
        return []
    return [
        f"the pieces do not reconcile the change: they sum to {sum(deltas):g} "
        f"against a move from {before:g} to {after:g}, which is "
        f"{after - before:g} — {residual:g} unexplained. A bridge exists to "
        f"attribute a change to its causes (AR-1), so a bridge that does not "
        f"close is asserting a cause it has not found"]


def load(path: pathlib.Path) -> tuple[dict | None, str | None]:
    """-> (spec, problem). Exactly one of the two is None.

    Two answers, never one: a spec that is absent, unreadable or not JSON is a
    different state from a spec that parsed, and a caller that cannot tell them
    apart writes the blind branch this package has shipped eight times.
    """
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        return None, f"{path}: the figure spec could not be read ({exc})"
    try:
        spec = json.loads(raw)
    except ValueError as exc:
        return None, f"{path}: the figure spec is not JSON ({exc})"
    if not isinstance(spec, dict):
        return None, (f"{path}: the figure spec is a "
                      f"{type(spec).__name__}, not an object")
    return spec, None


# The skeleton the scaffold writes. **Not one digit anywhere**, including in the
# examples: a scaffold that invents a number hands the author a figure that
# looks sourced and is not, and IDEA-18 measured four such numbers reaching a
# reader from this package's own sample block. Every slot is the marker D14
# already refuses in a rendered document.
_SLOT = {
    "period": "the window these numbers cover",
    "reading": "the direction, in words",
    "cause": "direction not tested, or say what was tested",
    "source": "where these observations came from",
    "name": "what is counted",
    "unit": "the unit it is counted in",
    "label": "what this one is",
    "value": "its value",
    "delta": "how much it moved, signed",
}


def _slot(key: str) -> str:
    return TO_FILL.format(_SLOT[key])


def _measure() -> dict:
    return {"name": _slot("name"), "unit": _slot("unit")}


def _labelled(value_key: str = "value") -> dict:
    return {"label": _slot("label"), value_key: _slot(value_key)}


def skeleton(move: str) -> dict:
    """-> a spec with every field present, every value a slot, no numbers.

    Raises `ValueError` on a move it does not know, rather than returning a
    universal-half-only dict that would look like a valid skeleton for a move
    nothing can draw.
    """
    move = str(move or "").strip().lower()
    if move not in MOVE_FIELDS:
        raise ValueError(
            f"no skeleton for move {move!r}; the five are "
            f"{', '.join(sorted(MOVE_FIELDS))} (analysis-rules.md AR-1)")
    out: dict = {"move": move}
    for field in ("period", "reading", "cause", "source"):
        out[field] = _slot(field)
    if move == "correlate":
        out["x"], out["y"] = _measure(), _measure()
        out["points"] = []
    elif move == "position":
        out["axes"] = {"x": _measure(), "y": _measure()}
        out["items"] = []
    else:
        out["measure"] = _measure()
        if move == "compare":
            out["subject"], out["references"] = _labelled(), []
        elif move == "decompose":
            out["total"], out["parts"] = _labelled(), []
        elif move == "bridge":
            out["before"], out["after"] = _labelled(), _labelled()
            out["pieces"] = []
    return out


def refuse_if_unusable(spec, path: str = "the spec") -> None:
    """Raise `SystemExit` with everything wrong, or return.

    The renderers' single entry point, so a scatter and a benchmark refuse the
    same specs for the same reasons in the same words.
    """
    if is_skeleton(spec):
        raise SystemExit(
            f"{path} is still the skeleton: at least one value is an unfilled "
            f"slot. Fill it before drawing — a figure rendered from a skeleton "
            f"goes on the page looking finished and carries nobody's numbers.")
    found = problems(spec)
    if found:
        raise SystemExit(f"{path} cannot be drawn:\n  - "
                         + "\n  - ".join(found))
