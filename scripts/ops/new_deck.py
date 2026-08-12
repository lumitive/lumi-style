#!/usr/bin/env python3
"""Emit a deck skeleton that already renders, in the standard order.

    python3 scripts/ops/new_deck.py > mydeck.en.html
    python3 scripts/ops/new_deck.py --genre internal --pages 8 --parts A,B,C

WHY THIS EXISTS. A deliverable shipped with no icons anywhere, a blank part
opener, and a block whose two halves rendered 246px and 34px wide — all of it
because the structure was hand-authored from memory of class names rather than
copied from the reference implementation that renders them.

The head is not the document. `fixtures/deck-pass.en.html` carries its token
block in `<head>` and its icon sprite and page ground in `<body>`, so a document
assembled by slicing to `</head>` has a full stylesheet and no icons at all —
and a `<use>` pointing at nothing is valid markup that renders as empty space.

THE STANDARD ORDER, which is the default unless a request says otherwise:

    cover · agenda · Part A opener · content… · Part B opener · content… · closing

`--genre training` appends the reference pages Template 4's arc ends on — a
glossary as `dl.gloss`, marked `data-role="apparatus"` — before the closing,
because a training document's last pages are the ones a learner returns to.

The first version of this file emitted cover, one opener, a run of pages and a
closing. That is not a deck; it is a deck's middle. The agenda is the page a
reader uses to decide what to skip, and parts are a sequence rather than a
single heading.

RUN THIS SCRIPT; DO NOT SLICE THE FIXTURE BY HAND. A 34-page review shipped
with the fixture's own furniture in reader-facing positions — `REPLACE ME` as
its title, `www.example.org` in every footer — because its pages were copied
from `fixtures/deck-pass.en.html` instead of generated here. The fixture is a
checker input; this scaffold is the thing an author starts from, and
`check_design.py`'s D14 now refuses the slots both of them emit.

D19 in check_design.py is the negative half of this: it refuses a document whose
references do not resolve and whose blocks do not carry their contract. This is
the positive half — it hands you the ones that do.

Standard library only.
"""
from __future__ import annotations

import argparse
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

_SCRIPTS_ROOT = next(p for p in _bs_pathlib.Path(__file__).resolve().parents
                     if p.name == "scripts")
for _sub in ("lib", "render", "check", "build", "ops", ""):
    _p = str(_SCRIPTS_ROOT / _sub) if _sub else str(_SCRIPTS_ROOT)
    if _p not in _bs_sys.path:
        _bs_sys.path.append(_p)
del _bs_pathlib, _bs_sys, _SCRIPTS_ROOT, _sub, _p
# --- end bootstrap ---
import embed_font  # noqa: E402
import embed_globe  # noqa: E402

ROOT = next(p for p in pathlib.Path(__file__).resolve().parents
            if p.name == "scripts").parent
FIXTURE = ROOT / "fixtures" / "deck-pass.en.html"
BRAND_GLOBE = ROOT / "assets" / "brand" / "lumivate" / "globe-field.svg"


# The selectors inside a vendored mark's style block that carry a DOCUMENT
# palette rather than the component's own rendering. Inline SVG shares the
# host document's style scope, so these would silently redefine the host's
# tokens; everything else in that block is the component and must survive.
PALETTE_SELECTORS = (":root", "body.dark", ".dark")


def _strip_palette(style):
    """Drop the palette blocks from a vendored component's CSS, keep the rest.

    The first cut of this dropped the ENTIRE `<style>` element, on the reading
    that "the document's token block paints the classes". It does not: the
    globe's own `.gl-*` rules and its `.trade` region palette live in that
    block and nowhere in `tokens/`, so stripping it left every trade region
    filling with the UA default — black — and the land unfilled. The region
    palette file says this failure in its own header ("a palette nobody could
    use… every check passed, because none reads rendered colour"), and the
    0.1.442 review found it again from the other side: the owner asked where
    the trade-region colours went.
    """
    out, i = [], 0
    while i < len(style):
        brace = style.find("{", i)
        if brace == -1:
            out.append(style[i:])
            break
        selector = style[i:brace].strip().lstrip("}").strip()
        depth, j = 1, brace + 1
        while depth and j < len(style):
            depth += 1 if style[j] == "{" else -1 if style[j] == "}" else 0
            j += 1
        # Comments first, THEN the split: these blocks are documented in prose
        # above them, and a comma inside that prose cut the selector mid-comment
        # so `:root` read as commentary and survived.
        selector = re.sub(r"/\*.*?\*/", " ", selector, flags=re.S)
        first = selector.split(",")[0].strip().split("\n")[-1].strip()
        if first not in PALETTE_SELECTORS:
            out.append(style[i:j])
        i = j
    return "".join(out)


def brand_globe():
    """The LUMIVATE field globe, prepared for embedding in a document.

    The default cover/closing mark (owner directive, 0.1.442 review: a
    deliverable shipped a fresh anonymous render instead of the brand). The
    vendored file is the standalone published form and carries its own
    `<style>` block, which holds two different things: the component's own
    rendering (`.gl-*` and the `.trade` region palette, which exist nowhere
    else) and a copy of the document palette. Only the second is stripped —
    inline SVG shares the host's style scope, so a vendored `:root` would
    redefine the host's tokens, while the component's rules are exactly what
    makes the mark render. The lock in assets/brand/LOCKED.json holds the
    file; this prepares a copy for embedding and changes nothing on disk.
    """
    src = BRAND_GLOBE.read_text(encoding="utf-8")
    return re.sub(r"<style>(.*?)</style>",
                  lambda m: "<style>" + _strip_palette(m.group(1)) + "</style>",
                  src, count=1, flags=re.S)

GENRES = ("sales", "consulting", "internal", "training")


def preamble(genre, geometry):
    """Everything before the first page: the token block AND the sprite.

    Taken from the fixture rather than rebuilt, because the fixture is the
    reference implementation — the artifact `check_fixtures.py` asserts the
    checkers' verdicts against, so it is the one file guaranteed to render
    every role this package defines.
    """
    src = FIXTURE.read_text(encoding="utf-8")
    head = src[:src.index("</head>") + len("</head>")]
    # EVERYTHING between <body> and the first page, not the first <svg>. The
    # fixture opens with the icon sprite AND a second hidden svg carrying the
    # page ground; taking only the first left `#g-ground` dangling. A preamble
    # is whatever comes before the content, and guessing how many elements that
    # is has now been wrong twice.
    body_at = src.index("<body", src.index("</head>"))
    body_open_end = src.index(">", body_at) + 1
    sprite = src[body_open_end:src.index("<section", body_open_end)]
    head = re.sub(r"<title>.*?</title>", "<title>REPLACE ME</title>", head, count=1)
    # The face rides along. design-rules.md requires it embedded, and when
    # embedding was a separate step, two deliverables in one week shipped with
    # zero @font-face blocks and rendered in the system stack. The fixture
    # itself stays font-free — it is a checker input, and the checkers read
    # markup, not metrics.
    head = head.replace("</head>",
                        "<style>\n" + embed_font.css() + "\n</style></head>")
    return (head + f'\n<body class="deck" data-theme="light" '
            f'data-geometry="{geometry}" data-genre="{genre}">\n' + sprite)


def ground(src):
    m = re.search(r'(<svg class="ground".*?</svg>)', src, re.S)
    if m is None:
        raise ValueError('the source deck has no <svg class="ground"> block')
    return m.group(1)


def foot(n, total):
    return ('<div class="foot"><div class="terms"><span class="conf">'
            '<svg class="ic" aria-hidden="true"><use href="#i-shield"/></svg>'
            'Confidential &#183; internal use &#183; do not forward</span></div>'
            '<span class="site">www.lumivate.io</span>'
            f'<span>{n:02d} / {total}</span></div>')


# One of every block pattern, with the markup the FIXTURE uses — not the markup
# a class name suggests. `.swap` is the worked example: its rendering is
# `grid-template-columns: 1fr 34px 1fr` and it takes THREE children — a before,
# an arrow, an after. Written with two, the after lands in the 34px arrow column
# and wraps one word per line. That shipped, and its content was trimmed three
# times before anyone measured the box.
ARROW = '<span class="arw">&#8594;</span>'

SAMPLES = [
    '      <p class="listhead">A heading over a block</p>\n'
    '      <p class="gd">The tier-one callout. One per page, no more.</p>\n'
    '      <ul><li>A bulleted list is a small set of criteria that must all '
    'hold.</li>\n'
    '      <li>A numbered list is a sequence someone performs in order.</li></ul>',

    '      <div class="band">'
    '<div><span class="k">Label</span><div class="v">41<span class="u">%</span>'
    '</div></div>'
    '<div><span class="k">Label</span><div class="v">312</div></div>'
    '</div>',

    '      <div class="grades">\n'
    '        <div class="gr g4"><i></i><p class="gn">The row&#8217;s subject</p>\n'
    '          <p class="gq">and what is true of it</p></div>\n'
    '        <div class="gr g2"><i></i><p class="gn">A second row</p></div>\n'
    '      </div>',

    '      <div class="swaps">\n'
    '        <div class="swap"><span class="no">What was believed</span>'
    + ARROW + '<span class="yes">What the measurement says</span></div>\n'
    '        <div class="swap"><span class="no">A second belief</span>'
    + ARROW + '<span class="yes">and its correction</span></div>\n'
    '      </div>',
]


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--genre", choices=GENRES, default="internal")
    ap.add_argument("--geometry", choices=("landscape", "portrait"),
                    default="landscape")
    ap.add_argument("--pages", type=int, default=6,
                    help="content pages, not counting cover, agenda, the part "
                         "openers and the closing")
    ap.add_argument("--parts", default="A,B",
                    help="part letters, comma separated. Two is the default: "
                         "one part is not a part, it is a document.")
    args = ap.parse_args(argv)

    src = FIXTURE.read_text(encoding="utf-8")
    g = ground(src)
    parts = [x.strip() for x in args.parts.split(",") if x.strip()]
    # cover, agenda, closing, + openers; training appends its reference page.
    apparatus = 1 if args.genre == "training" else 0
    total = args.pages + 3 + len(parts) + apparatus
    out = [preamble(args.genre, args.geometry)]

    # The cover title carries TWO INKS: the claim in ink, the noun the deck is
    # about as lime on its own dark chip (`.subj`) — the same green the part
    # openers carry at page scale, so the title marks what the page is FOR in
    # the deck's one event colour rather than decorating it.
    out.append(f'''<section class="page cover" id="cover">
  {g}
  <div class="body cover-grid">
    <div class="typeblock">
      <p class="wordmark">LUMI Style</p>
      <h1>A title that states the argument about its
      <span class="subj">subject</span></h1>
      <p class="sub">One sentence saying what this is.</p>
    </div>
    <div class="markcell" data-globe>{brand_globe()}</div>
    <div class="attrs">
      <div><span class="k">Label</span><span class="v">value</span></div>
      <div><span class="k">Label</span><span class="v">value</span></div>
    </div>
  </div>
  {foot(1, total)}
</section>''')

    rows = "".join(
        f'        <div class="gr g4"><i></i><p class="gn">Part {q} '
        f'&#183; its subject</p>\n'
        f'          <p class="gq">what these pages establish</p></div>\n'
        for q in parts)
    out.append(f'''<section class="page" id="agenda">
  {g}
  <div class="body stack">
    <div class="lede">
      <p class="eyebrow"><svg class="ic" aria-hidden="true"><use href="#i-list-checks"/></svg>Agenda</p>
      <h2 class="t">What this document argues, and where</h2>
      <p class="sup">One line saying how to read it.</p>
    </div>
    <div class="fill">
      <div class="grades">
{rows}      </div>
    </div>
  </div>
  {foot(2, total)}
</section>''')

    n = 3
    per = max(1, args.pages // max(1, len(parts)))
    for pi, part in enumerate(parts):
        # THE OPENER CARRIES class="page opener". The lime background is a
        # class, not a layout: without it the page renders blank.
        out.append(f'''<section class="page opener" id="open{part}">
  {g}
  <div class="body full-bleed no-lede">
    <div class="bleed openframe">
      <div class="openpart">Part {part}</div>
      <div class="openclaim">What this part argues</div>
      <div class="openrun">How many pages, and what they cover.</div>
    </div>
  </div>
  {foot(n, total)}
</section>''')
        n += 1
        count = per if pi < len(parts) - 1 else args.pages - per * (len(parts) - 1)
        for i in range(count):
            block = SAMPLES[(pi * per + i) % len(SAMPLES)]
            out.append(f'''<section class="page" id="p{n}">
  {g}
  <div class="body split">
    <div class="lede">
      <p class="eyebrow"><svg class="ic" aria-hidden="true"><use href="#i-radar"/></svg>Part {part} &#183; this page&#8217;s label</p>
      <h2 class="t">A title naming its subject and carrying a fact</h2>
      <p class="sup">The support line, one sentence and not a summary.</p>
    </div>
    <div class="fill">
{block}
    </div>
    <div class="fill">
      <div class="fig"><!-- draw what the content IS: a flow, a timeline, a
        bridge, a table. Shapes carry semantics; dashed means not built. -->
      <div class="cap"><span class="n">Figure {n - 2}</span> A title stating a
      conclusion <span class="srcline">Where this came from</span></div></div>
    </div>
  </div>
  {foot(n, total)}
</section>''')
            n += 1

    if apparatus:
        # Template 4's arc ends on the pages a learner returns to. The page is
        # DECLARED apparatus (design-rules.md §2b): D16's visual-share target
        # exempts it, up to the one-in-five ceiling.
        out.append(f'''<section class="page" id="gloss" data-role="apparatus">
  {g}
  <div class="body stack">
    <div class="lede">
      <p class="eyebrow"><svg class="ic" aria-hidden="true"><use href="#i-book-open"/></svg>Reference</p>
      <h2 class="t">The terms this document uses, defined once</h2>
      <p class="sup">The page a learner returns to after the session.</p>
    </div>
    <div class="fill">
      <dl class="gloss">
        <dt>Term</dt><dd>What it means in this document, one sentence.</dd>
        <dt>A second term</dt><dd>and its definition, with its source where a
        trainee will repeat it.</dd>
      </dl>
    </div>
  </div>
  {foot(n, total)}
</section>''')
        n += 1

    out.append(f'''<section class="page closing" id="close">
  {g}
  <div class="body cover-grid">
    <div class="typeblock">
      <p class="wordmark">LUMI Style</p>
      <h2>What the reader carries out about its
      <span class="subj">subject</span></h2>
      <p class="sub">The argument in one paragraph.</p>
    </div>
    <div class="markcell" data-globe>{brand_globe()}</div>
    <div class="attrs">
      <div><span class="k">Label</span><span class="v">value</span></div>
    </div>
    <p class="colophon">Built with lumi-style VERSION.</p>
  </div>
  {foot(total, total)}
</section>''')

    # The runtime turns every [data-globe] — the cover and the closing. It
    # respects prefers-reduced-motion, and with JavaScript off the reader keeps
    # the exact static frame above. Rotation is part of the mark's contract
    # (owner directive): a still field globe is the fallback, not the design.
    out.append(embed_globe.build())
    out.append("</body></html>")
    print("\n".join(out))
    print(f"<!-- scaffold: {total} pages, standard order. Every icon reference "
          f"resolves, every block carries its contract, and each opener carries "
          f"its class. check_design.py's D19 holds all three. -->", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
