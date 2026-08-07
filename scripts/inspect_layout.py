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

**Nothing here gates.** Exit code is 0 unless the page could not be rendered.
Release 1.9.0 answered "the pages look empty" with an 82% fill floor, satisfied
it by stretching table rows, and shipped four diagrams at 40% of their cell. A
number that can be satisfied without improving the page ends the looking.

    python3 scripts/inspect_layout.py docs/deck.html
    python3 scripts/inspect_layout.py docs/deck.html --geometry a4
    python3 scripts/inspect_layout.py docs/deck.html --json

Needs a headless Chrome. Uses Playwright if importable, otherwise falls back to
`chrome --headless --screenshot`; with neither it still prints the geometry
report from the DOM via the fallback and says the sheet was skipped.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
import tempfile

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
  const tagOf = (e) => ((e.className || '').toString().split(' ')[0]
                        || e.tagName.toLowerCase());
  const inkBox = (e) => {
    const r = e.getBoundingClientRect();
    if (e.tagName.toLowerCase() !== 'svg' || !e.viewBox || !e.viewBox.baseVal.width) return r;
    try {
      const bb = e.getBBox(), m = e.getScreenCTM();
      if (!m || !bb.height) return r;
      return {top: bb.y * m.d + m.f, bottom: (bb.y + bb.height) * m.d + m.f,
              left: bb.x * m.a + m.e, right: (bb.x + bb.width) * m.a + m.e,
              height: bb.height * m.d, width: bb.width * m.a};
    } catch (err) { return r; }
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
  const out = [];
  for (const s of document.querySelectorAll('section.page')) {
    const sr = s.getBoundingClientRect();
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
      const r = c.getBoundingClientRect();
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
        const r = e.getBoundingClientRect();
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
    const svg = [...s.querySelectorAll('.fig svg[viewBox]:not(.ic)')]
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
    const boxes = [...s.querySelectorAll(INK)].map(e => e.getBoundingClientRect())
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
    // Two different overflows, and 2.2.0 needs both.
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
      const r = inkBox(e);
      if (r.height < 2 || r.width < 2) continue;
      if (r.bottom > deepest) { deepest = r.bottom; deepestWho = tagOf(e); }
    }
    const footRule = footEl ? footEl.getBoundingClientRect().top : sr.bottom;
    const spillPx = deepest > -1e9 ? inPageUnits(deepest - footRule) : 0;
    const pageSpillPx = deepest > -1e9 ? inPageUnits(deepest - sr.bottom) : 0;
    // Frame alignment. The page frame's parts must share one width and one
    // centre line, or the composition and the source line that sources it drift
    // apart. This is invisible at the design geometry — 2.0.1 shipped a
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
    // the page reads as two unrelated documents. 2.1.0's provenance: layouts.css
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
    for (const e of s.querySelectorAll('*')) {
      // The page title is excluded, or it masks every flat page beneath it. A
      // cover or closing whose h2 *is* the composition carries no .t class,
      // so exclude the title specifically rather than the tag.
      if (e.closest('h2.t') || e.closest('.foot')) continue;
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

    const tables = [];
    for (const t of s.querySelectorAll('table')) {
      const txt = (t.innerText || '');
      const digits = (txt.match(/\d/g) || []).length;
      tables.push({rows: t.querySelectorAll('tr').length,
                   digitPct: +(100 * digits / Math.max(1, txt.length)).toFixed(0)});
    }
    const drawn = [...s.querySelectorAll('svg[viewBox]:not(.ic)')]
      .some(e => e.getBoundingClientRect().height > 60);
    out.push({
      id: s.id,
      pageH: Math.round(sr.height),
      overflowPx,
      spillPx, pageSpillPx, deepestWho,
      frameSkewPx,
      sideMarginSkewPx: Math.round(Math.abs((body.left - sr.left) - (sr.right - body.right))),
      layout, colCount, colTopSkewPx, colWeightRatio,
      focalPx: Math.round(focalPx), focalText, bodyPx: Math.round(bodyPx),
      focalRatio: +(focalPx / Math.max(1, bodyPx)).toFixed(2),
      figLeadPct: +(100 * figLead).toFixed(0),
      caps, tables, drawn, capGapPx, sourceEcho,
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
    out.push({id: s.id, w: Math.round(r.width), h: Math.round(r.height),
              aspect: +(r.width / r.height).toFixed(3)});
  }
  return out;
}
"""


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
            page = browser.new_page(viewport={"width": w, "height": h})
            page.goto(url)
            page.wait_for_timeout(300)
            rows = page.evaluate(ASPECT_PROBE)
            bad = [r for r in rows if abs(r["aspect"] - target) > 0.01]
            findings.append({"window": f"{w}x{h}", "pages": len(rows),
                             "offAspect": len(bad),
                             "worst": (max(bad, key=lambda r: abs(r["aspect"] - target))
                                       if bad else None)})
            page.close()
        browser.close()
    return findings


def with_playwright(url, geometry, dark, shot_dir):
    from playwright.sync_api import sync_playwright
    w, h = GEOMETRIES[geometry]
    rows, shots = None, []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": w, "height": h})
        page.goto(url)
        page.wait_for_timeout(350)
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
                out = shot_dir / f"{geometry}-{'dark' if dark else 'light'}-{r['id']}.png"
                page.locator(f"section#{r['id']}").screenshot(path=str(out))
                shots.append(out)
        browser.close()
    return rows, shots


def contact_sheet(shots, out_path, cols=4):
    """Stitch the page shots into one image. Pure stdlib is not enough for PNG
    compositing, so this shells out to `sips`/`montage` when present and
    otherwise writes an HTML sheet, which prints and shares just as well."""
    html = ["<style>body{margin:0;background:#111;display:grid;"
            f"grid-template-columns:repeat({cols},1fr);gap:10px;padding:10px}}"
            "figure{margin:0}img{width:100%;display:block;border:1px solid #333}"
            "figcaption{color:#888;font:11px monospace;padding:3px 0}</style>"]
    for s in shots:
        html.append(f'<figure><img src="{s.name}"><figcaption>{s.stem}</figcaption></figure>')
    out_path.write_text("".join(html), encoding="utf-8")
    return out_path


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("files", nargs="+")
    ap.add_argument("--geometry", action="append", choices=list(GEOMETRIES),
                    help="repeatable; defaults to 16x9 and a4")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-sheet", action="store_true", help="numbers only, no screenshots")
    ap.add_argument("--out", default=None, help="where the sheet and shots go")
    ap.add_argument("--no-aspect", action="store_true",
                    help="skip the off-shape aspect assertion")
    args = ap.parse_args(argv)
    geometries = args.geometry or DEFAULT_GEOMETRIES

    results = []
    for name in args.files:
        path = pathlib.Path(name).resolve()
        if not path.exists():
            print(f"missing: {name}")
            return 1
        out_dir = pathlib.Path(args.out) if args.out else path.parent / "_layout"
        dark = ".dark." in path.name
        for geometry in geometries:
            shot_dir = None
            if not args.no_sheet:
                out_dir.mkdir(parents=True, exist_ok=True)
                shot_dir = out_dir
            try:
                rows, shots = with_playwright(path.as_uri(), geometry, dark, shot_dir)
            except ImportError:
                print("playwright is not importable; run with --no-sheet or install it")
                return 1
            except Exception as exc:                       # noqa: BLE001
                print(f"could not render {path.name} at {geometry}: {exc}")
                return 1
            if shots:
                sheet = contact_sheet(shots, out_dir / f"sheet-{geometry}-"
                                      f"{'dark' if dark else 'light'}.html")
            results.append({"file": path.name, "geometry": geometry,
                            "size": GEOMETRIES[geometry], "pages": rows})
            if args.json:
                continue
            w, h = GEOMETRIES[geometry]
            print(f"\n{path.name} @ {geometry} ({w}x{h})")
            print(f"  {'page':8} {'centerpiece':22} {'of cell':>7}  {'empty band':>11}  "
                  f"{'cell fill':<34}aspect")
            for r in rows:
                a = r["aspect"]
                note = ""
                if a and a["ratio"] > 1.5:
                    note = (f"fig {a['figure']}:1 in cell {a['cell']}:1 — "
                            f"fills {a['fillsCellHeight']}% of cell height")
                elif a:
                    note = f"fig {a['figure']}:1 in cell {a['cell']}:1"
                over = f"  +{r['overflowPx']}px" if r['overflowPx'] > 1 else ""
                # This print sat one level out of the loop until 2.0.1, so the
                # table reported the last page 28 times over and every page-by-
                # page reading taken from it was of one page.
                print(f"  {r['id']:8} {str(r['centerpiece'] or '-'):22} "
                      f"{str(r['centerScale'] or '-'):>5}%  "
                      f"{str(r['emptyBandPct'])+'%':>11}  "
                      f"{' '.join(c['cls'][:4]+':'+str(c['fill'])+'%' for c in r['cells']):<34}{note}{over}")
            # Every block below reports and returns. The counts name pages so a
            # designer knows where to look; none of them is a threshold a page
            # must clear, because the fix for each is a design decision and a
            # number that can be satisfied without making the page better ends
            # the looking rather than directing it (SKILL.md rule 4).
            multi = [r for r in rows if r.get('colCount', 0) > 1]
            # 3px, not 8. A reader saw two tables 4px out of line and called it a
            # bug; the threshold was hiding exactly the case it was written for.
            bad_top = [r for r in multi if r['colTopSkewPx'] > 3]
            if bad_top:
                print(f"  COLUMN TOPS: {len(bad_top)} of {len(multi)} multi-column pages — "
                      "side-by-side cells do not start on one line: "
                      + ", ".join(f"{r['id']} {r['colTopSkewPx']}px"
                                  for r in sorted(bad_top, key=lambda r: -r['colTopSkewPx'])[:6]))
            elif multi:
                print(f"  column tops: all {len(multi)} multi-column pages start on one line")
            heavy = sorted((r for r in multi if r['colWeightRatio'] > 3),
                           key=lambda r: -r['colWeightRatio'])
            if heavy:
                print(f"  COLUMN WEIGHT: {len(heavy)} of {len(multi)} pages carry one column "
                      "far heavier than its neighbour: "
                      + ", ".join(f"{r['id']} {r['colWeightRatio']}:1" for r in heavy[:6]))
            elif multi:
                print(f"  column weight: no page exceeds 3:1 across {len(multi)} multi-column pages")

            flat = [r for r in rows if r['focalRatio'] < 1.35 and r['figLeadPct'] < 45]
            if flat:
                print(f"  FOCAL: {len(flat)} of {len(rows)} pages have no element larger than "
                      f"body copy and no dominant figure — nothing for the eye to enter on: "
                      + ", ".join(r['id'] for r in flat[:10])
                      + (f" (+{len(flat)-10} more)" if len(flat) > 10 else ""))
            else:
                print(f"  focal: every one of {len(rows)} pages has a focal element")

            capbad = [(r, c) for r in rows for c in r['caps']
                      if c['duplicated'] or c['words'] > 45]
            if capbad:
                print(f"  CAPTIONS: {len(capbad)} figure captions carry prose: "
                      + ", ".join(f"{r['id']} {c['words']}w"
                                  + (f", {c['duplicated']} sentence(s) repeated on the page"
                                     if c['duplicated'] else "")
                                  for r, c in capbad[:5]))
            else:
                ncap = sum(len(r['caps']) for r in rows)
                print(f"  captions: {ncap} carry prose under the figure number, none repeated")

            multi_t = [r for r in rows if len(r['tables']) > 1]
            if multi_t:
                print(f"  TWO TABLES: {len(multi_t)} pages carry more than one table — "
                      + ", ".join(f"{r['id']} ({len(r['tables'])})" for r in multi_t[:6])
                      + ". A grid claims its cells are comparable on the axis its header "
                        "names; two grids side by side claim nothing and cannot align.")
            else:
                print("  tables: no page carries more than one")
            prose_t = [(r, t) for r in rows for t in r['tables'] if t['digitPct'] <= 2]
            alltab = sum(len(r['tables']) for r in rows)
            if prose_t:
                print(f"  TABLES: {len(prose_t)} of {alltab} tables hold prose, not values "
                      f"(digit density <=2%): " + ", ".join(f"{r['id']}" for r, _ in prose_t[:10])
                      + (f" (+{len(prose_t)-10} more)" if len(prose_t) > 10 else ""))
            elif alltab:
                print(f"  tables: all {alltab} tables carry values")
            far = [r for r in rows if (r.get('capGapPx') or 0) > 20]
            if far:
                print(f"  CAPTION DETACHED: {len(far)} figures sit well above their "
                      "number and name — "
                      + ", ".join(f"{r['id']} {r['capGapPx']}px"
                                  for r in sorted(far, key=lambda r: -(r['capGapPx'] or 0))[:6]))
            else:
                ncap2 = sum(1 for r in rows if r.get('capGapPx') is not None)
                print(f"  caption: all {ncap2} captions sit against their drawing")
            echo = [r for r in rows if r.get('sourceEcho', 0)]
            if echo:
                print(f"  SOURCE TWICE: {len(echo)} pages state the same source under "
                      "the figure and again in the footer: "
                      + ", ".join(r['id'] for r in echo[:8]))
            else:
                print(f"  source: no page states the same source twice")
            ndrawn = sum(1 for r in rows if r['drawn'])
            print(f"  figures: {ndrawn} of {len(rows)} pages are built on a drawing "
                  f"rather than a grid or a block of prose")

            skew = [r for r in rows if r.get('frameSkewPx', 0) > 1
                    or r.get('sideMarginSkewPx', 0) > 2]
            if skew:
                print(f"  FRAME: {len(skew)} of {len(rows)} pages — the footer and the "
                      f"composition are not the same width, or the page is not centred: "
                      + ", ".join(f"{r['id']} skew {r['frameSkewPx']}px" for r in skew[:6]))
            else:
                print(f"  frame: footer and composition share one width and centre "
                      f"on all {len(rows)} pages")
            spill = [r for r in rows if r.get('spillPx', 0) > 1]
            if spill:
                print(f"  CONTENT SPILL: {len(spill)} of {len(rows)} pages run past the "
                      f"footer rule — "
                      + ", ".join(f"{r['id']} +{r['spillPx']}px ({r['deepestWho']})"
                                  for r in sorted(spill, key=lambda r: -r['spillPx'])[:8]))
            else:
                print(f"  content: all {len(rows)} pages stay above the footer rule")
            tall = [r for r in rows if r['overflowPx'] > 1]
            if tall:
                print(f"  PAGE HEIGHT: {len(tall)} of {len(rows)} pages exceed the "
                      f"{h}px page — " + ", ".join(f"{r['id']} +{r['overflowPx']}px" for r in tall[:8]))
            else:
                print(f"  page height: all {len(rows)} pages are exactly {h}px")
            if shots:
                print(f"  contact sheet: {sheet}")
                print("  Look at it. That is the check; the numbers only say where to look.")

    if not args.json and not args.no_aspect:
        for name in args.files:
            path = pathlib.Path(name).resolve()
            print(f"\n{path.name} — does a landscape page hold 16:9 in a window "
                  f"that is not 16:9?")
            try:
                for f in aspect_report(path.resolve().as_uri()):
                    if f["offAspect"]:
                        w = f["worst"]
                        print(f"  ASPECT: window {f['window']:>10} — "
                              f"{f['offAspect']} of {f['pages']} pages are not 16:9, "
                              f"worst {w['id']} at {w['w']}x{w['h']} ({w['aspect']}:1)")
                    else:
                        print(f"  aspect: window {f['window']:>10} — "
                              f"all {f['pages']} pages hold 16:9")
            except Exception as exc:            # no browser, or a load failure
                print(f"  aspect: skipped ({exc.__class__.__name__})")

    if args.json:
        print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
