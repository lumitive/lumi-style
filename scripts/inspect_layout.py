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

    python3 scripts/inspect_layout.py docs/deck.html
    python3 scripts/inspect_layout.py docs/deck.html --geometry a4
    python3 scripts/inspect_layout.py docs/deck.html --dark
    python3 scripts/inspect_layout.py docs/deck.html --json

Needs Playwright with Chromium (`pip install pillow playwright && playwright
install chromium`). Pillow is needed only for the ground contrast audit, which
reports `NOT MEASURED` without it rather than disappearing.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import tempfile


class Unmeasurable(Exception):
    """A check could not run. Never silently a pass — see the module docstring.

    Same type and same contract as `check_design.py:74`. That script has printed
    `UNMEASURABLE` and returned non-zero since 0.1.339 while this one, sitting in
    the same directory, expressed all five of its failure paths as silence.
    """


# Two things every render waits for. Fixed sleeps alone are what let a report be
# measured against fallback font metrics and printed as fact: this package
# embeds a display face (`scripts/embed_font.py`), and every number in the report
# is a distance between glyphs that have not necessarily arrived yet.
SETTLE_MS = 350

# The two page geometries every LUMI deliverable serves (SKILL.md, and
# design-rules.md §7). Landscape is primary; portrait is a composition, not a
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
DEFAULT_GEOMETRIES = ["16x9", "a4", "wide"]

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
      return {top: bb.y * m.d + m.f, bottom: (bb.y + bb.height) * m.d + m.f,
              left: bb.x * m.a + m.e, right: (bb.x + bb.width) * m.a + m.e,
              height: bb.height * m.d, width: bb.width * m.a};
    } catch (err) { if (visible) inkFail++; return r; }
  };
  // Widen this and the numbers change: lists and spec strips were absent once,
  // so a full column of ordered steps reported as 10% ink. Any new block class
  // has to be added here too — a probe is only as good as its vocabulary, and
  // one that cannot see .say or .vow reports a column as empty and its
  // neighbour as misaligned.
  const INK = 'table, svg, p, h1, h2, li, ol, ul, .listhead, .band, .key, .gd, .red,'
            + ' .note, .cap, .legend, .eyebrow, .spec, .spec div, .colophon, .wordmark,'
            + ' .card, .who, dl, dt, dd, .verdict, .say, .g, .swap, .vow, .vt, .vw,'
            + ' .ledname, .lead, .tag';
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
    for (const e of s.querySelectorAll('*')) {
      if ((titleEl && titleEl.contains(e)) || e.closest('.foot')) continue;
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
    // right. A table is not, however much of the cell it fills: `.fill > table`
    // is given `height:100%`, so every prose table on the deck reports 100% of
    // its cell and would have counted as a focal element here. That is D7's
    // exact failure — measuring the box instead of the thing in it — and it
    // reached this probe before the probe was a day old.
    const centerIsDrawing = best && (best.tag === 'svg' || best.cls === 'fig');
    const figLead = (best && centerIsDrawing) ? (best.w * best.h / best.cellArea) : 0;

    // ── caption budget ────────────────────────────────────────────────────
    // Under a figure belongs the number, the name and the source. Prose there is
    // body copy in a caption's clothes: it sits at caption size, far from the
    // sentence it explains, and on two pages it turned out to repeat the page's
    // own column verbatim. Duplication is the part worth measuring — a reader
    // sees it before they can say why.
    const pageText = (s.innerText || '').replace(/\s+/g, ' ');
    const caps = [];
    for (const cap of s.querySelectorAll('.cap')) {
      const d = cap.querySelector('.d');
      if (!d) continue;
      const txt = (d.innerText || '').replace(/\s+/g, ' ').trim();
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
    let capGapPx = null;
    for (const fig of s.querySelectorAll('.fig')) {
      const sv = fig.querySelector('svg[viewBox]:not(.ic)');
      const cap = fig.querySelector('.cap');
      if (!sv || !cap || sv.getBoundingClientRect().height < 4) continue;
      const gap = inPageUnits(cap.getBoundingClientRect().top - inkBox(sv).bottom);
      capGapPx = capGapPx === null ? gap : Math.max(capGapPx, gap);
    }

    // One source per page. §4 rule 4 asks every figure for a source line and the
    // footer contract asks every page for one; nobody checked the single-figure
    // page, where they say the same thing twice and sometimes word for word.
    const cite = (t) => new Set((t.match(/§\s?[\d.]+[a-z]?|Appendix\s+\w|findings summary/gi) || [])
                                 .map(x => x.replace(/\s+/g, '').toLowerCase()));
    const figSrc = s.querySelector('.cap .srcline');
    const footSrc = s.querySelector('.foot .src');
    let sourceEcho = 0;
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
    const TSEL = 'p,li,dt,dd,h1,h2,td,th,.k,.v,.g,.say,.gd,.key,.note,.listhead,'
               + '.eyebrow,.cap,.srcline,.conf,.site,.tick,.vt,.vw,.vn,.no,.yes,'
               + '.who,.verdict,.wordmark,.sub,.colophon,.openpart,.openclaim,'
               + '.openrun,.ledname';
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
      titleMissing: titleExpected && !anyTitle,
      hasGround: s.querySelectorAll('.ground').length,
      capBlocks: s.querySelectorAll('.cap').length,
      spillPx, pageSpillPx, deepestWho,
      frameSkewPx,
      sideMarginSkewPx: Math.round(Math.abs((body.left - sr.left) - (sr.right - body.right))),
      layout, colCount, colTopSkewPx, colWeightRatio,
      focalPx: Math.round(focalPx), focalText, bodyPx: Math.round(bodyPx),
      focalRatio: +(focalPx / Math.max(1, bodyPx)).toFixed(2),
      figLeadPct: +(100 * figLead).toFixed(0),
      caps, tables, drawn, capGapPx, sourceEcho, fields, horizons,
      textOverlaps, worstOverlap,
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


def aspect_report(url, dark=False):
    """Does a landscape page hold 16:9 in a window that is not 16:9?

    This exists because the page-height probe could not answer it and never
    could have. It sets the viewport to the design geometry and then measures
    `section.height - window.innerHeight`; the page was `min-height:100svh`, so
    that difference is zero by construction. "All 30 pages are exactly 720px"
    meant "the page filled the window I made 720px tall" — the probe was
    establishing the condition it verified, and a reader found 4:3 pages in a
    4:3 window while it reported success. **A probe that builds its own answer
    proves nothing.** So this one renders shapes nobody designed for.
    """
    from playwright.sync_api import sync_playwright
    target = 16 / 9
    findings = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for w, h in OFF_SHAPES:
            page, errors = open_page(browser, url, (w, h), dark)
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
            page.close()
        browser.close()
    return findings


def with_playwright(url, geometry, dark, shot_dir, stem):
    from playwright.sync_api import sync_playwright
    rows, shots = None, []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page, errors = open_page(browser, url, GEOMETRIES[geometry], dark)
        rows = page.evaluate(PROBE)
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
        browser.close()
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
    from playwright.sync_api import sync_playwright
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
        def f(v):
            v /= 255.0
            return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
        return 0.2126 * f(px[0]) + 0.7152 * f(px[1]) + 0.0722 * f(px[2])

    out = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page, _errors = open_page(browser, url, viewport, dark)
        page.add_style_tag(content=".page > .body, .page > .foot, .rail, .tools"
                                   "{visibility:hidden!important}"
                                   "html{scroll-behavior:auto!important;"
                                   "scroll-snap-type:none!important}")
        ids = page.evaluate("() => [...document.querySelectorAll('section.page')]"
                            ".filter(s => s.getBoundingClientRect().height > 4)"
                            ".map(s => s.id)")
        if not ids:
            browser.close()
            raise Unmeasurable("no section.page with a box, so no ground to measure")
        with tempfile.TemporaryDirectory() as td:
            for pid in ids:
                if not page.query_selector(f"section#{pid} > .ground"):
                    continue
                shot = pathlib.Path(td) / f"{pid}.png"
                page.locator(f"section#{pid}").screenshot(path=str(shot))
                im = Image.open(shot).convert("RGB")
                im = im.resize((im.width // 3, im.height // 3))
                # getdata() is deprecated in Pillow 14; get_flattened_data is its
                # replacement and does not exist before it.
                px = list(getattr(im, "get_flattened_data", im.getdata)())
                canvas = max(set(px), key=px.count)          # the page's own canvas
                cl = rel_lum(canvas)
                worst, worst_px = 1.0, canvas
                for q in set(px):
                    ql = rel_lum(q)
                    hi, lo = max(cl, ql), min(cl, ql)
                    r = (hi + 0.05) / (lo + 0.05)
                    if r > worst:
                        worst, worst_px = r, q
                out.append({"id": pid, "contrast": round(worst, 3),
                            "canvas": "#%02X%02X%02X" % canvas,
                            "loudest": "#%02X%02X%02X" % worst_px})
        browser.close()
    return out


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

  // One datum: content begins at the same height on every page OF A GEOMETRY.
  //
  // Landscape reserves the title block, so one height is the rule. Portrait
  // releases it — `lumi-layouts.css` sets `.body .lede { height: auto }` under
  // `max-aspect-ratio: 1/1`, because a title that sets on two lines at 1280
  // sets on three at 794 and reserving the landscape height would spend space
  // the sheet does not have. Portrait is a composition, not a reflow. Asking
  // the same aspect the stylesheet asks, so the probe and the CSS cannot
  // disagree about which geometry is which.
  const datumExpected = window.innerWidth >= window.innerHeight;
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
      const bb = r.getBoundingClientRect();
      // What a measure bar looks like, as a shape. All three are FLOORS and
      // CEILINGS on the candidate window, not targets a bar should aim at:
      // at least 120px long (shorter and it is a tick, a swatch or a rule),
      // between 30px and 90px thick (thinner is a rule, thicker is a panel).
      // A deck whose bars sit outside this window matches nothing here — which
      // is why the count above is reported rather than the window silently
      // yielding an empty result that reads as agreement.
      if (bb.width < 120 || bb.height < 30 || bb.height > 90) continue;
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
  return {roles, datums, datumPages, datumSkipped, datumExpected,
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
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page, errors = open_page(browser, url, viewport, dark)
        out = page.evaluate(CONSISTENCY_PROBE)
        browser.close()
    if not out or not out.get("pages"):
        raise Unmeasurable("no section.page matched, so no role could be compared")
    out["errors"] = errors
    return out


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


def _fmt_ids(rows, n=6, key=None):
    """Name the pages, so a designer knows where to look."""
    ordered = sorted(rows, key=key) if key else rows
    out = ", ".join(r["id"] for r in ordered[:n])
    return out + (f" (+{len(rows) - n} more)" if len(rows) > n else "")


def page_report(rows, geometry, errors):
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

    echo = [r for r in live if r.get("sourceEcho", 0)]
    if echo:
        print(f"  SOURCE TWICE: {len(echo)} pages state the same source under "
              "the figure and again in the footer: " + _fmt_ids(echo, 8))
    else:
        print("  source: no page states the same source twice")

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

    clash = [r for r in live if r.get("textOverlaps", 0)]
    if clash:
        print(f"  COLLISION: {len(clash)} pages have blocks landing on each other — "
              + ", ".join(f"{r['id']} {r['worstOverlap']['a']}/{r['worstOverlap']['b']} "
                          f"{r['worstOverlap']['w']}x{r['worstOverlap']['h']}px"
                          for r in clash[:5]))
    else:
        print(f"  collision: nothing overlaps anything on {len(live)} pages")

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
    print(f"  figures: {ndrawn} of {len(live)} pages are built on a drawing "
          f"rather than a grid or a block of prose")

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
    spill = [r for r in footed if r.get("spillPx", 0) > 1]
    if spill:
        print(f"  CONTENT SPILL: {len(spill)} of {len(footed)} pages run past the "
              f"footer rule — "
              + ", ".join(f"{r['id']} +{r['spillPx']}px ({r['deepestWho']})"
                          for r in sorted(spill, key=lambda r: -r["spillPx"])[:8]))
    elif footed:
        print(f"  content: all {len(footed)} pages stay above the footer rule")

    tall = [r for r in live if r["overflowPx"] > 1]
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
        elif len(v) > 1:
            note = f" (ignoring {', '.join(role['ignored'])})" if role["ignored"] else ""
            print(f"  ROLE SPLIT: {role['name']} renders {len(v)} different ways{note}")
            for x in v:
                print(f"      {x['n']:>3}x  {x['k']}")
                print(f"           on: {', '.join(sorted(set(x['ids']))[:5])}")
        else:
            print(f"  ok  {role['name']}: one rendering, {v[0]['n']} uses")

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
    elif len(d) > 1:
        worst = sorted(d.items(), key=lambda kv: -len(kv[1]))
        print(f"  NO DATUM: content starts at {len(d)} different heights — "
              + ", ".join(f"{y}px x{len(ids)}" for y, ids in worst[:6]))
    else:
        y = list(d)[0]
        print(f"  ok  datum: content starts at {y}px on all "
              f"{len(list(d.values())[0])} pages that hold one")

    if not c["comps"]:
        unmeasured += 1
        print(f"  -- component colour: NOT MEASURED, none of {c.get('barCandidates', 0)} "
              f"rects in a .fig is a filled measure bar (>=120px long, 30-90px thick, "
              f"class f-acc or f-lime)")
    for comp, uses in c["comps"].items():
        fills = {}
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


GROUND_CEILING = 1.40          # a ceiling, not a target: quieter is always fine


def ground_print(label, g):
    if not g:
        print(f"  ground: no page carries one")
        return 0
    loud = [r for r in g if r["contrast"] > GROUND_CEILING]
    if loud:
        print(f"  GROUND TOO LOUD: {len(loud)} of {len(g)} pages exceed "
              f"{GROUND_CEILING}:1 against their canvas — "
              + ", ".join(f"{r['id']} {r['contrast']}" for r in loud[:6]))
    else:
        w = max(g, key=lambda r: r["contrast"])
        print(f"  ground: all {len(g)} pages under the {GROUND_CEILING}:1 ceiling, "
              f"loudest {w['id']} at {w['contrast']}")
    return 0


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("files", nargs="+")
    ap.add_argument("--geometry", action="append", choices=list(GEOMETRIES),
                    help="repeatable; defaults to 16x9, a4 and wide")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-sheet", action="store_true", help="numbers only, no screenshots")
    ap.add_argument("--out", default=None, help="where the sheet and shots go")
    ap.add_argument("--dark", action="store_true",
                    help="render the dark palette (class=\"dark\" on <body>); "
                         "inferred from a *.dark.* filename")
    ap.add_argument("--no-aspect", action="store_true",
                    help="skip the off-shape aspect assertion")
    args = ap.parse_args(argv)
    geometries = args.geometry or DEFAULT_GEOMETRIES

    results, unmeasured = [], 0
    for name in args.files:
        path = pathlib.Path(name).resolve()
        if not path.exists():
            print(f"missing: {name}")
            return 1
        out_dir = pathlib.Path(args.out) if args.out else path.parent / "_layout"
        dark = args.dark or ".dark." in path.name
        for geometry in geometries:
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
            if not args.json:
                print(f"\n{label}")
            if not rows:
                unmeasured += 1
                if not args.json:
                    print(f"  NOT MEASURED: no section.page matched in {path.name}. "
                          f"Nothing below this line was checked — this is a report "
                          f"about zero pages, not a clean document.")
            elif not args.json:
                unmeasured += page_report(rows, geometry, errors)

            # Both audits run per geometry now, and say which one they ran at.
            try:
                c = consistency_report(path.as_uri(), GEOMETRIES[geometry], dark)
            except Unmeasurable as exc:
                c, unmeasured = None, unmeasured + 1
                if not args.json:
                    print(f"\n{label} — one role, one rendering: NOT MEASURED ({exc})")
            except Exception as exc:                       # noqa: BLE001
                c, unmeasured = None, unmeasured + 1
                if not args.json:
                    print(f"\n{label} — one role, one rendering: NOT MEASURED "
                          f"({exc.__class__.__name__}: {exc}). This audit did not run.")
            else:
                if not args.json:
                    unmeasured += consistency_print(label, c)

            try:
                g = ground_report(path.as_uri(), GEOMETRIES[geometry], dark)
            except Unmeasurable as exc:
                g, unmeasured = None, unmeasured + 1
                if not args.json:
                    print(f"  ground: NOT MEASURED ({exc})")
            except Exception as exc:                       # noqa: BLE001
                g, unmeasured = None, unmeasured + 1
                if not args.json:
                    print(f"  ground: NOT MEASURED ({exc.__class__.__name__}: {exc})")
            else:
                if not args.json:
                    unmeasured += ground_print(label, g)

            if sheet and not args.json:
                print(f"  contact sheet: {sheet}")
                print("  Look at it. That is the check; the numbers only say where to look.")
            results.append({"file": path.name, "geometry": geometry,
                            "size": GEOMETRIES[geometry], "dark": dark,
                            "pages": rows, "pageErrors": errors,
                            "consistency": c, "ground": g})

        if args.no_aspect:
            continue
        # Off-shape by definition, so it is per file and not per geometry.
        try:
            aspect = aspect_report(path.as_uri(), dark)
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
            if not args.json:
                print(f"\n{path.name} — does a landscape page hold 16:9 in a window "
                      f"that is not 16:9?")
                for f in aspect:
                    if f["unmeasurable"]:
                        unmeasured += 1
                        print(f"  ASPECT NOT MEASURED: window {f['window']:>10} — "
                              f"{f['unmeasurable']} of {f['pages']} pages have no box: "
                              + ", ".join(f["unmeasurableIds"][:4]))
                    if f["offAspect"]:
                        wf = f["worst"]
                        print(f"  ASPECT: window {f['window']:>10} — "
                              f"{f['offAspect']} of {f['measured']} measured pages are "
                              f"not 16:9, worst {wf['id']} at {wf['w']}x{wf['h']} "
                              f"({wf['aspect']}:1)")
                    elif f["measured"]:
                        print(f"  aspect: window {f['window']:>10} — "
                              f"all {f['measured']} measured pages hold 16:9")
        results.append({"file": path.name, "aspect": aspect})

    if args.json:
        print(json.dumps({"results": results, "unmeasured": unmeasured}, indent=2))
    elif unmeasured:
        print(f"\n{unmeasured} check(s) could not be measured. A check that did not "
              f"run is not a check that passed — exit 1.")
    return 1 if unmeasured else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
