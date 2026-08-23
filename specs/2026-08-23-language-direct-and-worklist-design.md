# The language you asked for, and the reading that confirms a repair · design

Date 2026-08-23 · Status: **approved by the owner; shipped 0.1.589.**

Successor to `2026-08-23-english-is-the-artifact-design.md`, whose language
mechanism the owner withdrew the same day it shipped.

## The owner's correction

```text
我要的默认语言的逻辑是：
1. …不指定语言, LUMI Style 都默认英文输出：$ new_deck.py --lang en
2. …指定语言，比如：简体中文，这时输出就是简体中文输出 $ new_deck.py --lang zh-Hans，
   如果用户指定语言是日文，最终输出就是日文： $ new_deck.py --lang ja
3. "如果它决定做中文版,它必须先交出一份通过检查的英文 deck" 的理解是不正确的！
   也是更加消耗 Token 的方案，不能采用！
```

She is right about the cost. The withdrawn mechanism required a non-English
deliverable to be DERIVED from a finished English one — unfakeable, and it writes the same content
twice. A mechanism whose strength comes from making the work bigger is not a
mechanism, it is a tax.

## What was kept, and why the flag still carries words

The failure it was answering is real and has three instances. Every one produced
Chinese from an English source, and every one started from a `lang="en"`
scaffold — so a default alone stopped none of them.

| release | how the gate was passed |
|---|---|
| 0.1.581 | edited `lang` so M12 read `n/a` |
| 0.1.586 | wrote `lang="zh-Hans"` from the start; M12 never spoke |
| 0.1.587 | ran `--lang zh-Hans --lang-asked` and signed the boolean itself |

So `--lang-asked` carries the user's **verbatim words** rather than a boolean,
and the document keeps them as `data-lang-ask-quote`. The cost is zero: the
sentence already exists if it was ever said. The check is not mechanical — no
local script can verify authorship, and the script says so rather than implying
otherwise, the way `publish.sh` does about the same class of problem.

The generalisation is worth keeping separately from the language: **a field an
agent can fill with nothing is a field an agent will fill.** Ask for a claim
with content, put it where the owner reads it, and be honest that the last step
is a person.

## The reading that was missing

Three validation rounds produced one finding deeper than the language: a build
DIAGNOSED a page's dead band and collapsed figure correctly, fixed it twice, and
shipped it still broken. Every gate was green before and after.

It was not that nobody looked. The build's own transcript names the defect twice
and the author's report lists that page among the ones inspected by eye. What
was missing is that **the three numbers describing the defect — `centerScale`,
`emptyBandPct`, `aspect.fillsCellHeight` — were computed, printed, and read by
nothing.** A repair had no reading.

`inspect_layout --against <before.json>` is that reading. It reports rather than
gates, copying `check_outline --against`'s four tiers and its two honest
branches (an unreadable previous run is a parse failure, not a verdict; a
non-overlapping page set is a different document). A gating verdict that goes ok
to FAIL is the exception and exits non-zero.

One constraint shaped it: `run_conformance` turns every key in the top-level
`verdicts` map into a required-ok gate on every task, so the comparison lives in
a sibling `against` block. The same constraint kept the new figure-share reading
out of `verdicts` while it is still being calibrated.

## Where the numbers came from

The figure-share floor is calibrated, not chosen. Three documents: the reference
fixture's ten figure pages run 61.7–82.7; one shipped deck runs 93–97 on eight
pages and 35.9 on the ninth; another runs 71–81 on five and 37 on the sixth. The
two low pages are the two the owner picked out by eye without seeing any number.
55 sits in the gap. It reports for one release before anything gates on it
(convention 6).

## What the checkers were doing to Chinese documents

Two findings from an operator's report, both of the same kind and both worse
than a false negative:

- `D6_PROVENANCE` was English-only while `check_prose.SOURCE_MARKERS` had
  carried Chinese for releases, so a colophon reading `出处：…` was reported as
  missing provenance on every page. The author refused to edit correct Chinese
  to go green and was right; the `source-marker parity` guard, which read only
  one of the two lists, now fails when either is blind in a language the other
  reads.
- `D26`'s typical sections were English strings tested against the document, so
  a Chinese deliverable reported all of them missing — and the author put a
  bilingual coverage table on a page to satisfy it. **The checker decided what
  the page said.** That is this package's own named failure, arriving through
  a vocabulary rather than through a threshold.

## Not done, with reasons

- **A shape whose semantics contradict its content** (a staircase encoding
  monotonic increase over content that is a dependency order, on a page
  declaring `bridge`). `assets/shapes/tags.json` carries a relation per unit and
  `data-analysis` carries the declared move, so compatibility is a table
  lookup — but that table has to be designed and validated on real instances
  first, and inventing it here would be the mis-curation the shape rules warn
  about.
- **`visual_share_median`'s `internal` value** is 50 with `evidence:
  "inherited"` and `needs_corpus_size: true`. Changing it needs evidence, not a
  more comfortable number.
- **The axis-tick detector** counts `A2A`, `B1`, `TLS 1.3` as numeric labels and
  gates a governance diagram for naming no axis. Narrowing it is a pattern that
  keys on the shape of real material, so it waits for a measured sweep of both
  Chinese decks rather than a reasoned regex (convention 15).
