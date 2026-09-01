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
import re

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

# Everything but the measures, which move (see the module docstring).
UNIVERSAL_FIELDS: tuple[str, ...] = ("period", "reading", "cause", "source",
                                     "move")


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
        axes = spec.get("axes") or {}
        return [(f"axes.{k}", (axes.get(k) or {})) for k in ("x", "y")]
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


def _pair_problems(where: str, obj, keys: tuple[str, ...], rule: str) -> list[str]:
    if not isinstance(obj, dict):
        return [f"`{where}` is {type(obj).__name__}, not an object with "
                f"{' and '.join(keys)} ({rule})"]
    return [f"`{where}` does not give its {k} ({rule})"
            for k in keys if not _filled(obj.get(k))]


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

    move = str(spec.get("move") or "").strip().lower()
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

        for field in MOVE_FIELDS[move]:
            # ABSENT, not merely empty. An empty `references` list is a
            # different finding from a missing one and `_move_problems` says
            # what it is — the judgment anchor, in WR-5's own words. Testing
            # `_filled` here reported both, and the one a reader saw first was
            # the wrong one.
            if spec.get(field) is None:
                out.append(
                    f"a `{move}` figure needs `{field}`, and this spec does "
                    f"not carry it. AR-1's input shape for {move} is "
                    f"{' + '.join(MOVE_FIELDS[move])}")
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
        crit = spec.get("criteria")
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
        value_key = ("values",) if crit is not None else ("value",)
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
    elif move == "bridge":
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
            drawable = [p for p in pts
                        if isinstance(p, dict)
                        and _filled(p.get("x")) and _filled(p.get("y"))]
            if len(drawable) < 2:
                out.append(
                    "a `correlate` figure shows PAIRED observations, and this "
                    "spec carries fewer than two points with both an x and a "
                    "y. One point is not a relation (AR-1)")
    return out


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
