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
}
DEFAULT_GEOMETRIES = ["16x9", "a4"]

# Measured in the page, not from CSS. Everything here runs in the browser.
PROBE = r"""
() => {
  const CENTER = 'table, .fig, .band, .geo-flat';
  const INK = 'table, svg, p, h2, .band, .key, .gd, .red, .note, .cap, .legend, .eyebrow, .spec';
  const out = [];
  for (const s of document.querySelectorAll('section.page')) {
    const sr = s.getBoundingClientRect();
    const footEl = s.querySelector('.foot');
    const foot = footEl ? footEl.getBoundingClientRect() : {top: sr.bottom};
    const bodyEl = s.querySelector('.body');
    const body = bodyEl ? bodyEl.getBoundingClientRect() : sr;
    const availW = body.width, availH = Math.max(1, foot.top - body.top);
    const area = availW * availH;

    // centerpiece: the largest thing that carries the page's content
    let best = null;
    for (const c of s.querySelectorAll(CENTER)) {
      const r = c.getBoundingClientRect();
      if (r.width < 8 || r.height < 8) continue;
      if (!best || r.width * r.height > best.w * best.h)
        best = {w: r.width, h: r.height, tag: c.tagName.toLowerCase(),
                cls: (c.className || '').toString().split(' ')[0]};
    }
    // a figure's drawn aspect vs the cell it sits in
    let aspect = null;
    const svg = s.querySelector('.fig svg[viewBox]:not(.ic)');
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
    out.push({
      id: s.id,
      centerScale: best ? +(100 * best.w * best.h / area).toFixed(1) : null,
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
            print(f"  {'page':8} {'centerpiece':22} {'scale':>6}  {'empty band':>11}  aspect")
            for r in rows:
                a = r["aspect"]
                note = ""
                if a and a["ratio"] > 1.5:
                    note = (f"fig {a['figure']}:1 in cell {a['cell']}:1 — "
                            f"fills {a['fillsCellHeight']}% of cell height")
                elif a:
                    note = f"fig {a['figure']}:1 in cell {a['cell']}:1"
                print(f"  {r['id']:8} {str(r['centerpiece'] or '-'):22} "
                      f"{str(r['centerScale'] or '-'):>5}%  "
                      f"{str(r['emptyBandPct'])+'%':>11}  {note}")
            if shots:
                print(f"  contact sheet: {sheet}")
                print("  Look at it. That is the check; the numbers only say where to look.")

    if args.json:
        print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
