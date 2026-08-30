# Making "McKinsey grade" decidable — research, independent validation, design

Date: 2026-08-31 · Status: **rev2 — substantially corrected by three reviews
(red team, blue team, independent internet validation).** rev1's diagnosis
stands; its design is retired and rebuilt. §8 is the landing order.

## Why this exists

The owner's product goal: **let a user on ANY AI agent deliver
McKinsey-consultant-grade deliverables.** She designed four checks — visual
share, repeated skeletons, shape ambiguity, text-only figures — and asked
whether they can judge "McKinsey grade", and if not, how to design checks that
are rational rather than dependent on human feeling.

> **rev1's largest failure:** the words "any AI agent" appeared once and were
> never mentioned again, while all four proposed metrics were checkers — which
> run only where scripts run. Red team CR-1. **rev2 makes tier reach a required
> field of every proposal.**

---

## 1 · Diagnosis (rev1, retained)

The four metrics measure **quantity**, not **relation**. Quantity is satisfiable
by decoration: the repo's own red team took a rejected document, re-tagged every
`<li>` as `.vows` and pasted one empty rect per page, and **cleared all four
bars** with no fact and no idea added (`evals/thresholds.json` status_note).
Separately, the accepted anchor A1 reads 78.6 on `layout_top_share` — **worse
than both faulted documents** — so any bar on that axis red-lines it.

**This is not a failure of the owner's taste.** Visual share is device 2 of the
package's own McKinsey study (`references/exemplars/mckinsey-design-notes.md`
EX-1: one exhibit dominates 50–70% of every content page). The instinct is
right; treating it as a gate is what is wrong.

### Two factual errors rev1 made here (red team M-3, corrected)

- The four bars the red team cleared were `prose_only_share`,
  `figures_per_content_page`, `list_items_per_content_page`,
  `visual_share_median` — **not the owner's four**. And the same note records
  that `rect_only_share` and `shape_kinds_min` **saw** the exploit — those are
  the metrics the owner's "shape ambiguity" and "text-only figures" correspond
  to. **Two of the owner's four intuitions map to metrics that caught the
  attack.** This strengthens rev1's own conclusion (keep them reported).
- The 81.0 / 16.5 separation is measured **at two different geometries** (a4 vs
  16x9; the same rejected document reads 17.0 at laptop width). The separation
  is weaker than rev1 stated.

---

## 2 · Measured: McKinsey, and an independent corpus

**McKinsey, 8 reports, 61 exhibits**: assertion titles 61/61; two-tier caption
100%; source line 100%; derived callouts >=14/61; numeric density one digit
token per 7–11 words.

**Independent corpus (new this round, not owner-supplied):**

| Source | Exhibits | Assertion title | Measure line | Source line |
|---|---|---|---|---|
| Bain, *Global PE Report 2025* | 43 | 43/43 | **43/43** | **43/43** |
| BCG, *The Widening AI Value Gap* | 10 | 10/10 | 8/10 | **10/10** |
| Deloitte, *Tech Trends 2025* | — | **topic-titled** | none | present |

**Deloitte is the counter-example**: its figures are concept diagrams, not data
exhibits. **These conventions are genre-specific, not universal.**

---

## 3 · Independent standards (the most important new evidence)

**IBCS** (International Business Communication Standards; non-profit
association founded 2004, ~12,400 members; **since 2024-07 the basis of
ISO/AWI 24896**), Top Ten rules 1 and 2, verbatim:

> **1. Messages** — "Reports and presentations have messages. Present them at
> the top of each slide or report page."
> **2. Titles** — "Titles identify pages, charts, and tables. **Name at least
> organizational unit(s), measure(s), and time period(s).**"

**This is the same two-part structure this design derived independently** — an
assertion at the top, a measure line beneath. IBCS additionally requires the
**organizational unit**, which this design omits. IBCS's variance notation
(AC/PL/PY/FC) presupposes a reference scenario — i.e. "compare needs a reference
value" also appears in a published standard.

**Academic corroboration**: the same convention exists in engineering
communication as **assertion–evidence** (Michael Alley, Penn State), and it has
been tested: 111 participants, same recorded talk; on comprehension of complex
concepts the assertion–evidence group scored higher, **p=0.010 and p=0.038**,
but **p=0.078 (not significant)** on the summed essay score. Real but modest.

**Harm evidence**: Kong, Liu & Karahalios (CHI 2019) — readers' **recall follows
the title, not the chart**, and even when a title contradicts its visualization
most readers still rate the visualization impartial. This is the strongest
justification for checking that a title's number is supported, and equally a
warning that titles are a persuasion instrument.

### Methodology correction (red team H-1)

rev1 wrote "the consulting standard (Minto pyramid + hypothesis-driven)" and
**attributed the pair's distinguishing claim to the authority that does not make
it.** The correct statement is **three orders**:

> **The problem-solving method is hypothesis-first; the analysis runs
> bottom-up; the presentation runs top-down.**

- "hypothesis -> test -> conclude" belongs to **hypothesis-driven problem
  solving** (McKinsey's 7 steps: define -> issue tree -> **storyline and ghost
  deck** -> workplan -> analyse -> synthesise -> build commitment; note the
  storyline precedes the data work). **It is not Minto.**
- **Minto's core is not "answer first"** but three structural rules: (i) an idea
  at any level is the **summary** of the ideas below it; (ii) ideas in a group
  must be the **same kind** (MECE); (iii) ideas in a group must be **logically
  ordered**. **Answer-first is a consequence of (i). The three rules are the
  checkable part.**
- rev1 omitted **horizontal logic** — the sequence of titles is itself the
  argument and must read alone. That is a third scale between page and section,
  and it is partly checkable.

**The package already holds the correct version**: `eval-rubric.md:325-333` (C2)
encodes Minto's rules (ii) and (iii) verbatim. **rev1's summary of the standard
was thinner than the rubric it cited.**

---

## 4 · Measured on a real deliverable (with new baselines)

| Property | LUMI real deliverable | Independent corpus | Verdict |
|---|---|---|---|
| Assertion titles | **83.3%** (M1) | McKinsey 100% | already strong |
| **In-figure source line** | **7/7 = 100%** | Bain 43/43, BCG 10/10 | **already met — not a gap** |
| `.take` implication line | 10, each answering "so what for you" | — | already strong |
| **Measure line (unit + period)** | **1 of 15 `.sup`** on the pass fixture | Bain 43/43; IBCS rule 2 | **real gap** |
| Declared move draws a shape (D32) | **9 of 10 pages fail** | — | **real gap (generation side)** |
| Page numbers inside the figure (D29) | 3 of 7 figure pages carry none | — | real gap, but see §6 M-C |

> **rev1 error**: it proposed a source-line check as a gap. **It is not** — the
> real deliverable is at 100%, matching both independent corpora. Only the test
> fixture lacks them. **Removed from the proposal.**

---

## 5 · The structural finding, the principle, and its ceiling

Insight checks are all **consistency checks** (declared vs delivered);
consistency needs a **declaration**; declarations are optional, so the checks
idle. `f-data` is declared on **1 of 60 figures across three shipped decks**
(rev1 said "0", over-generalised). GAP-031 records a deck deleting its entire
implication rung with every gate green.

**The principle** (the only class surviving every written refusal in
`FAILURE_MODES.md`):

> **Penalise only a contradiction between what the document declares and what it
> delivers. The target is always zero.**

The package's own words (`check_outline.py:202-205`; rev1 cited the wrong line
and altered the sense): "It is a CONSISTENCY check, never a judgement: it asks
whether the artifact still says what its own plan says … It cannot and does not
ask whether **either is good**."

### The ceiling, which must be stated (red team M-1 + independent counter-evidence)

**The Columbia Accident Investigation Board faulted a briefing slide that was
formally well-formed** — title, hierarchy, evidence beneath. **Form checking
would have passed it.** A document can satisfy every metric here and be a set of
unrelated true statements — **which is FM-16 (gate-clean, value-thin) reproduced
one layer up**, the very failure mode this design cites.

**What this method cannot reach**, and what therefore stays with the reviewer:
horizontal logic (C2(1)); MECE (C2(4)); the governing message and whether the
summary summarises the body (C1(1)(4)(5)); implication quality (all of AR-2);
framework fit (AR-4); actionability (C6(1)); whether the counter-argument is
named and answered (C6(3)); whether the figure form matches the comparison the
title makes (C8(1)).

**In one sentence: these checks raise the floor from "not obviously broken" to
"internally consistent". They do not measure argument quality and are not
evidence of it.**

---

## 6 · The metrics (rev2: one promoted, one demoted, one deferred, one deleted)

### M-A · The measure line — the best-evidenced item. SHIPPING THIS ROUND

- **What it measures**: on a content page whose section declares a QUANTITATIVE
  move (`compare`, `decompose`, `bridge`, `correlate` — AR-1), the `.sup`
  support line names the measure: a **unit** token and a **period** token.
- **Why not "every figure"** (red team CR-3): a framework page — 2x2, SWOT,
  issue tree — has no unit and no period. `frameworks.json` holds 11 frameworks
  (position 3, decompose 5, bridge 2, compare 1, correlate 0). EX-2 records the
  market 2x2 as one of only two pages the owner accepted outright. **Requiring a
  measure of every figure would red-line an accepted anchor — the same defect
  the four shape bars were refused for.** Scoping to the DECLARED move exempts
  framework pages by construction.
- **Use the existing `.sup`, mint nothing** (blue team): a new caption measure
  line collides with an owner ruling of 2026-08-22 (`design-rules.md` §4 rule 8:
  the caption holds the number and the name and nothing else) and with two gates
  (`D37_caption_scope`, `caption_name_wrap`). `.sup` is emitted by the scaffold
  on every content page (`new_deck.py:1120`) and measured present on **56 of 56
  figure pages** across four documents.
- **Tier reach**: the scaffold hands the slot over -> **12/12 platforms**; the
  prompt tier carries it in the page recipe; the checker confirms -> 10/12.
  **Generation side first, check side second.**
- **Reported, not gating**: the baseline is **1 of 15**. Gating now would
  red-line every stored document including the accepted anchor, and
  `eval-rubric.md`'s promotion rule asks for two releases of real documents
  first.
- **Language symmetry**: the unit list must carry CJK units and the period list
  CJK periods, or the metric measures less on a Chinese document while printing
  the same clean row. `check_prose`'s `blind` verdict is the precedent.

### M-B · A planned implication must land. NEXT RELEASE

- Every `implication:` declared in the analysis beat must appear in **some**
  element of its page.
- **Gate only true absence** (all three reviews converge): the 0.60 overlap band
  is a similarity judgement, closer to the refused rule than rev1 admitted.
- **Not in conflict with the earlier refusal**: `2026-08-19` refused *judging
  whether the take is good*; this asks only whether the sentence arrived. The
  implementation must cite that refusal or it trips FM-15.
- **rev1 error**: it said "wire `check_outline --against` into the pipeline".
  **`build.py:310-316` already runs it**, and `build.py:311-313` is a written
  decision explaining why it is not inside `check_deliverable`. The real gaps
  are that the outline is **optional** and that the finding is a **note** that
  never reaches the exit code.
- **Prerequisite**: `check_outline.py` has no version binding and `gates.json`
  has no `outline` family, so a gating verdict there would redden history.
- **Independent warning**: a ghost deck is a **hypothesis, not a contract**;
  consulting sources warn of people turning hypotheses into false facts. A
  second reason to gate absence only.

### M-C · Title numbers must be supported. DEMOTED TO REPORTED

**Refuted on real material.** Implemented to rev1's spec, it flagged 17 of 29
title numbers on the reference document with only 1–2 genuine defects;
independently it produced **26% false positives on Bain** (11% after year
normalisation) and **failed a correct BCG exhibit**: the title "Only 5% of
Companies Get Substantial Value from AI, While 60% Lag" over a chart showing 14%
and 46% — **60% is a sum the reader performs**.

Three legitimate cases it cannot satisfy: **derived ratios** (`3.6x` — which
this design itself identifies as a McKinsey signature), **sums**, and
**zero-findings** ("0 renderers support v1.0" — **an absence cannot be drawn**,
and that was rev1's headline example). With structural counts, CJK measure
words, identifier digits (`P0`), ratio denominators and abbreviated years, there
are **at least eight false-positive classes**.

**Worse, gating it creates the wrong gradient**: the cheapest fix for a flagged
page is to **delete the number from the title**, destroying the assertion M1
exists to reward. **The gate would push titles toward labels.**

Kept as reported — Kong et al.'s harm evidence is real — but **never gating**.

### M-D · A declared move must satisfy its input shape. DEFERRED TO BACKLOG

`f-data`'s schema (`{"series":[{"label","value"}]}`) **can express none of
AR-1's five input shapes**: compare cannot mark which point is the reference,
decompose has no total, position has one value per point, bridge has no
before/after, correlate has no pairing. This is a schema revision to a contract
already shipped in the wild — three or four releases, not an extension of D21.

It is also **blind to the misuse AR-4 names**: for `position` it verifies "two
axes exist" while the failure is "the axes are not independent", so it prints
identically for a real and a fake 2x2 — FM-24.

**Also**: this package's five moves match neither **Zelazny's** five comparisons
(component, item, time series, frequency distribution, correlation) nor IBCS's
set — "position" and "bridge" are not Zelazny's. `analysis-rules.md` must record
the taxonomy as **this package's own**, not as an industry standard.

### M-E · Source line. DELETED

The real deliverable is at **7/7 = 100%**, matching Bain 43/43 and BCG 10/10.
Not a gap.

### Structural fixes (unchanged from rev1 except as noted)

- **C2a** (blue team, measured): `d21_data_contract` **skips the value check
  when `value is None`**, so a scaffold emitting a label-only contract would
  **pass forever** — the gate would look activated and grade nothing, **FM-24
  dressed as a fix**. C2 must first make D21 reject a contract with no measured
  point.
- **C2b**: `f-data` **cannot be a universal default** — shape-library figures,
  the globe, 2x2s and icon rows have no values. Emit per figure kind and declare
  the absence with `data-figure-kind="schematic"`, giving D21 three states.
- **C3**: `correlate` has **zero entries** in `frameworks.json`; `driver-tree`
  is classified differently in two files; **`waterfall` is double-classified
  inside `analysis-rules.md` itself** (:39 decompose vs :53 bridge); and
  `check_repo.py:5197`'s frameworks guard **only checks that a move is one of
  the five and never that a move has an entry**, so `correlate: 0` passes
  silently — a second FM-24 sitting under C3.

### The owner's four metrics: keep as reported, do not gate, do not delete

Reasons unchanged, and strengthened: two of the four correspond to the metrics
that **caught** the repo's own red-team exploit (§1).

---

## 7 · How a metric could ever be validated (rev1's §7 largely retired)

- **`bar_replay.py` does not apply** (red team H-2): it replays a **threshold**,
  and every metric here is a target-0 contradiction count with no bar. It also
  exits non-zero when no judged document carries the reading — a new metric must
  first be **measured into `thresholds.json`'s corpus block**, a step rev1 never
  scheduled.
- **The promotion rule was misquoted** (H-3): `eval-rubric.md:592` is
  **M1-specific**, and its text is "two releases of real documents read against
  it", stronger than rev1's paraphrase.
- **It depends on blind review, which the owner has ruled out.** So these
  metrics **have no owner-independent promotion path today.** The substitute the
  directive asks for: a metric earns promotion when it fires on a document that
  an already-accepted gate independently faults, with zero firings on the
  accepted anchors.
- **`eval_agreement.py` has been run** (M-4; rev1 said "never"):
  `measured.local.json` exists and the study now produces three joined rows.
  Its `PREDICTS` table maps only to {C2, C3, C4} — **no metric even claims to
  predict C1, C6 or C8**, which is a stronger argument for this work than the
  one rev1 made.
- **Still true, and now first**: `corpus.local.json` registers the same file as
  both A1 and D5, and R1 and D3, while `eval_agreement.py:127` keys the join on
  filename — **the two anchors are silently overwritten inside the study.** Two
  lines, and it is the precondition for everything in this section.

---

## 8 · Landing order

| # | Item | Tier reach | Status |
|---|---|---|---|
| 0 | De-duplicate `corpus.local.json` (2 lines) | — | owed |
| **1** | **M-A measure line**: rule + scaffold slot + prompt recipe. **No check** — see the refutation below | **12/12 generation; enforcement via the existing D14 gate** | **shipped 0.1.659** |
| 2 | C2a: D21 rejects a contract with no measured point (3 lines) | 10/12 | next |
| 3 | M-B implication landed (needs an outline family + `since`) | 10/12 | next |
| 4 | C2b: per-figure-kind `f-data` + `schematic` declaration | 12/12 | later |
| 5 | C3: correlate / driver-tree / waterfall / the toothless guard | 12/12 | later |
| 6 | M-C title numbers (**reported only**) | 10/12 | later |
| — | M-D input shapes -> `backlog/ideas-prd.md` | — | deferred |

**Only item 1 ships this release**: it has the strongest evidence (IBCS/ISO,
Bain 43/43, an experimental result), the slot already exists, it is **the only
proposal whose generation side reaches 12/12**, and it needs no new markup, no
token change and touches no written ruling.

## 8b · The metric that was built and refuted (recorded, so it is not re-proposed)

`D42_measure_line` was implemented, wired into `measure()`/`grade()`, registered
in `evals/gates.json` and tested, and then **removed before shipping**. The
record, so a later session need not re-derive it:

**The predicate**: on a page whose declared move is quantitative, the `.sup`
support line must contain a UNIT token and a PERIOD token, from these two closed
vocabularies:

```
unit   : % $ EUR GBP JPY USD RMB CNY bn mn billion million thousand trillion
         CAGR index ppt bps "per <word>"
         万 亿 千 倍 元 美元 人次 占比
period : 19xx 20xx Q1-Q4 H1-H2 FYnn "past/last/next/trailing N"
         monthly quarterly annual YTD MoM YoY
         年 季度 月度 至今 近N
```

**The test**: seven real measure lines, transcribed from the reports, run through
the predicate.

| measure line (verbatim) | source | verdict |
|---|---|---|
| Global buyout assets under management | Bain Fig 2 | **false-fail** |
| Share of North American buyout value, by deal type and size (deal entry years 2014-24) | Bain Fig 7 | **false-fail** |
| Share of US middle-market leveraged buyout loan issuance, by debt type | Bain Fig 13 | **false-fail** |
| Use of AI by respondents' organizations, % of respondents | State of AI Ex 1 | **false-fail** |
| Household debt liabilities, GDP multiple | Balance sheet Ex 12 | **false-fail** |
| Financial depth 2017, % | mck-21 p4 | pass |
| Incremental revenue and market cap between 2022 and 2025, $ billion | Arenas E3 | pass |

**5 of 7 false-failed.** Relaxing the conjunction to `unit OR period` still
false-failed 3 of 7 (rows 1, 3 and 5) while flagging 0 of 3 prose control lines,
so the failure is not the conjunction — it is that **a measure line is a noun
phrase naming a quantity, and Bain Figure 2's carries neither token**. That is
the semantic class AG-1 and FM-23 refused twice.

**And it self-satisfied.** The scaffold's first placeholder read "What is
counted, in what unit, over what period — e.g. Revenue by segment, $ million,
2022-25". It contains `$` and `2022`, so the metric went **green on an unfilled
placeholder** — a check satisfied by the very slot it was written to police.

**Why this is recorded rather than summarised**: "the metric was tried and
refuted" is the strongest claim in 0.1.659, and a claim a later session cannot
reproduce is one it will re-propose. Convention 11 asks a deliberate-red to be a
recorded artifact; this is the same obligation for a deliberate *retirement*.

## 9 · Explicitly not doing

- Not gating the owner's four metrics.
- No check that decides what a sentence means (AG-1, FM-23 refused this twice).
- No page-level hypothesis check (presentation is answer-first; the hypothesis
  belongs to the analysis beat).
- **Not gating M-C** — it would push titles toward labels.
- **Not claiming this measures argument quality** (§5 ceiling).
