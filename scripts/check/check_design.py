#!/usr/bin/env python3
"""Measure the design metrics from references/eval-rubric.md on a deliverable.

The prose metrics made the prose half of this skill checkable. The design half stayed a
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
    D13 lime as text  the acid green never sets reader copy (reported)
    D16 visual presence  content pages carrying no visual block (reported)
    D17 export weight    blend modes, filters and vector nodes (reported)
    D18 region labels    every coloured region carries its name (reported)

    D12 commercial footer  handling terms and origin on every page (**gates**)
    D14 placeholders       slots the author left for themselves (**gates**)
    D15 footer path        no repository path reaches a footer (**gates**)
    D19 vocabulary         icons, blocks, openers, the globe runtime, and
                           a var() naming no custom property
                           resolve inside this document (**gates**)
    D20 palette fidelity   the colour tokens it declares are the ones
                           tokens/ ships (**gates**)

**A metric gates if and only if its row's target says `(gates)`** — read the
row table in `grade()`, never a list written anywhere else, including here. Every other number is a diagnostic for a
designer to read, and the exit code is 0 unless a file could not be measured at
all. SKILL.md rule 4 is the reason: a page is done when a human reads it as
intentional, and a metric that can be satisfied without improving the page ends
the looking instead of directing it. D7, an 82% page-fill floor, was withdrawn in
0.1.340 for exactly that — it was satisfied by stretching table rows while four
diagrams rendered at 40% of their cell. For page geometry and centerpiece scale
use scripts/check/inspect_layout.py.

**D12 and D14 are different in kind, which is why they are the exceptions.**
Neither is a judgement about whether a page is well made. D12 is a commercial
requirement on the artifact, like a contract term: pages travel alone — a slide
is screenshotted out of a deck and forwarded without the cover — so terms that
live only on page one do not travel with the page. D14 asks whether the document
is *finished*, which is decidable in a way that "is this page intentional" is
not. A design metric that gates is a mistake; a commercial one that does not is a
different mistake.

    python3 scripts/check/check_design.py deck.html [more files ...]
    python3 scripts/check/check_design.py --json deck.html   # top level is a LIST; take [0]

Standard library only, like the rest of scripts/.
"""
from __future__ import annotations

import argparse
import hashlib
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
from html.parser import HTMLParser

_SCRIPTS_ROOT = next(p for p in _bs_pathlib.Path(__file__).resolve().parents
                     if p.name == "scripts")
for _sub in ("lib", "render", "check", "build", "ops", ""):
    _p = str(_SCRIPTS_ROOT / _sub) if _sub else str(_SCRIPTS_ROOT)
    if _p not in _bs_sys.path:
        _bs_sys.path.append(_p)
del _bs_pathlib, _bs_sys, _SCRIPTS_ROOT, _sub, _p
# --- end bootstrap ---
import color_math  # noqa: E402 — after the bootstrap, deliberately
import css_tokens  # noqa: E402 — after the bootstrap, deliberately
import figure_spec  # noqa: E402 — after the bootstrap
import gate_registry  # noqa: E402 — after the bootstrap
import markup  # noqa: E402 — after the bootstrap
from deliverable_registry import (  # noqa: E402 — after the bootstrap
    TYPICAL_SECTIONS,
    section_alts,
    section_name,
)

ROOT = next(p for p in pathlib.Path(__file__).resolve().parents
            if p.name == "scripts").parent

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
# LAYOUT_MAX_SHARE (40.0), LAYOUT_MIN_DISTINCT (5) and LAYOUT_MIN_PAGES (15)
# stood here until 0.1.456. The first printed an advisory against the 40% share
# cap that 0.1.340 WITHDREW — the retired register records the withdrawal, and a
# withdrawn rule that still prints is not withdrawn. The other two were a floor
# no retrospective ever argued, and it fired on the accepted reference document
# (3 distinct layouts across 28 pages): an advisory that flags the document the
# owner accepted is measuring its own taste. D9 states the numbers; a reader
# judges them.

# The layouts shipped in tokens/lumi-layouts.css. A .body class outside this set
# is either a typo or a layout invented in the document, and both defeat D9.
LAYOUTS = {
    "stack", "hero-band", "band-hero", "thirds-v",
    "split", "split-wide", "split-narrow", "columns-2", "columns-3", "columns-4",
    "rail", "quad", "sidebar-notes", "full-bleed", "diagonal-flow", "cover-grid",
    "dense",
}

# Class names the house style uses for a tier-1 callout (tinted + border + edge).
TIER1_CLASSES = ("key", "red")


class Unmeasurable(Exception):
    """The file yielded nothing to measure. Never silently a pass."""


# ── colour ────────────────────────────────────────────────────────────────────
# _lin/_luma moved to color_math.py (0.1.420) — one sRGB implementation,
# one threshold (0.04045; integer-channel identical to the old 0.03928).
def contrast(fg, bg):
    a, b = color_math.luma255(fg), color_math.luma255(bg)
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
    return css_tokens.strip_comments(css, " ")


def token_blocks(css):
    """The :root and body.dark declaration blocks: the only place a literal
    colour is allowed to appear.

    Blocks with the same selector ACCUMULATE, which is what CSS does and what
    this used to get wrong: it kept the last one and dropped the rest. A document
    that appends a second `:root` — the shipped `tokens/region-palette.css` is
    one — lost its whole token block to that second one, and the file reported
    UNMEASURABLE for having no --bg. Found by building a deliverable with the
    globe in it (0.1.387).
    """
    return {k: "\n".join(v) for k, v in token_block_bodies(css).items()}


def token_block_bodies(css):
    """The same blocks, kept SEPARATE, because d4_palette strips them from the
    raw document by verbatim string match and a joined body matches nothing.
    Joining them there is what made every token colour report as a stray literal.
    """
    out: dict[str, list[str]] = {"light": [], "dark": []}
    for sel, body in BLOCK_RE.findall(css):
        s = sel.strip()
        if s in (":root", ".trade") or _declares_only_tokens(body):
            (out["dark"] if "dark" in s else out["light"]).append(body)
        elif re.fullmatch(r"body\.dark(\s+\.trade)?"
                          r"|:root\[data-theme=[\"']dark[\"']\]", s):
            out["dark"].append(body)
    return {k: v for k, v in out.items() if v}


# A token block is a block that declares ONLY custom properties. Naming the
# selectors instead was fine while there were two of them and wrong the moment
# `build_region_palette.py --prefix` shipped: a scoped palette is generated on
# whatever class the author passed, and this function had no way to know. A
# business plan carrying a four-region phase palette on `.phasemap` reported 26
# of its own generated hexes as stray literals — the identical failure the
# `.trade` comment below records, one release later and by the same cause.
# Deciding by SHAPE rather than by name covers every prefix anyone will pass.
def _declares_only_tokens(body: str) -> bool:
    decls = [d.strip() for d in css_tokens.strip_comments(body, " ").split(";")
             if d.strip()]
    return bool(decls) and all(d.startswith("--") for d in decls)


# `.trade` is in that list because this package ships TWO generated region
# palettes and D4 could only see one of them. `region-palette.css` declares its
# variables on `:root` and passed; `region-palette-trade.css` declares the same
# kind of values on `.trade` (the class the trade globe carries) and every one
# of its fifty hexes read as a stray literal — on a deliverable that had done
# exactly what SKILL.md tells an author to do, include the palette and let the
# figure paint. Found when the brand field globe became the default cover mark
# (0.1.447) and the pass fixture inherited its palette; a shipped deliverable
# from the same workspace had been failing D4 on all fifty since it was built.
# The rule D4 enforces is "no literal outside the token block". Which blocks
# hold tokens is a fact about this package, not a judgement — so the checker's
# list has to match what `tokens/` actually ships.


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
    panels: dict[str, str] = {}
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
                if re.search(rf"\.{re.escape(panel)}(?![\w-])", sel):
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
    # A DECLARED trademark mark keeps its owner's colours: an <svg> carrying
    # data-mark (the get-started page's platform logos) is excised before the
    # literal scan, because recolouring a trademark into the palette would
    # falsify the mark and drawing it in tokens would fabricate one. The
    # exemption is declared on the element, never inferred — an undeclared
    # logo's hexes still fail, which is what keeps this from becoming the
    # escape hatch that empties the metric. (Second blind review's get-started
    # spec is the documented case.)
    raw = re.sub(r"<svg\b[^>]*\bdata-mark\b.*?</svg>", " ", raw,
                 flags=re.S | re.I)
    stripped = css_tokens.strip_comments(raw, " ")
    for bodies in token_block_bodies(css_of(raw)).values():
        for body in bodies:
            stripped = stripped.replace(
                css_tokens.strip_comments(body, " "), " ")
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
VISUAL_BLOCKS = ("fig", "band", "lead", "swaps", "vows", "duo", "grades",
                 # `.launch` is the agenda's launch sequence — numbered dark
                 # chips, the claim at title weight, a quiet run line. It was
                 # adopted at 0.1.519 from an owner review that read a plain
                 # text agenda as TOO QUIET, so it is a designed block by its
                 # own origin. Missing from this tuple until 0.1.547, D16 read
                 # every agenda in the package as a content page carrying
                 # nothing visual — the accepted reference deck included, at
                 # 1 of 18. A block introduced to be visual, counted as prose.
                 "launch",
                 "field", "stats")


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



def _flat_text(fragment: str) -> str:
    """Visible text of a markup fragment, whitespace collapsed."""
    return markup.visible_text(fragment)


def _norm_line(s: str) -> str:
    """Case- and punctuation-blind form for the agenda-title comparison.

    The CJK space rule is `markup.join_cjk` (shared with the outline mirror);
    its reason is written there.
    """
    t = " ".join(re.sub(r"[^a-z0-9\u4e00-\u9fff ]+", " ", s.lower()).split())
    return markup.join_cjk(t)


def d27_agenda_mirror(raw):
    """Every claim line on the agenda is a line the deck's own titles say.

    **This gates.** D16's reader opened her review with it: the agenda's part
    titles matched no opener and its items matched no page title, because the
    author had written the agenda a second time in fresh words. An agenda is a
    quotation of the document, not a paraphrase of it — the discipline in
    references/storyline-templates.md says derive it from the titles, and this
    is the checkable half. A line is compared normalized (case and punctuation
    blind), and it passes when it contains a title or a title contains it, so
    an agenda row may add its part letter or trim a subtitle without failing.
    A document with no agenda page owes nothing here (n/a).
    """
    pages = list(_pages(raw))
    # THE SAME FINDER D35 USES. Each had its own, and they disagreed: this one
    # matched `id="agenda"` case-sensitively and only the English word within
    # 120 characters of an eyebrow, so a deck with `id="Agenda"` or a Chinese
    # `议程` had no agenda here and an agenda there. Two gates about one page
    # may not disagree about whether the page exists.
    agenda = None
    for _cls, pid, body in pages:
        if _is_agenda_page(pid, body):
            agenda = body
            break
    if agenda is None:
        return None
    titles = []
    for _cls, _pid, body in pages:
        if body is agenda:
            continue
        for m in re.finditer(r"<h[123][^>]*>(.*?)</h[123]>", body, re.S | re.I):
            titles.append(_flat_text(m.group(1)))
        # Openers title with .openclaim, not a heading — read a real instance
        # before keying on a shape (convention 15).
        for m in re.finditer(
                r'class="(?:[^"]*\s)?openclaim(?:\s[^"]*)?"[^>]*>(.*?)</',
                body, re.S | re.I):
            titles.append(_flat_text(m.group(1)))
    tnorm = [_norm_line(t) for t in titles if t]
    lines = []
    for m in re.finditer(
            r'class="(?:[^"]*\s)?(?:gn|listhead)(?:\s[^"]*)?"[^>]*>(.*?)</p>',
            agenda, re.S | re.I):
        lines.append(_flat_text(m.group(1)))
    for m in re.finditer(r"<li[^>]*>(.*?)</li>", agenda, re.S | re.I):
        lines.append(_flat_text(m.group(1)))
    orphans = []
    for ln in lines:
        n = _norm_line(ln)
        if not n:
            continue
        if not any(n in t or t in n for t in tnorm):
            orphans.append(ln[:80])
    return {"lines": len(lines), "titles": len(tnorm), "orphans": orphans}


# The genres whose reader is outside the building. Written here rather than
# imported because check_prose's DASH_BANNED answers a different question
# (which genres ban a dash) and borrowing it would couple two rules that have
# already diverged once.
EXTERNAL_GENRES = ("sales", "marketing", "consulting")


def d28_takeaway(raw):
    """External-genre content pages that end with nothing a reader can quote.

    Reported this release, on the new-gate caution — the role is new and a
    floor on day one would be satisfied by pasting a sentence, which is the
    withdrawn fill-floor mistake in prose form. D16's reader: "客户每页记住的
    要点和想尝试的冲动" — a page that leaves no line behind leaves nothing
    behind. The genre is the document's own data-genre declaration; a document
    that does not declare an external genre owes nothing here (n/a).
    """
    genre = markup.body_attr(raw, "data-genre")
    if genre not in EXTERNAL_GENRES:
        return None
    pages = _pages(raw)
    if not pages:
        return None
    apparatus = set(re.findall(
        r'<section[^>]*id="([^"]*)"[^>]*data-role="apparatus"', raw))
    apparatus |= set(re.findall(
        r'<section[^>]*data-role="apparatus"[^>]*id="([^"]*)"', raw))
    missing, content = [], 0
    for cls, pid, body in pages:
        if ("cover" in cls or "closing" in cls or "opener" in cls
                or pid in apparatus or pid == "agenda"):
            continue
        content += 1
        if not re.search(r'class="(?:[^"]*\s)?take(?:\s[^"]*)?"', body):
            missing.append(pid)
    return {"content_pages": content, "missing": missing}


_NUM_TOKEN = re.compile(r"\d[\d,.]*%?")


def d29_figure_numbers(raw):
    """A page that states numbers and draws a figure that carries none of them.

    Reported. D16's reader called the miss by name: 没有把数字和矢量图结合 =
    没有洞察. The decidable proxy: collect the numeric tokens the page itself
    states (title and stat band), and ask whether any of them appears inside
    the figure's own SVG text. Step indices in a figure do not satisfy a page
    claiming 206 units — the match is on the page's stated values, not on the
    presence of digits.
    """
    pages = _pages(raw)
    if not pages:
        return None
    naked, unasked, with_figs = [], [], 0
    for cls, pid, body in pages:
        if "cover" in cls or "closing" in cls or "opener" in cls:
            continue
        if not re.search(r'class="(?:[^"]*\s)?fig(?:\s[^"]*)?"', body):
            continue
        with_figs += 1
        stated = set()
        for m in re.finditer(r"<h2[^>]*>(.*?)</h2>", body, re.S | re.I):
            stated.update(_NUM_TOKEN.findall(_flat_text(m.group(1))))
        for m in re.finditer(
                r'class="(?:[^"]*\s)?v(?:\s[^"]*)?"[^>]*>(.*?)</div>',
                body, re.S | re.I):
            stated.update(_NUM_TOKEN.findall(_flat_text(m.group(1))))
        stated = {s.rstrip(",.") for s in stated}
        if not stated:
            # THE THIRD ANSWER. This was `continue`, so a page whose title
            # spells its numbers as words — "Three versions in eight months" —
            # gave the check nothing to look for and printed exactly what a
            # page whose figure carries every number prints. Measured on the
            # first deck built through the figure contract: `naked: []`, all
            # green, on a figure the owner opened and called empty. FM-24, in
            # the gate written to catch a figure that carries no numbers.
            unasked.append(pid)
            continue
        drawn = set()
        for m in re.finditer(r"<text[^>]*>(.*?)</text>", body, re.S | re.I):
            drawn.update(_NUM_TOKEN.findall(_flat_text(m.group(1))))
        drawn = {s.rstrip(",.") for s in drawn}
        if not (stated & drawn):
            naked.append(pid)
    return {"pages_with_figs": with_figs, "naked": naked,
            "unasked": unasked}


_CAP_N = re.compile(r'<span class="(?:[^"]*\s)?n(?:\s[^"]*)?"[^>]*>\s*'
                    r'(?:Figure|Exhibit|\u56fe|\u56fe\u8868)\s*(\d+)', re.I)


_ROLE_RE = {
    "take": re.compile(r'<[^>]*class="[^"]*\btake\b[^"]*"[^>]*>(.*?)</', re.S | re.I),
    "sup": re.compile(r'<[^>]*class="[^"]*\bsup\b[^"]*"[^>]*>(.*?)</', re.S | re.I),
    "lead": re.compile(r'<[^>]*class="[^"]*\blead\b[^"]*"[^>]*>(.*?)</', re.S | re.I),
    "gd": re.compile(r'<[^>]*class="[^"]*\bgd\b[^"]*"[^>]*>(.*?)</', re.S | re.I),
    "title": re.compile(r'<h2[^>]*class="[^"]*\bt\b[^"]*"[^>]*>(.*?)</h2>', re.S | re.I),
}
# A run this long, shared by two roles on one page, is a repetition rather than
# a coincidence. Counted in characters for CJK and in words for the rest,
# because a Chinese clause of eight characters is about an English clause of
# four words.
REPEAT_CHARS, REPEAT_WORDS = 8, 4


def _longest_shared(a: str, b: str) -> str:
    """-> the longest run both strings contain. Small inputs; a page's roles."""
    if not a or not b:
        return ""
    best = ""
    for i in range(len(a)):
        for j in range(i + len(best) + 1, len(a) + 1):
            if a[i:j] in b:
                best = a[i:j]
            else:
                break
    return best


def d41_role_echo(raw):
    """-> pages where two roles on one page say the same thing.

    **Measured across two documents**, which is this package's bar for
    promoting a lesson to a rule. A 20-page sales report put one sentence in a
    `.gd` and again in the page's `.take`; a 2026-08 deck's `.take` was its
    `.sup` with the head cut off, word for word, and its `.lead` restated the
    first half of the title. Every gate was green on all of them.

    The `.lead` case has a cause worth naming: SKILL.md ENCOURAGES `.lead` on a
    page whose argument turns on one number, and says nothing about what
    `.lead` must carry that the title does not — so the cheapest way to satisfy
    the rule is to repeat the title. Following the rule produced the defect.

    REPORTED. A page may legitimately echo a phrase, and only a reader can tell
    a refrain from a duplicate.
    """
    hits = []
    for _cls, pid, body in _pages(raw):
        got = {}
        for role, rx in _ROLE_RE.items():
            m = rx.search(body)
            if m:
                got[role] = markup.strip_tags(m.group(1)).strip()
        for left, right in (("take", "sup"), ("take", "gd"), ("lead", "title")):
            a, b = got.get(left, ""), got.get(right, "")
            shared = _longest_shared(a, b)
            if not shared:
                continue
            cjk = any("\u3400" <= ch <= "\u9fff" for ch in shared)
            long_enough = (len(shared.strip()) >= REPEAT_CHARS if cjk
                           else len(shared.split()) >= REPEAT_WORDS)
            if long_enough:
                hits.append((pid, left, right, shared.strip()[:60]))
    return hits


def _declares_spec(raw, pid) -> bool:
    """-> whether this page names the file its figure's numbers live in."""
    for pat in (rf'<section[^>]*id="{re.escape(pid)}"[^>]*data-figure-spec="',
                rf'<section[^>]*data-figure-spec="[^"]*"[^>]*id="{re.escape(pid)}"'):
        if re.search(pat, raw):
            return True
    return False


def _analysis_move(raw, pid):
    """-> the move a page declares, or "".

    `_pages()` does not capture section attributes — `data-analysis` is emitted
    after `id` and falls inside its uncaptured `[^>]*>`. Both attribute orders
    are matched, the way D16 and D18 already read `data-role`.
    """
    for pat in (rf'<section[^>]*id="{re.escape(pid)}"[^>]*data-analysis="([^"]*)"',
                rf'<section[^>]*data-analysis="([^"]*)"[^>]*id="{re.escape(pid)}"'):
        m = re.search(pat, raw)
        if m:
            return m.group(1).strip().lower()
    return ""


_SHAPE_USE = re.compile(r'<use\b[^>]*href="#shape-[^"]+"', re.I)
_ANALYSIS_PAGE = re.compile(r'<section\b[^>]*\bdata-analysis="[^"]+"', re.I)


def _drawable_moves() -> set[str]:
    """-> the analytical moves the shape library can actually draw.

    Read from `assets/frameworks.json` rather than listed here, because the
    answer is data and a list would rot. A move with no framework, or whose
    every framework is `drawn: native`, cannot be held to using a library
    shape — that is a gap in the registry, not a defect in the page.
    """
    try:
        reg = json.loads((ROOT / "assets" / "frameworks.json")
                         .read_text(encoding="utf-8"))["frameworks"]
    except (OSError, ValueError, KeyError):
        return set()
    return {f.get("move") for f in reg.values() if f.get("shapes")} - {None, ""}


def d32_shape_use(raw):
    """-> per page: does a page that declares an analytical move draw one?

    GATES since 0.1.543. **It counted DOCUMENT-WIDE until 0.1.589**, failing
    only when a document declared moves and drew no library shape anywhere —
    so one shape on one page cleared ten declared moves, which is what a
    measured deliverable did: `1 library shape(s) on 10 analysis page(s)`,
    green. Both prose sites describing this metric said *a page* that declares
    a move draws the library's shape for it (`CLAUDE.md`,
    `references/page-contracts.md`), so the code was the half that was wrong —
    the same shape as RC-431, where the register claimed an enforcement that
    did not exist.

    **A page is held only when its declared move is one the library can draw.**
    That exemption exists because `correlate` had no entry in
    `assets/frameworks.json` at all until 0.1.663 (GAP-032), so a page
    declaring it would have failed through no fault of its author. All five
    moves are drawable now and the exemption currently exempts nothing; it
    stays because the registry can lose a framework again, and `check_repo`'s
    `moves served` guard is what makes that fail CI instead of silently
    reopening the hole.

    The vendored library is 206 tagged units embedded on demand. Reuse is also
    the cheap path: on one measured pair of builds, the deck that drew its
    figures by hand spent 343k output tokens against 115k for the one that
    reused shapes, and output costs ~94x what a cached input token does.
    """
    drawable = _drawable_moves()
    bare, held = [], 0
    for _cls, pid, body in _pages(raw):
        move = _analysis_move(raw, pid)
        if not move or move not in drawable:
            continue
        held += 1
        # A PAGE THAT DECLARES ITS DATA HAS DRAWN FROM ITS OWN NUMBERS, which
        # is the other correct answer to "what did this move produce" and the
        # one D32 could not see. GAP-051: this keys on the MOVE, not on the
        # framework a page chose, so a page correctly drawing a waterfall, a
        # benchmark or a breakdown natively was reported `bare` by a metric
        # that gates at zero. The gap named two ways out and said both were
        # design decisions; this is neither — `data-figure-spec` is a fact
        # already on the page, and D42 already fails the page if the file it
        # names does not hold what the move needs. A figure drawn from a
        # verified data contract is not a figure that skipped the library.
        # On the SECTION TAG, which `_pages()` does not capture — the same
        # shape `_analysis_move` above exists for, and the reason the first cut
        # of this exemption matched nothing.
        if _declares_spec(raw, pid):
            continue
        if not _SHAPE_USE.search(body):
            bare.append(pid)
    return {"shapes": len(_SHAPE_USE.findall(raw)),
            "analysis_pages": len(_ANALYSIS_PAGE.findall(raw)),
            "held": held, "bare": bare,
            "undrawable": sorted(
                {m for m in (_analysis_move(raw, pid)
                             for _c, pid, _b in _pages(raw))
                 if m and m not in drawable})}


def d30_figure_sequence(raw):
    """Figure numbers that do not run 1..k once each, in page order.

    Reported. A caption number is the FIGURE's ordinal and a reader uses it to
    refer to a drawing out loud ("go back to figure four"); a duplicate makes
    the reference ambiguous and a hole makes it wrong. Nothing measured this,
    and the defect is in all three artifacts this package had on disk when the
    check was written: one accepted deck numbered two drawings `Figure 3` and
    had no Figure 4, another ran 2-8 then 12-14 then 9-11 because an appendix
    was cut out of the body and never renumbered, and the SCAFFOLD produced the
    holes on purpose -- it emitted `Figure {page index - 2}`, so every part
    opener consumed a number no drawing ever carried.

    That last one is why this is a check rather than an author's discipline:
    the generator taught the defect, and both decks inherited it.

    Read off `.cap .n`, which is where §4 rule 7 puts the number, and compare
    the sequence against `1..k` in document order. `Exhibit` and the Chinese
    forms are accepted spellings of the same slot.
    """
    nums = [int(m.group(1)) for m in _CAP_N.finditer(raw)]
    if not nums:
        return None
    dupes = sorted({n for n in nums if nums.count(n) > 1})
    holes = sorted(set(range(1, max(nums) + 1)) - set(nums))
    return {"count": len(nums), "sequence": nums, "duplicates": dupes,
            "holes": holes, "out_of_order": nums != sorted(nums)}


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

    A region is anchored by `data-region-label="<id>"` on any element, by a
    legend row carrying `data-legend="<id>"`, or by the globe component's own
    anchor, `data-bloc-label="<id>"` — the vocabulary `globe_svg.py` emits and
    `render-svg.js` re-places per frame. The brand field globe labels all eight
    of its blocs that way, and before this line D18 read the locked brand asset
    as eight unlabelled regions.
    """
    # A REGION IS `class="rg rg-<id>"`, and the id is read from a class list
    # split on whitespace rather than scanned out of the attribute. The scan
    # was wrong twice over: `\b` matched inside the globe's own furniture
    # (`gl-rg-label` read as a region named "label"), and being greedy it kept
    # only the LAST `rg-` token in an attribute, so `class="rg-outline
    # rg-outline-eu"` — which the package's own flat-map emitter writes on
    # every region — lost the first and invented a region called
    # "outline-eu". Both the map's furniture (`.rg-full`, `.rg-outline`,
    # `.rg-label*`) and the globe's are shipped vocabulary in
    # `tokens/region-palette.css`; a region is the token that rides beside the
    # bare `rg` marker.
    ids = set()
    for attr in re.findall(r'class="([^"]*)"', raw):
        classes = attr.split()
        if "rg" not in classes:
            continue
        ids |= {c[3:] for c in classes if c.startswith("rg-") and len(c) > 3}
    if not ids:
        return None
    labelled = set(re.findall(r'data-region-label="([\w-]+)"', raw))
    labelled |= set(re.findall(r'data-legend="([\w-]+)"', raw))
    labelled |= set(re.findall(r'data-bloc-label="([\w-]+)"', raw))
    return {"regions": len(ids), "unlabelled": sorted(ids - labelled)}


def d8_support_line(raw):
    """Every content page carries a support line under the title. Figure pages
    are not exempt: a diagram with nothing introducing it drops the reader in."""
    missing = []
    for cls, pid, body in _pages(raw):
        if "cover" in cls or "closing" in cls:
            continue
        # The agenda is exempt by owner directive at 0.1.522: its title names
        # the document and its rows name the parts, so a line between them
        # restates one or the other. `references/storyline-templates.md` says
        # the agenda may drop its lede whole; this row is that sentence's other
        # half. It was written into the prose one release before it was written
        # here, and the gap showed up as a permanently red row — which is how a
        # reader learns to stop reading rows.
        if "agenda" in cls or pid == "agenda":
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
        # The dark chip is the sanctioned form: lime `color` beside its OWN
        # `--on-lime` backing in the same rule (`.subj`, 0.1.443). The pairing
        # is what makes it legal — 16.44:1 on the chip against 1.21:1 on the
        # canvas — so the carve-out demands the background in the same block,
        # never somewhere an ancestor might provide it.
        if re.search(r"(^|;)\s*background(-color)?\s*:\s*var\(\s*--on-lime\s*[,)]",
                     body):
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
    return markup.strip_tags(body[m.end():i])

# The block patterns tokens/ renders as a STRUCTURE, and the children that
# structure assumes. A class with a rendering, used without the shape that
# rendering was written for, is markup that silently borrows somebody else's
# styling — `.grades` without `.gr` picked up the `.key` callout's red outline
# and left every paragraph outside the box it belonged to.
BLOCK_CONTRACTS = {
    "grades": ("gr",),
    "gr": ("gn",),
    "band": ("k", "v"),
    "swap": ("no", "yes"),
    "card": ("ledname",),
    "vow": ("vn", "vt"),
    # The stat tile (0.1.521): a number and the sentence under it. `.sv` alone
    # is a display number with nothing saying what it counts, which red line 1
    # forbids for the same reason `.lead` owes a `.g`.
    "stat": ("sv", "sn"),
}


def _element_body(raw, match):
    """The inner HTML of the element `match` opens, counting nested tags.

    A non-greedy `(.*?)</\1>` stops at the FIRST closing tag of that name,
    which for a div containing divs is the wrong one — it truncated a `.swap`
    body before its second half and reported a missing `.yes` that was right
    there. A gate that cries wolf is worse than no gate, because it teaches its
    reader to skip the line.
    """
    tag = match.group(1)
    depth, i = 1, match.end()
    opener = re.compile(rf'<{tag}\b', re.I)
    closer = re.compile(rf'</{tag}\s*>', re.I)
    while depth and i < len(raw):
        o = opener.search(raw, i)
        c = closer.search(raw, i)
        if not c:
            return raw[match.end():]
        if o and o.start() < c.start():
            depth += 1
            i = o.end()
        else:
            depth -= 1
            if not depth:
                return raw[match.end():c.start()]
            i = c.end()
    return raw[match.end():]


# _grid_arity lived here and was removed the hour it was written: it counted a
# block's children against its grid's column count, and CSS grid flows extra
# children onto the next row on purpose — `.gr` carries three children in a
# two-column grid and renders correctly. It failed the reference fixture on its
# first run, which is the same disqualifying move D19's first cut made.
#
# The property is real and it is not static. A child starved into a 34px track
# is measurable only once rendered, so it lives in inspect_layout.py as
# `starved_column`.


def d19_vocabulary(raw):
    """Every reference in this document resolves inside this document.

    **This gates.** Five assertions, none of them a judgement about a page:

    1. an icon `<use href="#x">` has a `<symbol id="x">` here;
    2. a block class is used with the children tokens/ renders it through;
    3. a part opener carries `class="page opener"`;
    4. a `[data-globe]` figure has the globe runtime in this document;
    5. a `var(--x)` with no fallback has a `--x` declared here.

    All four are what a deliverable got wrong while passing every other check
    in this file. The icon sprite lives in the reference fixture's BODY, so a
    document assembled by slicing its `<head>` carries none of it — thirteen
    pages of handling terms lost their seal-red shield, and nothing here could
    see it, because a `<use>` pointing at nothing is valid markup that renders
    as empty space.

    This is the deliverable-side mirror of the `probe vocabulary` guard in
    check_repo.py, which says a class a checker asserts must have a rendering in
    tokens/. The same sentence turned around: a class a DOCUMENT uses must have
    the rendering it is asking for, in the document that uses it.

    The fourth assertion is the same defect one layer out. `data-globe` is the
    runtime's selector and nothing else reads it, so the attribute is a
    REFERENCE to a script that has to be in the document — and a `[data-globe]`
    with no runtime is a `<use>` pointing at nothing, told in JavaScript. It
    shipped: a deliverable built by a one-off script that harvested the runtime
    out of a fixture with a regex, matched nothing, and emitted an empty
    `<script></script>`; the cover and closing globes were still frames, all
    three checkers passed it, and the brand contract says that mark is
    "embedded live … so it rotates" (storyline-templates.md, owner directive).
    Motion is not measurable here and is not what this asserts: the runtime is
    either in the file or it is not.

    **The direction matters.** A MARK obliges a RUNTIME, never the reverse. The
    mirrored assertion — a globe drawing obliges `data-globe` — would fail
    fixtures/deck-pass.en.html, which carries the drawing and deliberately
    carries no runtime, and a gate whose first act is to fail this package's own
    passing fixture is the mistake D19's first cut and `_grid_arity` both made.
    A cover globe with no `data-globe` is reported instead, below.
    """
    # EVERY id, not just <symbol>. A <use> may reference any element — the page
    # ground is a <g id="g-ground"> and the icons are <symbol>s — so a check
    # that only collected symbols called the reference implementation broken.
    # A gate whose first act is to fail the fixture is a gate nobody will keep.
    ids = set(re.findall(r'\bid="([^"]+)"', raw))
    symbols = set(re.findall(r'<symbol[^>]*\bid="([^"]+)"', raw))
    used = set(re.findall(r'<use[^>]*\bhref="#([^"]+)"', raw))
    dangling = sorted(used - ids)

    bad_blocks = []
    for cls, needs in BLOCK_CONTRACTS.items():
        # A CLASS IS A WHOLE TOKEN IN THE LIST, not a substring of one.
        # `\bcard\b` matched `f-card` — the SVG PAINT class every drawing uses
        # for a card-coloured fill — so a document with seventy-five painted
        # rects and four correct `.card` blocks reported thirteen cards
        # missing `.ledname`, and a conformance run was scored `fail` on it.
        # `(?<![\w-])` is the same fix D18 needed for `rg-`; this is that bug
        # in the other checker, found by a document that had done nothing
        # wrong.
        for m in re.finditer(
                rf'<(\w+)[^>]*class="[^"]*(?<![\w-]){cls}(?![\w-])[^"]*"[^>]*>',
                raw):
            body = _element_body(raw, m)
            missing = [n for n in needs
                       if not re.search(rf'class="[^"]*(?<![\w-]){n}(?![\w-])',
                                        body)]
            if missing:
                bad_blocks.append((cls, missing))

    openers = []
    for m in re.finditer(r'<section([^>]*)>(.*?)</section>', raw, re.S):
        attrs, body = m.group(1), m.group(2)
        if "openframe" in body and "opener" not in attrs:
            idm = re.search(r'id="([^"]*)"', attrs)
            openers.append(idm.group(1) if idm else "?")

    # `createGlobe` is the word embed_globe.py's own check() looks for in the
    # block it just built (scripts/build/embed_globe.py). One vocabulary, read
    # from both ends — a second spelling here would be FM-04 in miniature.
    marked = len(re.findall(r"\bdata-globe\b", raw))
    globe_no_runtime = bool(marked) and "createGlobe" not in raw

    # REPORTED, never counted. A cover or closing page drawing a globe with no
    # data-globe on it is a brand-contract question (brand.md: the mark is
    # embedded live), and the contract is not decidable from markup the way a
    # missing runtime is — the page may be quoting the drawing on purpose.
    still_marks = []
    for cls, pid, body in _pages(raw):
        if "cover" not in cls and "closing" not in cls:
            continue
        if re.search(r'<svg[^>]*class="[^"]*(?<![\w-])gl(?![\w-])', body) \
                and "data-globe" not in body:
            still_marks.append(pid)

    return {"symbols": len(symbols), "used": len(used), "dangling": dangling,
            "bad_blocks": bad_blocks, "bad_arity": [],
            "openers_missing_class": openers,
            "globe_marks": marked, "globe_no_runtime": globe_no_runtime,
            "globe_marks_missing_hook": still_marks,
            "dangling_vars": _dangling_vars(raw)}


# The attributes a browser resolves as CSS. `style=` is a declaration block;
# the rest are SVG presentation attributes, which is how this package paints
# — `new_deck.py` emits `fill="var(--tx2)"` — and where the reported defect
# lived. Anything else on the page is prose, and prose is not a reference.
_CSS_ATTRS = ("style", "fill", "stroke", "stop-color", "flood-color",
              "lighting-color", "color")


def _css_surfaces(raw) -> str:
    """-> only the text a browser reads as CSS, comments already stripped.

    Declarations and uses were read from DIFFERENT surfaces: `css_of()` reads
    `<style>` blocks, while the scan for `var()` ran over the whole document.
    So a `var()` in a `<pre><code>` example, or in a `data-` attribute, was a
    reference; and a property declared in an inline `style="--x:…"` — which
    this package's own scaffold emits — was not a declaration. Both directions
    were measured on synthetic documents that render correctly in Chromium and
    were reported dangling. A checker failing a document that did the right
    thing is the direction this package treats as the dangerous one.
    """
    parts = [_uncommented(b) for b in
             re.findall(r"<style[^>]*>(.*?)</style>", raw, re.S | re.I)]
    # A DOCUMENTED EXAMPLE IS NOT A DECLARATION. `<pre>`/`<code>` hold markup
    # a reader is meant to see rather than markup a browser applies, and
    # `<script>` holds strings; a `var()` in any of them resolves nothing and
    # obliges nothing.
    body = re.sub(r"<(script|pre|code|textarea)\b.*?</\1>", " ", raw,
                  flags=re.S | re.I)
    attrs = "|".join(_CSS_ATTRS)
    for m in re.finditer(rf'\b(?:{attrs})\s*=\s*(["\'])(.*?)\1', body,
                         re.S | re.I):
        parts.append(m.group(2))
    return "\n".join(parts)


def _var_uses(css: str) -> list[tuple[str, bool]]:
    r"""-> [(name, has_fallback), …] for every `var()`, NESTED ONES INCLUDED.

    `var\(\s*(--[\w-]+)\s*([^)]*)\)` cannot do this, and the miss was the
    reported deck's own shape. `[^)]*` stops at the first `)`, so in
    `var(--display, var(--sans))` the outer match swallows the inner one,
    `finditer` resumes past it, and NEITHER name is examined. Verified in
    Chromium: that string computes to `rgb(0, 0, 0)` — black, exactly the
    defect — and the first version of this check returned nothing for it.

    **How that got written is the lesson.** The docstring illustrated the
    fallback rule with `var(--display, Georgia, serif)`. The string in the deck
    is `var(--display, var(--sans))`. A real instance was read and then a
    paraphrase of it was what the pattern was written against — and the
    paraphrase happens to be the one form the regex handles, so the planted red
    went green. CLAUDE.md convention 15, in the release that cites convention 15.

    Every `var(` is found on its own and its fallback decided by counting
    parentheses forward from it, so nesting is depth-independent.
    """
    out = []
    for m in re.finditer(r"var\(\s*(--[\w-]+)", css, re.I):
        depth, i, comma = 1, m.end(), False
        while i < len(css) and depth:
            ch = css[i]
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            elif ch == "," and depth == 1:
                comma = True
                break
            i += 1
        out.append((m.group(1), comma))
    return out


def _dangling_vars(raw) -> list[str]:
    """-> `var(--x)` used with no `--x` declared and no fallback. Sorted.

    THE FIFTH REFERENCE, and the one a reader can see. `var(--undefined)` with
    no fallback is not an error to a browser: the property is invalid at
    computed-value time and the element falls back to the INITIAL value. For
    `fill` on an SVG shape the initial value is **black**.

    Reported by the owner, looking at a deck this package had passed. Two pages
    of a conformance deck rendered their drawings in black instead of the brand
    green — page 11's four shapes and three of page 8's eight — because the
    author wrote `fill="var(--bg1)"` seven times and the token block declares
    `--bg`, never `--bg1`. Confirmed in a browser: `getComputedStyle(...).fill`
    is `rgb(0, 0, 0)`. Every gate passed the document, including D20, which
    compares the values a document DECLARES against `tokens/` and has nothing
    to say about a name it never declared at all, and D1, which measures a
    declared text colour against a declared surface and had no surface to
    measure — so it printed `0`, which is what it prints when a document is
    clean. A review then found a SECOND shipped deliverable with the same
    defect, thirteen black boxes in an r6 conformance artifact.

    `check_repo` has held THIS repository to this rule for releases — every
    `var()` in `tokens/` must resolve to a custom property `tokens/` defines.
    This is that sentence turned to face the deliverable, which is the same
    turn D19's block-class assertion already makes.

    **A fallback is a definition.** `var(--display, var(--sans))` names what to
    use when the property is absent, so it renders what its author asked for
    and is not a dangling reference.

    **What this deliberately cannot see**, so that nobody reads its silence as
    more than it is: a declaration is any `--x:` in a CSS surface, with no
    notion of whether its selector matches or its `@media` applies. So
    `@media print { :root { --x: … } }` counts as declared while rendering
    black on screen. Deciding that needs the cascade, which is a browser's job
    — `inspect_layout` is where a rendered-geometry question belongs, and this
    one is left named rather than half-answered.
    """
    css = _css_surfaces(raw)
    declared = set(re.findall(r"(--[\w-]+)\s*:", css))
    # `@property --x { … }` is the standards-track declaration and its name is
    # followed by `{`, so the `:` scan cannot see it.
    declared |= set(re.findall(r"@property\s+(--[\w-]+)", raw, re.I))
    dangling: dict[str, int] = {}
    for name, has_fallback in _var_uses(css):
        if name in declared or has_fallback:
            continue
        dangling[name] = dangling.get(name, 0) + 1
    return [f"{n} ({c}x)" for n, c in sorted(dangling.items())]


def _uncommented(text: str) -> str:
    r"""-> the text with CSS and HTML comments blanked.

    Applied to `<style>` bodies rather than the whole document: `/\*.*?\*/`
    over prose opens a fake comment at any glob path (`scripts/*.py`) and
    closes it at the next `*/`, blanking whatever lies between. No document in
    the corpus does that today; scoping it costs nothing and removes the shape.
    """
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    return re.sub(r"<!--.*?-->", " ", text, flags=re.S)


def d12_commercial_footer(raw, site=None):
    """Every page carries its handling terms and the origin of the document.

    **The first of the four design checks that fail the run**, and the reason the
    other three are phrased against it. Everything else here is
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
        # The zh half was missing until the first real Chinese deliverable: a
        # public roadshow deck with honest terms failed all nineteen pages.
        if not any(w in low for w in ("confidential", "privileged", "internal use",
                                      "do not forward", "proprietary",
                                      "保密", "内部使用", "请勿转发", "请勿外传",
                                      "公开路演", "引用请注明出处")):
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
# The markers were English-only until 0.1.659, and the cost was measured on the
# release that made this gate the SOLE enforcement of the measure slot: a deck
# carrying four unfilled Chinese slots printed `ok D14_placeholders 0` — byte
# identical to a finished document. That is FM-24 in a gate, and D12 eleven
# hundred lines down already learned the same lesson ("the zh half was missing
# until the first real Chinese deliverable"). A deliverable is authored in the
# reader's language, so a marker list in one language is a gate that reads one
# language and reports clean on the rest.
PLACEHOLDER_MARKERS = re.compile(
    r"to\s*fill|to[-\s]?do\b|\btbd\b|\btba\b|fill[-\s]?in|\binsert\b|placeholder"
    r"|\bx{2,}\b|lorem|\bname here\b|your\s+\w+\s+here"
    r"|待填|待补|待定|填写|占位|此处填|待确认"
    r"|\u8981\u5165\u529b|\u672a\u5b9a"
    # zh / ja: the ways an author writes "fill this in" in a CJK deliverable.
    r"|^\s*$", re.I)
# `[...]` and `[…]` are deliberately NOT markers. Bracketed ellipsis is the
# standard editorial mark for an elision inside a quotation, which a consulting
# document uses legitimately, and a gate that fails on it is a gate people learn
# to route around.

# THE SCAFFOLD'S OWN SLOTS, which are not bracketed. `new_deck.py` hands an
# author a document that already renders, and the price of that is a page of
# furniture worded to be replaced: a title, a support line, attribute rows, a
# glossary entry, a colophon. A 34-page review reached its reader with
# `REPLACE ME` as its browser-tab title, and nothing here looked, because every
# marker this file knew wore brackets.
#
# The first cut of this list held two of them, so an author who fixed the two
# D14 named still shipped a cover whose support line read "One sentence saying
# what this is." The list lives HERE, because what a checker refuses is the
# checker's business and a deliverable grader may not import the scaffold
# generator — and `check_repo`'s **scaffold slots** guard holds it against
# what `new_deck.py` actually emits, in both directions: a string here that
# the scaffold no longer writes is stale, and a scaffold whose slots survive a
# full substitution pass is a scaffold with furniture this list has not
# learned. Completeness beyond that stays with the reviewer.
#
# Case-sensitive: these match the scaffold's literal output, not prose that
# mentions replacing things. (The fixture's `www.example.org` footer is
# deliberately NOT here: fixtures keep a reserved domain precisely so no
# engagement fact ships in this repository, and a deliverable's site slot
# stays with the reviewer — IDEA-9.)
AUTHOR_FILL = (
    "REPLACE ME",
    # `lumi-style VERSION` was here until 0.1.590, when the scaffold started
    # substituting the real version — a slot the package could always fill was
    # costing every build a red round and a hand edit. A pattern guarding
    # nothing misleads the next reader, which is what `scaffold slots` says.
    # A colophon that names no version is not unguarded: `gate_registry.held`
    # reads it, and an absent stamp is held to every gate.
    "A title that states the argument about its",
    "What the reader carries out about its",
    "One sentence saying what this is.",
    "The argument in one paragraph.",
    "What it means in this document, one sentence.",
    "A title naming its subject and carrying a fact",
    "The support line, one sentence and not a summary.",
    # The scaffold's worked shape example (0.1.499). Its two labels are
    # furniture like every other string here: a figure shipped with them is a
    # figure whose author never composed it with the page's own words, which is
    # §4.2's whole point — a library shape is a starting geometry, not a
    # finished figure.
    "the step this end names",
    "and the step it leads to",
    # The colophon's provenance clause (0.1.450). The scaffold's colophon read
    # "Built with lumi-style VERSION." and stopped there — which trips D6, the
    # check that asks the DOCUMENT where its numbers came from, on every page
    # at once. A scaffold that hands an author a document failing a check it
    # cannot see is the shape this file exists to close, so the clause is in
    # the scaffold and its slot is here.
    # One line since 0.1.674: the colophon became a rendered field with a
    # fallback, so the line break that used to sit inside it is gone. The
    # `scaffold slots` guard caught this the moment the template changed,
    # which is the whole reason a pattern is held to its emitter.
    "WHERE THE NUMBERS CAME FROM",
)
SCAFFOLD_SLOTS = re.compile("|".join(re.escape(s) for s in AUTHOR_FILL))


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
    for _cls, pid, page in _pages(body) or [("", "(document)", body)]:
        text = markup.visible_text(page)
        for m in PLACEHOLDER.finditer(text):
            inner = m.group(0).strip("[]{}<>").strip()
            if not PLACEHOLDER_MARKERS.search(inner):
                continue
            found.append({"page": pid, "text": m.group(0)[:40]})
        for m in SCAFFOLD_SLOTS.finditer(text):
            found.append({"page": pid, "text": m.group(0)[:40]})
    # The head is not a page, and the title lives there. The per-page walk
    # above never sees it, which is exactly how `REPLACE ME` shipped.
    head_end = body.find("<section")
    if head_end != -1:
        head_text = markup.strip_tags(body[:head_end])
        for m in SCAFFOLD_SLOTS.finditer(head_text):
            found.append({"page": "(head)", "text": m.group(0)[:40]})
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



def _equivalent_layouts(raw):
    """-> {name: canonical} for layouts this document's own CSS renders alike.

    D9 counts declared class names. In portrait, `tokens/lumi-layouts.css`
    collapses `split`, `split-wide`, `split-narrow` and `sidebar-notes` to one
    grid — `1fr / auto auto 1fr` — so all four render identically and a
    document can raise its distinct-layout count from three to six by editing
    class names and changing nothing a reader sees. That is a metric satisfied
    instead of met, which is the failure this package's own opening provenance
    note is about.

    Derived from the document's stylesheet rather than hard-coded: a rule that
    sets a grid for several `.body.<name>` selectors at once is the statement
    that those names are one layout at this geometry. Read from the document,
    so a deliverable carrying an older token block is judged by the CSS it
    actually ships.
    """
    # FROM THE REAL <body>. Anchoring on the string `<body` is not enough: the
    # stylesheet's own comment about the geometry rule contains a literal
    # `<body data-geometry="landscape">`, so on a portrait document the first
    # match reads "landscape". markup.body_attr skips comments, styles and
    # scripts first — the same skip embed_shapes needed at 0.1.492, shared now
    # rather than described.
    geometry = markup.body_attr(raw, "data-geometry")
    if not geometry:
        return {}
    alias: dict[str, str] = {}
    # Split on braces and walk. A regex with two unbounded classes around a
    # literal backtracks catastrophically on a 680KB deliverable — it hung for
    # two minutes on the first document it was pointed at, which is a good
    # reason to scan linearly instead of writing a cleverer pattern.
    chunks = raw.split("}")
    for chunk in chunks:
        head, _, body = chunk.rpartition("{")
        if not head or "grid-template-columns" not in body:
            continue
        if f'data-geometry="{geometry}"' not in head:
            continue
        names = re.findall(r"\.body\.([a-z0-9-]+)", head)
        if len(names) < 2:
            continue
        canonical = sorted(names)[0]
        for n in names:
            alias[n] = canonical
    return alias


def d9_layout_variety(raw):
    """One layout on 25 consecutive pages is what this metric exists to stop."""
    alias = _equivalent_layouts(raw)
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
            used.append(alias.get(layout, layout))
    if not used and not unknown:
        return None
    counts: dict[str, int] = {}
    for layout in used:
        counts[layout] = counts.get(layout, 0) + 1
    total = len(used) + len(unknown)
    top = max(counts.values()) if counts else 0
    return {
        "pages": total, "distinct": len(counts),
        "top_share": round(100.0 * top / total, 1) if total else 0.0,
        "top_layout": max(counts, key=counts.__getitem__) if counts else None,
        "counts": dict(sorted(counts.items(), key=lambda kv: -kv[1])),
        "unknown": unknown,
        # Named so a reader of the report can see WHY two class names counted
        # as one, rather than wondering whether the metric is broken.
        "merged": {k: v for k, v in sorted(alias.items()) if k != v},
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



# THE TWO ICON SETS THIS PACKAGE SHIPS, and the only places an icon may come
# from (design-rules §6). Named here rather than globbed so a directory added by
# accident cannot become a source of icons.
ICON_SETS = ("lucide", "koboyo")
# What counts as the geometry of a drawing: the attributes that decide its
# SHAPE, in document order. Comparing raw markup instead would fail on a
# reordered attribute or a self-closing tag, which is a difference in spelling
# rather than in the drawing.
GEOMETRY_ATTRS = ("d", "points", "cx", "cy", "r", "rx", "ry",
                  "x1", "y1", "x2", "y2", "x", "y", "width", "height")


# Path data written two ways for one drawing. `M 4 6 L 8 10`, `M4 6L8 10` and
# `M4,6L8,10` are the same line; an SVG minifier produces the second and third
# from the first. Comparing the raw strings would report a minified copy of a
# SHIPPED icon as somebody else's drawing — a false red on a gating metric,
# which is the failure class that rewrites a correct document.
ATTR = re.compile(r"""([a-z-]+)=(?:"([^"]*)"|'([^']*)')""")
_PATH_TOKEN = re.compile(r"[A-Za-z]|-?\d*\.?\d+(?:[eE][-+]?\d+)?")


def _path_tokens(value: str) -> tuple:
    """-> a path's commands and numbers, separated from how they were spaced."""
    return tuple(_PATH_TOKEN.findall(value))


def _geometry(markup: str) -> tuple:
    """-> the drawing inside `markup`, as a comparable tuple.

    Reads shape elements in order and keeps the attributes that decide their
    geometry. Path and polygon data is TOKENISED rather than string-compared,
    so `M 4 6 L 8 10` and `M4,6L8,10` — the same line, one of them minified —
    compare equal. Every other attribute is whitespace-collapsed only.

    What it deliberately does NOT read is `transform`: a scaled or translated
    copy of a shipped icon still compares equal to it. That is a gap and not an
    oversight — the rule this serves asks where the drawing came from, and a
    transformed copy came from the same place.
    """
    out = []
    for el in re.finditer(r"<(path|circle|rect|ellipse|line|polygon|polyline)\b"
                          r"([^>]*)>", markup):
        # EITHER QUOTE. Reading only double quotes gave a single-quoted
        # `d='M20 6'` an all-empty geometry tuple, so a shipped icon written
        # that way was reported `altered` while two DIFFERENT single-quoted
        # icons compared equal — the gate failing in both directions at once.
        attrs = {}
        for m in re.finditer(ATTR, el.group(2)):
            attrs[m.group(1)] = m.group(2) if m.group(2) is not None else m.group(3)
        vals = []
        for a in GEOMETRY_ATTRS:
            v = attrs.get(a, "")
            vals.append(_path_tokens(v) if a in ("d", "points")
                        else re.sub(r"\s+", " ", v).strip())
        out.append((el.group(1), tuple(vals)))
    return tuple(out)


def _shipped_icons(root: pathlib.Path | None = None) -> dict:
    """-> {name: {geometry, ...}} for every icon in the sets this package ships.

    **A SET of geometries per name, because both sets are authorized.** The two
    directories collide on 32 of koboyo's 36 names — `shield`, `globe`, `key`,
    `rocket`, `scale` and 27 more — and the first version kept only the first
    one it saw, which was always lucide's. So a document drawing a genuinely
    shipped koboyo silhouette was reported `altered`: the set's own name over
    the set's own drawing, on a gating metric. Matching against ANY set that
    carries the name is what "the two sets this package ships" means.
    """
    base = (root or ROOT) / "assets" / "icons"
    shipped: dict[str, set] = {}
    unreadable = []
    for setname in ICON_SETS:
        d = base / setname
        if not d.is_dir():
            continue
        for f in d.glob("*.svg"):
            try:
                shipped.setdefault(f.stem, set()).add(
                    _geometry(f.read_text(encoding="utf-8")))
            except OSError as exc:                         # pragma: no cover
                # NAMED, not swallowed. Dropping the file silently makes every
                # document using that icon fail as "drawn by hand", which points
                # the reader at the document instead of at this file.
                unreadable.append(f"{setname}/{f.name}: {exc}")
    if unreadable:                                         # pragma: no cover
        print("  note  icon set files that could not be read, so any document "
              "using them will read as hand-drawn: " + "; ".join(unreadable))
    return shipped


def d33_icon_provenance(raw, root=None):
    """-> {checked, unknown, altered}: icons that did not come from the sets.

    **This gates.** design-rules §6: "Never add icons to 'look rich'. Never draw
    one ad hoc" — every icon comes from the two sets this package ships. The
    rule had no check, and the owner's first instruction after opening a
    conformance deck was that the part-opener icon must come from
    `assets/icons/`.

    **Keyed on USE AS AN ICON, never on the id's spelling.** The first version
    matched `id="i-[a-z0-9-]+"` and counted nothing else, so `<symbol
    id="handdrawn">` — or `id="i-myIcon"`, one capital letter — was not
    reported as unknown, it was not COUNTED, and the gate returned `ok` on a
    document whose every icon was drawn by hand. A gate a naming choice walks
    past is not a gate. The material says what an icon is: an inline `svg.ic`
    pointing at a symbol, which is the vocabulary §6 and `tokens/` both use, and
    which resolved 35, 40 and 20 uses across the three documents on record. It
    also leaves alone the symbols that are NOT icons — the accepted reference
    defines a library shape and a trademark mark, and neither is drawn as `.ic`.

    Two findings, kept apart because they mean different things: a name in
    neither set was invented, and a shipped NAME over a different drawing is the
    set's label on somebody else's path.
    """
    shipped = _shipped_icons(root)
    if not shipped:
        return None                       # no sets to compare against; say so
    symbols = {m.group(1): m.group(2) for m in re.finditer(
        r'<symbol[^>]*\bid="([^"]+)"[^>]*>(.*?)</symbol>', raw, re.S)}
    used = set(re.findall(
        r'<svg[^>]*class="(?:[^"]*\s)?ic(?:\s[^"]*)?"[^>]*>\s*'
        r'<use[^>]*href="#([^"]+)"', raw))
    unknown, altered = [], []
    for ref in sorted(used):
        geo = symbols.get(ref)
        if geo is None:
            continue          # a reference resolving to nothing is D19's finding
        # `i-radar` is `radar.svg`. An id with no prefix is looked up as itself,
        # so a hand-drawn `#handdrawn` is reported rather than skipped.
        name = ref[2:] if ref.startswith("i-") else ref
        if name not in shipped:
            unknown.append(ref)
        elif _geometry(geo) not in shipped[name]:
            altered.append(ref)
    return {"checked": len(used), "unknown": unknown, "altered": altered}


# A figure name's ceiling, by the cell it sits in (design-rules §4 rule 7).
# REPORTED here and gated in `inspect_layout` — the true measurement is whether
# the rendered name wraps, and characters are the early warning an author can
# act on while writing rather than after rendering.
CAPTION_NAME_CHARS = {"full": 100, "split": 60}


def d37_caption_scope(raw):
    """-> {captions, with_source, long_names}: what sits under a figure.

    **This gates on the source line.** design-rules §4 rule 8 says the caption
    below a figure carries the number and the name and nothing else; the source
    is the drawing's own last text node (rule 17). The two bullets contradicted
    each other for several releases and every conformance deck followed the
    losing one, which produced `…off the green lineIllustrative programme-board
    values` — two roles in one inline flow with no separator, because nothing in
    the stylesheet supplies one and nothing required the author to.

    The long-name count is REPORTED. The ceiling is a character count standing
    in for a rendered line, and the rendered line is what `caption_name_wrap`
    measures; failing a document twice for one defect teaches a reader to skim.
    """
    # ANY HTML ELEMENT, AND NO SVG ONE. Two corrections in one line, both found
    # by running this against real decks rather than reading it:
    #
    # * It matched `<p` and `<div` only, and a deck wrote
    #   `<figcaption class="cap">` — so a source line walked past a GATING check
    #   on a tag name, the same shape as D33's `i-` id.
    # * Widening it to any element then flagged a deck that was CORRECT: it had
    #   put the source inside the drawing as rule 17 asks, wrapped in
    #   `<g class="cap">`, and the caption below the figure held only the number
    #   and the name. An in-figure source is the rule being followed, so a `.cap`
    #   inside an `<svg>` is not the caption this metric grades.
    svg_spans = [(m.start(), m.end())
                 for m in re.finditer(r"<svg\b.*?</svg>", raw, re.S | re.I)]
    caps = [m.group(2) for m in re.finditer(
        r'<([a-z]+)[^>]*class="(?:[^"]*\s)?cap(?:\s[^"]*)?"[^>]*>(.*?)</\1>',
        raw, re.S | re.I)
        if not any(a <= m.start() < b for a, b in svg_spans)]
    with_source, long_names = [], []
    for i, c in enumerate(caps, start=1):
        if re.search(r'class="(?:[^"]*\s)?srcline(?:\s[^"]*)?"', c):
            with_source.append(i)
        # The name is what is left once the number and any source are removed.
        name = markup.visible_text(
            re.sub(r'<span[^>]*class="(?:[^"]*\s)?(?:n|srcline)'
                   r'(?:\s[^"]*)?"[^>]*>.*?</span>', " ", c, flags=re.S))
        if len(name) > CAPTION_NAME_CHARS["full"]:
            long_names.append((i, len(name)))
    return {"captions": len(caps), "with_source": with_source,
            "long_names": long_names}


# Families a browser resolves without a file: the generic keywords, plus the
# CJK fallbacks a Latin face cannot carry and design-rules §2 explicitly scopes
# the embed rule away from ("the embed rule is scoped to the Latin faces").
GENERIC_FAMILIES = {
    "serif", "sans-serif", "monospace", "cursive", "fantasy", "system-ui",
    "ui-monospace", "ui-sans-serif", "ui-serif", "ui-rounded", "inherit",
    "initial", "unset", "-apple-system", "blinkmacsystemfont",
    "pingfang sc", "hiragino sans gb", "noto sans sc", "microsoft yahei",
    "heiti sc", "songti sc", "arial", "helvetica", "helvetica neue",
}


def d36_font_family(raw):
    """-> {embedded, declared, unembedded}: faces the document asks for and
    does not carry.

    **Reported, not gated, and the reason is in GAP-027.** design-rules §2 says
    a Latin face is embedded as a data URI and never linked. `--mono` names four
    faces and this package embeds none of them, so every document it has ever
    produced would fail this — the accepted reference included. A gate that
    fails the calibration anchor is measuring the tokens, not the document, and
    the tokens are the thing to fix.

    What it is worth reporting anyway: an owner review read the cover's key
    column as "not bold" twice, five releases apart, on a rule that measures as
    weight 700 both times. The weight was never the defect; the face was, and
    nothing said so.
    """
    embedded = {m.group(1).strip().strip('"\'').lower() for m in re.finditer(
        r"@font-face\s*\{[^}]*?font-family:\s*([^;}]+)", raw, re.S | re.I)}
    # THE STACK LIVES BEHIND A TOKEN. Almost every rule in this package says
    # `font-family: var(--din)`, so a scan that read only `font-family:` values
    # found nothing but variable names and reported a clean document. The
    # families are in the custom property, and only the ones a rule actually
    # reaches through are worth reporting — an unused token is not a face the
    # document asks for.
    stacks = dict(re.findall(r"(--[\w-]+):\s*([^;}]*(?:serif|monospace|'|\")[^;}]*)",
                             raw, re.I))
    used = set(re.findall(r"font-family:\s*var\(\s*(--[\w-]+)", raw, re.I))
    values = [stacks[v] for v in used if v in stacks]
    values += [m.group(1) for m in re.finditer(r"font-family:\s*([^;}]+)", raw, re.I)
               if "var(" not in m.group(1)]
    declared, unembedded = set(), set()
    for value in values:
        families = [f.strip().strip('"\'').lower() for f in value.split(",")]
        families = [f for f in families if f]
        declared |= set(families)
        # ONLY THE FIRST. The rest of a stack is the FALLBACK, and naming faces
        # you do not ship is what a fallback IS — "SF Mono, Menlo, Consolas"
        # after an embedded primary is correct, not a finding. Reporting the
        # whole stack flagged three fallbacks on a document that embeds
        # everything it asks for.
        if families and families[0] not in embedded \
                and families[0] not in GENERIC_FAMILIES:
            unembedded.add(families[0])
    return {"embedded": sorted(embedded), "declared": len(declared),
            "unembedded": sorted(unembedded)}


# A page span in an agenda row — "pages 4 to 7", "on pages 8-11". The rule names
# this shape as the thing an agenda row must not be.
AGENDA_PAGE_SPAN = re.compile(r"\bpages?\s*\d", re.I)


BOOKENDS = ("cover", "closing")
# A document that replaces the brand mark says so, on `<body>`, in words.
#
# **The default is the field globe and a replacement is the owner's call, not
# the author's** (owner directive, 2026-08-22: "规则是允许调整，但在用户没有显示
# 要求调整，默认就是选择的 3D 地球" — a replacement is permitted only when it was
# explicitly asked for). `storyline-templates.md` has always allowed a document
# to "render its own subject as geometry"; what it never had was a way to tell a
# requested replacement from a mark that simply went missing. Without one, an
# agent that deleted the brand from both bookends and drew a hundred-cell waffle
# of a collection statistic passed every gate in this package, and the owner
# found it by opening the file.
MARK_WAIVER = "data-brand-mark"


def _brand_globe_signature():
    """The locked asset's own geometry, read from the asset.

    Never a constant here: `assets/brand/lumivate/globe-field.svg` is generated
    and locked, and a signature typed into this file would be a second copy of a
    thing that regenerates — the drift class this repository has fixed
    twenty-six times. Sorted `d` attributes plus the node count, so an attribute
    reordering or a re-indent does not read as a different mark.
    """
    svg = (ROOT / "assets" / "brand" / "lumivate" / "globe-field.svg").read_text(
        encoding="utf-8")
    return _mark_signature(svg)


def _mark_signature(svg: str) -> str:
    ds = re.findall(r'\sd="([^"]+)"', svg)
    nodes = len(re.findall(r"<circle[\s/>]", svg))
    return hashlib.sha256(("|".join(sorted(ds)) + f"#{nodes}").encode()).hexdigest()[:12]


def _bookend_marks(raw):
    """-> {kind: (signature, shape census)} for each bookend page present.

    A bookend with no mark cell, or a cell with no drawing, maps to None — the
    page is here and the mark is not, which is a finding rather than a skip.
    """
    out: dict[str, tuple | None] = {}
    for kind in BOOKENDS:
        page = re.search(r'<section[^>]*class="page ' + kind + r'"[^>]*>(.*?)</section>',
                         raw, re.S | re.I)
        if not page:
            continue
        body = page.group(1)
        # A CLASS IS A TOKEN IN A LIST, NOT A STRING. The first cut looked for
        # `class="markcell"` exactly and read `class="markcell fig trade"` — the
        # owner's own globe demo — as a page with no mark at all. Three false
        # checker failures in this repository have come from matching a class
        # without its boundaries; this is the fourth, and calibrating on her
        # folder caught it where reading the code had not.
        cell = re.search(r'<[^>]*\sclass="[^"]*(?<![\w-])markcell(?![\w-])[^"]*"',
                         body, re.I)
        if not cell:
            out[kind] = None
            continue
        svg = re.search(r"<svg.*?</svg>", body[cell.start():], re.S | re.I)
        out[kind] = None if not svg else (
            _mark_signature(svg.group(0)),
            {sh for sh in ("rect", "path", "circle", "polygon", "polyline",
                           "ellipse", "use")
             if re.search(r"<" + sh + r"[\s/>]", svg.group(0))})
    return out


def d39_bookend_mark(raw):
    """One mark, twice — the cover's and the closing's are the same mark.

    `brand.md`: "LUMI's mark appears twice in a deck — the cover and the
    closing." Compared by which shape KINDS are present, never by their counts:
    two frames of a live globe legitimately differ because the runtime turns it,
    and a census demanding equal counts would fail a correct document for
    rotating — the mistake `_grid_arity` and D19's first cut both made.

    Calibrated across the owner's folder: one document reds,
    `LUMI-SIFT-intro.0.1.522.zh-Hans.html`, whose cover carried a funnel diagram
    while its closing kept the globe — and whose own r3 and r4 revisions made the
    two agree. The red names what those revisions already fixed.
    """
    marks = _bookend_marks(raw)
    if len(marks) < 2 or not all(marks.values()):
        return None                     # D40 owns an absent mark
    kinds = {k: v[1] for k, v in marks.items()}
    return {"differ": kinds[BOOKENDS[0]] != kinds[BOOKENDS[1]],
            "kinds": {k: sorted(v) for k, v in kinds.items()}}


def d40_bookend_is_the_brand(raw):
    """Each bookend carries the LOCKED field globe, or the document says why not.

    **The rule the owner stated on 2026-08-22**: a replacement is allowed and it
    is hers to ask for, so with no explicit instruction the mark is the 3D
    globe. This asserts exactly that and nothing about taste — the drawing's
    geometry either matches the locked asset or it does not, and a document that
    replaces it declares `<body data-brand-mark="…">` naming what was asked for.

    What it caught the day it was written: an agent replaced the brand on BOTH
    bookends with a hundred-cell waffle of a collection statistic. D19 could not
    see it and says so in its own docstring — "A MARK obliges a RUNTIME, never
    the reverse" — so a bookend with no globe at all was invisible to every gate
    in this file.

    The runtime is deliberately not asserted here. D19 already holds a
    `data-globe` mark to its runtime, and `fixtures/deck-pass.en.html` carries
    the brand drawing as a still frame on purpose (it is a checker input and
    ships no scripts). Two gates asserting one thing is how a document ends up
    with two explanations of one red.
    """
    waiver = markup.body_attr(raw, MARK_WAIVER)
    if (waiver or "").strip():
        return []                       # a declared replacement; D39 still binds
    want = _brand_globe_signature()
    out = []
    for kind, mark in _bookend_marks(raw).items():
        if mark is None:
            out.append(f"{kind}: no mark at all")
        elif mark[0] != want:
            out.append(f"{kind}: not the locked field globe "
                       f"(drawn with {'+'.join(sorted(mark[1])) or 'nothing'}); "
                       f"declare {MARK_WAIVER} if this replacement was asked for")
    return out


def d38_agenda_rows(raw):
    """-> {rows, unmarked, with_pages, echoing}: what each launch row does.

    Two findings GATE and one reports, by owner ruling 2026-08-22 after she read
    three conformance agendas side by side and named one correct.

    * **Every claim carries the lime chip.** storyline-templates: "The energy
      comes from weight and the lime chip, never from a louder ground." The
      accepted reference marks all three of its claims; two conformance decks
      marked none of theirs, and their rows read as a list rather than as the
      deck's argument.
    * **No page spans.** The same section: a row reading "the ban list, the rule
      set, the gates: pages 4 to 7" is "a table of contents wearing an agenda's
      clothes ... page spans are apparatus and sit in the apparatus position."
      One deck wrote "on pages 4 to 7" in both its rows.
    * **The run line does not restate the claim** — reported, not gated. The
      test is word overlap against the run's opening, which is crude enough to
      catch a paraphrase that is not one; a person decides.
    """
    for _cls, pid, body in _pages(raw):
        if not _is_agenda_page(pid, body):
            continue
        rows = re.findall(
            r'<p[^>]*class="(?:[^"]*\s)?gn(?:\s[^"]*)?"[^>]*>(.*?)</p>\s*'
            r'<p[^>]*class="(?:[^"]*\s)?gq(?:\s[^"]*)?"[^>]*>(.*?)</p>',
            body, re.S)
        if not rows:
            return None                 # not a launch sequence; D35's question
        unmarked, with_pages, echoing = [], [], []
        for i, (claim, run) in enumerate(rows, start=1):
            if not re.search(r'class="(?:[^"]*\s)?hl(?:\s[^"]*)?"', claim):
                unmarked.append(i)
            run_text = markup.visible_text(run)
            if AGENDA_PAGE_SPAN.search(run_text):
                with_pages.append(i)
            claim_words = set(markup.visible_text(claim).lower().split())
            head = markup.visible_text(run).lower().split()[:6]
            if claim_words and len(claim_words & set(head)) >= 3:
                echoing.append(i)
        return {"rows": len(rows), "unmarked": unmarked,
                "with_pages": with_pages, "echoing": echoing}
    return None


def d34_icon_uniqueness(raw):
    """-> {pages, distinct, reused}: eyebrow icons standing for more than one
    subject.

    **Reported, not gated, and the reference is why.** design-rules §6 says an
    icon means exactly one thing within a document — but the accepted reference
    deck reuses three of its twelve eyebrow icons across two and three pages
    each, and whether that is one meaning restated or two meanings collided is a
    judgement about the pages, not about the markup. A gate here would fail the
    document the owner accepted, so it counts and a person decides.

    What it does answer is the owner's actual complaint, which was blunter than
    the rule: two part openers and seven of eight content pages carrying one
    icon. That shows up here as a reuse count, loudly.

    Class tokens are matched with the whole-token form, not `\b`: `\bic\b`
    matches `fig-ic` and `\beyebrow\b` matches `sub-eyebrow`, because a word
    boundary sits at a hyphen. That has produced three false checker failures in
    this repository already.

    The AGENDA is out of scope. Its eyebrow icon names the act of routing rather
    than a subject being argued, so sharing one with a content page is not two
    meanings on one icon — and counting it made this package's own model
    document report a reuse it should not.
    """
    pat = re.compile(r'<\w+[^>]*class="(?:[^"]*\s)?eyebrow(?:\s[^"]*)?"[^>]*>\s*'
                     r'<svg[^>]*class="(?:[^"]*\s)?ic(?:\s[^"]*)?"[^>]*>\s*'
                     r'<use[^>]*href="#([^"]+)"')
    used: dict[str, list] = {}
    for cls, pid, body in _pages(raw):
        if any(k in cls for k in ("cover", "closing", "opener")):
            continue
        if pid == "agenda":
            continue
        m = pat.search(body)
        if m:
            used.setdefault(m.group(1), []).append(pid)
    reused = {k: v for k, v in used.items() if len(v) > 1}
    return {"pages": sum(len(v) for v in used.values()),
            "distinct": len(used), "reused": reused}


# Void elements, plus the SVG shapes a document writes self-closing. HTML's
# parser has no list of its own for the SVG ones, and `<circle cx=..>` written
# WITHOUT a slash is a start tag that never closes — which is the shape that
# defeated the first version of the scan below.
VOID_TAGS = frozenset((
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
    "param", "source", "track", "wbr",
    "path", "circle", "rect", "ellipse", "line", "polygon", "polyline", "use",
    "stop", "image",
))


class _ChildScan(HTMLParser):
    """The depth-1 children of a fragment, and whether the markup was balanced.

    **A tag STACK, not a depth counter.** The counter version recorded nothing
    when an element was left unclosed, so "no children" was indistinguishable
    from "no strays" — and worse, on a body whose depth happened to return to
    zero at its own closing tag it recorded the entire remaining content as ONE
    child under the first child's class name, swallowing a stat band inside what
    it believed was the lede. Both readings made D35 report `ok` on an agenda
    carrying a stat band, which is convention 8's "a check that did not run is
    not a check that passed" recreated inside a gate on the release that added
    it.

    A stack catches it: a closing tag that does not match the tag on top is
    proof the fragment cannot be read, and `balanced` says so. Callers must
    treat that as a finding.
    """

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack: list = []
        self.kids: list = []
        self.balanced = True
        self._open = None            # (class, offset) of the depth-1 child

    def _offset(self):
        line, col = self.getpos()
        return self._line_starts[line - 1] + col

    def feed_fragment(self, fragment: str):
        self.raw = fragment
        # getpos() reports (line, column), so an absolute offset needs where
        # each line starts.
        self._line_starts = [0]
        for ln in fragment.split("\n")[:-1]:
            self._line_starts.append(self._line_starts[-1] + len(ln) + 1)
        self.feed(fragment)
        self.close()
        if self.stack:
            self.balanced = False    # something was never closed
        return self.kids, self.balanced

    def handle_starttag(self, tag, attrs):
        if tag in VOID_TAGS:
            return
        if not self.stack:
            cls = dict(attrs).get("class") or ""
            self._open = (cls, self._offset() + len(self.get_starttag_text() or ""))
        self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        if not self.stack:
            cls = dict(attrs).get("class") or ""
            self.kids.append((cls, ""))

    def handle_endtag(self, tag):
        if tag in VOID_TAGS:
            return
        if not self.stack:
            # The container's own closing tag: everything after it belongs to
            # the page, not to the body. The footer's `.terms` and `.site` were
            # read as agenda children before this stopped the scan.
            self.balanced = True
            raise _ScanDone
        if self.stack[-1] != tag:
            self.balanced = False
            raise _ScanDone
        self.stack.pop()
        if not self.stack and self._open is not None:
            cls, start = self._open
            self.kids.append((cls, self.raw[start:self._offset()]))
            self._open = None


class _ScanDone(Exception):
    """The container closed, or the markup proved unreadable. Either way, stop."""


def _direct_children(fragment: str) -> tuple:
    """-> ([(class attribute, inner markup)], balanced)."""
    scan = _ChildScan()
    try:
        return scan.feed_fragment(fragment)
    except _ScanDone:
        return scan.kids, scan.balanced
    except Exception:                                    # pragma: no cover
        # A parser error is "could not read", never "nothing wrong".
        return scan.kids, False


# What an agenda page's `.body` may hold at its top level, and what may appear
# ANYWHERE inside it. storyline-templates: the launch sequence, and optionally
# the lede above it.
# The agenda's body holds the launch sequence and NOTHING ELSE — not even the
# lede. storyline-templates made that an obligation at 0.1.551; it had been a
# permission ("may carry no lede") for four releases, and two of three
# conformance agents kept the lede because the scaffold emitted one.
AGENDA_BODY_ALLOWED = ("fill",)
AGENDA_FILL_ALLOWED = ("launch",)
# The visual blocks that make an agenda into a second page. `launch` is the
# agenda's own block and is excluded; everything else in the vocabulary is an
# argument being made somewhere it does not belong.
AGENDA_FORBIDDEN_ANYWHERE = tuple(b for b in VISUAL_BLOCKS if b != "launch")
# How an agenda page says it is one, in either output language. `议程` and `目录`
# are rule DATA for Chinese output, which the repository's English-only red line
# permits. Without them a Chinese deck's agenda was not found at all, and a
# not-found agenda scored as a pass.
# The agenda vocabulary and the recognition rule live in `scripts/lib/markup.py`
# — two readers spelled it two ways and only one of them could read Chinese.
# See that module for what the divergence cost.
AGENDA_WORDS = markup.AGENDA_WORDS
_is_agenda_page = markup.is_agenda_page


def d35_agenda_exclusive(raw):
    """-> {found, strays}: blocks on the agenda page that are not the agenda.

    **This gates**, by owner ruling after a round in which one conformance deck
    put a stat band on its agenda and another invented an `.agenda-grid` class
    to lay it out. An agenda that also argues something is two pages sharing one
    sheet, and the page that routes the deck is the last one that should need
    routing itself.

    **The page with the id wins.** The first version took whichever page matched
    first, and a CONTENT page whose eyebrow read "PART A - agenda for the
    quarter" was graded in place of the real agenda, which was then never
    examined at all.

    **Two questions, because a top-level allowlist was walked past four ways.**
    Depth-1 children must be the lede or the fill — but an UNCLASSED wrapper is
    descended into rather than skipped, since one `<div>` around a stat band
    disabled the whole check; and any forbidden block anywhere in the subtree is
    a stray, because `.body > .fill > .launch > .band` was three levels down and
    `.lede > .band` was inside an allowed parent. A class LIST is read whole:
    `class="band lede"` and `class="foot band"` both slipped past tests that
    looked at one token.

    A document with no agenda owes nothing here — `deck_structure` is what asks
    whether it should have one, and asking twice would fail a deck once for the
    missing page and again for that page's contents.
    """
    pages = list(_pages(raw))
    named = [t for t in pages if t[1].lower() == "agenda"]
    matched = [t for t in pages if _is_agenda_page(t[1], t[2])]
    for _cls, pid, body in (named or matched):
        strays = []
        if re.search(r"<style\b", body, re.I):
            strays.append("a <style> element of its own")
        # NO LEDE, AND `no-lede` SAID OUT LOUD. Two halves of one rule: the
        # title and support line come out, and the body says so in its class so
        # the grid drops the row they reserved. Removing only one of the two
        # leaves a page reserving a title it does not carry — the "partial
        # removal is NOT SHIPPABLE" case the rule names.
        bm = re.search(r'<div[^>]*class="((?:[^"]*\s)?body(?:\s[^"]*)?)"', body)
        carries = [w for w, pat in (
            ("a title", r'<h2[^>]*class="(?:[^"]*\s)?t(?:\s[^"]*)?"'),
            ("a support line", r'class="(?:[^"]*\s)?sup(?:\s[^"]*)?"'),
        ) if re.search(pat, body)]
        # ONE FINDING, not four. A page that kept its lede trips the lede, the
        # title, the support line and the missing class all at once, and four
        # lines saying one thing is how a reader learns to skim the report.
        if carries:
            strays.append(", ".join(carries) + " above the launch rows: the "
                          "rows are the agenda's statement, so the agenda "
                          "carries no lede")
        elif bm and "no-lede" not in bm.group(1).split():
            # Partial removal — the title is gone and the row it sat in is not.
            strays.append("a .body that does not declare no-lede, so the page "
                          "still reserves the row a deleted title sat in")
        m = re.search(r'<div[^>]*class="(?:[^"]*\s)?body(?:\s[^"]*)?"[^>]*>',
                      body)
        if not m:
            return {"found": pid, "strays": ["no .body block at all"]}
        inner = body[m.end():]
        kids, readable = _direct_children(inner)
        if not readable:
            # NOT A PASS. An unreadable body is the state this gate cannot
            # judge, and reporting it as clean is how a check goes quiet.
            strays.append("the .body markup could not be read — an element is "
                          "left unclosed, so nothing inside it can be graded")
        strays += _agenda_strays(kids)
        # THE SUBTREE, not only the top level. One `<div>` of nesting hid every
        # defect this gate was written for.
        for block in AGENDA_FORBIDDEN_ANYWHERE:
            if re.search(rf'class="(?:[^"]*\s)?{block}(?:\s[^"]*)?"',
                         _without_footer(inner)):
                strays.append(f".{block} somewhere inside the agenda's body")
        return {"found": pid, "strays": sorted(set(strays))}
    # NO AGENDA PAGE IS A MEASURED ABSENCE AND PASSES, the same ruling D27
    # carries: a deck without an agenda owes nothing to a rule about what an
    # agenda may contain, and `deck_structure` is what asks whether it should
    # have one. `grade()` scores this as a pass rather than as UNMEASURABLE —
    # the flag lives there, not here.
    return None


def _without_footer(inner: str) -> str:
    """The body's markup with the page footer removed.

    The footer is the page's furniture, not the agenda's content, and it carries
    `.terms` and `.site` — neither forbidden, but the same reasoning applies to
    any class a footer template gains later.
    """
    cut = inner.find('class="foot"')
    return inner if cut < 0 else inner[:cut]


def _agenda_strays(kids) -> list:
    """Top-level children of an agenda body that are not the agenda. Recursive
    through UNCLASSED wrappers only, which is the one shape that is neither a
    stray itself nor allowed to hide one."""
    out = []
    for cls, contents in kids:
        tokens = cls.split()
        if "foot" in tokens:
            continue
        if not tokens:
            out += _agenda_strays(_direct_children(contents)[0])
            continue
        if "lede" in tokens:
            continue        # the lede has its own finding, in its own words
        if not any(t in AGENDA_BODY_ALLOWED for t in tokens):
            out.append(f".{tokens[0]} beside the launch sequence")
            continue
        if "fill" in tokens:
            for gcls, _ in _direct_children(contents)[0]:
                gt = gcls.split()
                if gt and not any(t in AGENDA_FILL_ALLOWED for t in gt):
                    out.append(f".{gt[0]} inside the agenda's fill")
    return out


# The provenance vocabulary D6 accepts in a colophon, NAMED because it was an
# inline regex nobody writing a colophon could find: a deck whose closing said
# its numbers were "cited to" their entries failed on all fifteen pages, and
# the author learned the accepted words from the checker's source. This is the
# same discipline writing-rules gives the M2/M6 marker list ("this list is the
# contract"); the scaffold's genre card prints these words.
# THE CHINESE HALF WAS MISSING, and `check_prose.SOURCE_MARKERS` has carried
# 来源/出处/示意/实测 for releases. A Chinese colophon reading `出处：…` was
# reported as missing provenance on EVERY page — the checker deciding what the
# page must say, in a language it could not read. Found on a real deliverable
# whose author refused to edit correct Chinese to go green, and was right.
#
# THE DECLARATION LABELS BELONG HERE TOO, and their absence had the failure
# direction this comment already warns about. `writing-rules.md` §4 rule 6
# names `illustrative` / `mock` / `proposal value` / `uncalibrated` beside the
# source markers and says outright that they "satisfy the same obligation: a
# number that says what it is is not a number pretending to be measured."
# `check_prose`'s M2 accepts them; D6 did not, so a colophon reading "all
# figures illustrative; no engagement data" — the honest colophon for an
# illustrative deck, and this package builds those — was reported as missing
# provenance on every page. Measured on `fixtures/deck-pass.en.html` with only
# that sentence changed: twenty pages red, and the cheapest way to clear it is
# to write a source line that is not true.
# NOT a blanket superset of `SOURCE_MARKERS`: that list also carries `per`,
# which appears in almost any prose and would leave D6 unable to fail. The
# declaration half is what the rule says satisfies the same obligation, and
# `check_repo`'s `source-marker parity` guard holds exactly that half.
D6_PROVENANCE = ("source", "derive from", "derives from", "derived from",
                 "based on", "provenance", "trace to", "traces to",
                 "traces back to", "drawn from", "comes from",
                 "illustrative", "mock", "proposal value", "uncalibrated",
                 "\u6765\u6e90", "\u51fa\u5904", "\u4f9d\u636e", "\u6458\u81ea",
                 "\u793a\u610f")

# The half of `check_prose.SOURCE_MARKERS` that writing-rules §4 rule 6 calls a
# declaration rather than a source. Named so a guard can hold D6 to it without
# dragging in markers whose job is a figure's number rather than a document's
# footing.
D6_DECLARATION_LABELS = ("illustrative", "mock", "proposal value",
                         "uncalibrated", "\u793a\u610f")
# Built FROM the tuple rather than retyped beside it: the two disagreed the
# moment one was edited, which is this repository's most-fixed defect class.
# A CJK term takes no word boundary — CJK characters count as \w, so \b never
# fires between 数据 and 来源 (check_prose's SOURCE_RE says the same thing).
# CJK terms that ride inside an ordinary compound. `\b` never fires between
# CJK characters, so 示意 matched 表示意向 ("no offer intended") and 表示意图
# and 提示意义 — three ordinary collocations, one of which is exactly what a
# closing colophon says. MEASURED rather than imagined: the three below are the
# cases a review found, and the list is a list because a general rule for CJK
# compound boundaries is not something this checker can have.
D6_CJK_NOT_PRECEDED_BY = {"\u793a\u610f": "\u8868\u63d0\u6697"}
# The English terms that need a TRAILING boundary too. Only `mock`: "mockup"
# and "mocked up" describe a layout rather than a number, and rule 2's own
# label for this declaration is "mock UI". Everything else keeps the leading
# boundary alone, so "sourced from" and "sources" go on matching.
D6_BOTH_BOUNDARIES = ("mock",)
# A LEADING BOUNDARY on the English half. `source` matched "resourced by the
# team"; `\bsource` does not, and still matches "sourced from" and "sources",
# which a trailing boundary would have broken — narrowing a checker until
# correct prose fails it is the direction this whole release is about.
D6_PROVENANCE_RE = re.compile("|".join(
    (rf"(?<![{D6_CJK_NOT_PRECEDED_BY[w]}]){re.escape(w)}"
     if w in D6_CJK_NOT_PRECEDED_BY else re.escape(w))
    if any("\u3400" <= ch <= "\u9fff" for ch in w)
    else (rf"\b{re.escape(w).replace(r'\ ', ' ')}\b"
          if w in D6_BOTH_BOUNDARIES
          else rf"\b{re.escape(w).replace(r'\ ', ' ')}")
    for w in D6_PROVENANCE))


def d6_footer(raw):
    pages = re.findall(r'<section[^>]*class="[^"]*\bpage\b[^"]*"[^>]*>(.*?)</section>',
                       raw, re.S | re.I)
    if not pages:
        return None
    missing_src, missing_total = [], []
    for i, body in enumerate(pages):
        text = _block_text(body, "foot")
        if not re.search(r"\b\w+\s*/\s*\d+\b", text):
            missing_total.append(i)
    # Provenance is stated once for the document, not on every page. 0.1.344
    # retired the per-page source line for sales and marketing material at a
    # reader's request: a source under every figure and again in every footer is
    # apparatus a customs manager does not need, and it was crowding out the
    # handling terms that a commercial document does need. The obligation did not
    # go away — it moved to where it is read once, on the cover and the closing.
    # So this asks the document, and D12 asks every page for its terms.
    # The vocabulary is deliberately wider than it looks necessary. A document
    # whose colophon read "every claim traces to the research report of
    # 2026-08-11" was reported as missing its provenance on all fifteen pages,
    # because "traces to" was not on the list — a checker failing a document
    # that does the right thing in words the checker did not anticipate. That
    # failure direction is the dangerous one: the cheapest way to clear it is to
    # edit correct prose until a pattern matches, which is the checker writing
    # the document.
    doc_text = _block_text(raw, "colophon").lower()
    if not D6_PROVENANCE_RE.search(doc_text):
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
    # DOES THIS DOCUMENT USE THE TOKEN VOCABULARY — not "does it define one
    # particular property". `--bg` alone was the sentinel, and it has now
    # produced two false UNMEASURABLE verdicts on documents that plainly do use
    # the block: once when a second `:root` shadowed the first (0.1.387), and
    # once on a conformance deck that defines --tx1..--tx4, --acc and --ln1 and
    # simply paints its canvas another way. The second cost that deck its whole
    # design report and cascaded into three commercial gates reading "never
    # reported" — an agent scored `fail` for a property nothing requires.
    #
    # The vocabulary is the test, and the file still says what it could not
    # find. Metrics that need a specific token report their own absence:
    # d1_contrast is the one that needs `--bg`, and it grades what it can.
    vocabulary = {"bg", "tx1", "tx2", "tx3", "tx4", "ln1", "ln2", "ln3",
                  "acc", "card-bg"}
    present = vocabulary & set(resolved)
    if len(present) < 3:
        raise Unmeasurable(
            f"this file does not use the LUMI token block: of {len(vocabulary)} "
            f"core tokens it defines {len(present)} "
            f"({', '.join('--' + t for t in sorted(present)) or 'none'})")
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
        "D19_vocabulary": d19_vocabulary(raw),
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
        "D20_palette_fidelity": d20_palette_fidelity(resolved, palette),
        "D21_data_contract": d21_data_contract(raw),
        "D24_images_embedded": d24_images_embedded(raw),
        "D25_image_provenance": d25_image_provenance(raw),
        "D26_declared_scope": (_ds := d26_declared_scope(raw, _storyline_of(raw))),
        # THE NUMBER, UNDER THE NAME THE VERDICT USES. `trace.py`'s close step
        # records a threshold reading only for a key named after the metric
        # (`value = row.get(mid)`), and D31's value lived inside a dict keyed
        # D26. So the metric at the top of the ledger's failing table had no
        # threshold history at all, and `ledger_instruments` could form no
        # opinion about it in either direction — "a real weakness, or a bar set
        # wrong" was unanswerable by construction rather than by lack of data.
        "D31_undeclared_sections": (None if _ds["missing"] is None
                                    else len(_ds["missing"])),
        "D27_agenda_mirror": (d27 := d27_agenda_mirror(raw)),
        "D27_detail": (d27 or {}).get("orphans"),
        "D28_takeaway": (d28 := d28_takeaway(raw)),
        "D28_detail": (d28 or {}).get("missing"),
        "D29_figure_numbers": (d29 := d29_figure_numbers(raw)),
        "D29_detail": (d29 or {}).get("naked"),
        "D30_figure_sequence": (d30 := d30_figure_sequence(raw)),
        "D30_detail": (d30 or {}).get("duplicates"),
        "D32_shape_use": d32_shape_use(raw),
        "D41_role_echo": d41_role_echo(raw),
        "D33_icon_provenance": d33_icon_provenance(raw),
        "D34_icon_uniqueness": d34_icon_uniqueness(raw),
        "D35_agenda_exclusive": d35_agenda_exclusive(raw),
        "D36_font_family": d36_font_family(raw),
        "D37_caption_scope": d37_caption_scope(raw),
        "D38_agenda_rows": d38_agenda_rows(raw),
        "D39_bookend_mark": d39_bookend_mark(raw),
        "D40_bookend_is_the_brand": d40_bookend_is_the_brand(raw),
        "D42_figure_spec": d42_figure_spec(raw, path.parent),
        "D43_figure_content": d43_figure_content(raw, path.parent),
        "D23_font_count": d23_font_count(
            raw, (ROOT / "tokens" / "lumi-theme.css").read_text(encoding="utf-8")),
    }


# --- D21: the data contract -------------------------------------------------
# A figure may DECLARE the data it draws, in a JSON block inside the figure:
#
#   <script type="application/json" class="f-data">
#     {"series": [{"label": "Rural", "value": 40}]}
#   </script>
#
# Then the numbers on the drawing, the numbers in its caption and the declared
# data are three views of one thing, and disagreement between them is decidable
# rather than a matter of reading carefully. This is the structural half of the
# figure-text hallucination problem: M13 catches a document contradicting
# itself in prose, and this catches a drawing contradicting its own data.
#
# It is OPT-IN by design. A figure that declares nothing is not failed — most
# figures in flight today declare nothing, and a checker that failed them all
# would be turned off within a day. What it will not tolerate is a declaration
# that disagrees with the drawing, because a false contract is worse than none.
_FDATA = re.compile(
    r'<script[^>]*class="[^"]*\bf-data\b[^"]*"[^>]*>(.*?)</script>', re.S | re.I)
# A figure in this package is `<div class="fig">`, not `<figure>` — the first
# version of this check assumed the HTML element and matched nothing on any
# real fixture. Rather than guess again, the scan starts at each declaration
# and walks BACK to the nearest figure container, which works for both.
_FIG_OPEN = re.compile(r'<figure\b|<div[^>]*class="[^"]*\bfig\b[^"]*"', re.I)


# --- D22 / D23: the two halves of P-1 that nothing held --------------------
# P-1 says the brand pack is the single source of visual identity. What was
# actually held was the palette. Typography and layout were not, and the gap was
# recorded as GAP-008 rather than left to read as coverage.
#
# D9 already collected pages whose layout class is not one the tokens define —
# and then its verdict was hard-coded to pass, so an invented layout was
# gathered into a list nothing read. That is the failure mode this repository
# calls a check that has only ever been seen passing.
def d22_layout_vocabulary(r):
    """Pages claiming a layout `tokens/` does not define."""
    v = r.get("D9_layout_variety") or {}
    return {"unknown": [pid for pid, names in (v.get("unknown") or [])],
            "detail": v.get("unknown") or []}


# The ceiling is DERIVED: it is the number of font families `tokens/` declares,
# not a number chosen here. design-rules §2 says two voices and the tokens
# declare exactly two; if a third is ever added the ceiling moves with it, and
# a rule that counted to a literal 2 would then be wrong in the quiet way.
_FONT_VAR = re.compile(r"--([\w-]*(?:din|mono|serif|sans|face|font)[\w-]*)\s*:\s*[^;]*",
                       re.I)
_FONT_USE = re.compile(r"font-family\s*:\s*([^;}]+)", re.I)


# An `@font-face` block DECLARES a face; it does not use one. The first version
# counted `font-family: 'D-DIN'` inside the face declaration as a third
# typeface, and fired on both accepted deliverables — each of which uses exactly
# the two voices the tokens define. A check that would have an author edit
# correct work to silence it is worse than no check, and this one was caught by
# running it against real deliverables before it was believed.
_AT_FACE = re.compile(r"@font-face\s*\{[^}]*\}", re.I | re.S)


def d23_font_count(raw, token_css):
    """Distinct font stacks the document uses, against what tokens/ declares."""
    declared = {m.group(1).lower() for m in _FONT_VAR.finditer(token_css)}
    used = set()
    for m in _FONT_USE.finditer(_AT_FACE.sub(" ", raw)):
        value = m.group(1).strip().lower()
        var = re.match(r"var\(\s*--([\w-]+)", value)
        used.add(var.group(1) if var else value.split(",")[0].strip(" '\""))
    literal = sorted(u for u in used if u not in declared)
    return {"declared": len(declared), "used": len(used),
            "ceiling": len(declared) or None,
            "over": sorted(used) if declared and len(used) > len(declared) else [],
            "literal_stacks": literal}



# An <img src> or an SVG <image href> pointing anywhere but at an embedded
# payload. `data:` is the only self-contained form; everything else is a request
# to a host at read time.
_RASTER = re.compile(r"<(?:img|image)\b[^>]*?(?:src|href|xlink:href)\s*=\s*"
                     r"[\"']([^\"']+)[\"']", re.I)
# Any CSS url() that is not a `data:` payload and not a same-document fragment.
# The first version required a scheme or `//` AFTER the (?!data:) lookahead, so
# a RELATIVE url — `url(assets/cover.jpg)`, which is how a person naturally
# writes a cover background — matched nothing and passed. It also renders
# correctly on the author's machine, because the file sits beside the HTML, so
# opening the deliverable over file:// does not catch it either. The reader
# receives one HTML file and a blank cover. CLAUDE.md credits D24 with making
# the imagery lift "safe rather than a hope"; this is the hole in it.
_CSS_URL = re.compile(r"url\(([^)]*)\)", re.I)
# The licence has to be NAMED, not gestured at. A colophon saying "images
# licensed appropriately" is the sentence that gets written when nobody checked.
# Attribute-borne prose a reader actually meets: `alt` is shown when the image
# fails and spoken by a screen reader; `aria-label` is the accessible name.
# Neither is a CSS comment, and both are where an author most naturally writes
# "Screenshot of ...".
_ATTR_PROSE = re.compile(r'(?:alt|aria-label)="([^"]*)"', re.I)

_LICENCE = re.compile(
    r"\b(public domain|CC0|CC[ -]BY(?:[ -]SA|[ -]NC|[ -]ND)?(?:[ -]\d\.\d)?"
    r"|Unsplash|licen[cs]ed under|used under|own work|screenshot of)\b", re.I)


def _is_embedded(url: str) -> bool:
    """Does this reference ship inside the file? `data:` is the only payload
    form; `#` is a same-document fragment and never leaves. Everything else —
    absolute, protocol-relative, or RELATIVE — is a request to a host at read
    time, and a relative one is the easiest of the three to write by accident.
    """
    u = url.strip().strip("\"'").strip()
    return not u or u.lower().startswith("data:") or u.startswith("#")


def d24_images_embedded(raw):
    """-> {rasters, external:[...]} — every image ships inside the file.

    A deliverable is one self-contained HTML file. A linked image is a page that
    breaks the first time it is read offline, and it reports the reader to
    whichever host is serving it. `data:` is the only form that is neither.
    """
    srcs = [m.group(1).strip() for m in _RASTER.finditer(raw)]
    external = [u[:60] for u in srcs if not _is_embedded(u)]
    # The url() target is decided in code rather than by a lookahead. The
    # regex version was bypassed by `url( #clip )` — an optional quote class
    # let the engine backtrack past the guard — and getting a self-contained
    # payload confused with a same-document fragment is the kind of thing a
    # lookahead should not be asked to arbitrate.
    external += [f"url({m.group(1).strip()})"[:60]
                 for m in _CSS_URL.finditer(raw)
                 if not _is_embedded(m.group(1))]
    return {"rasters": len(srcs), "external": external}



# A scope note is the DECLARED half of C5. The rubric specifies it and no
# checker read it, so the only place an omission could be declared was an
# outline file — an artifact the template path never produces. On path B,
# completeness therefore had no instrument at all.
_SCOPE_NOTE = re.compile(
    r"<([a-z]+)\b([^>]*\bdata-omitted\s*=\s*[\"\']([^\"\']*)[\"\'][^>]*)>(.*?)</\1>",
    re.I | re.S)
# A scope note by ROLE, whether or not it carries the declaration. Subtracted
# from the coverage corpus: a sentence whose job is to say what the document
# does not cover must not be the thing that makes it covered. Matching on the
# class as well as the attribute is deliberate — a note written without
# `data-omitted` is an undeclared omission, and it should read as one rather
# than as coverage supplied by its own apology.
_SCOPE_NOTE_ROLE = re.compile(
    r"<([a-z]+)\b[^>]*class=\"(?:[^\"]*\s)?scope-note(?:\s[^\"]*)?\"[^>]*>"
    r"(.*?)</\1>", re.I | re.S)
_INVISIBLE = re.compile(
    r"display\s*:\s*none|visibility\s*:\s*hidden|\bhidden\b|aria-hidden\s*=\s*"
    r"[\"\']true[\"\']", re.I)


def _storyline_of(raw):
    """-> the storyline the document declares, or None.

    Declared, never inferred. Guessing a storyline from the headings would make
    the completeness report a measurement of the guess.
    """
    m = re.search(r'data-storyline="([a-z-]+)"', raw)
    return m.group(1) if m else None


def d26_declared_scope(raw, storyline=None):
    """-> {storyline, missing, hidden, declared} — what the document leaves out.

    REPORTED, never gating, and that is a decision with evidence behind it.
    C5 is `declarable, never gating`: structural compliance does not predict
    quality, and a completeness gate is worth defeating — an author who has to
    clear it will write the heading and nothing under it. What IS decidable is
    whether an absence was declared, and whether the declaration is one a
    reader can see.

    **Reader-visible is the whole mechanism.** A marker only the checker can
    read would do nothing but silence the checker, so a `data-omitted` on a
    hidden element is reported as loudly as a missing section.
    """
    declared, hidden = set(), []
    for m in _SCOPE_NOTE.finditer(raw):
        attrs, body = m.group(2), m.group(4)
        # One note may declare several absences ("a, b; c") — a reader reads
        # one sentence, the checker reads each name.
        names = [n.strip().lower() for n in re.split(r"[,;·]", m.group(3)) if n.strip()]
        declared.update(names)
        if _INVISIBLE.search(attrs) or not markup.strip_tags(body, sep="").strip():
            hidden.extend(names or ["(unnamed)"])
    if not storyline:
        return {"storyline": None, "missing": None, "hidden": hidden,
                "declared": sorted(declared)}
    expected = TYPICAL_SECTIONS.get(storyline)
    if expected is None:
        return {"storyline": storyline, "missing": None, "hidden": hidden,
                "declared": sorted(declared)}
    # THE CORPUS IS WHAT A READER MEETS, MINUS WHAT THE DOCUMENT SAYS IT DOES
    # NOT COVER. Two defects lived on this one line and they compound.
    #
    # `strip_tags` keeps what is BETWEEN the tags, so a `<style>` block's own
    # text counted: injecting one CSS comment naming three sections took a
    # status report's `missing` from three to zero. `markup.reader_text` was
    # written for exactly this at 0.1.594, when a stylesheet comment silenced
    # D25, and it never reached this second call site.
    #
    # And a scope note's own BODY was in the corpus, so a note reading "this
    # deck states no target customer" satisfied `target customer` before
    # `declared` was ever consulted — measured, deleting the `data-omitted`
    # attribute changed nothing, which made the declaration decorative and the
    # `declared` branch a thing that had never once been load-bearing (FM-01,
    # inside the metric). A note declares; it does not cover.
    text = markup.reader_text(
        _SCOPE_NOTE_ROLE.sub(" ", _SCOPE_NOTE.sub(" ", raw))).lower()
    missing = [section_name(sec) for sec in expected
               if not any(a in text or a in declared
                          for a in section_alts(sec))]
    return {"storyline": storyline, "missing": missing, "hidden": hidden,
            "declared": sorted(declared)}

def d25_image_provenance(raw):
    """-> {rasters, licence_named} — an image on the page names its terms.

    Not a lawyer's check and not trying to be: it asks whether the document says
    anywhere, in words a person wrote, where its images came from and under what
    terms. A deck that ships a photograph and says nothing about it is the
    commercial risk D12 exists for, arriving through a different door.
    """
    n = len(_RASTER.findall(raw))
    # SEARCHED IN WHAT A READER SEES, not in the file. This scanned `raw`, so a
    # phrase anywhere in the document satisfied it — including inside a
    # `<style>` block. Measured at 0.1.594: a stylesheet comment about an
    # unrelated defect happened to contain the words "screenshot of", and a
    # fixture carrying an unattributed linked image began reporting
    # `terms named`. The gate was silenced by a sentence a reader never sees,
    # which is the same argument D26 already makes about scope notes — a marker
    # only the checker can read would do nothing but silence the checker.
    # THE CORPUS IS WHAT A READER MEETS, WHICH INCLUDES `alt`. Tightening this
    # to reader_text alone at 0.1.594 failed correct documents: "Screenshot of
    # the operator console" in an `alt` is provenance an author wrote for a
    # reader — it is read aloud by a screen reader and shown when the image
    # does not load — and the tightening dropped it with the CSS. Both
    # attribute forms are added back explicitly; a stylesheet comment still
    # does not count, which was the whole point.
    said = markup.reader_text(raw) + " " + " ".join(
        _ATTR_PROSE.findall(raw))
    # A document with no images has nothing to name, and it must PASS rather
    # than read `n/a` — check_design treats an unmeasurable gate as a failure on
    # purpose, and applying that to an optional element would fail every
    # text-and-vector deliverable this package has ever produced.
    return {"rasters": n, "licence_named": bool(_LICENCE.search(said)) if n else True}


def _measured(point) -> bool:
    """Does this series point ASSERT a reading the drawing can be held to?

    Three shapes are not assertions, and each was found by breaking the guard
    that was written without them:

    * a point that is not an object at all;
    * `value` absent or `null` — the documented way to label a series a figure
      does not quantify;
    * `value` present as a string that renders to nothing (`""`, `"  "`). An
      empty string is not `None`, so it cleared a `is not None` test and then
      made the agreement search an EMPTY pattern that matches anywhere.

    `0` and `0.0` ARE readings and must pass — the test is on the emptiness of
    the RENDERING, never on the truthiness of the value, because reading a
    falsy scalar as absence is a defect this repository has already shipped
    (0.1.650 counted a recorded `0` as "never recorded"). A bool is NOT a
    reading: `isinstance(False, int)` is true in Python, so `{"value": false}`
    rendered through `f"{v:g}"` as `0` and reported "declares A = 0", a number
    the contract never wrote.
    """
    if not isinstance(point, dict):
        return False
    value = point.get("value")
    if value is None or isinstance(value, bool):
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return True


_SPEC_DECL = re.compile(r'data-figure-spec="([^"]+)"')
_MOVE_DECL = re.compile(r'data-analysis="([a-z]+)"')


def d42_figure_spec(raw, base=None):
    """A page that DECLARES its data must be able to produce it.

    -> {declared, broken:[{page, ref, why}]}

    **Nothing here asks a figure to declare a spec.** A schematic, a 2x2, the
    globe and an icon row are correct answers that cannot satisfy such a demand
    — AG-10, which this package declined after shipping it for one commit and
    watching its author bind a wrong shape to satisfy his own guard. What gates
    is the contradiction only: the page said the numbers are in that file, and
    they are not, or they are not what the move needs.

    `base` is the document's own directory, because the spec sits beside the
    deck. Given no base the check reports `unmeasurable` rather than passing:
    a reference nobody could resolve is not a reference that resolved, and this
    metric's whole subject is references that do not.
    """
    decls = list(_SPEC_DECL.finditer(raw))
    if not decls:
        # `n/a`, NOT `ok`. A document that was never asked and a document that
        # declared its data and delivered it must not print the same line —
        # that is FM-24 inside a gate, and `evals/gates.json`'s `na_means` is
        # where this silence is declared honest.
        return None
    broken = []
    for m in decls:
        ref = m.group(1)
        pid = _page_id_before(raw, m.start())
        if base is None:
            # A declaration nobody could resolve is a broken declaration, never
            # an absent one. Collapsing this into the `n/a` above would let a
            # caller with no document directory report a clean sheet.
            broken.append({"page": pid, "ref": ref,
                           "why": "the document's directory is unknown, so "
                                  "this reference could not be resolved"})
            continue
        target = base / ref
        spec, problem = figure_spec.load(target)
        if problem or spec is None:
            broken.append({"page": pid, "ref": ref,
                           "why": problem or f"{target}: no spec came back"})
            continue
        if figure_spec.is_skeleton(spec):
            # A FINDING, and the comment that used to sit here was wrong.
            # It said D14 already refuses the slot that goes with a skeleton —
            # but `d14_placeholders` reads the document HTML and has never seen
            # this file, and `new_deck` tells the author to delete that very
            # note when they paste the drawing in. Measured: a spec with real
            # numbers everywhere and one leftover `[TO FILL]` source passed
            # both gates, and a figure reached a reader with no source at all.
            broken.append({"page": pid, "ref": ref,
                           "why": f"{ref} is still the scaffold's skeleton in "
                                  f"at least one field. Nothing else can see "
                                  f"it: D14 reads the document, not this file"})
            continue
        # THE ENCLOSING SECTION, not a character window and not "whatever came
        # before". Searching backwards 4000 characters found nothing when the
        # page wrote `data-figure-spec` before `data-analysis`, and nothing
        # again when the two sat further apart than the window — both printing
        # exactly what a correct page prints, which is FM-24 inside a check
        # written to fix an FM-24.
        declared_move = _MOVE_DECL.search(_enclosing_section(raw, m.start()))
        if declared_move and declared_move.group(1) != str(spec.get("move")):
            # The page and its spec disagree about what the figure IS. The
            # scaffold never overwrites an author's spec — right — so changing
            # a beat's move leaves a stale file behind, and nothing compared
            # the two until this line.
            broken.append({"page": pid, "ref": ref,
                           "why": f"the page declares "
                                  f"data-analysis=\"{declared_move.group(1)}\" "
                                  f"and {ref} declares "
                                  f"move=\"{spec.get('move')}\""})
            continue
        found = figure_spec.problems(spec)
        # EVERY finding, not `found[0]`. `problems` appends the arithmetic
        # last, so the one assertion in this package about the author's DATA
        # could only ever surface when it was the sole problem on the spec.
        for why in found:
            broken.append({"page": pid, "ref": ref, "why": why})
    return {"declared": len(decls), "broken": broken}


# The collection each named move draws, and the field that holds a member's
# NAME. `correlate.points` is deliberately absent: a scatter's points are dots,
# and demanding a label on each would fail the figure drawn correctly (AG-10).
# Discovered by hand rather than from `_COLLECTIONS` on purpose — that tuple
# says which fields hold many things, and this one says which of those the
# reader is supposed to be able to read off the drawing. They are not the same
# question, and deriving one from the other would silently add `points`.
NAMED_MEMBERS = {
    ("compare", "references"): "label",
    ("compare", "criteria"): "name",
    ("decompose", "parts"): "label",
    ("position", "items"): "label",
    ("bridge", "pieces"): "label",
    ("bridge", "stages"): "name",
}

# The source line is provenance, not the drawing naming a member. Counting it
# would let a figure pass because its own citation happened to contain an
# item's word — measured on this package's own breakdown, whose source string
# carries `specification`, which is also a part label.
_FNOTE_TEXT = re.compile(r'<text[^>]*class="[^"]*\bfnote\b[^"]*"[^>]*>.*?</text>',
                         re.S)
_ANY_TEXT = re.compile(r"<text[^>]*>(.*?)</text>", re.S)


def _drawn_words(section):
    """-> everything the FIGURES in this section actually say, or None.

    None means there was no figure to read — a raster, or a page that declared
    a spec and drew nothing. It is a third answer and never an empty string: an
    empty string compares equal to a drawing that names nothing, and those are
    different facts (FM-24).

    **Not every `<svg>` on a page is a figure**, and the first version of this
    function believed otherwise. Every page carries the ground behind it and an
    icon in its eyebrow, so a page with NO figure still held two `<svg>`
    elements — and the fixture page that declares a spec and draws no figure at
    all came back `thin` instead of unreadable, blaming the drawing for a
    defect that is the page's. The predicate is D5's, kept in the same shape:
    not `.ground`, not `.ic`, and carrying something actually drawn rather than
    a single `<use>` of a sprite.
    """
    figs = [m.group(0)
            for m in re.finditer(r'<svg(?![^>]*class="(?:ground|ic)")\b.*?</svg>',
                                 section, re.S)
            if re.search(rf"<(?:{'|'.join(SHAPES)}|text)\b", m.group(0))]
    if not figs:
        return None
    body = _FNOTE_TEXT.sub(" ", " ".join(figs))
    return markup.visible_text(" ".join(_ANY_TEXT.findall(body)))


def _names(member, field):
    """-> the strings that would count as this member being named."""
    whole = str(member.get(field) or "").strip()
    if not whole:
        return []
    # The longest word is the fallback because a drawing legitimately shortens
    # a long label to fit — `Catalog and system functions` may be drawn over
    # two lines or clipped to `Catalog and system`. Matching the whole string
    # OR its longest word is strictly weaker than matching the whole string,
    # so nothing that passes today starts failing; what it refuses is a drawing
    # carrying no part of the name at all.
    words = re.findall(r"[A-Za-z0-9_/.-]{4,}", whole)
    longest = max(words, key=len) if words else whole
    return [whole, longest]


def d43_figure_content(raw, base=None):
    """A drawing names every member the page's own spec declares.

    -> {checked, thin:[{page, ref, missing}], blind:[{page, ref, why}]}

    **This is the gate that was missing while every other one was green.** A
    library shape could carry two words, so a two-by-two shipped as an empty
    box with an axis word at each end and a staircase shipped with no dates —
    and nothing measured how much the drawing said, because the metrics all
    ask whether the markup is well formed rather than whether it speaks.

    **It is a self-contradiction, never a judgement.** The document states, in
    its own spec file, that the figure has these five items; the drawing then
    names three of them. No taste is involved and no reviewer is needed, which
    is why it can gate. A page that declares nothing is never asked.

    **`blind` is the third answer and it does not gate.** A page whose figure
    is a raster cannot be read this way, and failing it would be a gate a
    correct answer cannot satisfy (AG-10). It is carried into the row instead,
    so a document that could not be measured prints a different string from a
    document that measured clean — the distinction convention 11 requires.
    """
    decls = list(_SPEC_DECL.finditer(raw))
    if not decls:
        return None
    thin, blind, checked = [], [], 0
    for m in decls:
        ref, pid = m.group(1), _page_id_before(raw, m.start())
        if base is None:
            blind.append({"page": pid, "ref": ref,
                          "why": "the document's directory is unknown, so the "
                                 "spec could not be read"})
            continue
        spec, problem = figure_spec.load(base / ref)
        if problem or spec is None:
            # D42 gates this; here it is a measurement that did not happen, and
            # saying so keeps `checked` honest about its own reach.
            blind.append({"page": pid, "ref": ref,
                          "why": problem or "no spec came back"})
            continue
        move = str(spec.get("move") or "")
        wanted = [(f, key) for (mv, f), key in NAMED_MEMBERS.items() if mv == move]
        if not wanted:
            continue        # correlate, or a move with nothing named to check
        drawn = _drawn_words(_enclosing_section(raw, m.start()))
        if drawn is None:
            blind.append({"page": pid, "ref": ref,
                          "why": "the page declares this spec and holds no "
                                 "inline <svg>, so what the figure says could "
                                 "not be read"})
            continue
        low = drawn.lower()
        missing = []
        for field, key in wanted:
            for i, member in enumerate(spec.get(field) or []):
                if not isinstance(member, dict):
                    continue
                cands = _names(member, key)
                if cands and not any(c.lower() in low for c in cands):
                    missing.append(f"{field}[{i}] {cands[0]!r}")
        checked += 1
        if missing:
            thin.append({"page": pid, "ref": ref, "missing": missing})
    return {"checked": checked, "thin": thin, "blind": blind}


def _enclosing_section(raw, pos):
    """-> the whole <section> the character at `pos` sits in, tag included."""
    start = raw.rfind("<section", 0, pos)
    if start == -1:
        return raw[:pos]
    end = raw.find("</section>", pos)
    return raw[start:end if end != -1 else len(raw)]


def _page_id_before(raw, pos):
    # ATTRIBUTE ORDER FREE. It required `id=` to follow `class="page"` on the
    # tag, so `<section id="p1" class="page">` reported `(document)` and every
    # finding on that page lost its address.
    tag = _enclosing_section(raw, pos)[:400]
    if 'class="page' not in tag and "class='page" not in tag:
        opens = list(re.finditer(r"<section[^>]*\bid=[\"']([^\"']+)[\"']",
                                 raw[:pos]))
        return opens[-1].group(1) if opens else "(document)"
    got = re.search(r"\bid=[\"']([^\"']+)[\"']", tag)
    return got.group(1) if got else "(document)"


def d21_data_contract(raw):
    """-> {declared, mismatches:[...]} — three-way agreement, opt-in."""
    declared, mismatches = 0, []
    for m in _FDATA.finditer(raw):
        declared += 1
        opens = list(_FIG_OPEN.finditer(raw, 0, m.start()))
        start = opens[-1].start() if opens else max(0, m.start() - 2000)
        # The declaration must not be part of what it is checked against: with
        # it left in, every declared value found ITSELF and the check passed on
        # figures whose data contradicted the drawing outright.
        drawing = raw[start:m.start()] + raw[m.end():m.end() + 400]
        visible = markup.visible_text(drawing)
        try:
            data = json.loads(m.group(1))
        except json.JSONDecodeError as exc:
            mismatches.append(f"figure {declared}: the declared data is not "
                              f"valid JSON ({exc.msg}) — a contract nobody can "
                              f"read is not a contract")
            continue
        series = data.get("series") if isinstance(data, dict) else None
        if not isinstance(series, list) or not series:
            mismatches.append(f"figure {declared}: declares no series")
            continue
        # A CONTRACT THAT ASSERTS NOTHING CANNOT DISAGREE WITH THE DRAWING.
        # The value check below is skipped when `value is None`, so a contract
        # of labels alone — the cheapest thing a scaffold could emit — passes
        # forever while `evals/gates.json` flips D21's subject from "held
        # nothing" to "held 1, ok". The gate would read as activated and grade
        # nothing, which is FM-24 wearing the shape of a fix. Measured before
        # this guard existed: `{"series":[{"label":"North"},{"label":"South"}]}`
        # over a drawing carrying both labels returned zero mismatches.
        # `_measured`, not `is not None`. A review broke the first cut of this
        # guard one character later: `{"value": ""}` is not `None`, so it
        # cleared the guard, and then `shown` was `""` and the search below
        # compiled to `(?<![\d.])(?![\d])` — an empty pattern that matches
        # almost anywhere. The contract passed BOTH halves having asserted
        # nothing, and printed byte-identical output to a measured, agreeing
        # one. That is this guard's own accusation, committed by this guard,
        # and it is the likelier shape in practice: an unfilled numeric slot in
        # a template emits `""` far more naturally than it omits the key, and
        # D14 does not see it because `""` is not `[TO FILL]`.
        if not any(_measured(pt) for pt in series):
            # A contract of NON-OBJECTS falls through to the per-point loop
            # below, which already names that precisely. Reporting "no measured
            # point" for `{"series": ["a", "b"]}` would hand the author the
            # wrong remedy.
            if any(isinstance(pt, dict) for pt in series):
                mismatches.append(
                    f"figure {declared}: declares a contract with no measured "
                    f"point — a contract that asserts nothing cannot disagree "
                    f"with the drawing, so it grades nothing while reading as "
                    f"coverage. Give at least one series point a `value`, or "
                    f"drop the contract")
                continue
        for point in series:
            if not isinstance(point, dict):
                mismatches.append(f"figure {declared}: a series point is not an object")
                continue
            label = str(point.get("label", "")).strip()
            if label and label.lower() not in visible.lower():
                mismatches.append(f"figure {declared}: declares the series "
                                  f"{label!r}, which is nowhere on the drawing")
            if not _measured(point):
                continue
            value = point["value"]
            shown = (f"{value:g}" if isinstance(value, (int, float))
                     and not isinstance(value, bool) else str(value).strip())
            if not re.search(rf"(?<![\d.]){re.escape(shown)}(?![\d])", visible):
                mismatches.append(f"figure {declared}: declares {label or 'a point'} "
                                  f"= {shown}, which appears nowhere on the drawing")
    return {"declared": declared, "mismatches": mismatches}


def d20_palette_fidelity(resolved, palette):
    """Is the palette this document declares LUMI's palette? **This gates.**

    The other palette checks ask whether a document is consistent with the block
    it declares. Nothing asked whether that block is THIS package's — so a deck
    could define `--tx1`, `--acc` and the whole ladder with values of its own
    invention and pass every one of them, because each was graded against the
    invention. One did: a conformance deck whose ten shared colour tokens
    disagreed with the shipped values TEN times out of ten, including an `--acc`
    that was teal where LUMI's is olive. The owner saw it immediately — the deck
    simply looked like another design language — and no check in this package
    could. FM-10, in the one place the package's whole promise lives.

    **Colours only, and that is the principled line rather than a convenient
    one.** "One colour, one meaning" is a red line, and a different accent is a
    different language. Type SIZES are the document's to choose: 0.1.340
    withdrew the type floor, and SKILL.md's first rule is to design per page
    with no universal size floors. Measured on a compliant deck, the only
    tokens that differ from the shipped set are the six `--fs-*` sizes and one
    ground opacity — every colour matches. Gating on sizes would fail a document
    for obeying rule 1.

    Compared as PARSED colours, so `#FFF`, `#FFFFFF` and `rgb(255,255,255)` are
    one value, and per palette, so the dark block is held to the dark tokens.
    """
    try:
        shipped_css = (ROOT / "tokens" / "lumi-theme.css").read_text(encoding="utf-8")
    except OSError as exc:                                          # noqa: BLE001
        return {"unreadable": str(exc), "compared": 0, "differs": []}
    # Comments first, through the SAME helper the document path uses. Without
    # it the banner above tokens/lumi-theme.css's `:root` lands inside the
    # captured selector, the block matches nothing, and this check compares a
    # document against an empty palette and reports every document clean — the
    # failure `css_of` documents three functions above, met again by feeding
    # raw CSS in through a different door.
    shipped, _ = resolve(css_tokens.strip_comments(shipped_css, " "), palette)
    differs = []
    compared = 0
    for name, want in sorted(shipped.items()):
        theirs = resolved.get(name)
        if theirs is None:
            continue
        want_rgba, got_rgba = parse_color(want), parse_color(theirs)
        if want_rgba is None:
            continue            # a size, a font stack, a duration — not ours
        compared += 1
        if got_rgba is None or want_rgba != got_rgba:
            differs.append({"token": f"--{name}", "shipped": want.strip(),
                            "document": theirs.strip()})
    return {"compared": compared, "differs": differs}


def grade(r):
    rows: list[tuple[str, object, str, bool, bool]] = []
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
    pf = r["D20_palette_fidelity"]
    rows.append(("D20_palette_fidelity",
                 len(pf["differs"]) if "differs" in pf else None, "=0 (gates)",
                 not pf.get("differs"), "unreadable" in pf))
    lv = d22_layout_vocabulary(r)
    rows.append(("D22_layout_vocabulary", len(lv["unknown"]) or 0, "=0 (gates)",
                 not lv["unknown"], r.get("D9_layout_variety") is None))
    fc = r["D23_font_count"]
    rows.append(("D23_font_count",
                 f"{fc['used']} used, ceiling {fc['ceiling']}" if fc else None,
                 "<= what tokens/ declares (reported)",
                 not (fc and (fc["over"] or fc["literal_stacks"])), fc is None))
    im = r["D24_images_embedded"]
    rows.append(("D24_images_embedded", len(im["external"]) if im else None,
                 "=0 (gates)", not (im and im["external"]), im is None))
    pv = r["D25_image_provenance"]
    rows.append(("D25_image_provenance",
                 ("no images" if pv and not pv["rasters"] else
                  f"{pv['rasters']} image(s), terms named") if pv and pv["licence_named"]
                 else (f"{pv['rasters']} image(s), no terms named" if pv else None),
                 "every image names its terms (gates)",
                 bool(pv and pv["licence_named"]), pv is None))
    # D32 IS MEASURED FOR EVERY DOCUMENT, and its row used to live inside the
    # `data-storyline` branch below — so a deliverable declaring no storyline
    # emitted no D32 row at all and the gate vanished with it. `gating_metrics`
    # keys on what the report returned, so nothing noticed: a missing row reads
    # as a metric that did not apply rather than as a gate that went missing.
    # It is hoisted here and reports `n/a` where no move is declared, which is
    # what "a document that declares no moves is not measured against it" means
    # — the metric saying so, rather than the metric being absent.
    ec = r["D41_role_echo"]
    rows.append(("D41_role_echo", len(ec) if ec is not None else None,
                 "=0 (reported)", True, ec is None))
    su = r["D32_shape_use"]
    rows.append(("D32_shape_use",
                 (f"{len(su['bare'])} of {su['held']} analysis page(s) draw no "
                  f"library shape" + (f": {', '.join(su['bare'][:6])}"
                                      if su["bare"] else "")
                  + (f" · {', '.join(su['undrawable'])} not held (no framework "
                     f"in assets/frameworks.json names a shape)"
                     if su["undrawable"] else "")) if su else None,
                 "=0 per page where the move is drawable (gates)",
                 not (su and su["bare"]),
                 not su or not su["held"]))
    ds = r["D26_declared_scope"]
    if ds is None:
        rows.append(("D26_declared_scope", None,
                     "every declaration is one a reader meets", True, True))
    elif ds["storyline"] is None:
        rows.append(("D26_declared_scope", "no data-storyline declared",
                     "every declaration is one a reader meets", True, False))
    else:
        miss, hid = ds["missing"], ds["hidden"]
        detail = ("no checklist for this storyline" if miss is None else
                  (f"{len(miss)} section(s) neither covered nor declared"
                   if miss else "every typical section covered or declared"))
        if hid:
            detail += f"; {len(hid)} declaration(s) a reader cannot see"
        rows.append(("D26_declared_scope", detail,
                     "every declaration is one a reader meets", not hid, False))
        # The undeclared count is its own row so it REACHES a reader.
        # D26's verdict keyed on `hidden` alone, so a pitch deck covering six
        # of eleven typical sections with nothing declared produced "ok" and
        # check_deliverable printed "0 graded findings" — the whole C5
        # mechanism (declare the gap) was computed and then dropped. Surfacing
        # was the fix at the time; GATING is the fix now (0.1.543, owner
        # review). The condition was always binary and never a judgement: a
        # page that DECLARES an analysis move and draws none of the shapes the
        # library ships for it has said what it is doing and not done it. The
        # accepted reference deck declares no moves and passes untouched; the
        # conformance deck the owner opened declares seven and drew zero.
        rows.append(("D31_undeclared_sections",
                     None if miss is None else len(miss),
                     "=0 or declared (reported)",
                     not miss, miss is None))

    ip = r["D33_icon_provenance"]
    rows.append(("D33_icon_provenance",
                 None if ip is None
                 else len(ip["unknown"]) + len(ip["altered"]),
                 "=0 (gates)",
                 bool(ip) and not (ip["unknown"] or ip["altered"]),
                 ip is None))
    iu = r["D34_icon_uniqueness"]
    rows.append(("D34_icon_uniqueness",
                 f"{iu['distinct']} distinct over {iu['pages']} pages, "
                 f"{len(iu['reused'])} reused",
                 "reported", True, not iu["pages"]))

    ff = r["D36_font_family"]
    rows.append(("D36_font_family",
                 f"{len(ff['unembedded'])} declared, not embedded"
                 + (f" ({', '.join(ff['unembedded'][:3])})"
                    if ff["unembedded"] else ""),
                 "reported (GAP-027)", True, False))

    cs = r["D37_caption_scope"]
    rows.append(("D37_caption_scope", len(cs["with_source"]), "=0 (gates)",
                 not cs["with_source"], not cs["captions"]))
    rows.append(("D37_caption_name_len", len(cs["long_names"]),
                 f'<={CAPTION_NAME_CHARS["full"]} chars (reported)',
                 True, not cs["captions"]))

    ar = r["D38_agenda_rows"]
    rows.append(("D38_agenda_highlight",
                 len(ar["unmarked"]) if ar else "no launch rows",
                 "=0 (gates)", not (ar and ar["unmarked"]), False))
    rows.append(("D38_agenda_page_spans",
                 len(ar["with_pages"]) if ar else "no launch rows",
                 "=0 (gates)", not (ar and ar["with_pages"]), False))
    rows.append(("D38_agenda_run_echo",
                 len(ar["echoing"]) if ar else "no launch rows",
                 "reported", True, not ar))

    # THE BRAND MARK, which nothing looked at. The owner opened a deck on
    # 2026-08-22 whose cover and closing had lost the field globe and said so;
    # every gate in this file had passed it.
    bm = r["D39_bookend_mark"]
    rows.append(("D39_bookend_mark",
                 ("the two bookends carry different marks: "
                  + "; ".join(f"{k}={'+'.join(v) or 'nothing'}"
                              for k, v in bm["kinds"].items())
                  if bm["differ"] else 0) if bm else "no pair of drawn bookends",
                 "=0 (gates)", not (bm and bm["differ"]), bm is None))
    bmm = r["D40_bookend_is_the_brand"]
    d42 = r["D42_figure_spec"]
    rows.append(("D42_figure_spec",
                 len(d42["broken"]) if d42 else None, "=0 (gates)",
                 not (d42 and d42["broken"]), d42 is None))
    d43 = r["D43_figure_content"]
    # THREE STRINGS, and that is the point of the middle branch: `0` when every
    # declared figure named every member, `N thin` when one did not, and
    # `0, N unreadable` when a figure could not be read at all. A check whose
    # blind branch prints what its clean branch prints is FM-24.
    rows.append(("D43_figure_content",
                 (f"{len(d43['thin'])}"
                  + (f", {len(d43['blind'])} unreadable" if d43["blind"] else ""))
                 if d43 else None,
                 "=0 (gates)", not (d43 and d43["thin"]), d43 is None))
    rows.append(("D40_bookend_is_the_brand",
                 "; ".join(bmm) if bmm else 0,
                 "=0 (gates)", not bmm, bmm is None))

    ae = r["D35_agenda_exclusive"]
    rows.append(("D35_agenda_exclusive",
                 len(ae["strays"]) if ae else "no agenda page",
                 "=0 (gates)", not (ae and ae["strays"]), False))

    dc = r["D21_data_contract"]
    rows.append(("D21_data_contract",
                 len(dc["mismatches"]) if dc else None, "=0 (gates)",
                 bool(dc) and not dc["mismatches"], dc is None))
    vo = r["D19_vocabulary"]
    vo_bad = (len(vo["dangling"]) + len(vo["bad_blocks"]) + len(vo["bad_arity"])
              + len(vo["openers_missing_class"])
              + int(vo["globe_no_runtime"])
              + len(vo["dangling_vars"])) if vo else None
    rows.append(("D19_vocabulary", vo_bad, "=0 (gates)",
                 vo_bad == 0, vo is None))
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
    am = r["D27_agenda_mirror"]
    # "No agenda page" is a MEASURED absence and passes — a deck without an
    # agenda owes no mirror. n/a here would trip the blind-gates rule, which
    # is for a gate that could not look, not for one that looked and found
    # nothing to hold.
    rows.append(("D27_agenda_mirror",
                 len(am["orphans"]) if am else "no agenda page", "=0 (gates)",
                 am is None or not am["orphans"], False))
    tk = r["D28_takeaway"]
    rows.append(("D28_takeaway",
                 f"{len(tk['missing'])} of {tk['content_pages']} content pages "
                 f"without a takeaway" if tk else None,
                 "reported", True, tk is None))
    fn = r["D29_figure_numbers"]
    rows.append(("D29_figure_numbers",
                 (f"{len(fn['naked'])} of {fn['pages_with_figs']} figure pages "
                  f"carry none of the page's numbers"
                  + (f"; {len(fn['unasked'])} state their numbers as words, so "
                     f"this could not look at them" if fn.get("unasked") else ""))
                 if fn else None,
                 "reported", True, fn is None))
    fs = r["D30_figure_sequence"]
    rows.append(("D30_figure_sequence",
                 ("; ".join(filter(None, [
                     f"{len(fs['duplicates'])} repeated ({', '.join(str(d) for d in fs['duplicates'])})"
                     if fs["duplicates"] else "",
                     f"{len(fs['holes'])} missing ({', '.join(str(h) for h in fs['holes'])})"
                     if fs["holes"] else "",
                     "out of page order" if fs["out_of_order"] else "",
                 ])) or f"{fs['count']} figures numbered 1..{fs['count']}")
                 if fs else None,
                 "1..k once each, in page order (reported)",
                 bool(fs) and not (fs["duplicates"] or fs["holes"]
                                   or fs["out_of_order"]),
                 fs is None))
    vp = r["D16_visual_presence"]
    rows.append(("D16_visual_presence",
                 f"{len(vp['prose_only'])} of {vp['content_pages']} content pages "
                 f"prose-only, {len(vp['apparatus'])} apparatus "
                 f"({vp['apparatus_share']}%)" if vp else None,
                 "reported", True, vp is None))
    return [(n, v, t, "n/a" if skip else ("ok" if good else "FAIL"))
            for n, v, t, good, skip in rows]


def held_gates(r, verdicts, root=None) -> tuple[set, set]:
    """-> (the gating rows that had something to grade, the ones that did not).

    "Zero gating failures" is the sentence a board's reader takes away, and it
    does not say how much was held. Two decks of the 2026-08-26 conformance
    round both earned it: one had an agenda page, part openers and pages
    declaring an analysis move, so eighteen gates had a subject; the other had
    none of those, and four of its clean rows are gates printing `ok` over an
    absence with a fifth reading `n/a`.

    **This is not a defect in those four rows.** A measured absence passing is
    a deliberate ruling written into D27 and D35 in words — `n/a` is for a gate
    that could not look, not for one that looked and found nothing to hold —
    and a deck may legitimately have no agenda: the two intro decks the owner
    accepted have none. What was missing is the count beside the verdict, so a
    reader can tell a pass over eighteen from a pass over fifteen.

    The set is DECLARED in `evals/gates.json` (`subject`) rather than written
    here, and `check_repo`'s `vacuous gates` guard discovers it by blanking
    each measurement in turn and watching which gating rows keep saying `ok` —
    so a fifth cannot arrive undeclared, and a declaration naming a
    measurement `measure()` does not produce fails too.
    """
    import gate_registry
    import gating
    declared = gate_registry.load(root or ROOT)
    gates = gating.gating_metrics(verdicts, root or ROOT)
    held, vacuous = set(), set()
    for name in gates:
        subject = (declared.get(name) or {}).get("subject")
        # A GATE THAT FAILED OBVIOUSLY HAD SOMETHING TO GRADE. Without this a
        # metric could report FAIL and be counted as having nothing to check in
        # the same run — which D19 did the moment it grew a second, independent
        # assertion: a document with no `<use>` element made its declared
        # subject falsy while the new one had just failed on three dangling
        # colour names. The invariant is universal and cheap, and it holds for
        # every gate rather than for the one that exposed it.
        if verdicts.get(name) == "FAIL":
            held.add(name)
        elif verdicts.get(name) == "n/a" or _subject_absent(r, subject):
            vacuous.add(name)
        else:
            held.add(name)
    return held, vacuous


def _subject_absent(r, subject) -> bool:
    """Did the thing this gate grades fail to appear at all?

    Two shapes, because absence has two. `D27_agenda_mirror` is None when the
    document has no agenda page; `D25_image_provenance` is a dict that is
    present and says `rasters: 0`, which is a document with no images and a
    gate with nothing to check. `subject` names either the measurement or a
    `key.field` inside it, and `check_repo`'s `vacuous gates` guard validates
    the path against what `measure()` actually produces.
    """
    if not subject or subject == "always":
        # `always` is a positive claim, not a missing declaration: the subject
        # is the document itself — its text, its pages — so there is no shape
        # of deliverable this gate can be silent over. `check_repo`'s guard
        # requires EVERY gating row to say one or the other, because a gate
        # with no declaration would be counted held on a document that gave it
        # nothing, which is the whole defect.
        return False
    key, _, field = subject.partition(".")
    value = r.get(key)
    if value is None:
        return True
    if field:
        return not (isinstance(value, dict) and value.get(field))
    return False


def _d_number(name: str) -> int:
    """The D number in a verdict name, for ordering a summary line.

    A total order even for a name that does not open with one. None exists
    today; a crash inside a summary sentence is a poor way to learn that one
    arrived, and sorting it last is the harmless answer.
    """
    match = re.match(r"D(\d+)", name)
    return int(match.group(1)) if match else 999


def main(argv):
    ap = argparse.ArgumentParser(add_help=True, description=__doc__.split("\n")[0])
    ap.add_argument("files", nargs="+")
    ap.add_argument("--json", action="store_true",
                    help="the whole report as JSON. **The top level is a LIST, "
                         "one entry per document**, even for a single file — "
                         "take [0]. It is a list because this command accepts "
                         "several files; the shape is not going to change, "
                         "because scripts/lib/checker_report.py's parse_report "
                         "already normalises it for every caller inside this "
                         "package and a second shape would be a second thing "
                         "to keep in step. This help text is here because an "
                         "agent reading the stream from a shell has no such "
                         "reader, and three validation rounds each rediscovered "
                         "the list by crashing on it.")
    args = ap.parse_args(argv)

    results, failures, unmeasurable, gated_failure = [], 0, 0, 0
    blind_gates = 0
    for name in args.files:
        path = pathlib.Path(name)
        try:
            r = measure(path)
        except (Unmeasurable, OSError) as exc:
            unmeasurable += 1
            if not args.json:
                print(f"\n{name}\n  UNMEASURABLE  {exc}")
            continue
        _rows = grade(r)
        r["verdicts"] = {n: v for n, _, _, v in _rows}
        # HOW MANY GATES HAD A SUBJECT, beside what they said. "Zero gating
        # failures" is the sentence a reader takes away and it does not say how
        # much was held; a board printed it over a deck holding eighteen gates
        # and one holding thirteen. Reported through the report rather than
        # recomputed by each consumer, because the answer needs the gate
        # register and the raw measurement together.
        _held, _vacuous = held_gates(r, r["verdicts"])
        r["gates_held"] = sorted(_held)
        r["gates_with_nothing_to_grade"] = sorted(_vacuous)
        # The TARGET string, so a caller can tell a metric that could have
        # failed from one whose target is literally "reported" and therefore
        # cannot. check_fixtures.py needs exactly that to say which verdicts it
        # asserted and which it could not.
        r["targets"] = {n: t for n, _, t, _ in _rows}
        # WHICH METRICS GATE IS READ OFF THE ROWS, never listed here. This was a
        # hand-written tuple, and it fell one behind the day D20 was added: the
        # metric declared `"=0 (gates)"`, five documents were made to say five
        # gates because check_repo's `gating claims` guard reads that string,
        # and a file failing D20 alone exited 0. That guard compares the DOCS to
        # the target strings and cannot see a third copy of the list in here.
        # There is no third copy now — the target string is the one authority,
        # and adding a gate is adding "(gates)" to its row and nothing else.
        gates = {n for n, t in r["targets"].items() if "(gates)" in (t or "")}
        if any(r["verdicts"][n] == "FAIL" for n in gates):
            gated_failure += 1
        # A GATE THAT COULD NOT BE MEASURED HAS NOT BEEN PASSED. Three of the
        # five read `n/a` when no `<section class="page">` matches, and a
        # document is "measurable" on the strength of its token block alone —
        # so a deck whose pages are `<div class="page">` and which carries no
        # handling terms on any page printed "nothing flagged" and exited 0.
        # Both commercial gates were silent, on the checker SKILL.md puts on
        # the pre-delivery path. `inspect_layout` has said the sentence for
        # this since 0.1.350: a check that did not run is not a check that
        # passed.
        # NOT APPLICABLE IS NOT NOT MEASURED. This counted every `n/a` gating
        # row as blind, which was right for the case it was written for — D12
        # and D15 reading n/a because no `<section class="page">` matched, a
        # commercial gate silent on unreadable markup — and wrong for the six
        # gates that reach n/a because the predicate has nothing to look at: a
        # Chinese ban list on an English deck, a caption rule on a deck with no
        # captions. `evals/gates.json` carries the difference in `na_means`,
        # because no checker holds it: the row itself cannot tell you whether
        # its own silence is honest.
        na_ok = {n for n, g in gate_registry.load(ROOT).items()
                 if (g.get("na_means") or "").strip()}
        blind = sorted(n for n in gates
                       if r["verdicts"][n] == "n/a" and n not in na_ok)
        if blind:
            blind_gates += 1
            # IN THE REPORT, not over it. This warning used to print even under
            # --json, so the one document it fires on — div.page markup, the
            # exact case it describes — emitted prose in front of the JSON and
            # broke every machine consumer. trace.py read that as "the checker
            # had nothing to say" and nine design gates vanished from a build
            # record without a word (0.1.497 fixed the consumer; this is the
            # root). A warning that corrupts the channel it travels on warns
            # nobody.
            r["blind_gates"] = blind
            if not args.json:
                print(f"\n  {len(blind)} gating metric(s) could not be measured on "
                      f"{r['file']}: {', '.join(blind)}")
                print("        this is not a pass. D12 and D15 need "
                      "<section class=\"page\"> to find pages at all — check the "
                      "page markup before reading anything else here")
        results.append(r)

    if args.json:
        print(json.dumps(results, indent=2))
        return 1 if (unmeasurable or gated_failure or blind_gates) else 0

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
        for pid, left, right, shared in (r.get("D41_role_echo") or []):
            print(f"        {pid}: .{left} repeats .{right} — {shared!r}. "
                  f"Two roles, one sentence: the reader is told the same thing "
                  f"twice and one of the two slots is doing nothing")
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
        vv = r["D19_vocabulary"]
        if vv:
            if vv["dangling"]:
                print(f"        {len(vv['dangling'])} icon reference(s) resolve to "
                      f"nothing: {', '.join('#' + d for d in vv['dangling'][:5])}")
                if not vv["symbols"]:
                    print("        this document carries NO <symbol> at all — the "
                          "sprite lives in the reference fixture's BODY, and a "
                          "document assembled from its <head> alone has none of it")
            for dv in (vv.get("dangling_vars") or [])[:6]:
                print(f"        {dv} names no custom property this document "
                      f"declares — an unresolvable var() with no fallback is "
                      f"invalid at computed-value time, so the element takes "
                      f"the INITIAL value; for an SVG fill that is BLACK")
            if vv["globe_no_runtime"]:
                print(f"        {vv['globe_marks']} [data-globe] figure(s) and no "
                      f"globe runtime in this document — the marks are still "
                      f"frames; the assembler emits it with "
                      f"scripts/build/embed_globe.py, it is never copied out of "
                      f"another file")
            if vv["globe_marks_missing_hook"]:
                print(f"        reported, not graded: globe drawn without "
                      f"data-globe on "
                      f"{', '.join(vv['globe_marks_missing_hook'][:4])} — the "
                      f"brand mark is embedded live on the cover and the closing")
            for cls, missing in vv["bad_blocks"][:5]:
                print(f"        .{cls} is used without {', '.join('.' + m for m in missing)}"
                      f" — tokens/ renders it through those children, and without "
                      f"them it borrows whatever styling it collides with")
            for cls, got, want in vv["bad_arity"][:5]:
                print(f"        .{cls} has {got} children and tokens/ lays it "
                      f"out on {want} columns — the extra or missing child "
                      f"lands in the wrong track, which is how a half-width "
                      f"column became 34px and wrapped one word per line")
            for pid in vv["openers_missing_class"][:5]:
                print(f"        section {pid} carries an .openframe and not "
                      f"class=\"page opener\" — the lime opener is a class, not a "
                      f"layout, so the page renders blank")
        pfd = r["D20_palette_fidelity"]
        if pfd.get("differs"):
            print(f"        this document declares a palette of its own: "
                  f"{len(pfd['differs'])} of {pfd['compared']} shared colour "
                  f"tokens disagree with tokens/lumi-theme.css")
            for d in pfd["differs"][:5]:
                print(f"          {d['token']:16} shipped {d['shipped']:<24} "
                      f"document {d['document']}")
        for ph in r["D14_placeholders"][:8]:
            print(f"        {ph['page']} still carries the slot {ph['text']}")
        for fpath in (r["D15_footer_path"] or {}).get("found", [])[:6]:
            print(f"        page {fpath['page']} footer cites the file "
                  f"{fpath['path']} — a path is not a source a reader can open")
        v = r["D9_layout_variety"]
        if v:
            for pid, cls in v["unknown"][:6]:
                print(f"        {pid} uses no shipped layout (body class: {cls})")
            print(f"        layouts: {v['distinct']} distinct across "
                  f"{v['pages']} pages, {v['top_layout']} carries "
                  f"{v['top_share']}%")

    if blind_gates:
        # BEFORE "nothing flagged", always. A run with a gate it could not take
        # has not cleared that gate, and the reassuring sentence below it is the
        # one this package keeps finding in its own output.
        print(f"\n{blind_gates} file(s) carry a gating metric that could not be "
              f"measured. Nothing below is a verdict on those.")
    if not failures:
        print("nothing else flagged" if blind_gates else "\nnothing flagged")
    elif gated_failure:
        # Named from the rows, like the exit decision above. This sentence was
        # the fourth hand-written copy of the gating list and it was one behind
        # too — it said "those four block" while five metrics declared a gate.
        # The REASONS are keyed to the metric now for the same reason: the list
        # of five clauses was printed whatever failed, so three named ids came
        # with five explanations.
        why = {"D12": "a page missing its handling terms",
               "D14": "a document still carrying a slot",
               "D15": "a footer citing a file path",
               "D19": "markup that cannot render itself",
               "D20": "a palette that is not this package's"}
        blocked = sorted(
            {n for r in results for n, v in r["verdicts"].items()
             if v == "FAIL" and "(gates)" in (r["targets"].get(n) or "")},
            key=_d_number)
        ids = [n.split("_")[0] for n in blocked]
        print(f"\n{failures} metric(s) failed, and {gated_failure} file(s) fail on "
              f"{', '.join(ids)} — those block, because "
              + ", ".join(why.get(i, f"what {i} asks") for i in ids)
              + " are not judgements about design")
    else:
        print(f"\n{failures} thing(s) worth a look — none of this blocks; "
              f"read them, then look at the page")
    if unmeasurable:
        print(f"{unmeasurable} file(s) could not be measured at all")
    return 1 if (unmeasurable or gated_failure or blind_gates) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
