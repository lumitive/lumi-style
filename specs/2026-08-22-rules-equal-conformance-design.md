# Making conformance mean the rules · design

Date 2026-08-22 · Status: **approved by the owner, phase 1 shipped at 0.1.547**

## The complaint

Five rounds of multi-agent conformance ran one shape. The deliverable cleared
every gate, the owner opened it, she named defects, a gate was added, and the
next round produced a new set of defects nobody had a gate for. Her instruction
was to stop patching and find the root cause.

## What was measured, not argued

Three independent sweeps of `references/` and `SKILL.md` on 2026-08-22 agreed
on the count: **175 checkable rules about a deliverable's structure and
appearance. 78 are measured by some metric. 40 gate. 97 have no automated check
of any kind.**

The check set grew bottom-up from what was cheap to measure and has never once
been audited against the rule set it is supposed to enforce.

The behavioural half was measured the same day, on one model at one effort over
five rounds where the ONLY variable was how much of the standard the contract
put in front of the agent: 66KB failing six gates, then 591KB against 29 gates,
then 600KB with one miss, then 579KB passing. **An agent iterates to the edge of
what it is shown.**

Put together: multi-agent output converges on the 40 gated rules and diverges on
the other 135, and the owner's eye lands on the 135 every time. Three agents
making the same class of mistake are not copying each other — they are reading
one standard with the same holes in it.

## The four amplifiers, each confirmed separately

1. **`SKILL.md` never instructs the agent to read `design-rules.md`.** It has
   explicit "Read" instructions for brand, storyline-templates, analysis-rules
   and exemplars, and five bare "§N" pointers for design-rules. `AGENTS.md:29`
   has an ordered read list with design-rules as item 4. The Claude Code path is
   structurally blinder than the Codex path, and most unchecked rules live in
   the file it does not name. The phrase "subject mark" appears in `SKILL.md`
   zero times.
2. **The scaffold teaches the violations.** Every content page got the same
   `#i-radar`; the openers drew no subject mark, so a deck built straight from
   `new_deck.py` fails `opener_subject_mark` on every opener it has.
3. **Absence scores better than a poor attempt.** No agenda → D27 passes ("owes
   no mirror"). No openers → `opener_subject_mark` is `n/a`. `run_conformance`
   counts `n/a` as met. One conformance deck passed the structural gates by
   having none of the structure.
4. **`assets/icons/koboyo/` — 36 filled silhouettes whose `SOURCES.md` says they
   are for part-opener subject marks — appeared in no rule file, no entry point
   and no script.** Not even the fixtures used it.

## Decisions

**Phase 1 — close the amplifiers** (0.1.547). The read instruction, the
scaffold's defaults, and `deck_structure`.

`deck_structure`'s scope was decided from the material, not the prose.
`references/` says the agenda belongs to "every deck scenario"; a gate written
from that sentence fails two decks the owner accepted this month (nine and
eleven pages, page-for-page conversions of her own originals, no openers and no
agenda). So: **cover and closing unconditionally, agenda only once the deck has
part openers** — a part nothing routes is the defect, not a missing page as
such. Scope is "composes as a deck" (carries a cover, a closing or an opener),
never page count, because those intro decks are as long as a report.

**Phase 2 — the register.** `evals/rule-coverage.json`, one hand-written entry
per rule with `source`, `quote`, `metric`, `gates`, `why_unchecked` and
`page_kind`; `scripts/check/check_rule_coverage.py` verifies mechanically that
each cited `file:line` still holds its quote, that each named metric exists,
that each `gates: true` entry's metric really gates, and — the reverse
direction — that **no gate exists without a rule behind it**. It reports the
coverage numbers and deliberately does **not** gate on coverage, which would
turn into number-polishing.

`references/page-contracts.md` is **generated** from that register by
`scripts/build/build_page_contracts.py`, `--check` in CI, on the
`eval-inventory.md` precedent. Six sections at the owner's direction: cover,
agenda, opener, closing, **content pages on their own**, and all-page. It
carries pointers, never rule prose — a hand-written summary of 175 rules would
be the 176th place that can lie, and prose copies drifting is this repository's
measured worst defect class.

**Phase 3 — the checks her UAT named.** `D33_icon_provenance` (gates),
`D34_icon_uniqueness` (reported first — the reference reuses icons and it is
unsettled whether that is synonym reuse or a defect), opener silhouettes may not
repeat (gates), `D35_agenda_exclusive` (gates; the owner chose a hard rule),
`opener_pacing` (gates; the owner chose a floor). `figure_axes` reported only.

`opener_pacing`'s ceiling is **6, not 5.** The rule text says "about five
content pages between openers". Measured: the accepted reference runs 6, this
package's own passing fixture runs 7, the failing conformance deck runs 12. A
ceiling of 5 fails the document the owner accepted. 6 is "no worse than what she
accepted", the same line-setting principle as `bookend_title_length`.

## Not doing

No threshold on layout variety or figure-structure repetition. Both are GAP-024
and GAP-025 and both need a second accepted document; inventing the number from
one is what earned convention 6 in 0.1.339.

## How each new check is validated

Against the accepted reference deck and `fixtures/deck-pass.en.html` **first**.
A red reference means the check is wrong, not the document. Five checks written
on 2026-08-21 were each wrong on their first version and the reference caught
all five. Floors are shares of the page, never pixels — three one-viewport
mistakes in two days.
