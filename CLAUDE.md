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
python3 scripts/check_repo.py            # repo invariants; exit 1 on any failure
python3 scripts/check_prose.py <file>    # AI-flavor metrics (M4, M8-M11) on a deliverable
python3 scripts/check_design.py <file>   # design metrics (D1-D17) on a deliverable
python3 scripts/inspect_layout.py <file> # render a deliverable and report what the layout does
python3 scripts/export_pdf.py <file>     # PDF / 4K page rasters of a deliverable (local, Playwright)
python3 scripts/output_dir.py            # where a deliverable belongs; --create needs the user's say-so
python3 scripts/embed_font.py            # @font-face block with the face inlined
python3 scripts/embed_icons.py           # <symbol> sprite of the semantic icon set
python3 scripts/build_geography.py       # regenerate assets/vectors/ from lat/lon data
python3 scripts/build_worldmap.py        # shared-arc world topology + the golden grid
python3 scripts/build_region_palette.py  # region hues; --selftest asserts four floors
python3 scripts/globe_svg.py             # one static SVG frame of the globe
python3 scripts/regionmap_svg.py         # the flat region map, labels from the registry
python3 scripts/embed_regionmap.py       # the map runtime as one inline <script>
python3 scripts/check_globe.py           # globe maths + the JS port (needs Playwright)
python3 scripts/embed_globe.py           # the globe runtime as one inline <script>
python3 scripts/build_entrypoints.py     # regenerate every per-platform artifact; --check in CI
python3 scripts/build_fixtures.py        # regenerate the tracked test fixtures; --check in CI
python3 scripts/check_fixtures.py        # run the checkers against the fixtures and assert verdicts
python3 scripts/check_js.py              # node --check over the 8 tracked .js files + 3 embedded probes
python3 scripts/check_evidence.py        # --init | record --id X | --check: the evidence gate (see below)
python3 scripts/review_scores.py         # the six human dimensions over time; --check validates
python3 scripts/run_conformance.py       # validate | detect | run | score | report [--record] (runs are local)
python3 -m pytest -q                     # the test suite under tests/; gates in CI
python3 -m ruff check .                  # lint + the S security rules; gates in CI
python3 -m mypy                          # type-check (check_untyped_defs floor); gates in CI
bash    scripts/ci_wait.sh <PR>          # bounded wait, short-circuits on outage
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
entry, and overclaim phrases beside a waiver all fail the release. `inspect_layout.py` needs a headless Chromium (`pip install pillow
playwright && playwright install chromium`); its real output is a contact sheet
for a person to look at. **None of its design judgements gates, but it exits 1
when a check could not be measured at all** — a document whose markup it cannot
read, a role whose class it cannot find, an audit that crashed. That distinction
is the point: until 0.1.350 all three of those printed the same reassuring lines as
a clean document. **`--deliverable` gates a *document*, never this repo**: it
exits non-zero on the ten findings that are decidable rather than aesthetic
(collision, content spill, page height, hidden content, a wrapped footer, a
viewBox that does not parse, a drawing clipped by its own viewBox, an overspent
title reserve, a role split, a lost datum) and is the pre-delivery step in `SKILL.md`.
`run_conformance.py` runs it that way. Everything else it prints stays reported,
including the part-opener count, which is an observation and not a floor. `check_prose.py` is
English-only and takes `--genre {sales,internal,training}`; internal analysis
is exempt from the em-dash rule and training binds like sales. `check_design.py` reads a document's own token block, so it
grades a file against the palette that file actually declares rather than against
this repo's; a deliverable that does not use the token block is reported
`UNMEASURABLE` rather than passed. Three of its metrics **gate**, and none is a
design judgement: **D12** (handling terms and origin on every page) is a
commercial requirement on the artifact, **D14** (no `[TO FILL]`, `[TBD]` or
`{{…}}` reaching the reader) asks whether the document is finished, and **D15**
(no repository path in a footer) is D12's mirror. All three are
decidable in the way "does this page read as intentional" is not.

Its banned-phrase list is a second copy of `references/writing-rules.md` §2, so
the **ban-list parity** guard holds the two together: every phrase §2 bans must
appear in the script either as a matching pattern or in `NOT_MECHANIZED` with a
reason, and the script may not ban anything §2 does not list. Adding a phrase to
the rules without deciding what the machine does about it fails CI, which is the
point — the alternative is a rule that looks enforced and is not.

Everything the checks cannot decide — above all whether a rule change was
re-flowed into the entry points — stays with the reviewer.

## When CI is slow or down

`main` requires the `checks` status and enforces it for admins, so a GitHub
Actions incident blocks merging for everyone. Do not wait it out by polling.

1. **Ask the status page before waiting**, not after. One call to
   `githubstatus.com/api/v2/components.json` answers whether waiting is worth
   anything. Polling a capacity-constrained service also adds to the load causing
   the outage.
2. **Bound every wait.** `scripts/ci_wait.sh <PR>` does both of the above: it
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
5. Merging anyway is `scripts/emergency_merge.sh <PR>`, which verifies the merge
   result locally before it unlocks anything and restores protection on every
   exit path. It is the last resort, not the second.

## Architecture: one rule set, many entry points

`references/` is the single source of truth for rule prose:

- `references/brand.md` — the water thesis, the two brand devices (waterline, field), the ground, the acid green, the consistency rules; loaded first by SKILL.md and AGENTS.md
- `references/writing-rules.md` — output-language default, terminology red lines, banned phrases, punctuation, number discipline, the LUMI voice
- `references/storyline-templates.md` — narrative skeletons per scenario (sales / consulting / internal analysis / training), cover & closing templates, the pre-delivery critic gate
- `references/design-rules.md` — color semantics, typography, chart rules, semantic icons, layout guards, verification matrix
- `references/eval-rubric.md` — M1–M12 / D1–D17 / H1–H6 scoring rubric and the review protocol (the iteration engine)

`tokens/lumi-theme.css` and `tokens/design-tokens.json` are the authority for
palette and type values. Their palette values mirror each other exactly and must
be edited together, but the JSON is a superset: `palette_default`, `chart`,
`chart_scale_px`, and `layout` have no CSS counterpart. Where a numeric value in
`design-rules.md` disagrees with the tokens, the tokens win — the prose copies
drift.

Three entry points load these rules, and each restates part of them:

- `SKILL.md` — Claude Code entry; reads `references/` and `tokens/` on demand
- `AGENTS.md` — Codex entry; summarizes the load order and the six red lines inline
- `prompts/lumi-style-core.md` — **self-contained** single file for Kimi/DeepSeek (a strict subset of `references/`), so any substantive rule change must be re-flowed into it by hand

`adapters/platforms.json` is the **platform registry** — the single source of
install paths, capability tiers and entry files for every platform this package
claims. `adapters/*.md` are the per-platform loading notes, one per registry record and
**generated** by `scripts/build_entrypoints.py` — as are `GEMINI.md`,
`.github/copilot-instructions.md`, `.cursor/rules/lumi-style.mdc`, the plugin
manifests and `.well-known/skills/index.json`. Edit the registry, never the
artifact; `--check` runs in CI. `SKILL.md`, `AGENTS.md`,
`prompts/lumi-style-core.md` and `references/` stay hand-written, because
assembled prose is worse prose and those are the files a reader actually reads.
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
deliverables — `SKILL.md:50-62`. These are the separate rules for changing the
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
   `references/design-rules.md` §7.
9. This repo holds style rules and templates only — never add client names,
   project figures, or engagement facts. This binds `CHANGELOG.md` hardest, since
   every entry summarizes a real engagement's review: record the lesson and the
   score that forced it, never the client or the document (follow the anonymized
   phrasing of the existing entries).
10. **State lives in the ledgers, not in prose.** A known defect is a
    `KNOWN_GAPS.md` entry (a TODO in a script citing a GAP id fails CI); a
    recurring failure shape is a `FAILURE_MODES.md` entry; deferred work is a
    `Pipeline/ideas-prd.md` item. When a CHANGELOG entry defers something,
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
