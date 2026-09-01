#!/usr/bin/env python3
"""Emit a deck skeleton that already renders, in the standard order.

    python3 scripts/ops/new_deck.py > mydeck.en.html
    python3 scripts/ops/new_deck.py --genre internal --pages 8 --parts A,B,C

WHY THIS EXISTS. A deliverable shipped with no icons anywhere, a blank part
opener, and a block whose two halves rendered 246px and 34px wide — all of it
because the structure was hand-authored from memory of class names rather than
copied from the reference implementation that renders them.

The head is not the document. `fixtures/deck-pass.en.html` carries its token
block in `<head>` and its icon sprite and page ground in `<body>`, so a document
assembled by slicing to `</head>` has a full stylesheet and no icons at all —
and a `<use>` pointing at nothing is valid markup that renders as empty space.

THE STANDARD ORDER, which is the default unless a request says otherwise:

    cover · agenda · Part A opener · content… · Part B opener · content… · closing

`--genre training` appends the reference pages Template 4's arc ends on — a
glossary as `dl.gloss`, marked `data-role="apparatus"` — before the closing,
because a training document's last pages are the ones a learner returns to.

The first version of this file emitted cover, one opener, a run of pages and a
closing. That is not a deck; it is a deck's middle. The agenda is the page a
reader uses to decide what to skip, and parts are a sequence rather than a
single heading.

RUN THIS SCRIPT; DO NOT SLICE THE FIXTURE BY HAND. A 34-page review shipped
with the fixture's own furniture in reader-facing positions — `REPLACE ME` as
its title, `www.example.org` in every footer — because its pages were copied
from `fixtures/deck-pass.en.html` instead of generated here. The fixture is a
checker input; this scaffold is the thing an author starts from, and
`check_design.py`'s D14 now refuses the slots both of them emit.

D19 in check_design.py is the negative half of this: it refuses a document whose
references do not resolve and whose blocks do not carry their contract. This is
the positive half — it hands you the ones that do.

Standard library only.
"""
from __future__ import annotations

import argparse
import hashlib  # noqa: E402
import html
import json
import pathlib

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
import sys
import sys as _bs_sys  # noqa: E402

_SCRIPTS_ROOT = next(p for p in _bs_pathlib.Path(__file__).resolve().parents
                     if p.name == "scripts")
for _sub in ("lib", "render", "check", "build", "ops", ""):
    _p = str(_SCRIPTS_ROOT / _sub) if _sub else str(_SCRIPTS_ROOT)
    if _p not in _bs_sys.path:
        _bs_sys.path.append(_p)
del _bs_pathlib, _bs_sys, _SCRIPTS_ROOT, _sub, _p
# --- end bootstrap ---
import deliverable_registry  # noqa: E402
import embed_font  # noqa: E402
import embed_globe  # noqa: E402
import embed_shapes  # noqa: E402
import figure_spec  # noqa: E402
import versioning  # noqa: E402

# ONE ICON PER PAGE, ROTATED — not because rotation is right, but because the
# same icon on every page is demonstrably wrong and a scaffold teaches by what
# it does. Every content page carried `#i-radar` until 0.1.547; the conformance
# deck that inherited it reached the reader with one icon on seven of eight
# pages and twelve of the fifteen sprite symbols dead, while the two agents
# that varied theirs matched the accepted reference. A default nobody pushes
# back on IS the output. The list is the sprite the fixture ships, minus
# `i-shield` (the footer's, one meaning) and `i-list-checks` (the agenda's).
PAGE_ICONS = ("i-layers", "i-gauge", "i-scale", "i-route", "i-target",
              "i-git-branch", "i-split", "i-calendar", "i-funnel", "i-bell",
              "i-radar", "i-ban", "i-book-open")

ROOT = next(p for p in pathlib.Path(__file__).resolve().parents
            if p.name == "scripts").parent
# READ LAZILY, inside preamble(). build_fixtures.py imports this module for
# brand_globe(), and this module reads the artifact build_fixtures GENERATES —
# so a module-scope read here would stop the fixture generator from importing
# whenever the fixture is absent or stale, which is exactly when it is run.
FIXTURE = ROOT / "fixtures" / "deck-pass.en.html"

# The owner's default, 2026-08-23, after three validation rounds: ten content
# pages. Six was this file's own invention and it sat BELOW
# `evals/thresholds.json`'s `min_content_pages: 8`, so a default scaffold
# escaped the corpus ratios entirely and `check_prose`'s M11 reported n/a for
# want of titles. Ten clears both, and at the default `--parts A,B` it runs
# five pages per part - `opener_pacing`'s target exactly.
DEFAULT_PAGES = 10

# `judge_findings.py` rejects a quotation under three words as "a fragment that
# would match anything". The same floor, counted so it means the same thing in a
# language without spaces: a CJK character is a token.
_ASK_TOKEN = re.compile(r"[A-Za-z0-9]+|[\u3400-\u9fff\u3040-\u30ff\uac00-\ud7af]")


def _field(key: str, rest: str) -> str:
    """Pull `key: ...` out of an outline's pipe-separated analysis line."""
    m = re.search(rf"{key}\s*:\s*([^|]+)", rest, re.I)
    return m.group(1).strip() if m else ""


def outline_omissions(path: pathlib.Path | None):
    """-> [{section, reason}] the outline DECLARED out of scope, canonicalised.

    C5 lets a document declare a deliberate gap instead of filling it, and the
    declaration is a reader-visible note carrying `data-omitted`. On entry path
    B the author declares it in the OUTLINE, whose syntax exists for exactly
    this — and `outline_sections` above threw the parsed result away with an
    underscore, so the declaration reached the checker on no path at all.
    Measured on the two decks of the 2026-08-25 validation round: the author
    who hand-wrote the attribute passed D31, the author who used the outline's
    own syntax failed it, and the difference was not the documents.

    **The section is canonicalised to the checklist's own name**, because
    D26 tests `a in declared` — exact set membership, not a substring. An
    outline saying "sizing (TAM/SAM/SOM)" or "customer segments" against a
    checklist saying "sizing" and "segments" would otherwise produce a note
    that looks right, reads right, and clears nothing: a fix indistinguishable
    from no fix. The author's own wording stays in the sentence a reader meets.
    """
    if path is None:
        return []
    sys.path.insert(0, str(ROOT / "scripts" / "check"))
    import check_outline
    _meta, _groups, omissions, _analyses = check_outline.parse(
        path.read_text(encoding="utf-8"))
    checklist = deliverable_registry.TYPICAL_SECTIONS.get(
        _meta.get("storyline", ""), ())
    out = []
    for om in omissions:
        said, reason = om.get("section", ""), om.get("reason", "")
        # A DECLARATION WITHOUT A REASON IS NOT EMITTED. `check_outline`
        # already reports it, and a scaffold that supplied the reason would be
        # writing the author's judgement for them.
        if not reason:
            continue
        name = said
        words = set(re.findall(r"[\w']+", said.lower()))
        for entry in checklist:
            alts = deliverable_registry.section_alts(entry)
            # EVERY WORD OF THE CHECKLIST NAME, present in what the author
            # wrote — not a substring test, which is defeated by the ordinary
            # way people write these: "customer DECISION journey" contains
            # neither "customer journey" nor is contained by it. Measured on the
            # two outlines of the 2026-08-25 round, whose three phrasings were
            # "sizing (TAM/SAM/SOM)", "customer segments" and "customer
            # decision journey".
            if any(a in said or said in a
                   or set(re.findall(r"[\w']+", a.lower())) <= words
                   for a in alts):
                name = deliverable_registry.section_name(entry)
                break
        out.append({"section": name, "said": said, "reason": reason})
    return out


def outline_sections(path: pathlib.Path | None):
    """-> [{title, move, finding, implication}] from the analysis beat, or [].

    The beat produced a plan and nothing carried it into the markup. Measured on
    a shipped deck: fourteen sections declared a move, a finding and an
    implication, and not one of those titles still described a page -- the
    analysis ran and composition threw it away. Reading it here is what makes
    the beat an INPUT instead of a document.
    """
    if path is None:
        return []
    sys.path.insert(0, str(ROOT / "scripts" / "check"))
    import check_outline
    _meta, groups, _om, analyses = check_outline.parse(
        path.read_text(encoding="utf-8"))
    by_title = {}
    for a in analyses:
        t = a.get("after_title")
        if not t:
            continue
        rest = str(a.get("rest", ""))
        move = str(a.get("move", ""))
        # SAY SO. `check_outline` validates the vocabulary and this tool does
        # not run it, so a typo (`comparison`) or a missing space before the
        # first pipe (`compare|finding:` — the parser's `(\S+)` swallows the
        # delimiter) shipped an invalid `data-analysis` and a page that is
        # quantitative silently never got asked for its measure.
        if move and move not in check_outline.ANALYTICAL_MOVES:
            print(f"note  outline: analysis move {move!r} is not one of "
                  f"{check_outline.ANALYTICAL_MOVES} — the page ships the "
                  f"declaration but gets no framework, no shape and no measure "
                  f"slot. Check for a typo or a missing space before the pipe.",
                  file=sys.stderr)
        by_title[t] = {"move": move,
                       "finding": _field("finding", rest),
                       "implication": _field("implication", rest),
                       "framework": _field("framework", rest),
                       "data": _field("data", rest)}
    out = []
    for _h, titles in groups:
        for t in titles:
            d = by_title.get(t, {})
            out.append({"title": t, "move": d.get("move", ""),
                        "finding": d.get("finding", ""),
                        "implication": d.get("implication", ""),
                        "framework": d.get("framework", ""),
                        "data": d.get("data", "")})
    return out


# The support line's SEED, chosen by the declared analytical move. A page whose
# move is quantitative owes a measure — unit and period — because that is what
# a reader needs before they can read the drawing at all (design-rules §3;
# IBCS Top Ten rule 2, the basis of ISO/AWI 24896, asks a title to name the
# organizational unit, the measure and the time period). A framework page has
# neither, so it keeps the prose seed: requiring a measure of every figure
# would red-line the market 2x2 that EX-2 records as an accepted page.
#
# This is a SLOT, not a check. The measured lesson this follows is 0.1.522's:
# row labels x56 and stat blocks 11/11 landed automatically while benchmark
# lines came to 0 over 14 pages — "what a stylesheet can carry gets applied".
# A rule the generator does not emit is a rule that does not happen.
# DERIVED from AR-1's vocabulary, not a fourth copy of it. The five moves
# already live in `analysis-rules.md`, `check_outline.ANALYTICAL_MOVES` and
# `assets/frameworks.json`; a literal tuple here would route a sixth move to
# prose silently and every check would stay green.
def _quantitative_moves() -> tuple[str, ...]:
    """-> AR-1's moves whose finding is a quantity.

    DERIVED from the one vocabulary, not a fourth copy of it: the five moves
    already live in `analysis-rules.md`, `check_outline.ANALYTICAL_MOVES` and
    `assets/frameworks.json`. A literal tuple here would route a sixth move to
    prose silently and leave every check green. `check_outline` is imported
    lazily because this module reaches it through the scripts/check path it
    inserts at call time.
    """
    sys.path.insert(0, str(ROOT / "scripts" / "check"))
    import check_outline
    return tuple(m for m in check_outline.ANALYTICAL_MOVES if m != "position")
SUP_PROSE = "The support line, one sentence and not a summary."
# A BRACKETED SLOT, not an example. Two reasons, both measured.
# (1) An example satisfies any token test written against it, so a metric
#     graded on "unit and period tokens" went green on this very placeholder.
# (2) A measure line is a NOUN PHRASE NAMING A QUANTITY, and that is not
#     decidable from tokens: "Global buyout assets under management" (Bain,
#     Figure 2) carries neither a unit nor a period, and a unit-and-period
#     predicate false-failed 5 of 7 real McKinsey and Bain measure lines.
#     So there is no new check here — the slot is handed over, and D14, which
#     already GATES, refuses to let an unfilled one reach the reader.
SUP_MEASURE = "[TO FILL: the measure, its unit, and the period]"


def sup_for(move: str) -> str:
    """-> the support-line seed for a page declaring `move`."""
    return SUP_MEASURE if move in _quantitative_moves() else SUP_PROSE


def _registry() -> dict:
    """-> the framework registry, or exit loudly. Never an empty dict.

    Three functions read `assets/frameworks.json` and each used to swallow
    `OSError`/`ValueError` into its own empty answer. That made a truncated or
    renamed registry indistinguishable from "this move has no framework": the
    page still declared its move, carried no shape and no tool slot, and so
    gave `d14_placeholders` nothing to refuse — a deck that renders finished
    and is not. Measured on a truncated file and on one whose top-level key was
    renamed; both were green.

    The registry is a tracked, guarded asset, so a read failure is a broken
    checkout rather than a data state, and exiting is the honest answer.
    """
    path = ROOT / "assets" / "frameworks.json"
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SystemExit(
            f"{path}: the framework registry could not be read ({exc}). The "
            f"scaffold cannot resolve a move's framework, shape or tool, and a "
            f"deck built without it looks finished and is not.") from exc
    entries = d.get("frameworks")
    if not isinstance(entries, dict) or not entries:
        raise SystemExit(f"{path}: parsed, but carries no `frameworks` object "
                         f"— the registry is not the registry.")
    return entries


def framework_for(move: str) -> str:
    """-> a one-line hint naming the frameworks that draw this move, and the
    misuse each is known for.

    `assets/frameworks.json` has been validated by a guard and read by no
    runtime since it shipped: an author asking "which framework does this page
    want" got the same answer as before the dictionary existed. This is the
    question -> framework -> shape chain of analysis-rules.md AR-4, executed.
    It NAMES the candidates and their misuse; it does not choose, because the
    relation lives in the content and this file cannot see it.
    """
    if not move:
        return ""
    # One reader of the registry (`frameworks_matching`) owns the failure
    # message; this one asks it rather than swallowing the same exception into
    # a different empty string.
    entries = _registry()
    hits = [(k, v) for k, v in entries.items()
            if isinstance(v, dict) and v.get("move") == move]
    if not hits:
        return ""
    parts = [f"{k} — misuse: {v.get('misuse', '')[:110]}" for k, v in hits[:3]]
    return f"move={move}; frameworks that draw it: " + " | ".join(parts)


def shape_for(move: str, framework: str = "",
              seed: str = "") -> tuple[str, str]:
    """-> (shape id or "", comment). The question -> framework -> shape chain
    (analysis-rules AR-4, design-rules §4.0) executed to its last link.

    Until 0.1.533 the scaffold named the candidate frameworks in a comment and
    left the figure empty, on the reasoning that the relation lives in the
    content and a prescribed shape would repeat the mis-curation. Measured
    across five shipped deliverables the library's use count was zero: a
    comment is not a path. So a page whose outline declares a move now
    ARRIVES with the first shape of the first framework that draws it — or of
    the framework the outline names — in the figure slot, and the comment
    lists the alternatives. The choice stays the author's; the default is no
    longer "nothing". A framework the registry marks `drawn: "native"` names no
    shape, and a page that NAMES one gets an empty slot with a note saying why
    — deliberately not a sibling framework's shape, which is what it used to
    get. (Which frameworks those are is the registry's to say, not this
    docstring's: it once listed three and there are five.)

    **`seed` is why three decks stopped looking like one deck.** Until 0.1.596
    this returned `shapes[0]` of the first matching framework — deterministic on
    the MOVE alone — and the alternatives it listed were siblings of that same
    unit. Measured after an owner reported that three platforms' decks looked
    alike: across the four moves an outline can declare, the library offers 25
    shapes and the scaffold emitted **four**, the same four to everyone. Of 206
    units, 1.9% were reachable, and every `position` page ever scaffolded
    arrived as `p126-2x2-01`.

    The candidates are now every shape of every framework that draws the move,
    and `seed` — the page's own planned title — picks among them.
    Content-derived, so it stays REPRODUCIBLE (the same outline rebuilds the
    same deck, which `build_fixtures --check` gates on) while two documents
    about different things, and two pages of one document, get different
    drawings. An empty seed keeps the first-shape behaviour for a caller with
    no content yet.
    """
    if not move:
        return "", ""
    # A NAMED framework is the answer, not the head of a queue -- see
    # `frameworks_matching`, which owns that rule for this module and for
    # `tool_for`.
    hits = frameworks_matching(move, framework)
    # EVERY framework that draws this move, not just the first: the pool an
    # author chooses from should be the library's answer to the question, not
    # one entry's first row.
    pool: list[tuple[str, str]] = []
    drawn_natively = False
    for k, v in hits:
        for x in v.get("shapes") or []:
            if (ROOT / "assets" / "shapes" / f"{x}.svg").exists():
                pool.append((k, x))
        drawn_natively = drawn_natively or bool(v.get("drawn"))
    if not pool:
        # Native frameworks reach here, and the slot staying empty is correct --
        # a waterfall is drawn from its own numbers. What was NOT correct was
        # returning an empty note with it, so the scaffold said nothing about
        # why there is no shape and an author read the silence as an oversight.
        if any(v.get("drawn") == "native" for _k, v in hits):
            name = hits[0][0]
            return "", (f"{name} is drawn natively — no library shape; build "
                        f"it from the page's own numbers")
        return "", ""
    # A stable digest of the page's own words, never `random`: the same outline
    # must rebuild the same deck byte for byte.
    pick = (int(hashlib.sha256(seed.encode("utf-8")).hexdigest(), 16) % len(pool)
            if seed else 0)
    framework_name, shape = pool[pick]
    others = ", ".join(x for _, x in (pool[:pick] + pool[pick + 1:])[:3])
    return shape, (f"{framework_name} drawn with shape {shape}"
                   + (f"; alternatives: {others}" if others else "")
                   + (" — or draw the framework natively" if drawn_natively else ""))


def frameworks_matching(move: str, framework: str = "") -> list[tuple]:
    """-> [(name, entry)] the registry offers for this move, named one first.

    ONE resolution, read by `shape_for` and `tool_for`. They had a copy each
    for one commit, and the rule about a NAMED framework — that it is the
    answer rather than the head of a queue — is a decision this repository
    already paid to get right once (0.1.596: an author who asked for a
    benchmark table received Harvey balls). Two copies of a decision is one
    copy that will be corrected and one that will not.
    """
    if not move and not framework:
        return []
    entries = _registry()
    hits = [(k, v) for k, v in entries.items()
            if isinstance(v, dict) and v.get("move") == move]
    if framework:
        hits = [(k, v) for k, v in entries.items() if k == framework] or hits
    return hits


def tool_for(move: str, framework: str = "") -> tuple[str, str]:
    """-> (framework name, the command that draws it), or ("", "").

    The last link of the chain, and the one that was missing. `shape_for`
    answers a natively-drawn framework with an empty slot and a note saying
    why — correct, and as far as it went: the author was told a waterfall is
    built from its own numbers and left to find the tool themselves. Measured
    at 0.1.664, `scatter_svg` had shipped a release earlier with zero callers,
    a published rule pointing at it, and no path from a page that declares
    `correlate` to the script that draws one.

    0.1.533 settled how this is answered: the scaffold named its candidates in
    a COMMENT and five deliverables used the shape library zero times. A
    comment is not a path. So the command goes in the page's visible body,
    where D14 refuses it until an author has done something about it — the
    same treatment every other slot the scaffold leaves gets.

    Resolution mirrors `shape_for` exactly, including that a NAMED framework is
    the answer rather than the head of a queue: an author who asked for a
    benchmark table is told nothing rather than told to run the scatter tool.
    """
    for name, entry in frameworks_matching(move, framework):
        run = (entry.get("tool") or {}).get("run")
        if run:
            return name, run
    return "", ""


def shape_aspect(shape: str) -> float | None:
    """-> the unit's own width/height, from the generated geometry manifest."""
    try:
        g = json.loads((ROOT / "assets" / "shapes" / "geometry.json")
                       .read_text(encoding="utf-8"))["units"]
    except (OSError, ValueError, KeyError):
        return None
    return (g.get(shape) or {}).get("aspect")


# The scaffold's figure box, and the proportion it suits. A `<symbol>` maps its
# own viewBox into this viewport under `preserveAspectRatio`, so a unit of a
# different proportion is letterboxed inside it — and the letterboxing is real
# emptiness on the page, not a measurement artifact.
FIG_BOX = (640, 239)
FIG_BOX_ASPECT = FIG_BOX[0] / FIG_BOX[1]


def shape_fill(shape: str) -> float | None:
    """-> what share of the figure box this unit will actually ink, in percent.

    **Measured across the library: 160 of the 206 units come in under 55% of
    this box, and the median unit fills 43%** — which is the visual share two
    shipped decks reported, and the shape of the page an owner picked out by
    eye with "the figure is too small". The author was handed a box shaped for
    one unit (`p009-arrow-3d-01`, 2.68:1) and graded on the drawing.

    This does NOT resize anything to make the number go up. A 1.08:1 unit
    cannot fill a 2.68:1 box, and a scaffold that stretched it would be
    0.1.339's withdrawn fill floor in another costume — satisfying a metric by
    deforming the work. It says the number instead, at the moment the shape is
    chosen, so the choice is informed: pick a wider unit, give the page a
    layout whose cell is squarer, or put something beside the drawing.
    """
    a = shape_aspect(shape)
    if not a:
        return None
    w = min(FIG_BOX[0], FIG_BOX[1] * a)
    h = min(FIG_BOX[1], FIG_BOX[0] / a)
    return round(100 * w * h / (FIG_BOX[0] * FIG_BOX[1]), 1)


# The layouts a figure-led content page may take, and why `split` is not among
# them. `references/storyline-templates.md` states the rule this scaffold used
# to break on every page it emitted (search it for "figure-led page" — a line
# number here would rot, which CLAUDE.md convention 13 is about). NOTE ITS
# SCOPE: the sentence sits under Template 11's seed/first-meeting register,
# where "this number" is the pitch deck's 80% floor, and `inspect_layout.py`
# keys the share target on the storyline. The scaffold generalises it because
# the CELL GEOMETRY the rule reasons from is the same at every genre — half a
# row is half a row — while the number it cannot reach differs. What is
# generalised is "do not hand every page the narrowest cell", not the 80: "A `split` page gives the figure half the area and
# measures about 43% once the lede and the takeaway are counted, so it cannot
# reach this number however the words are trimmed. A figure-led page is `stack`
# or `split-wide` with the drawing in the wide cell."
#
# The scaffold hard-coded `body split` for EVERY content page until 0.1.592, so
# the one layout that rule excludes was the only one an author was handed. The
# cost was measured on a real build: nine of fourteen pages in one layout, seven
# content pages at exactly 35% visual share, and a deck the owner faulted by eye
# for figures that were too small. (35% is that DECK's number. The scaffold's
# own output measured 37% at its worst page — two different documents, and an
# earlier draft of this comment merged them into one row.) The deck GAP-024 records as ACCEPTED — the
# landscape roadshow deck at 6 layouts / 33.3% top share, not A1 — uses `split`
# ZERO times: it runs split-wide, stack, split-narrow, full-bleed, hero-band and
# sidebar-notes. Two different documents in this repository are called "the
# accepted reference" and they disagree about `split`: A1, the corpus's training
# anchor, is 22 of 30 pages `split` at 78.6% top share, which is why no bar can
# be drawn on top share (KNOWN_GAPS GAP-024). Name which one you mean.
#
# `stack` gives the drawing the whole width; `split-wide` gives it the wide cell
# — 62% of the row at 16x9, though `tokens/lumi-layouts.css` collapses it to one
# column in portrait — and keeps prose beside it. (That 62% is a COLUMN WIDTH,
# not a visual share; the shares quoted below are page areas.) Alternating is what stops the deck reading as one
# template — D9_layout_spread measures that and, per GAP-024, cannot yet fail,
# so the scaffold is where variety has to come from rather than from a gate.
#
# **The rotation is unconditional, and the first version of it was not.** It
# began by giving any unit too thin for the figure box `stack` regardless of its
# turn, on the reasoning that a thin drawing wants the whole width. Measured on
# the plan-driven path, which is the main one: `shape_for` resolves `compare` to
# a unit that inks 6.7% of the box and `position` to one that inks 38.4%, both
# under the threshold — so an outline whose pages repeat one analytical move put
# **every** content page in `stack`, a 100% top share. That is the defect this
# release exists to remove, reached through the door the release walked in by.
#
# The override also bought less than it looked: `shape_fill` measures a unit
# against FIG_BOX's PROPORTION, and that proportion does not change with the
# layout — a 6.7% unit inks 6.7% of whichever cell it is given. What a thin unit
# actually needs is a wider unit, which is what `shape_figure` already prints a
# comment asking for.
FIGURE_LAYOUTS = ("split-wide", "stack")


def figure_layout(index: int, shape: str | None) -> str:
    """-> the layout for content page `index` (0-based).

    `shape` is accepted and deliberately unused: the first version keyed on it
    and collapsed the rotation, and the parameter stays so the caller reads as
    "the layout for this page's figure" rather than a bare modulo. See the block
    comment above for the measurement.
    """
    del shape
    return FIGURE_LAYOUTS[index % len(FIGURE_LAYOUTS)]


def shape_figure(shape: str, label_a: str, label_b: str) -> str:
    fill = shape_fill(shape)
    note = ""
    if fill is not None and fill < 55:
        note = (f"\n        <!-- {shape} is {shape_aspect(shape):.2f}:1 in a "
                f"{FIG_BOX_ASPECT:.2f}:1 box, so it inks about {fill:.0f}% of "
                f"this cell. That reads as a thin page. Pick a wider unit "
                f"(assets/shapes/geometry.json lists every aspect), give this "
                f"page a layout with a squarer cell, or compose something "
                f"beside the drawing. Do not stretch it. -->")
    return f'''<svg viewBox="0 0 640 300" role="img"
        aria-label="{label_a}: replace the labels, keep or swap the shape">{note}
        <use href="#shape-{shape}" x="0" y="0" width="640" height="239"/>
        <text x="16" y="278" class="flbl" style="fill:var(--tx2)">{label_a}</text>
        <text x="624" y="278" text-anchor="end" class="flbl" style="fill:var(--tx2)">{label_b}</text>
      </svg>'''


def wordmark(override: str | None = None) -> str:
    """-> the cover/closing wordmark: the product this document is for.

    `brands/registry.json` has carried a per-brand `wordmark` since the registry
    was written and NOTHING read it — both generators hard-coded "LUMI Style",
    which is the design system's own name. It reached a product business plan,
    where the cover named the stylesheet rather than the company (owner review,
    0.1.521). The registry is the source; `--wordmark` covers a subject that is
    not a registered brand.
    """
    if override:
        return override
    reg = json.loads((ROOT / "brands" / "registry.json").read_text(encoding="utf-8"))
    return reg["brands"][reg["default"]]["wordmark"]
BRAND_GLOBE = ROOT / "assets" / "brand" / "lumivate" / "globe-field.svg"


def brand_globe():
    """The LUMIVATE field globe, prepared for embedding in a document.

    The default cover/closing mark (owner directive, 0.1.442 review: a
    deliverable shipped a fresh anonymous render instead of the brand).

    THE VENDORED FILE IS THE STANDALONE PUBLISHED FORM, so it carries its own
    `<style>` — a copy of the document palette plus a copy of both region
    palettes. Inline SVG shares the host document's style scope, so embedding
    that block redefines the host's tokens; the whole element comes out, and
    the host paints the mark from `tokens/`, where every rule in it also
    lives.

    0.1.447 first stripped only the palette SELECTORS and kept the rest, on
    the reading that the component's rules existed nowhere else. They do:
    `.gl-*` and `.trade` are `tokens/region-palette.css` and
    `tokens/region-palette-trade.css`, both generated and both `--check`ed.
    What had actually gone wrong was narrower — the trade palette was the one
    generated file the fixture preamble did not include, so the mark's eight
    blocs fell back to the UA default. Keeping a copy inside the SVG cured the
    symptom and froze a generated file inside a LOCKED asset where no
    regeneration check can see it drift. The preamble includes both palettes
    now, which is the same answer figure 9's black rectangles got in 0.1.391.

    The scaffold therefore owes the mark its palette: `test_new_deck.py` holds
    that every `--rg-*` the embedded globe references is defined by the CSS
    the preamble ships, which is the machine form of "the mark paints".
    """
    src = BRAND_GLOBE.read_text(encoding="utf-8")
    blocks = re.findall(r"<style\b[^>]*>", src)
    if len(blocks) != 1:
        raise SystemExit(f"FAIL  {BRAND_GLOBE.name} carries {len(blocks)} "
                         f"<style> blocks; this prepares exactly one, and a "
                         f"second would ship the palette it exists to remove")
    out = re.sub(r"<style\b[^>]*>.*?</style>", "", src, count=1, flags=re.S)
    if "<style" in out:
        raise SystemExit(f"FAIL  {BRAND_GLOBE.name} still carries a <style> "
                         f"block after stripping")
    return out

# The genres this scaffold can EMIT — a documented subset of the package's
# vocabulary, not a second copy of it. `marketing` has no skeleton of its
# own (storyline-templates.md folds it into Template 1 with sales), so it
# is absent here and present everywhere the vocabulary is just a label.
# check_repo's `genre vocabulary` guard holds this to the registry's names.
SCAFFOLDED = ("sales", "consulting", "internal", "training")
GENRES = SCAFFOLDED



def genre_card(genre: str) -> str:
    """The genre-conditional contract, as a comment the author reads at write
    time instead of discovering at check time.

    Ten rounds of one build were autopsied and two or three of them were
    exactly this: constraints that existed, enforced by checkers, knowable
    before the first word — the dash ban for the genre, the title-frame
    taxonomy, the colophon's provenance vocabulary — and discoverable only by
    failing them, because each lived inside the checker that fires on it.
    Every value below is IMPORTED from its checker. A card that retyped them
    would be the twenty-seventh copy-drift fix waiting to happen.
    """
    import check_design
    import check_prose
    dashes = ("em/en dashes are BANNED in this genre (M9 gates at 0; only a "
              "digit-digit range like 2026-08 is exempt — C1-C8 is not)"
              if genre in check_prose.DASH_BANNED else
              "em dashes allowed (internal analysis exemption)")
    return f"""<!-- THE CONTRACT FOR genre={genre} — read before writing, not after failing.
  words   · {dashes}
          · quoted rule-data (banned-phrase examples, decoy markup) belongs in
            FIGURE INK: text inside <svg> is invisible to M4/M9 by design;
            the same phrase in HTML prose fails the run
  titles  · M11 counts syntactic frames {check_prose.TITLE_FRAMES} — no one
            frame may carry more than 60% of the titles
  colophon· D6 accepts these provenance words: {", ".join(w for w in check_design.D6_PROVENANCE if w.isascii())}
          · and their Chinese equivalents when the deliverable is Chinese —
            the checker holds the full list; a card printed into an English
            document does not need to carry the other language's rule data
  roles   · every page role is defined by the pages this scaffold emits —
            compose FROM them (the closing title is the closing's h2, not a
            second cover h1); a role rewritten from memory drops out of the
            audit instead of failing it
  checks  · one command runs the whole stack and ends in one block:
            python3 scripts/ops/check_deliverable.py <file>
            read that block whole; fix everything it names in one pass -->"""


def open_trace(genre, geometry, storyline, entry_path, out_path=None):
    """-> a trace id, or None when no trace could be opened (and why, on
    stderr). The scaffold is where a build begins, so the record opens here
    and the build clock starts here; check_deliverable.py stops the clock and
    closes the record through the id the body carries. Fourteen consecutive
    builds of one deck left no trace while the ledger counted zero abandoned
    builds — the record was optional, so it was omitted.

    A storyline is required by the schema; without one the trace is not
    opened and the scaffold says so, because a trace is a declaration and
    a guessed declaration is the thing the schema exists to refuse.

    **The entry path is declared, never inferred.** Until 0.1.592 this passed
    path A whenever an outline existed and path B otherwise, and an outline is
    used on BOTH paths — so every build that happened to hand one over was
    recorded as an original four-beat build. Two replays of one frozen script landed in the ledger that way, with
    identical outline hashes, which is the precise record `--recipe` exists to
    make impossible. The same guessed-declaration rule that governs the
    storyline above governs this: no `--entry-path`, no trace.

    **The outline is not the recipe either.** It was passed as `--recipe`, so
    the file fingerprinted was the PLAN while the script that produced every
    page was fingerprinted by nothing — and an outline carries no version
    stamp, so those builds read as `unknown` vintage for ever. The builder does
    not exist yet at scaffold time — true of the SCAFFOLD, and false of the
    driver, which is handed the script on its own command line. `build.py`
    records it from `--script` after the fill (0.1.603); a hand-run
    `trace.py annotate --id <id> --recipe <build script>` is what a build
    assembled some other way still owes.

    **A trace belongs to the DOCUMENT, not to the round that scaffolded it**
    (0.1.602). A build is N rounds and the driver re-scaffolds each one, so
    this opened a fresh trace every round; `--fast` — the loop the build card
    recommends — closes none of them, so N-1 were left abandoned and the build
    clock covered only the last round. The local store had collected 28. When
    the deck being written already carries a `data-trace` that resolves in the
    store, that id is reused and the clock is left running.
    """
    if not storyline:
        print("<!-- no trace opened: a trace declares its storyline, and none "
              "was given (--storyline) -->", file=sys.stderr)
        return None
    if entry_path not in ("A", "B"):
        print("<!-- no trace opened: a trace declares its entry path, and none "
              "was given (--entry-path A|B). A is the four-beat discussion, B "
              "starts from a recipe; handing over an outline does not decide "
              "which, and guessing it is what put two replays in the ledger as "
              "original builds -->", file=sys.stderr)
        return None
    import subprocess
    tool = pathlib.Path(__file__).with_name("trace.py")
    # THE DECK'S OWN RECORD, IF IT HAS ONE. Reused whether or not it is closed:
    # identity is the document, and a mid-loop delivery round that closes the
    # trace must not send the next round back to opening a new one.
    if out_path is not None:
        existing = pathlib.Path(out_path)
        if existing.is_file():
            import re as _re
            m = _re.search(r'data-trace="(t-[0-9a-f]{12})"',
                           existing.read_text(encoding="utf-8"))
            # Resolved through `trace.py`'s OWN store resolver rather than a
            # path rebuilt here: `LUMI_TRACES`, the state directory and an
            # in-repo `evals/traces` all answer to it, and a second copy of
            # that answer is the shadow-implementation defect this package
            # keeps closing.
            if m:
                found = subprocess.run(
                    [sys.executable, str(tool), "annotate", "--id", m.group(1)],
                    capture_output=True, text=True)
                if found.returncode == 0:
                    print(f"<!-- trace {m.group(1)} reused: one document, one "
                          f"record; the build clock is already running -->",
                          file=sys.stderr)
                    return m.group(1)
    stage = deliverable_registry.STAGE_OF.get(geometry, "16x9")
    argv = [sys.executable, str(tool), "open", "--genre", genre,
            "--storyline", storyline, "--entry-path", entry_path,
            "--geometry", stage]
    opened = subprocess.run(argv, capture_output=True, text=True)
    if opened.returncode != 0:
        print(f"<!-- no trace opened: {opened.stderr.strip()[:200]} -->",
              file=sys.stderr)
        return None
    trace_id = opened.stdout.strip()
    subprocess.run([sys.executable, str(tool), "phase", "start", "build",
                    "--id", trace_id], capture_output=True, text=True)
    return trace_id


def preamble(genre, geometry, storyline=None, trace_id=None,
             lang="en", ask_quote=None):
    """Everything before the first page: the token block AND the sprite.

    Taken from the fixture rather than rebuilt, because the fixture is the
    reference implementation — the artifact `check_fixtures.py` asserts the
    checkers' verdicts against, so it is the one file guaranteed to render
    every role this package defines.
    """
    src = FIXTURE.read_text(encoding="utf-8")
    head = src[:src.index("</head>") + len("</head>")]
    # EVERYTHING between <body> and the first page, not the first <svg>. The
    # fixture opens with the icon sprite AND a second hidden svg carrying the
    # page ground; taking only the first left `#g-ground` dangling. A preamble
    # is whatever comes before the content, and guessing how many elements that
    # is has now been wrong twice.
    body_at = src.index("<body", src.index("</head>"))
    body_open_end = src.index(">", body_at) + 1
    sprite = src[body_open_end:src.index("<section", body_open_end)]
    # THE DEFAULT IS ENGLISH, and it is a default rather than a lock: a
    # deliverable the user asked for in another language is authored IN that
    # language, directly. 0.1.588 briefly required it to be derived from a
    # finished English deck, which wrote the same content twice and was the
    # wrong answer to the right problem — the owner's ruling, and she is right
    # about the cost.
    #
    # What survives is the cheap half. `--lang-asked` carries the user's OWN
    # WORDS rather than a boolean, because 0.1.587's boolean was typed by the
    # agent on the same command line as the language it was attesting to. A
    # quotation costs nothing to pass and is checkable by the one party who
    # knows: the person who either said it or did not.
    head = re.sub(r'(<html[^>]*\blang\s*=\s*)["\'][\w-]+["\']',
                  lambda m: f'{m.group(1)}"{lang}"', head, count=1)
    head = re.sub(r"<title>.*?</title>", "<title>REPLACE ME</title>", head, count=1)
    # The face rides along. design-rules.md requires it embedded, and when
    # embedding was a separate step, two deliverables in one week shipped with
    # zero @font-face blocks and rendered in the system stack. The fixture
    # itself stays font-free — it is a checker input, and the checkers read
    # markup, not metrics.
    head = head.replace("</head>",
                        "<style>\n" + embed_font.css() + "\n</style></head>")
    return (head + f'\n<body class="deck" data-theme="light" '
            f'data-geometry="{geometry}" data-genre="{genre}"'
            # ASKED, and quoted. English is the default and carries no record;
            # any other language without the user's words fails M16.
            + (f' data-lang-asked="{lang}"'
               f' data-lang-ask-quote="{html.escape(ask_quote, quote=True)}"'
               if ask_quote else "")
            # DECLARED, never inferred. D26 reads this to say which sections
            # the document neither covers nor declares; guessing a storyline
            # from the headings would make the report a measurement of the
            # guess.
            + (f' data-storyline="{storyline}"' if storyline else "")
            # The build's own record, so the check step closes the trace the
            # scaffold opened without anyone retyping an id.
            + (f' data-trace="{trace_id}"' if trace_id else "")
            + '>\n' + genre_card(genre) + '\n' + sprite)


def ground(src):
    m = re.search(r'(<svg class="ground".*?</svg>)', src, re.S)
    if m is None:
        raise ValueError('the source deck has no <svg class="ground"> block')
    return m.group(1)


def foot(n, total):
    return ('<div class="foot"><div class="terms"><span class="conf">'
            '<svg class="ic" aria-hidden="true"><use href="#i-shield"/></svg>'
            'Confidential &#183; internal use &#183; do not forward</span></div>'
            '<span class="site">www.lumivate.io</span>'
            f'<span>{n:02d} / {total}</span></div>')


# ONE OF EVERY BLOCK PATTERN THAT CARRIES A GATED CONTRACT, with the markup the
# FIXTURE uses — not the markup a class name suggests. `.swap` is the worked
# example: its rendering is `grid-template-columns: 1fr 34px 1fr` and it takes
# THREE children — a before, an arrow, an after. Written with two, the after
# lands in the 34px arrow column and wraps one word per line. That shipped, and
# its content was trimmed three times before anyone measured the box.
#
# `.card` and `.vow` joined at 0.1.450, from the conformance board's first
# refresh in fifteen releases: an agent given this scaffold reached for `.card`
# — named in SKILL.md's prose, holding a contract D19 GATES on — and wrote
# twelve of them without `.ledname`, because prose is what it had. That is this
# file's own opening paragraph happening to this file. Every entry in
# check_design's BLOCK_CONTRACTS now has a worked example here; when a contract
# is added there, its example belongs here in the same release.
ARROW = '<span class="arw">&#8594;</span>'


# ONE worked example of the shape library's mechanics, on the first content
# page. The scaffold used to hand an author an empty `.fig` with a comment in
# it, and three shipped deliverables referenced NONE of the 206 units — the
# rebuild spec's D1 calls that guaranteed rather than accidental, because an
# agent following the entry points had no path to the library.
#
# It teaches the MECHANICS, not the choice. Which shape a page wants is decided
# by the RELATION in its content (design-rules.md §4.1) and this file cannot
# know that; the library was mis-curated twice by reading names as
# classifications, so a scaffold that prescribed a shape would be the same
# mistake with a friendlier face. What it does show is the part that has no
# judgement in it and bites every time:
#
#   · EVERY unit in the library has a non-zero viewBox origin — all 206, not
#     some — so a bare `<use href="#shape-…">` renders shifted off frame. The
#     x/y/width/height below are not decoration.
#   · a `fill=` attribute on `<text>` loses to CSS, so a label written that way
#     silently takes the stylesheet's colour. `style="fill:"` is the form.
#   · the sprite is BUILT at emit time by embed_shapes.apply(), never pasted.
SCAFFOLD_SHAPE = "p009-arrow-3d-01"          # relation: order · process
SHAPE_FIGURE = f'''<svg viewBox="0 0 640 300" role="img"
        aria-label="A worked example: replace the shape and both labels">
        <use href="#shape-{SCAFFOLD_SHAPE}" x="0" y="0" width="640" height="239"/>
        <text x="16" y="278" class="flbl" style="fill:var(--tx2)">the step this end names</text>
        <text x="624" y="278" text-anchor="end" class="flbl" style="fill:var(--tx2)">and the step it leads to</text>
      </svg>'''
FIG_PLACEHOLDER = ("<!-- draw what the content IS: a flow, a timeline, a bridge,"
                   " a table. Shapes carry semantics; dashed means not built."
                   " embed_shapes.py --list names every unit the library ships."
                   " IF THE DRAWING SCALES NUMBERS, name its axes with the"
                   " shipped classes. Put class=axname-x on a text node below"
                   " the baseline, running level, and class=axname-y on one to"
                   " the LEFT of the vertical axis; tokens/ turns that one"
                   " upright to read bottom to top. Neither may lie across the"
                   " marks. figure_axis_overlap and figure_axis_orientation gate"
                   " both. A name is a ROLE: without the class a checker cannot"
                   " tell an axis name from a data label on its own mark, and"
                   " three conformance decks printed one across the plot. -->")

SAMPLES = [
    '      <p class="listhead">A heading over a block</p>\n'
    # `.gd` is the standard callout, NOT the tier-1 one: D3 budgets `.key` and
    # `.red`, and this line said "tier-one" while emitting neither, which
    # taught the wrong class for the rule it named.
    '      <p class="gd">A marked aside, one size everywhere.</p>\n'
    '      <p class="key">The tier-1 callout: the aside that changes a '
    'decision. One per page, and no more than a third of the pages.</p>\n'
    '      <ul><li>A bulleted list is a small set of criteria that must all '
    'hold.</li>\n'
    '      <li>A numbered list is a sequence someone performs in order.</li></ul>',

    '      <div class="card"><p class="ledname">The card&#8217;s subject</p>\n'
    '        <dl><dt>The question it answers</dt>\n'
    '          <dd>and the answer, in a sentence.</dd></dl>\n'
    '        <p class="verdict">The one line to carry away. Page 00.</p></div>',

    '      <div class="vows">\n'
    '        <div class="vow"><span class="vn">01</span>'
    '<p class="vt">The commitment, named</p>\n'
    '          <p class="vw">What it means in practice, and what it '
    'rules out.</p></div>\n'
    '        <div class="vow"><span class="vn">02</span>'
    '<p class="vt">A second commitment</p>\n'
    '          <p class="vw">Its consequence, stated the same way.</p></div>\n'
    '      </div>',

    '      <div class="band">'
    '<div><span class="k">Label</span><div class="v">41<span class="u">%</span>'
    '</div></div>'
    '<div><span class="k">Label</span><div class="v">312</div></div>'
    '</div>',

    '      <div class="grades">\n'
    '        <div class="gr g4"><i></i><p class="gn">The row&#8217;s subject</p>\n'
    '          <p class="gq">and what is true of it</p></div>\n'
    '        <div class="gr g2"><i></i><p class="gn">A second row</p></div>\n'
    '      </div>',

    '      <div class="swaps">\n'
    '        <div class="swap"><span class="no">What was believed</span>'
    + ARROW + '<span class="yes">What the measurement says</span></div>\n'
    '        <div class="swap"><span class="no">A second belief</span>'
    + ARROW + '<span class="yes">and its correction</span></div>\n'
    '      </div>',

    # The stat tile (0.1.521). The number first and the sentence under it -- the
    # order design-rules.md 7 fixes -- and the row's ONE key figure in accent,
    # the rest in ink. Three across is the shape the accepted deck used.
    '      <div class="stats">\n'
    '        <div class="stat"><p class="sv acc">1 copy</p>\n'
    '          <p class="sn">what the reader installs, and what it '
    'brings with it.</p></div>\n'
    '        <div class="stat"><p class="sv">12 platforms</p>\n'
    '          <p class="sn">the count, and what the count is of.</p></div>\n'
    '        <div class="stat"><p class="sv">190 lessons</p>\n'
    '          <p class="sn">a third figure, glossed the same way.</p></div>\n'
    '      </div>',

    # The field — brand.md's signature device, "many small marks, varying in
    # intensity, ordered by the thing they measure" — shipped in the tokens at
    # 0.1.379 and was used by nothing the audit measured. It rides in the
    # rotation so an author meets it; its rule rides with it: ONE MARK PER
    # DATUM. With no set behind it, delete the block — a shimmer with no data
    # is the decoration the brand file names as dishonest.
    '      <p class="listhead">A set with a shape: one mark per item, '
    'ordered by what it measures</p>\n'
    '      <!-- .field: one <i> per real datum, data-w 1..5 from the datum, '
    'order from the data. No set? delete this block. -->\n'
    '      <div class="field tall">'
    + "".join(f'<i data-w="{w}"></i>' for w in (1, 1, 2, 2, 3, 3, 3, 4, 4, 5, 5, 4, 3, 2, 2, 1))
    + '</div>',
]


# THE PART OPENER'S SUBJECT MARK, from the set vendored for it. design-rules
# §3 permits exactly one — a filled silhouette carrying no text of its own,
# reversed out of the field — and §6 vendored the set it comes from
# (`assets/icons/koboyo/`, 36 of them, "for part-opener subject marks").
# `tokens/` has styled `.openmark` since the
# opener composition landed. Neither this scaffold nor any fixture drew one
# until 0.1.547, so three conformance decks reached the reader with five bare
# openers between them and `opener_subject_mark` (0.1.546) failed all of them.
#
# One per part, never the same twice: the mark says what the part is about, so
# two identical ones say the two parts are the same thing. WHICH silhouette
# fits WHICH part is the author's choice — these are placeholders, and the
# emitted comment says so.
OPENER_MARKS = ("chart", "globe", "key", "rocket", "clipboard", "scale",
                "shield", "cpu")


def opener_mark(index: int) -> str:
    """-> the `.openmark` block for part `index`, or "" if the set is missing.

    Reads the vendored file rather than restating its geometry: a path copied
    into this script is a second copy of an asset, and `assets/icons/koboyo/`
    is the authority. A missing set yields no mark rather than a broken one —
    the gate then says so, which beats this script inventing a silhouette.
    """
    root = ROOT / "assets" / "icons" / "koboyo"
    names = [n for n in OPENER_MARKS if (root / f"{n}.svg").exists()]
    if not names:
        return ""
    name = names[index % len(names)]
    svg = (root / f"{name}.svg").read_text(encoding="utf-8").strip()
    note = ("<!-- design-rules \u00a73: ONE filled silhouette, and it is the "
            f"part's subject.\n           `{name}` is a placeholder from "
            "assets/icons/koboyo/ (36 to choose from);\n           two openers "
            "may not carry the same mark. -->")
    return f'<div class="openmark">{svg}</div>\n      {note}'


def spec_servable(move: str, ref: str, out_path) -> bool:
    """-> whether the scaffold will write a skeleton for this beat's `data:`.

    The page emission and the skeleton writer used to answer this separately,
    and disagreed: a beat pointing outside the deck's directory got no file and
    a `data-figure-spec` anyway.
    """
    if not ref or str(move or "").strip().lower() not in figure_spec.MOVE_FIELDS:
        return False
    if out_path is None:
        return True          # no deck on disk; the author places it themselves
    home = out_path.parent.resolve()
    return (out_path.parent / ref).resolve().is_relative_to(home)


def write_spec_skeletons(plan, out_path):
    """Write a skeleton for every beat that points at one.

    -> ([(path, move)] written, [what could not be done]). The second list is
    why this returns a pair: four silent `continue`s meant a spec that was
    never written, one left stale by a changed beat, one outside the deck's
    directory and one an unwritable disk all produced the same nothing.

    **Skeletons only, and never over an existing file.** The scaffold's job is
    to give the author a shape with every field present and no value invented;
    the numbers are the author's, and a rebuild that overwrote them would
    destroy the one artefact this whole chain exists to hold. A spec that is
    already there is left exactly as it is.

    Silent when there is no `--out`: the spec sits beside the deck, so without
    a deck on disk there is no `beside`. The page still declares
    `data-figure-spec`, and `check_design`'s D42 reports the dangling
    reference — which is the correct reading of "the author has not written it
    yet" rather than a scaffold guessing at a directory.
    """
    if not out_path:
        return [], []
    written, notes = [], []
    for sec in plan or []:
        ref = str(sec.get("data") or "").strip()
        move = str(sec.get("move") or "").strip().lower()
        if not ref:
            continue
        # SAID, not skipped. A refusal used to be a silent `continue`, so the
        # author met the problem later, through a different tool, as "could
        # not be read" — pointed at a file nobody had told them was never
        # written. And a spec sits BESIDE the deck: `data: ../escaped.json`
        # wrote outside the deck's directory, which is a silent success in the
        # wrong place.
        if not spec_servable(move, ref, out_path):
            notes.append(
                f"{ref} was NOT written: the beat declares move {move!r}, "
                f"which is not one of "
                f"{', '.join(sorted(figure_spec.MOVE_FIELDS))}"
                if move not in figure_spec.MOVE_FIELDS else
                f"{ref} was NOT written: it resolves outside the deck's own "
                f"directory, and a figure spec lives beside the document it "
                f"belongs to")
            continue
        target = (out_path.parent / ref).resolve()
        if target.exists():
            existing, problem = figure_spec.load(target)
            if problem:
                notes.append(f"{ref} exists and could not be read ({problem}); "
                             f"it was left exactly as it is")
            elif str((existing or {}).get("move")) != move:
                # Never overwrite the author's numbers — but never be silent
                # about a file that no longer matches the beat pointing at it.
                notes.append(f"{ref} exists and declares move "
                             f"{(existing or {}).get('move')!r} while the beat "
                             f"now declares {move!r}. It was left alone; "
                             f"D42 fails the page until the two agree")
            continue
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                json.dumps(figure_spec.skeleton(move), indent=1,
                           ensure_ascii=False) + "\n", encoding="utf-8")
        except OSError as exc:
            notes.append(f"{ref} could not be written ({exc})")
            continue
        written.append((target, move))
    return written, notes


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--genre", choices=GENRES, default="internal")
    # The composition vocabulary is IMPORTED, not retyped. It used to be a
    # literal pair here while the trace declared (16x9, a4, laptop) and
    # inspect_layout declared five viewports — three lists for one word, with
    # no guard between any pair.
    ap.add_argument("--geometry", choices=deliverable_registry.COMPOSITIONS,
                    default="landscape")
    ap.add_argument("--storyline", choices=deliverable_registry.STORYLINES,
                    help="seed the agenda from this storyline's typical "
                         "sections. A CHECKLIST, never a template: the rows "
                         "are furniture to replace, and a storyline with no "
                         "checklist says so rather than emitting nothing.")
    ap.add_argument("--entry-path", dest="entry_path", choices=("A", "B"),
                    help="how this document reached the workflow: A is the "
                         "four-beat discussion, B starts from a recipe. "
                         "DECLARED, never inferred — handing over an outline "
                         "does not decide it, and guessing it recorded two "
                         "replays as original builds. Without it no trace "
                         "opens, on the same rule as --storyline.")
    ap.add_argument("--outline", type=pathlib.Path,
                    help="the analysis beat's outline. Each content page is "
                         "emitted carrying its planned title and implication "
                         "and declaring its analytical move, so the beat is an "
                         "INPUT rather than a document written and then "
                         "forgotten (analysis-rules.md AR-3).")
    ap.add_argument("--wordmark",
                    help="the cover/closing wordmark. Defaults to the default "
                         "brand's `wordmark` in brands/registry.json; pass this "
                         "for a subject that is not a registered brand.")
    ap.add_argument("--lang", default="en",
                    help="the deliverable's output language, BCP-47, for "
                         "<html lang>. **Default: en.** American English is "
                         "LUMI's default output language (writing-rules "
                         "section 0). Pass another code when the USER asked "
                         "for it — the deck is then authored in that language "
                         "directly, not translated from English.")
    ap.add_argument("--lang-asked", metavar="QUOTE",
                    help="the user's OWN WORDS asking for --lang, verbatim. "
                         "Required for any language but English. Not your "
                         "summary of them, and never the fact that the source "
                         "material or this conversation was in that language — "
                         "neither is an instruction (FM-18). It is written into "
                         "the document as `data-lang-ask-quote`, where the "
                         "owner reads it.")
    ap.add_argument("--out", type=pathlib.Path,
                    help="write the scaffold here instead of to stdout. "
                         "Stdout stays the default; this exists so a caller "
                         "does not have to capture it")
    ap.add_argument("--no-trace", action="store_true",
                    help="do not open a build trace (fixtures, tests, dry runs). "
                         "A real build keeps the default: the record opens "
                         "here, and check_deliverable.py closes it.")
    ap.add_argument("--pages", type=int, default=None,
                    help="content pages, not counting cover, agenda, the part "
                         "openers and the closing. Default: the number of "
                         "sections in --outline, or " + str(DEFAULT_PAGES) +
                         " with no outline. Pass it to scaffold a subset on "
                         "purpose")
    ap.add_argument("--parts", default="A,B",
                    help="part letters, comma separated. Two is the default: "
                         "one part is not a part, it is a document.")
    args = ap.parse_args(argv)

    # SAID BEFORE ANYTHING IS BUILT, because the fix is a question for the user
    # and not an edit to the document. Three validation rounds produced a
    # language nobody asked for; the quotation is what makes the claim visible
    # to the one party who can check it.
    if args.lang.split("-")[0].lower() != "en" and not args.lang_asked:
        sys.exit(
            f"--lang {args.lang} without --lang-asked: American English is "
            f"LUMI's default output language, and another language is asked "
            f"for — never inferred from the source material, the venue, the "
            f"audience, or the language of this conversation (writing-rules "
            f"section 0, FM-18). If the user asked, quote them:\n"
            f"    --lang {args.lang} --lang-asked \"<their words>\"")
    if args.lang_asked and len(_ASK_TOKEN.findall(args.lang_asked)) < 3:
        sys.exit(f"--lang-asked {args.lang_asked!r} is a fragment that would "
                 f"match anything. Quote what the user actually said.")

    src = FIXTURE.read_text(encoding="utf-8")
    g = ground(src)
    parts = [x.strip() for x in args.parts.split(",") if x.strip()]
    mark = wordmark(args.wordmark)
    plan = outline_sections(args.outline)
    omissions = outline_omissions(args.outline)
    # THE OUTLINE KNOWS HOW MANY PAGES THERE ARE. `--pages` defaulted to a
    # literal whatever the outline said, so a ten-title plan silently emitted
    # six content pages and four findings had nowhere to go -- silently,
    # because the scaffold is valid either way and no check compares a scaffold
    # to a plan. An explicit `--pages` still wins: an author may deliberately
    # scaffold a subset.
    if args.outline and plan and args.pages is None:
        args.pages = len(plan)
        print(f"note  --pages {args.pages}, from the {len(plan)} section(s) in "
              f"{args.outline.name}", file=sys.stderr)
    if args.pages is None:
        args.pages = DEFAULT_PAGES
    # cover, agenda, closing, + openers; training appends its reference page.
    apparatus = 1 if args.genre == "training" else 0
    total = args.pages + 3 + len(parts) + apparatus
    trace_id = None if args.no_trace else open_trace(
        args.genre, args.geometry, args.storyline, args.entry_path, args.out)
    out = [preamble(args.genre, args.geometry, args.storyline, trace_id,
                    args.lang, args.lang_asked)]

    # The cover title carries TWO INKS: the claim in ink, the noun the deck is
    # about as lime on its own dark chip (`.subj`) — the same green the part
    # openers carry at page scale, so the title marks what the page is FOR in
    # the deck's one event colour rather than decorating it.
    out.append(f'''<section class="page cover" id="cover">
  {g}
  <div class="body cover-grid">
    <div class="typeblock">
      <p class="wordmark">{mark}</p>
      <h1>A title that states the argument about its
      <span class="subj">subject</span></h1>
      <p class="sub">One sentence saying what this is.</p>
    </div>
    <!-- The brand mark. Keep it: with no explicit instruction from the
         owner this is the mark, and D40 fails a deck that carries
         something else without `<body data-brand-mark="…">` naming the
         replacement that was asked for. -->
    <div class="markcell" data-globe>{brand_globe()}</div>
    <div class="attrs">
      <div><span class="k">Label</span><span class="v">value</span></div>
      <div><span class="k">Label</span><span class="v">value</span></div>
    </div>
  </div>
  {foot(1, total)}
</section>''')

    # THE AGENDA IS THE LAUNCH SEQUENCE (0.1.519, owner review: the grades
    # agenda read as quiet apparatus). One row per part: a numbered chip, the
    # part's claim at title weight — QUOTE the opener's claim, D27 holds the
    # mirror — and a quiet run line. The storyline checklist seeds the run
    # lines, chunked across parts: a checklist applied at the end, never a
    # template to start from, exactly as the registry's comment demands.
    sections = (deliverable_registry.TYPICAL_SECTIONS.get(args.storyline, ())
                if args.storyline else ())
    chunks: list[list[str]] = [[] for _ in parts]
    for i, checklist_entry in enumerate(sections):
        chunks[i * len(parts) // max(1, len(sections))].append(
            deliverable_registry.section_name(checklist_entry))
    rows = ""
    for i, q in enumerate(parts):
        run = (" &#183; ".join(chunks[i]) if sections
               else "which pages, and what they cover")
        rows += (
            f'      <div class="lrow">\n'
            f'        <div class="ln">{i + 1:02d}</div>\n'
            f'        <div><p class="gn">What Part {q} argues, its key phrase '
            f'<span class="hl">set in the light</span></p>\n'
            f'          <p class="gq">{run}</p></div>\n'
            f'      </div>\n')
    if args.storyline and not sections:
        # A storyline with no checklist SAYS SO. Emitting nothing here is
        # how `proposal` shipped for eight releases looking like a
        # storyline whose sections were all present.
        rows += (f'      <p class="gq">no typical-section checklist exists '
                 f'for {args.storyline}; completeness is yours to establish '
                 f'at the storyline review</p>\n')
    out.append(f'''<section class="page" id="agenda">
  {g}
  <div class="body stack no-lede">
    <div class="fill">
      <div class="launch">
{rows}      </div>
    </div>
  </div>
  {foot(2, total)}
</section>''')

    n = 3
    # The figure ordinal is the FIGURE's, not the page's. It was `n - 2` until
    # 0.1.521, which counted PAGES: every part opener consumed a number no
    # drawing ever carried, so a two-part scaffold emitted Figure 3, 4, 8, 9,
    # 11 ... and the tracked fixture shipped six holes. Both accepted
    # deliverables reproduced the pattern from this generator -- one numbered
    # two drawings `Figure 3`, the other ran 2-8 then 12-14 then 9-11. A reader
    # says "go back to figure four" out loud, so a hole makes the reference
    # wrong and a repeat makes it ambiguous; check_design.py D30 reads the
    # sequence back.
    figno = 1
    per = max(1, args.pages // max(1, len(parts)))
    for pi, part in enumerate(parts):
        # THE OPENER CARRIES class="page opener". The lime background is a
        # class, not a layout: without it the page renders blank.
        out.append(f'''<section class="page opener" id="open{part}">
  {g}
  <div class="body full-bleed no-lede">
    <div class="bleed openframe">
      <div class="openpart">Part {part}</div>
      <div class="openclaim">What this part argues</div>
      <div class="openrun">How many pages, and what they cover.</div>
      {opener_mark(pi)}
    </div>
  </div>
  {foot(n, total)}
</section>''')
        n += 1
        count = per if pi < len(parts) - 1 else args.pages - per * (len(parts) - 1)
        for i in range(count):
            block = SAMPLES[(pi * per + i) % len(SAMPLES)]
            figure = SHAPE_FIGURE if (pi == 0 and i == 0) else FIG_PLACEHOLDER
            # The beat's output, carried in. Where an outline exists, the page
            # ARRIVES holding the finding it was planned to state and the
            # implication it was planned to leave, and declares the move that
            # produced them. Without one, the slots stay as prompts.
            sec = plan[len(plan) and (pi * per + i) % len(plan)] if plan else {}
            title = sec.get("title") or "A title naming its subject and carrying a fact"
            take = sec.get("implication") or "The line the reader carries off this page."
            move = sec.get("move", "")
            hint = framework_for(move)
            sup = sup_for(move)
            adecl = f' data-analysis="{move}"' if move else ""
            # SEEDED WITH THE PAGE'S OWN TITLE, so two documents about
            # different subjects do not arrive as the same drawings.
            shape, shape_note = shape_for(move, sec.get("framework", ""),
                                          seed=f"{title}|{move}")
            if shape:
                figure = shape_figure(shape, "what this end names", "and what it leads to")
                hint = (hint + "; " if hint else "") + shape_note
                _tool_name, _tool_run = tool_for(move, sec.get("framework", ""))
                if _tool_run:
                    # The shape is the default and the tool is the other
                    # answer. Naming it here costs nothing and is how an author
                    # discovers that this move can be drawn from its numbers.
                    hint += (f"; or draw it from data: add `data:` to the beat "
                             f"and run {_tool_run}")
            # A natively-drawn framework has no library shape, so this is where
            # an author was previously left with a comment. The command goes in
            # the VISIBLE body: `d14_placeholders` strips comments and <svg>
            # before it looks, so a slot hidden in either is a slot no gate can
            # refuse, and the author who ignores it ships a finished-looking
            # page. The bracket is what D14 keys on and stays under its 60
            # character window; the command sits beside it, unbracketed.
            toolslot, specdecl = "", ""
            dataref = str(sec.get("data") or "").strip()
            # ONE RULE, asked in both places: a page declares its spec only
            # where `write_spec_skeletons` would serve it. Declaring one it
            # refused points the reader at a file that does not exist and
            # never will.
            if dataref and not spec_servable(move, dataref, args.out):
                dataref = ""
            if dataref:
                # THE PAGE NAMES ITS OWN SPEC. Without this the drawing and the
                # numbers behind it have no link a checker can follow, which is
                # the state 58 shipped figures were in: one declared its data.
                specdecl = f' data-figure-spec="{html.escape(dataref)}"'
            # A BEAT THAT NAMES ITS DATA IS A DATA FIGURE, and the tool wins
            # over the library shape. This used to be `if not shape:`, so a
            # move with ANY shape-bearing framework never reached its tool —
            # and four of the five moves have one. Measured: `compare`,
            # `decompose` and `bridge` all resolved to a shape, so
            # `benchmark_svg`, `breakdown_svg` and `waterfall_svg` shipped with
            # no path from a page to them. That is 0.1.664's defect exactly,
            # three times over, in the release that added the tools — and
            # `correlate` hid it, being the one move with no shape at all.
            fw_name, run = tool_for(move, sec.get("framework", ""))
            if run and (dataref or not shape):
                # The demo drawing goes with it. Page one of a scaffold
                # carries SHAPE_FIGURE as furniture regardless of the move,
                # and seen next to "draw this figure" the two contradict:
                # the box held a four-headed arrow — a `position` unit — on
                # a page that declares `correlate`. Caught by looking at the
                # render, by nothing that measures it.
                figure = FIG_PLACEHOLDER
                shape = ""
                cmd = (run.replace("<spec.json>", dataref) if dataref
                       else run)
                where = (f' The numbers go in <code>'
                         f'{html.escape(dataref)}</code>, which the '
                         f'scaffold has written as a skeleton.'
                         if dataref else "")
                toolslot = (
                    f'\n      <p class="notes">[TO FILL: draw this figure]'
                    f' \u00b7 {fw_name} is drawn from its own numbers, not '
                    f'from a library shape.{where} '
                    f'<code>{html.escape(cmd)}</code>'
                    f' renders one from a JSON spec: paste its SVG here in '
                    f'place of this line.</p>')
            fignote = (f"\n      <!-- {hint} -->" if hint else "")
            lay = figure_layout(figno - 1, shape)
            # `.body.stack` is "one full-width centerpiece": its grid declares
            # `auto 1fr` — a lede and ONE cell. A page that hands it three
            # children puts the figure in an implicit auto row, and it renders
            # at 3% of the page. That is measured, on the first scaffold built
            # after this rotation existed, which is why the rotation ships with
            # the child structure rather than only the class name.
            if lay == "stack":
                cells_open = ("    <div class=\"fill\">\n" + block
                              + "\n      <!-- stack gives ONE cell the 1fr row,"
                                " so the block and the drawing share it -->")
            else:
                cells_open = ("    <div class=\"fill\">\n" + block
                              + "\n    </div>\n    <div class=\"fill\">")
            # THE OUTLINE'S DECLARED OMISSIONS, ON THE LAST CONTENT PAGE.
            # Not the agenda — D35 gates that page to the launch sequence — and
            # not the closing, whose contents `page-contracts.md` enumerates, so
            # adding to them is a rule revision rather than a scaffold change.
            # The shape copies `build_fixtures.py`'s reference implementation,
            # which is what `check_fixtures` already asserts against.
            scope_notes = ""
            if omissions and pi == len(parts) - 1 and i == count - 1:
                scope_notes = "\n" + "\n".join(
                    f'      <p class="scope-note" data-omitted="{o["section"]}">'
                    f'This deck does not cover {o["said"]}: {o["reason"]}.</p>'
                    for o in omissions)
            out.append(f'''<section class="page" id="p{n}"{adecl}{specdecl}>
  {g}
  <div class="body {lay}">
    <div class="lede">
      <p class="eyebrow"><svg class="ic" aria-hidden="true"><use href="#{PAGE_ICONS[(n - 1) % len(PAGE_ICONS)]}"/></svg>Part {part} &#183; this page&#8217;s label</p>
      <!-- The icon is a PLACEHOLDER rotated so no two pages start alike.
           design-rules §6: within one document an icon means exactly one
           thing, so replace it with this page's own subject.
           `embed_icons.py --search <term>` finds one among 2007. -->
      <h2 class="t">{title}</h2>
      <p class="sup">{sup}</p>
    </div>
{cells_open}{fignote}
      <div class="fig">{figure}{toolslot}
      <div class="cap"><span class="n">Figure {figno}</span> A title stating a
      conclusion</div></div>
      <!-- design-rules §4 rule 8: the caption holds the number and the name and
           NOTHING ELSE. The source line is the drawing's own last text node
           (rule 17) — see the `<text class="fnote">` at the foot of the figure
           above. Run together in one caption the two read as one sentence, and
           the line break lands in the source so the name never appears to
           wrap. -->
      <p class="take">{take}</p>{scope_notes}
    </div>
  </div>
  {foot(n, total)}
</section>''')
            n += 1
            figno += 1

    if apparatus:
        # Template 4's arc ends on the pages a learner returns to. The page is
        # DECLARED apparatus (design-rules.md §3): D16's visual-share target
        # exempts it, up to the one-in-five ceiling.
        out.append(f'''<section class="page" id="gloss" data-role="apparatus">
  {g}
  <div class="body stack">
    <div class="lede">
      <p class="eyebrow"><svg class="ic" aria-hidden="true"><use href="#i-book-open"/></svg>Reference</p>
      <h2 class="t">The terms this document uses, defined once</h2>
      <p class="sup">The page a learner returns to after the session.</p>
    </div>
    <div class="fill">
      <dl class="gloss">
        <dt>Term</dt><dd>What it means in this document, one sentence.</dd>
        <dt>A second term</dt><dd>and its definition, with its source where a
        trainee will repeat it.</dd>
      </dl>
    </div>
  </div>
  {foot(n, total)}
</section>''')
        n += 1

    out.append(f'''<section class="page closing" id="close">
  {g}
  <div class="body cover-grid">
    <div class="typeblock">
      <p class="wordmark">{mark}</p>
      <h2>What the reader carries out about its
      <span class="subj">subject</span></h2>
      <p class="sub">The argument in one paragraph.</p>
    </div>
    <!-- The brand mark. Keep it: with no explicit instruction from the
         owner this is the mark, and D40 fails a deck that carries
         something else without `<body data-brand-mark="…">` naming the
         replacement that was asked for. -->
    <div class="markcell" data-globe>{brand_globe()}</div>
    <div class="attrs">
      <div><span class="k">Label</span><span class="v">value</span></div>
    </div>
    <p class="colophon">Built with lumi-style {versioning.skill_version()} &#183; source: WHERE THE
    NUMBERS CAME FROM.</p>
  </div>
  {foot(total, total)}
</section>''')

    # The runtime turns every [data-globe] — the cover and the closing. It
    # respects prefers-reduced-motion, and with JavaScript off the reader keeps
    # the exact static frame above. Rotation is part of the mark's contract
    # (owner directive): a still field globe is the fallback, not the design.
    out.append(embed_globe.build())
    out.append("</body></html>")
    # BUILT, never pasted — the same rule the globe runtime above follows.
    doc = embed_shapes.apply("\n".join(out))
    # STDOUT REMAINS THE DEFAULT, because that is what every existing caller
    # and every recorded recipe uses. `--out` exists because "this script
    # prints to stdout, redirect it" was the single most-repeated build trap on
    # record, and because a driver that has to capture stdout cannot record the
    # command through `debug_log run`, which writes stdout itself.
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(doc + "\n", encoding="utf-8")
        print(f"note  wrote {args.out}", file=sys.stderr)
        wrote, notes = write_spec_skeletons(plan, args.out)
        for target, move in wrote:
            print(f"note  wrote {target} — a `{move}` skeleton with every "
                  f"field present and no value invented", file=sys.stderr)
        for note in notes:
            print(f"note  {note}", file=sys.stderr)
        if notes:
            # The scaffold did not do everything it was asked. On a read-only
            # mount every page would point at a spec that was never written
            # and the run still exited 0.
            print(f"note  {len(notes)} figure spec(s) were not written; the "
                  f"pages that name them will fail D42 until they are",
                  file=sys.stderr)
            return 1
    else:
        print(doc)
    print(f"<!-- scaffold: {total} pages, standard order. Every icon reference "
          f"resolves, every block carries its contract, and each opener carries "
          f"its class. check_design.py's D19 holds all three. -->", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
