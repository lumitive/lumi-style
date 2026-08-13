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

Output lands next to the input file unless --out names a directory. That is NOT
the skill's output-directory default and is not meant to be: since 0.1.385 a new
document is written to `Documents/LUMI-Style/`, while an export belongs beside
the document it was made from, so a deliverable's HTML and PDF travel together.
Do not "fix" this to resolve the default — design-rules.md §7 says both halves.

Dependency posture matches inspect_layout.py: optional local tool, never in CI
beyond a syntax check. `pip install playwright && playwright install chromium`.
Exit is non-zero only on mechanical failure — a missing browser, an unreadable
file, a document with no pages — never as a design judgement (0.1.350: a tool
that cannot measure must say so, not reassure).

    python3 scripts/ops/export_pdf.py deck.html                    # PDF, landscape
    python3 scripts/ops/export_pdf.py deck.html --geometry portrait
    python3 scripts/ops/export_pdf.py deck.html --png --scale 3    # 4K page rasters
"""
from __future__ import annotations

import argparse
import pathlib

# The genre vocabulary is imported from its one home, never copied. This tool
# additionally knows `consulting`, which has no check_prose flag (a recorded
# no-change) but does have a primary geometry: 16:9, like sales.
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
from check_prose import GENRES  # noqa: E402

# One stage per geometry, the same fixed boxes the tokens declare.
STAGES = {"landscape": (1280, 720), "portrait": (794, 1123)}
SCALE_FLOOR = 2.0    # 2x the stage: 2K on the landscape stage. A floor, not a target.
SCALE_DEFAULT = 3.0  # 3x: 3840x2160 on the landscape stage — 4K, the default.

# The same page selector inspect_layout.py discovers pages with. Copied, not
# imported: importing the inspector to read one string would run the module,
# and the two tools agreeing on what a page is matters more than sharing code.
PAGE_SELECTOR = "section.page"


def export(path: pathlib.Path, geometry: str, scale: float, png: bool,
           out_dir: pathlib.Path | None, seen: set) -> int:
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

    # Two files with one stem exporting into one directory silently clobber
    # each other while the tool prints ok twice — a genuine loss with no
    # re-run to blame it on, so it fails instead.
    key = (out_dir.resolve(), stem, geometry)
    if key in seen:
        print(f"FAIL  {path}: another input already exported as "
              f"{stem}-{geometry}* into {out_dir}; name an --out per file")
        return 1
    seen.add(key)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page(viewport={"width": w, "height": h},
                                    device_scale_factor=scale if png else 1)
            # The settle discipline inspect_layout.py was rewritten for
            # (see open_page there): this tool DELIVERS the artifact, so a
            # half-built page is worse here than there. A page whose own
            # script throws is a failed export, not a quiet one; and with
            # `font-display: swap` on the embedded face, capturing before
            # document.fonts settles is guaranteed to ship fallback metrics.
            page_errors = []
            page.on("pageerror", lambda e: page_errors.append(str(e)))
            page.goto(path.resolve().as_uri(), wait_until="load")
            try:
                page.wait_for_function(
                    "() => document.fonts && document.fonts.status === 'loaded'",
                    timeout=5000)
            except Exception:
                print(f"FAIL  {path}: webfonts did not finish loading in 5s; "
                      f"the export would ship a fallback face")
                return 1
            if page_errors:
                print(f"FAIL  {path}: the document's own script threw during "
                      f"build — {page_errors[0][:120]}")
                return 1
            # PIN EVERY GLOBE BEFORE CAPTURING. A rotating figure makes an
            # export a screenshot of whatever moment the browser reached, so
            # two runs of this tool on one unchanged document produced two
            # different PDFs. Each globe carries the longitude its document
            # wants exported; a globe that names none is pinned where it
            # stands, which still stops the clock.
            pinned = page.evaluate("""() => {
              const gs = window.lumiGlobes || [];
              for (const g of gs) {
                const v = Number(g.container.dataset.globePrintLon0);
                g.pin(Number.isFinite(v) ? v : undefined);
              }
              return gs.length;
            }""")
            if pinned:
                print(f"      pinned {pinned} globe(s) for a reproducible frame")

            sections = page.query_selector_all(PAGE_SELECTOR)
            if not sections:
                print(f"FAIL  {path}: no {PAGE_SELECTOR!r} sections; nothing to export")
                return 1

            if png:
                digits = max(2, len(str(len(sections))))
                for i, s in enumerate(sections, 1):
                    s.scroll_into_view_if_needed()
                    target = out_dir / f"{stem}-{geometry}-p{i:0{digits}d}.png"
                    s.screenshot(path=str(target))
                # A deck that shrank since the last export leaves higher-numbered
                # pages from the old edition beside the fresh ones; a directory
                # shipped wholesale then ships dead pages. Say so.
                stale = [q for q in sorted(out_dir.glob(f"{stem}-{geometry}-p*.png"))
                         if q.stem[len(f"{stem}-{geometry}-p"):].isdigit()
                         and int(q.stem[len(f"{stem}-{geometry}-p"):]) > len(sections)]
                if stale:
                    print(f"WARN  {len(stale)} stale page files from an earlier, "
                          f"longer export remain: {stale[0].name} … — delete them "
                          f"before shipping the directory")
                print(f"ok    {len(sections)} pages at {scale:g}x "
                      f"({int(w * scale)}x{int(h * scale)} px) -> {out_dir}")
            else:
                target = out_dir / f"{stem}-{geometry}.pdf"
                page.pdf(path=str(target), width=f"{w}px", height=f"{h}px",
                         print_background=True, prefer_css_page_size=False,
                         margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
                # page.pdf paginates by the document's own @media print rules,
                # not by this tool's section count; a deck missing its print
                # break rules splits mid-section. Reconcile the two counts.
                raw = pathlib.Path(target).read_bytes()
                # "/Type /Pages" (the tree node) contains "/Type /Page", so
                # subtract it; a compressed PDF with neither literal skips the
                # reconciliation rather than warning falsely.
                pdf_pages = raw.count(b"/Type /Page") - raw.count(b"/Type /Pages")
                if pdf_pages and pdf_pages != len(sections):
                    print(f"WARN  {target.name} paginated to ~{pdf_pages} PDF "
                          f"pages against {len(sections)} sections — check the "
                          f"document's @media print break rules")
                blends = raw.count(b"/BM") - raw.count(b"/BM /Normal")
                if blends > 0:
                    print(f"WARN  {target.name} carries {blends} blend-mode entries; "
                          f"one blended element makes the reader composite a whole "
                          f"page, measured at 10x render time on a 31-page deck")
                print(f"ok    {len(sections)} pages -> {target} "
                      f"(vector; the stage is the page size)")
        finally:
            browser.close()
    return 0


def main(argv):
    ap = argparse.ArgumentParser(add_help=True, description=__doc__.split("\n")[0])
    ap.add_argument("files", nargs="+")
    ap.add_argument("--geometry", choices=sorted(STAGES), default=None,
                    help="which fixed stage to render; defaults to the genre's "
                         "primary (design-rules §7)")
    ap.add_argument("--genre", choices=list(GENRES),
                    default="sales",
                    help="picks the default geometry: training leads portrait "
                         "(printed, annotated, bound), everything else leads "
                         "landscape. --geometry overrides.")
    ap.add_argument("--png", action="store_true",
                    help="page rasters instead of a PDF")
    ap.add_argument("--scale", type=float, default=SCALE_DEFAULT,
                    help=f"device pixels per CSS pixel for --png; default "
                         f"{SCALE_DEFAULT:g} (4K on the landscape stage), "
                         f"floor {SCALE_FLOOR:g} (2K)")
    ap.add_argument("--out", default=None,
                    help="output directory; default is the input file's own")
    args = ap.parse_args(argv)

    # The floor executed in code, not advised in prose: a 1x export looks
    # fine on the machine that made it and soft on every dense display. It
    # binds rasters only — a PDF is vector and has no scale to be under.
    if args.png and args.scale < SCALE_FLOOR:
        ap.error(f"--scale {args.scale:g} is below the floor of {SCALE_FLOOR:g} "
                 f"(2x the stage, 2K); the default is {SCALE_DEFAULT:g} (4K)")

    # The document's own declaration decides, because a deliverable is designed
    # for ONE geometry (design-rules §7). Exporting a landscape deck at A4 is
    # how a portrait PDF came back with dead half-pages, starved figures and a
    # wrapped footer on all 31 pages: nothing was broken, the composition had
    # simply never been designed. So a contradiction is a refusal, not a warning.
    def declared_geometry(path):
        try:
            head = path.read_text(encoding="utf-8", errors="replace")[:400000]
        except OSError:
            return None
        # The real <body> tag, not the stylesheet's selectors and not the
        # worked example inside its comments. Strip style blocks and comments
        # first; what is left is markup. (inspect_layout.py reads it the same
        # way, and both got this wrong twice before stripping.)
        head = re.sub(r"<style\b.*?</style>|<!--.*?-->", " ", head, flags=re.S | re.I)
        m = re.search(r'<body\b[^>]*\bdata-geometry=["\'](\w+)["\']', head)
        return m.group(1) if m else None

    geometry = args.geometry or ("portrait" if args.genre == "training" else "landscape")

    rc = 0
    seen: set = set()
    for name in args.files:
        path = pathlib.Path(name)
        if not path.exists():
            print(f"FAIL  {name}: no such file")
            rc = 1
            continue
        # One bad file must not abort the batch: a zero-size section or a
        # mid-render browser death FAILs this file and the loop continues,
        # which is the contract the per-file rc already promised.
        decl = declared_geometry(path)
        if decl and decl != geometry:
            if args.geometry:
                print(f"FAIL  {name}: declares data-geometry=\"{decl}\" and you asked "
                      f"for {geometry}. A deliverable is designed for one geometry; "
                      f"exporting the other renders a composition nobody designed. "
                      f"Build a {geometry} edition, or export {decl}.")
                rc = 1
                continue
            geometry = decl        # no flag given: follow the document
        try:
            rc = max(rc, export(path, geometry, args.scale, args.png,
                                pathlib.Path(args.out) if args.out else None, seen))
        except Exception as exc:                             # noqa: BLE001
            print(f"FAIL  {name}: {type(exc).__name__}: {str(exc)[:160]}")
            rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
