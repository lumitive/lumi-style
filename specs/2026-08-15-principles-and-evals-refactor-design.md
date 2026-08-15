# Principles, taxonomy and evals — design record

Date: 2026-08-15 · Status: settled after owner review; plan file to follow ·
Owner ask: 129 patch releases have produced a rule set that is scattered,
an eval suite that cannot tell good from bad, and repeated omissions that cost
several rounds of fixes per iteration. Rebuild the product goal, the philosophy
layer, the brand statement and the evals — and argue against the design where it
deserves it.

Working documents (Chinese, owner's folder, outside this repo): the v3 plan, the
red/blue record, two research memos and a corpus measurement memo. This file is
the English design record the repository keeps; it is not a translation of the
plan, and once implemented it stays as history and is never cited as authority.

## What is actually broken

Ten of the twelve modules the owner listed already exist and are mostly mature.
The missing pieces are a product definition and a deliverable-side privacy red
line. So this is a structural problem, not a feature gap, and it has four parts —
each measured from this repository's own records.

**The rule surface is fragmented.** One red line has eight hand-written copies;
roughly seventy quantitative constraints live only in checker code and appear in
no rule file; **26 of the 129 releases in `CHANGELOG.md` exist to fix a prose
copy that disagreed with the code, and five of the last ten did.** That is the
mechanism behind "every iteration finds something missed": N hand-written copies,
edit one and miss N−1.

**The evals cannot separate good from bad.** Thresholds were calibrated against
two documents and a red team cleared all four bars with two rewrites that added
no content (GAP-004); only the training tier has an accepted reference
(GAP-005); there are two human score records in total, and both lack
`corpus_id`, so the agreement study has **zero joinable rows**.

**The instruments themselves are unreliable.** Of the last five findings, three
turned out to be instrument defects rather than real results. Nothing in the
process required verifying an instrument before believing its reading.

**Performance is unmeasured.** Model usage, wall-clock and cost have no record
at all, so "faster and cheaper" has no baseline to improve on.

The word the owner used — hallucination — has two halves here: invalid
thresholds (measuring nothing) and defective instruments (measuring wrong).

## Decisions

**D1 — A constitution layer, `references/PRINCIPLES.md`, above the rules.**
Six clauses, stable numbering, owner-only, expected to change less than once a
year. Numbering is identity order (brand consistency first, because it is the
only thing unique to this skill). It constrains **how rules are made and where
they belong**, not the generation of individual documents; that distinction is
stated in the file itself, because the first draft read as if it governed
deliverables and would have become a sixth restatement surface — precisely what
`CLAUDE.md` warns about.

**D2 — Obligation strength per clause, not an ordering between clauses.**
The first draft ranked the six clauses by irreversibility of harm. A
falsification pass killed the **form**, not the intuition: five professional
codes (NSPE, ACM, ACM/IEEE-CS SE, IEEE, IESBA — plus AICPA, the EU HLEG
guidelines, Ross, Beauchamp & Childress) rank nothing; every one that expresses
an asymmetry does it with a single "paramount" clause and leaves the rest
unranked. Three technical objections land as well: a strict order is lossless
only where each criterion outweighs the sum of all below it (Hogarth–Karelaia),
which fails for two of our levels; with continuous scores ties essentially never
occur so the lower clauses are never reached (NISTIR 5663); and priority-list
execution fails to maximise benefit when items interact (Cox 2009), and ours
interact because one edit routinely satisfies several clauses.

Irreversibility survives as **the reason a clause gets its strength** — why P-6
is absolute and P-5 is a MUST — which is how RAPEX, CLP and MIL-STD-882E use it:
as a severity axis inside a trade-off, never as a ranking.

**D3 — Conflicts are dissolved by writing the clauses more precisely, not
adjudicated afterwards.** Of the three conflicts the ordering existed to
resolve, two were artefacts of clauses written too coarsely and one was already
handled by P-4's own wording. Only a genuine collision reaches the exit.

**D4 — A conflict exit, which the design previously lacked and every
professional code has.** When two MUST clauses still cannot both be satisfied:
record the conflict and the reasoning, **refuse to emit, and hand it to a
human.** It must be written into `SKILL.md`'s pre-delivery step and
`storyline-templates`' critic gate — a procedure that exists only in
`PRINCIPLES.md` will not be executed at the moment it applies. Each refusal
names the two clauses that collided, which makes it the highest-quality input
the candidate queue receives.

**D5 — `genre` is split into two axes.** One field was carrying both the rule
tier (which thresholds and prose rules apply) and the narrative skeleton (how
the story is told); five labels produced four behaviours and one distinction
that did not exist. `genre` keeps the rule tier, `storyline` takes the skeleton.
**The accepted-reference obligation hangs off the tier (three of them), not off
genre × storyline** — the split does not multiply the corpus requirement, and
saying so explicitly is part of the design because every reader assumes it does.

**D6 — Constrain the form of the argument; never constrain its content.**
Form may gate (answer-first, figures drawn in proportion, a handling statement
on every page). Content may not ("a market analysis must have seven sections").
The evidence is unusually clean: SEC Rule 421 leaves order free but makes form
mandatory; IAS 1 ¶31 explicitly refuses to treat a list of required sections as
a threshold; a study of over a thousand essays found structural compliance does
not predict quality while depth of development does.

**D7 — Completeness reports, and offers a way to declare a deliberate
omission.** The report/gate dichotomy missed the option every regulator actually
chose: PCAOB, the ISO directives, FDA and the EU prospectus regulation all
require that **a gap be declared**, not that the section exist. So the checker
reports "not found: competitive landscape" unless the document carries a
**reader-visible** scope note carrying `data-omitted`. Reader-visible is not a
detail: every one of those precedents prints the declaration for the reader, and
that is the whole source of its effect; a hidden marker would only silence the
checker. The checker must **not** decide section existence by grepping headings —
naming is the one thing all of these standards explicitly decline to mandate.

**D8 — H1–H6 is replaced by C1–C7, scored by ticking binary evidence items
rather than by overall impression.** PresentBench measures fine-grained binary
checklists as far closer to human judgement than holistic scoring; ReportLogic
measures LLM judges being fooled by fluent verbosity. So the items count things
rather than rate feelings, and the LLM's role is reduced to producing findings
with quotations, never scores.

Scoring and release are separated: C1–C7 score quality; P-5 and P-6 are
pass/fail and stay out of the score table. The dividing line is **decidability**,
not importance — all of P-1…P-5 are MUST. "Did it leak" is a decidable binary
fact; "how well sourced is it" is a matter of degree.

**D9 — One pipeline, two entry paths, and a four-beat conversation on the
discussion path.** Entry B is the template path that exists today. Entry A is a
conversation, and its order is fixed because reversing it changes the answer:

1. **Free statement** — the user talks first and the agent does not interrupt.
   Asking first anchors the user and turns their problem into ours.
2. **Segmented questioning** — the agent leads, and every question must pass the
   form/content line of D6: it may ask about structure and evidence, it may not
   decide the conclusion for the user.
3. **Advice** — the agent proposes.
4. **Storyline review** — titles, order and the logic connecting them.
   **Building starts only after this passes.**

The timing baseline starts when the storyline is agreed; discussion and outline
are not counted against the budget, because charging a user for the thinking
they were asked to do would push the pipeline back toward Entry B.

Beat 4 is where completeness is actually enforced (see the risk section), so
`outline_reviewed` is recorded on every trace.

**D10 — The evidence ledger, not a self-improving loop.** Traces are written by
machine, opened when the storyline is agreed and closed at delivery (an
abandoned build must leave a record, or the loop is blind to its most valuable
signal and biased toward success). The volume is tens of documents a year, so
statistical inference does not hold and the design says so; the value is that
nothing is lost, every change traces to evidence, and the owner ratifies. Two
new closed-vocabulary fields carry the constitution's consequences:
`principle_yields` (how often each clause loses — without the count, the
prediction that severity-led rules starve high-frequency low-severity harms can
be neither confirmed nor refuted) and `refused_to_emit`. Reasoning text goes to
the debug log, never the trace, so red line 9 stays enforced by schema.

**D11 — The McKinsey shape library is curated before it is ingested, and it does
not become a third figure vocabulary.** Extraction is complete (206 figure units,
11336 primitives, all recoloured to bind design tokens, 30 rebuilt as vector 3D).
Ingestion is not automatic: a family enters `assets/` only if its relation
semantics serve the existing chart rules.

Provenance and licence status are recorded in the library's own `SOURCE.md`
before anything is ingested — the owner settled the licence question on
2026-08-14 and the record is where a later session will look for it, not a
conversation. One clarification belongs in that record: the confidentiality
notice on the template's first page is **sample body text** of the template,
of a kind with "EXHIBIT TITLE" and "Source:", not a licence term for the asset. Shapes reach a deliverable through a
selective sprite — the deliverable references `<use href="#shape-…">` and the
build emits only the referenced symbols, following `embed_icons.py`. Two
consequences fall out for free: **D19 becomes this pipeline's correctness check**
(a reference with no symbol already fails), and only recoloured assets have any
path into a deliverable, which turns brand purity from a discipline into an
engineering fact.

**D12 — `check_privacy.py` grades by decidability, in three layers.**
Layer 1 is decidable and gates: credential-shaped strings, and terms the user
declared out of bounds for this engagement. Layer 2 is reported, not gated:
patterns that are usually but not always sensitive. Layer 3 is a human residue
named in the pre-delivery step — "is this piece of commercial analysis
sensitive" is a judgement, and pretending otherwise would produce a gate that
fires on the wrong documents. The out-of-bounds list accumulates across
engagements but **stores strings only, is never committed, and never enters a
trace**; it starts on filesystem permissions rather than a new secret store.

**A privacy check that could not run is not a pass.** It reports
`not_attempted`, and the release gate treats that as unmet, on the same
reasoning that made `not_measured` distinct from zero.

**D13 — One evidence item was lost in the migration and is restored.** Old H3
read "every figure's message is clear **without the body text**". It was mapped
onto three items that cover form-fit, family semantics and sourcing — none of
which asks that question. Verification confirmed `check_design.py` has no axis,
unit or legend check (D18's globe labels are the only relative), and
`design-rules.md` does not contain those words. Restored as C3-⑥. It was hard to
see because the bottom of H3's scale ("figures are decoration") is guarded well
by P-4's wording and the visual-share gates.

## The constitution, as it will ship

> **P-1 Brand consistency** — the brand pack is the single source of visual and
> verbal identity; a deliverable does not improvise. *MUST.*
>
> **P-2 Grounded** — every assertion carries evidence, and the kind of evidence
> follows the kind of assertion: facts trace to a source the user supplied;
> judgements and recommendations trace to facts and reasoning already shown in
> the document; claims about the document's own quality trace to an actual
> measurement. Never invent; illustrative values are labelled illustrative; an
> agent that cannot run the checks lists what it owes and may not call anything
> verified. *MUST.*
>
> **P-3 Plain language** — plain, calm, concrete; no AI register; terms
> explained where they appear. *MUST, with exceptions the clause may state.*
>
> **P-4 Figures over prose** — what a figure can express precisely is not piled
> into words. A figure carries the argument: **one that carries no argument is
> decoration, and violates this clause rather than satisfying it.**
> *MUST, with exceptions the clause may state.*
>
> **P-5 Safety and compliance** — sensitive information does not leave the
> document boundary; every page states how it may be handled, because pages
> travel alone. *MUST.*
>
> **P-6 Accountability** — AI does not take the byline; money and safety
> conclusions are always made by a person. *Absolute: a boundary, not a goal
> that trades against others.*

Every rule family in `references/` declares the P-id or `GOAL` it serves
(`GOAL` = it serves the product goal rather than a constitutional clause, and
that is a legitimate parent, not an orphan). A new `principle trace` guard
checks that the declaration exists and the P-id is real. **Its limit is written
into its own documentation: it cannot verify that the right parent was chosen.**
It stops orphans, not misclassification.

## Two things this refactor does not change

**Rules still enter only through retrospectives.** No rule is added or removed
speculatively; an owner directive is itself a documented case; a lesson becomes
a formal rule once it has appeared across two documents; and a retrospective may
legitimately end in a revised anchor or a recorded no-change. The constitution
sits above the rules but does not alter how they are made — that stays
`CLAUDE.md`'s convention 2, and D1's scope statement exists partly so nobody
later reads `PRINCIPLES.md` as a second governance document.

**The owner ratifies; the pipeline never ships a change on its own.**
What did change is where her time goes: **ratification comes first and is
uncapped; full scoring is sampled** — at least one document per cycle, the rest
inspected only where a machine flags a doubt. The reasoning is that the
agreement study needs enough paired rows, not every document scored, whereas
ratification is the one task nobody else can do. The earlier allocation had it
backwards and would have spent her scarcest resource on reviewer work.

## Risks accepted

**"Faster and cheaper" has measurement and no mechanism.** T1 instruments cost;
it does not reduce it, and the total may rise (an outline phase, more checks,
traces). The one candidate mechanism is avoided rework, with
`titles_changed_after_approval` as its proxy. **Falsification condition: once the
T1 baseline exists, if the four-beat group's total usage is not below the
control, the economic argument for the four beats is withdrawn** (the narrative
argument stands separately). Until then this work may promise measurability and
may not promise savings.

**Completeness has a single point of defence.** Since C5 never gates, a missing
section is caught only at the storyline review beat. Skip that beat and
completeness has no defence at all. `outline_reviewed` in the trace makes
skipping it a countable fact rather than an invisible choice.

**One rater.** The agreement study compares machine metrics against human
scores, so a single rater is sufficient for it — but rater drift is then
unmeasurable, and "scores did not regress" cannot distinguish better documents
from a looser rater. Mitigation: the permanent fixtures (the red-team gaming
document and the thin deck) are re-scored each cycle as the rater's own
calibration point.

**The constitution will not improve any single document.** It changes rule-making.
Stating that plainly is part of the design.

## Phases

Two tracks in parallel, plus one early proof point.

| Track | Phase | Contents |
|---|---|---|
| Structure | P0 | Rule reorder (pure move) + stable rule IDs + section-citation re-flow |
| Structure | P1 | `PRINCIPLES.md` + principle-trace guard + quote-parity guard + claim_sweep extension + delete red-line copies |
| **Proof** | **E1** | **At the end of P1, rebuild one real deliverable under the new rules and score it. If it is worse than the 0.1.449 level, the whole plan stops for re-examination.** |
| Structure | P2 | Product definition in `specs/` + the two-axis split + trace schema and collector + `check_privacy.py` + `brands/registry.json` |
| Structure | P3 | C1–C7 into `eval-rubric.md` + `scores.json` migration (`corpus_id` required) + agreement study + cross-page number consistency + judge finding layer + `check_outline.py` |
| Capability | T1 | Usage fields and per-phase attribution (starts alongside P1, so a baseline exists for the whole run) |
| Capability | T2 | Shape-library curation, tagging, selective embedding, selection rules into `design-rules.md` |
| Capability | T3 | Data contract: a figure declares its data; the checker cross-checks label, data block and body text |
| Converge | P4 | Model matrix — Opus 5 / Sonnet 5 × three effort levels, quality and cost columns produced together |
| Converge | P5 | Candidate queue live; owner ratifies; ledger health metrics start counting |

Every new gate ships with a deliberate-red run (convention 11), and guards get
synthetic-tree tests with at least one failing fixture.

**One change is ready ahead of the phases**: the sentence-length CV floor rises
from 0.35 to 0.50, calibrated against the deck-genre reference document (0.633
measured; corpus 0.612–1.543; passing fixture 0.546; degenerate fixture 0.347).
The overlong-sentence ceiling stays at 8% — the reference document sits at 2.5%,
and the corpus's 19.9% is a property of research publications, not of client
deliverables. That correction is itself the lesson: **when an outside corpus
calibrates a threshold, measure the in-genre reference in the same pass.**

## Declined

**A total order over the principles.** See D2. The evidence is against the form,
and the internal contradiction it forced ("lower in the order never means
optional" — which a strict order cannot honour) is what a reviewer noticed first.

**Gating structural completeness.** See D6 and D7. Every study and every standard
found points the other way, and the reverse would penalise exactly the principled
deviation that marks professional work.

**A scoring LLM judge.** ReportLogic's measurement is decisive. The judge produces
findings with quotations, which are reported and never gate; a finding without a
quotation is rejected by the pipeline.

**Forking rules or prompts per model.** The model matrix measures differences; it
does not license divergent rule sets, which would multiply the surface this
refactor exists to shrink.

**Speed work before instrumentation.** Optimising an unmeasured pipeline is how a
regression ships silently.
