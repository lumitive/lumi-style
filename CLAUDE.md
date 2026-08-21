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
python3 scripts/ops/eval_corpus.py <file>    # a deliverable against evals/thresholds.json; REPORTS, never gates
python3 scripts/check/check_prose.py <file>    # the prose metrics on a deliverable (the script's row table is the list)
python3 scripts/check/check_outline.py <outline> [--against DECK]  # the storyline beat; --against gates the deck on its own plan
python3 scripts/check/check_facts.py <contract> <file>  # the build against the facts it was built from
python3 scripts/check/check_design.py <file>   # the design metrics on a deliverable (the script's row table is the list)
python3 scripts/check/inspect_layout.py <file> # render a deliverable and report what the layout does
python3 scripts/ops/export_pdf.py <file>     # PDF / 4K page rasters of a deliverable (local, Playwright)
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
python3 scripts/check/check_evidence.py        # --init | record --id X | --check: the evidence gate (see below)
python3 scripts/ops/review_scores.py         # the six human dimensions over time; --check validates
python3 scripts/ops/run_conformance.py       # validate | detect | run [--drive] | score | report [--record] (local only: no keys in CI)
python3 -m pytest -q                     # the test suite under tests/; gates in CI
python3 -m ruff check .                  # lint + the S security rules; gates in CI
python3 -m mypy                          # type-check (check_untyped_defs floor); gates in CI
bash    scripts/ops/ci_wait.sh <PR>          # bounded wait, short-circuits on outage
```

**The deliverable path is standard library only** — nothing in `scripts/`
imports outside it at runtime. Development tools (ruff, mypy, pytest) are
pinned in `requirements-dev.txt`, installed by CI and by `preflight.py`'s
pip step, and ship in no deliverable. `.github/workflows/ci.yml` holds the
authoritative step list — deliberately not counted here: this file once said
"seventeen" while preflight's docstring said "fifteen", and both numbers were
somebody's memory of the workflow rather than the workflow.
**`check_repo.py` is ONE of those steps, and reporting it green is not
reporting the release green** — 0.1.415 was verified on eight of the gates,
pushed, and failed CI on a generator check nothing local had invoked.
`scripts/preflight.py` reads the step list out of `ci.yml` and runs all of it,
so "local green" and "CI green" are the same claim; it refuses to run a subset
if it cannot parse the workflow, and `--timing-update` records a local
per-step timing baseline that later runs WARN against (warn-only by design —
a baseline is one machine's number). Its guards are the mechanical half of the invariants below: version
stamps, version citations, the English-only red line, markdown link targets,
stale forward promises, the platform manifest, retired values, palette parity
between the two `tokens/` files, that every `var()` in `tokens/` resolves to a
custom property `tokens/` defines, that every class a checker asserts has a base
rendering in `tokens/` or a written waiver, that nothing is styled only inside a
media query, that the layouts `tokens/` defines are the layouts `check_design.py`
grades, the text ladder's contrast floor,
ban-list parity, that every statement of the output-directory default names the
same literal directory, that every generated artifact and fixture is current, that the
checkers still produce the expected verdicts on both fixtures, that the
vendored assets are intact, that no script re-grows a private copy of the
shared color/CSS implementations (`color_math.py` / `css_tokens.py`), that
the three ledgers parse and no GAP/FM/IDEA citation dangles, that the release
commit's subject carries its version (HEAD only — history is not
retroactively reddened), and that no credential-shaped string ships in a
tracked file.
The list above is representative; `check_repo.py`'s `CHECKS` tuple is the
authority, and a guard with no entry there does not run.

`tests/` holds the pytest suite: characterization tests for the shared
modules, synthetic-tree tests that prove each guard can FAIL as well as pass
(a guard only ever seen passing is FM-01 in `FAILURE_MODES.md`), and a
`--help` floor over every argparse CLI (the flag-less ones — check_repo,
check_js, check_fixtures, embed_font — are exempt by construction). Every
new gate ships with a deliberate-red
run recorded in its CHANGELOG entry.

`check_globe.py`'s browser half narrowed at 0.1.426: the JS projection port
is now held to the Python authority IN CI — the 1300-sample golden grid runs
under bare `node` (`--python-only --node`), since `projection.js` is DOM-free.
What still needs a browser (renderer parity, painted ink, occlusion) is an
operator step recorded through the evidence gate. There is still no
package.json and no JS runner beyond `node` itself; `check_js.py` syntax-parses
both JavaScript surfaces — the tracked `.js` files and the probe strings
embedded in `inspect_layout.py` (discovered by naming convention, never
hand-listed) that `py_compile` reads as prose.

`check_prose.py`, `check_design.py` and `inspect_layout.py` all measure a
**deliverable** rather than this repo. Two of them do run in CI, against the
tracked synthetic fixtures in `fixtures/` — that is the whole point of shipping
them. `inspect_layout.py` still cannot: it needs a headless Chromium, so it is
run locally — and since 0.1.424 (gating since 0.1.425) its result is
recorded through
**`check_evidence.py`**, never as a sentence in the release notes. The
evidence gate is the standing answer to GAP-002: each release writes
`releases/evidence/<version>.json`; `--init` computes which operator checks
the release diff obliges (browser layout gates, the globe's browser half,
conformance freshness), `record --id X` EXECUTES the canonical command and
machine-writes exit code + output digest + date (the schema has no verdict
field — a human never types "pass"), and `--check` gates in CI: unmet
obligations, copied digests, nonzero exits not citing an open KNOWN_GAPS
entry, and overclaim phrases beside a waiver all fail the release.
Evidence files are kept forever: they are small (under 1KB), they are the
audit trail, and the gate only ever reads the current release's file — there
is nothing to prune for and deleting evidence would be against the point. `inspect_layout.py` needs a headless Chromium (`pip install pillow
playwright && playwright install chromium`); its real output is a contact sheet
for a person to look at. **None of its design judgements gates, but it exits 1
when a check could not be measured at all** — a document whose markup it cannot
read, a role whose class it cannot find, an audit that crashed. That distinction
is the point: until 0.1.350 all three of those printed the same reassuring lines as
a clean document. **`--deliverable` gates a *document*, never this repo**: it
exits non-zero on the findings that are decidable rather than aesthetic
(collision, a starved column, content spill, page height, hidden content, a
wrapped footer, a footer whose runs sit on different baselines, a viewBox that
does not parse, a drawing clipped by its own viewBox, a stat band whose
labels render outside it, an overspent title
reserve, a role split, a lost datum, a mark drawn out of proportion to the value it declares, and a document whose content pages are mostly not drawn on at all — the code's `deliverable_verdicts` is the
authority; this list has been counted wrong in four files at once) and is the
pre-delivery step in `SKILL.md`.
`run_conformance.py` runs it that way. Everything else it prints stays reported,
including the part-opener count, which is an observation and not a floor. `check_prose.py` grades either output
language — it reads the document's own `lang`, takes `--lang` to override, and
runs the Chinese ban list and punctuation rules on a Chinese document; **M12 is
what fails an English deliverable carrying Chinese a reader can see.** It takes
`--genre {sales,internal,training}`; internal analysis
is exempt from the em-dash rule and training binds like sales. `check_design.py` reads a document's own token block, so
most of it grades a file against the palette that file actually declares rather
than against this repo's; a deliverable that does not use the token block at all
— fewer than three of the ten core tokens — is reported `UNMEASURABLE` rather
than passed. **D20 is the one that looks the other way**: every COLOUR token the
document declares that `tokens/` also defines must carry the shipped value,
because a document can be perfectly consistent with a palette of its own
invention and that is a different design language. Sizes are exempt by the same
logic that withdrew the type floor at 0.1.340. Ten of its metrics **gate**, and none is a
design judgement: **D12** (handling terms and origin on every page) is a
commercial requirement on the artifact, **D14** (no `[TO FILL]`, `[TBD]` or
`{{…}}` reaching the reader) asks whether the document is finished, **D15**
(no repository path in a footer) is D12's mirror, and **D19** (every reference
resolves inside the document — an icon pointing at no symbol, a `data-globe`
mark with no runtime) asks whether the markup can render itself, and **D20**
(the colour tokens it declares are the ones `tokens/` ships) asks whether the
palette is LUMI's at all, and **D21** (a figure that declares the
data it draws is held to it) asks whether the drawing agrees with its own
numbers, and **D22** (every page's layout is one `tokens/` defines) asks
whether the page structure is the brand's at all, and **D24** (every image ships
inside the file) and **D25** (every image names its terms) are what made lifting
the imagery restriction safe rather than a hope, and **D27** (every agenda
line quotes a title the document actually carries) asks whether the agenda is
the document's own story or a second one. All ten are
decidable in the way "does this page read as intentional" is not. The list is
`check_design.py`'s to change: a row whose target says `(gates)` gates, and the
`gating claims` guard holds this sentence to it.

Its banned-phrase list is a second copy of `references/writing-rules.md` §2, so
the **ban-list parity** guard holds the two together: every phrase §2 bans must
appear in the script either as a matching pattern or in `NOT_MECHANIZED` with a
reason, and the script may not ban anything §2 does not list. Adding a phrase to
the rules without deciding what the machine does about it fails CI, which is the
point — the alternative is a rule that looks enforced and is not.

Everything the checks cannot decide — above all whether a rule change was
re-flowed into the entry points — stays with the reviewer.

## When CI is slow or down

`main` takes changes only through a pull request, requires the `checks` status
on it, and enforces both for admins, so a GitHub Actions incident blocks
merging for everyone. (No approving review is required: the rule closes the
direct push — including fast-forwarding `main` to a branch commit that already
carries a green status — not the solo merge.) Do not wait it out by polling.

1. **Ask the status page before waiting**, not after. One call to
   `githubstatus.com/api/v2/components.json` answers whether waiting is worth
   anything. Polling a capacity-constrained service also adds to the load causing
   the outage.
2. **Bound every wait.** `scripts/ops/ci_wait.sh <PR>` does both of the above: it
   short-circuits when Actions is degraded, and otherwise checks three times over
   about four minutes and then stops. Open-ended polling turns a service problem
   into a person problem — during the 2026-08-06 outage it consumed most of a
   working session and merged nothing.
3. **Separate correctness from the gate.** `check_repo.py` answers "is this
   change good", locally and in seconds. CI only unlocks the merge button. During
   an outage, report the local verdict and hand over the decision rather than
   blocking on a queue nobody can drain.
4. **A cancelled run is a symptom, not a verdict.** Re-run it once. If it is
   cancelled again during a declared incident, stop re-running.
5. Merging anyway is `scripts/ops/emergency_merge.sh <PR>`, which verifies the merge
   result locally before it unlocks anything and restores protection on every
   exit path. It is the last resort, not the second.

## Architecture: one rule set, many entry points

`references/` is the single source of truth for rule prose:

- `references/brand.md` — the water thesis, the two brand devices (waterline, field), the ground, the acid green, the consistency rules; loaded first by SKILL.md and AGENTS.md
- `references/writing-rules.md` — output-language default, terminology red lines, banned phrases, punctuation, number discipline, the LUMI voice
- `references/storyline-templates.md` — narrative skeletons, one per storyline in its roster (sales through the investor pitch), cover & closing templates, the pre-delivery critic gate
- `references/design-rules.md` — color semantics, typography, chart rules, semantic icons, layout guards, verification matrix
- `references/eval-rubric.md` — the M / D / C scoring rubric and the review protocol (the iteration engine)
- `references/operating-rules.md` — how the work is done rather than what a deliverable is: the debug-log contract, the parallel-build protocol and its merge gate, questions-come-once, scaffold-never-fixture, and generate-a-world-figure-rather-than-draw-it. It exists because those five had their only home in an entry point, and an entry point is a restatement by design — a rule living only there has no source for its restatements to be checked against
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

`adapters/platforms.json` is the **platform registry** — the single source of
install paths, capability tiers and entry files for every platform this package
claims. `adapters/*.md` are the per-platform loading notes, one per registry record and
**generated** by `scripts/build/build_entrypoints.py` — as are `GEMINI.md`,
`.github/copilot-instructions.md`, `.cursor/rules/lumi-style.mdc`, the plugin
manifests and `.well-known/skills/index.json`. Edit the registry, never the
artifact; `--check` runs in CI. `SKILL.md`, `AGENTS.md`,
`prompts/lumi-style-core.md` and `references/` stay hand-written, because
assembled prose is worse prose and those are the files a reader actually reads —
with one owner-directed exception: `references/eval-inventory.md` is generated,
because it is a table of some one hundred and eighty numbers rather than prose,
and a hand-written copy of the checkers' numbers is the drift class this
repository has fixed twenty-six times.
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
`YYYY-MM-DD-<topic>-plan.md` that decomposes it into commits. It exists because `docs/` is gitignored
on purpose (it is where validation runs write, and a deliverable committed there
would breach the no-engagement-facts red line), so a design record had nowhere
to live and was being lost between sessions. A spec is a record of what was
decided and why, written before the work; it is **not** a source of rules. Rule
prose stays in `references/`, values stay in `tokens/`, and the shipped rationale
stays in `CHANGELOG.md`. A spec that has been implemented stays as history and is
never cited as authority.

**Drift is this repo's main hazard, and the checks catch only its mechanical
half — semantic drift between prose copies is invisible to them.** After changing
`references/`, re-read all three entry points *and* `README.md`, which
independently restates the file map, the design language, and the iteration
protocol. (The two stale spots this section used to name — pre-0.1.332 hexes in
`prompts/lumi-style-core.md` and a Simplified-Chinese default in `AGENTS.md` —
were both fixed by 0.1.349 and 0.1.333 respectively; verified at 0.1.350.)

**Drift also runs the other way: from a check into the rules.** A probe that
keys on class names is asserting a vocabulary, and that vocabulary has to ship in
`tokens/` or it is a private convention borrowed from whatever document the probe
was developed against. 0.1.349 audited ten roles against six class names that
existed nowhere in this repository. Prefer a check that reads the shipped tokens;
where it cannot, make it name what it failed to find.

## Maintenance conventions

("Red lines" in this repo names the six non-negotiable *content* rules for
deliverables — SKILL.md's "Six non-negotiable red lines". These are the
separate rules for changing the
repo itself.)

1. **Repository language is English only.** Chinese strings appear in rule files
   only as rule *data* for Chinese-language output (banned phrases, punctuation
   examples) — never as document prose.
2. **Rule changes come only from review retrospectives.** No rule is added or
   removed without a documented case (a reader review with a dimension diverging
   ≥2 points, or a reported defect). Do not invent or "improve" rules
   speculatively. A retrospective may legitimately end in an *anchor* revision or
   a recorded no-change instead of a rule revision — `references/eval-rubric.md`
   is itself editable under the protocol. A lesson is promoted to a formal rule
   once it has appeared across two documents.
3. **A rule revision requires a `CHANGELOG.md` entry and a version bump.**
   The repo carries **one version**, and it now lives in three tiers rather than
   the five files this rule used to enumerate. Saying "five places… and they are
   the only ones" stopped being true at 0.1.352 and stayed in the file for six
   releases, which is the drift this document exists to warn about, in the
   document itself.

   - **Hand-stamped and checked.** `metadata.version` in SKILL.md frontmatter,
     the newest CHANGELOG heading, the stamp in each of the three `tokens/`
     files, the blockquote in `AGENTS.md`, and the snapshot line in
     `prompts/lumi-style-core.md`. `check_versions` compares the first five;
     `check_version_citations` compares the entry points against `ENTRY_STAMP`,
     which declares where each one's stamp lives. **Adding a token file means
     adding it to the tuple in `check_versions`; adding an entry point means
     adding it to `ENTRY_STAMP`.** Those two tables are what keep this list
     honest, and a stamp with no declared position fails rather than being
     skipped.
   - **Generated and regenerated.** Everything `build_entrypoints.py` writes.
     Deliberately not a list: the first version of this tier named six files when
     there were eight, which is the same enumeration failure the old "five
     places" wording was replaced for. `--check` is the forcing function and it
     needs no inventory.
   - **Not a stamp.** Historical notes inside `tokens/lumi-theme.css`
     ("v0.1.333: light-first…") name the version that introduced a change —
     leave them alone. The CLI builds recorded in `conformance/CONFORMANCE.md`'s
     table rows belong to other projects; that file's own first-line skill stamp
     is a stamp, and is in `ENTRY_STAMP`.

   Commit messages follow `X.Y.Z — comma-separated summary of the rule changes`.
   **A branch carrying several releases is MERGED or REBASED, never
   squashed** — a rebase merge keeps one commit per release, which is the
   form the two guards below need, and is how 0.1.457–0.1.522 landed (an
   audit read the absence of merge commits as the absence of pull requests;
   it was the absence of squashes). If a branch is squashed anyway, its
   subject takes the NEWEST version, never the range and never the PR title. Two independent pieces of this repo's machinery assume
   one commit per release: `check_commit_convention` holds a
   CHANGELOG-touching subject to `X.Y.Z — summary` *and* to the newest heading
   in that same commit, and `check_evidence.py --init` finds the previous
   release by looking for a commit whose subject starts with it. Squashing
   PR #94 put `0.1.443–0.1.447` — a title written before the branch's last
   release — on a tree whose CHANGELOG said 0.1.448: main's own CI went red on
   the merge, and the next release could not compute its diff base. Set the
   subject at merge time (`gh pr merge --subject`) and read it against the
   CHANGELOG before pressing it.

4. **A number in a rule states whether it is a floor, a ceiling, or a target.**
   This repo has now shipped three regressions from the same root: 0.1.332's
   "3–6 word headline" was a ceiling read as a target and deleted every evidence
   figure from deck titles; 0.1.336's "short sentences" was a direction read as a
   target and drove sentence variance to zero; 0.1.337's "titles budget two lines"
   was a ceiling read as a target and folded every title in half. An author
   optimizes toward any number you give them, so say which way it points.
5. **A rule may not mandate an asset the package does not ship, and a rule may not
   ban a whole category because one member of it is unavailable.** 0.1.332 required
   an embedded display face and shipped none, so it rendered nothing until 0.1.337.
   §5 required a semantic icon library and shipped none, so deliverables carried
   zero icons until 0.1.338. The cover rule banned all imagery because there was no
   photo library, when the risk was photography alone. Ship it, or scope the ban
   to the actual risk.
6. **A prescribed value carries the floor below which it stops working.** The
   alpha ladder had no contrast floor, the type scale had no minimum size, the
   callout tiers had no budget, the figure vocabulary had no consistency
   requirement. Each gap produced a defect a reader could see, and each is now a
   `check_design.py` metric. If a rule hands out numbers, hand out the limit too.
7. **The skill's own conventions are the reference. A validation artifact never
   is.** When a deliverable is built to exercise these rules, the engagement it
   is built from supplies *facts* and nothing else: not conventions, not
   registries, not naming, not versioning, not layout. Those come from
   `references/` and `tokens/`. Reading a convention back out of a test document
   reverses the direction of authority and quietly imports another project's
   decisions. (Field-tested: while validating 0.1.337 the author cited an
   engagement's document registry as a source of truth about deliverables, and
   raised its staleness as an issue for this repository. It was neither.)
8. **Ship-blocking asymmetry between the checks and the eye.** A metric that
   passes is not a verified document. `check_design.py` reported all-clear on a
   figure whose band was clipped by its own viewBox, because the script measures
   declared CSS and cannot see rendered geometry. Screenshot every figure page at
   the design viewport and look at it. See the browser checks in
   `references/design-rules.md` §8.
9. This repo holds style rules and templates only — never add client names,
   project figures, or engagement facts. This binds `CHANGELOG.md` hardest, since
   every entry summarizes a real engagement's review: record the lesson and the
   score that forced it, never the client or the document (follow the anonymized
   phrasing of the existing entries).
10. **State lives in the ledgers, not in prose.** A known defect is a
    `KNOWN_GAPS.md` entry (a TODO in a script citing a GAP id fails CI); a
    recurring failure shape is a `FAILURE_MODES.md` entry; deferred work is a
    `backlog/ideas-prd.md` item. When a CHANGELOG entry defers something,
    name the ledger id it now lives under — this is a prose rule, not a gate
    (AG-1 records why the mechanical version was declined), but the
    dangling-reference half IS mechanical: a cited id that no ledger defines
    fails CI. A declined enforcement mechanism goes to FAILURE_MODES'
    "Abandoned gates" with its reason, so it is a decision instead of a
    quarterly re-debate.
11. **A new gate ships with a deliberate-red run.** Plant a violation, watch
    the gate fail, remove it, record the exercise in the CHANGELOG entry.
    Guards additionally get synthetic-tree tests with at least one failing
    fixture (`tests/test_check_repo_guards.py` is the pattern). This repo has
    shipped three checks that ran green and were later found incapable of
    failing; a gate's first proof is that it can go red.
12. **Changing a fact means sweeping its restatements — mechanically, not by
    memory.** Run `python3 scripts/check/claim_sweep.py` before committing and
    read the claims touching what you changed. This is convention 3's problem in
    general form and it is this repository's worst one, measured: **twenty-six of
    its releases have carried a fix for a prose copy that disagreed with the
    code, and five of the last ten did** — the rate is rising, not falling. The
    mean time to notice, where the entry says, is four to eleven releases. Two
    whole releases (0.1.360, 0.1.429) exist only to do this work.
    *Grepping by hand does not count as sweeping.* 0.1.443 re-synced one list in
    four prose files and missed two code comments; 0.1.451 re-synced one count in
    two files and missed eight, one of them in `AGENTS.md` eighty-six lines below
    the line it had just corrected, beside that file's own written confession
    about this exact drift.
13. **Prefer deleting the number to maintaining it.** A sentence that names its
    authority cannot rot; a sentence that counts can. `preflight.py`'s docstring
    is the model — "how many is whatever the workflow says today, never a number
    written here" — and 0.1.429 *deleted* the CI step count rather than
    correcting it. Where a count must stay, it goes in a parity guard with the
    code as one side (`metric id ranges` and `gating claims` are the pattern),
    never in prose alone.
14. **Do not write a claim about behaviour you have not read in the code.** This
    binds `CHANGELOG.md` hardest, because an entry is what a later session
    believes. 0.1.450's entry said Cursor's conformance tasks "ran
    non-interactively like any other"; `run_conformance.py` invoked no agent and
    never had, and what had changed was `shutil.which` finding a binary. The
    entry was corrected at 0.1.452, and the capability was BUILT at 0.1.454 —
    which is the order these two things go in. A capability sentence cites the
    function that implements it or it does not ship.

15. **Look at a real instance before writing a pattern that keys on its shape,
    and run the planted failure FIRST rather than last.** Six checks in the
    0.1.457–0.1.473 run were wrong on their first implementation, and every one
    encoded an assumption about the material rather than a mistake in the logic:
    that a rule id should say where the rule is; that a summary keeps its
    distinguishing word; that in English the label precedes the number; that a
    figure element is `<figure>` when this package uses `div.fig`; that a phone
    number appears in prose when the scan covered attributes too. **Reading the
    code cannot find these, because reading uses the model that produced them.**
    One `grep` at a real fixture costs seconds and checks the model against the
    material instead. Convention 11 already requires a deliberate-red run; what
    changes here is *when*: planted first it kills a wrong model in minutes,
    planted last it confirms code that has already grown around one. **A check
    that has never fired on a real artifact is not a check.**

16. **A verification command is never piped, and a commit is never chained to
    one.** `preflight.py | tail && git commit` reads `tail`'s exit status, so a
    red preflight was committed twice in one session — after the same lesson had
    already been recorded in an earlier one. A rule written down and then broken
    does not need writing more firmly; it needs a tool that holds it.
    **`scripts/ops/release.py` performs the whole flow and refuses to commit
    when preflight fails, with no override flag**, on the same reasoning that
    makes `check_evidence.py` execute its own commands rather than accept a
    typed verdict.

17. **A rebuild inherits its predecessor's facts. Losing one is a defect, not a
    simplification.** Measured across two consecutive builds of one business
    plan: the second silently dropped **eleven** facts the first carried — four
    platform names, **five of the seven market names whose count the deck still
    stated**, and two delivery figures — and all forty-odd deliverable gates
    reported green, because not one of them had anything to compare the document
    to. `scripts/check/check_facts.py` is that comparison: absent facts are
    reported, and a quantity the document states that its fact list does not is
    red line 1 and gates. This is `references/exemplars/karpathy-notes.md`
    §3's surgical-change test — *every changed line traces to the request* —
    applied to a deliverable rather than to code.

18. **State what "done" means for the reader before building, and loop to that.**
    Green gates are the floor. `SKILL.md` has said so since 0.1.344 — *"Passing
    metrics is necessary but never sufficient"* — and the practice drifted
    anyway: five builds in two days, each delivered gate-green, each returned by
    the owner with defects no gate can see. EX-4 §4 names the mechanism:
    **weak success criteria require constant clarification**, so with no
    criterion beyond the metrics the loop terminates at the metrics and the
    reader becomes the missing check.
    Two things follow, and both are obligations on the report rather than on the
    document. **A build reported as complete states its grade against the
    package's own knowledge** — how many titles are findings rather than labels
    (AR-1), how many takes carry the reader's implication rather than restating
    the title (AR-2) — not only its gate results. And **a rebuild reports what it
    dropped**: `check_outline.py --against` and `check_facts.py` both exist to
    make that answerable without waiting for a review.
