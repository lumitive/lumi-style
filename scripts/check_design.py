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

**Nothing here gates.** Every number is a diagnostic for a designer to read, and
the exit code is 0 unless a file could not be measured at all. SKILL.md rule 4 is
the reason: a page is done when a human reads it as intentional, and a metric that
can be satisfied without improving the page ends the looking instead of directing
it. D7, an 82% page-fill floor, was withdrawn in 2.0.0 for exactly that — it was
satisfied by stretching table rows while four diagrams rendered at 40% of their
cell. For page geometry and centerpiece scale use scripts/inspect_layout.py.

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

TYPE_FLOOR_PX = 11.0
SOURCE_FLOOR_PX = 10.5      # the single documented exception: figure source lines
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
    "rail", "quad", "sidebar-notes", "full-bleed", "diagonal-flow",
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
    """Report the small end of the type scale. There is no floor: 2.0.0 withdrew
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


def d8_support_line(raw):
    """Every content page carries a support line under the title. Figure pages
    are not exempt: a diagram with nothing introducing it drops the reader in."""
    missing = []
    for cls, pid, body in _pages(raw):
        if "cover" in cls or "closing" in cls:
            continue
        # A .lead block does exactly what a support line does — say what the
        # page is about, under the title — and 2.1.0 made it the answer on the
        # pages whose point is one number or one claim. A statement page that
        # carries only a claim needs nothing else under it.
        if re.search(r'<p class="(?:sup|lede)\b', body):
            continue
        if re.search(r'class="[^"]*\blead\b', body) or "opener" in cls:
            continue
        missing.append(pid)
    return missing


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
    eyebrow = len(re.findall(r'<div class="eyebrow">\s*<svg class="ic"', raw))
    in_fig = len(re.findall(r'<use href="#i-[\w-]+"/>\s*</svg>\s*(?:<text|</g>)', raw))
    svg_icons = len(re.findall(r'<svg[^>]*class="[^"]*\bic\b[^"]*"', raw))
    return {"eyebrow_icons": eyebrow, "icon_instances": svg_icons,
            "figure_or_row_icons": max(0, svg_icons - eyebrow)}


def d6_footer(raw):
    pages = re.findall(r'<section[^>]*class="[^"]*\bpage\b[^"]*"[^>]*>(.*?)</section>',
                       raw, re.S | re.I)
    if not pages:
        return None
    missing_src, missing_total = [], []
    for i, body in enumerate(pages):
        foot = re.search(r'class="[^"]*\bfoot\b[^"]*"[^>]*>(.*?)</div>', body, re.S)
        text = re.sub(r"<[^>]+>", " ", foot.group(1)) if foot else ""
        # The page is sourced, wherever the line lives. A single-figure page
        # states its source under the figure, and repeating it in the footer is
        # what 2.2.0 removed: eleven pages said the same thing twice and two
        # said it word for word. What this metric is for is a page that cites
        # nothing at all, so it asks the page, not the footer.
        footer_src = bool(foot) and 'class="src"' in foot.group(1) and \
            re.sub(r"<[^>]+>", "", re.search(r'class="src"[^>]*>(.*?)</span>',
                                             foot.group(1), re.S).group(1)).strip()
        figure_src = re.search(r'class="[^"]*\bsrcline\b', body) is not None
        if not (footer_src or figure_src):
            missing_src.append(i)
        if not re.search(r"\b\w+\s*/\s*\d+\b", text):
            missing_total.append(i)
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
        "D6_footer": d6_footer(raw),
        "D8_support_line": d8_support_line(raw),
        "D9_layout_variety": d9_layout_variety(raw),
        "D10_label_icons": d10_label_icons(raw),
    }


def grade(r):
    rows = []
    rows.append(("D1_contrast", len(r["D1_contrast"]), "=0",
                 not r["D1_contrast"], False))
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
    v = r["D9_layout_variety"]
    rows.append(("D9_layout_spread",
                 f"{v['distinct']} layouts, top {v['top_share']}%" if v else None,
                 "reported", True, v is None))
    i = r["D10_label_icons"]
    rows.append(("D10_label_icons",
                 f"{i['eyebrow_icons']} eyebrow, {i['figure_or_row_icons']} in figures"
                 if i else None, "reported", True, i is None))
    return [(n, v, t, "n/a" if skip else ("ok" if good else "FAIL"))
            for n, v, t, good, skip in rows]


def main(argv):
    ap = argparse.ArgumentParser(add_help=True, description=__doc__.split("\n")[0])
    ap.add_argument("files", nargs="+")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    results, failures, unmeasurable = [], 0, 0
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
        results.append(r)

    if args.json:
        print(json.dumps(results, indent=2))
        return 1 if unmeasurable else 0

    for r in results:
        rows = grade(r)
        print(f"\n{r['file']}  ({r['palette']} palette)")
        for name, value, target, verdict in rows:
            print(f"  {verdict:<5} {name:<22} {str(value):<24} target {target}")
            if verdict == "note":
                failures += 1
        for f in r["D1_contrast"][:6]:
            print(f"        contrast {f['ratio']}:1 on {f['on']} — "
                  f"{f['selector']} uses --{f['token']}"
                  + (f" at {f['font_size_px']}px" if f["font_size_px"] else ""))
        for line in r["D2_type_scale"]["smallest"]:
            print(f"        {line}")
        for h in r["D4_palette_literals"][:6]:
            print(f"        literal colour {h} outside the token block")
        for o in (r["D3_callouts"] or {}).get("over_budget", [])[:6]:
            print(f"        page {o['page_index']} carries {o['tier1']} tier-1 callouts")
        for pid in r["D8_support_line"][:8]:
            print(f"        {pid} has no support line under its title")
        v = r["D9_layout_variety"]
        if v:
            for pid, cls in v["unknown"][:6]:
                print(f"        {pid} uses no shipped layout (body class: {cls})")
            if v["top_share"] > LAYOUT_MAX_SHARE:
                print(f"        {v['top_layout']} carries {v['top_share']}% of pages")
            if v["pages"] >= LAYOUT_MIN_PAGES and v["distinct"] < LAYOUT_MIN_DISTINCT:
                print(f"        only {v['distinct']} distinct layouts across {v['pages']} pages")

    print("\nnothing flagged" if not failures
          else f"\n{failures} thing(s) worth a look — none of this blocks; "
               f"read them, then look at the page")
    if unmeasurable:
        print(f"{unmeasurable} file(s) could not be measured at all")
    return 1 if unmeasurable else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
