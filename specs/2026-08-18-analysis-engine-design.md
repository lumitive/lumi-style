# The analysis engine — closing the generation gap · design record

Date: 2026-08-18 · Status: approved by the owner (plan session, this date)
Provenance: the owner's offline verdict on the r12 rebuild — `变化不大`, three
named gaps (no insight, no audience narrative, design feel below 0.1.449) —
and a root-cause investigation across the refactor archive, the shipped rule
surface, and a visual comparison of 0.1.449 against r12.

## The finding

The positioning ("consultant-grade documents from your own facts", refactor
v2 §1.1) was never wrong and never implemented. The refactor's four diseases
were all governance; v3 §12.4 states no deliverable would directly improve;
"insight" appears zero times in v3. Four root causes:

1. Output quality was never in the problem statement (K3 defined
   as infrastructure conditions, first still unmet per GAP-005).
2. The research classified the analytical toolkit as a DRAWING taxonomy —
   SWOT / 2x2 / value chain / issue tree entered under `图表语法与图形分类学`
   and shipped as geometry tags; the framework names appear zero times in the
   repo; MECE once, as a spot-check. The system can render an issue tree and
   cannot build one.
3. The form/content line (`约束论证的形式，绝不约束论证的内容`) is right
   about GATING and was over-applied to GUIDANCE: the plan's own cited
   evidence (Albertson 2007) says content development predicts quality, and
   no mechanism develops content. Five value dimensions score post-hoc what
   no workflow step produces — which is why the blind-sheet loop does not
   converge.
4. Design quality was never researched, defined or measured: the named deck
   corpus was never acquired, aesthetics was ruled undecidable at v1 and
   never revisited, and every D-instrument is prohibitive. The eye can see
   the 0.1.449-to-r12 regression; no instrument can.

Side finding (process): the research falsified batch questioning and adopted
segmented questioning; the shipped SKILL.md says the opposite. Findings can
be lost in transit and no guard compares the repo against the research.

## The design (six pieces)

- **S1 Positioning**: README fenced customer block (single source, per the
  v2 mechanism); acceptance for external documents redefined as per-page
  insight presence + owner benchmark review, not score non-regression.
- **S2 Insight pipeline**: `references/analysis-rules.md` (parent GOAL) with
  five analytical moves (compare / decompose / position / correlate /
  bridge); a new ANALYSIS BEAT between storyline and writing that produces,
  per section, the move + finding (page title) + implication (`.take`);
  ghost-deck storyboarding folded into the outline beat; the outline records
  the declarations and `check_outline.py` reports their coverage —
  declaration-checked, content never gated.
- **S3 Framework dictionary**: `assets/frameworks.json` (first ten:
  SWOT, 2x2, issue tree, value chain, funnel, waterfall, Mekko, radar,
  Harvey scorecard, three horizons) — per framework: the analytical question
  it answers, slots/axes, misuse warning, bound shape ids from the 206
  library; `tags.json` gains a `framework` axis; design-rules §4.1 gains the
  selection chain question → framework → shape; a repo guard holds every
  bound shape id to the library.
- **S4 Audience registers**: writing-rules per-genre register profiles
  (sales = buyer economics; training = operational; internal = analytical)
  with contrast examples; Templates 7–10 written from the already-completed
  research skeletons (market-analysis, gtm, status-report, due-diligence).
- **S5 Design exemplars** (Phase 1): `references/exemplars/` — external
  McKinsey references (owner-directed source: plusai.com blog collection,
  downloaded for study only, never copied into deliverables) plus annotated
  strong pages from 0.1.449; composition step names its reference page.
- **S6 Verification switch**: benchmark-anchored review (side-by-side with a
  reference page, owner verdicts per page) replaces the blind sheet as the
  primary acceptance; one page is calibrated to `这页到了` before any full
  rebuild; review evidence items answer with an artifact, never a tick;
  the batch-questioning regression is fixed to segmented questioning.

## Phasing

Phase 0 = S1–S4 + E.7 fix + S6 protocol text, one release. Phase 1 =
exemplars + single-page calibration on adopting-lumi-style. Phase 2 = full
rebuild through the new pipeline, benchmark-reviewed.
