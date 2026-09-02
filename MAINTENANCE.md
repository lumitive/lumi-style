# Maintenance conventions — the full text and the cases behind them

This is the ONE home for the twenty conventions that govern changes to this
repository. `CLAUDE.md` carries the same twenty, numbered identically, as the
rule alone; this file carries each rule together with the shipped defect that
forced it. The numbering is load-bearing — a convention is never renumbered,
and a retired one keeps its number with a note. `grep -rhoE 'convention [0-9]+|CLAUDE\.md rule [0-9]+' scripts/ tests/ references/ SKILL.md AGENTS.md | wc -l` says 95 at 0.1.681.

`CONTRIBUTING.md` is a third, shorter view of the same set, written for a
person opening a pull request. Where the three disagree, this file wins,
because it is the one that carries the reasoning.

**Why the split exists.** These conventions used to live in `CLAUDE.md` in
full, and `CLAUDE.md` is loaded into context on every single turn of every
session in this repository. The rules have to be there — an agent that cannot
see a rule cannot follow it. The case histories do not: they are read when a
convention is being applied, argued with, or revised, which is a moment a
person or an agent can open a file for. Moved at 0.1.681; nothing was deleted.

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
11. **A new gate ships with a deliberate-red run, and answers what it prints
    when it cannot look.** Plant a violation, watch the gate fail, remove it,
    record the exercise in the CHANGELOG entry. Guards additionally get
    synthetic-tree tests with at least one failing fixture
    (`tests/test_check_repo_guards.py` is the pattern). This repo has shipped
    three checks that ran green and were later found incapable of failing; a
    gate's first proof is that it can go red.
    **The second proof is the unmeasurable branch, and it is a different
    question.** Ask what the check prints when the thing it measures is not
    there, and compare that answer *literally* with what it prints on a clean
    document. If the two are the same string, number or empty list, the check
    is blind and says it is clean — FM-24, six shipped instances in
    0.1.608-0.1.612, every one a check that could fail and had been seen
    failing. **A planted red is planted where the measurement SUCCEEDS**, so it
    never visits the branch this lives on; FM-24 is FM-01's specialization
    rather than a rival, and FM-01's prevention is necessary and not
    sufficient. Three answers, never two, and the third counts as a failure:
    `check_prose`'s `blind` verdict is the precedent and `evals/gates.json`'s
    `na_means` is the same distinction one layer up. Reading the code does not
    find these — reading uses the model that wrote them, which is convention
    15's argument about patterns and holds equally about silences.
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

19. **Consolidating a fact is an entry in `evals/single-source.json`, never a
    new guard.** The register maps fact → owning module → the definition names,
    the retired private spellings, and the non-`def` shapes it owns;
    `check_one_home` reads it, and a waiver is a written decision that must name
    a reason and must still be needed. **Adding the next fact is one entry.**
    This is a rule about the rule: before 0.1.634 the mechanism was two
    hand-written guards for two facts, so consolidating a third meant writing a
    third guard — the duplication being refused, one layer up, in the code that
    refuses it. Two obligations come with an entry, and they are conventions 11
    and 15 in this specific setting: **plant the duplicate first** and watch the
    guard name the owner, and **give every pattern a `selftest` string it must
    match**, because a regex that has quietly stopped matching prints exactly
    what a clean tree prints. The register itself is held to its owners, and the list of ways
    it can go blind is `check_one_home`'s docstring rather than this sentence —
    a `def` name the owner does not define, a fact that declares nothing to look
    for, a key the schema does not define, two facts owning one name, a missing
    owner, a dead waiver, a pattern that no longer matches its own selftest, and
    a scan that visited no files are all findings, on one reasoning: an entry
    that guards nothing is worse than no entry, because it reads as coverage.
    That list grew by four the first time a review looked at it, which is why
    the authority is the code.

20. **A design document is verified before it is shown, not after it is
    questioned.** Measured on 2026-09-01: one spec went through four review
    rounds and every round found defects — fifteen in total, and the owner had
    to ask for each round. Sorted by what would actually have caught them, only
    **three** needed an independent reader. The other twelve were preventable by
    the author, and each has a cheap rule:

    - **Five were numbers or citations asserted without being run.** A chain
      link marked `ok` that measurement showed broken; `assemble.py:948` in a
      tree whose longest such file is 850 lines; "both give the same two
      findings" where one gives four; a grading baseline that string-sorted `r9`
      after `r11` and so read a two-revision-old document. **Every quantitative
      claim in a spec carries the command that produced it, and the command is
      run at the moment the claim is written.** A number without its command is
      a number nobody has checked, including its author.
    - **Two re-proposed a mechanism this repository had already declined in
      writing** — FM-23, and AG-10's shape twice in one session. **Before
      designing any new gate, guard or mechanism, grep `FAILURE_MODES.md`'s
      abandoned gates and `KNOWN_GAPS.md` for it.** That search is step zero,
      not a review finding. Overruling a written refusal is legitimate and needs
      convention 2's documented case; overruling one *without noticing it
      exists* is FM-15.
    - **Three described the instrument's reach as the requirement's** — "0 false
      negatives" about a predicate that could not see seventeen further cases,
      "every row machine-checkable" where four were attested by a person.
      **A coverage claim states what its instrument cannot see, in the same
      sentence.** This is FM-24 moved up a layer: a document that reports its
      own blind spot as clean is the same defect as a check that does.
    - **Two shrank the scope when a sub-part met resistance** — four changes
      became three when one predicate failed, then effectively one file. **A
      predicate that fails is a reason to change the predicate, never to drop
      the requirement.** Where a plan carries a checklist, that checklist is
      append-only: a row is re-scoped and re-measured, never deleted, and
      retiring one needs a documented case.

    **What remains for an independent reader is the fourth class**, and it is
    the one that earns the cost: contradictions visible only on a full read. The
    worst of them: a plan graded on a number that one of its own refusals
    forbade it to move. No local check finds that; a reader who holds the whole
    document at once does.

    So: **run the adversarial review yourself, before presenting, and say what
    it found.** Two readers is the measured shape — one attacking the design and
    one strengthening it. The reviews on 2026-09-01 overturned the plan's
    headline arithmetic, its scope, and its success criterion; none of that
    survived to the owner, which is the point. A design shown without them has
    not been finished, and the audit round the owner had to ask for four times
    is the author's job, not hers.

---

# The checks, in full

The long form of `CLAUDE.md`'s *Checks* section, moved here at 0.1.682 for the
same reason the conventions' case histories were moved at 0.1.681: `CLAUDE.md`
is read on every turn, and what a checker's history explains is read when the
checker is being changed. Nothing below was deleted; the sentences `CLAUDE.md`
kept are the rules, and the ones here are why.


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
vendored assets are intact, that no script re-grows a private copy of a fact
`evals/single-source.json` gives one home to, that
the three ledgers parse and no GAP/FM/IDEA citation dangles, that the release
commit's subject carries its version (HEAD only — history is not
retroactively reddened), and that no credential-shaped string ships in a
tracked file.
The list above is representative; `check_repo.py`'s `CHECKS` tuple is the
authority, and a guard with no entry there does not run.

**Every verdict a deliverable can receive is declared in `evals/gates.json`**,
with the concept it belongs to (`family`), the release that introduced it
(`since`), whether an `n/a` from it is an honest silence (`na_means`) or a
measurement that did not happen, and — on every GATING row — what it grades
(`subject`), so a clean sheet can say how much it held rather than only that it
was clean. `checker` and `severity` are held to the
checkers themselves by the `gate declarations` guard, and `subject` by
`vacuous gates`, so the register adds knowledge and cannot contradict.
(`subject` is `key`, `key.field`, or the literal `always`. It is declared
rather than discovered because absence has a shape no probe can see: a gate
whose row prints its VIOLATION count renders identically on a document that
gave it nothing and one whose subject is flawless.) **A gate binds a document built at or after its
`since`** — an older deliverable reports `not held`, which is neither a pass nor
a failure — and a document with no version stamp is held to everything, because
an absent stamp must not become an exemption. This exists because the gate set
applied was always HEAD's: `built_version` was captured and read by nothing that
decided anything, so a deck accepted at 0.1.449 was failed by a rule written
after it and the failure read exactly like a defect.

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
what fails an English deliverable carrying Chinese a reader can see** — and,
since 0.1.575, a document carrying Chinese that declares NO language, which it
reports `blind` rather than exempting, because silence would otherwise be the
cheapest exemption there is (`writing-rules.md` §0 is the rule; `blind` is a
fourth verdict beside ok / FAIL / n/a, and it fails). Since
0.1.559 it exits the way `check_design.py` does — **a prose row fails the run if
and only if its target is zero and it does not say `(reported)`** (GAP-029, and
`grade`'s docstring is the authority). A target of zero is a line the document
either crosses or does not; a target that is a share is a direction, and an
author optimizes toward any number you give them. It takes
`--genre {sales,internal,training}`; internal analysis
is exempt from the em-dash rule and training binds like sales. `check_design.py` reads a document's own token block, so
most of it grades a file against the palette that file actually declares rather
than against this repo's; a deliverable that does not use the token block at all
— fewer than three of the ten core tokens — is reported `UNMEASURABLE` rather
than passed. **D20 is the one that looks the other way**: every COLOUR token the
document declares that `tokens/` also defines must carry the shipped value,
because a document can be perfectly consistent with a palette of its own
invention and that is a different design language. Sizes are exempt by the same
logic that withdrew the type floor at 0.1.340. The list of gating design metrics lives in `CLAUDE.md` and only there: the `gating claims` guard holds that sentence to `check_design.py`, and a second copy here would be exactly the drift convention 12 is about.

Its banned-phrase list is a second copy of `references/writing-rules.md` §2, so
the **ban-list parity** guard holds the two together: every phrase §2 bans must
appear in the script either as a matching pattern or in `NOT_MECHANIZED` with a
reason, and the script may not ban anything §2 does not list. Adding a phrase to
the rules without deciding what the machine does about it fails CI, which is the
point — the alternative is a rule that looks enforced and is not.

Everything the checks cannot decide — above all whether a rule change was
re-flowed into the entry points — stays with the reviewer.

