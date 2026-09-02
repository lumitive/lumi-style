# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

lumi-style packages LUMI's design language and writing style as a cross-platform
LLM skill. It ships Markdown rules and design tokens — there is nothing to build
or install. "Development" here means editing rules, keeping the entry points in
sync, and recording changes in the changelog.

## Checks

```bash
python3 scripts/preflight.py             # run EXACTLY what CI runs, read from ci.yml
python3 scripts/check/check_repo.py            # repo invariants; exit 1 on any failure
python3 scripts/check/claim_sweep.py           # counted claims + file:line citations; REPORTS, never fails
python3 scripts/check/precedent.py <terms>     # has this mechanism been refused before? step zero for any new gate
python3 scripts/ops/eval_corpus.py <file>    # a deliverable against evals/thresholds.json; REPORTS, never gates
python3 scripts/check/check_prose.py <file>    # the prose metrics on a deliverable (the script's row table is the list)
python3 scripts/check/check_outline.py <outline> [--against DECK]  # the storyline beat; --against gates the deck on its own plan
python3 scripts/check/check_facts.py <contract> <file>  # the build against the facts it was built from
python3 scripts/check/check_design.py <file>   # the design metrics on a deliverable (the script's row table is the list)
python3 scripts/check/inspect_layout.py <file> # render a deliverable and report what the layout does
python3 scripts/ops/export_pdf.py <file>     # PDF / 4K page rasters of a deliverable (local, Playwright)
python3 scripts/ops/export_pptx.py <file>    # one full-bleed page raster per slide (local, Playwright)
python3 scripts/ops/output_dir.py            # where a deliverable belongs; --create needs the user's say-so
python3 scripts/ops/new_deck.py              # emit a deck skeleton that already renders, in the standard order
python3 scripts/build/embed_font.py            # @font-face block with the face inlined
python3 scripts/build/embed_icons.py           # <symbol> sprite of the semantic icon set
python3 scripts/build/recolor_shapes.py        # the shape library from its vendored originals + tokens; --check in CI
python3 scripts/build/build_geography.py       # regenerate assets/vectors/ from lat/lon data
python3 scripts/build/build_worldmap.py        # shared-arc world topology + the golden grid
python3 scripts/build/build_region_palette.py  # region hues; --selftest asserts the contrast floors
python3 scripts/render/globe_svg.py             # one static SVG frame of the globe
python3 scripts/render/regionmap_svg.py         # the flat region map, labels from the registry
python3 scripts/build/embed_regionmap.py       # the map runtime as one inline <script>
python3 scripts/check/check_globe.py           # globe maths + the JS port (needs Playwright)
python3 scripts/build/embed_globe.py           # the globe runtime as one inline <script>
python3 scripts/build/build_entrypoints.py     # regenerate every per-platform artifact; --check in CI
python3 scripts/build/build_fixtures.py        # regenerate the tracked test fixtures; --check in CI
python3 scripts/check/check_fixtures.py        # run the checkers against the fixtures and assert verdicts
python3 scripts/check/check_js.py              # node --check over the 8 tracked .js files + 3 embedded probes
python3 scripts/check/surgical_diff.py         # did a diff reformat a file it meant to edit? gates in release.py and CI
python3 scripts/check/check_evidence.py        # --init | record --id X | --check: the evidence gate (see below)
python3 scripts/ops/review_scores.py         # the six human dimensions over time; --check validates
python3 scripts/ops/nightly_review.py        # what today shipped, against the measured failure classes; REPORTS
python3 scripts/ops/run_conformance.py       # validate | detect [--ask-models] | run [--drive --cell] | score | report [--record] (local only: no keys in CI)
python3 scripts/ops/agent_evals.py           # board [--write|--check] | suggest --agent ID | plan — the MULTI-AGENT evals, separate on purpose
python3 scripts/build/build_readme_configs.py  # README's measured-configuration block; --check in CI
python3 -m pytest -q -n auto             # the test suite under tests/; gates in CI
python3 -m ruff check .                  # lint + the S security rules; gates in CI
python3 -m mypy                          # type-check (check_untyped_defs floor); gates in CI
bash    scripts/ops/ci_wait.sh <PR>          # bounded wait, short-circuits on outage
```
**The deliverable path is standard library only** — nothing in `scripts/`
imports outside it at runtime; dev tools are pinned in `requirements-dev.txt`
and ship in no deliverable. **`.github/workflows/ci.yml` is the authoritative
step list and is deliberately not counted here.** `scripts/preflight.py` reads
that list and runs all of it, so "local green" and "CI green" are the same
claim; it refuses to run a subset. **`check_repo.py` is ONE of those steps** —
its `CHECKS` tuple is the authority on what it guards, and a guard with no
entry there does not run. What each guard exists for, and the history behind
the checkers below, is in [`MAINTENANCE.md`](MAINTENANCE.md) under *The checks,
in full*.

**Every verdict a deliverable can receive is declared in `evals/gates.json`**
— its `family`, the release it is `since`, what an `n/a` from it means
(`na_means`), and on every gating row what it grades (`subject`). **A gate
binds a document built at or after its `since`**; an older deliverable reports
`not held`, and a document with no version stamp is held to everything.

`tests/` holds the pytest suite: characterization tests for the shared
modules, synthetic-tree tests that prove each guard can FAIL as well as pass,
and a `--help` floor over every argparse CLI. Every new gate ships with a
deliberate-red run recorded in its CHANGELOG entry (convention 11).

`check_prose.py`, `check_design.py` and `inspect_layout.py` measure a
**deliverable**, not this repo; the first two run in CI against `fixtures/`,
and `inspect_layout.py` needs a browser, so its result is recorded through
**`check_evidence.py`** rather than as a sentence. **`inspect_layout.py
--deliverable` gates a document** on the findings that are decidable rather
than aesthetic — the code's `deliverable_verdicts` is the authority — and it
exits 1 when a check could not be measured at all. **`check_prose.py`** reads
the document's own `lang`; **M12** fails an English deliverable carrying
visible Chinese, and a document carrying Chinese that declares no language is
`blind`, which fails. **A prose row fails the run if and only if its target is
zero and it does not say `(reported)`** (GAP-029; `grade`'s docstring is the
authority) — a target of zero is a line, a share is a direction. It takes
`--genre {sales,internal,training}`. **`check_design.py`** grades a document
against the token block it declares, reports `UNMEASURABLE` below three of the
ten core tokens, and **D20** alone looks the other way: every colour token the
document declares that `tokens/` also defines must carry the shipped value.
The metrics that **gate** are the
rows whose target says `(gates)`, however many that is today, and none is a
design judgement: **D12** (handling terms and origin on every page) is a
commercial requirement on the artifact, **D14** (no `[TO FILL]`, `[TBD]` or
`{{…}}` reaching the reader) asks whether the document is finished, **D15**
(no repository path in a footer) is D12's mirror, and **D19** (every reference
resolves inside the document — an icon pointing at no symbol, a `data-globe`
mark with no runtime, a `var()` naming a colour the document never declared)
asks whether the markup can render itself, and **D20**
(the colour tokens it declares are the ones `tokens/` ships) asks whether the
palette is LUMI's at all, and **D21** (a figure that declares the
data it draws is held to it) asks whether the drawing agrees with its own
numbers, and **D22** (every page's layout is one `tokens/` defines) asks
whether the page structure is the brand's at all, and **D24** (every image ships
inside the file) and **D25** (every image names its terms) are what made lifting
the imagery restriction safe rather than a hope, and **D27** (every agenda
line quotes a title the document actually carries) asks whether the agenda is
the document's own story or a second one, and **D32** (a page that declares an
analysis move draws the library's shape for it) asks whether the page did what
it said it was doing, and **D33** (every icon's geometry is a file in
`assets/icons/`) asks whether the icons are the two shipped sets or somebody's
hand, and **D35** (an agenda page's body holds the launch sequence and
optionally its lede, and nothing else) asks whether the page that routes the
deck is only doing that, and **D37** (the caption below a figure holds the
number and the name, and the source line lives inside the drawing) asks whether
two roles were run together into one sentence, and **D38** (every agenda claim
carries the lime chip, and no agenda row names a page span) asks whether the page
that routes the deck reads as its argument or as a table of contents, and **D39**
(the cover's mark and the closing's are the same mark) and **D42** (a page
that declares the file its numbers live in names a file that exists and holds
what its move needs — nothing asks a figure to declare one, which is AG-10, so
what gates is the contradiction alone) and **D43** (the drawing names every
member that spec declares — the gate that was missing while a two-by-two
shipped as an empty box with an axis word at each end and every other metric
ran green) and **D40** (each bookend
carries the locked field globe unless the document declares the replacement that
was asked for) ask whether the brand is still on the pages that carry it. Every one of them is
decidable in the way "does this page read as intentional" is not. The list is
`check_design.py`'s to change: a row whose target says `(gates)` gates, and the
`gating claims` guard holds this sentence to it.

Its banned-phrase list is a second copy of `references/writing-rules.md` §2,
and the **ban-list parity** guard holds the two together: every phrase §2 bans
is either a pattern in the script or in `NOT_MECHANIZED` with a reason, and the
script may not ban what §2 does not list.

Everything the checks cannot decide — above all whether a rule change was
re-flowed into the entry points — stays with the reviewer.

## When CI is slow or down

`main` takes changes only through a pull request with a green `checks` status,
enforced for admins too, so a GitHub Actions incident blocks everyone. Do not
wait it out by polling: **`scripts/ops/ci_wait.sh <PR>`** asks the status page
first, short-circuits on a declared incident, and otherwise stops after about
four minutes. Correctness is `check_repo.py`'s answer, locally; CI only unlocks
the merge button, so during an outage report the local verdict and hand over
the decision. A cancelled run is re-run once, never twice into an incident.
`scripts/ops/emergency_merge.sh <PR>` is the last resort, not the second. The
full protocol and the outage that wrote it are in `MAINTENANCE.md`.

## Architecture: one rule set, many entry points

`references/` is the single source of truth for rule prose:

- `references/brand.md` — the water thesis, the two brand devices (waterline, field), the ground, the acid green, the consistency rules; loaded first by SKILL.md and AGENTS.md
- `references/writing-rules.md` — output-language default, terminology red lines, banned phrases, punctuation, number discipline, the LUMI voice
- `references/storyline-templates.md` — narrative skeletons, one per storyline in its roster (sales through the investor pitch), cover & closing templates, the pre-delivery critic gate
- `references/design-rules.md` — color semantics, typography, chart rules, semantic icons, layout guards, verification matrix
- `references/eval-rubric.md` — the M / D / C scoring rubric and the review protocol (the iteration engine)
- `references/operating-rules.md` — how the work is done rather than what a deliverable is: the debug-log contract, the parallel-build protocol and its merge gate, questions-come-once, scaffold-never-fixture, and generate-a-world-figure-rather-than-draw-it. A rule that lives only in an entry point has no source its restatements can be checked against, so these live here
- `references/eval-inventory.md` — **generated** (`scripts/build/build_eval_inventory.py`, `--check` in CI): every quantitative constraint extracted from the checkers, with its tier and whether any reference file states it

`tokens/lumi-theme.css` and `tokens/design-tokens.json` are the authority for
palette and type values. Their palette values mirror each other exactly and must
be edited together, but the JSON is a superset: `palette_default`, `chart`,
`chart_scale_px`, and `layout` have no CSS counterpart. Where a numeric value in
`design-rules.md` disagrees with the tokens, the tokens win — the prose copies
drift.

Three entry points load these rules, and each restates part of them:

- `SKILL.md` — Claude Code entry; reads `references/` and `tokens/` on demand
- `AGENTS.md` — Codex entry; summarizes the load order and the six red lines inline
- `prompts/lumi-style-core.md` — **self-contained** single file for Kimi/DeepSeek. It was described as "a strict subset of `references/`" and that has been false since it grew rules of its own (never name a region by its colour in prose; the prompt-tier debug degradation format). It is a **derived restatement that may carry prompt-tier-only rules**, and those are the second thing to check when the two disagree, so any substantive rule change must be re-flowed into it by hand

`adapters/` also carries **`shipped.json`**, which is not about platforms: it
declares which side of the repository split each tracked file is on, and three
guards (`shipped closure`, `cross-boundary paths`, and the reachability
computation in `scripts/lib/shipped.py`) hold the tree to it.

**The agent evaluation is a separate register and a separate tool, and
`conformance/README.md` is where that boundary is written down.** `evals/` and
`ledger.py` answer whether a DOCUMENT is good; `conformance/agent-evals.json`
and `agent_evals.py` answer whether a CONFIGURATION — `agent x model x effort`,
never an agent id — is worth running. The Score Evals declare axes and an
ordering and **no numbers**: the bar is already `evals/gates.json`, applied by
`agent_runs.board()` as an admission ticket, and a cost board without that
ticket rewards writing thinner decks. `run_conformance.py` stays where it is —
it is a driver, not an evaluation. An enum of model names (FM-25) and binding
the release gate to the configurations board (FM-26) were declined in writing.

`adapters/platforms.json` is the **platform registry** — the single source of
install paths, capability tiers, entry files, the model vocabulary probe and
the EFFORT vocabulary of every platform the harness can drive, because effort
is not one tuple: one CLI accepts eight levels, one spells the level inside the
model id, and one has no such concept. `adapters/*.md` are the per-platform loading notes, one per registry record and
**generated** by `scripts/build/build_entrypoints.py` — as are `GEMINI.md`,
`.github/copilot-instructions.md`, `.cursor/rules/lumi-style.mdc`, the plugin
manifests and `.well-known/skills/index.json`. Edit the registry, never the
artifact; `--check` runs in CI. `SKILL.md`, `AGENTS.md`,
`prompts/lumi-style-core.md` and `references/` stay hand-written, because
assembled prose is worse prose and those are the files a reader actually reads.
The one exception is `references/eval-inventory.md`, above: a table of the
checkers' numbers is generated, because a hand-written copy of it is
convention 12's drift class.
The notes also carry the precedence rule that `references/` wins on conflict. The
`platform manifest` guard requires every registry claim to have a file behind it,
every note to be claimed by a platform, and every *unverified* claim to carry a
written waiver naming what is unconfirmed. Adding a platform is a registry record
and a note — never a restatement of a rule.

Three capability tiers, because what matters is not the vendor but what the agent
can do: `full` reads the bundled files and runs `scripts/`; `files` reads but
cannot execute; `prompt` gets one pasted context and no tools. **An agent that
cannot run the checks may not call a deliverable verified** — it names the checks
it owes and the operator runs them.

`specs/` holds design records for changes to **this package** — per change, a
`YYYY-MM-DD-<topic>-design.md` and, once the design is settled, a
`YYYY-MM-DD-<topic>-plan.md` that decomposes it into commits. (`docs/` is
gitignored on purpose: validation runs write there, and a deliverable committed
there would breach the no-engagement-facts red line.) A spec is a record of
what was decided and why, written before the work; it is **not** a source of
rules. Rule prose stays in `references/`, values stay in `tokens/`, and the
shipped rationale stays in `CHANGELOG.md`. A spec that has been implemented
stays as history and is never cited as authority.

**Drift is this repo's main hazard, and the checks catch only its mechanical
half — semantic drift between prose copies is invisible to them.** After changing
`references/`, re-read all three entry points *and* `README.md`, which
independently restates the file map, the design language, and the iteration
protocol.

**Drift also runs the other way: from a check into the rules.** A probe that
keys on class names is asserting a vocabulary, and that vocabulary has to ship in
`tokens/` or it is a private convention borrowed from whatever document the probe
was developed against. Prefer a check that reads the shipped tokens; where it
cannot, make it name what it failed to find. The cases behind both directions
are in `MAINTENANCE.md`.

## Maintenance conventions

The twenty rules for changing THIS repository. ("Red lines" names something
else — the six non-negotiable *content* rules for deliverables, in SKILL.md.)

**Each rule below is the whole rule. The shipped defect that forced it is in
[`MAINTENANCE.md`](MAINTENANCE.md), which is the one home for the reasoning —
read the entry there before applying, arguing with, or revising a convention.**
The numbering is load-bearing — a convention is never renumbered, because the
scripts, tests and references cite conventions by number.

1. **Repository language is English only.** Chinese appears in rule files only
   as rule *data* for Chinese output (banned phrases, punctuation examples),
   never as document prose.
2. **Rule changes come only from review retrospectives** — a documented case (a
   reader review diverging ≥2 points, or a reported defect), never a
   speculative improvement. A retrospective may legitimately end in an anchor
   revision or a recorded no-change. A lesson becomes a formal rule once it has
   appeared across two documents.
3. **A rule revision requires a `CHANGELOG.md` entry and a version bump.** The
   repo carries ONE version, living in three tiers: hand-stamped and checked
   (`check_versions`' tuple and `check_version_citations`' `ENTRY_STAMP` are the
   authority — adding a token file or an entry point means adding it there);
   generated (`build_entrypoints.py --check` is the forcing function, and the
   tier is deliberately not enumerated); and not-a-stamp (historical notes
   inside `tokens/`, and other projects' CLI builds in `conformance/`).
   Commit subjects read `X.Y.Z — comma-separated summary`. **A branch carrying
   several releases is MERGED or REBASED, never squashed** — two guards assume
   one commit per release. If one is squashed anyway its subject takes the
   NEWEST version, never the range and never the PR title.
4. **A number in a rule states whether it is a floor, a ceiling, or a target.**
   An author optimizes toward any number you give them, so say which way it
   points. Three shipped regressions came from this.
5. **A rule may not mandate an asset the package does not ship, and may not ban
   a whole category because one member of it is unavailable.** Ship it, or
   scope the ban to the actual risk.
6. **A prescribed value carries the floor below which it stops working.** If a
   rule hands out numbers, hand out the limit too.
7. **The skill's own conventions are the reference. A validation artifact never
   is.** An engagement supplies *facts* and nothing else — not conventions, not
   registries, not naming, not versioning, not layout. Reading a convention
   back out of a test document reverses the direction of authority.
8. **Ship-blocking asymmetry between the checks and the eye.** A metric that
   passes is not a verified document — the scripts measure declared CSS and
   cannot see rendered geometry. Screenshot every figure page at the design
   viewport and look at it (`references/design-rules.md` §8).
9. **This repo holds style rules and templates only — never client names,
   project figures, or engagement facts.** This binds `CHANGELOG.md` hardest:
   record the lesson and the score that forced it, never the client or the
   document.
10. **State lives in the ledgers, not in prose.** A known defect is a
    `KNOWN_GAPS.md` entry; a recurring failure shape is a `FAILURE_MODES.md`
    entry; deferred work is a `backlog/ideas-prd.md` item. Name the ledger id
    when a CHANGELOG entry defers something — the dangling-reference half is
    mechanical and fails CI. A declined enforcement mechanism goes to
    FAILURE_MODES' *Abandoned gates* with its reason, so it is a decision
    instead of a quarterly re-debate.
11. **A new gate ships with a deliberate-red run, AND answers what it prints
    when it cannot look.** Plant a violation, watch it fail, remove it, record
    the exercise in the CHANGELOG entry; guards additionally get synthetic-tree
    tests with at least one failing fixture (`tests/test_check_repo_guards.py`
    is the pattern). **The second proof is a different question**: compare,
    literally, what the check prints when its subject is absent against what it
    prints on a clean one. Same string, number or empty list means the check is
    blind and says it is clean — FM-24. A planted red is planted where the
    measurement SUCCEEDS, so it never visits that branch. Three answers, never
    two, and the third counts as a failure.
12. **Changing a fact means sweeping its restatements — mechanically, not by
    memory.** Run `python3 scripts/check/claim_sweep.py` before committing and
    read the claims touching what you changed. This is this repository's worst
    defect class, measured: twenty-six releases have carried a fix for a prose
    copy that disagreed with the code. *Grepping by hand does not count.*
13. **Prefer deleting the number to maintaining it.** A sentence that names its
    authority cannot rot; a sentence that counts can. Where a count must stay,
    it goes in a parity guard with the code as one side (`metric id ranges` and
    `gating claims` are the pattern), never in prose alone.
14. **Do not write a claim about behaviour you have not read in the code.**
    This binds `CHANGELOG.md` hardest, because an entry is what a later session
    believes. A capability sentence cites the function that implements it or it
    does not ship.
15. **Look at a real instance before writing a pattern that keys on its shape,
    and run the planted failure FIRST rather than last.** Reading the code
    cannot find a wrong model of the material, because reading uses the model
    that produced it. One `grep` at a real fixture checks the model against the
    material instead. **A check that has never fired on a real artifact is not
    a check.**
16. **A verification command is never piped, and a commit is never chained to
    one** — `preflight.py | tail && git commit` reads `tail`'s exit status.
    A rule written down and then broken does not need writing more firmly; it
    needs a tool that holds it. **`scripts/ops/release.py` performs the whole
    flow and refuses to commit when preflight fails, with no override flag.**
17. **A rebuild inherits its predecessor's facts. Losing one is a defect, not a
    simplification.** `scripts/check/check_facts.py` is the comparison: absent
    facts are reported, and a quantity the document states that its fact list
    does not is red line 1 and gates.
18. **State what "done" means for the reader before building, and loop to
    that.** Green gates are the floor; with no criterion beyond the metrics the
    loop terminates at the metrics and the reader becomes the missing check.
    Two obligations on the REPORT: a build reported as complete states its
    grade against the package's own knowledge (AR-1, AR-2), not only its gate
    results, and **a rebuild reports what it dropped** (`check_outline.py
    --against`, `check_facts.py`).
19. **Consolidating a fact is an entry in `evals/single-source.json`, never a
    new guard.** The register maps fact → owning module → the names it owns;
    `check_one_home` reads it. Two obligations come with an entry: plant the
    duplicate first and watch the guard name the owner, and give every pattern
    a `selftest` string it must match. `check_one_home`'s docstring is the
    authority on the ways the register can go blind.
20. **A design document is verified before it is shown, not after it is
    questioned.** Measured: of fifteen defects across four review rounds, only
    three needed an independent reader. Every quantitative claim in a spec
    carries the command that produced it, run at the moment the claim is
    written. Before designing any new gate or mechanism, grep `FAILURE_MODES.md`'s
    abandoned gates and `KNOWN_GAPS.md` for it — that search is step zero, not
    a review finding. A coverage claim states what its instrument cannot see,
    in the same sentence. A predicate that fails is a reason to change the
    predicate, never to drop the requirement. **Run the adversarial review
    yourself, before presenting, and say what it found** — two readers, one
    attacking the design and one strengthening it.
