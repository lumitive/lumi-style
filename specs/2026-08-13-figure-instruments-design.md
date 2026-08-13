# Instruments that can see a thin document — design record

Date: 2026-08-13 · Status: settled, implementing at 0.1.453 · Owner ask: Cursor's
figures are much worse than Claude Code's; find out whether that is agent
capability before changing any rule.

## What the comparison showed

Two 30-page decks, same rules, same tokens, same genre family:

| | Claude Code (`adopting-lumi-style`) | Cursor (`Overseas_Signal_Radar`) |
|---|---|---|
| visual share, median | 67.5% | 0.0% |
| content pages with nothing visual | 0 of 23 | 10 of 22 |
| figures / captions | 22 / 22 | 5 / 5 |
| rectangle-only figures | 0 | 3 |
| figures with arrows | 12 | 1 |
| bullet items | 17 | 97 |

So the answer to the owner's question is **both**: there is a capability
difference, and it is invisible to this package. The thin deck passed all
nineteen design verdicts and all twelve layout gates. An instrument that cannot
distinguish 22 figures from 5 is not measuring the thing the rules are about.

## Decisions

**D1 — Fix the two checks that measured nothing before adding any new one.**
The caption budget required a `.cap .d` wrapper and skipped every caption
lacking one; nothing in this package has ever emitted `.d` — 74 captions across
three documents, zero. `tokens/` even ships a rendering for the class, added
because the probe asserted it, with a comment recording that the vocabulary
guard cannot see an inline `querySelector`. The probe now takes the caption's
own text minus its `.n` and `.srcline`, which is what rule 7b defines a caption
to be, and needs no class at all.

`M2_number_sourcing` printed "too little data: 270 sentences" on a document
whose numbers are all bare counts. True verdict, false reason — the same line
M12 printed before 0.1.4xx gave it its own explanation.

**D2 — Do not widen M2's window.** Measured before deciding: a net that catches
bare integers finds 172 in that deck, dominated by HTML entity codes (`8217`,
`8594`, `183`), page numbers and years. That is a metric reviewers learn to
skip, which is worse than a narrow one that says what it does not cover. The n/a
states its reason instead. Recorded rather than silently declined, because the
audit that found it will otherwise find it again.

**D3 — Gate on a drawing that contradicts its own numbers.**
Undecidable in general; decidable exactly when the mark declares the quantity it
encodes. So the convention ships first (maintenance rule 5 — a rule may not
mandate what the package does not provide): design-rules §4 rule 9 states the
quantitative `data-datum` form and the proportionality it obliges, and
`figure_distorts` fails a mark drawn out of proportion to it. Tolerance 2px or
4% of the largest mark.

The escape is real and stated: a figure that declares nothing cannot be checked.
That is acceptable because the alternative — inferring which rectangles are bars
— is a heuristic gate, and this repository has a ledger full of those.

**D4 — Gate thinness on a ceiling of blank pages, not a share of ink.**
Owner decision: thinness gates, with a low floor. The predicate is *content
pages carrying no visual block at all*, and the ceiling is one third. Two
reasons for that shape over a percentage target: the 82% fill floor withdrawn at
0.1.340 was satisfiable by stretching table rows, and a page-count ceiling
cannot be met by making an existing drawing bigger. Calibration needed no
judgement — the two decks sit at 0% and 45.5%.

Gaming move, recorded: one token drawing per page. Paired with D3 (a drawing
that encodes wrongly fails) and with D5's shape-vocabulary spread (a document
whose figures are all one rectangle is reported).

**D5 — Plant the distortion fixture on an existing page.**
`deck-degenerate.en.html` fails `M8_length_cv` at 0.347 against a floor of 0.35.
A new page's title moved it to 0.361 and flipped the verdict. The plant went
onto an existing page instead, adding no title and no sentence. The margin is
recorded in the fixture's own comment: a fixture that fails by 0.003 flips on
any edit not measured against it.

## Not done here

The thin deck still fails `visual_absent` after its build script is fixed. Ten
of its pages draw nothing, which is an authoring job on the document rather than
a defect in a helper, and rewriting an owner's deliverable content is not this
release's business.

Whether a figure is *good* — form matched to content, one accent, a conclusion
title — remains unmeasured and stays a reading task. What these two gates add is
narrower and worth stating plainly: a document that is mostly not drawn on, and
a drawing that contradicts the numbers printed on it.
