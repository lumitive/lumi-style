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

    python3 scripts/build_fixtures.py            # write
    python3 scripts/build_fixtures.py --check    # verify current (CI)
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "fixtures"
STALE = "is stale or missing; re-run without --check"

# The icon sprite comes from the vendored library via embed_icons.sprite(), so
# the fixture exercises the same path a deliverable uses and cannot drift from
# the library it claims to demonstrate.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from embed_icons import sprite  # noqa: E402

TERMS = "Confidential &#183; internal use &#183; do not forward"
SITE = "www.example.org"

# The producing-skill version, for the colophon the cover rule requires. Read
# from SKILL.md so it cannot drift; the fixtures already regenerate every
# release because the embedded token block carries the version stamp.
_version_m = re.search(r'^\s*version:\s*"([^"]+)"',
                       (ROOT / "SKILL.md").read_text(encoding="utf-8"), re.M)
if _version_m is None:
    raise SystemExit("SKILL.md frontmatter carries no version stamp; "
                     "the fixtures cannot state what produced them")
VERSION = _version_m.group(1)

# The cover/closing mark, inlined verbatim from the generated asset.
GLOBE = (ROOT / "assets/vectors/globe-orthographic.svg").read_text(encoding="utf-8").strip()

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
     ["Relay siting needs a survey.", "Crew allocation needs a decision."]),
]

# The eyebrow sprite plus the footer's handling marker.
SPRITE = sprite([p[0] for p in PAGES] + ["shield"])


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
    return (":root {" + css[start + len(":root {"):i] + "}\n"
            + (ROOT / "tokens/lumi-layouts.css").read_text(encoding="utf-8"))


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
      </svg>
      <div class="cap"><span class="n">Figure {i}</span> The gap follows terrain,
      not meter age, so relay siting is the lever
      <span class="srcline">Meter management system, extract of the period</span></div></div>
    </div>"""

# The rect-only figure the broken fixture keeps, so D5 has a subject.
FIGURE_WEAK = """<div class="fill">
      <div class="fig"><svg viewBox="0 0 640 186" preserveAspectRatio="xMidYMid meet"
        role="img" aria-label="bars"><rect class="f-acc" x="0" y="0" width="380"
        height="46" fill="var(--acc)"/><rect class="f-acc" x="0" y="70" width="250"
        height="46" fill="var(--acc)"/><rect class="f-acc" x="0" y="140" width="170"
        height="46" fill="var(--acc)"/></svg>
      <div class="cap"><span class="n">Figure {i}</span> Reads by feeder class
      <span class="srcline">Meter management system, extract of the period</span></div></div>
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


def page(i: int, total: int, spec, broken: bool) -> str:
    icon, eyebrow, title, sup, bullets = spec
    # The eyebrow contract (design-rules §3): subject icon, then
    # `PART <letter> · <label>`. Pages 3-9 sit under Part A, 11-17 under Part B.
    part = "A" if i <= 9 else "B"
    gd = ("A callout carries the aside a reader should not miss, and no more than one "
          "of them belongs on a page.")
    style = ""
    terms = TERMS
    src = ""
    if broken:
        if i == 4:
            gd = ("Leveraging a seamless framework, this callout showcases a robust "
                  "and comprehensive approach.")            # M4 banned phrases
        if i == 12:
            # D4 literal colour. It sat on page 5 until 0.1.369, which then became
            # a `stack` page carrying cards and no `.gd` at all — so the planted
            # defect silently vanished and D4 came back `ok` on the fixture whose
            # whole job is to make it fire. `check_fixtures.py` caught it, which
            # is the assertion earning its place: a defect that stops being
            # planted is indistinguishable from a check that stopped working.
            style = ' style="border-color:#ABCDEF"'
        if i == 8:
            terms = "Prepared for circulation"               # D12: no handling terms
        if i == 7:
            # a real prose em-dash, which M9 must still catch
            sup = "The gap is signal &#8212; not hardware, and it follows terrain."
        if i == 14:
            # M12: visible CJK in a document that declares English. The Chinese
            # here is rule DATA — the defect under test — exactly as banned
            # phrases and punctuation examples are elsewhere in this package.
            # A real deliverable named `*.en.html`, carrying `lang="en"`, shipped
            # a badge like this in a page lede and passed every metric.
            sup = "\u5df2\u56de\u6536 15/15 \u9898. Coverage held across the surveyed feeders."
        if i == 15:
            # D15: a repository path poured into the footer as a "source". The
            # second document to do this; 0.1.366 removed `.foot .src` from
            # tokens/ after the first.
            src = ('<span class="src">resources/'
                   '\u60c5\u62a5\u6e90\u76ee\u5f55-20260730.zh.html</span>')
        if i == 13:
            # D14: the slot an author leaves for themselves and then ships. A
            # real deliverable carried four of these on its closing page and
            # every check in this package passed it, because a placeholder is
            # not a banned phrase, not a colour, and occupies exactly as much
            # room as the text that should have replaced it.
            sup = "Read success held at [TO FILL]% across the surveyed feeders."
        if i == 11:
            sup = sup + " The gap is measured against a baseline taken in the first "\
                        "quarter of the programme, before the rural feeders had been "\
                        "surveyed at all, which makes the comparison generous."  # M8 overlong
    lis = "".join(f"<li>{b}</li>" for b in bullets)
    # Page 12 carries the graded ladder and page 17 the glossary, so the two
    # block patterns promoted in 0.1.375 are exercised by the suite instead of
    # merely shipped; check_prose counts both as enumerations (M10).
    listblock = f"<ul>{lis}</ul>"
    if i == 12:
        listblock = (
            '<div class="grades">'
            '<div class="gr g4"><i></i><p class="gn">Estimate rate, weekly</p>'
            '<p class="gq">leads the read rate by a cycle</p></div>'
            '<div class="gr g3"><i></i><p class="gn">Read rate</p></div>'
            '<div class="gr g2"><i></i><p class="gn">Backlog count</p></div>'
            '<div class="gr g1"><i></i><p class="gn">Crew hours</p>'
            '<p class="gc">recorded, but not predictive</p></div></div>')
    if i == 17:
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
    if i == 9:
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
        band = ('<div class="band">'
                '<div><span class="k">Coverage</span><div class="v">41<span class="u">%</span></div></div>'
                '<div><span class="k">Feeders</span><div class="v">312</div></div>'
                '<div><span class="k">Estimates</span><div class="v">8.4</div></div>'
                '</div>')
    # The field, exercised at last: brand.md names it the deck's signature and
    # inspect_layout audits it, yet no fixture had ever drawn one — a mark per
    # datum, each carrying its data-datum, intensity from the datum.
    field = ""
    if i == 4:
        marks = "".join(f'<i data-w="{(k * 3) % 5 + 1}" data-datum="F{k + 1:02d}"></i>'
                        for k in range(12))
        field = ('<p class="listhead">Feeder signal strength</p>'
                 f'<div class="field tall" data-count="12">{marks}</div>')
    lead = ""
    if i not in (3, 4):
        lead = f'<div class="lead"><div class="v">{i * 7}</div>' \
               f'<p class="g">Units returned per avoided visit, illustrative</p></div>'
    if broken and i == 16:
        # D16: a page with no visual block at all — no figure, no band, no
        # lead, no comparison pattern; prose, a list and a callout. The static
        # half of the visual-share directive reports it as prose-only.
        lead = ""
    # One page each for the four block patterns; every other page keeps the
    # figure. The tier-1 pair is exercised in both colours on DIFFERENT pages:
    # `.key` in page 5's notes column and `.red` in page 8's, because D3 budgets
    # tier-1 callouts at one per page and putting both on one page trips it —
    # which the fixture should demonstrate obeying, not by luck.
    if i == 8:
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
    fig = FIGURE_WEAK if (broken and i == 4) else FIGURE
    layout, cells = "split", argument + "\n    " + fig.format(i=i)
    if broken and i == 16:
        layout, cells = "stack", argument
    if i == 5:
        layout, cells = "sidebar-notes", argument + "\n    " + NOTES
    # A one-line `.lead.row` above each block. Two purposes: it gives these two
    # pages an entry point — without it `inspect_layout.py` reports them as the
    # only pages in the deck with nothing above body copy — and `.lead.row` is a
    # shipped pattern that nothing in this repository rendered until now, which
    # is how its `flex-direction: row` lost an argument to the fill rule twice.
    row = ('<div class="lead row"><div class="v">41<span class="u">%</span></div>'
           '<p class="g">Metering coverage, illustrative</p></div>')
    if i == 6:
        layout, cells = "stack", f'<div class="fill">{row}{CARDS}</div>'
    if i == 7:
        layout, cells = "stack", f'<div class="fill">{row}{VOWS}</div>'
    return f"""
<section class="page" id="p{i}">
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


def opener(part: str, number: int, total: int, claim: str, run: str) -> str:
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
    </div>
  </div>
  {foot(number, total)}</section>"""


def build(broken: bool) -> str:
    total = len(PAGES) + 4   # cover, two part openers, closing
    # Cover and closing are the same kind of page, set the same way: cover-grid,
    # with the orthographic globe as the one vector mark on each (the closing
    # repeats the cover's geography rather than introducing a new claim).
    cover = f"""
<section class="page cover" id="cover">
  {GROUND}
  <div class="body cover-grid">
    <div class="typeblock">
      <p class="wordmark">LUMI</p>
      <h1>Metering programme review</h1>
      <p class="sub">A synthetic deliverable. Every figure here is invented.</p>
    </div>
    <div class="markcell">{GLOBE}</div>
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
      <p class="wordmark">LUMI</p>
      <h2>What to settle this month</h2>
      <p class="sub">Relay siting first, then crew allocation.</p>
    </div>
    <div class="markcell">{GLOBE}</div>
    <div class="attrs">
      <div><span class="k">Owner</span><span class="v">The analysis team</span></div>
      <div><span class="k">Source</span><span class="v">Meter management system</span></div>
    </div>
    <div class="closenote"><p class="colophon">Built with lumi-style {VERSION}.
    Source: meter management system; every number here is invented, and a
    bracketed slot must not ship.</p></div>
  </div>
  {foot(total, total)}</section>"""

    body = (cover
            + opener("A", 2, total, "What the estate measures today",
                     "Seven pages: coverage, the backlog, and what a read is worth.")
            + "".join(page(i + 3, total, s, broken)
                      for i, s in enumerate(PAGES[:7]))
            + opener("B", 10, total, "Where the reads actually fail",
                     "Seven pages on signal, terrain and the relay siting decision.")
            + "".join(page(i + 11, total, s, broken)
                      for i, s in enumerate(PAGES[7:]))
            + closing)
    label = "broken" if broken else "pass"
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Metering programme review ({label} fixture)</title>
<!-- generated by scripts/build_fixtures.py - do not hand-edit -->
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
.band {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }}
.band > div {{ display: flex; flex-direction: column; gap: 8px; }}
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
</style></head><body data-geometry="landscape" data-genre="sales">{SPRITE}{GROUND_DEFS}{body}</body></html>
"""


def targets() -> dict[str, str]:
    return {"fixtures/deck-pass.en.html": build(False),
            "fixtures/deck-broken.en.html": build(True)}


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
