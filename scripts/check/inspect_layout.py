#!/usr/bin/env python3
"""Render a deliverable page by page and report what the layout actually does.

This exists because SKILL.md rule 4 says a page is done when a human reads it as
intentional, and 27 pages across two geometries and two palettes is 108 screens.
Nobody looks at 108 screens by scrolling. So the real output is a **contact
sheet**: every page as one image, per geometry, for a person to judge at a glance.

The numbers beside it answer the question a fill percentage could not:

  centerpiece scale    how much of the content area the figure or table occupies.
                       This is what "the chart is too small" means.
  aspect mismatch      figure aspect against its cell's aspect. A 5:1 diagram in
                       a 1.8:1 cell renders at 40% of the height however it is
                       scaled, and no amount of CSS fixes it — the drawing is
                       wrong for the page.
  largest empty rect   the biggest clear rectangle on the page, which is what
                       "looks empty" means geometrically.

**No judgement here gates.** Release 0.1.339 answered "the pages look empty" with
an 82% fill floor, satisfied it by stretching table rows, and shipped four
diagrams at 40% of their cell. A number that can be satisfied without improving
the page ends the looking.

**A check that did not run is not a check that passed.** Every summary below is
written `if <defects>: LOUD else: reassuring`, and until 0.1.350 the reassuring
branch also fired when the probe had matched nothing at all: a document with no
`section.page` reported "one horizon on each of 0 pages" and exit 0, and a
document whose class vocabulary differed from the probe's lost eight of ten role
checks without printing a word. Absence of vocabulary is not absence of defects.
So this file now carries the concept its sibling `check_design.py` already had —
`Unmeasurable`, printed as `NOT MEASURED (<reason>)` — and **exit code is 1 when
anything could not be measured**. That is not a gate on the design; it is the
difference between a probe that says nothing and a probe that says everything is
fine. The judgements themselves still gate nothing.

    python3 scripts/check/inspect_layout.py ~/Documents/LUMI-Style/deck.html
    python3 scripts/check/inspect_layout.py ~/Documents/LUMI-Style/deck.html --geometry a4
    python3 scripts/check/inspect_layout.py ~/Documents/LUMI-Style/deck.html --dark
    python3 scripts/check/inspect_layout.py ~/Documents/LUMI-Style/deck.html --json

Needs Playwright with Chromium (`pip install pillow playwright && playwright
install chromium`). Pillow is needed only for the ground contrast audit, which
reports `NOT MEASURED` without it rather than disappearing.
"""
from __future__ import annotations

import argparse
import collections
import contextlib
import io
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
import tempfile
from contextlib import redirect_stdout
from typing import Any

_SCRIPTS_ROOT = next(p for p in _bs_pathlib.Path(__file__).resolve().parents
                     if p.name == "scripts")
for _sub in ("lib", "render", "check", "build", "ops", ""):
    _p = str(_SCRIPTS_ROOT / _sub) if _sub else str(_SCRIPTS_ROOT)
    if _p not in _bs_sys.path:
        _bs_sys.path.append(_p)
del _bs_pathlib, _bs_sys, _SCRIPTS_ROOT, _sub, _p
# --- end bootstrap ---
import color_math  # noqa: E402 — after the bootstrap, deliberately
import deliverable_registry  # noqa: E402


class Unmeasurable(Exception):
    """A check could not run. Never silently a pass — see the module docstring.

    Same type and same contract as `check_design.py`'s `Unmeasurable`. That script has printed
    `UNMEASURABLE` and returned non-zero since 0.1.339 while this one, sitting in
    the same directory, expressed all five of its failure paths as silence.
    """


# Two things every render waits for. Fixed sleeps alone are what let a report be
# measured against fallback font metrics and printed as fact: this package
# embeds a display face (`scripts/build/embed_font.py`), and every number in the report
# is a distance between glyphs that have not necessarily arrived yet.
SETTLE_MS = 350

# The two page geometries every LUMI deliverable serves (SKILL.md, and
# design-rules.md §8). Landscape is primary; portrait is a composition, not a
# reflow, so it is measured separately rather than assumed to follow.
GEOMETRIES = {
    "16x9":   (1280, 720),
    "16x9-hd": (1920, 1080),
    "a4":     (794, 1123),
    "laptop": (1000, 550),
    # Deliberately not a design geometry. A constraint set on one child of the
    # page frame is exact at 1280 and wrong everywhere else, so one render of a
    # size nobody designed for is worth more here than a third designed one.
    "wide":   (1800, 1000),
}
# EVERY geometry the rules name, plus the one off-design render. Until 0.1.390
# this was ["16x9", "a4", "wide"] and the other two were unreachable without a
# flag — including `laptop`, which design-rules.md §8 names explicitly and tells
# you what it catches ("a short laptop window (e.g. 1000x550)"), and `16x9-hd`,
# which §7 also names ("checked at 1920x1080") and is the shape a deck is
# actually projected at in most rooms.
#
# The argument for rendering `wide` at all is that a defect invisible at the
# design size shows at a shape nobody designed for. That argument covers these
# two exactly as well, and two of the five geometries being opt-in meant the
# rules named a check nothing ran. Two more renders per file is the cost; the
# alternative the rules already argue against is dropping them.
DEFAULT_GEOMETRIES = ["16x9", "16x9-hd", "a4", "laptop", "wide"]

# A CEILING on content pages carrying nothing visual, not a target for the
# rest (CLAUDE.md convention 4 — say which way a number points). One third,
# calibrated against two 30-page decks built from these same rules: the one
# a reader called good carries 0 such pages of 23, the one she called thin
# carries 10 of 22. Any line between them separates them, so this one is set
# where a document has to be mostly undrawn before it fails.
VISUAL_ABSENT_CEILING = 1 / 3

# Measured in the page, not from CSS. Everything here runs in the browser.
PROBE = r"""
() => {
  const CENTER = 'table, .fig, .band, .geo-flat';
  // Where the ink actually is. An <svg> box is not its drawing: with
  // preserveAspectRatio the art is centred inside whatever box it is given, so
  // a grown box reports a top that is up to 185px above the first mark. Every
  // "is it aligned" question has to be asked of the drawing, mapped out of user
  // space through the CTM — asking the element is how six pages reported 0px of
  // skew while the reader could see they were not level.
  // SVG elements carry an SVGAnimatedString, not a string, so className.split
  // gave "[object" as the name of everything the ground reported.
  const tagOf = (e) => {
    const c = (typeof e.className === 'string') ? e.className
            : (e.getAttribute && e.getAttribute('class')) || '';
    return c.split(' ')[0] || e.tagName.toLowerCase();
  };
  // The ground is not ink. It is continuous, uncountable and behind everything
  // by construction, so counting it as content made all thirty pages report
  // that they ran past their own footer rule.
  const isGround = (e) => !!(e.closest && e.closest('.ground'));
  // Every fallback path below returns the element box — which the comment above
  // identifies as the value that reported 0px of skew on six visibly crooked
  // pages. Returning it silently means the fix reverts to the bug for exactly
  // the elements the fix was written for, and prints the reverted number as
  // fact. `getBBox()` throws on an unrendered SVG and `getScreenCTM()` returns
  // null for one, and unrendered SVGs are a *shipped pattern* here — a page
  // carries a landscape and a portrait composition of the same figure and hides
  // one. So count the fallbacks and let the page report that its ink numbers
  // are element boxes.
  let inkFail = 0;
  const inkBox = (e) => {
    const r = e.getBoundingClientRect();
    if (e.tagName.toLowerCase() !== 'svg' || !e.viewBox || !e.viewBox.baseVal.width) return r;
    // A deliberately hidden drawing is not an unreadable one. A page ships a
    // landscape and a portrait composition of the same figure and hides one by
    // design; counting those as unmeasured reported 61 "failures" on a healthy
    // deck, which is the same false alarm this release exists to remove, only
    // pointed the other way. Only a drawing that HAS a box and still cannot
    // report where its ink is counts.
    const visible = r.width > 2 && r.height > 2;
    try {
      const bb = e.getBBox(), m = e.getScreenCTM();
      if (!m || !bb.height) { if (visible) inkFail++; return r; }
      // The mapping below is a scale-and-translate. A rotated or skewed CTM has
      // non-zero b/c and cannot be reduced to one top/left pair, so it would
      // return a confidently wrong box with no exception at all.
      if (Math.abs(m.b) > 1e-6 || Math.abs(m.c) > 1e-6) { if (visible) inkFail++; return r; }
      // CLAMPED TO THE ELEMENT'S OWN BOX. getBBox() is the union of the
      // children in user space and knows nothing about the viewport: an SVG
      // with a viewBox clips at its edges, so geometry outside the box is not
      // painted and must not be measured. The globe's plate carries a
      // drop-shadow, whose filter region inflates the bbox by a tenth of the
      // viewBox in every direction — about 50 CSS px at a figure's size — and
      // that phantom band collided with the paragraph above the figure and
      // spilled past the footer below it. Two GATING findings, on a document
      // where nothing was out of place. An intersection is the honest answer
      // and it costs a correct figure nothing, because its ink is inside its
      // box already.
      const box = {
        top: Math.max(r.top, bb.y * m.d + m.f),
        bottom: Math.min(r.bottom, (bb.y + bb.height) * m.d + m.f),
        left: Math.max(r.left, bb.x * m.a + m.e),
        right: Math.min(r.right, (bb.x + bb.width) * m.a + m.e),
      };
      if (box.bottom <= box.top || box.right <= box.left) return r;
      box.height = box.bottom - box.top;
      box.width = box.right - box.left;
      return box;
    } catch (err) { if (visible) inkFail++; return r; }
  };
  // Widen this and the numbers change: lists and spec strips were absent once,
  // so a full column of ordered steps reported as 10% ink. Any new block class
  // has to be added here too — a probe is only as good as its vocabulary, and
  // one that cannot see .say or .vow reports a column as empty and its
  // neighbour as misaligned.
  // `.field` is in this list because it is INK. The brand's signature device
  // was absent until 0.1.374, so a page built on one reported its column as
  // starting 339px late and its cell as nearly empty — measured on a real
  // deliverable where both columns began at the same pixel.
  const INK = 'table, svg, p, h1, h2, li, ol, ul, .listhead, .band, .key, .gd, .red,'
            + ' .note, .cap, .legend, .eyebrow, .spec, .spec div, .colophon, .wordmark,'
            + ' .card, .who, dl, dt, dd, .verdict, .say, .g, .swap, .vow, .vt, .vw,'
            + ' .ledname, .lead, .tag, .field';
  // The ink extent of a block: the union of its own drawing boxes, not the box
  // the browser gives the block. Centerpiece scale is the number this file's
  // own docstring calls the answer to "the chart is too small", and it was
  // computed from getBoundingClientRect() — so a `.fig` whose SVG box had grown
  // reported an inflated scale AND filled the empty-band scan with phantom ink,
  // under-reporting the blank around it at the same time. That is the 0.1.339
  // regression the docstring exists to prevent, arrived at from the other side.
  const inkExtent = (el) => {
    const parts = [];
    if (el.matches && el.matches(INK)) parts.push(inkBox(el));
    for (const e of el.querySelectorAll(INK)) { if (!isGround(e)) parts.push(inkBox(e)); }
    const live = parts.filter(r => r.height > 2 && r.width > 2);
    if (!live.length) return el.getBoundingClientRect();
    const top = Math.min(...live.map(r => r.top)), bottom = Math.max(...live.map(r => r.bottom));
    const left = Math.min(...live.map(r => r.left)), right = Math.max(...live.map(r => r.right));
    return {top, bottom, left, right, width: right - left, height: bottom - top};
  };
  // Leaf text, named once. Two probes need it — the collision scan and the
  // opener-inset scan — and the opener block sits earlier in source order, so
  // the constant is hoisted rather than copied. A vocabulary written in two
  // places is a vocabulary that drifts in one of them.
  // The absolute floor for two glyph runs overlapping, in CSS px. Both
  // dimensions must clear it. Calibrated on the accepted reference deck and
  // this package's own passing fixture, which must report zero.
  const GLYPH_OVERLAP_W = 20, GLYPH_OVERLAP_H = 6;
  const ROLE_WEIGHT_SELECTORS = __ROLE_WEIGHT_SELECTORS__;
  const TEXT_SEL = 'p,li,dt,dd,h1,h2,td,th,.k,.v,.g,.say,.gd,.key,.note,.listhead,'
             + '.eyebrow,.cap,.srcline,.conf,.site,.tick,.vt,.vw,.vn,.no,.yes,'
             + '.who,.verdict,.wordmark,.sub,.colophon,.openpart,.openclaim,'
             + '.openrun,.ledname';
  const out = [];
  for (const s of document.querySelectorAll('section.page')) {
    const sr = s.getBoundingClientRect();
    const inkFailAtStart = inkFail;
    // A page with no box cannot be measured, and every geometric check credits
    // it: overflow is -720 (not > 1), frame skew is 0, the horizon count is 1
    // because .foot is still in the DOM, and width/height is NaN — which no
    // `> threshold` test is ever true for. Three hidden pages reported as three
    // passing pages on every line of the report.
    if (sr.width < 4 || sr.height < 4) {
      out.push({id: s.id, unmeasurable: 'page has no box (display:none, zero-size or collapsed parent)'});
      continue;
    }
    // The page is a scaled stage, so a device pixel is no longer the unit of
    // the design: at a 1.389 zoom a 3px misalignment measures 4px and a
    // threshold silently tightens as the window grows. Every distance below is
    // divided back into page units, which is what the designer laid out in.
    const scale = s.offsetWidth ? (sr.width / s.offsetWidth) : 1;
    const inPageUnits = (v) => Math.round(v / (scale || 1));
    const footEl = s.querySelector('.foot');
    const foot = footEl ? footEl.getBoundingClientRect() : {top: sr.bottom};
    const bodyEl = s.querySelector('.body');
    const body = bodyEl ? bodyEl.getBoundingClientRect() : sr;
    const availW = body.width, availH = Math.max(1, foot.top - body.top);
    const area = availW * availH;

    // Centerpiece scale is measured against the cell the centerpiece lives in,
    // not the whole content area. Measuring against the page made every split
    // layout look half empty when its two columns were both full.
    let best = null;
    for (const c of s.querySelectorAll(CENTER)) {
      if (isGround(c)) continue;
      const r = inkExtent(c);
      if (r.width < 8 || r.height < 8) continue;
      if (!best || r.width * r.height > best.w * best.h) {
        const own = c.closest('.fill, .notes, .typeblock, .markcell, .body > div') || bodyEl;
        const o = own.getBoundingClientRect();
        best = {w: r.width, h: r.height, cellArea: Math.max(1, o.width * o.height),
                tag: c.tagName.toLowerCase(),
                cls: (c.className || '').toString().split(' ')[0]};
      }
    }
    // Per-cell fill, so an empty column in a split cannot hide behind a full one.
    const cells = [];
    for (const cell of s.querySelectorAll('.body > div, .body > header')) {
      const cr = cell.getBoundingClientRect();
      if (cr.height < 4) continue;
      let t = Infinity, b2 = -Infinity;
      for (const e of cell.querySelectorAll(INK)) {
        if (isGround(e)) continue;
        const r = inkBox(e);
        if (r.height < 2) continue;
        t = Math.min(t, r.top); b2 = Math.max(b2, r.bottom);
      }
      const used = (b2 > t) ? (b2 - t) : 0;
      cells.push({cls: (cell.className||'').toString().split(' ')[0] || 'cell',
                  fill: +(100 * used / cr.height).toFixed(0)});
    }
    // a figure's drawn aspect vs the cell it sits in
    let aspect = null;
    // Pick the *visible* drawing. A page can ship a landscape and a portrait
    // composition of the same figure, and reporting the hidden one's aspect
    // says the opposite of the truth.
    const svg = [...s.querySelectorAll('.fig svg[viewBox]:not(.ic):not(.ground)')]
      .find(e => e.getBoundingClientRect().height > 4) || null;
    if (svg) {
      const vb = svg.viewBox.baseVal;
      const cell = svg.closest('.fill, .body > div') || bodyEl;
      const cr = cell.getBoundingClientRect();
      if (vb.width && cr.height > 4) {
        const figA = vb.width / vb.height, cellA = cr.width / cr.height;
        const drawn = svg.getBoundingClientRect();
        aspect = {figure: +figA.toFixed(2), cell: +cellA.toFixed(2),
                  ratio: +(figA / cellA).toFixed(2),
                  fillsCellHeight: +(100 * Math.min(1, cellA / figA)).toFixed(0),
                  drawnH: Math.round(drawn.height), cellH: Math.round(cr.height)};
      }
    }
    // largest empty band: scan rows of the content area for ink
    const boxes = [...s.querySelectorAll(INK)].filter(e => !isGround(e))
      .map(e => inkBox(e))
      .filter(r => r.height > 2 && r.width > 2);
    const STEP = 8; let run = 0, maxRun = 0, runTop = 0, bestTop = 0;
    for (let y = body.top; y < foot.top; y += STEP) {
      const hit = boxes.some(r => r.top < y + STEP && r.bottom > y);
      if (hit) { run = 0; } else { if (!run) runTop = y; run += STEP;
        if (run > maxRun) { maxRun = run; bestTop = runTop; } }
    }
    // Page-height conformance. A deck is a set of fixed pages: one page must be
    // exactly one page. A section taller than the geometry prints across two
    // sheets and scrolls past the fold when projected, and it is invisible to
    // every fill or aspect number because those are all measured *within* it.
    // Two different overflows, and 0.1.343 needs both.
    //   · the section box against the viewport — the only one that existed, and
    //     the only one that meant anything while the page was `min-height:100svh`;
    //   · the *content* against the section box, which is the one that matters now
    //     the page is a fixed 720px stage. A fixed-height box does not grow when
    //     its content does; it just spills, and the first measure reports zero
    //     while the page is visibly broken. Locking the geometry moved the blind
    //     spot rather than removing it.
    const overflowPx = Math.round(sr.height - window.innerHeight);
    // Where the deepest ink on the page actually is, against the footer rule it
    // must stay above and against the page edge it must stay inside.
    //
    // The first version of this asked `s.scrollHeight - s.clientHeight`, and on
    // an `overflow: visible` box **scrollHeight does not count children that
    // spill out of it** — it reports the box, and the box does not know. Two
    // pages ran 26px and 8px past the footer rule while it returned exactly
    // zero. Same failure as the column probe before it: ask the ink.
    let deepest = -1e9, deepestWho = '';
    for (const e of s.querySelectorAll(INK)) {
      if (isGround(e)) continue;
      // The footer's own furniture lives below the rule by design — the
      // handling marker (0.1.375) is an svg the INK census matches, and
      // counting it reported every page as spilling past its own footer.
      if (e.closest('.foot')) continue;
      const r = inkBox(e);
      if (r.height < 2 || r.width < 2) continue;
      if (r.bottom > deepest) { deepest = r.bottom; deepestWho = tagOf(e); }
    }
    // With no .foot there is no footer rule, and falling back to the page edge
    // let the report say "all N pages stay above the footer rule" about pages
    // that have none — contradicting the waterline count two lines below it.
    const footRule = footEl ? footEl.getBoundingClientRect().top : sr.bottom;
    const spillPx = deepest > -1e9 ? inPageUnits(deepest - footRule) : 0;
    const pageSpillPx = deepest > -1e9 ? inPageUnits(deepest - sr.bottom) : 0;
    // Frame alignment. The page frame's parts must share one width and one
    // centre line, or the composition and the source line that sources it drift
    // apart. This is invisible at the design geometry — 0.1.341 shipped a
    // max-width on .body and none on .foot, which is exact at 1280 and opens a
    // dead band down the right of every page on a wider window. Hence --wide.
    let frameSkewPx = 0;
    if (footEl && bodyEl) {
      const f = footEl.getBoundingClientRect();
      frameSkewPx = inPageUnits(Math.max(Math.abs(f.left - body.left),
                                         Math.abs(f.right - body.right)));
    }

    // ── column alignment and weight ───────────────────────────────────────
    // Side-by-side cells must start on one line and carry comparable weight, or
    // the page reads as two unrelated documents. 0.1.342's provenance: layouts.css
    // said `.body.split > div { justify-content: flex-start }` at specificity
    // (0,2,1) while the fill rule above it reached (0,6,1) — each :not() counts
    // its argument — so every multi-column page centred its columns
    // independently and drifted by up to 333px. A rule that loses silently is
    // indistinguishable from no rule, which is why this is measured and not read.
    const layout = bodyEl ? ([...bodyEl.classList].filter(c => c !== 'body')[0] || '') : '';
    const multi = /split|columns|sidebar|quad/.test(layout);
    let colTopSkewPx = 0, colWeightRatio = 1, colCount = 0;
    if (multi && bodyEl) {
      const cells = [...bodyEl.children].filter(e => !e.classList.contains('lede')
                                               && !e.classList.contains('span'));
      colCount = cells.length;
      const boxes = [], tops = [], weights = [];
      for (const c of cells) {
        let t = Infinity, w = 0;
        for (const e of c.querySelectorAll(INK)) {
          if (isGround(e)) continue;
          const r = inkBox(e);
          if (r.height < 2 || r.width < 2) continue;
          t = Math.min(t, r.top); w += r.height * r.width;
        }
        if (t < Infinity) {
          const cr = c.getBoundingClientRect();
          boxes.push(cr); tops.push(t); weights.push(Math.max(1, w));
        }
      }
      // Only cells that actually sit side by side can be out of line. In
      // portrait every horizontal layout becomes a vertical one by design, and
      // comparing a stacked cell's top to the one above it reported a 792px
      // "misalignment" that is the composition working exactly as intended.
      for (let i = 0; i < boxes.length; i++) {
        for (let j = i + 1; j < boxes.length; j++) {
          const sideBySide = (boxes[i].right <= boxes[j].left + 1
                           || boxes[j].right <= boxes[i].left + 1)
                          && (boxes[i].top < boxes[j].bottom
                           && boxes[j].top < boxes[i].bottom);
          if (!sideBySide) continue;
          colTopSkewPx = Math.max(colTopSkewPx, inPageUnits(Math.abs(tops[i] - tops[j])));
          const r = Math.max(weights[i], weights[j]) / Math.min(weights[i], weights[j]);
          colWeightRatio = Math.max(colWeightRatio, +r.toFixed(1));
        }
      }
    }

    // ── focal element ─────────────────────────────────────────────────────
    // The largest type below the title, against body copy. A page whose biggest
    // thing is a paragraph has no entry point: the eye starts top-left and reads
    // it as a document. Measured after a reader called 28 pages flat and 24 of
    // them turned out to have nothing above 15px on them at all. Reported as a
    // ratio, never a floor — the answer for some pages is a dominant figure, and
    // a type threshold would push a number onto a page that does not want one.
    let focalPx = 0, focalText = '', bodyPx = parseFloat(getComputedStyle(document.body).fontSize) || 15;
    // The page title is excluded, or it masks every flat page beneath it. This
    // used to test `e.closest('h2.t')` inline, which made the verdict a function
    // of one class name: on a document that titles its pages any other way the
    // title became the focal element and the check *inverted* — the same flat
    // page reported "no focal element" with the class and "has a focal element"
    // without it. Resolve the title once, and say so when it cannot be found,
    // because then the focal number below is not the one this check means.
    //
    // Only the CONTENT title is excluded. A cover or closing whose title *is*
    // the composition should count it as its focal element — excluding those too
    // reported the cover and the closing of a healthy deck as pages with nothing
    // to enter on, which is the check answering a question nobody asked.
    const titleEl = s.querySelector('h2.t');
    const anyTitle = titleEl || s.querySelector('.cover h1, .closing h2, h1, h2');
    // A title is only *expected* where the frame reserves room for one. `.lede`
    // is the block that holds eyebrow, title and support, and it ships in
    // lumi-layouts.css — so this asks the layout, not a class vocabulary. A
    // cover, a part opener and a closing compose freely and carry no lede;
    // demanding a heading of them flagged two healthy openers whose composition
    // is their title.
    const titleExpected = !!(bodyEl && bodyEl.querySelector(':scope > .lede'));
    // The content title is excluded only where the frame RESERVES one. On a page
    // that composes freely — a cover, a closing, a part opener — the title is
    // the thing the eye lands on, and excluding it reported those pages as
    // having no entry point at all. `titleExpected` already asks the layout
    // rather than a class vocabulary, so reuse it rather than naming the three.
    for (const e of s.querySelectorAll('*')) {
      if ((titleExpected && titleEl && titleEl.contains(e)) || e.closest('.foot')) continue;
      // Own text, not descendants'. Testing e.children.length instead skipped
      // every display number that carried a unit in a <span> — which was all of
      // them — and reported four newly-composed pages as having no focal
      // element at all.
      const own = [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
      if (!own) continue;
      const r = e.getBoundingClientRect();
      if (r.height < 2) continue;
      // SVG type scales with the viewBox, so the declared size lies. Use the
      // rendered height of the line instead.
      const px = e.ownerSVGElement ? r.height : parseFloat(getComputedStyle(e).fontSize);
      if (px > focalPx) { focalPx = px; focalText = (e.textContent || '').trim().slice(0, 24); }
    }
    // A *drawing* that owns most of its cell is a focal element in its own
    // right. A table is not, however much of the cell it fills. Until 0.1.384
    // `.fill > table` was given `height:100%`, so every prose table on the deck
    // reported 100% of its cell and would have counted as a focal element here:
    // D7's exact failure — measuring the box instead of the thing in it — and it
    // reached this probe before the probe was a day old. Tables no longer
    // stretch, so the box lies less; the exclusion stays, because a full grid of
    // values is still not the thing an eye lands on before it starts reading.
    const centerIsDrawing = best && (best.tag === 'svg' || best.cls === 'fig');
    const figLead = (best && centerIsDrawing) ? (best.w * best.h / best.cellArea) : 0;

    // ── visual share (owner directive 2026-08-09) ─────────────────────────
    // How much of the content area the page's visual blocks occupy: figures,
    // stat bands, display leads and the comparison patterns. Tables and prose
    // are deliberately not counted — a table is for values. Reported against a
    // target of about half the page, never gated: the withdrawn 82% fill floor
    // is the standing lesson that a satisfiable number ends the looking.
    // null, not 0: a page with no body or a lede taller than its body has no
    // share to report, and printing it as "0%" under the target would report
    // an absence of measurement as a (bad) measurement.
    let visualPct = null;
    if (bodyEl) {
      // Held to check_design's VISUAL_BLOCKS by the `probe vocabulary`
      // guard: one metric with two carriers, one asking whether a page
      // has anything visual and this one asking how much of the page it
      // covers. `.launch` joined both at 0.1.547.
      const VIS = '.fig, .band, .lead, .swaps, .vows, .duo, .grades, .launch, .field, .stats';
      let visPx = 0;
      for (const e of s.querySelectorAll(VIS)) {
        if (e.parentElement && e.parentElement.closest(VIS)) continue;  // count outermost only
        const r = e.getBoundingClientRect();
        visPx += r.width * r.height;
      }
      // Against the area below the title block: the lede reserve is apparatus
      // shared by every page, and counting it in the denominator would report
      // a page whose whole working area is one drawing as barely half visual.
      const br = bodyEl.getBoundingClientRect();
      const lede = bodyEl.querySelector(':scope > .lede');
      const ledePx = lede ? lede.getBoundingClientRect().height * br.width : 0;
      const denom = br.width * br.height - ledePx;
      if (denom > 0)
        visualPct = Math.min(100, Math.round(100 * visPx / denom));
    }

    // ── does the drawing agree with its own numbers? ──────────────────────
    // A mark that encodes a quantity declares it (design-rules §4 rule 14). Where
    // it does, the drawing is checkable against it, and that is the only way a
    // checker can ever tell a bar chart from a picture of one: 48px means
    // nothing to a script until the markup says what it is 48px OF.
    //
    // Two findings, both decidable and neither a matter of taste:
    //   * two marks in one figure declaring DIFFERENT values and rendering at
    //     the SAME length — the shape a minimum-width floor makes, and it is
    //     how a deliverable drew 1 and 4 identically while its own caption
    //     said the smaller one was the point;
    //   * a length that is out of proportion to its value against the largest
    //     mark in the same figure.
    // The encoding dimension is whichever of width/height actually varies, so
    // horizontal and vertical bars need no flag.
    const distorted = [];
    for (const fig of s.querySelectorAll('svg')) {
      const marks = [...fig.querySelectorAll('[data-datum]')]
        .map(m => ({v: parseFloat(m.getAttribute('data-datum')),
                    r: m.getBoundingClientRect()}))
        .filter(m => Number.isFinite(m.v) && m.v > 0);
      if (marks.length < 2) continue;
      const spread = k => Math.max(...marks.map(m => m.r[k]))
                        - Math.min(...marks.map(m => m.r[k]));
      const dim = spread('width') >= spread('height') ? 'width' : 'height';
      const top = marks.reduce((a, b) => (b.v > a.v ? b : a));
      if (!(top.r[dim] > 0)) continue;
      for (const m of marks) {
        const expected = top.r[dim] * (m.v / top.v);
        // 2px OR 4% of the largest bar, whichever is larger: rounding and a
        // stroke are not distortion, and a tolerance tighter than the renderer
        // would fail honest drawings.
        const slack = Math.max(2, top.r[dim] * 0.04);
        if (Math.abs(m.r[dim] - expected) > slack)
          distorted.push({value: m.v, drew: Math.round(m.r[dim]),
                          shouldDraw: Math.round(expected)});
      }
    }

    // ── what the page says, beside what it shows (§4, 0.1.384) ────────────
    // A slide is narrated and a sheet is read alone, so a portrait content page
    // owes a second content block beside its centerpiece and one highlighted key
    // point. Both counted OUTSIDE the title reserve, because the support line is
    // a different budget and §3 caps it at three sentences — a rule that grew
    // the lede to satisfy this one would be the two rules fighting.
    // Outermost only, or a list inside a callout counts twice.
    let saidBlocks = null, keyPoints = null;
    if (bodyEl) {
      const SAID = 'p, ul, ol, dl, .listhead, .key, .red, .note, .ask, .card,'
                 + ' .swap, .vow, .gd, .grades';
      const lede = bodyEl.querySelector(':scope > .lede');
      saidBlocks = 0;
      for (const e of bodyEl.querySelectorAll(SAID)) {
        if (lede && lede.contains(e)) continue;
        if (e.closest('.cap, .legend, .geolegend, .spec, .colophon')) continue;
        if (e.parentElement && e.parentElement.closest(SAID)) continue;
        if (e.getBoundingClientRect().height < 4) continue;
        saidBlocks++;
      }
      // Any marked aside, tier-1 or standard. NOT tier-1 only: §4 budgets
      // `.key`/`.red` at one page in three, so a probe asking every page for one
      // would ask an author to break the rule three lines above the one it
      // enforces. The standard tier is `.gd`, and it is the one that scales.
      keyPoints = [...bodyEl.querySelectorAll('.gd, .key, .red')]
        .filter(e => !(lede && lede.contains(e))).length;
    }

    // ── caption budget ────────────────────────────────────────────────────
    // Under a figure belongs the number, the name and the source. Prose there is
    // body copy in a caption's clothes: it sits at caption size, far from the
    // sentence it explains, and on two pages it turned out to repeat the page's
    // own column verbatim. Duplication is the part worth measuring — a reader
    // sees it before they can say why.
    // WHAT THE DESCRIPTION IS. Rule 7b says what goes under a figure: the
    // number, the conclusion name, and the source line — and nothing else. So
    // the description is the caption's own text minus those parts, however the
    // author marked it up. This used to require a `.d` wrapper and skip any
    // caption without one. Nothing has ever emitted `.d`: not the scaffold, not
    // the passing fixture, not either shipped deliverable — 74 captions across
    // three documents, zero. tokens/ even carries a rendering for it, added
    // because this probe asserted the class, and the check went on measuring
    // nothing while reporting a caption count beside it.
    const pageText = (s.innerText || '').replace(/\s+/g, ' ');
    const caps = [];
    for (const cap of s.querySelectorAll('.cap')) {
      let txt = (cap.innerText || '').replace(/\s+/g, ' ').trim();
      for (const part of cap.querySelectorAll('.n, .srcline')) {
        const t = (part.innerText || '').replace(/\s+/g, ' ').trim();
        if (t) txt = txt.replace(t, ' ');
      }
      txt = txt.replace(/\s+/g, ' ').trim();
      if (!txt) continue;
      const sentences = txt.split(/(?<=[.?!])\s+/).filter(x => x.split(' ').length > 6);
      const rest = pageText.replace(txt, '');
      const dup = sentences.filter(x => rest.includes(x.slice(0, 45))).length;
      caps.push({words: txt.split(/\s+/).filter(Boolean).length,
                 sentences: sentences.length, duplicated: dup});
    }

    // ── what the page is built out of ─────────────────────────────────────
    // Digit density separates a table of values from prose poured into a grid.
    // A grid says "these cells are comparable on this axis"; prose in one says
    // only that the author had a list and reached for a table.
    // Caption attachment. The number and name belong under the figure; when the
    // svg box grows past its drawing they end up 95-205px below it, floating
    // near the footer, and a reader asks why the figure's name has been
    // separated from the figure.
    // Ink outside the viewBox is ink the reader never sees: a root <svg> clips
    // at its viewBox, so a label drawn past the right edge is simply gone, with
    // no overflow, no collision and no spill for any other probe to catch. This
    // is the defect CLAUDE.md rule 8 names as the reason a person has to look at
    // the render — and it is decidable, so it does not need one. Measured per
    // drawing in USER UNITS, and reported as a share of the viewBox so a 660-wide
    // and a 300-wide drawing are comparable.
    const clipped = [];
    const badBox = [];
    // INK LANDING ON INK, INSIDE THE DRAWING. `collision` measures page BLOCKS
    // — .fig against .band, a title against a footer — and never opens an svg,
    // so a chart whose arrow sits on a box and whose label sits under both is
    // a clean page to every gate this package has. Three agents shipped decks
    // that way on 2026-08-21: each iterated until all three checkers exited 0,
    // and none was told. The owner opened one and saw it in a second.
    //
    // FILLED ink only, and containment is not collision: a label plate BEHIND
    // its text, a bar inside its plot frame and a halo around a node are all
    // one shape inside another and all correct. What is left is two solid
    // marks that partly cover each other, which is the thing a reader sees as
    // broken. Held against the accepted reference deck before shipping.
    // THE TWO-LINE CEILING, which design-rules states as the headline's only
    // hard limit and which nothing has ever checked. `reserve` asks a different
    // question — does the title block fit the height it reserved — and a title
    // can run to five lines inside a generous reserve and pass it.
    //
    // WHERE IT BINDS is set by the accepted reference deck rather than by
    // reading the sentence alone: that document keeps every part opener and
    // every content headline at two lines or fewer, and exceeds only on its
    // cover and its closing page, which are separate templates with their own
    // claim at display scale. So those two are measured and reported, and the
    // ceiling gates everywhere else.
    let titleLines = null;
    {
      const t = s.querySelector('h1, h2, .t, .openclaim');
      if (t && (t.textContent || '').trim()) {
        // COUNTED ON THE RENDERED TEXT, via a Range, exactly as the caption
        // measurement above does — and for the same reason. Height divided by
        // line-height counts PADDING as text: it read a thirty-character
        // headline in the passing fixture as three lines, at two of four
        // viewports, and would have failed the document this package ships as
        // its own example. A Range yields one client rect per line box and
        // knows nothing about the box around them.
        const rng = document.createRange();
        rng.selectNodeContents(t);
        const tops = new Set();
        for (const r of rng.getClientRects()) {
          if (r.width < 1 || r.height < 1) continue;
          tops.add(Math.round(r.top));         // one entry per line box
        }
        rng.detach && rng.detach();
        const kind = /cover|clos/i.test((s.id || '') + ' ' + (s.className || ''))
                     ? 'bookend' : 'body';
        titleLines = {lines: Math.max(1, tops.size), kind,
                      text: (t.textContent || '').trim().slice(0, 40)};
      }
    }
    // A PART OPENER'S SUBJECT MARK. design-rules §3 permits exactly one — a
    // single silhouette carrying no text of its own, reversed out of the field,
    // restating the part's claim in another modality — and it is the only thing
    // permitted there besides the label, the claim and the run line. The
    // accepted reference deck carries one on every part opener (211x331,
    // 260x331, 193x331, all filled); three conformance decks driven to pass
    // every other gate carried none at all, on five openers between them. The
    // rule was in the prose and in nothing else.
    //
    // FILLED, never stroked: the same section says a hairline outline scaled to
    // display size is the accident and a filled silhouette is the graphic.
    let openerMark = 'not-an-opener';
    if (/open/i.test((s.id || '') + ' ' + (s.className || ''))
        && !/cover|clos/i.test((s.id || '') + ' ' + (s.className || ''))) {
      // MEASURED AS A SHARE OF THE PAGE, not in pixels. A deck is a fixed
      // canvas that SCALES to the window, so a silhouette 193px wide at 16x9
      // is 272px at laptop and 844px at wide — and a pixel floor tuned at one
      // of them mis-reads the others. The reference's smallest mark is 15% of
      // the page width and 46% of its height at every viewport; the floor is
      // half of that, so a mark has to be genuinely small to fail rather than
      // merely rendered at a smaller window. Found the hard way: a floor of
      // 120px failed the accepted reference at laptop and nowhere else, which
      // is the same one-viewport mistake this file has now made twice.
      const pageBox = s.getBoundingClientRect();
      let best = null;
      for (const e of s.querySelectorAll('svg, img')) {
        if (e.closest('.foot') || e.classList.contains('ic')
            || e.classList.contains('ground')) continue;
        const r = e.getBoundingClientRect();
        if (r.width < pageBox.width * 0.07 || r.height < pageBox.height * 0.23) continue;
        let filled = 0, stroked = 0;
        e.querySelectorAll('path,rect,circle,ellipse,polygon,polyline,line')
         .forEach(k => {
           const cs = getComputedStyle(k);
           const f = (cs.fill || '').trim(), st = (cs.stroke || '').trim();
           if (f && f !== 'none' && f !== 'transparent') filled++;
           if (st && st !== 'none' && st !== 'transparent'
               && parseFloat(cs.strokeWidth || 0) > 0) stroked++;
         });
        // A SIGNATURE FOR THE SILHOUETTE ITSELF, so two openers carrying one
        // mark can be told apart from two openers carrying two. The marks are
        // inlined SVG with no name to compare, so this is the geometry: the
        // path data, the `use` targets, and an image's own src. Truncated per
        // element because a silhouette runs to thousands of characters and the
        // first hundred already separate the vendored set's members.
        // EVERY SHAPE THE FILLED COUNTER ACCEPTS, and the WHOLE value. The
        // first version read five element kinds and truncated each attribute to
        // 100 characters, which broke both ways: a silhouette drawn from
        // `<circle>`/`<rect>` produced an empty signature and
        // `_openers_repeating_a_mark` skipped it, so three openers sharing one
        // circle-and-rect mark passed; and two genuinely different marks whose
        // paths diverge after character 115 collided and produced a FALSE red,
        // which is the class of defect that rewrites a correct document.
        // `xlink:href` is read too — `getAttribute('href')` returns null for
        // the namespaced form that older generators emit.
        const parts = [];
        e.querySelectorAll('path,polygon,polyline,circle,ellipse,rect,line,use,image')
         .forEach(k => {
           const geo = ['d', 'points', 'cx', 'cy', 'r', 'rx', 'ry',
                        'x', 'y', 'width', 'height', 'x1', 'y1', 'x2', 'y2']
             .map(a => k.getAttribute(a) || '').join(' ').trim();
           const ref = k.getAttribute('href')
                    || k.getAttributeNS('http://www.w3.org/1999/xlink', 'href') || '';
           parts.push(k.tagName.toLowerCase() + ':' + geo + ref);
         });
        if (e.tagName.toLowerCase() === 'img') parts.push('img:' + (e.src || ''));
        const cand = {w: Math.round(r.width), h: Math.round(r.height),
                      filled, stroked, img: e.tagName.toLowerCase() === 'img',
                      sig: parts.join('|')};
        if (!best || cand.w * cand.h > best.w * best.h) best = cand;
      }
      openerMark = best;   // null = an opener that carries none
    }

    // FIGURE STRUCTURE, coarsely. Which primitives a drawing is made of and in
    // what proportion — rounded hard, so two charts of the same KIND collide
    // and two different kinds do not. The accepted reference carries 21
    // drawings in 21 distinct structures and Cursor's passing deck 7 in 7;
    // one deck drew the same line-and-bar skeleton four times over.
    const figShapes = [];
    for (const sv of s.querySelectorAll('.fig svg:not(.ic)')) {
      const kinds = {};
      sv.querySelectorAll('rect,circle,ellipse,path,line,polygon,polyline,text')
        .forEach(e => { const t = e.tagName.toLowerCase();
                        kinds[t] = (kinds[t] || 0) + 1; });
      const total = Object.values(kinds).reduce((a, b) => a + b, 0);
      if (total < 4) continue;         // a mark, not a drawing
      figShapes.push(Object.keys(kinds).sort()
        .map(k => `${k}:${Math.round(100 * kinds[k] / total / 10) * 10}`).join(','));
    }

    // FIGURES THAT SCALE NUMBERS WITHOUT DRAWING THE SCALE. design-rules §4:
    // a baseline is the datum the marks are measured from, which is a different
    // thing from the gridlines rule 3 bans. REPORTED, never gated: the accepted
    // reference trips it (2 of its 9 scaled figures, measured 2026-08-22), so
    // one document cannot say whether it is a defect or the house style.
    let figNoAxis = 0, figScaled = 0;
    for (const sv of s.querySelectorAll('.fig svg:not(.ic)')) {
      let numeric = 0;
      sv.querySelectorAll('text').forEach(t => {
        // A VALUE, not a year and not a bare index: at least one digit, and
        // nothing but digits, separators and a short unit around it.
        const v = (t.textContent || '').trim();
        // A CURRENCY PREFIX AND A CJK UNIT ARE STILL VALUES. The first pattern
        // required the digits to come first and allowed only Latin units, so
        // `US$4.2m`, `41％` and `4.2亿` all read as "not a number" — which
        // silently exempted every Chinese-language figure from the check.
        if (v.length <= 14 && /\d/.test(v)
            && /^[^\d]{0,3}[\d][\d.,\s]*[^\d]{0,4}$/.test(v)) numeric++;
      });
      // TWO, not three. This package's own bar charts carry exactly two value
      // labels, so a bar of three made `figScaled` zero on all ten figures of
      // the passing fixture and the report printed NOTHING — no line, not even
      // "0 of 0". A check that cannot fire on the package's own artifact is not
      // a check (convention 15).
      if (numeric < 2) continue;        // not a figure that scales anything
      figScaled++;
      const box = sv.viewBox && sv.viewBox.baseVal;
      const W = (box && box.width) || 100, H = (box && box.height) || 100;
      let axis = false;
      sv.querySelectorAll('line,rect,path').forEach(e => {
        if (axis) return;
        const tag = e.tagName.toLowerCase();
        if (tag === 'line') {
          const x1 = +e.getAttribute('x1'), y1 = +e.getAttribute('y1');
          const x2 = +e.getAttribute('x2'), y2 = +e.getAttribute('y2');
          if (y1 === y2 && Math.abs(x2 - x1) > W * 0.4) axis = true;
          if (x1 === x2 && Math.abs(y2 - y1) > H * 0.4) axis = true;
        } else if (tag === 'rect') {
          const w = +e.getAttribute('width'), h = +e.getAttribute('height');
          if (h <= 2 && w > W * 0.4) axis = true;
          if (w <= 2 && h > H * 0.4) axis = true;
        } else {
          // A straight two-point run, which is how a baseline is usually
          // drawn once a figure is built from paths rather than primitives.
          const d = (e.getAttribute('d') || '').trim();
          const m = d.match(/^M\s*(-?[\d.]+)[ ,]+(-?[\d.]+)\s*[Ll]?\s*(-?[\d.]+)[ ,]+(-?[\d.]+)\s*$/);
          if (m) {
            const [x1, y1, x2, y2] = m.slice(1).map(Number);
            if (y1 === y2 && Math.abs(x2 - x1) > W * 0.4) axis = true;
            if (x1 === x2 && Math.abs(y2 - y1) > H * 0.4) axis = true;
          }
        }
      });
      if (!axis) figNoAxis++;
    }

    // The LIGHTEST rendering of each weight-bearing role on this page. Lightest
    // rather than first: one row of a ladder rendered at 400 is the defect, and
    // an average would hide it behind three correct siblings.
    const roleWeights = {};
    for (const sel of ROLE_WEIGHT_SELECTORS) {
      let worst = null;
      for (const e of s.querySelectorAll(sel)) {
        if (!(e.textContent || '').trim()) continue;
        const w = parseInt(getComputedStyle(e).fontWeight, 10);
        if (!isNaN(w) && (worst === null || w < worst)) worst = w;
      }
      if (worst !== null) roleWeights[sel] = worst;
    }

    // ── AXIS NAMES AGAINST THE PLOT THEY NAME ───────────────────────────
    // A name declared with `.axname-x` / `.axname-y` may not lie across the
    // region the marks occupy, and the vertical one reads bottom to top. Both
    // are decidable ONLY because the document says which text is an axis name:
    // a data label printed on its own mark is the same geometry and is
    // correct, so without the declared role a checker is guessing.
    const axisNames = [];
    for (const sv of s.querySelectorAll('.fig svg:not(.ic)')) {
      const names = [...sv.querySelectorAll('.axname-x, .axname-y')];
      if (!names.length) continue;
      // The plot is where the MARKS are — every drawn thing that is not one of
      // these names, and not text at all. `use` and `image` are in: a plot
      // square composed from a `<symbol>` is still the plot, and leaving them
      // out is why `figure_ink_collision` could not see one.
      let px0 = Infinity, py0 = Infinity, px1 = -Infinity, py1 = -Infinity;
      for (const m of sv.querySelectorAll(
             'rect,circle,ellipse,path,polygon,polyline,line,use,image')) {
        if (m.closest('defs,symbol,marker,clipPath,mask,pattern')) continue;
        const r = m.getBoundingClientRect();
        if (r.width < 2 && r.height < 2) continue;
        px0 = Math.min(px0, r.left); py0 = Math.min(py0, r.top);
        px1 = Math.max(px1, r.right); py1 = Math.max(py1, r.bottom);
      }
      if (!isFinite(px0)) continue;
      for (const n of names) {
        const r = n.getBoundingClientRect();
        const ox = Math.min(r.right, px1) - Math.max(r.left, px0);
        const oy = Math.min(r.bottom, py1) - Math.max(r.top, py0);
        const vertical = /vertical/.test(getComputedStyle(n).writingMode);
        const wantsVertical = n.classList.contains('axname-y');
        axisNames.push({
          text: (n.textContent || '').trim().slice(0, 40),
          over: (ox > GLYPH_OVERLAP_W && oy > GLYPH_OVERLAP_H)
                ? {w: inPageUnits(ox), h: inPageUnits(oy)} : null,
          misturned: vertical !== wantsVertical,
        });
      }
    }

    const figInk = [];
    for (const sv of s.querySelectorAll('.fig svg:not(.ic)')) {
      const marks = [];
      // NO TEXT. A label lying on the region it names is what a map IS, and
      // the reference deck carries dozens: `'path' over '3 · Australia, New
      // Zealand'` was this check's second false finding against a document the
      // owner has accepted. Paint order settles it — every label in all four
      // documents measured is drawn ON TOP of its shape, so text is never the
      // thing being covered. What is left is solid mark against solid mark.
      sv.querySelectorAll('rect,circle,ellipse,path,line,polygon,polyline').forEach(e => {
        if (e.closest('defs,symbol,marker,clipPath,mask,pattern')) return;
        const cs = getComputedStyle(e);
        if (cs.visibility === 'hidden' || cs.display === 'none') return;
        if (+cs.opacity < 0.15) return;                 // a wash is not ink
        const fill = (cs.fill || '').trim();
        if (!fill || fill === 'none' || fill === 'transparent') return;
        const r = e.getBoundingClientRect();
        if (r.width < 3 || r.height < 3) return;
        marks.push({tag: e.tagName.toLowerCase(), x: r.x, y: r.y,
                    w: r.width, h: r.height,
                    txt: (e.textContent || '').trim().slice(0, 24)});
      });
      for (let i = 0; i < marks.length; i++) {
        for (let j = i + 1; j < marks.length; j++) {
          const a = marks[i], b = marks[j];
          const holds = (p, q) => p.x >= q.x - 1 && p.y >= q.y - 1 &&
                                  p.x + p.w <= q.x + q.w + 1 &&
                                  p.y + p.h <= q.y + q.h + 1;
          if (holds(a, b) || holds(b, a)) continue;
          const ox = Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x);
          const oy = Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y);
          if (ox <= 3 || oy <= 3) continue;
          // AN ABSOLUTE FLOOR, set by measuring the accepted reference deck
          // rather than by choosing a number. Every drawing overlaps itself:
          // an arrowhead rests on its line, a rounded corner meets its edge, a
          // node sits on its halo. The reference carries **64 such pairs and
          // not one exceeds 7x6px** — they are draughtsmanship. The defect the
          // owner opened a deck and saw was 20x49px, a solid box with a solid
          // polygon lying across it: seven times the reference's largest.
          //
          // A share of the smaller mark was the first rule here and it was
          // wrong on its face: 5x5px of a 12px arrowhead is 81% of it, so the
          // reference failed three pages the first time this ran. What a
          // reader sees as broken is ABSOLUTE — ink the size of a word, not a
          // fraction of a glyph.
          if (ox < 12 || oy < 12) continue;
          figInk.push({w: Math.round(ox), h: Math.round(oy),
                       a: a.txt || a.tag, b: b.txt || b.tag});
        }
      }
    }
    for (const sv of s.querySelectorAll('.fig svg[viewBox]:not(.ic)')) {
      const vb = sv.viewBox.baseVal;
      // A viewBox that does not parse is not "nothing to check": the browser
      // discards it and lays the drawing out against a box nobody chose, which
      // is how a six-row figure rendered three rows and this probe skipped it.
      // Caught by writing `viewBox="7 560 416"` — three numbers, silently legal
      // as an attribute and meaningless as a value.
      if (!vb || !vb.width || !vb.height) {
        badBox.push((sv.getAttribute('viewBox') || '').slice(0, 24));
        continue;
      }
      let worst = 0;
      for (const e of sv.querySelectorAll('*')) {
        // A NESTED <svg> starts a new coordinate system, and getBBox() answers
        // in it. Comparing those numbers to the OUTER viewBox is comparing two
        // different rulers: an official trademark inlined at 39x13 inside a
        // 900-unit drawing reported as 988 units wide, because its own viewBox
        // is 1090 across. The rules permit exactly that markup (design-rules.md
        // §1's declared `data-mark` exception), so the probe fired on correct
        // work — which is worse than not firing at all.
        if (e.ownerSVGElement !== sv) continue;   // measured with its own svg
        // A DEFINITION does not render where it is written: <symbol>, <defs>,
        // <marker>, <clipPath>, <mask> and <pattern> are templates, and their
        // geometry is drawn only where something references them. An official
        // trademark vendored from its owner (the Reddit lockup) carries a
        // <symbol> whose bbox sits 162 units outside the wrapper's viewBox, and
        // this probe read that as a fifth of the drawing being clipped away on a
        // page where nothing was clipped at all.
        if (e.closest('defs,symbol,marker,clipPath,mask,pattern')) continue;
        if (e.tagName.toLowerCase() === 'svg') {
          // Compare what is RENDERED, which is the only frame the two share,
          // then convert back to the outer drawing's units.
          const a = e.getBoundingClientRect(), b = sv.getBoundingClientRect();
          if (!b.width || !b.height) continue;
          const sx = vb.width / b.width, sy = vb.height / b.height;
          worst = Math.max(worst,
            (a.right - b.right) * sx, (b.left - a.left) * sx,
            (a.bottom - b.bottom) * sy, (b.top - a.top) * sy);
          continue;
        }
        let bb; try { bb = e.getBBox(); } catch (err) { continue; }
        if (!bb.width && !bb.height) continue;
        worst = Math.max(worst,
          (bb.x + bb.width) - (vb.x + vb.width), vb.x - bb.x,
          (bb.y + bb.height) - (vb.y + vb.height), vb.y - bb.y);
      }
      // Half a unit of rounding is not a clipped label.
      if (worst > 0.5)
        clipped.push({over: +worst.toFixed(0),
                      pct: +(100 * worst / Math.max(vb.width, vb.height)).toFixed(1)});
    }

    // A STAT BAND RENDERING OUTSIDE ITSELF. `.body > *` carries `min-height: 0`
    // so a figure can give back space; a band cannot give any back, and its
    // grid row collapsing below the cells' height puts the labels outside the
    // box — usually on the footer beneath. `collision` sees that case only when
    // something is there to be hit, and a band collapsing over empty canvas is
    // the same defect with nothing to collide with. Measured against the BAND's
    // own box, so it is true wherever the band sits on the page.
    const bandEscape = [];
    for (const bd of s.querySelectorAll('.band')) {
      const box = bd.getBoundingClientRect();
      if (!box.height && !box.width) continue;
      let out = 0;
      for (const cell of bd.querySelectorAll('.k, .v')) {
        const r = cell.getBoundingClientRect();
        if (!r.height) continue;
        out = Math.max(out, r.bottom - box.bottom, box.top - r.top);
      }
      // A pixel of rounding is not an escaped label; 2px is a visible one.
      if (out > 1)
        bandEscape.push({out: +out.toFixed(0), boxPx: +box.height.toFixed(0),
                         needPx: bd.scrollHeight});
    }

    // Caption centring (§4 rule 7b, 0.1.384). The horizontal companion to the
    // gap above: the caption block centres on its figure, and the two come apart
    // when the drawing's ink is not centred inside its own viewBox — which no
    // stylesheet can fix, so this reports a REDRAW and not a CSS defect.
    //
    // Measured on the rendered TEXT, via a Range over the caption's contents,
    // never on `cap.getBoundingClientRect()`. The caption element is stretched to
    // the cell, so its box centre is the cell centre whether or not the rule
    // shipped — a thermometer reading its own water, which §7 forbids.
    let capGapPx = null, capOffPct = null;
    for (const fig of s.querySelectorAll('.fig')) {
      const sv = fig.querySelector('svg[viewBox]:not(.ic)');
      const cap = fig.querySelector('.cap');
      if (!sv || !cap || sv.getBoundingClientRect().height < 4) continue;
      const ink = inkBox(sv);
      const gap = inPageUnits(cap.getBoundingClientRect().top - ink.bottom);
      capGapPx = capGapPx === null ? gap : Math.max(capGapPx, gap);
      const rng = document.createRange();
      rng.selectNodeContents(cap);
      const rects = [...rng.getClientRects()].filter(r => r.width > 1 && r.height > 1);
      if (!rects.length || !(ink.right > ink.left)) continue;
      const l = Math.min(...rects.map(r => r.left)), r2 = Math.max(...rects.map(r => r.right));
      // As a SHARE of the drawing's width, not in pixels: the same 30px is
      // invisible under a full-width figure and obvious under a figure in a
      // two-column cell, so pixels are the wrong unit for this one.
      const off = 100 * Math.abs((l + r2) / 2 - (ink.left + ink.right) / 2)
                      / (ink.right - ink.left);
      capOffPct = capOffPct === null ? +off.toFixed(1) : Math.max(capOffPct, +off.toFixed(1));
    }

    // One source per page. §4 rule 4 asks every figure for a source line and the
    // footer contract asks every page for one; nobody checked the single-figure
    // page, where they say the same thing twice and sometimes word for word.
    const cite = (t) => new Set((t.match(/§\s?[\d.]+[a-z]?|Appendix\s+\w|findings summary/gi) || [])
                                 .map(x => x.replace(/\s+/g, '').toLowerCase()));
    // The document's colophon, not a per-page footer slot. `.foot .src` was
    // removed in 0.1.366: it had no rule, and a deliverable filled it with a
    // build path on every page. Provenance is stated once for the document, so
    // that is what a figure's source line can echo.
    const figSrc = s.querySelector('.cap .srcline');
    const footSrc = document.querySelector('.colophon');
    // Distinguish "compared, and they differ" from "never comparable". The
    // audit read `if (figSrc && footSrc)` and reported success on every
    // document where either was absent, which was every document, because
    // `.src` shipped nowhere.
    let sourceEcho = 0, sourceComparable = !!(figSrc && footSrc);
    if (figSrc && footSrc) {
      const a = cite(figSrc.textContent || ''), b = cite(footSrc.textContent || '');
      sourceEcho = [...a].filter(x => b.has(x)).length;
    }

    // ── the two brand devices, checked for honesty (references/brand.md) ──
    // A field with nothing behind it is decoration, and decoration is the page
    // competing for attention it has not earned. Every mark must map to one
    // real item: the container declares data-count, each mark declares its own
    // data-datum, and the two have to agree. This is the one new brake 0.1.345
    // adds, and it is what keeps the shimmer from becoming texture.
    const fields = [];
    for (const f of s.querySelectorAll('.field')) {
      const marks = f.querySelectorAll(':scope > i');
      const declared = parseInt(f.getAttribute('data-count') || '0', 10);
      const bound = [...marks].filter(m => m.getAttribute('data-datum')).length;
      fields.push({marks: marks.length, declared, bound});
    }
    // One horizon per page. Two and the page has stripes instead of a datum;
    // none and it is a document again.
    const horizons = s.querySelectorAll('.foot').length;

    // Text sitting on text. Every other probe here measures a block against the
    // page — its top, its bottom, its column, the footer rule — and none of them
    // can see two blocks landing on each other in the middle of a page. A reader
    // found this before any check did, twice, when 0.1.346's heavier register grew
    // past grid rows that had been sized for the old one. Leaf text only: a
    // container legitimately encloses its children.
    const TSEL = TEXT_SEL;
    // ...and text against anything DRAWN. 0.1.347 shipped this comparing text to
    // text only, and a reader then found two defects it could not see: a field
    // sitting 22px on a paragraph, and the cover globe crossing the document
    // attributes. Eleven pairs, all of them text against a drawing. A probe
    // that only knows one kind of collision finds one kind of collision.
    const DSEL = '.field,.fig,.band,.spec,.geo-flat,svg[viewBox]:not(.ic):not(.ground)';
    const leaves = [...s.querySelectorAll(TSEL)].filter(e => !e.closest('.ground')
      && (e.textContent || '').trim()
      && ![...e.children].some(c => c.matches && c.matches(TSEL)));
    const drawnEls = [...s.querySelectorAll(DSEL)].filter(e => !e.closest('.ground'));
    let textOverlaps = 0, worstOverlap = null;
    const clash = (A, B, na, nb) => {
      // Ink, not boxes. A grown SVG box overlaps its neighbour while the drawing
      // inside it does not, and reporting that is how a probe teaches an author
      // to ignore it.
      const a = inkBox(A), b = inkBox(B);
      if (a.height < 2 || b.height < 2) return;
      const ox = Math.min(a.right, b.right) - Math.max(a.left, b.left);
      const oy = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
      if (ox <= 2 || oy <= 2) return;
      textOverlaps++;
      const area = ox * oy;
      if (!worstOverlap || area > worstOverlap.area) {
        worstOverlap = {area, w: inPageUnits(ox), h: inPageUnits(oy), a: na, b: nb};
      }
    };
    // ── TEXT INSIDE A DRAWING IS TEXT ────────────────────────────────────
    // `TEXT_SEL` above names HTML roles only, so an `<svg>` entered this scan
    // as ONE opaque box and two labels inside one drawing were, to this probe,
    // the same object overlapping itself. The rule it implements has always
    // said "nothing may land on anything"; the probe just never enumerated
    // SVG text as text. Six real overlaps sat in one conformance deck — an
    // axis unit printed over the word "Illustrative", a risk label over its
    // own category name — and `collision` reported `ok` on all of them.
    //
    // A SEPARATE FLOOR, because a glyph run is not a paragraph. Kerning and
    // anti-aliasing put a few pixels of two labels together routinely: the
    // noise measured 32x4 and 15x16, the real defects 21x13 and up. Neither
    // dimension separates them alone, so both must clear.
    const svgText = [...s.querySelectorAll('svg text')].filter(t =>
      (t.textContent || '').trim()
      && !t.closest('.ground')
      // THE GLOBE IS EXEMPT. Its signal labels are HS codes printed along
      // trade arcs and they overlap by construction at 5+ places on the cover
      // and closing of every deck built with it, the accepted reference
      // included. Gating them would fail page 1 of the document this package
      // calibrates on. Recorded as a gap rather than treated as clean.
      && !t.closest('svg.gl')
      && !t.closest('defs,symbol,marker,clipPath,mask,pattern'));
    for (let i = 0; i < svgText.length; i++) {
      for (let j = i + 1; j < svgText.length; j++) {
        const a = svgText[i].getBoundingClientRect();
        const b = svgText[j].getBoundingClientRect();
        const ox = Math.min(a.right, b.right) - Math.max(a.left, b.left);
        const oy = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
        if (ox < GLYPH_OVERLAP_W || oy < GLYPH_OVERLAP_H) continue;
        textOverlaps++;
        const area = ox * oy;
        if (!worstOverlap || area > worstOverlap.area) {
          worstOverlap = {area, w: inPageUnits(ox), h: inPageUnits(oy),
                          a: (svgText[i].textContent || '').trim().slice(0, 40),
                          b: (svgText[j].textContent || '').trim().slice(0, 40)};
        }
      }
    }

    // ── A STROKE THROUGH A GLYPH RUN ────────────────────────────────────
    // The other half of "text against every drawn element", inside a drawing.
    // Only STROKED marks, and that restriction is the whole discriminator: a
    // data label sitting ON its own filled mark is what a labelled chart looks
    // like, and `figure_ink_collision` excludes text for exactly that reason.
    // A line drawn THROUGH a word is never a labelling relationship. Found on a
    // conformance deck where three arrow rules crossed the sentences beneath
    // them.
    const strokes = [...svgText.length ? s.querySelectorAll(
      '.fig svg line, .fig svg path, .fig svg polyline') : []].filter(m => {
        if (m.closest('defs,symbol,marker,clipPath,mask,pattern')) return false;
        if (m.closest('svg.gl')) return false;
        const cs = getComputedStyle(m);
        const f = (cs.fill || '').trim();
        // Stroked and NOT filled: a filled path is a shape, and a label on a
        // shape is the case above.
        return (cs.stroke || 'none') !== 'none'
               && parseFloat(cs.strokeWidth || 0) > 0
               && (f === 'none' || f === 'transparent' || !f);
      });
    for (const t of svgText) {
      const a = t.getBoundingClientRect();
      for (const m of strokes) {
        const b = m.getBoundingClientRect();
        // A long thin box is the stroke's own extent, so require the overlap to
        // be a real bite out of the TEXT rather than a graze along its edge.
        const ox = Math.min(a.right, b.right) - Math.max(a.left, b.left);
        const oy = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
        if (ox < GLYPH_OVERLAP_W || oy < GLYPH_OVERLAP_H) continue;
        if (oy > a.height * 0.9) continue;   // the stroke spans the whole line:
                                             // a rule under a caption, not through it
        textOverlaps++;
        const area = ox * oy;
        if (!worstOverlap || area > worstOverlap.area) {
          worstOverlap = {area, w: inPageUnits(ox), h: inPageUnits(oy),
                          a: (t.textContent || '').trim().slice(0, 40),
                          b: 'a stroke drawn through it'};
        }
      }
    }

    for (let i = 0; i < leaves.length; i++) {
      for (let j = i + 1; j < leaves.length; j++) {
        clash(leaves[i], leaves[j], tagOf(leaves[i]), tagOf(leaves[j]));
      }
      for (const d of drawnEls) {
        // Containment is not collision: a caption inside its own figure, a
        // label inside its own band.
        if (d.contains(leaves[i]) || leaves[i].contains(d)) continue;
        clash(leaves[i], d, tagOf(leaves[i]), tagOf(d) || 'drawing');
      }
    }

    // ── the part opener against the page frame ────────────────────────────
    //
    // A reported deliverable set its opener claim hard against the page edge
    // while the footer stayed inset by the page padding, so the two read as
    // different left margins on the same page. `frameSkewPx` above compares
    // `.foot` to `.body` and cannot see it: an opener composes freely and its
    // copy need not live in a `.body` at all.
    //
    // Measured without a vocabulary. The reporting note proposed keying on
    // `.openframe`, which ships in no token file — keying a probe on an
    // unshipped name is the reverse drift `check_probe_vocabulary` exists to
    // stop, and it would report nothing on a document that names the block
    // anything else. So: TEXT ink on an opener may not sit outside the
    // footer's own left and right edges. `.bleed` is excluded because running
    // past the content margin is exactly what that shipped class is for.
    //
    // REPORTED, never gated. One deliverable is one case, and 0.1.372 declined
    // to reshape a probe on the strength of one.
    let openerOutsidePx = 0, openerSide = '';
    if (s.classList.contains('opener') && footEl) {
      const f = footEl.getBoundingClientRect();
      for (const e of s.querySelectorAll(TEXT_SEL)) {
        if (e.closest('.ground') || e.closest('.bleed')) continue;
        if (!(e.textContent || '').trim()) continue;
        if ([...e.children].some(c => c.matches && c.matches(TEXT_SEL))) continue;
        const r = e.getBoundingClientRect();
        if (r.height < 2 || r.width < 2) continue;
        const left = inPageUnits(f.left - r.left);
        const right = inPageUnits(r.right - f.right);
        if (left > openerOutsidePx) { openerOutsidePx = left; openerSide = 'left'; }
        if (right > openerOutsidePx) { openerOutsidePx = right; openerSide = 'right'; }
      }
    }

    // ── the title reserve, and what an author does when it is overspent ───
    //
    // `.body .lede` RESERVES its height, and lumi-layouts.css states the rule in
    // the direction that matters: a title needing three lines does not get a
    // taller reserve, it gets shorter text. A real deliverable broke it — four
    // title lines in a two-line reserve — and then answered the overflow with
    // `-webkit-line-clamp: 2; overflow: hidden`. Three of four title lines and
    // the tail of a support sentence stopped rendering, on a client page.
    //
    // Every probe above was blind to it by construction. Clamped text produces
    // no spill (the ink is clipped), no collision (nothing lands on anything)
    // and no page overflow (the reserve is a fixed box). So measure the two
    // things that are actually decidable, and neither is a vocabulary:
    //
    //   · the reserve is OVERSPENT — what the children need exceeds what the
    //     block reserves. Note what this deliberately is NOT: comparing
    //     scrollHeight to clientHeight element by element. Measured on
    //     fixtures/deck-pass.en.html, `h2.t` is a 35px box holding 42px of ink,
    //     because --fs-title resolves to 34.56px against a line-height of 1.02.
    //     That is the tight leading this design uses on purpose, and a check
    //     built on it fires on every correctly-set title in the system.
    //   · content is being HIDDEN. A clamp or a hidden overflow anywhere in a
    //     lede is never legitimate; the answer is always shorter text.
    //
    // Landscape only, and asked the way the stylesheet asks it: `.body .lede`
    // is `height: auto` under `@media (max-aspect-ratio: 1/1)`, because a title
    // that sets on two lines at 1280 sets on three at 794 and reserving the
    // landscape height would spend space the sheet does not have. Portrait is a
    // composition, not a reflow — there is no reserve there to overspend, and
    // measuring anyway reported all ten of the fixture's ledes 5px over their
    // own auto height, which is the rounding of `scrollHeight` and nothing else.
    // The clamp half still runs in both: hidden text is hidden in any geometry.
    // Released by the document's declared geometry, never by the window's
    // shape. A portrait handbook opened in a wide window is still portrait —
    // reading the window here reported a released reserve as an overspent one
    // the moment the reader resized, which is the window deciding the design.
    const reserveExpected = document.body.dataset.geometry
      ? document.body.dataset.geometry !== 'portrait'
      : window.innerWidth >= window.innerHeight;
    // Seeded null, not 0. Written as `let over = 0` the tightest-block numbers
    // were only ever recorded for a block that overspends, so a healthy page
    // reported "tightest p2 at 0px of 0px" — a reassuring line about nothing,
    // which is the exact failure mode this file's docstring exists to name.
    let ledeWorst = null, ledeBlocks = 0;
    const ledeClamped = [];
    for (const lede of s.querySelectorAll('.lede')) {
      const lr = lede.getBoundingClientRect();
      if (lr.height < 4) continue;
      ledeBlocks++;
      const ls = getComputedStyle(lede);
      // The reserve is a CONTENT box: padding is not space the title can use.
      const reserve = lede.clientHeight
        - parseFloat(ls.paddingTop || 0) - parseFloat(ls.paddingBottom || 0);
      const kids = [...lede.children];
      let need = 0;
      for (const kid of kids) {
        const ks = getComputedStyle(kid);
        if (ks.display === 'none') continue;
        // ONE SPACE, and this is the whole subtlety of the measurement. The page
        // is a `zoom`ed stage: `getBoundingClientRect()` comes back multiplied by
        // the zoom, while `scrollHeight`, `clientHeight` and every computed
        // margin come back in CSS pixels. Written as
        // `max(scrollHeight, rect.height)` the box term was scaled and the margin
        // term was not, so at the 1800x1000 window every healthy lede in the
        // fixture reported 1.1px over a reserve it actually cleared by 45. Divide
        // the rect back before comparing anything to anything.
        //
        // The larger of the box and its content: a flex item in a column that has
        // run out of room is SHRUNK by default, so its box is smaller than the
        // text inside it — which is the state being looked for, and the box alone
        // would report it as fitting.
        need += Math.max(kid.scrollHeight, kid.clientHeight,
                         kid.getBoundingClientRect().height / (scale || 1))
              + parseFloat(ks.marginTop || 0) + parseFloat(ks.marginBottom || 0);
      }
      const gap = parseFloat(ls.rowGap === 'normal' ? 0 : ls.rowGap) || 0;
      need += gap * Math.max(0, kids.length - 1);
      const over = Math.round(need - reserve);
      if (reserveExpected && (!ledeWorst || over > ledeWorst.over)) {
        ledeWorst = {over, reserve: Math.round(reserve), need: Math.round(need)};
      }
      for (const e of [lede, ...lede.querySelectorAll('*')]) {
        // Only a box that HOLDS TEXT can hide text. `<svg>` carries
        // `overflow: hidden` from the UA stylesheet, so the first version of
        // this flagged the eyebrow icon on 26 of 30 pages of a real deliverable
        // — a 26-page false alarm on a finding that gates, which is how a gate
        // teaches people to route around it. A clamp is suspicious on any
        // text-bearing element; a hidden overflow is ordinary on everything
        // else, and an icon is not text however close to the title it sits.
        if (e.ownerSVGElement || e.tagName.toLowerCase() === 'svg') continue;
        // Text ANYWHERE beneath it, not its own text nodes. The clamp that cost
        // a real deliverable three title lines sat on the `.lede` container,
        // whose own child nodes are elements — asking for own text let the
        // exact case this check was written for through.
        if (!(e.textContent || '').trim()) continue;
        const c = getComputedStyle(e);
        const clamp = c.webkitLineClamp || c.getPropertyValue('-webkit-line-clamp');
        const why = (clamp && clamp !== 'none') ? `line-clamp: ${clamp}`
                  : /hidden|clip/.test(c.overflowY) ? `overflow-y: ${c.overflowY}`
                  : /hidden|clip/.test(c.overflowX) ? `overflow-x: ${c.overflowX}`
                  : '';
        if (why) ledeClamped.push({who: tagOf(e), why});
      }
    }

    // A ground may be decorative only because it cannot be counted. The moment
    // it is built from repeated identical marks it is pretending to be a field,
    // and a reader will try to read meaning into it. Continuous paths of
    // differing length are a ground; a run of same-sized rects is not.
    let groundMarks = 0, groundRepeats = 0;
    for (const g of s.querySelectorAll('.ground')) {
      const shapes = g.querySelectorAll('rect, circle, ellipse, line, use');
      groundMarks += shapes.length;
      const sig = {};
      for (const sh of shapes) {
        const r = sh.getBoundingClientRect();
        const k = Math.round(r.width) + 'x' + Math.round(r.height);
        sig[k] = (sig[k] || 0) + 1;
      }
      groundRepeats += Object.values(sig).filter(n => n >= 4).length;
    }

    const tables = [];
    for (const t of s.querySelectorAll('table')) {
      const txt = (t.innerText || '');
      const digits = (txt.match(/\d/g) || []).length;
      tables.push({rows: t.querySelectorAll('tr').length,
                   digitPct: +(100 * digits / Math.max(1, txt.length)).toFixed(0)});
    }
    const drawn = [...s.querySelectorAll('svg[viewBox]:not(.ic):not(.ground)')]
      .some(e => e.getBoundingClientRect().height > 60);
    out.push({
      id: s.id,
      pageH: Math.round(sr.height),
      overflowPx,
      // How many SVGs on this page could not report their drawing box. Any
      // page with a non-zero count has spill, column-skew and caption-gap
      // numbers measured against element boxes, which is the pre-fix behaviour.
      inkUnavailable: inkFail - inkFailAtStart,
      hasFooter: !!footEl,
      // A STARVED COLUMN: a block carrying words, rendered too narrow to hold
      // them. This is the shape of a defect no markup reader can see — the
      // `.swap` grid is `1fr 34px 1fr` and takes three children, so a block
      // written with two put its second half in the 34px arrow track. Every
      // gate passed; the text wrapped one word per line and its content was
      // trimmed three times before anyone measured the box.
      //
      // The test is not "narrow" — a chip or a number legitimately is. It is
      // narrow WHILE HOLDING A SENTENCE: more than a few words in less than
      // 60px, which is under four characters a line at body size.
      starved: (() => {
        const bad = [];
        for (const e of s.querySelectorAll(TEXT_SEL)) {
          const r = e.getBoundingClientRect();
          const words = (e.textContent || '').trim().split(/\s+/).length;
          if (r.width > 1 && r.width < 60 && words >= 4 && r.height > r.width) {
            bad.push((e.className || e.tagName) + ' ' + Math.round(r.width) +
                     'x' + Math.round(r.height) + 'px, ' + words + ' words');
          }
        }
        return bad;
      })(),
      // The footer is one line by contract: three spans on a row. A second
      // line is furniture overflowing its own frame, and it shipped on all 31
      // pages of a real deliverable because the document's `.page` padding
      // overrode the sheet's margin. Measured on the SPANS, not the row, since
      // the row carries the waterline's padding.
      //
      // COUNT THE LINE BOXES, do not infer them from a height. This compared
      // getBoundingClientRect().height against `parseFloat(lineHeight) || 14`,
      // and both halves were wrong at once: the stage is SCALED to the
      // viewport, so the rect is in device space while lineHeight is in CSS
      // px, and `line-height: normal` does not parse, so every comparison fell
      // back to a hard-coded 14. At 1920x1080 the page scales 1.5x and a
      // perfectly good one-line footer measured 22.5 against a threshold of
      // 22.4 — all 18 pages reported wrapped, by a tenth of a pixel, on the
      // matrix point design-rules.md §8 names and nothing had ever run.
      // A Range over the contents yields one client rect per line box, in
      // whatever space the element is drawn in, so the ratio is scale-free.
      footWrapped: !!footEl && [...footEl.children].some(e => {
        // TEXT NODES, not the element. A Range over element contents returns
        // the element's own border box as one rect, so a two-line footer
        // counted as one line and the planted case did not fire.
        const walker = document.createTreeWalker(e, NodeFilter.SHOW_TEXT);
        const range = document.createRange();
        const rects = [];
        let n;
        while ((n = walker.nextNode())) {
          if (!n.nodeValue.trim()) continue;
          range.selectNodeContents(n);
          for (const r of range.getClientRects()) {
            if (r.width > 0.5 && r.height > 0.5) rects.push(r);
          }
        }
        if (!rects.length) return false;
        // An inline icon sits on the same line as its text at a different top,
        // so tops within most of a line box count as the same line.
        const tall = Math.max(...rects.map(r => r.height));
        const tops = [];
        for (const r of rects) {
          if (!tops.some(t => Math.abs(t - r.top) < tall * 0.6)) tops.push(r.top);
        }
        return tops.length > 1;
      }),
      // Same rects, different axis: the footer's runs share one BASELINE by
      // contract — one row, one face, one size. `.conf`'s synthesized baseline
      // came from its 12px shield icon (a replaced element, baseline = bottom
      // edge) until the 0.1.442 owner review, so the handling terms rode 2px
      // above the site and the page number on every page of a shipped 34-page
      // deliverable, and nothing here had ever measured the axis. Bottom edges
      // of the TEXT-NODE rects stand in for baselines (constant descent at one
      // face and size), and the spread is a ratio of the tallest rect so the
      // zoomed stage can neither manufacture nor hide it.
      //
      // THE NULLS ARE NOT ALL THE SAME, and reading them as one another was
      // how this probe went blind exactly where the defect is worst. `line1`
      // keeps the runs within 0.6 of a line box of the topmost rect, so a run
      // displaced by MORE than that becomes the topmost rect and stands alone
      // — the probe returned null, every consumer read `null or 0`, and the
      // report printed "one line, one baseline" for a footer 12px out of true.
      // A check that fires at 3px and goes silent at 12px is worse than none.
      // So the shape carries what happened: `runs` (how many text runs the
      // footer has at all) and `split` (there are runs, and no two of them
      // share the first line — which is not an absence of evidence, it is the
      // finding, one size up).
      footBaseline: (() => {
        const out = {ratio: null, runs: 0, split: false};
        if (!footEl) return out;
        const walker = document.createTreeWalker(footEl, NodeFilter.SHOW_TEXT);
        const range = document.createRange();
        const rects = [];
        let n;
        while ((n = walker.nextNode())) {
          if (!n.nodeValue.trim()) continue;
          range.selectNodeContents(n);
          for (const r of range.getClientRects()) {
            if (r.width > 0.5 && r.height > 0.5) rects.push(r);
          }
        }
        out.runs = rects.length;
        // One run is a footer with nothing to compare — a page number alone.
        // Nothing to grade, and saying so is not the same as saying "clean".
        if (rects.length < 2) return out;
        const tall = Math.max(...rects.map(r => r.height));
        const top = Math.min(...rects.map(r => r.top));
        // First line only: a wrapped footer is footWrapped's finding, and
        // grading its second line here would report one defect twice.
        const line1 = rects.filter(r => r.top - top < tall * 0.6);
        if (line1.length < 2) { out.split = true; return out; }
        const bottoms = line1.map(r => r.bottom);
        out.ratio = (Math.max(...bottoms) - Math.min(...bottoms)) / tall;
        return out;
      })(),
      // A figure's number and name are one line too: wrapped, the caption stops
      // reading as a label and starts reading as prose under the drawing.
      // Measured on the NAME — the text between the number span and the source
      // line — with a Range, because the first version measured `.cap .n`,
      // which is the two-word "Figure 5" span and cannot wrap: the check
      // printed "all figure names hold one line" on every document ever run,
      // including one whose reviewer called long captions this author's
      // chronic defect. An instrument that measures the label of the thing
      // instead of the thing has never measured anything.
      capWrapped: [...s.querySelectorAll('.cap')].filter(cap => {
        const n = cap.querySelector('.n'), src = cap.querySelector('.srcline');
        const r = document.createRange();
        if (n) r.setStartAfter(n); else r.setStart(cap, 0);
        if (src) r.setEndBefore(src); else r.setEnd(cap, cap.childNodes.length);
        const rects = [...r.getClientRects()].filter(b => b.width > 1 && b.height > 1);
        if (!rects.length) return false;
        const tops = rects.map(b => Math.round(b.top / 4));
        return new Set(tops).size > 1;
      }).length,
      capCount: s.querySelectorAll('.cap').length,
      titleMissing: titleExpected && !anyTitle,
      hasGround: s.querySelectorAll('.ground').length,
      // The part opener. `.page.opener` is styled in lumi-layouts.css and named
      // in brand.md, and nothing has ever required, reported or checked it — so
      // a deck with none of them looked the same in every report as a deck with
      // six. Reported as a count and NEVER floored: how many part divisions a
      // document wants is a structural decision belonging to its storyline, and
      // a minimum here would grow openers to satisfy the number.
      isOpener: s.classList.contains('opener'),
      // Declared apparatus: a reference page (glossary, scoring table,
      // boundaries list, how-to) is exempt from the visual-share target,
      // because asking reference material to carry a figure produces
      // decoration. Declared, never inferred, and counted below.
      isApparatus: s.dataset.role === 'apparatus',
      isCover: s.classList.contains('cover'),
      isClosing: s.classList.contains('closing'),
      // The agenda, found the way check_design's D27 finds it — the id the
      // scaffold emits, or an eyebrow naming it. Two checks that located the
      // agenda differently could disagree about whether a deck has one, and
      // D27 is already the authority on that page.
      // A deck that is deliberately ONE undivided sequence says so, the way an
      // apparatus page declares itself. Read per row because the rows are all
      // the Python side gets; it is the same value on every one.
      partsDeclaredNone: (document.body.dataset.parts || '') === 'none',
      isAgenda: (s.id || '').toLowerCase() === 'agenda'
        || /agenda/i.test(((s.querySelector('.eyebrow') || {}).textContent) || ''),
      capBlocks: s.querySelectorAll('.cap').length,
      spillPx, pageSpillPx, deepestWho,
      frameSkewPx,
      sideMarginSkewPx: Math.round(Math.abs((body.left - sr.left) - (sr.right - body.right))),
      layout, colCount, colTopSkewPx, colWeightRatio, visualPct, distorted, saidBlocks, keyPoints,
      focalPx: Math.round(focalPx), focalText, bodyPx: Math.round(bodyPx),
      focalRatio: +(focalPx / Math.max(1, bodyPx)).toFixed(2),
      figLeadPct: +(100 * figLead).toFixed(0),
      caps, tables, drawn, capGapPx, capOffPct, clipped, badBox, sourceEcho, sourceComparable, fields, horizons,
      bandEscape, hasBand: s.querySelectorAll('.band').length > 0,
      figInk, titleLines, openerMark, figShapes, figNoAxis, figScaled, roleWeights,
      axisNames,
      textOverlaps, worstOverlap,
      ledeBlocks, ledeClamped, reserveExpected,
      openerOutsidePx, openerSide,
      ledeOverspendPx: ledeWorst ? ledeWorst.over : 0,
      ledeReservePx: ledeWorst ? ledeWorst.reserve : 0,
      ledeNeededPx: ledeWorst ? ledeWorst.need : 0,
      groundMarks, groundRepeats,
      overflowPct: +(100 * overflowPx / window.innerHeight).toFixed(1),
      centerScale: best ? +(100 * best.w * best.h / best.cellArea).toFixed(1) : null,
      cells,
      centerpiece: best ? `${best.tag}.${best.cls}` : null,
      aspect,
      emptyBandPx: maxRun,
      emptyBandPct: +(100 * maxRun / availH).toFixed(1),
      emptyBandFromTop: Math.round(bestTop - body.top),
    });
  }
  return out;
}
"""


# Window shapes chosen because they are NOT the design geometry. A page that
# only holds 16:9 when the window happens to be 16:9 is not a 16:9 page, and no
# amount of rendering at 1280x720 can tell you which one you have.
OFF_SHAPES = [(1280, 960), (1440, 900), (1600, 1200), (1366, 768), (1920, 1200)]

ASPECT_PROBE = r"""
() => {
  const out = [];
  for (const s of document.querySelectorAll('section.page')) {
    const r = s.getBoundingClientRect();
    // A zero-size page gives 0/0 = NaN, and `Math.abs(NaN - target) > 0.01` is
    // false — so every hidden page landed in the *passing* set and the report
    // said "all 30 pages hold 16:9" about pages with no box at all.
    if (!(r.width > 4) || !(r.height > 4)) {
      out.push({id: s.id, w: Math.round(r.width), h: Math.round(r.height),
                aspect: null, unmeasurable: true});
      continue;
    }
    out.push({id: s.id, w: Math.round(r.width), h: Math.round(r.height),
              aspect: +(r.width / r.height).toFixed(3), unmeasurable: false});
  }
  return out;
}
"""


def open_page(browser, url, viewport, dark=False):
    """One way in, for every probe in this file.

    Three things were previously done four different ways, or not at all:

    · **Fonts.** Four unexplained sleeps (350/300/500/600ms) and no wait on
      `document.fonts.ready`. This package embeds a display face, and every
      number in the report is a distance between glyphs — measured against
      fallback metrics if the face has not applied, and printed as fact.
    · **The document's own errors.** No `pageerror` listener anywhere, so a
      deliverable whose inline script threw mid-build was measured
      half-constructed and reported normally.
    · **The dark palette.** `dark` was threaded through three functions and read
      only to name output files; nothing ever switched the palette, so the
      docstring's "two palettes" was unimplemented and a file not literally
      named `*.dark.*` produced sheets labelled `-light-` whatever it rendered.
      `lumi-theme.css` applies dark with `class="dark"` on <body>, so do that.

    Returns (page, errors). The caller decides what an error means.
    """
    page = browser.new_page(viewport={"width": viewport[0], "height": viewport[1]})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(url, wait_until="load")
    if dark:
        page.evaluate("() => document.body.classList.add('dark')")
    try:
        page.wait_for_function("() => document.fonts && document.fonts.status === 'loaded'",
                               timeout=5000)
    except Exception:                                   # noqa: BLE001
        errors.append("webfonts did not finish loading in 5s; type metrics below "
                      "may be a fallback face")
    page.wait_for_timeout(SETTLE_MS)
    return page, errors


class _Shared:
    """One Playwright, one Chromium, however many probes a run makes.

    Until 0.1.444 every report function opened its own `sync_playwright()`
    context and launched its own browser — three per geometry plus one per
    file, so a landscape deck's default run launched Chromium THIRTEEN times
    to answer questions one browser could hold. The launch cycle measures
    ~1.4s, so that alone was ~18s of a run's wall clock, twelve launches of it removable, and it was the shape
    of the code, not a decision anyone had made. Probes now share this
    process-wide pair; `atexit` closes it, so standalone callers (tests,
    run_conformance) leak nothing.
    """
    pw: Any = None
    browser: Any = None


def shared_browser():
    if _Shared.browser is None:
        import atexit

        from playwright.sync_api import sync_playwright
        _Shared.pw = sync_playwright().start()
        _Shared.browser = _Shared.pw.chromium.launch()
        atexit.register(close_shared_browser)
    return _Shared.browser


def close_shared_browser():
    if _Shared.browser is not None:
        with contextlib.suppress(Exception):
            _Shared.browser.close()
        with contextlib.suppress(Exception):
            _Shared.pw.stop()
        _Shared.browser = _Shared.pw = None


def aspect_stage(declared_geometry, file_geometries):
    """The geometry whose shape a document OWES: its declared stage, else the
    first matrix point it was run at. Kept as a function so a test can hold it
    without a browser — the bug it replaces was a loop variable read after the
    loop, which no rendered check could have noticed because every verdict it
    produced was merely wrong rather than unmeasurable."""
    stage = deliverable_registry.STAGE_OF.get(declared_geometry)
    if stage:
        return stage
    return file_geometries[0] if file_geometries else "16x9"


def aspect_report(url, dark=False, geometry="16x9"):
    """Does a page hold its DECLARED shape in a window that is not that shape?

    This exists because the page-height probe could not answer it and never
    could have. It sets the viewport to the design geometry and then measures
    `section.height - window.innerHeight`; the page was `min-height:100svh`, so
    that difference is zero by construction. "All 30 pages are exactly 720px"
    meant "the page filled the window I made 720px tall" — the probe was
    establishing the condition it verified, and a reader found 4:3 pages in a
    4:3 window while it reported success. **A probe that builds its own answer
    proves nothing.** So this one renders shapes nobody designed for.

    The target follows the declaration. The first version hard-coded 16:9 and
    told a portrait handbook that 30 of 30 pages "are not 16:9" — every one of
    them holding A4's 0.707:1 exactly, which is what they owe. A report that
    reads as failure on a correct document teaches its reader to skip the
    section, and a skipped section is how the real failure ships.
    """
    w0, h0 = GEOMETRIES.get(geometry, GEOMETRIES["16x9"])
    target = w0 / h0
    findings = []
    browser = shared_browser()
    for w, h in OFF_SHAPES:
        page, errors = open_page(browser, url, (w, h), dark)
        try:
            rows = page.evaluate(ASPECT_PROBE)
            if not rows:
                raise Unmeasurable("no section.page matched, so no page's aspect "
                                   "could be read")
            live = [r for r in rows if not r["unmeasurable"]]
            blind = [r for r in rows if r["unmeasurable"]]
            bad = [r for r in live if abs(r["aspect"] - target) > 0.01]
            findings.append({"window": f"{w}x{h}", "pages": len(rows),
                             "measured": len(live), "unmeasurable": len(blind),
                             "unmeasurableIds": [r["id"] for r in blind],
                             "offAspect": len(bad), "errors": errors,
                             "worst": (max(bad, key=lambda r: abs(r["aspect"] - target))
                                       if bad else None)})
        finally:
            page.close()
    return findings


def with_playwright(url, geometry, dark, shot_dir, stem):
    rows, shots = None, []
    page, errors = open_page(shared_browser(), url, GEOMETRIES[geometry], dark)
    try:
        # The weight table is Python's, so the probe is handed the
        # selectors rather than repeating them — a vocabulary written in
        # two places is a vocabulary that drifts in one of them.
        rows = page.evaluate(PROBE.replace(
            '__ROLE_WEIGHT_SELECTORS__', json.dumps(list(ROLE_WEIGHTS))))
        if shot_dir:
            # Screenshot the section element, not the viewport. The first version
            # scrolled each page into view and shot the viewport, and with
            # scroll-behavior:smooth plus scroll-snap every frame landed
            # mid-transition: the whole sheet was half-pages captioned with the
            # wrong page id. An element shot is exact and needs no scrolling.
            page.add_style_tag(content="html{scroll-behavior:auto!important;"
                                       "scroll-snap-type:none!important}")
            for r in rows:
                # A page with no box cannot be screenshotted, and asking would
                # raise rather than report.
                if r.get("unmeasurable"):
                    continue
                # The stem, or two files in one run destroy each other's sheet:
                # the names carried geometry and palette but not the source, and
                # `out_dir` defaults to the file's own parent, so
                # `inspect_layout.py a.html b.html` overwrote every shared page
                # id and replaced A's sheet with B's — while printing the same
                # path under both headings. The docstring calls the sheet the
                # real output of this script.
                out = shot_dir / f"{stem}-{geometry}-{'dark' if dark else 'light'}-{r['id']}.png"
                page.locator(f"section#{r['id']}").screenshot(path=str(out))
                shots.append(out)
    finally:
        page.close()
    return rows, shots, errors


def ground_report(url, viewport=(1280, 720), dark=False):
    """Measure the ground as rendered, not as declared.

    A ground is water and light behind the page. Two things make it dishonest:
    being loud enough to compete with the content, and resolving into countable
    marks so it pretends to be a field. The first is measured here by hiding
    every foreground element, screenshotting the page, and asking what the
    loudest ground pixel actually contrasts at against the canvas. Reasoning
    about alpha from the CSS is how you end up with a texture that measures fine
    and looks like graffiti — this repo has made that mistake in three different
    forms already.
    """
    try:
        from PIL import Image
    except ImportError as exc:
        # Returning None put "Pillow is not installed" and "this deck is clean"
        # into the same output: nothing. The ground is the brand thesis of the
        # 3.x line and GROUND_CEILING is the only thing between water and
        # graffiti, so the one audit that needs a third-party library was also
        # the one whose absence was invisible.
        raise Unmeasurable("ground contrast needs Pillow — pip install pillow") from exc

    def rel_lum(px):
        # color_math.luma255 (0.1.420) — one sRGB implementation for the repo.
        return color_math.luma255(px)

    out = []
    page, _errors = open_page(shared_browser(), url, viewport, dark)
    try:
        page.add_style_tag(content=".page > .body, .page > .foot, .rail, .tools"
                                   "{visibility:hidden!important}"
                                   "html{scroll-behavior:auto!important;"
                                   "scroll-snap-type:none!important}")
        ids = page.evaluate("() => [...document.querySelectorAll('section.page')]"
                            ".filter(s => s.getBoundingClientRect().height > 4)"
                            ".map(s => s.id)")
        if not ids:
            raise Unmeasurable("no section.page with a box, so no ground to measure")
        nested = []
        with tempfile.TemporaryDirectory() as td:
            for pid in ids:
                if not page.query_selector(f"section#{pid} > .ground"):
                    # A ground wrapped a div deep breaks the token contract —
                    # `.page > .ground` is what the opacity tiers select — and
                    # skipping it silently let this audit say "no page draws
                    # one" about a page that visibly does, in the same report
                    # where the page probe counted it at any depth.
                    if page.query_selector(f"section#{pid} .ground"):
                        nested.append(pid)
                    continue
                shot = pathlib.Path(td) / f"{pid}.png"
                page.locator(f"section#{pid}").screenshot(path=str(shot))
                im = Image.open(shot).convert("RGB")
                im = im.resize((im.width // 3, im.height // 3))
                # getdata() is deprecated in Pillow 14; get_flattened_data is its
                # replacement and does not exist before it.
                px = list(getattr(im, "get_flattened_data", im.getdata)())
                # Counter, not `max(set(px), key=px.count)`: `.count` is O(N)
                # and ran once per unique colour, so this line alone measured
                # ~2.6s per page — ~90s per geometry on a 34-page document,
                # the single largest cost in the whole script. One pass counts
                # everything, and the unique keys feed the contrast loop too.
                counts = collections.Counter(px)
                canvas = counts.most_common(1)[0][0]         # the page's own canvas
                cl = rel_lum(canvas)
                worst, worst_px = 1.0, canvas
                for q in counts:
                    ql = rel_lum(q)
                    hi, lo = max(cl, ql), min(cl, ql)
                    r = (hi + 0.05) / (lo + 0.05)
                    if r > worst:
                        worst, worst_px = r, q
                out.append({"id": pid, "contrast": round(worst, 3),
                            "canvas": "#{:02X}{:02X}{:02X}".format(*canvas),
                            "loudest": "#{:02X}{:02X}{:02X}".format(*worst_px)})
    finally:
        page.close()
    return {"pages": out, "nested": nested}


CONSISTENCY_PROBE = r"""
() => {
  // One role, one rendering.
  //
  // A reader asked for a full consistency audit and this is its general form:
  // for every role that repeats across the deck, collect what it actually
  // computes to and count the distinct renderings. More than one is a finding.
  //
  // The sanctioned exceptions are DECLARED here rather than tolerated, because
  // "that one is on purpose" living in someone's head is exactly how a deck ends
  // up with a callout at three sizes. If a new exception is needed it gets
  // written down, and the write-down is the review.
  //
  // These selectors are a CONTRACT, not a description of one deck. Until 0.1.350
  // six of them — .t .sup .eyebrow .k .n .listhead — appeared nowhere in
  // `tokens/`, so they were read out of a validation artifact; a new document
  // built from the token files it is told to copy matched two of ten roles and
  // the other eight vanished from the report without a word. The classes now
  // ship in `tokens/lumi-layouts.css` under "the role vocabulary", and a role
  // that matches nothing is reported below rather than dropped.
  const ROLES = [
    // The title was ONE role ignoring size, because a cover title is legitimately
    // larger than a content title. The cost was total: 34px and 57.6px produced
    // the same key, so the first defect 0.1.349 set out to catch — "the title
    // rendered three ways" — was undetectable by the check written for it, and
    // only the closing's weight-400 was ever visible. Three registers, three
    // roles, size checked inside each. Never ignore the axis the defect is on.
    ['content title', 'h2.t',            []],
    ['cover title',   '.cover h1',       []],
    ['closing title', '.closing h2',     []],
    ['support',       '.sup',            []],
    ['eyebrow',       '.eyebrow',        []],
    ['band value',    '.band .v',        ['color']],   // three importance tiers
    ['band label',    '.band .k',        []],
    ['figure caption','.cap .n',         []],
    ['listhead',      '.listhead',       []],
    ['callout',       '.gd',             []],
    ['footer terms',  '.foot .conf',     ['color']],   // inverts on the lime openers
    ['page number',   '.foot span:last-child', ['color']],  // same lime openers
  ];
  const key = (e, ignore) => {
    const c = getComputedStyle(e);
    // Tracking is authored in em and computes to px, so comparing the px across
    // two sizes can never agree even when the design is identical. Normalise it
    // back to em — that is the number a designer actually set.
    const fs = parseFloat(c.fontSize) || 1;
    const ls = c.letterSpacing === 'normal' ? 'normal'
             : (Math.round(parseFloat(c.letterSpacing) / fs * 1000) / 1000) + 'em';
    const parts = [c.fontFamily.split(',')[0].replace(/["']/g, ''), c.fontWeight,
                   Math.round(parseFloat(c.fontSize) * 10) / 10 + 'px',
                   c.textTransform, ls];
    if (!ignore.includes('color')) parts.push(c.color);
    return parts.join(' | ');
  };
  const roles = [];
  for (const [name, sel, ignore] of ROLES) {
    const seen = {};
    for (const s of document.querySelectorAll('section.page')) {
      for (const e of s.querySelectorAll(sel)) {
        if (!(e.textContent || '').trim()) continue;
        const k = key(e, ignore);
        (seen[k] = seen[k] || []).push(s.id);
      }
    }
    const variants = Object.entries(seen).map(([k, ids]) => ({k, n: ids.length, ids}));
    // Pushed even when empty. `if (variants.length)` dropped the role from the
    // array entirely, so renaming a class made this report SHORTER AND GREENER
    // — a drift detector that stops running, silently, the moment drift happens.
    roles.push({name, sel, variants, ignored: ignore});
  }

  // The roles above are SCOPED, and a scoped role hides its own subject.
  //
  // `.band .k` and `.band .v` duly report "one rendering" while `.k` and `.v`
  // outside a band render five different ways each — measured on a real
  // deliverable. That is not the audit being wrong; it is the audit answering a
  // narrower question than the one it appears to answer, which is worse, because
  // the report reads like a clean bill.
  //
  // `tokens/lumi-layouts.css` defines `.k` under `.band` and `.v` under `.band`
  // and `.lead`, and nowhere else. Those two scopes are genuinely different
  // roles — a band value is --fs-band-value, a lead value is --fs-lead — so
  // merging them would invent a split that is not one. What is reported here is
  // the third case: a class from the shipped vocabulary used somewhere the
  // stylesheet says nothing about, where the author necessarily invented the
  // rendering. Count the renderings they invented.
  const SCOPED = [
    // `.attrs` and `.spec` joined the shipped scopes in 0.1.375, when the
    // cover-grid furniture promoted the mono key/value rows the cover and
    // closing carry. Same rule as `.band` vs `.lead`: distinct scopes are
    // distinct roles, and only a use outside every shipped scope is invented.
    // The graded ladder's row name. It is a heading inside a repeating
    // block, so one deck rendering it at 700 and another at 400 is the
    // same split this contract exists to find.
    ['.gn', ['.gr', '.launch']],
    ['.k', ['.band', '.attrs', '.spec']],
    ['.v', ['.band', '.lead', '.attrs', '.spec']],
    // Shipped scoped in 0.1.369 for the reason `.k` is: `.no` and `.yes` are the
    // most collidable names in this vocabulary, so `tokens/` styles them only
    // inside a `.swap` rather than reaching into any document that uses them for
    // something else. Scoping a role means auditing what sits outside the scope,
    // or the audit reports a clean bill about a third of the uses.
    // `.tag` joins in 0.1.381: `tokens/` ships `.tag.no` (the refused status
    // chip) as well as `.swap .no`, so a document using the chip was reported
    // as inventing a rendering it had not. A scoped audit must know every
    // scope the stylesheet declares, or it manufactures the split it exists
    // to find — and the deliverable that hit this worked around it by
    // choosing a different chip, which is worse than the finding.
    ['.no', ['.swap', '.tag']],
    ['.yes', ['.swap']],
    // `.say` ships as `.lead .say` and nowhere else, so a bare `.say` carries the
    // class this probe audits and none of the type the token file names. Found
    // twice in one week on real deliverables, where a display claim rendered at
    // body size and the page reported as having no entry point.
    ['.say', ['.lead']],
  ];
  const unscoped = [];
  for (const [sel, scopes] of SCOPED) {
    const seen = {};
    let total = 0;
    for (const s of document.querySelectorAll('section.page')) {
      for (const e of s.querySelectorAll(sel)) {
        if (!(e.textContent || '').trim()) continue;
        total++;
        if (scopes.some(sc => e.closest(sc))) continue;
        const k = key(e, []);
        (seen[k] = seen[k] || []).push(s.id);
      }
    }
    unscoped.push({sel, scopes, total,
                   variants: Object.entries(seen).map(([k, ids]) => ({k, n: ids.length, ids}))});
  }

  // One datum: content begins at the same height on every page OF A GEOMETRY.
  //
  // Landscape reserves the title block, so one height is the rule. Portrait
  // releases it — `lumi-layouts.css` sets `.body .lede { height: auto }` under
  // `max-aspect-ratio: 1/1`, because a title that sets on two lines at 1280
  // sets on three at 794 and reserving the landscape height would spend space
  // the sheet does not have. Portrait is a composition, not a reflow. Asking
  // the same aspect the stylesheet asks, so the probe and the CSS cannot
  // disagree about which geometry is which.
  // Same rule as the reserve above: the declaration decides, not the window.
  const datumExpected = document.body.dataset.geometry
    ? document.body.dataset.geometry !== 'portrait'
    : window.innerWidth >= window.innerHeight;
  const datums = {};
  let datumPages = 0, datumSkipped = 0;
  for (const s of document.querySelectorAll('section.page')) {
    if (s.getBoundingClientRect().height < 4) continue;
    const b = s.querySelector('.body'); if (!b) { datumSkipped++; continue; }
    const cell = [...b.children].find(x => !x.classList.contains('lede'));
    // A cover composes freely and has no datum to hold. Identified by the title
    // role, so a document that titles its pages another way is *counted as
    // skipped* rather than quietly leaving the audit with nothing to report.
    if (!cell) { datumSkipped++; continue; }
    if (!s.querySelector('h2.t')) { datumSkipped++; continue; }
    // A part opener holds no datum, for the reason a cover does not: it is a
    // COMPOSITION, not a content page. It carries no `.lede`, reserves no title
    // block, and `check_design.py`'s D8 has exempted it from the support-line
    // rule on the same grounds since that metric was written. Counting it
    // reported "content starts at 2 different heights" on a deck whose fourteen
    // content pages all start at 202px — a true measurement of the wrong set.
    if (s.classList.contains('opener')) { datumSkipped++; continue; }
    datumPages++;
    const sc = s.getBoundingClientRect().width / (s.offsetWidth || 1);
    const y = Math.round((cell.getBoundingClientRect().top
                          - b.getBoundingClientRect().top) / (sc || 1));
    (datums[y] = datums[y] || []).push(s.id);
  }

  // The same component may not change colour between pages: a bar that is one
  // green here and another there asks a reader what the difference means.
  const comps = {};
  let barCandidates = 0;
  for (const s of document.querySelectorAll('section.page')) {
    for (const r of s.querySelectorAll('.fig svg rect')) {
      barCandidates++;
      // SVG user units — the units the figure was AUTHORED in. Rendered size
      // is the wrong basis twice over: the page is zoom-scaled, and the drawing
      // is then scaled again to its cell, so an identical bar measured 46px at
      // 1280 and 28px at 794 and the window rejected every bar in the document
      // at A4 while accepting them all in landscape. A candidate window is a
      // statement about the drawing, so measure the drawing.
      const bb = (r.width && r.width.baseVal)
        ? {width: r.width.baseVal.value, height: r.height.baseVal.value}
        : r.getBoundingClientRect();
      // What a measure bar looks like, as a shape. LENGTH is the long side and
      // THICKNESS the short one, whichever way the bar runs: this used to read
      // width as length and height as thickness, so a VERTICAL bar chart —
      // 18 units wide and 180 tall — matched nothing, and a conformance deck
      // full of them was recorded as having no measure bars at all.
      // The thickness floor is 12 rather than 30 for the same reason: the deck
      // that exposed this draws honest 18-unit bars, and 30 was a number from
      // the one document the window was written against.
      // All of these are FLOORS and CEILINGS on the candidate window, not
      // targets a bar should aim at, and the window is a HEURISTIC — which is
      // why an empty result reports and never fails the run (FM-13).
      const len = Math.max(bb.width, bb.height);
      const thick = Math.min(bb.width, bb.height);
      if (len < 120 || thick < 12 || thick > 90) continue;
      // The filled measure bar specifically — the rect whose length IS the
      // number. Washes, card fills and callout panels are furniture and are
      // allowed to differ; the mark that encodes a value is not, because a
      // reader compares it across pages.
      const cls = (r.getAttribute('class') || '');
      if (!/\bf-(acc|lime)\b/.test(cls)) continue;
      (comps['filled measure bar'] = comps['filled measure bar'] || [])
        .push({page: s.id, cls, fill: getComputedStyle(r).fill});
    }
  }

  // Values and labels inside one band share their edges.
  const bandSkew = [];
  // Only defects were pushed, and an empty array was read as success — so
  // "values and labels share their edges" was printed about a document with no
  // band in it at all. Count what was actually looked at.
  let bandsExamined = 0, bandsTooSmall = 0;
  for (const s of document.querySelectorAll('section.page')) {
    // Where the TYPE sits, not where its box ends. A value written the shipped
    // way — `41<span class="u">%</span>` — has a box 25px deeper than a value
    // with no unit, because the extra inline box grows the line box while the
    // digits stay on the same baseline. Measured on a fresh deliverable: three
    // values whose glyphs occupied an identical 1093..1154, reported as 25px
    // out of line. The band check was reading the element box, which is the one
    // mistake this whole release is about, committed by a check added to catch
    // it. Compare the first text fragment of each.
    const textRect = (el) => {
      const w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
      let n;
      while ((n = w.nextNode())) {
        if (!n.textContent.trim()) continue;
        const r = document.createRange(); r.selectNodeContents(n);
        const rects = r.getClientRects();
        if (rects.length) return rects[0];
      }
      return el.getBoundingClientRect();
    };
    for (const band of s.querySelectorAll('.band')) {
      const kb = [...band.querySelectorAll('.k')].map(textRect);
      const vb = [...band.querySelectorAll('.v')].map(textRect);
      if (kb.length < 2) { bandsTooSmall++; continue; }
      // Only cells that actually sit side by side can be out of line — the same
      // reasoning the column probe already applies. In portrait a four-across
      // band becomes a vertical list by design, and comparing a stacked label's
      // top to the one above it reported 338px of "skew" that is the
      // composition doing exactly what the stylesheet asks.
      // Labels align on their top edge, values on their bottom: a value is set
      // large and sits on a baseline, so its top moves with its own size.
      const sideBySide = (bs, edge) => {
        let worst = 0, any = false;
        for (let i = 0; i < bs.length; i++)
          for (let j = i + 1; j < bs.length; j++) {
            if (!(bs[i].top < bs[j].bottom && bs[j].top < bs[i].bottom)) continue;
            any = true;
            worst = Math.max(worst, Math.abs(bs[i][edge] - bs[j][edge]));
          }
        return {any, worst};
      };
      const kr = sideBySide(kb, 'top'), vr = sideBySide(vb, 'bottom');
      if (!kr.any) { bandsTooSmall++; continue; }   // fully stacked: not a row
      bandsExamined++;
      const sc = s.getBoundingClientRect().width / (s.offsetWidth || 1);
      const k = Math.round(kr.worst / (sc || 1));
      const v = Math.round(vr.worst / (sc || 1));
      if (k > 1 || v > 1) bandSkew.push({page: s.id, labels: k, values: v});
    }
  }
  return {roles, unscoped, datums, datumPages, datumSkipped, datumExpected,
          comps, barCandidates, bandSkew, bandsExamined, bandsTooSmall,
          pages: document.querySelectorAll('section.page').length};
}
"""


def consistency_report(url, viewport=(1280, 720), dark=False):
    """Read the deck as a system rather than as pages. Returns the raw findings;
    main() decides what to print. No judgement here gates.

    The viewport is a parameter because it was a constant, and the constant was
    landscape. §7 makes A4 a required matrix point, `main()` runs the page probe
    at every requested geometry, and this audit ran once at 1280x720 whatever was
    asked for — then printed its verdicts under the filename with no viewport
    beside them, so an author running `--geometry a4` read landscape results as
    portrait ones. Run at A4, the probe finds the callout at three sizes on a
    deck that is clean in landscape, because the portrait block in
    `lumi-layouts.css` set it per context.
    """
    page, errors = open_page(shared_browser(), url, viewport, dark)
    try:
        out = page.evaluate(CONSISTENCY_PROBE)
    finally:
        page.close()
    if not out or not out.get("pages"):
        raise Unmeasurable("no section.page matched, so no role could be compared")
    out["errors"] = errors
    return out


def default_sheet_dir(doc: pathlib.Path) -> pathlib.Path:
    """Where the contact sheet and its page shots go when nobody says.

    A RENDER, NOT A RECORD — which is what `.gitignore` had already concluded
    twice, one directory at a time, for `fixtures/_layout/` and
    `backlog/_layout/`. The default was the document's own folder, so every run
    left a set of 4K rasters beside the deliverable it had just measured, and
    the owner's delivery folder reached 2,164 of them and 349MB between two
    cleanups a fortnight apart (2026-08-18, 2026-08-21). The standing order
    after the first one — no rasters in the delivery folder — lived in prose
    and was broken by the tool that made them.

    So the floor is the temp directory, per document, and `--out` is how a
    person keeps a sheet on purpose. The path is printed either way: a render
    nobody can find is the same as no render.
    """
    return pathlib.Path(tempfile.gettempdir()) / "lumi-layout" / doc.stem


def contact_sheet(shots, out_path, cols=4):
    """Lay the page shots out as one sheet. Pure stdlib is not enough for PNG
    compositing, so this writes an HTML sheet, which prints and shares just as
    well. (It claimed to shell out to `sips`/`montage` "when present" until
    0.1.350. It never did, and `subprocess` was imported for the call that was
    never written.)"""
    html = ["<style>body{margin:0;background:#111;display:grid;"
            f"grid-template-columns:repeat({cols},1fr);gap:10px;padding:10px}}"
            "figure{margin:0}img{width:100%;display:block;border:1px solid #333}"
            "figcaption{color:#888;font:11px monospace;padding:3px 0}</style>"]
    for s in shots:
        html.append(f'<figure><img src="{s.name}"><figcaption>{s.stem}</figcaption></figure>')
    out_path.write_text("".join(html), encoding="utf-8")
    return out_path


# ── the gating predicates ─────────────────────────────────────────────────────
# Defined once and read twice: `page_report` prints them and `--deliverable`
# exits on them. Written as two copies they would drift, and a gate that
# disagrees with the report printed above it is worse than no gate at all.
#
# What is here and what is not is the whole judgement of 0.1.368. Each of these is
# DECIDABLE — two blocks either overlap or they do not, a page is either 720px
# or it is not — and each is a defect a reader sees. Focal ratio, column weight,
# caption detachment, centerpiece scale, empty band and the part-opener count
# stay reported, because the fix for each is a design decision and a number that
# can be satisfied without improving the page ends the looking (SKILL.md rule 4,
# and D7's withdrawal in 0.1.340 is what it cost to learn that).
def _colliding(live):
    return [r for r in live if r.get("textOverlaps", 0)]


def _title_over_two_lines(live):
    """Pages whose headline runs past two lines at the design viewport.

    `design-rules` states it as the headline's ONLY hard limit and nothing
    checked it: the `reserve` verdict asks whether a title block fits the height
    it reserved, and a five-line cover inside a generous reserve passes that.
    Measured on three conformance decks 2026-08-21 — one cover ran to five
    lines.

    Bookends are exempt and the reference deck is why: it keeps every opener and
    content headline inside two lines and exceeds only on its cover and closing,
    which carry their claim at display scale under their own templates.
    """
    return [r for r in live
            if (r.get("titleLines") or {}).get("kind") == "body"
            and (r.get("titleLines") or {}).get("lines", 0) > 2]


# The cover and closing claim carries at DISPLAY scale, where two lines is not
# reachable: the accepted reference deck sets its cover in 46 characters at 58px
# and takes five lines to do it. So the bookends have their own ceiling, and it
# is not a number chosen here — it is **the accepted document's own**. Anything
# a reader has approved is by definition acceptable; anything worse than it has
# never been approved by anyone.
#
# Measured 2026-08-21 at four viewports, stable at every one because the deck is
# a fixed canvas that scales rather than reflows:
#   reference (accepted)          5 / 5
#   Cursor (passed)               3 / 3
#   Claude Code (owner: a bug)   10 / 8   — 130 characters of cover claim
BOOKEND_TITLE_LINES = 5


def _bookends_over_ceiling(live):
    """Cover or closing pages whose claim runs past the reference's own length."""
    return [r for r in live
            if (r.get("titleLines") or {}).get("kind") == "bookend"
            and (r.get("titleLines") or {}).get("lines", 0) > BOOKEND_TITLE_LINES]


# REPORTED, NOT GATED, and the accepted reference is why. A first reading of it
# counted drawings and made the reference fail its own p4, where four small
# charts of one kind sit side by side as one composition. Counting PAGES instead
# was the right correction and the reference still repeats a skeleton across
# p7/p10/p21/p22/p23 — four and five pages — while carrying 21 drawings in 21
# structures overall. So a deck the owner has accepted does reuse a skeleton
# across separate pages, and a gate at three would have failed it.
#
# The owner's complaint is real and this measures it: the deck she faulted drew
# one skeleton on four of its seven figure pages, a far higher share than the
# reference's four of twenty-one. The number that separates them is a RATIO
# nobody has calibrated, and inventing it from one accepted document is what
# GAP-024 refuses for layout variety and what 0.1.339 earned convention 6 for.
# See GAP-025.
FIGURE_SHAPE_REPEAT = 3


def _composes_as_a_deck(live):
    """Is this document a deck at all?

    A cover, a closing or a part opener — any one of the three. NOT page count:
    the two intro decks accepted in 2026-08 are nine and eleven pages, which is
    the length of a report, and a prose report carrying none of the three owes
    nothing to a rule written for decks.
    """
    return any(r.get("isCover") or r.get("isClosing") or r.get("isOpener")
               for r in live)


def _deck_structure_missing(live):
    """The structural pages a deck composes without. -> [name, ...]

    Two requirements, scoped differently, and the difference came from reading
    the folder rather than the rules:

    * **Cover and closing, unconditionally.** storyline-templates: "A deck opens
      with a cover and ends with a closing page." Every deck on the owner's
      machine carries both.
    * **An agenda, once the deck is divided into parts.** The agenda renders as
      the launch sequence, "one row per part" (0.1.519) — so a deck with parts
      and no agenda has parts nothing routes. Deliberately NOT unconditional:
      the two intro decks the owner accepted are nine and eleven pages with no
      openers and no agenda, and a checker that failed them would be inventing
      a requirement her own practice has declined. `references/` says "every
      deck scenario" and means the storyline roster; a page-for-page conversion
      of an existing deck is not one of those scenarios.

    This exists because ABSENCE SCORED BETTER THAN A POOR ATTEMPT. D27 passes a
    deck with no agenda ("owes no mirror"), `opener_subject_mark` reads `n/a` on
    a deck with no openers, and `run_conformance` counts `n/a` as met — so one
    conformance deck passed the structural gates by having none of the
    structure. A missing page is now a finding rather than a silence.
    """
    # Out of scope yields NO findings rather than "missing everything": the
    # verdict would read `n/a` either way, but `add()` formats the detail from
    # the hit list regardless, and a prose one-pager printed "composes without a
    # cover, a closing page" beside its own n/a.
    if not _composes_as_a_deck(live):
        return []
    missing = []
    if not any(r.get("isCover") for r in live):
        missing.append("a cover")
    if any(r.get("isOpener") for r in live) and not any(
            r.get("isAgenda") for r in live):
        missing.append("an agenda routing its parts")
    if not any(r.get("isClosing") for r in live):
        missing.append("a closing page")
    return missing


# THE PACING CEILING. storyline-templates makes five the writing target; this is
# the limit, one page above it.
#
# **The first version of this number was wrong, and the way it was wrong is the
# lesson.** It was set at six because the accepted reference "runs 6" — but that
# six was the reference's SIX APPENDIX PAGES AFTER ITS CLOSING, counted as an
# unbroken stretch of argument by a run computation that did not know a deck
# ends. Re-measured with `_opener_runs` fixed: the reference's longest run
# between seams is 5, and this package's passing fixture also runs 5.
#
# Six stays, for a reason that is now about the rule rather than about the
# artifact: a ceiling equal to the target is a target (CLAUDE.md convention 4,
# and 0.1.332, 0.1.336 and 0.1.337 are three shipped regressions from exactly
# that confusion). One page of headroom is what keeps five a target.
# This number is a CEILING.
OPENER_RUN_CEILING = 6


def _opener_runs(live):
    """-> [content pages between each seam], for the ARGUMENT only.

    Three things end a run, and the first two were missing until 0.1.550:

    * **The closing page ends the deck.** Anything after it is back matter. The
      accepted reference carries SIX appendix pages there, and they were being
      read as one unbroken stretch of argument — which is where the ceiling of
      six came from. Its real longest run between seams is five. A ceiling
      calibrated on an appendix is a number this package invented.
    * **A declared apparatus page is a seam.** A glossary or a scoring table is
      not the argument continuing; this file already exempts those pages from
      the visual-share target for the same reason.
    * A part opener, or the cover.
    """
    runs, run = [], 0
    for r in live:
        if r.get("isClosing"):
            runs.append(run)
            return runs                 # back matter is not an unbroken run
        if r.get("isOpener") or r.get("isCover") or r.get("isApparatus"):
            runs.append(run)
            run = 0
        else:
            run += 1
    runs.append(run)
    return runs


def _pacing_overrun(live):
    """Runs of content pages longer than a deck may go without a seam.

    **Why this gates now.** It was reported in those words — "a target, not a
    floor" — from 0.1.376 until this release, and a conformance deck came back
    as twelve pages with TEN unbroken content pages and no opener at all, which
    the report noted and no gate caught. The owner's rule is a seam about every
    five pages unless she says otherwise, and the "unless" is what kept this
    reported. (Both numbers here were wrong when first written: "four releases"
    for what was 173, and "twelve content pages" for a twelve-PAGE deck. A
    version citation cannot rot the way a count can — convention 13.)

    The "unless" is now DECLARED rather than inferred: `<body data-parts="none">`
    says this deck is deliberately one undivided sequence, on the precedent of
    `data-role="apparatus"` — "a page is apparatus because the author says so"
    (design-rules §3). Two decks the owner accepted in 2026-08 are page-for-page
    conversions running seven and nine pages without a seam; they are not decks
    that forgot their openers, and a checker cannot tell those apart by looking.
    Making the author say which keeps the exemption auditable and printed
    instead of guessed at.
    """
    if not _composes_as_a_deck(live):
        return []                  # a prose report has no seams to rate
    if any(r.get("partsDeclaredNone") for r in live):
        return []
    return [n for n in _opener_runs(live) if n > OPENER_RUN_CEILING]


def _pacing_not_applicable(live):
    """Is the seam rate a question this document does not answer?

    Two cases, and the second is the point: **a declared exemption reads `n/a`,
    never `ok`.** `run_conformance` treats both as met, but the SCORE records
    which one — so returning `ok` made a single `<body data-parts="none">` the
    cheapest way to switch this gate off leaving no trace, on a release whose
    central finding is that an agent iterates to the edge of what it is shown.
    """
    return (not _composes_as_a_deck(live)
            or any(r.get("partsDeclaredNone") for r in live))


# ROLES WHOSE WEIGHT CARRIES THE MEANING, and the weight `tokens/` ships for
# each. A heading that renders at body weight is not a heading — the graded
# ladder's row name declared no weight at all until 0.1.551 and computed to 400,
# so a four-row ladder read as four paragraphs and an owner review could not
# tell the names from their notes.
#
# The numbers are held to `tokens/lumi-layouts.css` by check_repo's
# `role weights` guard, so this table cannot drift away from the stylesheet it
# claims to quote.
ROLE_WEIGHTS = {".gr .gn": 700, ".launch .gn": 800}


def _underweight_roles(live):
    """Roles rendering lighter than the weight `tokens/` gives them.

    Rendered, not declared: a document inlines its own copy of the stylesheet,
    and the copy is where the weight goes missing. `check_design`'s D20 asks the
    same question of colour tokens and can ask it statically because a colour is
    a literal; a weight arrives through the cascade and only the browser knows
    which rule won.
    """
    hits = []
    for r in live:
        for sel, want in (r.get("roleWeights") or {}).items():
            if want is not None and want < ROLE_WEIGHTS.get(sel, 0):
                hits.append({"id": r["id"], "sel": sel, "got": want,
                             "want": ROLE_WEIGHTS[sel]})
    return hits


def _axis_names_over_plot(live):
    """Declared axis names lying across the region the marks occupy."""
    return [{"id": r["id"], **a} for r in live
            for a in (r.get("axisNames") or []) if a.get("over")]


def _axis_names_misturned(live):
    """A y-axis name that does not read upward, or an x-axis name that does.

    The vertical one is set with `writing-mode` plus a 180-degree rotation,
    which is what makes it read bottom to top; `tokens/` ships both halves and a
    document that overrides one gets a name reading downward.
    """
    return [{"id": r["id"], **a} for r in live
            for a in (r.get("axisNames") or []) if a.get("misturned")]


def _openers_repeating_a_mark(live):
    """Openers whose subject mark is one another opener already used.

    design-rules §3 says the mark "is the part's subject or it is not there", so
    two parts carrying one silhouette are saying the two parts are the same
    thing. The accepted reference draws three openers with three different
    marks; this package's own passing fixture drew one mark twice until 0.1.549,
    and the conformance deck the owner opened drew two openers byte-identical.

    Compared on the mark's own geometry, not on a name: the marks are inlined
    SVG and two copies of one silhouette have no name to differ in.
    """
    seen, repeats = {}, []
    for r in live:
        mark = r.get("openerMark")
        if not isinstance(mark, dict):
            continue
        sig = mark.get("sig")
        if not sig:
            continue
        if sig in seen:
            repeats.append(r)
        else:
            seen[sig] = r["id"]
    return repeats


def _openers_without_a_mark(live):
    """Part openers carrying no oversized filled silhouette.

    design-rules §3 permits exactly one and the reference deck carries one on
    every opener. Three decks driven to pass every other gate carried none on
    any of five openers, because the rule lived in prose and nothing read it.
    """
    return [r for r in live
            if r.get("openerMark", "absent") is None]


def _openers_with_a_stroked_mark(live):
    """Openers whose mark is an outline scaled to display size — the accident
    the same section names, as against the filled silhouette it asks for."""
    return [r for r in live
            if isinstance(r.get("openerMark"), dict)
            and not r["openerMark"].get("img")
            and r["openerMark"].get("stroked", 0) > r["openerMark"].get("filled", 0)]


def _repeated_figure_shapes(live):
    """-> [(signature, [page ids])] for structures drawn FIGURE_SHAPE_REPEAT+ times."""
    # ONE VOTE PER PAGE. The reference deck puts four small drawings of the
    # same kind side by side on p4 — that is one composition, not four repeats,
    # and counting drawings failed the accepted document on its own layout.
    # What the owner saw was a skeleton reused across SEPARATE pages.
    seen: dict[str, set[str]] = {}
    for r in live:
        for sig in set(r.get("figShapes") or []):
            seen.setdefault(sig, set()).add(r["id"])
    return [(sig, sorted(ids)) for sig, ids in seen.items()
            if len(ids) >= FIGURE_SHAPE_REPEAT]


def _fig_ink_collides(live):
    """Pages where two solid marks inside a drawing partly cover each other.

    `collision` measures page BLOCKS and never opens an svg, so a chart whose
    arrow sits on a box and whose label sits under both passes every gate this
    package has. Three agents shipped decks that way on 2026-08-21, each having
    iterated until all three checkers exited 0.
    """
    return [r for r in live if r.get("figInk")]


def _fig_ink_worst(live):
    """-> the largest {w,h,a,b} across every page, or None."""
    all_ = [x for r in _fig_ink_collides(live) for x in r["figInk"]]
    return max(all_, key=lambda x: x["w"] * x["h"]) if all_ else None


def _band_escaped(live):
    """Pages where a stat band renders outside its own box.

    Held here rather than in the probe so it can be tested without a browser,
    which is the pattern `aspect_stage` set: the measurement needs Chromium,
    the decision does not.
    """
    return [r for r in live if r.get("bandEscape")]


def _band_escape_worst(live):
    """-> the worst {out, boxPx, needPx} across every page, or None.

    `out` is what hangs outside the band; `boxPx` and `needPx` are why, and
    both are reported because "the labels are 45px out" is a symptom and
    "the row is 15px for content needing 61px" is the defect.
    """
    all_ = [b for r in _band_escaped(live) for b in r["bandEscape"]]
    return max(all_, key=lambda b: b["out"]) if all_ else None


def _starved(live):
    return [r for r in live if r.get("starved")]


def _spilling(live):
    return [r for r in live if r.get("hasFooter") and r.get("spillPx", 0) > 1]


def _too_tall(live):
    return [r for r in live if r["overflowPx"] > 1]


def _hiding(live):
    return [r for r in live if r.get("ledeClamped")]


# 4px, and the number is a rounding allowance rather than a design judgement:
# scrollHeight is an integer and a block box is fractional, so a lede that fits
# exactly can measure up to ~1.5px over across its three children. One title line
# is 35px at the design geometry, so the allowance is nowhere near wide enough to
# hide the thing this measures.
RESERVE_ALLOWANCE_PX = 4

# How far a caption's centre may sit off its drawing's ink centre, as a share of
# the drawing's own width. A CEILING, not a target — a drawing whose ink is
# perfectly centred reports 0 and that is the ordinary case. Ten percent is where
# the eye starts reading the caption as belonging to the cell rather than to the
# figure. Measured on the two tracked fixtures rather than chosen: the
# deliberately weak figure reports 34.2 and every well-composed one reports 6.1
# or less, so the threshold separates them with room on both sides.
CAP_OFF_AXIS_PCT = 10


def _overspent(live):
    ledes = [r for r in live if r.get("ledeBlocks")]
    if ledes and not ledes[0].get("reserveExpected"):
        return []                      # portrait releases the reserve by design
    return [r for r in ledes if r.get("ledeOverspendPx", 0) > RESERVE_ALLOWANCE_PX]


def _role_split(role):
    return len(role["variants"]) > 1


def _footer_wrapped(live):
    return [r for r in live if r.get("hasFooter") and r.get("footWrapped")]


# The measured defect was 2.4px of spread on a ~15px line box (ratio .16); the
# fixed sheet measures 0.00. The floor sits at half the defect so a regression
# fails long before a reader sees it, while sub-pixel rounding across zoom
# levels stays inside it.
FOOT_BASELINE_RATIO = 0.08


def _footer_baseline_gradable(live):
    """Pages whose footer carries two runs to compare.

    A footer that is only a page number has nothing to grade, and grading it
    `ok` would be the same false all-clear the probe's own nulls used to
    produce — n/a is the honest verdict, and it is not the same as passing.
    """
    return [r for r in live
            if r.get("hasFooter")
            and (r.get("footBaseline") or {}).get("runs", 0) >= 2]


def _footer_misaligned(live):
    """Footers whose runs do not sit on one baseline.

    Two shapes of the same defect: a measurable spread past the floor, and a
    footer whose runs do not share a line at all (`split`). The second is the
    LARGER displacement, and reading its null as zero is what let a footer 12px
    out of true report as "one line, one baseline". A genuinely wrapped footer
    is excluded — `footer_wrap` is already failing that page, and one defect
    reported twice under two names teaches an author to distrust both.
    """
    out = []
    for r in live:
        if not r.get("hasFooter"):
            continue
        fb = r.get("footBaseline") or {}
        if (fb.get("ratio") or 0) > FOOT_BASELINE_RATIO:
            out.append(r)
        elif fb.get("split") and not r.get("footWrapped"):
            out.append(r)
    return out


def _role_splits(c):
    return [role for role in c["roles"] if _role_split(role)]


def _no_datum(c):
    """True when the geometry expects one datum and the pages hold several.

    Absence is not a finding here: a document with no `.lede`-and-title page
    pairs reports NOT MEASURED above, and turning that into a gate would fail
    every one-page artifact for having nothing to compare.
    """
    return bool(c.get("datumExpected") and len(c["datums"]) > 1)


def _fmt_ids(rows, n=6, key=None):
    """Name the pages, so a designer knows where to look."""
    ordered = sorted(rows, key=key) if key else rows
    out = ", ".join(r["id"] for r in ordered[:n])
    return out + (f" (+{len(rows) - n} more)" if len(rows) > n else "")


def page_report(rows, geometry, errors, genre=None, declared_geometry=None,
                storyline=None):
    """Print the per-geometry table and every page-level judgement.

    Returns the number of things that could not be measured. Every block here
    reports and returns; none is a threshold a page must clear, because the fix
    for each is a design decision and a number that can be satisfied without
    making the page better ends the looking rather than directing it
    (SKILL.md rule 4). What *is* new in 0.1.350 is the other half: a block whose
    subject does not exist says so instead of congratulating the document.
    """
    unmeasured = 0
    w, h = GEOMETRIES[geometry]
    for e in errors:
        unmeasured += 1
        print(f"  PAGE ERROR: {e}")
    live = [r for r in rows if not r.get("unmeasurable")]
    blind = [r for r in rows if r.get("unmeasurable")]
    if blind:
        unmeasured += len(blind)
        print(f"  NOT MEASURED: {len(blind)} of {len(rows)} pages have no box — "
              + ", ".join(f"{r['id']} ({r['unmeasurable']})" for r in blind[:4])
              + ". Nothing below counts them.")
    if not live:
        print(f"  NOT MEASURED: no page at {geometry} had a box to measure. "
              f"Every judgement below was skipped.")
        return unmeasured + 1

    print(f"  {'page':8} {'centerpiece':22} {'of cell':>7}  {'empty band':>11}  "
          f"{'cell fill':<34}aspect")
    for r in live:
        a = r["aspect"]
        note = ""
        if a and a["ratio"] > 1.5:
            note = (f"fig {a['figure']}:1 in cell {a['cell']}:1 — "
                    f"fills {a['fillsCellHeight']}% of cell height")
        elif a:
            note = f"fig {a['figure']}:1 in cell {a['cell']}:1"
        over = f"  +{r['overflowPx']}px" if r["overflowPx"] > 1 else ""
        # `centerScale or '-'` printed 0.0 and "no centerpiece found" the same way.
        cs = r["centerScale"]
        # This print sat one level out of the loop until 0.1.341, so the table
        # reported the last page 28 times over and every page-by-page reading
        # taken from it was of one page.
        print(f"  {r['id']:8} {str(r['centerpiece'] or '-'):22} "
              f"{('-' if cs is None else str(cs)):>5}%  "
              f"{str(r['emptyBandPct'])+'%':>11}  "
              f"{' '.join(c['cls'][:4]+':'+str(c['fill'])+'%' for c in r['cells']):<34}{note}{over}")

    # Ink that could not be read. Every number below fed by inkBox — spill,
    # column skew, caption gap — is an element box on these pages, which is the
    # value this file's own comments call the bug.
    noink = [r for r in live if r.get("inkUnavailable")]
    if noink:
        unmeasured += len(noink)
        n = sum(r["inkUnavailable"] for r in noink)
        print(f"  INK NOT MEASURED: {n} drawings on {len(noink)} pages could not report "
              f"their own box (unrendered, rotated or skewed SVG) — spill, column "
              f"skew and caption gap on those pages are element boxes, not ink: "
              + _fmt_ids(noink))

    notitle = [r for r in live if r.get("titleMissing")]
    if notitle:
        unmeasured += len(notitle)
        print(f"  TITLE NOT IDENTIFIED: {len(notitle)} of {len(live)} pages reserve a "
              f".lede but carry no h2.t / h1 / h2 in it — the focal ratio on those "
              f"pages includes whatever titles them: " + _fmt_ids(notitle))

    multi = [r for r in live if r.get("colCount", 0) > 1]
    # 3px, not 8. A reader saw two tables 4px out of line and called it a bug;
    # the threshold was hiding exactly the case it was written for.
    bad_top = [r for r in multi if r["colTopSkewPx"] > 3]
    if bad_top:
        print(f"  COLUMN TOPS: {len(bad_top)} of {len(multi)} multi-column pages — "
              "side-by-side cells do not start on one line: "
              + ", ".join(f"{r['id']} {r['colTopSkewPx']}px"
                          for r in sorted(bad_top, key=lambda r: -r["colTopSkewPx"])[:6]))
    elif multi:
        print(f"  column tops: all {len(multi)} multi-column pages start on one line")
    else:
        print(f"  -- column tops: no multi-column page at {geometry}, nothing to compare")

    heavy = sorted((r for r in multi if r["colWeightRatio"] > 3),
                   key=lambda r: -r["colWeightRatio"])
    if heavy:
        print(f"  COLUMN WEIGHT: {len(heavy)} of {len(multi)} pages carry one column "
              "far heavier than its neighbour: "
              + ", ".join(f"{r['id']} {r['colWeightRatio']}:1" for r in heavy[:6]))
    elif multi:
        print(f"  column weight: no page exceeds 3:1 across {len(multi)} multi-column pages")

    flat = [r for r in live if r["focalRatio"] < 1.35 and r["figLeadPct"] < 45]
    if flat:
        print(f"  FOCAL: {len(flat)} of {len(live)} pages have no element larger than "
              f"body copy and no dominant figure — nothing for the eye to enter on: "
              + _fmt_ids(flat, 10))
    else:
        print(f"  focal: every one of {len(live)} pages has a focal element")

    ncap = sum(len(r["caps"]) for r in live)
    capbad = [(r, c) for r in live for c in r["caps"] if c["duplicated"] or c["words"] > 45]
    if capbad:
        print(f"  CAPTIONS: {len(capbad)} figure captions carry prose: "
              + ", ".join(f"{r['id']} {c['words']}w"
                          + (f", {c['duplicated']} sentence(s) repeated on the page"
                             if c["duplicated"] else "")
                          for r, c in capbad[:5]))
    elif ncap:
        print(f"  captions: {ncap} carry prose under the figure number, none repeated")
    else:
        # Precisely what was looked for, or this line contradicts the caption-gap
        # line below it: this block reads `.cap .d`, that one counts `.cap`.
        nblocks = sum(r.get("capBlocks", 0) for r in live)
        print(f"  -- caption prose: none of {nblocks} .cap blocks carries a .d "
              f"description, nothing to read for prose")

    multi_t = [r for r in live if len(r["tables"]) > 1]
    alltab = sum(len(r["tables"]) for r in live)
    if multi_t:
        print(f"  TWO TABLES: {len(multi_t)} pages carry more than one table — "
              + ", ".join(f"{r['id']} ({len(r['tables'])})" for r in multi_t[:6])
              + ". A grid claims its cells are comparable on the axis its header "
                "names; two grids side by side claim nothing and cannot align.")
    elif alltab:
        print("  tables: no page carries more than one")
    else:
        print("  -- tables: no table in this document, nothing to census")
    prose_t = [(r, t) for r in live for t in r["tables"] if t["digitPct"] <= 2]
    if prose_t:
        print(f"  TABLES: {len(prose_t)} of {alltab} tables hold prose, not values "
              f"(digit density <=2%): "
              + _fmt_ids([r for r, _ in prose_t], 10))
    elif alltab:
        print(f"  tables: all {alltab} tables carry values")

    ncap2 = sum(1 for r in live if r.get("capGapPx") is not None)
    far = [r for r in live if (r.get("capGapPx") or 0) > 20]
    if far:
        print(f"  CAPTION DETACHED: {len(far)} figures sit well above their number "
              "and name — "
              + ", ".join(f"{r['id']} {r['capGapPx']}px"
                          for r in sorted(far, key=lambda r: -(r["capGapPx"] or 0))[:6]))
    elif ncap2:
        print(f"  caption: all {ncap2} captions sit against their drawing")
    else:
        print("  -- caption: no figure pairs a drawing with a caption, nothing to measure")

    # The horizontal half. A caption centres on its figure's BOX, so an offset
    # here means the drawing's ink is off-centre inside its own viewBox: a
    # redraw, not a stylesheet fix. Reported and never gated for that reason —
    # `--deliverable` cannot ask an author to redraw on the way out the door.
    ncap3 = sum(1 for r in live if r.get("capOffPct") is not None)
    off = [r for r in live if (r.get("capOffPct") or 0) > CAP_OFF_AXIS_PCT]
    if off:
        print(f"  CAPTION OFF-CENTRE: {len(off)} "
              f"figure{'s' if len(off) != 1 else ''} carr"
              f"{'y' if len(off) != 1 else 'ies'} the caption off the drawing's axis "
              f"by more than a tenth of its width — the ink sits off-centre inside "
              f"its own viewBox, so this is a redraw: "
              + ", ".join(f"{r['id']} {r['capOffPct']}%"
                          for r in sorted(off, key=lambda r: -(r["capOffPct"] or 0))[:6]))
    elif ncap3:
        worst = max(r["capOffPct"] for r in live if r.get("capOffPct") is not None)
        print(f"  caption: all {ncap3} captions centre on their drawing "
              f"(worst {worst}% of the drawing's width)")
    else:
        print("  -- caption axis: nothing to measure")

    bad = [r for r in live if r.get("badBox")]
    if bad:
        n = sum(len(r["badBox"]) for r in bad)
        print(f"  FIGURE VIEWBOX UNREADABLE: {n} drawing{'s' if n != 1 else ''} on "
              f"{len(bad)} page{'s' if len(bad) != 1 else ''} carr"
              f"{'y' if n != 1 else 'ies'} a viewBox the browser cannot parse, so "
              f"the drawing is laid out against a box nobody chose "
              f"(first: {bad[0]['badBox'][0]!r}): " + _fmt_ids(bad, 8))

    clip = [r for r in live if r.get("clipped")]
    if clip:
        n = sum(len(r["clipped"]) for r in clip)
        worst = max((c for r in clip for c in r["clipped"]), key=lambda c: c["pct"])
        print(f"  FIGURE CLIPPED: {n} drawing{'s' if n != 1 else ''} on "
              f"{len(clip)} page{'s' if len(clip) != 1 else ''} draw outside their "
              f"own viewBox, so a root svg clips it away and the reader never sees "
              f"it (worst {worst['over']} user units, {worst['pct']}% of the "
              f"drawing): " + _fmt_ids(clip, 8))
    elif any(r.get("drawn") for r in live):
        print("  ok  figures: every drawing stays inside its own viewBox")

    echo = [r for r in live if r.get("sourceEcho", 0)]
    if echo:
        print(f"  SOURCE TWICE: {len(echo)} pages state the same source under "
              "the figure and again in the footer: " + _fmt_ids(echo, 8))
    elif any(r.get("sourceComparable") for r in live):
        n = sum(1 for r in live if r.get("sourceComparable"))
        print(f"  source: none of the {n} pages carrying both a figure source and a "
              f"footer source states the same one twice")
    elif genre in EXTERNAL_GENRES:
        # Sales and marketing material states its provenance ONCE, in the
        # colophon, and its figures carry no source line (design-rules.md §4
        # rule 9, scoped to the figure at 0.1.521). This probe exists to catch
        # the source stated TWICE; with the rule obeyed there is one statement
        # and nothing to compare. That is the rule working, not a blind spot,
        # so it is n/a with its reason rather than an unmeasured check.
        print(f"  source: n/a, a {genre} document states its provenance once in "
              f"the colophon and its figures carry no source line (rule 9; "
              f"consulting and internal analysis are NOT in this branch, they "
              f"keep per-page sourcing and reach NOT MEASURED below)")
    else:
        unmeasured += 1
        print("  -- source: NOT MEASURED, no page pairs a `.cap .srcline` with a "
              "a document `.colophon`, so nothing could be compared")

    nf = sum(len(r.get("fields", [])) for r in live)
    loose = [(r, f) for r in live for f in r.get("fields", [])
             if f["bound"] != f["marks"] or f["declared"] != f["marks"]]
    if loose:
        print(f"  FIELD WITHOUT DATA: {len(loose)} of {nf} fields have marks that "
              "carry no datum — a shimmer with nothing behind it is decoration: "
              + ", ".join(f"{r['id']} ({f['bound']}/{f['marks']} bound, "
                          f"{f['declared']} declared)" for r, f in loose[:5]))
    elif nf:
        print(f"  fields: all {nf} carry one mark per real item")
    else:
        print("  -- fields: no .field on any page, the brand device is unused here")

    # The title reserve. Two findings, and the second is the one that hides from
    # every other probe on this page: clamped text produces no spill, no
    # collision and no overflow, so a page that deletes three of its four title
    # lines reads as clean everywhere else in this report.
    ledes = [r for r in live if r.get("ledeBlocks")]
    hidden = _hiding(live)
    if hidden:
        print(f"  CONTENT HIDDEN: {len(hidden)} pages clip their own title block — "
              "text that does not render is deleted content, and the fix for an "
              "overspent reserve is shorter text: "
              + ", ".join(f"{r['id']} {r['ledeClamped'][0]['who']} "
                          f"({r['ledeClamped'][0]['why']})" for r in hidden[:5]))
    released = ledes and not ledes[0].get("reserveExpected")
    over = _overspent(live)
    if over:
        print(f"  RESERVE OVERSPENT: {len(over)} of {len(ledes)} title blocks need "
              f"more height than they reserve — the reserve is a ceiling, so this "
              f"is a request for shorter text, not a taller block: "
              + ", ".join(f"{r['id']} needs {r['ledeNeededPx']}px of "
                          f"{r['ledeReservePx']}px"
                          for r in sorted(over, key=lambda r: -r["ledeOverspendPx"])[:6]))
    elif released:
        # Reported, never flagged — the same treatment the datum line gives the
        # same geometry, and for the same reason.
        print(f"  -- reserve: released in this geometry by design (portrait sets "
              f"`.lede {{ height: auto }}`), {len(ledes)} title blocks unweighed")
    elif ledes:
        worst = max(ledes, key=lambda r: r["ledeOverspendPx"])
        print(f"  reserve: all {len(ledes)} title blocks fit what they reserve, "
              f"tightest {worst['id']} at {worst['ledeNeededPx']}px of "
              f"{worst['ledeReservePx']}px")
    else:
        print(f"  -- reserve: no page carries a .lede at {geometry}, nothing to weigh")

    clash = _colliding(live)
    if clash:
        print(f"  COLLISION: {len(clash)} pages have blocks landing on each other — "
              + ", ".join(f"{r['id']} {r['worstOverlap']['a']}/{r['worstOverlap']['b']} "
                          f"{r['worstOverlap']['w']}x{r['worstOverlap']['h']}px"
                          for r in clash[:5]))
    else:
        print(f"  collision: nothing overlaps anything on {len(live)} pages")

    long_titles = _title_over_two_lines(live)
    if long_titles:
        print(f"  TITLE PAST TWO LINES: {len(long_titles)} page"
              f"{'s' if len(long_titles) != 1 else ''} carry a headline longer "
              f"than the two-line ceiling design-rules sets: "
              + ", ".join(f"{r['id']} {r['titleLines']['lines']} lines"
                          for r in long_titles[:5]))
    else:
        print("  title lines: every headline outside the bookends fits two lines")
    bookends = _bookends_over_ceiling(live)
    if bookends:
        print(f"  BOOKEND CLAIM TOO LONG: {len(bookends)} of cover/closing run "
              f"past {BOOKEND_TITLE_LINES} lines, which is what the accepted "
              f"reference deck's own cover takes: "
              + ", ".join(f"{r['id']} {r['titleLines']['lines']} lines"
                          for r in bookends))

    bare = _openers_without_a_mark(live)
    stroked = _openers_with_a_stroked_mark(live)
    if bare or stroked:
        if bare:
            print(f"  OPENER WITHOUT A SUBJECT MARK: {len(bare)} part opener"
                  f"{'s' if len(bare) != 1 else ''} carry no oversized silhouette, "
                  f"which design-rules §3 permits as the one thing besides the "
                  f"claim: " + _fmt_ids(bare, 8))
        if stroked:
            print(f"  OPENER MARK IS STROKED: {len(stroked)} carry an outline "
                  f"scaled to display size rather than a filled silhouette: "
                  + _fmt_ids(stroked, 8))
    elif any(r.get("openerMark") for r in live):
        print("  opener mark: every part opener carries a filled silhouette")

    absent = _deck_structure_missing(live)
    if absent:
        print("  DECK COMPOSES WITHOUT " + ", ".join(absent).upper()
              + ". A page that is absent is not a page that passed: D27 owes "
                "no mirror without an agenda, and the opener checks read n/a "
                "without openers.")
    elif _composes_as_a_deck(live):
        print("  deck structure: cover, closing"
              + (", and an agenda routing its parts"
                 if any(r.get("isOpener") for r in live) else "")
              + " — all present")

    dups = _repeated_figure_shapes(live)
    if dups:
        worst = max(dups, key=lambda kv: len(kv[1]))
        print(f"  FIGURE STRUCTURE REPEATS: {len(dups)} skeleton"
              f"{'s' if len(dups) != 1 else ''} drawn "
              f"{FIGURE_SHAPE_REPEAT}+ times — worst {len(worst[1])} pages "
              f"share one ({worst[0][:40]}): " + ", ".join(worst[1][:6]))
    elif any(r.get("figShapes") for r in live):
        print(f"  figure structure: no skeleton is drawn "
              f"{FIGURE_SHAPE_REPEAT} times or more")

    inked = _fig_ink_collides(live)
    if inked:
        w = _fig_ink_worst(live)
        print(f"  INK ON INK INSIDE A DRAWING: {len(inked)} page"
              f"{'s' if len(inked) != 1 else ''} draw two solid marks over each "
              f"other (worst {w['w']}x{w['h']}px: {w['a']!r} over "
              f"{w['b']!r}): " + _fmt_ids(inked, 8))
    elif any(r.get("drawn") for r in live):
        print(f"  figure ink: nothing overlaps anything inside "
              f"{sum(1 for r in live if r.get('drawn'))} drawn page(s)")

    scaled = sum(r.get("figScaled", 0) for r in live)
    noaxis = sum(r.get("figNoAxis", 0) for r in live)
    if scaled:
        print(f"  figure axes: {noaxis} of {scaled} figure(s) that put numbers "
              f"on a scale draw no baseline for it (design-rules §4). "
              f"REPORTED, never gated — the accepted reference trips it too, so "
              f"one document cannot say whether this is a defect or the house "
              f"style. A gridline is background; a baseline is the datum.")

    escaped = _band_escaped(live)
    if escaped:
        worst = _band_escape_worst(live)
        print(f"  BAND ESCAPES ITS BOX: {len(escaped)} "
              f"{'page holds' if len(escaped) == 1 else 'pages hold'} "
              f"a stat band whose row "
              f"collapsed below the height its own cells need, so the labels "
              f"render outside it (worst {worst['out']}px out of a "
              f"{worst['boxPx']}px box needing {worst['needPx']}px): "
              + _fmt_ids(escaped, 8))
    elif any(r.get("hasBand") for r in live):
        print(f"  band: every stat band on "
              f"{sum(1 for r in live if r.get('hasBand'))} page(s) contains its "
              f"own labels")
    else:
        print("  -- band: no stat band in this document, nothing to measure")

    countable = [r for r in live if r.get("groundRepeats", 0)]
    # Whether a page HAS a ground, not whether its ground is built from the
    # countable shapes. A ground drawn in <path> has zero of those by
    # construction, so keying off the shape count said "no page draws one"
    # about thirty pages that do — and contradicted the contrast audit below.
    ngrounds = sum(1 for r in live if r.get("hasGround"))
    if countable:
        print(f"  GROUND IS COUNTABLE: {len(countable)} pages draw their ground from "
              "repeated identical marks — that is a field pretending to be water: "
              + _fmt_ids(countable))
    elif ngrounds:
        print(f"  ground: continuous on all {ngrounds} pages that carry one, "
              f"nothing to count")
    else:
        print("  -- ground: no page draws one, nothing to count")

    noh = [r for r in live if r.get("horizons", 1) != 1]
    if noh:
        print(f"  WATERLINE: {len(noh)} pages do not have exactly one horizon: "
              + ", ".join(f"{r['id']} ({r['horizons']})" for r in noh[:6]))
    else:
        print(f"  waterline: one horizon on each of {len(live)} pages")

    ndrawn = sum(1 for r in live if r["drawn"])
    openers = [r for r in live if r.get("isOpener")]
    # 2px, a rounding allowance rather than a design judgement — the invariant is
    # that an opener's copy shares the footer's inset, and either it does or it
    # does not. Reported, never gated: one deliverable is one case.
    outside = [r for r in openers if r.get("openerOutsidePx", 0) > 2]
    if outside:
        print(f"  OPENER INSET: {len(outside)} of {len(openers)} part openers set "
              f"their copy outside the footer's own margin — the page then reads "
              f"as two different left edges: "
              + ", ".join(f"{r['id']} {r['openerOutsidePx']}px {r['openerSide']}"
                          for r in sorted(outside,
                                          key=lambda r: -r["openerOutsidePx"])[:6]))
    elif openers:
        print(f"  opener inset: all {len(openers)} part openers keep their copy "
              f"inside the footer's margin")

    print(f"  part openers: {len(openers)} of {len(live)} pages"
          + (" — " + _fmt_ids(openers) if openers
             else ", so the deck runs as one undivided sequence")
          + ". An observation, not a floor.")
    # The pacing target (storyline-templates.md): about five content pages
    # between openers. Reported so a long run prompts the author to look for an
    # unmarked seam; a target read as a quota would force openers where the
    # argument has no seam, so this never gates.
    if live:
        # NOT `if openers`. A deck with no openers is the case that most needs
        # saying — the conformance deck with ten unbroken content pages
        # printed nothing here, because the block that would have reported it
        # only ran when there was already at least one seam to measure between.
        runs = _opener_runs(live)
        longest = max(runs)
        over = _pacing_overrun(live)
        if over:
            print(f"  DECK RUNS PAST ITS SEAM RATE: longest run is {longest} "
                  f"content pages against a ceiling of {OPENER_RUN_CEILING} "
                  f"(runs: {[n for n in runs if n] or runs}). About five is "
                  f"the writing target and the accepted reference's longest is "
                  f"five; six is the ceiling, one page of headroom so the "
                  f"target does not become the limit. A deck "
                  f"meant to be one undivided sequence declares "
                  f'<body data-parts="none">.')
        elif any(r.get("partsDeclaredNone") for r in live):
            print(f"  opener pacing: the deck declares itself one undivided "
                  f"sequence (data-parts=\"none\"), so the seam rate does not "
                  f"bind. Longest run {longest} content pages.")
        else:
            print(f"  opener pacing: longest run between openers is {longest} "
                  f"content page{'s' if longest != 1 else ''}, inside the "
                  f"ceiling of {OPENER_RUN_CEILING}. About five is the target.")

    # The visual-share target (owner directive 2026-08-09): about half of a
    # content page's area carries something drawn or figured. A target and a
    # review trigger, never a gate; pages under it are listed so a human looks
    # at them, and check_design.py's D16 asks the presence half statically.
    # Graded at the geometry the document DECLARES, and reported at every other.
    # The reason it is not graded off-design: the portrait tokens capped a figure
    # at 36svh and then 52svh, which put ~40% at the practical ceiling for a
    # split page — measured on the package's own fixture, where every page sat
    # "under target" at A4 while healthy. A target no page can meet is a line
    # reviewers learn to skip. That ceiling is withdrawn in 0.1.385, so the
    # sheet's shares are now reachable; the off-design report stays reported
    # because a composition graded at a shape nobody designed it for is noise.
    content = [r for r in live
               if not (r.get("isOpener") or r.get("isCover") or r.get("isClosing")
                       or r.get("isApparatus"))
               and r.get("visualPct") is not None]
    apparatus = [r for r in live if r.get("isApparatus")]
    if apparatus:
        share = round(100.0 * len(apparatus) / max(1, len(apparatus) + len(content)), 1)
        over = " — past the one-in-five ceiling" if share > 20.0 else ""
        print(f"  apparatus: {len(apparatus)} pages declared reference rather "
              f"than argument ({share}% of content pages{over}), exempt from the "
              f"share target: " + ", ".join(r["id"] for r in apparatus[:8]))
    # A hand-list, knowingly: "a4" is the only portrait geometry today. A new
    # portrait geometry added to GEOMETRIES without joining this tuple would be
    # graded against a landscape target it structurally cannot meet.
    # Grade the share at the geometry the document was DESIGNED for, and only
    # report it elsewhere. Before 0.1.382 this asked "is this render A4", which
    # was right while portrait was always a second edition and wrong the moment
    # a document declared portrait as its own stage.
    designed = (declared_geometry or "landscape")
    off_design = (geometry == "a4") != (designed == "portrait")
    # The target follows the GENRE (owner directive, 0.1.380): a sales or
    # marketing page argues visually and carries about half its area in visual
    # blocks; a training page carries about a third, because a learner needs
    # the words beside the drawing. Both are targets and review triggers, never
    # floors.
    #
    # A storyline that names its own share wins over the genre's, because it is
    # the more specific claim about the document (0.1.521). `pitch-deck` is the
    # only one today; the table, not this sentence, is the authority.
    unknown_genre = genre is not None and genre not in VISUAL_SHARE_TARGET
    unknown_storyline = (storyline is not None
                         and storyline not in deliverable_registry.STORYLINES)
    if storyline in STORYLINE_SHARE_TARGET:
        target, keyed_by = STORYLINE_SHARE_TARGET[storyline], storyline
    else:
        target, keyed_by = VISUAL_SHARE_TARGET.get(genre or "sales", 50), (genre or "sales")
    low = [r for r in content if r["visualPct"] < target]
    if content and unknown_storyline:
        # As loud as the unknown-genre branch below, and for the same reason: a
        # typo in `data-storyline` would silently drop a pitch deck back to the
        # sales 50 and print a confident green line about it.
        unmeasured += 1
        print(f"  -- visual share: NOT MEASURED, the document declares "
              f"data-storyline=\"{storyline}\" and this package knows "
              + ", ".join(sorted(deliverable_registry.STORYLINES))
              + " — fix the declaration rather than trusting a default")
    elif content and unknown_genre:
        # Loud, because the whole point of this change is that it used to be
        # silent: a typo in the declaration graded a training handbook against
        # the sales target and printed a confident green line about it.
        unmeasured += 1
        print(f"  -- visual share: NOT MEASURED, the document declares "
              f"data-genre=\"{genre}\" and this package knows "
              + ", ".join(sorted(VISUAL_SHARE_TARGET))
              + " — fix the declaration rather than trusting a default")
    elif content and off_design:
        w = min(content, key=lambda r: r["visualPct"])
        print(f"  visual share: reported only, since this is not the geometry "
              f"the document declares; lowest {w['id']} at {w['visualPct']}%")
    elif content and low:
        print(f"  visual share: {len(low)} of {len(content)} content pages sit under "
              f"the {target}% {keyed_by} target — "
              + ", ".join(f"{r['id']} {r.get('visualPct', 0)}%" for r in
                          sorted(low, key=lambda r: r.get('visualPct', 0))[:8])
              + ". A target and a review trigger, never a floor.")
    elif content:
        print(f"  visual share: all {len(content)} content pages carry visual blocks "
              f"at or above the {target}% {keyed_by} target")

    # Sheet density (§4, owner directive 2026-08-09). Reported on the geometry the
    # rule is about and nowhere else — a slide is narrated, so a landscape page
    # carrying only its centerpiece is not a finding. Reported, never gated: what
    # a page ought to say is a judgement, and `--deliverable` decides only the
    # things a rendered page can be wrong about mechanically.
    if designed == "portrait" and content:
        thin = [r for r in content if (r.get("saidBlocks") or 0) < 1]
        unlit = [r for r in content if (r.get("keyPoints") or 0) < 1]
        if thin:
            print(f"  SHEET DENSITY: {len(thin)} of {len(content)} portrait content "
                  f"pages carry a centerpiece and no second content block — "
                  + _fmt_ids(thin, 8)
                  + ". The sheet is read alone; §4 asks for what to notice, the "
                    "steps, the caution or the worked example beside the drawing.")
        else:
            print(f"  sheet density: all {len(content)} portrait content pages carry "
                  f"a second content block beside the centerpiece")
        if unlit:
            print(f"  sheet density: {len(unlit)} of {len(content)} portrait content "
                  f"pages carry no highlighted key point — " + _fmt_ids(unlit, 8))

    print(f"  figures: {ndrawn} of {len(live)} pages are built on a drawing "
          f"rather than a grid or a block of prose")

    fw = _footer_wrapped(live)
    if fw:
        print(f"  FOOTER WRAP: {len(fw)} of {len(live)} footers run to a second "
              f"line — the handling row is one line by contract: " + _fmt_ids(fw))
    elif [r for r in live if r.get("hasFooter")]:
        print(f"  footer: one line on all "
              f"{len([r for r in live if r.get('hasFooter')])} pages that carry one")
    fb = _footer_misaligned(live)
    graded = [r for r in live
              if r.get("hasFooter") and (r.get("footBaseline") or {}).get("runs", 0) >= 2]
    if fb:
        worst = max((r.get("footBaseline") or {}).get("ratio") or 0 for r in fb)
        split = [r for r in fb if (r.get("footBaseline") or {}).get("split")]
        print(f"  FOOTER BASELINE: {len(fb)} of {len(live)} footers set their "
              f"runs on different baselines (worst measured spread "
              f"{worst:.2f} of the line box"
              + (f"; {len(split)} so far apart that no two runs share the "
                 f"first line" if split else "") + ") — one row, one "
              "baseline: " + _fmt_ids(fb))
    elif graded:
        print(f"  footer baseline: one line, one baseline on all {len(graded)} "
              f"pages whose footer carries more than one run")
    capw = sum(r.get("capWrapped", 0) for r in live)
    capn = sum(r.get("capCount", 0) for r in live)
    if capw:
        print(f"  CAPTION WRAP: {capw} of {capn} figure captions run to a second "
              f"line — shorten the name (design-rules.md \u00a74 states the ceiling "
              f"per geometry): "
              + ", ".join(r["id"] for r in live if r.get("capWrapped")))
    elif capn:
        print(f"  captions: all {capn} figure names hold one line")

    skew = [r for r in live if r.get("frameSkewPx", 0) > 1 or r.get("sideMarginSkewPx", 0) > 2]
    if skew:
        print(f"  FRAME: {len(skew)} of {len(live)} pages — the footer and the "
              f"composition are not the same width, or the page is not centred: "
              + ", ".join(f"{r['id']} skew {r['frameSkewPx']}px" for r in skew[:6]))
    else:
        print(f"  frame: footer and composition share one width and centre "
              f"on all {len(live)} pages")

    # Only pages that HAVE a footer rule can stay above one. Falling back to the
    # page edge let this line contradict the waterline count directly above it.
    footed = [r for r in live if r.get("hasFooter")]
    unfooted = [r for r in live if not r.get("hasFooter")]
    if unfooted:
        unmeasured += len(unfooted)
        print(f"  FOOTER MISSING: {len(unfooted)} of {len(live)} pages carry no .foot, "
              f"so they have no footer rule to stay above: " + _fmt_ids(unfooted))
    spill = _spilling(live)
    if spill:
        print(f"  CONTENT SPILL: {len(spill)} of {len(footed)} pages run past the "
              f"footer rule — "
              + ", ".join(f"{r['id']} +{r['spillPx']}px ({r['deepestWho']})"
                          for r in sorted(spill, key=lambda r: -r["spillPx"])[:8]))
    elif footed:
        print(f"  content: all {len(footed)} pages stay above the footer rule")

    tall = _too_tall(live)
    if tall:
        print(f"  PAGE HEIGHT: {len(tall)} of {len(live)} pages exceed the {h}px page — "
              + ", ".join(f"{r['id']} +{r['overflowPx']}px" for r in tall[:8]))
    else:
        print(f"  page height: all {len(live)} pages are exactly {h}px")
    return unmeasured


def consistency_print(label, c):
    """Print the role audit. Returns how much of it could not be run."""
    unmeasured = 0
    print(f"\n{label} — one role, one rendering")
    for e in c.get("errors", []):
        unmeasured += 1
        print(f"  PAGE ERROR: {e}")
    for role in c["roles"]:
        v = sorted(role["variants"], key=lambda x: -x["n"])
        if not v:
            unmeasured += 1
            print(f"  -- {role['name']}: NOT MEASURED, no element matched "
                  f"'{role['sel']}' anywhere in the document")
        elif _role_split(role):
            note = f" (ignoring {', '.join(role['ignored'])})" if role["ignored"] else ""
            print(f"  ROLE SPLIT: {role['name']} renders {len(v)} different ways{note}")
            for x in v:
                print(f"      {x['n']:>3}x  {x['k']}")
                print(f"           on: {', '.join(sorted(set(x['ids']))[:5])}")
        else:
            print(f"  ok  {role['name']}: one rendering, {v[0]['n']} uses")

    # What the scoped roles above cannot see. Reported separately and never
    # merged into the role's own verdict: `.band .v` and `.lead .v` are two
    # renderings on purpose, and calling that a split would be a false finding
    # sitting next to a true one.
    for u in c.get("unscoped", []):
        scopes = " or ".join(u["scopes"])
        if not u["total"]:
            print(f"  -- {u['sel']} outside {scopes}: nothing on any page uses "
                  f"{u['sel']} at all")
        elif not u["variants"]:
            print(f"  ok  {u['sel']}: all {u['total']} uses sit inside {scopes}, "
                  f"where the stylesheet defines them")
        else:
            n = sum(v["n"] for v in u["variants"])
            print(f"  UNSHIPPED SCOPE: {n} of {u['total']} uses of {u['sel']} sit "
                  f"outside {scopes} — tokens/ says nothing about them, so the "
                  f"document invented {len(u['variants'])} rendering(s):")
            for x in sorted(u["variants"], key=lambda v: -v["n"]):
                print(f"      {x['n']:>3}x  {x['k']}")
                print(f"           on: {', '.join(sorted(set(x['ids']))[:5])}")

    d = c["datums"]
    if not d:
        unmeasured += 1
        print(f"  -- datum: NOT MEASURED, no page paired a .body cell with an h2.t "
              f"title ({c.get('datumSkipped', 0)} pages skipped)")
    elif not c.get("datumExpected"):
        # Reported, never flagged. Portrait releases the reserve by design.
        print(f"  -- datum: released in this geometry by design (portrait is a "
              f"composition, not a reflow) — content starts at {len(d)} heights "
              f"across {c.get('datumPages', 0)} pages")
    elif _no_datum(c):
        worst = sorted(d.items(), key=lambda kv: -len(kv[1]))
        print(f"  NO DATUM: content starts at {len(d)} different heights — "
              + ", ".join(f"{y}px x{len(ids)}" for y, ids in worst[:6]))
    else:
        y = list(d)[0]
        print(f"  ok  datum: content starts at {y}px on all "
              f"{len(list(d.values())[0])} pages that hold one")

    if not c["comps"]:
        # REPORTED, NEVER COUNTED AS UNMEASURED. The candidate window is a shape
        # heuristic, and FM-13 governs: a proxy may report, but a run must not
        # fail on one failing to recognise its subject. It did — a deck of
        # vertical bars exited 1 on four "unmeasured" checks, one per geometry,
        # with no gating finding anywhere in it.
        print(f"  -- component colour: not measured, none of {c.get('barCandidates', 0)} "
              f"rects in a .fig matches the bar window (>=120 long, 12-90 "
              f"thick either way round, class f-acc or f-lime) — a window, "
              f"not a rule about your figures")
    for comp, uses in c["comps"].items():
        fills: dict[str, list[str]] = {}
        for u in uses:
            fills.setdefault(u["fill"], []).append(u["page"])
        if len(fills) > 1:
            print(f"  COMPONENT COLOUR: the {comp} is drawn in {len(fills)} colours — "
                  + "; ".join(f"{f} on {', '.join(sorted(set(p)))}" for f, p in fills.items()))
        else:
            print(f"  ok  {comp}: one colour across {len(uses)} uses")

    if not c.get("bandsExamined"):
        unmeasured += 1
        print(f"  -- band baseline: NOT MEASURED, no .band with two or more labels "
              f"({c.get('bandsTooSmall', 0)} too small to compare)")
    elif c["bandSkew"]:
        print("  BAND BASELINE: " + ", ".join(
            f"{b['page']} labels {b['labels']}px / values {b['values']}px apart"
            for b in c["bandSkew"][:5]))
    else:
        print(f"  ok  band baseline: values and labels share their edges "
              f"across {c['bandsExamined']} bands")
    return unmeasured


def deliverable_verdicts(rows, consistency):
    """The gating findings for one file at one geometry, as {name: (verdict, detail)}.

    Computed from the same rows the report prints and through the same
    predicates, so `--deliverable` can never disagree with the text above it. A
    finding whose subject is absent is `n/a`, never `ok`: a document with no
    multi-column page has not passed the datum check, it has not taken it.
    """
    live = [r for r in rows if not r.get("unmeasurable")] if rows else []
    out = {}

    def add(name, hits, na, detail):
        out[name] = ("n/a" if na else "FAIL" if hits else "ok",
                     detail(hits) if hits else "")

    add("collision", _colliding(live), not live,
        lambda h: f"{len(h)} pages have blocks landing on each other: " + _fmt_ids(h))
    footed = [r for r in live if r.get("hasFooter")]
    add("starved_column", _starved(live), not live,
        lambda h: (f"{len(h)} pages hold a sentence in a column too narrow for "
                   f"it: " + _fmt_ids(h) + " — "
                   + "; ".join(x for r in h[:2] for x in r["starved"][:2])))
    add("content_spill", _spilling(live), not footed,
        lambda h: f"{len(h)} pages run past the footer rule: " + _fmt_ids(h))
    add("page_height", _too_tall(live), not live,
        lambda h: f"{len(h)} pages exceed the page box: " + _fmt_ids(h))
    add("content_hidden", _hiding(live), not live,
        lambda h: f"{len(h)} pages clip their own title block: " + _fmt_ids(h))
    add("footer_wrap", _footer_wrapped(live), not footed,
        lambda h: f"{len(h)} footers wrap to a second line: " + _fmt_ids(h))
    add("footer_baseline", _footer_misaligned(live),
        not _footer_baseline_gradable(footed),
        lambda h: f"{len(h)} footers set their runs on different baselines: "
                  + _fmt_ids(h))
    drawn = [r for r in live if r.get("drawn")]
    add("figure_viewbox", [r for r in live if r.get("badBox")], not drawn,
        lambda h: f"{len(h)} pages carry a drawing whose viewBox does not parse: "
                  + _fmt_ids(h))
    add("figure_clipped", [r for r in live if r.get("clipped")], not drawn,
        lambda h: f"{len(h)} pages draw outside a figure's own viewBox, which "
                  f"clips it away unseen: " + _fmt_ids(h))
    # A BAND WHOSE ROW COLLAPSED. Decidable, not aesthetic: the cells are
    # measured against the band's own box, and text outside the box it belongs
    # to is on top of whatever is beneath it.
    add("title_two_lines", _title_over_two_lines(live),
        not any(r.get("titleLines") for r in live),
        lambda h: (f"{len(h)} pages carry a headline past the two-line ceiling: "
                   + ", ".join(f"{r['id']} {r['titleLines']['lines']} lines "
                               f"({r['titleLines']['text']!r})" for r in h[:3])))
    add("deck_structure", _deck_structure_missing(live),
        not _composes_as_a_deck(live),
        lambda h: ("this deck composes without " + ", ".join(h)
                   + " — a page that is absent is not a page that passed"))
    add("opener_subject_mark",
        _openers_without_a_mark(live) + _openers_with_a_stroked_mark(live)
        + _openers_repeating_a_mark(live),
        not any(r.get("openerMark", "absent") != "absent" for r in live),
        lambda h: (f"{len(h)} part openers carry no filled silhouette, one "
                   f"that is stroked rather than filled, or one another opener "
                   f"already used — design-rules §3 permits exactly one and it "
                   f"is the part's own subject: " + _fmt_ids(h)))
    # THE SEAM RATE. Gating since 0.1.549; reported from 0.1.376 until then,
    # during which a conformance deck came back with ten unbroken content pages
    # and no opener at all and nothing failed it.
    # THE FIGURE NAME HOLDS ONE LINE (design-rules §4 rule 7). Reported since
    # the probe was written and gating from 0.1.551, and what changed in
    # between is that the measurement became a real one: while the caption also
    # carried the source line, the two were a single inline flow and the break
    # landed inside the SOURCE, so the name never appeared to wrap. Nine of ten
    # captions on one deck rendered two lines with every name reported as
    # holding one. Rule 8 now keeps the source inside the drawing, so the name
    # is alone under the figure and its wrap is its own.
    axis_declared = any(r.get("axisNames") for r in live)
    add("figure_axis_overlap", _axis_names_over_plot(live), not axis_declared,
        lambda h: (f"{len(h)} axis name(s) lie across the plot they name: "
                   + ", ".join(f"{x['id']} {x['text']!r} "
                               f"({x['over']['w']}x{x['over']['h']}px)"
                               for x in h[:3])))
    add("figure_axis_orientation", _axis_names_misturned(live), not axis_declared,
        lambda h: (f"{len(h)} axis name(s) face the wrong way — the y name "
                   f"reads bottom to top, the x name reads level: "
                   + ", ".join(f"{x['id']} {x['text']!r}" for x in h[:3])))
    add("caption_name_wrap", [r for r in live if r.get("capWrapped")],
        not any(r.get("caps") for r in live),
        lambda h: (f"{len(h)} figure names wrap to a second line — shorten the "
                   f"name, never set it smaller: " + _fmt_ids(h)))
    add("role_weight", _underweight_roles(live),
        not any(r.get("roleWeights") for r in live),
        lambda h: ("a role renders lighter than the weight tokens/ gives it: "
                   + ", ".join(f"{x['id']} {x['sel']} at {x['got']} "
                               f"(shipped {x['want']})" for x in h[:3])))
    add("opener_pacing", _pacing_overrun(live), _pacing_not_applicable(live),
        lambda h: (f"{len(h)} run(s) of content pages go past "
                   f"{OPENER_RUN_CEILING} without a seam (longest {max(h)}). "
                   f"The accepted reference's longest is 5. A deck that is "
                   f"deliberately one undivided sequence declares it with "
                   f"<body data-parts=\"none\">"))
    add("bookend_title_length", _bookends_over_ceiling(live),
        not any((r.get("titleLines") or {}).get("kind") == "bookend"
                for r in live),
        lambda h: (f"{len(h)} cover/closing claims run past "
                   f"{BOOKEND_TITLE_LINES} lines, the length of the accepted "
                   f"reference's own: "
                   + ", ".join(f"{r['id']} {r['titleLines']['lines']} lines "
                               f"({r['titleLines']['text']!r})" for r in h[:3])))
    add("figure_ink_collision", _fig_ink_collides(live), not drawn,
        lambda h: (f"{len(h)} pages draw two solid marks over each other inside "
                   f"a figure: " + _fmt_ids(h)
                   + (lambda w: f" — worst {w['w']}x{w['h']}px "
                                f"({w['a']!r} over {w['b']!r})"
                      )(_fig_ink_worst(live))))
    add("band_escape", _band_escaped(live), not live,
        lambda h: (f"{len(h)} pages hold a stat band whose labels render "
                   f"outside it: " + _fmt_ids(h)
                   + (lambda w: f" — worst {w['out']}px out of a {w['boxPx']}px "
                                f"box needing {w['needPx']}px"
                      )(_band_escape_worst(live))))
    # A DRAWING THAT CONTRADICTS ITS OWN NUMBERS. Not a design judgement and not
    # a matter of taste: the mark declares the quantity, and the length either
    # follows it or it does not. A minimum-width floor drew 1 and 4 as the same
    # bar and stretched a 4 to twice its length on the page whose caption said
    # the 4 was the finding.
    add("figure_distorts", [r for r in live if r.get("distorted")],
        not live,
        lambda h: f"{len(h)} pages draw a mark out of proportion to the value it "
                  f"declares: " + "; ".join(
                      f"{r['id']} " + ", ".join(
                          f"{d['value']} drawn as {d['drew']}px, not {d['shouldDraw']}px"
                          for d in r["distorted"][:2]) for r in h[:3]))

    # HOW MUCH OF THE DOCUMENT IS NOT DRAWN AT ALL. A ceiling on blank pages,
    # not a target for full ones, and set loose on purpose: the two documents
    # that calibrated it carry 0% and 45.5% of their content pages with nothing
    # visual, so anything between separates them and the number needs no
    # argument.
    #
    # The gaming move, written down because 0.1.339's fill floor was met by
    # stretching table rows: put one token drawing on every page. `figure_distorts`
    # is its pair — a drawing that encodes nothing cannot be checked, but one
    # that encodes wrongly now fails — and D5's shape-vocabulary spread still
    # reports a document whose figures are all the same rectangle.
    contentp = [r for r in live
                if not (r.get("isOpener") or r.get("isCover") or r.get("isClosing")
                        or r.get("isApparatus"))
                and r.get("visualPct") is not None]
    blank = [r for r in contentp if r["visualPct"] == 0]
    add("visual_absent",
        blank if contentp and len(blank) > len(contentp) * VISUAL_ABSENT_CEILING else [],
        not contentp,
        lambda h: f"{len(h)} of {len(contentp)} content pages carry nothing visual "
                  f"at all, past the {VISUAL_ABSENT_CEILING:.0%} ceiling: " + _fmt_ids(h))

    ledes = [r for r in live if r.get("ledeBlocks")]
    add("reserve_overspent", _overspent(live),
        not ledes or not ledes[0].get("reserveExpected"),
        lambda h: f"{len(h)} title blocks need more height than they reserve: "
                  + _fmt_ids(h))

    if not consistency:
        out["role_split"] = ("n/a", "the consistency audit did not run")
        out["datum"] = ("n/a", "the consistency audit did not run")
        return out
    splits = _role_splits(consistency)
    # A role that matched nothing is NOT MEASURED and already exits 1 through the
    # unmeasured path; counting it here too would report one defect twice under
    # two different names.
    graded = [r for r in consistency["roles"] if r["variants"]]
    add("role_split", splits, not graded,
        lambda h: ", ".join(f"{r['name']} renders {len(r['variants'])} ways" for r in h))
    out["datum"] = (
        "n/a" if not consistency["datums"] or not consistency.get("datumExpected")
        else "FAIL" if _no_datum(consistency) else "ok",
        f"content starts at {len(consistency['datums'])} different heights"
        if _no_datum(consistency) else "")
    return out


def deliverable_print(label, verdicts):
    print(f"\n{label} — graded as a deliverable")
    for finding, (verdict, detail) in verdicts.items():
        print(f"  {verdict:<5} {finding:<18}" + (f" {detail}" if detail else ""))


# The share target per genre. `internal` joined in 0.1.385: it had been absent,
# so an internal-analysis deck fell through the dict's default and was graded
# against the sales number without anything saying so. The value is the same 50 —
# what changed is that it is now a declared decision rather than a fallback.
#
# EVERY genre this package declares needs an entry here, and a genre that is not
# in this table is reported as not measured rather than graded as sales. A
# document declares its genre in markup, and markup has typos: `data-genre="traning"`
# used to score a training handbook against the 50% target in silence.
# Every genre in the package vocabulary needs a target here, or a document
# declaring it prints NOT MEASURED below and exits 1 — the run stops rather
# than the metric going quiet. The `genre vocabulary` guard in check_repo.py
# holds these keys equal to the registry's names.
# The genres that state provenance once for the document rather than under
# every figure (design-rules.md §4 rule 9).
#
# NOT the same set as check_design.py's constant of the same name, and the two
# must not be aligned. That one means "whose reader is outside the building"
# and decides who owes a quotable takeaway (D28); consulting belongs in it.
# This one acts on rule 9, which says the opposite in terms: "consulting
# deliverables and internal analysis KEEP per-page sourcing, because there the
# reader is auditing the claim rather than being sold to."
#
# It shipped carrying `consulting`, borrowed with the name from the other file.
# A consulting deck that had dropped its per-page sources was then told
# `n/a, a consulting document states its provenance once in the colophon` --
# the reverse of the rule it cited -- and the branch skips `unmeasured += 1`,
# so the run stopped exiting 1 on a check it had not performed.
# tests/test_provenance_genre_scope.py pins both directions.
EXTERNAL_GENRES = ("sales", "marketing")

VISUAL_SHARE_TARGET = {"sales": 50, "marketing": 50, "consulting": 50,
                       "internal": 50, "training": 30}

# The STORYLINE can raise the bar its genre sets, and one does. A seed investor
# pitch is looked at while a founder talks: the room is listening, not reading,
# so concepts and figures carry about four fifths of every content page and the
# prose is the title, one support line, the labels inside the drawing and the
# takeaway (owner directive 0.1.521; storyline-templates.md Template 11).
#
# It is a FLOOR ON THE DRAWING and therefore a CEILING ON THE PROSE, which is
# the direction that matters: an author reading it as a target inflates the
# figure instead of cutting the words. The measurement that produced it: an
# accepted roadshow BP put a figure on all thirteen of its content pages and
# still read text-heavy, because every page was a 50/50 `split` and the
# argument sat in 15-23 word titles. A `split` page cannot reach this number,
# so choosing the layout is part of meeting it.
#
# Genre keys the rule tier; this keys the shape. Where both speak, the
# storyline wins, because it is the more specific claim about the document.
STORYLINE_SHARE_TARGET = {"pitch-deck": 80}

GROUND_CEILING = 1.40          # a ceiling, not a target: quieter is always fine


def ground_print(label, g):
    pages, nested = g["pages"], g["nested"]
    # A ground the audit cannot isolate is a finding, not a skip: it exists at
    # the wrong depth for the `.page > .ground` opacity tiers, and calling the
    # page groundless would contradict the any-depth count printed above.
    if nested:
        print(f"  GROUND UNMEASURED: {len(nested)} page(s) wrap the ground "
              f"inside another element — the tiers select `.page > .ground`, "
              f"so the contrast audit cannot isolate it: "
              + ", ".join(nested[:6]))
    if not pages:
        if nested:
            return len(nested)
        # A visible finding, not a shrug: brand.md asks for the ground behind
        # every page, and until 0.1.378 a deck with none read the same here as
        # a deck that had been checked. Reported, never gated — a document
        # outside the brand may be quiet on purpose, and a reviewer decides.
        print("  GROUND MISSING: no page draws one — brand.md asks for water "
              "and light behind every page, dense to sparse by page class")
        return 0
    loud = [r for r in pages if r["contrast"] > GROUND_CEILING]
    if loud:
        print(f"  GROUND TOO LOUD: {len(loud)} of {len(pages)} pages exceed "
              f"{GROUND_CEILING}:1 against their canvas — "
              + ", ".join(f"{r['id']} {r['contrast']}" for r in loud[:6]))
    else:
        w = max(pages, key=lambda r: r["contrast"])
        print(f"  ground: all {len(pages)} pages under the {GROUND_CEILING}:1 ceiling, "
              f"loudest {w['id']} at {w['contrast']}")
    return len(nested)


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("files", nargs="+")
    ap.add_argument("--geometry", action="append", choices=list(GEOMETRIES),
                    help="repeatable; NARROWS the matrix. Left alone, the "
                         "document's data-geometry picks the points it owes "
                         "(landscape: 16x9, 16x9-hd, laptop, wide; portrait: "
                         "a4, wide) and a file declaring neither gets all five")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-sheet", action="store_true", help="numbers only, no screenshots")
    ap.add_argument("--out", default=None,
                    help="where the sheet and shots go. Default: a per-document "
                         "folder under the system temp directory, because a "
                         "contact sheet is a render and not a record. Name a "
                         "directory here to keep one on purpose.")
    ap.add_argument("--dark", action="store_true",
                    help="render the dark palette (class=\"dark\" on <body>); "
                         "inferred from a *.dark.* filename")
    ap.add_argument("--no-aspect", action="store_true",
                    help="skip the off-shape aspect assertion")
    ap.add_argument("--deliverable", action="store_true",
                    help="grade this file as something about to be sent: exit "
                         "non-zero on collision, a starved column, content "
                         "spill, page height, hidden content, a wrapped footer, "
                         "a footer whose runs sit on different baselines, an "
                         "unparseable viewBox, a drawing clipped by its own "
                         "viewBox, an overspent title reserve, a role split or "
                         "a lost datum. Without it nothing here gates.")
    args = ap.parse_args(argv)

    def declared(path):
        """The document's own geometry and genre, or (None, None).

        A deliverable is designed for ONE geometry and says so
        (`<body data-geometry="landscape">`). Rendering a landscape deck at A4
        and grading the result reports defects of a composition nobody designed
        — which is how a portrait PDF of a landscape deck came back with dead
        half-pages and a wrapped footer on every page.
        """
        try:
            head = path.read_text(encoding="utf-8", errors="replace")[:400000]
        except OSError:
            return None, None
        # Read the real <body> tag, and nothing that merely looks like one. The
        # embedded stylesheet carries both the selectors (`body[data-geometry=
        # "portrait"]`) and, in its own comments, a worked example of the tag —
        # so the first two versions of this read a landscape deck as portrait
        # and then a portrait handbook as landscape, each time out of tokens/'s
        # own documentation. Strip style blocks and comments first; what is
        # left is markup.
        head = re.sub(r"<style\b.*?</style>|<!--.*?-->", " ", head, flags=re.S | re.I)
        g = re.search(r'<body\b[^>]*\bdata-geometry=["\'](\w+)["\']', head)
        n = re.search(r'<body\b[^>]*\bdata-genre=["\'](\w+)["\']', head)
        t = re.search(r'<body\b[^>]*\bdata-storyline=["\']([\w-]+)["\']', head)
        return ((g.group(1) if g else None), (n.group(1) if n else None),
                (t.group(1) if t else None))

    geometries = args.geometry or DEFAULT_GEOMETRIES

    results, unmeasured = [], 0
    # {(file, geometry): {finding: (verdict, detail)}}. Collected whether or not
    # anything is printed, because `--json` skips every print block and the gate
    # may not depend on which output mode the operator chose.
    graded = {}
    for name in args.files:
        path = pathlib.Path(name).resolve()
        if not path.exists():
            print(f"missing: {name}")
            return 1
        decl_geo, decl_genre, decl_storyline = declared(path)
        file_geometries = geometries
        if not args.geometry and decl_geo:
            # The declared stage and every matrix point the rules attach to it,
            # plus one off-shape window to prove the stage holds regardless of
            # the reader's window.
            #
            # This narrowed to two geometries until 0.1.390, which is the real
            # reason `laptop` and `16x9-hd` were never run: widening
            # DEFAULT_GEOMETRIES alone would not have reached a deliverable,
            # because a deliverable declares its stage and took this branch.
            #
            # design-rules.md §8 makes both landscape entries matrix points, not
            # options: "16:9 landscape, 1280x720, CHECKED AT 1920x1080". The
            # short laptop window is named there too, and its stated rationale
            # is a slide one — "Slides use min-height:100svh, so an overflowing
            # page pushes its footer below the fold silently" — so it binds the
            # landscape stage. A4 is a print geometry and rendering a 1123px
            # page in a 550px window would report an overflow that means
            # nothing, so portrait does not take it.
            file_geometries = (["a4", "wide"] if decl_geo == "portrait"
                               else ["16x9", "16x9-hd", "laptop", "wide"])
        elif not args.geometry and not decl_geo:
            # STDERR. This printed to stdout, ahead of the JSON document, so
            # `--json` on any deliverable that declares no data-geometry emitted
            # a stream no parser could read — and run_conformance scored the run
            # "layout emitted no parseable report", which reads as a defect in
            # the deliverable rather than in this file. A note about what was
            # measured belongs beside the data, not inside it.
            print(f"  note: {path.name} declares no data-geometry, so all of "
                  f"{', '.join(geometries)} are graded. A deliverable is designed "
                  f"for one geometry and should say which.", file=sys.stderr)
        out_dir = pathlib.Path(args.out) if args.out else default_sheet_dir(path)
        dark = args.dark or ".dark." in path.name
        # Which matrix points this run covers, and which it is skipping. Printed
        # rather than assumed: "verified at one matrix point is not verified" is
        # a rule in design-rules.md §8, and a report that does not say how many
        # points it visited cannot be read against it.
        skipped = [g for g in GEOMETRIES if g not in file_geometries]
        print(f"\n{path.name}: {len(file_geometries)} geometry point(s) — "
              f"{', '.join(file_geometries)}"
              + (f"; not run: {', '.join(skipped)}" if skipped else ""),
              file=sys.stderr if args.json else sys.stdout)
        for geometry in file_geometries:
            shot_dir = None
            if not args.no_sheet:
                out_dir.mkdir(parents=True, exist_ok=True)
                shot_dir = out_dir
            try:
                rows, shots, errors = with_playwright(path.as_uri(), geometry, dark,
                                                      shot_dir, path.stem)
            except ImportError:
                # `--no-sheet` was the advice here and it does not help: it only
                # nulls shot_dir, and with_playwright imports playwright either way.
                print("playwright is not importable — "
                      "pip install playwright && playwright install chromium")
                return 1
            except Exception as exc:                       # noqa: BLE001
                print(f"could not render {path.name} at {geometry}: {exc}")
                return 1
            sheet = contact_sheet(shots, out_dir / f"{path.stem}-sheet-{geometry}-"
                                  f"{'dark' if dark else 'light'}.html") if shots else None

            w, h = GEOMETRIES[geometry]
            label = f"{path.name} @ {geometry} ({w}x{h}, {'dark' if dark else 'light'})"
            # `--json` used to skip the three report functions outright, and each
            # of them RETURNS the count of what it could not measure — so the
            # machine-readable mode, the one a harness consumes, was the one
            # whose exit code did not count a single unmeasured check. The
            # functions now always run and their output is swallowed instead:
            # "a check that did not run is not a check that passed" cannot be
            # true only in the mode a person is watching.
            quiet = (redirect_stdout(io.StringIO()) if args.json
                     else contextlib.nullcontext())
            with quiet:
                print(f"\n{label}")
                if not rows:
                    unmeasured += 1
                    print(f"  NOT MEASURED: no section.page matched in {path.name}. "
                          f"Nothing below this line was checked — this is a report "
                          f"about zero pages, not a clean document.")
                else:
                    unmeasured += page_report(rows, geometry, errors, decl_genre,
                                              decl_geo, decl_storyline)

            # Both audits run per geometry now, and say which one they ran at.
            try:
                c = consistency_report(path.as_uri(), GEOMETRIES[geometry], dark)
            except Unmeasurable as exc:
                c, unmeasured = None, unmeasured + 1
                with quiet:
                    print(f"\n{label} — one role, one rendering: NOT MEASURED ({exc})")
            except Exception as exc:                       # noqa: BLE001
                c, unmeasured = None, unmeasured + 1
                with quiet:
                    print(f"\n{label} — one role, one rendering: NOT MEASURED "
                          f"({exc.__class__.__name__}: {exc}). This audit did not run.")
            else:
                with quiet:
                    unmeasured += consistency_print(label, c)

            try:
                g = ground_report(path.as_uri(), GEOMETRIES[geometry], dark)
            except Unmeasurable as exc:
                g, unmeasured = None, unmeasured + 1
                with quiet:
                    print(f"  ground: NOT MEASURED ({exc})")
            except Exception as exc:                       # noqa: BLE001
                g, unmeasured = None, unmeasured + 1
                with quiet:
                    print(f"  ground: NOT MEASURED ({exc.__class__.__name__}: {exc})")
            else:
                with quiet:
                    unmeasured += ground_print(label, g)

            verdicts = deliverable_verdicts(rows, c)
            graded[(path.name, geometry)] = verdicts
            if args.deliverable and not args.json:
                deliverable_print(label, verdicts)

            if sheet and not args.json:
                print(f"  contact sheet: {sheet}")
                print("  Look at it. That is the check; the numbers only say where to look.")
            results.append({"file": path.name, "geometry": geometry,
                            "size": GEOMETRIES[geometry], "dark": dark,
                            "pages": rows, "pageErrors": errors,
                            "verdicts": {k: v for k, (v, _) in verdicts.items()},
                            "consistency": c, "ground": g})

        if args.no_aspect:
            continue
        # Off-shape by definition, so it is per file and not per geometry —
        # and the target is the DECLARED stage, never the matrix loop's
        # leftover. Until 0.1.524 this passed `geometry`, which after the loop
        # above is its last value ("wide", 1.8:1), so every correct 16:9 deck
        # read "23 of 23 pages do not hold the declared wide shape" on every
        # window. The docstring of aspect_report records the same error in its
        # first version with 16:9 hard-coded; this was the second arrival.
        try:
            aspect = aspect_report(path.as_uri(), dark,
                                   aspect_stage(decl_geo, file_geometries))
        except Unmeasurable as exc:
            unmeasured += 1
            aspect = None
            if not args.json:
                print(f"\n{path.name} — aspect: NOT MEASURED ({exc})")
        except Exception as exc:                # no browser, or a load failure
            unmeasured += 1
            aspect = None
            if not args.json:
                print(f"\n{path.name} — aspect: NOT MEASURED "
                      f"({exc.__class__.__name__}: {exc})")
        else:
            with (redirect_stdout(io.StringIO()) if args.json
                  else contextlib.nullcontext()):
                shape = "16:9" if geometry.startswith("16x9") else "its declared shape"
                print(f"\n{path.name} — does a {geometry} page hold {shape} in "
                      f"a window that is not that shape?")
                for f in aspect:
                    if f["unmeasurable"]:
                        unmeasured += 1
                        print(f"  ASPECT NOT MEASURED: window {f['window']:>10} — "
                              f"{f['unmeasurable']} of {f['pages']} pages have no box: "
                              + ", ".join(f["unmeasurableIds"][:4]))
                    if f["offAspect"]:
                        wf = f["worst"]
                        print(f"  ASPECT: window {f['window']:>10} — "
                              f"{f['offAspect']} of {f['measured']} measured pages "
                              f"do not hold the declared {geometry} shape, "
                              f"worst {wf['id']} at {wf['w']}x{wf['h']} "
                              f"({wf['aspect']}:1)")
                    elif f["measured"]:
                        print(f"  aspect: window {f['window']:>10} — "
                              f"all {f['measured']} measured pages hold the "
                              f"declared {geometry} shape")
        results.append({"file": path.name, "aspect": aspect})

    # One verdict per finding across every geometry: a page that collides at A4
    # and not at 1280 collides. Reported per geometry above; folded here, because
    # a deliverable is one artifact and it ships or it does not.
    folded: dict[str, tuple[str, str]] = {}
    for verdicts in graded.values():
        for finding, (verdict, detail) in verdicts.items():
            was = folded.get(finding, ("n/a", ""))
            if verdict == "FAIL" or (verdict == "ok" and was[0] == "n/a"):
                folded[finding] = (verdict, detail)
            folded.setdefault(finding, was)
    failing = {k: v for k, v in folded.items() if v[0] == "FAIL"}

    if args.json:
        print(json.dumps({"results": results, "unmeasured": unmeasured,
                          "verdicts": {k: v for k, (v, _) in folded.items()}},
                         indent=2))
    else:
        # ONE final line carrying BOTH facts. These used to be two prints: the
        # not-measured count first, the gating summary last — so a run could
        # end on "No gating finding fired" and still exit 1, and an operator
        # who read the last line (or grepped for it) shipped past a check that
        # never ran. Twice in one session. The last line of a verdict tool is
        # the verdict, whole.
        if args.deliverable:
            if failing:
                print(f"\nNOT SHIPPABLE: {len(failing)} of {len(folded)} gating "
                      f"findings fired — " + ", ".join(sorted(failing))
                      + (f" · and {unmeasured} check(s) could not be measured"
                         if unmeasured else ""))
            elif unmeasured:
                print(f"\nNOT SHIPPABLE: 0 gating findings fired, but "
                      f"{unmeasured} check(s) could not be measured — a check "
                      f"that did not run is not a check that passed. Exit 1.")
            else:
                na = sorted(k for k, v in folded.items() if v[0] == "n/a")
                print("\nNo gating finding fired"
                      + (f" ({len(na)} had nothing to grade: {', '.join(na)})" if na else "")
                      + ". That is geometry and consistency, not a verdict on the "
                        "design — look at the contact sheet.")
        elif unmeasured:
            print(f"\n{unmeasured} check(s) could not be measured. A check that did not "
                  f"run is not a check that passed — exit 1.")
    if args.deliverable and failing:
        return 1
    return 1 if unmeasured else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
