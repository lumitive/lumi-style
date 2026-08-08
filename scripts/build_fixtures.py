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


def tokens_block() -> str:
    """The :root block, lifted from tokens/ so the fixture cannot grade itself
    against a palette the skill has stopped shipping."""
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
    return ":root {" + css[start + len(":root {"):i] + "}"


def foot(n: int, total: int, terms: str = TERMS, site: str = SITE) -> str:
    # Spans, never a nested div: d12_commercial_footer captures non-greedily to
    # the first </div>, so a div inside .foot truncates the text it reads.
    return (f'<div class="foot"><span class="conf">{terms}</span>'
            f'<span class="src">Meter management system</span>'
            f'<span class="site">{site}</span><span>{n:02d} / {total:02d}</span></div>')


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
        if i == 5:
            style = ' style="border-color:#ABCDEF"'          # D4 literal colour
        if i == 7:
            terms = "Prepared for circulation"               # D12: no handling terms
        if i == 9:
            sup = sup + " The gap is measured against a baseline taken in the first "\
                        "quarter of the programme, before the rural feeders had been "\
                        "surveyed at all, which makes the comparison generous."  # M8 overlong
    lis = "".join(f"<li>{b}</li>" for b in bullets)
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
    return f"""
<section class="page" id="p{i}">
  <div class="body split">
    <div class="lede">
      <p class="eyebrow">{eyebrow}</p>
      <h2 class="t">{title}</h2>
      <p class="sup">{sup}</p>
    </div>
    <div class="fill">
      <p class="listhead">What the data shows</p>
      <p class="gd"{style}>{gd}</p>
      <ul>{lis}</ul>
      {band}{lead}
    </div>
    <div class="fill">
      <div class="fig"><svg viewBox="0 0 640 186" preserveAspectRatio="xMidYMid meet"
        role="img" aria-label="bars"><rect class="f-acc" x="0" y="0" width="380"
        height="46" fill="var(--acc)"/><rect class="f-acc" x="0" y="70" width="250"
        height="46" fill="var(--acc)"/><rect class="f-acc" x="0" y="140" width="170"
        height="46" fill="var(--acc)"/></svg>
      <div class="cap"><span class="n">Figure {i}</span> Reads by feeder class
      <span class="srcline">Meter management system, extract of the period</span></div></div>
    </div>
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
{tokens_block()}
*, *::before, *::after {{ box-sizing: border-box; }}
body {{ font-family: var(--din); font-size: 15px; color: var(--tx1);
        background: var(--bg); margin: 0; }}
.page {{ position: relative; display: flex; flex-direction: column;
         padding: 46px 92px 26px; min-height: 720px; }}
.body {{ flex: 1; display: grid; gap: 26px; }}
.body.split {{ grid-template-columns: 1fr 1fr; grid-template-rows: auto 1fr; }}
.body.split > .lede {{ grid-column: 1 / -1; }}
.lede {{ display: flex; flex-direction: column; gap: 10px; }}
.eyebrow {{ font-family: var(--mono); font-size: 12px; font-weight: 700;
            letter-spacing: var(--ls-eyebrow); text-transform: uppercase; color: var(--tx3); }}
h1 {{ font-size: var(--fs-display); font-weight: var(--w-display);
      line-height: var(--lh-display); color: var(--tx1); margin: 0 0 24px; }}
h2 {{ font-size: var(--fs-title); font-weight: var(--w-title);
      line-height: 1.02; color: var(--tx1); margin: 0; }}
.sup {{ font-size: var(--fs-support); font-weight: var(--w-support);
        line-height: 1.42; color: var(--tx2); }}
.listhead {{ font-family: var(--mono); font-size: 11.5px; letter-spacing: .16em;
             text-transform: uppercase; color: var(--tx3); }}
.gd {{ border-left: 2px solid var(--ln1); padding: 2px 0 2px 15px;
       font-size: var(--fs-fig-title); line-height: 1.5; color: var(--tx2); }}
ul {{ margin: 0; padding-left: 18px; color: var(--tx2); font-size: 14px; }}
.band {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px;
          align-items: start; }}
.band > div {{ display: flex; flex-direction: column; gap: 8px; }}
.band .k {{ font-family: var(--mono); font-size: var(--fs-fine); letter-spacing: .16em;
            text-transform: uppercase; color: var(--tx3); }}
.band .v {{ font-size: var(--fs-band-value); font-weight: 700; line-height: .92;
            color: var(--tx1); }}
.band .v .u {{ font-size: .42em; color: var(--tx3); }}
.lead {{ display: flex; flex-direction: column; gap: 10px; }}
.lead .v {{ font-size: var(--fs-lead); line-height: .94; color: var(--tx1); }}
.lead .g {{ font-family: var(--mono); font-size: var(--fs-fine); letter-spacing: .12em;
            text-transform: uppercase; color: var(--tx3); }}
.cap {{ font-family: var(--mono); font-size: var(--fs-source); color: var(--tx3); }}
.cap .n {{ font-weight: 700; font-size: var(--fs-fine); color: var(--tx2); }}
.foot {{ display: flex; gap: 18px; align-items: baseline; font-family: var(--mono);
         font-size: var(--fs-source); color: var(--tx4); }}
.foot .site {{ margin-right: auto; color: var(--acc); }}
.colophon {{ font-family: var(--mono); font-size: var(--fs-source); color: var(--tx4); }}
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
