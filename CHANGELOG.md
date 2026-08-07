# Changelog

Rule revisions come only from review retrospectives (divergence ≥2 → retrospective
→ revision), recorded here with a version bump.

## 2.0.1 — the measure cap belonged to the page, not to one of its children

`.body` carried `max-width: 1180px` and `.foot` carried nothing. On the design
page that is invisible, because 1180 plus the padding is the page. On any wider
window the footer ran to the window edge while the composition stayed anchored
left, so **all 28 pages showed a dead band down the right** and the source line no
longer lined up with the content it sourced. A reader caught it at 1817px; the
contact sheet never would have, because `inspect_layout.py` renders at exactly
1280x720 and 794x1123, where the defect does not exist.

The cap is right — prose should not widen to fill a monitor. Applying it to one of
the page's three children was the defect. Anything sharing the page frame now takes
the same width and centers, so the leftover space becomes a symmetric margin
instead of a hole. Verified at 1280, 1817 and 1920: 28 of 28 pages align, and the
right margin equals the left.

Lesson recorded in `references/design-rules.md` §7: a probe that only ever renders
the design geometry cannot see a defect that only appears away from it. Check one
size the document was not designed for.

## 2.0.0 — 2026-08-07

Reader review scored H1, H2 and H3 at **1**, against self-scores of 3. The anchors
for 1 are "the page talks to itself", "a template forced onto the content" and
"figures are decoration". All three were fair, and the root cause is one sentence:
**1.9.0 turned qualitative design feedback into metrics and then optimised the
metrics instead of designing the pages.**

**Principles now govern.** `SKILL.md` opens with the principal-designer role and
four hard rules, above every mechanical rule in `references/`: design per page; no
new universal size floors without an explicit ask; verify on rendered geometry and
content weight, never the element box alone; if a page looks empty, redraw or
recompose rather than growing chrome. **Done when a human reads the page as
intentional — passing metrics is necessary but never sufficient.**

**Three invented floors withdrawn.** D7 (82% page fill), D9's 40% layout-share cap,
and the 11px type floor. D7 is the cautionary one: it measured the bounding box of
all ink, so a small chart with a long caption scored as full, and it was satisfied
by stretching table rows while four diagrams rendered at 40% of their cell. The
skill already forbade this move on the prose side — click-through must never
measure relevance, because the metric rewards what it exists to suppress. D7 was
the same mistake in the design half. **The whole D-series stops gating**;
`check_design.py` reports and exits 0.

**Two output geometries are now a governing principle**, both latent defaults for
internal and market material: 16:9 landscape at 1280×720 (primary, checked at
1920×1080) for projection and PDF/PPT export, and A4 portrait at 794×1123 for
printing and binding. Portrait is a composition, not a reflow; collapsing every
horizontal layout at a width breakpoint is the landscape design giving up.

**`scripts/inspect_layout.py`** renders a deliverable page by page at both
geometries and emits a **contact sheet** — the whole deck as one image, which is
what makes human review of 27 pages possible at all — plus centerpiece scale,
figure-to-cell aspect, and the largest empty band. It gates nothing. Its own first
version shot the viewport after a smooth scroll and produced a sheet of half-pages
under the wrong captions; it screenshots the section element now.

What the tool found immediately, and D7 had hidden: four diagrams at 4.6–5.4:1
sitting in 2.4:1 cells and filling 44–51% of the available height, two pages with
centerpieces at 13–15% and empty bands over a third of the page, and a blanket
`.body > div{flex-direction:column}` rule from 1.9.0 that stacked every spec strip
vertically — which alone made the cover 1301px tall inside a 720px page.


**Second pass, same release.** The four wide diagrams were redrawn rather than
rescaled, per hard rule 3. Nodes went from 46px strips to 112px cards carrying the
detail that earns the space: the S0–S4 chain gained the three ledgers with their
real status and a feedback band with a return path; the origin chain gained the
tier scale and the watershed as a decision; the funnel gained its below-threshold
branch and the two exempt classes; the evals ladder gained what each layer tests,
what it needs, and its status. Captions were compressed to a reading plus a source.

**Every page now fits 1280×720**, the primary geometry. Eight did not, and the
causes were a flex chain missing `min-height:0` at three levels, so a figure's
intrinsic height beat its cell, and an absolutely-sized cover mark. Twelve
stroke-only `<path>` polylines in the new figures had no `fill:none` and rendered
as solid black wedges — visible on the contact sheet, invisible to every metric.


**Third pass · palette, lists, captions, legends.** Four reader items.

*Colour.* The light canvas is **pure white (#FFFFFF)**, not the warm cream the
field has settled on, and the dark canvas is **Apple space grey (#1D1D1F)**. The
state palette grew from two colours to four, each with one fixed meaning and each
measured as text on its own canvas: `--amber` (#A86407 / #E0A73E) for partial, in
progress, awaiting an input; `--brass` (#7A6C52 / #C3B393) for reference and
archival. Before this, "partial" and "not built" both rendered as dashed grey, so
a deck could not say the one thing it most needed to say about itself.

*Lists are back.* "Bullet pileups are banned" had been read as "lists are banned",
and a 27-page deck shipped with **zero** `ul` or `ol` — M10 could not even be
computed. The rule now separates the pileup from the list and says what each form
is for: ordered for a sequence performed in order, bulleted for conditions that
must all hold, dashed for alternatives.

*Figure number and name go below the figure, and that does not change.* Two split
pages had moved the caption into the side column, which detached the number from
the thing it numbers.

*The legend goes where the figure wants it.* "Top right, above the plot" was
applied to every figure regardless of shape, at a size that competed with the
figure title. It is now a key in the narrative voice at caption weight, positioned
by the figure's own layout.

`inspect_layout.py` gained per-cell fill and now measures centerpiece scale against
the cell the centerpiece lives in rather than the whole page — measuring against
the page made every split look half empty when both its columns were full. Its ink
selector had also omitted lists and spec strips, so a full column of ordered steps
reported as 10% ink.


**Fourth pass · portrait, and the two thinnest pages.**

*A4 portrait is now a composition.* The width breakpoint that collapsed every
horizontal layout was the landscape design giving up; portrait now has its own
rules keyed to aspect ratio, with tighter margins, a narrower measure, and
asymmetric splits becoming a centerpiece over a band rather than two gutters.
Two-column layouts keep their columns, because 682px of content carries them.

*Figures are drawn twice.* A 2.39:1 chain in a 0.79:1 cell fills a third of it and
no CSS fixes that, so the four wide diagrams gained portrait compositions: the
same content as vertical chains. Measured, the three that had no portrait variant
sat at 71 to 73 percent empty band; with one they sit at 1.5. Aspect now matches
the cell in both geometries, 0.76:1 in portrait and 2.39:1 in landscape.

*The two thinnest pages were recomposed, not padded.* A two-row table cannot fill
a page and, worse, it hides that its two rows are opposites — the mutual-exclusion
page is now two facing cards, one per product family, each carrying its 232 status,
its country-layer status and the dimension that owns it. The filing-timeline page
moved its table to full width with the two caveats as a band beneath.

`inspect_layout.py` gained two fixes found by using it: it now measures the
*visible* figure, because a page carrying both a landscape and a portrait drawing
was being reported on the hidden one, and its ink selector had omitted the card
and definition-list elements, so a full column read as 2 percent.


**Fifth pass · page-height conformance, and the last thin pages.** The reader
noticed two pages were simply longer than their neighbours in portrait. They were:
**p18 ran 94px and p22 116px past A4**, and no existing measurement could see it,
because fill, aspect and centerpiece scale are all measured *within* a page. That
is now **D11**, reported per geometry and the first thing to read. The causes were
a callout pasted into both cells of a split and orphan one-paragraph cells left
behind by an earlier re-lay — content defects that no content metric catches.

All 27 pages now render at exactly 720px at 16:9 and exactly 1123px at A4, in both
palettes. The four-tile stat band became a grid that owns its cell and goes 2x2 in
portrait, taking two pages from 37% fill to 100%, and the trade map lost a fixed
620px cap it had been given to stop it overflowing a page it no longer overflows.


**Sixth pass · the last thin page.** p17 argued that the public record exists on
filing day while the industry announcement waits for approval, and it argued it
with a three-row table. A table cannot carry a duration. The page is now a split
with **Figure 3, a timeline**, drawn for both geometries: three accent nodes on
filing day, a dashed run of weeks or months, and a muted node where everyone
without the docket starts. Its type is set larger than the default figure scale,
because a figure carrying half a page's argument should not read as secondary to
the table beside it. No content page in the deck now sits below 45% cell fill in
either geometry.


**Seventh pass · the glossary, and H5 off 3.** Business readability had sat at 3
for four rounds because layout and colour work cannot touch it: a sales reader
meets HTS, 301, 232, GN11, RVC, HS2012, USMCA's four names and two unrelated L
numberings, and the deck offered nothing to resolve them. Twelve terms now sit at
page 7, **before the pillar pages that first use the vocabulary** rather than in
an appendix nobody reaches, and the last entry is the two-L trap the source
document calls the easiest misreading in the engagement. Four terms a reader can
infer from context were cut so the twelve that actually block a reading stand
clearly. The deck is 28 pages, still exactly one page each in both geometries, and
the usage-tier citations are now generated from page ids so they cannot drift when
a page is inserted.

The cover and closing are recomposed: the globe is part of the composition rather
than absolutely-positioned decoration mostly off-page. The remaining page-by-page
design work is open and tracked.

## 1.9.0 — 2026-08-07

Reader review of five annotated pages, all about layout. One measurement explains
most of it: **the deck contained exactly one layout, used on 25 consecutive
pages.** `.body` and `.body.top` differed only in `justify-content`, and there
were zero grid rules in the file. Every page was eyebrow, title, one block,
footer. That is a template rather than a design language, and it is why the pages
read flat and left roughly 40% of every text page empty.

**Fifteen layouts now ship**, in `tokens/lumi-layouts.css`. Vertical: `stack`,
`hero-band` (dominant block over a thin strip), `band-hero` (its inverse),
`thirds-v`. Horizontal: `split`, `split-wide` at 38/62, `split-narrow` at 62/38,
`columns-2`, `columns-3`, `columns-4`. Composite: `rail`, `quad`,
`sidebar-notes`, `full-bleed`, `diagonal-flow`.
`design-rules.md` §3 gains a content-to-layout selection table in the same shape
as §4's chart form-selection, because a vocabulary without a rule for choosing
just moves the arbitrariness one level up. This is a third token file, so version
lockstep now covers five stamps rather than four.

**The gap above the footer was mechanical.** `.fig svg{width:100%;height:auto}`
gave every figure its intrinsic aspect and no way to grow, so a 3:1 diagram in a
tall page left the difference under the footer. The centerpiece row is now `1fr`
and the figure fills it. **D7** puts a floor under it at 82% of available height,
and a page that still cannot fill has the wrong layout, which the selection table
is there to fix.

**A rule that had no floor was simply not followed.** §3 has required "one to
three sentences of support" since 1.6.0, and 10 of 25 pages had none — every
figure page plus four table pages. It is now unconditional and checked by **D8**.
Third release running that a prescribed value without a floor produced a visible
defect, which is why `CLAUDE.md` §6 exists.

**Icons extend past the eyebrow.** Labelled nodes inside figures and table
row-head groups carry their semantic icon, minimum 14px effective, honouring the
reserved bindings. **D9** caps any single layout at 40% of a deck's pages and
requires at least five distinct layouts in a deck of fifteen or more, so 25
identical pages cannot recur. **D10** reports label icon coverage.

On tilted layouts, asked for at 15, 30 and 45 degrees: **implied diagonal only**.
`diagonal-flow` gets its movement from stepped offsets and an angled accent rule
behind the blocks. Rotating body text and tables breaks printing, copy and paste
and screen reading, and a document about tariff law cannot pay that for a
flourish. On filling the text measure to the full column width, also asked for:
the cap stays at 88ch. An 1180px column at 14.5px holds about 115 characters
against a comfortable measure of 45 to 75, so filling the line would read worse.
The page was unbalanced because the right half was empty, and a second column is
what fixes that.

## 1.8.0 — 2026-08-07

Reader review of a sales-enablement deck: seven defects, and measurement said
three of them were the skill's fault rather than the deliverable's. An author
following `design-rules.md` literally would reproduce them every time.

Three failure classes sit behind the seven, and all three are now maintenance
rules in `CLAUDE.md` §4–6.

**The ladder was unreadable below its second step, and one alpha list served two
canvases.** Measured against their own backgrounds, the lower steps ran 2.91 /
1.81 / 1.32 / 1.16 on light and 4.08 / 1.99 / 1.36 / 1.16 on dark. The deck put
its eyebrows, captions, source lines, page numbers, table headers and every 9px
SVG label on those steps, which is the whole of a document's connective tissue,
and the reader's first note was that both canvases were exhausting to read. The
ladder is now two ladders with names that carry the rule: `--tx1..--tx4` for text,
every step clearing 4.5:1 against both `--bg` and `--card-bg`, and `--ln1..--ln3`
for rules, borders and fills, never text. Each palette carries its own alphas.
`--on-acc` became palette-dependent after measuring cold white on the lifted dark
accent at 2.65; until now one value claimed to serve both and white labels inside
accent bars shipped unreadable. `check_repo.py` recomputes every step and refuses
a ladder below the floor — the guard that used to enforce the shared alpha list
now enforces legibility instead.

**Two assets the rules required and the package never shipped.** §5 has demanded
a semantic icon library since 1.2 and shipped none, so the deck contained zero
icons; the eight icons now live in `assets/icons/` with `scripts/embed_icons.py`.
The cover rule banned imagery because the skill had no photo library, applying the
ban to every kind of image when photography was the actual risk; `assets/vectors/`
now ships an orthographic globe and a flat trade map, generated from lat/lon by
`scripts/build_geography.py`, and a cover may carry exactly one vector mark. Both
are the defect 1.7.0 fixed for the display face, repeated one directory over.
`.gitignore`'s blanket `*.svg` would have dropped both silently and now carries
the exceptions.

**Prescribed values with no floor.** The type scale had no minimum and its two
copies disagreed (tokens 11 / 10.5 / 9.5 against prose 14 / 10–11 / 11, tokens
winning, so 9.5px source lines shipped); there is now an 11px floor and the scale
is 13 / 11.5 / 10.5. The three callout tiers had no budget and a deck put 18
tier-one callouts on 14 of 27 pages, so the hierarchy degraded back into the flat
page it was introduced to fix; tier one is now capped at one per page and a third
of a deck's pages. The figure vocabulary had no consistency requirement and one
figure carried three shape kinds, six dashed states and nine arrows while four
others were rectangles and text; figures must now hold one level across a
document, and a grid of rectangles containing sentences is a table. Footers carry
`N / total`.

**A ceiling read as a target, for the third time.** "Titles budget two lines"
produced titles engineered to two lines: the author capped the container at 48ch
and all 24 content titles broke near the middle. One line is now the goal, two the
ceiling, and narrowing a title container to manufacture a break is banned outright.
1.2.0 and 1.6.0 record the same shape, which is why it is now a maintenance rule.

**`scripts/check_design.py` (D1–D6)** makes the design half of the skill checkable
the way M1–M11 made the prose half: contrast, type floor, callout budget, palette
purity, figure parity (reported, not graded — the judgement is not automatable),
footer completeness. Run against the 1.7.0 deck it reports 32 contrast failures,
17 sub-floor type sizes, four pages over budget on 51.9% of pages, and two footer
gaps, which is the reader's list in numbers. `eval-rubric.md` also now requires a
self-score to carry its reasons; a bare number gives a reviewer nothing to diverge
from.

**Second reader pass, before this release shipped.** Two more defects, and both
say the same thing about how it was verified.

*The icon set was too small to say anything.* Eight hand-drawn icons across
twenty-five pages meant `gauge` did five jobs and the reader called the match to
content poor. Fixed by vendoring Lucide (2007 icons, ISC, `assets/icons/lucide/`,
searchable through its `tags.json`) and keeping LUMI's contribution where it
belongs: the reserved bindings in `scripts/embed_icons.py` that pin one icon per
recurring meaning. `embed_icons.py` now emits a **subset** sprite — the deck
embeds 25 icons in 7.7 KB rather than 0.9 MB of library. Breadth and consistency
are separate problems and a house set of eight solved neither.

*A figure shipped clipped.* The evals-ladder band was extended to y=212 inside a
viewBox 208 tall, so its bottom edge was cut and it collided with the caption.
`check_design.py` said all-clear because it reads declared CSS and cannot see
rendered geometry. Three browser checks are now in `design-rules.md` §7 — every
drawn element inside its viewBox, every label inside its shape tested at the
corners rather than the midline, and both re-run after any type-size change,
which had moved seven labels out of their boxes at once. Two of those three
probes passed clean on the visibly broken document before they were corrected,
hence the rule that a probe which has never failed is not a probe.

Also from this pass: a decision diamond had been used for a state, to satisfy the
new figure-parity rule. Parity means building every figure to the same level, not
using the same shapes regardless of meaning; the shape vocabulary still binds.

Two maintenance rules in `CLAUDE.md` (§7, §8) and one scoring rule in
`eval-rubric.md` (§3b): a validation artifact is never a source of conventions,
metrics passing is not a verified document, and a dimension where the reader found
a defect the author claimed to have verified cannot be self-scored above 3 in the
round that fixes it.

Deferred to a later round, recorded so it is not lost: a `check_version.py` that
tells a user of Claude Code, Codex or Gemini that their installed copy is behind
upstream. The immediate mitigation is to install the skill as a symlink to a git
checkout, which makes drift structurally impossible — the copy this round was
built against had been stranded at 1.4.0 while the repo reached 1.7.0.

## 1.7.0 — 2026-08-07

Two operational gaps, both found by asking why a step kept costing time.

**The display face now ships with the skill.** `design-rules.md` has required
D-DIN to be embedded since 1.2, and 1.2 itself shipped with the face declared but
not vendored, so it rendered nothing. The rule was right and the package could not
satisfy it: every deliverable's author had to find the font again. The two woff2
files (43 KB together) now live in `assets/fonts/` with their OFL text, and
`scripts/embed_font.py` prints the ready `@font-face` block or verifies the files
with `--check`. Confirmed the vendored files produce base64 byte-identical to the
already-shipped deck, so nothing about existing deliverables changes. CI checks
the sizes, because a silently swapped face would alter the metrics of every
document that embeds it. Note that `.gitignore` blocks font formats as
deliverable output and now carries an explicit exception — the face is part of the
design language, not a render.

**Waiting on CI is now bounded and outage-aware.** During the 2026-08-06 Actions
incident, open-ended polling consumed most of a working session and merged
nothing: runs queued for six minutes, were cancelled, were re-run, queued again.
`scripts/ci_wait.sh` asks the status page *before* waiting and short-circuits when
Actions is degraded, otherwise checking three times over about four minutes and
then stopping. The protocol behind it is recorded in `CLAUDE.md`: correctness is
answered locally by `check_repo.py` in seconds, CI only unlocks the merge button,
a cancelled run is a symptom rather than a verdict, and re-running into a declared
incident adds to the load causing it.

## 1.6.0 — 2026-08-07

Internal review: sales and marketing deliverables still read as AI-written. The
`humanizer` skill (github.com/blader/humanizer, MIT) was evaluated as a candidate
fix and its rules adapted rather than the skill adopted — LUMI keeps one source of
truth and no runtime dependency. See `NOTICE` for attribution and scope.

The evaluation found three causes, and humanizer only addresses the first:

1. **Coverage was lexical, not structural.** The `[en-output]` ban list was a
   five-item seed while English had been the default output language since 1.3.0,
   and the "delete filler phrases" move shipped without a list of filler phrases.
2. **The de-AI-flavor pass was an orphan.** It is the repo's only real
   anti-AI-flavor machinery and no workflow step, checklist, gate, or metric
   invoked it; it was absent from `prompts/lumi-style-core.md` entirely, so Kimi
   and DeepSeek users got none of it. The repo already knew the lesson — "a pass
   in the pipeline beats good intentions" — and had applied it only to punctuation.
3. **The mandated forms were themselves the tells.** A deliverable could satisfy
   every rule, score clean on all eight metrics, and still read as machine-written,
   because compliance is what made it read that way.

Changes:

- **[en-output] ban list grown from 5 entries to 8 grouped classes** — significance
  inflation, promotional register, AI high-frequency vocabulary, filler with its
  fixes, authority tropes, signposting, fake-candid openers, closing filler.
- **De-AI-flavor pass is now mandatory and gated**, with seven structural moves
  added (em/en dash ban for en sales/marketing, rule-of-three, list-shape variety,
  inline-header bullets, manufactured punchlines and aphorism formulas, boldface
  inflation, synonym cycling) and a two-pass audit: ask the draft what makes it
  obviously AI-generated, then fix what you named, and confirm no fact was added.
- **New section 6b, de-translationese** — sales and marketing material is now
  authored in English with Chinese translated from it, which imports a second
  failure mode. Precedent: 1.1.0 translated the Chinese rule "not X, but Y" into
  "Not X. Y.", models rendered it back into Chinese, and the round trip amplified
  until readers called the decks AI-flavored.
- **Conflicts with LUMI house style resolved in humanizer's favor**: negation-first
  openings retired as a mandated signature and stripped of their de-flavor
  exemption; the three canned responsibility frames reduced to a disclosure
  requirement phrased in the sentence's own words; the "short sentences" mandate
  replaced by a variance requirement; the accent-word bold made optional.
- **Structural loosening** — the colon title is the reference form, not the
  required one (capped at 60% of titles by M11); sibling-page parallelism only
  where it aids comparison; one to three support sentences of visibly differing
  length per page; the page arc is a default order rather than "never reorder";
  the stock metaphor and the imperative closing line are no longer mandated.
- **M8 is now two-tailed** (overlong share plus a sentence-length variance floor)
  and never waived for decks: it used to count only long sentences, so uniformly
  clipped prose — the dominant modern AI tell, and what the voice rule itself
  mandated — scored a perfect zero. **M9-M11 added**: em dashes, triad rate,
  title-shape uniformity.
- **`scripts/check_prose.py` added.** M1-M8 were called "scriptable" for six
  versions with no script in the repo. This measures M4 and M8-M11 on a real
  deliverable, and reports a file it could not parse as *unmeasurable* rather
  than clean — a linter that says "pass" when it read nothing is worse than none.
- `scripts/emergency_merge.sh` added: a documented, self-restoring path to merge
  when GitHub Actions cannot run the required check. `.gitignore` now also blocks
  deliverable exports and renders — this repo holds the skill, never its output.
- **CI now covers `scripts/`** (`py_compile` plus `bash -n`). It had none, so a
  syntax error would have shipped silently — including into the emergency path
  that runs precisely when CI is unavailable.
- **Fifth guard: ban-list parity.** `check_prose.py`'s phrase list is a second
  copy of §2 and was held to it only by a comment saying "change both together".
  `check_repo.py` now parses §2 and the script's declarations (by AST, so the
  guard never executes the other script) and fails when they disagree in either
  direction. Phrases that cannot be matched mechanically — `rich (figurative)`,
  `key (adjective)`, "adjective stacks in place of numbers" — must now be listed
  in `NOT_MECHANIZED` with a reason, which turns the gap between what the rules
  ban and what the machine can enforce from invisible into documented.

Review round on this release, recorded because the findings were real:

- The emergency merge script executed code supplied by the pull request. Copying
  a trusted `check_repo.py` over the PR's copy was not enough — the script's own
  directory is `sys.path[0]`, so a planted `scripts/json.py` hijacks an import
  and runs. Reproduced, then fixed with `PYTHONSAFEPATH=1` (Python 3.11+ now
  required) plus fork refusal and a merge-ref parent check.
- Its restore path could leave `main` unprotected while exiting 0, and a signal
  handler that returned instead of exiting let a killed merge report success.
  Distinct exit codes now separate "refused", "check failed", "could not run the
  checker", "merge failed", and "protection still off".
- `check_prose.py` matched multi-word entries as unanchored substrings and single
  words with word boundaries — exactly backwards. It flagged "deserves as much"
  and a finance "leverage ratio" while missing "leveraging" and "fostering", the
  actual tells. Every entry is now an explicit anchored pattern with its
  inflections, and ordinary business words are qualified rather than banned.
- Empty, non-UTF-8, and unparseable files reported "all metrics pass"; `--json`
  never evaluated a threshold and always exited 0; HTML markup merged into
  27-word pseudo-sentences that inflated the rhythm metric. All fixed and each
  verified against the failing case.

## 1.5.0 — 2026-08-07

Reader review of two shipped sales decks (zh + en, V1.3.0) against their own
V4.1 predecessor: "page titles suddenly became very short and AI-flavored,
overusing the it-is-X-not-Y contrast — this violates the PwC title principle the
skill was founded on." Measured: title length fell from a median of ~29 CJK
characters to ~8; display type rose 29.8pt → 37.4pt; every evidence figure
(18×, 4,557, 194, 29,845) vanished from the title line.

Root cause: 1.2.0 answered a review complaint about *visual* divergence from
spacex.com by writing a *writing* rule — "a giant short headline (3–6 words)" —
into design-rules §3, without reconciling it against the PwC title contract that
already existed in storyline-templates. The word ceiling then collided with the
still-standing requirement that a title be a complete assertion carrying the
takeaway, and with the negation-first signature's explicit de-flavor exemption;
in ~6 CJK characters the only form that satisfies all three is a bare antithesis.

- **The word ceiling is removed.** design-rules §3 now defers to the title
  contract; headline length follows the fact, bounded only by the two-line budget.
- **Title contract promoted to shared discipline** (was scoped to the consulting
  template, so sales decks had no title rule at all): "Topic: assertive subtitle",
  naming a subject and carrying a verifiable fact.
- **Information floor added**: a bare contrast, a slogan, or a section label is
  not a title. Contrast is a lead-in that must keep the evidence that earns it.
- **Two-line guard rewritten**: display titles are a size *range*; a long title
  takes the lower end before any word is cut. The old "shorten the title, never
  shrink the type" left cutting words as the only legal move once titles went
  giant, and the evidence went first.
- **Negation-first scoped** to the cover and hook, once per document; it is not a
  page-title form.
- **M1 is never waived for decks.** It had been marked "distorted for slides —
  advisory", which removed the only metric that measures this exact failure; the
  regression ran three versions unmeasured.

## 1.4.0 — 2026-08-06

Reader review of the anchor document (five annotated screenshots):

- Long-document callout hierarchy: three tiers (tinted+bordered key conclusion /
  left-rule guidance / muted note) — one uniform left-rule flattens the page.
- Charts: legend at the top right above the plot; two-part caption anatomy
  ("Figure N · Name" centered bold, description left-aligned at figure width).
- Flow-diagram shape vocabulary: parallelogram=I/O, rectangle=process,
  diamond=decision, stadium=terminal, dashed=not built — shapes carry semantics.
- Figure vocabulary ⊆ body vocabulary: body renames must sweep figure labels.
- Deliverables state results, not process: revision stories live in the ledger.
- Version lockstep refined: a user-assigned document-edition sequence (v1.01)
  owns filename+masthead; the colophon still records the producing skill version.

## 1.3.0 — 2026-08-06

Reviewer-driven round (five inputs from deck review):

- **Light-first**: the default canvas is near-white with the ink ladder; dark is
  applied only on explicit request via one `body.dark` override block. Both
  palettes share one token structure; literal colors in components or inline
  SVG are defects. Full dual-palette token set in `tokens/` (lumi-theme.css
  rewritten to v1.3.0; design-tokens.json restructured as palette.light /
  palette.dark).
- **American English by default**: when the user does not specify a language,
  output is American English (spelling, idiom, double quotes, serial comma);
  writing-rules §0 rewritten.
- **Icon-alignment guard** (from a reported alignment bug): an icon on a text
  line lives in a flex container with align-items:center — never a bare inline
  SVG nudged with vertical-align; icon ≈ 1.4× the accompanying text size.
- **Version lockstep**: a deliverable's version number is the lumi-style version
  that produced it; carried on the cover meta strip and closing colophon.
- **Cover and closing templates**: every deck opens with a typographic cover
  (wordmark / title / meta strip) and ends with a closing page (closing
  statement / recap / contact placeholder slots `[TO FILL]` — inventing contact
  details is inventing a fact / colophon). Added to storyline-templates.

## 1.2.0 — 2026-08-06

Direction change, reviewer-driven: "the output diverged from spacex.com — why?"
The 1.x fusion ("skeleton only, keep rounded type and light canvas") kept too
much consulting-deck idiom, and the one adopted SpaceX element (D-DIN in the
data voice) never shipped because the font was declared but not vendored.

- design-rules: decks are **dark-first** (near-black canvas, cold-white ink
  ladder); light canvas stays for long documents.
- design-rules: **D-DIN takes over** as the single Latin face; ALL-CAPS
  display titles at weight 400; rounded faces retired from decks; vendor and
  embed the font — a declared-but-unshipped face renders nothing.
- design-rules: one-statement-per-screen sharpened (giant short headline, one
  support sentence, one centerpiece, thin footer); hairline rows over card
  boxes on dark canvases.
- Accent green lifts to a dark-canvas form (#7C9F63); red text on black uses a
  lifted form while fills keep the seal red.

## 1.1.2 — 2026-08-06

- design-rules: added three field-tested guards from a reader-reported bug round —
  two-line title budget (shorten, never shrink); icon size independent of
  container scaling (blanket `svg{width:100%}` rules must exclude icons; an
  accidentally-stretched icon is not a design choice); in-row card alignment
  constraints (equalized title heights, stat numbers stacked above labels).
- design-rules: new "Verification matrix" section — language axis × viewport axis
  (design / print / short-laptop); footer rule and page number must be visible at
  every matrix point; height-based media queries as the mechanism. Supersedes the
  standalone localization guard (merged in).

## 1.1.1 — 2026-08-06

- Added the localization layout guard to design-rules: translated text runs
  30–50% longer/shorter — re-inspect every fixed-width container page by page
  after any localization pass. (From the English-deck audit: seven layout defects
  found — a wrapped stat band, ragged stat labels, and three SVG text overflows.)

## 1.1.0 — 2026-08-06

- **Repository language: English only — declared a red line.** LUMI serves a
  global audience; all rule prose, entry points, adapters, tokens, and this
  changelog are now English. Chinese strings remain only as rule data for
  Chinese-language output (banned phrases, punctuation patterns, collocation
  examples).
- Rules generalized to be output-language-aware: language-agnostic core
  (facts / voice / structure / charts) + a marked [zh-output] module; an
  [en-output] banned-phrase seed added.
- New field-tested layout guard in design-rules: right-anchored labels on
  full-width bars must anchor inside the fill (white-on-white invisibility bug,
  caught in per-page inspection).

## 1.0.0 — 2026-08-06

Initial release. Rules distilled from six rounds of real delivery polishing and a
first round of reader review on a consulting engagement's deliverables:

- Terminology red lines: no coined Chinese; direct English for concepts without
  an established Chinese term; substring-collision exemptions;
- Banned AI-tell phrases (with the "sales enablement" fixed-collocation lesson);
- Number discipline: sourcing, illustrative labels, repo-wide retraction with
  retirement notes for unreliable citations;
- The "value & future" sales storyline (boundaries converge to one trust page) —
  from a reader review scoring H5=2;
- "So-what is a writing discipline, not a page element" — from a reader review
  scoring H1=1;
- Plain-language scoring anchors ("anchors must be written in the reviewer's
  language") — from a reader review scoring H2=1;
- Five chart iron rules and form selection (partly adapted from
  enterprise-ai-skills, localized);
- Visual tokens v2: space-gray canvas + natural green single accent + China red
  warnings; layout skeleton informed by SpaceX/Tesla research (transparency
  ladder, dual-voice typography, cold-white dark canvas).
