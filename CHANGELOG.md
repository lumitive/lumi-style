# Changelog

Rule revisions come only from review retrospectives (divergence ≥2 → retrospective
→ revision), recorded here with a version bump.

## 0.1.363 — the first agent outside Claude Code, and the checker was wrong

Cursor was installed from the registry path, driven by hand through all three
conformance tasks, and scored. **Three of three pass** — the first real reading
this scoreboard has ever carried, and the first evidence that the claim behind
this whole release line survives contact with a different model.

| task | result |
|---|---|
| red-line recall | **5/5** — seal red and its hex, "AI never signs", "source or derivation", "exactly one focal element" |
| de-AI rewrite | **pass** — 14 seeded banned phrases to 0 |
| twelve-page deck | **pass** — every design metric clean, including D12 |

**The one failure in the first run was ours.** T1 came back `M9_dashes = 1`, and
the dash was `<td>&#8212;</td>` — an empty-cell placeholder, the standard
typographic convention for "no value". M9 exists to catch em-dashes in *prose*, an
AI-flavor tell; it counted a table cell and failed a deliverable that had no such
dash in a sentence anywhere. The numeric-range exemption already in the checker
shows the mechanism was right and the case was simply missed. Cell placeholders,
in both literal and entity form, are now exempt.

This is worth recording as a class: **we had never run these checkers against
output we did not write.** Every fixture in this repository was authored by the
same hand that authored the checks, so a convention we happened not to use was a
convention the suite could not see. The fixtures now carry both cases — a
placeholder that must not fire, and a prose em-dash that must — and removing the
exemption fails the suite.

**A task shorter than the checker's floor measures nothing.** T1 asked for six
pages while M11 needs eight titles to grade, so it reported `n/a` every run and
the task could never exercise the metric it was scoring against. It asks for
twelve pages now.

**`run --agent <id>`** prepares a task directory for a platform that answers no
probe. Cursor is an IDE, Antigravity is an IDE, Kimi and DeepSeek are API models —
four of twelve platforms can never be detected, and the harness only served the
ones that could, so the most common case required building the directory by hand.

**`report --run` now reads `scores.json`** instead of rendering "not run" into
every cell regardless. An agent driven by hand shows its real verdicts and its CLI
column reads `driven by hand`, which is what it is.

## 0.1.362 — the fixes had been re-enacting the defect they closed

A second review of the fix releases returned a verdict worth recording plainly:
**every one of the four contained at least one fix that re-enacted the defect
class it was written to close.** Five rounds now. That is not bad luck.

**The raise added to catch an empty description could not catch an empty
description.** `skill_field` returned early on an inline scalar, so
`description: ""` — the precise case the guard's own comment cites — never
reached the emptiness test, and the manifests shipped an empty field with CI
fully green. The test now runs on both paths.

**The scoreboard read one flag and ignored the other.** 0.1.358 fixed `score`
passing a crashed checker by reading the `unparseable` flag it had been writing
and never reading. It went on writing the checker's **exit code** into every
record and never reading that: `require` names two metrics of eighteen, so an
artifact failing sixteen others scored `pass`. Same defect, same release, one
field over. A parseable report that graded nothing now counts as unparseable too
— a `deliverable` glob matching a directory produced exactly that and read as a
pass.

**The fixture was still shaped around the bug it was supposed to test.** 0.1.359
fixed the footer parser and left the fixture using spans to avoid the old one, so
the buggy regex still passed the suite — the parser fix was never tested by
anything. The fixture footer now nests a `<div>` deliberately, and reinstating the
old regex fails the suite, which is the only evidence that the fix is real.

**The stale-promise guard, having stopped over-matching, stopped matching at
all.** Removing the bare `from` in 0.1.361 cured the false positives on
retrospective citation and blinded it to its founding case — the registry's own
*"from 0.1.354 … will generate"*. An inventory of verb phrases was the wrong
shape in both directions; it now matches any shipped version named in a
future-tense sentence, and reads the generated entry points and manifests it
previously could not see.

**Recall scoring, fixed for one hole, opened another.** Matching by ordinal
position marked a correct answer sheet 0/5 when the agent echoed the prompt's own
five numbered questions above its answers — failing a recall task for a formatting
reason unrelated to recall. It keys on the literal number now.

Also closed: a run directory with nothing in it reported zero rows and exit 0;
unknown task directories were dropped silently, so renaming a task erased every
prior result for it; a task with an empty `score` list passed anything, and four
other malformed shapes crashed mid-scoreboard and discarded every row already
scored; a guard returning `None` read as a guard that found nothing; a `probe` of
the wrong type published an installed agent as absent.

*The pattern is the finding.* Five rounds of hand-written guards, each closing a
defect and carrying a new instance of it. What has actually worked, every time, is
mutation testing — reintroducing the defect and checking the guard notices. That
belongs in the suite rather than in a reviewer's hands, and it is the next thing
this repository needs.

## 0.1.361 — half a vocabulary makes a check look wired up

A review of the four fix releases found the fixes had reproduced the defect class
they were fixing, for the third round running.

**`.foot .src` was never shipped, so an audit reported success on every document
that will ever be measured.** 0.1.359 added `.cap .srcline` to `tokens/` to close
the assert-before-you-ship gap, and shipped only half the pair: the source-echo
audit compares a figure's source line against the footer's, and `.src` existed
nowhere — not in `tokens/`, not in `references/`, not in either fixture. So
`footSrc` was structurally always null, the comparison never ran, and the probe
printed *"no page states the same source twice"* unconditionally. **That is worse
than shipping neither**, because the check now looked wired up. `.foot .src`
ships, the fixture emits it, and the audit reports `NOT MEASURED` when there is
no pair to compare rather than reporting success.

**A task file documented behaviour its code did not have.** T3's new `scoring`
field claimed word-boundary regexes "matched per numbered answer line". The code
matched the whole document, so `\bone\b` for question five was satisfied by
question three's own "no one" — and a one-line reply answering nothing scored
**5 of 5**. Answer *i* is now matched against line *i*. The same junk reply now
scores 0 of 5. Writing the claim into the file before the code was worse than the
honest substrings it replaced.

**The rewritten maintenance rule 3 re-enumerated, and was wrong the day it
shipped.** It replaced "five places… and they are the only ones" — false for six
releases — with a tier naming six generated files when there were eight. That
tier now says "everything `build_entrypoints.py` writes" and deliberately lists
nothing: `--check` is the forcing function and it needs no inventory. Rule 3 also
filed `conformance/CONFORMANCE.md` under "not a stamp" while line 1 of that file
is a first-class skill stamp, hand-bumped in the same release. It is in
`ENTRY_STAMP` now, so a stale one fails instead of staying legal forever.

**`check_stale_promises` was one sentence from a false failure.** Its pattern
included a bare `from`, which matches "carried over from 0.1.352", "survived from
0.1.340", "renumbered from 0.1.328" — retrospective version citation being this
repository's entire documentation voice. It would have failed CI while asserting
the opposite of what the sentence said. Every alternative is future-tense now.

**0.1.358 silently mangled a token authority.** A `json.dump` round-trip with
`ensure_ascii=True` and no trailing newline turned seven em-dashes in
`tokens/design-tokens.json` into escapes and dropped the final byte. Nothing in
that release mentioned touching the file and no guard catches encoding — palette
parity compares values. Restored.

Also: `run` announced a directory it had not created when few agents were
detected, which is the case the scoreboard itself documents; `expected.json`
overstated what its new coverage buys, since four D-metrics are reported rather
than graded and both D3 tiers pass vacuously on fixtures carrying no tier-1
callout; `CLAUDE.md` claimed in one paragraph that CI cannot run the deliverable
checkers and in another that it runs them on the fixtures every push — CI does run
two of the three; and a duplicated draft comment in `inspect_layout.py` is gone.

*Outstanding and named:* the reference fixture reports `COLUMN WEIGHT` on 12 of 14
pages at A4, because its two cells carry very different ink. It is a reported
diagnostic that gates nothing, and it is a design job on the fixture.

## 0.1.360 — the documentation catches up with six releases

Nothing new is built here. Five releases of machinery landed while the files that
describe the repository went on describing the repository as it was at 0.1.351,
and `CLAUDE.md` names that exact hazard on its own first page.

**Maintenance rule 3 had become false, in the document that binds.** It said the
version lives in "**five places** … and they are the only ones a version string
lives." It stopped being true at 0.1.352 and stayed for six releases. The version
now lives in three tiers and the rule says so: hand-stamped-and-checked (SKILL.md,
CHANGELOG, three token files, `AGENTS.md`, the core prompt), generated (the plugin
manifests, the `.well-known` index and the three pointer files, which
`build_entrypoints.py --check` keeps current), and not-a-stamp (historical notes
in the theme; third-party CLI versions on the scoreboard). The forcing function is
named for each: adding a token file means adding it to the tuple in
`check_versions`, adding an entry point means adding it to `ENTRY_STAMP`, and a
stamp with no declared position fails rather than being skipped.

**The Checks block listed one of the four new scripts** and the CI-guard summary
listed none of the three new guards, so three of the five commands a reviewer must
run to reproduce a release were undocumented in the file that documents the
commands. `README.md`'s file map was unchanged from 0.1.351 and had no entry for
`fixtures/` or `conformance/` at all, though both are tracked top-level
directories the README already links into.

**One sentence in `CLAUDE.md` was unparseable** — two edits collided in the clause
that states where the `references/`-wins precedence rule is documented.

**The registry made two claims it could not support.** Its Hermes record cited
OpenClaw's repository as Hermes documentation — a different project — while the
record's own waiver said no documentation could be cited; and it declared a CLI
probe that has never been run, which satisfied the guard built to force unverified
claims into the open, because that guard only asked whether the field was null.
Both are now null with written waivers. The registry also carried a hand-written
version stamp, unguarded and four releases stale; it is gone, because the registry
is not a copy of the rules and has nothing to drift from.

**The third-party version exemption was file-wide.** It was justified entirely on
the agent CLI builds the scoreboard records, but exempted the whole file,
including the skill's own stamp on its first line — so the one file that makes
versioned claims about this repository was the one file where those claims went
unchecked. It is now scoped to the table rows that carry them. Falsified: a bogus
`lumi-style 0.9.999` in the scoreboard's prose now fails.

## 0.1.359 — the fixture suite starts proving what it claimed

0.1.355 shipped two fixtures to test the check scripts, and the review found the
suite could not do the job it was built for.

**Ten of thirteen design metrics were asserted on neither fixture.** `D1_contrast`,
`D6_footer`, `D8_support_line`, `D9_layout_spread`, `D10_label_icons`,
`D13_lime_as_text` and four more returned `ok` on both documents and were checked
against nothing, so any of them rewritten to `return "ok"` unconditionally would
have passed the suite. That is the 0.1.350 defect one level up: a regression test
built to prove the checkers fire, unable to notice a checker that stopped firing.
`expected.json` now asserts every metric each checker emits, on both fixtures.

**The one gating design check had a real parsing bug, and the fixture was written
around it.** `d12_commercial_footer` captured the footer non-greedily to the first
`</div>`, so a deliverable wrapping its handling terms in a nested `<div>` failed
the only check that blocks a ship — for a reason having nothing to do with the
terms being present. `build_fixtures.py` carried a comment explaining precisely
this and used spans to avoid it, which guaranteed the regression suite could never
surface it. That is the letter of `fixtures/README.md`'s own rule, written in the
same release: **never edit a fixture to make a check pass.** The parser now
balances the element's own tags, and D6 and the colophon check, which carried the
identical shape, use it too.

**`.srcline` and `.f-acc` were asserted before they were shipped.** The
component-colour audit keys on `.f-acc` and both fixtures emit both classes, while
neither existed in `tokens/`. This is the reverse-drift CLAUDE.md names and the
defect 0.1.349 was penalised for, at smaller scale but load-bearing rather than
incidental: they were gated by `--check` in CI. Both now ship.

**Two recorded numbers were wrong, and one task was unfailable.** T2 claimed six
banned phrases in its seeded passage; `check_prose.py` measures fourteen. T3's
recall key used bare substrings, so `"not"` matched *note*, *cannot* and
*nothing*, `"1"` was guaranteed by the prompt's own instruction to number the
answers, and `"red"` matched *red line* and *required* — three of five questions
could not be failed. Measured after the fix: an answer sheet of "I do not know /
Not sure / Cannot say / No idea / Nothing" scores **0 of 5**, where it previously
scored 3. A recall task an agent passes without loading anything measures nothing.

Also: `glob` is now `sorted`, so an agent that leaves a second Markdown file
alongside its answer cannot make the scored artifact depend on filesystem order.

*Not fixed here, and worth naming rather than burying:* `deck-pass.en.html` still
uses one layout on all fourteen body pages and carries none of the eight semantic
icons — the pathology `D9` and `D10` exist to report. Both metrics are now
asserted, so the decay is at least visible; making the reference deliverable
actually model layout variety is a design job, not a test job, and it is
outstanding.

## 0.1.358 — absence stops meaning assent

A review of the five preceding releases mutation-tested every new guard and found
the same defect in all four new scripts and three of the guards: **the code read
absence as agreement.** A missing frontmatter field, an empty section, an omitted
flag, an unemitted verdict, an unparseable report, an empty spec — each was
treated as "fine" rather than "unknown". That is the defect 0.1.350 removed from
`inspect_layout.py`, reproduced inside the machinery built to prevent it.

**`--check` certified garbage.** `skill_field()` returned `""` for a field it
could not find, so renaming `description:` in `SKILL.md` rendered three manifests
with an empty description and `build_entrypoints.py --check` called them current —
with the same sentence it uses for correct output. The structural point is worth
keeping: `--check` compares the tree against what the generator produces *now*, so
it can catch a stale tree and can never catch a generator whose extraction failed.
Extraction now raises. So does `red_lines()` on an empty section, which had let
all three pointer files ship a heading promising six non-negotiable rules with
nothing beneath it, every guard green.

**The conformance scoreboard passed a crashed checker.** `require` was checked
per-checker, which forced an `is not None` clause to skip the other checker's
metrics — and that clause also swallowed a required metric that reported nothing
at all. A document using none of LUMI's tokens returns `UNMEASURABLE`, so an agent
emitting exactly that scored green. `require` is now checked once against the
union of every checker's verdicts, a metric that never reported is a failure, and
the `unparseable` flag that was written into the record and never read is now a
failure too. An empty JSON list also crashed the scorer mid-scoreboard.

**Deleting one optional field stripped a published warning.** `path_verified` was
only checked for an explicit `false`, so removing it turned an install path the
repository admits is a guess into an apparently-verified instruction, in the
generated note. It now requires an explicit `true`. `docs: ""` and `probe: []`
satisfied `is None` and no longer do — `probe: []` was worse than cosmetic,
because `detect()` read it as no probe while the manifest guard called the record
complete, so the two files disagreed about what "has a probe" means.

**A ratchet that was never a ratchet.** A comment claimed that a note promising
work "in 0.1.354" became a CI failure once 0.1.354 shipped. It did not: the
citation guard fails only when *no* heading defines a version, so shipping made
the promise more legal, and it globbed `*.md`, so the registry's own two stale
promises were never read at all. `check_stale_promises` is the check that comment
described, and it scans the registry JSON as well. The registry's promises are
gone.

Smaller, same class: a guard that raised took every guard after it with it and the
output never said so, which left five `ok` lines and a traceback; the fixture
suite reported `ok` on an empty spec; `contains` searched the whole serialized
report, so its metric key asserted nothing and keying it to a name no checker
emits still passed — in the one assertion whose stated job is that a check failing
for the wrong reason has not passed. And `--repeat` is removed rather than fixed:
nothing looped, so it printed back the number the operator typed, which in a
document whose purpose is evidence is the worst possible field.

Every fix above was falsified by reintroducing the defect.

## 0.1.357 — the harness scored nothing, and the fixture was not a deliverable

Two defects in 0.1.356 and 0.1.355, both found by using them, and both instances
of failures this repository had already named and fixed elsewhere.

**`run_conformance.py score` scored nothing.** `score_checks` and `score_recall`
were defined and never called; `score` shared a branch with `run` and did exactly
what `run` does, then told the operator to go and run `score`. So the harness
whose stated purpose is *"scores every output with the same three check scripts"*
did not score. That is the dead-constant defect removed from `check_design.py`
five releases earlier — `TYPE_FLOOR_PX`, declared and never read — committed
again in the release that was meant to close the loop. `score` now walks the run
directory, finds each deliverable, runs `check_prose.py` and `check_design.py`
against it, keyword-scores the recall task, writes `scores.json`, and exits
non-zero on any failure. **A task that produced no artifact records `no
deliverable`, never a pass** — an agent that answered in chat instead of writing a
file is the most common real outcome, and it has to read as a failure to produce.

**`fixtures/deck-pass.en.html` did not pass.** It cleared `check_prose.py` and
`check_design.py` — the two CI can run — and failed `inspect_layout.py` with
three unmeasured checks and no focal element on 14 of 16 pages. A fixture named
`pass` that passes two of three checks is the same overclaim the checks exist to
prevent, and it was only visible because 0.1.355 deferred the browser check to a
local run and the local run was then actually performed. The fixture now carries
a stat band and a display lead, exercising `.band .k`, `.band .v` and the focal
element, and clears all three checkers at all three geometries with nothing
unmeasured.

**One genuine probe bug fell out of that.** `inspect_layout.py`'s measure-bar
candidate window — at least 120 long, 30 to 90 thick — was applied to *rendered*
pixels. A page is a zoom-scaled stage and a figure is scaled again into its cell,
so an identical bar measured 46 at 1280 and 28 at 794: the component-colour audit
accepted every bar in a document in landscape and rejected all of them at A4, for
a reason having nothing to do with the document. The window is a statement about
the *drawing*, so it now reads SVG user units — the units the figure was authored
in, which are the same at every geometry.

## 0.1.356 — the conformance harness, and an honest scoreboard

The last of the five releases. `scripts/run_conformance.py` runs a fixed task
suite through whichever agent CLIs are installed on the operator's machine and
scores every output with the same three check scripts, so the claim this package
makes — *one bar, whichever model wrote it* — has something behind it.

Three tasks, chosen because they are scorable without a judge:

- **T1 deck** — a six-page HTML deck on an invented subject, graded by
  `check_design.py` and `check_prose.py`. D12 and M4 must come back `ok`.
- **T2 de-AI rewrite** — a tracked passage seeded with six banned phrases, which
  must reach zero. Deterministic and model-portable: no taste involved.
- **T3 red-line recall** — five closed-form questions with a keyword answer key.
  **No LLM judge.** It tests the one cross-model property that can be scored
  mechanically: whether the rules were loaded and retained at all.

`conformance/CONFORMANCE.md` is the tracked scoreboard; `conformance/results/` is
gitignored, because raw agent output is a render and renders live with the run.
CI gains `run_conformance.py validate`, which parses the suite and nothing else —
it cannot invoke an agent, and must never look as though it did.

**The first run records one agent of twelve.** Claude Code is present, and the
scoreboard names the exact CLI build;
everything else on this machine reports `not installed — not exercised`, and two
platforms report why they can never be probed at all (Antigravity ships as an IDE
rather than a CLI; Kimi and DeepSeek are API chat models with no binary). That is
the honest state, and it is printed rather than omitted — an agent nobody ran is
not an agent that passed.

What the harness cannot do is stated in its own docstring and repeated in the
README, because the temptation to overclaim here is the whole risk. It cannot show
a model writes well: the checks measure mechanical conformance, and a page is done
when a human reads it as intentional. It cannot show reproducibility, because
agent CLIs are non-deterministic and their versions drift weekly, so a recorded
pass is one run of one version on one machine on one date and the report always
prints its `n`. And it does not run in CI.

The README's support claim is rewritten to match. It no longer says "works with"
a list of platforms; it says what is verified every push, what is only observed
per release, and what is not verified at all.

## 0.1.355 — the gates get tested

`check_prose.py`, `check_design.py` and `inspect_layout.py` decide whether a
deliverable is acceptable, and until now **none of them had ever been tested**.
They measure a deliverable, and the only deliverables this repository could reach
sat in the gitignored `docs/`, carrying a client name red line 9 bars from here.
So the machinery meant to make output quality portable across models was itself
unverified — which matters more as the number of platforms grows, because the
checks are the only thing that does not vary with the model.

Two tracked fixtures, both synthetic and client-free — a fictional metering
programme, `www.example.org` as the origin, no engagement fact anywhere:

- `fixtures/deck-pass.en.html` — 16 pages, 133 sentences, 16 titles. Every graded
  metric passes and both scripts exit 0.
- `fixtures/deck-broken.en.html` — the same deck with one named defect per metric:
  four banned phrases (M4), a literal hex outside the token block (D4), and a page
  whose footer states no handling terms (D12, the one design check that gates).

**The broken one is the point.** A suite proving only that clean input passes
cannot tell a working check from one that returns `ok` unconditionally — which is
exactly the defect 0.1.350 removed from `inspect_layout.py`, where every
reassuring line was the `else` branch of a defect test. `check_fixtures.py`
asserts *which finding fired*, not merely that the run failed, because a check
that fails for the wrong reason is not a check that passed.

`fixtures/expected.json` is hand-written and asserts **verdicts, not values** —
`M8_length_cv: "ok"`, never `0.578`. A golden file full of raw numbers rots on
every cosmetic change and teaches people to regenerate it unread; this way a
legitimate threshold change touches one line and reads in review as an intent
change, while an accidental regression reads as a verdict flip. It also carries
`forbid_verdicts: ["n/a"]`, so the passing fixture cannot quietly decay into a
document too thin to grade and report green for it.

The fixtures are generated by `scripts/build_fixtures.py`, which lifts the `:root`
block from `tokens/`: a fixture grading a document against a palette the skill no
longer ships is worse than no fixture. `--check` runs in CI.

Falsified: repairing the planted D12 defect makes the suite fail, so it is not
vacuous. `fixtures/README.md` records the rule that pays for all of this — **never
edit a fixture to make a check pass**. If a check fails on the passing deck, one
of the two is wrong; decide which and say so. Editing the evidence to match the
verdict is how a metric becomes decorative.

`inspect_layout.py` stays out of CI because it needs Chromium, and is run against
the fixtures locally.

## 0.1.354 — the per-platform artifacts become generated, and the package gets a front door

Twelve platforms, each wanting an install note; three wanting a pointer file at a
path their own convention dictates; two wanting a plugin manifest. Hand-written,
that is fifteen more copies of facts this repository already holds — and it has
shipped the consequence twice already: `adapters/claude-code.md` told people to
`git clone` into the skills directory while `README.md` insisted on a symlink
*because a copy had stranded at an old version*, and `AGENTS.md` carried a
withdrawn fill floor for four releases.

**`scripts/build_entrypoints.py` renders all eighteen of them** from
`adapters/platforms.json` and `SKILL.md`, with the `--check` mode this repository
already uses for `embed_font.py`, `embed_icons.py` and `build_geography.py`, and
the same failure sentence, so a stale tree reports as stale rather than as a
mystery. It runs in CI before `check_repo.py`, because a stale artifact must be
named as stale rather than surfacing as a puzzling guard failure.

Generated: the twelve `adapters/*.md`; `GEMINI.md`,
`.github/copilot-instructions.md` and `.cursor/rules/lumi-style.mdc`;
`.claude-plugin/plugin.json` and `marketplace.json`; and
`.well-known/skills/index.json`. The six red lines are **lifted from `SKILL.md`**
rather than paraphrased, because a pointer file that restates them is a seventh
copy waiting to drift.

**Deliberately not generated:** `SKILL.md`, `AGENTS.md`,
`prompts/lumi-style-core.md`, `references/`. Assembled prose is worse prose, and
the entry points a reader is most likely to actually read should be the ones a
person composed. The generator covers the artifacts whose content is *packaging* —
paths, invocations, manifests — where there is no judgement to lose. That is a
narrower claim than the plan for this release made, and the narrower claim is the
true one.

**The first cut of the pointer files was broken and the guards caught it.** All
three wrote `[SKILL.md](SKILL.md)`, which resolves to `.github/SKILL.md` from a
file in `.github/`. Links are now computed from each artifact's own depth. A
generator that emits the same mistake into every file has made the breakage
uniform rather than impossible; the markdown-link guard is what noticed.

CI also gains `inspect_layout.py` in its `py_compile` list, which it has never
been in — the largest script in `scripts/` had no syntax coverage at all.

Still to come: tested fixtures (0.1.355), and the cross-agent conformance harness
(0.1.356). No claim of cross-agent verification is made yet, because none has been
performed.

## 0.1.353 — a withdrawn number may not be restated as though it still binds

`tokens/design-tokens.json` gains a **`retired` register**: the values this rule
set withdrew, each with the release that withdrew it and why. A withdrawn number
has to be *stated* somewhere or no machine can tell it from a number deleted by
accident, and this repository's documented worst drift is exactly that — the 82%
page-fill floor and the 11px type floor were withdrawn in 0.1.340 and went on
living in two entry points for four more versions, invisible because nothing
compared the copies.

`check_repo.py` gains **`retired values`**: every paragraph restating a retired
number must mark it as retired. It reads the register rather than a hand-written
list of things an entry point should not say, which is the direction of authority
CLAUDE.md requires — a check that asserts its own expectations is a second source
of truth.

Two things the first cut got wrong, both caught before it shipped:

**Line scope was the wrong unit.** This prose is hard-wrapped, so "Withdrawn in
0.1.340 … the 11px type floor" straddles two lines, and a line-scoped check
reported the second half as an unmarked restatement — twelve false positives on a
clean repository. A sentence is the unit a reader reads, so it is the unit the
marker has to be found in.

**A bare number is not a rule.** `40%` names the withdrawn D9 share cap in one
sentence and "four diagrams rendered at 40% of their cell" in another. Same
digits, opposite claims. Each retired entry now carries `context` phrases, and a
value counts as a restatement only alongside one of them; an entry with no context
list fails rather than guessing. The guard also reports a waiver that no longer
matches anything, which is how the one waiver this needed came to be deleted —
once `context` landed, the sentence sizing an icon against an 11px caption stopped
looking like a floor claim at all. A waiver that survives its cause is a standing
permission nobody re-reads.

What it cannot do: tell whether a rule's polarity changed while its digits stayed.
"3-6 word headline" as a ceiling and as a target are the same characters, and
CLAUDE.md rule 4 exists because that has cost three regressions. That stays with
the reviewer.

## 0.1.352 — the platforms get a registry, and a withdrawn floor stops shipping

First of five releases making this skill work across many agents. This one adds
no platform support by itself; it makes the current state *checkable* before it
changes, which is the only order in which adding twelve platforms is safe.

**A floor withdrawn twelve releases ago was still shipping.** `design-rules.md` 1
and `eval-rubric.md` both record that 0.1.340 withdrew the 11px type floor as
invented without an ask. `tokens/design-tokens.json` went on declaring
`size_floor_px: 11` under a note asserting it *"binds every text run except
chart_scale_px.source"*, and `lumi-theme.css` went on calling the same value
`--fs-floor`. CLAUDE.md makes the tokens win on conflict, so the authority
mandated a floor the rules had retired, and every deliverable built from the
token block inherited it. The value stays — it is the smallest size the scale
uses — under the name it deserves: `--fs-fine`, `size_smallest_px`, with the
binding claim withdrawn. `check_design.py` also carried `TYPE_FLOOR_PX` and
`SOURCE_FLOOR_PX`, defined and never read since 0.1.340; a constant naming a
withdrawn rule is a trap, because the next person needing a threshold finds one
already declared and wires it up.

**`adapters/platforms.json` — one place platform facts live.** Twelve platforms,
each with its install paths, capability tier, entry file and install note. The
facts had been spread across four hand-written notes and a README table, and they
had already disagreed: `adapters/claude-code.md` said `git clone` into the skills
directory while `README.md` insisted on a symlink *because a copy had stranded at
0.1.334 while the repo reached 0.1.337*. Two files, one fact, opposite
instructions.

Three capability tiers, because the axis that matters is not which vendor an
agent comes from but what it can do: `full` reads the bundled files and runs the
scripts, `files` reads but cannot execute, `prompt` gets one pasted context and
no tools. What verification means differs per tier, and an agent that cannot run
the checks may not call a deliverable verified.

**Most of these platforms already worked; nobody had said so.** `~/.agents/skills/`
turns out to be a convergent location — Gemini CLI, GitHub Copilot, OpenCode,
OpenClaw and Pi all read it, and Gemini CLI gives it precedence over its own
directory — so one install serves five. Google Antigravity's workspace path is
`.agent/skills/`, singular, and is deliberately recorded as *not* the same
convention. Eight install notes join the four that existed.

**Two guards.** `platform manifest` requires every registry claim to have a file
behind it, every install note to be claimed by a platform, and every unverified
claim to carry its own written reason — Hermes ships with `path_verified: false`
and a waiver naming exactly what is unconfirmed, rather than an invented path.
`version citations` closes a gap this repo has had since it had entry points:
only `SKILL.md`'s frontmatter version was ever checked, so `AGENTS.md` carried no
stamp at all and the core prompt's self-declared snapshot line was unverified —
the two files that had already shipped four versions of drift. It also requires
every version cited anywhere to name a release some heading defines, which is the
drift CLAUDE.md calls this repo's worst.

Still to come: the numeric-claim guard (0.1.353), generated entry points and the
plugin manifests (0.1.354), tested fixtures (0.1.355), and the cross-agent
conformance harness (0.1.356). No claim of cross-agent verification is made here,
because none has been performed.

## 0.1.351 — the history moves onto the 0.1.x scheme

0.1.350 restarted the numbering but left the 22 releases behind it on the old
1.0.0 → 3.4.0 scale, so a public repository advertised two schemes at once and its
newest entry sorted below its oldest. They now occupy **0.1.328 – 0.1.349** in
their original order, running contiguously into 0.1.350.

**The citations moved in the same pass, which is the part that could have gone
wrong.** This repository names versions constantly — "since 0.1.339", "0.1.346's
register", "0.1.332's headline" — and those names are load-bearing: they are how a
rule carries the defect that produced it. All **165** references across
`references/`, `tokens/`, `scripts/`, the three entry points and `README.md` were
rewritten together, and every version cited anywhere in the repository now
resolves to a heading in this file. A citation naming a version no heading defines
is exactly the drift the checks cannot see, so it was verified explicitly rather
than assumed.

**Git history was deliberately not touched.** Commit subjects and the merged pull
requests still read `3.4.0 — one role, one rendering`, because rewriting 22
commits means force-pushing a public branch: every clone breaks and PRs #17–26
detach from their commits. The CHANGELOG is the canonical record; the git log is a
factual account of what each release was called when it landed. The same applies
outward — a deliverable exported before this carries a 3.x stamp that no longer
names anything here.

*No rule changed. This is bookkeeping, and it takes a version of its own because
the convention says a revision gets an entry and a bump — including the revision
that edits the convention.*

## 0.1.350 — a check that did not run is not a check that passed

**The version scheme changed with this release.** The package had been climbing
into a fourth major version, which read as a maturity it has not earned; 0.x says
plainly that
this is still pre-stable. From here the **patch position** carries ordinary
releases (0.1.351, 0.1.352, …), and the minor moves only for a change that would
break a deliverable built on the previous one. *(The releases before this one were
renumbered onto the scheme in 0.1.351, the entry above.)*

A review of 0.1.349 asked whether the layout probe establishes complete check
factors for a **new** document. It does not, and the way it failed is worse than
a gap: every reassuring line it printed was the `else` branch of a defect test,
so a check with nothing to examine reported the same thing as a check that found
nothing wrong.

**A document with no recognisable pages passed.** Run on an HTML file with no
`section.page`, the probe printed eleven affirmative lines — "one horizon on each
of **0 pages**", "all 0 pages hold 16:9" — and exited 0. Hidden pages passed too:
a zero-size page has `overflow` of −720 (not > 1), zero frame skew, one horizon
because `.foot` is still in the DOM, and an aspect of `0/0`, which no `>`
threshold is ever true for. Three `display:none` pages were credited as three
passing pages on every line.

**Coverage was a property of class names, not of the design system.** Measured on
two documents identical apart from their class names: ten role checks became two.
Six of the ten selectors — `.t .sup .eyebrow .k .n .listhead` — appeared nowhere
in `tokens/`; they had been read out of a deliverable. A document built from the
token files the skill tells an author to copy therefore matched two roles, lost
the other eight **without printing a word**, and the focal check *inverted*: with
no `.t` to exclude, the title became the page's focal element and a flat page
passed. Renaming a class made the report shorter and greener.

The fix is in both halves. The role vocabulary now ships in
`tokens/lumi-layouts.css` as a declared contract, and every check that finds
nothing says `NOT MEASURED` with the reason and the selector it wanted.
`inspect_layout.py` **exits 1 when anything could not be measured** — the design
judgements still gate nothing, which is the whole distinction: reporting that a
check did not run is not a judgement about the page. `check_design.py` has had
this concept since 0.1.339, in the same directory, while this script expressed all
five of its failure paths as silence.

**Three checks were measuring the box instead of the thing in it** — the mistake
0.1.349 was written to catch, committed by 0.1.349's own additions. The title role
ignored size, to excuse a cover legitimately larger than a content page, so 34px
and 57.6px produced the same key and the first defect the audit was built for was
undetectable by it; a title is now three registers, each compared on size. The
band-baseline check compared element boxes, and a value written the shipped way —
`41<span class="u">%</span>` — sits in a box 25px deeper than one without a unit
while the digits stay on one baseline, so it flagged bands whose numbers were
exactly aligned. Centerpiece scale, cell fill, the empty-band scan and the
collision probe all used `getBoundingClientRect()`, so a grown SVG box inflated
the scale *and* filled the empty-band scan with phantom ink at the same time.

**The consistency and ground audits only ever ran at 1280×720.** Run at A4 — a
required matrix point since 0.1.340 — the same probe found the callout at
**12 / 13 / 11.5px**, set per context by the portrait block of the token file that
carries the rule against it, and the strong ground tier breaking its own 1.40:1
ceiling on two independent documents. Both audits now run at every requested
geometry and say which one they ran at; `--ground-strong` drops .25 → .20, which
measures 1.369 where .21 measured 1.396 and left no room for a document's own
ground drawing.

**Two rules mandated mechanisms the package does not ship**, the failure mode
`CLAUDE.md` §5 exists for and now the fourth and fifth instances. The title-block
reserve that holds the content datum shipped in a deliverable and not in
`tokens/`, so every document built from the tokens kept the floating lede the
rule bans. And `box-sizing: border-box` shipped nowhere, while the layouts file
declares fixed 1280×720 and 794×1123 stages that are arithmetic nonsense without
it — measured on a fresh document, **all six pages +72px**, page-height
conformance being the first thing §7 says to check. `.lead .v` also asked for
`var(--display, var(--sans))`, and neither token has ever existed, so the one
number that *is* the page silently inherited the body face.

Smaller, all found by using the thing: a missing Pillow deleted the ground audit
rather than reporting it; a crashed consistency probe printed nothing at all and
`--json` omitted three audits entirely; two files in one run overwrote each
other's contact sheet, which the docstring calls the real output; the `ImportError`
message advised `--no-sheet`, which does not help because the import happens
either way; `contact_sheet` documented a `sips`/`montage` shell-out that was never
written, and `subprocess` was imported for it; nothing waited on `document.fonts`
or listened for the document's own errors, so a report could be measured against
fallback metrics and printed as fact; and `--dark` was read only to name output
files while nothing switched the palette.

Two false alarms went the other way and were fixed with the same discipline: a
band that stacks in portrait is not 338px out of line, and a figure deliberately
hidden by the landscape/portrait pair is not an unreadable drawing.

## 0.1.349 — one role, one rendering: a consistency system, and the probe that holds it

A reader asked for a complete consistency audit of all 30 pages and for the
confirmed style to live in the tool rather than in my head. They named four
inconsistencies. Measuring every repeated role across every page found those four
**and two more**, one deeper than anything reported.

**The title rendered three ways** — content 34px/700, cover 57.6px/700, and the
**closing at weight 400**: the register reached every page in 0.1.346 except the
last one. **The callout rendered three ways**, 12 / 12.5 / 13.5px, unreported —
residue from three rounds of per-page density fixes, each locally right and the
accumulation exactly the inconsistency a reader can see. That produced a rule: **a
page that no longer fits gets its content trimmed, never its type nudged.**

**The deepest defect was not on the list.** Titles all began at the same y, but the
support line began at three different heights and the first content cell at **ten,
106px to 219px**. Content started somewhere different on almost every page, which
is what a reader feels flipping through even when every type style matches. The
title block now reserves a fixed height derived from the line-heights, and content
begins at **198px on all 26 content pages**. Six support lines were trimmed to two
lines and one glossary page went from twelve terms to ten to pay for it — content,
not type. The datum is per geometry: portrait releases it, because portrait is a
composition and not a reflow.

**The stat band was 17px out of line.** Two causes, both mine: the lime highlight
replaced the band cell's padding, making the headline number's box 40px where its
neighbours were 80px; and the band centred each cell, so a label that wrapped one
line further lifted its own number. The highlight now paints the *text*, and a
band aligns at the top — it is a row of comparable things.

**Two comparison bars, two greens.** This was a collision between two of these
rules — *one lime event per page* met *the same component always looks the same* —
and the component lost. Resolved as a rule: **the lime marks a number panel, never
a chart mark.** A chart mark encodes a value a reader compares across pages. A page
with no number panel simply has no lime.

**The probe is the general form, not four checks.** `inspect_layout.py` now reads
the deck as a system: for every repeated role it collects the computed family,
weight, size, transform, tracking and colour and counts distinct renderings, with
every sanctioned exception **declared in the probe** rather than tolerated. Plus
one datum, one colour per chart component, and a shared band baseline. Tracking is
normalised to em first — it is authored in em and computes to px, so two sizes can
never agree otherwise, which cost a round of chasing a difference that was not
there.

Known and reported rather than fixed: at **1800x1000**, an off-design shape kept
deliberately in the probe set, three pages still show small collisions and two
spill by under 8 page-units. Text rewraps at that zoom. Both design geometries are
clean.

## 0.1.348 — the working green and the event green, numbers that rank, a quieter cover

Six items from a review. One needed measurement rather than taste, two were
defects, and both defects were invisible to the probe added one release earlier.

**Can the new green be used everywhere on content pages?** No, and the usage
counts say why. The accent appears there **84 times as a fill, 71 times as a
stroke, 23 times as a wash, and 0 times as text**. The lime cannot do the strokes:
1.21:1 on white makes a chart rule, a connector or a decision outline invisible,
and §1 already counts a mark a reader must tell apart as text. It could do the
fills, but 84 acid panels is the opposite of non-contention and destroys the thing
that makes it an event. So the two greens are named for the two jobs the canvas
forces apart: **`--acc` forest is the working green** — anything that must read on
white — and **`--lime` is the event green** — large panels only. Collapsing them
into one would take a dark content canvas, declined in 0.1.346.

**The collision probe only knew one kind of collision.** 0.1.347 added it after a
reader found text on text; it compares text to text and nothing else. The same
reader immediately found two defects it could not see, and measuring text against
*drawn* elements found **11 pairs**: a field sitting 22px on a paragraph, and the
globe crossing `DATE`, `VERSION` and `CLASSIFICATION` on both the cover and the
closing. It now compares text against every drawn element — field, figure, band,
spec, geography — with containment excluded, because a caption inside its own
figure is not a collision.

**The catalogue field is removed from page 3.** Its label was cut in 0.1.347 to fix
a different collision, and unlabelled the 161 marks read as texture rather than as
evidence — which is exactly what the reader called them. The stat band on that
page already says 161. The field survives where it earns its place: the
thirty-page tier strip, where the distribution *is* the argument and no number
states it. A signature device used twice, once meaningfully and once not, is used
once.

**Key numbers rank in three steps and are set like arguments.** `.band .v` was
weight **400** — a caption with large type. It is now the display weight, and
importance is three tiers rather than a single highlight: the number the page
turns on gets a **lime panel** with near-black numerals (16.44:1), its support is
**forest**, and context is **ink**. One lime panel per page, because ΔE against
the forest is 94 and two greens on one page would read as two meanings.

**The cover and closing get quieter.** Both subtitles are gone — the title is the
page. The source clause is cut from the cover colophon, after verifying `D6` still
finds the document's provenance on the closing. The build stamp now appears
**once**, in the closing colophon: `SKILL.md`'s version-lockstep rule said cover
*and* closing, so the rule moved with the deck rather than being quietly broken.
The document attributes are retained and stop competing — out from under the globe
into one narrow mono column in the clear lower-left. The closing title takes the
cover's register.

One self-inflicted defect on the way: the new number tier was first called
`.v.lead`, which collides with `.lead`, the focal block. D1's surface discovery
keys on class tokens, so it began grading every focal element against the lime
panel — five false contrast failures on the dark palette. Renamed to `.v.first`.
**A class name is an interface.**

## 0.1.347 — text on text, the display pulled back, and one lime event in the body

A reader reviewing 0.1.346 found characters overlapping at the bottom of two pages,
asked for the display type 30% smaller, and asked whether the acid green could
appear once inside the body rather than only on the part openers.

**The overlaps were real and neither existing probe could see them.** Every check
in `inspect_layout.py` measures a block against the *page* — its top, its bottom,
its column, the footer rule — so two blocks landing on each other in the middle of
a page is invisible to all of them. The cover's support paragraph sat 34px into
the spec strip and the catalogue page's stat labels sat 48px into the paragraph
below. One cause: **0.1.346's heavier register outgrew grid rows sized for the old
one**, so a block overflowed its track onto the next instead of lengthening its
own. `min-content` on those rows fixes it, and that is now a rule — when the type
scale moves, the tracks that hold it move with it.

A **text-collision probe** joins the set: leaf text against leaf text, since a
container legitimately encloses its children. Confirmed by restoring the old
`hero-band` row definition and watching it fire.

**Display type is down 30%** — `clamp(64px, 9vw, 132px)` to
`clamp(45px, 6.3vw, 92px)`. Big enough to be the event, not so big the page
becomes a poster with a caption.

**One lime event per body page, and it is a fill.** The deck's single most
important number — code intersection at 100% — is now an acid-lime bar with
near-black numerals. Measured, because "is this comfortable to read" deserves an
answer rather than an opinion: the panel's edge against the canvas is **1.21:1**,
so it *glows rather than cuts*; near-black on it is **16.44:1**; at **chroma 102**
it is right at panel size and would be harsh as a hairline or as small text, so it
is never a rule or a caption. Once per page, because ΔE against the semantic
forest is **94** — plainly a different colour, and two greens on one page would
read as two meanings.

Ground tiers unchanged at the reader's request.

## 0.1.346 — the ground, the acid green, and type that commits

The reader asked for water and light behind every page, and pointed at
`silviamalavasi.com` for the green and the register. I read that site with a
headless browser rather than from its rendered text, because the markdown
conversion returns one line of copy and nothing else.

What it actually is: canvas `#0A0907`, paper `#F2EDE4`, **the green `#B8FF00`**
across 91 text uses, plus magenta, yellow and red. Type is Inter with **245
elements at weight 700 and 52 at weight 900** against only 57 at 400; display at
254px and 120px, line-height ~0.9, and letter-spacing `normal` everywhere.

**Two measurements shaped the release.** `#B8FF00` measures **1.21:1 as text on
LUMI's white canvas** — unreadable — and 16.44:1 with near-black reversed out of
it. That site is dark-canvas-first and its palette depends on it. LUMI stays
light-first, so **the lime is a surface and never light-canvas text**, which is
how that site uses its yellow and magenta anyway. And **we ship D-DIN Regular and
Bold and nothing else**: Inter is not vendored, no font tooling is installed, and
the system faces cannot be redistributed. No rule names a face the package does
not carry — `CLAUDE.md` §5, written after 0.1.332 required a display face, shipped
none, and rendered nothing for five releases.

**The ground, and the rule that lets it exist.** `brand.md` says a field with
nothing behind it is decoration and decoration is contention. A background
texture *is* decoration. It resolves on one distinction, now the rule:

> A field is discrete and countable; a ground is continuous and uncountable. If a
> reader can count the marks, every mark must mean something. If there is nothing
> to count, there is nothing to misread — so a ground may be decorative precisely
> because it can never be mistaken for evidence.

Its honesty test is therefore different in kind, and both halves are measured: it
may never exceed **1.40:1** against its canvas, and it may never resolve into
repeated identical marks. The contrast is measured on the **rendered** page with
every foreground element hidden — and that mattered: the three tiers were tuned
analytically, measured at **1.428 and 1.549**, and had to come back down. The
probe caught its own author.

The flows crowd **below the waterline** and thin out above it, so the air where
the claim lives stays clear. That is what makes the ground structural rather than
wallpaper, and it is also what answers "it must not overpower the content" with a
number instead of an opinion. The wider hue range — lime, forest, teal, blue,
gradients along each line — lives here, safely, because the ground cannot be read
as data. The foreground stays one colour, one meaning.

**The register commits.** Display to `clamp(64px, 9vw, 132px)` at weight 700 with
0.92 leading; page titles from 22px/400 to 34px/**700**; support lines from
14.5px to 16px/500 so the subtitle is a second voice rather than small print;
lead numerals to 116px; figure numerals bold. `.3em` eyebrow tracking is gone —
the most dated device in the deck, and the reference tracks nothing anywhere. The
part openers are now full **lime fields** with the claim in near-black at display
size, and they are the only pages in the deck that are.

Three probes added, each confirmed by making it fail: the ground's rendered
contrast ceiling, the ground-is-countable test (fired on a ground built from
eight identical rects), and **D13**, which forbids the lime as light-canvas text.
D13 had to be rewritten to scan the raw CSS after the first version silently
passed the exact case it was written for — the rule map merges duplicate
selectors and a later `.sup` in a media query dropped the declaration. A guard you
cannot make fire is not a guard.

The ground also had to be excluded from every ink measurement. It is behind
everything and covers the page, so on first render all thirty pages reported that
they ran past their own footer rule.

## 0.1.345 — the water thesis: LUMI gets a brand, and the skill finally says what to reach for

Four rounds of review made this skill measurably more correct and no more alive.
The reader said the same thing four times. Two measurements say why.

**The rule set was 23 : 1 brakes to accelerators** — 272 lines that restrict
against 12 that invite. A documented study of this exact failure mode
(`impeccable.style/research`, ~30 skill iterations, ~200 sampled concepts) found
that **5 : 1 produced "65% commitment, and 65% commitment is what bland looks
like"**, and that inverting the order — land fully committed first, then make it
clear — was "the biggest single quality jump" in the whole study. This repo ran
nearly five times more braked than the ratio that already produced bland, and
every release had added more, because every release fixed a defect a reader found.
Nothing was ever added on the other side.

**And there was no brand.** `references/` held writing rules, storyline templates,
design rules and an eval rubric — all craft, no identity. The word "brand"
appeared once in the entire rule set, and it said branding was subordinate to
data. A style guide answers *is this correct*; a brand answers *what is this, and
why does it look like nothing else*. Only one of those had ever been asked here.

**`references/brand.md` is new and it loads first.** The thesis is
`上善若水，水利万物而不争`, and three of its four parts were already true of what
LUMI does — one of them already in the source code. One apparatus serves every
industry the way water takes the shape of any vessel. LUMI declines where others
claim: click-through never measures relevance, no accuracy figure before the
golden set, AI never signs, a refusal is honoured by hand — that is not modesty,
it is *we are the one you can check*. LUMI is light, and you cannot see a current,
only the light on it.

**Two structural devices**, because "committed skin hides template bones" — a
fully-committed surface on a standard grid is the trap:

- **The field** — many small marks at varying intensity, one per datum, ordered by
  the data's own sequence. The deck was already drawing this by accident in the
  tier strip and the stat bands. Page 3 now carries the whole catalogue as 161
  marks, 121 on the automated chain and 40 off it because those sources refused.
  **A field with nothing behind it is decoration**, so every mark declares its
  datum and `inspect_layout.py` fails a field whose marks outnumber its data. That
  is the one new brake this release adds, and it is what keeps the shimmer honest.
- **The waterline** — one horizon per page: air above, record below. The footer
  hairline stops being a border closing a box and becomes the surface the page
  sits on. Two horizons is stripes, none is a document; exactly one is checked.

**The accent gains a five-step ramp** for fields and surfaces. It carries no
meaning — one colour one meaning still governs data, and those tokens stay flat
and measurable. Keeping the two jobs in separate tokens is what lets the brand
shimmer without the data lying. Every step was measured on both canvases and every
one carries text: 5.93 / 4.54 / 6.52 / 9.18 / 12.32 on light, 5.61 / 4.69 / 6.67 /
9.70 / 13.46 on dark.

**The ratio moved from 23 : 1 to 9.1 : 1 — and brakes went up, not down**, from
272 to 309. Nothing was deleted; all of it is hard-won defect history and all of
it still applies. What changed is that the skill now says what to reach for, and
the brakes apply at step 4 instead of framing step 0. Still roughly twice the
ratio the study used, so this is a direction and not a destination.

The English-only guard was tightened while doing it. The allowlist was per file,
which is too coarse in both directions — it let prose drift into an allowlisted
file and forced a whole file onto the list for one quoted line. CJK is now
permitted inside backticks or a fenced block and nowhere else, which is exactly
the distinction the red line always meant.

## 0.1.344 — handling terms on every page, provenance once per document, and one table per page

A reader asked for four things and two of them were defects the checks had just
been rebuilt to catch and still missed.

**Per-page source lines go, for sales and marketing.** A source under every figure
and again in every footer is apparatus a customs manager does not need, and it was
occupying the line a commercial document does need. Provenance moves to the cover
and the closing, where it is read once instead of skipped thirty times. Red line 1
is unchanged — no invented facts, every number still traces. **Genre-scoped**:
consulting deliverables and internal analysis keep per-page sourcing, because
there the reader is auditing the claim rather than being sold to. `D6` now asks
the document for provenance instead of asking every footer.

**Every page carries handling terms and where the document is from.** Left of the
footer rule: the confidentiality line and the organisation's site; right: the page
number. Pages travel alone — a slide is screenshotted out of a deck and forwarded
without the cover. `check_design.py` gains **D12, the one design check that fails
the run**. Everything else there reports, because a page is done when a human
reads it as intentional and a threshold satisfiable without improving the page
ends the looking. D12 is different in kind: not a judgement about whether a page
is well made, but a commercial requirement on the artifact. A design metric that
gates is a mistake; a commercial one that does not is a different mistake.

**Two tables side by side is two documents on one page.** A grid claims its cells
are comparable along the axis its header names; two grids with different columns
and different row counts share no axis, so their rows can never align and a reader
sees the misalignment before they can name it. That page is now one drawing — the
deck's own thirty pages as a strip, each tick coloured by whether it is client
safe, needs adapting, or never leaves the building — over three numbered steps.
16 / 10 / 4. `inspect_layout.py` reports any page carrying more than one table.

**The 4px that made two columns look wrong was `.lead + *`.** In a grid, the
adjacent sibling is **the next column**, not the block below, so an unscoped rule
put a 4px top margin on the first cell of every page whose lead spanned the row —
six pages with one column sitting low. An adjacent-sibling selector inside a grid
container is almost always a mistake.

**And the spill probe was asking the box again.** `scrollHeight` on an
`overflow: visible` box **does not count children that spill out of it**: it
returned exactly zero while two pages ran 26px and 8px past their footer rule.
That is the third probe in three releases to measure a container instead of its
contents. It now measures the deepest ink against the footer rule.

Distances are reported in **page units, not device pixels**. Once the page is a
scaled stage a device pixel is not the unit of the design, and the same layout was
reporting 3px of skew at one window size and 4px at another — a threshold that
silently tightened as the window grew.

## 0.1.343 — the page becomes a page, and a probe stops verifying its own setup

A reader suspected the landscape page was not 16:9, asked why the layout tool had
not caught it, and marked three more things on four screenshots. The suspicion was
right, the tool could never have caught it, and the three marks turned out to be
one cause.

**The page was whatever shape the window was.** `.page` was `min-height: 100svh`
with no aspect lock anywhere: 16:9 at 1280x720, **4:3 at 1280x960**, 1.6:1 at
1440x900. The surplus height was the dead band above the footer that the reader
circled. Landscape is now a fixed **1280x720** stage and A4 a fixed **794x1123**
sheet, each scaled to fit with `zoom` and letterboxed in a gutter that never holds
page content. `zoom` rather than `transform`, because zoom participates in layout,
so pages still stack, scroll and snap.

**The probe could not have caught it, and the reason is the most important line in
this release.** `inspect_layout.py` set the viewport to 1280x720 and then measured
`section.height - window.innerHeight` on a `100svh` page: **zero by construction**,
on every page, in every run since it was written. "All 30 pages are exactly 720px"
meant "the page filled the window I made 720px tall". It had never tested the
aspect ratio at all. **A probe that establishes the condition it verifies proves
nothing** now leads the verification section of `design-rules.md` §7 and the
rubric, above "a probe that has never failed is not a probe". The new aspect probe
renders five window shapes chosen because they are *not* the design geometry.

Locking the geometry moved the blind spot rather than removing it: a fixed box does
not grow when its content does, it spills, and the height probe would report zero
while the page was visibly broken. A content-spill probe measures `scrollHeight`
against `clientHeight`, confirmed by shrinking the stage to 620px and watching four
pages fire.

**Three of the reader's four marks were one cause.** `.fig svg` was `flex: 1 1 0`,
so the box grew into all leftover height and `preserveAspectRatio` centred the
drawing inside it. Measured: the first mark sat **79-185px below the top of its own
box**, and the caption **95-205px below the drawing**. That is why six pages read
as "columns not level" while the column probe reported 0px — **it compared element
boxes and the reader was looking at ink**. Column tops and weight now map an SVG's
`getBBox()` through its CTM. The drawing takes its own aspect, ten viewBoxes were
trimmed to the art they hold, and the caption's doubled spacing (a gap on `.fig`
and a margin on `.cap`) became one.

**A page states its source once.** Thirteen figure pages carried both a figure
source line and a footer one; eleven cited overlapping sections and two were
identical word for word. The figure's line wins, and the footer keeps a source only
when it says something the figure's cannot.

**And the deck got a voice.** Asked how 0.1.342 answered "no visual impact,
mediocre, flat", the honest answer was that it fixed hierarchy and structure, not
brand presence — and that nothing could be composed to a frame while there was no
frame. With one: the two part openers are full accent fields with the claim
reversed out, and the cover's globe is height-led and bleeds off the right edge
instead of sitting beside the type as an ornament.

Three checker defects surfaced doing it. `D1` graded every colour against `--bg`
and `--card-bg` because those were the only surfaces the deck had; it now
discovers painted surfaces by reading the CSS, composites translucent washes onto
the canvas first, and grades a rule that declares its own background against that
background. That found two real defects invisible since 0.1.338: **amber measured
4.68 against a canvas it never touches and 4.24 against the wash it actually sits
on**, and the dark seal the same. Both moved. `D6` asked the footer for a source
line; it now asks the page.

## 0.1.342 — a focal element on every page, a table only for values, and probes for both

A reader called all 28 pages flat, mediocre and without visual impact, named the
split layouts as ugly, said far too many tables carried non-numeric information,
and pointed at one figure caption as plainly odd. Every one of the four was
measurable, and three had a single mechanical cause.

**The flatness had a number: 24 of 28 pages carried nothing larger than 15px body
copy.** Only the cover and two stat-band pages had any display tier at all. A page
with no entry point gets read top-left like a document instead of looked at. Every
page now has one focal element — a display number with its gloss, a claim at
display size, or a figure composed to dominate — chosen per page, and half the
pages got a redrawn figure rather than a number. A display tier (`--fs-lead`,
`--fs-lead-xl`, `--fs-say`) and a `.lead` block ship in `tokens/`. **There is no
floor on it**, and there will not be one: a threshold would push a number onto a
page whose figure already carries it, which is the 82% fill floor's mistake in a
new costume.

**Fourteen of sixteen tables held prose, not values** — digit density at or below
2%, including a literal two-by-two truth table laid out as four rows and three
pages whose "table" was a tempting sentence beside a safer one. A grid claims its
cells are comparable along the axis its header names, and sentences make that
claim false. They are now a timeline, a relay, a two-by-two, three maturity cards,
a veto diagram, two graded ladders, numbered vows and paired swaps. A scoring form
stayed a form.

**The split layouts were ugly for one reason, and it was a specificity bug.**
`lumi-layouts.css` had said `.body.split > div { justify-content: flex-start }`
since 0.1.339 and it had **never once applied**: the fill rule above it reaches
(0,6,1) because every `:not()` contributes its argument, against that selector's
(0,2,1). Twelve of fifteen multi-column pages centred their columns independently
and drifted by up to 132px. One line fixed twelve pages. The same chain has since
won two more arguments it should not have.

**The odd caption was a duplicate.** Two of its four sentences appeared verbatim in
the same page's right-hand column, and a second page's 124-word caption restated
that page's entire ordered list. Below a figure now goes the number, its
conclusion name and the source line, and nothing else; explanation moves into the
page's own column where it is set at reading size beside the argument it serves.
Eight caption prose blocks retired.

Two part-opener statement pages join the deck — one line at display scale saying
where the reader is and what the next run of pages argues. A navigation rail
cannot do that at a glance, and the quiet page is what makes the dense ones read
as dense on purpose.

Six probes join `inspect_layout.py`, each confirmed by reintroducing the defect it
was written for: column tops, column weight, focal ratio, caption budget and
duplication, table census, figure share. Three of them were wrong within a day of
being written — two because their selector did not know a new block class, and one
because it counted a table stretched to 100% of its cell as a dominant figure,
which is D7's own failure reproduced inside the tool built to replace it. **A probe
is only as good as its vocabulary** is now recorded in the rubric.

Three checker defects fixed while measuring: `check_design.py` read `&#183;` as a
literal hex colour, and required a support line on pages whose display lead does
that job better; `check_prose.py` counted only `<ul>/<ol>`, so M10 measured three
enumerations on a deck that enumerates constantly in named blocks and reported a
66.7% triad rate off a sample of three.

Also corrected: `AGENTS.md` and `prompts/lumi-style-core.md` still carried the
82% fill floor and the 11px type floor, both withdrawn in 0.1.340, and the core
prompt still described the pre-0.1.340 cream and near-black canvases, the fixed
legend position and the retired caption description. That is four versions of
semantic drift in the two entry points the checks cannot read.

## 0.1.341 — the measure cap belonged to the page, not to one of its children

`.body` carried `max-width: 1180px` and `.foot` carried nothing. On the design
page that is invisible, because 1180 plus the padding is the page. On any wider
window the footer ran to the window edge while the composition stayed anchored
left, so **all 28 pages showed a dead band down the right** and the source line no
longer lined up with the content it sourced. A reader caught it at 1817px; the
contact sheet never would have, because `inspect_layout.py` renders at exactly
1280x720 and 794x1123, where the defect does not exist.

The cap is right — prose should not widen to fill a monitor. Applying it to one of
the page's three children was the defect. Anything sharing the page frame now takes
the same width and centers, so the leftover space becomes a symmetric margin
instead of a hole. Verified at 1280, 1817 and 1920: 28 of 28 pages align, and the
right margin equals the left.

Lesson recorded in `references/design-rules.md` §7: a probe that only ever renders
the design geometry cannot see a defect that only appears away from it. Check one
size the document was not designed for.

## 0.1.340 — 2026-08-07

Reader review scored H1, H2 and H3 at **1**, against self-scores of 3. The anchors
for 1 are "the page talks to itself", "a template forced onto the content" and
"figures are decoration". All three were fair, and the root cause is one sentence:
**0.1.339 turned qualitative design feedback into metrics and then optimised the
metrics instead of designing the pages.**

**Principles now govern.** `SKILL.md` opens with the principal-designer role and
four hard rules, above every mechanical rule in `references/`: design per page; no
new universal size floors without an explicit ask; verify on rendered geometry and
content weight, never the element box alone; if a page looks empty, redraw or
recompose rather than growing chrome. **Done when a human reads the page as
intentional — passing metrics is necessary but never sufficient.**

**Three invented floors withdrawn.** D7 (82% page fill), D9's 40% layout-share cap,
and the 11px type floor. D7 is the cautionary one: it measured the bounding box of
all ink, so a small chart with a long caption scored as full, and it was satisfied
by stretching table rows while four diagrams rendered at 40% of their cell. The
skill already forbade this move on the prose side — click-through must never
measure relevance, because the metric rewards what it exists to suppress. D7 was
the same mistake in the design half. **The whole D-series stops gating**;
`check_design.py` reports and exits 0.

**Two output geometries are now a governing principle**, both latent defaults for
internal and market material: 16:9 landscape at 1280×720 (primary, checked at
1920×1080) for projection and PDF/PPT export, and A4 portrait at 794×1123 for
printing and binding. Portrait is a composition, not a reflow; collapsing every
horizontal layout at a width breakpoint is the landscape design giving up.

**`scripts/inspect_layout.py`** renders a deliverable page by page at both
geometries and emits a **contact sheet** — the whole deck as one image, which is
what makes human review of 27 pages possible at all — plus centerpiece scale,
figure-to-cell aspect, and the largest empty band. It gates nothing. Its own first
version shot the viewport after a smooth scroll and produced a sheet of half-pages
under the wrong captions; it screenshots the section element now.

What the tool found immediately, and D7 had hidden: four diagrams at 4.6–5.4:1
sitting in 2.4:1 cells and filling 44–51% of the available height, two pages with
centerpieces at 13–15% and empty bands over a third of the page, and a blanket
`.body > div{flex-direction:column}` rule from 0.1.339 that stacked every spec strip
vertically — which alone made the cover 1301px tall inside a 720px page.


**Second pass, same release.** The four wide diagrams were redrawn rather than
rescaled, per hard rule 3. Nodes went from 46px strips to 112px cards carrying the
detail that earns the space: the S0–S4 chain gained the three ledgers with their
real status and a feedback band with a return path; the origin chain gained the
tier scale and the watershed as a decision; the funnel gained its below-threshold
branch and the two exempt classes; the evals ladder gained what each layer tests,
what it needs, and its status. Captions were compressed to a reading plus a source.

**Every page now fits 1280×720**, the primary geometry. Eight did not, and the
causes were a flex chain missing `min-height:0` at three levels, so a figure's
intrinsic height beat its cell, and an absolutely-sized cover mark. Twelve
stroke-only `<path>` polylines in the new figures had no `fill:none` and rendered
as solid black wedges — visible on the contact sheet, invisible to every metric.


**Third pass · palette, lists, captions, legends.** Four reader items.

*Colour.* The light canvas is **pure white (#FFFFFF)**, not the warm cream the
field has settled on, and the dark canvas is **Apple space grey (#1D1D1F)**. The
state palette grew from two colours to four, each with one fixed meaning and each
measured as text on its own canvas: `--amber` (#A86407 / #E0A73E) for partial, in
progress, awaiting an input; `--brass` (#7A6C52 / #C3B393) for reference and
archival. Before this, "partial" and "not built" both rendered as dashed grey, so
a deck could not say the one thing it most needed to say about itself.

*Lists are back.* "Bullet pileups are banned" had been read as "lists are banned",
and a 27-page deck shipped with **zero** `ul` or `ol` — M10 could not even be
computed. The rule now separates the pileup from the list and says what each form
is for: ordered for a sequence performed in order, bulleted for conditions that
must all hold, dashed for alternatives.

*Figure number and name go below the figure, and that does not change.* Two split
pages had moved the caption into the side column, which detached the number from
the thing it numbers.

*The legend goes where the figure wants it.* "Top right, above the plot" was
applied to every figure regardless of shape, at a size that competed with the
figure title. It is now a key in the narrative voice at caption weight, positioned
by the figure's own layout.

`inspect_layout.py` gained per-cell fill and now measures centerpiece scale against
the cell the centerpiece lives in rather than the whole page — measuring against
the page made every split look half empty when both its columns were full. Its ink
selector had also omitted lists and spec strips, so a full column of ordered steps
reported as 10% ink.


**Fourth pass · portrait, and the two thinnest pages.**

*A4 portrait is now a composition.* The width breakpoint that collapsed every
horizontal layout was the landscape design giving up; portrait now has its own
rules keyed to aspect ratio, with tighter margins, a narrower measure, and
asymmetric splits becoming a centerpiece over a band rather than two gutters.
Two-column layouts keep their columns, because 682px of content carries them.

*Figures are drawn twice.* A 2.39:1 chain in a 0.79:1 cell fills a third of it and
no CSS fixes that, so the four wide diagrams gained portrait compositions: the
same content as vertical chains. Measured, the three that had no portrait variant
sat at 71 to 73 percent empty band; with one they sit at 1.5. Aspect now matches
the cell in both geometries, 0.76:1 in portrait and 2.39:1 in landscape.

*The two thinnest pages were recomposed, not padded.* A two-row table cannot fill
a page and, worse, it hides that its two rows are opposites — the mutual-exclusion
page is now two facing cards, one per product family, each carrying its 232 status,
its country-layer status and the dimension that owns it. The filing-timeline page
moved its table to full width with the two caveats as a band beneath.

`inspect_layout.py` gained two fixes found by using it: it now measures the
*visible* figure, because a page carrying both a landscape and a portrait drawing
was being reported on the hidden one, and its ink selector had omitted the card
and definition-list elements, so a full column read as 2 percent.


**Fifth pass · page-height conformance, and the last thin pages.** The reader
noticed two pages were simply longer than their neighbours in portrait. They were:
**p18 ran 94px and p22 116px past A4**, and no existing measurement could see it,
because fill, aspect and centerpiece scale are all measured *within* a page. That
is now **D11**, reported per geometry and the first thing to read. The causes were
a callout pasted into both cells of a split and orphan one-paragraph cells left
behind by an earlier re-lay — content defects that no content metric catches.

All 27 pages now render at exactly 720px at 16:9 and exactly 1123px at A4, in both
palettes. The four-tile stat band became a grid that owns its cell and goes 2x2 in
portrait, taking two pages from 37% fill to 100%, and the trade map lost a fixed
620px cap it had been given to stop it overflowing a page it no longer overflows.


**Sixth pass · the last thin page.** p17 argued that the public record exists on
filing day while the industry announcement waits for approval, and it argued it
with a three-row table. A table cannot carry a duration. The page is now a split
with **Figure 3, a timeline**, drawn for both geometries: three accent nodes on
filing day, a dashed run of weeks or months, and a muted node where everyone
without the docket starts. Its type is set larger than the default figure scale,
because a figure carrying half a page's argument should not read as secondary to
the table beside it. No content page in the deck now sits below 45% cell fill in
either geometry.


**Seventh pass · the glossary, and H5 off 3.** Business readability had sat at 3
for four rounds because layout and colour work cannot touch it: a sales reader
meets HTS, 301, 232, GN11, RVC, HS2012, USMCA's four names and two unrelated L
numberings, and the deck offered nothing to resolve them. Twelve terms now sit at
page 7, **before the pillar pages that first use the vocabulary** rather than in
an appendix nobody reaches, and the last entry is the two-L trap the source
document calls the easiest misreading in the engagement. Four terms a reader can
infer from context were cut so the twelve that actually block a reading stand
clearly. The deck is 28 pages, still exactly one page each in both geometries, and
the usage-tier citations are now generated from page ids so they cannot drift when
a page is inserted.

The cover and closing are recomposed: the globe is part of the composition rather
than absolutely-positioned decoration mostly off-page. The remaining page-by-page
design work is open and tracked.

## 0.1.339 — 2026-08-07

Reader review of five annotated pages, all about layout. One measurement explains
most of it: **the deck contained exactly one layout, used on 25 consecutive
pages.** `.body` and `.body.top` differed only in `justify-content`, and there
were zero grid rules in the file. Every page was eyebrow, title, one block,
footer. That is a template rather than a design language, and it is why the pages
read flat and left roughly 40% of every text page empty.

**Fifteen layouts now ship**, in `tokens/lumi-layouts.css`. Vertical: `stack`,
`hero-band` (dominant block over a thin strip), `band-hero` (its inverse),
`thirds-v`. Horizontal: `split`, `split-wide` at 38/62, `split-narrow` at 62/38,
`columns-2`, `columns-3`, `columns-4`. Composite: `rail`, `quad`,
`sidebar-notes`, `full-bleed`, `diagonal-flow`.
`design-rules.md` §3 gains a content-to-layout selection table in the same shape
as §4's chart form-selection, because a vocabulary without a rule for choosing
just moves the arbitrariness one level up. This is a third token file, so version
lockstep now covers five stamps rather than four.

**The gap above the footer was mechanical.** `.fig svg{width:100%;height:auto}`
gave every figure its intrinsic aspect and no way to grow, so a 3:1 diagram in a
tall page left the difference under the footer. The centerpiece row is now `1fr`
and the figure fills it. **D7** puts a floor under it at 82% of available height,
and a page that still cannot fill has the wrong layout, which the selection table
is there to fix.

**A rule that had no floor was simply not followed.** §3 has required "one to
three sentences of support" since 0.1.336, and 10 of 25 pages had none — every
figure page plus four table pages. It is now unconditional and checked by **D8**.
Third release running that a prescribed value without a floor produced a visible
defect, which is why `CLAUDE.md` §6 exists.

**Icons extend past the eyebrow.** Labelled nodes inside figures and table
row-head groups carry their semantic icon, minimum 14px effective, honouring the
reserved bindings. **D9** caps any single layout at 40% of a deck's pages and
requires at least five distinct layouts in a deck of fifteen or more, so 25
identical pages cannot recur. **D10** reports label icon coverage.

On tilted layouts, asked for at 15, 30 and 45 degrees: **implied diagonal only**.
`diagonal-flow` gets its movement from stepped offsets and an angled accent rule
behind the blocks. Rotating body text and tables breaks printing, copy and paste
and screen reading, and a document about tariff law cannot pay that for a
flourish. On filling the text measure to the full column width, also asked for:
the cap stays at 88ch. An 1180px column at 14.5px holds about 115 characters
against a comfortable measure of 45 to 75, so filling the line would read worse.
The page was unbalanced because the right half was empty, and a second column is
what fixes that.

## 0.1.338 — 2026-08-07

Reader review of a sales-enablement deck: seven defects, and measurement said
three of them were the skill's fault rather than the deliverable's. An author
following `design-rules.md` literally would reproduce them every time.

Three failure classes sit behind the seven, and all three are now maintenance
rules in `CLAUDE.md` §4–6.

**The ladder was unreadable below its second step, and one alpha list served two
canvases.** Measured against their own backgrounds, the lower steps ran 2.91 /
1.81 / 1.32 / 1.16 on light and 4.08 / 1.99 / 1.36 / 1.16 on dark. The deck put
its eyebrows, captions, source lines, page numbers, table headers and every 9px
SVG label on those steps, which is the whole of a document's connective tissue,
and the reader's first note was that both canvases were exhausting to read. The
ladder is now two ladders with names that carry the rule: `--tx1..--tx4` for text,
every step clearing 4.5:1 against both `--bg` and `--card-bg`, and `--ln1..--ln3`
for rules, borders and fills, never text. Each palette carries its own alphas.
`--on-acc` became palette-dependent after measuring cold white on the lifted dark
accent at 2.65; until now one value claimed to serve both and white labels inside
accent bars shipped unreadable. `check_repo.py` recomputes every step and refuses
a ladder below the floor — the guard that used to enforce the shared alpha list
now enforces legibility instead.

**Two assets the rules required and the package never shipped.** §5 has demanded
a semantic icon library since 1.2 and shipped none, so the deck contained zero
icons; the eight icons now live in `assets/icons/` with `scripts/embed_icons.py`.
The cover rule banned imagery because the skill had no photo library, applying the
ban to every kind of image when photography was the actual risk; `assets/vectors/`
now ships an orthographic globe and a flat trade map, generated from lat/lon by
`scripts/build_geography.py`, and a cover may carry exactly one vector mark. Both
are the defect 0.1.337 fixed for the display face, repeated one directory over.
`.gitignore`'s blanket `*.svg` would have dropped both silently and now carries
the exceptions.

**Prescribed values with no floor.** The type scale had no minimum and its two
copies disagreed (tokens 11 / 10.5 / 9.5 against prose 14 / 10–11 / 11, tokens
winning, so 9.5px source lines shipped); there is now an 11px floor and the scale
is 13 / 11.5 / 10.5. The three callout tiers had no budget and a deck put 18
tier-one callouts on 14 of 27 pages, so the hierarchy degraded back into the flat
page it was introduced to fix; tier one is now capped at one per page and a third
of a deck's pages. The figure vocabulary had no consistency requirement and one
figure carried three shape kinds, six dashed states and nine arrows while four
others were rectangles and text; figures must now hold one level across a
document, and a grid of rectangles containing sentences is a table. Footers carry
`N / total`.

**A ceiling read as a target, for the third time.** "Titles budget two lines"
produced titles engineered to two lines: the author capped the container at 48ch
and all 24 content titles broke near the middle. One line is now the goal, two the
ceiling, and narrowing a title container to manufacture a break is banned outright.
0.1.332 and 0.1.336 record the same shape, which is why it is now a maintenance rule.

**`scripts/check_design.py` (D1–D6)** makes the design half of the skill checkable
the way M1–M11 made the prose half: contrast, type floor, callout budget, palette
purity, figure parity (reported, not graded — the judgement is not automatable),
footer completeness. Run against the 0.1.337 deck it reports 32 contrast failures,
17 sub-floor type sizes, four pages over budget on 51.9% of pages, and two footer
gaps, which is the reader's list in numbers. `eval-rubric.md` also now requires a
self-score to carry its reasons; a bare number gives a reviewer nothing to diverge
from.

**Second reader pass, before this release shipped.** Two more defects, and both
say the same thing about how it was verified.

*The icon set was too small to say anything.* Eight hand-drawn icons across
twenty-five pages meant `gauge` did five jobs and the reader called the match to
content poor. Fixed by vendoring Lucide (2007 icons, ISC, `assets/icons/lucide/`,
searchable through its `tags.json`) and keeping LUMI's contribution where it
belongs: the reserved bindings in `scripts/embed_icons.py` that pin one icon per
recurring meaning. `embed_icons.py` now emits a **subset** sprite — the deck
embeds 25 icons in 7.7 KB rather than 0.9 MB of library. Breadth and consistency
are separate problems and a house set of eight solved neither.

*A figure shipped clipped.* The evals-ladder band was extended to y=212 inside a
viewBox 208 tall, so its bottom edge was cut and it collided with the caption.
`check_design.py` said all-clear because it reads declared CSS and cannot see
rendered geometry. Three browser checks are now in `design-rules.md` §7 — every
drawn element inside its viewBox, every label inside its shape tested at the
corners rather than the midline, and both re-run after any type-size change,
which had moved seven labels out of their boxes at once. Two of those three
probes passed clean on the visibly broken document before they were corrected,
hence the rule that a probe which has never failed is not a probe.

Also from this pass: a decision diamond had been used for a state, to satisfy the
new figure-parity rule. Parity means building every figure to the same level, not
using the same shapes regardless of meaning; the shape vocabulary still binds.

Two maintenance rules in `CLAUDE.md` (§7, §8) and one scoring rule in
`eval-rubric.md` (§3b): a validation artifact is never a source of conventions,
metrics passing is not a verified document, and a dimension where the reader found
a defect the author claimed to have verified cannot be self-scored above 3 in the
round that fixes it.

Deferred to a later round, recorded so it is not lost: a `check_version.py` that
tells a user of Claude Code, Codex or Gemini that their installed copy is behind
upstream. The immediate mitigation is to install the skill as a symlink to a git
checkout, which makes drift structurally impossible — the copy this round was
built against had been stranded at 0.1.334 while the repo reached 0.1.337.

## 0.1.337 — 2026-08-07

Two operational gaps, both found by asking why a step kept costing time.

**The display face now ships with the skill.** `design-rules.md` has required
D-DIN to be embedded since 1.2, and 1.2 itself shipped with the face declared but
not vendored, so it rendered nothing. The rule was right and the package could not
satisfy it: every deliverable's author had to find the font again. The two woff2
files (43 KB together) now live in `assets/fonts/` with their OFL text, and
`scripts/embed_font.py` prints the ready `@font-face` block or verifies the files
with `--check`. Confirmed the vendored files produce base64 byte-identical to the
already-shipped deck, so nothing about existing deliverables changes. CI checks
the sizes, because a silently swapped face would alter the metrics of every
document that embeds it. Note that `.gitignore` blocks font formats as
deliverable output and now carries an explicit exception — the face is part of the
design language, not a render.

**Waiting on CI is now bounded and outage-aware.** During the 2026-08-06 Actions
incident, open-ended polling consumed most of a working session and merged
nothing: runs queued for six minutes, were cancelled, were re-run, queued again.
`scripts/ci_wait.sh` asks the status page *before* waiting and short-circuits when
Actions is degraded, otherwise checking three times over about four minutes and
then stopping. The protocol behind it is recorded in `CLAUDE.md`: correctness is
answered locally by `check_repo.py` in seconds, CI only unlocks the merge button,
a cancelled run is a symptom rather than a verdict, and re-running into a declared
incident adds to the load causing it.

## 0.1.336 — 2026-08-07

Internal review: sales and marketing deliverables still read as AI-written. The
`humanizer` skill (github.com/blader/humanizer, MIT) was evaluated as a candidate
fix and its rules adapted rather than the skill adopted — LUMI keeps one source of
truth and no runtime dependency. See `NOTICE` for attribution and scope.

The evaluation found three causes, and humanizer only addresses the first:

1. **Coverage was lexical, not structural.** The `[en-output]` ban list was a
   five-item seed while English had been the default output language since 0.1.333,
   and the "delete filler phrases" move shipped without a list of filler phrases.
2. **The de-AI-flavor pass was an orphan.** It is the repo's only real
   anti-AI-flavor machinery and no workflow step, checklist, gate, or metric
   invoked it; it was absent from `prompts/lumi-style-core.md` entirely, so Kimi
   and DeepSeek users got none of it. The repo already knew the lesson — "a pass
   in the pipeline beats good intentions" — and had applied it only to punctuation.
3. **The mandated forms were themselves the tells.** A deliverable could satisfy
   every rule, score clean on all eight metrics, and still read as machine-written,
   because compliance is what made it read that way.

Changes:

- **[en-output] ban list grown from 5 entries to 8 grouped classes** — significance
  inflation, promotional register, AI high-frequency vocabulary, filler with its
  fixes, authority tropes, signposting, fake-candid openers, closing filler.
- **De-AI-flavor pass is now mandatory and gated**, with seven structural moves
  added (em/en dash ban for en sales/marketing, rule-of-three, list-shape variety,
  inline-header bullets, manufactured punchlines and aphorism formulas, boldface
  inflation, synonym cycling) and a two-pass audit: ask the draft what makes it
  obviously AI-generated, then fix what you named, and confirm no fact was added.
- **New section 6b, de-translationese** — sales and marketing material is now
  authored in English with Chinese translated from it, which imports a second
  failure mode. Precedent: 0.1.329 translated the Chinese rule "not X, but Y" into
  "Not X. Y.", models rendered it back into Chinese, and the round trip amplified
  until readers called the decks AI-flavored.
- **Conflicts with LUMI house style resolved in humanizer's favor**: negation-first
  openings retired as a mandated signature and stripped of their de-flavor
  exemption; the three canned responsibility frames reduced to a disclosure
  requirement phrased in the sentence's own words; the "short sentences" mandate
  replaced by a variance requirement; the accent-word bold made optional.
- **Structural loosening** — the colon title is the reference form, not the
  required one (capped at 60% of titles by M11); sibling-page parallelism only
  where it aids comparison; one to three support sentences of visibly differing
  length per page; the page arc is a default order rather than "never reorder";
  the stock metaphor and the imperative closing line are no longer mandated.
- **M8 is now two-tailed** (overlong share plus a sentence-length variance floor)
  and never waived for decks: it used to count only long sentences, so uniformly
  clipped prose — the dominant modern AI tell, and what the voice rule itself
  mandated — scored a perfect zero. **M9-M11 added**: em dashes, triad rate,
  title-shape uniformity.
- **`scripts/check_prose.py` added.** M1-M8 were called "scriptable" for six
  versions with no script in the repo. This measures M4 and M8-M11 on a real
  deliverable, and reports a file it could not parse as *unmeasurable* rather
  than clean — a linter that says "pass" when it read nothing is worse than none.
- `scripts/emergency_merge.sh` added: a documented, self-restoring path to merge
  when GitHub Actions cannot run the required check. `.gitignore` now also blocks
  deliverable exports and renders — this repo holds the skill, never its output.
- **CI now covers `scripts/`** (`py_compile` plus `bash -n`). It had none, so a
  syntax error would have shipped silently — including into the emergency path
  that runs precisely when CI is unavailable.
- **Fifth guard: ban-list parity.** `check_prose.py`'s phrase list is a second
  copy of §2 and was held to it only by a comment saying "change both together".
  `check_repo.py` now parses §2 and the script's declarations (by AST, so the
  guard never executes the other script) and fails when they disagree in either
  direction. Phrases that cannot be matched mechanically — `rich (figurative)`,
  `key (adjective)`, "adjective stacks in place of numbers" — must now be listed
  in `NOT_MECHANIZED` with a reason, which turns the gap between what the rules
  ban and what the machine can enforce from invisible into documented.

Review round on this release, recorded because the findings were real:

- The emergency merge script executed code supplied by the pull request. Copying
  a trusted `check_repo.py` over the PR's copy was not enough — the script's own
  directory is `sys.path[0]`, so a planted `scripts/json.py` hijacks an import
  and runs. Reproduced, then fixed with `PYTHONSAFEPATH=1` (Python 3.11+ now
  required) plus fork refusal and a merge-ref parent check.
- Its restore path could leave `main` unprotected while exiting 0, and a signal
  handler that returned instead of exiting let a killed merge report success.
  Distinct exit codes now separate "refused", "check failed", "could not run the
  checker", "merge failed", and "protection still off".
- `check_prose.py` matched multi-word entries as unanchored substrings and single
  words with word boundaries — exactly backwards. It flagged "deserves as much"
  and a finance "leverage ratio" while missing "leveraging" and "fostering", the
  actual tells. Every entry is now an explicit anchored pattern with its
  inflections, and ordinary business words are qualified rather than banned.
- Empty, non-UTF-8, and unparseable files reported "all metrics pass"; `--json`
  never evaluated a threshold and always exited 0; HTML markup merged into
  27-word pseudo-sentences that inflated the rhythm metric. All fixed and each
  verified against the failing case.

## 0.1.335 — 2026-08-07

Reader review of two shipped sales decks (zh + en, V0.1.333) against their own
V4.1 predecessor: "page titles suddenly became very short and AI-flavored,
overusing the it-is-X-not-Y contrast — this violates the PwC title principle the
skill was founded on." Measured: title length fell from a median of ~29 CJK
characters to ~8; display type rose 29.8pt → 37.4pt; every evidence figure
(18×, 4,557, 194, 29,845) vanished from the title line.

Root cause: 0.1.332 answered a review complaint about *visual* divergence from
spacex.com by writing a *writing* rule — "a giant short headline (3–6 words)" —
into design-rules §3, without reconciling it against the PwC title contract that
already existed in storyline-templates. The word ceiling then collided with the
still-standing requirement that a title be a complete assertion carrying the
takeaway, and with the negation-first signature's explicit de-flavor exemption;
in ~6 CJK characters the only form that satisfies all three is a bare antithesis.

- **The word ceiling is removed.** design-rules §3 now defers to the title
  contract; headline length follows the fact, bounded only by the two-line budget.
- **Title contract promoted to shared discipline** (was scoped to the consulting
  template, so sales decks had no title rule at all): "Topic: assertive subtitle",
  naming a subject and carrying a verifiable fact.
- **Information floor added**: a bare contrast, a slogan, or a section label is
  not a title. Contrast is a lead-in that must keep the evidence that earns it.
- **Two-line guard rewritten**: display titles are a size *range*; a long title
  takes the lower end before any word is cut. The old "shorten the title, never
  shrink the type" left cutting words as the only legal move once titles went
  giant, and the evidence went first.
- **Negation-first scoped** to the cover and hook, once per document; it is not a
  page-title form.
- **M1 is never waived for decks.** It had been marked "distorted for slides —
  advisory", which removed the only metric that measures this exact failure; the
  regression ran three versions unmeasured.

## 0.1.334 — 2026-08-06

Reader review of the anchor document (five annotated screenshots):

- Long-document callout hierarchy: three tiers (tinted+bordered key conclusion /
  left-rule guidance / muted note) — one uniform left-rule flattens the page.
- Charts: legend at the top right above the plot; two-part caption anatomy
  ("Figure N · Name" centered bold, description left-aligned at figure width).
- Flow-diagram shape vocabulary: parallelogram=I/O, rectangle=process,
  diamond=decision, stadium=terminal, dashed=not built — shapes carry semantics.
- Figure vocabulary ⊆ body vocabulary: body renames must sweep figure labels.
- Deliverables state results, not process: revision stories live in the ledger.
- Version lockstep refined: a user-assigned document-edition sequence (v1.01)
  owns filename+masthead; the colophon still records the producing skill version.

## 0.1.333 — 2026-08-06

Reviewer-driven round (five inputs from deck review):

- **Light-first**: the default canvas is near-white with the ink ladder; dark is
  applied only on explicit request via one `body.dark` override block. Both
  palettes share one token structure; literal colors in components or inline
  SVG are defects. Full dual-palette token set in `tokens/` (lumi-theme.css
  rewritten to v0.1.333; design-tokens.json restructured as palette.light /
  palette.dark).
- **American English by default**: when the user does not specify a language,
  output is American English (spelling, idiom, double quotes, serial comma);
  writing-rules §0 rewritten.
- **Icon-alignment guard** (from a reported alignment bug): an icon on a text
  line lives in a flex container with align-items:center — never a bare inline
  SVG nudged with vertical-align; icon ≈ 1.4× the accompanying text size.
- **Version lockstep**: a deliverable's version number is the lumi-style version
  that produced it; carried on the cover meta strip and closing colophon.
- **Cover and closing templates**: every deck opens with a typographic cover
  (wordmark / title / meta strip) and ends with a closing page (closing
  statement / recap / contact placeholder slots `[TO FILL]` — inventing contact
  details is inventing a fact / colophon). Added to storyline-templates.

## 0.1.332 — 2026-08-06

Direction change, reviewer-driven: "the output diverged from spacex.com — why?"
The 1.x fusion ("skeleton only, keep rounded type and light canvas") kept too
much consulting-deck idiom, and the one adopted SpaceX element (D-DIN in the
data voice) never shipped because the font was declared but not vendored.

- design-rules: decks are **dark-first** (near-black canvas, cold-white ink
  ladder); light canvas stays for long documents.
- design-rules: **D-DIN takes over** as the single Latin face; ALL-CAPS
  display titles at weight 400; rounded faces retired from decks; vendor and
  embed the font — a declared-but-unshipped face renders nothing.
- design-rules: one-statement-per-screen sharpened (giant short headline, one
  support sentence, one centerpiece, thin footer); hairline rows over card
  boxes on dark canvases.
- Accent green lifts to a dark-canvas form (#7C9F63); red text on black uses a
  lifted form while fills keep the seal red.

## 0.1.331 — 2026-08-06

- design-rules: added three field-tested guards from a reader-reported bug round —
  two-line title budget (shorten, never shrink); icon size independent of
  container scaling (blanket `svg{width:100%}` rules must exclude icons; an
  accidentally-stretched icon is not a design choice); in-row card alignment
  constraints (equalized title heights, stat numbers stacked above labels).
- design-rules: new "Verification matrix" section — language axis × viewport axis
  (design / print / short-laptop); footer rule and page number must be visible at
  every matrix point; height-based media queries as the mechanism. Supersedes the
  standalone localization guard (merged in).

## 0.1.330 — 2026-08-06

- Added the localization layout guard to design-rules: translated text runs
  30–50% longer/shorter — re-inspect every fixed-width container page by page
  after any localization pass. (From the English-deck audit: seven layout defects
  found — a wrapped stat band, ragged stat labels, and three SVG text overflows.)

## 0.1.329 — 2026-08-06

- **Repository language: English only — declared a red line.** LUMI serves a
  global audience; all rule prose, entry points, adapters, tokens, and this
  changelog are now English. Chinese strings remain only as rule data for
  Chinese-language output (banned phrases, punctuation patterns, collocation
  examples).
- Rules generalized to be output-language-aware: language-agnostic core
  (facts / voice / structure / charts) + a marked [zh-output] module; an
  [en-output] banned-phrase seed added.
- New field-tested layout guard in design-rules: right-anchored labels on
  full-width bars must anchor inside the fill (white-on-white invisibility bug,
  caught in per-page inspection).

## 0.1.328 — 2026-08-06

Initial release. Rules distilled from six rounds of real delivery polishing and a
first round of reader review on a consulting engagement's deliverables:

- Terminology red lines: no coined Chinese; direct English for concepts without
  an established Chinese term; substring-collision exemptions;
- Banned AI-tell phrases (with the "sales enablement" fixed-collocation lesson);
- Number discipline: sourcing, illustrative labels, repo-wide retraction with
  retirement notes for unreliable citations;
- The "value & future" sales storyline (boundaries converge to one trust page) —
  from a reader review scoring H5=2;
- "So-what is a writing discipline, not a page element" — from a reader review
  scoring H1=1;
- Plain-language scoring anchors ("anchors must be written in the reviewer's
  language") — from a reader review scoring H2=1;
- Five chart iron rules and form selection (partly adapted from
  enterprise-ai-skills, localized);
- Visual tokens v2: space-gray canvas + natural green single accent + China red
  warnings; layout skeleton informed by SpaceX/Tesla research (transparency
  ladder, dual-voice typography, cold-white dark canvas).
