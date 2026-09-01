#!/usr/bin/env python3
"""Export a deliverable to PowerPoint, one full-bleed page raster per slide.

**Bitmap, never reflow, and that is the decision rather than a shortcut.** A
LUMI page is a fixed stage composed to the pixel: its layouts are CSS grids,
its figures are SVG, its type is a clamp() written against 1280x720. Rebuilding
that as PowerPoint shapes would make the export a SECOND surface to debug — a
title that wraps differently, a figure that letterboxes, a footer that lands on
two baselines — and every defect found there would be a defect in a document
the checkers had already passed. One raster per slide is exact by construction:
what the reader opens is what `inspect_layout` measured.

What that costs is honest and worth saying: the text is not selectable and not
editable. A deck that must be edited in PowerPoint is a deck to build in
PowerPoint.

    python3 scripts/ops/export_pptx.py deck.html
    python3 scripts/ops/export_pptx.py deck.html --scale 2      # smaller file

The slide is the document's own stage: 13.333 x 7.5 inches for landscape,
A4 for portrait, so the image fills the slide edge to edge with no letterbox
and no crop.

Dependency posture matches export_pdf.py: the rasters come from that tool, so
this needs the same local Playwright and is never in CI beyond a syntax check.
The PPTX itself is written with the standard library — a .pptx is a ZIP of XML.

Exit is non-zero only on mechanical failure: a page that produced no raster, an
unreadable file, a document with no pages. A missing slide is a FAILURE and
never a shorter deck, because a deck quietly missing page 7 is the export a
reader presents from.
"""
from __future__ import annotations

import argparse
import pathlib

# --- scripts path bootstrap (canonical; the bootstrap guard enforces this) ---
import pathlib as _bs_pathlib  # noqa: E402
import re
import shutil
import sys
import sys as _bs_sys  # noqa: E402
import tempfile
import zipfile

_SCRIPTS_ROOT = next(p for p in _bs_pathlib.Path(__file__).resolve().parents
                     if p.name == "scripts")
for _sub in ("lib", "render", "check", "build", "ops", ""):
    _p = str(_SCRIPTS_ROOT / _sub) if _sub else str(_SCRIPTS_ROOT)
    if _p not in _bs_sys.path:
        _bs_sys.path.append(_p)
del _bs_pathlib, _bs_sys, _SCRIPTS_ROOT, _sub, _p

import export_pdf  # noqa: E402

EMU_PER_INCH = 914400
# The stages, in slide units. Landscape is PowerPoint's own 16:9 widescreen so
# the deck opens at the size every other 16:9 deck opens at; portrait is A4,
# which is the stage `tokens/` composes the printed genre against.
SLIDE = {"landscape": (round(13.3333 * EMU_PER_INCH), round(7.5 * EMU_PER_INCH)),
         "portrait": (7560000, 10692000)}

# A file this size stops being something anyone emails. Reported, never a
# refusal: the operator may well want the 4K edition for a projector, and a
# tool that refuses the thing it was asked for teaches people to work around it.
MAIL_CEILING_MB = 20.0

CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Default Extension="png" ContentType="image/png"/>
<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>
<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>
<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
{slides}</Types>"""

ROOT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
</Relationships>"""

PRESENTATION = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
<p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst>
<p:sldIdLst>{ids}</p:sldIdLst>
<p:sldSz cx="{cx}" cy="{cy}"/><p:notesSz cx="{cy}" cy="{cx}"/>
</p:presentation>"""

SLIDE_MASTER = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
<p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
</p:spTree></p:cSld><p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>
<p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst>
</p:sldMaster>"""

SLIDE_MASTER_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/>
</Relationships>"""

SLIDE_LAYOUT = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="blank" preserve="1">
<p:cSld name="Blank"><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sldLayout>"""

SLIDE_LAYOUT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/>
</Relationships>"""

# A theme is required by the format even though every slide here is a picture.
# The colours are LUMI's ink, canvas and accent so that anything a recipient
# adds to the deck lands in the palette rather than in Office blue.
THEME = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="LUMI">
<a:themeElements>
<a:clrScheme name="LUMI"><a:dk1><a:srgbClr val="2B2E33"/></a:dk1><a:lt1><a:srgbClr val="FFFFFF"/></a:lt1>
<a:dk2><a:srgbClr val="1D1D1F"/></a:dk2><a:lt2><a:srgbClr val="FAFAFA"/></a:lt2>
<a:accent1><a:srgbClr val="48633E"/></a:accent1><a:accent2><a:srgbClr val="B8FF00"/></a:accent2>
<a:accent3><a:srgbClr val="C8102E"/></a:accent3><a:accent4><a:srgbClr val="9C5D06"/></a:accent4>
<a:accent5><a:srgbClr val="7A6C52"/></a:accent5><a:accent6><a:srgbClr val="889A82"/></a:accent6>
<a:hlink><a:srgbClr val="48633E"/></a:hlink><a:folHlink><a:srgbClr val="7A6C52"/></a:folHlink></a:clrScheme>
<a:fontScheme name="LUMI"><a:majorFont><a:latin typeface="Helvetica Neue"/><a:ea typeface=""/><a:cs typeface=""/></a:majorFont>
<a:minorFont><a:latin typeface="Helvetica Neue"/><a:ea typeface=""/><a:cs typeface=""/></a:minorFont></a:fontScheme>
<a:fmtScheme name="LUMI">
<a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst>
<a:lnStyleLst><a:ln w="6350"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln><a:ln w="12700"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln><a:ln w="19050"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst>
<a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle><a:effectStyle><a:effectLst/></a:effectStyle><a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst>
<a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst>
</a:fmtScheme></a:themeElements></a:theme>"""

PRESENTATION_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>
{rels}<Relationship Id="rIdTheme" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="theme/theme1.xml"/>
</Relationships>"""

SLIDE_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
<p:cSld><p:spTree>
<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
<p:pic>
<p:nvPicPr><p:cNvPr id="2" name="Page {n}" descr="{alt}"/><p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr/></p:nvPicPr>
<p:blipFill><a:blip r:embed="rId1"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>
<p:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr>
</p:pic></p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>"""

SLIDE_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/image{n}.png"/>
</Relationships>"""


def build(pngs: list[pathlib.Path], out: pathlib.Path, geometry: str) -> None:
    """Write `pngs` into a .pptx at `out`, one full-bleed slide each."""
    cx, cy = SLIDE[geometry]
    overrides = "".join(
        f'<Override PartName="/ppt/slides/slide{i}.xml" '
        f'ContentType="application/vnd.openxmlformats-officedocument.'
        f'presentationml.slide+xml"/>\n' for i in range(1, len(pngs) + 1))
    ids = "".join(f'<p:sldId id="{255 + i}" r:id="rId{i + 1}"/>'
                  for i in range(1, len(pngs) + 1))
    rels = "".join(
        f'<Relationship Id="rId{i + 1}" Type="http://schemas.openxmlformats.org'
        f'/officeDocument/2006/relationships/slide" '
        f'Target="slides/slide{i}.xml"/>\n' for i in range(1, len(pngs) + 1))

    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml",
                   CONTENT_TYPES.format(slides=overrides))
        z.writestr("_rels/.rels", ROOT_RELS)
        z.writestr("ppt/presentation.xml",
                   PRESENTATION.format(ids=ids, cx=cx, cy=cy))
        z.writestr("ppt/_rels/presentation.xml.rels",
                   PRESENTATION_RELS.format(rels=rels))
        z.writestr("ppt/slideMasters/slideMaster1.xml", SLIDE_MASTER)
        z.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels",
                   SLIDE_MASTER_RELS)
        z.writestr("ppt/slideLayouts/slideLayout1.xml", SLIDE_LAYOUT)
        z.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels",
                   SLIDE_LAYOUT_RELS)
        z.writestr("ppt/theme/theme1.xml", THEME)
        for i, png in enumerate(pngs, 1):
            z.writestr(f"ppt/slides/slide{i}.xml",
                       SLIDE_XML.format(n=i, cx=cx, cy=cy,
                                        alt=f"Page {i} of the deliverable"))
            z.writestr(f"ppt/slides/_rels/slide{i}.xml.rels",
                       SLIDE_RELS.format(n=i))
            z.writestr(f"ppt/media/image{i}.png", png.read_bytes())


def page_count(path: pathlib.Path) -> int:
    """-> how many pages the DOCUMENT declares, read from its markup.

    The count comes from the source rather than from the rasters, because the
    two disagreeing is exactly the failure this tool must not ship quietly: a
    slide missing from the middle of a deck is the export a reader presents
    from, and a shorter deck looks like a shorter deck.
    """
    raw = path.read_text(encoding="utf-8", errors="replace")
    # `section.page` is what both the exporter and the inspector call a page,
    # so this reads exactly that tag from the source. Style blocks and comments
    # go first: the stylesheet is full of `.page` selectors and the scaffold's
    # comments quote its own markup, and counting either would make this
    # disagree with the browser in the direction that reports a MISSING slide
    # on a complete deck.
    body = re.sub(r"<style\b.*?</style>|<!--.*?-->", " ", raw, flags=re.S | re.I)
    return len(re.findall(r'<section\b[^>]*\bclass=["\'][^"\']*\bpage\b',
                          body))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("files", nargs="+")
    ap.add_argument("--geometry", choices=sorted(SLIDE),
                    help="which fixed stage; defaults to the document's own "
                         "data-geometry declaration")
    ap.add_argument("--scale", type=float, default=2.0,
                    help="device pixels per CSS pixel for the page rasters. "
                         "Default 2 rather than export_pdf's 3: a slide is "
                         "displayed at the projector's resolution and every "
                         "page rides inside one file, so 3x buys nothing a "
                         "viewer can see and triples what a recipient "
                         "downloads. Floor is export_pdf's.")
    ap.add_argument("--out", help="output directory; default is beside the "
                                  "input file, like the PDF")
    a = ap.parse_args(argv)

    rc = 0
    for name in a.files:
        path = pathlib.Path(name)
        if not path.exists():
            print(f"FAIL  {name}: no such file")
            rc = 1
            continue
        declared = None
        raw = path.read_text(encoding="utf-8", errors="replace")[:400000]
        head = re.sub(r"<style\b.*?</style>|<!--.*?-->", " ", raw,
                      flags=re.S | re.I)
        m = re.search(r'<body\b[^>]*\bdata-geometry=["\'](\w+)["\']', head)
        if m:
            declared = m.group(1)
        geometry = a.geometry or declared or "landscape"
        if declared and a.geometry and declared != a.geometry:
            # export_pdf's refusal, for export_pdf's reason: a deliverable is
            # designed for ONE geometry, and exporting the other presents a
            # composition nobody designed.
            print(f"FAIL  {name}: declares data-geometry=\"{declared}\" and "
                  f"you asked for {a.geometry}. Build a {a.geometry} edition, "
                  f"or export {declared}.")
            rc = 1
            continue

        want = page_count(path)
        if not want:
            print(f"FAIL  {name}: no pages; nothing to export")
            rc = 1
            continue

        tmp = pathlib.Path(tempfile.mkdtemp(prefix="lumi-pptx-"))
        try:
            if export_pdf.export(path, geometry, a.scale, True, tmp, set()):
                print(f"FAIL  {name}: the page rasters could not be made")
                rc = 1
                continue
            pngs = sorted(tmp.glob("*.png"))
            if len(pngs) != want:
                # HARD STOP. A deck quietly missing page 7 is the export a
                # reader presents from, and nothing downstream can tell a
                # thirteen-slide deck built from thirteen pages from one built
                # from twelve.
                print(f"FAIL  {name}: the document declares {want} pages and "
                      f"{len(pngs)} raster(s) came back. A slide missing from "
                      f"the middle is not a shorter deck, it is a wrong one.")
                rc = 1
                continue
            out_dir = pathlib.Path(a.out) if a.out else path.parent
            target = out_dir / f"{path.stem}-{geometry}.pptx"
            build(pngs, target, geometry)
            mb = target.stat().st_size / 1_000_000
            print(f"ok    {len(pngs)} slides at {a.scale:g}x -> {target} "
                  f"({mb:.1f} MB)")
            if mb > MAIL_CEILING_MB:
                print(f"note  {mb:.1f} MB is past what most mail systems "
                      f"accept ({MAIL_CEILING_MB:g} MB). --scale 2 is the "
                      f"default already; below it the slide is soft on a "
                      f"projector. Send a link, or send the PDF.")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    return rc


if __name__ == "__main__":
    sys.exit(main())
