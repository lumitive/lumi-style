# LUMI Document Eval Rubric

> Every external deliverable is self-scored first, then reader-scored; divergence
> drives rule iteration. This is the skill's continuous-improvement engine.
> (Repository language: English only — red line.)

## Machine metrics M1–M8 (scriptable; spot-check manually when no script)

| id | Metric | Target | Predicate |
|---|---|---|---|
| M1 | Assertive-title rate | ≥70% (decks included — never waived) | share of titles that name a subject and carry a verifiable fact |
| M2 | Number-sourcing rate | ≥90% | share of percentage figures with a nearby source marker |
| M3 | Coined-term violations | =0 | occurrences of banned legacy coinages (substring exemptions apply) |
| M4 | Banned AI-tell phrases | =0 | banned-phrase hits (fixed-collocation exemptions apply) |
| M5 | Punctuation violations (zh) | =0 | half-width punctuation adjacent to CJK (code/pre/formula exempt) |
| M6 | Unsourced range figures | =0 | range-shaped numbers with no nearby source |
| M7 | Term mixing | =0 | old and new names of one concept co-occurring |
| M8 | Sentence-rhythm health (two-tailed) | overlong ≤8% **and** length CV ≥0.35 (decks included — never waived) | share of sentences past the length threshold, **and** the coefficient of variation of sentence length |
| M9 | Em dashes in en sales/marketing | =0 | em/en dash characters outside code, data, and internal analysis documents |
| M10 | Triad rate | ≤50% | share of enumerations (lists, appositive series) containing exactly three items |
| M11 | Title-shape uniformity | ≤60% | share of page titles sharing one syntactic frame (e.g. "Topic: clause") |

## Design diagnostics D1–D10 (`scripts/check_design.py` — reported, never gating)

| id | Metric | Target | Predicate |
|---|---|---|---|
| D1 | Text contrast | ≥4.5:1 (≥3.0 at 24px+) | every declared text color against `--bg` and `--card-bg` of its palette. **Reader-reported, so treat a finding as real** |
| D2 | Type scale | reported | the small end of the declared type scale. **No floor** — see the withdrawal note |
| D3 | Tier-1 callout spread | reported | tinted-plus-bordered callouts per page, and the share of pages carrying one |
| D4 | Palette purity | reported | literal hex colors outside the token block, which break the palette switch |
| D5 | Figure parity | reported | shape-kind spread across figures, and how many are rectangles-only |
| D6 | Footer completeness | reported | pages missing a source line or a `N / total` page number |
| D8 | Support line present | reported | content pages with no support sentence under the title |
| D9 | Layout spread | reported | which layouts a deck uses, and the share on the most common |
| D10 | Label icon coverage | reported | icons on figure nodes and table row-heads, beyond the page eyebrow |
| D11 | Page-height conformance | reported, and the first thing to read | pages whose rendered height differs from the geometry's, per format (`inspect_layout.py`) |

**None of the D-series gates.** `check_design.py` exits 0 unless a file cannot be
measured at all; every number is a diagnostic for a designer to read. `SKILL.md`
rule 4 is why: a page is done when a human reads it as intentional, and a metric
that can be satisfied without improving the page ends the looking rather than
directing it.

**Withdrawn in 2.0.0**, all three invented without an ask: **D7** (82% page fill),
**D9's 40% share cap**, and the **11px type floor**. D7 is the cautionary one — it
measured the bounding box of all ink, so a small chart with a long caption scored
as full, and it was satisfied by stretching table rows while four diagrams
rendered at 40% of their cell. The skill already forbade this move on the prose
side (click-through must never measure relevance, because the metric rewards what
it exists to suppress); D7 was the same mistake in the design half.

For page geometry, centerpiece scale and figure-to-cell aspect, use
`scripts/inspect_layout.py`, which renders the pages and reports. It gates nothing
either, and its real output is a contact sheet for a human to look at.

Provenance: M1–M11 made the prose half of this skill checkable while the design
half stayed a reading task, and a deck that passed every prose metric came back
from its reader with seven defects. Four were arithmetic the whole time. Run
`check_design.py` on the 1.7.0 deck and it reports 32 contrast failures, 17
sub-floor type sizes, four pages over the callout budget on 51.9% of pages, and
two footer gaps — which is the reader's list, in numbers, before they had to read
anything.

## Human metrics H1–H6 (anchors 1–5 — **anchors must be written in the reviewer's language, not internal jargon**)

- **H1 Reader value**: 5 = after each page the reader knows what they got and what
  to do next; 3 = most pages carry value, some merely state; 1 = the page talks to
  itself.
- **H2 Structural expression**: 5 = each page's layout best expresses its topic and
  the page order best expresses the storyline; 3 = usable but some pages fight
  their layout; 1 = a template forced onto the content.
- **H3 Chart self-explanation**: 5 = every figure's message is clear without the
  body text; 3 = most figures need the text; 1 = figures are decoration.
- **H4 Honest-boundary disclosure**: 5 = every illustrative/proposal/not-built item
  is labeled and findable in one place; 3 = disclosed but scattered; 1 = only the
  built parts are shown.
- **H5 Business readability**: 5 = a reader outside the project understands in one
  pass, no glossary needed; 3 = pauses to look things up every few paragraphs;
  1 = insiders only.
- **H6 Narrative persuasion**: 5 = the reader arrives at the author's conclusion
  naturally; 3 = evidence present but the reader assembles the causality; 1 = fact
  list, no storyline.

## Review protocol (the iteration engine)

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
   summary of effort spent. (Field-tested twice: H2 was self-scored 4 while four
   of a reader's seven defects sat in H2, and H3 was self-scored 4 in the round
   that shipped a clipped figure.)
4. The retrospective produces one of three outcomes: a rule revision (CHANGELOG +
   version bump) / an anchor revision (anchors can be wrong too) / a recorded
   no-change with reasons;
5. The same lesson appearing across 2 documents → promoted to a formal rule.

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
