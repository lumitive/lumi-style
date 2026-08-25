# The board refresh — what was driven, what was withdrawn, and what it cost

Date: 2026-08-26 · Status: implemented across the releases whose
CHANGELOG entries cite this file — deliberately not listed here, because a spec
that names the releases it will produce is a forward promise the guard reads as
a citation.

## Why

Nine consecutive releases — 0.1.596 through 0.1.604 — waived
`conformance-freshness`, each promising the same thing: the honest refresh is
one round driven after the branch lands. The board's last measurement was the
run recorded at 0.1.580, well outside the fifteen releases the gate allows.
This is the round that pays it.

## The round was driven twice, and the first attempt is the finding

The first attempt ran against installs still at 0.1.597 — every agent skill path
on this machine pointed at the release BEFORE the seven the waivers were written
for. Nothing catches that: `run_conformance.skill_version()` reads the checkout,
never the install the agent opened, so the board would have carried `skill
0.1.605` over twelve cells that measured none of it.

The installs were updated to the published 0.1.604 and the whole round was
re-driven. **Both the four history rows and the four traces from the first
attempt were withdrawn**, because each carried a `skill_version` its agent had
never read.

**The withdrawal is not total, and that is a decision rather than an oversight.**
Two figures in the release entry still come from the withdrawn run: Cursor's
1004-second T1, and Gemini passing T3 there. They are kept because they are
comparisons rather than verdicts — one is a middle row in a timing table, the
other is what tells a reader Gemini's ceiling is its quota and not its ability.
What was withdrawn is everything that would have been *scored* as a measurement
of rules nobody read. A reader who wants to check the two survivors will find
them in `~/Documents/LUMI-Style/_conformance/0.1.604-2026-08-25/`.

## What the round measured, and what it could not

Four agents, three tasks, twelve cells. One agent — Cursor — earned all three.
Claude Code ran to the hour cap on the deck twice; Hermes wrote its deliverable
outside the working directory on two tasks, twice; Gemini was rate-limited on
all three.

Three things this round CANNOT say, written down so the entry does not imply
them:

1. **Why the two deck-building agents diverged.** Cursor got faster across three
   rule versions; Claude Code stopped finishing. One sample each.
2. **That two unscored decks are equally good because both report zero gating
   failures.** They are not the same zero: several gates pass on Hermes's deck
   because the content they grade is absent from it.
3. **That the board's header describes what the agents read.** It carries the
   checkout's version. The per-cell `built_version` is the honest field, and
   only the HTML deliverable carries one — the markdown answers have no stamp.

## What this exposed about the machinery

- The stamp mechanism forces a hand edit to a GENERATED file every release
  (`stamps.py` requires `skill {v}` in `conformance/CONFORMANCE.md`), and the
  cheapest edit FREEZES the "N releases behind" disclosure the generator writes
  rather than removing it — which is worse, because a frozen number reads as a
  measurement. Twenty-four releases, 0.1.581 through 0.1.604, shipped one
  unchanged clause: true when written and wrong for the twenty-three after.
  `check_evidence` then exempts the change by name as stamp-sized. Recorded as
  GAP-037 and closed by a guard plus a `restamp` realigner.
- The test suite was writing `source: build` traces into the tracked store on
  every run. **182 of the store's 199 `source: build` records** are that leak,
  across sixteen distinct `skill_version`s; the release that stops it cites
  this file. (An earlier draft said 178 of 247 — a different denominator, all
  records rather than build records, and wrong on both numbers.)
- `produced[0]` picks the scored artifact alphabetically, and one agent's
  timeout left five HTML files whose first is a shape sprite. Latent; recorded.

## What was deliberately not done

No cell was re-driven to improve a verdict. The one thing re-driven is the whole
round, because the first attempt measured the wrong version of the rules — which
made the reading harder rather than kinder. No bar moved, and no trace was
closed to tidy the ledger.

## What the pre-PR review found, and why it is in the record

Four readers over the three commits, before the pull request. Two of the three
new instruments could not have failed, and one would have made every future
release impossible by failing the repository on a board the generator writes
correctly. The findings are in 0.1.608's entry; what belongs here is the shape
of them, because it recurs:

- **A guard and the fix it backs must not share a predicate.** Both went quiet
  on the same input, so neither was watching.
- **A test that runs the real command against the real tree damages the tree
  when it goes red** — and the assertion happens after the write.
- **A test can cover a function completely and cover nothing a reader sees.**
  `suite_artifact` and `load` were held; the report they feed was not, and four
  mutations of it survived the suite.
- **A fingerprint made of a thing's initial state matches everything new.**
  Three of `suite_artifact`'s four conditions are what `trace.py` writes on
  every open.
- **Nine false numbers shipped in a branch about a number nobody recomputed.**
  Sweeping by grep after fixing by hand is still memory.
