---
name: lumi-style
description: |
  LUMI's design language and output writing style. Use when producing business documents, slides, client materials, marketing copy, HTML reports, or charts for LUMI — in any language — or when reviewing existing drafts against LUMI standards. Triggers: "LUMI style", "lumi-style", "按 LUMI 风格". Not for: pure coding tasks or content unrelated to LUMI deliverables.
license: MIT
compatibility: >-
  Scripts need Python 3.12+ (standard library only at runtime).
  inspect_layout.py and export_pdf.py additionally need local Playwright
  (Chromium) and Pillow; everything else runs anywhere.
metadata:
  version: "0.1.592"
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
question worth a round trip, because the answer changes every page.
**The output language is asked on the same terms, and it is asked rather
than inferred**: the language of the source material, the venue and the
audience's nationality are all evidence about the reader and none of them is
an instruction. A language the same user chose for a comparable deliverable
outranks every inference from the material; naming a language in a plan and
having the plan approved does not convert an inference into an instruction
(FM-18, which has now happened twice — the second time
the build was stopped by M12 and got past it by editing `lang="en"` to
`lang="zh-Hans"`, because M12 asks whether an ENGLISH document is free of
Chinese and relabelling turned a gating failure into `n/a`). **The ask is
recorded rather than remembered**: `new_deck.py --lang <code> --lang-asked`
writes `data-lang-asked` on `<body>`, and **M16 fails a deliverable in any
language but English that carries no such record**. A second
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
Exports otherwise follow the export axis in `references/design-rules.md` §8
(PDF at the stage; rasters default 4K, floor 2K).

**Repository language: English only (red line).** Chinese strings appear in the
rules only as rule data for Chinese-language output.

## Workflow

Seven steps, and the numbers are their names — comments and release notes cite
them: [step 0](#step-0--read-brandmd-and-commit) commit to what the deliverable
is · [step 1](#step-1--study-the-input-then-pick-the-scenario) the input and the
scenario · [step 2](#step-2--write-and-review) write · [step 3](#step-3--visuals-and-charts)
draw · [step 4](#step-4--before-delivery) the pre-delivery checks ·
[step 5](#step-5--version-lockstep) the version stamp ·
[step 6](#step-6--review-loop) the review loop.

**The order matters, and it is commit first, clarify second.** Land the concept
fully, then apply the red lines and the craft rules to make it clear. Doing it the
other way — starting inside the constraints and decorating outward — is
measurably how you get work that is correct and lifeless. Through 0.1.344 this
skill ran 272 restricting lines against 12 inviting ones, and every release added
more brakes because every release fixed a defect a reader had found. No brake has
been removed; they now apply at step 4 instead of framing step 0.

> Source: [`references/operating-rules.md`](references/operating-rules.md) §6.
> That file is where the entry paths are true; this is a restatement.

**A document reaches this workflow one of two ways, and the build records
which.** **Path A** is a discussion in four beats whose order cannot be
reversed: the user's free statement first and uninterrupted, then the agent's
questions (step 1 below), then advice, then a **storyline review** — titles,
order and the logic joining them, agreed before anything is built.
**Beat 4 is the only defence completeness has**, because C5 reports and never
gates; run `check_outline.py` on the outline and read the titles as one
paragraph. **Path B** starts from a recipe — a scaffold, a previous build's
source, a structure carried forward — and it is what most real builds use.
**Both are held to the current rules, gates and evals: re-running a recipe
shows that nothing broke, and shows nothing about what the rules gained since
it was written.** Timing starts when the storyline is agreed; the discussion is
not charged against it. Open the build's trace at that moment
(`scripts/ops/trace.py open --entry-path A|B [--recipe <path>] …`) and close it
after the checks (`trace.py close`), which transcribes the verdicts rather than
accepting them. **`--recipe` at open only when the recipe is already in hand** —
a fill script written after the scaffold does not exist yet, and is recorded
then with `trace.py annotate --id <id> --recipe <build script>`; never point
either at the outline, which is the plan rather than the driver. **`--recipe` is how path B stays honest**: a trace's
`skill_version` is read from SKILL.md at open, so it can never be stale, and
without the recipe's own version stamp a replay of a frozen script is
indistinguishable from a build made to today's rules. `ledger.py` reports
current, stale, or **unknown** — and unknown is not current.

### Step 0 · Read `brand.md` and commit

**Read [`references/brand.md`](references/brand.md) and commit.** 上善若水 —
what LUMI is, the field and the waterline, and the accelerators. This is the
only file that says what to reach for. Decide what the deliverable *is* before
you decide what it may not do.

### Step 1 · Study the input, then pick the scenario

**Study the input, then pick the scenario.** Read everything the user
supplied before designing anything, and work from the reader's side — the
first-principles question: what does this reader need to do differently
after reading, and which of the supplied facts earn a page for that. **Questioning is segmented, and the segments are the user's**: let the
user state everything freely first, then ask follow-ups grouped by the
topics THEY raised — segment-by-segment follow-up roughly doubles the
core detail recovered versus one batched round (the batched form shipped
here for six releases against the research that had already falsified
it). Questions may probe structure and evidence and may never decide the
user's conclusions for them. When nothing needs asking, state the
assumptions in the delivery note and proceed. **Genre and geometry are asked
before anything is generated** — the answer changes every page.
**Output language is not one of them, because it is not open by
default: the build is American English unless the user asked otherwise.**
When they did ask, quote them — `new_deck.py --lang <code> --lang-asked
"<their words>"` — and the deck is authored in that language directly.
M16 fails a non-English deliverable carrying no quotation. Never read the
language off their material, off the language THEY are typing in, off
the venue, or off where the audience is. This is written here rather
than only in the preamble because the rule sat in the preamble, correct
and forceful, for all three of the builds that broke it — and because
the version that asked for a record got one the agent wrote itself
(FM-18). **For an external document, the value pass comes before the build**: answer
5W+1H for the document as a whole (what, why, who, when, where, how — the
reader should recover all six from the deck alone), give every key number
its judgment anchor, and write the ask as who-does-what-by-when. The first
blind review scored a gate-clean deck 1 on completeness and 1 on
actionability for skipping exactly this pass (FM-16). Then
pick the scenario on both axes: the **genre** (sales/marketing ·
consulting/client document · internal analysis · training material — which
rules bind) and the **storyline** (which narrative skeleton — the roster in
[`references/storyline-templates.md`](references/storyline-templates.md),
from market analysis to the investor pitch). Read that file and choose both
before writing.

**Read [`references/design-rules.md`](references/design-rules.md) here too,
not when a section pointer sends you.** It is the longest rule file in this
package and the only one this entry point never told you to open: colour
(§1), type (§2), one claim per screen and the layout table (§3), the chart
iron rules and form selection (§4, with the shape library under §4.0–4.2),
the commercial footer (§5), **semantic icons (§6)**, numbers as the copy
(§7), the verification matrix (§8) and imagery (§9). **Most of this package's
rules have no automated check at all** — how many is what
[`references/page-contracts.md`](references/page-contracts.md) counts, never
a number written here — and most of the unchecked ones live in that file, so
an agent that does not read it is relying on gates that were never written.
Three conformance decks passed
every gate and repeated one icon across seven pages, left every part opener
without its subject mark, and put a stat band on the agenda; all three are
§3 and §6 rules, and none of the three agents had been told to read them.

**Fetch all of it in one command**: `python3 scripts/ops/brief.py --genre <g>
--storyline <s>` concatenates every file named above — brand, the one storyline
template, analysis rules, writing rules, the card, the exemplar note, and the
section index of the two long ones (`--full` for those whole). It changes
nothing about WHAT you read; it changes that reading it cost twenty API calls
and 82,000 output tokens on a measured build, 84KB of it fetched twice by two
different tools in adjacent calls.

**Keep [`references/build-card.md`](references/build-card.md) open while you
compose, and stop re-opening the reference files for a class name.** It is
generated from the registers and the tokens, `--check` in CI, and it carries
only what a script can fail you for: the three must-asks, the gating verdicts,
what gates per page kind, the layout and role vocabulary, and the one command.
It is about 5,900 tokens against the ~98,000 the reads above cost, and the
difference is the whole reason it exists — a 2026-08 ten-page build re-sent
**105 million cached tokens across 460 API calls**, and every one of those calls
carried the reference set. **The card is not the rules and says so on its face**:
it holds no judgement, and an agent that reads only the card produces a document
that passes every gate and says nothing, which is exactly what five conformance
rounds produced. Read the references above to have something to say; read the
card so you do not read them again.

**Building or checking ONE kind of page? Read
[`references/page-contracts.md`](references/page-contracts.md) rather than
hunting.** It is generated from the rule register, so it cannot drift: every
rule binding the cover, the agenda, the part openers, the closing page, the
content pages and every page, each with the one `file:line` where it is
actually written and whether any check enforces it. "What a cover owes" was
spread across three files, and every conformance round broke a different one
of those rules. Its deck-wide disciplines bind every scenario: the
agenda is **derived from the page titles** (D27 gates the mirror — an
agenda paraphrased in fresh words fails the document) and renders as the
**launch sequence** the scaffold emits, every external
content page closes with one **`.take` takeaway line** (D28 reports the
coverage), and a customer-facing product deck walks **What → Why → How →
Value** in the reader's order (Template 6), and an investor BP is built
vertebrae-first — the page titles agreed as one argument, evidence before
vision, the ask as the climax (Template 11, storyline `pitch-deck`). **A seed
pitch is looked at rather than read**: concepts and figures carry about 80%
of a content page, which is a floor on the drawing and so a ceiling on the
prose, and a 50/50 `split` cannot reach it. **Work in parallel where the platform allows** —
pages are independent once the storyline is fixed — and the parallel form
has a protocol, proven on real builds (owner target: a 30-page document in
under ten minutes end-to-end):

- **The orchestrator owns the frame.** It fixes the storyline and the page
  order, generates the scaffold (`new_deck.py`), and splits the content
  pages into contiguous parts — `body-1.html`, `body-2.html`, … — each a
  run of complete `<section class="page">` blocks. Shared things stay OUT
  of the parts as placeholders: `FOOT_<n>` where each footer goes,
  `GLOBE_SVG` and friends for shared assets, so no part needs to know the
  page total or carry a copy of an asset.
- **Part authors run in parallel**, one agent per part, each against the
  same tokens and rules and its slice of the storyline. A part writes page
  markup only — no `<head>`, no fonts, no runtime, no page numbers.
- **A small assembler stitches**: preamble + parts joined in order +
  placeholder substitution (footers with the now-known total, assets once)
  — and then the merge gate: scan for any unreplaced placeholder and REFUSE
  the build on a leftover (`SystemExit`, naming them). A placeholder that
  survives to the reader is D14's territory; the scan catches it at merge.
  **The runtime is BUILT, never harvested**: the assembler calls
  `embed_globe.build()` for the block that turns the cover and closing
  marks. A 0.1.449 deliverable scraped it out of a fixture with a regex
  instead, matched nothing, emitted an empty `<script></script>`, and
  shipped two still globes — and a substitution that resolves to the empty
  string passes the merge gate, because the gate looks for leftovers rather
  than for losses. D19 gates that one now.
- **Verify once, at the end, on the assembled document** — the step-4 gate
  stack does not run per part. During authoring a part gets at most the
  cheap text checks (`check_prose.py`, `check_design.py`; both take
  multiple files and run in under a second).

When the expected end-to-end time still passes ten minutes — a serial
platform, or a document far past thirty pages — say so before starting.
1b. **The analysis beat — facts become findings before any page is
written.** Read [`references/analysis-rules.md`](references/analysis-rules.md)
and, for every content section of the agreed storyline, apply one of the
five analytical moves (compare · decompose · position · correlate ·
bridge) and record in the outline:
`analysis: <move> | finding: <the page title> | implication: <the take>`.
Pick the figure at the same time — the ghost deck: the framework from
[`assets/frameworks.json`](assets/frameworks.json) (question → framework
→ shape) or a chart form from design-rules §4, so every page knows what
it will draw before anything is composed; name it in the outline
(`framework: <id>`) and the scaffold puts that framework's shape in the
page's figure slot. **Read the exemplar notes here, not later**:
[`references/exemplars/mckinsey-design-notes.md`](references/exemplars/mckinsey-design-notes.md)
(the ten devices a consulting page uses to carry an argument) and, for a
`pitch-deck`, [`references/exemplars/yc-pitch-notes.md`](references/exemplars/yc-pitch-notes.md)
— this beat is the one place they can act; loaded at composition they
landed as typography and never as analysis. `check_outline.py` reports
declaration coverage and the move vocabulary; whether the analysis is
REAL stays with the benchmark review. A deck that skips this beat renders
fine and reads as display — both blind reviews scored exactly that shape
1 on insight. **The reader-outcome rule binds the external genres** (AR-5):
an internal metric appears on a page only as the driver of an evidenced
reader outcome; a metric label the target reader would have to ask about
has failed the jargon test; a figure whose placements are judgements
prints its basis inside the figure.

### Step 2 · Write and review

**Write and review** under
[`references/writing-rules.md`](references/writing-rules.md) (terminology red
lines / banned phrases / punctuation / number discipline / the LUMI voice /
de-AI-flavor pass). **Run the punctuation pass after drafting.**

### Step 3 · Visuals and charts

**Visuals and charts**: compose against `brand.md`'s two devices first — the
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
**A figure title states a conclusion, not a label.** **The page's numbers
go into the geometry, not beside it** — in the external genres a figure
carries the values the page states (D29 reports the page that states
numbers and draws none), because a shape composed with words alone is an
icon wearing labels. "Sources feeding the
radar" is a label; "every narrowing step names its criterion" is what a reader
carries away. Every figure gets a source line, and its number and name go
below it, and the caption numbers run 1..k once each in page order (D30 —
the scaffold numbered them from the PAGE index until 0.1.521, so every
accepted deliverable shipped holes).
**The number reads before the words it belongs to** (§7): above its label in
a stat block (`.stats`/`.stat`, and `.band` renders the same way round), at
the FRONT of a title rather than spelled into the middle of one, and on or
above its mark inside a figure. It is an order, not a size floor. A page
whose argument turns on a single number has `.lead` waiting for it — which
no shipped deliverable had used even once before this rule was written.
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

**Then compose the page — starting from the scaffold, never the fixture.**
`python3 scripts/ops/new_deck.py --genre <genre> --geometry <geometry>` emits
the standard order with the display face embedded and every icon reference
resolving (to stdout by default; `--out <file>` writes it).
**It now chooses each content page's layout rather than handing every page the
same one.** It used to emit `body split` on all of them — the one layout
`references/storyline-templates.md` rules out for a figure-led page (search it
for "figure-led page"), because half the width cannot reach the
visual-share target however the prose is cut. Measured on its own output: 10 of
11 content pages under the 50% internal target and a top layout share of
**71.4%**, which is worse than the 70.0% deck an owner review rejected. It now
alternates `split-wide` and `stack` and gives a thin unit the whole width: 4 of
11 under target, top share 42.9%. A `stack` page also emits ONE cell rather than
two, because that grid declares `auto 1fr` and a third child starved the drawing
to 3% of the page.
**`python3 scripts/ops/build.py` is the whole build in one command** — scaffold,
your fill script, `embed_shapes`, and the step-4 gate stack — and it is what a
real build should run, because every separate command is an API round trip
carrying the whole conversation. Measured on a 2026-08 ten-page deck that ran
them separately: **389 terminal commands and 460 API calls, 105 million cached
input tokens**, of which the fill script alone was 46 invocations and
`embed_shapes` 38. The driver also writes the debug log as a side effect, so
debug mode stops costing a turn per command.
**It also carries the previous round's reading forward**: from the second round
on it passes `--against` by itself, so a round that moved no measured number
says so — one session ran **six rounds after its last failure** with nothing
able to tell it that. `--facts <contract.md>` adds the one check that asks
whether the rebuild still carries the facts it was built from; `--deliver`
folds in the PDF export and the scoring sheet, which were separate commands
after the driver had already returned. `fixtures/` are checker inputs: a 34-page review reached its
reader with `REPLACE ME` as its browser-tab title and the fixture's
`www.example.org` in all 34 footers because its pages were hand-copied from
one, and `check_design.py`'s D14 now refuses the scaffold's own slots.
**The palette is not yours to choose. Copy the token block in
[`tokens/lumi-theme.css`](tokens/lumi-theme.css) into the document and use
it** — the scaffold above already does, which is the easiest way to be right.
Layouts come from [`tokens/lumi-layouts.css`](tokens/lumi-layouts.css) and
the same values in machine-readable form from
[`tokens/design-tokens.json`](tokens/design-tokens.json). **Sizes you may
set** — design per page, and 0.1.340 withdrew the type floor — **colours you
may not.** One colour means one thing across every LUMI document, and a deck
that redefines the accent is a different design language wearing the same
variable names. `check_design.py`'s D20 fails a document whose colour tokens
disagree with the shipped ones.
*Provenance: this paragraph said only where tokens come from, while the rule
for the display face beside it said "embed rather than improvise". The
asymmetry was found while diagnosing three runs that each invented a fresh
palette — but those runs turned out to have been unable to READ `tokens/`
at all (a harness fault, fixed in the same release), so they are not
evidence about this sentence. It is corrected because a rule that states a
location where it means an instruction is a rule waiting to be read the
generous way, not because it is known to have been.* **Choose a page layout for
the content**: §3's table is a reference of what has worked, not a lookup, and
a page that wants something not in it should get it. **On portrait the split
family renders as one composition** — variety there comes from the vertical
and composite families, chosen from the content and checked on the rendered
page (§3's portrait note carries the two cautions). **Embed the vendored
assets rather than improvising**: `scripts/build/embed_font.py` for the display face,
`scripts/build/embed_icons.py` for the icon library,
`scripts/build/embed_shapes.py` for the shape library, `assets/vectors/` for
the globe and trade map. **Choose a shape by the RELATION the content has**
— composition, order, process, hierarchy, degree, correlation — and never by
how the shape looks; `assets/shapes/tags.json` carries that relation for each
of the 206 units, and §4.1 is the rule. This line omitted the shape library
for the releases in which it existed, and the consequence was measured: three
shipped deliverables referenced **none** of the 206 shapes, because an agent
following this file had no path to them. **A shape is a starting geometry,
not a finished figure**: 192 of the 206 units carry no text, so composing this
page's own words and numbers onto them is the work — §4.2, which also carries
the two traps that do not announce themselves (a `<use>` of a non-zero-origin
viewBox renders shifted off frame unless it declares `x`/`y`/`width`/`height`;
a `fill=` attribute on a `<text>` loses to CSS, so labels use `style="fill:"`).
Layering, recolouring within the accent ladder, and transforming are all in
scope where the relation survives the transform.
**Imagery is allowed and governed by §9**: an image carries an argument or it
is not on the page; it ships as a `data:` URI and never a link (**D24 gates**);
it names its source and terms (**D25 gates**); it is tinted into the palette;
and text never sits on raw photography. The stock tells — the handshake, the
glass tower, the team around a laptop — are banned by name. **For a world figure that states data, generate it rather than
drawing it**: `python3 scripts/render/regionmap_svg.py` emits the flat trade-region
map with its labels already placed (`--labels zh` for Chinese, `--states`
for the data), and `python3 scripts/render/globe_svg.py` the rotating globe.
These are two components, not two forms of one
(the split is recorded in `references/design-rules.md` §1.2's figure
vocabulary; the dated design history lives in specs/): the map is flat, labelled
and state-driven; the globe rotates and carries `--marks`, its data as a
JSON list of `{lon, lat, weight, label}`.
Colour comes from `tokens/region-palette.css`, which ships the class
bindings too — include it and the figure paints. **Every coloured region
needs a label or a legend row** — D18 checks for it, because hue groups
regions at a glance and only text identifies them; the map emits its own
labels, so this is only work when you suppress them with `--labels none`. Never place the generated 110m map and the coarse
`globe-orthographic.svg` mark in one view; they disagree about where a
coastline is (design-rules §1.2). Text uses the `--tx*` ladder only; `--ln*` is rules and fills.
**Icons come from the two sets this package ships, never drawn ad hoc**:
`assets/icons/lucide/` (2007 stroked icons) for every eyebrow, figure node
and row head, reached through `embed_icons.py --search`; and
`assets/icons/koboyo/` (36 filled silhouettes) for part-opener subject marks
only. **Within one document an icon means exactly one thing** — an icon
reused for a second meaning teaches the reader a vocabulary that then lies
to them (design-rules §6). The scaffold seeds every content page with
`#i-radar` as a placeholder; replacing it per page is yours to do.
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

3b. **Before building, after the storyline is agreed**: run
`python3 scripts/check/check_outline.py <outline.md>`. It decides the cheap
half — topic-label titles, group size, whether a typical section is unnamed
and undeclared — and **prints the titles for you to read as one paragraph
without judging whether they cohere**, because that judgement is the point
of the beat. Completeness is caught here or not at all: C5 reports and never
gates.
**After building, run it again with `--against <deck.html>`, and this half
gates.** Every planned **title** must still be the title of a page, and
every planned `implication:` is reported against that page's `.take`.
(The outline's bullet is the finding, written as the title it will
become; the separate `finding:` field is the author's note to
themselves and no check reads it.) It is
the same consistency question D27 already asks of the agenda, asked of the
plan: not whether either artifact is good, only whether they still say the
same thing. When they diverge, correct whichever is weaker — a title
sharpened in composition means the outline is now stale, and a title that
drifted off the finding means the page lost the analysis. *0.1.522 measured
this on a shipped deck: fourteen sections declared a move, a finding and an
implication, and* **not one of those findings still described a page.** *The
beat ran and composition threw its output away, with every gate green.*

### Step 4 · Before delivery

**Before delivery**, the privacy question — P-5's other half. `check_privacy`
runs INSIDE `check_deliverable.py` below, so **do not run it as a separate
step**; pass the engagement's list through with `--terms <list>` and read its
lines out of the one verdict block. Layer 1 gates (credential shapes, and terms
declared out of bounds: every `*.terms.txt` under `~/.lumi/terms/`, the one home
`references/operating-rules.md` OR-8 names, or the `--terms <list>` you pass);
layer 2 reports; **layer 3 is yours**: is any commercial analysis
here sensitive? The script names that question and does not answer it.
**With no list anywhere the term half reports NOT ATTEMPTED and exits
non-zero** — a check nobody ran is not a check that found nothing. Then: if two MUST clauses of `references/PRINCIPLES.md`
cannot both be satisfied, take its §3 exit — **record both clauses and what
each demanded, do not emit, hand it to a person**; it is rare, and it is not
a way out of an inconvenient rule. Otherwise run the critic gate (structure before polish) and its
red-team pass — read the draft as its most skeptical reader, and treat
over-design as a finding, not a virtue — then the
**mandatory de-AI-flavor pass** — `references/writing-rules.md` §6, including
its two-pass audit and, for an external deliverable, the findings file that
`scripts/ops/judge_findings.py` will only accept with quotations, because a
pass that leaves nothing behind cannot be told from one that was skipped;
for Chinese translated from English also §6b de-translationese — then the C1–C8 self-score per
[`references/eval-rubric.md`](references/eval-rubric.md);
**never self-score 5 before a reader has scored it, and give the reason for
every score**.

**Then measure rather than trust**, and this is where the gates live, because
they belong after the making rather than inside it. **One command runs the
whole stack**: `python3 scripts/ops/check_deliverable.py <file> [--terms
<list>]` launches the rendered check first, runs every text instrument while
the browser works, applies the Evals thresholds, and ends in one block naming
every gating failure, every graded finding, every check that could not be
measured, and — for a document that declares an older build — every gate
written after it, marked `past` and binding nothing. **The block groups by
concept**: five agenda defects arrive under one `── agenda` heading rather
than scattered through the order the checkers happened to emit them, so a
page you have to fix is met once and not four times. Severity stays the
outer axis — a gating failure has to be fixed and a graded one is a reading. **A gate binds a
document built at or after the release that introduced it**; a document
carrying no `built with lumi-style X.Y.Z` line is held to all of them, so
omitting the stamp is not a way out — read that block whole, then fix everything it names in ONE pass.
**While you are still fixing, add `--fast`**: it renders the declared stage
only and skips the off-shape sweep, which is 3 seconds instead of 16 on a
twelve-page deck with every gate still running. It is not a delivery reading
and it says so; the last round before you hand the document over runs without
it, **with `--sheet`**, which builds the contact sheet and prints where it
landed. *Both flags exist because the loop is where the cost is. Measured on a
2026-08 build that used neither: `inspect_layout` ran **64 times at 22 seconds
each** — twenty-three minutes and sixty-four round trips — against six runs of
this one command. The author was running the slow instrument separately to get
the sheet, which is the artifact this file calls the last gate and which
`check_deliverable` used to suppress unconditionally.* It also closes the build's
trace: `new_deck.py` opens one at scaffold time (when a `--storyline` **and an
`--entry-path A|B`** are given) and writes its id into `<body data-trace>`,
starting the build clock;
the check step stops that clock, records its own duration as the checks
phase, and transcribes the verdicts. A document with no trace is reported
`unmeasured` — a build that leaves no record is not a measured build.
**The entry path is declared, never inferred, and the recipe is the builder.**
Pass `--entry-path A|B` to `build.py` (it hands it to the scaffold) or to
`new_deck.py` directly.
Until 0.1.592 the scaffold read path A from the mere presence of an `--outline`
— an outline is used on both paths — and fingerprinted that outline as the
recipe. Two replays of one frozen build script were therefore recorded as
original four-beat builds carrying identical outline hashes, and because an
outline bears no version stamp they sit in the ledger as `unknown` vintage for
ever, while the 39KB script that produced every page was fingerprinted by
nothing. So: pass `--entry-path`, and once the fill script exists record it with
`python3 scripts/ops/trace.py annotate --id <id> --recipe <build script>` —
the hash and the version stamp are computed from the file, never typed. It exists because a
fifteen-page deck once took ten rounds, at least three of them from reading
the reports in installments.

**The instruments below are already inside that command** — prose, design,
layout, privacy and the Evals, in one process, with the browser rendering while
the text checks run. **Do not run them as steps.** They are described here so
you can re-run ONE of them against ONE finding while you fix it, and that is the
only reason to invoke them directly. Running the stack and then the instruments
is the same work twice, and the expensive half of it is a browser.

`python3
scripts/check/inspect_layout.py <file>` renders the pages and builds a contact sheet;
its design judgements gate nothing but it **exits 1 when a check could not be
measured**, and those lines come before every green one. **`--iterate` is its
author's loop** — the declared stage only, no off-shape sweep, every gate still
running — and with `--no-sheet` it measures a twelve-page deck in about 4
seconds instead of 22. It is not a delivery reading. `--deliverable` exits
non-zero on the findings a rendered page
can be wrong about decidably: collision, a starved column, content spill,
page height, hidden content, a wrapped footer, a footer whose runs sit on
different baselines, a viewBox that does not parse, a drawing clipped by
its own viewBox, a stat band whose labels render outside it, an overspent title reserve, a role split, a lost datum, a mark drawn out of proportion to the value it declares, and a document whose content pages are mostly not drawn on at all.
**Do not pass it a `--geometry`** — it reads `data-geometry` and runs the
matrix that declaration implies, and a single `--geometry` switches the matrix
off. (This sentence read "pass it the file and nothing else", which was about
`--geometry` and was followed as a ban on every flag, including the two that
make the loop cheap.) Add a second run with `--dark` if the deliverable ships a dark variant;
one run renders one palette.
`python3 scripts/check/check_design.py <file>` reports the design metrics and
gates on every row its own table marks `(gates)` — none of them a design
judgement, and the script is the authority on which they are. These four are
the ones a draft trips first: **D12**, the handling terms and origin
every page owes (the terms open with the seal-red `shield` handling marker —
the rendering ships in `tokens/`, the gate is the terms); **D14**, any slot
left for yourself; **D15**, a file path in a footer; and **D19**, a reference
that does not resolve inside the document — an icon pointing at no symbol, or
a `data-globe` mark with no runtime to turn it. `python3 scripts/check/check_prose.py <file>` grades the prose, and the
language pair is two questions rather than one. **M12 fails on Chinese in text a
reader sees** when the document declares English, and reports `blind` — which
also fails — when it declares no language at all. **M16 fails a document
declaring any language but English with no record that the user asked for it**
(`data-lang-asked` on `<body>`, or `--asked-lang`). M12 alone was escapable:
relabelling `lang="en"` to `lang="zh-Hans"` moved a document out of M12's
question entirely, and a shipped build made exactly that edit to go green. A
clean banned-phrase run is not a language pass, an undeclared document is not an
exempt one, and a relabelled one is not a fixed one.
`python3 scripts/check/check_facts.py <contract.md> <file>` asks the
question no other check asks — **whether this build still carries the facts
it was built from**. Quantities in the document that appear nowhere in the
contract **gate**, because an invented number is red line 1; facts the
contract permits and the document drops are **reported**, because dropping a
fact is often the right editorial call and sometimes is not. *A rebuild
measured at 0.1.522 had silently lost eleven, including five of the seven
markets whose count the deck still claimed, and passed every gate.*
**A clean run is not a verified document. Look at the sheet.**
(The de-AI pass was advisory until 0.1.336 and nothing invoked it; three versions
of AI-flavored decks shipped past it. The design half had no metrics at all
until 0.1.338, and a deck that passed every prose metric came back from its
reader with seven defects, four of them arithmetic.)

### Step 5 · Version lockstep

**Version lockstep**: stamp every deliverable with the lumi-style version
that produced it — **once, in the closing colophon**, small and out of the
way ("built with lumi-style X.Y.Z"). It used to be stamped on the cover as
well; a reader pointed out that a build stamp and a source citation on the
opening page are apparatus for the author, not information for the reader.
The stamp still has to exist and still has to match — `check_repo.py` fails on
a mismatch — it just does not open the document — the deliverable's own version number **is** that
version. Decks open with a cover and end with a closing page, each carrying
the single vector mark, and every part boundary gets a lime opener page —
about five content pages between openers is the pacing target and **six
is the ceiling `opener_pacing` gates on** — a deck meant to run undivided
says so with `<body data-parts="none">`
(see `references/storyline-templates.md`).

### Step 6 · Review loop

**Review loop**: decks embed the scoring table as the final page; on receiving
reviews, any dimension diverging ≥2 forces a retrospective that produces a rule
revision (CHANGELOG + version bump) — this is the skill's iteration engine.
**The instruments it runs on are these, and they are named here because an
instrument nobody can find is an instrument nobody runs**: `python3
scripts/ops/scoring_sheet.py <file>` prints the blind C1–C8 sheet a reader
fills in — generated from the rubric, so it cannot drift from it — and
`scripts/ops/review_scores.py --check` validates and reports the store the
scores are written into, which needs a `corpus_id` on every record because the
agreement study joins a machine reading to a human score on the same document.
(Transcribing a filled sheet into the store is the operator's edit; the script
reads and validates, and has never had a write path.) `python3 scripts/ops/judge_findings.py` runs the
register pass that has to quote what it objects to; it reports and never
gates, because a judge that scored would be scoring fluency. `python3
scripts/ops/ledger.py` reads every closed trace and says which metric keeps
failing, which instrument is suspect, whether the recipe was written against
these rules, and whether the storyline review happened and held.

**What the build cost, in units that survive being compared.** `python3
scripts/ops/session_cost.py --hermes <session_id>` or `--claude
<transcript.jsonl>` prints API calls, tool calls and every token field for
either platform, and says the two traps out loud: a Claude Code transcript
writes **one record per content block**, each repeating the same `usage`, so a
per-record sum multiplied one build's call count from 70 to 187 and every token
figure by 2.5–3.6×; and a Hermes reading that names the main task row omits
`background_review`, and a task split across two sessions is one task. It
reports tool calls beside API calls because **an API call is not a unit of
work** — the platforms batch differently, and the ratio is the number that says
how much was done.

## Debug mode (on request only)

> Source: [`references/operating-rules.md`](references/operating-rules.md) §1. That file is where the operating rules are true; this is a restatement.

When the user's request says **"debug mode"**, write an execution log beside
the deliverable — `<stem>.debug.json` in the same folder — through
`scripts/ops/debug_log.py`, never by hand
(design: `specs/2026-08-12-debug-mode-design.md`; the subcommands are the
schema, so every platform produces the same log):

- `init <deliverable> --platform <registry id>` at the start;
- `run <log> --label <step> -- <command>` for **every check or build command**
  — it executes the command and machine-writes exit code, output digest and
  timing, so the log is evidence, not claims;
- `attach <log> --kind design|prose|layout --json-file <f>` with each
  checker's `--json` output;
- `assess <log> --dim C1..C8 --score 1-4 --reason "…"` after the self-score
  step (5 is refused — never self-score 5 before a reader). **This said
  `H1..H6` for forty-odd releases after C replaced H**, so an agent following
  this file typed a dimension argparse rejects and spent a round trip finding
  out. `scripts/ops/build.py --assess C1=4:"…"` folds all eight into the run
  you are already making, and attaches each checker's report from the ones the
  check step already produced — the contract used to ask for documents this
  pipeline threw away, so honouring it cost six commands and a second browser
  render;
- `error <log> --stage <where> --message <what>` the moment anything fails;
- `validate <log>` before delivery, and point the user at the file in the
  delivery note.

The log is **English-only**, carries **no engagement fact** (its key set is
closed so there is nowhere to put one), and stays in the engagement folder —
never in this repository. A platform that cannot run scripts (the prompt tier)
writes what it can into the delivery note and names what it owes, the same
degradation contract the checkers use. Without the words "debug mode", write
no log.

## Seven non-negotiable red lines (every scenario)

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
7. Output language is **American English** by default. Another language is
   asked for **in the user's own words**, which the build quotes onto the
   document — never inferred from the source material, from the language they
   are writing to you in, from the venue, or from where the audience is. A deck
   they asked for in another language is written in it, not translated into it.

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
