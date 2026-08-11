#!/usr/bin/env python3
"""Emit a deck skeleton that already renders.

    python3 scripts/new_deck.py > mydeck.en.html
    python3 scripts/new_deck.py --genre internal --pages 8

WHY THIS EXISTS. A deliverable shipped with no icons anywhere, a blank part
opener and a block whose numbers had come away from their content — all of it
because the structure was hand-authored from memory of class names rather than
copied from the reference implementation that renders them.

The head is not the document. `fixtures/deck-pass.en.html` carries its token
block in `<head>` and its **icon sprite in the first element of `<body>`**, so
a document assembled by slicing to `</head>` has a full stylesheet and no icons
at all — and a `<use>` pointing at nothing is valid markup that renders as
empty space. Nothing caught that until D19.

So this emits the whole preamble, and one of every block pattern with the
markup `tokens/` actually renders it through. An author edits content into a
structure that already works, which is the opposite of what happened.

D19 in check_design.py is the negative half of this: it refuses a document
whose references do not resolve. This is the positive half — it hands you the
ones that do.

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
    reference implementation — it is the artifact `check_fixtures.py` asserts
    the checkers' verdicts against, so it is the one file guaranteed to render
    every role this package defines.
    """
    src = FIXTURE.read_text(encoding="utf-8")
    head = src[:src.index("</head>") + len("</head>")]
    # The sprite: the hidden <svg> that opens <body>. Everything from the body
    # tag to the end of that element.
    # EVERYTHING between <body> and the first page, not the first <svg>. The
    # fixture opens with the icon sprite AND a second hidden svg carrying the
    # page ground; taking only the first left `#g-ground` dangling, which is
    # the same class of miss as taking only the head — a preamble is whatever
    # comes before the content, and guessing how many elements that is has now
    # been wrong twice.
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
            f'<span class="site">www.lumivate.io</span>'
            f'<span>{n:02d} / {total}</span></div>')


# One of every block pattern, with the children tokens/ renders it through.
# Copy a stanza, replace the words, delete the rest. Each carries the contract
# D19 checks for, so a stanza edited in place cannot fail it.
BLOCKS = '''      <p class="listhead">A heading over a block</p>
      <p class="gd">The tier-one callout. One per page, no more.</p>
      <ul><li>A bulleted list is a small set of criteria that must all hold.</li>
      <li>A numbered list is a sequence someone performs in order.</li></ul>
      <div class="band"><div><span class="k">Label</span><div class="v">41<span class="u">%</span></div></div>
        <div><span class="k">Label</span><div class="v">312</div></div></div>
      <div class="grades">
        <div class="gr g4"><i></i><p class="gn">The row's subject</p>
          <p class="gq">and what is true of it</p></div>
        <div class="gr g2"><i></i><p class="gn">A second row</p></div>
      </div>
      <div class="swap">
        <div class="no"><p class="listhead">One option</p>
          <ul><li>what it costs</li></ul></div>
        <div class="yes"><p class="listhead">The other</p>
          <ul><li>what it costs</li></ul></div>
      </div>'''


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--genre", choices=GENRES, default="internal")
    ap.add_argument("--geometry", choices=("landscape", "portrait"),
                    default="landscape")
    ap.add_argument("--pages", type=int, default=6,
                    help="content pages, not counting cover, opener and closing")
    args = ap.parse_args(argv)

    src = FIXTURE.read_text(encoding="utf-8")
    g = ground(src)
    total = args.pages + 3
    out = [preamble(args.genre, args.geometry)]

    out.append(f'''<section class="page cover" id="cover">
  {g}
  <div class="body cover-grid">
    <div class="typeblock">
      <p class="wordmark">LUMI</p>
      <h1>A title that states the argument</h1>
      <p class="sub">One sentence saying what this is.</p>
    </div>
    <div class="markcell"><!-- the mark, or a live globe: see assets/brand/README.md --></div>
    <div class="attrs">
      <div><span class="k">Label</span><span class="v">value</span></div>
      <div><span class="k">Label</span><span class="v">value</span></div>
    </div>
  </div>
  {foot(1, total)}
</section>''')

    # THE OPENER CARRIES class="page opener". The lime background is a class,
    # not a layout: a section with an .openframe and no `opener` renders blank,
    # which is exactly the page a reader reported as a bug.
    out.append(f'''<section class="page opener" id="openA">
  {g}
  <div class="body full-bleed no-lede">
    <div class="bleed openframe">
      <div class="openpart">Part A</div>
      <div class="openclaim">What this part argues</div>
      <div class="openrun">How many pages, and what they cover.</div>
    </div>
  </div>
  {foot(2, total)}
</section>''')

    # One block per page rather than all of them on one. A page carrying every
    # pattern at once overflows its column, and a scaffold that fails the
    # layout gate teaches its reader that the gate is noise.
    stanzas = BLOCKS.split("\n      <div class=\"grades\">")
    samples = [BLOCKS.split("<div class=\"band\">")[0],
               '      <div class="band"><div><span class="k">Label</span>'
               '<div class="v">41<span class="u">%</span></div></div>'
               '<div><span class="k">Label</span><div class="v">312</div></div></div>',
               '      <div class="grades">\n'
               '        <div class="gr g4"><i></i><p class="gn">The row\'s subject</p>\n'
               '          <p class="gq">and what is true of it</p></div>\n'
               '        <div class="gr g2"><i></i><p class="gn">A second row</p></div>\n'
               '      </div>',
               '      <div class="swap">\n'
               '        <div class="no"><p class="listhead">One option</p>\n'
               '          <ul><li>what it costs</li></ul></div>\n'
               '        <div class="yes"><p class="listhead">The other</p>\n'
               '          <ul><li>what it costs</li></ul></div>\n'
               '      </div>']
    del stanzas
    for i in range(args.pages):
        n = i + 3
        block = samples[i % len(samples)]
        out.append(f'''<section class="page" id="p{n}">
  {g}
  <div class="body split">
    <div class="lede">
      <p class="eyebrow"><svg class="ic" aria-hidden="true"><use href="#i-radar"/></svg>Part A &#183; This page's label</p>
      <h2 class="t">A title naming its subject and carrying a fact</h2>
      <p class="sup">The support line, which is one sentence and not a summary.</p>
    </div>
    <div class="fill">
{block}
    </div>
    <div class="fill">
      <div class="fig"><!-- draw the thing the content IS: a flow, a timeline,
        a table, a bridge. Shapes carry semantics; dashed means not built. -->
      <div class="cap"><span class="n">Figure {i + 1}</span> A title stating a
      conclusion <span class="srcline">Where this came from</span></div></div>
    </div>
  </div>
  {foot(n, total)}
</section>''')

    out.append(f'''<section class="page closing" id="close">
  {g}
  <div class="body cover-grid">
    <div class="typeblock">
      <p class="wordmark">LUMI</p>
      <h1>What the reader carries out</h1>
      <p class="sub">The argument in one paragraph.</p>
    </div>
    <div class="attrs">
      <div><span class="k">Label</span><span class="v">value</span></div>
    </div>
    <p class="colophon">Built with lumi-style VERSION.</p>
  </div>
  {foot(total, total)}
</section>''')

    out.append("</body></html>")
    print("\n".join(out))
    print(f"<!-- scaffold: {total} pages. Every icon reference resolves, every "
          f"block carries its contract, and the opener carries its class. "
          f"check_design.py's D19 holds all three. -->", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
