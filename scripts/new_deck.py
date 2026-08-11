#!/usr/bin/env python3
"""Emit a deck skeleton that already renders, in the standard order.

    python3 scripts/new_deck.py > mydeck.en.html
    python3 scripts/new_deck.py --genre internal --pages 8 --parts A,B,C

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

The first version of this file emitted cover, one opener, a run of pages and a
closing. That is not a deck; it is a deck's middle. The agenda is the page a
reader uses to decide what to skip, and parts are a sequence rather than a
single heading.

D19 in check_design.py is the negative half of this: it refuses a document whose
references do not resolve and whose blocks do not carry their contract. This is
the positive half — it hands you the ones that do.

Standard library only.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "fixtures" / "deck-pass.en.html"

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
    return (head + f'\n<body class="deck" data-theme="light" '
            f'data-geometry="{geometry}" data-genre="{genre}">\n' + sprite)


def ground(src):
    return re.search(r'(<svg class="ground".*?</svg>)', src, re.S).group(1)


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
    total = args.pages + 3 + len(parts)      # cover, agenda, closing, + openers
    out = [preamble(args.genre, args.geometry)]

    # The cover title carries TWO INKS: the claim in ink, the noun the deck is
    # about in the live green, so the green marks what the page is for rather
    # than decorating it.
    out.append(f'''<section class="page cover" id="cover">
  {g}
  <div class="body cover-grid">
    <div class="typeblock">
      <p class="wordmark">LUMI</p>
      <h1>A title that states the argument about its
      <span class="subj">subject</span></h1>
      <p class="sub">One sentence saying what this is.</p>
    </div>
    <div class="markcell"><!-- the mark, or a live globe: assets/brand/README.md --></div>
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

    out.append(f'''<section class="page closing" id="close">
  {g}
  <div class="body cover-grid">
    <div class="typeblock">
      <p class="wordmark">LUMI</p>
      <h2>What the reader carries out about its
      <span class="subj">subject</span></h2>
      <p class="sub">The argument in one paragraph.</p>
    </div>
    <div class="markcell"><!-- the same mark as the cover --></div>
    <div class="attrs">
      <div><span class="k">Label</span><span class="v">value</span></div>
    </div>
    <p class="colophon">Built with lumi-style VERSION.</p>
  </div>
  {foot(total, total)}
</section>''')

    out.append("</body></html>")
    print("\n".join(out))
    print(f"<!-- scaffold: {total} pages, standard order. Every icon reference "
          f"resolves, every block carries its contract, and each opener carries "
          f"its class. check_design.py's D19 holds all three. -->", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
