#!/usr/bin/env python3
"""Build the tracked fixture deliverables that the check scripts are tested on.

`check_prose.py`, `check_design.py` and `inspect_layout.py` have never had a
regression test, because until now this repository contained no deliverable to
measure. The only ones that existed sat in the gitignored `docs/`, carrying a
client name that red line 9 bars from the repository. So the gates that are meant
to make output quality portable across models were themselves unverified.

Two fixtures, both synthetic and both client-free — a fictional metering
programme, `www.example.org` as the origin, no engagement fact anywhere:

    fixtures/deck-pass.en.html     a well-formed deliverable; every check passes
    fixtures/deck-broken.en.html   the same deck with one named defect per metric

The broken one matters more. A fixture that only proves "clean input passes"
cannot tell a working check from a check that returns ok unconditionally — which
is exactly the failure this repository spent 0.1.350 removing from
`inspect_layout.py`. Each defect is planted to trip a *named* metric, and
`check_fixtures.py` asserts which finding fired, not merely that something did.

They are generated rather than hand-written so the token block cannot drift from
`tokens/`: a fixture grading a document against a palette the skill no longer
ships is worse than no fixture.

    python3 scripts/build/build_fixtures.py            # write
    python3 scripts/build/build_fixtures.py --check    # verify current (CI)
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

ROOT = next(p for p in pathlib.Path(__file__).resolve().parents
            if p.name == "scripts").parent
OUT = ROOT / "fixtures"
STALE = "is stale or missing; re-run without --check"

# The icon sprite comes from the vendored library via embed_icons.sprite(), so
# the fixture exercises the same path a deliverable uses and cannot drift from
# the library it claims to demonstrate.
# --- scripts path bootstrap (canonical; the bootstrap guard enforces this) ---
# Bare-name sibling imports must resolve from any drawer depth: walk up to
# the scripts/ root and APPEND it and its drawers to sys.path — append,
# never insert(0), so the standard library and the caller's environment
# always win. Drawer order is lib-first and the scripts ROOT LAST on
# purpose: the emergency path overwrites a PR's lib/ files with trusted
# copies, and lib-first means a file PLANTED at the scripts root can never
# outrank them (the shadowing the PR #92 review demonstrated).
import pathlib as _bs_pathlib  # noqa: E402
import sys as _bs_sys  # noqa: E402

_SCRIPTS_ROOT = next(p for p in _bs_pathlib.Path(__file__).resolve().parents
                     if p.name == "scripts")
for _sub in ("lib", "render", "check", "build", "ops", ""):
    _p = str(_SCRIPTS_ROOT / _sub) if _sub else str(_SCRIPTS_ROOT)
    if _p not in _bs_sys.path:
        _bs_sys.path.append(_p)
del _bs_pathlib, _bs_sys, _SCRIPTS_ROOT, _sub, _p
# --- end bootstrap ---
import new_deck  # noqa: E402
import versioning  # noqa: E402
from embed_icons import sprite  # noqa: E402

TERMS = "Confidential &#183; internal use &#183; do not forward"
SITE = "www.example.org"

# The producing-skill version, for the colophon the cover rule requires. Read
# from SKILL.md so it cannot drift; the fixtures already regenerate every
# release because the embedded token block carries the version stamp.
VERSION = versioning.skill_version(ROOT)

# The cover/closing mark, inlined verbatim from the generated asset.
# The cover/closing mark is the LUMIVATE FIELD GLOBE — the locked brand asset
# and, since the 0.1.442 owner review, the default mark a deliverable embeds
# (BUG#1 there was a fresh anonymous render where the brand belonged).
# Prepared by new_deck.brand_globe(), which strips the vendored file's copy of
# the DOCUMENT palette (inline SVG shares the host's style scope) and keeps the
# component's own rules — the `.gl-*` rendering and the `.trade` region palette
# live in that block and nowhere in tokens/. Static here: the fixture is a
# checker input and ships no scripts; the scaffold embeds the runtime that
# turns it.
GLOBE = new_deck.brand_globe().strip()

# Titles deliberately spread across five frames. M11 fails a deck whose titles
# all take one shape, and a fixture that trips it by accident teaches nothing.
# Each page carries its subject icon (design-rules §3's eyebrow contract), one
# icon one meaning across the deck.
PAGES = [
    ("radar", "Coverage", "Metering coverage reached 41% of the estate",
     "Two regions carry most of the shortfall, and both are rural.",
     ["Rural feeders were surveyed last.", "Access needs a scheduled outage."]),
    ("layers", "Backlog", "Why the install backlog stopped shrinking",
     "Crew hours moved to fault response in the second quarter.",
     ["Fault response has first call on crews.", "Installs resume when the queue clears."]),
    ("gauge", "Reads", "Read success: 96.2% on urban feeders, 71.4% on rural",
     "The gap is signal, not hardware, and it follows terrain rather than meter age.",
     ["Signal strength tracks terrain closely.", "Meter age shows no correlation."]),
    ("scale", "Cost", "Each avoided truck roll returns 38 units",
     "The figure holds only where a read succeeds on the first attempt.",
     ["A second attempt erases the saving.", "Third attempts cost more than a visit."]),
    ("bell", "Risk", "Three assumptions carry the forecast",
     "Each one is checkable, and one of them has already moved.",
     ["Crew availability held through June.", "Signal coverage assumptions have not."]),
    ("route", "Sequence", "Install density beats install count",
     "Clustering work by feeder cuts travel more than raising the daily target.",
     ["Travel is the largest non-productive cost.", "Density compounds across a week."]),
    ("target", "Quality", "What a failed read actually costs",
     "A failed read is not a missing number; it is an estimate that later has to be corrected.",
     ["Estimates propagate into billing.", "Corrections arrive two cycles later."]),
    ("git-branch", "Signal", "Can the rural gap close without new hardware?",
     "Relay siting explains more of the variance than any equipment choice does.",
     ["Relay siting was never optimised.", "Two candidate sites are already owned."]),
    ("list-checks", "Crews", "Crew training pays back inside one quarter",
     "Trained crews complete more first-attempt reads, which is where the return sits.",
     ["First-attempt rate rises with training.", "The effect persists after six months."]),
    ("book-open", "Data", "The estimate rate is the number to watch",
     "It moves before the read rate does, so it gives roughly a cycle of warning.",
     ["Estimate rate leads read rate.", "One cycle is enough to reschedule."]),
    ("ban", "Scope", "What this analysis does not cover",
     "Commercial meters, prepayment customers, and anything outside the two named regions.",
     ["Commercial meters have their own programme.", "Prepayment is a separate contract."]),
    ("funnel", "Evidence", "Every figure here traces to the meter management system",
     "Extracts are dated, and the extract date is on each figure.",
     ["Extracts are dated at source.", "No figure is carried between extracts."]),
    ("split", "Decision", "Reschedule the rural phase, or accept the estimate rate",
     "Those are the two options; a third that changes neither has not been found.",
     ["Rescheduling costs one quarter.", "Accepting it costs billing accuracy."]),
    ("calendar", "Next", "Three things to settle before the next cycle",
     "Relay siting, crew allocation, and whether the estimate rate becomes a reported metric.",
     # M6_label_enumerations: "blocks 1&#8211;3" is an ENUMERATION LABEL, not a
     # data range, and it sits in a block far longer than the 40-character
     # proxy that used to carry this exemption. The rules ask whether the pair
     # has quantitative context (writing-rules section 4 rule 6); a counting
     # noun in front of it says it does not. Planted here so the exemption is
     # proven at the verdict level and not only in a unit test.
     ["Relay siting needs a survey covering blocks 1&#8211;3 in the rural phase.",
      "Crew allocation needs a decision."]),
]

# The eyebrow sprite plus the footer's handling marker.
SPRITE = sprite([p[0] for p in PAGES] + ["shield"])
# D33 NEEDS A FIXTURE THAT FAILS IT. Two hand-drawn symbols, one of each kind
# the metric separates: `i-handdrawn` is a name in neither shipped set, and
# `i-shield` keeps a shipped NAME over geometry nobody shipped — the set's label
# on somebody else's drawing, which is the harder of the two to notice by eye.
# Only the broken deck carries them; the passing one must not, or the suite
# cannot tell the metric from one rewritten to return ok.
# `i-truck` is a name BOTH shipped sets carry and this sprite does not emit, so
# the altered-geometry plant is a real `<use>` resolving to a real definition.
# It was `i-shield` — an id the sprite already holds — so the document carried
# the id twice, the browser resolved every `<use>` to the first (correct) one,
# and the planted defect existed in the markup and in no rendering of it.
HAND_DRAWN = (
    '<symbol id="i-handdrawn" viewBox="0 0 24 24" fill="none" '
    'stroke="currentColor" stroke-width="2"><path d="M3 3 L21 21"/>'
    '<path d="M21 3 L3 21"/></symbol>'
    '<symbol id="i-truck" viewBox="0 0 24 24" fill="none" '
    'stroke="currentColor" stroke-width="2"><path d="M12 2 L4 6 L4 13 '
    'L12 22 L20 13 L20 6 Z"/></symbol>'
    '<svg class="ic" aria-hidden="true" style="display:none">'
    '<use href="#i-handdrawn"/></svg>'
    '<svg class="ic" aria-hidden="true" style="display:none">'
    '<use href="#i-truck"/></svg>')


def ground_defs() -> str:
    """The ripple ground, defined once and instantiated per page with <use>.

    brand.md's contract, exercised at last: sixteen lines, no two sharing a
    width, amplitude, wavelength or phase (a ground that can be counted is a
    field pretending to be water), crowding below the waterline with one line
    of air above it, colours from the ramp and the chart hues via tokens only,
    drawn with `slice` so the A4 sheet crops instead of stretching. Every
    number here is a fixed table — a fixture must be byte-stable.
    """
    import math
    lines = []
    for i in range(16):
        y0 = 260 if i == 0 else 300 + 26 * i + (i * i * 7) % 60
        amp = 8 + (i * 5.3) % 40
        wavelength = 210 + (i * 37) % 240
        width = 0.6 + i * 0.09
        opacity = min(0.9, 0.22 + i * 0.045)
        colour = ("--acc-5", "--acc-4", "--d-teal", "--d-blue")[i % 4]
        pts = " ".join(f"{x} {y0 + amp * math.sin(x / wavelength + i * 1.7):.1f}"
                       for x in range(0, 1281, 40))
        lines.append(f'<polyline points="{pts}" fill="none" '
                     f'stroke="var({colour})" stroke-width="{width:.2f}" '
                     f'stroke-opacity="{opacity:.2f}"/>')
    return ('<svg width="0" height="0" style="position:absolute" aria-hidden="true">'
            '<defs><g id="g-ground">' + "".join(lines) + "</g></defs></svg>")


GROUND_DEFS = ground_defs()
GROUND = ('<svg class="ground" viewBox="0 0 1280 720" '
          'preserveAspectRatio="xMidYMid slice" aria-hidden="true" '
          'focusable="false"><use href="#g-ground"/></svg>')


def shipped_css() -> str:
    """The palette AND the layout stylesheet, both lifted from tokens/.

    The fixture used to inline only the `:root` block and then reimplement the
    design system underneath it — its own `.body.split`, `.lede`, `.eyebrow`,
    `.sup`, `.listhead`, `.gd`, `.band`, `.lead`, `.cap .n`, `.foot`, every one
    of which ships in `lumi-layouts.css`. So the shipped stylesheet was never
    loaded by anything in this repository, and a missing `display: flex` on
    `.foot` and two entirely absent title registers reached a real deliverable
    unseen. A fixture that reimplements what it is testing is testing itself.
    """
    css = (ROOT / "tokens/lumi-theme.css").read_text(encoding="utf-8")
    start = css.index(":root {")
    depth, i = 0, start + len(":root {") - 1
    for i in range(start + len(":root {"), len(css)):
        if css[i] == "{":
            depth += 1
        elif css[i] == "}":
            if depth == 0:
                break
            depth -= 1
    # region-palette.css too. The fixture draws a region map with `rg rg-europe`
    # classes and never defined a single `--rg-*`, so every region fell back to
    # black: figure 9 of the REFERENCE IMPLEMENTATION rendered as four black
    # rectangles, at every geometry, while D18_region_labels, D5_drawn_share and
    # D5_figure_parity all passed. Nothing in this package reads rendered
    # colour, which is convention 8 in CLAUDE.md and why the sheet gets looked
    # at. 0.1.388 taught check_design to accumulate `:root` blocks rather than
    # keep the last one, precisely so a document could append this file; the
    # fixture then never did.
    # AND THE DARK PALETTE. Only the :root block was taken, so `body.dark`
    # never reached a deliverable — adding the class to a shipped document
    # changed nothing at all, because the values it redefines were not in the
    # file. The dark palette had been in tokens/ since 0.1.333 and reachable
    # from nothing since. A palette a document cannot express is a palette the
    # package does not have.
    dstart = css.index("body.dark {")
    ddepth, dend = 0, dstart
    for dend in range(dstart + len("body.dark {"), len(css)):
        if css[dend] == "{":
            ddepth += 1
        elif css[dend] == "}":
            if ddepth == 0:
                break
            ddepth -= 1
    dark = css[dstart:dend + 1] + "\n"

    # AND THE TRADE PALETTE, for the same reason and by the same history. The
    # cover and closing mark is the LUMIVATE field globe, whose regions are
    # trade blocs carrying `rg rg-eu` and friends; `region-palette.css` binds
    # the CONTINENTAL ids and defines none of those, so the mark's eight blocs
    # fell back to black exactly as figure 9 once did. 0.1.447 first answered
    # that by keeping the mark's own copy of this file inside the SVG — which
    # worked and was wrong: it froze a copy of a GENERATED file inside a locked
    # asset, where `build_region_palette.py --check` cannot see it drift. Two
    # generated palettes, both included, both checked.
    return (":root {" + css[start + len(":root {"):i] + "}\n" + dark
            + (ROOT / "tokens/lumi-layouts.css").read_text(encoding="utf-8")
            + (ROOT / "tokens/region-palette.css").read_text(encoding="utf-8")
            + (ROOT / "tokens/region-palette-trade.css").read_text(encoding="utf-8"))


# region_bindings() lived here from 0.1.390 to 0.1.391 — the fixture generating
# privately the join between `.rg-<id>` classes and `--rg-*` variables that
# nothing in tokens/ shipped. tokens/region-palette.css ships the bindings
# itself now (build_region_palette.py emits them beside the variables), so the
# fixture gets them through shipped_css() like any deliverable would, and a
# reference implementation no longer needs a private companion to render.


def foot(n: int, total: int, terms: str = TERMS, site: str = SITE,
         src: str = "") -> str:
    # A NESTED DIV, deliberately. This footer used spans to avoid a parser bug
    # that truncated the footer at its first closing tag — which guaranteed the
    # regression suite could never surface the bug, and is what
    # fixtures/README.md means by "never edit a fixture to make a check pass".
    # 0.1.359 fixed the parser and left the fixture shaped around it, so the old
    # buggy regex still passed the suite. The nesting is the test.
    # No `.src` span. It was here until 0.1.367, left behind when 0.1.366 removed
    # `.foot .src` from the token file: a per-page provenance slot that the rules
    # say belongs once per document in the closing colophon, kept alive in the
    # reference implementation of those rules. A fixture is a worked example, and
    # a worked example that uses a retired slot teaches the retired slot.
    # The handling marker: the seal-red shield ahead of the terms (design-rules
    # §4b), which inverts with the opener's lime field via `.foot .conf .ic`.
    return (f'<div class="foot"><div class="terms"><span class="conf">'
            f'<svg class="ic" aria-hidden="true"><use href="#i-shield"/></svg>'
            f'{terms}</span></div>'
            f'{src}<span class="site">{site}</span><span>{n:02d} / {total:02d}</span></div>')


# The four block patterns, one page each. Until 0.1.369 the fixture used none of
# them, so `tokens/` could ship a font-size for `.key`, `.no`, `.yes`, `.ledname`
# and `.card dd` inside the portrait media query and nowhere else, and nothing in
# this repository would ever render one. A reference implementation that skips a
# quarter of the shipped vocabulary cannot tell a working rule from an absent one
# — which is the same argument that put `lumi-layouts.css` into this file at all.
#
# Placed on the right-hand cell so each page keeps its lede, its footer and its
# left column, and the datum still holds across all sixteen.
# The worked example draws. Until 0.1.374 every figure in this fixture was three
# bare rectangles — 11 of 11 rect-only, which is precisely what D5 exists to flag
# as weak — so the only reference implementation in the package demonstrated the
# thing the rules call a figure that stopped trying. A reader compared a 3.4.0
# deck against a 0.1.373 one and named the gap: 24 drawn figures against 1.
#
# This one carries what §4 asks a figure to carry: an axis, labelled values, a
# conclusion in the caption, and a source line. The broken fixture keeps a
# rect-only figure so D5 still has something to report.
FIGURE = """<div class="fill">
      <div class="fig"><svg viewBox="0 0 640 420" preserveAspectRatio="xMidYMid meet"
        role="img" aria-label="Read success by feeder class, urban against rural">
        <line x1="132" y1="24" x2="132" y2="332" class="s-line" stroke-width="1"/>
        <text class="axname-y" x="118" y="180">feeder class</text>
        <text class="axname-x" x="132" y="352">read success, % of scheduled reads</text>
        <text class="flbl" x="0" y="76">Urban</text>
        <rect class="f-acc" x="132" y="40" width="380" height="64" fill="var(--acc)"/>
        <text class="fval" x="524" y="79">96.2%</text>
        <text class="flbl" x="0" y="180">Rural</text>
        <rect class="f-acc" x="132" y="144" width="250" height="64" fill="var(--acc)"/>
        <text class="fval" x="394" y="183">71.4%</text>
        <text class="flbl" x="0" y="284">Deferred</text>
        <rect x="132" y="248" width="170" height="64" class="f-none s-dash"
          fill="none" stroke-width="1.3"/>
        <text class="fnote" x="314" y="287">not surveyed this cycle</text>
        <text class="fnote" x="132" y="372">A dashed bar is a class with no
          measurement, never a low one</text>
        <text class="fnote" x="132" y="410">Meter management system, extract of the period</text>
      </svg>
      <div class="cap"><span class="n">Figure {i}</span> The gap follows terrain,
      not meter age, so relay siting is the lever</div></div>
    </div>"""

# A region figure, for D18. Deliberately small: the real globe is 68 KB of path
# data and the metric reads class names and label anchors, not geometry, so
# embedding the world here would be sixty-eight kilobytes of fixture proving
# nothing the four shapes below do not.
#
# The pass fixture labels every coloured region. The broken one omits the legend
# row for southeast-asia and nothing else — hue alone is left to say which
# region that is, which is exactly what D18 exists to catch.
REGION_FIGURE = """<div class="fill">
      <div class="fig"><svg viewBox="0 0 640 300" preserveAspectRatio="xMidYMid meet"
        role="img" aria-label="Coverage by trade region">
        <path class="rg rg-north-america is-live" d="M20 40h150v90H20Z"/>
        <path class="rg rg-europe is-live" d="M200 30h130v70H200Z"/>
        <path class="rg rg-southeast-asia is-live" d="M360 60h120v80H360Z"/>
        <path class="rg rg-africa is-zero" d="M240 140h110v120H240Z"/>
        <text class="flbl" x="20" y="272">Filled regions carry a source; a washed
          one carries none</text>
        <text class="fnote" x="20" y="294">Illustrative, www.example.org</text>
      </svg>
      <ul class="legend">{rows}</ul>
      <div class="cap"><span class="n">Figure {i}</span> Coverage follows the
      licensed counterparty, not market size</div></div>
    </div>"""

REGION_ROWS = {
    "north-america": "North America 60",
    "europe": "Europe 63",
    "southeast-asia": "Southeast Asia 35",
    "africa": "Africa, no source",
}


def region_rows(skip=()):
    return "".join(
        f'<li data-legend="{rid}"><span class="k rg-{rid}"></span>{label}</li>'
        for rid, label in REGION_ROWS.items() if rid not in skip)


# The rect-only figure the broken fixture keeps, so D5 has a subject.
# FIVE PLANTS IN ONE BROKEN-ONLY FIGURE. The two `.fval` percentages make it a
# figure that SCALES numbers while naming no axis, which is `figure_axis_named`'s
# red: a reader is handed a quantity and no dimension.
#
# FOUR OTHERS. Two are the axis names: `.axname-x`
# printed across the bars it is supposed to sit under, and `.axname-y` forced
# back to horizontal writing so it reads across instead of upward. Both are what
# three conformance decks did, and neither could be found before `tokens/`
# shipped the classes that say which text is an axis name.
#
# The `.srcline` in its caption is
# `D37_caption_scope`'s red: design-rules §4 rule 8 keeps the caption to the
# number and the name, and every conformance deck put the source there instead,
# where it runs into the name with no separator.
#
# The two `.sm` labels on y=176 are the planted SVG-TEXT COLLISION: one anchored
# from each end of the same baseline, meeting in the middle. It is the exact
# shape a conformance deck shipped twice — an axis unit printed over the word
# "Illustrative" — and `collision` reported `ok` on it until 0.1.551, because
# the probe's text vocabulary named HTML roles only and read an `<svg>` as one
# opaque box.
FIGURE_WEAK = """<div class="fill">
      <div class="fig"><svg viewBox="0 0 640 186" preserveAspectRatio="xMidYMid meet"
        role="img" aria-label="bars"><rect class="f-acc" x="0" y="0" width="380"
        height="46" fill="var(--acc)"/><rect class="f-acc" x="0" y="70" width="250"
        height="46" fill="var(--acc)"/><rect class="f-acc" x="0" y="140" width="170"
        height="46" fill="var(--acc)"/><polygon class="f-nw" points="150,60 260,60 300,93
        260,126 150,126" fill="var(--nw)"/><text class="axname-x" x="60"
        y="96">share of scheduled reads</text><text class="axname-y" x="8" y="90"
        style="writing-mode:horizontal-tb">feeder class</text><text class="sm" x="400" y="30">a label that runs
        past the right edge of its own viewBox</text><text class="sm" x="620" y="176"
        text-anchor="end">92% of the estate</text><text class="sm" x="520" y="176"
        text-anchor="start">Illustrative.</text><text class="fnote" x="0" y="182"
        >Meter management system, extract of the period</text></svg>
      <div class="cap"><span class="n">Figure {i}</span> Reads by feeder class
      <span class="srcline">Meter management system, extract of the period</span></div>
      <script type="application/json" class="f-data">{{"series":[{{"label":"Feeder C","value":91}}]}}</script>
      </div>
    </div>"""
# ^ The polygon is figure_ink_collision's failing subject (0.1.543): a solid
# chevron laid across the solid bar above it, which is the defect the owner
# opened a conformance deck and saw — 20x49px of one mark under another. The
# accepted reference deck carries 64 self-overlaps and none exceeds 7x6px, so
# the gate's floor is 12x12px and this plants well over it. Without a fixture
# that FAILS, check_fixtures says out loud that the metric cannot be told from
# one rewritten to return ok.
#
# ^ D21's failing subject: the figure DECLARES a series called "Feeder C" at 91,
# and neither the label nor the number is anywhere on the drawing. A figure that
# declares nothing is fine; one whose declaration contradicts it is not, because
# a false contract is worse than none — and the fixture suite refuses a graded
# metric that no fixture can fail, since that cannot be told from a metric
# rewritten to return ok.

# A viewBox with three numbers instead of four: legal as an attribute,
# meaningless as a value, and discarded by the browser — so the drawing lays out
# against a box nobody chose. Found in a real deliverable at 0.1.386, where a
# six-row figure rendered three rows while every check stayed green, because the
# clipping probe read the unparsed box as "nothing to measure" and skipped it.
# Broken-only, and it carries TWO plants: the three-number viewBox below, and a
# figure NAME long enough to wrap. `caption_name_wrap` needs a red, and it has
# to sit on a figure whose caption holds no source line — with a source in the
# caption the break lands there instead and the name never appears to wrap,
# which is the blindness rule 8 was rewritten to remove.
FIGURE_BADBOX = """<div class="fill">
      <div class="fig"><svg viewBox="0 640 300" preserveAspectRatio="xMidYMid meet"
        role="img" aria-label="steps"><rect class="f-acc" x="20" y="20" width="600"
        height="60" rx="4"/><rect class="f-accw" x="20" y="110" width="600"
        height="60" rx="4"/><rect class="f-accw" x="20" y="200" width="600"
        height="60" rx="4"/><text class="fval" x="640" y="56">62%</text>
        <text class="fval" x="640" y="146">28%</text>
        <text class="fnote" x="20" y="286">Meter management
        system, extract of the period</text></svg>
      <div class="cap"><span class="n">Figure {i}</span> Three tiers of feeder loss,
      and the reason the middle tier is the one that moves the estate's number
      when the relay programme finally reaches it</div></div>
    </div>"""

NOTES = """<div class="notes">
      <p class="listhead">What qualifies it</p>
      <p class="key">A tier-1 callout marks the one aside that changes a decision.
      The budget is one per page.</p>
      <!-- `tight` on purpose: the modifier had no base rule until 0.1.370,
           so nothing in this repository ever rendered one at 1280. -->
      <div class="swaps tight">
        <div class="swap"><span class="no">Rural coverage is poor</span><span
          class="arw">&#8594;</span><span class="yes">71.4% of rural reads succeed</span></div>
        <div class="swap"><span class="no">Crews need more hours</span><span
          class="arw">&#8594;</span><span class="yes">Clustering by feeder cuts travel</span></div>
      </div>
    </div>"""

# Cards and vows get the page to themselves, on `stack`. Written first as a
# second column beside the usual list-and-callout cell, they ran 44px past the
# footer rule at 1280 and 135px at A4 — and `--deliverable` said so, on the
# repository's own fixture, before any of it was committed. The rule for a page
# that does not fit is that its CONTENT is trimmed, so the content is trimmed:
# these two blocks are what their page is about, and a page about four
# commitments does not also carry a bullet list and a display number.
CARDS = """<div class="duo">
      <div class="card"><p class="ledname">First-attempt reads</p>
        <dl><dt>Measure</dt><dd>Meters returning a value without a revisit.</dd></dl>
        <p class="verdict">Watch this before the read rate.</p></div>
      <div class="card"><p class="ledname">Estimate rate</p>
        <dl><dt>Measure</dt><dd>Billed reads that were inferred, not taken.</dd></dl>
        <p class="verdict">One cycle of warning, and no more.</p></div>
    </div>"""

VOWS = """<div class="vows">
      <div class="vow"><span class="vn">01</span><p class="vt">Date every extract</p>
        <p class="vw">A figure without its extract date cannot be reconciled later.</p></div>
      <div class="vow"><span class="vn">02</span><p class="vt">Name the region</p>
        <p class="vw">Two regions differ enough that an average hides both.</p></div>
      <div class="vow"><span class="vn">03</span><p class="vt">Count attempts</p>
        <p class="vw">A read that took three visits did not succeed.</p></div>
      <div class="vow"><span class="vn">04</span><p class="vt">Say what moved</p>
        <p class="vw">A number that changed for no stated reason is not evidence.</p></div>
    </div>"""


def renumber_figures(doc: str) -> str:
    """Caption numbers, resequenced 1..k in document order.

    The captions are written `Figure {i}` where `i` is the PAGE number, so the
    part openers and the pages carrying no drawing punched holes: the tracked
    pass fixture shipped 3, 4, 8, 9, 11 ... and check_design.py D30 fails it.
    Renumbering here rather than threading a counter through `page()` keeps the
    figure ordinal a property of the finished document, which is what it is --
    a page can gain or lose a drawing without every later caption moving in the
    source. The broken fixture deliberately keeps the holes: D30 needs a
    fixture that fails it.
    """
    n = iter(range(1, 999))
    return re.sub(r'(<span class="n">Figure )\d+(</span>)',
                  lambda m: f"{m.group(1)}{next(n)}{m.group(2)}", doc)


def page(i: int, total: int, spec, broken: bool, k: int) -> str:
    """One content page. `i` is its page NUMBER; `k` is its ordinal among the
    content pages, and every planted defect keys on `k`.

    **Why two numbers.** The plants used to key on `i`, and a page number is a
    function of how the deck is split into parts. Re-splitting it at 0.1.549
    moved page 12 from a content page to a part opener and took three planted
    defects with it — D4's literal colour and D24/D25's untermed image all came
    back `ok`, and only `check_fixtures`' refusal to grade a metric no fixture
    fails said so. It had happened once before: the same D4 plant sat on page 5
    until 0.1.369 turned that page into a `stack` layout with no `.gd` at all.
    Twice is a pattern, and the pattern is that a plant must be anchored to the
    page's CONTENT, never to its position.

    It also fixes a quieter bug: the two decks numbered differently (the passing
    one carries an agenda), so `i == 8` meant the fifth content page in one deck
    and the sixth in the other. The plants now land on the same page in both.
    """
    icon, eyebrow, title, sup, bullets = spec
    # The eyebrow contract (design-rules §3): subject icon, then
    # `PART <letter> · <label>`. Pages 3-9 sit under Part A, 11-17 under Part B.
    part = "A" if i <= 9 else "B"
    gd = ("A callout carries the aside a reader should not miss, and no more than one "
          "of them belongs on a page.")
    style = ""
    terms = TERMS
    src = ""
    spec_decl = ""
    if broken and k == 6:
        # THE DEEPER BRANCH. `k == 4` below plants a spec file that is not
        # there — the easiest failure `load()` can have. This one parses, is
        # complete, and its parts do not sum to its total: the arithmetic
        # assertion of 0.1.669, which no fixture reached until 0.1.671 and
        # which therefore could not be told from a metric rewritten to return
        # ok.
        spec_decl = ' data-figure-spec="figures/broken-bridge.json"'
    if broken and k == 4:
        # D42's PLANT. The page says its numbers are in a file, and the file is
        # not there. Nothing asks a figure to declare a spec (AG-10); what this
        # fixture carries is the contradiction — a declaration the document
        # cannot honour. Anchored to `k`, never to `i`: two planted defects were
        # lost when a re-split moved their page number, twice.
        spec_decl = ' data-figure-spec="figures/does-not-exist.json"'
    if broken:
        if k == 2:
            gd = ("Leveraging a seamless framework, this callout showcases a robust "
                  "and comprehensive approach.")            # M4 banned phrases
        if k == 9:
            # D4 literal colour. It sat on page 5 until 0.1.369, which then became
            # a `stack` page carrying cards and no `.gd` at all — so the planted
            # defect silently vanished and D4 came back `ok` on the fixture whose
            # whole job is to make it fire. `check_fixtures.py` caught it, which
            # is the assertion earning its place: a defect that stops being
            # planted is indistinguishable from a check that stopped working.
            style = ' style="border-color:#ABCDEF"'
        if k == 6:
            terms = "Prepared for circulation"               # D12: no handling terms
        if k == 5:
            # a real prose em-dash, which M9 must still catch
            sup = "The gap is signal &#8212; not hardware, and it follows terrain."
        if k == 11:
            # M12: visible CJK in a document that declares English. The Chinese
            # here is rule DATA — the defect under test — exactly as banned
            # phrases and punctuation examples are elsewhere in this package.
            # A real deliverable named `*.en.html`, carrying `lang="en"`, shipped
            # a badge like this in a page lede and passed every metric.
            sup = "\u5df2\u56de\u6536 15/15 \u9898. Coverage held across the surveyed feeders."
        if k == 12:
            # D15: a repository path poured into the footer as a "source". The
            # second document to do this; 0.1.366 removed `.foot .src` from
            # tokens/ after the first.
            src = ('<span class="src">resources/'
                   '\u60c5\u62a5\u6e90\u76ee\u5f55-20260730.zh.html</span>')
        if k == 10:
            # D14: the slot an author leaves for themselves and then ships. A
            # real deliverable carried four of these on its closing page and
            # every check in this package passed it, because a placeholder is
            # not a banned phrase, not a colour, and occupies exactly as much
            # room as the text that should have replaced it.
            sup = "Read success held at [TO FILL]% across the surveyed feeders."
        if k == 8:
            sup = sup + " The gap is measured against a baseline taken in the first "\
                        "quarter of the programme, before the rural feeders had been "\
                        "surveyed at all, which makes the comparison generous."  # M8 overlong
            # This sup runs to three lines, so from 0.1.522 it also trips
            # `reserve_overspent` on this page -- the reserve is a ceiling and
            # three support lines exceed it. Left as is on purpose: shortening
            # it to quiet the layout probe would delete the M8 case this page
            # exists for, and expected.json records both verdicts rather than
            # one of them being tuned away.
    lis = "".join(f"<li>{b}</li>" for b in bullets)
    # Page 12 carries the graded ladder and page 17 the glossary, so the two
    # block patterns promoted in 0.1.375 are exercised by the suite instead of
    # merely shipped; check_prose counts both as enumerations (M10).
    listblock = f"<ul>{lis}</ul>"
    if k == 9:
        listblock = (
            '<div class="grades">'
            '<div class="gr g4"><i></i><p class="gn">Estimate rate, weekly</p>'
            '<p class="gq">leads the read rate by a cycle</p></div>'
            '<div class="gr g3"><i></i><p class="gn">Read rate</p></div>'
            '<div class="gr g2"><i></i><p class="gn">Backlog count</p></div>'
            '<div class="gr g1"><i></i><p class="gn">Crew hours</p>'
            '<p class="gc">recorded, but not predictive</p></div></div>')
    if k == 14:
        listblock += (
            '<dl class="gloss"><dt>Estimate rate</dt>'
            '<dd>Billed reads inferred rather than taken.</dd>'
            '<dt>First-attempt read</dt>'
            '<dd>A value returned without a revisit.</dd></dl>')
    # A table whose last cell is an em-dash placeholder — "no value", the
    # standard convention. M9 bans em-dashes in PROSE and counted this, failing
    # a deliverable that had none. Found by running the checker against real
    # agent output; the fixtures we wrote ourselves never used a placeholder.
    cell = ""
    if k == 7:
        cell = ('<table><tbody>'
                '<tr><td>Rural feeders</td><td>41</td>'
                '<td><span class="tag built">surveyed</span></td></tr>'
                '<tr><td>Deferred</td><td>&#8212;</td>'
                '<td><span class="tag part">awaiting outage</span></td></tr>'
                '</tbody></table>')
    # Pages 3 and 4 carry a stat band and a display lead. Without them the
    # fixture never exercises `.band .k`, `.band .v` or the focal element, and
    # inspect_layout.py correctly reports those roles as NOT MEASURED — a
    # reference implementation that skips a third of the role vocabulary is not
    # a reference implementation.
    band = ""
    if i in (3, 4):
        # band_escape (0.1.541): the broken fixture's first band OVERRIDES the
        # `min-height: min-content` floor `tokens/` gained this release, which
        # is the only way to reach the defect now that the floor ships — and it
        # is not a contrivance: the deck that produced the finding carried the
        # tokens verbatim and still collapsed, because `.body > *`'s
        # `min-height: 0` was the whole of the band's protection. A document
        # that reintroduces that zero gets the old behaviour, and the checker
        # has to see it. Without a fixture that FAILS, check_fixtures says out
        # loud that the metric cannot be told from one rewritten to return ok.
        squeeze = ' style="min-height:0;height:18px"' if broken and k == 1 else ''
        band = (f'<div class="band"{squeeze}>'
                '<div><span class="k">Coverage</span><div class="v">41<span class="u">%</span></div></div>'
                '<div><span class="k">Feeders</span><div class="v">312</div></div>'
                '<div><span class="k">Estimates</span><div class="v">8.4</div></div>'
                '</div>')
    # The field, exercised at last: brand.md names it the deck's signature and
    # inspect_layout audits it, yet no fixture had ever drawn one — a mark per
    # datum, each carrying its data-datum, intensity from the datum.
    field = ""
    if k == 2:
        marks = "".join(f'<i data-w="{(k * 3) % 5 + 1}" data-datum="F{k + 1:02d}"></i>'
                        for k in range(12))
        field = ('<p class="listhead">Feeder signal strength</p>'
                 f'<div class="field tall" data-count="12">{marks}</div>')
    lead = ""
    # ORDINAL, not page number. This was the one plant left keyed on `i` after
    # 0.1.549, so it suppressed `.lead` on content page 1 of the passing deck
    # and on 1 AND 2 of the broken one — the asymmetry the `page()` docstring
    # says no longer exists.
    if k not in (1, 2):
        lead = f'<div class="lead"><div class="v">{i * 7}</div>' \
               f'<p class="g">Units returned per avoided visit, illustrative</p></div>'
    if not broken and k == 10:
        # The reference implementation of a declared omission: named, reasoned,
        # and where a reader meets it. deck-broken carries the same declaration
        # hidden, so the pair is what tells a working D26 from one rewritten to
        # return ok.
        lead = ('<div class="lead"><div class="v">91</div>'
                '<p class="g">Units returned per avoided visit, illustrative</p>'
                '<p class="scope-note" data-omitted="pricing">Pricing is set by '
                'the commercial team and is out of scope here.</p>'
                # D31: the six typical gtm sections this synthetic deck does
                # not carry are DECLARED, in one reader-visible sentence, so
                # the pass fixture shows what a declared scope looks like and
                # deck-broken (same absences, nothing declared) is what fails.
                '<p class="scope-note" data-omitted="target customer, value '
                'proposition, channels, messaging, sales motion, success '
                'measure">This deck states no target customer, value '
                'proposition, channels, messaging, sales motion or success '
                'measure: it exists to exercise the checks.</p></div>')
    if broken and k == 9:
        # D24 and D25: a linked image with no terms named. Both gates need a
        # fixture that FAILS them or the suite cannot tell them from a metric
        # rewritten to return ok — which is what check_fixtures says out loud.
        # One page carries both defects because they are one mistake: an image
        # pasted in from a search result, still pointing at its host and still
        # unattributed.
        lead = ('<div class="lead"><img src="https://example.org/plate.png" '
                'alt="a linked plate"></div>')
    elif broken and k == 10:
        # D26: a scope note a reader cannot see. The rubric's whole argument
        # for the scope note is that it is READER-VISIBLE — a marker only the
        # checker can read would do nothing but silence the checker — so the
        # failing case is a declaration hidden from the page, not a missing
        # one. Without this the metric would only ever have been seen passing.
        lead = ('<div class="lead"><div class="v">91</div>'
                '<p class="g">Units returned per avoided visit, illustrative</p>'
                '<p class="scope-note" style="display:none" '
                'data-omitted="pricing">Pricing is set elsewhere.</p></div>')
    elif broken and k == 13:
        # D16: a page with no visual block at all — no figure, no band, no
        # lead, no comparison pattern; prose, a list and a callout. The static
        # half of the visual-share directive reports it as prose-only.
        lead = ""
    if k == 14:
        # The apparatus exemption, exercised in both directions (0.1.381): this
        # page is prose-only AND declares itself reference, so it must NOT be
        # listed — while the broken fixture's undeclared p16 still is. A rule
        # that exempts something needs a fixture where the exemption is the
        # only thing standing between a clean report and a finding.
        lead = ""
    # One page each for the four block patterns; every other page keeps the
    # figure. The tier-1 pair is exercised in both colours on DIFFERENT pages:
    # `.key` in page 5's notes column and `.red` in page 8's, because D3 budgets
    # tier-1 callouts at one per page and putting both on one page trips it —
    # which the fixture should demonstrate obeying, not by luck.
    if k == 6:
        gd = ('<p class="red">The seal colour marks a red line, never emphasis. '
              'A page carries at most one tier-1 callout.</p>')
    else:
        gd = f'<p class="gd"{style}>{gd}</p>'
    argument = f"""<div class="fill">
      <p class="listhead">What the data shows</p>
      {gd}
      {listblock}
      {cell}{band}{field}{lead}
    </div>"""
    fig = FIGURE
    if k == 7:
        fig = REGION_FIGURE.replace(
            "{rows}", region_rows(skip=("southeast-asia",) if broken else ()))
    if broken and k == 2:
        fig = FIGURE_WEAK
    elif broken and k == 6:
        fig = FIGURE_BADBOX
    layout, cells = "split", argument + "\n    " + fig.format(i=i)
    if broken and k == 13:
        layout, cells = "stack", argument
    if k == 14:
        layout, cells = "stack", argument
    if k == 3:
        layout, cells = "sidebar-notes", argument + "\n    " + NOTES
    # A one-line `.lead.row` above each block. Two purposes: it gives these two
    # pages an entry point — without it `inspect_layout.py` reports them as the
    # only pages in the deck with nothing above body copy — and `.lead.row` is a
    # shipped pattern that nothing in this repository rendered until now, which
    # is how its `flex-direction: row` lost an argument to the fill rule twice.
    row = ('<div class="lead row"><div class="v">41<span class="u">%</span></div>'
           '<p class="g">Metering coverage, illustrative</p></div>')
    if k == 4:
        layout, cells = "stack", f'<div class="fill">{row}{CARDS}</div>'
    if k == 5:
        layout, cells = "stack", f'<div class="fill">{row}{VOWS}</div>'
    role = ' data-role="apparatus"' if k == 14 else ""
    # D32's failing subject (0.1.543, promoted to gating): a page that DECLARES
    # an analysis move and draws none of the shapes the library ships for it.
    # The condition was always binary — the page said what it was doing and did
    # not do it — and it was reported for three releases while the deck the
    # owner opened declared seven such pages and drew zero. Only the broken
    # fixture carries the declaration; the passing one must not, because
    # `check_fixtures` refuses a graded metric no fixture can fail.
    if broken and k == 6:
        role += ' data-analysis="bridge"'
    return f"""
<section class="page" id="p{i}"{role}{spec_decl}>
  {GROUND}
  <div class="body {layout}">
    <div class="lede">
      <p class="eyebrow"><svg class="ic" aria-hidden="true"><use href="#i-{icon}"/></svg>Part {part} &#183; {eyebrow}</p>
      <h2 class="t">{title}</h2>
      <p class="sup">{sup}</p>
    </div>
    {cells}
  </div>
  {foot(i, total, terms, src=src)}</section>"""


# The one oversized subject mark design-rules §3 permits on a part opener: a
# filled silhouette carrying no text of its own, reversed out of the lime field,
# restating the part's claim in another modality. FILLED and not stroked — the
# same section calls a hairline outline scaled to display size the accident and
# the silhouette the deliberate graphic. Added 0.1.546: the rule had lived in
# prose for four releases, no fixture drew one, and three conformance decks
# driven to pass every other gate carried none on five openers between them.
def opener_mark(shape: str) -> str:
    """One part opener's subject mark. THREE OPENERS, THREE MARKS.

    design-rules §3 says the mark "is the part's subject or it is not there", so
    two parts carrying one silhouette assert the two parts are the same thing.
    This fixture drew one mark on both its openers until 0.1.549 — the defect
    the owner had already found on a conformance deck, sitting unnoticed in the
    package's own model of a correct document, because nothing compared them.
    """
    return ('<div class="openmark"><svg viewBox="0 0 116 182" '
            'aria-hidden="true" focusable="false">' + shape + '</svg></div>')


# Three silhouettes, geometrically distinct so the repetition check has
# something real to separate — not three colours of one shape.
MARK_HEX = ('<path d="M58 6 L110 48 L110 140 L58 178 L6 140 L6 48 Z"/>'
            '<path d="M58 42 L86 64 L86 124 L58 146 L30 124 L30 64 Z" '
            'fill="var(--lime)"/>')
MARK_TOWER = ('<path d="M20 178 L20 60 L58 20 L96 60 L96 178 Z"/>'
              '<path d="M42 178 L42 120 L74 120 L74 178 Z" fill="var(--lime)"/>')
MARK_WAVE = ('<path d="M8 150 C40 96 76 96 108 150 L108 178 L8 178 Z"/>'
             '<path d="M8 96 C40 42 76 42 108 96 L108 122 C76 68 40 68 8 122 Z" '
             'fill="var(--lime)"/>')
OPENER_MARK = opener_mark(MARK_HEX)
# THE PACKAGE ALREADY SHIPS THE CONTAINER. `tokens/` has styled `.openmark`
# since the opener composition landed — a second grid column, `height: 46svh`,
# `fill: currentColor` — and the accepted reference deck uses exactly that.
# Three attempts here wrote inline styles instead: 15% of the copy column
# rendered 14px wide, viewport units pushed the mark past the page box and
# `content_spill` caught it, and percentages of the frame were too small again.
# Every one of those rounds was spent re-deriving a rendering that was already
# in `tokens/`, which is what the class vocabulary is for.


def opener(part: str, number: int, total: int, claim: str, run: str,
           mark: str = OPENER_MARK) -> str:
    # The part opener, in the shipped composition: the lime field carrying
    # `.openpart` / `.openclaim` / `.openrun` and nothing else
    # (storyline-templates.md). `.page.opener` was styled since 0.1.345 and no
    # fixture rendered one until 0.1.369's lesson made the worked example the
    # test; the composition classes shipped in 0.1.375 and are exercised here.
    return f"""
<section class="page opener" id="open{part}">
  {GROUND}
  <div class="body full-bleed no-lede">
    <div class="bleed openframe">
      <div class="openpart">Part {part}</div>
      <div class="openclaim">{claim}</div>
      <div class="openrun">{run}</div>
      {mark}
    </div>
  </div>
  {foot(number, total)}</section>"""


# (number, claim, marked phrase, run line). The MARKED phrase is wrapped in
# `.hl` — storyline-templates: "The energy comes from weight and the lime chip,
# never from a louder ground." The accepted reference marks all three of its
# claims; this fixture marked none until 0.1.554, so the package's own model of
# an agenda was the flat one the rule exists to prevent.
AGENDA_ROWS = (
    ("01", "What the estate", "measures today",
     "Coverage, the backlog, and what a read is worth."),
    ("02", "Where the reads", "actually fail",
     "Signal, terrain and the relay siting decision."),
    ("03", "What the month has", "to settle",
     "Crew allocation, the siting shortlist, and the cost of waiting."),
)


def agenda(number: int, total: int) -> str:
    """The launch sequence, one row per part (0.1.519).

    **The rows quote the openers verbatim** — same strings, one tuple — because
    D27 fails an agenda line matching no title the deck carries, and writing the
    agenda twice is the defect D27 exists for. The pass fixture cannot be a
    fixture for D27 and a document that quietly violates it.

    The broken fixture gets NO agenda: that is the planted failure for
    `deck_structure` (0.1.547), and it is the shape three conformance decks
    arrived in — parts nothing routes.
    """
    rows = "".join(f"""
      <div class="lrow">
        <div class="ln">{n}</div>
        <div><p class="gn">{claim} <span class="hl">{mark}</span></p>
          <p class="gq">{run}</p></div>
      </div>""" for n, claim, mark, run in AGENDA_ROWS)
    return f"""
<section class="page" id="agenda">
  {GROUND}
  <div class="body stack no-lede">
    <div class="fill">
      <div class="launch">{rows}
      </div>
    </div>
  </div>
  {foot(number, total)}</section>"""


# HOW THE CONTENT PAGES SPLIT BETWEEN THE THREE PART OPENERS. Two shapes, and
# the difference IS the fixture:
#
# * The passing deck runs 5 / 5 / 4, inside `opener_pacing`'s ceiling of six.
# * The broken deck runs 7 / 1 / 6, so its longest stretch goes past the ceiling
#   and a fixture can fail the check. Until 0.1.549 BOTH decks ran 7 / 7 — this
#   package's own model of a correct document broke the seam rate it was about
#   to start enforcing.
#
# Asserted against len(PAGES) rather than trusted: a page added to PAGES would
# otherwise fall off the end of the last part without a word.
SPLIT_PASS = (5, 5, 4)
SPLIT_BROKEN = (7, 1, 6)


def build(broken: bool) -> str:
    split = SPLIT_BROKEN if broken else SPLIT_PASS
    if sum(split) != len(PAGES):
        # Raised, not asserted: `-O` strips an assert and this one is the whole
        # protection against a new PAGES entry falling off the last part.
        raise SystemExit(
            f"the part split covers {sum(split)} pages and PAGES holds "
            f"{len(PAGES)}; a page was added without deciding which part it "
            f"belongs to")
    # Content pages + one opener per part + the bookends: cover and closing
    # always, plus the agenda on the passing deck. Written out as a sum of what
    # is actually emitted, because the shorthand it replaces — `+ (1 if broken
    # else 2)` — silently DROPPED THE COVER when the third opener landed, and
    # both fixtures shipped declaring one page fewer than they hold, with the
    # closing page repeating the previous page's number. Nothing caught it:
    # `build_fixtures --check` compares the generator to its own artifact and
    # they agreed, and D6 asks only whether a total is present.
    bookends = 2 + (0 if broken else 1)            # cover, closing, [agenda]
    total = len(PAGES) + len(split) + bookends
    # Cover and closing are the same kind of page, set the same way: cover-grid,
    # with the LUMIVATE field globe as the one vector mark on each (the closing
    # repeats the cover's mark rather than introducing a new claim).
    # THE BROKEN DECK LOSES ITS BRAND MARK, both bookends, the way the deck the
    # owner opened on 2026-08-22 had: the cover keeps a drawing that is a CHART
    # rather than the locked globe (D40), and the closing carries a different
    # mark from the cover (D39). Two plants because the two gates say different
    # things — a bookend that is not the brand, and two bookends that disagree.
    waffle = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" '
              'role="img" aria-label="Twenty-five cells, one per thousand '
              'meters read">'
              + "".join(f'<rect class="f-acc" x="{(i % 5) * 20 + 2}" '
                        f'y="{(i // 5) * 20 + 2}" width="16" height="16"/>'
                        for i in range(25))
              + "</svg>")
    other = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" '
             'role="img" aria-label="A single ring, not the deck\'s own mark">'
             '<circle class="s-mut" cx="50" cy="50" r="40" fill="none"/></svg>')
    cover_mark = waffle if broken else GLOBE
    closing_mark = other if broken else GLOBE
    cover = f"""
<section class="page cover" id="cover">
  {GROUND}
  <div class="body cover-grid">
    <div class="typeblock">
      <p class="wordmark">{new_deck.wordmark()}</p>
      <h1>Metering programme <span class="subj">review</span></h1>
      <p class="sub">A synthetic deliverable. Every figure here is invented.</p>
    </div>
    <div class="markcell">{cover_mark}</div>
    <div class="attrs">
      <div><span class="k">Audience</span><span class="v">Checker regression suite</span></div>
      <div><span class="k">Classification</span><span class="v">Synthetic, client-free</span></div>
      <div><span class="k">Edition</span><span class="v">Regenerates with the tokens</span></div>
    </div>
    <p class="colophon">Built with lumi-style {VERSION} &#183; source: meter management system.</p>
  </div>
  {foot(1, total)}</section>"""
    closing = f"""
<section class="page closing" id="closing">
  {GROUND}
  <div class="body cover-grid">
    <div class="typeblock">
      <p class="wordmark">{new_deck.wordmark()}</p>
      <h2>What to settle this <span class="subj">month</span></h2>
      <p class="sub">Relay siting first, then crew allocation.</p>
    </div>
    <div class="markcell">{closing_mark}</div>
    <div class="attrs">
      <div><span class="k">Owner</span><span class="v">The analysis team</span></div>
      <div><span class="k">Source</span><span class="v">Meter management system</span></div>
    </div>
    <div class="closenote"><p class="colophon">Built with lumi-style {VERSION}.
    Source: meter management system; every number here is invented, and a
    bracketed slot must not ship.</p></div>
  </div>
  {foot(total, total)}</section>"""

    # Page numbers are COUNTED OUT as the parts are laid down, never written as
    # literals: a hand-numbered second copy of this arithmetic is the drift this
    # repository has fixed twenty-six times, and since 0.1.549 the two decks do
    # not even have the same shape to hand-number.
    #
    # The marks: three distinct silhouettes on the passing deck, and on the
    # broken one part B carries none while part C repeats part A's — the two
    # halves of what `opener_subject_mark` grades, each with its own fixture.
    # Until 0.1.549 the passing deck drew ONE mark on both its openers, which is
    # the defect the owner had already reported on a conformance deck sitting
    # unnoticed in this package's own model of a correct document.
    marks = ([opener_mark(MARK_HEX), "", opener_mark(MARK_HEX)] if broken
             else [opener_mark(MARK_HEX), opener_mark(MARK_TOWER),
                   opener_mark(MARK_WAVE)])
    body, n, taken = cover, 2, 0
    if not broken:
        body += agenda(n, total)
        n += 1
    for part, count, mark in zip("ABC", split, marks, strict=True):
        # NOT `mark` — that name is the opener's silhouette, bound by the loop
        # above. Shadowing it blanked all three marks and `opener_subject_mark`
        # went red on the passing fixture, which is what caught it.
        _n, head, marked, run = AGENDA_ROWS["ABC".index(part)]
        claim = f"{head} {marked}"
        body += opener(part, n, total, claim, run, mark=mark)
        n += 1
        for j, spec in enumerate(PAGES[taken:taken + count]):
            body += page(n, total, spec, broken, taken + j + 1)
            n += 1
        taken += count
    body += closing
    label = "broken" if broken else "pass"
    # The pass fixture is what a correct document looks like, so its figure
    # numbers run 1..k. The broken one keeps the page-index holes, because
    # D30 needs a fixture that fails it.
    if not broken:
        body = renumber_figures(body)
    hand = HAND_DRAWN if broken else ""
    # `role_weight` needs a fixture that fails it. This is the real shape of the
    # defect: not a missing rule but a document whose own copy of the stylesheet
    # renders a weight-bearing role at body weight. Two conformance decks
    # shipped exactly this, and the ladder read as four paragraphs.
    weight_loss = ("<style>.gr .gn { font-weight: 400; }</style>"
                   if broken else "")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Metering programme review ({label} fixture)</title>
<!-- generated by scripts/build/build_fixtures.py - do not hand-edit -->
<style>
{shipped_css()}
*, *::before, *::after {{ box-sizing: border-box; }}
/* No .foot, h1 or h2 rules here on purpose. The fixture defined its own footer
   flex and its own title sizes, so it tested its own stylesheet rather than the
   one this package ships — and a missing `display: flex` on `.foot` reached a
   real deliverable unseen. What is shipped is what gets exercised. */
body {{ font-family: var(--din); font-size: 15px; color: var(--tx1);
        background: var(--bg); margin: 0; }}
/* Only what a DOCUMENT legitimately decides for itself. Everything else — the
   layouts, the role vocabulary, the footer row, the page frame and its stage —
   now comes from tokens/lumi-layouts.css above, so the fixture exercises the
   shipped stylesheet instead of a private copy of it. The `.page` padding lived
   here until 0.1.380, where it was found overriding the A4 margin and wrapping
   the footer of a real deliverable on every page. */
ul {{ margin: 0; padding-left: 18px; color: var(--tx2); font-size: 14px; }}
.band .v .u {{ font-size: .42em; color: var(--tx3); }}
.cap {{ font-family: var(--mono); font-size: var(--fs-source); color: var(--tx3); }}
.flbl {{ font-size: 12.5px; font-weight: 700; fill: var(--tx1); }}
.fval {{ font-family: var(--din); font-size: 15px; font-weight: 700;
         fill: var(--tx1); font-variant-numeric: tabular-nums; }}
.fnote {{ font-size: 11px; fill: var(--tx3); }}
.f-none {{ fill: none; }}
.s-line {{ stroke: var(--ln1); }}
.s-dash {{ stroke: var(--ln1); stroke-dasharray: 5 4; }}
.colophon {{ font-family: var(--mono); font-size: var(--fs-source); color: var(--tx4); }}
</style></head><body data-geometry="landscape" data-genre="sales" data-storyline="gtm">{SPRITE}{hand}{weight_loss}{GROUND_DEFS}{body}</body></html>
"""


# ── the third fixture ─────────────────────────────────────────────────────────
# deck-broken carries ONE NAMED DEFECT PER PAGE and is readable as a worked
# example of what each rule catches. Ten metrics could not be given a failing
# case there without destroying that: four are document-WIDE prose properties
# (every sentence the same length, every title the same shape) that cannot be
# confined to one labelled page, and adding six more design defects to a deck
# that already carries eight stops it teaching anything.
#
# So this is the deck's own second option: a third fixture whose only job is to
# fail. It is NOT a worked example and must never be read as one. Every defect
# in it is deliberate, and each is annotated with the metric it exists to trip.
#
# Before 0.1.390 these ten metrics were asserted `ok` on both fixtures, which
# cannot tell a working checker from one rewritten to `return "ok"`.

# Sixteen sentences of 36 words each, and the length is the point: over
# OVERLONG_WORDS (32) so M8_overlong_share reads 100%, and IDENTICAL so
# M8_length_cv reads ~0 against a floor of 0.35. One body of text trips both,
# which is why they could not be planted on separate pages.
_LONG = (
    "The programme reports that the estate remains only partially covered by "
    "the current metering estate rollout across every region under review, and "
    "that the position has not materially changed since the previous reporting "
    "cycle closed for review"
)
DEGENERATE_SENTENCES = [f"{_LONG} number {n}." for n in range(1, 17)]

# Every title takes the `plain` frame: no colon, no question mark, no leading
# numeral, no gerund or wh-word. M11_title_uniformity reads 100% against a
# ceiling of 60%. Nine of them, over MIN_TITLES (8), or the metric reads n/a.
#
# They are also as long as the body sentences, and that is not decoration.
# M8_length_cv is a coefficient of variation over EVERY extracted sentence, so a
# deck of long paragraphs under short titles still varies: the first draft of
# this fixture measured 0.701 against a floor of 0.35 and passed. Driving it to
# zero means the whole document has one sentence length, titles included —
# which is precisely the shape 0.1.336 shipped when "short sentences" was read
# as a target rather than a direction, and precisely what this metric exists to
# catch. The fixture is absurd to read. It is supposed to be.
_TITLE = (
    "The reporting position across the estate under review has not moved "
    "materially since the previous cycle closed and remains subject to the same "
    "constraints that were recorded at the time by the programme"
)
DEGENERATE_TITLES = [f"{_TITLE} for area {n}" for n in range(1, 10)]


def _degenerate_page(i: int, total: int, title: str, tier1: int) -> str:
    """One page of the failing deck.

    `tier1` plants D3: TIER1_PER_PAGE is 1 and TIER1_PAGE_SHARE is 33%, so a
    page carrying two `.key` blocks trips the per-page budget and enough pages
    carrying any trips the share.

    No `.sup`, `.lede` or `.lead` anywhere — that is D8_support_line, which
    needs the absence of a support line rather than the presence of a defect.

    The footer carries no `n / total`, which is D6_footer's missing_total.
    """
    keys = "".join(f'<div class="key"><span class="v">{40 + k}</span>'
                   f'<span class="l">units</span></div>' for k in range(tier1))
    # Three items, every time: M10_triad_rate reads 100% against a ceiling of 50%.
    items = "".join(f"<li>{s}</li>" for s in DEGENERATE_SENTENCES[i % 14:i % 14 + 3])
    # A body paragraph of the same long sentences. It is here for M8_length_cv:
    # the handling terms in every footer are nine words and count as a sentence,
    # so eleven pages contribute eleven short ones, and with lists alone the
    # coefficient of variation sat at 0.453 against a floor of 0.35. Diluting
    # them is not a trick — a page with no running prose is not a page.
    para = " ".join(DEGENERATE_SENTENCES[(i + 5) % 9:(i + 5) % 9 + 8])
    return f"""
<section class="page" id="d{i}">
  <div class="body">
    <h2>{title}</h2>
    {keys}
    <p>{para}</p>
    <ul>{items}</ul>
  </div>
  <div class="foot"><div class="terms"><span class="conf">{TERMS}</span></div>
  <span class="site">{SITE}</span></div></section>"""


def build_degenerate() -> str:
    pages = "".join(_degenerate_page(i + 1, len(DEGENERATE_TITLES), t,
                                     2 if i < 6 else 0)
                    for i, t in enumerate(DEGENERATE_TITLES))
    # D27_agenda_mirror: an agenda whose every line was written fresh rather
    # than quoted from the titles. Both lines below match no title in the deck,
    # which is exactly the defect the second blind review (D16) opened with.
    # D35_agenda_exclusive: a stat band on the agenda page, which is the defect
    # the owner found on a conformance deck. It sits inside a real `.body` on
    # purpose — the earlier version had no `.body` at all, so D35's red came
    # from its "no .body block" guard clause and the STRAY SCAN, which is the
    # metric, had never gone red on any fixture. A gate whose only failing
    # sample takes an early return is a gate with one arm untested.
    pages = ('<section class="page" id="agenda">'
             '<p class="eyebrow">Agenda</p>'
             '<div class="body stack">'
             '<p class="listhead">A story the pages never tell</p>'
             '<ul><li>An agenda line quoted from no title anywhere</li></ul>'
             '<div class="band"><div class="k">41%</div>'
             '<div class="v">A number the agenda has no business making</div>'
             '</div>'
             # D38's two gating arms, planted: launch rows whose claims carry no
             # lime chip, and run lines that are a table of contents. The rule
             # names this exact shape — "a row reading ... pages 4 to 7 is a
             # table of contents wearing an agenda's clothes" — and a
             # conformance deck wrote it in both its rows.
             '<div class="fill"><div class="launch">'
             '<div class="lrow"><div class="ln">01</div><div>'
             '<p class="gn">What the estate measures today</p>'
             '<p class="gq">Coverage and the backlog, on pages 4 to 9.</p>'
             '</div></div>'
             '<div class="lrow"><div class="ln">02</div><div>'
             '<p class="gn">Where the reads actually fail</p>'
             # Long enough to wrap: `agenda_run_wrap`'s red. A conformance
             # deck packed three facts into 203 characters here and the row
             # rendered as two lines, which is the opposite of "a quiet run".
             '<p class="gq">Signal, terrain and the relay siting decision, '
             'with the crew allocation that follows from it and the cost of '
             'waiting another quarter before any of it is settled, '
             'on pages 10 to 15.</p>'
             '</div></div>'
             '</div></div></div>'
             '<div class="foot"><div class="terms"><span class="conf">'
             f'{TERMS}</span></div><span class="site">{SITE}</span></div>'
             '</section>') + pages
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Degenerate fixture (fails on purpose)</title>
<!-- generated by scripts/build/build_fixtures.py - do not hand-edit -->
<!-- NOT A WORKED EXAMPLE. Every defect here is deliberate and exists so that a
     metric which would otherwise be asserted ok on both fixtures has a case on
     which it fails. Read fixtures/deck-pass.en.html for what good looks like. -->
<style>
{shipped_css()}
/* D20_palette_fidelity: a SECOND :root redefining the accent to a colour this
   package does not ship. The document stays internally consistent — every use
   resolves, D4 sees no stray literal, D1 measures contrast against it — and
   that is the point: until 0.1.454 nothing compared a document's declared
   palette with the shipped one, so a deck could carry another design language
   and pass every check. The owner found it by eye on a conformance deck whose
   ten shared colour tokens disagreed ten times out of ten. */
:root {{ --acc: #0F6E6B; }}
*, *::before, *::after {{ box-sizing: border-box; }}
body {{ font-family: var(--din); font-size: 15px; color: var(--tx1);
        background: var(--bg); margin: 0; }}
/* D1_contrast: a text colour declared against the canvas it cannot be read on.
   --acc-5 is a pale ramp step meant for fills. */
.washed {{ color: var(--acc-5); }}
/* D13_lime_as_text: the acid green is a surface, never a member of the text
   ladder on the light canvas. Stated directly rather than left to D1, because
   D1 only catches it when surface detection resolves the right background. */
.limetext {{ color: var(--lime); }}
/* footer_baseline: one run lifted off the row's shared baseline. The shipped
   defect was subtler — the shield icon's replaced-element baseline capturing
   `.conf`, 2.4px on a 15px line box — but the probe measures the spread, not
   the mechanism, so the plant states the shift directly. */
#d3 .foot .site {{ position: relative; top: -3px; }}
/* page_height: a page that sets its own height past the 720px stage. A child
   cannot do this — `.page` is a fixed-height frame, so an overlong child spills
   and trips content_spill instead. Overriding the frame is what a document
   actually does wrong when a page runs long. */
#dtall {{ min-height: 900px; }}
/* content_hidden: a lede that clamps its own text away. tokens/lumi-layouts.css
   deliberately does NOT clamp `.lede` — a two-line clamp there once hid a third
   title line from readers — so a document reintroducing one is exactly the
   defect this gate exists to catch: the checker reads text nobody can see. */
.clamped {{ display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
            overflow: hidden; }}
ul {{ margin: 0; padding-left: 18px; color: var(--tx2); font-size: 14px; }}
</style></head><body data-geometry="landscape" data-genre="sales">
<!-- D19_vocabulary: #g-ground here and #i-shield below resolve to nothing. -->
<svg class="ground" viewBox="0 0 1280 720" aria-hidden="true"><use href="#g-ground"/></svg>
<section class="page cover" id="cover">
  <div class="body cover-grid">
    <div class="typeblock">
      <p class="wordmark">{new_deck.wordmark()}</p>
      <h1>{_TITLE} on the cover</h1>
    </div>
  </div>
  <!-- footer_wrap: handling terms long enough to take a second line in the
       footer row. inspect_layout counts LINE BOXES rather than comparing a
       scaled height to a fixed line-height, and this is the case that proves
       it still fires after that was fixed. -->
  <div class="foot"><div class="terms"><span class="conf"><svg class="ic"
  aria-hidden="true"><use href="#i-shield"/></svg>{TERMS} &#183; not for
  distribution outside the receiving organisation &#183; retain under the record
  schedule &#183; destroy on request &#183; this line exists to wrap</span></div>
  <span class="site">{SITE}</span></div></section>{pages}
<section class="page" id="dtall">
  <div class="body">
    <h2>{_TITLE} on the overlong page</h2>
    <div class="toolong"><p>{_LONG} once more.</p></div>
  </div>
  <div class="foot"><div class="terms"><span class="conf">{TERMS}</span></div>
  <span class="site">{SITE}</span></div></section>
<section class="page" id="dclamp">
  <div class="body">
    <h2>{_TITLE} on the clamped page</h2>
    <div class="lede"><p class="clamped">{_LONG} and then a third line that the
    clamp removes from the page without removing it from the markup, which is
    the shape of the defect: the checker reads text a reader cannot see.</p></div>
  </div>
  <div class="foot"><div class="terms"><span class="conf">{TERMS}</span></div>
  <span class="site">{SITE}</span></div></section>
<section class="page" id="dstarved">
  <div class="body">
    <h2>{_TITLE} on the starved page</h2>
    <!-- starved_column: .swap is a 1fr/34px/1fr grid and takes three children;
         with two, the second lands in the 34px arrow track. -->
    <div class="swaps"><div class="swap"><span class="no">{_LONG} before</span>
    <span class="yes">{_LONG} after</span></div></div>
  </div>
  <div class="foot"><div class="terms"><span class="conf">{TERMS}</span></div>
  <span class="site">{SITE}</span></div></section>
<section class="page" id="dnumbers">
  <div class="body">
    <h2>{_TITLE} on the unsourced page</h2>
    <!-- M2_number_sourcing: percentages and a currency amount on a page whose
         text carries no source marker at all. The window is the PAGE
         (writing-rules section 4 rule 6), so nothing here is sourced.
         M6_unsourced_ranges: a range figure in a block with no marker of its
         own. Rule 1 makes a range stricter than an ordinary figure — it must
         trace to a SINGLE source or it may not appear — so its window is the
         block, and one source three blocks away does not answer it. -->
    <p>Coverage sits at 41% against a target of 60%, and the shortfall is worth
    $2,400,000 across the estate.</p>
    <p>Rural read success runs 62&#8211;78% depending on terrain.</p>
    <!-- figure_distorts: three bars declaring 80, 4 and 1 with a minimum-width
         floor under them, so the 4 and the 1 come out the same length as each
         other and both far longer than their share. A shipped deliverable did
         exactly this and no metric could see it: the true values were already
         in the markup, one attribute away from the width that ignored them.
         Drawn on this page rather than its own so it adds no title and no
         sentence — M8_length_cv fails here by 0.003, and a fixture that
         narrow flips on any edit that is not measured against it. -->
    <div class="fig"><svg viewBox="0 0 400 90" preserveAspectRatio="xMidYMid meet"
      role="img" aria-label="Three counts, drawn wrong">
      <rect class="f-acc" x="60" y="8" width="320" height="18" data-datum="80"/>
      <rect class="f-acc" x="60" y="34" width="48" height="18" data-datum="4"/>
      <rect class="f-acc" x="60" y="60" width="48" height="18" data-datum="1"/>
    </svg></div>
  </div>
  <div class="foot"><div class="terms"><span class="conf">{TERMS}</span></div>
  <span class="site">{SITE}</span></div></section>
<section class="page" id="dreserve">
  <div class="body">
    <h2>{_TITLE} on the overspent page</h2>
    <!-- reserve_overspent: a lede far past the two-line reserve the title
         budget allows, and NOT clamped, so it pushes the page instead of
         hiding itself. The clamped page above is the other half of the same
         pair: one hides the overspend, this one spends it. -->
    <div class="lede"><p>{_LONG} first. {_LONG} second. {_LONG} third.
    {_LONG} fourth.</p></div>
  </div>
  <div class="foot"><div class="terms"><span class="conf">{TERMS}</span></div>
  <span class="site">{SITE}</span></div></section>
<section class="page closing" id="closing">
  <div class="body cover-grid">
    <div class="typeblock"><p class="wordmark">{new_deck.wordmark()}</p>
    <h2>{_TITLE} at the close</h2></div>
    <!-- D6_footer missing_source: the colophon names no provenance, and D6 asks
         the DOCUMENT once rather than every page. -->
    <div class="closenote"><p class="colophon">Built with lumi-style {VERSION}.</p></div>
  </div>
  <div class="foot"><div class="terms"><span class="conf">{TERMS}</span></div>
  <span class="site">{SITE}</span></div></section>
</body></html>
"""


# ── the Chinese fixture ───────────────────────────────────────────────────────
# PROSE ONLY, and that boundary is the point. The backlog files a Chinese
# fixture PAIR under a phase blocked on a font licence, because a fixture has to
# render and rendering Chinese needs a face this package has no right to embed.
# That is true of the RENDERED half. check_prose.py does not render anything, so
# the half that measures text was never blocked by the licence — it was blocked
# by nobody separating the two. This gives M4zh and M5 a case they fail on;
# a Chinese deck-pass, and anything inspect_layout must open, still waits.
ZH_DEFECTS = """<section class="page"><h2>众所周知，这个结论是显然的</h2>
<p>值得注意的是,覆盖率停留在 41%,而目标是 60%。</p>
<p>综上所述:科技赋能了整个行业!这一点不可否认。</p>
<p>让我们一起看下一步;总而言之,还需要三个决定。</p></section>"""

# The same page with every defect removed: full-width punctuation throughout,
# no banned phrase, and 赋能 only in the collocation section 2 allows.
ZH_CLEAN = """<section class="page"><h2>覆盖率停留在 41%</h2>
<p>覆盖率停留在 41%，目标是 60%，差距集中在两个区域。</p>
<p>销售赋能是这里唯一允许的用法。</p>
<p>下一步需要三个决定：中继选址、班组分配、估算率是否成为上报指标。</p></section>"""


def build_zh(broken: bool, localized: bool = True) -> str:
    body = ZH_DEFECTS if broken else ZH_CLEAN
    label = ("broken" if broken else "pass") if localized else "unasked"
    # M16's failing case, and it is the BROKEN fixture's job to carry it: a
    # Chinese deliverable with no provenance at all. The pass fixture carries
    # the three declarations `localize.py` writes, because a Chinese
    # deliverable somebody asked for is a legitimate document and must read
    # `ok` rather than being exempted — and `data-localized-from` has to name a
    # file that is really there, which for a fixture is the English deck
    # sitting beside it in the same directory.
    # THREE fixtures, because there are three states and each needs one that
    # fails it. `localized` carries the provenance `localize.py` writes, so the
    # Chinese ban list and the punctuation pass are GRADED on it — which is
    # what makes the broken one able to fail them. `unasked` carries none, so
    # M16 fails and the Chinese metrics fall silent by design (0.1.588): the
    # package does not coach a language a document has no recorded ask to be
    # in. `data-localized-from` has to name a file that is really there, which
    # for a fixture is the English deck beside it.
    asked = ("" if not localized else
             ' data-lang-asked="zh"'
             ' data-lang-ask-quote="\u8bf7\u628a\u62a5\u544a\u5199\u6210\u4e2d\u6587"'
             ' data-localized-from="deck-pass.en.html"')
    return f"""<!doctype html>
<html lang="zh"><head><meta charset="utf-8">
<title>中文校验样本（{label}）</title>
<!-- generated by scripts/build/build_fixtures.py - do not hand-edit.
     Prose fixture only: no token block, no stylesheet, nothing to render. It
     exists so check_prose.py's Chinese path has a document that fails it. -->
</head><body data-geometry="landscape" data-genre="sales"{asked}>{body}</body></html>
"""


def build_figure() -> str:
    """A one-page deliverable whose figure is DRAWN FROM A SPEC.

    It exists so the browser gates that grade a drawing have something to
    grade. Measured before it existed: `inspect_layout --deliverable` reported
    `figure_distorts` and `figure_axis_named` as `n/a` on every tracked
    fixture, because not one of them carried a mark declaring the value it
    draws. Two gates reported clean on a corpus that could not make them fail,
    which is FM-01 at the fixture layer rather than in the checker.

    The drawing comes from `scatter_svg.render` and the spec from
    `fixtures/figures/scatter-demo.json`, so the fixture goes stale — loudly,
    through `build_fixtures --check` — the moment either changes. A fixture
    hand-copied from a renderer's output is a fixture that stops describing it.
    """
    import figure_spec
    import scatter_svg
    spec_path = ROOT / "fixtures" / "figures" / "scatter-demo.json"
    spec, problem = figure_spec.load(spec_path)
    if problem:
        raise SystemExit(problem)
    svg = scatter_svg.render(spec, trend="smooth", path=str(spec_path))
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>A figure drawn from its own data</title>
<style>
{shipped_css()}
</style></head>
<body>
{ground_defs()}
{SPRITE}
<section class="page cover-grid" id="cover" data-role="cover">
  <div class="gd"></div>
  <h1 class="ct">Support hours buy adoption only to a point</h1>
  <p class="cs">A fixture whose one figure declares the data it draws.</p>
  {opener_mark("globe")}
  <p class="colophon">Every figure on the following page is drawn from the spec
  it names; the numbers are illustrative and are sourced from that file.</p>
{foot(1, 2)}
</section>
<section class="page" id="p2" data-analysis="correlate"
         data-figure-spec="figures/scatter-demo.json">
  <div class="gd"></div>
  <div class="body stack">
    <div class="lede">
      <p class="eyebrow">Part A &#183; support economics</p>
      <h2 class="t">Adoption rises with support hours, then flattens near forty</h2>
      <p class="sup">Feature adoption, % of seats, first twelve months after signup.</p>
    </div>
    <div class="fill">
      <div class="fig">{svg}
      <div class="cap"><span class="n">Figure 1</span> Adoption flattens past
      forty support hours</div></div>
      <p class="take">Past forty hours more support stops buying adoption.</p>
    </div>
  </div>
{foot(2, 2)}
</section>
</body></html>'''


def targets() -> dict[str, str]:
    return {"fixtures/deck-pass.en.html": build(False),
            "fixtures/deck-figure.en.html": build_figure(),
            "fixtures/deck-broken.en.html": build(True),
            "fixtures/deck-degenerate.en.html": build_degenerate(),
            "fixtures/prose-zh-pass.zh.html": build_zh(False),
            "fixtures/prose-zh-broken.zh.html": build_zh(True),
            "fixtures/prose-zh-unasked.zh.html": build_zh(False, localized=False)}


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    stale = []
    for path, content in sorted(targets().items()):
        target = ROOT / path
        current = target.read_text(encoding="utf-8") if target.exists() else None
        if current == content:
            continue
        if args.check:
            stale.append(path)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
    if args.check:
        for path in stale:
            print(f"FAIL  {path} {STALE}")
        if not stale:
            print("ok    fixtures are current")
        return 1 if stale else 0
    print(f"wrote {len(targets())} fixtures")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
