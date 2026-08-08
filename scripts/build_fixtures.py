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

TERMS = "Confidential &#183; internal use &#183; do not forward"
SITE = "www.example.org"

# Titles deliberately spread across five frames. M11 fails a deck whose titles
# all take one shape, and a fixture that trips it by accident teaches nothing.
PAGES = [
    ("Coverage", "Metering coverage reached 41% of the estate",
     "Two regions carry most of the shortfall, and both are rural.",
     ["Rural feeders were surveyed last.", "Access needs a scheduled outage."]),
    ("Backlog", "Why the install backlog stopped shrinking",
     "Crew hours moved to fault response in the second quarter.",
     ["Fault response has first call on crews.", "Installs resume when the queue clears."]),
    ("Reads", "Read success: 96.2% on urban feeders, 71.4% on rural",
     "The gap is signal, not hardware, and it follows terrain rather than meter age.",
     ["Signal strength tracks terrain closely.", "Meter age shows no correlation."]),
    ("Cost", "Each avoided truck roll returns 38 units",
     "The figure holds only where a read succeeds on the first attempt.",
     ["A second attempt erases the saving.", "Third attempts cost more than a visit."]),
    ("Risk", "Three assumptions carry the forecast",
     "Each one is checkable, and one of them has already moved.",
     ["Crew availability held through June.", "Signal coverage assumptions have not."]),
    ("Sequence", "Install density beats install count",
     "Clustering work by feeder cuts travel more than raising the daily target.",
     ["Travel is the largest non-productive cost.", "Density compounds across a week."]),
    ("Quality", "What a failed read actually costs",
     "A failed read is not a missing number; it is an estimate that later has to be corrected.",
     ["Estimates propagate into billing.", "Corrections arrive two cycles later."]),
    ("Signal", "Can the rural gap close without new hardware?",
     "Relay siting explains more of the variance than any equipment choice does.",
     ["Relay siting was never optimised.", "Two candidate sites are already owned."]),
    ("Crews", "Crew training pays back inside one quarter",
     "Trained crews complete more first-attempt reads, which is where the return sits.",
     ["First-attempt rate rises with training.", "The effect persists after six months."]),
    ("Data", "The estimate rate is the number to watch",
     "It moves before the read rate does, so it gives roughly a cycle of warning.",
     ["Estimate rate leads read rate.", "One cycle is enough to reschedule."]),
    ("Scope", "What this analysis does not cover",
     "Commercial meters, prepayment customers, and anything outside the two named regions.",
     ["Commercial meters have their own programme.", "Prepayment is a separate contract."]),
    ("Evidence", "Every figure here traces to the meter management system",
     "Extracts are dated, and the extract date is on each figure.",
     ["Extracts are dated at source.", "No figure is carried between extracts."]),
    ("Decision", "Reschedule the rural phase, or accept the estimate rate",
     "Those are the two options; a third that changes neither has not been found.",
     ["Rescheduling costs one quarter.", "Accepting it costs billing accuracy."]),
    ("Next", "Three things to settle before the next cycle",
     "Relay siting, crew allocation, and whether the estimate rate becomes a reported metric.",
     ["Relay siting needs a survey.", "Crew allocation needs a decision."]),
]


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


def foot(n: int, total: int, terms: str = TERMS, site: str = SITE) -> str:
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
    return (f'<div class="foot"><div class="terms"><span class="conf">{terms}</span></div>'
            f'<span class="site">{site}</span><span>{n:02d} / {total:02d}</span></div>')


# The four block patterns, one page each. Until 0.1.369 the fixture used none of
# them, so `tokens/` could ship a font-size for `.key`, `.no`, `.yes`, `.ledname`
# and `.card dd` inside the portrait media query and nowhere else, and nothing in
# this repository would ever render one. A reference implementation that skips a
# quarter of the shipped vocabulary cannot tell a working rule from an absent one
# — which is the same argument that put `lumi-layouts.css` into this file at all.
#
# Placed on the right-hand cell so each page keeps its lede, its footer and its
# left column, and the datum still holds across all sixteen.
FIGURE = """<div class="fill">
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
    eyebrow, title, sup, bullets = spec
    gd = ("A callout carries the aside a reader should not miss, and no more than one "
          "of them belongs on a page.")
    style = ""
    terms = TERMS
    if broken:
        if i == 3:
            gd = ("Leveraging a seamless framework, this callout showcases a robust "
                  "and comprehensive approach.")            # M4 banned phrases
        if i == 10:
            # D4 literal colour. It sat on page 5 until 0.1.369, which then became
            # a `stack` page carrying cards and no `.gd` at all — so the planted
            # defect silently vanished and D4 came back `ok` on the fixture whose
            # whole job is to make it fire. `check_fixtures.py` caught it, which
            # is the assertion earning its place: a defect that stops being
            # planted is indistinguishable from a check that stopped working.
            style = ' style="border-color:#ABCDEF"'
        if i == 7:
            terms = "Prepared for circulation"               # D12: no handling terms
        if i == 6:
            # a real prose em-dash, which M9 must still catch
            sup = "The gap is signal &#8212; not hardware, and it follows terrain."
        if i == 11:
            # D14: the slot an author leaves for themselves and then ships. A
            # real deliverable carried four of these on its closing page and
            # every check in this package passed it, because a placeholder is
            # not a banned phrase, not a colour, and occupies exactly as much
            # room as the text that should have replaced it.
            sup = "Read success held at [TO FILL]% across the surveyed feeders."
        if i == 9:
            sup = sup + " The gap is measured against a baseline taken in the first "\
                        "quarter of the programme, before the rural feeders had been "\
                        "surveyed at all, which makes the comparison generous."  # M8 overlong
    lis = "".join(f"<li>{b}</li>" for b in bullets)
    # A table whose last cell is an em-dash placeholder — "no value", the
    # standard convention. M9 bans em-dashes in PROSE and counted this, failing
    # a deliverable that had none. Found by running the checker against real
    # agent output; the fixtures we wrote ourselves never used a placeholder.
    cell = ""
    if i == 8:
        cell = ('<table><tbody><tr><td>Rural feeders</td><td>41</td></tr>'
                '<tr><td>Deferred</td><td>&#8212;</td></tr></tbody></table>')
    # Pages 2 and 3 carry a stat band and a display lead. Without them the
    # fixture never exercises `.band .k`, `.band .v` or the focal element, and
    # inspect_layout.py correctly reports those roles as NOT MEASURED — a
    # reference implementation that skips a third of the role vocabulary is not
    # a reference implementation.
    band = ""
    if i in (2, 3):
        band = ('<div class="band">'
                '<div><span class="k">Coverage</span><div class="v">41<span class="u">%</span></div></div>'
                '<div><span class="k">Feeders</span><div class="v">312</div></div>'
                '<div><span class="k">Estimates</span><div class="v">8.4</div></div>'
                '</div>')
    lead = ""
    if i not in (2, 3):
        lead = f'<div class="lead"><div class="v">{i * 7}</div>' \
               f'<p class="g">Units returned per avoided visit, illustrative</p></div>'
    # One page each for the four block patterns; every other page keeps the
    # figure. The tier-1 pair is exercised in both colours on DIFFERENT pages:
    # `.key` in page 4's notes column and `.red` in page 7's, because D3 budgets
    # tier-1 callouts at one per page and putting both on one page trips it —
    # which the fixture should demonstrate obeying, not by luck.
    if i == 7:
        gd = ('<p class="red">The seal colour marks a red line, never emphasis. '
              'A page carries at most one tier-1 callout.</p>')
    else:
        gd = f'<p class="gd"{style}>{gd}</p>'
    argument = f"""<div class="fill">
      <p class="listhead">What the data shows</p>
      {gd}
      <ul>{lis}</ul>
      {cell}{band}{lead}
    </div>"""
    layout, cells = "split", argument + "\n    " + FIGURE.format(i=i)
    if i == 4:
        layout, cells = "sidebar-notes", argument + "\n    " + NOTES
    # A one-line `.lead.row` above each block. Two purposes: it gives these two
    # pages an entry point — without it `inspect_layout.py` reports them as the
    # only pages in the deck with nothing above body copy — and `.lead.row` is a
    # shipped pattern that nothing in this repository rendered until now, which
    # is how its `flex-direction: row` lost an argument to the fill rule twice.
    row = ('<div class="lead row"><div class="v">41<span class="u">%</span></div>'
           '<p class="g">Metering coverage, illustrative</p></div>')
    if i == 5:
        layout, cells = "stack", f'<div class="fill">{row}{CARDS}</div>'
    if i == 6:
        layout, cells = "stack", f'<div class="fill">{row}{VOWS}</div>'
    return f"""
<section class="page" id="p{i}">
  <div class="body {layout}">
    <div class="lede">
      <p class="eyebrow">{eyebrow}</p>
      <h2 class="t">{title}</h2>
      <p class="sup">{sup}</p>
    </div>
    {cells}
  </div>
  {foot(i, total, terms)}</section>"""


def build(broken: bool) -> str:
    total = len(PAGES) + 2
    cover = f"""
<section class="page cover" id="cover">
  <div class="body stack no-lede"><div class="fill">
    <h1>Metering programme review</h1>
    <p class="sup">A synthetic deliverable. Every figure here is invented.</p>
  </div></div>
  {foot(1, total)}</section>"""
    closing = f"""
<section class="page closing" id="closing">
  <div class="body stack no-lede"><div class="fill">
    <h2>What to settle this month</h2>
    <p class="sup">Relay siting first, then crew allocation.</p>
    <p class="colophon">Source: meter management system. Prepared by the analysis team.</p>
  </div></div>
  {foot(total, total)}</section>"""
    body = cover + "".join(page(i + 2, total, s, broken) for i, s in enumerate(PAGES)) + closing
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
   layouts, the role vocabulary, the footer row, the page stage — now comes from
   tokens/lumi-layouts.css above, so the fixture exercises the shipped
   stylesheet instead of a private copy of it. */
.page {{ position: relative; display: flex; flex-direction: column;
         padding: 46px 92px 26px; }}
ul {{ margin: 0; padding-left: 18px; color: var(--tx2); font-size: 14px; }}
.band {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }}
.band > div {{ display: flex; flex-direction: column; gap: 8px; }}
.band .v .u {{ font-size: .42em; color: var(--tx3); }}
.cap {{ font-family: var(--mono); font-size: var(--fs-source); color: var(--tx3); }}
.colophon {{ font-family: var(--mono); font-size: var(--fs-source); color: var(--tx4); }}
.foot {{ font-family: var(--mono); font-size: var(--fs-source); color: var(--tx4); }}
</style></head><body>{body}</body></html>
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
