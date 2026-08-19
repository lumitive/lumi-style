# Number-first, and the seed pitch register — design record

*Written 2026-08-19, before the 0.1.521 work. A record of what was decided and
why; not a source of rules. Rule prose lives in `references/`, values in
`tokens/`, shipped rationale in `CHANGELOG.md`.*

## What prompted it

An owner review of two decks — `adopting-lumi-style.0.1.517.r14` (accepted) and
`LUMI-Agent-BP-chengdu.0.1.519.r2` (rejected as text-heavy) — asked why a
convention she had accepted in the first did not survive into the second, and
directed that a seed investor deck be about 80% concepts and figures.

## What the measurement found

1. **The number-first convention was never shipped.** r14 carries twenty stat
   blocks with the number on top at display size; every one is an inline
   `style=` with no class on the number, and their gloss uses `class="sm"`,
   which this package renders only inside SVG — so the sentences silently took
   the body's 15px. The shipped role, `.band`, rendered the OPPOSITE order,
   while `references/exemplars/mckinsey-design-notes.md` EX-2 item 2 had stated
   the correct one for eleven releases. Prose right, stylesheet wrong, nothing
   comparing them.
2. **`.lead` is used zero times in either deck.** The focal-number component
   ships, is documented, and no deliverable has ever used it. Both decks push
   their numbers into 15-23 word titles instead; the BP's most important number,
   `0 signed customers`, sits in a band under a title that spells the page's
   other quantities out in words.
3. **The BP is not short of figures.** All thirteen content pages carry a
   captioned figure. It is long of words: 130 median against the accepted deck's
   60, every page a 50/50 `split` measuring **43%** rendered visual share.
4. **Figure numbering is broken everywhere, and the generator is why.**
   `new_deck.py` emitted `Figure {page index - 2}`, so every part opener
   consumed a number no drawing carried. r14 numbered two drawings `Figure 3`
   with no Figure 4; the BP ran 2-8, 12-14, 9-11 with no Figure 1; the tracked
   pass fixture shipped six holes.

## Decisions

| Question | Decision | Why |
|---|---|---|
| How to measure 80% | per-page rendered visual share, keyed on **storyline** | owner's answer; genre keys the rule tier, storyline keys the shape |
| Where number-first lands | flip `.band` **and** ship `.stats`/`.stat` | owner's answer |
| How to flip `.band` | `flex-direction: column-reverse` in CSS | every document already written renders correctly on its next build; a markup reorder would fix new decks and leave old ones wrong, which is the failure this release is about |
| Where `.stats` sits | inside `.fill`, never a `.body >` child | a new `.body >` child must join a `:not()` chain in four places |
| Gate or report | both new metrics **reported** | every design judgement in this package is reported; D30 may still say FAIL, which costs no exit code |
| M15's threshold | none on day one | a threshold invented at ship time is the withdrawn fill-floor and type-floor mistake; report the distribution and let a directive set the ceiling |
| M15 on Chinese | n/a | the word splitter does not transfer; the zh fixtures returned 6-7 "words" for whole pages. A character-count metric is a separate metric with its own calibration |
| `--fs-stat` in `design-tokens.json` | **no** | parity between the two token files is palette-only; `--fs-band-value`, `--fs-lead` and `--fs-say` are all CSS-only. Adding it would invent a parity that does not exist |

## Deliberate-red

D30 was written and fired **before** the scaffold was fixed, per convention 15,
and went red on all three artifacts on disk. The scaffold and the pass fixture
were corrected afterwards; `deck-broken` keeps the holes as D30's failing case.

## Deferred

The conformance board refresh (≥2 agents) is unrelated to this change and
remains owed from the 0.1.443-449 retrospective.

---

## Second pass, same day, same release

The deck built from the decisions above was reviewed and produced six more.

### What the first pass got wrong

**§7's number rule was read as a quota.** "In a title the number goes at the
front" produced a deck whose fourteen content titles all opened on a small
operational count; M11 title uniformity reached 52.9% against a 60% ceiling.
Restated as *where* a title carries a number. This is convention 4's failure
mode occurring inside a rule written to prevent it, which is worth keeping as
evidence that stating the direction is not optional.

**Spelling numbers out does not diversify a title set.** The first correction
replaced digit-led titles with word-led ones and M11 got *worse* — 62.5%, a
FAIL — because `title_frame` classifies "Four approaches…" as `plain`, and plain
then held 10 of 16. Frame diversity needs different SHAPES (a question, a colon,
a digit), not different spellings. Final: 43.8%.

### Decisions

| Question | Decision |
|---|---|
| Wordmark | The cover carries the document's own product/subject. `brands/registry.json` already had an unread `wordmark` field; both generators now read it, `--wordmark` overrides |
| Agenda lede | May be dropped **whole** (`body stack no-lede`). Partial removal is NOT SHIPPABLE — a `.lede` with no `h2.t` sets `titleMissing` |
| Per-figure source line | Rule 4 gains rule 9's genre scope. Sales states provenance once, in the colophon |
| Opener icon | Rule redrafted, not broken: one text-free subject mark, `--on-lime`. Filled, never stroked |
| Icon library | koboyo (owner's choice), vendored with terms. Fill-based, which is what makes it scale |
| Market | Analogy companies, not a top-down TAM (YC's own escape hatch) |

### Trademarks: what actually shipped, and why less than asked

The owner asked for coloured logos for Google, Meta, X, Reddit and Microsoft.
Only **Google** could be verified as an official vector on the owner's own
domain. Meta's CDN serves the **facebook** wordmark, not the Meta mark — it was
vendored, rendered, caught on the page, and removed. Microsoft publishes rasters
only; Reddit returns 403; the X asset that resolves is the legacy Twitter bird.
`assets/logos/SOURCES.md` records each. The deck sets all five in type, per the
manifest's standing rule that a mark which cannot be fetched is never redrawn.
**A partial logo row was rejected as worse than none**: one mark among four
names reads as an omission rather than a choice.

### Two probes were wrong, and the rule change exposed them

`figure_clipped` compared a nested `<svg>`'s `getBBox()` — its own user units —
against the outer viewBox, so an inlined trademark measured 988 units wide in a
900-unit drawing. The markup it fired on is markup the rules had just been
widened to permit. `source` reported NOT MEASURED on a sales deck that had
correctly dropped its figure source lines; it is now n/a with its reason for
external genres. Both are the same lesson as convention 15: a check that has
never met the artifact it governs has not been checked.
