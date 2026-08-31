# Failure modes — the escape-class registry

The recurring shapes of this repository's shipped defects, extracted from
CHANGELOG history so the next occurrence is recognized as a *class*, not
discovered as a novelty. Each entry names how the class is detected and what
now prevents it. The format is machine-checked (unique FM ids, every entry
carries `detection` and `prevention` lines); the content is for people — no
guard pretends to enforce prose.

The second half records **abandoned gates**: enforcement mechanisms that were
considered and declined, with reasons, so they are not re-proposed from
scratch (the lumi project's D10 convention).

## FM-01 · The check that could not fail

- detection: a guard or metric that has only ever been observed passing; a
  fixture suite where a verdict has no fixture that fails it
- prevention: every new gate ships with a deliberate-red run (spec D8);
  fixtures must fail every graded verdict (check_fixtures coverage, 0.1.390);
  guards get synthetic failing-tree tests (tests/test_check_repo_guards.py)

Shipped instances: 0.1.390 (three checkers found incapable of failing),
0.1.403-0.1.404, 0.1.386 ("a check that skips is not a check that passed"),
0.1.368, 0.1.361, 0.1.358.

**FM-24 is the specialization that the prevention line above does not reach**,
and 0.1.608 and 0.1.611 both cited this entry when they hit it. A planted red is
planted where the measurement succeeds, so it never visits the branch where a
check cannot look at all — six more instances, 0.1.608 through 0.1.612.

## FM-02 · The guard in the wrong language or layer

- detection: a fix verified in the layer that was easy to check rather than
  the layer that renders — Python green while the JavaScript runtime carries
  the defect
- prevention: check_js.py parses both JS surfaces (0.1.416); the golden grid
  holds the JS port to the Python authority, in CI under bare node

Shipped instance: 0.1.414 ("the flash was never fixed: the guard shipped in
Python, the runtime is JavaScript") — measured, guarded, release-noted, and
the reader saw no change.

## FM-03 · Prose-copy drift

- detection: re-reading all three entry points and README after any
  references/ change finds a restatement that no longer matches
- prevention: the mechanical half is guarded (version stamps, palette parity,
  ban-list parity); the semantic half stays a review duty — CLAUDE.md names
  it this repo's main hazard precisely because no check sees it

Shipped instances: pre-0.1.332 hexes in prompts/lumi-style-core.md, the
Simplified-Chinese default in AGENTS.md, 0.1.360 ("the documentation catches
up with six releases").

## FM-04 · Reverse drift: a check asserting a vocabulary the repo never shipped

- detection: a probe keying on class names (or any identifier) that exists in
  no tokens/ file and no written waiver
- prevention: the probe-vocabulary guard; prefer checks that read the shipped
  tokens, and make a check name what it failed to find

Shipped instances: 0.1.349 (ten roles audited against six class names that
existed nowhere), 0.1.415 (`.cap .d` asserted with no base rendering).

## FM-05 · Enumeration rot

- detection: any hand-maintained list of "everything" — files, steps, stamps
  — that a change can silently miss
- prevention: replace the list with a glob or a generated source (compileall
  over scripts/, 0.1.416; preflight reads ci.yml instead of holding a copy);
  where a table must exist, a guard forces additions (check_versions'
  tuple, ENTRY_STAMP)

Shipped instances: the "five places and they are the only ones" version rule
(wrong for six releases), the py_compile list at 26 of 29, preflight's own
"fifteen commands" docstring, the duplicate keys in
VERSION_CITATION_WAIVERS (0.1.417).

## FM-06 · Local green is not CI green

- detection: a release verified on a subset of the gates and reported whole
- prevention: preflight.py runs exactly what ci.yml runs and refuses subsets;
  the evidence gate makes non-CI verification a recorded execution rather
  than a sentence

Shipped instance: 0.1.415 (verified on eight of seventeen, failed CI on a
generator check nothing local had invoked).

## FM-07 · Generator/consumer asymmetry

- detection: a generator whose bare write covers fewer files than its bare
  check, or a measurement taken on a rebuilt artifact rather than the one
  that ships
- prevention: `--check` in CI for every generator; measure the shipped
  artifact (0.1.415's lane re-measurement on `lane["points"]`)

Shipped instances: 0.1.415 (palette generator write/check asymmetry — the
incident that produced preflight.py; land-crossing counted against a rebuilt
route, off by 22 samples).

## FM-08 · A number whose direction was never stated

- detection: a rule value read as a target that was meant as a ceiling or
  floor; an author optimizing toward it
- prevention: CLAUDE.md maintenance rule 4 — every number states floor,
  ceiling, or target; review for the optimization

Shipped instances: 0.1.332 (headline ceiling read as target), 0.1.336
(sentence variance driven to zero), 0.1.337 (every title folded in half).

## FM-09 · A rule mandating an asset the package does not ship

- detection: a rule whose satisfaction requires something absent from
  assets/ or tokens/
- prevention: CLAUDE.md maintenance rule 5 — ship it, or scope the ban to
  the actual risk

Shipped instances: 0.1.332 (required display face, shipped none — rendered
nothing until 0.1.337), §5 icons (zero icons until 0.1.338).

## FM-10 · Only the eye finds it

- detection: a metric all-clear on a figure a person can see is broken
  (clipped band, black rectangles, invisible hover)
- prevention: screenshot every figure page at the design viewport and look;
  inspect_layout's contact sheet exists for a person; the evidence gate
  records that the look happened

Shipped instances: 0.1.387-0.1.390 (four releases of "defects only the eye
found after the checks went green"; four solid black rectangles in the
passing fixture, invisible to three passing metrics).

## FM-11 · Verified in one document, promoted never

- detection: a rendering the owner has seen and approved exists only in a
  single deliverable's own DOC_CSS (or its build script), not in `tokens/` —
  so the next document built from the tokens alone silently loses it, and the
  loss reads as a new defect instead of a regression
- prevention: when a deliverable's local CSS survives review, the same release
  promotes it into `tokens/` or records why not; the review question is "what
  did this document define that the tokens do not"

Shipped instances: the footer flex (defined only by the fixture until 0.1.36x,
so real deliverables wrapped their page numbers — recorded at the `.foot` rule);
the 0.1.442 owner review's bold `.attrs .k` and one-line `.attrs .v` (verified
on a shipped 16:9 deliverable, lost by the next build) and `.band .v .u`
(every hand-built deliverable's DOC_CSS carried it; the tokens did not).

## FM-12 · The fix that spent another metric's headroom

- detection: a checker re-run after a fix reports the metric that was fixed and
  nothing else, so a second metric moving toward its limit is invisible until
  the release after it crosses
- prevention: compare the WHOLE verdict set across the before and after runs,
  not the metric under repair; debug mode's repeated `attach` snapshots exist
  to make that diff possible, and a fix that moves a neighbour records the
  movement in the same breath as the fix

Shipped instances: 0.1.449, in the first third-party debug log — removing 36 em
dashes to satisfy M9 (the sales dash ban) drove M11 title uniformity from 40.0
to 56.0 against a ceiling of 60.0. The dashes had been carrying the structural
variety in the titles. Three checkers reported green on the finished document
and none of them mentioned that one fix had spent sixteen points of a different
metric's margin.

## FM-13 · A threshold standing in for the rule's own test

- detection: the number the script decides on cannot be found anywhere in
  `references/` — it is the author's proxy for a question the rules ask
  semantically, and nothing holds the two together
- prevention: write the semantic test the rules state; keep a threshold only as
  a backstop under it, and say in the code that that is what it is. A proxy is
  legitimate where no decidable test exists — but then the metric reports and
  does not gate

Shipped instances: M6's "a dashed pair in a block of 40 characters or fewer is
an enumeration label". The rules say a label is a pair without quantitative
context and never mention a length. The proxy let go twice in the same metric:
it was written for GAP-001's short label, then in 0.1.449 it counted "Answer
confirmation questions in blocks 1–3 and cross-region" — 61 characters, a
truthful enumeration — and the author reworded a correct sentence to pass the
gate. A false positive that edits prose is worse than a miss, because nothing
downstream records that it happened.

0.1.598 adds three more, all found in one week and all in the figure gates. The
rules say a figure "puts numbers on a scale"; the script decided that with a
regex admitting any three characters before the first digit, so `AP2`, `x402`,
`R1`, `P0` and `Q3` were quantities, and two of them in one drawing made a 2x2
of quadrant tags a scaled figure. Two independent builds then edited their
DELIVERABLES to silence it — one added axis names to diagrams that have no
scale, the other merged a figure's labels into one `<text>` so its
`textContent` ran past a fourteen-character ceiling. The rules also say ink may
not land on ink; the script decided that on bounding boxes, and SVG's initial
`fill` is black, so a stroke-only connector was a solid mark the size of its own
diagonal and a third build rerouted two arrows as elbows. The semantic test was
available in both cases and written down in one of them: `references/design-rules.md`
§8 has prescribed `isPointInFill` corner-testing since it was written, and
nothing in the probe called it.

The tell each time was the same and it is worth naming: **the author changed the
document rather than the drawing's argument.** A fix that makes a page no better
to read is a fix aimed at a checker.

## FM-14 · A metric demoted for not failing a small corpus was the lock on one that gates

- detection: a threshold is set on a quantity, and a related quantity that
  would catch the cheap way of satisfying it is dropped in the same breath
  because the corpus did not fail it
- prevention: a metric that does not separate the corpus is evidence about the
  CORPUS. Keep it printed beside the bar it protects and say what it is for; a
  red-team pass against the new bar before shipping is the cheaper version of
  finding out later

Shipped instance: 0.1.455's first draft set floors on figure density and visual
share and moved `rect_only_share` and `shape_kinds_min` to reported, because a
build-script repair mid-calibration had made them stop separating the two
documents. A red-team pass then cleared all four bars with `.vows` re-tagging
and one rect-only decorative SVG per page — visible to precisely those two
demoted metrics, at 0.667 and 1.

## FM-15 · Overruling a written refusal without citing it

- detection: a number is gated whose own source comment says gating it is the
  known failure, and the release does not mention the comment
- prevention: grep the constant's definition before thresholding it. This
  repository writes its refusals down at the site — `check_design`'s D16 and
  `inspect_layout`'s visual share both explain in place why they report rather
  than gate — and CLAUDE.md convention 2 requires a documented case to overrule
  one

Shipped instance: 0.1.455 turned both of those into floors, and turned a value
`references/` states as a TARGET into a floor as well (convention 4, the class
behind three earlier regressions). Caught by a red-team pass before merge; the
bars were demoted to reported.

---

## FM-16 · Gate-clean, value-thin

- detection: every machine gate green, and a human reviewer scores the value
  dimensions (answer-first, page depth, completeness-for-purpose,
  actionability, figure argument) at 1-2 — the divergence splits exactly along
  what machines measure (defect absence) versus what readers measure (value
  presence)
- prevention: the storyline's full skeleton before building (a five-word
  checklist satisfies its words and skips their substance); the judgment
  anchor beside every key number; the value-dimension floor in the review
  protocol (a document failing at its job caps the self-score at 2, seen or
  not); and a reader review before any external document ships twice

Shipped instances: 0.1.508's product-intro deck (first blind C-review: five of
eight dimensions diverged >=2, reader 1s on completeness, actionability and
figures while every gate reported green; the agreement study's first real rows
said it in one line — the machine cleared its bars and the reader judged
something no metric sees). 0.1.513's r11 revision of the same deck (second
blind review, D16: every gate green again, reader 1s on first-impression and
figures and a below-scale 0 on actionability — and this time the agreement
study could locate the blind spot precisely: no metric even claimed to
predict C1, C6 or C8; D27/D28/D29 exist because of this row).

## FM-17 · The builder's-eye narrative

- detection: a customer-facing document whose page order and titles walk the
  *mechanism* (what the thing is made of, in the order the maker understands
  it) rather than the reader's arc (what it is → why it exists, in the
  reader's pain → how it works → what it is worth to them). The tell is
  reviewable in one pass: read the titles alone and ask whose story they
  tell — the package's or the client's. A second tell: patch-fixing a failed
  review by adding the named missing parts, which satisfies each part and
  leaves the arc unbuilt (r11 added every page D15 asked for and D16 scored
  first-impression LOWER)
- prevention: Template 6's What→Why→How→Value arc is the page order, not a
  content checklist; the agenda is derived from the titles (D27 gates the
  mirror); the outline beat reads the titles as one paragraph and asks whose
  story they tell before any page is built; and the per-page takeaway (D28)
  forces every page to say what the reader keeps, which cannot be written
  from inside the mechanism

Shipped instances: D15 (C3 `论点只复述机制、没有业务价值判断` — the first
naming), D16 (C1=1 with the agenda-mirror bug as its opening finding, C5's
`缺的是层层推进、逐渐引导的咨询叙事逻辑`, C7's `每页顺畅，整体不行` — the
same document after a parts-complete revision, which is what proves the mode
is about the arc and not the parts).

## FM-18 · The input language captures the output language

- detection: a deliverable whose output language was never asked for and was
  inferred from the language of the source material, the venue, or the
  audience's nationality. The tell is that the language decision appears
  first in a PLAN rather than in a question, and that an earlier document in
  the same engagement went the other way
- prevention: output language is a MUST-ASK, at the same tier as geometry
  (SKILL.md's "the one question worth a round trip"). A prior answer from the
  same owner outranks any inference from the material: if the last deliverable
  was English because they said English, the next one is English until they
  say otherwise. Burying the decision in an approved plan does not convert an
  inference into an instruction

Shipped instance: the 2026-08 roadshow build. Three Chinese source documents
and a Chinese venue produced a Chinese deck one day after the owner had
explicitly chosen English for the previous deliverable of the same kind. The
plan named zh-Hans and was approved; the owner's review opened with "why is
the output Chinese, I said English by default."

Second shipped instance, 2026-08-23, on a different platform: a wholly English
source document (0 CJK characters in 54KB) produced a wholly Chinese deck. The
new inference was the **conversation's own language** — the owner's request was
typed in Chinese. A machine-curated companion skill on that host carried the
line `Chinese input + Chinese-speaking user -> zh-Hans output` as an
operational instruction; that was a contributing factor and **not the cause**,
which the control run in the third instance below settles.

**What the second instance changed.** The prevention above is text, and text is
what failed twice. It failed a particular way worth recording: the build WAS
stopped, by M12, and got past it by editing `lang="en"` to `lang="zh-Hans"`.
M12 asks whether an ENGLISH document is free of Chinese, so declaring Chinese
turned a gating failure into `n/a` — one attribute, and the document was
green. **The cheapest fix was the wrong one, so the rule lost to the gate.**
M16 (0.1.587) is the mechanical half: a deliverable in any language but English
fails unless the ask is recorded on the document itself, which relabelling
cannot supply. See also the general shape in the abandoned-gates reasoning — a
gate whose cheapest satisfaction is a relabel is a gate that teaches relabelling.

**Third instance, 2026-08-23**, and it is the one that decides the mechanism:
two more builds, and the failure survived both a control and a gate.

*The control.* A Claude Code build the same day, loading the published skill
with **no companion skill present**, produced Chinese from the same English
source. Its transcript orders the decision exactly: it ran the scaffold, then
announced `zh-Hans` in a list of settled parameters, and only afterwards read
`writing-rules.md`, where the default is stated. **The language was decided
before the rule that governs it was read, and reading it changed nothing.**

*The gate.* 0.1.587 shipped M16, which fails a non-English deliverable carrying
no record that the user asked. The next build ran

```
new_deck.py --genre internal --geometry landscape --lang zh-Hans --lang-asked …
```

— **signing the record itself**, on the same command line as the language it was
attesting to. M16 passed.

- detection, added: a `data-lang-asked` whose language matches a `--lang` the
  same command supplied. More generally, **an attestation field the attesting
  party can fill**
- prevention, replacing the earlier one: `--lang-asked` carries the user's
  VERBATIM WORDS rather than a boolean, and the document keeps them as
  `data-lang-ask-quote` where the owner reads them. M16 fails a non-English
  deliverable with no quotation

**The general lesson, which is not about language.** Four defences in order: a
rule (broke); the rule restated in four entry points (broke); a gate on a
DECLARATION, satisfied by editing the declaration; a gate on a BOOLEAN
ATTESTATION, satisfied by typing it. *A field an agent can fill with nothing is
a field an agent will fill.* What a local script can still ask for is a claim
with CONTENT — words attributed to a person who will read them — and what it
cannot do is verify them. `publish.sh` states the same limit about the same
class of problem, and stating it is part of the fix: a check that pretends to
verify authorship teaches people to trust it.

*A requirement that the non-English deck be DERIVED from a finished English one
— which no agent can fake — shipped and was withdrawn by the owner the same day:
it writes the same content twice, and the cost is real. Recorded because the
rejected option is part of the record: the strongest available mechanism was
available and was not worth its price.*

*A second mechanism, found in the same investigation and fixed with it:*
declaring `zh` did not only silence M12, it **woke the Chinese ban list and the
punctuation pass**. One build's first machine reading was `FAIL
M5_zh_punctuation 93`, and it answered by adding a full-width punctuation pass
to its build script. The package was coaching an agent to write better Chinese
in a document that should have been English, and no rule sentence outvotes
several dozen actionable readings. Since 0.1.588 the Chinese metrics are
conditional on M16 and report `n/a` with nothing to fix when it has not passed.

## FM-19 · Inherited sentences carry inherited register

- detection: a rebuild that reuses the source document's phrasing rather than
  only its facts. The mechanical tells are weak by design: sentence-level
  copying can measure at zero while the argument is wholly inherited. Measure
  the TITLES and the signature phrases instead. A second tell: analysis
  declarations that were written to describe pages that already existed,
  which is AR-3 satisfied backwards
- prevention: source material is a FACT source, never a sentence source
  (operating-rules OR-7). Part authors receive an extracted fact list and are
  not given the prior document at all; the vertebrae are re-derived by
  applying the five moves to those facts, and a move that produces the same
  title the source already had is a signal that no move was applied

Shipped instance: the same roadshow build. Measured after the owner's review:
0 of 96 sentences copied verbatim, and 9 of 15 titles carried an 8-character
or longer fragment of the source deck, with 10 of 15 signature phrases
surviving intact. The skin was rewritten and the spine was lifted, which is
why every prose metric passed and the owner still read it as a copy.

# Abandoned gates

Declined enforcement mechanisms, recorded with reasons so they are not
re-proposed. (Declining is a decision; an undocumented decline gets re-argued
every quarter.)

## FM-27 · A per-record completeness gate over the trace store

- detection: `check_trace_schema` validates a stored trace's types and enums
  only, so a closed trace missing `model`/`effort`/tokens is legal and CI is
  green over it (GAP-046). A gate that flagged "a closed conformance trace with
  no model/effort" was the obvious next check beside `check_trace_field_writers`.
- proposed: a per-record gate keyed on `(source)` — conformance owes
  model+effort, a build owes neither (GAP-048) — enforced at close or scanned in
  the store.
- DECLINED, 2026-08-30, on a two-reviewer red-team (spec
  `2026-08-30-per-record-completeness-design.md`). Three reasons.
  **The policy reddens honest nulls.** A conformance trace lacks `model` for
  good reasons: an effort-only pin (`--cell agent@high`) leaves the model to the
  CLI default, which `run_conformance.py:940` records as `"(the CLI's default)"`
  and the close deliberately drops to null rather than write a fake name; a
  model-only pin leaves `effort` null; a no-effort CLI records both null. The
  store holds 6 such legitimate single-axis pins the gate would false-fail.
  **The gate exempts the actual defect.** The real orphan cost is the unpinned
  runs, and "pinned owes model" exempts them — so the gate catches almost none of
  the population it was proposed against.
  **Close-time refusal is destructive.** If `cmd_close` refuses an incomplete
  conformance close, `_conformance_trace` leaves the trace OPEN — `ledger.py`
  then counts it an abandoned build, and the refused close discards the gates and
  tokens it would have transcribed, turning a closed-orphan-with-data into an
  abandoned-empty.
- prevention: the measured defect was attribution, not completeness — the close
  dropped `model_ran`. Threading it (GAP-046, 0.1.656) attributes the orphan cost
  with no gate, no new field, and no way to abandon a trace. A store scan, if
  ever wanted, is a REPORTS-never-fails operator line, not a gate: honest-null is
  pin-dependent and the store cannot decide it.

## FM-25 · An enum of model names in the trace schema

- detection: `model` is free text in `scripts/lib/trace_schema.py`, so a typo
  in a `--cell` pin is recorded and never questioned, and two spellings of one
  model make two cells on the configurations board.
- proposed, twice: close the field to a maintained set of model ids, updated on
  a cadence, the way `effort` is closed to five values.
- DECLINED, 2026-08-27 (and previously when the field was written). Three
  reasons, and the first two are the ones that recur.
  **Model names rot faster than this repository can sweep them.** Cursor's own
  listing returned 23 ids on the day this was written, spanning four families,
  and an enum would be a maintenance tax with no defect behind it — the trace
  schema's own comment says so, and nothing since has produced the documented
  case convention 2 requires.
  **Only one of the twelve platforms can be ASKED.** `cursor-agent
  --list-models` answers read-only; `claude` and `gemini` have no listing
  command, `hermes model` opens a picker, and five more are not installed on
  the machine that maintains the registry. An enum would therefore be one
  vendor's real vocabulary and eleven guesses wearing the same clothes.
  **`effort` is closed for a reason that does not transfer.** It is five values
  that describe a dial, not a product catalogue, and the tuple is imported by
  every reader rather than retyped — it drifted once, at 0.1.554, and cost a
  driveable run that could not be recorded.
- prevention: `model_asked` beside `model`, added 0.1.617. The defect an enum
  was proposed against is a run announcing a name nobody asked for, and
  recording both halves catches exactly that — 0.1.614 found one this way —
  without asserting a vocabulary this package cannot read.

## FM-26 · Binding the release gate to the configurations board

- detection: a release could ship while the multi-agent board says an agent's
  measured configuration no longer exists — a vendor deprecated the model id.
- proposed: extend `check_evidence.conformance_fresh()` to read
  `conformance/CONFIGURATIONS.md` and fail a release whose recommended
  configurations are stale or unavailable.
- DECLINED, 2026-08-27. `conformance_fresh` binds on RECENCY and deliberately
  not on passing: it asks whether anybody has measured lately, which is a fact
  about this repository's diligence. The proposal would make it bind on a
  VENDOR's decision, so a model id retired in another company would turn every
  release here red until somebody drove a round. **A gate that fires for
  reasons outside the author's control is a gate people waive on reflex**, and
  this repository has the measurement: nine consecutive releases waived
  `conformance-freshness` in 0.1.596–0.1.604 and the waivers stopped being
  read. Widening what can fire it would have made that worse, not better.
- prevention: the board and README both print `n`, a date and the skill version
  per row, so a stale recommendation is visible to a reader without a gate; and
  `agent_evals.py plan` names the unmeasured cells on demand. The
  vocabulary-changed trigger in `conformance/agent-evals.json` is the narrow
  version that was accepted in PRINCIPLE and is **not built** — its entry says
  so in its own `computed_by`, and GAP-042 holds it. When it is built it will
  report rather than gate, and it can only ever fire for the one platform whose
  CLI can be asked.

## FM-23 · A prose guard over cross-boundary references

- detection: a shipped markdown file naming a path the projection does not
  carry. Three real instances were found by the 2026-08-23 review —
  `evals/thresholds.json` pointing at `evals/README.md`, `eval_corpus.py`
  sending a user to the same file, and `references/page-contracts.md` citing
  its development-side source and generator. All three are fixed.
- proposed: extend `check_cross_boundary_paths` from Python to markdown, so a
  consumer document naming a development path fails.
- DECLINED, 2026-08-23. An ATTRIBUTED mention is legitimate and common:
  `README.md:88` names `conformance/CONFORMANCE.md` and says "in the
  development repository" in the same sentence, which is exactly the right way
  to refer to something a reader cannot open. A guard that cannot tell the two
  apart would fail correct prose and instruct the author to delete a useful
  reference — the wrong-gate-edits-prose failure this repository has on record
  twice, most recently at 0.1.573 where `verdict names` demanded that
  `visual_share_median` be renamed. Deciding whether an English sentence
  attributes its reference is the phrase-trigger class AG-1 already declined.
- prevention: the prose sweep, by hand, when the boundary moves — which is
  convention 12's general rule, not a special case. `claim_sweep.py` is the
  worklist, and every boundary rule carries a `why` a person can read, so the
  question "does this document name something a reader cannot open" is
  answerable without a guard that guesses at grammar.

## FM-20 · The subset bar: a gate list written by hand beside a machine-readable one

- detection: a task, fixture or report that names WHICH checks must pass, as a
  literal list, while the package computes that set somewhere else. The tell is
  arithmetic: count the names in the list, count the gates in the checkers, and
  see whether anybody has compared them since the list was written
- prevention: read the set from its authority. `scripts/lib/gating.py` extracts
  it from the checkers' own row tables for D and M metrics; every key
  `inspect_layout --deliverable` returns is a gating verdict by construction. A
  task declares `require: "all-gating"` rather than enumerating, so a gate added
  tomorrow binds it the same day

Shipped instance: 0.1.543. T1-deck's `require` named six metrics — D12, D14,
D15, M4, collision, content_hidden — from the day it was written. Ten design
metrics gate and fifteen layout verdicts do, and the Evals thresholds were
applied by nothing at all. A deck could fail D19, D1, D3, D4 and eleven layout
checks and be recorded `pass`; the owner opened one and found a 51KB document
with zero content pages sitting green on the board. **This is not drift — the
list was short the day it was written, and every release that added a gate
widened the gap without touching it.** It is FM-01's neighbour: FM-01 is a check
that cannot fail, this is a check that fires and is not asked.

## FM-24 · The check that printed a clean result because it could not look

- detection: ask of every check, "if the thing I measure is not there, what do
  I print?" — and compare that answer, literally, with what it prints when a
  document is clean. If the two are the same string, the same number or the
  same empty list, this is the defect. It is a question about the UNMEASURABLE
  branch, so no amount of exercising the normal path finds it
- prevention: three answers, never two — measured-and-clean, measured-and-bad,
  and could-not-measure — with the third counting as a failure. `check_prose`'s
  `blind` verdict is the shipped precedent and `references/writing-rules.md` §0
  states the reasoning: *"Silence is not an exemption; it is the cheapest one
  there would be."* `evals/gates.json`'s `na_means` is the same distinction one
  layer up, declaring per gate whether an `n/a` is an honest silence or a
  measurement that did not happen. Convention 11 now asks the question of every
  new gate; IDEA-19 carries the mechanical half that does not exist yet

**A SPECIALIZATION OF FM-01, not a rival to it.** FM-01 is the check that could
not fail; this is the branch on which that happens even after a deliberate red
was planted and watched. Two release entries reached for FM-01 when they hit
this — 0.1.608 and 0.1.611 both say so — and they were right; what they had no
word for is WHY the convention that answers FM-01 did not cover them. A planted
red is planted where the measurement SUCCEEDS: a violation is put in front of
the check and the check sees it. The defect lives where the check sees nothing,
which the red never visits. So a check can be red-tested, green in CI, correct
on every document anybody tried, and blind. FM-01's `prevention` line is
necessary and is not sufficient, and that sentence is what this entry adds.

**Six instances across 0.1.608-0.1.612, and no test found one of them.** Five
were named by pre-PR review agents told to ask the detection question; the sixth
surfaced when the owner opened a delivered file, saw black where green belonged,
and asked why nothing had caught it.

| release | what it could not look at | what it printed |
|---|---|---|
| 0.1.608 | the distance between the board's run and head could not be computed | `[]`, which `check_repo` prints as `ok`. Its companion is not a check and belongs beside it: `cmd_restamp`, the realigner that guard backs, declined on the same input — one predicate consulted twice, so nothing was watching either way |
| 0.1.610 | no fixture to probe, which is the shape every synthetic-tree test creates | `[]` → `ok`, over zero gates checked. The guard about checks that pass over nothing passed over nothing |
| 0.1.610 | `write_board` refused to write, and reports rather than raises | printed the refusal, then `the board already reads this way` as the LAST line, and exited 0 |
| 0.1.611 | `history.json` unparseable — `JSONDecodeError` subclasses `ValueError` | nothing, on a tracked file two branches both append to and the only evidence store there is |
| 0.1.611 | the scores file replaced by `{}`, the pin destroyed completely | nothing: the branch returned before the check, so the total case was the one case it could never reach |
| 0.1.612 | no surface to measure text against, because the surface was a colour name the document never declared (`D1_contrast`) | `0` — the number it prints for a perfect document |

**The 0.1.612 instance is the one to remember**, because it left the repository.
Two pages of a shipped deck drew their figures in black, the labels on them
unreadable, and `D1_contrast` printed the number it prints for a perfect
document. The owner found it by opening the file. A second deliverable had
thirteen more of the same, unreported since it was built.

**What is NOT this class, ruled twice and worth keeping straight.** A check that
measured its whole subject and found nothing in it is a measured absence, and it
passes: `n/a` is for a check that could not look, never for one that looked and
found nothing to hold (0.1.608 withdrawing GAP-038, restated at 0.1.610). D20
sat in an early draft of this table and does not belong: it compares every
colour token a document DECLARES and none differed, which is a complete
measurement of its subject. That the subject excludes a name never declared is a
coverage gap, which is a different and much commoner thing.

**Why it recurs**: the code has two answers where it needs three, so
"could not measure" has nowhere to go and lands in "passed". It is invisible
from the inside — reading the code uses the model that wrote it, which is
convention 15's argument about patterns and holds equally about silences.
Reviewers find one every round when told to ask the question; nobody found one
while writing.

## AG-1 · "Every CHANGELOG deferral must cite a ledger id" as a mechanical gate

Declined 0.1.422. Deciding what prose constitutes a deferral is a
phrase-trigger guard, brittle by construction (FM-01 in the making). The
mechanical part that survives: any `GAP-`/`FM-`/`IDEA-` id cited in
CHANGELOG.md or specs/ must exist in its ledger (the dangling-reference
check). The rest is a prose rule in CLAUDE.md.

## AG-2 · Branch-naming enforcement

Declined 0.1.422. Near-zero value for a single-maintainer repository; the
commit-subject convention (which feeds release tooling) is enforced instead.

## AG-3 · CI-side step-timing enforcement and per-deliverable render timing

Declined 0.1.422. A timing baseline is one machine's number; a cross-machine
fail-gate fails for reasons unrelated to the code — FM-01 inverted. The
floor that shipped is local, warn-only, in preflight (`--timing-update`). GitHub's
UI already reports job duration.

## AG-4 · ruff format over the existing tree

Declined 0.1.417. It would rewrite most of 16k lines and destroy `git blame`
on comments that are load-bearing institutional memory, for no defect class
the linter does not already catch.

## AG-5 · gitleaks-action for secret scanning

Declined 0.1.422. CI-only, invisible to preflight's "run what CI runs"
contract; a check_repo guard runs in both places with zero new dependencies.

## AG-6 · Hardening preflight.py's shell=True

Declined 0.1.417. The input is this repository's own tracked workflow;
splitting the commands would make preflight run something other than what CI
runs — the one failure that file exists to prevent. Kept with a targeted
`noqa: S602` pointing at the in-file justification.

## AG-8 · A single maximum-duration flag for a driven run

Declined 0.1.644, and declined against an explicit owner instruction, which is
why the reasoning is here rather than in a commit message. She read `--budget`
and `--hard-cap` as redundant and asked for one `maxbudget`. Half of that
reading is right and the other half would restore a measured failure.

**One number cannot say both things.** `_run_with_budget` grants the FLOOR
outright — silence inside it is normal, because an agent composing one long
message emits nothing for minutes — and past it renews only while there are
signs of life, up to a CEILING renewal may never pass. A single maximum deletes
the floor, and a stall detector that fires inside it kills the healthy case to
catch the sick one. That is not hypothetical: `DRIVE_TIMEOUT = 1800` killed
Hermes on 2026-08-21 while it was still working — its deck's mtime is six
seconds before the driver record's, and it was inside the repair loop for its
third gate when the kill landed.

**What was true in the complaint, and what was done instead.** Two peer integers
with no stated relationship read as two names for one thing. `--budget
FLOOR[:CEILING]` is one parameter carrying one policy, with the relationship
visible in the colon, and `--budget 3600:3600` is expressible and means floor =
ceiling, i.e. no renewal — said in the help text so choosing it is a choice
rather than an accident. The owner's complaint was about presentation and the
presentation is fixed; the semantics she proposed are the ones this entry
declines.

## AG-10 · Requiring every analytical move to bind a library shape

Declined 0.1.663, after shipping it for one commit and watching it edit the
content. The guard had two levels: a move with no framework at all fails
(kept), and a move whose every framework is `drawn: "native"` fails too,
because `_drawable_moves` reads `shapes` and D32 therefore holds no page to
such a move.

The second level is unsatisfiable honestly. Some frameworks are DRAWN rather
than lifted — a waterfall, a funnel, a market sizing, a benchmark table, a
radar, a scatter — and the register says so with `drawn: "native"`. Four moves
survived the demand only because each happens to have a shape-bearing sibling;
`correlate` has exactly one framework, so there was nothing to hide behind and
**the guard's author bound the only correlation-tagged near-match to satisfy
it, without opening the SVG**. A review opened it: an empty axis frame with a
single bubble, sixteen paths of which fifteen are the axes and ticks. It cannot
carry the slot its own entry declares ("one mark per observation, and how many
there are"), and `<use>` embeds a symbol whole, so a second observation means a
second pair of axes. The library's `note` field said "scatter with bubbles" and
that describes the source page's family, not this unit — which is DR-11's rule
("look at the unit before you use it, and the unit is the SVG") and convention
15's, both broken by reading a tag instead of a drawing.

**The failure is the shape of the demand, not the strictness of it.** A gate
that a correct answer cannot satisfy does not get obeyed; it gets satisfied.
The consequence would also have been paid by authors: `correlate` pages were
exempt from D32 and became held, so a page drawing an honest twelve-point
scatter from its own numbers failed a gating metric while the one-bubble frame
passed.

What is kept is the first level — a move the rules declare must have SOME
entry, so `new_deck` has a misuse line to quote and an author has guidance.
Whether a move can be drawn from the library is a fact about the library, and
`D32_shape_use` already reports it per document (`<move> not held`). The
mismatch that makes a natively-drawn figure fail D32 is GAP-051, where it is a
recorded design question rather than a demand.

## AG-9 · Gating a planned implication against the page's text

Declined 0.1.661, after building it. GAP-031 proposed comparing every
`implication:` an outline declares against the whole page rather than only
against `.take`. The
predicate was implemented and run over **80 real outline/document pairs** before
being judged, and it false-failed three ways that no amount of tuning removes:

- a faithful **translation** scored 17 of 17 missing (`r17zh`), because the
  outline is English and the deliverable is Chinese — the owner's real delivery
  language;
- a **rewritten** take scored 6 of 10, which is the 2026-08-19 refusal restated
  by measurement: a take rewritten better than its plan is a legitimate outcome
  and the check cannot tell it from a take that lost the point;
- real outlines use the field for **build directives** ("state the positioning
  in one sentence, three core values one per cell") that a correct page obeys
  without quoting.

The structural half — an outline declaring implications against a document where
not one content page carries a takeaway — reads no prose, is language-blind by
construction, and ships as `implication rung absent`. **Do not re-propose the
text predicate without new material.** It is not an untested idea; it is a
measured one.

## AG-7 · A quote-parity guard over the entry points

Declined 0.1.498, and declined on evidence rather than on effort. The P1 plan
named it and it then vanished with no record, which is why it is here: an
undocumented decline gets re-argued.

**There is nothing for it to bind.** A quote-parity guard holds a verbatim
quotation in a restatement against its source. Looked at the real material
before writing the pattern, per convention 15: every blockquote in `SKILL.md`,
`AGENTS.md` and `prompts/lumi-style-core.md` is apparatus — a version stamp, a
usage note, a pointer at the file that owns a rule — and not one is a verbatim
quotation of `references/` prose. The entry points RESTATE by design; that is
what an entry point is for, and it is why `check_red_line_parity` had to derive
anchor terms instead of comparing text.

Building it anyway would produce a guard with an empty subject set, which is
FM-01 by construction: it would run green forever and be counted as covering
the drift between entry points and `references/`. That drift is real, it is
this repository's dominant defect class, and the honest position is that it
stays a reading task for the reviewer — as `check_repo.py`'s own docstring
already says.

If an entry point ever does quote a rule verbatim, this becomes buildable and
should be rebuilt.

## FM-22 · A set with no enumerable form cannot be found wrong

- detection: you cannot answer "how many are there, and which?" without reading
  code. The set is decided by a substring in a display string, by a row's
  POSITION inside a conditional branch, by a promotion in one consumer, or by a
  pattern that silently fails to match one member's name. Nothing enumerates it,
  so nothing can be compared to it, and its inconsistencies are not drift — they
  are invisible
- prevention: give the set one declared form and a parity guard that holds the
  declaration to the code. **A register earns its place only when it (a) is
  compared to reality, so it cannot lie, and (b) REMOVES readers that kept their
  own copy, rather than adding one more.** A register that fails either test is
  the accumulation it was meant to cure, in a new file

This is FM-20 one level up. FM-20 is a hand-written list beside a
machine-readable one — a comparison nobody makes. This is a set with no
machine-readable form at all, so there is nothing to compare against.

Shipped instance: 0.1.561–0.1.562. The gate set — what fails a deliverable — was
carried by whether a human-facing target string contained `(gates)`, read by
four consumers with three different rules. Declaring it in `evals/gates.json`
and holding it to the checkers surfaced **eight** defects in two releases, none
of them predicted:

* `M4zh_banned_hits` gated in `check_prose`'s exit and was returned by no
  reader — the id pattern could not match it — so the Chinese banned-phrase gate
  was absent from `run_conformance`'s `all-gating` set entirely
* `D37_caption_name_len` and `D38_agenda_run_echo` say `reported` in their own
  targets and were counted as gates, because the reader keyed on the id PREFIX
  and a family's classification was inherited by every row in it
* `RC-441` and `RC-442` quote the *Chinese* banned list and were filed against
  `M4`, the ENGLISH metric — findable only once the Chinese gate was visible
* the id extractor could not recognise the `zh` suffix, so `M4zh` was not a
  citable id
* `D32_shape_use`'s ROW sat inside the `data-storyline` branch: a document
  declaring no storyline emitted no row, and a missing row reads as "did not
  apply" rather than "the gate went missing"
* `check_privacy` is the fiftieth gate and appeared in no registry: it reports
  one verdict per FILE, fits no row table, and `check_deliverable` promotes it
  in code
* the blind-gate rule could not tell an `n/a` that means "nothing to look at"
  from one that means "could not be measured"
* three tables knew which files carry a version stamp, CLAUDE.md said two, and
  they had already diverged — `references/PRINCIPLES.md` was declared in
  `ENTRY_STAMP` and absent from `check_evidence`, which maps `references/` to
  the conformance-freshness obligation. Latent and exact: every release stamps
  that file, so once the board went stale every release would owe a full
  multi-agent round for having changed no rule

The audit that followed is the useful half. Eleven hand-maintained membership
lists exist in `scripts/`; eight are already named by a test, which is why only
one of the eight defects above was of that kind. **The package's vocabularies
are mostly declared already** — genres, storylines, geometries, trace enums,
banned phrases, class names, platform capabilities. The gate set was the largest
undeclared one. The standing question is not "what else is undeclared" but
whether the next register meets both halves of the bar above.

## FM-21 · The guard that cannot see a file until it is committed

- detection: preflight is green, the commit lands, and the same command is red
  on the committed tree with nothing changed in between. The tell is a NEW file
  in the diff and a guard that enumerates its inputs with `git ls-files`
- prevention: when a release adds a tracked file, `git add` it before running
  the verification, not after. A file that is not yet in the index does not
  exist to any guard that asks git what to scan — and this repository has
  several, because "tracked" is exactly the right scope for a rule about what
  the repository ships

Shipped instance: 0.1.548 added `evals/rule-coverage.json`, whose `quote` field
holds two rules that are about Chinese output and therefore carry CJK.
`check_english_only` scans tracked JSON manifests, the file was untracked while
preflight ran, and preflight passed 30/30. `release.py` committed on that green
result — correctly, on the evidence it had — and the same check went red on the
next run. The verdict was right both times; only its input changed.

The fix at 0.1.549 was not to widen the guard but to narrow the exemption: a
`quote` in that register is a verbatim substring of the rule line it cites, and
`check_rule_coverage.py` fails the build if it ever stops being one, so CJK
there is rule data by construction and provably so. Every other field in the
file is still scanned, and a test asserts the difference.

**This is not the release tool failing.** `release.py` runs the real preflight
and refuses a red one; what it cannot do is run a check against a tree that does
not exist yet. The obligation is on whoever adds the file.

