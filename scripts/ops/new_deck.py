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
import deliverable_registry  # noqa: E402
import embed_font  # noqa: E402
import embed_globe  # noqa: E402
import embed_shapes  # noqa: E402

ROOT = next(p for p in pathlib.Path(__file__).resolve().parents
            if p.name == "scripts").parent
# READ LAZILY, inside preamble(). build_fixtures.py imports this module for
# brand_globe(), and this module reads the artifact build_fixtures GENERATES —
# so a module-scope read here would stop the fixture generator from importing
# whenever the fixture is absent or stale, which is exactly when it is run.
FIXTURE = ROOT / "fixtures" / "deck-pass.en.html"
BRAND_GLOBE = ROOT / "assets" / "brand" / "lumivate" / "globe-field.svg"


def brand_globe():
    """The LUMIVATE field globe, prepared for embedding in a document.

    The default cover/closing mark (owner directive, 0.1.442 review: a
    deliverable shipped a fresh anonymous render instead of the brand).

    THE VENDORED FILE IS THE STANDALONE PUBLISHED FORM, so it carries its own
    `<style>` — a copy of the document palette plus a copy of both region
    palettes. Inline SVG shares the host document's style scope, so embedding
    that block redefines the host's tokens; the whole element comes out, and
    the host paints the mark from `tokens/`, where every rule in it also
    lives.

    0.1.447 first stripped only the palette SELECTORS and kept the rest, on
    the reading that the component's rules existed nowhere else. They do:
    `.gl-*` and `.trade` are `tokens/region-palette.css` and
    `tokens/region-palette-trade.css`, both generated and both `--check`ed.
    What had actually gone wrong was narrower — the trade palette was the one
    generated file the fixture preamble did not include, so the mark's eight
    blocs fell back to the UA default. Keeping a copy inside the SVG cured the
    symptom and froze a generated file inside a LOCKED asset where no
    regeneration check can see it drift. The preamble includes both palettes
    now, which is the same answer figure 9's black rectangles got in 0.1.391.

    The scaffold therefore owes the mark its palette: `test_new_deck.py` holds
    that every `--rg-*` the embedded globe references is defined by the CSS
    the preamble ships, which is the machine form of "the mark paints".
    """
    src = BRAND_GLOBE.read_text(encoding="utf-8")
    blocks = re.findall(r"<style\b[^>]*>", src)
    if len(blocks) != 1:
        raise SystemExit(f"FAIL  {BRAND_GLOBE.name} carries {len(blocks)} "
                         f"<style> blocks; this prepares exactly one, and a "
                         f"second would ship the palette it exists to remove")
    out = re.sub(r"<style\b[^>]*>.*?</style>", "", src, count=1, flags=re.S)
    if "<style" in out:
        raise SystemExit(f"FAIL  {BRAND_GLOBE.name} still carries a <style> "
                         f"block after stripping")
    return out

# The genres this scaffold can EMIT — a documented subset of the package's
# vocabulary, not a second copy of it. `marketing` has no skeleton of its
# own (storyline-templates.md folds it into Template 1 with sales), so it
# is absent here and present everywhere the vocabulary is just a label.
# check_repo's `genre vocabulary` guard holds this to the registry's names.
SCAFFOLDED = ("sales", "consulting", "internal", "training")
GENRES = SCAFFOLDED



def genre_card(genre: str) -> str:
    """The genre-conditional contract, as a comment the author reads at write
    time instead of discovering at check time.

    Ten rounds of one build were autopsied and two or three of them were
    exactly this: constraints that existed, enforced by checkers, knowable
    before the first word — the dash ban for the genre, the title-frame
    taxonomy, the colophon's provenance vocabulary — and discoverable only by
    failing them, because each lived inside the checker that fires on it.
    Every value below is IMPORTED from its checker. A card that retyped them
    would be the twenty-seventh copy-drift fix waiting to happen.
    """
    import check_design
    import check_prose
    dashes = ("em/en dashes are BANNED in this genre (M9 gates at 0; only a "
              "digit-digit range like 2026-08 is exempt — C1-C8 is not)"
              if genre in check_prose.DASH_BANNED else
              "em dashes allowed (internal analysis exemption)")
    return f"""<!-- THE CONTRACT FOR genre={genre} — read before writing, not after failing.
  words   · {dashes}
          · quoted rule-data (banned-phrase examples, decoy markup) belongs in
            FIGURE INK: text inside <svg> is invisible to M4/M9 by design;
            the same phrase in HTML prose fails the run
  titles  · M11 counts syntactic frames {check_prose.TITLE_FRAMES} — no one
            frame may carry more than 60% of the titles
  colophon· D6 accepts these provenance words: {", ".join(check_design.D6_PROVENANCE)}
  roles   · every page role is defined by the pages this scaffold emits —
            compose FROM them (the closing title is the closing's h2, not a
            second cover h1); a role rewritten from memory drops out of the
            audit instead of failing it
  checks  · one command runs the whole stack and ends in one block:
            python3 scripts/ops/check_deliverable.py <file>
            read that block whole; fix everything it names in one pass -->"""


def preamble(genre, geometry, storyline=None):
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
            f'data-geometry="{geometry}" data-genre="{genre}"'
            # DECLARED, never inferred. D26 reads this to say which sections
            # the document neither covers nor declares; guessing a storyline
            # from the headings would make the report a measurement of the
            # guess.
            + (f' data-storyline="{storyline}"' if storyline else "")
            + '>\n' + genre_card(genre) + '\n' + sprite)


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


# ONE OF EVERY BLOCK PATTERN THAT CARRIES A GATED CONTRACT, with the markup the
# FIXTURE uses — not the markup a class name suggests. `.swap` is the worked
# example: its rendering is `grid-template-columns: 1fr 34px 1fr` and it takes
# THREE children — a before, an arrow, an after. Written with two, the after
# lands in the 34px arrow column and wraps one word per line. That shipped, and
# its content was trimmed three times before anyone measured the box.
#
# `.card` and `.vow` joined at 0.1.450, from the conformance board's first
# refresh in fifteen releases: an agent given this scaffold reached for `.card`
# — named in SKILL.md's prose, holding a contract D19 GATES on — and wrote
# twelve of them without `.ledname`, because prose is what it had. That is this
# file's own opening paragraph happening to this file. Every entry in
# check_design's BLOCK_CONTRACTS now has a worked example here; when a contract
# is added there, its example belongs here in the same release.
ARROW = '<span class="arw">&#8594;</span>'


# ONE worked example of the shape library's mechanics, on the first content
# page. The scaffold used to hand an author an empty `.fig` with a comment in
# it, and three shipped deliverables referenced NONE of the 206 units — the
# rebuild spec's D1 calls that guaranteed rather than accidental, because an
# agent following the entry points had no path to the library.
#
# It teaches the MECHANICS, not the choice. Which shape a page wants is decided
# by the RELATION in its content (design-rules.md §4.1) and this file cannot
# know that; the library was mis-curated twice by reading names as
# classifications, so a scaffold that prescribed a shape would be the same
# mistake with a friendlier face. What it does show is the part that has no
# judgement in it and bites every time:
#
#   · EVERY unit in the library has a non-zero viewBox origin — all 206, not
#     some — so a bare `<use href="#shape-…">` renders shifted off frame. The
#     x/y/width/height below are not decoration.
#   · a `fill=` attribute on `<text>` loses to CSS, so a label written that way
#     silently takes the stylesheet's colour. `style="fill:"` is the form.
#   · the sprite is BUILT at emit time by embed_shapes.apply(), never pasted.
SCAFFOLD_SHAPE = "p009-arrow-3d-01"          # relation: order · process
SHAPE_FIGURE = f'''<svg viewBox="0 0 640 300" role="img"
        aria-label="A worked example: replace the shape and both labels">
        <use href="#shape-{SCAFFOLD_SHAPE}" x="0" y="0" width="640" height="239"/>
        <text x="16" y="278" class="flbl" style="fill:var(--tx2)">the step this end names</text>
        <text x="624" y="278" text-anchor="end" class="flbl" style="fill:var(--tx2)">and the step it leads to</text>
      </svg>'''
FIG_PLACEHOLDER = ("<!-- draw what the content IS: a flow, a timeline, a bridge,"
                   " a table. Shapes carry semantics; dashed means not built."
                   " embed_shapes.py --list names every unit the library ships."
                   " -->")

SAMPLES = [
    '      <p class="listhead">A heading over a block</p>\n'
    # `.gd` is the standard callout, NOT the tier-1 one: D3 budgets `.key` and
    # `.red`, and this line said "tier-one" while emitting neither, which
    # taught the wrong class for the rule it named.
    '      <p class="gd">A marked aside, one size everywhere.</p>\n'
    '      <p class="key">The tier-1 callout: the aside that changes a '
    'decision. One per page, and no more than a third of the pages.</p>\n'
    '      <ul><li>A bulleted list is a small set of criteria that must all '
    'hold.</li>\n'
    '      <li>A numbered list is a sequence someone performs in order.</li></ul>',

    '      <div class="card"><p class="ledname">The card&#8217;s subject</p>\n'
    '        <dl><dt>The question it answers</dt>\n'
    '          <dd>and the answer, in a sentence.</dd></dl>\n'
    '        <p class="verdict">The one line to carry away. Page 00.</p></div>',

    '      <div class="vows">\n'
    '        <div class="vow"><span class="vn">01</span>'
    '<p class="vt">The commitment, named</p>\n'
    '          <p class="vw">What it means in practice, and what it '
    'rules out.</p></div>\n'
    '        <div class="vow"><span class="vn">02</span>'
    '<p class="vt">A second commitment</p>\n'
    '          <p class="vw">Its consequence, stated the same way.</p></div>\n'
    '      </div>',

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
    # The composition vocabulary is IMPORTED, not retyped. It used to be a
    # literal pair here while the trace declared (16x9, a4, laptop) and
    # inspect_layout declared five viewports — three lists for one word, with
    # no guard between any pair.
    ap.add_argument("--geometry", choices=deliverable_registry.COMPOSITIONS,
                    default="landscape")
    ap.add_argument("--storyline", choices=deliverable_registry.STORYLINES,
                    help="seed the agenda from this storyline's typical "
                         "sections. A CHECKLIST, never a template: the rows "
                         "are furniture to replace, and a storyline with no "
                         "checklist says so rather than emitting nothing.")
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
    out = [preamble(args.genre, args.geometry, args.storyline)]

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
    # A storyline seeds the agenda with the sections it typically carries — as
    # FURNITURE TO REPLACE, which is what everything else the scaffold emits
    # is. The registry's own comment is the constraint: this is a checklist
    # applied at the end, never a template to start from, so the rows are
    # marked with the storyline they came from and carry no argument.
    if args.storyline:
        sections = deliverable_registry.TYPICAL_SECTIONS.get(args.storyline, ())
        if sections:
            rows += "".join(
                f'        <div class="gr g4"><i></i><p class="gn">{s}</p>\n'
                f'          <p class="gq">a title naming its subject and '
                f'carrying a fact</p></div>\n' for s in sections)
        else:
            # A storyline with no checklist SAYS SO. Emitting nothing here is
            # how `proposal` shipped for eight releases looking like a
            # storyline whose sections were all present.
            rows += (f'        <div class="gr g4"><i></i><p class="gn">'
                     f'no typical-section checklist exists for '
                     f'{args.storyline}</p>\n'
                     f'          <p class="gq">completeness is yours to '
                     f'establish at the storyline review</p></div>\n')
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
            figure = SHAPE_FIGURE if (pi == 0 and i == 0) else FIG_PLACEHOLDER
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
      <div class="fig">{figure}
      <div class="cap"><span class="n">Figure {n - 2}</span> A title stating a
      conclusion <span class="srcline">Where this came from</span></div></div>
    </div>
  </div>
  {foot(n, total)}
</section>''')
            n += 1

    if apparatus:
        # Template 4's arc ends on the pages a learner returns to. The page is
        # DECLARED apparatus (design-rules.md §3): D16's visual-share target
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
    <p class="colophon">Built with lumi-style VERSION &#183; source: WHERE THE
    NUMBERS CAME FROM.</p>
  </div>
  {foot(total, total)}
</section>''')

    # The runtime turns every [data-globe] — the cover and the closing. It
    # respects prefers-reduced-motion, and with JavaScript off the reader keeps
    # the exact static frame above. Rotation is part of the mark's contract
    # (owner directive): a still field globe is the fallback, not the design.
    out.append(embed_globe.build())
    out.append("</body></html>")
    # BUILT, never pasted — the same rule the globe runtime above follows.
    print(embed_shapes.apply("\n".join(out)))
    print(f"<!-- scaffold: {total} pages, standard order. Every icon reference "
          f"resolves, every block carries its contract, and each opener carries "
          f"its class. check_design.py's D19 holds all three. -->", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
