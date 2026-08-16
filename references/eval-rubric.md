# LUMI Document Eval Rubric

*Serves: **P-2*** — measuring the document is how the claim "this is verified" becomes grounded. · id `ER-1`

> Every external deliverable is self-scored first, then reader-scored; divergence
> drives rule iteration. This is the skill's continuous-improvement engine.
> (Repository language: English only — red line.)

## Contents

- [Machine metrics M1–M13 (scriptable; spot-check manually when no script)](#machine-metrics-m1m13-scriptable-spot-check-manually-when-no-script)
- [Design diagnostics (`scripts/check/check_design.py`)](#design-diagnostics-scriptscheckcheck_designpy)
- [Human dimensions C1–C7 (tick evidence items; do not rate an impression)](#human-dimensions-c1c7-tick-evidence-items-do-not-rate-an-impression)
- [Review protocol (the iteration engine)](#review-protocol-the-iteration-engine)
- [Known genre distortions (never chase the score)](#known-genre-distortions-never-chase-the-score)

## Machine metrics M1–M13 (scriptable; spot-check manually when no script)

**Ten of the twelve have code.** `check_prose.py` implements M1, M2, M4, M5, M6,
M8, M9, M10, M11 and M12. Until 0.1.390 the parenthesis in this heading carried
half the table, and three of the six it carried stood behind a fact red line.

**Two are recorded as NOT MECHANIZED, with the reason**, which is a decision
rather than a gap:

- **M3, coined-term violations** and **M7, term mixing**, both need a per-document
  registry of concept-to-name pairs that this package does not ship. §1's term
  rules are about consistency *within a document*, so the data is the document's,
  not the skill's — and inventing a registry here would be a rule nobody wrote,
  which maintenance convention 2 forbids and convention 5 names directly ("a rule
  may not mandate an asset the package does not ship"). §1's own substring-collision
  warning (`金标` ⊂ `金标准`) is why a naive matcher would be worse than none.
- **The de-translationese pass (§6b)** is judgement about register. Approximating
  it with patterns would produce a number that reads like a measurement and is not
  one.

M5 is the counter-example that makes the line honest: Chinese punctuation looked
like the same kind of judgement and is not. A half-width mark with a Han
character beside it is decidable, and the single adjacency test replaces §3's
whole exemption list — code, URLs, emails, version strings and pure English runs
have no Han character next to their punctuation.

| id | Metric | Target | Predicate |
|---|---|---|---|
| M1 | Assertive-title rate | ≥70%, **reported not gating** (decks included — never waived) | share of titles that name a subject and carry a verifiable fact |
| M2 | Number-sourcing rate | ≥90% | share of percentage and currency figures whose PAGE carries a source marker (writing-rules §4 rule 6) |
| M3 | Coined-term violations | =0 | occurrences of banned legacy coinages (substring exemptions apply) |
| M4 | Banned AI-tell phrases | =0 | banned-phrase hits (fixed-collocation exemptions apply) |
| M5 | Punctuation violations (zh) | =0 | half-width punctuation adjacent to CJK (code/pre/formula exempt) |
| M6 | Unsourced range figures | =0 | range-shaped numbers with no source marker in their own BLOCK; an enumeration label ("blocks 1–3") is reported, not counted (writing-rules §4 rule 6) |
| M7 | Term mixing | =0 | old and new names of one concept co-occurring |
| M8 | Sentence-rhythm health (two-tailed) | overlong ≤8% **and** length CV ≥0.35 (decks included — never waived) | share of sentences past the length threshold, **and** the coefficient of variation of sentence length |
| M9 | Em dashes in en sales/marketing | =0 | em/en dash characters outside code, data, and internal analysis documents |
| M10 | Triad rate | ≤50% | share of enumerations (lists, appositive series) containing exactly three items |
| M11 | Title-shape uniformity | ≤60% | share of page titles sharing one syntactic frame (e.g. "Topic: clause") |
| M13 | One quantity, one value | =0 — **reported** | the same two-word noun phrase carrying two different values with no qualifier near either mention. Deliberately narrow: a time series, a target/actual pair and a per-region split are different quantities, not contradictions |
| M12 | Visible CJK in an English deliverable | =0 — **gates** | Chinese in text a reader sees, when the document declares English by `lang`, filename or `--lang`. Quoted as data (`<code>`, `<pre>`, backticks) is exempt |

## Design diagnostics (`scripts/check/check_design.py`)

| id | Metric | Target | Predicate |
|---|---|---|---|
| D1 | Text contrast | ≥4.5:1 (≥3.0 at 24px+) | every declared text color against `--bg` and `--card-bg` of its palette. **Reader-reported, so treat a finding as real** |
| D2 | Type scale | reported | the small end of the declared type scale. **No floor** — see the withdrawal note |
| D3 | Tier-1 callout spread | reported | tinted-plus-bordered callouts per page, and the share of pages carrying one |
| D4 | Palette purity | reported | literal hex colors outside the token block, which break the palette switch |
| D5 | Figure parity and drawn share | reported | shape-kind spread across figures, how many are rectangles-only, and how many `.fig` blocks hold a drawing at all |
| D6 | Footer completeness | reported | pages missing a source line or a `N / total` page number |
| D8 | Support line present | reported | content pages with no support sentence under the title |
| D9 | Layout spread | reported | which layouts a deck uses, and the share on the most common |
| D10 | Label icon coverage | reported | icons on figure nodes and table row-heads, beyond the page eyebrow |
| D11 | Page-height conformance | reported, and the first thing to read | pages whose rendered height differs from the geometry's, per format (`inspect_layout.py`) |
| D12 | Commercial footer | =0 — **gates** | handling terms and the origin site on every page; pages travel alone |
| D13 | Lime as light text | =0, reported | the acid green may never be light-on-light text; a surface, not a ladder step |
| D14 | Unfilled placeholders | =0 — **gates** | slots the author left for themselves: `[TO FILL]`, `[TBD]`, `{{…}}`, an empty bracket pair |
| D15 | File path in a footer | =0 — **gates** | a repository path pasted into reader copy: two segments and a file extension. The site D12 requires, and any URL, are not paths |
| D16 | Visual presence and share | reported | content pages carrying no visual block (static half, `check_design.py`); rendered visual area against the genre's target — ~50% sales/marketing/consulting, ~30% training (`inspect_layout.py`). Pages declaring `data-role="apparatus"` are exempt, up to a ceiling of one content page in five |
| D17 | Export weight | reported | blend modes, filters and vector nodes: what the document will cost a reader who opens the PDF |
| D18 | Region labels | reported | every coloured region on a map carries its name or a legend entry — the one place hue encodes identity, and the condition under which it may |
| D22 | Layout vocabulary | =0 — **gates** | a page whose layout class is not one `tokens/` defines. D9 collected these and its verdict was hard-coded to pass, so an invented layout was caught by nothing (GAP-008) |
| D23 | Font count | reported | distinct font stacks against **what `tokens/` declares** — the ceiling is derived, not a literal, so it moves if a third voice is ever added |
| D21 | Data contract | =0 — **gates** | a figure that DECLARES the data it draws is held to it: every declared series and value must appear on the drawing. Opt-in — a figure declaring nothing is not failed — but a declaration that contradicts the drawing is a false contract, which is worse than none |
| D20 | Palette fidelity | =0 — **gates** | every colour token the document declares that `tokens/lumi-theme.css` also defines carries the shipped value. Sizes are the document's to choose (0.1.340 withdrew the type floor); a colour is not, because one colour means one thing |
| D19 | Vocabulary resolves | =0 — **gates** | every reference in the document resolves inside it: an icon `<use>` with no `<symbol>`, a block class used without the children `tokens/` renders it through, a part opener with no `opener` class, a `data-globe` mark with no runtime. All render as valid markup and empty space |

**Three tiers, not two, and the Target column above says which.**

| tier | what it does |
|---|---|
| **gate** | fails the run |
| **graded** | prints `FAIL`, does **not** fail the run |
| **reported** | no predicate; a number to read |

**The checker is the authority on which tier a metric is in, not the Target
column here** — `check_design.grade()`'s target string carries `(gates)` for a
gate and `reported` for the third tier, and everything else is graded. The
Target column below has not been re-stated against that and is known to be
wrong for the graded rows: it reads `reported` for metrics the checker grades
against a hard predicate and prints `FAIL` for. Re-stating it by hand is how
this table fell behind in the first place; read the checker.

The middle tier is the one this rubric had no word for. **It is where an Evals
threshold belongs** — a number that can already fail, but on a document rather
than on the run. `evals/thresholds.json` carries those bars, and none of them
gates: see its `status_note` for why, and for the red-team pass that cleared
all four with two mechanical rewrites.

**No design judgement in the D-series gates.** `check_design.py` exits non-zero
when a file cannot be measured at all, or when a metric whose target says
`(gates)` fails. Which metrics those are is read off the rows and written down
nowhere else: a hand-written copy of that list fell one behind the day D20
arrived, and a document failing D20 alone exited 0 while five files said it
gated. `SKILL.md` rule 4 is why the rest only report: a page is done when a human
reads it as intentional, and a metric that can be satisfied without improving the
page ends the looking rather than directing it.

**Seven exceptions, and none is a design judgement.** D12 is a commercial
requirement on the artifact, D14 asks whether the document is finished, D15
asks whether the footer cites something a reader can open, D19 asks whether
every reference in the document resolves inside it, D20 asks whether the
colour tokens it declares are the ones this package ships, and D21 asks
whether a figure that declared the data it draws agrees with its own
numbers, and D22 whether every page's layout is one the tokens
define — all decidable, in the way "does this page read as intentional" is not. **D15 is the second instance of
one defect:** `.foot .src` was removed from `tokens/` in 0.1.366 after the first
deliverable to meet it filled every client page with a build path, and a second
put one back — in Chinese, on almost every content page — while D6, D12 and D14
all passed it. Per-page sourcing stays legitimate for consulting and internal
analysis; what no genre wants is a path. D14 exists
because a real deliverable shipped four `[TO FILL]` markers on its closing page,
beside its own callout saying they must not ship, and every instrument in this
package passed it: a placeholder is not a banned phrase, not a colour, and takes
up exactly as much room as the text that should have replaced it. Bracketed
ellipsis (`[...]`) is deliberately not a marker — it is the standard editorial
elision inside a quotation, and a gate that fires on legitimate prose is one
people learn to route around.

**D16 is a review trigger, not a floor** (owner directive, 2026-08-09). A content
page with no visual block, or a rendered visual share under its genre's target, goes
back to a human to look at: the fix is a redrawn centerpiece, or a deliberate
decision that the page earns its prose, recorded in the delivery note. Both
numbers exist to start the looking, not end it — the withdrawn D7 below is what
happens when a number like this is allowed to end it, and D16 counts classified
blocks rather than ink area precisely so it cannot be satisfied by stretching
anything.

**Withdrawn in 0.1.340**, all three invented without an ask: **D7** (82% page fill),
**D9's 40% share cap**, and the **11px type floor**. D7 is the cautionary one — it
measured the bounding box of all ink, so a small chart with a long caption scored
as full, and it was satisfied by stretching table rows while four diagrams
rendered at 40% of their cell. The skill already forbade this move on the prose
side (click-through must never measure relevance, because the metric rewards what
it exists to suppress); D7 was the same mistake in the design half.

For anything that has to be rendered before it can be seen, use
`scripts/check/inspect_layout.py`. Its real output is a contact sheet for a human to
look at, and none of its **design** judgements gates.

**`--deliverable` is the exception, and it is a pre-delivery step, not a repo
check.** Run against a file you are about to hand over, it exits non-zero on the
things a rendered page can be wrong about decidably. **The code's
`deliverable_verdicts` is the list, and `references/eval-inventory.md` renders
it** — this sentence enumerated twelve findings while the code carried
fourteen, and five files counted it four different ways (ten, twelve, fourteen,
fourteen), which is what a hand-kept enumeration of a growing list does. Focal weight, column balance, caption distance, centerpiece scale,
empty band and the part-opener count stay reported, because the fix for each is a
design decision and a number satisfiable without improving the page ends the
looking. Without the flag nothing here gates and the behaviour is unchanged, so
the repository's own "no design judgement blocks" stays true.

*Provenance: a deliverable with overlapping text, an overspent reserve and a lost
datum was recorded `pass` by the conformance harness, because the harness scored
prose and design and **never ran the one instrument that renders the page**. Five
of the findings above fire on it. A gate nothing invokes is not a gate.*

| Probe | Reports | What it caught |
|---|---|---|
| **aspect** | the page box at window shapes that are **not** the design geometry | 30 of 30 pages were 4:3 in a 4:3 window |
| page height | pages whose rendered height differs from the geometry's | the first thing to read |
| content spill | content against the page box, now the box is fixed | the blind spot locking the geometry created |
| caption attachment | the gap between the drawing and its number and name | 95–205px, a reader asked why they were separated |
| caption axis | the caption's centre against the drawing's ink centre, as a share of the drawing's width | a rule that had said "align left" for eleven releases while the CSS aligned to the cell |
| **figure viewBox** | a viewBox the browser cannot parse — **gates** | three numbers instead of four: legal as an attribute, discarded as a value, and a six-row figure rendered three rows with every check green |
| **figure clipped** | ink drawn outside a figure's own viewBox — **gates** | a sentence 221 units past the right edge on a handbook page, invisible with no overflow, no collision and no spill to catch it |
| source echo | a page citing the same source under the figure and in the footer | 11 pages, 2 word for word |
| two tables | a page carrying more than one table | one page, and its rows could never align |
| **D12 commercial footer** | handling terms and origin on every page — **gates** | a commercial requirement, not a design judgement |
| title reserve | what a `.lede`'s children need against what the block reserves | a four-line title in a two-line reserve |
| **content hidden** | a clamp or a hidden overflow inside a title block | three of four title lines and half a sentence never rendered |
| unshipped scope | uses of `.k` / `.v` outside the `.band` / `.lead` the tokens define them in | five renderings each, invisible to a scoped role audit |
| frame | footer and composition sharing one width and centre | a dead band down 28 of 28 pages, visible only off-geometry |
| column tops | top-edge skew between side-by-side cells | 12 of 15 pages, from a rule that had never once applied |
| column weight | ink-area ratio between siblings | one column at 9.1:1 against its neighbour |
| focal | largest element against body copy; pages with neither that nor a dominant drawing | 24 of 28 pages had nothing above body copy |
| captions | caption word count, and sentences repeated elsewhere on the page | 124 words under one figure; another repeating its own page |
| tables | tables by digit density | 14 of 16 tables held prose, not values |
| figures | share of pages built on a drawing | 9 of 28 |
| centerpiece scale · aspect · empty band | what "too small" and "looks empty" mean geometrically | — |
| **one role, one rendering** | distinct computed renderings per repeated role, per geometry | a callout at 12 / 12.5 / 13.5px, and the same callout at three sizes again in portrait only |
| one datum | where content begins, across the pages of a geometry | ten different heights while every title started level |
| component colour · band baseline | one colour per chart component; type sharing its edges inside a band | two comparison bars in two greens |
| **NOT MEASURED** | any check whose subject is absent — the only thing here that sets a non-zero exit | eleven affirmative lines about a document with zero pages |

**A probe that establishes the condition it verifies proves nothing**, and this
is the one to read first. The page-height probe set the viewport to 1280x720 and
measured the page against `window.innerHeight` on a page that was
`min-height:100svh` — zero by construction, on every page, in every run since it
was written. It reported success for two releases while the deck was 4:3 in a
4:3 window. Before trusting a probe, construct the failure; if you cannot, it is
measuring its own setup.

**Its twin: a probe whose subject is missing must not report a pass.** Every
reassuring line above was written as the `else` branch of a defect test, so it
also fired when nothing had been examined — "one horizon on each of 0 pages",
"all 0 pages hold 16:9". Absence of vocabulary is not absence of defects, and
the failure is worse than a false negative because it arrives phrased as
success. Construct the *empty* case as well as the failing one: run the probe on
a document it cannot read and check that it says so.

**A probe is only as good as its vocabulary.** Every one of these reads the DOM
through a selector list, and a selector that does not know a block class reports
its column as empty and its neighbour as misaligned. Adding a block pattern to a
deliverable means adding it to `INK`. Two probes were wrong within a day of being
written for exactly this reason, and a third counted a table stretched to 100% of
its cell as a "dominant figure" — D7's own failure, reproduced inside the tool
built to replace it.

Provenance: the prose metrics made the prose half of this skill checkable while the design
half stayed a reading task, and a deck that passed every prose metric came back
from its reader with seven defects. Four were arithmetic the whole time. Run
`check_design.py` on the 0.1.337 deck and it reports 32 contrast failures, 17
sub-floor type sizes, four pages over the callout budget on 51.9% of pages, and
two footer gaps — which is the reader's list, in numbers, before they had to read
anything.

## Human dimensions C1–C7 (tick evidence items; do not rate an impression)

*Serves: **P-2**.* · id `ER-2`

Each dimension scores 1–5, but **the score is arrived at by ticking binary
evidence items**, not by forming an impression. Two measurements say why:
fine-grained binary checklists agree with human judgement far better than
holistic scoring does, and LLM judges are reliably fooled by fluent verbosity.
So the items **count things**; they do not rate feelings.

Three rules come before the list:

**Only what a machine cannot decide is on it.** Items a gate already holds are
struck through and name the gate. Asking a reviewer to re-check something already
gated spends the scarcest resource in this process on nothing.

**Scoring and release are different questions.** C1–C7 score quality. P-5 and
P-6 are pass/fail and are decided at the pre-delivery gate, not here. The
dividing line is **decidability**, not importance — every clause from P-1 to
P-5 is a MUST. "Did it leak" is a decidable binary fact; "how well sourced is
it" is a matter of degree.

**Each item says whether it can run at the outline stage**, marked `[outline]`.
Those are what a storyline review can check before the document exists.

### C1 · Governing message (answer-first) · parent `GOAL`

| Evidence item | Decided by |
|---|---|
| ① the governing statement can be quoted in one sentence from the first content page | human · `[outline]` |
| ② the reader knows which question the evidence serves before it appears (SCQA or answer-first both qualify) | human · `[outline]` |
| ③ the executive summary is one page and reads in two minutes | human |
| ④ each summary point maps to a body section, in the same order (countable: N=N, order matches) | human · `[outline]` |
| ⑤ no summary point states only a quantity ("there are three problems") without saying what they are | human · `[outline]` |

### C2 · Storyline integrity (titles read as an argument) · parent `GOAL` · whole dimension runs at outline stage

| Evidence item | Decided by |
|---|---|
| ① title read-through: the titles in order read as an argument with no gap, repeat or jump | human · `[outline]` |
| ② topic-label titles ("Market overview") in the argument body: count is zero | human · `[outline]` |
| ③ each group is 2–5 claims of one kind at one level, and the reviewer can state the ordering logic | human · `[outline]` |
| ④ MECE spot-check: try to name an overlap or a gap in any group; record found / not-found | human · `[outline]` |
| ~~⑤ rendered titles fit two lines~~ | **held, by a better measure**: `reserve_overspent` asks whether a title overruns the height reserved for it. **Counting lines is the measure that folded every title in half**, and it does not come back |

### C3 · Page argument (vertical logic) · parent `P-2` + `P-4`

| Evidence item | Decided by |
|---|---|
| ① one claim per page: no second independent conclusion can be stated | human |
| ② the title's assertion, including any number in it, is verifiable from evidence on that page | human (**the hold on figure-text hallucination**; C3 asks about the same page, C4 about the outside source) |
| ③ so-what test: every element can be tied to the title in one sentence; orphan elements count zero | human |
| ④ the figure form matches the comparison the title makes | temporarily human → machine once the shape vocabulary lands |
| ⑤ a non-data figure's family semantics hold in the content (a funnel decreases, a 2×2's axes are independent) | temporarily human → machine once the shape vocabulary lands |
| ⑥ **each figure reads without the body text**: the title states the conclusion, axes and units are present, the legend is legible, magnitudes are stated | human |

### C4 · Evidence and sourcing discipline · parent `P-2`

| Evidence item | Decided by |
|---|---|
| ① the source line names a dataset or report, not "analysis" | human (existence is held by D6; **whether it names anything is not machine-decidable**) |
| ~~② one quantity, one value across the document~~ | **held, reported**: M13. It anchors on a repeated two-word noun phrase and looks forward for the number; a qualifier anywhere near either mention (a year, a quarter, target/actual, a region) silences it, because those are different quantities rather than a contradiction |
| ③ estimates and forecasts are visibly distinguished from actuals, with the key assumption stated where the estimate appears | human |
| ~~④ share of argument titles carrying a number~~ | **held**: M1 (reported) |
| ⑤ limits and boundaries appear where the reader meets them, not only in an appendix | human |

### C5 · Type completeness · parent `GOAL` · declarable, never gating

Completeness is **reported**, and the document may **declare** a deliberate gap.
That third option is what every regulator that mandates structure actually
chose: the requirement is that an absence be **declared**, not that the section
exist. A declaration is a reader-visible scope note carrying `data-omitted`:

```html
<p class="scope-note" data-omitted="competitive landscape">This report excludes
competitive landscape analysis: it was commissioned separately.</p>
```

**Reader-visible is the point.** Every precedent prints the declaration for the
reader, and that is where its effect comes from; a marker only the checker can
see would do nothing but silence the checker.

**Existence may be mandated; naming almost never is.** A checker that decides
whether a section exists by grepping headings would be enforcing the one thing
those standards explicitly decline to enforce.

| Evidence item | Decided by |
|---|---|
| ① checked against the typical structure for that storyline | human · `[outline]` · report only |
| ② supporting material is in an appendix; the body has no padding | human · report only |
| ③ status documents: every red or amber item is paired with a specific ask | human · `[outline]` · report only |
| ④ the ending is a next step with an owner and a date, not a restatement | human · `[outline]` · report only |
| ~~⑤ navigation exists (page numbers, agenda)~~ | **half held**: page numbers by D6; **agenda and tracker existence is checked by nothing today** — mechanisable, not built |

### C6 · Actionability and decision focus · parent `GOAL`

| Evidence item | Decided by |
|---|---|
| ① every recommendation names an actor, an action and a time or magnitude | human · `[outline]` |
| ② the document says what it asks of the reader (approve / decide / fund / note) | human · `[outline]` |
| ③ the main risk or counter-argument is named and answered | human |
| ④ recommendations carry a success measure or checkpoint | human |
| ⑤ **write down one question** a decision-maker would certainly ask that the document does not answer; if none can be written, this passes | human |

### C7 · Professional finish and reader efficiency · parent `P-3` + `P-1` + `GOAL`

It is the only dimension that looks at the document from the reader's time
rather than from the argument, which is why it is separate. Reader efficiency
belongs to the product's purpose, hence `GOAL` among its parents.

| Evidence item | Decided by |
|---|---|
| ① any page is understandable in about sixty seconds (time five sampled pages) | human · sampled |
| ② terminology is stable: each key concept has one name throughout (check three) | human · sampled |
| ~~③ placeholders and draft markers~~ | **held**: D14 (gates) |
| ~~④ layout consistency (≤2 typefaces, restrained palette, alignment)~~ | **half held**: palette by D4 and D20; **there is no font-count check** — mechanisable, not built |
| ~~⑤ plain-language baseline~~ | **held**: M4, M8, M9. Register as a whole goes to the **judge-finding layer** (`scripts/ops/judge_findings.py`): a language model may point at a sentence and say what is wrong with it, and **every finding carries a quotation that must appear in the document** — a model that cannot produce the sentence it objects to has not found anything. No scores, and never gates |

## Review protocol (the iteration engine)

0. Before any of this, run the checks against the artifact:
   `check_prose.py` (English), `check_design.py` (any HTML), and
   **`inspect_layout.py --deliverable`**. **A clean dash-and-banned-phrase run is
   not a language pass** — M12 is the metric that answers whether an English
   deliverable is in English, and it is `n/a` unless the document says which
   language it claims. Step 1's self-score is a claim about a
   document, and a claim made before the instruments have run is a guess. An
   agent that cannot execute them names the checks it owes and the operator runs
   them — see the capability tiers in `CLAUDE.md`;
0b. **The red-team pass** (storyline-templates, shared discipline): before
   self-scoring, read the draft as its most skeptical reader — overstated
   claims, the first number they would check, pages designed past their
   content. A self-score written before the red team has read the document is
   the builder grading the builder;
1. Ship with a self-score attached (**never self-score 5 before a reader has
   scored it** — mistaking mechanical completeness for reader value is a
   documented, once-punished failure). **A self-score carries its reasons**: the
   number alone tells a reader nothing they can argue with, and the reason is what
   a divergence gets measured against in step 3. Say what the page does that earns
   the score and what it fails to do that caps it;
2. Readers score against the anchors with a one-line comment each; slide decks
   embed the scoring table as the final page; long documents use a standalone
   review form;
3. **Any dimension diverging ≥2 points forces a retrospective**: name the root
   cause (what the self-score missed / which rule is absent);
3b. **A dimension where the reader found a defect the author claimed to have
   verified cannot be self-scored above 3 in the round that fixes it.** The
   author already believed it was better than that and was wrong, so the next
   number needs evidence from a reader, not from the fix. Scoring is not a
   summary of effort spent. (Field-tested twice under the previous dimension set H1–H6, which C1–C7
   replaced: H2 — now C2 and C3 — was self-scored 4 while four of a reader's
   seven defects sat in it, and H3 — now C3 — was self-scored 4 in the round
   that shipped a clipped figure.)
4. The retrospective produces one of three outcomes: a rule revision (CHANGELOG +
   version bump) / an anchor revision (anchors can be wrong too) / a recorded
   no-change with reasons. **Record the round in `reviews/scores.json`** — release,
   genre, six self-scores, six reader scores, outcome — and read the series back
   with `python3 scripts/ops/review_scores.py`. Until 0.1.390 this loop had no memory:
   every score lived as a sentence in a release note, so no dimension could be read
   over time and nobody could say whether the loop was working. The store carries
   **no free-text field**, which is not an omission — a scores file is the shape
   that walks a client name into this repository, and reasons belong in
   `CHANGELOG.md`, which is already written under that red line. **A no-change is written down like the other two**,
   because the alternative is a decision nobody can find later and a question
   that gets re-opened by the next person to notice the same number;
5. The same lesson appearing across 2 documents → promoted to a formal rule.
   **This binds a probe as hard as it binds a rule.** A finding that turns out
   to be a false positive on one document is not grounds for reshaping the check
   that raised it — 0.1.372 declined to change the column-top probe on exactly
   that reasoning, having diagnosed all three of its findings on one deck and
   watched a second deck produce none.

## Known genre distortions (never chase the score)

Figure fragments concatenate into false run-ons when a deck is parsed as prose, so
**M8's overlong tail** is unreliable on decks: measure it on body copy only rather
than skipping the metric. When a metric is genuinely distorted, **note it and skip
it** — genre adaptation is the metric's debt, not the document's.

**M8 as a whole is never skipped, and neither are M9–M11.** M8 used to be
one-tailed and marked advisory for decks: it counted only sentences that ran too
long, so prose in which every sentence is uniformly clipped — the dominant modern
AI tell, and what §5 used to mandate outright — scored a perfect zero. The
variance floor is the half that matters, and it is the half that was missing.

**M1 is not distorted and is never skipped.** A deck's page titles are precisely
where its claims live, so a low assertive-title rate on a deck is a real defect,
not a genre artifact. (Lesson: M1 was waived for decks as "advisory", which
removed the only metric that would have caught deck titles collapsing to bare
antitheses — the regression ran for three versions unmeasured.)

**Measured always, gating never — and those are different things.** 0.1.390 gave
M1 code for the first time, and it REPORTS. This is not the waiver above
returning in another costume: that waiver stopped measuring decks, and this
measures every document and prints the titles it doubts. What it declines to do
is fail a run on a REGEX PROXY for a judgement. "Names a subject and carries a
verifiable fact" is not decidable, so the script tests for a numeral, a named
entity or a dated term — and a metric that gates gets satisfied, which for a
title heuristic means writing titles the regex likes. That is how the page-fill
floor was met in 0.1.339 and why it was withdrawn in 0.1.340. The number is
information for a reader, who overrules it. It is promoted to a gate only if a
review shows it caught something a person did not, which needs two releases of
real documents read against it.

**M2 and M6 do gate**, because their predicates are decidable: a marker from a
stated list is either in the window or it is not. Both windows are defined in
`writing-rules.md` §4 rule 6 rather than only in code, and `check_repo.py`'s
`source-marker parity` guard holds the script's list to the rules' — the same
discipline as the ban list, added because a metric that invents its own
vocabulary is a second rule nobody wrote down. What M6 exempts is defined
there too, and for the same reason: the script had been deciding "label or
range" on a length nobody had written down, and it reworded a correct sentence
in a shipped document before anyone noticed the rules never mentioned a length
at all.
