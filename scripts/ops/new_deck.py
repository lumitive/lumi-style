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

# ONE ICON PER PAGE, ROTATED — not because rotation is right, but because the
# same icon on every page is demonstrably wrong and a scaffold teaches by what
# it does. Every content page carried `#i-radar` until 0.1.547; the conformance
# deck that inherited it reached the reader with one icon on seven of eight
# pages and twelve of the fifteen sprite symbols dead, while the two agents
# that varied theirs matched the accepted reference. A default nobody pushes
# back on IS the output. The list is the sprite the fixture ships, minus
# `i-shield` (the footer's, one meaning) and `i-list-checks` (the agenda's).
PAGE_ICONS = ("i-layers", "i-gauge", "i-scale", "i-route", "i-target",
              "i-git-branch", "i-split", "i-calendar", "i-funnel", "i-bell",
              "i-radar", "i-ban", "i-book-open")

ROOT = next(p for p in pathlib.Path(__file__).resolve().parents
            if p.name == "scripts").parent
# READ LAZILY, inside preamble(). build_fixtures.py imports this module for
# brand_globe(), and this module reads the artifact build_fixtures GENERATES —
# so a module-scope read here would stop the fixture generator from importing
# whenever the fixture is absent or stale, which is exactly when it is run.
FIXTURE = ROOT / "fixtures" / "deck-pass.en.html"


def _field(key: str, rest: str) -> str:
    """Pull `key: ...` out of an outline's pipe-separated analysis line."""
    m = re.search(rf"{key}\s*:\s*([^|]+)", rest, re.I)
    return m.group(1).strip() if m else ""


def outline_sections(path: pathlib.Path | None):
    """-> [{title, move, finding, implication}] from the analysis beat, or [].

    The beat produced a plan and nothing carried it into the markup. Measured on
    a shipped deck: fourteen sections declared a move, a finding and an
    implication, and not one of those titles still described a page -- the
    analysis ran and composition threw it away. Reading it here is what makes
    the beat an INPUT instead of a document.
    """
    if path is None:
        return []
    sys.path.insert(0, str(ROOT / "scripts" / "check"))
    import check_outline
    _meta, groups, _om, analyses = check_outline.parse(
        path.read_text(encoding="utf-8"))
    by_title = {}
    for a in analyses:
        t = a.get("after_title")
        if not t:
            continue
        rest = str(a.get("rest", ""))
        by_title[t] = {"move": str(a.get("move", "")),
                       "finding": _field("finding", rest),
                       "implication": _field("implication", rest),
                       "framework": _field("framework", rest)}
    out = []
    for _h, titles in groups:
        for t in titles:
            d = by_title.get(t, {})
            out.append({"title": t, "move": d.get("move", ""),
                        "finding": d.get("finding", ""),
                        "implication": d.get("implication", ""),
                        "framework": d.get("framework", "")})
    return out


def framework_for(move: str) -> str:
    """-> a one-line hint naming the frameworks that draw this move, and the
    misuse each is known for.

    `assets/frameworks.json` has been validated by a guard and read by no
    runtime since it shipped: an author asking "which framework does this page
    want" got the same answer as before the dictionary existed. This is the
    question -> framework -> shape chain of analysis-rules.md AR-4, executed.
    It NAMES the candidates and their misuse; it does not choose, because the
    relation lives in the content and this file cannot see it.
    """
    if not move:
        return ""
    try:
        d = json.loads((ROOT / "assets" / "frameworks.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ""
    entries = d.get("frameworks", d)
    hits = [(k, v) for k, v in entries.items()
            if isinstance(v, dict) and v.get("move") == move]
    if not hits:
        return ""
    parts = [f"{k} — misuse: {v.get('misuse', '')[:110]}" for k, v in hits[:3]]
    return f"move={move}; frameworks that draw it: " + " | ".join(parts)


def shape_for(move: str, framework: str = "") -> tuple[str, str]:
    """-> (shape id or "", comment). The question -> framework -> shape chain
    (analysis-rules AR-4, design-rules §4.0) executed to its last link.

    Until 0.1.533 the scaffold named the candidate frameworks in a comment and
    left the figure empty, on the reasoning that the relation lives in the
    content and a prescribed shape would repeat the mis-curation. Measured
    across five shipped deliverables the library's use count was zero: a
    comment is not a path. So a page whose outline declares a move now
    ARRIVES with the first shape of the first framework that draws it — or of
    the framework the outline names — in the figure slot, and the comment
    lists the alternatives. The choice stays the author's; the default is no
    longer "nothing". A framework drawn natively (funnel, waterfall,
    market-sizing) names no shape and the slot stays a prompt.
    """
    if not move:
        return "", ""
    try:
        d = json.loads((ROOT / "assets" / "frameworks.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return "", ""
    entries = d.get("frameworks", d)
    hits = [(k, v) for k, v in entries.items()
            if isinstance(v, dict) and v.get("move") == move]
    if framework:
        named = [(k, v) for k, v in entries.items() if k == framework]
        hits = named + [h for h in hits if h[0] != framework]
    for k, v in hits:
        shapes = [x for x in (v.get("shapes") or []) if (ROOT / "assets" / "shapes" / f"{x}.svg").exists()]
        if shapes:
            others = ", ".join(shapes[1:4])
            return shapes[0], (f"{k} drawn with shape {shapes[0]}"
                               + (f"; alternatives: {others}" if others else "")
                               + (" — or draw the framework natively" if v.get("drawn") else ""))
    return "", ""


def shape_figure(shape: str, label_a: str, label_b: str) -> str:
    return f'''<svg viewBox="0 0 640 300" role="img"
        aria-label="{label_a}: replace the labels, keep or swap the shape">
        <use href="#shape-{shape}" x="0" y="0" width="640" height="239"/>
        <text x="16" y="278" class="flbl" style="fill:var(--tx2)">{label_a}</text>
        <text x="624" y="278" text-anchor="end" class="flbl" style="fill:var(--tx2)">{label_b}</text>
      </svg>'''


def wordmark(override: str | None = None) -> str:
    """-> the cover/closing wordmark: the product this document is for.

    `brands/registry.json` has carried a per-brand `wordmark` since the registry
    was written and NOTHING read it — both generators hard-coded "LUMI Style",
    which is the design system's own name. It reached a product business plan,
    where the cover named the stylesheet rather than the company (owner review,
    0.1.521). The registry is the source; `--wordmark` covers a subject that is
    not a registered brand.
    """
    if override:
        return override
    reg = json.loads((ROOT / "brands" / "registry.json").read_text(encoding="utf-8"))
    return reg["brands"][reg["default"]]["wordmark"]
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


def open_trace(genre, geometry, storyline, outline):
    """-> a trace id, or None when no trace could be opened (and why, on
    stderr). The scaffold is where a build begins, so the record opens here
    and the build clock starts here; check_deliverable.py stops the clock and
    closes the record through the id the body carries. Fourteen consecutive
    builds of one deck left no trace while the ledger counted zero abandoned
    builds — the record was optional, so it was omitted.

    A storyline is required by the schema; without one the trace is not
    opened and the scaffold says so, because a trace is a declaration and
    a guessed declaration is the thing the schema exists to refuse.
    """
    if not storyline:
        print("<!-- no trace opened: a trace declares its storyline, and none "
              "was given (--storyline) -->", file=sys.stderr)
        return None
    import subprocess
    tool = pathlib.Path(__file__).with_name("trace.py")
    stage = deliverable_registry.STAGE_OF.get(geometry, "16x9")
    argv = [sys.executable, str(tool), "open", "--genre", genre,
            "--storyline", storyline, "--entry-path", "A" if outline else "B",
            "--geometry", stage]
    if outline is not None:
        argv += ["--recipe", str(outline)]
    opened = subprocess.run(argv, capture_output=True, text=True)
    if opened.returncode != 0:
        print(f"<!-- no trace opened: {opened.stderr.strip()[:200]} -->",
              file=sys.stderr)
        return None
    trace_id = opened.stdout.strip()
    subprocess.run([sys.executable, str(tool), "phase", "start", "build",
                    "--id", trace_id], capture_output=True, text=True)
    return trace_id


def preamble(genre, geometry, storyline=None, trace_id=None,
             lang="en", lang_asked=False):
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
    # The fixture is `deck-pass.en.html`, so the head it hands over says
    # `lang="en"` whatever the deliverable is about to be written in. That was
    # invisible while nothing could say otherwise, and it meant a Chinese build
    # started from an English declaration and had to edit it by hand — which is
    # exactly the edit that walked a 2026-08 build past M12 (FM-18).
    head = re.sub(r'(<html[^>]*\blang\s*=\s*)["\'][\w-]+["\']',
                  lambda m: f'{m.group(1)}"{lang}"', head, count=1)
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
            # ASKED, never inferred, and recorded only when a person actually
            # asked. American English is the default and carries no record;
            # any other language without one fails M16. The evidence for
            # "the user asked" cannot live in the agent's memory of the
            # conversation, because that is precisely what FM-18 is about.
            + (f' data-lang-asked="{lang}"' if lang_asked else "")
            # DECLARED, never inferred. D26 reads this to say which sections
            # the document neither covers nor declares; guessing a storyline
            # from the headings would make the report a measurement of the
            # guess.
            + (f' data-storyline="{storyline}"' if storyline else "")
            # The build's own record, so the check step closes the trace the
            # scaffold opened without anyone retyping an id.
            + (f' data-trace="{trace_id}"' if trace_id else "")
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
                   " IF THE DRAWING SCALES NUMBERS, name its axes with the"
                   " shipped classes. Put class=axname-x on a text node below"
                   " the baseline, running level, and class=axname-y on one to"
                   " the LEFT of the vertical axis; tokens/ turns that one"
                   " upright to read bottom to top. Neither may lie across the"
                   " marks. figure_axis_overlap and figure_axis_orientation gate"
                   " both. A name is a ROLE: without the class a checker cannot"
                   " tell an axis name from a data label on its own mark, and"
                   " three conformance decks printed one across the plot. -->")

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

    # The stat tile (0.1.521). The number first and the sentence under it -- the
    # order design-rules.md 7 fixes -- and the row's ONE key figure in accent,
    # the rest in ink. Three across is the shape the accepted deck used.
    '      <div class="stats">\n'
    '        <div class="stat"><p class="sv acc">1 copy</p>\n'
    '          <p class="sn">what the reader installs, and what it '
    'brings with it.</p></div>\n'
    '        <div class="stat"><p class="sv">12 platforms</p>\n'
    '          <p class="sn">the count, and what the count is of.</p></div>\n'
    '        <div class="stat"><p class="sv">190 lessons</p>\n'
    '          <p class="sn">a third figure, glossed the same way.</p></div>\n'
    '      </div>',

    # The field — brand.md's signature device, "many small marks, varying in
    # intensity, ordered by the thing they measure" — shipped in the tokens at
    # 0.1.379 and was used by nothing the audit measured. It rides in the
    # rotation so an author meets it; its rule rides with it: ONE MARK PER
    # DATUM. With no set behind it, delete the block — a shimmer with no data
    # is the decoration the brand file names as dishonest.
    '      <p class="listhead">A set with a shape: one mark per item, '
    'ordered by what it measures</p>\n'
    '      <!-- .field: one <i> per real datum, data-w 1..5 from the datum, '
    'order from the data. No set? delete this block. -->\n'
    '      <div class="field tall">'
    + "".join(f'<i data-w="{w}"></i>' for w in (1, 1, 2, 2, 3, 3, 3, 4, 4, 5, 5, 4, 3, 2, 2, 1))
    + '</div>',
]


# THE PART OPENER'S SUBJECT MARK, from the set vendored for it. design-rules
# §3 permits exactly one — a filled silhouette carrying no text of its own,
# reversed out of the field — and §6 vendored the set it comes from
# (`assets/icons/koboyo/`, 36 of them, "for part-opener subject marks").
# `tokens/` has styled `.openmark` since the
# opener composition landed. Neither this scaffold nor any fixture drew one
# until 0.1.547, so three conformance decks reached the reader with five bare
# openers between them and `opener_subject_mark` (0.1.546) failed all of them.
#
# One per part, never the same twice: the mark says what the part is about, so
# two identical ones say the two parts are the same thing. WHICH silhouette
# fits WHICH part is the author's choice — these are placeholders, and the
# emitted comment says so.
OPENER_MARKS = ("chart", "globe", "key", "rocket", "clipboard", "scale",
                "shield", "cpu")


def opener_mark(index: int) -> str:
    """-> the `.openmark` block for part `index`, or "" if the set is missing.

    Reads the vendored file rather than restating its geometry: a path copied
    into this script is a second copy of an asset, and `assets/icons/koboyo/`
    is the authority. A missing set yields no mark rather than a broken one —
    the gate then says so, which beats this script inventing a silhouette.
    """
    root = ROOT / "assets" / "icons" / "koboyo"
    names = [n for n in OPENER_MARKS if (root / f"{n}.svg").exists()]
    if not names:
        return ""
    name = names[index % len(names)]
    svg = (root / f"{name}.svg").read_text(encoding="utf-8").strip()
    note = ("<!-- design-rules \u00a73: ONE filled silhouette, and it is the "
            f"part's subject.\n           `{name}` is a placeholder from "
            "assets/icons/koboyo/ (36 to choose from);\n           two openers "
            "may not carry the same mark. -->")
    return f'<div class="openmark">{svg}</div>\n      {note}'


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
    ap.add_argument("--outline", type=pathlib.Path,
                    help="the analysis beat's outline. Each content page is "
                         "emitted carrying its planned title and implication "
                         "and declaring its analytical move, so the beat is an "
                         "INPUT rather than a document written and then "
                         "forgotten (analysis-rules.md AR-3).")
    ap.add_argument("--wordmark",
                    help="the cover/closing wordmark. Defaults to the default "
                         "brand's `wordmark` in brands/registry.json; pass this "
                         "for a subject that is not a registered brand.")
    ap.add_argument("--out", type=pathlib.Path,
                    help="write the scaffold here instead of to stdout. "
                         "Stdout stays the default; this exists so a caller "
                         "does not have to capture it")
    ap.add_argument("--lang", default="en",
                    help="the deliverable's output language, as a BCP-47 code "
                         "for <html lang>. Default: en. American English is "
                         "LUMI's default output language (writing-rules "
                         "section 0) and another language is asked for, never "
                         "inferred from the source material, the venue or the "
                         "audience.")
    ap.add_argument("--lang-asked", action="store_true",
                    help="the user ASKED for --lang. Writes data-lang-asked on "
                         "<body>, which is what M16 reads. Required for any "
                         "language but English: without it the deck fails "
                         "check_prose. Do not pass it because the input "
                         "document or the conversation was in that language "
                         "- neither is an instruction (FM-18).")
    ap.add_argument("--no-trace", action="store_true",
                    help="do not open a build trace (fixtures, tests, dry runs). "
                         "A real build keeps the default: the record opens "
                         "here, and check_deliverable.py closes it.")
    ap.add_argument("--pages", type=int, default=None,
                    help="content pages, not counting cover, agenda, the part "
                         "openers and the closing. Default: the number of "
                         "sections in --outline, or 6 with no outline. Pass it "
                         "to scaffold a subset on purpose")
    ap.add_argument("--parts", default="A,B",
                    help="part letters, comma separated. Two is the default: "
                         "one part is not a part, it is a document.")
    args = ap.parse_args(argv)

    src = FIXTURE.read_text(encoding="utf-8")
    g = ground(src)
    parts = [x.strip() for x in args.parts.split(",") if x.strip()]
    mark = wordmark(args.wordmark)
    plan = outline_sections(args.outline)
    # THE OUTLINE KNOWS HOW MANY PAGES THERE ARE. `--pages` defaulted to 6
    # whatever the outline said, so a ten-title plan silently emitted six
    # content pages and four findings had nowhere to go -- silently, because the
    # scaffold is valid either way and no check compares a scaffold to a plan.
    # An explicit `--pages` still wins: an author may deliberately scaffold a
    # subset.
    if args.outline and plan and args.pages is None:
        args.pages = len(plan)
        print(f"note  --pages {args.pages}, from the {len(plan)} section(s) in "
              f"{args.outline.name}", file=sys.stderr)
    if args.pages is None:
        args.pages = 6
    # cover, agenda, closing, + openers; training appends its reference page.
    apparatus = 1 if args.genre == "training" else 0
    total = args.pages + 3 + len(parts) + apparatus
    trace_id = None if args.no_trace else open_trace(
        args.genre, args.geometry, args.storyline, args.outline)
    out = [preamble(args.genre, args.geometry, args.storyline, trace_id,
                    args.lang, args.lang_asked)]

    # The cover title carries TWO INKS: the claim in ink, the noun the deck is
    # about as lime on its own dark chip (`.subj`) — the same green the part
    # openers carry at page scale, so the title marks what the page is FOR in
    # the deck's one event colour rather than decorating it.
    out.append(f'''<section class="page cover" id="cover">
  {g}
  <div class="body cover-grid">
    <div class="typeblock">
      <p class="wordmark">{mark}</p>
      <h1>A title that states the argument about its
      <span class="subj">subject</span></h1>
      <p class="sub">One sentence saying what this is.</p>
    </div>
    <!-- The brand mark. Keep it: with no explicit instruction from the
         owner this is the mark, and D40 fails a deck that carries
         something else without `<body data-brand-mark="…">` naming the
         replacement that was asked for. -->
    <div class="markcell" data-globe>{brand_globe()}</div>
    <div class="attrs">
      <div><span class="k">Label</span><span class="v">value</span></div>
      <div><span class="k">Label</span><span class="v">value</span></div>
    </div>
  </div>
  {foot(1, total)}
</section>''')

    # THE AGENDA IS THE LAUNCH SEQUENCE (0.1.519, owner review: the grades
    # agenda read as quiet apparatus). One row per part: a numbered chip, the
    # part's claim at title weight — QUOTE the opener's claim, D27 holds the
    # mirror — and a quiet run line. The storyline checklist seeds the run
    # lines, chunked across parts: a checklist applied at the end, never a
    # template to start from, exactly as the registry's comment demands.
    sections = (deliverable_registry.TYPICAL_SECTIONS.get(args.storyline, ())
                if args.storyline else ())
    chunks: list[list[str]] = [[] for _ in parts]
    for i, sec in enumerate(sections):
        chunks[i * len(parts) // max(1, len(sections))].append(sec)
    rows = ""
    for i, q in enumerate(parts):
        run = (" &#183; ".join(chunks[i]) if sections
               else "which pages, and what they cover")
        rows += (
            f'      <div class="lrow">\n'
            f'        <div class="ln">{i + 1:02d}</div>\n'
            f'        <div><p class="gn">What Part {q} argues, its key phrase '
            f'<span class="hl">set in the light</span></p>\n'
            f'          <p class="gq">{run}</p></div>\n'
            f'      </div>\n')
    if args.storyline and not sections:
        # A storyline with no checklist SAYS SO. Emitting nothing here is
        # how `proposal` shipped for eight releases looking like a
        # storyline whose sections were all present.
        rows += (f'      <p class="gq">no typical-section checklist exists '
                 f'for {args.storyline}; completeness is yours to establish '
                 f'at the storyline review</p>\n')
    out.append(f'''<section class="page" id="agenda">
  {g}
  <div class="body stack no-lede">
    <div class="fill">
      <div class="launch">
{rows}      </div>
    </div>
  </div>
  {foot(2, total)}
</section>''')

    n = 3
    # The figure ordinal is the FIGURE's, not the page's. It was `n - 2` until
    # 0.1.521, which counted PAGES: every part opener consumed a number no
    # drawing ever carried, so a two-part scaffold emitted Figure 3, 4, 8, 9,
    # 11 ... and the tracked fixture shipped six holes. Both accepted
    # deliverables reproduced the pattern from this generator -- one numbered
    # two drawings `Figure 3`, the other ran 2-8 then 12-14 then 9-11. A reader
    # says "go back to figure four" out loud, so a hole makes the reference
    # wrong and a repeat makes it ambiguous; check_design.py D30 reads the
    # sequence back.
    figno = 1
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
      {opener_mark(pi)}
    </div>
  </div>
  {foot(n, total)}
</section>''')
        n += 1
        count = per if pi < len(parts) - 1 else args.pages - per * (len(parts) - 1)
        for i in range(count):
            block = SAMPLES[(pi * per + i) % len(SAMPLES)]
            figure = SHAPE_FIGURE if (pi == 0 and i == 0) else FIG_PLACEHOLDER
            # The beat's output, carried in. Where an outline exists, the page
            # ARRIVES holding the finding it was planned to state and the
            # implication it was planned to leave, and declares the move that
            # produced them. Without one, the slots stay as prompts.
            sec = plan[len(plan) and (pi * per + i) % len(plan)] if plan else {}
            title = sec.get("title") or "A title naming its subject and carrying a fact"
            take = sec.get("implication") or "The line the reader carries off this page."
            move = sec.get("move", "")
            hint = framework_for(move)
            adecl = f' data-analysis="{move}"' if move else ""
            shape, shape_note = shape_for(move, sec.get("framework", ""))
            if shape:
                figure = shape_figure(shape, "what this end names", "and what it leads to")
                hint = (hint + "; " if hint else "") + shape_note
            fignote = (f"\n      <!-- {hint} -->" if hint else "")
            out.append(f'''<section class="page" id="p{n}"{adecl}>
  {g}
  <div class="body split">
    <div class="lede">
      <p class="eyebrow"><svg class="ic" aria-hidden="true"><use href="#{PAGE_ICONS[(n - 1) % len(PAGE_ICONS)]}"/></svg>Part {part} &#183; this page&#8217;s label</p>
      <!-- The icon is a PLACEHOLDER rotated so no two pages start alike.
           design-rules §6: within one document an icon means exactly one
           thing, so replace it with this page's own subject.
           `embed_icons.py --search <term>` finds one among 2007. -->
      <h2 class="t">{title}</h2>
      <p class="sup">The support line, one sentence and not a summary.</p>
    </div>
    <div class="fill">
{block}
    </div>
    <div class="fill">{fignote}
      <div class="fig">{figure}
      <div class="cap"><span class="n">Figure {figno}</span> A title stating a
      conclusion</div></div>
      <!-- design-rules §4 rule 8: the caption holds the number and the name and
           NOTHING ELSE. The source line is the drawing's own last text node
           (rule 17) — see the `<text class="fnote">` at the foot of the figure
           above. Run together in one caption the two read as one sentence, and
           the line break lands in the source so the name never appears to
           wrap. -->
      <p class="take">{take}</p>
    </div>
  </div>
  {foot(n, total)}
</section>''')
            n += 1
            figno += 1

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
      <p class="wordmark">{mark}</p>
      <h2>What the reader carries out about its
      <span class="subj">subject</span></h2>
      <p class="sub">The argument in one paragraph.</p>
    </div>
    <!-- The brand mark. Keep it: with no explicit instruction from the
         owner this is the mark, and D40 fails a deck that carries
         something else without `<body data-brand-mark="…">` naming the
         replacement that was asked for. -->
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
    doc = embed_shapes.apply("\n".join(out))
    # STDOUT REMAINS THE DEFAULT, because that is what every existing caller
    # and every recorded recipe uses. `--out` exists because "this script
    # prints to stdout, redirect it" was the single most-repeated build trap on
    # record, and because a driver that has to capture stdout cannot record the
    # command through `debug_log run`, which writes stdout itself.
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(doc + "\n", encoding="utf-8")
        print(f"note  wrote {args.out}", file=sys.stderr)
    else:
        print(doc)
    print(f"<!-- scaffold: {total} pages, standard order. Every icon reference "
          f"resolves, every block carries its contract, and each opener carries "
          f"its class. check_design.py's D19 holds all three. -->", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
