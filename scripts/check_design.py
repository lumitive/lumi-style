#!/usr/bin/env python3
"""Measure the design metrics from references/eval-rubric.md on a deliverable.

M1-M11 made the prose half of this skill checkable. The design half stayed a
reading task, and a reader found seven defects in a deck that passed every prose
metric. Four of them were arithmetic:

    D1  contrast      every text/background pair clears the floor
    D2  type floor    no text below the documented minimum size
    D3  callouts      tier-1 callout budget, per page and per document
    D4  palette       no literal colour outside the token block
    D5  figure parity shape-vocabulary spread across figures (reported)
    D6  footer        every page carries a source line and "N / total"
    D8  support line  every content page has one under its title
    D9  layout spread  which layouts a deck uses (reported)
    D10 label icons   figure nodes and row-heads carrying an icon (reported)
    D16 visual presence  content pages carrying no visual block (reported)
    D17 export weight    blend modes, filters and vector nodes (reported)

    D12 commercial footer  handling terms and origin on every page (**gates**)
    D14 placeholders       slots the author left for themselves (**gates**)
    D15 footer path        no repository path reaches a footer (**gates**)

**Nothing here gates except D12, D14 and D15.** Every other number is a diagnostic for a
designer to read, and the exit code is 0 unless a file could not be measured at
all. SKILL.md rule 4 is the reason: a page is done when a human reads it as
intentional, and a metric that can be satisfied without improving the page ends
the looking instead of directing it. D7, an 82% page-fill floor, was withdrawn in
0.1.340 for exactly that — it was satisfied by stretching table rows while four
diagrams rendered at 40% of their cell. For page geometry and centerpiece scale
use scripts/inspect_layout.py.

**D12 and D14 are different in kind, which is why they are the exceptions.**
Neither is a judgement about whether a page is well made. D12 is a commercial
requirement on the artifact, like a contract term: pages travel alone — a slide
is screenshotted out of a deck and forwarded without the cover — so terms that
live only on page one do not travel with the page. D14 asks whether the document
is *finished*, which is decidable in a way that "is this page intentional" is
not. A design metric that gates is a mistake; a commercial one that does not is a
different mistake.

    python3 scripts/check_design.py deck.html [more files ...]
    python3 scripts/check_design.py --json deck.html

Standard library only, like the rest of scripts/.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# TYPE_FLOOR_PX / SOURCE_FLOOR_PX lived here until 0.1.352, defined and never
# read — dead since 0.1.340 withdrew the type floor they encoded. A constant that
# names a withdrawn rule is a trap: the next person to need a type threshold
# finds one already declared and wires it up, restoring a rule nobody re-argued.
# D2 reports the small end of the scale and grades nothing.
CONTRAST_FLOOR = 4.5
CONTRAST_FLOOR_LARGE = 3.0
LARGE_TEXT_PX = 24.0
TIER1_PER_PAGE = 1
TIER1_PAGE_SHARE = 33.0     # percent of a deck's pages that may carry one
LAYOUT_MAX_SHARE = 40.0     # percent of a deck's pages one layout may carry
LAYOUT_MIN_DISTINCT = 5     # in a deck of this many pages or more
LAYOUT_MIN_PAGES = 15

# The layouts shipped in tokens/lumi-layouts.css. A .body class outside this set
# is either a typo or a layout invented in the document, and both defeat D9.
LAYOUTS = {
    "stack", "hero-band", "band-hero", "thirds-v",
    "split", "split-wide", "split-narrow", "columns-2", "columns-3", "columns-4",
    "rail", "quad", "sidebar-notes", "full-bleed", "diagonal-flow", "cover-grid",
}

# Class names the house style uses for a tier-1 callout (tinted + border + edge).
TIER1_CLASSES = ("key", "red")


class Unmeasurable(Exception):
    """The file yielded nothing to measure. Never silently a pass."""


# ── colour ────────────────────────────────────────────────────────────────────
def _lin(c):
    c /= 255
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def _luma(rgb):
    r, g, b = (_lin(x) for x in rgb[:3])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(fg, bg):
    a, b = _luma(fg), _luma(bg)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


def parse_color(value):
    """-> (r, g, b, alpha) or None. Handles #rgb, #rrggbb, rgb(), rgba()."""
    v = value.strip()
    m = re.fullmatch(r"#([0-9A-Fa-f]{3})", v)
    if m:
        return tuple(int(c * 2, 16) for c in m.group(1)) + (1.0,)
    m = re.fullmatch(r"#([0-9A-Fa-f]{6})", v)
    if m:
        h = m.group(1)
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (1.0,)
    m = re.fullmatch(r"rgba?\(([^)]+)\)", v)
    if m:
        parts = [p.strip() for p in m.group(1).replace("/", ",").split(",")]
        try:
            r, g, b = (float(p) for p in parts[:3])
        except ValueError:
            return None
        a = float(parts[3]) if len(parts) > 3 else 1.0
        return (r, g, b, a)
    return None


def over(fg, bg):
    """Composite an rgba foreground onto an opaque background."""
    a = fg[3]
    return tuple(fg[i] * a + bg[i] * (1 - a) for i in range(3))


# ── extraction ────────────────────────────────────────────────────────────────
BLOCK_RE = re.compile(r"([^{}]+)\{([^{}]*)\}")


def css_of(raw):
    css = "\n".join(m.group(1) for m in re.finditer(r"<style[^>]*>(.*?)</style>",
                                                    raw, re.S | re.I))
    # Comments must go before the block scan. A banner comment above :root ends up
    # inside the captured selector, ":root" then never matches exactly, and the
    # token block is treated as ordinary CSS: the file reads as unmeasurable and
    # its own palette definitions get reported as stray literals.
    return re.sub(r"/\*.*?\*/", " ", css, flags=re.S)


def token_blocks(css):
    """The :root and body.dark declaration blocks: the only place a literal
    colour is allowed to appear."""
    out = {}
    for sel, body in BLOCK_RE.findall(css):
        s = sel.strip()
        if s == ":root":
            out["light"] = body
        elif re.fullmatch(r"body\.dark|:root\[data-theme=[\"']dark[\"']\]", s):
            out["dark"] = body
    return out


def resolve(css, palette):
    """Custom properties for one palette, dark inheriting from :root."""
    blocks = token_blocks(css)
    vars_ = {}
    for key in ("light", palette):
        for m in re.finditer(r"--([\w-]+)\s*:\s*([^;]+);", blocks.get(key, "")):
            vars_[m.group(1)] = m.group(2).strip()

    def deref(value, depth=0):
        if depth > 8:
            return value
        m = re.fullmatch(r"var\(\s*--([\w-]+)\s*(?:,[^)]*)?\)", value.strip())
        if m:
            return deref(vars_.get(m.group(1), ""), depth + 1)
        return value

    return {k: deref(v) for k, v in vars_.items()}, vars_


def rules(css):
    """[(selector, {prop: value})] for every non-token block."""
    out = []
    for sel, body in BLOCK_RE.findall(css):
        s = " ".join(sel.split())
        if s == ":root" or s.startswith("@") or re.fullmatch(
                r"body\.dark|:root\[data-theme=[\"']dark[\"']\]", s):
            continue
        props = {m.group(1).strip(): m.group(2).strip()
                 for m in re.finditer(r"([\w-]+)\s*:\s*([^;]+)", body)}
        if props:
            out.append((s, props))
    return out


def px(value):
    m = re.search(r"(-?\d*\.?\d+)px", value or "")
    return float(m.group(1)) if m else None


# ── metrics ───────────────────────────────────────────────────────────────────
def over_bg(surface, bg):
    """A wash is usually translucent. Composite it onto the canvas before using
    it as a surface, or a 14%-alpha tint is graded as if it were opaque and
    every chip on it reports 1.0:1."""
    if surface is None:
        return bg
    if len(surface) > 3 and surface[3] < 1.0:
        a = surface[3]
        return tuple(round(surface[i] * a + bg[i] * (1 - a)) for i in range(3)) + (1.0,)
    return surface


def d1_contrast(css, resolved, palette):
    """Every declared text colour, against the surface its selector sits on."""
    bg = parse_color(resolved.get("bg", "#FFFFFF")) or (255, 255, 255, 1.0)
    card = parse_color(resolved.get("card-bg", resolved.get("bg", "#FFFFFF"))) or bg
    # Painted surfaces, discovered rather than assumed: any selector that sets a
    # background to a palette token declares a surface, and text scoped under it
    # is graded against that surface. Found by reading the CSS, so a deck that
    # paints a panel a new colour is measured correctly without editing this.
    panels = {}
    for sel, props in rules(css):
        bgv = (props.get("background") or props.get("background-color") or "").strip()
        m = re.fullmatch(r"var\(\s*--([\w-]+)\s*(?:,[^)]*)?\)", bgv)
        if not m or m.group(1) in ("bg", "card-bg", "card"):
            continue
        for part in re.split(r"\s*,\s*", sel):
            last = part.strip().split()[-1]
            for cls in re.findall(r"\.([\w-]{3,})", last):
                panels.setdefault(cls, m.group(1))
    findings = []
    for sel, props in rules(css):
        raw = props.get("color") or props.get("fill")
        if not raw or raw in ("none", "inherit", "currentColor", "transparent"):
            continue
        m = re.fullmatch(r"var\(\s*--([\w-]+)\s*(?:,[^)]*)?\)", raw.strip())
        token = m.group(1) if m else None
        col = parse_color(resolved.get(token, raw) if token else raw)
        if col is None:
            continue
        size = px(props.get("font-size", "")) or 0
        # A fill on a shape is a mark, not text; only grade it when the selector
        # is clearly textual, or when a font-size sits beside it.
        textual = ("text" in sel or props.get("font-size") or "color" in props)
        if not textual:
            continue
        # Which surface does this text actually sit on? The metric assumed two
        # canvases, --bg and --card-bg, because that was every surface the deck
        # had. A page painted as an accent field is a third, and the check
        # reported its text at 1.13:1 — measuring correct, contrasting colour
        # against a canvas it never touches. A metric that cannot see a surface
        # reports the page it imagined, and a false alarm teaches an author to
        # stop reading the output, which is worse than the gap.
        surfaces = []
        own = (props.get("background") or props.get("background-color") or "").strip()
        mo = re.fullmatch(r"var\(\s*--([\w-]+)\s*(?:,[^)]*)?\)", own)
        if mo:
            # The rule paints its own surface and puts text on it. Nothing to
            # infer: grade it against the thing it sits on. Without this, four
            # status chips were each graded against the first wash discovered
            # rather than their own.
            surfaces = [(mo.group(1), over_bg(parse_color(resolved.get(mo.group(1), "")), bg))]
        else:
            # Longest class wins, so `.tag.no` is not answered by `.tag`.
            for panel in sorted(panels, key=len, reverse=True):
                # A class token, not a substring: keying on `i` once matched
                # every selector containing the letter i and put half the deck
                # on the wrong surface.
                if re.search(r"\.%s(?![\w-])" % re.escape(panel), sel):
                    surfaces = [(panels[panel],
                                 over_bg(parse_color(resolved.get(panels[panel], "")), bg))]
                    break
        if not surfaces:
            surfaces = [("card-bg", card)] if "card" in sel else [("bg", bg), ("card-bg", card)]
        floor = CONTRAST_FLOOR_LARGE if size >= LARGE_TEXT_PX else CONTRAST_FLOOR
        for surface_name, surface in surfaces:
            ratio = contrast(over(col, surface[:3]), surface[:3])
            if ratio < floor:
                findings.append({
                    "selector": sel, "token": token or raw,
                    "on": surface_name, "ratio": round(ratio, 2),
                    "floor": floor, "font_size_px": size or None,
                })
    return findings


def d2_type_scale(css):
    """Report the small end of the type scale. There is no floor: 0.1.340 withdrew
    the 11px one as a universal size invented without an ask. Small type is a
    problem when it is also low contrast (D1) or when the page cannot carry it —
    both are judgements about a page, not a threshold."""
    sizes = []
    for sel, props in rules(css):
        size = px(props.get("font-size", ""))
        if size is not None:
            sizes.append((size, sel))
    sizes.sort()
    return {"smallest_px": sizes[0][0] if sizes else None,
            "smallest": [f"{s}px {sel[:44]}" for s, sel in sizes[:4]]}


def d3_callouts(raw):
    pages = re.findall(r'<section[^>]*class="[^"]*\bpage\b[^"]*"[^>]*>(.*?)</section>',
                       raw, re.S | re.I)
    if not pages:
        return None
    per_page, over_budget = [], []
    for i, body in enumerate(pages):
        n = sum(len(re.findall(rf'class="[^"]*\b{c}\b[^"]*"', body)) for c in TIER1_CLASSES)
        per_page.append(n)
        if n > TIER1_PER_PAGE:
            over_budget.append({"page_index": i, "tier1": n})
    with_any = sum(1 for n in per_page if n)
    return {
        "pages": len(pages), "tier1_total": sum(per_page),
        "pages_with_tier1": with_any,
        "page_share": round(100.0 * with_any / len(pages), 1),
        "over_budget": over_budget,
    }


def d4_palette(raw):
    stripped = re.sub(r"/\*.*?\*/", " ", raw, flags=re.S)
    for body in token_blocks(css_of(raw)).values():
        stripped = stripped.replace(re.sub(r"/\*.*?\*/", " ", body, flags=re.S), " ")
    stripped = re.sub(r"src:\s*url\(data:[^)]*\)", " ", stripped)
    stripped = re.sub(r"<!--.*?-->", " ", stripped, flags=re.S)
    # Numeric HTML entities are not colours. `&#183;` is a middot and the deck
    # is full of them; three of them reported as literal hexes, which is the
    # kind of false positive that teaches an author to stop reading the output.
    stripped = re.sub(r"&#\d+;", " ", stripped)
    hits = re.findall(r"(?<![\w#&])#[0-9A-Fa-f]{6}\b|(?<![\w#&])#[0-9A-Fa-f]{3}(?![\w-])",
                      stripped)
    return sorted(set(hits))


SHAPES = ("rect", "circle", "ellipse", "polygon", "polyline", "line", "path")


def d5_drawn_share(raw):
    """How many `.fig` blocks hold a drawing, against how many are pure markup.

    **Reported, never a floor.** A share here would be satisfied by drawing
    badly, which is D7's withdrawn fill floor in a new costume. What it is for is
    the case a reader raised: a deck whose figures were all HTML blocks measured
    clean on every gate and read as flat, because nothing in the package could
    see the difference between a figure and a layout.
    """
    figs = re.findall(r'<div class="fig[^"]*">(.*?)(?=<div class="cap|</div>\s*</div>)',
                      raw, re.S)
    if not figs:
        return None
    drawn = sum(1 for x in figs
                if re.search(r'<svg(?![^>]*class="(?:ground|ic)")', x))
    return {"figures": len(figs), "drawn": drawn, "laid_out": len(figs) - drawn}


def d5_figure_parity(raw):
    figs = []
    for m in re.finditer(r"<svg\b(?![^>]*width=\"0\")[^>]*>(.*?)</svg>", raw, re.S | re.I):
        s = m.group(1)
        if "<symbol" in s:
            continue
        # An <svg><use/></svg> is one icon instance, not a figure. Counting them
        # buried the seven real figures under 25 eyebrow icons.
        if "<use" in s and not re.search(r"<(?:path|rect|circle|line|polygon)\b", s):
            continue
        counts = {k: len(re.findall(rf"<{k}\b", s)) for k in SHAPES}
        counts["text"] = len(re.findall(r"<text\b", s))
        counts["arrows"] = len(re.findall(r"marker-end", s))
        counts["dashed"] = len(re.findall(r"dash", s))
        shape_kinds = sum(1 for k in SHAPES if counts[k])
        figs.append({"shape_kinds": shape_kinds, "arrows": counts["arrows"],
                     "dashed": counts["dashed"], "text": counts["text"],
                     "rect_only": shape_kinds <= 1 and counts["rect"] > 0})
    if not figs:
        return None
    kinds = [f["shape_kinds"] for f in figs]
    return {
        "figures": len(figs),
        "shape_kinds_min": min(kinds), "shape_kinds_max": max(kinds),
        "rect_only_figures": sum(1 for f in figs if f["rect_only"]),
        "figures_with_arrows": sum(1 for f in figs if f["arrows"]),
        "detail": figs,
    }


def _pages(raw):
    return re.findall(
        r'<section[^>]*class="[^"]*\bpage\b([^"]*)"[^>]*id="([^"]*)"[^>]*>(.*?)</section>',
        raw, re.S | re.I)


# The blocks the visual-share directive counts as "visual": a figure, a stat
# band, a display lead, and the purpose-built comparison patterns. Tables are
# deliberately absent — a table is for values (§4), and the directive that
# created this metric asked for figures over tables.
VISUAL_BLOCKS = ("fig", "band", "lead", "swaps", "vows", "duo", "grades", "field")


def d16_visual_presence(raw):
    """Content pages that carry no visual block at all. Reported, never gating.

    The static half of the owner's visual-share directive (2026-08-09): the
    decidable question is whether a page carries anything visual, and the pages
    that answer no are listed for a human to look at. The 50% *area* target is
    rendered geometry, so it lives in inspect_layout.py — measuring area from
    declared CSS is how the withdrawn 82% fill floor lied. A floor here would
    be satisfied by pasting a small block on every page, which is the same
    failure with a different number, so this reports and a reviewer decides.
    """
    pages = _pages(raw)
    if not pages:
        return None
    # An apparatus page is DECLARED, never inferred: `data-role="apparatus"` on
    # the section. A glossary, a scoring table, a boundaries list and a how-to
    # page are reference the reader returns to rather than a claim the deck
    # advances, and asking them to carry a figure produces decoration. The
    # declaration is what keeps this from becoming the escape hatch that empties
    # the metric — it is auditable, it is counted, and the pages that claimed it
    # are named in the report.
    apparatus = set(re.findall(
        r'<section[^>]*id="([^"]*)"[^>]*data-role="apparatus"', raw))
    apparatus |= set(re.findall(
        r'<section[^>]*data-role="apparatus"[^>]*id="([^"]*)"', raw))
    prose_only, content = [], 0
    for cls, pid, body in pages:
        # Substring on the SECTION class list, whose values are single words
        # (page/cover/opener/closing) — same idiom as d8. The block test below
        # is different: `.body` classes like `band-hero` would collide, so it
        # matches a whole class token.
        if "cover" in cls or "closing" in cls or "opener" in cls:
            continue
        if pid in apparatus:
            continue
        content += 1
        if any(re.search(rf'class="(?:[^"]*\s)?{b}(?:\s[^"]*)?"', body)
               for b in VISUAL_BLOCKS):
            continue
        prose_only.append(pid)
    # A ceiling, not a target: a deck is an argument and reference pages support
    # it, so past about one content page in five the deck has become a handbook.
    # Reported, like everything else here.
    share = round(100.0 * len(apparatus) / max(1, content + len(apparatus)), 1)
    return {"content_pages": content, "prose_only": prose_only,
            "apparatus": sorted(apparatus), "apparatus_share": share}


def d17_export_weight(raw, css):
    """What this document will cost the reader when it is exported.

    Reported, never gating: a heavy page is not a wrong page. But the cost is
    invisible on screen and brutal in a PDF, and it is decidable from the CSS.

    *Provenance: a 31-page deck exported to a 513 KB PDF that took 4515ms to
    render — ten times its content's worth — because five opener pages carried
    `mix-blend-mode: multiply` on the ground. One blended element forces the
    reader to composite the whole page. Removing the mode alone brought it to
    448ms; the node count and the group opacity together changed nothing
    measurable.*
    """
    blends = re.findall(r"mix-blend-mode\s*:\s*([\w-]+)", css)
    filters = re.findall(r"(?<!-)\bfilter\s*:\s*(?!none)([^;}]+)", css)
    shadows = len(re.findall(r"box-shadow\s*:\s*(?!none)", css))
    nodes = sum(len(m.split()) for m in re.findall(r'points="([^"]+)"', raw))
    nodes += raw.count("<path ")
    return {"blend_modes": [b for b in blends if b != "normal"],
            "filters": len(filters), "shadows": shadows, "vector_nodes": nodes}


def d18_region_labels(raw):
    """Every coloured region in a globe figure carries a label or a legend entry.

    Hue encodes region IDENTITY in that figure, by owner directive, and this is
    what makes that safe. Measured at the theoretical maximum hue separation of
    90 degrees, deuteranopia collapses two adjacent regions to delta-E00 9.6 and
    protanopia to 8.5 — and a real map runs at 60 or less. Hue separates
    neighbours at a glance; text is what carries identity.

    So this checks for the TEXT and never counts hues. Counting them would make
    the rule conditional on a number the measurement does not support, and would
    pass a two-region map whose two regions are unlabelled.

    A region is anchored by `data-region-label="<id>"` on any element, or by a
    legend row carrying `data-legend="<id>"`.
    """
    ids = set(re.findall(r'class="[^"]*\brg-([\w-]+)', raw))
    if not ids:
        return None
    labelled = set(re.findall(r'data-region-label="([\w-]+)"', raw))
    labelled |= set(re.findall(r'data-legend="([\w-]+)"', raw))
    return {"regions": len(ids), "unlabelled": sorted(ids - labelled)}


def d8_support_line(raw):
    """Every content page carries a support line under the title. Figure pages
    are not exempt: a diagram with nothing introducing it drops the reader in."""
    missing = []
    for cls, pid, body in _pages(raw):
        if "cover" in cls or "closing" in cls:
            continue
        # A .lead block does exactly what a support line does — say what the
        # page is about, under the title — and 0.1.342 made it the answer on the
        # pages whose point is one number or one claim. A statement page that
        # carries only a claim needs nothing else under it.
        if re.search(r'<p class="(?:sup|lede)\b', body):
            continue
        if re.search(r'class="[^"]*\blead\b', body) or "opener" in cls:
            continue
        missing.append(pid)
    return missing


def d13_lime_never_light_text(css, resolved, palette):
    """The acid green is a surface, not a member of the text ladder.

    #B8FF00 measures 1.21:1 as text on the white canvas and 16.44:1 with
    near-black reversed out of it. On light it may only ever be a fill. D1 would
    catch it as a contrast failure, but only if the rule happens to be graded
    against the right surface — this states the constraint directly, so it
    cannot be lost to a surface-detection edge case the way two colours were in
    0.1.343.
    """
    if palette != "light":
        return []
    # Scanned from the raw CSS, not from the parsed rule map: that map merges
    # duplicate selectors and a later `.sup` in a media query silently dropped
    # the declaration this check exists to find. A guard you cannot make fire is
    # not a guard — this one is confirmed by putting the lime on a text rule.
    bad = []
    for m in re.finditer(r"([^{}]+)\{([^}]*)\}", css):
        sel, body = m.group(1).strip(), m.group(2)
        if not re.search(r"(^|;)\s*color\s*:\s*var\(\s*--lime\s*[,)]", body):
            continue
        if "dark" in sel:                       # the dark canvas may use it as text
            continue
        bad.append(re.sub(r"\s+", " ", sel)[:60])
    return bad



def _block_text(body, cls):
    """The whole footer, with nested elements included.

    This was `class="[^"]*\bfoot\b[^"]*"[^>]*>(.*?)</div>` — non-greedy to the
    FIRST closing tag — so a footer that wraps its handling terms in a nested
    <div> had its text truncated before the terms were reached, and D12, the one
    design check that blocks a ship, failed for a reason having nothing to do
    with the terms being present. The fixture that was supposed to test this
    check was written with spans specifically to avoid the bug, which guaranteed
    the regression suite could never surface it.
    """
    m = re.search(rf'<(\w+)[^>]*class="[^"]*\b{cls}\b[^"]*"[^>]*>', body)
    if not m:
        return ""
    tag, i, depth = m.group(1), m.end(), 1
    token = re.compile(rf"<(/?){tag}\b[^>]*>")
    while depth and (found := token.search(body, i)):
        depth += -1 if found.group(1) else 1
        i = found.end()
    return re.sub(r"<[^>]+>", " ", body[m.end():i])

def d12_commercial_footer(raw, site=None):
    """Every page carries its handling terms and the origin of the document.

    **This is the one design check that fails the run.** Everything else here is
    a diagnostic for a designer to read, because a page is done when a human
    reads it as intentional and a threshold that can be satisfied without
    improving the page ends the looking. This one is different in kind: it is not
    a judgement about a page, it is a commercial requirement on the artifact. A
    slide gets screenshotted out of a deck and forwarded on its own, so terms
    that live only on the cover do not travel with it.
    """
    pages = re.findall(r'<section[^>]*class="[^"]*\bpage\b[^"]*"[^>]*>(.*?)</section>',
                       raw, re.S | re.I)
    if not pages:
        return None
    missing_terms, missing_site = [], []
    for i, body in enumerate(pages):
        low = _block_text(body, "foot").lower()
        if not any(w in low for w in ("confidential", "privileged", "internal use",
                                      "do not forward", "proprietary")):
            missing_terms.append(i)
        if not re.search(r"\b[\w.-]+\.(io|com|cn|ai|net|org)\b", low):
            missing_site.append(i)
    return {"pages": len(pages), "missing_terms": missing_terms,
            "missing_site": missing_site}


# What an author leaves for themselves and then ships. Each alternative is a
# marker vocabulary rather than "anything in brackets", because brackets are
# ordinary prose punctuation — `[sic]`, `[2]`, `[EU]` — and a check that fails on
# those is one people learn to ignore. Braces and angle brackets are doubled
# because a single pair of either is markup or arithmetic, never a slot.
PLACEHOLDER = re.compile(
    r"\[[^\]\n]{0,60}\]|\{\{[^}\n]{0,60}\}\}|<<[^>\n]{0,60}>>", re.I)
PLACEHOLDER_MARKERS = re.compile(
    r"to\s*fill|to[-\s]?do\b|\btbd\b|\btba\b|fill[-\s]?in|\binsert\b|placeholder"
    r"|\bx{2,}\b|lorem|\bname here\b|your\s+\w+\s+here|^\s*$", re.I)
# `[...]` and `[…]` are deliberately NOT markers. Bracketed ellipsis is the
# standard editorial mark for an elision inside a quotation, which a consulting
# document uses legitimately, and a gate that fails on it is a gate people learn
# to route around.


def d14_placeholders(raw):
    """No slot an author left for themselves may reach the reader.

    **This gates, for the same reason D12 does.** It is not a judgement about
    whether a page is well made — it is whether the document is finished, which
    is decidable, and an unfinished document is not a deliverable at whatever
    quality. A real deliverable shipped four `[TO FILL]` markers on its closing
    page, immediately beside its own callout saying they must not ship. Every
    check in this package passed it: prose because the marker is not a banned
    phrase, design because it is not a colour or a contrast, layout because a
    placeholder occupies exactly as much space as the text that should replace
    it. Nothing had ever looked.
    """
    body = re.sub(r"<(script|style|svg)\b.*?</\1>", " ", raw, flags=re.S | re.I)
    body = re.sub(r"<!--.*?-->", " ", body, flags=re.S)
    found = []
    for cls, pid, page in _pages(body) or [("", "(document)", body)]:
        text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", page))
        for m in PLACEHOLDER.finditer(text):
            inner = m.group(0).strip("[]{}<>").strip()
            if not PLACEHOLDER_MARKERS.search(inner):
                continue
            found.append({"page": pid, "text": m.group(0)[:40]})
    return found


# A path to a file, which is a build artifact reference and not a source a
# reader can act on. Two segments and a known extension, because that is what
# separates `resources/GLOBAL-catalog-20260730.zh.html` from `www.example.org`,
# which D12 *requires* the footer to carry. Anything inside a URL is skipped:
# a link is a link, and the defect is a filesystem path pasted into reader copy.
FILE_PATH = re.compile(
    r"(?<!/)\b[\w.㐀-鿿-]+/[\w.㐀-鿿-]+"
    r"\.(?:html?|md|json|jsonl|csv|tsv|xlsx?|docx?|pptx?|pdf|zip|txt|xml|ya?ml|py|js)\b",
    re.I)


def d15_footer_path(raw):
    """No footer may name a file. **Gates**, with D12 and D14.

    Not a design judgement and not a genre question: a repository path is not a
    reader-facing source line in any genre, and a customs manager cannot open
    `resources/…zh.html`. `.foot .src` was removed from `tokens/` in 0.1.366
    because the first deliverable to meet it filled every client page with a
    build path and three processing dates. Removing the styling did not stop the
    span — a second deliverable put one back, in Chinese, on almost every content
    page, and D6, D12 and D14 all passed it. **That is the same lesson in two
    documents, which is what this repository promotes to a rule.**

    Deliberately not the genre fork the reporting note proposed. Per-page
    sourcing is legitimate for consulting and internal analysis, and an English
    one-line source there is apparatus rather than a defect; what no genre wants
    is a path. Banning the path needs no `--genre` plumbed into this script and
    catches the thing a reader actually saw.
    """
    pages = re.findall(r'<section[^>]*class="[^"]*\bpage\b[^"]*"[^>]*>(.*?)</section>',
                       raw, re.S | re.I)
    if not pages:
        return None
    found = []
    for i, body in enumerate(pages):
        text = re.sub(r"\s+", " ", _block_text(body, "foot"))
        for m in FILE_PATH.finditer(text):
            if "://" in text[max(0, m.start() - 8):m.start()]:
                continue
            found.append({"page": i + 1, "path": m.group(0)[:60]})
    return {"pages": len(pages), "found": found}


def d9_layout_variety(raw):
    """One layout on 25 consecutive pages is what this metric exists to stop."""
    used, unknown = [], []
    for cls, pid, body in _pages(raw):
        if "cover" in cls or "closing" in cls:
            continue
        m = re.search(r'<div class="body([^"]*)"', body)
        names = [c for c in (m.group(1).split() if m else []) if c not in ("top",)]
        layout = next((n for n in names if n in LAYOUTS), None)
        if layout is None:
            unknown.append((pid, " ".join(names) or "(none)"))
        else:
            used.append(layout)
    if not used and not unknown:
        return None
    counts = {}
    for layout in used:
        counts[layout] = counts.get(layout, 0) + 1
    total = len(used) + len(unknown)
    top = max(counts.values()) if counts else 0
    return {
        "pages": total, "distinct": len(counts),
        "top_share": round(100.0 * top / total, 1) if total else 0.0,
        "top_layout": max(counts, key=counts.get) if counts else None,
        "counts": dict(sorted(counts.items(), key=lambda kv: -kv[1])),
        "unknown": unknown,
    }


def d10_label_icons(raw):
    """Reported, not graded. Labelled figure nodes and table row-head groups
    should carry a semantic icon; whether a given label is a heading is a
    judgement, so this counts rather than gates."""
    # Element- and attribute-order-agnostic, and per page: the eyebrow may be
    # any element (<p> in the fixtures, <div> in the reference deck), `class`
    # need not be the first attribute on either element, and `ic` matches as a
    # whole class token. The same regression shipped here twice in two forms —
    # keyed to <div>, then to attribute position — each counting 0 on a deck
    # with an icon in every eyebrow and silently reclassifying them as figure
    # icons. The per-page list feeds D10_detail so the fixtures can pin it.
    pat = re.compile(r'<\w+[^>]*class="[^"]*\beyebrow\b[^"]*"[^>]*>\s*'
                     r'<svg[^>]*class="[^"]*\bic\b')
    with_icon = [pid for cls, pid, body in _pages(raw) if pat.search(body)]
    svg_icons = len(re.findall(r'<svg[^>]*class="[^"]*\bic\b[^"]*"', raw))
    return {"eyebrow_icons": len(with_icon), "icon_instances": svg_icons,
            "figure_or_row_icons": max(0, svg_icons - len(with_icon)),
            "eyebrow_pages": with_icon}


def d6_footer(raw):
    pages = re.findall(r'<section[^>]*class="[^"]*\bpage\b[^"]*"[^>]*>(.*?)</section>',
                       raw, re.S | re.I)
    if not pages:
        return None
    missing_src, missing_total = [], []
    for i, body in enumerate(pages):
        text = _block_text(body, "foot")
        pass  # provenance is a document-level question now; see below
        if not re.search(r"\b\w+\s*/\s*\d+\b", text):
            missing_total.append(i)
    # Provenance is stated once for the document, not on every page. 0.1.344
    # retired the per-page source line for sales and marketing material at a
    # reader's request: a source under every figure and again in every footer is
    # apparatus a customs manager does not need, and it was crowding out the
    # handling terms that a commercial document does need. The obligation did not
    # go away — it moved to where it is read once, on the cover and the closing.
    # So this asks the document, and D12 asks every page for its terms.
    doc_text = _block_text(raw, "colophon").lower()
    if not re.search(r"source|derived from|based on|provenance", doc_text):
        missing_src = list(range(len(pages)))
    return {"pages": len(pages), "missing_source": missing_src,
            "missing_total": missing_total}


# ── driver ────────────────────────────────────────────────────────────────────
def measure(path):
    raw = path.read_text(encoding="utf-8")
    css = css_of(raw)
    if not css.strip():
        raise Unmeasurable("no <style> block; nothing to measure")
    palette = "dark" if re.search(r'<body[^>]*\bclass="[^"]*\bdark\b', raw) else "light"
    resolved, _ = resolve(css, palette)
    if "bg" not in resolved:
        raise Unmeasurable("no --bg token; this file does not use the LUMI token block")
    return {
        "file": str(path), "palette": palette,
        "D1_contrast": d1_contrast(css, resolved, palette),
        "D2_type_scale": d2_type_scale(css),
        "D3_callouts": d3_callouts(raw),
        "D4_palette_literals": d4_palette(raw),
        "D5_figure_parity": d5_figure_parity(raw),
        "D5_drawn_share": d5_drawn_share(raw),
        "D6_footer": d6_footer(raw),
        "D8_support_line": d8_support_line(raw),
        "D12_commercial_footer": d12_commercial_footer(raw),
        "D14_placeholders": d14_placeholders(raw),
        "D15_footer_path": d15_footer_path(raw),
        "D13_lime_as_text": d13_lime_never_light_text(css, resolved, palette),
        "D9_layout_variety": d9_layout_variety(raw),
        "D10_label_icons": (d10 := d10_label_icons(raw)),
        "D16_visual_presence": (d16 := d16_visual_presence(raw)),
        "D17_export_weight": d17_export_weight(raw, css),
        "D18_region_labels": (d18 := d18_region_labels(raw)),
        # The contains hook in check_fixtures.py reads <PREFIX>_detail. D16's
        # is the WHOLE dict, not just the prose-only list, so the pass fixture
        # can assert '"prose_only": []' — a regression that flags every
        # healthy page would otherwise stay green, since reported verdicts
        # pass unconditionally.
        "D16_detail": d16,
        "D10_detail": d10["eyebrow_pages"],
        # The contains hook in check_fixtures.py reads <PREFIX>_detail. Naming
        # the regions is what lets the broken fixture assert WHICH one was left
        # unlabelled; a count alone cannot tell a real catch from an off-by-one.
        "D18_detail": (d18 or {}).get("unlabelled"),
    }


def grade(r):
    rows = []
    rows.append(("D1_contrast", len(r["D1_contrast"]), "=0",
                 not r["D1_contrast"], False))
    d18 = r["D18_region_labels"]
    rows.append(("D18_region_labels",
                 len(d18["unlabelled"]) if d18 else None, "=0",
                 not (d18 and d18["unlabelled"]), d18 is None))
    rows.append(("D2_type_scale",
                 f"smallest {r['D2_type_scale']['smallest_px']}px", "reported", True, False))
    c = r["D3_callouts"]
    rows.append(("D3_tier1_per_page", len(c["over_budget"]) if c else None,
                 f"<={TIER1_PER_PAGE} per page", not (c and c["over_budget"]), c is None))
    rows.append(("D3_tier1_page_share", c["page_share"] if c else None,
                 f"<={TIER1_PAGE_SHARE}%",
                 bool(c) and c["page_share"] <= TIER1_PAGE_SHARE, c is None))
    rows.append(("D4_palette_literals", len(r["D4_palette_literals"]), "=0",
                 not r["D4_palette_literals"], False))
    p = r["D5_figure_parity"]
    rows.append(("D5_figure_parity",
                 f"{p['rect_only_figures']}/{p['figures']} rect-only" if p else None,
                 "reported", True, p is None))
    f = r["D6_footer"]
    ok6 = bool(f) and not f["missing_source"] and not f["missing_total"]
    rows.append(("D6_footer", (len(f["missing_source"]) + len(f["missing_total"]))
                 if f else None, "=0", ok6, f is None))
    rows.append(("D8_support_line", len(r["D8_support_line"]), "=0",
                 not r["D8_support_line"], False))
    rows.append(("D13_lime_as_text", len(r["D13_lime_as_text"]), "=0",
                 not r["D13_lime_as_text"], False))
    cf = r["D12_commercial_footer"]
    # The fifth field is "could not be measured", not "gates" — passing True here
    # would have printed the one check that matters as n/a. Gating is decided in
    # main() from the finding itself.
    rows.append(("D12_commercial_footer",
                 (len(cf["missing_terms"]) + len(cf["missing_site"])) if cf else None,
                 "=0 (gates)",
                 bool(cf) and not cf["missing_terms"] and not cf["missing_site"],
                 cf is None))
    d = r["D5_drawn_share"]
    rows.append(("D5_drawn_share",
                 f"{d['drawn']}/{d['figures']} figures drawn" if d else None,
                 "reported", True, d is None))
    rows.append(("D14_placeholders", len(r["D14_placeholders"]), "=0 (gates)",
                 not r["D14_placeholders"], False))
    fp = r["D15_footer_path"]
    rows.append(("D15_footer_path", len(fp["found"]) if fp else None, "=0 (gates)",
                 bool(fp) and not fp["found"], fp is None))
    v = r["D9_layout_variety"]
    rows.append(("D9_layout_spread",
                 f"{v['distinct']} layouts, top {v['top_share']}%" if v else None,
                 "reported", True, v is None))
    i = r["D10_label_icons"]
    rows.append(("D10_label_icons",
                 f"{i['eyebrow_icons']} eyebrow, {i['figure_or_row_icons']} in figures"
                 if i else None, "reported", True, i is None))
    ew = r["D17_export_weight"]
    rows.append(("D17_export_weight",
                 f"{len(ew['blend_modes'])} blend modes, {ew['vector_nodes']} nodes",
                 "reported", True, False))
    vp = r["D16_visual_presence"]
    rows.append(("D16_visual_presence",
                 f"{len(vp['prose_only'])} of {vp['content_pages']} content pages "
                 f"prose-only, {len(vp['apparatus'])} apparatus "
                 f"({vp['apparatus_share']}%)" if vp else None,
                 "reported", True, vp is None))
    return [(n, v, t, "n/a" if skip else ("ok" if good else "FAIL"))
            for n, v, t, good, skip in rows]


def main(argv):
    ap = argparse.ArgumentParser(add_help=True, description=__doc__.split("\n")[0])
    ap.add_argument("files", nargs="+")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    results, failures, unmeasurable, gated_failure = [], 0, 0, 0
    for name in args.files:
        path = pathlib.Path(name)
        try:
            r = measure(path)
        except (Unmeasurable, OSError) as exc:
            unmeasurable += 1
            if not args.json:
                print(f"\n{name}\n  UNMEASURABLE  {exc}")
            continue
        r["verdicts"] = {n: v for n, _, _, v in
                         ((a, b, c, d) for a, b, c, d in grade(r))}
        # The two gating metrics. Neither is a judgement about whether a page is
        # well made: D12 is a commercial requirement on the artifact and D14 asks
        # whether the document is finished. Both are decidable, which is what
        # separates them from every other row here.
        if any(r["verdicts"].get(m) == "FAIL"
               for m in ("D12_commercial_footer", "D14_placeholders",
                         "D15_footer_path")):
            gated_failure += 1
        results.append(r)

    if args.json:
        print(json.dumps(results, indent=2))
        return 1 if (unmeasurable or gated_failure) else 0

    for r in results:
        rows = grade(r)
        print(f"\n{r['file']}  ({r['palette']} palette)")
        for name, value, target, verdict in rows:
            print(f"  {verdict:<5} {name:<22} {str(value):<24} target {target}")
            # `verdict == "note"` until 0.1.367 — a value `grade()` has never
            # produced, so `failures` was always 0 and the last line of every run
            # read "nothing flagged". It printed that under a report carrying two
            # FAIL rows, on a real deliverable, which is the sentence the whole
            # 0.1.366–0.1.368 line of work exists to stop this package from
            # saying. A summary is a claim about what is above it.
            if verdict == "FAIL":
                failures += 1
        for f in r["D1_contrast"][:6]:
            print(f"        contrast {f['ratio']}:1 on {f['on']} — "
                  f"{f['selector']} uses --{f['token']}"
                  + (f" at {f['font_size_px']}px" if f["font_size_px"] else ""))
        if r["D17_export_weight"]["blend_modes"]:
            print(f"        blend modes make the export composite whole pages: "
                  f"{', '.join(sorted(set(r['D17_export_weight']['blend_modes'])))} "
                  f"— measured 10x on a 31-page deck")
        for line in r["D2_type_scale"]["smallest"]:
            print(f"        {line}")
        for h in r["D4_palette_literals"][:6]:
            print(f"        literal colour {h} outside the token block")
        for o in (r["D3_callouts"] or {}).get("over_budget", [])[:6]:
            print(f"        page {o['page_index']} carries {o['tier1']} tier-1 callouts")
        for pid in r["D8_support_line"][:8]:
            print(f"        {pid} has no support line under its title")
        cf = r.get("D12_commercial_footer")
        if cf:
            for i in cf["missing_terms"][:6]:
                print(f"        page {i + 1} footer states no handling terms")
            for i in cf["missing_site"][:6]:
                print(f"        page {i + 1} footer does not say where the document is from")
        d = r["D5_drawn_share"]
        if d and d["laid_out"]:
            print(f"        {d['laid_out']} of {d['figures']} figures are markup "
                  f"rather than a drawing; §4 asks what the content is and to draw that")
        for ph in r["D14_placeholders"][:8]:
            print(f"        {ph['page']} still carries the slot {ph['text']}")
        for fpath in (r["D15_footer_path"] or {}).get("found", [])[:6]:
            print(f"        page {fpath['page']} footer cites the file "
                  f"{fpath['path']} — a path is not a source a reader can open")
        v = r["D9_layout_variety"]
        if v:
            for pid, cls in v["unknown"][:6]:
                print(f"        {pid} uses no shipped layout (body class: {cls})")
            if v["top_share"] > LAYOUT_MAX_SHARE:
                print(f"        {v['top_layout']} carries {v['top_share']}% of pages")
            if v["pages"] >= LAYOUT_MIN_PAGES and v["distinct"] < LAYOUT_MIN_DISTINCT:
                print(f"        only {v['distinct']} distinct layouts across {v['pages']} pages")

    if not failures:
        print("\nnothing flagged")
    elif gated_failure:
        print(f"\n{failures} metric(s) failed, and {gated_failure} file(s) fail on "
              f"D12, D14 or D15 — those three block: a page missing its handling "
              f"terms, a document still carrying a slot, and a footer citing a file "
              f"path are not judgements about design")
    else:
        print(f"\n{failures} thing(s) worth a look — none of this blocks; "
              f"read them, then look at the page")
    if unmeasurable:
        print(f"{unmeasurable} file(s) could not be measured at all")
    return 1 if (unmeasurable or gated_failure) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
