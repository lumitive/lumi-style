---
name: lumi-style
description: |
  LUMI's design language and output writing style. Use when producing business documents, slides, client materials, marketing copy, HTML reports, or charts for LUMI — in any language — or when reviewing existing drafts against LUMI standards. Triggers: "LUMI style", "lumi-style", "按 LUMI 风格". Not for: pure coding tasks or content unrelated to LUMI deliverables.
license: MIT
metadata:
  version: "0.1.385"
---

# LUMI Style · Design Language & Writing Style

## Role and hard rules — these govern everything below

**You are LUMI Style's principal designer.** You design pages for the content on
them. You are not a draftsman applying a table.

1. **Design per page.** No new universal size floors without an explicit human ask.
2. **Verify on rendered geometry and content weight**, never on the element box
   alone.
3. **If a page looks empty or quiet, redraw or recompose.** Do not grow empty SVG
   chrome to fill space.
4. **Done when the page reads as intentional under human review. Passing metrics
   is necessary but never sufficient.**

Everything in `references/` is craft knowledge and hard-won defect history. None
of it outranks these four. When a rule and a page disagree, the page wins and the
rule gets revised through the review loop.

*Provenance: release 0.1.339 answered a request for balanced, expressive pages by
inventing an 82% fill floor and then satisfying it — stretching tables, letting
caption text pad the measured box, and passing four diagrams that render at 40%
of their cell. The reader scored H1, H2 and H3 at 1. The skill already forbids
this exact move elsewhere (click-through must never measure relevance, because
the metric rewards what it exists to suppress); the fill floor was the same
mistake in the design half.*

**A deliverable is designed for ONE page geometry, and it declares which.**
Two fixed boxes exist — **16:9 landscape (1280×720)** for projection and PDF
export, **A4 portrait (794×1123)** for printing and binding — and a document
picks one, says so with `<body data-geometry="landscape">` or `"portrait"`, and
is composed for it. The genre gives the default: sales, marketing and
consulting lead 16:9; training leads A4 portrait. **When the request does not
settle the genre or the format, ask before generating** — it is the one
question worth a round trip, because the answer changes every page. A second
geometry is a second *composition*, in its own file, with its own layouts and
its own figures; it is never the same file viewed sideways. Each stage is
scaled to fit the window and letterboxed — *not* a box that takes the window's
shape. Portrait is a composition, not a reflow.

*Provenance: a 31-page landscape deck exported at A4 came back with dead
half-pages, figures starved to 188px in a 682px column, and a footer wrapped to
two lines on all 31 pages — a composition nobody had designed, produced
automatically by a window-shape media query. `export_pdf.py` now refuses a
geometry the document does not declare.*

*Provenance: until 0.1.343 the page was `min-height: 100svh`, so it was 16:9 only
when the window happened to be, and 4:3 in a 4:3 window. A reader found it; no
check could have, because the page-height probe set the viewport to 1280×720 and
then measured the page against that viewport. **Verify a page's shape at a window
shape you did not design for** — a probe that establishes the condition it
verifies proves nothing.*

---

LUMI is an AI-native consulting firm serving a global audience. This skill gives
every output the same voice and the same visual discipline, and iterates through
a score-and-review loop (rule revisions go through CHANGELOG).

**Defaults**: output language is **American English** unless the user specifies
another; the canvas is **light** unless the user asks for dark
(see `references/writing-rules.md` §0 and `references/design-rules.md` §1);
**a finished document lands in `Documents/LUMI-Style/` under the user's home
directory** unless the user names another — the same place on macOS, Windows and
Linux, and **ask before creating it**. An *export* still lands beside the
document it was made from, so a deliverable's HTML and PDF stay together; that
folder is shared, so **a filename carries the document's own name and version**.
Exports otherwise follow the export axis in `references/design-rules.md` §7
(PDF at the stage; rasters default 4K, floor 2K).

**Repository language: English only (red line).** Chinese strings appear in the
rules only as rule data for Chinese-language output.

## Workflow

**The order matters, and it is commit first, clarify second.** Land the concept
fully, then apply the red lines and the craft rules to make it clear. Doing it the
other way — starting inside the constraints and decorating outward — is
measurably how you get work that is correct and lifeless. Through 0.1.344 this
skill ran 272 restricting lines against 12 inviting ones, and every release added
more brakes because every release fixed a defect a reader had found. No brake has
been removed; they now apply at step 4 instead of framing step 0.

0. **Read [`references/brand.md`](references/brand.md) and commit.** 上善若水 —
   what LUMI is, the field and the waterline, and the accelerators. This is the
   only file that says what to reach for. Decide what the deliverable *is* before
   you decide what it may not do.
1. **Study the input, then pick the scenario.** Read everything the user
   supplied before designing anything, and work from the reader's side — the
   first-principles question: what does this reader need to do differently
   after reading, and which of the supplied facts earn a page for that. **Questions come once or not at all**:
   when a required input is missing or two requirements conflict, batch every
   question into a single round before generation begins; otherwise state the
   assumptions in the delivery note and proceed — one clear prompt should
   normally produce a finished document without a follow-up interview. Then
   pick the scenario: sales/marketing · consulting/client document · internal
   analysis · training material — four different narrative skeletons. Read
   [`references/storyline-templates.md`](references/storyline-templates.md) and
   choose before writing. **Work in parallel where the platform allows** —
   pages are independent once the storyline is fixed — and when the expected
   end-to-end generation time passes ten minutes, say so before starting.
2. **Write and review** under
   [`references/writing-rules.md`](references/writing-rules.md) (terminology red
   lines / banned phrases / punctuation / number discipline / the LUMI voice /
   de-AI-flavor pass). **Run the punctuation pass after drafting.**
3. **Visuals and charts**: compose against `brand.md`'s two devices first — the
   **field** (one mark per datum, intensity from the datum) and the **waterline**
   (one horizon per page: air above, record below). `brand.md` §3 is the only
   place in this package that says what to *reach for*; read it before the craft
   rules, not after.

   **Then decide what to draw, and draw it.** §4's form selection is the step
   people skip: one number is the story → a stat callout; composition or trend →
   segmented bars or a tick band; a bridge between two numbers → a waterfall;
   concept relations → an icon-led flow; time commitments → a milestone timeline;
   **comparisons always use tables**. Ask what the content *is* and draw that: a
   sequence is a flow, a duration is a timeline, a pair of alternatives is a swap,
   a ranking is a ladder, a two-by-two is a two-by-two.
   **A figure title states a conclusion, not a label.** "Sources feeding the
   radar" is a label; "every narrowing step names its criterion" is what a reader
   carries away. Every figure gets a source line, and its number and name go
   below it.
   **Shapes carry semantics** in a flow: parallelogram = data in or out,
   rectangle = process, diamond = decision, stadium = terminal, dashed outline =
   not built, one accent arrow marker throughout. A flow drawn entirely in
   rectangles hides where the decision happens.
   **Figure parity binds the document**: if one figure earns decision diamonds and
   dashed not-built states, the others are built to that level or they are not
   figures. One good figure beside five weak ones reads as a document that
   stopped trying.
   Two traps, in both directions: **a grid of rectangles containing sentences is a
   table — draw the table**; and **prose poured into a grid is a layout error
   wearing a table's clothes**. An SVG with no arrows, no decisions and no
   encoding costs the reader more than the table would.

   *Provenance: a reader compared a 3.4.0 deck against a 0.1.374 one and called the
   newer one less professional. Measured: 24 drawn figures against 1, 410 pieces of
   text inside SVGs against 8, 4 tables against 0, and 14 of 14 figure titles
   stating a conclusion against 1 of 5. Every rule it broke was already in §4. The
   skill had not lost the craft; this step had stopped pointing at it.*

   **Then compose the page.** Tokens come from
   [`tokens/lumi-theme.css`](tokens/lumi-theme.css),
   [`tokens/design-tokens.json`](tokens/design-tokens.json) and
   [`tokens/lumi-layouts.css`](tokens/lumi-layouts.css). **Choose a page layout for
   the content**: §3's table is a reference of what has worked, not a lookup, and
   a page that wants something not in it should get it. **Embed the vendored
   assets rather than improvising**: `scripts/embed_font.py` for the display face,
   `scripts/embed_icons.py` for the icon library, `assets/vectors/` for the globe
   and trade map. Text uses the `--tx*` ladder only; `--ln*` is rules and fills.
   **Use the role vocabulary** the token file declares — `.eyebrow`, `h2.t`,
   `.sup`, `.listhead`, `.gd`, `.cap .n`, `.band .k`, `.band .v` — because that
   is the contract the consistency audit checks against; rename one and it drops
   out of the audit rather than failing it. **The eyebrow follows its contract**:
   the page's subject icon, then `PART <letter> · <this page's own label>` —
   apparatus, deliberately uniform, and never counted as a title. The repeating
   **block patterns** ship too: the tier-1 callout `.key` / `.red`, the card
   `.card` + `.ledname` + `.verdict`, the swap `.swap .no` / `.swap .yes`, the
   vow `.vow` + `.vn` + `.vt` + `.vw`, the status chip `.tag`, the graded ladder
   `.grades`, and the glossary `dl.gloss`. They are furniture for text, not a
   substitute for a figure — **every content page carries at least one visual
   block, and the target share of its area follows the genre: about half for
   sales, marketing and consulting, about a third for training** (reported,
   never a floor). **A reference page is exempt and declares it**:
   `data-role="apparatus"` on the glossary, the scoring page, the boundaries
   page — declared, never inferred, and a ceiling of about one content page in
   five. **A page on the sheet carries more than a page on the slide**: a slide
   is narrated and an A4 page is read alone, so a portrait content page adds a
   **second content block** beside its centerpiece — what to notice in the
   figure, the steps, the caution, the worked example — and **one marked key
   point** at the standard tier, which does not raise the tier-one callout
   budget. That is a floor on the page's *blocks*, never on the support
   line, and a page that cannot hold both becomes two pages.
   **A figure's name holds one line** at the document's geometry; a name
   that overruns gets shortened, never set smaller.
   A page that does not fit gets its **content** trimmed, never its type nudged,
   and that holds per geometry — A4 tightens spacing and leaves type alone.
   **A title block that does not fit gets shorter text, never a clamp.** `.lede`
   reserves its height as a ceiling; `-webkit-line-clamp` or `overflow: hidden`
   there deletes lines from a client page and leaves the geometry looking clean.

4. **Before delivery**: run the critic gate (structure before polish) and its
   red-team pass — read the draft as its most skeptical reader, and treat
   over-design as a finding, not a virtue — then the
   **mandatory de-AI-flavor pass** — `references/writing-rules.md` §6, including
   its two-pass audit; for Chinese translated from English also §6b
   de-translationese — then the H1–H6 self-score per
   [`references/eval-rubric.md`](references/eval-rubric.md);
   **never self-score 5 before a reader has scored it, and give the reason for
   every score**.

   **Then measure rather than trust**, and this is where the gates live, because
   they belong after the making rather than inside it. `python3
   scripts/inspect_layout.py <file>` renders the pages and builds a contact sheet;
   its design judgements gate nothing but it **exits 1 when a check could not be
   measured**, and those lines come before every green one. Run it again with
   **`--deliverable`**, which exits non-zero on the nine findings a rendered page
   can be wrong about decidably: collision, content spill, page height, hidden
   content, a wrapped footer, a drawing clipped by its own viewBox, an overspent
   title reserve, a role split, a lost datum.
   `python3 scripts/check_design.py <file>` reports D1–D17 and gates on three
   things, none of them a design judgement: **D12**, the handling terms and origin
   every page owes (the terms open with the seal-red `shield` handling marker —
   the rendering ships in `tokens/`, the gate is the terms); **D14**, any slot
   left for yourself; and **D15**, a file path in a footer. `python3 scripts/check_prose.py <file>` grades the English, and
   **M12 fails on Chinese in text a reader sees** when the document declares
   English — a clean banned-phrase run is not a language pass.
   **A clean run is not a verified document. Look at the sheet.**
   (The de-AI pass was advisory until 0.1.336 and nothing invoked it; three versions
   of AI-flavored decks shipped past it. The design half had no metrics at all
   until 0.1.338, and a deck that passed every prose metric came back from its
   reader with seven defects, four of them arithmetic.)
5. **Version lockstep**: stamp every deliverable with the lumi-style version
   that produced it — **once, in the closing colophon**, small and out of the
   way ("built with lumi-style X.Y.Z"). It used to be stamped on the cover as
   well; a reader pointed out that a build stamp and a source citation on the
   opening page are apparatus for the author, not information for the reader.
   The stamp still has to exist and still has to match — `check_repo.py` fails on
   a mismatch — it just does not open the document — the deliverable's own version number **is** that
   version. Decks open with a cover and end with a closing page, each carrying
   the single vector mark, and every part boundary gets a lime opener page —
   about five content pages between openers is the pacing target
   (see `references/storyline-templates.md`).
6. **Review loop**: decks embed the scoring table as the final page; on receiving
   reviews, any dimension diverging ≥2 forces a retrospective that produces a rule
   revision (CHANGELOG + version bump) — this is the skill's iteration engine.

## Six non-negotiable red lines (every scenario)

1. No invented facts; every number carries its source; illustrative values are
   labeled;
2. No coined Chinese: new concepts with no established Chinese term take the
   English term directly;
3. The sales storyline is **value and future**; honesty boundaries converge to a
   single trust page;
4. Every title names its subject and carries a verifiable fact — no word ceiling,
   no bare-antithesis titles, and no single title frame across more than 60% of a
   document; all titles concatenated must read as a complete argument;
5. Charts: one accent color, conclusion-style titles, a source line on every
   figure;
6. AI never signs; money/safety conclusions never come from a language model.

## Cross-platform

Three entry points load one rule set (single source in `references/`, with
`brand.md` first in every load order):
Claude Code uses this file; Codex reads `AGENTS.md`; Kimi / DeepSeek use
`prompts/lumi-style-core.md` (self-contained single file). Per-platform loading
notes live in `adapters/`.

## Boundaries

- This skill contains style rules and templates only — no client names, project
  figures, or engagement facts;
- Style rewrites must not change facts or framing;
- Rule revisions come only from review retrospectives — no additions or deletions
  without a documented case.
