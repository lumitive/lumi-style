#!/usr/bin/env python3
"""Export a deliverable to PDF and high-resolution page rasters.

The page geometries are fixed stages (design-rules.md §7): 1280x720 landscape,
794x1123 A4 portrait. This tool renders at those stages and nowhere else:

  * **PDF** — one PDF page per `.page` section at the stage size. Vector, so
    there is no resolution to pick; the document's own `@media print` rules
    apply and `print_background` keeps the ground and the fields.
  * **Rasters** (`--png`) — one PNG per page at `--scale` device pixels per CSS
    pixel. **Default 3 — a 1280x720 stage exports at 3840x2160, which is 4K.
    The floor is 2 (2K), and the script refuses a smaller scale** rather than
    quietly producing a soft image; a prescribed value carries the floor below
    which it stops working (CLAUDE.md rule 6).

The scale is an export multiplier only. It never touches the CSS stage, because
every clamp() in tokens/ is written against the stage; the HTML edition needs no
scale at all — the zoom stage adapts to the reader's window and pixel density
natively.

Output lands next to the input file unless --out names a directory, matching the
skill's output-directory default.

Dependency posture matches inspect_layout.py: optional local tool, never in CI
beyond a syntax check. `pip install playwright && playwright install chromium`.
Exit is non-zero only on mechanical failure — a missing browser, an unreadable
file, a document with no pages — never as a design judgement (0.1.350: a tool
that cannot measure must say so, not reassure).

    python3 scripts/export_pdf.py deck.html                    # PDF, landscape
    python3 scripts/export_pdf.py deck.html --geometry portrait
    python3 scripts/export_pdf.py deck.html --png --scale 3    # 4K page rasters
"""
from __future__ import annotations

import argparse
import pathlib
import sys

# One stage per geometry, the same fixed boxes the tokens declare.
STAGES = {"landscape": (1280, 720), "portrait": (794, 1123)}
SCALE_FLOOR = 2.0    # 2x the stage: 2K on the landscape stage. A floor, not a target.
SCALE_DEFAULT = 3.0  # 3x: 3840x2160 on the landscape stage — 4K, the default.

# The same page selector inspect_layout.py discovers pages with. Copied, not
# imported: importing the inspector to read one string would run the module,
# and the two tools agreeing on what a page is matters more than sharing code.
PAGE_SELECTOR = "section.page"


def export(path: pathlib.Path, geometry: str, scale: float, png: bool,
           out_dir: pathlib.Path | None) -> int:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("FAIL  playwright is not installed; this is a local tool — "
              "pip install playwright && playwright install chromium")
        return 1

    w, h = STAGES[geometry]
    out_dir = out_dir or path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = path.stem

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": w, "height": h},
                                device_scale_factor=scale if png else 1)
        page.goto(path.resolve().as_uri())
        page.wait_for_timeout(300)
        sections = page.query_selector_all(PAGE_SELECTOR)
        if not sections:
            print(f"FAIL  {path}: no {PAGE_SELECTOR!r} sections; nothing to export")
            browser.close()
            return 1

        written = []
        if png:
            digits = max(2, len(str(len(sections))))
            for i, s in enumerate(sections, 1):
                s.scroll_into_view_if_needed()
                target = out_dir / f"{stem}-{geometry}-p{i:0{digits}d}.png"
                s.screenshot(path=str(target))
                written.append(target)
            print(f"ok    {len(written)} pages at {scale:g}x "
                  f"({int(w * scale)}x{int(h * scale)} px) -> {out_dir}")
        else:
            target = out_dir / f"{stem}-{geometry}.pdf"
            page.pdf(path=str(target), width=f"{w}px", height=f"{h}px",
                     print_background=True, prefer_css_page_size=False,
                     margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
            written.append(target)
            print(f"ok    {len(sections)} pages -> {target} "
                  f"(vector; the stage is the page size)")
        browser.close()
    return 0


def main(argv):
    ap = argparse.ArgumentParser(add_help=True, description=__doc__.split("\n")[0])
    ap.add_argument("files", nargs="+")
    ap.add_argument("--geometry", choices=sorted(STAGES), default="landscape",
                    help="which fixed stage to render; the genre picks the "
                         "primary (design-rules §7): training leads portrait, "
                         "everything else leads landscape")
    ap.add_argument("--png", action="store_true",
                    help="page rasters instead of a PDF")
    ap.add_argument("--scale", type=float, default=SCALE_DEFAULT,
                    help=f"device pixels per CSS pixel for --png; default "
                         f"{SCALE_DEFAULT:g} (4K on the landscape stage), "
                         f"floor {SCALE_FLOOR:g} (2K)")
    ap.add_argument("--out", default=None,
                    help="output directory; default is the input file's own")
    args = ap.parse_args(argv)

    if args.scale < SCALE_FLOOR:
        # The floor executed in code, not advised in prose: a 1x export looks
        # fine on the machine that made it and soft on every dense display.
        ap.error(f"--scale {args.scale:g} is below the floor of {SCALE_FLOOR:g} "
                 f"(2x the stage, 2K); the default is {SCALE_DEFAULT:g} (4K)")

    rc = 0
    for name in args.files:
        path = pathlib.Path(name)
        if not path.exists():
            print(f"FAIL  {name}: no such file")
            rc = 1
            continue
        rc = max(rc, export(path, args.geometry, args.scale, args.png,
                            pathlib.Path(args.out) if args.out else None))
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
