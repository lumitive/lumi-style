# The figure data contract — the complete plan

> Design record, 2026-09-01. **This is the whole plan in one file.** It replaces
> `2026-08-31-figure-chain-design.md`. **That file was never committed, so the
> claim "its content is folded in below" cannot be verified by anyone, now or
> later — the merge destroyed its own audit trail.** What IS verifiable: the
> chain, the four prerequisite changes, both review rounds' findings, and the
> refusals are all present here, and a keyword sweep found two items lost in
> the merge (the evidence obligations), restored as rows 21 and 23. Two red/blue review rounds
> are recorded in §5, §6 and §8, and every claim was verified against the
> shipped code and the owner's real deliverables before it was written here.
>
> **§12 is the execution checklist.** It is the only place that says what
> "done" means, and every item on it is machine-checkable.

## 1 · What the owner asked for

Three statements, given over one session, which are one requirement:

1. **Build the foundation for data figures and professional number display INTO
   the scaffold**, so it is designed the moment a requirement arrives rather
   than reworked when a gate fires.
2. **This must not relax gate enforcement.**
3. **All business display figures must live in one unified directory** — "the
   current scattering and non-handling IS 100% omission and forgetting in
   actual use" — and *directory, processing and guard must all be unified*,
   with a later correction that those three words may be incomplete: what she
   means is **the complete chain**.

## 2 · A recorded process failure, so it is not repeated

This design was scoped down twice under no new evidence, by the author:

- The whole-chain analysis produced four changes. They were approved.
- One of the four (a prose-scanning guard) failed its first predicate — 2 false
  positives, 1 false negative — and the author **dropped the requirement**
  rather than the predicate, cutting four changes to three.
- The remaining three were then summarised as "make the scatter tool ship",
  which is one file.

A whole-chain optimisation became one file, and the owner stopped it. **A
predicate that fails is a reason to change the predicate.** The second attempt
(§7, change D) narrows the SCOPE the predicate runs over rather than abandoning
it, and measures 0 false positives, 0 false negatives, 2 true findings. That
result is what the first attempt would have reached by iterating.

## 3 · The goal, restated exactly

> Build the foundation for data figures and professional number display INTO the
> scaffold, so it is designed the moment a requirement arrives — **not reworked
> later when a gate or a red line fires**. This must not relax enforcement.

Asked to double-confirm whether the four prerequisite changes (§8) achieve that,
the honest answer was **no — about 25%**. They make the drawing tools reachable.
They do not make a single figure declare what it draws. §9 is the rest, and §12
is how completion is checked rather than asserted.

## 4 · THE CHAIN — the shared basis for this and every later figure change

This is the agreed picture of what a business data figure's life *is*. Every
change in this document, and every later one, is located on it. Thirteen links,
**nine broken**, verified individually against the shipped code and the owner's
real deliverables. Every break sits in one region: between *the data exists* and
*the drawing is made from it*.

```
REQUIREMENT ─┬─ 1  an entry that receives the data                        BROKEN
             │
PLAN ────────┼─ 2  the analysis beat: move / finding / implication         ok
             ├─ 3  the data captured in the move's own input shape        BROKEN
             │       AR-1 has said since it was written that compare needs
             │       "one value plus at least one reference value".
             │       Nothing reads it.
             │
CHOICE ──────┼─ 4  the registry says which tool draws it                  BROKEN
             │
MATERIAL ────┼─ 5  the shape library, the geographic data                  ok
             │
DRAW ────────┼─ 6  a renderer exists                                       ok
             ├─ 7  something calls it                                     BROKEN
             │       shipped 0.1.664; zero callers
             ├─ 7b the reader actually has it                             BROKEN
             │       a published rule names a script the package omits
             ├─ 8  changing the data redraws the figure                   BROKEN
             │       the author pastes SVG; there is no input to re-run
             │
SURVIVAL ────┼─ 9  a rebuild inherits the figure's data                   BROKEN
             │       convention 17's measured case: eleven facts lost
             ├─ 10 a second language redraws the figure                   BROKEN
             │       localize.py copies and marks; touches figure text 0 times
             │
CHECK ───────┼─ 11 the numbers agree with the fact contract              BROKEN
             │       the contract has no `## FACTS` heading, so all 62 lines
             │       are scanned as the permitted set; the deck states 43
             │       quantities the contract does not list — and that is the
             │       clause that GATES (red line 1). `--facts` is an optional
             │       flag on `build.py`, not a step.
             ├─ 12 the drawing is graded                                BROKEN
             │       D21 holds 1 of 58 figures. `figure_distorts` needs two
             │       marks carrying `data-datum` and two of the three
             │       deliverables have zero. `figure_axis_named` GATES and
             │       fires without a declaration — but all fifteen
             │       number-scaling figures carry zero `.axname-*`, and all
             │       three documents predate its `since`, so it has never run
             │       against this corpus at all.
             └─ 13 the rules reach all twelve platforms                    ok
```

**Ten links are marked broken above: 1, 3, 4, 7, 7b, 8, 9, 10, 11, 12.** The document said
"nine" in four places and enumerated a different nine in two of them — an audit
caught it. The set is fixed here and every later count refers to THIS list:
**{1, 3, 4, 7, 7b, 8, 9, 10, 11, 12}**, ten links, one root cause — nothing holds a
figure's data. Where an earlier sentence says "nine", it is counting the nine
this plan can act on and excluding **link 4**, which §11 records as closed by no
step.

*Links 11 and 12 were marked `ok` in the first draft of this document and were
wrong. Verifying them against real deliverables — which is what the owner asked
for, on the grounds that the chain is the basis of every later decision —
moved both. The correction ENLARGES the root cause rather than weakening it:
the data contract and the fact contract are both "checked only where declared",
and with no artefact holding a figure's data, one idles at 1.8% and the other
is not on the build path at all.*

Because no such artefact exists: intake has nowhere to put the numbers (1), the
beat has nothing to point at (3), the registry has no reason to name a tool (4),
the renderer has nothing to be *called with* (7), there is nothing to redraw
from (8), nothing for a rebuild to inherit (9), and nothing for a translation to
re-render (10).

The information is not missing — it is scattered across four places, none
authoritative: the CONTRACT prose, the outline's `finding:` string, a tuple
inside the author's own `assemble.py`, and the text nodes of hand-written SVG.

**So the unification the owner asked for is not primarily a directory.** A
directory puts the tools side by side. What is missing is the **figure spec**:
one file per figure holding the measure, its unit, the period, the data arranged
in the shape its analytical move requires, the reference value, and the source.
With it, the nine breaks are one repair — the drawing is generated from it, a
rebuild inherits it, a translation re-renders it, the registry names who draws
it, and the gates grade against it. The directory and the guards come after
that: the tools sit together, and none of them is unreachable.

### The same picture as a table, with the evidence for each verdict

| # | Link | State | Evidence |
|---|---|---|---|
| 1 | The requirement and its data arrive | **broken** | `brief.py` has no `--data`/`--facts` input; the numbers exist only in the agent's context window |
| 2 | The plan declares the analytical move | ok | AR-3's beat: `analysis: <move> \| finding: … \| implication: …` |
| 3 | The data is captured in the move's own input shape | **broken** | the beat has no `data:` field. AR-1 already declares an input shape per move and nothing reads it |
| 4 | The registry says which tool draws it | **broken** | `assets/frameworks.json` has no `tool` key on any of its 14 entries |
| 5 | The material exists | ok | the 206-unit shape library, the geo data |
| 6 | A renderer exists | ok | `scripts/render/scatter_svg.py`, shipped 0.1.664 |
| 7 | Something calls it | **broken** | zero importers. The only mentions are prose and one comment |
| 7b | The reader has it | **broken** | it computes to the DEV side; the published package does not contain it, while a published rule names it |
| 8 | Changing the data redraws the figure | **broken** | the author pastes SVG; there is no input to re-run |
| 9 | A rebuild inherits the figure's data | **broken** | convention 17's measured case: a rebuild silently dropped eleven facts |
| 10 | A second language redraws the figure | **broken** | `localize.py` copies and marks; it touches figure text zero times |
| 11 | The numbers agree with the fact contract | **broken** | the contract carries no `## FACTS` heading, so all 62 lines are scanned as the permitted set; the deck states **43 quantities the contract does not list**, which is the clause that gates (red line 1). `--facts` is an optional flag on `build.py`, not a step |
| 12 | The drawing is graded | **broken** | D21 holds 1 of 58. `figure_distorts` requires two `data-datum` marks; two of three deliverables have zero. `figure_axis_named` gates but has never run against this corpus — 15 number-scaling figures, zero `.axname-*` |
| 13 | The rules reach every platform | ok | DR-20 in `design-rules.md` and `prompts/lumi-style-core.md` |

Consequences, measured on the owner's own material:

- **57 business figures across three real deliverables; 1 declares its data.**
- **355 delivered pages; 0 carry a declared analytical move**, although the
  outline declares 17 of 17 and the scaffold emits all 17. `assemble.py:948`
  deletes the scaffold's content run and pastes hand-authored pages.

## 5 · Root cause

**No artefact holds a figure's data.**

One absence produces nine breaks: there is nothing for intake to receive (1),
nothing for the beat to point at (3), no reason for the registry to name a tool
(4), nothing to call the renderer *with* (7), nothing to redraw from (8),
nothing for a rebuild to inherit (9), nothing for a translation to re-render
(10), nothing letting the fact contract bind a number to the page that draws it
rather than to a bag of scalars (11), and almost nothing for the figure gates to
grade (12).

The information exists — it is scattered across the CONTRACT prose, the
outline's `finding:` string, a tuple inside the author's `assemble.py`, and the
text nodes of hand-written SVG. Four copies, none authoritative.

## 6 · What was considered and rejected, with evidence

**Moving 12–13 figure files into one directory.** The owner's diagnosis is
right; this does not treat it. Three verified reasons:

- `sea_route.py` contains **zero** `svg`/`<path>`. It emits JSON coordinates —
  a router that keeps a lane off land. Filing it under `figures/` is a factual
  error, not a taste call.
- The twelve split **exactly 6 consumer / 6 dev** under the package's own
  `shipped.py`. Every embedder is consumer, every asset builder is dev, the
  drawers split. The directory boundary would sit at 90° to the boundary that
  governs what ships.
- The live defect is a **cross-boundary reference**: a published rule names a
  script the published package omits. After the move that reference is still
  cross-boundary. Nothing improves.

Additionally, `scripts/lib/shipped.py`'s path resolver matches `scripts/<one
segment>/<file>.py` only, so a *nested* figure directory would remove these
files from the one guard that prevents silent omission — committing the owner's
complaint while claiming to fix it.

**Deferred, not refused:** one flat directory with verb prefixes
(`build_*`/`draw_*`/`embed_*`) is a legibility improvement worth its own design
record. It is not a reachability fix, and conflating the two is what made the
guard unsatisfiable in the first draft.

## 7 · The principle the guards must obey

AG-10, declined 0.1.663 after shipping for one commit: *"A gate that a correct
answer cannot satisfy does not get obeyed; it gets satisfied."* Its author,
required to bind every analytical move to a library shape, bound the only
correlation-tagged near-match **without opening the SVG** — an empty axis frame
carrying one bubble.

Every guard below is therefore stated so that **each correct answer has a way
to satisfy it**: ship the tool, or reword the sentence, or record a waiver with
a reason. Only the actual defect has no path.

## 8 · Prerequisites — the four changes that make a tool reachable

*These close 2 of the 9 breaks. They are necessary and nowhere near sufficient; §9 is the part that closes the other seven.*


### A · The renderer ships

`adapters/shipped.json` `consumer_seeds` gains `scatter_svg`. Its own comment
already scopes the list as *"consumer-facing scripts SKILL.md does not name by
path… and the two embedders the deck scaffold calls"* — a figure renderer the
scaffold calls is that class exactly.

*Closes link 7b.* Without it, change C cannot pass its own guard, which is the
point: the registry may not name a tool the reader does not receive.

### B · The registry names the tool, and the scaffold hands over a runnable path

`assets/frameworks.json` gains an optional `tool` object per framework:

```json
"tool": {"module": "scatter_svg",
         "invoke": "python3 scripts/render/scatter_svg.py --data <spec>",
         "spec": ["x", "y", "points", "source"]}
```

An object rather than a bare string for one mechanical reason, verified:
`SCRIPT_PATH_RE` scans every tracked text file except a frozen list, and
`assets/frameworks.json` is tracked and not frozen — so `invoke` carrying the
literal path gets rename protection from the *existing* guard at no cost.

**Two corrections a review made to the first draft of this section, both
verified in the code:**

1. **The sentence this change proposed to rewrite is never emitted.**
   `new_deck.py:1161` merges `shape_note` into the page hint only under
   `if shape:` — and for a natively-drawn framework `shape` is empty. So the
   "drawn natively — build it from the page's own numbers" line has **never
   reached a scaffolded deck**. It is not "a comment is not a path"; it is not
   even a comment. The emission site must change, not the string.
2. **The invocation may not go in the note.** The note reaches the page as an
   HTML comment, and `d14_placeholders` strips comments (and `<svg>`) before it
   looks. An invocation there is a slot no gate can refuse — the same failure
   one layer over. It goes in a **visible** `[TO FILL: … run <command> …]`
   line inside `div.fig`, which `D14 already gates`. This is 0.1.659's measure
   slot exactly: hand the slot over, add no new check.

**The scaffold has no data, and must not invent any.** It writes a spec file
whose structure is complete and whose data is *absent* — `"points": []`, every
field a `[TO FILL]` — at a real relative path named in the slot. Fed to the
renderer that file is refused by the renderer's own existing guard ("no point
carries both an x and a y"). IDEA-18 records that the scaffold already hands
authors four plausible numbers `D14` cannot see; this branch adds **zero**, and
that is assertable by a test scanning the written spec for any digit.

*Closes link 7. Link 4 is discussed under C.*

### C · A tool named must be a tool reachable

`check_frameworks` gains: a declared `tool` must name a module that **exists**,
**imports**, and is **consumer-side**; and `invoke` must contain
`scripts/<drawer>/<module>.py` so the two spellings cannot drift.

**Three corrections from review, each verified:**

1. **This is a DRIFT guard, not a reachability guard, and the first draft
   overclaimed it.** The `tool` field is optional, so a framework whose drawer
   is legitimately dev-only satisfies C by omitting it — which is today's state
   of every entry. After A+B+C, **1 of 14 entries names a tool**; link 4 moves
   from 0/14 to 1/14 and nothing requires the other thirteen to declare
   anything. Saying C "closes link 4" was wrong. It closes the *drift* that
   would otherwise appear the moment a second tool is declared.
2. **`shipped.consumer_scripts` RAISES** when `SKILL.md` is absent, and six
   existing tests in `tests/test_frameworks_guard.py` build trees containing
   only two JSON files. Calling it unconditionally breaks all six; calling it
   inside the existing `except (OSError, …)` misreports the failure as "could
   not read the two dictionaries" on a correct registry. **It must be called
   lazily — only once some entry declares a `tool`** — so today's fixtures never
   reach it. The new synthetic trees then need `SKILL.md` and
   `adapters/shipped.json`, which is heavier than "synthetic trees" implies and
   is stated here so it is budgeted.
3. **The arithmetic in the first draft was wrong**: the registry is 8 entries
   binding shapes and **6** drawn natively, not 5. That is 14.

**FM-24 at this guard's own layer.** Before B lands, no entry declares a tool
and C returns `[]` — byte-identical to a clean registry. So C ships with a
fourth answer from day one: a note reading *"14 entries declare no tool at all —
no tool reachability was checked, which is not the same as every tool being
reachable"*. The note is present at C's step and absent after B's, and both are
asserted.

### D · A rule may not name a tool its reader does not have

**This revives a mechanism declined in writing, and that must be said first.**
`FAILURE_MODES.md` FM-23 — *"A prose guard over cross-boundary references"* —
was **DECLINED 2026-08-23**, proposing exactly this: *"extend
check_cross_boundary_paths from Python to markdown, so a consumer document
naming a development path fails."* Its reason is one case: `README.md:88` names
a development-side file **and says "in the development repository" in the same
sentence**, which is the right way to refer to something a reader cannot open.
A guard that cannot tell an attributed mention from an instruction *"would fail
correct prose and instruct the author to delete a useful reference"* — the
wrong-gate-edits-prose failure this repo has on record twice.

**What changed is the scope, not the evidence.** FM-23's counterexample is a
README. This guard's scope is **the rule prose an agent is told to follow** —
files under `references/`, `SKILL.md`, `AGENTS.md`, `prompts/` — and a README is
not one, so **the guard never has to judge attribution at all**. FM-23's
objection is answered by removing the case rather than by teaching the guard to
read English, which is the AG-1/FM-23 class this package refuses twice over.
Per convention 2 and FM-15, FM-23's entry is amended in place when this ships:
it is not left standing as declined while the thing is running.

**The scope is decidable, and is not a hand-written list.** The definition of a
rule file already exists in `check_rule_coverage.py` under its own comment "A
RULE LIVES IN A RULE FILE" — that constant is reached, not retyped
(convention 19). Generated indexes are excluded **by the banner their own
generators emit**, line-level, so a fourth generated file needs no list edit and
a banner that stops matching brings the file back into scope loudly. Measured
both ways: 15 files with a file-level exclusion, 17 with the line-level one, and
**both give the same two findings**. The line-level rule ships, because a
hand-maintained subset is the failure `release.py`'s own docstring records
happening three times.

**Measured on today's tree: 2 findings** — `references/design-rules.md:171` and
`:1057`. That is the deliberate red, and it is not planted: it is the tree.

**What this guard does NOT see, stated because the first draft claimed "0 false
negatives" and that was false.** The predicate keys on the literal
`scripts/<drawer>/<name>.py`. Inside the same scope, verified: **9** mentions of
dev-only tools by bare filename (`` `check_repo.py` `` and kin) and **7** of
dev-side files (`` `CLAUDE.md` ``, `` `KNOWN_GAPS.md` ``, `reviews/scores.json`)
send the reader to material they do not have and are invisible to it. So the
honest claim is: **2 findings of the path-literal shape, 16 further
cross-boundary references the predicate cannot see.** Saying "0 false negatives"
described the predicate's own reach as if it described the requirement — FM-24,
at the guard layer, committed by this document. Widening to bare filenames is
NOT proposed here: `check_repo.py` as a bare name is ambiguous with prose and
would reopen exactly FM-23's objection. It is recorded as known, unclosed.

**Three honest repairs per finding**, and one is already proved available:
`prompts/lumi-style-core.md` carries DR-20's content with no tool path at all,
so "state the fact without the path" is costless — meaning D does not depend on
A. Note also that repairing `design-rules.md:171` **must not change the file's
line count**: 230 of `evals/rule-coverage.json`'s entries for that file sit
below line 171 and each pins a quote to an exact line.

## 9 · THE ARTEFACT — the figure data contract

One file per figure, at `figures/<page-id>-<framework>.json` beside the deck.
It holds what a reader needs before they can read the drawing, and nothing else.

**The universal half** — required of every spec, because these are the six
things `references/design-rules.md` DR-20 and `writing-rules.md` WR-5 already
demand of any figure that carries a number:

```json
{
  "measure": {"name": "...", "unit": "..."},
  "period":  "FY2025",
  "reading": "the direction, in words",
  "cause":   "direction not tested",
  "source":  "where these observations came from",
  "move":    "compare"
}
```

**The move half** — the shape AR-1 has declared since it was written, now
readable. This is the whole reason the schema is per-move rather than one flat
series list: `f-data`'s `{"series":[{"label","value"}]}` **can express none of
the five**, which is why M-D deferred extending it and why this is a new
artefact rather than a revision of that one.

| move | AR-1's input shape | the spec's fields |
|---|---|---|
| compare | one value + ≥1 reference value | `subject: {label, value}`, `references: [{label, value}]` |
| decompose | a total and its parts | `total: {label, value}`, `parts: [{label, value}]` |
| position | items scoreable on two dimensions | `axes: {x:{name,unit,low,high}, y:{…}}`, `items: [{label,x,y}]` |
| correlate | paired observations | `x/y: {name,unit}`, `points: [{x,y,size?,series?}]` |
| bridge | a before, an after, attributable pieces | `before/after: {label,value}`, `pieces: [{label,delta}]` |

**The judgment anchor becomes structural.** WR-5 rule 0 — *"a key number carries
its judgment anchor"* — is unchecked today, `rule-coverage` RC-448
`metric: null`, no candidate. Under this schema a `compare` spec **without a
reference value cannot be drawn**: the renderer refuses it, naming AR-1. Not a
new gate; an input shape. The anchor exists or the figure does not.

### 9.1 · The lifecycle

```
REQUIREMENT ──► the author writes the numbers into the spec
                  (the first place in this package where they can be written)
       │
PLAN ──┴──────► the beat points at it:  data: figures/p5-compare.json
       │
SCAFFOLD ─────► writes the SKELETON: every field present, "parts": [],
       │        every value a [TO FILL].  ZERO numbers invented.
       │        The page carries data-figure-spec="…" and a visible
       │        [TO FILL: fill <path>, run <command>] slot that D14 gates.
       │
DRAW ─────────► the tool reads the spec and emits the SVG, with
       │        data-datum per mark, .axname-x/.axname-y, the source
       │        line inside the drawing
       │
CHECK ────────► the browser gate re-derives geometry INDEPENDENTLY and
       │        measures rendered pixels;  check_facts compares the spec's
       │        values against the permitted facts
       │
REBUILD ──────► the spec is an input file; the rebuild reads it.
TRANSLATE ────► translate the spec's labels; redraw. The geometry is
                identical by construction.
```

### 9.2 · Why this is not self-satisfying

The standing objection, recorded twice in `check_design.py`'s own comments and
once as a metric removed before shipping: **a tool that draws from a dict and a
checker that verifies against the same dict agree by construction**, while the
gate's subject climbs and the board reads as coverage.

Two verifications survive that, and both are used here:

1. **The browser proportion gate** (`inspect_layout.py`). It re-derives the
   expected length with a **second implementation**
   (`expected = top.r[dim] * (m.v / top.v)`, or `sqrt` under
   `data-encoding="area"`) and measures the **rendered pixel** — a third party
   the generator does not control (viewBox, `preserveAspectRatio`, stroke,
   clipping). It caught this author's own area-encoding error one release ago:
   small marks overstated 23%.
2. **The fact contract** (`check_facts.compare`). `unsourced = document
   quantities − contract quantities`, over **two independently authored
   sources**. The spec's values are checked *against* the contract.

**The spec must never BE the contract.** One source makes `unsourced` empty
forever and red line 1's only instrument goes blind. The contract is written
from the engagement; the spec is written for a figure; the check is that they
agree.

### 9.3 · What gates, and what does not

**Nothing mandates that a figure have a spec.** Schematics, 2×2s, the globe and
icon rows are correct answers that cannot satisfy such a demand — AG-10, which
this package declined after shipping it for one commit and watching its author
bind a wrong shape to satisfy his own guard.

What gates is the **contradiction class only**, target always zero:

- a page declaring `data-figure-spec` whose file is missing or unparseable
- a spec whose move does not satisfy AR-1's input shape for that move
  (a `compare` with no reference, a `bridge` whose pieces do not reconcile
  before → after, a `decompose` whose parts do not sum to the total)
- a drawn mark out of proportion to its declared value (existing gate)
- an unfilled `[TO FILL]` reaching the reader (existing gate)

The arithmetic ones are the prize: **a decompose spec whose parts do not sum to
its total is a genuine assertion about the author's data**, not about the
drawing. No existing check can make it, because no existing artefact holds both
the total and the parts.

### 9.4 · Reach — stated, not assumed

| tier | count | what it gets |
|---|---|---|
| runs scripts | 10 | the scaffold writes the skeleton, the tool draws, the gates grade |
| one pasted context | 2 | the **rule** — the spec's fields as prose in `prompts/lumi-style-core.md`, so an agent writing SVG by hand still states measure, unit, period, anchor, source, and direction |

Prose reaches 12/12; a Python renderer reaches 10. That split is the package's
existing shape (DR-20 and `scatter_svg` already ship it) and is not new debt.

### 9.5 · What this cannot reach, and why the goal is not 100% by itself

**`355 delivered pages, 0 carrying a declared analytical move.`** The scaffold
emits all 17 declarations for a 17-beat outline; the author's own `assemble.py`
— in her deliverable repository, **not in this package** — replaces the entire
content run with hand-written pages. No change in this repository can move that
number.

What this package can do, and this plan includes it: **`check_outline --against`
reports the loss** — *"the outline declares N analytical moves; the document
carries M"* — about ten lines, no gate, language-blind. Today that deletion is
invisible; after, it is a line in every build that uses an outline. The repair
is the author's, and it becomes a repair they can see.

Stating this is the honest boundary of the claim. A plan that promised the 355
would be promising something it cannot do.

## 10 · What this does NOT do, and why

- **No mandate that a figure declare data.** Schematics, 2×2s, the globe and
  icon rows are correct answers that cannot satisfy it — AG-10.
- **No tool-generated `f-data` graded by D21.** Drawing and checking from one
  dict makes agreement true by construction while D21's subject climbs from 0
  to N and the board reads as coverage. `check_design.py:2839` records this
  self-satisfaction twice. The only non-circular verification is
  `inspect_layout`'s: a second implementation re-derives the expected geometry
  and measures the rendered pixel — it caught this author's own area-encoding
  error one release ago (small marks overstated 23%).
- **The figure spec must never double as the `--facts` contract.**
  `unsourced = document quantities − contract quantities`; one source makes
  that set empty forever and red line 1's only instrument goes blind.
- **No `f-data` schema revision** (M-D, recorded as three to four releases), no
  title-number gate (M-C, refuted at 26% false positives), no measure line in
  the caption (owner ruling 2026-08-22, two gates).

## 11 · Landing order

Each step ships as its own release and is provable on its own. **No version
number is written here**: a spec that names a version it cannot define is a
promise the guard rightly refuses, and the release number is known only when
the release is cut.

| # | Step | Contents | Links genuinely closed | Cumulative |
|---|---|---|---|---|
| 1 | step 1 | the four prerequisites A/B/C/D, **FM-23 amended in the same commit**, and the `CLAUDE.md` scope question decided **before** the counts are pinned | 7b, 7 | 2/9 |
| 2 | step 2 | the contract artefact for `correlate` — universal-half schema **plus a move dispatch**, skeleton writer, `data:` pointer, `data-figure-spec`, the scatter reading it | **12** | 3/9 |
| 3 | step 3 | `compare` — `benchmark_svg` and `radar`, each shipped to `consumer_seeds` **before** its registry entry, or change C rejects it | none whole (WR-5's anchor becomes structural, which is not a chain link) | 3/9 |
| 4 | step 4 | `decompose` + `bridge` — the arithmetic moves. **`position` is scoped out**: its three entries are library-drawn with no `drawn: native`, it has no arithmetic invariant, and demanding a spec of a 2×2 is the AG-10 trap | completes **3** and **8** | 5/9 |
| 5 | step 5 | survival — `check_facts` reads specs, `localize` redraws, `check_outline --against` reports the landing rate | 9, 10; **11 only in part** | 7/9 |

**Every release additionally carries the standing rows** — 19, 20, 21, 22, 23,
24, 25, 28, 29, 42, 43, 44, 47 — and rows 30, 31 and 46 recur in steps 2 through
5, because each step adds a verdict, a rule sentence and fixtures.

**The honest ceiling is 7 of 9, not 9 of 9.** A third-party audit corrected the
first draft's arithmetic on three counts, each verified:

- **Link 4** (the registry names the tool) is credited to no step. §8 C already
  says so in its own words — after A+B+C *"1 of 14 entries names a tool… saying
  C closes link 4 was wrong."* Even at step 5 the registry reaches at most one
  `tool` per natively-drawn framework. It is not closed by this plan, and
  pretending otherwise was the arithmetic inflating itself.
- **Link 11** (numbers agree with the fact contract) is closed only in part. Its
  two named defects are that the owner's contract carries no `## FACTS` heading
  and that `--facts` is an optional flag rather than a build step. **Both live
  outside this repository**, exactly like the 355 pages of §9.5. Step 5 adds the
  comparison; it cannot add the heading.
- **Link 12** closes at **step 2**, not step 3 — both of its instruments
  (`figure_distorts`, `figure_axis_named`) are step-2 rows.

Steps 1–4 reach 5 of 9 and are worth shipping alone. **A plan that claimed 9 of
9 would be claiming two links it cannot reach.**


## 12 · THE EXECUTION CHECKLIST — the only definition of "done"

Neither of the two documents this replaces had one, and the author could not
answer *"how do you guarantee both specs are fully executed?"* because nothing
in either file could be checked. **Most rows are machine-checkable and carry
the command that checks them. Four are not** — rows 20, 24, 25 and 44 are
attested by a person, and saying "every row is machine-checkable" while four
were not is the same overclaim this document exists to stop. They are marked. A release claiming a row is done
runs the command and puts the output in its CHANGELOG entry.

### The number this plan is graded on

```
python3 - <<'PY'
import sys, pathlib, re; sys.path.insert(0,"scripts/check"); import check_design as cd
base = pathlib.Path.home()/"Documents/LUMI-Style"
newest = {}
for f in sorted(base.glob("*.html")):
    raw = f.read_text(errors="replace")
    if 'class="page' not in raw or '<div class="fig"' not in raw: continue
    if "globe-demo" in f.name: continue          # a brand asset, not a business figure
    stem = re.sub(r'\.0\.1\.\d+.*$','',f.name)
    # BY REVISION NUMBER, not by string. A plain sort puts r9 after r11, so
    # the first version of this block read a two-revision-old deliverable and
    # printed 57 where the newest carries 58 — the number this whole plan is
    # graded on, off by one, in the document that declares it the grade.
    rev = int(m.group(1)) if (m := re.search(r'\.r(\d+)\.', f.name)) else 0
    if rev >= newest.get(stem, (-1, None))[0]:
        newest[stem] = (rev, f)
figs = dec = datum = 0
for _rev, f in newest.values():
    raw = f.read_text(errors="replace")
    figs  += len(re.findall(r'<div class="fig"', raw))
    dec   += cd.d21_data_contract(raw)["declared"]
    datum += raw.count("data-datum")
print(f"figures {figs} | declaring their data {dec} | marks declaring a value {datum}")
PY
```

Baseline, 2026-09-01: **`figures 58 | declaring their data 1 | marks declaring a value 10`**.

**Two of those three terms this plan MUST NOT move, and saying otherwise was the
worst error in the first draft of this document.** `declaring their data` counts
`<script class="f-data">` blocks (`check_design.py:2551`) — and §10 refuses to
generate `f-data`, a refusal row 28 is written to protect. A plan graded on a
number its own refusals forbid it to raise is a plan that has arranged to fail
or to cheat. `figures` moves only when the owner authors a new deck.

**The grade is the third term plus one the package can actually own:**

```
marks declaring a value          — data-datum in delivered decks (owner-gated)
figures drawn from a spec        — files under figures/*.json with a page
                                   carrying the matching data-figure-spec
```

The second is the honest measure of this plan: **it counts figures whose numbers
came from a declared artefact rather than from typed markup**, it is what every
step of §11 actually builds toward, and it is zero today. The first stays,
because it is what a reader ultimately gets — but with §9.5's boundary attached:
**the package makes it movable; only the owner's rebuild moves it.** A release
that raises the second and not the first has done its half.

**This reads `~/Documents/LUMI-Style`, outside the repository.** It is not
reproducible in CI or on another machine, and that is stated rather than hidden:
the grade is a measurement of the owner's real work, which is the only place the
question means anything.

### Row by row

| # | Done means | Command that checks it | Step |
|---|---|---|---|
| 1 | the renderer is on the consumer side | `python3 -c "import sys;sys.path.insert(0,'scripts/lib');import shipped,pathlib;assert 'scatter_svg' in shipped.consumer_scripts(pathlib.Path('.'))"` | 1 |
| 2 | shipping it drags nothing else across | the consumer set grows by exactly one name | 1 |
| 3 | the registry names a tool | `assets/frameworks.json` has ≥1 `tool`, and `check_repo` `frameworks` is green | 1 |
| 4 | a declared tool is reachable | synthetic trees: missing / unimportable / dev-side / `invoke`≠`module` each fail | 1 |
| 5 | the tool-reachability guard is not vacuous | its "no entry declares a tool" note is **present** before B and **absent** after | 1 |
| 6 | rule prose names no tool the reader lacks | `check_repo` `rule script reach`: **2 findings before, 0 after** | 1 |
| 7 | a scaffolded page hands over a runnable path | the emitted HTML contains the literal command **outside** any `<!-- -->` and any `<svg>`, and `d14_placeholders` returns a finding for the slot | 1 |
| 8 | the scaffold invents no number | the written spec file matches `re.search(r"[0-9]", json.dumps(spec)) is None` | 2 |
| 9 | a spec drives a real drawing | a `correlate` beat with a real spec produces `<svg>` carrying ≥2 `data-datum` marks | 2 |
| 10 | no data changes nothing | a scaffold with no `data:` is byte-identical to today's, and `d21_data_contract(raw)["declared"] == 0` | 2 |
| 11 | the page names its spec | `data-figure-spec` present, the file exists and parses; a missing file fails | 2 |
| 12 | the browser grades the drawing | `inspect_layout --deliverable` reports `figure_distorts` **held**, not `n/a` | 2 |
| 13 | the anchor is structural | a `compare` spec with no reference is refused, and the message names AR-1 | 3 |
| 14 | the arithmetic is asserted | a `decompose` whose parts do not sum to its total is refused; a `bridge` whose pieces do not reconcile is refused | 4 |
| 15 | a rebuild inherits | rebuilding from an unchanged spec is byte-identical | 5 |
| 16 | translation redraws | a translated deck's figure geometry is identical to its source; only labels differ | 5 |
| 17 | the spec's values are checked against the facts | `check_facts` compares them; the spec is **not** the contract (`unsourced` is still computed from two independent sources) | 5 |
| 18 | the loss is visible | `check_outline --against` reports "declares N moves, document carries M" on the owner's 17 documents | 5 |
| 19 | every guard has a third answer | each new guard's could-not-look output is asserted by test to differ from its clean output | all |
| 20 | every figure was looked at | a PNG rendered and read by a person, per release | all |
| 21 | the evidence obligations are met, not discovered | `check_evidence.py --check` green. **This diff touches `scripts/ops/new_deck.py` and `references/`, so it WILL demand `scaffold-render`, `layout-fixtures` and `conformance-freshness`** — three browser/agent rounds. Budget them at the start of each step, not at `release.py` time | all |
| 22 | new rule prose is registered | every rule sentence added to `references/` or `prompts/` has an entry in `evals/rule-coverage.json`; `python3 scripts/check/check_rule_coverage.py --check` green | 1–5 |
| 24 | the directory move stays rejected on evidence | if a future session re-proposes moving figure code into one directory, §6's three verified reasons must be answered with NEW evidence, not re-argued. `sea_route` still emits zero SVG; the 12 files still split 6 consumer / 6 dev; `shipped.py`'s resolver still matches one path segment. Re-run those three checks before reopening | all |
| 25 | every new guard is satisfiable by a correct answer | for each guard added, name in its docstring the correct answer that satisfies it and the defect that cannot. A guard with no such sentence is AG-10 in the making — the failure that made its author bind a wrong shape without opening the SVG | 1–5 |
| 26 | FM-23 is amended in place, not left standing | shipping change D while `FAILURE_MODES.md` still records the mechanism as DECLINED is FM-15. The entry must say what changed (the scope) and cite this spec. `check_ledgers` holds a cited id to its ledger | 1 |
| 27 | the spec artefact is never wired to the facts contract | `check_facts.permitted()` must not read figure specs. Grep the diff: if `check_facts` gains a path into `figures/`, `unsourced` becomes empty by construction and red line 1's only instrument goes blind | 5 |
| 28 | the refusals in §10 stay refused | no release under this plan may mandate a figure declare data (AG-10), grade tool-generated `f-data` with D21, revise `f-data`'s schema (M-D), rebuild the title-number gate (M-C), or move a measure line into a caption. Each is recorded with its measured reason; overruling one needs a documented case under convention 2 | all |
| 29 | enforcement is not relaxed | the owner's second requirement, and it had no row. `git diff evals/gates.json`: no `severity` moves `gate`→`reported`, no `subject` narrows, no `since` advances past an existing deliverable. `check_repo` `gate declarations`, `gating claims`, `vacuous gates` green | all |
| 30 | **every new verdict is registered** | §9.3 adds gates, and four guards enforce the register. Each needs an entry in `evals/gates.json` with `checker`, `family`, `severity`, `since`, `subject`, `na_means`, and an id in range. `check_repo` `gate declarations`, `metric id ranges`, `vacuous gates` green. *The largest omission the coverage audit found: adding a gate without this fails CI and no row said so* | 2–5 |
| 31 | the prompt tier reaches 12/12 | the six universal fields appear as prose in `prompts/lumi-style-core.md` **and** the sentence is added to `PROMPT_MUST_CARRY`; `check_repo` `prompt parity` goes red if it is deleted. Today `prompts/` has zero entries in `evals/rule-coverage.json` | 2–5 |
| 32 | the 16 invisible references are on a ledger | a `GAP-` entry records the 9 bare dev filenames and 7 dev-side document mentions the predicate cannot see, with counts and why widening is refused (it reopens FM-23). `check_repo` `ledgers` green | 1 |
| 33 | the rule-file scope is consolidated, not copied | the prefix tuple is one named constant with an `evals/single-source.json` entry (convention 19). **Decide `CLAUDE.md` explicitly** — `check_rule_coverage.py` includes it, §8 D's scope does not | 1 |
| 34 | the predicate is pinned by number | a test asserts: 18 files raw, the banner exclusion removes exactly the three generated indexes, and the surviving set is exactly `{design-rules.md:171, design-rules.md:1057}` | 1 |
| 35 | the six existing framework-guard tests pass unchanged | `pytest tests/test_frameworks_guard.py -q` green **without** those trees gaining `SKILL.md` — proving `consumer_scripts` is reached lazily | 1 |
| 36 | the slot lands on the branch that was broken | scaffold a `drawn: native` framework, so `if shape:` does not fire. The `[TO FILL: … run …]` line is present outside any comment and any `<svg>`. Before the change this branch emits nothing | 1 |
| 37 | the empty skeleton is refused | running the renderer on the skeleton the scaffold just wrote exits non-zero. A skeleton that renders is a slot no gate can refuse | 2 |
| 38 | the universal half is required | a spec missing any of measure name, unit, period, reading, cause, source, move is refused, naming DR-20 and WR-5 | 2 |
| 39 | `position` is landed or scoped out | §11 covers four of AR-1's five moves while the registry files three entries under `position`. Either it gets a step and a refusal test, or §9 states why it is out of scope | 4 |
| 40 | the drawing's other two outputs are graded | `inspect_layout --deliverable` reports `figure_axis_named` **held**, not `n/a`, and the SVG carries `.axname-x`, `.axname-y` and a source line inside the drawing. Today 15 number-scaling figures carry zero `.axname-*` | 2 |
| 41 | the rule register catches up | RC-448 no longer reads `metric: null`, or states why an input-shape refusal is not a metric. `check_rule_coverage --check` green, run **without `--relocate`**, which would silently rewrite the 230 line pins below `design-rules.md:171` | 3 |
| 42 | the chain arithmetic is asserted, not announced | each step's CHANGELOG names which of §4's links it moved broken→ok, with the command, and the running total. Steps 1–3 must reach 6; step 5 must reach 9 | all |
| 43 | the graded number is printed every release | every release runs §12's baseline and pastes the three numbers into its entry. A release shipping only the prerequisites prints unchanged numbers and says, in those words, that the plan has not moved | all |
| 44 | **the checklist is append-only** | a row may not be deleted, renumbered away or narrowed. A row whose predicate misfires is re-scoped and re-measured, never dropped — that is §2's failure, mechanised. Retiring one needs a documented case and a CHANGELOG line naming the row. Checked by diffing §12's row set across commits | all |
| 45 | the flat-directory deferral has a ledger id | "deferred, not refused" becomes an `IDEA-` entry in `backlog/ideas-prd.md`, so it is a state something holds rather than a sentence in a spec | 1 |
| 46 | no engagement facts enter with the specs | every figure-spec fixture uses synthetic values; `check_privacy` and `check_repo` `secrets` green | 2–5 |
| 47 | preflight is the floor | `python3 scripts/preflight.py` green at the end of every step. No row above substitutes for it | all |
| 23 | the conformance-board debt is stated, not hidden | if a step ships with the `conformance-freshness` waiver, its CHANGELOG entry says which consecutive release this is and what is unconfirmed. Three in a row already; a waiver repeated is a waiver becoming a rubber stamp | all |

### How the two are guaranteed to be executed together

They are one document now: rows 1–7 are the prerequisites, 8–18 the artefact,
19–28 the obligations both share, and 29–47 what a coverage audit found
uncovered — **one list, one baseline number**. A release that
ships rows 1–7 and stops has moved the graded number by **zero**, and its
CHANGELOG entry must say so in those words. That is the mechanism: not a
promise to continue, but a measurement that stays visibly unmoved until the
work that moves it is done.
