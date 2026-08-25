## 0.1.596 — one analytical move, one drawing, for everybody, forever

An owner read three platforms' round-5 decks side by side and said the figures
looked alike. They did, and it was not the agents.

`shape_for` returned **`shapes[0]` of the first matching framework** —
deterministic on the analytical MOVE alone. Every page that declared `position`
arrived as `p126-2x2-01`; every `decompose` as `p125-top-down-01`; every
`compare` as `p156-very-attractiveaveragevery-unattractive-01`. The
alternatives the scaffold offered in its comment were **siblings of that same
unit**, so an author who varied the default varied within one visual family.

Measured. Across the four moves an outline can declare, the registry offers 25
shapes and the scaffold emitted **four** — the same four to every agent, on
every document, in every round. Of the library's 206 units, **1.9%** were
reachable. On the three round-5 decks the single `compare` default accounted for
**56%, 68% and 75%** of each deck's figure references, and the three decks
shared exactly the three defaults.

The candidate pool is now every shape of every framework that draws the move,
and the page's own planned title picks among them by digest. Content-derived,
so it stays reproducible — the same outline rebuilds the same deck byte for
byte, which `build_fixtures --check` gates on — while two documents about
different subjects, and two pages of one document, get different drawings.
Measured after: two outlines declaring the identical four moves now differ on
three of four figures.

**This did not widen the library, and the entry that says so is GAP-033.** The
pool is only as wide as `frameworks.json`, which names 23 of 206 units;
`compare` has three. Assigning the other 183 from their ids is the mistake
GAP-009 records — `box` is a 2×2 grid with a cycle, `surround` is an arrow — so
that stays a curation task done against rendered previews, not a patch.

Deliberate-red run: three of the five new tests fail against `pick = 0`, which
is the previous behaviour exactly.

## 0.1.595 — the corpus keeps its own numbers now

Two gaps have been open since 0.1.543 waiting for "a second measured document".
Neither was waiting on a decision. They were waiting because **no build kept its
numbers**, so every comparison had to be assembled by reopening old files, and
0.1.592's layout bar was duly drafted from five documents somebody had
remembered and refuted by a sixth nobody had thought of.

**Every build now records its own shape.** `trace.py` carries a `shape` block —
layout top share, layout kinds, figures, visual-share median, repeated-skeleton
pages — transcribed at close from the reports `check_deliverable` already ran.
No extra render, no second measurement. `ledger.py` reports the distribution and
nothing else: a reading says what a build WAS, never whether it was good. That
is the whole difference between a corpus that grows and a number somebody
invented.

**`scripts/ops/bar_replay.py` asks a proposed bar whether it contradicts the
record.** Given a metric and a number it replays them against every document
carrying an owner verdict and names the disagreements. Pointed at the withdrawn
`layout_top_share <= 50`, it reproduces 0.1.592's conclusion mechanically — and
finds a second disagreement the hand pass missed: **R1, which the owner
rejected, sits at 42.9 and that bar would have passed it.** The bar was not
merely wrong about the accepted document; it orders the two backwards. That
run is the tool's own deliberate red, and it is a test.

The tool sets nothing. It reports, and a person decides — a tool that could
write the threshold it had just validated would be the invented-number machine
with an extra step.

**The judge is organised by the rubric's own dimensions.** `judge_findings.py`
accepts an optional `dimension`, validates it against `rubric_items` rather than
a retyped list, and groups its report. The contract is untouched: a quotation
must appear verbatim, and there is still no field for a score, because a judge
that scores gets fooled by fluent verbosity and that is measured.

**A second review round changed this release too.** With mutation evidence, it
found that `bar_replay` passed its tests without consulting the owner's verdict
at all — both existing cases happened to be genuine disagreements, so a tool
that flagged everything produced identical output, and nothing asserted an exit
of 0. It found `test_the_tool_sets_nothing` disarmed by the three tests above
it: the snapshot was taken after they had already run the tool, so a mutant that
wrote to the corpus passed while leaving the tracked file modified on disk. And
it found the write side of the `shape` migration untouched — a trace opened
before this release, or carrying the `null` the schema explicitly blesses, died
at close with `KeyError` / `TypeError` and lost its record. That is 135 stored
traces and every build in flight.

It also found the text-only exclusion wrong about the real material: signature
parts are percentages rounded to ten, so one stray element makes
`line:0,text:100` — as structureless as `text:100` and not excluded by a rule
that keyed on the absence of a comma. Three of one deck's four signatures were
90%+ text and only one was excluded. The rule now keys on the text share, and
the count of excluded figures is recorded beside the clash count, because
`move_skeleton_clashes: 0` over nothing but text blobs reads as the stronger
claim.

And `bar_replay` now reports its two directions apart. A bar that FAILS a
document the owner accepted is wrong outright. A bar that PASSES one she
rejected is weaker evidence — R1 was rejected for its figures, so a layout bar
has no obligation to fail it, and collapsing the two would make every metric
unpassable as rejected documents accumulate, pushing an author toward a number
chosen to fail R1 for the wrong reason. That is this tool's own badge on the
invented-number machine.

**A gate was built, calibrated, and not shipped as a gate.** GAP-025 can be
asked without a threshold — two pages declaring DIFFERENT analytical moves must
not arrive as the SAME drawing — and the browser probe now carries each page's
`data-analysis` so the two facts stop living in different checkers. It does not
gate: the one accepted document on record and the one rejected beside it declare no
moves at all — both predate the convention — so neither can exercise it, and on the two decks that do, every
clash came from `text:100` — "a drawing made only of text", the absence of
structure rather than a structure two pages share. Excluding that leaves zero
clashes on both. **A check with no failing case anywhere is not a gate**, so the
count joins the shape block and waits for material. Both gap entries record it.

## 0.1.594 — every y-axis name this package shipped was invisible

The release set out to save round trips. Repairing the first instrument
uncovered a defect the instrument had been agreeing with.

**`svg .axname-y` rotated the label about the corner of the drawing.** The rule
is `writing-mode: vertical-rl; rotate: 180deg`, and the CSS `rotate` property
turns an element about `transform-origin` — which for an SVG element defaults to
the USER-SPACE ORIGIN, not the glyph. So every y-axis name was spun a half turn
about (0, 0) and thrown outside the viewBox, where the root svg clips it away.

Measured on this package's own passing fixture, **in the viewBox's own units**:
the label's box ran x −125.9…−110.1, y −242.4…−180 — wholly outside a
640×420 drawing — and a screenshot of the figure shows no vertical axis name at
all: bars, value labels, x-axis name, caption, and a bare axis where the name
should be. Nine drawings on nine pages, in the fixture the evidence gate renders
every release. `transform-box: fill-box` and `transform-origin: center` put it
back: x 110.1…125.9, y 180…242.4, left of the axis line at x=132, reading
bottom to top. The screenshot shows it.

*A first draft of this entry gave those four numbers as 103, 199, 90 and 148 —
the CSS-pixel values, the svg being rendered at 0.8219 of its user scale. Naming
screen units as drawing units is the exact confusion that produced the matrix
bug below, in the entry describing it.*

The rotation is about (0, 0), so this is geometry- and theme-independent: any
label at positive coordinates lands at negative ones.

**The check agreed with the defect**, which is why it lasted. `figure_clipped`
compared the UNTRANSFORMED box — see below — so it read the label's pre-rotation
position, found it inside, and said so. Two wrongs reporting green.

*This is the shape CLAUDE.md convention 8 is about: a metric that passes is not
a verified document. The fixture had passed every gate every release.*

**A claim this entry made and had to withdraw.** A draft said `figure_clipped`
had no planted failure of its own and passed `check_fixtures` only on the
accident above, and a new fixture was added to give it one. That was wrong:
`FIGURE_WEAK` has carried a deliberate runaway label since before this release,
and with the corrected matrix it still fails at 58 units. The suite's momentary
red was the *stylesheet* repair changing which pages failed, not the gate losing
its subject. The added fixture was removed. Recorded because "the gate had
nothing exercising it" is the most alarming thing a release can say, and it
should not be said without running the case without it.

**Two more things this release broke and repaired, both worth recording because
each is the release's own subject happening to the release.**

The first correction of the clipped probe used `getCTM()`, which for a direct
child of the root svg returns the viewBox-to-VIEWPORT matrix — so the corners
came back in screen units and a rect sitting comfortably inside a 400-unit box
measured 641 units outside it. `deck-degenerate` caught it. The matrix is now
`sv.getScreenCTM()⁻¹ · e.getScreenCTM()`, which cancels the viewport scale and
leaves only the transforms between the element and its svg. Convention 15, in
the release that quotes convention 15: a pattern written against an assumption
rather than against a real instance of every shape it meets.

And the stylesheet comment written to explain the y-axis defect contains the
words "screenshot of the figure" — which is one of the phrases `D25` accepts as
naming an image's terms. **D25 searched the raw file**, so a comment about
something else, in a file no reader opens, made a deck carrying an unattributed
linked image report `terms named`. It now searches what a reader sees, through a
new `markup.reader_text` that drops `<style>`, `<script>` and comments — the same
argument D26 already makes about scope notes, which is that a marker only the
checker can read does nothing but silence the checker.

### Six tools that were right about the document and unclear about themselves

A validation round measured the author's loop and found roughly **twelve extra
round trips, eighteen per cent of the calls**, spent on tools that had already
found the answer and could not hand it over. None of these changes what a
document must be; all six change what an author is told.

**A drawing was measured before its own transform.** `getBBox()` answers in the
element's own user space, and this package's axis-name convention rotates text
(`translate(x, y) rotate(-90)`), so such a label's untransformed box sits at
negative y. Six correct drawings in one deck were reported as clipped, and the
author shortened real axis names to silence a probe that was wrong. The corners are now
carried into the frame the viewBox is in — see the matrix note below for which
one, since the obvious choice is the wrong one.

**The same push recorded `{over, pct}` and nothing else** — eight pages, one
number each, and no way to find the element without writing a private probe. It
now names the worst element: `at <text.lbl 'this label really does run off…'>`.

**`debug_log validate` said `ok` about an empty self-assessment.** It graded each
entry in `quality`, so a block with no entries was graded zero times: a log
recording seven commands and not one self-score printed *the log holds its
contract*. That is the shape `verify_gates.py` exists to refuse — a validator
saying yes to work that was never done. Keyed on `commands`, so an initialised
log is not nagged before there is anything to assess.

**And the thing that emptied it:** `build.py --restart` rebuilt the log every
round, so scores passed on round 9 were gone by round 12. A C1–C8 score is a
judgement about the DOCUMENT, not about one round of building it. It now
carries across the restart, through the `assess` subcommand so a carried value
meets the same validation a typed one does.

**`judge_findings.py` could only validate the advice you did not take.** The
de-AI pass exists to change the sentence; once it has, the quotation that caused
the repair no longer appears and the finding was refused for having worked. One
build split its findings into two files for this reason. `--before <snapshot>`
holds a finding marked `fixed` to the text it objected to. **The contract does
not move** — the quotation must still appear verbatim, and `fixed` without a
snapshot is refused, because a repair claimed without the text it repaired is a
claim with no evidence.

**`brief.py` was built to save a round trip and cost five.** It writes the whole brief to
stdout — tens of kilobytes, and more with `--full` — which a harness with a single-output ceiling turns into a 2KB preview:
run it, probe the file, fail a Read on the token ceiling, read it in two halves.
`--out <dir>` writes it in parts and prints the manifest, which is where the count and the real sizes live — they vary with the genre, the storyline and `--full`. The parts are a
SPLIT of the joined text, not a second assembly — a test pins that they rejoin
to exactly the bytes stdout carries, because a `--out` that built the text its
own way would drift invisibly.

**`check_outline` accepted one dash.** `omitted: sizing - <reason>` reported
"declared without a reason" while the reason sat right there, and the syntax was
written down only in the script's docstring. Em dash, en dash and a **spaced**
hyphen now all separate — spaced, because a bare one would call
`go-to-market — deferred` a section named "go". The failure names the three.

**`check_design --json` returns a list, and a shell caller had no way to know.**
Three validation rounds each rediscovered it by crashing. The shape is not
changing: `checker_report.parse_report` already normalises it for every caller
inside the package, and a second shape would be a second thing to keep in step.
`--help` says it instead.

**A four-agent review ran before merge and changed this release too.** Beyond
the three withdrawn claims above, it found: the clipped probe fell back to the
untransformed box — the very ruler this release removes — whenever the matrix
could not be computed, silently, on a gating verdict (now counted and reported
as `CLIPPING NOT MEASURED`, which exits nonzero); the nested-`<svg>` branch
raised `worst` without claiming the identity, so the report named an innocent
element and sent the operator back to writing a private probe; `reader_text`
shipped as a second near-copy of `markup.SKIP_RE` in the module whose guard
refuses exactly that; **D25's tightening failed correct documents**, because
provenance written in an `alt` is provenance a reader meets and the narrowing
dropped it with the CSS; the assessment carry-forward died on a previous log
that was valid JSON but not an object, and lost a list-shaped `quality` without
a word; `brief.py --out` left a previous brief's parts in the directory and
still said "read them in order"; `judge_findings` accepted `<b> <i> <u>` as a
three-word quotation because the floor counted the raw string and the match ran
on the normalised one; `fixed` was satisfied by passing the same file as both
`--document` and `--before`; and `check_outline` chose its separator by tuple
order rather than position, so a reason containing an em dash keyed the section
under a name no checklist matches.

Deliberate-red runs: each item was reproduced before it was fixed. The clipped
pair got a real instance first (convention 15) — a rotated axis name that
renders wholly inside its box, reported at "10 user units" outside — and both
tests were then confirmed red against the old measurement. The rest were pinned
by tests that fail on the previous behaviour: an empty `quality` validating
clean, a second build round losing round one's scores, a `fixed` finding refused
against the repaired text, brief parts that do not rejoin, and a spaced hyphen
read as no reason at all.

## 0.1.593 — the id was kept and the record was not

A build trace's id rides in the document (`<body data-trace="t-…">`). Whether a
record answers to that id was checked on the delivery round and nowhere else.

**`trace.py close` fails on an id it cannot find** — `no such trace: t-…`,
nonzero exit — so a full `check_deliverable` run has always caught a dangling
id. **That step is skipped under `--fast`**, which is the author's inner loop
and the one run many times per build. So a deck naming a trace stored nowhere
ran the whole loop clean: **exit 0, and the word `trace` appeared nowhere in the
output.** The absent case was louder than the dangling one — a build with no
`data-trace` at all has printed `trace: none` since 0.1.531.

`check_deliverable` now resolves the id against the trace store on every run,
`--fast` included, and reports a dangling one as an unmeasured finding naming
the store it looked in.

*The field case: a six-run validation round across three platforms. Three of the
six decks carried a `data-trace` for a trace that is in no store — not
`~/.lumi/traces`, not the checkout's `evals/traces`, not even as an open phase
clock. Two of those three had recorded `check_deliverable` exit 0 in their own
debug logs, so the records existed when they closed and were gone afterwards.
**What removed them is not established, and this release does not claim to know
— it makes the condition visible on every round instead of on the last one.***

Deliberate-red run: a fixture deck patched with `data-trace="t-000000000000"`
and checked under `--fast`. The first draft of that test was wrong twice and
both mistakes are worth recording, because each is a way a green test can mean
nothing. It first injected the attribute into an earlier `<body` lookalike in
the file rather than the tag `markup.body_attr` actually reads, so the parser
never saw it. Corrected, it then passed against unfixed code — because without
`--fast` the close step supplied the failure the test was claiming to detect.
Only the `--fast` form goes red for the reason the check exists.

## 0.1.592 — the scaffold handed out the one layout the rule rules out

Three defects, one shape: a rule stated in prose, a tool that did the opposite,
and a metric that measured the gap and said nothing.

**The scaffold emitted `body split` on every content page it produced.**
`storyline-templates.md` has said since 0.1.521 that "a `split` page gives the
figure half the area ... so it cannot reach this number however the words are
trimmed. A figure-led page is `stack` or `split-wide` with the drawing in the
wide cell." `new_deck.py` hard-coded the excluded layout, so every author began
from it. Measured on the scaffold's own output: **10 of 11 content pages under
the 50% internal target, worst page 37%, top layout share 71.4%** — worse than
the **70.0%** deck a review rejected and recorded in GAP-024, while the accepted
reference deck uses `split` **zero** times. It now alternates `split-wide` and
`stack`, and hands a unit too thin for the figure box the whole width, which is
the advice `shape_fill` was already printing as a comment instead of acting on.
After: **4 of 11 under target, worst 46%, top share 42.9%.** A `stack` page also
emits ONE cell rather than two — that grid declares `auto 1fr`, so the third
child landed in an implicit auto row and the drawing rendered at **3%** of the
page. That number is why the rotation ships with the child structure and not
only with a class name.

*The field case: a ten-page deck built at 0.1.591 came back faulted by eye for
figures that were too small. Nine of its fourteen pages were one layout and
seven content pages sat at exactly 35% visual share. The author had not chosen
that; the scaffold had.*

**A trace inferred its entry path, and fingerprinted the wrong file.**
`new_deck.py` read path A from the mere presence of an `--outline` — an outline
is used on both paths — and passed that outline as `--recipe`. Two replays of
one frozen build script were therefore recorded as original four-beat builds
carrying identical outline hashes, which is the exact record `--recipe` exists
to make impossible. And because an outline carries no version stamp, those
builds read as `unknown` vintage for ever while the 39KB script that produced
every page was fingerprinted by nothing. The entry path is now declared
(`--entry-path A|B`, no trace without it, the same rule `--storyline` already
had) and the builder is recorded once it exists, with
`trace.py annotate --id <id> --recipe <build script>`.

**`version_in` could not read a recipe's own stamp.** One pattern claimed to
cover both a deliverable's colophon and a recipe's source. A build script writes
its colophon as `f"Built with lumi-style {VERSION}"` — an interpolation, not a
literal — so a script whose line 22 says `VERSION = "0.1.591"` read as
unstamped. Eleven builds sit in the ledger as `unknown` for this reason.
Convention 15 in one line: the pattern was written against the rendered artifact
and then applied to the source that renders it.

**The Hermes token counter reported exactly twice the truth.** `hermes()` summed
the four token fields and a second reader summed the same rows into the same
dict again; `api_calls` and `tool_calls` were correct, which is the worst shape
a broken instrument can take, because the counts look sane and the doubling
reads as usage. It survived two releases and was caught in the field by a
comparison that halved the numbers by hand and put the correction in a footnote
— a reader doing the tool's job. The two readers are merged rather than one
trimmed: the defect was not a stray line but two readers of one table sharing an
accumulator, and trimming leaves that shape for the next edit to re-grow.

**A bar was drafted here and withdrawn.** GAP-024 wants a threshold on layout
top share and five documents now carry a verdict; ordered, they looked decisive
(28.6 / 30.0 / 33.3 not faulted, 64.3 / 70.0 faulted). Measured against A1, this
package's own accepted reference: **78.6%**. The accepted document scores worse
than both faulted ones, so the bar was removed and the metric moved to
`reported_not_thresholded` with the counter-example beside it. That is the
automated route working — a bar a person had blessed would have shipped, and
this one disconfirmed itself in one command. The reasoning is recorded in
`specs/2026-08-24-round-4-retrospective-design.md`, which also records why round
5 has to run two passes rather than one.

The evidence gate's obligation map listed the layout instrument and the tokens
but not the generator between them, so a release that changed every page's
layout owed no browser check. `scripts/ops/new_deck.py` now maps to
`layout-fixtures`.

**A four-agent review ran against this release before it shipped, and it
changed the release.** What it caught, each verified by measurement rather than
by reading:

- **The first rotation collapsed on the plan-driven path.** It gave any unit too
  thin for the figure box `stack` whatever its turn; `shape_for` resolves
  `compare` to a unit that inks 6.7% of the box and `position` to one that inks
  38.4%, so an outline repeating one move put **every** content page in `stack` —
  a 100% top share, worse than the 71.4% being removed, through the door this
  package's own main route walks in by. The override is gone. The test that was
  meant to cover it could not: it looped over the one unit `shape_fill`'s
  docstring names as *filling* the box (100%), so its assert never executed —
  FM-01 and convention 11 in one function.
- **The scaffold's before-worst page is 37%, not 35%.** 35% is the field deck's
  number, and the two documents were merged into one row in three files.
- **The new evidence obligation rendered the wrong document.** It mapped the
  scaffold to `layout-fixtures`, which renders a hand-written fixture carrying
  ten `body split` pages and none of the new shape — an exit 0 that proved
  nothing about the change it was added for. There is now a `scaffold-render`
  obligation that renders what `new_deck.py` actually emits.
- **`version_in` had been widened for both its callers, and one of them decides
  which gates bind.** A document with no colophon but a line-initial
  `VERSION = "9.9.9"` would have manufactured a stamp and exempted itself from
  every newer gate — the exact thing CLAUDE.md forbids. The recipe reader is now
  a separate function.
- **`session_cost.py` crashed on a NULL `api_call_count`** (the merge guarded the
  tokens and left the counts) and reported an unknown session id as a whole
  table of zeros under a "1 session(s)" header. Both fixed; an unknown id is now
  refused, matching the Claude branch.
- **`ledger.py` printed "N build(s) had no recipe (path A looks like this)" over
  a bucket that is 100% path B** — false for every row it described, while the
  row data already carried the entry path.
- Three restatements the release contradicted and had not swept: `AGENTS.md`'s
  scaffold command, `references/build-card.md`'s one command, and two comments
  inside `trace.py`. Plus a `SKILL.md` section citation pointing at §4, which is
  "Five chart iron rules".

Two claims were also softened rather than fixed: the eleven `unknown`-vintage
ledger records had two different causes attributed to all of them by two
different files, and the trace does not record which file it hashed — so neither
cause can claim them. And the rule the scaffold now follows is scoped to Template
11's seed register; what generalises is "do not hand every page the narrowest
cell", not the 80% number.

Deliberate-red runs: the token double-count was pinned by a synthetic sqlite
fixture asserting a known row (`800 == 400` before, green after); the entry-path
and recipe defects by three source-and-behaviour assertions that all failed
first; the layout change by measuring the emitted scaffold before and after with
`inspect_layout.py`, including the 3% stack page the first attempt produced;
and the collapsed rotation by a test that generates an outline whose pages repeat
one analysis move, run against the reinstated override to watch it go red before
the override was removed.

## 0.1.591 — the counter did not ship

`scripts/ops/session_cost.py` arrived at 0.1.590 to settle a comparison, and
**the projection left it behind**: the consumer boundary is computed from what
SKILL.md names, SKILL.md did not name it, so the one tool both platforms need in
order to measure the next round shipped to neither.

This is the third time in four releases that an instrument was built and put on
no documented path — `--iterate` lived only in `--help` until 0.1.587, the
0.1.589 readings were named nowhere until this release named them, and now a
counter that CI could not see was invisible to the reachability computation for
the same reason. **A tool nobody is told about is a tool nobody runs**, and here
the boundary made that mechanical: the file was not merely unfound, it was not
present.

SKILL.md names it now, beside the debug-mode section, with both counting traps
stated where an author meets them.

## 0.1.590 — the calls the package was charging for, and the counter that found them

Design record: `specs/2026-08-24-fewer-round-trips-design.md`.

### The comparison that started this was measuring two different things

The owner's target was that Claude Code, on a stronger model and harness, should
spend fewer API calls than Hermes on the same deck. The reported figures were
**187 against 37**. Both were wrong, in opposite directions.

Claude Code writes its transcript with **one JSONL record per content block**,
and every record repeats the same `usage` object. A counter that sums per record
multiplies the call count and every token total. The build's real figure was
**70 calls**, and its reported tokens were inflated 2.5-3.6x. Hermes ran the task
across **two** sessions and the reading named one of them, with
`background_review` excluded.

Counted the same way, the whole task was **Claude Code 76 calls against Hermes
130** — the target was already met — with tool calls level at 121 and 117, and
output tokens 195k against 325k. `scripts/ops/session_cost.py` reads either
platform and prints both traps in its own docstring, because each of them fooled
this repository once.

### What the package was charging for

Ten forced round trips, each one the package's doing rather than an agent's
habit. In order of what they cost per build:

**A gating placeholder the package could always have filled.** The scaffold
emitted `Built with lumi-style VERSION`, and `check_design`'s `AUTHOR_FILL`
listed that string as a D14 **gate** — so every build by every user was
guaranteed one red round and one hand edit, to write a number
`debug_log._skill_version` had been reading all along. The scaffold stamps
itself now, and the pattern is gone from `AUTHOR_FILL`, because a pattern
guarding nothing misleads the next reader.

**Eleven to fourteen reads before the first page.** SKILL.md names them by line
and the build card is explicitly an addition, not a substitute. On one measured
build that was 20 calls and 82,000 output tokens before a page existed, with
84KB fetched twice by two different tools in adjacent calls.
`scripts/ops/brief.py --genre <g> --storyline <s>` fetches all of it once. **It
changes nothing about what is read** — the card's own warning that an agent
composing from it alone produces a document that passes everything and says
nothing is repeated at the end of the brief.

**A debug log that refused the second round.** `debug_log init` declines an
existing log, and `build.py` passed no `--restart` and had no flag for one — so
every iteration after the first died before a single stage ran, and one build
moved the log aside by hand nine times. One run of the driver **is** one build's
record, which is the invariant that guard protects; it restarts by default now.

**A verdict block that named the check and not the page.** `deliverable_verdicts`
returns `(verdict, detail)` and both JSON emissions dropped the detail, so an
author who knew which check failed re-ran the renderer to learn which page —
four calls on one build, for information already in memory. The block carries it
now. The `capWrapped` line immediately above was the same need, solved by hand
for exactly one finding.

**A shape library that published no geometry.** All 206 units carry a non-zero
viewBox origin, 133 of them span more than 1000 user units, and `tags.json`
carried a ten-word relation vocabulary and no measurements. So placing a label
meant reading raw SVGs — four calls for eleven shapes — or estimating, and one
build estimated: **five figures drew outside their own viewBox**, and the round
that followed rewrote the whole figure layer.
`assets/shapes/geometry.json` is generated and `--check`s in CI.

**And the same manifest explains the thin figures.** The scaffold's figure box
is 640x239 — 2.68:1, which is `p009-arrow-3d-01`'s proportion and almost nothing
else's. A `<symbol>` maps its own viewBox into that viewport, so **160 of the 206
units ink less than 55% of the box and the median unit fills 43%** — which is
exactly the visual share both round-3 decks reported, and the page an owner
picked out by eye with "the figure is too small". The author was handed a
starved box and graded on the drawing.

The scaffold says the number when the shape is chosen, and names the three real
answers: a wider unit, a layout with a squarer cell, or something composed
beside the drawing. **It does not resize anything.** A scaffold that stretched
the unit to make the metric move would be 0.1.339's withdrawn fill floor in
another costume.

**A debug contract asking for documents the driver destroyed.** `attach` wanted
each checker's `--json`; `check_deliverable` gathered all three in memory and
wrote none — so honouring the contract meant re-running all three checkers, one
of them a second browser render. `--reports-dir` hands them over and the driver
attaches in process. `assess` cost eight more calls, and **SKILL.md documented
the wrong dimension names** (`H1..H6` against the code's `C1..C8`, a mismatch
`debug_log`'s own comment describes), so the first one was a guaranteed argparse
failure. `build.py --assess C1=4:"…"` folds all eight into the run being made
anyway.

**Three checks and a trace outside the driver.** `check_facts` — the only check
that asks whether a rebuild still carries the facts it was built from — was not
in the stack. The pre-build half of `check_outline` was not either. `export_pdf`
had no caller anywhere in the package. And the trace closed only on a green,
non-`--fast` run, so every loop round left one open for `ledger.py` to report as
abandoned; a red build is still a measured build, and it closes now.

**A contact sheet that cost one read per page.** It is an HTML page referencing N
PNGs, on the stated reasoning that pure stdlib cannot composite. The browser is
already paid for: 17 of one build's 27 file reads were page shots at 120-384KB,
the cover read four times. `--sheet` now also screenshots the sheet it just
wrote — one image, every page, one read.

### Rounds

`build.py` keeps each round's layout reading and passes `--against` itself from
the second round on. The reading that says **"no measured number moved — if you
were repairing something here, the repair did not land"** now appears without
anyone asking for it. One measured session ran six rounds after its last
failure with nothing able to tell it that, and its debug log recorded nothing on
a green round, so neither the author nor a reader could say whether those rounds
improved anything.

### Corrected

`specs/2026-08-23-english-is-the-artifact-design.md` is marked **superseded** —
its derivative requirement was withdrawn by the owner the same day, and an
unmarked spec is a stale truth waiting to be cited. And 0.1.589 printed D6's
Chinese provenance words into the scaffold's genre card, so eight CJK characters
shipped inside every English deliverable; the card prints the English words and
the checker keeps the full list.

## 0.1.589 — the language you asked for, and the reading that confirms a repair

Design record: `specs/2026-08-23-language-direct-and-worklist-design.md`.

### The owner withdrew 0.1.588's language mechanism, and she is right

0.1.588 required a non-English deliverable to be DERIVED from a finished English
one. No agent can fake that, and it is the wrong answer: it writes the same
content twice. Her rule is simpler and it is the one this package should always
have implemented —

```
new_deck.py                                              # English, the default
new_deck.py --lang zh-Hans --lang-asked "<their words>"  # they asked for Chinese
new_deck.py --lang ja      --lang-asked "<their words>"  # they asked for Japanese
```

A deck asked for in another language is **authored in that language**, not
translated into it. `localize.py` stays, demoted to what it is actually good
for: giving a finished deck a second language version to ship beside the first.

**What survives is the cheap half.** `--lang-asked` carries the user's own words
rather than a boolean — 0.1.587's boolean was typed by the agent on the same
command line as the language it was attesting to — and the document keeps them
as `data-lang-ask-quote`. M16 fails a non-English deliverable with no quotation.
It costs nothing: the sentence already exists if it was ever said.

Four defences, in order: a rule; the rule restated in four entry points; a gate
on a declaration, satisfied by editing the declaration; a gate on a boolean,
satisfied by typing it. **A field an agent can fill with nothing is a field an
agent will fill.** What a local script can ask for is a claim with CONTENT —
words attributed to a person who will read them — and what it cannot do is
verify them. `publish.sh` states the same limit about the same class of problem,
and stating it is part of the fix.

### One shape cleared ten declared moves

`D32_shape_use` counted DOCUMENT-WIDE and failed only when a document declared
analytical moves and drew no library shape anywhere. A measured deck read
`1 library shape(s) on 10 analysis page(s)` — **green**. Both prose sites
describing this metric said *a page* that declares a move draws the library's
shape for it, so the code was the half that was wrong, the same shape as
RC-431's false enforcement claim.

Per page now. On the deck above: `9 of 10 analysis page(s) draw no library
shape: p4, p5, p6, p8, p9, p10`. No fixture verdict moved.

It also makes reuse the cheap path, which it was not before: on one measured
pair of builds the deck that drew its figures by hand spent 343k output tokens
against 115k for the one that reused shapes, and output costs about 94x a cached
input token.

Making it per-page surfaced **GAP-032**: `correlate` is one of the five
analytical moves and has no entry in `assets/frameworks.json` at all, so a page
declaring it arrives with an empty figure slot. A page is held only when its
move is one the library can draw, and the exemption is printed — which is how
the gap became visible rather than becoming a false failure.

### An instrument that finds a defect, and none that confirms a repair

The deepest finding of three validation rounds. A build diagnosed a page's dead
band and collapsed figure correctly — better than this release's author did —
fixed it twice, and shipped it still broken. Every gate was green before and
after, because **the three numbers that describe that defect were computed,
printed, and read by nothing**: `centerScale`, `emptyBandPct`,
`aspect.fillsCellHeight`.

`inspect_layout --against <before.json>` reads them. It prints what moved per
page, in `check_outline --against`'s four-tier vocabulary, and says the sentence
that was missing:

```
note  every compared page   no measured number moved — if you were repairing
                            something here, the repair did not land
```

It reports rather than gates, on that file's stated caution — a page rewritten
better than its plan is a legitimate outcome. A gating verdict that goes ok to
FAIL is the exception and exits non-zero. The comparison lands in a sibling
`against` block and **never inside `verdicts`**, because `run_conformance` turns
every key there into a required-ok gate on every task.

### The emptiest figure was the one nothing annotated

The annotation that says a figure is small fired on `aspect.ratio > 1.5` — a
HEIGHT reading — so a wide flat figure that filled its width and a third of its
height got no annotation, while two better pages did. `fillsCellHeight` is
derived from the declared viewBox and reads 100 whenever ratio ≤ 1; the measured
pair `drawnH`/`cellH` was computed, carried, and never printed.

By area now, against a floor **calibrated rather than reasoned**: the reference
fixture's ten figure pages run 61.7–82.7; one shipped deck runs 93–97 on eight
pages and 35.9 on the ninth; another runs 71–81 on five and 37 on the sixth. The
two low pages are the two an owner picked out by eye. 55 sits in the gap and
clears the reference by 6.7 points. Reported, not gated — one release of
readings before any floor gates.

### Two roles, one sentence

`D41_role_echo`, reported. A 20-page sales report put one sentence in a `.gd`
and again in the page's `.take`; a later deck's `.take` was its `.sup` with the
head cut off, word for word, and its `.lead` restated the first half of the
title. Two documents is this package's bar for promoting a lesson to a rule.

The `.lead` case has a cause worth naming: SKILL.md ENCOURAGES `.lead` on a page
whose argument turns on one number and says nothing about what `.lead` must
carry that the title does not — so the cheapest way to satisfy the rule is to
repeat the title. **Following the rule produced the defect.**

### The checkers could not read Chinese, and one of them edited a page

`D6_PROVENANCE` was English-only while `check_prose.SOURCE_MARKERS` had carried
`来源` / `出处` / `示意` / `实测` for releases, so a Chinese colophon reading
`出处：…` was
reported as missing provenance on **every page**. The author of one such
deliverable refused to edit correct Chinese to go green and was right. The
regex is now built FROM the tuple rather than retyped beside it, and the
`source-marker parity` guard — which read only `check_prose`'s list — now fails
when one of the two vocabularies is blind in a language the other reads.

`D26`'s `TYPICAL_SECTIONS` were English strings tested against the document
text, so a correct Chinese deliverable reported every typical section missing —
and the author of one put a bilingual coverage table on a page to satisfy it.
**The checker decided what the page said.** Each entry now carries the Chinese a
reader would meet, through one shared `section_alts`/`section_name` helper
rather than three unpackings.

### And the debug log could not name two language versions apart

`debug_log init` took the stem before the FIRST dot, so `x.0.1.588.zh-Hans.html`
and `x.0.1.588.en.html` wrote to one `x.debug.json` — and since `init` refuses
to start when the log exists, the second one hard-failed, or with `--restart`
destroyed the first one's evidence. It takes everything but the final extension
now, so `guide.en.html` and `guide.en.pdf` still share one log, which was the
point. `build.py` asks `debug_log` for the path instead of computing its own.

### Corrected

**GAP-030's evidence was written backwards.** It said "ten figures, zero
`.cap .srcline`", as though a missing caption source line were the defect — zero
is what D37 REQUIRES, since the source is the drawing's own last text node. The
conclusion held; the evidence named the wrong thing. Restated: two deliverables
carry a source **nowhere**, and `inspect_layout` looks for one in the place D37
gates against, which is a contradiction the entry now records. The spec that
repeated the claim is corrected too.

## 0.1.588 — a field an agent can fill is a field an agent will fill

Design record: `specs/2026-08-23-english-is-the-artifact-design.md`.

Third validation round. Same English source document — 54KB, zero Chinese
characters. Same Chinese output. Third release.

**0.1.587 asked for a record that the user had asked. The build wrote it
itself:**

```
new_deck.py --genre internal --geometry landscape --lang zh-Hans --lang-asked …
```

M16 passed. The attestation and the thing attested to were typed on one command
line by one party.

**And a control run the same day settles what this is not.** A Claude Code
build, loading the published skill with **no companion skill present**, produced
Chinese from the same source. Its transcript orders the decision: scaffold,
*then* announce `zh-Hans` among settled parameters, *then* read
`writing-rules.md` where the default is written. The language was decided before
the rule that governs it was read. So the earlier entry naming a machine-curated
companion skill as the "proximate trigger" claimed too much — corrected here and
in FM-18; it was a contributing factor, and the failure does not need it.

Four defences have now been tried in order: a rule; the rule restated in four
entry points; a gate on a DECLARATION, satisfied by editing the declaration; a
gate on an ATTESTATION, satisfied by writing the attestation. **What holds is a
gate on an ARTIFACT.**

### English is not a rule any more; it is the artifact

`new_deck.py` has no `--lang` and no `--lang-asked`. Neither does `build.py`.
Every build is American English and there is no flag to make it otherwise.

Another language is `scripts/ops/localize.py`, a second command producing a
second file. It refuses unless the English deck **already passes its own
checks**, requires the user's verbatim words, and writes three declarations:
`data-lang-asked`, `data-lang-ask-quote`, and `data-localized-from` naming the
English source. M16 fails a non-English deliverable missing any of them — and
the third cannot be satisfied by typing, because the file it names has to be
there.

The consequence that matters is not the gate. It is that **producing Chinese now
costs a complete, passing English deck first**, so the owner gets the English
version whether or not the agent was right about the language. That is what a
default is; a sentence in a rule file is not.

Said in the script itself, in `publish.sh`'s words about the same class of
problem: no local script can verify the quotation came from the user. What
changes is the cost, and that the claim now sits where the owner reads it.

### The package was arguing the other side

Declaring `zh` did not only silence M12 — it **woke** `M4zh_banned_hits` and
`M5_zh_punctuation`. One build's first machine reading was `FAIL
M5_zh_punctuation 93`, and it answered by adding a full-width punctuation pass
to its build script. Several dozen actionable readings coaching better Chinese,
against one sentence saying the document should have been English.

The Chinese metrics are now conditional on M16, not on the declaration: when the
ask is not recorded they report `n/a` with nothing to fix, and say why. `is_zh`
split in two — which metrics can MEAN anything on spaceless text is a different
question from whether to grade the Chinese, and conflating them briefly had the
English rhythm metrics scoring Chinese prose at 0.0.

The language is also stated ONCE, up front, instead of being reassembled from
four scattered `n/a` notes: `check_prose` prints a language block before the
metrics, and `check_deliverable`'s verdict block prints a language line — that
file had zero occurrences of `lang` before this release.

### Ten pages, by owner directive

`new_deck.py`'s no-outline default was 6 — this file's own invention, and it sat
BELOW `evals/thresholds.json`'s `min_content_pages: 8`, so a default scaffold
escaped the corpus ratios entirely and M11 reported `n/a` for want of titles.
Ten clears both, and at the default `--parts A,B` runs five pages per part,
which is `opener_pacing`'s target exactly.

### Not one of three deliverables could reach exit 0

`--deliverable` conflated two silences. A check that CRASHED and a check with
**nothing to measure** — no `.band` in the document, no bar rectangle in any
figure — both exited 1. The component-colour line calls its own criterion "a
window, not a rule about your figures" and failed the run anyway.

Measured: three deliverables, three platforms, three releases, every one
`NOT SHIPPABLE`, every one for lacking an optional block. The reference fixture
passes only because it happens to use every block this package defines, which is
a rule nowhere.

`Unmeasured` now counts `failed` and `absent` apart. `failed` gates; `absent` is
reported in the same line so nobody hunts for why a count moved. All three real
decks now exit 0 with their absences still printed, and `deck-broken` and
`deck-degenerate` still fail on 14 and 15 gating findings respectively — the
gate did not soften, it stopped answering a question nobody asked.

### Deliberate red, run first

The round-2 deck was measured before the change (M16 `ok`, exit 0 — the
self-signed flag) and after (M16 `FAIL`, exit 1). The three real decks were run
before and after the unmeasured split; every one had `0 gating findings fired`
both times, so nothing was masked. A third Chinese fixture joins the two: pass
(derived, graded), broken (derived, Chinese defects fail), unasked (no
provenance, M16 fails and the Chinese metrics fall silent) — because with the
coaching conditional there was no longer any fixture that could fail `M4zh` or
`M5`, and `check_fixtures` requires one for every graded verdict.

Seven tests for `localize.py`, five rewritten in `test_gate_semantics.py`
(including one that reproduces 0.1.587's mechanism exactly and asserts it is no
longer enough), and the two that pinned the old defaults.

## 0.1.587 — the cheapest way past the language gate was to relabel the document

Design record: `specs/2026-08-23-language-gate-and-build-cost-design.md`.

An English source document, 54KB and not one Chinese character in it, produced a
wholly Chinese deck. The rule it broke has been written since 0.1.333 — American
English is the default, another language is ASKED for and never inferred — and it
is restated correctly in four places. It was catalogued as **FM-18** after the
first time. This was the second.

**The build was stopped, and got past.** `M12` fired: Chinese in text a reader
sees, in a document declaring `lang="en"`. The fix applied was to change the
attribute to `lang="zh-Hans"`. M12 asks whether an ENGLISH document is free of
Chinese, so a document declaring Chinese is `n/a` to it — one attribute, and a
gating failure became a pass. Nothing else in the package asked whether the
document should have been English at all.

So the rule did not lose to an agent ignoring it. **It lost to being cheaper to
satisfy the wrong way**, which is the shape this repository has now fixed in
three different gates.

**M16 is the half a sentence cannot do.** A deliverable in any language but
English carries `data-lang-asked="<code>"` on `<body>`, written by
`new_deck.py --lang <code> --lang-asked`, and M16 fails one that does not.
English needs no record — it is the default, and reads `ok` rather than `n/a`,
because a metric that goes quiet on the ordinary case teaches a reader to skip
the row. Relabelling `lang` no longer silences anything: it moves the document
from M12's question to M16's.

The register was claiming an enforcement that did not exist. `RC-431` mapped
"Write in American English when the user specifies no language" to **M12, gates:
yes**, and `page-contracts.md` printed the claim — so an agent reading the
generated contract index was told a machine was holding a rule no machine could
see. RC-431 and RC-003 now cite M16, and two new entries name the sentences M12
and M16 actually measure.

**Deliberate red, run first.** The Chinese deck and the `prose-zh-broken`
fixture were measured before the metric existed (M12 `n/a`, exit 0), then after
(M16 FAIL, exit 1); the English fixture stayed `ok` throughout, and recording the
ask via `--asked-lang` returned the deck to exit 0. Six tests in
`tests/test_gate_semantics.py`, beside the ones for the escape M12 left open.

The rule also moved to where questions are asked. It sat in SKILL.md's preamble
for both builds that broke it, while Step 1 — the step that organizes the
questions — never mentioned language. It is now in Step 1 beside genre and
geometry, it is the **seventh** red line (the six omitted it while including a
Chinese-coinage rule, so an agent compressing the rules to six came away
thinking Chinese output was routine), and the two restatements that named only
genre and format now name language too. `build_entrypoints.py` matched the
literal string "## Six non-negotiable" and crashed on a seventh line; it reads
the heading now, which is convention 13 applied to the generator written to stop
prose from counting.

### The same build cost 460 API calls, and the workflow was why

Measured from the host's own session store rather than estimated: **460 API
calls, 105.4 million cached input tokens, 389 terminal commands, about 50
minutes** for one ten-page deck. The bill for an agent build is `calls x context
per call`, and both halves were the workflow's doing.

`inspect_layout` ran **64 times at 22 seconds each** — twenty-three minutes and
sixty-four round trips — against **6** runs of `check_deliverable.py`, the one
command that already contains it. Not one of those 70 expensive runs used a loop
flag; `--iterate` and `--no-sheet` appear nowhere in SKILL.md, `references/` or
`AGENTS.md`, only in `--help`, and the sentence beside the command said "pass it
the file and nothing else" — written about `--geometry` and read as a ban on
every flag.

**The structural cause was ours.** `check_deliverable` forced `--no-sheet`, so
the contact sheet — the artifact this package calls the last gate — was
unreachable from the one-command path, and every author ran the slow instrument
a second time to get it. It takes `--sheet` now and prints where the sheet
landed; `inspect_layout`'s JSON carries the path, which it never did.
`check_privacy` was prescribed as a standalone step AND run inside
`check_deliverable`: a duplicate the skill itself specified. The per-instrument
paragraphs that followed "one command runs the whole stack" were written as
imperatives; they now say they are already inside it.

**`scripts/ops/build.py` is the missing driver.** Nothing in this package ran
scaffold -> fill -> embed -> check, so each stage cost a turn whether or not
anything had changed. It runs all four in one process — measured end to end on a
fresh scaffold at **3.96 seconds** — and writes the debug log as a side effect,
so debug mode stops costing one wrapped command per turn (16 of them on the
build above). It refuses a non-English `--lang` without `--lang-asked`, before
scaffolding rather than three stages later, because that fix is a question for
the user and not an edit to the document. It invents **no** page-content format:
the fill script is the author's own, which is the pattern real builds already
converged on, and a schema designed without a real instance in front of it is
convention 15's warning.

`new_deck.py` takes `--out` — "this prints to stdout, redirect it" was the
single most-repeated build trap on record, and a driver that must capture stdout
cannot record its command through `debug_log run`, which writes stdout itself.

**`references/build-card.md` is the context half.** Following SKILL.md literally
costs about **98,000 tokens of reading before the first page**, and ~148,000 with
the two files it pressures you into; every call then re-sends it. The card is
generated from the registers and the tokens — the three must-asks, the 53 gating
verdicts, what gates per page kind, the layout and role vocabulary, the one
command — at about **5,900 tokens**, `--check` in CI, every line carrying its
`file:line`. It states on its own face that it is not the rules and that an agent
reading only it will produce a document that passes everything and says nothing,
because that is precisely what five conformance rounds produced.

**A logged failure was not a resolved one.** `debug_log validate` passed as soon
as `errors` was non-empty — and `run` fills `errors` automatically, so the pair
could never disagree. The build above recorded `"exit_code": 1` for its layout
check and for its full-stack check, both as the LAST run of each, and the report
beside it called them green. `validate` now fails when a command's last run is
red and nothing ran it clean afterwards, unless an error message cites an OPEN
`KNOWN_GAPS` entry — `check_evidence.py`'s rule, which had no counterpart on the
deliverable side. Run against that build's own log, it reports both.

## 0.1.586 — the confirmation named one version and the push shipped another

The gate added at 0.1.585 read the version from `$DEV` — whatever branch happens
to be checked out — while the thing it pushes is a projection of `origin/main`.

So publishing 0.1.585 from a branch, while `main` was still at 0.1.584,
confirmed 0.1.585, shipped 0.1.584, and printed **"published 0.1.585"** over
content whose stamp said 0.1.584. Caught by asking the published repository what
it actually carried, one command after the push.

**A confirmation that names something other than what is pushed is worse than no
confirmation**, because it is believed. This is the third defect in three
releases in the same small piece of code, and all three are the same mistake:
the line a person reads before an irreversible act was describing something
other than the act — an unknown version at 0.1.584, a cached version at 0.1.583,
and now the wrong version entirely.

`here` is read from the projection. The test asserts both halves — that it reads
`$WORK/proj`, and that it does not read `$DEV` — because the second is what
regressed.

Verified end to end this time rather than by reading: published, then asked
GitHub what the file says. It says 0.1.585.

## 0.1.585 — the gate built one release ago blocked the person it was built for

0.1.584 made `--push` refuse whenever stdin was not a terminal, reasoning that
an agent running non-interactively could not then publish. **The owner ran it
and it refused her.** `!` in Claude Code has no TTY either, so a check meant to
distinguish an agent from a person distinguished neither — and failed in the
worst available direction, against the person it existed to serve.

Convention 15, in the release that added the gate: look at a real instance
before writing a pattern that keys on its shape. I wrote a model of how she
works instead of looking at how she works.

**The honest replacement admits what a local script cannot do.** No command can
tell whose hands typed it, and this one no longer pretends to. What it can do
is make publishing impossible to do by HABIT, and that is the actual failure
being prevented: a bare `--push` had already become routine — mine, after every
merge, which is what the owner asked to stop.

So `--push` takes the version as an argument. `--push 0.1.585` names what is
about to happen; a missing or mismatched version refuses and publishes nothing.
A version changes every release, so it cannot become muscle memory the way a
flag can.

Three refusals, each verified against the real script: no version named, a
version this checkout is not at, and the dry run that remains the default. The
test that asserted the TTY check now asserts its ABSENCE, with the reason,
because the next person to reach for `-t 0` should meet the story rather than
the idea.

## 0.1.584 — publishing needs a person, and the script is what holds that

Owner instruction, 2026-08-23: the push to the published repository waits for
her say-so, one publication at a time. 0.1.582 gave a release a note about how
far the projection was behind; this makes the push itself stop.

**`--push` is no longer enough.** The last step prints what is about to happen —
the version being published, the version being replaced, and that the published
history is REPLACED rather than merged — and then asks for the version to be
typed back. A keypress would not do: typing the version means having read the
line above it.

**And it refuses outright when stdin is not a terminal.** That is the half an
agent cannot satisfy. Everything else in the script is a check a machine can
pass; this one exists so that an agent running non-interactively has to hand the
command back rather than decide. A rule that lives only in an agent's memory is
a rule until the next session, which is convention 16's whole argument and the
reason `release.py` refuses to commit on a red preflight rather than trusting
anyone to look.

The refusal says what is true: every check passed, nothing is wrong with the
projection, and what is missing is the authorisation.

Also fixed on the way: the "replacing version X" line read `an unknown version`
because the remote probe was built from a mangled repository slug — a line that
is wrong is a line that gets skipped, and this one is the last thing read before
a force-push. It asks the API rather than `raw.githubusercontent` for the reason
0.1.583 records: the raw host is a CDN and names the previous version for
minutes after a publish, which is exactly when this line is read.

Six tests, none of which push anything. One of them asserts the confirmation
compares against the version rather than accepting any answer, because the
difference between those two is the whole feature.

## 0.1.583 — the note told the truth of five minutes ago

0.1.582's publishing note read `raw.githubusercontent`, which is a CDN and
caches. Measured immediately after publishing 0.1.582: the API returned
0.1.582 and raw still returned 0.1.581.

So the note told someone who had just published that they were a release
behind. That is worse than no note — **a tool that is wrong right after you
act trains its reader to ignore it**, and this one exists precisely to be
believed at that moment.

It asks GitHub's API through `gh` now, which this workflow already depends on
(`emergency_merge.sh`), and which answers from the repository rather than from
an edge cache. Two more tests: one asserts the command is `gh api` and carries
no raw host, and one asserts a body that is not base64 returns None rather than
raising out of a note.

Found the way the last three of these have been found — by running the thing
and reading what it said, one command after the change it was reporting on.

## 0.1.582 — a release now says how far the published package is behind

Two repositories, and nothing joined them. The development one advances on every
merge; the published projection advances only when `publish.sh --push` runs. So
the projection falls behind SILENTLY — it did, between 0.1.580 and 0.1.581, and
a person noticing was the only thing that caught it.

`release.py` asks the published package which version it carries and says so as
its last line, beside `shipping.report()`'s count of unpushed work. Same
argument, one repository over: forty releases once accumulated on an unpushed
branch while every local check stayed green, because nothing asked.

**Reported, never a gate.** Being behind is a normal state — a maintainer may
hold several releases before publishing, and a gate here would fail a release
for a decision somebody made on purpose. What is not normal is not knowing.

Four answers, and the two that are not "behind" both took a fix:

- **In sync** says nothing to publish.
- **Behind** names the gap and the command, counted from the CHANGELOG rather
  than from either git history — the projection's commits are REWRITTEN, so
  their hashes cannot be compared to this repository's at all.
- **The published package is NEWER** is not a gap of minus three. It means this
  checkout is behind its own remote, or something published from elsewhere, and
  the first draft reported it as "-3 release(s) ahead".
- **Could not ask** says exactly that. A release must not fail because an
  advisory note could not be written, and a note claiming "current" on a failed
  fetch would be worse than none.

`curl` rather than `urllib`, and the reason is the kind this package keeps
finding: a Python.org install on macOS ships without a certificate bundle, so
`urlopen` failed here with CERTIFICATE_VERIFY_FAILED against a URL `curl`
fetches with a 200. Shelling out is this file's habit anyway — every other step
reads an exit code from the process that produced it.

Eight tests, none of them touching the network.

## 0.1.581 — the board is refreshed, and the answer to the question 0.1.575 could not answer

0.1.575 changed what a prose row can return and what an exit means, and waived
the conformance obligation with the honest reason: a deck that scored `pass` on
the r16-pinned board might not score `pass` now, and the board could not say so.
This run answers it. **It still passes.**

Four agents driven concurrently against 0.1.580 — the version carrying the
`blind` verdict, the exit computed from `check_deliverable`'s own buckets, and
M12's refusal to treat an undeclared language as an exemption.

| | T1-deck | T2 | T3 | |
|---|---|---|---|---|
| Claude Code | pass | pass | pass | **3 of 3**, T1 in 17 minutes |
| Cursor | pass | pass | pass | **3 of 3**, T1 in 30 minutes |
| Hermes | not earned | pass | not earned | 1 of 3 |
| Gemini CLI | not earned | not earned | not earned | 0 of 3 |

**Not one verdict on either passing deck was `blind`, and not one was `n/a`.**
Every row read `ok`. That is the result the change was supposed to produce: a
gate that fails a document refusing to say what language it is in should be
invisible to a document that says so, and both agents' decks do.

**Hermes fails in a shape, not at random.** Its T1 stalled after 1854 seconds
and its T3 came back `misplaced` in 25 — both times a deck existed on disk and
the harness declined to credit it, because the path was not one Hermes had
NAMED. That is 0.1.572's rule working: a path the transcript names is evidence
of authorship, a path that merely appeared is a coincidence with a timestamp.
The artifact is kept under `misplaced/` rather than deleted, so the operator can
see what was rejected and why.

**Gemini CLI earned nothing on any task**, failing T2 and T3 in fifteen and
seventeen seconds. The key on this machine is free-tier; the harness records
what happened rather than guessing why.

Two agents fully passing is what the freshness obligation asks for, so
`releases/evidence/0.1.575.json`'s waiver is discharged here rather than
carried forward.

**And the refresh found a defect in the release that fixed this exact class.**
0.1.568 collapsed the operator's home directory in what `report` RENDERS and
missed what it RECORDS: `history.json`'s `run_dir` kept writing the absolute
path, so every history row carried the username into a tracked file.
`check_local_paths` caught it on the first refresh after that release, which is
the guard doing its job — but the fix had been reported as complete. Both ends
are portable now, including the de-duplication comparison, which would
otherwise append a second row for one run; verified by re-recording and
counting.

## 0.1.580 — the publication was a script in /tmp, which is where steps go to be forgotten

0.1.578 gave the published package a check that can speak for it. This gives the
PUBLICATION itself one, because until now it was a shell script in a temporary
directory — the shape of every step this repository has lost between sessions,
and the reason `release.py` exists at all.

`scripts/ops/publish.sh` rebuilds the projection from `origin/main` and checks
five things before its last line, which is the only line that pushes. A
projection is easy to rebuild and a published name is not, so the order is that
way round rather than "push, then look".

**The check worth naming is the first one, and it refuses rather than reports.**
`check_secrets`'s client-name half reads the operator's out-of-bounds list, and
its default location is usually EMPTY — so the guard returns the same green
whether it checked or skipped, which is how 0.1.579's finding survived until the
day of publication. The script will not publish without a list at all. An empty
directory is not an absence of clients.

The other four: every release subject preserved (`check_evidence` and `shipping`
read them to find a version, so losing one breaks the next release rather than
this one); no development file rode along; the home-path and English-only guards
asked of the PROJECTION rather than of this tree; and a fresh clone of the
projection builds a deck above a 400 KB **floor** and passes its own checkers.

`--push` is opt-in; the bare command is a dry run.

**It went red on its first real invocation, correctly.** It reads `origin/main`,
0.1.579's fix was still in review, and it refused to publish a projection
carrying the name that release removes. That is the whole design working before
it had shipped.

## 0.1.579 — a name the owner had declared out of bounds, found by running the scan the publication needed

Publishing the projection is irreversible in the way that matters — a name that
reaches a public repository has reached it — so the pre-publish step was to run
the guards against the PROJECTION rather than against this tree. Three came back
clean. Then the fourth revealed that one of them had not actually run.

**`check_secrets`'s client-name half needs the operator's list, and this machine
had none installed.** The guard says so in its own comment — *"In CI the
directory does not exist and the half is simply not run"* — and a clean report
from it means "no credential shape", never "no client name". Pointed at the
owner's real list, it failed immediately: a company name she had declared out of
bounds sat in a `CHANGELOG.md` entry, and `CHANGELOG.md` ships.

Red line 9's hard core is that no client name reaches a tracked file, and the
2026-08-20 audit found a city name in eight of them. This is the same class,
one file, found before publication rather than after. The sentence is
anonymized the way every other entry in this file is.

**The city name in the same paragraph stays**, on the owner's ruling: it is used
as a project codename rather than as a client, and it is not on her list. Written
down so the next scan does not re-open it.

The lesson is about the SCAN, not the string: a privacy guard that silently
skips its own subject reports the same green as one that checked. The
publication checklist now points the guard at the operator's list explicitly,
because the default is an empty directory and an empty directory is not an
absence of clients.

## 0.1.578 — the published package gets the only check that can speak for it

The projection carries no tests, no repository guards and no development
scripts. `check_repo.py` grades THIS repository and cannot say whether the
shipped package still works; nothing could, until now.

`.github/workflows/skill.yml` ships. It runs here and it runs in the projection,
and it uses the skill the way a reader does:

- the scaffold renders, above a **floor** of 400 KB — a scaffold that shrank to
  nothing would otherwise still "succeed", and the floor is under the embedded
  font, icons and shape sprite rather than a size to aim at;
- the reference document passes its own three checkers, which is what makes it
  usable as an assertion at all;
- a raw scaffold is clean where it must be from the first byte — a raw scaffold
  FAILS the design checks, because it is full of slots, so only the half that
  can be clean is asserted;
- **every shipped script loads.** The projection drops modules nothing
  reachable imports, so an ImportError here means the boundary cut a live edge
   — the one failure `check_shipped_closure` and `check_cross_boundary_paths`
  cannot see, because both are static and this is not;
- a store is written where the package SAYS it is written.

Every step was run against a real projection built from this commit's parent
before the file was written, which is the order convention 15 asks for — and it
was still not enough. The first push went red on `eval_corpus.py`: one of its
thresholds is measured by RENDERING, so on a machine with no Chromium it
reports "a threshold that was not measured has not been cleared" and exits 1,
correctly. It had passed locally only because this machine has Playwright.
Asserting it would either force a browser on everyone who forks the published
package, or bake in the exact green-on-my-machine failure this workflow exists
to catch. Verified the other way round before removing it: with `playwright`
made unimportable, `check_design` and `check_prose` stay green on the reference
document and `eval_corpus` does not.

The second push went red on the store step, for the mirror-image reason: it
asserted the trace landed in `/tmp`, which is true in the projection and FALSE
here, because this repository has `evals/traces/` and the resolver correctly
prefers it. A workflow that ships has to hold in both trees. The invariant that
does is the one worth asserting anyway — a trace lands in the store the tool
NAMES — and it was checked in a real projection and in this repository before
being written down this time.

**And the published repository now says where changes go.** `CONTRIBUTING.md`
is development-side, so a reader landing in the projection had nowhere to look —
and an edit made there is overwritten by the next publish. One paragraph in
`README.md`, which ships, says so. Written carefully: the first draft named
`adapters/shipped.json`, a file the projection does not carry, which is the
cross-boundary prose class this same review had just found three instances of.

That class is now a recorded DECLINE rather than an open question. Extending
`check_cross_boundary_paths` to markdown was proposed and refused in
`FAILURE_MODES.md` FM-23: an ATTRIBUTED mention is legitimate — `README.md`
names the conformance board and says "in the development repository" in the same
sentence — and a guard that cannot tell the two apart would instruct an author
to delete a useful reference. Deciding whether an English sentence attributes
its reference is the phrase-trigger class AG-1 already declined.

The boundary guard caught its own author on the way in: the rule was added to
`adapters/shipped.json` before the file was `git add`ed, and `shipped closure`
failed it as a rule claiming nothing. That is the guard doing exactly what it
is for.

## 0.1.577 — a guard that could whitelist a wrong name against itself, and a store that changed under a tool without saying so

The review's remainder. Three things that were not defects yet and were each one
edit away from becoming one.

**`check_verdict_names` read `evals/*.json` whole, and one of those files stores
verbatim quotes of reference prose.** So a wrong verdict name written into a
sentence that `rule-coverage.json` quotes would enter the guard's dictionary and
whitelist itself against the guard policing that very sentence. Exactly one
snake_case token lives in those quotes today and nothing is masked; the
circularity is the defect, not its current reach. The JSON gives up its KEYS
now. Both directions re-checked on the real tree: a name that exists nowhere
still fails, and `visual_share_median` and `page_share` still do not.

**`check_review_scores` could report `ok` having read nothing.** 0.1.572 taught
`review_scores.py --check` that an absent store is a legal state — right for a
freshly installed skill, where nobody has reviewed anything yet. It is wrong
here, where the store is a TRACKED file: an absent one is a deletion, and the
guard whose stated reason for running in CI is red line 9 would pass having
validated nothing. The guard asks about the tracked file itself before
delegating.

**`state_dir` moved a store under a tool without saying so.** The resolution
flips on whether a directory happens to exist, and two of the four candidates
are gitignored — so a fresh clone, a worktree, or deleting one untracked file
moves a store with no warning, and a write afterwards leaves two copies
diverging invisibly. `describe()` names which arm answered, and the one tool
that prints a store path uses it. `run_conformance` prints `writing into
{run_dir}` for the same reason.

Also: `references/eval-rubric.md` said "Eleven exceptions" and listed
seventeen — pre-existing, and convention 13's answer is to delete the number
rather than correct it.

The design record is `specs/2026-08-23-gate-consolidation-design.md`.

## 0.1.576 — the tests the review found could pass against broken code

0.1.575 fixed what five reviews found. This is the other half of what they
found: assertions that held while the thing they were named for was gone.

**Three tests could not fail.**

- `test_the_four_stores_all_route_through_it` checked BASENAMES. Every basename
  is identical under the pre-0.1.571 `ROOT / "evals" / "corpus.local.json"`, so
  reverting the fix passed the test written to prevent it — and two of the four
  stores were never asserted at all. It cannot be asserted on the resolved
  values either, because `in_repo` correctly wins in a maintainer's checkout,
  which is where the suite runs. It reads the SOURCE now: no store may build an
  in-repo path by hand.
- `test_a_finding_with_no_declared_metric_keeps_its_own_heading` accepted
  `"privacy:" in out`, which the finding line itself satisfies — the disjunct
  survived deleting the heading the test is named for.
- `test_a_path_built_from_two_pieces_is_seen` asserted `== []` twice and never
  showed a two-segment join being seen.

**And nine behaviours had no test in the failing direction**, every one of them
something this range shipped, broke, or fixed with nothing watching: the four
`silent` branches that lost their exit; an unknown `lang` value; the summary
line agreeing with the exit; a blind gate travelling through `check_deliverable`
rather than only through `check_prose`; an empty consumer set and a missing
SKILL.md; a register declaring no layout verdict; the derived generator list
being non-empty and complete against `ci.yml`; and the home-collapse guard for a
root home directory.

The pattern in all twelve is the same one this repository names in its own
conventions: a check that has never fired is not a check, and an assertion that
cannot fail is not an assertion. Twelve of them shipped inside a run whose whole
subject was gates that could not go red.

**And `SKILL.md` said "gates on four things" while eighteen design verdicts
gate** — in the file an agent actually loads, unwatched by anything, and carried
through 0.1.569's restructure without a sweep. It names the authority now
instead of counting, and it is a declared gating-claim site: the guard fails if
the sentence goes, and fails if a list grows back into it. Each authority-named
site now declares its own anchor, because there is more than one and they do not
share wording.

The design record for this phase is
`specs/2026-08-23-gate-consolidation-design.md`.

## 0.1.575 — five reviews of the eleven releases before it, and three bugs I wrote in the last one

A full review of 0.1.564–0.1.574 across five lenses: comment accuracy, test
coverage, silent failures, convention compliance, and a prose-drift sweep. It
found three live bugs, all of them mine, all of them from 0.1.574.

**A document nothing could measure exited 0.** 0.1.574 stopped inheriting the
instruments' exit codes so that `since` could move a finding out of the gating
bucket. Five branches append to `silent`; only one still raised the exit. So
`check_deliverable` — the pre-delivery step SKILL.md names — printed
`gating metric D12_handling_terms could not be measured (this is not a pass)`
and returned **zero**, and because the run looked clean it then closed the build
trace as a completed passing build. A deck whose pages are `div.page` rather
than `section.page` takes both commercial gates silent that way; a Chinese deck
exported as GB18030 does it to the whole prose instrument. Every silent branch
raises the exit now, and `main` holds the invariant the summary line has always
asserted: a finding in either bucket is a nonzero exit.

**`check_prose` printed "all metrics pass" on a run that exited 1.** The `blind`
verdict was counted into `gated` and not into `failed`, and the summary branches
on `failed`. An author reading the tool's own last line ships the document. This
is the summary-contradicts-the-exit failure three lines below the comment that
says the release exists to end it.

**The M12 escape reopened one character wider.** 0.1.574 closed "delete the
`lang` attribute". `declared_language` returns whatever the attribute SAYS, with
no membership test, so `lang="xx"` went straight back to `n/a` — printed as a
legitimate exemption. `gate_registry.held` gets the closed-set question right
one field over: an unknown name is never silently exempt. Any language this
package does not produce is now treated as undeclared.

**And the boundary could be redrawn in silence.** `shipped.consumer_scripts()`
seeds itself with a regex over SKILL.md. A documentation pass that names the
commands in prose rather than as paths collapses it — measured: **fourteen
scripts flip to the development side, `new_deck.py` among them**, the projection
ships nothing runnable, and BOTH boundary guards stay green, because "dev" is a
valid side and the cross-boundary loop simply iterates over nothing. An empty
consumer set raises now, and a missing SKILL.md raises rather than returning
one.

**A rule was gating on something no rule file stated.** M12 now fails a document
that will not declare its language, and `references/` never asked for a
declaration — the remedy existed only inside a failure message. `writing-rules`
§0 states it: a deliverable declares the language it is in, and silence is not
an exemption because it is the cheapest one there would be.

Also closed, from the same five reviews:

- `gating.layout_verdicts` still returned the empty set on an unreadable
  `inspect_layout` while the comment beside it said all three readers raise.
  Two more callers — `check_rule_coverage.audit` and `run_conformance`'s scoring
  pass — turned that raise into a traceback rather than a finding; a scoring
  pass that cannot read the gate set now says so instead of discarding a run
  that has already driven every agent.
- `check_verdict_names` returned `[]` when the register declared no layout
  verdict, which in this file means "checked and found nothing".
- `emergency_merge.sh`'s trusted closure carried neither `shipped.py` nor
  `state_dir.py`, so the two new boundary guards would have run a pull
  request's own copy of the module that decides what ships. The test that
  should have caught it kept a hand-written module list that stopped at
  `corpus`; it reads `check_repo.SIBLING_MODULES` now.
- `trace_store.ROOT` raised `StopIteration` from an import in any tree without
  a `SKILL.md` — its sibling, written the same release, carries the fallback and
  says why.
- Fourteen comments and docstrings that had stopped being true, including two
  hypotheticals I had written in the past tense as shipped defects (convention
  14, in the release that fixed three of them), `release.py` carrying two
  different numbers for one fact twenty-eight lines apart, and `trace.py`
  claiming a re-resolution that has never happened.
- The prose sweep: `blind` existed nowhere outside this file; the register's own
  `na_means` for M12 stated the pre-0.1.574 rule; the review protocol told an
  author that an undeclared document was harmless; three reference files still
  named `reviews/scores.json` as a path; `thresholds.json` — a shipped file —
  pointed at two things the projection does not carry; `scripts/README.md`'s
  import-edge paragraph was false in five places; and nothing outside a
  docstring documented where an operator's stores live, which is now
  `operating-rules` OR-8b.

The conformance board is **not** refreshed here and the evidence file says why:
this release changed what a prose row can return and what an exit means, so a
deck that scored `pass` on the r16-pinned board might not score `pass` now, and
the board does not say so. Refreshing it needs the owner's keys and cannot run
in CI. Recorded as an obligation, owed before any number from that board is
quoted again. The review and what it found are recorded in
`specs/2026-08-23-gate-consolidation-design.md`.

## 0.1.574 — a document escaped the Chinese gate by deleting one attribute, and the version scope was cosmetic

The third half of the adversarial review: what a verdict MEANS, and whether a
document can escape one.

**Deleting `lang="en"` took M12 from FAIL to silence.** M12 is the gate that
fails an English deliverable carrying Chinese a reader can see. It went `n/a`
whenever the document declared no language — and `check_deliverable` prints no
`n/a` — so a byte-identical deck with one attribute removed exited 0 and the
Chinese appeared nowhere in the report. `gate_registry.held` settled the same
question one field over: **an absent stamp must not become an exemption**,
because the cheapest escape would otherwise be to omit the line that says what
you are. Nothing in this package requires a deliverable to declare `lang`, and
`new_deck.py` emits one, so any hand-assembled or converted deck was one
deletion away.

It does not GUESS the language, which would be a worse cure. A document with no
CJK has nothing for M12 to find and is honestly `n/a`. A document that carries
Chinese and will not say what it is cannot be decided, so it is measured as
**blind** — a third verdict beside ok and n/a — and blind on a gating row fails
the run, with a message naming the three ways to declare.

**The Chinese pair stated a reason that was false.** `M4zh_banned_hits` and
`M5_zh_punctuation` came back "too little data: 149 sentences" on a document
with 149 sentences. The true reason — the document is not Chinese — has been in
`evals/gates.json`'s `na_means` since the register shipped, and the printer
never read it. This is the third time this exact failure has been found in this
printer, and the comment three lines above it claims to have fixed it.

**`since` never changed an exit code.** The block filed a too-new gate under
`not held` and the run still failed on it, because the exit was INHERITED from
the instrument — and `check_design` grades against HEAD by construction and
knows nothing about `since`. The summary then read `exit 1 · 0 gating findings`,
which is a summary contradicting the block above it. The exit is computed from
this block's own buckets now. An instrument that exits nonzero and produces no
verdicts is a different thing: that is a crash, and it still fails.

**And a claim in the design record was wrong.** It said no assertion had been
deleted, only names and readers reduced. The red team tested that rather than
believing it: **it is false for `check_prose`.** GAP-029 narrowed the prose exit
from "any failing row" to "any failing row whose target is zero", which on this
repository's own degenerate fixture turned five real defects — every title the
same shape, 90% triads, 82.6% overlong sentences, 0% of figures sourced — from a
failing run into a passing one. The decision stands and its reasoning is good.
It is still an assertion removal rather than a rename, and
`specs/2026-08-23-gate-consolidation-design.md` says so now.

Also: the register's own row count was stale in four places in the release that
introduced it — the failure class this repository names as its worst, inside the
thing built to end it. The number is deleted rather than corrected, per
convention 13.

## 0.1.573 — six guards that were green while wrong, and two that were red while right

The second half of the adversarial review: the guards themselves. This
repository's rule is that a guard's first proof is that it can go red — the
review asked the other question, **can it stay green while wrong**, and the
answer was yes six times.

**A verdict that blocks delivery could be invisible to the register.**
`check_gate_declarations` read every three-element `ast.Tuple` in the module.
So a row written as a LIST (`rows.append([...])`) emitted a fully functional
gating verdict the register never had to declare, and a row whose NAME was
built at runtime was skipped in silence. Both now fail: rows are read from the
`rows` table specifically, a list row is a row, and a name that is not a literal
is a finding about the checker rather than a pass.

**Worse, the guard could be talked into breaking the register.** A target that
is not a literal — moving `"=0 (gates)"` into a constant — read as the WEAKEST
severity, so a live gate silently became `graded` AND the guard then reported
the (correct) register as the liar. An operator following that message would
have demoted a real commercial gate. An unreadable target is now a finding, not
a downgrade.

**And the answer depended on `ast.walk` order.** A three-element tuple in an
unrelated helper — `("D12_commercial_footer", "design-rules.md", "section 6")`
— overwrote the real row and produced the same false accusation. Reading the
`rows` table rather than every tuple ends it.

**The fiftieth gate was audited against unrelated code.** The privacy parity
asked whether `'if kind == "privacy":'` and `"gating.append"` both appeared
anywhere in `check_deliverable.py`. In the real file they are eighteen lines and
one scope apart: `gating.append(line)` belongs to the METRIC loop, and the
privacy branch appends through `(gating if held else not_held)`. Demoting the
privacy gate left the guard green. It parses the branch now.

**`gating.py` had three failure policies for one broken file, and two of them
meant "nothing gates".** An unreadable register made `gating_metrics` return the
empty set, which `run_conformance` reads as "no design or prose verdict is
required" — it would have scored a conformance deck on the layout verdicts
alone. All three raise now: a register nobody could read is a fact about the
run, not a verdict about the document.

**Two guards would have made an author edit correct work**, which is the
failure this repository takes most seriously.

- `verdict names` failed **23 real identifiers**, `visual_share_median` and
  `page_share` among them — actual output keys of `eval_corpus.py` and
  `check_design.py`, mapped to a rubric dimension — because the verdict
  families include ordinary English (`page`, `content`, `title`, `visual`). The
  message told the author to rename correct code. The repository is its own
  dictionary now: an identifier that exists in the tracked code is a real thing,
  and what remains is a name that exists nowhere, which is what an abbreviation
  or a half-remembered name actually is. Harvesting dict KEYS and subscripts
  rather than every string constant, because the first attempt let this guard's
  own docstring — which cites `figure_axis` as the thing it exists to catch —
  enter the dictionary and pull its teeth.
- `local paths` failed `/Users/you` in an install instruction, accusing the
  author of shipping a username they had not shipped. Placeholders are named
  now. The tilde-user form `~someone/` is IN scope, because it leaks exactly as
  the absolute form does — with the slash required, since `~2.6s` in a timing
  note is not a home directory, and the first draft failed on this file's own
  performance figures.
- `prose gating claims` failed a **column-aligned table**: the row pattern
  demanded exactly one space, so any markdown formatter turned a correct table
  into an accusation, and a partial match routed past the "re-point the entry"
  branch into the wrong message entirely.

The review and what it found are recorded in
`specs/2026-08-23-gate-consolidation-design.md`.

Two of the fixes were themselves caught by existing tests — the placeholder list
invalidated `test_local_paths`'s own fixture name, and treating an empty `rows`
literal as a missing table failed four synthetic trees. Both were the tests
being right.

## 0.1.572 — the red team built the projection and drove it, and the boundary was wrong in eight places

**Three adversarial reviews, run against 0.1.556–0.1.571 with one instruction:
break it.** This entry is the split half; the gate half follows. Every finding
below was demonstrated with a runnable command before it was accepted, and every
one is now a test.

**The crash I shipped one release earlier.** `eval_corpus.py --corpus` — the
flag's headline path — died with an uncaught `ValueError` on any machine with no
local corpus. 0.1.571 moved the registry out of the repository and left
`local_path.relative_to(ROOT)` behind, so the line that REPORTS the absence
raised on it. It survived here only because this machine happens to have the
file. **This is the exact class the cross-boundary guard cannot see**, which is
the argument for driving the projection rather than reasoning about it.

**A partition that reported itself total published two maintainer files.**
`side_of` compared with a bare `startswith`, so the `NOTICE` rule claimed
`NOTICE_TO_MAINTAINERS.md` and `LICENSE` claimed `LICENSE-AUDIT-NOTES.md`. This
repository has now shipped the same missing path boundary **five times** —
`\bcard\b` matching `f-card` among them. `shipped.matches()` spells the
comparison out.

**One capitalised letter disarmed the teeth silently.** Writing `"Dev"` instead
of `"dev"` in a rule made an entire directory invisible to
`check_cross_boundary_paths`, while `check_shipped_closure` still reported a
total partition — because it only asked whether a side was non-`None`. Both the
side value and a non-empty `why` are validated now.

**Half the tree was unscanned.** The boundary scan matched double-quoted
literals with a regex, and this repository's lint config selects no quote rule:
`inspect_layout.py` alone carries five hundred single-quoted strings. It reads
the AST now, which sees single, triple and implicitly-joined literals; it
reconstructs `/`-chains of any length (two was the old limit); it treats a
wholly-development DIRECTORY as fatal, because `ROOT / "reviews"` resolves to
nothing after the projection; and it reports a dynamic
`importlib.import_module("x")`, which is an import the reachability that decides
the boundary cannot see.

Two exemptions, both by construction rather than by waiver, and both found by
running it: a path named only as `state_dir.store(in_repo=...)`'s fallback is
the thing that is ALLOWED to be absent, and a directory holding any consumer
file is not missing — `evals/` carries `thresholds.json` and `gates.json`.
A bare word is not a path either: `trace_schema.py` declares the enum value
`"conformance"`, which is not the directory of that name.

**`.gitignore` was on the wrong side, and it is the only mechanical enforcement
of red line 9 on a working tree.** The consumer half ships every producer of
operator data — `eval_corpus`, `check_privacy --terms`, `ledger`, `trace` — and
the projection carried no ignore rules at all, so a client's terms file, a
corpus registry naming engagement paths and a rendered deck under `docs/` were
all staged by a plain `git add -A`. Demonstrated, then fixed.

**Two development tools rode a docstring into the consumer half.** Reachability
cannot tell a CALL from a MENTION: `check_globe` (2,200 lines, needs Playwright)
shipped because `geo_projection.py`'s docstring says the projection "is held to
them by a golden grid in scripts/check/check_globe.py", and `build_worldmap`
because an error string names it. `dev_pins` fixes both — and a pin is AUDITED
rather than trusted: no consumer script may IMPORT a pinned stem, which is the
half a mention cannot fake.

**`new_deck.py`'s only edge to the trace store was invisible.**
`pathlib.Path(__file__).with_name("trace.py")` is exactly the assembled path the
regex was added to catch, and the regex could not see it — there is no
`scripts/<drawer>/` in the string. `trace` stayed on the consumer side by
accident, through an unrelated literal in another file.

**An absent store is not an unreadable one.** `review_scores.py --check` exited
1 on every fresh install, reporting "unreadable" with a raw errno — which reads
as corruption — before a single review had been recorded, and naming a path that
was not the one it opened. Nobody has reviewed anything yet is a legal state.

Also: `scripts/README.md` had no rule and was being classified by the script
computation; `evals/rule-coverage.json` and `fixtures/expected.json` ship with
no consumer reader and are development now; `README.md`'s one link that breaks
in the projection is prose; `scoring_sheet.py`'s Chinese sheet promised to
transcribe into a path the projection does not carry; and `SKILL.md` said
`review_scores.py` "stores what comes back" when its CLI is `[-h] [--check]` and
it has never had a write path — convention 14, in the entry point.

**The projection was built and driven, not reasoned about.** 2,415 files, 260
commits, every release subject preserved — which matters because
`check_evidence.find_release_commit` and `shipping._released_versions` read
them. A fresh clone of it builds a 622 KB deck from the scaffold and runs the
whole consumer surface. The sequence and the assignments are in
`specs/2026-08-23-gate-consolidation-design.md`; the second repository exists
and is private until its contents have been read.

## 0.1.571 — four stores that only exist because a repository is around them, and the guard with the teeth

**The consumer half has to stand on its own, and four things it writes did
not.** The trace store, the local corpus registry, the price table and the
review scores all resolved against the repository root. Three of them are
gitignored on purpose — one machine's facts with a date on them — and all four
would have no directory to live in once the skill is installed from a projection
that carries no `evals/` and no `reviews/`.

`scripts/lib/state_dir.py` is the one answer: `LUMI_STATE`, else
`$XDG_STATE_HOME/lumi`, else `~/.lumi`, with the per-store variables that
already existed still winning over all of it.

**The resolution is deliberately not a flat default.** It prefers the in-repo
directory WHEN THIS CHECKOUT ACTUALLY HAS IT, so a maintainer's existing data
stays exactly where it is and **no release moves an operator's file**; it falls
back to the state directory everywhere else, which is what an installed skill
sees. Nothing creates a directory by resolving — `check_privacy.py`'s
`LUMI_TERMS_DIR` is the precedent and the 2026-08-09 instruction is explicit:
create on an explicit write, never on import and never on a read.

**`check_cross_boundary_paths` is the guard with the teeth.**
`check_shipped_closure` (0.1.570) proves the boundary is total; this proves the
consumer half can survive the projection. A script that ships while the file it
opens does not is a skill that is green here and broken in a fresh clone — the
class `check_assets_tracked` exists for. It reports **zero** today, because the
four stores are what it would have found: the residue was measured first (five
paths across five scripts), then closed, and the guard is what keeps it closed.
Planted red on real material anyway, since a check that has never fired on a
real artifact is not a check.

Two limits, stated rather than implied: a path assembled from variables is
invisible to it, and an untracked path is not its business. Both guards are the
prerequisites `specs/2026-08-23-gate-consolidation-design.md` names as landing
before any file moves, and with these two the list is closed.

**An existing test went red, and it was right to.** `trace_store`'s default
changed, so the test asserting it unconditionally now asserts both halves — the
checkout that has the directory and the install that does not. Twelve new tests
besides. `state_dir` also carries corpus.py's tolerant root fallback, without
which a guard test's synthetic tree raises `StopIteration` from an import.

## 0.1.570 — a list of what ships can omit a file silently; a partition cannot

**The boundary the repository split needs, landed before anything moves.** The
design record calls for the public repository to be a mechanical projection of
this one rather than a hand-copied subset, and a projection needs a boundary a
machine can compute.

`adapters/shipped.json` is that boundary, and it is written as a **partition**
rather than as a list. The distinction is the whole point: a list of what ships
can omit a file and still look complete, which is the failure
`check_assets_tracked` was written for — *a guard that reads the filesystem
cannot tell "published" from "on the author's machine"*. `check_shipped_closure`
requires every tracked file to be claimed by exactly one rule, every rule to
claim at least one file, and every declared seed to name a script that exists.

**Scripts are absent from the manifest on purpose: their side is COMPUTED.**
Reachability from the scripts SKILL.md tells an agent to run, following imports
AND `scripts/<drawer>/<name>.py` strings — this package's scripts invoke each
other by subprocess as often as they import each other, and a boundary that saw
only imports would cut a live edge. A script nobody can reach from the skill's
own surface is development by default, which is the safe direction to be wrong
in: a dev script wrongly kept is dead weight, a consumer script wrongly dropped
is a broken install.

**Measured, not estimated.** 2,976 tracked files partition into **2,417 consumer
(8.49 MB) and 559 development (4.61 MB)**, and 65 scripts into 40 and 25. The
single largest item on the development side is `assets/shapes/source/` — 207
vendored originals, 2.77 MB, 22% of the whole tracked tree, read by
`recolor_shapes.py` and by no deliverable. It was not in the original estimate.

Three planted reds before the tests: a deleted rule (the unclaimed file is
named), a rule claiming nothing, and a seed naming no script. Seven
synthetic-tree tests, including the two that matter for the computation — a
script reached only through a subprocess string counts as reachable, and an
unreachable one is development.

Nothing has moved. The split still needs the second repository, which is the
owner's to create; the sequence, the three assignments that read backwards, and
the measured footprint are in
`specs/2026-08-23-gate-consolidation-design.md`.

## 0.1.569 — 440 lines under one heading with no way in, and what the length guideline is actually asking for

**The skill-creator audit the owner asked for, done against the installed
validator rather than from memory.** `quick_validate.py` passes: every
frontmatter key is allowed, the name is legal, the description is 361 characters
against a 1024 limit, `compatibility` is 186 against 500. One PROSE guideline is
exceeded — 594 lines against a suggested 500 — and the specific complaint was
navigational rather than volumetric: **`## Workflow` held 440 of those 594 lines
under a single H2 with not one H3 inside it.** Seven numbered steps, one of them
177 lines long, and no way to reach any of them.

The seven steps are H3 headings now, so the file has a table of contents, an
anchor per step, and a seven-line pointer under `## Workflow` naming what each
one is for. **The numbers stay** — comments in `debug_log.py` and dozens of
release notes cite "SKILL.md step 1" and "step 3", so a step's number is its
name. Verified word-for-word: the token stream before and after is identical
apart from the seven added headings and the seven removed list markers.

**What was NOT done, and why.** The obvious way to reach 500 lines is to move
step 3's 177 lines of figure craft into `references/design-rules.md` and leave a
pointer. **That exact change has already been made and already regressed.** Step
3 records it: a reader compared a 3.4.0 deck against a 0.1.374 one and called
the newer one less professional; measured, 24 drawn figures against 1, 410
pieces of text inside SVGs against 8, and 14 of 14 figure titles stating a
conclusion against 1 of 5. Every rule the weaker deck broke was already in §4.
*The skill had not lost the craft; this step had stopped pointing at it.*

So the file is 628 lines rather than 602, and the guideline is still not met.
That is the honest outcome: the guideline's stated purpose is that an agent can
find what it needs, the audit's own diagnosis was a missing level of hierarchy,
and shortening the file by re-hiding the craft behind a pointer would trade a
measured regression for a number.

**Also recorded**: the Phase D footprint, measured rather than estimated.
`assets/shapes/source/` is 207 vendored originals, **2.77 MB — 22% of the whole
tracked repository — and a build input** that `recolor_shapes.py` reads and no
deliverable does. It is the largest single item on the wrong side of the
consumer boundary and it was not in the original estimate. The measured table is
in `specs/2026-08-23-gate-consolidation-design.md`, together with the correction
that matters more: a fresh clone is 8.28 MiB, so the case for splitting is that
a consumer reads none of this, never that the clone is large.

## 0.1.568 — the board shipped the operator's username, and the ledger looked in a directory nobody wrote to

Two defects that had to be fixed before the repository can be split in two, and
that are defects today regardless of whether it ever is. Both are the same
shape: **two halves that are each individually correct.**

**`report --record` wrote an absolute run directory onto the board.** The
conformance board's fourth line has read `Runs /Users/<name>/Documents/…` since
the results moved out of the repository, and the board is a TRACKED file — so
every recorded run carried the operator's username into git, and would have
carried it into a public repository. Six leaks across five tracked files when
this was counted, one of them written there by a generator.

The run id is not decoration: `skill_version()` opens it to recover the version
of a run whose directory name carries none, which is exactly the owner's
`r16-pinned`. So the fix is at both ends — `_portable()` collapses this
machine's home to `~` in anything RECORDED, and every read-back
`expanduser()`s. The path stays meaningful and resolves on the only machine
that could ever resolve it.

`check_local_paths` is the standing form. A single-letter name (`/Users/x`) is
excluded by the pattern rather than by a waiver, because a placeholder in an
example is not a person.

**`ledger.py` read `ROOT/evals/traces`; `trace.py` writes wherever
`LUMI_TRACES` says.** Set the variable and the writer goes one place while the
reader looks in another — and the ledger reports an EMPTY STORE rather than an
error, because an empty directory is a legal state. Nothing was wrong on either
side, which is why no guard caught it and why the fix ships with a test rather
than a guard.

One resolver now, `scripts/lib/trace_store.py`, imported by both. It is not
called `trace`: the canonical bootstrap APPENDS to `sys.path` so the standard
library always wins, and the standard library has a `trace` module — a reader
reaching for the obvious name would get stdlib's and fail in a way that has
nothing to do with traces. The test asserts that too, because it is the kind of
thing a later session will try.

Nine tests across the two, both directions, and the ledger split was
demonstrated live before it was fixed.

**The guard's own first red was itself**, and it is worth recording because it
is a shape rather than a slip. It reads `git ls-files`, so while its tests were
still untracked it saw nothing and preflight passed; the release committed them
and CI failed on the fixtures that plant the very string it looks for.
`SCRIPT_PATH_FROZEN` has excluded `tests/` for the identical reason since it was
written. **A guard that reads git behaves differently before and after `git
add`, and a local green taken before the commit is not the same claim.**

## 0.1.567 — a rule told an author a check would not fail them, and it would

**Asking the layout family the same question 0.1.566 asked the prose family.**
The 27 layout verdicts have no enumerated list in prose — `CLAUDE.md` already
names `deliverable_verdicts` as the authority, which is convention 13's
preferred outcome — so there was nothing to hold to a set. What prose does do is
name individual verdicts, and a name that no verdict carries is decidable.

Scanning for it found three things in one section of `references/design-rules.md`:

- **`figure_axis`** — an abbreviation of a family. The verdicts are
  `figure_axis_named`, `figure_axis_overlap` and `figure_axis_orientation`, and
  a reader looking up the abbreviation finds nothing.
- **`figure_axes`** — given a verdict-shaped name in backticks, when it is a
  printed observation line that no verdict carries and nothing keys on.
- **And the consequence of confusing those two**: the section said "a figure
  that scales numbers and names no axis is reported". `figure_axis_named` GATES
  exactly that case. The rule told an author the check would not fail them,
  three paragraphs below an owner ruling taken knowing that it does — and the
  accepted reference fails it on 10 of its 10 scaled figures. What is reported
  is a different measurement: a figure that draws no BASELINE for a scale, which
  is a property of the drawing rather than of a declared role.

The section is rewritten to the code: three verdicts, all gating, two of them
blind until a figure declares the classes, and the report line named as a report
line.

**The guard is narrow on purpose.** It reads a backticked identifier only when
its FIRST WORD is one a layout verdict already owns — the shape an abbreviation
or a half-remembered name takes. Reading every snake_case identifier would flag
functions, probe fields and CSS names, which is a guard that rewrites prose to
match itself; this repository has that failure on record. Waivers exist for the
deliberate illustration, as `SCRIPT_PATH_WAIVERS` does, and CHANGELOG entries
and specs are frozen history: an entry names the verdict that existed when it
was written.

Planted red on the real file before either fix, green after, seven
synthetic-tree tests including the frozen-history and waiver paths.

The design record for this phase is
`specs/2026-08-23-gate-consolidation-design.md`, written now rather than
backdated: it carries what the measurements DISPROVED as well as what they
confirmed — the planned 49-to-30 merge would have deleted assertions, because
the families that look redundant discriminate on the fixtures — so that a later
session reads the reason before re-proposing it. Phases D, E and F, and the four
prerequisites that must land before any file moves, are recorded there.

## 0.1.566 — the gate that fails a Chinese deck was missing from the table that teaches the gates

**The prose metrics had no prose guard, and both of their claim sites were wrong
the moment one was written.** `check_gating_claims` has held the DESIGN metrics
to their prose since 0.1.422; nothing held the prose metrics to theirs. Adding
that guard and running it once, against the real repository, found two defects:

- **The rubric's metric table had no `M4zh` row at all.** M4zh is the ban list
  for Chinese output, it gates, and it is the one prose gate that can fail a
  Chinese deliverable — absent from the document a reader learns the metrics
  from, in a package whose decks are largely Chinese. It appears correctly in
  the *generated* `eval-inventory.md`, which is how the hand-written table could
  disagree with the code and with the generated table simultaneously.
- **The sentence below it said "M2 and M6 do gate".** M2 has never carried
  `(gates)`. The commit that wrote the sentence did not touch M2's code, which
  is convention 14 — a claim about behaviour nobody read — in the file that
  teaches the rubric. Corrected to M6, with M2's actual reason stated: its
  predicate is decidable, but ninety per cent is a POLICY threshold rather than
  a red line, and a document at eighty-nine is not broken the way one carrying
  an unsourced range is.

**Two claim shapes, because the sites make two different claims.** A table of
metrics ENUMERATES, so its `**gates**` marks must equal the gate set. A sentence
arguing from an example NAMES A SUBSET, and what it may not do is call something
a gate that is not one. Holding the sentence to the full set would have forced
every mention of a metric into a six-item list — the guard being wrong about its
material, which is convention 15 and which this guard hit on its first draft.

**The truth is read by name, never by prefix.** `gating.metric_ids("M")` matches
`M\d+_` and therefore cannot see `M4zh_banned_hits`. A guard built on the prefix
reader would have confidently reported the table correct — the same blindness
that let M4zh gate in production while three registries had no idea it existed
(0.1.561). It reads `evals/gates.json` by name instead.

Deliberate red first, per convention 15: the guard was planted before either
prose fix and named both sites and both defects on its first run. Six
synthetic-tree tests, both directions — a table missing a gate, a table marking
a reported metric, a sentence misattributing, and a deleted sentence failing
rather than passing silently, because dropping the claim must not drop the
watch.

Also folded in: the Chinese-agenda end-to-end test added at 0.1.564 renders, so
it skips where Playwright is absent, which includes CI. A broken Playwright
still errors loudly rather than vanishing.

## 0.1.565 — the one block meets a page once instead of four times

**Where the owner's "every use gets more expensive" is actually felt.** Forty-six
lines came out of `check_deliverable` in the order the checkers happened to emit
them, so a document with five agenda defects reported them in four separate
places — a reader met the same page four times without being told it was the same
page. The block groups by concept now, using the `family` field the register
gained at 0.1.561:

    ── agenda
      GATE  design: D38_agenda_highlight FAIL
      GATE  design: D38_agenda_page_spans FAIL
      GATE  design: D35_agenda_exclusive FAIL
      GATE  design: D27_agenda_mirror FAIL
      GATE  layout: agenda_run_wrap FAIL

**Severity stays the outer axis**, deliberately: a gating failure has to be fixed
and a graded one is a reading, so a concept may legitimately head a group under
`GATE` and another under `note`. What must not happen — and what the test asserts
— is the same concept split into two groups at the same severity, which is
exactly the scattering this ends.

A finding whose metric is not a declared verdict — the privacy line, the trace
line, the Evals rows — heads its own group under its own kind rather than being
filed under a taxonomy built for gates.

This is the second half of what the classification was for. Naming 85 verdicts
in 30 families changed nothing on its own at 0.1.561; it is what makes the report
readable here, and what made 0.1.564's merge question decidable rather than a
matter of taste.

**And the release flow regenerated four artefacts while CI checked fourteen.**
Found by asking why the same two commands had been run by hand three times in one
afternoon. `release.py`'s `GENERATORS` was a hand-written list of four;
`.github/workflows/ci.yml` `--check`s **fourteen**. The other ten passed only
because their inputs rarely change — `build_page_contracts.py` was simply the
first one to start changing, once the rule register began moving, and it failed
three releases in a row. Nine more sat behind it.

It is derived from `ci.yml` now, through `preflight.ci_commands` — the parser
that already gives preflight its step list, so a generator added to CI tomorrow
is regenerated by the next release with nobody editing anything. Thirteen run;
the fourteenth is separated by what it IS rather than by name. `--check` means
two things in `scripts/build/`: most of these write a tracked artefact and ask
whether it is current, and dropping the flag makes it so, while
`embed_icons.py --check` asks whether the vendored LIBRARY is intact — 2007
icons, LICENSE present, 18 reserved bindings resolving — produces no tracked
artefact, and run bare wants icon names. The first derivation dropped the flag
from all fourteen and the release stopped on that one, which is the rule about
looking at the material rather than at the shape, applied to me. The same shape
as every other hand-written subset this package has fixed, in the one script
whose entire purpose is that local green and CI green are the same claim.

`check_rule_coverage.py --relocate` joins it. Line numbers in the rule register
are POINTERS, not assertions: editing a paragraph above a rule moves fifty of
them without changing one rule, and `--relocate` follows a quote only where that
quote appears exactly once — an ambiguous or vanished one stays a finding for a
person. Doing it by hand three times in an afternoon is what a tool is for.

**Deliberate red, planted first.** Restoring the flat print reddens the grouping
test. The test's own first version asserted global heading uniqueness and failed
correctly — severity-first grouping means a concept appears under two severities
on purpose, and the assertion had to be narrowed to the contract that actually
matters. Two new tests.

Design record: `specs/2026-08-22-rules-equal-conformance-design.md`.

## 0.1.564 — a Chinese agenda page was found by one checker and missed by the other

**Phase C opened by disproving its own plan, and that is the finding worth
recording first.** The plan said "merge the overlapping gate families: 49 gates
down to about 30, fewer names and not fewer assertions." Measured against the
fixtures, **the families do not overlap**. On `deck-broken`, `reserve_overspent`
fails while `content_hidden` passes — a title block can overspend its reserve
without being clipped. `band_escape` fails while `page_height` and
`content_spill` pass. On `deck-degenerate`, `collision` fails while
`figure_ink_collision` passes, because one reads page blocks and the other reads
inside a drawing. **Seven gates that look like one concept discriminate in
practice, and merging them would have deleted real assertions to reach a
number.** The count was the wrong target; the classification shipped at 0.1.561
was the deliverable, and it stands.

What *is* duplicated is machinery, and one piece of it was actively wrong.

**Two readers of "which page is the agenda", and only one could read Chinese.**
`check_design._is_agenda_page` matched the id case-insensitively OR any of
`agenda`, `议程`, `目录` in the eyebrow. `inspect_layout`'s probe matched the id
OR the English word alone — `/agenda/i`. So a Chinese deck whose agenda page is
named by its eyebrow rather than its id is found by the design checker and
missed by the layout one, which then reports `deck_structure` FAIL — *"this deck
has openers and no agenda"* — about a deck that has one. Reproduced, then fixed,
then reproduced again with the fix removed.

`markup.is_agenda_page` is the one rule now; `check_design` delegates to it and
the probe is handed `markup.AGENDA_WORDS` as JSON, the way
`ROLE_WEIGHT_SELECTORS` already is — so the vocabulary cannot be spelled twice
and the probe source stays ASCII.

**A correction to what I reported while finding this.** The first construction
was invalid: I removed the agenda page's id from a fixture whose agenda page has
no eyebrow at all, so *both* readers lost it and `deck_structure` failing was
correct. The divergence is narrower than that and more precise — it needs an
agenda page named in Chinese, which is the case that matters here, since the
decks this package is used for are largely Chinese.

**Deliberate red, planted first.** Restoring the English-only regex reddens two
tests, one of them the end-to-end case against a real rendered document. Four
new tests.

Design record: `specs/2026-08-22-rules-equal-conformance-design.md`.

## 0.1.563 — three tables knew which files carry a version stamp, and this file said two

**Found by asking where else the last two releases' defect shape lives.** Eight
defects surfaced in 0.1.561–0.1.562 the moment the gate set became declarable,
and none had been predicted; the useful question after that is not "fix them"
but "what else is carried implicitly". The audit is in `FAILURE_MODES.md` as
**FM-22**, and its result is reassuring rather than alarming: eleven
hand-maintained membership lists exist in `scripts/`, **eight are already named
by a test**, and this package's vocabularies — genres, storylines, geometries,
trace enums, banned phrases, class names, platform capabilities — are mostly
declared already. The gate set was the largest exception and is now declared.

One real instance came out of it. **Three tables answered "which files carry the
version stamp"**: `check_versions`' `TOKEN_STAMPS`, `check_version_citations`'
`ENTRY_STAMP`, and `check_evidence`'s `STAMPED_PREFIXES` — while `CLAUDE.md`
states there are two, and names them. Nothing compared the three, and they had
already diverged: `references/PRINCIPLES.md` is declared in `ENTRY_STAMP` and
was absent from the evidence gate's list.

**The cost was latent and exact.** `check_evidence.TOUCH_MAP` maps `references/`
to the `conformance-freshness` obligation — a full multi-agent conformance
round. Every release stamps `PRINCIPLES.md`. The evidence gate could not tell
that stamp from an edit, so **once the board went stale, every release would owe
a conformance round for having changed no rule at all.** It has not fired yet
only because the board was refreshed at 0.1.556.

`scripts/lib/stamps.py` is the one table now, and `stamped_paths()` is DERIVED
from the two that already existed and are already guarded — adding a token file
or an entry point still means editing exactly one of them, and the evidence gate
follows. The line budget stays in `check_evidence`, because how many changed
lines still count as a stamp is that gate's business rather than the table's.
Eleven paths are now recognised where ten were.

`ENTRY_STAMP`'s own comment records the same class of miss once already —
PRINCIPLES.md was undeclared there from 0.1.459 to 0.1.475. **A table forgotten
twice is a table that wants a single home.**

**The discipline this run is now held to**, written into FM-22 so the next
register has to clear it: a register earns its place only when it (a) is
compared to reality, so it cannot lie, and (b) REMOVES readers that kept their
own copy rather than adding one more. `evals/gates.json` took four readers to
one; `stamps.py` took three hand-written copies to none. A register that clears
neither is the accumulation it was meant to cure, in a new file.

**Deliberate red, planted first.** Deleting `PRINCIPLES.md` from the shared
table reddens the test named for that exact case; letting `check_evidence` type
its own list again reddens four. Teaching `check_repo` to read
`check_deliverable.py` last release had already made
`test_emergency_checker_closure` fail with *"the emergency run would execute the
PR's copy"* — `stamps.py` joins that closure for the same reason. Five new tests.

Design record: `specs/2026-08-22-rules-equal-conformance-design.md`.

## 0.1.562 — a gate written after the document stops failing it, plus three holes the register made visible

**The owner's directive, 2026-08-22: historical deliverables were never meant to
be upgraded to satisfy rules written after them.** She never asked for that; the
bug she reported was that a NEW deliverable must obey the new rules. The code
agreed with her more literally than I had: **no gate was scoped to a document's
version at all.** `fingerprint.version_in` has two call sites in the whole
repository; `run_conformance` stores `built_version` in the scoreboard and the
verdict is computed without ever reading it, and `check_deliverable` read no
version whatever. So a deck accepted at 0.1.449 was failed by a gate written at
0.1.560, and the failure read exactly like a defect.

Now: **a gate binds a document built at or after the release that introduced
it.** An older document reports the finding as `past` — neither a pass nor a
failure, not counted in the exit code, and the line says which gate arrived when
and which version the document declares, so an exemption cannot be mistaken for
a pass. Verified on one document under two stamps: at 0.1.500 it shows three
gating failures and four `past`; the same bytes at 0.1.562 show seven gating and
none. An older gate still binds an older document — `D19` and the privacy line
hold in both.

**The scoping must not become an escape.** A document carrying no
`built with lumi-style X.Y.Z` is held to everything, deliberately: the cheapest
way out of every gate would otherwise be to delete the one line that says which
rules you were written against. The planted red for that is its own test, and so
is the one for a NEW document — reversing the comparison so scoping applies
forwards reddens it.

**The calibration use is unchanged and is the reason to keep it.** Running new
gates against the owner's accepted documents is how a wrong check gets caught —
it caught two of mine in one session. What changes is that those reds are no
longer work: a red on an old document now says the check is wrong or the gate is
new, and never that the document owes an edit.

### The three holes the register made visible

Three holes the gate register made visible the moment it existed. None is
tidying; each fails a build or fails to.

**A gate that disappeared instead of saying `n/a`.** `D32_shape_use` is measured
for every document — `d32_shape_use(raw)` runs unconditionally — but its ROW sat
inside the `data-storyline` branch of `grade()`. A deliverable declaring no
storyline emitted no D32 row at all, and `gating_metrics` keys on *what the
report returned*, so the absence read as a metric that did not apply rather than
as a gate that had gone missing. Those two are indistinguishable from outside,
which is exactly why the row has to be present saying `n/a`. Hoisted out of the
branch. Its docstring also still said "Reported, never gating" — seventeen
releases after 0.1.543 made it gate.

**The fiftieth gate, in no registry anywhere.** `check_privacy` reports one
`verdict` per FILE rather than a verdicts map, so it fits no row table, and
`check_deliverable` promotes a non-`ok` one into the gating bucket in code. It
has been failing builds while `gating.py`, the rule register and
`run_conformance`'s `all-gating` set all had no idea it existed. It is
`privacy_terms` in `evals/gates.json` now, and the parity guard asserts it where
its gating actually lives — the promotion in `check_deliverable`'s own source,
which reddens if that line is renamed.

**Not applicable is not not measured.** Making D32 report `n/a` immediately
reddened this package's own passing fixture, and the reason is a distinction
nothing could express. `check_design` fails a run on **any** gating row reading
`n/a` — right for the case it was written for, D12 and D15 going silent because
no `<section class="page">` matched, a commercial gate mute on unreadable
markup. It is wrong for the six gates that reach `n/a` because the predicate has
nothing to look at: a Chinese ban list on an English deck, a caption rule on a
deck with no captions. Measured across the fixtures and twelve real
deliverables, those six are `D32_shape_use`, `M4zh_banned_hits`,
`M5_zh_punctuation`, `M12_visible_cjk`, `D37_caption_scope` and
`D39_bookend_mark`.

`na_means` carries it, and it belongs in the register rather than in a checker
for a reason worth stating: **a row cannot tell you whether its own silence is
honest.** The commercial gates are deliberately not given the field — their
`n/a` means the markup could not be read, and excusing it would re-open the hole
the blind rule exists for. Verified both ways: renaming `section.page` to
something the probe cannot see still reddens `D12`, `D15` and `D22` as blind and
exits 1; deleting one `na_means` reddens the passing fixture.

**Two things the repository's own machinery caught in this release.** Teaching
the parity guard to read `check_deliverable.py` made `check_repo` depend on a
file the emergency-merge path did not carry a trusted copy of —
`test_emergency_checker_closure` failed with *"the emergency run would execute
the PR's copy"*, which is the whole point of that closure. `check_deliverable.py`
and `gate_registry.py` join it. And adding a paragraph to `SKILL.md` moved
fourteen rule quotes down four lines; `--relocate` followed them, which is what
it is for.

**Deliberate red, planted first.** Removing D32's `na_means` reddens
`check_fixtures`; renaming the privacy promotion reddens the parity guard; the
blind case is exercised against a real mutated document rather than asserted.
Three new tests.

Design record: `specs/2026-08-22-rules-equal-conformance-design.md`.

## 0.1.561 — a gate stops being a substring in a display string, and three rows were in the wrong set

**The owner's read was right and the code agrees with her.** Forty-odd gates
were added one at a time with no abstraction, and the classification — *does
this fail a deliverable* — was carried by whether a human-facing display string
contained `(gates)`. Four readers parsed that string with three different
rules: `gating.py` by AST on the source, the two checkers at runtime for their
own exit codes, `check_deliverable` on the emitted JSON, and `check_fixtures`
inverted. A contract that lives in a substring will eventually be read four
ways, and it was.

**Three rows were in the wrong set, and one of them mattered.**

| row | was | is |
|---|---|---|
| `M4zh_banned_hits` | **returned by nobody** — the id pattern cannot match `M4zh_`, so the Chinese banned-phrase gate was absent from `run_conformance`'s `all-gating` require set entirely | a gate |
| `D37_caption_name_len` | counted as a gate by every consumer, while its own target says `reported` | reported |
| `D38_agenda_run_echo` | the same | reported |

The mechanism behind all three: `gating_metrics` matched the metric ID
**prefix**, so one row's classification was inherited by its whole family, and a
row whose id did not fit the pattern was invisible.

**`evals/gates.json` is the declaration.** 85 verdicts, each carrying what no
checker knows — **`family`**, the concept it belongs to, and **`since`**, the
release that introduced it. `checker` and `severity` are held to the checkers
themselves by a new `gate declarations` guard, so the register adds knowledge
and cannot contradict: the same discipline `check_rule_coverage` applies one
layer up. Every field was exported from the code and from git; none was typed
from memory.

**The classification, which is the thing that was missing.** 85 rows fall into
30 families. The largest are `fit` (7 — content that does not fit its box, split
across `collision`, `content_spill`, `page_height`, `content_hidden`,
`reserve_overspent`, `starved_column`, `band_escape`), `agenda` (6),
`figure-labelling` (6) and `footer` (5). Naming them changes nothing today and
is what makes the merges decidable rather than a matter of taste.

**`since`, and the trap in it.** A document carries `built with lumi-style
X.Y.Z`; a gate introduced after that version has nothing to say about it. Six
gates predate the version history this CHANGELOG keeps, and the scheme they were
numbered under — the one-point and three-point releases this file no longer
defines — **sorts above every 0.1.x version**. Written as numbers they would have
silenced themselves; they carry `always`. A document with
no stamp at all is held to everything, because an absent stamp must never become
an exemption: the cheapest way to escape every gate would otherwise be to delete
the one line saying which rules you were written against. The verdict a scoped-out
gate produces is `not held` — neither a pass nor a failure — and it lands in the
next release.

**One fix, three drifts behind it.** Making `M4zh` visible immediately reddened
the rule register: nothing had ever asked the Chinese gate for a rule, because
nothing could see it. Going to write one found `RC-441` and `RC-442` — which
quote the *Chinese* banned list (`值得注意的是`, `赋能`) — filed against `M4`, the
**English** metric. Repointing them reddened it again: the id extractor could not
recognise the `zh` suffix either, so `M4zh` was not a citable id. All three are
fixed, and the sequence is the argument for the register: a thing that cannot be
seen cannot be found wrong.

**The guard caught me on its first run.** Reading only `ast.Constant` made two
rows whose targets interpolate a threshold look `graded` when their literal text
says `(reported)`. The guard was right and my reader was wrong; it now joins a
JoinedStr's literal parts, and a synthetic-tree test pins that exact case.

**Deliberate red, planted first.** Five ways of lying in the register each go
red — a downgraded severity, a wrong checker, an unregistered gate, an empty
family, a `since` that is neither a version nor `always` — plus an empty
register, which must not pass by agreeing with nothing. Restoring the prefix
rule reddens the misclassification tests; making a missing stamp an exemption
reddens the scoping test. Fourteen new tests across three files.

Design record: `specs/2026-08-22-rules-equal-conformance-design.md`. This is
Phase A of the gate consolidation the owner asked for; B (version scoping) and C
(merging the families this release named) follow.

## 0.1.560 — the brand mark left both bookends and every gate passed it

**The owner opened a conformance deck and said the 3D globe was gone from the
cover and the closing. It was.** An agent had replaced the LUMIVATE field globe
on both bookends with a hundred-cell waffle of a collection figure — and
`check_design` reported zero failures, `inspect_layout --deliverable` reported
zero, the Evals reported zero. Forty-odd gates and not one of them looks at
whether the brand is still there.

**Why nothing saw it.** D19 is the gate the rules pointed at, and it asserts a
`data-globe` mark HAS its runtime. Its own docstring says why that is one-way:
*"A MARK obliges a RUNTIME, never the reverse"* — the mirrored assertion would
fail this package's own passing fixture, which carries the drawing as a still
frame on purpose. So a bookend with no globe at all was invisible by
construction, and two register entries (RC-089, RC-393) cited D19 as their gate
for something D19 refuses to assert. That is the same borrowing 0.1.557 found in
RC-417 and D12, in the rule that matters most.

**The rule, as the owner states it.** A replacement has always been permitted —
`storyline-templates.md` lets a document "render its own subject as geometry" —
but permission was read as the author's. It is not: *with no explicit
instruction the mark is the locked field globe*, and a document carrying
something else declares `<body data-brand-mark="what was asked for">`. The
declaration is the whole point: it separates a replacement somebody asked for
from a brand mark that went missing, which nothing could tell apart before.

**D40** gates each bookend against the locked asset's own geometry — read from
`assets/brand/lumivate/globe-field.svg` at run time, never a signature typed
into the checker, because the asset regenerates. **D39** gates the other half of
`brand.md`'s sentence, that the mark "appears twice … the cover and the
closing": whatever the mark is, both bookends carry it. Compared by which shape
kinds are present rather than by counts — the two frames of a live globe differ
because the runtime turns it, and a census demanding equality would fail a
correct document for rotating.

**Calibrated on the owner's folder before it shipped, and it changed the check
twice.** The first cut looked for `class="markcell"` as a literal and read her
own `class="markcell fig trade"` as a page with no mark — the fourth false
checker failure in this repository from matching a class without its token
boundaries, and calibration caught it where reading the code had not. The
second cut gated "not a chart" rather than "is the brand", which was the rule
read loosely; the owner corrected it.

**What reds, stated rather than discovered later.** Thirteen documents in the
delivery folder carry a deliberate subject globe and now need one attribute
each, because there has never been a way to say so: the SIFT and Agent intros,
the three training decks for one client, the older ops guide, and the two globe demos
whose closing carries no mark at all. Every Chengdu BP build, `adopting-lumi-style`,
the 0.1.448 ops guide, both fixtures and the scaffold pass untouched — as does
the Cursor deck from the same conformance round, which kept the brand on both
bookends while the Claude Code deck did not.

The design record is `specs/2026-08-22-rules-equal-conformance-design.md`: this
is its thesis meeting the one rule nobody had written a check for, found the way
the spec says defects are still being found — by the owner opening the file.

**Deliberate red, planted first.** The broken fixture loses its brand mark the
way the owner's deck did — a chart on the cover for D40, a different mark on the
closing for D39 — and both go red there and stay green on the passing fixture.
Removing the declaration check reds a document that declares its replacement.

## 0.1.559 — a prose row gates if and only if its target is zero (GAP-029 closed)

**The owner's decision, and it turns a list into a sentence.** GAP-029 recorded
that `check_design` exits non-zero only on rows whose target says `(gates)` while
`check_prose` exited non-zero on ANY failing row and marked one — so eight prose
metrics failed a build through the exit code and were classified as graded by
`gating.py`, which every other consumer reads. `check_deliverable` printed them
as `note` beside an exit that said otherwise.

The rule now: **a prose row gates if and only if its target is zero and it does
not say `(reported)`.** Nothing enumerates the gates, because an enumeration of
gates is a list that rots — this file shipped one that named M12 alone.

    gates      M4, M4zh, M5, M6, M9, M12      every =0 row
    graded     M2, M8, M10, M11               every share
    reported   M1, M13, M14, M15              =0 rows opted out on purpose

**Why zero is the line.** A target of zero is a rule the document either obeys
or breaks: a banned phrase is present or it is not, a range figure traces to a
source or it does not. A target that is a share — 90% of numbers sourced,
sentence-length variance at or above 0.50 — is a DIRECTION, and this repository
has shipped three regressions from an author optimizing toward a direction read
as a target. 0.1.336 drove sentence variance to zero doing exactly that, which
is why gating M8 would have mechanized the mistake rather than caught it.

**M9 was not in the recommendation and belongs by the rule.** Its target is
zero and the em-dash ban is a writing-rules red line of the same kind as the
banned-phrase list. A first scan showed it failing four of the owner's accepted
documents — and that was an artifact of the scan, not a finding: all four
declare `data-genre="internal"`, which the rule exempts, and `check_prose`
defaults to `sales` rather than reading the document's own declaration. Under
their own genre every one reads `n/a`. Calibrating on the accepted documents
caught this before it shipped, which is the whole reason that rule exists.

`check_prose` now counts two things apart: `failed` is what the run reports and
`gated` is what it fails on, so a run printing "4 metric failure(s)" no longer
sits beside `echo $?` printing 1 for reasons nobody declared. When nothing
gating failed it says so — *"none of them gating — read them, they are
directions rather than lines"*. An unmeasurable document still fails, because
"not measured" has never been a pass here.

Thirteen register entries were re-synced to the new gate set by reading it from
the checker rather than by hand, and `eval-rubric.md` marks the four new gates
in the column that was already there for M12.

**Deliberate red, planted first.** Restoring the old exit turns two tests red;
marking a share-targeted row `(gates)` turns the rule test red; removing the
marker from a zero-targeted row turns the same test red the other way. The
end-to-end test needed a real artifact and its first two candidates failed no
metric at all — they would have passed the assertion without ever exercising it,
so the document in the test is six three-item lists, built by running it.

## 0.1.558 — the effort levels had two definitions, and the run that passed everything left no row on the cost board

**Found by reading the driver log of the round that closed 0.1.557, and it is a
sweep this branch itself failed to finish.** 0.1.554 widened `--effort` from
`low|medium|high` to include `xhigh` and `max`, because Cursor spells its top
level `xhigh` inside its model id and the harness could not express it. That
edit did not reach `scripts/lib/trace_schema.py`, which owned the same tuple —
so a run could be **driven** at xhigh and could not be **recorded** at it.

The cost is measured rather than hypothetical. On 2026-08-22 Cursor was the only
agent to pass all three conformance tasks; `trace.py close --effort xhigh` was
rejected by argparse, which printed its usage and exited, and the driver logged
`trace … could not close`. The trace stayed open, so `ledger.py --board` — the
model × effort matrix those runs exist to fill — has no xhigh row from the run
that earned one. The board still shows `cursor-grok-4.6-high`, from an older
round.

**The fix is not a parity guard.** `run_conformance` now imports
`trace_schema.ENUMS["effort"]` instead of naming the levels itself, which is
what that file's own comment already says about the genre vocabulary — *"sharing
the tuple makes the drift impossible instead of checked"*. The test asserts the
property (the harness reads the schema's tuple, and no literal tuple has grown
back) rather than the values, because asserting the values would be a third
copy of them.

The levels are the CLIs' and not this repository's: `claude --effort` documents
low|medium|high|xhigh|max, and `hermes --reasoning` adds none, minimal and ultra
beyond those. The schema carries the five every driven CLI shares.

**And writing that down broke a test, which was right to break.**
`test_cli_contracts` decides which scripts owe a `--help` by asking whether the
file contains the string `argparse` — so the comment above, which explains that
*argparse* rejected the value, conscripted `scripts/lib/trace_schema.py` into the
list of operator CLIs and failed it for printing no help it was never meant to
print. The rule now keys on `^import argparse`, which is what it always meant:
a file that wires one up, not one that mentions the name. Same list of 43
scripts, minus the data module. Convention 15 again, this time in a test's own
discovery rule — a pattern keyed on a shape, meeting material it had not been
shown.

**Deliberate red, planted first.** Putting a literal tuple back in
`run_conformance` fails the new test; narrowing the schema's tuple removes
`xhigh` from `trace.py close --help` — the exact shape of the original defect.

## 0.1.557 — where the shared parts of a page are decided, and a horse race that can finally pin three models at once

**The owner asked the question this release answers: for the parts every page
kind shares — the water-ripple ground, the footer — where do the design, the
execution, the Inspector and the Evals live, so per-page-kind configuration
cannot interfere?** She remembered two overlaps. The register could not answer
at all, because nothing in it said which rules talk about the same thing.

`covers` names the property an entry decides; `overrides` names the entry it is
written against. One root per property — the entry nothing points away from is
where the value is decided, and every other entry says which one it is written
against, whether it narrows it, restates it, or contradicts it on purpose. The
check does not care which; it cares that a second statement of the same property
is deliberate rather than found later by somebody chasing a value that changed in
one file. `check_rule_coverage.py` prints the map on every run:

    footer.marker-colour   RC-100 (all) ← RC-101 (opener), RC-272 (opener), RC-417 (opener)
    ground.contrast-ceiling RC-060 (all) ← RC-329 (all)
    ground.tier            RC-058 (all) ← RC-365 (agenda), RC-418 (opener)
    title.max-lines        RC-293 (all) ← RC-163 (content), RC-422 (all)

Three of those four were genuine collisions. **The footer marker's colour is
stated once for every page and three times for openers, in two different files.**
**The ground's contrast ceiling is stated twice for every page**, in `brand.md`
and `design-rules.md`, and neither knew about the other. **The ground's tier is
stated in `brand.md` for all pages and again in `storyline-templates.md` for
openers.** `references/page-contracts.md` grows a Property column so a per-kind
sentence can no longer read as the whole story. 69 cover/agenda/opener/closing
rules still name no property and the run says so — a count that shrinks, never a
floor, because a coverage floor becomes a number to polish.

**A per-kind rule was borrowing an all-page gate's authority.** RC-417 — "keep
the footer's handling marker on an opener, inverted with the field" — cited D12
and claimed to gate. `d12_commercial_footer` scans the footer's TEXT for handling
words and a domain; it reads neither the marker, its icon, nor its colour. The
entry now carries no metric and says what nothing measures.

**And the ceiling gets a parity guard.** `1.40` is written in six places with
nothing joining them, so `--ground-ceiling` in `tokens/` is now the authority and
`inspect_layout.GROUND_CEILING` plus the three prose copies are held to it — the
`role weights` pattern. The first version read ratios off any line mentioning
"ground" and failed on `brand.md:193` ("5.21:1 on white, 3.23:1 on the dark
ground" — two contrast figures for the *lime*) while missing `design-rules.md`,
where the word "Ground" sits on the line above the number. One grep at the real
material, per convention 15; what ships is the narrower guard that does what it
says.

**GAP-029 — and the correction that comes with it.** `check_prose.py:963` said
"M2 gates" and M2's row carries no gating marker, so the comment was fixed. The
larger asymmetry behind it — `check_design` exits non-zero only on its marked
rows while `check_prose` exits non-zero on any failing row, where the marker is
emphasis rather than mechanism — **was already known and already tested**:
`test_the_two_checkers_express_gating_differently` asserts exactly that, and its
closing line names the hazard, "a count taken from one convention and applied to
the other is wrong, and one was". What is NOT recorded anywhere, and is the gap,
is that the consumers still do it: `gating.py` reads the design convention into
both, so `gating.metric_ids("M")` returns `{M12}`, `run_conformance`'s
`all-gating` block demands nothing of the other eight, and `check_deliverable`
prints them as `note` beside an exit code that fails the build on them. Measured
on the degenerate fixture: check_design exits 1 with 7 of 13 failures marked,
check_prose exits 1 with 0 of 6. **Which of them should gate is the owner's call
and not a refactor**, so the gap carries the measurement and a recommendation
rather than a quiet change — gating M8's length variance would mechanize the
0.1.336 regression, where a direction was read as a target and drove sentence
variance to zero.

The design record is `specs/2026-08-22-rules-equal-conformance-design.md`; this
closes its question about where a shared property is decided.

**And the concurrency shipped in 0.1.556 could not be used for the thing it was
built for.** A horse race between three CLIs has three different model ids —
`opus`, `cursor-grok-4.6`, an Anthropic id through Hermes — and `--model` was one
global flag, so the three agents still had to be driven in three invocations and
the workers had nothing to do. Both pins are repeatable now and take
`<agent>=<value>`; an id that resolves to no platform, or a level that is not a
level, stops the run rather than pinning nobody, which is the failure `--effort`
already produced once and reported as a level that was never applied.

**The board is fresh again, and the round it was refreshed from says something
about the performance question.** Three agents driven concurrently on T1 with
both axes pinned: **Cursor passed every gate in 28.5 minutes** on
`cursor-grok-4.6-xhigh`; **Claude Code was still working when the hard cap
arrived at 60.0 minutes** on `opus`/xhigh — 6702 stream events, never a stall,
verdict `over budget`, and what it left is a draft rather than a result. Hermes
wrote its deck to HOME again (GAP-022). Both finished decks clear every layout
and design gate, and **Cursor now names its axes** — nine of each class, against
five unnamed axes in the round before `figure_axis_named` gated.

Two of the three ran within 100 seconds of the old fixed 1800s ceiling (Cursor
1708.7s, Hermes 1614.0s). Under the code this branch replaced, the round that
produced the only passing deck would most likely have been SIGKILLed a minute
and a half before it finished.

**Deliberate red, planted first.** Removing the one-root rule turns two register
tests green-to-red; disabling the prose read in the ceiling guard turns the
drift test red; the guard's own first version was killed by a grep at
`brand.md`; ignoring the `<agent>=` form turns the pinning test red. Fifteen
new tests.

## 0.1.556 — the author's loop stops costing what the delivery check costs, and three agents stop queuing behind each other

**The owner's number is five minutes for a twelve-page deck, and the honest
answer is that four fifths of the wall clock is the model writing.** Measured on
one Claude Code run: 1191.5s total, of which 958.0s (80.7%) is output tokens
leaving the API at 62.8 tok/s. Deleting every check in this package would take
that run to 963s — still three times the target. **The lever that reaches five
minutes is making the agent write less**, which is an authoring-model change
(the scaffold emitting content-page structure so the agent fills facts instead
of hand-writing SVG), not a performance fix. This release takes the other 19.3%
seriously and says plainly that it is the other 19.3%.

**The loop was priced like the delivery check.** `inspect_layout` renders four
matrix points plus five off-shape windows — seventeen full page loads, 16.4s on
this package's own fixture — and an author fixing a collision on page 7 paid all
of it every round, then paid it AGAIN because `eval_corpus.py` shells out and
re-renders the same document (17.0s) to recompute numbers `check_deliverable`
had just measured. One round of the author's loop was 33.4 seconds of rendering
the same twelve pages twice.

Now: `inspect_layout --iterate` runs the declared stage only and skips the
off-shape sweep, and `check_deliverable --fast` passes it through. **Every gate
still runs** — on the broken fixture both modes return the identical fourteen
findings, and a test asserts that equality rather than trusting it. What is
given up is the coverage claim, so the flag says so on stderr after the verdict
block and the trace is not closed from a `--fast` run. And `eval_corpus.measure`
now accepts the two runs its caller already holds instead of making its own.

    check_deliverable                 16.4s
    + eval_corpus (separate command)  17.0s   →  33.4s per round
    check_deliverable --fast           3.6s   (the Evals now included)

**The Evals were not in the one block at all.** The command that exists so
nobody meets failures in installments left out the measure of whether the
document is the right KIND of document — prose-only share, figures per content
page, list density, visual share. They are in it now, GRADED and never gating,
which is what `eval_corpus` has always been.

**Three agents stopped queuing.** They share nothing — separate CLIs, separate
temporary directories, separate accounts — so the 74 minutes three of them took
back to back on 2026-08-21 was the shape of a `for` loop and not a requirement.
One worker per agent now; tasks WITHIN an agent stay sequential, because one CLI
driven twice at once shares an installation, a rate limit and sometimes a session
store, and a horse race whose entrants interfere with themselves measures the
interference. Each agent's lines print together under a lock — interleaved line
by line, three concurrent agents produce a transcript nobody can attribute — and
the model and effort line moved from the start of a task to its end, because a
line announcing an intention is not a line reporting what happened.

**And 113 seconds of one run were the harness refusing its own agent.** The
driven allowlist was `Bash(python3 *)`, which denies `cd <dir> && python3 …`,
`sed` and `grep`; thirteen denials, each followed by the agent rephrasing. A
permission the harness withholds is not a finding about the skill. Widened to
those commands, still never `bypassPermissions`.

`json.loads` of `evals/thresholds.json` existed in three places; `thresholds()`
is now the one loader, the shape `checker_report` and `gating` were both
extracted to end.

Design record: `specs/2026-08-22-rules-equal-conformance-design.md`.

**Deliberate red, planted first.** Starting each thread and joining it
immediately turns the concurrency test red at 6s for three 2s agents; making
`--iterate` skip its geometry turns the gate-equality test red; deleting the one
line that folds the Evals in turns the block test red. The first version of the
`--fast` notice printed to stdout and broke `--json`'s parse — caught by its own
test, which is convention 15 working as intended.

## 0.1.555 — a budget that renews while the agent is still working, and the verdict that finally describes itself

**The thirty-minute ceiling killed an agent that was still writing.** The 2026-08-21
round recorded `hermes/T1-deck` as a timeout at 1800.0s. The deck it left has an
mtime six seconds before the driver's record, and it still fails
`title_two_lines` today — the agent was inside the repair loop for the third
gate when the SIGKILL landed. Nothing about thirty minutes was a statement about
that run; it was a number somebody wrote, and the only thing it measured was
itself.

The replacement is not a bigger number. A run gets a **base budget** outright
(1800s, unchanged), and past it continues only while it keeps showing signs of
life, up to a **hard cap** (3600s) that renewal can never pass. Three properties
matter and each is tested: a run that finishes early is unaffected, a run still
working at the base budget gets more, and a run that has genuinely stopped is
collected without waiting out a clock nobody set for it.

**What counts as a sign of life, in the order of how much it tells you.** Claude
Code and Cursor are now driven with `--output-format stream-json` and their
partial-message flags, so every tool call and every token chunk is an event and
silence really is silence; the same stream ends in the identical result object
`json` returned, so the usage counts this board runs on are unaffected. A CLI
that streams nothing is watched through the artifact instead — the mtime of
anything matching the deliverable in the places `_misplaced` already searches,
which is how Hermes, whose deck lands in HOME whatever cwd it is given, is
visibly working from outside a process that reports nothing. A platform with
neither gets the base budget and the record says `signal: none` rather than
pretending a renewal rule did something.

The token deltas are counted as liveness and dropped from the stored transcript.
Nothing is lost: both CLIs also emit each completed message as its own event, so
the text a reader wants is there either way, and keeping the deltas would put
roughly one JSON line per output token into a file whose job is to be read by a
person. Both delta shapes were read off a real invocation rather than reasoned
about — Claude Code spells it `type: "stream_event"`, Cursor spells it
`subtype: "delta"` — which is convention 15 costing thirty seconds.

**SIGTERM before SIGKILL, and to the process group.** The old code killed the
parent outright, so the CLI never wrote its result object — a run collected at
its ceiling lost its usage counts, the model it had actually run, and whatever
it was about to say about why it was slow — and the browsers these agents start
were left orphaned. The group is signalled, given fifteen seconds to flush, then
killed. A synthetic grandchild proves it: with the parent alone signalled, the
grandchild outlives the collection and writes its marker.

**And the verdict now describes what happened.** `timeout` was decided first in
the verdict chain and described last in the detail chain, so a collected run
whose file had also landed somewhere odd was recorded `verdict: timeout` with a
detail explaining a misplaced artifact — which is exactly what Hermes's record
says, and reading it tells you neither thing. The detail follows the verdict's
own order now, and the one word has become two: `stall` for a run that showed no
sign of life after its base budget, `over budget` for one still moving when the
hard cap arrived. A reader asking "was it stuck or was it slow" gets the answer
from the verdict instead of reasoning from a duration. Both are still "not
earned" on the board; historical `timeout` records keep their word.

`--timeout` survives as an alias for `--budget`, and `--hard-cap` is new. The
design record is `specs/2026-08-22-rules-equal-conformance-design.md`; this is
the harness half of it — a conformance run that ends on a clock rather than on
the agent's own behaviour measures the clock.

**Deliberate red, planted first.** Deleting the renewal line turns the two
renewal tests red (`ended: stall` where `hard cap` is required); signalling the
parent instead of the group leaves the grandchild alive and turns the orphan
test red. Six new tests in `tests/test_conformance_driver.py`.

## 0.1.554 — three agenda rows the owner read side by side, an axis that has to be named, and an effort flag that pinned nothing

**She opened the three r15 agendas and said one was right.** The difference is
now four measurements rather than an impression, and her own accepted deck is
the standard answer at every one: three rows, three lime chips, run lines of 30
to 35 characters, no page numbers.

| | chip | run length | page span | echoes the claim |
|---|---|---|---|---|
| **accepted reference** | **3/3** | 30–35 | no | no |
| Claude Code | 2/2 | 77–83 | no | no |
| Cursor | **0/2** | **167–203, wrapping to two lines** | no | no |
| Hermes | **0/2** | 73–90 | **yes** | **yes** |

`D38` gates the chip and the page span; `agenda_run_wrap` gates the wrap,
counted in rendered lines the way a figure name is rather than by a character
budget nobody measured. Whether a run line merely restates its claim is
REPORTED — the test is word overlap and too coarse to fail a document on.

**A rule two sentences from its own counter-example.** The launch sequence read
"a quiet run line naming the pages", and one paragraph above it the same section
calls a row ending "pages 4 to 7" a table of contents in an agenda's clothes.
An agent took the nearer sentence literally and wrote "on pages 4 to 7" into
both its rows. It now reads "naming **what those pages cover**". The ambiguous
sentence won for four releases because nothing measured which reading shipped.

**This package's own agenda had no chips either** — the fixture marked none of
its three claims, so the model of a correct agenda was the flat one the rule
exists to prevent. Fixed here, and fixing it caught a second defect: the edit
shadowed the loop variable holding the opener silhouettes and blanked all three,
which `opener_subject_mark` reported immediately.

**A figure that scales numbers must name its axes (`figure_axis_named`, gates).**
Without the name a reader is handed a quantity and no dimension — and the two
placement gates added at 0.1.551 have nothing to grade, so a document could walk
past both by declining to say which text is an axis name. **The owner ruled it
gates knowing the cost**: every document built before the classes shipped fails
until rebuilt, the accepted reference on 10 of its 10 scaled figures and an
accepted intro deck on 4 of 4. GAP-027 records that the reference is not the
calibration anchor for THIS gate until the rebuild, and remains the anchor for
every other one.

**`--effort` pinned nothing, and said nothing.** An agent that spells effort
inside its model id needs both halves; given only `--effort`, the driver
composed nothing, pinned nothing, and recorded `(not pinned)` — honest in the
record, invisible on the console. **A whole comparison round was reported as
"Cursor at high effort" when Cursor had run on the server's default model at the
server's default level**, and the matrix row the flag exists to fill was dropped
without a word. It is a hard error now. The earlier ruling — "recording (not
pinned) is the honest outcome; inventing a model name to hang the level on is
not" — was right about the record and is superseded on the behaviour.

Two facts found by asking the CLI rather than the registry: **`cursor-grok-4.6-max`
does not exist** — Grok 4.6 tops out at `xhigh`, and `max` in that CLI belongs to
other families — and `--effort` accepted only `low|medium|high`, so the highest
level a comparison could ask for was `high` on every agent. Both fixed.

The design record is `specs/2026-08-22-rules-equal-conformance-design.md`; this
release is its "the checks her UAT named" phase continuing, one round further in.

**`release.py` no longer commits files the owner owns.** `git add -A` takes
everything in the tree, and 0.1.547 swept 413 lines of her in-progress
brand-packs spec into a release commit — untracked, hers, and nothing asked. The
content was unchanged, but a release should not decide when someone else's work
enters the history. `OWNER_OWNED` is now excluded from the commit and printed as
left alone; preflight still checks those paths like any other.

## 0.1.553 — D37 was reading the caption by its tag name, and then by too many of them

**Found by running the new gate against the round it was written for, not by
reading it.** Both corrections landed within minutes of each other and they
point in opposite directions, which is the useful part.

**It matched `<p>` and `<div>` only.** One conformance deck wrote
`<figcaption class="cap">` and its source line walked straight past a GATING
check — on a tag name, which is the identical shape of D33's `i-` id that
0.1.550 closed for the same reason. A class is the role; the element is the
author's choice, and a gate keyed on the element is a gate a markup preference
walks around.

**Widening it to any element then failed a deck that was CORRECT.** The other
agent had done exactly what §4 rule 17 asks — put the source INSIDE the drawing,
wrapped in `<g class="cap">`, with the caption below the figure holding only the
number and the name — and the widened pattern read that in-figure source as a
caption source. A rule being followed, reported as the rule being broken. It
was caught because the accepted reference and both fixtures were re-run before
the result was believed; the false positive lasted one command.

So: any HTML element carrying `.cap` is graded, and a `.cap` inside an `<svg>`
is not, because an in-figure source is the rule working. Both cases are pinned
by tests named after the decks that produced them.

## 0.1.552 — the data voice is embedded, and "not bold" turns out to have been "not there"

**Owner authorisation, with a licence condition she set: the embedded face must
be cleared for commercial use.** IBM Plex Mono is SIL OFL 1.1 — the same licence
as D-DIN, which this package has shipped since v1.2 — and the OFL permits
commercial use, embedding, bundling and redistribution, forbidding only the sale
of the font on its own. Both licences now sit in `assets/fonts/COPYING.txt`, as
the OFL requires.

**What was actually broken.** `--mono` named four faces and this package shipped
none of them. Every mono role in every deliverable — the cover and closing key
column, figure captions, the footer, the colophon, the part-opener label —
rendered in whatever mono the reader's machine happened to have, at whatever
that face called weight 700, which on a synthesising fallback is not a weight at
all. The owner read the key column as "not bold" at 0.1.442 and again at
0.1.551; it measured 700 both times, and the CSS written in answer the first
time was correct and could not help.

**Vendored from the official package and subset here.** `@ibm/plex@6.4.0`, then
`fontTools.subset` to the Latin ranges these roles use: **33.7 KB for the pair
against 92 KB complete**, 254 codepoints, 340 glyphs. The range was chosen by
measurement rather than habit — every character appearing in a mono role across
the accepted reference in both languages and a conformance deck falls inside it,
with zero misses — and the vendoring note says to widen it rather than accept a
fallback if one ever turns up. Subsetting is a Modified Version under OFL
clause 2 and is permitted; the Reserved Font Name is untouched and the files
still identify themselves as IBM Plex Mono.

**The cover key returns to the voice it was designed for.** 0.1.551 moved it to
D-DIN because that was the only embedded face; the mono is embedded now, so the
key is mono again and genuinely bold.

**`D36_font_family` reads the PRIMARY face, not the stack.** Its first version
reported "SF Mono, Menlo, Consolas" as unembedded on a document that embeds
everything it asks for — but a fallback naming faces you do not ship is what a
fallback IS. Only the first family in a stack must be embedded. A deck built
from current tokens now reads 0; the accepted reference reads 1 and will until
it is rebuilt, which is why the metric reports and does not gate. GAP-027 stays
open on that rebuild.

## 0.1.551 — the collision gate could not see inside a drawing, and five rules the owner marked had no check

**Nine screenshots, twelve markings, and the register named almost all of them
before the code was touched.** The pattern changed from the last round: this
time it was not that the rules had no checks, but that a check's REACH was
narrower than the rule it implements. `collision` gates, its rule says "nothing
may land on anything — text against text and text against every drawn element",
and four visible text-on-text overlaps inside figures passed it on three decks.

**`collision` now reads text inside a drawing.** Its text vocabulary named HTML
roles only, so an `<svg>` entered the scan as ONE opaque box and two labels
inside one figure were, to the probe, the same object overlapping itself. Six
real overlaps sat in one conformance deck — an axis unit printed over the word
"Illustrative", a risk label over its own category name. A separate absolute
floor, because a glyph run is not a paragraph: kerning puts a few pixels of two
labels together routinely, the noise measured 32x4 and 15x16, the defects 21x13
and up, and neither dimension separates them alone.

**The globe is exempt and GAP-026 says so.** The first thing the new scan found
was the brand globe: its HS-code trade labels overlap by construction at five or
more places on the cover and closing of every deck built with it, the accepted
reference included. Gating them would fail page 1 of the document every other
gate is calibrated against, for a defect the runtime and not the author
controls.

**A stroke drawn through a glyph run is the other half**, and the restriction to
STROKED marks is the whole discriminator: a data label sitting on its own filled
mark is what a labelled chart looks like, which is why `figure_ink_collision`
excludes text on purpose. A line drawn through a word is never a labelling
relationship.

**The agenda's lede went from permission to obligation.** The rule read "the
agenda MAY carry no lede" for four releases and two of three agents kept it —
because the scaffold emitted one, with a placeholder title reading *"What this
document argues, and where"*, the exact redundant sentence the rule asks authors
to delete. The prose changed at 0.1.521 and the generator never followed.
Measured: the accepted reference's rows sit 119px below the body top and 115px
above the footer; a deck that kept its lede, 267 and 99 — the same page, 2.7
times out of balance. **Centring needed no gate of its own**: `no-lede` drops the
row the title reserved and `.fill` already centres what it holds, so removing
the lede IS the centring.

**The figure caption's two halves were one sentence.** `.cap` is a single inline
flow — number, name, source — and the separator was whatever whitespace the
author happened to type. One deck typed none: `…off the green lineIllustrative
programme-board values`. §4's rule 8 and rule 17 had contradicted each other for
several releases about whether the source belongs there at all; **rule 17 wins
by owner ruling** and the source moves inside the drawing, where the accepted
reference already puts it — 21 captions, one `srcline` in the whole file.

**That ruling repaired a probe that was structurally blind.** `capWrapped` has
existed, reported, and never gated — and could not work: with the source in the
same inline flow the break landed inside the SOURCE, so the NAME never appeared
to wrap. It reported every name holding one line on decks where six of seven and
eight of ten captions rendered two. With the caption holding the name alone the
measurement is real, and `caption_name_wrap` gates it.

**`M2` could not see where the rules put a source.** `check_prose` strips every
`<svg>` before scanning, so a source line following rule 17 was invisible to the
one metric that asks whether a number carries its source. The two rules
contradicted each other in the only place it mattered: a document that put the
source where the rules say could not satisfy M2 without ALSO repeating it in
prose — which is what the reference happens to do and what nothing required.
The page window now carries what a figure prints inside itself; blocks do not,
because a chart's axis labels are not a run of prose. The reference's English
twin went from 95.7% to 100%.

**A repeating block's row name renders at title weight.** `.gr .gn` declared no
`font-weight` at all and computed to 400 — the same weight as its own note and
as the body around it, separated by one pixel of size and a step of colour. The
agenda's `.launch .gn`, the same class name one scope over, has always been 800.
`role_weight` gates the RENDERED weight, because a weight arrives through the
cascade and only the browser knows which rule won; a parity guard holds the
table to `tokens/` so it cannot quote a number the stylesheet does not ship.

**The cover's key column: the weight was never the problem.** Measured on the
owner's own deck, `.attrs .k` computes to 700 and aligns left — it has since
0.1.442, when the same complaint was made and answered with the same CSS.
`--mono` names "IBM Plex Mono", "SF Mono", Menlo and Consolas and **this package
embeds none of them**, so the key falls to whatever mono the reader's machine
has and whatever that face calls 700, often a synthesised bold. The key is a
label rather than tabular data, so it moves to the embedded `--din`; the other
fifteen mono uses are data and wait on GAP-027, which is a licensing and
package-weight decision. `D36_font_family` reports every declared-but-unembedded
family and does not gate, because it would fail every document this package has
ever made.

**Axis names needed a vocabulary before they could have a gate.** Geometry
cannot tell an axis name lying across the plot from a data label printed on its
own mark — on one figure four labels sat inside the plot square and all four
were correct, while the axis name beside them was the defect. The only role
signal was a class the deck invented. So `tokens/` ships `.axname-x` and
`.axname-y`, the y one paired with `rotate: 180deg` because bare
`writing-mode: vertical-rl` reads downward; `figure_axis_overlap` and
`figure_axis_orientation` gate a figure that declares them, and the scaffold now
tells an author to. A figure that scales numbers and names no axis is reported —
"the author did not say" is a different finding from "the author said and got it
wrong".

**One marking measured as not a defect, and GAP-028 records it.** Three arrow
rules the owner read as overlapping the text beneath them have ZERO overlap at a
0.5px threshold: they sit in the LEADING between two lines. The measurement that
would catch them is a clearance floor, and the accepted reference carries a
legitimate 194x17px rule sitting exactly on the line it underlines — any floor
that catches the arrows fails that. It waits on a second accepted document, as
GAP-024 and GAP-025 do.

The design record this line of work runs under is
`specs/2026-08-22-rules-equal-conformance-design.md`. Its thesis held again: the
owner's eye lands where nothing measures, and the register can now name those
places before she has to.

**No per-agent rule prompts.** The owner asked whether each agent should get its
own tuned rules. Three decks broke the same rules — 22 of 24 captions over a
stated ceiling, three agenda ledes, three unweighted ladders — so the defects
are not agent-shaped. `adapters/platforms.json` carries 18 fields per platform
and not one of them holds a rule, by design: "adding a platform is a registry
record and a note, never a restatement of a rule". Forking the rules per agent
would build the largest drift surface this repository has ever had, and would
turn conformance from "does the skill hold across agents" into "did we tune this
one".

## 0.1.550 — four reviews ran the gates 0.1.549 added, and nine of them had a way through

**Every finding here came from RUNNING the new checks, not from reading them.**
Four review passes over the 0.1.549 diff — general, comments, tests, silent
failures — converged on the same conclusion from different angles, and none of
the nine defects below is a logic slip. Each is an assumption about the material:
that a symbol id spells itself `i-`, that an attribute is double-quoted, that a
class list has one token, that a deck ends where its closing page is, that a
name belongs to one icon set. **Convention 15 says reading the code cannot find
these, because reading uses the model that produced them.** This release is that
sentence collecting on itself.

**The two shipped fixtures declared the wrong page count.** Adding a third part
opener changed the bookend arithmetic and the new expression dropped the cover,
so both decks numbered their pages one short and the closing page repeated the
previous page's number. It passed everything: `build_fixtures --check` compares
the generator to its own artifact and they agreed, and D6 asks only whether a
total is *present*. The package's model of a correct document was teaching a
footer defect.

**The pacing ceiling was calibrated on an appendix.** 0.1.549 set it at six
because "the accepted reference runs 6" — and that six was **the reference's six
pages after its closing page**, counted as one unbroken stretch of argument by a
run computation that did not know a deck ends. Its real longest run between
seams is five, and this package's fixture also runs five. A run now ends at the
closing page, and a declared apparatus page is a seam.

Six stays, for a reason that is now about the rule rather than about the
artifact: **a ceiling equal to the target is a target.** This repository has
shipped three regressions from exactly that confusion. One page of headroom is
what keeps five a target.

**D35 could be walked past four ways, and every one is what ordinary generated
markup looks like**: an unclassed `<div>` wrapper, a class list whose first
token is `foot`, a class list carrying an allowed token beside a forbidden one,
and anything nested three levels down. It reads the whole subtree now, and
descends through unclassed wrappers rather than skipping them. Its finder was
narrow enough that `id="Agenda"` — one capital — and a Chinese deck's `议程`
both scored as "no agenda page", which is a pass. D27 had its own copy of that
finder and they disagreed; there is one finder now, because two gates about one
page may not disagree about whether the page exists.

**D33 was bypassed by a naming choice.** It matched `id="i-[a-z0-9-]+"` and did
not merely fail to report anything else — it did not COUNT it, so a deck whose
every icon was `#handdrawn` returned `ok`. It keys on use as an icon now (an
`svg.ic` pointing at a symbol), which is the vocabulary the rule and the tokens
both use, and which leaves alone the library shape and the trademark mark the
accepted reference legitimately defines.

**And D33 called 32 of the 36 shipped silhouettes forgeries.** The two icon sets
collide on 32 names and the lookup kept whichever it read first, always
lucide's — so a document drawing a genuine `koboyo/shield.svg` was reported as
the set's name over somebody else's drawing. A name may now carry a drawing from
either set. Separately, `_geometry` read only double-quoted attributes, so
`d='M20 6'` produced an empty geometry: a shipped icon written that way failed,
and two *different* single-quoted icons compared equal. The gate was failing in
both directions at once.

**The opener-mark signature read five of the seven shapes the filled-silhouette
counter accepts**, so a mark drawn from `<circle>`/`<rect>` produced an empty
signature and three openers sharing one were not a finding — and it truncated
each attribute at 100 characters, so two genuinely different marks diverging
later collided into a FALSE red. It reads every shape and the whole value now,
plus `xlink:href`.

**A declared pacing exemption read as `ok`.** `run_conformance` records which of
`ok` and `n/a` a gate returned, so one `<body data-parts="none">` was the
cheapest way to switch the gate off leaving no trace in the score — on a release
whose central finding is that an agent iterates to the edge of what it is shown.
It is `n/a` with the reason attached.

**`figure_axes` could not fire on this package's own fixture.** Its bar of three
numeric labels excluded the house figure shape, which carries two, so
`figScaled` was zero on all ten figures and the report printed nothing at all —
not "0 of 0". Its value pattern also required digits first and Latin units, so
`US$4.2m`, `41％` and `4.2亿` all read as "not a number", silently exempting
every Chinese-language figure.

**The CJK exemption added at 0.1.549 was wider than its own comment claimed**,
and a reviewer demonstrated two ways through: it matched any JSON path ending
`.quote` — including a nested `rules[0].notes.quote`, a key the register's own
reader ignores — and it placed no restriction on which file a rule could be
quoted *from*, so a sentence of Chinese lifted out of an HTML fixture passed as
"rule data". The path is matched whole now, and a rule may only cite a rule
file.

**Two counts in 0.1.549's entry were wrong** and are corrected here rather than
edited out of the record: it said the seam rate had been "reported for four
releases" when it was reported from 0.1.376 to 0.1.548 — 173 of them — and it
described a conformance deck as having "twelve content pages and no opener"
when the artifact is twelve PAGES with ten content pages. Both are the failure
convention 13 warns about; a version citation cannot rot the way a count can.

The design record for this line of work is
`specs/2026-08-22-rules-equal-conformance-design.md`; nothing in it changed, but
its "how each new check is validated" section now has nine more entries behind
it than the five it was written from.

**Two bugs found by using the tool rather than reviewing it.** `--run <name>`
was taken as a path relative to the working directory, so a conformance round
launched from the checkout wrote its whole record — transcripts, driver files,
an agent's deck — into the repository, which is the one place the owner
directive says results may not go. And `--agent` took a single value, so three
flags kept the last and a round announced as three agents drove one.

**What the fixtures owed.** D35's only red came from its "no `.body`" guard
clause, so the stray scan — the actual metric — had never gone red on any
fixture; the degenerate deck's agenda now carries a real body with a stat band
in it. The altered-icon plant reused `i-shield`, an id the sprite already
defines, so the document carried a duplicate DOM id and every `<use>` resolved
to the correct symbol — the defect existed in the markup and in no rendering of
it. And one plant was still keyed on the page number while `page()`'s docstring
said none were.

## 0.1.549 — five rules the owner named now have checks, and the ceiling comes from the accepted deck rather than the prose

**Phase 3 of `specs/2026-08-22-rules-equal-conformance-design.md`.** The register
built at 0.1.548 was the point of doing this in order: for each thing the owner
found by eye, it could say whether a rule already existed, and three of the five
did — unchecked, in a file `SKILL.md` never told anyone to open.

**Icons have a provenance now (`D33`, gates).** design-rules §6 has always said
never to draw one ad hoc, and nothing read it. Every `<symbol id="i-*">` must
carry the geometry of a file in `assets/icons/lucide/` or
`assets/icons/koboyo/`. Two findings, kept apart because they mean different
things: a name in neither set was invented, and a shipped NAME over a different
drawing is the set's label on somebody else's path — the harder of the two to
catch by eye, so the broken fixture plants one of each. Measured on the three
documents on record before the check was written: fifteen symbols each, zero
unmatched.

**Icon reuse is counted and NOT gated (`D34`).** The rule says an icon means one
thing per document; the accepted reference reuses three of its twelve eyebrow
icons across two and three pages. Whether that is one meaning restated or two
meanings collided is a judgement about the pages, so it reports. It still
answers the owner's actual complaint, which was blunter than the rule: seven of
eight content pages carrying one icon shows up here as a reuse count, loudly.

**A part opener's silhouette may not be another part's (`opener_subject_mark`).**
The mark is the part's subject, so two parts sharing one assert the two parts
are the same thing. Compared on the geometry, because the marks are inlined SVG
with no name to differ in. **It fired on this package's own passing fixture** —
two openers, one silhouette, sitting there since the mark was added at 0.1.546 —
which is the deliberate red this gate shipped with, on a real artifact rather
than a planted one.

**The agenda page carries the agenda and nothing else (`D35`, gates).** Owner
ruling from one conformance round: one deck put a stat band on its agenda, one
invented an `.agenda-grid` class with a private `<style>` to lay it out, the
third was clean. The body holds the launch sequence in a `.fill` and optionally
the `.lede` above it.

**The seam rate gates, and the number is six (`opener_pacing`).** This was
reported for four releases on the argument that a quota would force openers
where the argument has no seam. What settled it was a conformance deck with
twelve content pages and no opener at all: the report said so and nothing
failed. **Six, not the five the prose states** — five as a ceiling fails the
deck the owner accepted, which runs 6, and this package's own fixture, which ran
7. Five stays the writing target precisely so six is not one.

**The "unless the author says otherwise" half is now declared, not inferred.**
`<body data-parts="none">` says a deck is deliberately one undivided sequence,
on the `data-role="apparatus"` precedent. Two decks the owner accepted this
month are page-for-page conversions running seven and nine pages without a seam;
no checker can tell those apart from a deck that forgot its openers, so the
author says which, and the exemption is auditable and printed rather than
guessed at.

**Figure axes are reported, and the accepted document is why (`figure_axes`).** A
figure that puts numbers on a scale should draw the baseline and name the unit —
a baseline is the datum, which is not the gridline §4 rule 3 bans. Measured: the
reference draws none on two of its nine scaled figures, an accepted intro deck
on one of four, three other documents carry no scaled figure at all. A rule the
reference breaks is either a rule it should have followed or a bar nobody has
earned; one document cannot tell those apart.

**The fixtures were rebuilt into three parts, and doing it lost three planted
defects.** Re-splitting moved page 12 from a content page to an opener, and D4's
literal colour and D24/D25's untermed image went with it — all three came back
`ok`, and only `check_fixtures`' refusal to grade a metric no fixture fails said
so. **It had happened before**: the same D4 plant sat on page 5 until 0.1.369
turned that page into a `stack` layout with no `.gd` at all. Twice is a pattern,
so every plant now keys on the page's ordinal among the CONTENT pages rather
than on its position in the deck. That also fixed a quieter bug — the two decks
number differently, so `i == 8` had meant the fifth content page in one and the
sixth in the other.

**0.1.548 was committed red, and FM-21 records why.** Its new register file was
still untracked when preflight ran, and `check_english_only` enumerates its
inputs with `git ls-files` — so the file did not exist to the guard, preflight
passed 30/30, and the same check went red once the commit made it visible. The
verdict was right both times; only its input changed. The fix is not a wider
guard but a narrower exemption: a `quote` in that register is a verbatim
substring of the line it cites and `check_rule_coverage.py` fails the build if
it stops being one, so CJK there is rule data by construction. Every other field
is still scanned, and a test asserts the difference.

**Two counts deleted rather than corrected.** `CLAUDE.md` opened "Eleven of its
metrics gate" and closed "All eleven are" — two words the parity guard does not
read, so adding a gate could leave them wrong while the check stayed green. The
sentence now names its authority (convention 13) and the guard's anchors moved
with it.

## 0.1.548 — the rules and the checks are now held against each other, and the count is worse than the estimate

**0.1.547 closed the amplifiers. This is the measurement they were amplifying.**

`evals/rule-coverage.json` is one entry per checkable rule about a deliverable:
where the rule is written, which metric measures it, whether that metric gates,
and — where nothing does — why not. Extracted from `references/` and `SKILL.md`
by five parallel sweeps, one per file, with **every quotation pulled out of the
file mechanically rather than retyped**: an agent that paraphrases a rule while
claiming to quote it produces a register that passes its own quote check and
describes sentences nobody wrote. All 471 anchors resolved byte-for-byte at
their cited lines on the first pass.

**471 rules · 132 measured · 58 gated · 339 with no automated check.** The
working estimate carried into this work was 175 and 97. It was low by a factor
of nearly three, which is the more useful finding: nobody had counted, and the
number people carry when nobody has counted is the number that feels bearable.

**`references/page-contracts.md` is the owner's request, generated.** Her
instruction was to gather the deck's cover, closing and agenda rules into one
place so they stop being forgotten, and to gather the content-page rules
separately. The need is real — "what a cover owes" was spread across three
files, and five conformance rounds each broke a different one of those rules.
But a hand-written summary of 471 rules would be the largest prose copy this
package has ever created, and prose copies drifting is its worst measured defect
class. So the page is generated from the register, `--check` in CI, on the
`eval-inventory.md` precedent, and it carries pointers rather than rule text:
the rule still lives in exactly one place. Six sections at her direction, with
the content pages given one of their own. **The cover section reads 20 rules,
18 of them unchecked** — which is the answer to why every round broke a
different one.

**The reverse direction is the half that earned its keep.**
`check_rule_coverage.py` asks four things of the register — the quote is still
at its line, the metric exists, it gates as claimed — and one thing of the
CHECKERS: **every gate is asked for by some rule.** That fourth question found
nine gates with no rule behind them on its first run. Four were mismapped and
now trace correctly. Five do not: `bookend_title_length` and `band_escape` were
calibrated from an accepted document and a rendering defect rather than from a
sentence; `figure_ink_collision` extends a rule about text onto ink that the
prose does not extend; and `footer_wrap` and `footer_baseline` enforce a
requirement stated only inside a provenance note about how the defect was
found. They are recorded in `orphan_gates` with the reason, on the KNOWN_GAPS
pattern — a gate this package invented is a decision, not an accident, and an
UNDECLARED one now fails CI.

Phase 3 of `specs/2026-08-22-rules-equal-conformance-design.md` — the checks
her UAT named, now that the register can say which of them have a rule behind
them — is next.

**Coverage is reported and never gated.** A coverage floor becomes a number to
polish, which is 0.1.339's withdrawn 82% fill floor wearing different clothes.
What gates is the register not lying.

**`.launch`, `datum`, and the reader that knew one spelling.** `gating.py` now
reads the layout gate set from the function that defines it — and its first
version read only `add(...)` calls, missing `datum` and `role_split`, which are
assigned into the dict directly. It reported 19 gates where there are 20. The
same class of mistake convention 15 is about, and found the same way: by
looking at the material rather than at the code.

## 0.1.547 — the scaffold stops teaching the violations, and a page that is absent stops passing

**Five rounds of multi-agent conformance ran the same shape: the deliverable
passed every gate, the owner opened it, and her eye landed on a rule no gate
reads.** The finding behind this release is that the agents were not the
variable. Same model, same effort, five rounds — the only thing that changed was
how much of the standard the contract exposed, and the output went from 66KB
failing six gates to 579KB passing everything. **An agent iterates to the edge
of what it is shown**, so the boundary that matters is the boundary of the
shown standard, not of the model.

Measured against `references/` on 2026-08-22: **175 checkable rules about a
deliverable's structure and appearance, 78 of them measured by some metric, 40
of them gated, and 97 with no automated check of any kind.** The check set grew
from what was easy to measure and has never been audited against the rule set.
Three agents making the same class of mistake is not three agents copying each
other; it is three agents reading one standard with the same holes in it.

This release closes the amplifiers. The rule-to-check register that makes the
remaining 97 visible is the next one. The decision record, including the two
phases still to come, is `specs/2026-08-22-rules-equal-conformance-design.md`.

**The scaffold was teaching the violations.** `new_deck.py` gave every content
page the same `#i-radar` eyebrow — one agent inherited it onto seven of eight
pages, leaving twelve of the fifteen shipped symbols unused — and its part
openers carried no subject mark at all, so a deck built straight from the
scaffold failed 0.1.546's `opener_subject_mark` on every opener it had. Both
are fixed at the source: the eyebrow rotates through thirteen symbols and says
in an HTML comment that it is a placeholder, and each opener now carries a
filled silhouette read out of `assets/icons/koboyo/` — the set of thirty-six
vendored for exactly this and named in no rule file, no entry point and no
script until now. A scaffold is the most-read documentation this package has,
and it was arguing against the rules.

**A page that is absent was scoring better than a page done badly.** D27 passes
a deck with no agenda, on the correct reasoning that it owes no mirror.
`opener_subject_mark` reads `n/a` on a deck with no openers. `run_conformance`
counts `n/a` as met. Compose the three and a deck passed the structural gates
by having none of the structure, which is how one conformance deck passed.
`deck_structure` gates on it now: a cover and a closing unconditionally, and an
agenda once the deck is divided into parts, because a part opener nothing
routes is a part nothing routes.

**What set that scope was the folder, not the rules.** `references/` says the
agenda belongs to "every deck scenario", and a gate written from that sentence
fails two decks the owner accepted this month — nine and eleven pages,
page-for-page conversions of her own originals, no openers and no agenda
between them. The rule means the storyline roster; a conversion is not one of
its scenarios. Reading the material before writing the pattern is convention 15,
and here it was the difference between a gate and a false accusation.

**The package's own good sample failed the new gate**, carrying two part
openers and no agenda. It has one now, its rows quoting the openers from a
single tuple so the fixture cannot violate the D27 it exists to exercise, and
the broken fixture keeps no agenda as the planted red.

**`.launch` was counted as prose.** The agenda's launch sequence — numbered dark
chips, the claim at title weight — was adopted at 0.1.519 *because* an owner
review read a plain text agenda as too quiet, and D16 has been reporting every
agenda in this package as a content page carrying nothing visual ever since,
the accepted reference deck included. It is a visual block in both carriers now;
the `probe vocabulary` guard caught the half-done version of this change in the
same run that made it.

## 0.1.546 — a part opener without its silhouette is a finding, and figure repetition is measured rather than guessed at

**The owner named three things her eye found in decks that had passed every
gate.** Two are answered here and the third is refused on purpose.

**A part opener must carry its subject mark.** design-rules §3 permits exactly
one — a filled silhouette carrying no text of its own, reversed out of the lime
field, restating the part's claim in another modality (0.1.521, owner
directive) — and it is the only element allowed there besides the label, the
claim and the run line. The accepted reference deck carries one on every opener.
**Three conformance decks driven to pass every other gate carried none, on five
openers between them**, and no fixture in this package drew one either. The rule
had been prose for four releases and nothing read it.

`opener_subject_mark` gates. Its floor is a share of the page, not a pixel
count, because a deck is a fixed canvas that SCALES: the reference's smallest
mark is 193px wide at 16x9, 272 at laptop, 844 at wide. A 120px floor passed it
at three viewports and failed it at the fourth — **the third time this file has
made the one-viewport mistake in two days**, after the band floor and the title
line count.

**Figure repetition is measured and NOT gated, and the reference is why.**
The owner is right that the decks repeat: the one she faulted draws a single
line-and-bar skeleton on four of its seven figure pages. But the reference
repeats too — one skeleton across five pages of twenty-one — so a ceiling of
three fails the document she has accepted and a ceiling of six passes the deck
she rejected. What separates them is a share, not a count, and one accepted
document cannot set it. **GAP-025**, alongside GAP-024's layout variety, closes
when a second accepted document exists.

A first reading of it counted DRAWINGS and made the reference fail its own p4,
where four small charts of one kind sit side by side as a single composition.
Counting pages was the correction; the disagreement that survived it is real.

**The content-page kicker icons the owner could not see are there.** Every
content page in every deck measured carries a semantic eyebrow icon, and the
deck she faulted carries eight distinct ones across eight pages where the
reference reuses three of its twelve. Reported here because a finding that
turns out to be absent is worth as much as one that lands, and because what she
saw may still be real at a size these numbers cannot see: §3 sets an inline
icon at roughly 1.4x its text, which beside a 58px claim is easy to miss.

**Where the fixture work went wrong, which is the part worth keeping.** Adding a
mark to the passing fixture took three attempts: `width:15%` inside the copy
column rendered 14px wide, viewport units sized it correctly and pushed it past
the page box until `content_spill` caught it, and percentages of the frame were
too small again. **`tokens/` had shipped `.openmark` all along** — a second grid
column, `height: 46svh`, `fill: currentColor` — and the reference deck uses
exactly that. Three rounds were spent re-deriving a rendering the package
already owned, which is what the class vocabulary exists to prevent.

## 0.1.545 — the misplaced-artifact sweep was attributing one agent's deck to another, and 0.1.544's evidence came from the wrong file

**The owner opened the deck this harness had filed as Hermes's and said its
cover was worse than ever. It was not Hermes's deck.** Three agents were driven
in parallel, all of them able to write to HOME and into the checkout, and
`_misplaced` sorted its candidates by mtime and took the newest. Hermes's record
therefore cited a deck at the repository ROOT — 130 characters of cover claim
over ten lines — while Hermes's transcript names `~/deck.en.html`
and nothing else. That impostor was copied into Hermes's run record, scored as
Hermes's, reported to the owner as Hermes's, and reviewed by her as Hermes's.

**Hermes's real deliverable passes.** Cover four lines, twenty-four characters,
`47.6% now, 51.2% planned`; closing three lines; **29 of 29 gates, three
checkers at exit 0, no Evals miss.** All three agents pass the full standard at
high effort with the check loop. The two failures previously reported against
Hermes — `figure_clipped` and seven content pages — belong to a file it did not
write.

**The fix is that the agent's own word outranks the clock.** A path the
transcript names is evidence of authorship; a path that merely appeared inside
the run's time window is a coincidence with a timestamp, which is all this ever
had. Named candidates sort first; unnamed ones stay in the record — a reviewer
may want them — and never become the artifact.

**0.1.544's evidence is corrected here, and its gate is not.** That release set
the bookend ceiling at five lines from three measurements, and one of them —
the ten-line cover attributed to Claude Code's round-three deck — was read off
the same impostor file. Re-measured against what each agent actually wrote:

| | cover | closing |
|---|---|---|
| the accepted reference | 5 | 5 |
| Cursor | 3 | 3 |
| Hermes | 4 | 3 |
| Claude Code | 10 | 8 |

The Claude Code figure survives — that deck is genuinely its own work and
genuinely carries a paragraph in its cover slot — so five lines remains the
ceiling and the reference remains its source. What changes is which agent the
worst number belongs to, and that the ledger said the wrong one.

**What this cost, stated plainly.** An instrument that guesses attribution does
not merely record the wrong name: it hands a reviewer another author's work and
invites a judgement about the wrong agent. The owner made exactly that judgement
and was right about the artifact in front of her.

## 0.1.544 — the cover claim gets the ceiling the two-line rule could not give it

**The owner opened the deck that had just passed and said the cover and closing
carried the same defect.** They did, and 0.1.543 had exempted them from the
two-line gate on evidence that was wrong. The exemption's reasoning was sound —
two lines is unreachable for a claim set at 58px, and the accepted reference
deck exceeds it — but the MEASUREMENT behind it was the height-over-line-height
reading this same release replaced everywhere else. It put the reference's cover
at three lines. Counted from the rendered text, it is five.

**So the bookends get their own ceiling, and it is not a number chosen here.**
It is the accepted document's own: **five lines**, because a document a reader
has approved is by definition acceptable and one worse than it has never been
approved by anyone. Measured at four viewports, stable at every one — a deck is
a fixed canvas that scales rather than reflows:

| | cover | closing |
|---|---|---|
| the accepted reference | 5 | 5 |
| Cursor, which passed | 3 | 3 |
| the deck the owner called a bug | **10** | **8** |

Ten lines is 130 characters of cover claim at display scale. That is not a
headline that ran long; it is a paragraph in a headline's slot, and no line
count derived from a rule about content headlines was ever going to catch it.

**What this release is really recording** is that a gate written from a rule and
a gate written from a measurement are different objects. `title_two_lines` came
from the sentence in `design-rules`, and the sentence is about the page headline
— it says so, in the paragraph about topic-plus-assertive-subtitle. Reading it
as though it governed every heading in the document produced an exemption for
the two pages where the reader looks first. The reference deck was the authority
all along; it just had to be measured correctly to say so.

## 0.1.543 — the conformance bar becomes the package's own bar, and three checks the owner's eye found before any instrument did

**A hand-written list of six was standing in for the standard.** T1's `require`
named D12, D14, D15, M4, `collision` and `content_hidden`. Ten design metrics
gated and fifteen layout verdicts did, and the Evals thresholds were applied by
nothing at all — so a deck could fail D19, D1, D3, D4 and eleven layout checks
and be recorded `pass`. One was: the owner opened a conformance deck on
2026-08-21, found 51KB with zero content pages sitting green on the board, and
said the deliverables did not meet the standard. She was right, and the board
had said otherwise all day. `require` is now `"all-gating"`, read from the
checkers' own row tables through `scripts/lib/gating.py`, plus `evals: true`.
The set is no longer copyable, so it cannot fall behind. **FM-20** names the
shape: not drift — the list was short the day it was written, and every release
that added a gate widened the gap without touching it.

**Held against a document known to be good, because the owner suspected the
instrument.** She said the validation was probably buggy, which was the right
suspicion — six of this session's findings were bugs in it. So the scorer was
pointed at the accepted reference deck: **26 of 26 gates, three checkers at exit
0, no Evals miss, in both genres.** The instrument passes what is good and fails
what is not; what failed was the bar it was asked to apply.

**The task now asks the agent to check its own work,** which is the owner's
decision and the reason the earlier verdicts meant nothing. The reference deck
was built by Claude Code through this package's real pipeline — scaffold, build,
check, fix, repeat, eleven revisions — and a single non-interactive call with no
loop produced 66KB against its 923KB. Holding a one-shot process to a
pipeline's output standard measures the contract, not the agent, and every
agent failed it identically. With the loop: Claude Code went from six gate
failures and `visual_share 18.5` to every gate passing at 44.0, same model, same
effort. **The one variable was whether it was told to look.**

**And the `full` tier's central claim was impossible to meet.** That tier says
the agent runs check_prose, check_design and inspect_layout ITSELF. Claude Code
was driven with `--permission-mode acceptEdits`, which permits writing files and
not running commands: asked to check its work it stopped after 141 seconds
having written nothing and requested a `python3` allowlist entry. No run had
noticed in the releases the claim has stood, because until now no task asked.
It is driven with an explicit `--allowedTools` allowlist now — not
`bypassPermissions`, which an automated review flagged and which would have
handed arbitrary shell to an agent on every machine that runs this harness. A
test refuses both a mode that cannot execute and a mode that grants everything.

**Half the standard shown is half the standard met.** The first version of the
loop named the three checkers and not the Evals, and the cost was measured
inside the hour: Claude Code ran `check_design` five times, cleared all 29
gates, and stopped at `visual_share_median 42.0` against a floor of 50 — a bar
no checker reports. Hermes stopped at 44.0, Cursor at 43.5 the round before. An
agent iterates to the edge of what it is shown; `eval_corpus.py` is the fourth
command in the contract now.

**Three checks the eye found first, and each was wrong twice before it was
right.**

`figure_ink_collision` — `collision` measures page BLOCKS and never opens an
svg, so a chart whose arrow lies across its box is a clean page to every gate
this package has. Three agents shipped decks that way, each having iterated
until all three checkers exited 0, and none was told. Rule v1 keyed on the share
of the smaller mark and **failed the accepted reference on three pages**: 5x5px
of a 12px arrowhead is 81% of it and is how a drawing is MADE. v2 added a size
floor and still failed it — on `'path' over '3 · Australia, New Zealand'`, a map
label lying on the region it names. v3 excludes text entirely, because paint
order settles it: every label in all four documents measured is drawn ON TOP.
The floor is 12x12px, and it is the reference's own number — 64 self-overlaps
there and **not one exceeds 7x6px**, against the 20x49px the owner saw.

`title_two_lines` — design-rules calls two lines the headline's only hard limit
and nothing checked it; `reserve` asks whether a title fits the height it
reserved, which a five-line cover inside a generous reserve passes. Rule v1
counted `height / line-height` and read a thirty-character headline in this
package's own passing fixture as three lines, at two of four viewports —
padding counted as text. v2 counts line boxes from a `Range` over the rendered
text, which is the technique the caption measurement in the same file has used
since 0.1.384 and which reading the file would have found. Bookends are exempt
on the reference's evidence: it keeps every opener and content headline inside
two lines and exceeds only on cover and closing, as do all four documents
measured. They are reported.

`D32_shape_use` gates. Its condition was always binary — a page that DECLARES
an analysis move and draws none of the library's shapes has said what it is
doing and not done it — and it was reported for three releases. The reference
declares no moves and passes untouched; the deck the owner opened declares seven
and drew zero. Four prose sites named the gating set and the guard caught all
four.

**What is measured, reported, and still cannot fail** is `D9_layout_spread`,
whose pass condition is the literal `True`. The owner's first complaint was that
most pages are the same left/right split; the metric had already measured
exactly that — 3 layouts, top share 70.0%, against the reference's 6 at 33.3% —
and said nothing. It is **GAP-024** rather than a new gate, because a threshold
between those two numbers would be invented from one accepted document, and
0.1.339's 82% page-fill floor is what this package earned convention 6 with.

**Also from the same session.** A misplaced artifact is kept in the run record
under `misplaced/` — not scorable, because the scorer's glob does not recurse,
and not lost, because a run directory holding a transcript and no deliverable is
one a reviewer cannot review; the owner looked for one and reported the absence.
`run --drive` reads usage from a CLI's own file (`drive_usage_file_flag`, Hermes)
and accepts `inputTokens` as well as `input_tokens` (Cursor), each of which had
been silently recording no cost at all. Cursor pins effort through the model id
(`drive_effort_in_model`), since `cursor-grok-4.6-low|-medium|-high` are three
ids rather than one model and a flag. `_eval_misses` reports a document it
cannot read instead of raising KeyError on it.

## 0.1.542 — Hermes is driven and its registry guess was wrong, a misplaced artifact is named, and the delivery folder stops collecting renders

**Hermes joins the board, and two of the three things the registry said about
it were false.** Its `probe` was `null` — withdrawn at 0.1.473 because nobody
could confirm the binary name — and its install path was a guess carrying a
waiver that said so: *"the shared ~/.agents/skills/ location is the most likely
and must be confirmed on a machine with Hermes installed"*. It is not the
location. Hermes answers `Unknown skill(s)` to that path and files skills by
CATEGORY under `~/.hermes/skills/<category>/<name>/`. The binary is `hermes`,
and the board's `cli` column carries whatever version it answers rather than a
number written here. Both facts are now measured rather than assumed, and the waiver that
made them checkable is what made the correction possible — an unverified claim
with a written waiver is a claim that gets tested.

**What driving it needs, none of which is in any document.** `-z/--oneshot
<prompt>` is the only headless mode and the prompt is the flag's VALUE, so it
uses `drive_prompt_flag` — the mechanism 0.1.540 added for Gemini, second
customer inside two releases. `--yolo` for approvals. `--skills` resolves names
and installed paths and **refuses an arbitrary one**: pointed at the repository
itself it exits 1. `--reasoning` takes low/medium/high, which makes Hermes the
second agent after Claude Code that can fill the effort axis of the matrix.
`--usage-file` writes token counts to a FILE rather than the transcript, so this
run records no usage for it and says so instead of implying zero.

**The delivery folder is where verification lives now** (owner directive). Run
directories resolve through `output_dir.py` — the same resolver design-rules §8
already owned — so they land beside the deliverables a person reads rather than
inside a checkout. It **reads that folder and never creates it**: the 2026-08-09
directive gives `output_dir.py --create` that job alone, so a machine that has
not run it keeps its runs in the checkout, and the run prints which of the two
it chose rather than switching silently. `LUMI_CONFORMANCE_RESULTS` overrides
both.

**A misplaced artifact is named instead of being reported as nothing.** Two
agents have now written their deliverable somewhere the driver does not look,
and the board recorded both as agents that produced nothing. The cost is
measurable and was measured: Hermes's first T1 deck passes `check_design`,
`check_prose` AND `inspect_layout --deliverable` with no failure — the cleanest
artifact any agent has produced for this suite — and its cell read `no
deliverable`. `drive()` now sweeps HOME, the declared `skill_paths` roots and
this package's root, non-recursively and inside the run's own time window, and
records `verdict: misplaced` with the path. **The file is never copied in and
scored**, because scoring it would launder a run that missed the task's own
instruction into a pass. `score` folds it into `not earned`: neither credit nor
blame, which is honest about a question this release does not settle — whether
ignoring the driver's cwd is the agent's defect or the harness's assumption.
GAP-022 carries both readings and stays open.

**The 0.1.540 entry generalised from one case and this release withdraws it.**
It said the misplaced deck "fails on its own merits, so no verdict changes if it
is scored". True of Gemini's. Not true of Hermes's, three releases later, in a
ledger entry whose whole job is to be read by someone later.

**A run may also write into the run's own folder, and that counts.** Told to
write "in the working directory" and unable to see the driver's cwd, Hermes
looked for where `input.md` lives and wrote beside it — the run folder, because
the driver leaves a copy of the input there too. Its transcript reasons it out
in those words. That is where the driver copies the artifact anyway, so it now
counts as produced and the record says by which route. Before this, `score`
graded that file `pass` while the `driver.json` beside it said `produced: []` —
two files in one directory telling a reader different stories.

**Renders stop being written where records live.** `inspect_layout` wrote its
contact sheet and 4K page rasters into the document's own folder, so the owner's
delivery folder reached 5,834 rasters and 1.0GB by 2026-08-18 and — after a
cleanup and a standing order against exactly that — 2,164 and 349MB again a
fortnight later. `.gitignore` had already reached the same conclusion twice,
one directory at a time (`fixtures/_layout/`, `backlog/_layout/`). The default
is now a per-document folder under the system temp directory, `--out` keeps one
on purpose, and the path is printed either way.

`scripts/ops/housekeeping.py --check` is the guard, in CI and therefore in
preflight: it fails when the delivery folder holds a render. Its rule is three
tests in an order that matters — nothing under `_sources/` is a render whatever
it looks like, a raster anywhere else is one, an HTML file is one only when it
carries inspect_layout's `-sheet-` infix. **The first test exists because the
first real run of the tool proposed deleting two thumbnails a recipe READS**,
which is convention 15 in four seconds: the model was wrong about the material,
and only the material could say so. `--apply` deletes renders and nothing else;
the retention policy for documents is the owner's and is not encoded here.

**Red first, everywhere.** The misplaced sweep, the run-folder route, the
results root and the housekeeping rule each ship with tests that fail without
their code — including one that fails by deleting a recipe input.

## 0.1.541 — a stat band may not be shorter than its own labels, in either geometry

**What a page did.** `.body > *` carries `min-height: 0` so a figure can give
back space it does not need. A stat band cannot give any back — its cells are
text, at `align-items: start` — and the same declaration let its grid row
collapse below the height those cells need. The cells do not shrink with the
row: they hang out of the bottom of a box too short for them, onto whatever is
beneath. Measured on the 0.1.540 conformance deck: a `.body.hero-band` page
computed its rows as `138px 381px 35px`, the band needing 61px in the 35px row,
and its labels rendered 12px below the content area's bottom edge, overlapping
the confidential footer line by 352x5px. `collision` caught it, and only
because the footer happened to be there to be hit.

**The floor, and it is a floor.** `.body > .band { min-height: min-content; }`.
`min-content` rather than a pixel number because the same markup needs 61px in
landscape and 48px in portrait, so any constant would be wrong in one of them.
The figure keeps giving back its own space, so nothing spills: measured at every
collapse point in both geometries.

**Both geometries were swept, and the second one is why.** Landscape's band
collapses once the figure on the page passes about 380px; portrait's holds
until about 900px — a taller page, the same mechanism, `min-height` computing
to `0px` in both. At the extreme both crush the row to 0px and the band renders
entirely outside itself. The first sweep of this reported portrait as
unaffected, which was an artifact of the reproduction rather than a fact about
portrait: the test figure was sized for a 720px-tall page. **A held-fixed axis
is an unchecked axis**, and the fix would have shipped as landscape-only on the
strength of a case that simply had not been pushed far enough.

**The gate.** `band_escape` in `inspect_layout.py --deliverable`: a band whose
`.k`/`.v` cells render outside the band's own box. Decidable, not aesthetic —
text outside the box it belongs to is on top of whatever is under it — and it
sees the case `collision` cannot, a band collapsing over empty canvas with
nothing to hit. The measurement needs Chromium; **the decision does not**, so
the decision is `_band_escaped` / `_band_escape_worst` in Python with tests that
run without a browser, the pattern `aspect_stage` set at 0.1.524. The report
names the row and the need together, because "45px of labels are outside" is the
symptom and "a 15px row for 61px of content" is the defect.

**Planted red on a real document, first.** A scaffold-built page in each
geometry, its band collapsed by a figure that grew: red before the token floor,
green after, both geometries. Then `check_fixtures` refused the metric outright
— *"band_escape is graded and no fixture fails it — the suite cannot tell it
from a metric rewritten to return ok"* — so `deck-broken.en.html`'s page 3 band
now overrides the floor and fails it. That override is not a contrivance: the
deck that produced the finding carried these tokens verbatim, and `.body > *`'s
zero was the whole of the band's protection.

**What this does not fix, stated plainly.** It does not make an overfull page
fit. Re-run against the deck that produced it, `band_escape` goes green and
`collision` still fails — now reading `conf/band 413x5px` rather than
`k/conf 352x5px`. The band is no longer lying about its height, and the page is
still 5px too tall for its content. That is the right attribution: one defect
was text rendering outside its own box, and the other is a page with too much
on it.

Swept: the `--deliverable` verdict list is restated in `CLAUDE.md` and
`SKILL.md`, and both name the new one.

## 0.1.540 — Gemini becomes drivable, the board names the model behind each row, and two findings the run itself produced

**The board is measured again, on three agents.** It had stood on the 0.1.522
run since 2026-08-19 and carried a waiver at 0.1.538 and 0.1.539 saying so.
Claude Code, Cursor and Gemini CLI were each driven through all three tasks on
2026-08-21. Cursor passes all three. Claude Code passes T2 and T3 and **fails
T1-deck on a collision** — a change of kind rather than of grade: at 0.1.522
that cell read `not earned` because the driver's ceiling was 900s, and with the
default 1800s the agent finished in 1608.9s and produced a deck whose blocks
land on each other. A timeout became a measurement. Gemini passes T2 and T3.

The header of a freshly refreshed board reads `1 release behind` **by
construction**, and it is not a sign the refresh was skipped: the runs execute
before the release stamps its version, so the run directory carries the
previous number while the history rows — which are what the freshness gate
actually reads — carry this one. Anything larger than one is real staleness;
this board's previous header said five.

**Gemini could not be driven at all, and the reason was one flag's position.**
Its registry record had a probe and no `drive` argv, so `detect` saw it and
`run --drive` skipped it. Gemini's only non-interactive mode is `-p <prompt>`,
where the prompt is the flag's VALUE — and this harness appends the prompt
last, after `--model` and the effort and usage flags. Declaring `-p` in the
registry's argv would therefore have sent `--model` as the prompt and left the
real one as an interactive-mode positional: a run that reaches the model,
answers a question nobody asked, and exits 0. So the prompt flag is now
declared as `drive_prompt_flag` and the driver puts it where it has to go,
immediately before the prompt — the same lesson `drive_skill_flag` carries two
comments above it, that where a flag sits is part of the flag. Planted red
first, per convention 15: without the driver change the test reads
`['--model', 'a-model', 'write the file']`.

**A second Gemini fact that only a real CLI could have taught.** Headless runs
need `--skip-trust`. Without it the CLI prints `Approval mode overridden to
"default" because the current folder is not trusted`, exits 55 in about a
second, and never reaches the model — an environment refusal that reads on a
board as an agent that failed. It is in the registry's notes and in the
generated adapter page.

**The board now names the model behind every row, because this run needed it.**
The account's free-tier quota for `gemini-2.5-pro`, `gemini-2.5-flash`,
`gemini-2.0-flash` and `gemini-3-pro-preview` was spent, so Gemini was pinned to
`gemini-flash-lite-latest` while the other two ran their CLI defaults. Three
rows on one table, one of them a lite tier, with nothing to tell them apart —
which is the reading this file's own driver test has warned about since 0.1.454:
*a cell that says nothing about the model reads as a claim about the agent
rather than about one of its configurations.* `score` now carries the driver's
model into each entry and `report` renders it as a column; a row mixing
configurations lists them rather than averaging them away. Planted red first.

**Two findings the run produced, both in the ledger rather than in this
entry.** **GAP-022**: Gemini's T1-deck exited 0 after 663.7s saying it had
written the deck *"in the working directory"*, and the file — 571KB, finished —
landed in the **skill directory** instead, which on this machine is a symlink to
this repository. `drive()` globs the working directory only, so the run recorded
`produced: []` and the board cell reads `no deliverable`. The deck fails on its
own merits when measured (D19 9, D6 12, M11 91.7% against a 60% ceiling), so no
verdict is being withheld — what is wrong is a run reporting that nothing was
written when something was, somewhere it should not have been. **GAP-023**:
`trace.py` resolves its store from `__file__`, so a driven agent running the
scaffold writes `source: build` traces into the *installed skill*. Cursor's one
T1-deck task opened three of them here, all left open. `release.py` stages with
`git add -A`, which puts a stranger's traces one release from being committed as
the owner's, and `ledger.py --board` reads every stored trace into the same
median. Four such traces were removed by hand before this release; the
`LUMI_TRACES` escape hatch that would fix it already exists and is unused on
that path.

**The efficiency board has its first reading.** Claude Code's T1 trace carries
the API's own counts — 176 in, 114413 out over 8 content pages, 14301.6 tokens
per content page — so `ledger.py --board` reports 1 of 13 runs qualifying rather
than 0. It sits in the `? × ?` cell, because neither model nor effort was
pinned. That cell is what the six-cell matrix exists to fill, and it remains an
operator step.

## 0.1.539 — main takes changes only through a pull request, and the lock reports the rule it gained

**The setting the owner had left open is now closed.** 0.1.538 recorded, as an
open operator step, "whether to require a pull request in `main`'s branch
protection — which today requires the `checks` status and nothing about how the
commit arrives". It now requires both. No approving review is asked for: the
rule closes the direct push, not the solo merge, and a review requirement would
have made every release wait on a second person rather than on a check.

**What it actually closes, since the `checks` status was already required.** A
commit that has gone green on a branch carries that status wherever it goes, so
fast-forwarding `main` onto it was a push GitHub would accept — no pull request,
no second CI run, no record. That path is what disappears. The protection object
was written whole (the API has no partial update), and the sixteen settings that
were not the subject — the required check and its strictness, admin enforcement,
linear history, force-push and deletion blocks, conversation resolution — were
read back field by field against a pre-change snapshot and are identical.

**`emergency_merge.sh` needed no new lock, and said so wrongly.** Turning
`enforce_admins` off suspends the whole rule set for admins, so the one lock it
opens is still the only one; and it reaches the merge through `gh pr merge`,
which is what the new rule asks for anyway. Its header comment claimed the
protection was the `checks` status alone, and its closing "Final state" report
printed four settings — neither of which would have mentioned the rule after
this release, so the report would have looked complete while omitting one. Both
now name it. The new `jq` line was run against two real protection objects
before shipping, per convention 15: the live one, which prints
`pr_required=true approvals=0`, and the pre-change snapshot, which has no such
block at all and prints `pr_required=false approvals=0` rather than failing.

**Swept, not remembered.** `CLAUDE.md`'s "When CI is slow or down" opened on the
old fact and is corrected. The other two restatements — 0.1.538's entry above
and step 14 of `specs/2026-08-20-audit-remediation-plan.md` — are history and
stay as written; both describe the setting as the owner's to change, which it
was, and this entry is where it changed.

## 0.1.538 — ten red CI runs on the remediation branch, and the symlink that caused them

**Local green was not CI green, again.** Every release from 0.1.528 to
0.1.537 passed `preflight.py` here and failed in CI: `run_conformance.py
run --drive` repointed a `results/latest` symlink inside
`conformance/results/`, a directory that exists on this machine (gitignored,
forty megabytes of runs) and not on a runner, and two driver tests reached
that line. Ten pushes, ten failures, noticed when the PR was marked ready —
which is FM-06's shape (`check_repo` green is not the release green) with
the twist that preflight was green too, because the condition was
environmental. The repo's own note after every release — "Forty once
accumulated this way and CI had seen none of them" — was printed ten times
and read zero.

The link is now made only when the run lives under `results/`, and never
fatally: a link is a convenience, a run directory is the result. The
regression test reproduces the runner's condition (no results directory) and
both previously failing tests pass under it. The lesson for the branch is
procedural and is recorded rather than re-learned: **watch the run after
every push of a release branch**, and treat the draft PR's CI as part of
`release.py`'s verdict rather than as something to read at the end.

## 0.1.537 — the audit's process finding is withdrawn, and the branch is ready to merge

Audit-remediation step 14 (`specs/2026-08-20-audit-remediation-design.md`),
the last.

**A finding of the audit was wrong, and this entry says so.** The audit
read `git log --merges` as empty and concluded that sixty-six releases had
reached `main` with no pull request. `gh pr list --state merged` shows
otherwise: #102 carried 0.1.457–0.1.495 as one PR, and #104 through #127
carried one release each, every one rebase-merged — which keeps one commit
per release and leaves no merge commit. The audit inferred pull requests
from merge commits, and the inference was the defect; the audit document,
the remediation design and its plan are corrected at their three sites.
This is the second of the audit's readings withdrawn on this branch (the
first, at 0.1.524, was the phase clock), recorded here because an entry is
what a later session believes (convention 14).

**Convention 3 says what it meant.** "Merged, not squashed" read as though a
rebase merge were a third thing; it is the form the two guards need, and it
is how the whole refactor landed. The convention now names it.

**What this branch leaves open, on purpose and in the ledger.** GAP-015
(privacy layer 3 is not the designed allow-list report), GAP-016
(`check_outline.py` mechanises three of thirteen outline items), GAP-020 (the
trace schema's `feedback` field), GAP-021 (A1 fails D27; the owner's
calibration-only ruling stands until a second accepted document exists),
GAP-004 and GAP-005. And three operator steps the instruments are now ready
for: the six model×effort cells (`run_conformance.py run --drive --model …
--effort …`, which now writes conformance traces), the blind score of
corpus D18 (its sheet is in the delivery directory), and whether to require a
pull request in `main`'s branch protection — which today requires the
`checks` status and nothing about how the commit arrives.

Fifteen releases, 0.1.523–0.1.537, each with its own CHANGELOG entry,
planted-red run and tests; seven new guards (`secret patterns parity`,
`no shadow markup`, `rubric unbuilt claims`, `prompt parity`, `entry
restatement ceiling`, the manifest half of `assets tracked`, and
`review_scores --check`'s corpus resolution), one new generator with a CI
`--check` (`recolor_shapes.py`), three new reported rows (D31, D32, and the
board's generated findings), and four rules homed in `references/`
(OR-8, OR-9, OR-10, DR-6's parentage). The audit's §10-A list is empty;
§10-B is done or ruled; §10-C is the prompt-parity guard, the field in the
scaffold, and a ledger that says what the `files` tier and the second brand
are waiting for.

## 0.1.536 — AGENTS.md becomes a map, and the sweep learns to scope to what you touched

Audit-remediation step 13 (`specs/2026-08-20-audit-remediation-design.md`).
**Closes GAP-018.**

**AGENTS.md: 286 lines → 125.** The Codex entry point restated most of
`references/` in its own words — the load order alone ran ninety lines of
paraphrased rules — and grew by a third during a refactor whose design said
it would shrink. Every restatement was a copy that could drift, and this
file had carried withdrawn rules for four versions before. It is a map now:
the stamp, the language default, the capability tiers and OR-9, the six
files in reading order with the section each rule lives in, the build loop
and the instruments named once each, debug mode, and — kept verbatim — the
six red lines, the gating line and the rule-change sentence the guards read.
The `red line parity`, `gating claims`, `output default` and
`version citations` guards all pass on the rewrite, which is what lets a
hand-written file shrink without anyone reading it twice. **`entry
restatement ceiling`** holds it to 150 lines, the number beside the guard
and nowhere in prose; raising it is a CHANGELOG decision, the way a
threshold is.

**`claim_sweep.py --changed [REF]`.** Convention 12 says "read the claims
touching what you changed"; the sweep printed two hundred and eighty and its
last two lines were what `release.py` showed. The flag scopes the counted
claims to the files changed since a ref (working tree, index and untracked
files), and `release.py`'s step 5 now prints those — five lines on this
release instead of a total. This is the "claim_sweep extension" the refactor
design listed for P1 and the audit found untouched since 0.1.453.

Four tests in `tests/test_shadow_guards_audit.py`; the planted reds are an
AGENTS.md one line over the ceiling and a sweep whose scoped result names a
file that was not changed.

## 0.1.535 — a city name leaves the tracked files, and a manifest may not describe what git does not have

Audit-remediation step 12 (`specs/2026-08-20-audit-remediation-design.md`).

**Red line 9's edge.** The hard core held — no client name, figure, email or
phone in any tracked file — and one city name had reached eight of them
through a single path: a design-provenance comment in `tokens/lumi-layouts.css`
("the … pilot of this form was accepted"), propagated by `build_fixtures.py`
into three fixtures, then written by hand into a test, two backlog entries
and a spec that cited a deliverable by its filename. Each is now neutral
("the 2026-08 roadshow pilot", "the 0.1.519 r2 build of the investor
deck"), the fixtures regenerated, and the remediation's own spec and plan
were carrying the word too and are corrected with the rest. The one
remaining mention is inside `releases/evidence/0.1.519.json`, a waiver
text in a released evidence record: evidence is history and is left as
written. The instrument for the edge is 0.1.526's — the repo secrets guard
reading the operator's out-of-bounds lists — and it would have caught this
on any machine carrying the list.

**`assets tracked` now runs in both directions.** It asked git which files
under `assets/` were ignored-but-present; it did not ask whether the files
a `SOURCES.md` describes are tracked at all. Two manifests described 37
assets that were on disk and untracked — neither ignored nor in the index,
so invisible to the first question — which is 0.1.504's shape (a manifest
describing 206 preview files nobody had) arriving again. Every `| file |`
row in every `assets/**/SOURCES.md` is now held to `git ls-files`. Red run:
a synthetic repo with a manifest row for `ghost.svg`, in
`tests/test_shadow_guards_audit.py`.

## 0.1.534 — a scored document is never deleted, the losses are recorded, and the pitch deck gets a corpus id

Audit-remediation step 11 (`specs/2026-08-20-audit-remediation-design.md`).

**The evidence behind the first C1–C8 scores is gone, and now the file says
so.** Eight of the fifteen entries in the local corpus registry pointed at
files that no longer exist — among them D15 and D16, the only two documents
with human scores, and D17, the only other one with a trace. The agreement
study's three joinable pairs can never be re-measured; a retrospective that
wanted to read the page a score was given for has nothing to open. Nothing
had noticed, because nothing resolved a scored id to a file.

**OR-10 · a scored document is never deleted.** A document that has been
scored, registered as a corpus id, or named by the threshold table is kept
under its build name for as long as the score stands; superseded builds that
were never scored may go. A corpus entry may now be `{path, archived:
{sha256, pages, removed_before}}`, so a loss that already happened is a
recorded fact rather than a dangling id; the three deleted documents carry
that record with `sha256: null` — nobody can hash a file that is gone, and
writing a digest for it would be the fabricated join key the scores file's
own comment warns about. **`review_scores.py --check` fails a scored id that
resolves to neither a file nor an archive**, and reports `not attempted`
where the local registry is absent (CI), never `ok`. `scripts/lib/corpus.py`
is the one reader of the registry; three scripts had each parsed it their
own way.

**The pitch deck is corpus D18.** The largest deliverable of the 0.1.521–
0.1.522 campaign had never been scored. It is registered, and a blind
C1–C8 sheet for it is written to the delivery directory by
`scoring_sheet.py` (owner ruling D2: the sheet is generated, the scoring is
hers and not blocking).

**A1's standing is written down, not changed.** The only accepted reference
fails D27, a gate shipped five releases after its acceptance; its agenda
paraphrases its openers, and it cannot be rebuilt to pass without ceasing
to be the document that was accepted. Owner ruling D3 (default taken):
calibration-only. `evals/thresholds.json` now says `accepted_under: 0.1.449,
shippable_under_current_gates: false` beside it, no gate is loosened, and
**GAP-021** records the ruling with its close condition — a second accepted
document on the tier, which is hers to start.

Six tests in `tests/test_corpus_resolution.py`; the planted red is a scored
id whose file is gone and which carries no archive.

## 0.1.533 — the framework's shape reaches the figure slot, the library's use is counted, and the exemplars are read where they can act

Audit-remediation step 10 (`specs/2026-08-20-audit-remediation-design.md`).
The audit's finding on the two bodies of domain knowledge was the same
finding twice: the McKinsey shape library (206 units, tagged, embeddable on
demand) was referenced by **zero** `<use>` elements across five shipped
deliverables, and the exemplar notes were loaded by no entry point. Both
were reachable and neither was on the path.

**A declared move now arrives with a shape.** `new_deck.py` used to name the
candidate frameworks in a comment and leave the figure empty, on the
reasoning that the relation lives in the content and a prescribed shape would
repeat the mis-curation. The reasoning holds for the *choice* and the
measurement says the *default* was wrong: a comment is not a path. So the
question → framework → shape chain (AR-4, design-rules §4.0) now runs to its
last link in the scaffold: a page whose outline declares a move gets the
first shape of the first framework that draws it — or of the framework the
outline names, `framework: <id>` being a new optional field of the analysis
line — in its figure slot, with the alternatives in the comment and the
x/y/width/height the library's non-zero viewBox origins require. A move no
framework draws (`correlate`) or a framework drawn natively (funnel,
waterfall, market-sizing) leaves the slot a prompt. Run against the real
outline of the 0.1.522 pitch deck: fourteen pages, eleven slots filled, D19
resolving every one.

**D32 · shape-library use** is a reported row: how many library shapes the
document draws with, against how many pages declare a move. It is a finding
only on a document that declares moves and draws none of them — a deck
whose every page says `compare` and whose figures are all hand-drawn has
either drawn natively on purpose or let its slots go, and the count tells a
reader which to look for. A document that declares no moves is not measured
against it, so nothing built before the analysis beat existed reads
differently.

**The exemplars are read at the analysis beat.** `SKILL.md` step 1b and the
`AGENTS.md` load order now send the agent to
`references/exemplars/mckinsey-design-notes.md` (and `yc-pitch-notes.md` for
a `pitch-deck`) at the beat, which is the one place ten devices about how a
page carries an argument can act; loaded at composition, 0.1.522 measured
that they landed as typography (row labels, number-top) and never as
analysis (zero benchmark lines, zero unit lines).

**The field rides in the scaffold.** `brand.md`'s signature device — one
mark per datum, intensity from the datum — shipped in the tokens at 0.1.379
and was used by nothing the audit measured. It is in the sample rotation
now with its rule as the comment beside it: no set behind it, delete the
block. The owner's D5 ruling was "keep and scaffold"; retiring it remains
hers.

Five tests in `tests/test_new_deck.py` (a named framework beats the move's
first candidate; `correlate` leaves a prompt; an outline with moves yields
slots) and D32's fixture expectations. GAP-016's sibling — that the scaffold
prescribes nothing — is the reasoning this entry overrules, and it is
overruled on a measurement rather than a preference.

## 0.1.532 — the shape library is regenerable from inside the repository, and held to the tokens

Audit-remediation step 9 (`specs/2026-08-20-audit-remediation-design.md`).
**Closes GAP-017.**

**The recolour tool comes home, and the originals come with it.** The 206
units under `assets/shapes/` were produced by a script in the owner's review
directory from originals that were not vendored, so no clone could
regenerate the library and nothing held the committed SVGs to the tokens
they claim to follow — the one vendored asset here without a `--check`.
`scripts/build/recolor_shapes.py` is the port: the ramp, the ink, the cold
white, the lime and the canvas are read from `tokens/design-tokens.json` at
run time, the colour maths comes from `color_math` (the `no shadow math`
guard holds that), and `assets/shapes/source/` carries the un-recoloured
originals with a unit list in extraction order. **The first `--check`
against the committed library was byte-identical on all 206 files**, which
is the proof that the in-repo tool is the tool that made them; the check
now runs in CI beside the other nine asset generators, and `release.py`
regenerates the library with the other generated artefacts.

**Two fallbacks are not token values, and the file says so.** The
extraction wrote `--ln1`/`--ln2` fallbacks as "rgba(43,46,51,.20)/.12
flattened on white", and they are not — the true composites are `#D5D5D6`
and `#E6E6E7`. They are kept verbatim, because they sit inside every
committed file and the `var()` wins inside any LUMI document; moving them is
a regeneration decision, and `--check` is where that decision becomes
visible rather than silent.

Four tests in `tests/test_recolor_shapes.py`; the planted red is one
`--acc-5` rewritten to `--acc-4` in a copy of the library, which `--check`
names by file. The extraction's full index (page names and family labels in
the template's own language) stays outside the repository; the English-only
guard would not have it, and the committed tags in `tags.json` are the
classification that matters.

## 0.1.531 — the loop keeps its own time: traces open at the scaffold, close at the check, and the matrix can be fed

Audit-remediation step 8 (`specs/2026-08-20-audit-remediation-design.md`).
**Closes GAP-014.** Nine traces, zero phases, zero tokens, zero effort — the
cost instrument existed as a schema and a board, and nothing in the build
loop had a clock. The audit's reading was that the instrument was built and
never wired; this entry wires it, with the same rule `--usage` already
followed: every number is the tooling's, and there is no flag to type one.

**`trace.py phase start|stop <name>`.** The tool stamps the clock at start,
stamps it at stop, and writes the difference; open clocks live in a
gitignored sidecar beside the store, because a started-at timestamp is one
machine's state and the trace carries only seconds. `--phase NAME SECONDS`
on close stays, for a machine dump, and `LUMI_TRACES` is honoured (it was
passed by one test for eight releases and ignored), so tests write to a
scratch store.

**The scaffold opens the record; the check closes it.** `new_deck.py` opens
a trace whenever a `--storyline` is given (a trace declares its storyline,
and the scaffold does not guess one), starts the `build` clock, and writes
the id into `<body data-trace>` so it rides in the document. `check_deliverable.py`
reads that attribute, stops the build clock, closes the trace with its own
wall-clock as the `checks` phase, and — this is the part that changes what a
reader sees — **reports a document with no trace as `unmeasured`** and
exits non-zero, the established "did not run is not ok" shape. Fourteen
consecutive builds of one deck had left no trace while the ledger counted
zero abandoned builds; that absence now prints.

**`run --drive --effort low|medium|high`** pins the effort through a flag the
registry names per agent (`drive_effort_flag`; Claude Code's CLI has
`--effort`, verified on this machine) and records what was *pinned* — an
agent with no such flag records `(not pinned)`, never the requested value.
Where the registry names a `drive_usage_flag`, the CLI is asked for a JSON
transcript and the API's own `input_tokens`/`output_tokens` are read from
it. Each driven task with a `storyline` opens a `source: conformance` trace,
closed with the driver's seconds as the build phase, the model, the effort
and the usage, so the model×effort matrix reads real rows from the harness
— the first use of the `conformance` source the schema has carried since
0.1.462. `T1-deck` declares `storyline: status-report` (not fingerprinted; a
verdict does not depend on it). **The six cells themselves are still an
operator step**: `ledger.py --board` reads "0 qualify" until she runs them,
and that is now a statement about runs not made.

Thirteen new tests across `test_trace.py`, `test_new_deck.py` and
`test_conformance_driver.py`; the planted reds are a `phase stop` with no
start, a scaffold without a storyline (no trace, and it says so), a
check_deliverable run on a fixture with no trace (`trace: none`), and an
effort requested of an agent with no flag.

## 0.1.530 — the prompt tier is held to the rules it could not see, and the capability rule comes home

Audit-remediation step 7 (`specs/2026-08-20-audit-remediation-design.md`).

**`prompts/lumi-style-core.md` was a subset with nothing holding it.** The
self-contained file for agents with no tools was missing the number-first
rule (0.1.521's headline), six of the eight storyline names, twenty-five of
the sixty phrases `check_prose` gates on, and the unconditional form of the
capability rule — while `ban-list parity` held the checker to
`writing-rules.md` and never looked at the prompt. A prompt-tier agent
following §3 to the letter would still have emitted two in five of the
phrases the full tier fails. All four are in the file now: every storyline
by its `data-storyline` name with the sections a reader of that kind looks
for (a checklist to report against, never a gate); the checker's ban list
verbatim; the number-first sentence; and the prohibition stated outside the
debug-mode branch it had been scoped to.

**`prompt parity` is the guard.** It holds the prompt to three sources — the
storyline vocabulary in `deliverable_registry`, `check_prose.BANNED` (or a
`NOT_IN_PROMPT` waiver with a reason; the table is empty on purpose), and
two load-bearing sentences — and it fired on real material before it was
green: run against the 0.1.529 prompt it returns thirty-four findings, and
its first run on the edited file caught `proposal`, the one storyline whose
skeleton lives in a template rather than in `TYPICAL_SECTIONS`, which the
edit had skipped. Five synthetic-tree tests in
`tests/test_shadow_guards_audit.py`.

**OR-9 · an agent that cannot run the checks may not call a deliverable
verified.** The prohibition half of the capability-tier rule existed only in
`adapters/platforms.json`, a file every entry point says loses to
`references/` on conflict; `eval-rubric.md` carried the obligation half
alone. The whole rule now lives in `references/operating-rules.md` as OR-9,
and the registry and the review protocol cite it. This is the shape GAP-006
was opened for, one instance of which survived its closing.

**Smaller.** `emergency_merge.sh`'s trusted execution closure gains
`check_prose.py`, `check_privacy.py`, `markup.py` and `secret_patterns.py`,
which `check_repo.py` now imports; `tests/test_emergency_checker_closure.py`
caught the omission, which is what it is for.

## 0.1.529 — the ledger catches up with the refactor: seven gaps and two ideas that had no entry

Audit-remediation step 6 (`specs/2026-08-20-audit-remediation-design.md`).
The refactor design's rule was "every shortfall goes to KNOWN_GAPS; none
stops at 'later'". The audit found nine shortfalls with no entry anywhere,
and that between 0.1.489 and 0.1.522 — thirty-three releases — not one GAP
had been opened while two real-build defects went to the backlog. This
release writes the entries. It changes no behaviour; its value is that the
next session reads a ledger that says what is missing instead of a design
that reads as delivered.

**Opened.** **GAP-014** the cost instrument has never produced a reading (nine
traces, zero phases, zero tokens, zero effort; K1's six cells empty; the
four-beat falsification test unrunnable). **GAP-015** privacy layer 3 is not
the designed allow-list report and says so only in its own docstring.
**GAP-016** `check_outline.py` mechanises three of the thirteen `[outline]`
items and the rubric's tags promise the other ten. **GAP-017** the shape
library cannot be regenerated from the tokens inside this repository.
**GAP-018** AGENTS.md grew from 210 to 286 lines against a design item that
said it would shrink. **GAP-020** the trace schema dropped `feedback` with no
recorded reason. **IDEA-16** `marketing` is a genre name with no behaviour
of its own. **IDEA-17** M13 reads a quantity conflict on an English file that
it does not read on the file's Chinese twin (out of this branch's scope: it
sits inside the frozen Chinese-output diagnosis).

**Opened and closed in one entry.** **GAP-019** the forty megabytes of
unreferenced conformance results the design's P0 named and the plan dropped
— closed by 0.1.528's dated per-run directories rather than by a deletion,
because the mechanism that let one directory hold several runs is what
mattered, and the old directories are on one machine and in no clone.

Three of the open entries name the step of this branch that closes them
(GAP-014 at the T1 step, GAP-017 at the recolour step, GAP-018 at the
AGENTS.md step); the rest carry their close condition and no promise of a
date. GAP-005 was reworded at 0.1.527 and is not repeated here.

## 0.1.528 — the conformance board's prose is generated, its header is dated, and a run id names one run

Audit-remediation step 5 (`specs/2026-08-20-audit-remediation-design.md`).

**The hand-written half of the board narrated a different run than its
table.** `CONFORMANCE.md`'s generated region refreshed at 0.1.522; the
paragraphs under it still said "Both agents fail T1-deck" and "Cursor:
`M2_number_sourcing` at 86.0%" beneath a table in which Cursor had passed all
three tasks with every verdict `ok` — for six days, on a tracked file. The
prose about the current run is now **generated from `scores.json`**: one
line per agent/task that did not pass, naming the failed metrics or the
driver's reason, and a `pass` row has no line at all. The old paragraphs are
kept, under a heading that says they are history of earlier runs, dated in
their own text. A sentence derived from the file cannot disagree with a
table derived from the same file.

**The header carries the run's date and the version it was scored at.** The
date is read from the scores file's own timestamp, never typed. The version
falls back to the newest `instrument_version` in the scores when the run id
carries none — `results/latest` does not, and a board rendered from it read
"skill 0.1.527" over a run scored at 0.1.522, which is precisely the claim
the `built_version` machinery exists to stop a cell from making. It now
reads `skill 0.1.527 · newest run 0.1.522 · 5 releases behind`.

**A driven run gets its own dated directory, and a task directory is cleared
before it is driven.** Every drive used to write into `results/latest`, so a
fresh `driver.json` (timeout, nothing produced) could sit beside a 569KB deck
from six days earlier in the same directory, and `history.json`'s `run_dir`
pointed at a tree last written on another day. `run --drive` now writes
`results/<version>-<date>/`, repoints the `latest` symlink, and removes the
task directory before driving so whatever is in it afterwards was produced by
that drive or by nothing. The stale deck under `latest/claude-code/T1-deck/`
is removed locally (the directory is gitignored; nothing tracked changes).

Five tests in `tests/test_conformance_board_generated.py`; the planted red
is a scores file with one failing task rendered into a board whose prose
names it, and a detect-only board that says nothing was scored rather than
that everything passed.

## 0.1.527 — five prose drifts corrected, and a claim of absence must now name its ledger

Audit-remediation step 4 (`specs/2026-08-20-audit-remediation-design.md`).
Every site below was written true and became false within a few releases;
this entry edits them and adds the guard that would have fired on the
previous state of the rubric at lines 364 and 387 — run against the 0.1.526
file before the edits, which is the planted-red this guard ships with.

**`references/eval-rubric.md` contradicted itself about two checks it also
documents.** Its metric table listed D23 (font count) and D27 (agenda
mirror); two rows of the same file said "there is no font-count check" and
"agenda and tracker existence is checked by nothing today". Both rows now
cite the checks, and the heading's "ten of the twelve have code" — wrong
since M13 — is replaced by the sentence that cannot rot: the table is the
list. **`rubric unbuilt claims`** is the guard: a sentence in that file
saying a check is not built must cite a GAP or IDEA, so the ledger guard
holds the id and the entry's closing is where the sentence gets revisited.
This is IDEA-11's shape (a promise conditional on a state) applied to the
file that had it twice.

**DR-6 stops promising a split that P0.5 never made.** `design-rules.md`
§4 read "P0.5's rule IDs will split them" eight releases after P0.5 shipped.
DR-15 established the multi-parent form in the meantime, so DR-6 now serves
**P-4 + P-1 + P-2** as one family with three parents, and says why the
split was not made.

**GAP-005 speaks the two-axis model.** The entry still said "product
introduction has no genre at all" while `product-intro` had been a templated
storyline since 0.1.513; it now states the obligation where 0.1.465 put it —
on the rule tier, three tiers, two without an accepted reference — and
points at the separate fact that A1 itself fails a later gate.

**Smaller.** `review_scores.py`'s docstring said "six human dimensions,
H1–H6" while its validator required C1–C8. Cursor's capability waiver in
`adapters/platforms.json` said `run_conformance.py` invokes no agent, which
stopped being true at 0.1.454; it now states what is actually unverified —
a synthetic conformance deck is not a real deliverable through the entry
file — rather than a mechanism that exists.

## 0.1.526 — the out-of-bounds list gets a home, and the checks that read it stop reading fonts

Audit-remediation step 3 (`specs/2026-08-20-audit-remediation-design.md`).
P-5's boundary had three holes the audit measured: the deny list — "the most
sensitive single file in the workflow" by the design's own words — had no
canonical location and no `.gitignore` net; the check that reads it had been
weakened in production to stay usable (IDEA-15); and the repository side of
the same principle was held by habit, with a city name in eight tracked
files.

**OR-8 · one place, outside every repository.** `~/.lumi/terms/<engagement>.terms.txt`,
one term per line, accumulated across engagements (the owner's 2026-08-15
ruling) with its three constraints restated as rules rather than advice:
strings only, never in a repository or trace or log, file-system permissions
first. `check_privacy.py` reads every list there when given no `--terms`,
and the `.gitignore` nets `*.terms.txt` and `terms-oob*` as the second layer,
with the same reasoning it already gives for `docs/`. `SKILL.md` and
`AGENTS.md` point at the rule instead of at a bare flag. `LUMI_TERMS_DIR`
overrides the location, which is how the test suite keeps a developer's real
list from turning "not attempted" into "loaded".

**IDEA-15 closes.** A three-letter Latin term had fired six times inside an
embedded font's base64 on a real build, and the term was dropped from the
list to keep the check usable. `term_text` now blanks `data:` URIs and long
base64 runs before the term scan (same length, so line numbers hold; the
credential scan keeps the whole file — a JWT is base64 by construction), and
`term_pattern` gives a pure-Latin term word boundaries while a term carrying
a CJK character still matches as a substring, because that script puts no
space where a boundary would be. Four tests were planted red on the
0.1.525 code: the font case, the boundary case (`Rayleigh` no longer
matches `Ray`), the real-name-in-prose case, and the directory default.

**The repository's secrets guard runs the same lists.** On a machine that
has `~/.lumi/terms/`, `check_repo.py`'s `secrets` guard runs every list over
the tracked text files and fails on a hit without echoing the term; where
the directory is absent (CI) that half is not run, and the deliverable-side
checker is where its absence is reported as NOT ATTEMPTED. Red line 9's hard
core — no client name in a tracked file — now has an instrument on the side
that lets the file in, not only on the side that ships it. Red run: a
synthetic tree with a declared term in `notes.md`, in
`tests/test_shadow_guards_audit.py`.

## 0.1.525 — one credential table, one strip-tags, and the guards that keep them single

Audit-remediation step 2 (`specs/2026-08-20-audit-remediation-design.md`).
Both changes are the `no shadow math` shape — a
shared implementation under `scripts/lib/` and a guard that refuses a private
copy — because a fix that edits the copies back into agreement is the drift
class this repository has fixed twenty-six times.

**The credential table is `scripts/lib/secret_patterns.py`, and nothing else
under `scripts/` may spell one.** `check_repo.SECRET_PATTERNS` had five shapes
and `check_privacy.CREDENTIALS` had eight, written four months apart, neither
a superset: a `github_pat_` token in a deliverable was caught by the repo
guard and missed by the deliverable checker, a Slack or Google key in a
tracked file the other way round. The refactor design had forbidden this by
name. The union is one table with nine shapes; both checkers import it; the
**`secret patterns parity`** guard fails a `re.compile(` anywhere else that
carries a credential marker (the markers are assembled at runtime so the
guard's own source does not trip it) and fails either importer that stops
importing. The repo guard reports one finding per line, because the merged
assignment shape overlaps the token shapes (`token = ghp_…` is both) and a
chatty scanner is a scanner people stop reading. Red run: a planted
`AKIA…` regex in a second file, and `check_privacy.py` with its import
removed — both in `tests/test_shadow_guards_audit.py`.

**Strip-tags is `markup.strip_tags` / `markup.visible_text`, and the
CJK-space rule is `markup.join_cjk`.** The audit counted four private
`re.sub(r"<[^>]+>", …)` copies; the **`no shadow markup`** guard, written
to report every occurrence rather than the first per file, found
**thirteen** across `check_design.py`, `check_prose.py`, `check_facts.py`,
`check_outline.py`, `check_privacy.py` and `judge_findings.py`, each a
little different (one lowercased, one collapsed whitespace, one resolved
entities, one joined with nothing). All thirteen now call the shared
helpers — `sep=""` exists for the two callers asking "is anything left at
all" — and the two CJK-space copies added at 0.1.523, each with a comment
pointing at the other, are one function. Fixture verdicts are unchanged
across the change (`check_fixtures` 13 runs, all as expected), which is the
evidence the copies were meant to be the same operation. Three scripts that
had never imported a sibling gained the canonical bootstrap block.

## 0.1.524 — three instruments corrected: the aspect probe, the phase clock, and a count that never reached the reader

Audit-remediation step 1 (`specs/2026-08-20-audit-remediation-plan.md`). Each
of the three was found by reading the code against the audit's measurements,
and one of the audit's readings was itself wrong — recorded below, because an
entry is what a later session believes (convention 14).

**The aspect probe held every landscape deck to the wrong shape.** `inspect_layout.py`
called `aspect_report(…, geometry)` after the geometry loop had finished, so
`geometry` was the loop's last value — `wide`, 1.8:1 — and every correct 16:9
page (1.778:1) read off-shape on every off-shape window: "23 of 23 measured
pages do not hold the declared wide shape", on all fifteen landscape
deliverables of the 0.1.521–0.1.522 campaign. `aspect_report`'s own docstring
records the first arrival of this bug (16:9 hard-coded; a portrait handbook
failing 30 of 30); this was the second, from the other direction, and it
reproduced the docstring's warning exactly: a report that reads as failure on
a correct document teaches its reader to skip the section. The target now
comes from `aspect_stage()` — the declared stage via
`deliverable_registry.STAGE_OF`, else the first matrix point run — and
`tests/test_inspect_layout_aspect.py` holds it without a browser. Red run:
`fixtures/deck-pass.en.html` read 18 of 18 off-shape before, 0 of 18 after.

**The phase clock rejects what it cannot store, instead of dying.** The audit
reported that `trace.py --phase` stored strings which `ledger.py` would sum
into a `TypeError`. **That reading was wrong**: `main()` already converted the
pair with `int()`. What was true is narrower and still a defect — `3.5` or
`twelve` ended in a traceback rather than a message, and `trace_schema`
typed the phase *name* and never its *value*, so a hand-edited string
validated. The parse now lives in `cmd_close` with a message, accepts
fractional seconds, and the schema types the value; three CLI-path tests were
planted red on the old code first (two of the three failed there, one for a
different reason than the audit named). The audit document has been corrected
at its three sites.

**An undeclared section count now reaches the verdict block.** D26 keyed its
verdict on *hidden* declarations only, so a pitch deck covering six of eleven
typical sections with nothing declared read `ok`, and `check_deliverable`
printed `0 graded findings` on the largest deck of the campaign — the whole
C5 mechanism (declare the gap, reader-visibly) was computed and then dropped.
**D31 · undeclared sections** is its own reported row, never gating (C5's
evidence stands; surfacing is the fix), and one scope note may now declare
several absences in one reader-visible sentence
(`data-omitted="team, vision"`). `deck-pass` declares its six synthetic
absences and reads ok; `deck-broken` carries the same absences undeclared and
fails — which is the first time this metric has been seen failing. The
matching stays what it was, a substring over visible text: C5's own warning
is that naming is almost never mandated, so a sharper matcher would be a
sharper wrong answer; the row is a prompt for a person, not a verdict.

## 0.1.523 — the checkers read Chinese in the mirror, a reserve is re-derived, and three marks are declined

**The first release of the audit-remediation branch** (design and plan:
`specs/2026-08-20-audit-remediation-design.md`). It ships the batch that had
been held on `main` uncommitted since 0.1.522, plus the asset intake the
manifests already described.

**The outline↔deck mirror gate and D27 now read Chinese.** A pure-CJK title
failed `check_outline.py --against` against *itself*: `_WORD` matched only
`[a-z0-9]+`, so a title with no Latin word and no digit had no content words
and the 60% overlap test had nothing to overlap. The zh build had been passing
this gate on its digits. CJK runs now contribute character bigrams, and a space
between two CJK characters (left behind by `<span>` stripping) is dropped in
both the mirror matcher and D27's agenda normaliser. **IDEA-14 is not closed by
this** — `is_label` still judges assertion with an English verb list.

**`check_facts.py` stops inventing quantities.** `$10.95 Meal` normalised to ten
million and `$9.00 back` to nine billion because the magnitude suffix had no
word boundary; a clock time left a bare `22`; a source filename's digits were
reported as an invented figure; and a dose (`150mg`) was invisible to all three
patterns. Each has a planted-red test in
`tests/test_fact_and_outline_defects.py` §7–§10.

**`.lede` reserves one title line, not two.** The prose above the rule said
"two title lines plus one support line" while the calc reserved two of each —
a drift inside the rule that exists to stop layout drift. Measured across a
22-page deck no title wraps (12-word ceiling, 34px face), so a full line was
reserved on every page and used on none: 43px per page recovered, and the
`+24px` term now accounts for `.lede`'s two 10px flex gaps. Fixtures
regenerated; one page is left tripping `reserve_overspent` on purpose because
tuning it away would delete the M8 overlong case it carries.

**Assets enter with their manifests.** 33 koboyo icons and three model marks
were on disk and described in `SOURCES.md` while absent from git — the shape of
0.1.504 again. They are added; the koboyo manifest's "twenty-two" was wrong
(the table is the count) and eight missing rows are filled in. **Three
owner-supplied raster marks are declined**: no source URL, no date, no usage
basis, which is the precondition the `.gitignore` exception for vendored
trademarks rests on. Their chips set the product name in type.

# Changelog

## 0.1.522 — the plan becomes an input, and a build is held to the facts it was built from

The owner's retrospective, in her words: the analysis and insight capability
does not take effect by itself, the intelligence has *serious inertia*,
information is forgotten or omitted between rounds, and McKinsey and YC have
been absorbed without the work getting better. All four are correct, and the
audit found a mechanism rather than a shortfall of effort.

**The analysis beat ran, and composition threw its output away.** The outline
for a shipped deck declares an analytical move, a written finding and a written
implication for **14 of 14** content sections — it is the best-executed artifact
in the chain. Then **0 of those 14 findings still described a page**. One
section's declared implication appeared in no element of the page at all.
Nothing in the pipeline carried `finding:` into `<h2 class="t">` or
`implication:` into `<p class="take">`, and nothing noticed the divergence —
though `references/analysis-rules.md` (AR-2) binds those rungs to those elements
precisely so the ladder is visible in the markup rather than a hope.

**A rebuild silently deleted eleven facts.** Measured across one rebuild: four
brand names, **five of the seven market names the deck still claims a count
of**, and two delivery figures. Every gate was green, because nothing compared a
build against the fact list it was built from.

**The package taught a stylesheet and the deck learned a stylesheet.** The
exemplar study's *typographic* devices landed by themselves — row labels 56
times, number-top stat blocks 11 of 11, captions 14 of 14. Its *analytical*
devices did not land at all: 0 benchmark lines, 0 unit lines, 1 scope flag
across 14 pages, 1 scorecard and it ungraded. Knowledge a stylesheet can carry
gets applied; knowledge needing a compositional judgement does not, because
there was no step at which that judgement was made and recorded.

The root cause is architectural and this repo had already half-written it:
0.1.516's spec says *"the form/content line, right about GATING, was
over-applied to GUIDANCE."* The correct policy **never gate on quality** —
earned honestly by the withdrawn 82% fill floor — was being executed as **do
not act on quality at build time**. So every absorbed body of knowledge went to
the one open slot, `references/` prose, which is inert by construction. Six
counts make it concrete: dozens of deliverable gates, as many reported
metrics, and every guard in `check_repo.CHECKS` — against one structural
generator, **zero content generators**, and
`assets/frameworks.json` validated by a guard and read by no runtime.

The answer is not more rules and not quality gates. It is to make the plan an
**input** to the build and then hold the artifact to its own declared plan.
Both are consistency checks of exactly the class D27 already applies to the
agenda, and neither asks whether anything is good.

- **`new_deck.py --outline <path>`** emits each content page pre-filled from the
  beat: the section's `finding:` as `<h2 class="t">`, its `implication:` as
  `<p class="take">`, `data-analysis="<move>"` on the section, and a placeholder
  comment naming the framework that move implies **and quoting its `misuse`
  line** — the first time `assets/frameworks.json` is read by anything at
  runtime rather than merely validated.
- **`check_outline.py --against <deck.html>`.** Every planned title must
  still be a page title — **gates**. Every planned implication is reported against
  that page's `.take`. When they diverge, the weaker artifact is corrected;
  a title sharpened during composition means the outline is stale, and a title
  that drifted off its finding means the page lost its analysis.
- **`check_facts.py <contract.md> <deck.html>`.** A quantity in the document
  that appears nowhere in the contract **gates** — an invented number is red
  line 1's territory. A permitted fact the document drops is **reported**,
  because dropping a fact is often right and sometimes is the eleven above.
  Deliberate-red first, per convention 15: run against the rebuild that lost
  them, it named all eleven before the code was trusted.
- `topic-label titles` **stops gating and becomes a note.** Its verb list is
  closed and English's is not; it failed five titles that were plainly sentences
  (*"Three things stand between us and the first contract, each dated"*) because
  `stand`, `buys`, `consume`, `price` and `leaving` were absent from it. Whether
  a title asserts something is a judgement about prose, and this repo does not
  gate on those. The list was widened anyway, and the overlap test gained a
  crude stemmer after it reported `hold` and `holding` as two different claims.
- **D8 exempts the agenda**, by owner directive: its title names the document
  and its rows name the parts, so a line between them restates one or the
  other. `references/storyline-templates.md` had already been changed to permit
  dropping that lede — one release before the checker was, which showed up as a
  permanently red row. That is how a reader learns to stop reading rows.
- Two maintenance conventions, each carrying the evidence that earned it:
  **17**, a rebuild inherits its predecessor's facts; **18**, state what *done*
  means for the reader before building, and report the build's grade against
  the package's own ladder rather than its gate results alone. Their source
  material is archived at `references/exemplars/karpathy-notes.md` as EX-4, for
  provenance only — **the archive is deliberately not the mechanism**, since
  this audit's central finding is that `references/exemplars/` is where
  knowledge goes to be inert.

- **The opener run line takes a `max-width` ceiling of 52ch.** Measured on a shipped
  opener, the section summary wrapped to **five lines** and stopped at half the
  available width, with the subject mark — which sits in its own grid column and
  never overlapped it — a long way clear to the right. The owner asked for three
  lines. 52ch is a **ceiling** (convention 4) and the comment says so: the copy
  is what shortens when a section still runs past three lines, and all three
  openers were shortened rather than the cap raised again.

**Six defects a review of this entry's own code found, each fixed with the red
planted first** (`tests/test_fact_and_outline_defects.py`, nine failing tests
before a line was changed). Every one of them got through because the test
written alongside the check assumed the same shape the check assumed — which is
convention 15's warning, met inside the release that added it.

- **`check_facts.py` failed correct documents.** Any two-digit run read as a
  quantity, so a roadmap year, a telephone number and a page-derived percentage
  all reported as invented figures. This is the worst shape a gate can have
  here: the author's cheapest route to green is to delete a correct year.
  A bare 1900–2099 integer is now a date, and a `+NN …` run is contact
  furniture. `$2027` and `2027%` are still claims.
- **It had no unmeasurable floor.** `dq` came back empty both when a document
  invented nothing and when everything it stated sat inside a stripped
  drawing — and both printed `ok`. A document whose every figure was drawn in
  an excluded `<svg>` graded clean while claiming markets, revenue and
  customers the contract had never heard of. `compare()` now strips the tags
  *without* the exclusions and reports **UNMEASURABLE** when that text carries
  quantities and the visible text carries none.
- **It was blind to bulleted fact lists and to every acronym.** A name had to
  appear preceded by a lowercase word or a comma — false for every entry in a
  `- ` list, which is the natural shape for a FACTS section, so such a contract
  yielded zero names and the report read `0 of 0 permitted facts`. Acronyms
  were excluded outright by `tok.isupper()`, and the measured defect this
  module exists for was **four platform names** dropped in a rebuild. `A2A` and
  `AP2` were additionally invisible to the proper-noun pattern, which required
  letters.
- **`deck_pages()` blamed the author for a parse failure.** The section regex
  required `class` before `id`, so `<section id="p4" class="page">` parsed to
  nothing and the report announced that the outline described a different
  document. Attributes are now read in either order, the cover/closing/opener
  test compares whitespace-delimited class **tokens** rather than substrings
  (`discovery` contained `cover`), and a document no page could be read from is
  **`not_measured`** — the tier this file introduced for exactly this and did
  not apply to its own new code.
- **The implication rung reported a denominator it never measured.** Titles with
  no page were skipped by the loop and counted in the total, so one report said
  `all 3 planned implications reached a takeaway` directly beneath a mirror
  finding naming a planned title that reached no page at all. It now counts
  what it checked and says how many it could not.
- **The entry above claimed a binding the code does not have.** It said every
  planned `finding:` must still be a page title; `drift()` compares the
  outline's bullet titles and never reads the `finding:` field. The gate is
  sound, the sentence was not. Corrected here and in `SKILL.md`. This is
  convention 14 — *do not write a claim about behaviour you have not read in
  the code* — broken in the release that added it. Also corrected: the rung
  binding is `references/analysis-rules.md` (AR-2), not `eval-rubric.md`; the
  guard count named its authority instead of a number that was wrong by eleven;
  a bullet describing a file this repository does not contain was removed.

- **A seventh, found by the same review: `inspect_layout.py` told consulting
  documents the opposite of rule 9.** Its `EXTERNAL_GENRES` — the genres that
  state provenance once for the document rather than under every figure —
  shipped as `("sales", "marketing", "consulting")`, borrowed whole from
  `check_design.py`'s constant of the same name. That one means *whose reader
  is outside the building* and decides who owes a quotable takeaway (D28);
  consulting belongs in it. Rule 9 says the reverse in terms: consulting and
  internal analysis **keep** per-page sourcing, because the reader is auditing
  the claim rather than being sold to. So a consulting deck that had dropped
  its per-page sources was told `n/a, a consulting document states its
  provenance once in the colophon`, and the branch skips `unmeasured += 1`, so
  the run stopped exiting 1 on a check it had not performed — the
  measured-versus-not distinction this package rebuilt at 0.1.350, lost again
  for one genre. The borrowed member is gone and
  `tests/test_provenance_genre_scope.py` pins **both** constants, because the
  tempting edit here is to make two same-named things agree. Note that
  `check_design.py`'s own comment warns against exactly this borrowing, one
  file away.

- **`check_evidence.py --init` keeps a diff base an earlier pass established.**
  It recomputed the base by finding the previous release's commit, and returned
  1 when there was none — which is the normal state when a branch carried two
  releases and they were folded into one commit at merge time. `release.py`
  aborted its step 3 on that, so the release could not be committed by the one
  tool that exists to refuse committing on a red preflight. The evidence file
  already named a valid base; it is now kept, with a note saying so. A release
  with no base *anywhere* still fails, and a test pins that direction too.

*One of these fixes was itself wrong first.* Matching the decorative-drawing
class as `(?:^|\s)` inside a prefix cannot match mid-string, so the globe's
`class="gl trade …"` stopped being excluded and the shipped deck went red with
eighteen coordinate figures. The repo's own token idiom
(`(?:[^"]*\s)?X(?:\s[^"]*)?`) was the fix. Running the check against the real
artifact caught it; the unit tests all passed.

The design record is `specs/2026-08-19-analysis-plan-binding-design.md`.

**Acceptance test, and the point of the release.** The rebuilt deck was run
through both new checks. The drift check found **six** planned titles that had
never reached the document and **two** genuine regressions where the finding had
been demoted into a support line; the fact check found the restored names. After
correction: 14 of 14 titles are the findings that produced them, 14 of 14 takes
carry their implication, and 0 unsourced quantities. The mechanism caught by
script what had previously taken five rounds of the owner's review to catch by
eye, which was the whole claim.

## 0.1.521 — the number goes first, and a seed pitch is looked at rather than read

**An owner review of two decks asked why a convention she had accepted did not
survive into the next document. The answer was that it had never been written
down anywhere the next document could read.** The deck that reached her standard
put its numbers on top at display size — `1 copy`, `12 platforms`, `190 lessons`
— twenty times across eight pages, and **all twenty were inline `style=`
attributes with no class on the number at all.** The package shipped no role, so
the author wrote the role twenty times. Their gloss used `class="sm"`, and the
only `.sm` rule in this package is `svg .sm`: every one of those sentences
silently took the body's 15px and no instrument could have said so.

**The shipped role did the opposite, and the package's own study said so.**
`.band` rendered `.k` above `.v` — label above number — for eleven releases,
while `references/exemplars/mckinsey-design-notes.md` EX-2 item 2 has read *"a
stat block is number-top: the figure first at display size, the explanation
under it in support ink"* the whole time. Prose right, stylesheet wrong, nothing
comparing the two. `.band > div` is now `column-reverse`, which is deliberate:
reversing it in CSS means every document already written renders the right way
round on its next build, where reordering the markup would have fixed new decks
and left every existing one wrong — the exact failure this release is about, so
it may not be the fix's shape as well. `.stats` / `.stat` / `.sv` / `.sn` ship
the tile itself, with `--fs-stat` and `--fs-support-sm` as declared tiers rather
than inherited accidents, and **`.stats` lives inside `.fill`, never as a
`.body >` child**, so it stays out of the four-site `:not()` chain. The rule is
stated once in `design-rules.md` §7 as an ORDER and not a size floor: number
above its label in a stat block, at the front of a title rather than spelled
into the middle of it, and on or above its mark inside a figure.

**A related emptiness turned up while measuring.** `.lead` — this package's
documented focal-number component, with `.lead .v`, its `.g` gloss and an `xl`
tier — **is used zero times in both accepted deliverables.** Both push their
numbers into 15-23 word titles instead. In the roadshow BP the cost is exact:
`0 signed customers` is the most important number in the deck and it sits in a
band below a title that spells the page's other quantities out in words. §3 now
says which way round the pair goes and names the apparatus that was waiting.

**A seed pitch is looked at while someone talks.** Owner directive: for a first
conversation with a seed investor, concepts and figures carry about 80% of a
content page. Template 11 gains the register without touching its eleven
sections, and the number is stated in the direction that decides what an author
does with it — **a floor on the drawing is a ceiling on the prose**, because read
as a target it produces an inflated figure instead of a cut paragraph. The
layout is part of the rule rather than a separate decision: the deck that
triggered this carried a captioned figure on **all thirteen** of its content
pages and still read text-heavy, because every page was a 50/50 `split`, which
measures **43%** once the lede and takeaway are counted. It cannot reach 80
however the words are trimmed. Template 11 also gains the figure vocabulary —
which relation each BP section actually has, and therefore which drawing answers
it — because a BP is where the pull toward a professional-looking diagram is
strongest.

**Two reported metrics, and one of them found its bug in the generator.**
`inspect_layout.py` keys the visual-share target on the STORYLINE where one is
declared (`pitch-deck` → 80), genre elsewhere, with the unknown-storyline branch
as loud as the unknown-genre branch already was. `check_prose.py` **M15** counts
the prose a content page asks a reader to read beside its drawing, excluding the
lede, the takeaway, the footer, the figure and the caption — the exclusions
matter, since a rule may not punish a page for obeying D8 or D28. It reports a
distribution and no threshold, on the withdrawn-fill-floor caution, and the
first measurement is the finding: **the accepted product deck sits at a median
of 60 words per page and the BP its owner called text-heavy at 130.**

**`check_design.py` D30** asserts caption numbers run 1..k, once each, in page
order. Planted first, per convention 15, and it went red on **every artifact
this package had on disk**: the accepted product deck numbered two drawings
`Figure 3` and had no Figure 4; the roadshow BP ran 2-8, then 12-14, then 9-11,
with no Figure 1; and the tracked fixture shipped six holes. The cause was not
three authors making the same slip — **it was the scaffold**, which emitted
`Figure {page index - 2}`, so every part opener consumed a number no drawing
ever carried. `new_deck.py` now counts figures. This is convention 15's point in
its cleanest form: reading the code would not have found it, because reading
uses the model that produced it; one `grep` at three real artifacts did.

**A second owner pass on the same release, and the first finding is against a
rule this release had just shipped.** §7 said "in a title the number goes at the
front", and the deck built from it opened **all fourteen** content titles on a
small operational count, with M11 title uniformity at **52.9% against a 60%
ceiling**. A placement rule had been read as a quota — convention 4's failure
mode inside a rule written to prevent it. It now says *where* a title carries a
number, and adds that a title with no number is a normal title.

**The cover was naming the stylesheet instead of the company.** The wordmark was
the literal string "LUMI Style" on a product business plan. It was never a
designed rule: two generators emitted it and a 2026-08-12 directive wrote prose
around the markup, and **`brands/registry.json` has carried a per-brand
`wordmark` field the whole time that nothing read.** The rule now says the cover
carries the product or subject the document is for, `new_deck.py` and
`build_fixtures.py` read the registry, and `--wordmark` covers a subject that is
not a registered brand. No check ever asserted the string, so nothing broke; the
blast radius was four prose surfaces.

**The agenda may now drop its lede**, because rows that already argue the deck do
not need a title saying they will. `body stack no-lede` centres them. The rule
states the trap rather than leaving it to be found: **remove the lede whole or not
at all** — deleting the title while keeping the block leaves a page reserving a
title it does not carry, which `inspect_layout.py` reports as NOT SHIPPABLE.

**§4 contradicted itself about source lines and had for releases.** Rule 9
exempted sales material from per-page provenance; rule 4 still demanded a line
under every figure with no genre qualifier, so a sales deck was told to state its
provenance once and to repeat it fourteen times. Rule 4 now carries rule 9's
scope. The trap is written down with it: **M2's window is the page and SVG is
stripped before it measures**, so a deck that drops every source line passes while
it has fewer than four percent-or-currency figures in HTML prose and collapses the
day it has more — the page keeps a marker in its own text regardless.

**The part opener may carry one oversized subject mark.** "No figure, no map, no
icon" was stated in three files, one MUST-tier, and the owner asked for the
exception; per `PRINCIPLES.md` §3 it was redrafted rather than adjudicated. The
redraft keeps what the rule was protecting (one statement per opener, no
navigation rail) and licenses a text-free silhouette reversed out of the field.
§6 gains the constraint that makes it work rather than repeat a recorded defect:
**a mark at display scale is filled, never stroked** — a hairline blown up is the
accident §6 already describes, and Lucide is stroked.

**A third owner pass, and the finding is about figures.** Fourteen content pages
were `body stack`, fourteen figures were 900 units wide, and every one was
rectangles and text: 1 to 9 rects, 13 to 35 texts, no plotted geometry anywhere.
**580 words of explanation were inside the drawings**, set at 12 to 15px in a
scaled SVG. The rebuild gives each page its own analytical form — a 2x2, a
proportional field, a funnel, a permission matrix, a convergence timeline, an
interval with analogy precedents, an area chart, a capability scorecard and a
generated world map — and moves the explanation into a left column at reading
size. Measured: **6 layouts where there was 1**, and M15's prose-beside-the-drawing
went 4 words to 57 because the words came out of the SVG and into the page.

**§4 rule 15 was wrong, and it was one release old.** It said "a document's
figures share one viewBox width". Its evidence was miscounted (the deck it cited
runs 640, 660 and 680) and its effect was backwards: 660 units render at 1.0
px/unit in a 652px cell and 1.66 in a 1096px one, so with varied layouts one
declared size becomes two rendered sizes. It now says the viewBox width is chosen
to MATCH THE CELL, so a `font-size` inside a drawing is literal. **15b** adds the
ladder that was missing entirely — row and section names at 17px bold
(`svg .row-lbl`, EX-2 item 5), values at `.mid` or `.huge`, fine print at `.lbl`
— because "a type scale that suits the figure" was the only guidance and it
produced fourteen drawings whose largest heading was 13px.

**`.stats.col`, and why it is not a metric being gamed.** A stat row is
content-height, so a left rail written as one measured 59% of its page while
visibly occupying the whole column; the numerator reads element boxes. The
column form distributes the stats down the cell they are actually in, which is
what the eye already saw. The alternative — leaving it and arguing with the
number — is how a page ends up designed against its own measurement.

**The map is generated, not drawn.** `regionmap_svg.py` with a four-region
registry of the market phases, a scoped palette from `build_region_palette.py`
(`--prefix phasemap`, so it cannot touch the cover globe's hues), and the three
contrast floors asserted at generation: worst label 5.42:1, worst stroke 5.78:1,
worst adjacent ΔE00 54.7. The first attempt used the SHIPPED registry and was
wrong in a way worth recording — eleven regions each took their own identity
hue, so a four-phase sequence read as five unrelated colours. Region hue encodes
identity by directive; a phase story needs a registry whose regions ARE the
phases.

**All five ecosystem marks now ship, and two of them carry a recorded
transformation.** Google, Meta, Reddit and X are official vectors from their
owners' own domains; **X publishes only the white variant**, so the fill is set
to its own black one, which is choosing between the owner's two monochrome
variants rather than tinting into this palette. **Microsoft publishes no public
vector at all** — the CMS endpoint 403s and every SVG path 404s — so its mark
ships as the 216x46 raster its own UHF service serves, embedded as a `data:`
URI. It is the first image any deliverable from this package has carried, which
is why the colophon now names its terms: D25 gates on that and passed only
because the sentence was added with the mark.

**Three defects the marks exposed, all in this package rather than in the
markup.** `.gitignore` excluded `*.png` globally, so a vendored trademark would
have been one `git add -f` away from existing — caught by the `assets tracked`
guard, and un-ignored scoped to `assets/logos/` because the blanket rule exists
to stop an engagement screenshot, and that reason does not reach a mark whose
provenance is recorded beside it. **D4's token-block detection knew two selector
names**, `:root` and `.trade`, so a scoped region palette generated on
`.phasemap` reported 26 of its own generated hexes as stray literals — the
identical failure its own comment records about `.trade`, one release later and
by the same cause. It now decides by SHAPE: a block that declares only custom
properties is a token block, whatever `--prefix` produced it. And
**`figure_clipped` measured `<symbol>` elements**: the Reddit lockup carries one
whose bbox sits 162 units outside the wrapper's viewBox, and the probe read that
as a fifth of the drawing clipped away on a page where nothing was clipped. A
definition does not render where it is written, so `<defs>`, `<symbol>`,
`<marker>`, `<clipPath>`, `<mask>` and `<pattern>` are now skipped. All three
were found by putting real vendored markup in front of checks that had never
met any.

**Three protocol marks ship** — MCP, A2A and AP2, official vectors from each
protocol's own repository, inlined with `data-mark`. A2UI and UCP publish raster
avatars only and stay in type, recorded in `assets/logos/SOURCES.md` beside the
brands that could not be verified last release.

**Two probes were wrong, and the rule change is what exposed them.**
`figure_clipped` walked every descendant of a figure and compared `getBBox()` to
the outer viewBox — but a nested `<svg>` starts its own coordinate system, so an
official trademark inlined at 39x13 inside a 900-unit drawing measured as 988
units wide and the gate fired on correct markup. It now compares rendered rects
for a nested mark and skips what that mark's own `<svg>` already measures. The
markup that exposed it is markup the rules had just been widened to permit, which
is the shape worth noticing: **a permission that no artifact had exercised was
being enforced against by a probe nobody had run it past.** And the source-echo
probe reported NOT MEASURED on a sales deck that had correctly dropped its
per-figure source lines — it exists to catch provenance stated *twice*, so with
the rule obeyed there is one statement and nothing to compare. It now says n/a
with that reason for external genres instead of counting itself unmeasured.

**Template 11 gains a stage axis.** The owner's directive — at seed the data is
not the point, the market and the narrative are — collides head-on with "evidence
before vision is the arc's one inviolable ordering", which the same owner adopted
from the YC study at 0.1.518. Both are right about different stages: at seed there
is no traction to put first, so demanding it demands it of nothing. Vision leads
at seed and pre-A and the evidence changes job, from *this already earns* to *we
can build what we say*; from Series A the original ordering is unchanged. Red
line 1 and the ban list bind both, and an unbounded market is drawn the way the
study already permits — **analogy companies, never a top-down TAM.**

The design record is
`specs/2026-08-19-number-first-and-seed-pitch-register-design.md`, including the
two decisions taken AGAINST the plan: `--fs-stat` does not go in
`design-tokens.json`, because parity between the two token files is palette-only
and every other size tier is CSS-only, and M15 is n/a on Chinese rather than
reporting a number the word splitter cannot produce.

The `probe vocabulary` guard earned its keep mid-change, refusing the release
until `inspect_layout.py`'s `VIS` list learned `.stats` alongside
`check_design.py`'s `VISUAL_BLOCKS` — one metric, two carriers, caught by the
guard that exists for exactly that.

## 0.1.520 — three defects the checks were not measuring

**A deliverable came back from its owner with three findings, and every
instrument this package runs had reported clean on it.** That is the shape this
release is about: the instruments were working and were measuring the wrong
layer. Each finding is written up as a mode with its measurement, because the
measurement is what makes it detectable next time.

**FM-18 · the input language captures the output language.** The output
language was inferred from the source material (three Chinese documents), the
venue and the audience, and shipped as Chinese one day after the same owner
had explicitly chosen English for the previous deliverable of the same kind.
The language decision had been named in a plan and the plan had been approved,
which is not the same as being asked for. Output language now sits beside
geometry as the question worth a round trip, with the rule stated in the
direction the failure took: **evidence about the reader is not an instruction,
and a language this user chose for a comparable deliverable outranks every
inference from the material.** Re-flowed into all three entry points.

**FM-19 · inherited sentences carry inherited register, and the copy metric
does not see it.** Asked whether the deck was a copy of the draft it was built
from, the honest answer needed measurement rather than memory: 0 of 96
sentences matched verbatim, and 9 of 15 page titles carried an 8-character or
longer fragment of the source, with 10 of 15 signature phrases intact. The
skin was rewritten; the spine was lifted. **OR-7 is the rule that follows: a
source document contributes facts and constraints, never sentences, titles or
the order of the argument.** In practice the part authors are handed an
extracted fact list and never the prior document, and a re-derived title that
lands exactly where the source already was is evidence that no analytical move
was applied.

**The de-AI pass now leaves an artifact, and the register rule gained its
document-level form.** §6's item 12 forbade a manufactured punchline; the
build that triggered this release ended all thirteen of its content pages on
one, which no metric counts. **12b makes the distribution the test**: vary
what a closing line does, and more than half of them being short and quotable
is itself the tell. The pass also ends in a findings file run through
`judge_findings.py`, which accepts a finding only when it quotes what it
objects to, because a pass that leaves nothing behind cannot be told from one
that was skipped. This bites hardest in Chinese, where M8 correctly reads n/a
(0.1.519) and the register is therefore unmeasured by construction.

The rebuilt deliverable is the evidence that the three rules are executable:
titles re-derived from the fact list by the five moves, an English build, four
independent register jobs across its closing lines, four judge findings raised
with quotations and all four applied, and a check stack that ended on
`every instrument spoke, and nothing failed` before a person looked at the
contact sheet and found two more things no instrument had (a footer numbered
from the scaffold's page order, two figure labels crossing a plotted line).


## 0.1.519 — the launch-sequence agenda, and the checkers learn to read Chinese

**The first real Chinese deliverable was the deliberate-red run for five
checker blind spots at once.** A competition roadshow deck built on real
engineering data — Chinese output, sales genre, public audience — fired every
one of these before any fix was written, which is convention 15's order
executed on a real artifact rather than a fixture. Four are fixed in this
release; the fifth is IDEA-14. Every fix shipped with unit tests written red
first against the unmodified code.

- **Title frames now read full-width punctuation.** `title_frame` counted a
  full-width ：title as "plain", so thirteen genuinely varied zh titles
  collapsed into one frame and M11 failed at 81% on a deck whose frames
  varied. Full-width ？now reads as the question frame too.
- **M8 reads n/a on a Chinese document.** Its splitter measures English word
  counts; on zh prose it measured the stray Latin fragments and failed the
  deck at CV 0.23 on a sample of digits and product names. The module's own
  design note had said "M8 stays n/a for Chinese" since the language gate
  shipped; the emission now agrees with it, and the rubric's "never skipped"
  claim is amended to say exactly what is and is not skipped.
- **The source-marker vocabulary gains its zh half**: `来源` · `出处` · `示意` ·
  `实测`, matched without word boundaries because CJK compounds have none —
  a page carrying `来源：Momentum Works` on every figure was counted unsourced.
  `writing-rules.md` §4 rule 6 and `SOURCE_MARKERS` updated together; the
  parity guard held them to each other through the change.
- **D12's handling-terms vocabulary was English-and-confidential only.** A
  public zh roadshow deck carrying honest terms (`公开路演版 · 引用请注明出处`)
  failed all nineteen pages; the vocabulary now carries the zh handling forms
  (`保密` · `内部使用` · `请勿转发` · `请勿外传` · `公开路演` · `引用请注明出处`).

**Template 11's first real build produced the agenda the skill now ships.**
An owner review read the grades agenda as too quiet for a deck that opens a
pitch; the launch sequence — a numbered dark chip per part, the part's claim
at title weight quoting its opener, a quiet run line — was piloted on the
roadshow deck and accepted. It is now the scaffold's agenda
(`new_deck.py`), a tokens pattern (`.launch`, with the lime chip carrying its
own `--on-lime` backing in the same rule, which is D13's sanctioned pairing —
the first cut used the text ink as the chip and D13 caught it on the
regenerated fixtures), and a sentence in the agenda discipline
(`storyline-templates.md`). D27 needs no change: the claim lines carry `.gn`,
which it already reads wherever the stylesheet defines them, and the
storyline checklist still seeds the scaffold's run lines.

Deferred, each with its ledger id: the outline gate cannot read assertion in
a Chinese title (IDEA-14, worked around with Arabic digits on the real
build — compliance with the instrument, noted as such); short Latin privacy
terms false-positive on embedded base64 (IDEA-15). Re-flowed into all three
entry points; fixtures and the eval inventory regenerated.


## 0.1.518 — the investor pitch: YC's argument shape joins the storyline roster

**By owner directive (2026-08-18): the package needed a roadshow BP
capability, and it is imported the way the consulting standards were —
studied at source, written up as an exemplar, then bound into the
vocabulary.** The study is `references/exemplars/yc-pitch-notes.md` (EX-3):
original analysis of Y Combinator's three published fundraising-deck guides
(the Series A pitch guide, the seed deck template, the deck-design essay),
read in full together with the twenty-two template slides embedded in them —
the owner's instruction was to learn the slides, not just the prose, and the
slide-level grammar (the title as the claim sentence with its number in it;
chart left, hero bullets right; the market as a labeled arithmetic band; the
mirrored problem/solution pair) is in the notes with the deck each device was
seen in.

**Template 11 · Investor pitch, storyline `pitch-deck`.** The owner's stated
core requirement — a BP lives or dies on the whole deck's narrative logic,
one complete story about a future business, not per-page quality — is YC's
own vertebrae method, and the template binds it as the build order: the
10–15 page titles are written and agreed as one argument before any page
exists, which is red line 4 and the storyline review beat bound hardest.
The arc runs one-liner → traction teaser → problem → solution → traction in
depth → market → competition → vision → team → ask → appendix, with two
boundary rules: evidence before vision is the one inviolable ordering, and
the YC floor is not the LUMI ceiling — the study's bare-bones design advice
is a clarity floor and LUMI's composition rules still bind every page.
**It is a storyline, not a genre** (the Template 5 precedent): a BP is
external sales material, so the `sales` tier binds, and the registry change
is one tuple entry plus a `TYPICAL_SECTIONS` checklist — every guard, the
outline gate, the trace schema and the scaffold derive from the tuple.
Named `pitch-deck`, not `pitch`: the two-axis tests use `pitch` as their
canonical *unknown*-genre sentinel, and a storyline of that name would have
inverted the test silently.

**`market-sizing` joins frameworks.json** (decompose, drawn native): the
bottoms-up equation — prospective customers × value per customer, from the
business's own numbers, the arithmetic printed as a labeled band. The named
misuse is the top-down report figure pasted as a market. Use-of-funds needed
no entry; the existing `waterfall` is its shape.

**Numbers discipline, BP-flavoured, stated where it binds** (Template 11 and
EX-3, not new metrics): traction states trends, not points — four to six
months of monthly or quarterly history as the floor of believability;
cumulative-only and double-axis charts banned by name; every number defines
what it measures; a scaffold built on illustrative data says so on its title
page, which is YC's own practice and red line 1 doing its ordinary work.

Re-flowed into all three entry points and README; the stale storyline counts
those restatements carried ("four narrative skeletons", "all four
scenarios", "none of the four genres") are deleted rather than incremented,
per convention 13. Deferred: the unguarded `EXTERNAL_GENRES` tuple found
while mapping the genre vocabulary is IDEA-13. No new gate ships in this
release, so no deliberate-red run is owed; the roster row and tuple are held
together by the existing storyline-vocabulary guard and its synthetic-tree
tests.


## 0.1.517 — two pages reached the owner's standard, and the path is now the rule

**The benchmark-anchored review's first full cycle converged where two
blind-sheet cycles had not.** One page — the product deck's evidence page —
was iterated six versions against a named reference page until the owner's
verdict was "this page is basically there"; a second page in a NEW scenario
(a market-analysis competitive landscape, consulting register, the position
move, the 2x2 under its dictionary contract, real sourced market data
including a competitor's real exit) passed on its first review. The
protocol's design held: a page had a standard to clear, not a defect list
to empty, and what changed between versions is what this release writes
down.

**AR-5 · the reader-outcome rule.** In the external genres an internal
metric appears on a page only as the driver of a reader outcome, with the
link evidenced — a named published source or this package's own
measurement. The calibration's turning point was the owner asking, of a
page presenting three instrument readings as achievements, *why would this
make anything better for the user?* Two clauses ride on the rule: the
**jargon test** (a metric label the target reader must ask about has
failed — the `heaviest layout, %` precedent), and **a judgement declares
itself where it is drawn** (a positioning figure prints its assessment
basis inside the figure, because the consulting register allows judgement
and forbids judgement dressed as measurement).

**The debunked-statistics ban.** Writing-rules' number discipline now names
the two presentation-folklore numbers that nearly reached a page and fail
verification — the 43% persuasion figure (its own 1986 working paper does
not support it) and the 60,000× image-speed claim (no source has ever been
produced) — and states the cost: a debunked number makes the one reader who
knows discount every honest number beside it. The sturdier findings that
survived the same check (the 10-against-65 recall pair, Mayer's controlled
comparisons) are the ones the accepted page cites.

**EX-2 · the calibration codicil.** Five devices validated on our own
accepted pages join the exemplar standard: one benchmark line through every
measure (normalised attainment, not three charts with three targets);
number-top stat blocks with colour spent by importance; captions of a
number and a name; reader-outcome lanes (AR-5 drawn as driver → named
evidence → gain); row labels at title weight.

**The reader-outcome layer, reported.** Eval-rubric now tables what each
machine proxy stands in for (comprehension, retention, attention, novelty,
efficiency, actionability) and the honest future measurement of each; each
benchmark review carrying the two-question comprehension check accumulates
one row of the dose-response data the proxies cannot honestly claim today.
Nothing in the layer gates: a gate on an unmeasured outcome would be a
fabricated number with a threshold.

Re-flowed into all three entry points. The two accepted pages stay outside
the repository with the other deliverable sources; the codicil records the
devices, not the files.


## 0.1.516 — the analysis engine: the generation side the package never had

**The owner's verdict on r12 (`变化不大`) triggered a root-cause investigation
instead of a third rebuild, and the finding closed the case on two blind
reviews' worth of non-convergence: the positioning promised consultant-grade
documents and the machinery only ever verified the absence of defects.** Four
root causes, each now on record in `specs/2026-08-18-analysis-engine-design.md`:
output quality was never in the refactor's problem statement (the word
"insight" appears zero times in the v3 plan); the research filed the entire
analytical toolkit — SWOT, 2x2, value chain, issue tree — under chart grammar,
so the library can draw an issue tree and nothing could build one (the
framework names appeared zero times in this repository until this release);
the form/content line, right about gating, was over-applied to guidance, so
five value dimensions scored post-hoc what no workflow step produced; and
design quality was never researched, defined, or measured. This release ships
the generation side. The blind-sheet loop's non-convergence was the symptom:
a dashboard was being tuned on a car with no engine.

**The five analytical moves, and the beat that runs them.** New rule family
`references/analysis-rules.md` (AR-1..4): compare, decompose, position,
correlate, bridge — each with its input shape, its finding form, and its
tell when missing; the insight ladder (finding → implication → action) bound
to page elements (title → `.take` → the ask); and a new ANALYSIS BEAT
between storyline and writing whose product is one declaration per content
section: `analysis: <move> | finding: … | implication: …`. The ghost-deck
storyboard lives in the same beat. `check_outline.py` now reports
declaration coverage and FAILS a move outside the five (vocabulary, not
content — the form/content line holds; red run: `vibes` rejected, coverage
"1 of 2" reported). Content itself is never gated; whether a declared
analysis is real goes to the benchmark review.

**The framework dictionary.** `assets/frameworks.json`: ten entries (SWOT,
2x2, nine-box, issue tree, driver tree, value chain, funnel, waterfall,
Harvey scorecard, three horizons), each carrying the analytical question it
answers, the slots, the misuse line that names how it becomes decoration,
and the library shape ids that draw it — the 206-unit library's analytical
heritage (the 2x2 boards, the 3x3 grids, the driver trees) is queryable for
the first time. Design-rules gains DR-16, the selection chain: **question →
framework → shape**, one step upstream of §4.1's relation rule. A new
`frameworks` repo guard holds every binding to the library and every entry
to usability (missing misuse line, unknown move, unusable entry all fail;
planted red first, four failure shapes, then six synthetic-tree tests).
Deliberately NO second copy of the binding in `tags.json` — a reverse lookup
beats a mirrored axis in the repository whose dominant defect is the
hand-written second copy.

**Register profiles: the audience decides the language.** Writing-rules
WR-9: one underlying fact rendered four ways — buyer economics for
sales/marketing, the operator's imperative procedure for training and
manuals, judgement-with-confidence for consulting, hypothesis-and-hedge for
internal analysis. The genre axis previously changed punctuation and visual
share and never diction; the owner's review said it plainly: market material
argues in the market's language.

**Templates 7–10, from research already paid for.** The four skeletonless
storylines (market-analysis with the TAM/SAM/SOM double-count, GTM's six
decisions, the status report's eight elements with an ask per risk, due
diligence with the red-flag matrix) were fully documented in the 2026-08
consulting-standards research and then sat in a backlog for four releases.
They are now Templates 7–10; `TYPICAL_SECTIONS` aligned; IDEA-10 closed by
owner decision, with the deviation from its one-at-a-time close condition
recorded in the ledger entry itself.

**A falsified practice, shipped anyway, now fixed.** The research record
falsified "batch every question into one round" as an evidence-free
invention and adopted segmented follow-up (roughly twice the core detail
recovered, experimental, N=80); the refactor plan took the finding; the
shipped SKILL.md said the opposite for six releases. All four restatements
now teach segmented questioning grouped by the user's own topics, and
operating-rules §3 records the transit loss — found only because an owner
review forced an audit that compared the repo against the research, which
no guard does.

**The acceptance changes: benchmark-anchored review.** The blind sheet
remains the record and stops being the primary acceptance (two full cycles
on one deck did not converge — a defect list cannot say what better looks
like). Eval-rubric now names the comparative protocol: side-by-side against
a named reference page, owner verdict better/worse/why per page; ONE page
calibrates to the owner's standard before any full rebuild; and review
evidence answers with an artifact, never a tick (the misreport spread
between judgement items and object-leaving items is about fivefold). The
customer-facing positioning sentence now lives in one fenced README block,
quoted never rewritten, per the refactor's own single-source design.


## 0.1.515 — a trademark mark keeps its owner's colours, and declares itself to say so

The r12 rebuild put four official platform marks on the get-started page
(0.1.514's shop-window spec) and D4 flagged their seven hexes — a true
conflict between two written rules, not a false positive: the palette-literal
scan exists so no author smuggles in a colour, and the marks rule exists
because recolouring a trademark falsifies it while redrawing it in tokens
fabricates one. Resolution, declared rather than inferred: an `<svg>`
carrying **`data-mark`** is excised from D4's literal scan; an undeclared
logo's hexes still fail. Deliberate red first: the same hex fails undeclared
and passes declared, in `tests/test_check_design_units.py`. Rule prose in
design-rules §1 beside the palette contract it excepts. The build that hit
this is the documented case, one command away from being re-hit by anyone
following 0.1.514's get-started spec — which is why it ships now rather than
waiting for a second document.


## 0.1.514 — the second blind review: the parts were all present, and the arc still was not

**The engine's second cycle, on the revised deck (corpus D16), and the row
that locates the blind spot.** The owner blind-scored the r11 revision:
reader C1=1, C2 unreadable-because-of-C1, C3=3, C4 unscored, C5=3, C6 marked
**0** (below the scale — recorded as 1, whose anchor text is her own verdict
that an external document failing at its job `就是失败，不是扣一分`; the raw
marking is preserved here verbatim), C7=3, C8=1, beside the builder's sealed
4/3/3/4/3/3/3/3. C5 moved 1→3 — the pages Template 6 demanded landed. C1
moved 2→**1**: the revision that added every named part scored *lower* on
first impression, which is the datum this whole entry hangs on. And this
time the agreement study could say precisely where the machines were blind:
its C3 proxies and the reader agreed at 3, while **no metric even claimed to
predict C1, C6 or C8** — narrative, takeaway, figure insight. Instruments
now exist for all three, each run red on the reviewed deck itself before it
was trusted.

**The root cause is one thing, recorded as FM-17 · the builder's-eye
narrative.** Eight findings, one shape: the deck walks the *mechanism* in the
maker's order, and the reviewer asked for the consultant's arc —
`是什么 → 为什么（痛点）→ 怎么做 → 对企业的核心价值`. Patch-fixing D15's named
gaps satisfied every part and left the arc unbuilt; that move is now FM-17's
second detection tell. Template 6 is rewritten to the arc (her design, taken
as the template), and `TYPICAL_SECTIONS["product-intro"]` follows it.

**Her opening finding becomes a gate.** The r11 agenda's part titles matched
no opener and its items matched no page title — the author had told the story
twice in different words. New deck-wide discipline: the agenda quotes the
document, derived from the page titles at assembly; **D27_agenda_mirror
gates** (normalized containment, so a row may carry its part letter). Planted
red first: 12 orphan lines on the reviewed deck, then a permanent red case in
the degenerate fixture — 44 of 44 graded verdicts now have a failing fixture.
"No agenda page" is a measured pass, not an n/a, so the blind-gates rule
stays about instruments that could not look.

**Two reported instruments for the other two blind dimensions.** Every
external content page now closes with one quotable **`.take`** line (new
token role, a tier below the callout so D3's budget is untouched);
**D28_takeaway** reports coverage — the reviewed deck read 10 of 10 content
pages without one, beside her C6 note that the deck read as `无感`. And the
page's numbers go into the figure's geometry (design-rules §4.2):
**D29_figure_numbers** reports every figure page whose SVG text carries none
of the page's own stated values — the value-match matters, because the
reviewed staircase carried step digits 1–6 on a page claiming 206 units, and
digit-presence would have passed it. Both start reported on the new-gate
caution; both are candidates to gate after r12 measures them on a real build.

**One new AI tell, from her quotation.** "Worth your attention if… / Worth
your attention before…" — the templated parallel frame, sibling blocks of one
role differing only in the slot. Writing-rules §6 move 15 names it;
**M14_parallel_frames** reports same-role siblings sharing a three-word
opening (the reviewed deck read exactly one echo: hers). Reported, never
gating — deliberate anaphora is rhetoric, and M13's reason applies verbatim.

**The get-started page gets its shop-window spec, and the assets to honour
it.** Official platform marks ship in `assets/logos/` (Claude, Cursor,
Gemini, GitHub — fetched from each owner's own domain, provenance and the
not-shipped list in SOURCES.md; OpenAI serves 403 to fetchers, DeepSeek and
Kimi publish no vector, and those get typographic chips — never a redrawn
imitation). Trademark marks keep their own colours; §9's tinting rule scopes
to imagery. C1/C6/C8 anchor examples carry this review's real shapes, and the
C4-unscored/C2-unreadable dimensions are stored as null per the validator's
own rule.


## 0.1.513 — the first blind review: five dimensions diverge, and the divergence splits exactly where the machines stop

**The evaluation engine's first real cycle, run end to end.** The owner
blind-scored the product-intro deck (corpus D15) against the C1–C8 sheet:
reader 2/3/2/3/1/1/3/1 beside the builder's sealed 4/4/4/4/4/4/4/3 — **five
dimensions diverged ≥2**, each one forcing this retrospective. The record is
the store's first schema-3 row, and the agreement study produced its first
real finding in one sentence: *the machine cleared its bars (visual share 54.5
against a floor of 50) and the reader judged something no metric sees.*

**The divergence is not noise; it has a shape.** Sort the dimensions by what
they measure and the split is clean: on defect-absence (finish, sourcing,
title mechanics) reader and builder sat one point apart; on value-presence
(answer-first, page depth, completeness-for-purpose, actionability, figure
argument) they sat two to three apart, every time in the same direction. The
gates are all defect-shaped. The deck was built through ten rounds of
gate-fixing and zero rounds of value review, and the self-score inherited the
instruments' blindness. Recorded as **FM-16 · gate-clean, value-thin**.

**The sharpest single datum**: the builder's sealed C6 note said the ask
"names no owner or date" — the exact defect the reviewer named — and priced it
at minus one. The reviewer priced it as the document failing at an external
document's job, and scored 1. So the protocol gains **3c**: a value dimension
where the document fails at its job caps the self-score at 2, seen or not.
The sheet's C3/C6/C8 anchor examples now carry this review's real shapes.

**Template 6 · product-intro, written from the document that lacked it.** The
reader's 1 on completeness and 1 on actionability were the documented case
IDEA-10's entry was waiting for: the deck was derived from a five-word
checklist, satisfied each word, and skipped the substance — no overview page a
reader could carry away, no get-started page with the four artifacts (link,
per-tier install, first command, feedback channel), an ask naming nobody and
no date. The skeleton now states all of it, 5W+1H first, and
`TYPICAL_SECTIONS` grows `overview` and `get started`. Four storylines remain
skeletonless, one at a time by design.

**Two rules from the review's own words.** Number discipline rule 0: in
external genres a key number carries its judgment anchor — the deck said "181
releases came from this loop" and the reviewer asked *is that Wow, or bad, or
nothing?*, which is the whole rule in one question. And agenda rows state
value, not contents — a row reading "the ban list, the rule set, the gates:
pages 4 to 7" is a table of contents wearing an agenda's clothes.

**The chronic defect had a broken instrument behind it.** The reviewer called
long figure captions "your chronic defect" (`你有一个通病`, her words as data). The
caption-wrap probe existed — and measured `.cap .n`, the two-word "Figure 5"
span, which cannot wrap: it printed "all figure names hold one line" on every
document ever run. It measures the NAME now, via a Range between the number
and the source line, and the reviewed deck immediately reads **2 of 7 captions
wrapped** where it read zero. The driver surfaces the finding into its one
block — where the first version read a nonexistent top level and its own
planted red caught it — so the defect reaches the eye every round instead of
living in report prose nobody grepped for.

**Loose ends closed in the same pass**: `trace.py annotate` writes the two
link fields nothing could write (`corpus_id`, `review_ref` — addresses, never
verdicts); `debug_log.py` scores C1–C8 after saying H1–H6 for forty-odd
releases; the protocol's "six self-scores" stale count is gone; the noun-pile
enumeration tell is parked as IDEA-12 under the two-document promotion rule,
with the reviewer's two examples as anchors.

## 0.1.512 — the genre's contract rides in the scaffold, and one rule stops having three genre sets

Release 3 of the ten-round autopsy, closing the cause the first two could not:
constraints that existed, were enforced, and were knowable before the first
word — discoverable only by failing them, because each lived inside the
checker that fires on it.

**The scaffold now emits the contract.** `new_deck.py` writes a comment block
straight after `<body>`: the genre's dash policy, the five title frames M11
counts, the nine provenance words D6 accepts, the figure-ink rule for quoted
tells, the pointer at the scaffold's own pages as the role reference, and the
one command that runs the whole gate stack. **Every value is imported from the
checker that enforces it** — the tests assert identity with `DASH_BANNED`,
`TITLE_FRAMES` and `D6_PROVENANCE`, not resemblance, because a card that
retyped them would be the twenty-seventh copy-drift fix waiting to happen. And
the card is proven harmless to its own carrier: a test runs the prose checker
over the scaffold and asserts the card's quoted dashes and phrases fire
nothing.

**Two vocabularies stop being code-only.** M11's frame taxonomy lived inside a
closure in `measure()` — an author varying their titles had no way to learn
what counted as "one frame" short of reading the function. It is
`TITLE_FRAMES` at module level now, named in eval-rubric's M11 row and in
storyline-templates' vary-the-frame passage. D6's provenance regex becomes
`D6_PROVENANCE`, stated in design-rules beside the obligation it serves, under
the same sentence writing-rules already gives the M2/M6 markers: the list is
the contract.

**One rule, three genre sets, resolved.** Writing-rules said the dash ban
covers sales/marketing/training; eval-rubric said sales/marketing; the checker
enforced four genres including consulting, and its comment recorded the
conflict instead of resolving it. All three now state the same fact — every
genre but internal analysis — and the prose names what it failed to say for
fifty releases. The letter-digit range trap (a C1-to-C8 style span is not the
digit-digit data exemption) is written where an author meets it.

**And the figure-ink rule is a rule now.** The checkers strip `<svg>` before
measuring, on purpose — text drawn inside a figure is the figure's ink. That
load-bearing behaviour was documented nowhere: the A4 handbook's ban-list
figure passed on it, and a product deck quoted three filler phrases in a swap
block and failed on all three until they moved into the drawing. Writing-rules
§2 states it, with both cases.

## 0.1.511 — the sentence splitter stops reading a source-line wrap as a full stop, and the 0.50 floor survives the honest instrument

Release 2 of the ten-round autopsy, built in a parallel worktree.

**M8 was measuring source lines, not sentences.** The extractor collapsed
spaces and tabs but left newlines standing, and the splitter treated `\n` as a
boundary — so a 45-word sentence soft-wrapped across three source lines inside
one `<p>` counted as three short fragments, and an author who wanted a long
sentence measured honestly had to keep it on one physical line. That is
compliance with the instrument rather than with the rule, and it cost two of
the ten rounds. Block boundaries now do all the separating: the `.` injected
at `</p>`/`</li>` in HTML, the blank line and list item given the same
treatment in markdown, and every remaining newline is editor formatting that
becomes a space. The block windows M2 and M6 read are flattened the same way,
so "its block" stops meaning "its source line" there too.

**The 0.50 floor was recalibrated, not presumed.** Old and new splitters ran
side by side over the three fixtures and four rebuilt deliverables: every real
document ROSE — 0.639 to 0.854, from 0.593 to 0.711 — because un-chopping the
fragments restores the long tail the old instrument was amputating, and the
degenerate fixture fell to 0.332. The separation the floor relies on widened
from 0.246 to 0.307, so the number stands and only its cited measurements
moved. Deliberate red, planted first: the wrapped 45-word sentence read
`[15, 15, 15]` and the wrapped markdown paragraph `[7, 7]` before the fix,
beside the invariant — proven on both sides of the change — that two `<p>`
blocks stay two sentences. No fixture verdict flipped; M8 stays graded, never
gating.

## 0.1.510 — every pre-delivery instrument in one command, after a ten-round build was autopsied

**The case is measured, not felt.** A fifteen-page product deck took ten
build-check-fix rounds. The autopsy attributed at least three of them to
nothing but partial reading — the author assembled the gate stack by hand,
filtered each tool's output through grep and tail to protect their own
context, and so met failures in installments: four findings present in the
first report were discovered in the third round, and a role failure present in
the seventh round's output was discovered in the ninth. One more round came
from running the slow rendered check serially, only after the text checks were
clean. The historical lineages are worse — one proposal carries twenty-three
run numbers under the same workflow.

**`check_deliverable.py` is the structural answer.** One command launches the
rendered check first — the browser renders while the text instruments run —
executes prose, design, privacy and layout, and ends in ONE block naming every
gating failure, every graded finding, and every check that could not be
measured. Nothing to grep, nothing to scroll past; the exit code is the
strictest aggregation and a test asserts it cannot disagree with the block.
On the deck that took ten rounds, the whole stack now answers in sixteen
seconds, and its one finding is the operator-owed terms list. The planted red
is the point made twice: the tri-failing document showed all four instrument
families in a single block — and the first version of that red run was read
through a pipe, which swallowed the exit code, in the release built to end
partial reading. Convention 16 held where the eye did not.

**Four private copies of the checker contract became one module.** How to
invoke each kind (`--genre` for prose, `--deliverable --no-sheet` for layout)
and how to read the two report shapes lived separately in
`run_conformance.score_checks`, `check_fixtures.verdicts_of`,
`debug_log.failing_verdicts` and `trace.py`'s `_checker_json`.
`scripts/lib/checker_report.py` owns both facts now and all four import it.
The distinction it must never lose is stated at the top: a checker that could
not speak is not a checker with nothing to say.

**And the root of 0.1.497's silent-transcription defect is closed.**
`check_design.py` printed its blind-gate warning even under `--json`, so the
one document the warning fires on — `div.page` markup, the exact case it
describes — emitted prose over the JSON and broke every machine consumer.
0.1.497 fixed the consumer; this fixes the channel: the warning now travels
inside the report as `blind_gates`, and the regression test asserts the JSON
stays parseable on the very document that used to corrupt it. A checker whose
"empty report + nonzero exit" answer used to vanish from the driver's block is
also named now — the tri-failing red run showed prose, privacy and layout and
said nothing at all about design until that line existed.

**`inspect_layout`'s last line now carries the whole verdict.** It used to
print the not-measured count early and the gating summary last, so a run could
end on "No gating finding fired" and still exit 1 — an operator who read the
last line, or grepped for it, shipped past a check that never ran. Twice in
one session. The last line of a verdict tool is the verdict, whole.

## 0.1.509 — the agreement study can finally produce a row, and its silences say why

Built in a parallel worktree against the pre-merge review's findings, and landed
now because the owner is about to produce the study's first real row: a blind
C1–C8 score of a deck built for exactly that purpose.

**The study's join was disjoint by schema.** The measurement cache is keyed by
filename; a reader record by the corpus id `review_scores.py` validates — and a
corpus id can never equal a filename, so `study()` returned empty for every
input the schema permits while CI's `--report` exited 0 on empty by design.
`review_scores.py` had required `corpus_id` *for this join* since the field
existed, and `eval_agreement.py` never read it. The join now runs filename →
corpus id (through the gitignored corpus registry) → reader record, and when
the registry is absent the study **says it could not join** rather than
printing an empty success — absence stated, never implied.

**Two adjacent silences closed the same way.** `--measure` could measure
nothing and exit 0, writing an empty cache over a good one; it now names what
it could not find, reports how many of how many resolved, and exits non-zero
when nothing was measured. And the verdicts with no pass/miss to compare —
`no bar`, `too few pages`, `not measured` — are counted and printed per metric
instead of vanishing, reported and not gating.

**The `--sheet` dimension list is deleted, not corrected.** It stopped at C7
after C8 shipped, so a reader who filled it produced a record the validator
rejects. The sheet is rendered from `rubric_items.py` — the same source
`scoring_sheet.py` uses — because a second copy is the drift class this
repository keeps paying for. Deliberate red: the disjoint join is reproduced in
the tests with valid inputs that still yield nothing under the old join, beside
the joined row, the stated absences, and the C8-bearing sheet.

## 0.1.508 — the sentence-rhythm floor moves to 0.50, replayed against the rebuilt corpus before moving

The refactor's research note called this change ready a week ago — code and
verification done, replayable — and it then sat unshipped, which is the
done-and-not-landed state this delivery run exists to end. It does not land on
the note's word: **it lands on a measurement taken today, against documents that
exist now.**

**The case for the floor at all** is 0.1.336: "short sentences" read as a
target drove sentence variance to zero, and M8 grew a second tail so uniform
rhythm fails as machine-made. **The case for 0.50 over 0.35** is discriminating
power, now measured rather than argued: the three rebuilt deliverables sit at
**0.593, 0.627 and 0.687**; the degenerate fixture — built to fail everything —
sits at **0.347**. A floor of 0.35 therefore separated nothing real from
anything: every live document cleared it by half again, and the pathological
case failed it by two hundredths. The rhythm the raise exists to catch is the
band between the two numbers — uniform enough to read machine-made, green under
the old floor.

Every fixture sits on the same side of 0.50 as of 0.35, so no expected verdict
flips; the deliberate red is the degenerate fixture itself, now failing by a
margin instead of a rounding error. M8 stays **graded, never gating** — the
floor says where the report turns red, not where a delivery stops.

## 0.1.507 — 64 pages recomposed for the sheet they are printed on, and the rules the work taught

R7's remaining two rebuilds, done as composition rather than as renaming —
which is the distinction 0.1.505 made checkable.

**Both documents now meet the rebuild spec's bar honestly.** `adopting-lumi-style`
(30 pages, A4): 3 effective layouts at 78.6% → **8 at 39.3%**, eleven pages
restructured child-by-child, every one verified on its rendered PNG, page order
identical and **all 30 titles verbatim**. `signal-radar-ops-guide` (34 pages,
A4, built by a parallel author against the same method): 4 effective layouts at
56.2% → **8 at 37.5%**, one library shape composed in, order identical and
**all 34 titles verbatim**. Both pass every design gate, both exit 0 from the
rendered deliverable check, and both carry a closed trace whose recipe
fingerprint reads **current** — the recipes were rewritten against these rules
and now say so, which is what Ledger 2b exists to ask.

**Three conversions were reverted after looking, and that is the method
working.** Metrics stayed green through both states; the contact sheet decided.
The lessons went into `references/design-rules.md` §3 rather than into memory:
on portrait the split family is ONE composition and variety comes from the
vertical and composite families; **content volume is part of "choose from the
content"** — a thin list under a 1fr hero row opens a dead band, and the fix is
a second content block from the page's own facts, never a stretched one;
portrait `columns-2` centers cells independently, so it suits near-equal
columns. §4.2 gains the label-scale rule: a token 11px class inside a
thousands-of-units viewBox renders invisibly, so labels scale by the
viewBox-to-cell ratio.

**One deviation from the spec's checklist, stated rather than gamed.**
`adopting-lumi-style` references zero library shapes. Its 22 figures are
semantic flows with decision diamonds and dashed not-built states — already at
the parity the library exists to raise documents to — and the one candidate
match (Harvey balls on the prose-metric verdicts) would have encoded degree
where the content is categorical. Forcing a unit in to satisfy "shapes
referenced > 0" is the metric-satisfied-instead-of-met failure 0.1.505 just
recorded. `check_privacy.py --terms` also remains owed: the out-of-bounds list
is engagement data only the operator can supply.

**The fifth defect from the same stylesheet sentence, caught by the first real
use of the thing it broke.** `trace.py`'s geometry cross-check — built at
0.1.499, before `markup.py` existed — read `data-geometry` by first match, so
its first run against a real portrait document read the comment's `landscape`
and **refused a correct trace**, the exact inversion of its job. It reads the
real `<body>` now, through the shared helper, with the decoy in a test.

**And the aspect probe held every page to 16:9, whatever the document
declared.** On a portrait handbook it printed "30 of 30 measured pages are not
16:9" — every one holding A4's 0.707:1 exactly, which is what they owe. A
report that reads as failure on a correct document teaches its reader to skip
the section, and a skipped section is how a real failure ships. The target now
follows the declaration.

## 0.1.506 — a typed token count was a typed verdict, and the board now crosses model with effort

R8, the code half of the model matrix (K1).

**`trace.py close` no longer takes a typed token count.** The doctrine at the
top of the file — the verdict fields are machine-written, there is no flag for
supplying one — stopped one line short of the bill: `--input-tokens N
--output-tokens N` were numbers typed by the agent being measured, which is the
exact shape `check_evidence.py` was built to end. Both flags are gone; `close
--usage <path>` reads the API's own usage dump, tolerates the extra keys a real
dump carries, and refuses — naming exactly what is wrong — a file it cannot
read, a file that is not JSON, a missing token key, and a non-integer count. A
refused close exits before the checkers run and leaves the trace open, rather
than closing a record that reads as a cheaper build than the one that happened.

**The planted red ran first, and fired twice.** Before any wiring, the parser
*accepted* `--input-tokens 5` — the test failed at the trace lookup, not at the
flag, which is the defect stated by the tool itself. Then `--usage` was wired
permissively on purpose: that reader closed a trace with exit 0 against a usage
file carrying no `output_tokens` at all, and answered malformed JSON with a
traceback instead of a refusal. The tests assert the difference — a refusal
names what is wrong, and `Traceback` may not appear in one.

**`ledger.py --board` now ends in the model × effort matrix: quality and cost
columns produced together.** Rows are models; columns are the schema's effort
vocabulary in its own order plus `?` — imported from `trace_schema.ENUMS`,
never retyped, the sixth-literal-copy hazard the genre enum already grew once.
A cell is the median output tokens per content page with its n; qualification
is `board()`'s own, one implementation of the quality line, so a thin deck that
cannot be on the board cannot set a median here either. An empty cell is drawn
as an em dash rather than skipped.

**Cost exists only at render time.** `cost_usd` left the schema at 0.1.501
because a stored derivation goes stale the day the price does; the matrix holds
that line by computing cost per content page from `evals/prices.local.json` —
untracked, beside the other two `.local.json` entries, because a price is one
operator machine's dated fact — and labelling every cost row with the table's
own price date. A model with no price row is said in words; a run that never
recorded input tokens stays in the token median and is excluded from the cost
one rather than counted at zero, since input is most of the bill and an
understated cost flatters the run. When there is no price table at all, the
board says cost is not computed and why — absence stated, never implied.

## 0.1.505 — D9 could be satisfied by renaming a class, and the fix was found by trying to satisfy it

**Found by attempting the rebuild honestly.** The rebuild spec asks a document
for **≥6 distinct layouts with the heaviest under 40%**. A 30-page A4 handbook
sat at 3 layouts and 78.6%, so its content pages were reassigned across
`split`, `split-wide`, `split-narrow` and `sidebar-notes` by what each page
actually holds — text weight, a figure that carries the page, a load-bearing
qualification. D9 went from **3 layouts / 78.6%** to **6 / 25.0%**, the gates
stayed green, and `inspect_layout --deliverable` exited 0.

**Then the contact sheet.** The pages were unchanged. In portrait,
`tokens/lumi-layouts.css` collapses those four to a single grid —
`1fr / auto auto 1fr` — so all four render identically, and the reassignment
had bought a number and nothing else. **D9 counted declared class names, so a
document could double its layout variety by editing strings.** That is a metric
satisfied instead of met, which is the failure this package's opening
provenance note is about, arriving in the metric rather than in the design.

The reassignment was reverted rather than shipped.

**D9 now counts what the geometry distinguishes**, derived from the
document's own stylesheet rather than hard-coded: a rule that sets a grid for
several `.body.<name>` selectors at once is the statement that those names are
one layout there. The renamed build and the original now both report **3
layouts at 78.6%** — which is the truth, and the criterion is unmet for that
document until its pages are actually recomposed.

**The same comment has now cost four defects.** The token block explains the
geometry rule with a line containing a literal
`<body data-geometry="landscape">`, hundreds of characters ahead of the real
tag, in **every** deliverable. `embed_shapes.py` injected the sprite after it
at 0.1.492 and shipped a document where every `<use>` resolved to nothing.
D9's lookup read its `landscape` on a portrait document here — written while
reading the comment describing the first one. So the skip is a shared
`scripts/lib/markup.py` now instead of a warning: `body_attr` computes comment,
`<style>` and `<script>` spans first, and `embed_shapes.py` calls it too, so
there is one implementation rather than one implementation and one description.

**And a two-minute hang worth recording.** The first version of the
equivalence scan used `([^{}]*)\{([^{}]*grid-template-columns[^{}]*)\}`, which
backtracks catastrophically on a 680KB document. It reads the CSS linearly now.
A pattern that is correct on a fixture and quadratic on a deliverable is not a
correct pattern.

## 0.1.504 — the shape manifest described 206 files nobody had, in a language this repository does not use

Found while preparing R7's rebuilds, by trying to follow the rule that says to
look at a shape before using it.

**The `preview` path was dangling on all 206 records.**
`assets/shapes/previews/` is empty, `.gitignore` excludes `*.png`, and no code
has ever read the field. The rebuild spec's own discipline — *"verified against
its rendered preview before use"* — pointed at files that existed on nobody's
machine, which is the shape-library defect in miniature and it survived the
release that fixed the library. The previews do exist, in the extraction
staging area outside this repository, at 18MB against 13MB of current assets;
shipping them would more than double the package's asset weight to satisfy a
rule that has a cheaper honest form.

**So §4.1 states a check the package can honour.** `embed_shapes.py --list`
names what a document references and `assets/shapes/<id>.svg` opens in any
browser. That is the whole check, it is one the package ships the file for, and
it keeps the discipline the rule exists for: `relation` narrows the field and
does not tell you what the geometry draws, which is how this library was
curated wrongly twice.

**Seventy records were written in Chinese.** Descriptions of geometry —
*"stacked columns rising"*, *"a centre with five satellites, hub and spoke"* —
in a repository whose first maintenance red line is that it is written in
English, and not rule data for Chinese output by any reading. All seventy are
translated.

**Both were invisible for the same reason, and it is a lesson this repository
had already learned once.** `check_english_only` scanned markdown; `check_stale_promises`
says in its own docstring that it was widened to registry JSON because *"every
text scan in this file globs `*.md`"* — and that was not carried across.
English-only now reads tracked JSON manifests too, and `check_shape_library`
refuses a manifest field pointing at a file the package does not ship.

**Two things the planted red taught that reading would not have.** The
dangling-path guard's first version matched any value containing a slash and
read a *note* — "illustrative / draft / for discussion only stamps" — as a
filename; convention 15, in one run against the real manifest. And the
English-only widening was first written as a text scan, which misses
`样式` — valid JSON for the same characters, with no CJK byte in the
file. It parses the document and walks the values now, so an escaped string
cannot hide.

**Four manifests are allowlisted, each with its reason in the code.** The three
plugin artifacts carry the skill's own trigger phrase, which is the string a
Chinese-speaking user types; the geography registries carry the `z` field that
`regionmap_svg.py --labels zh` renders onto a Chinese map. Deleting those would
not make the repository more English — it would make the Chinese map wrong.

## 0.1.503 — an instrument nobody can find is an instrument nobody runs, and the board stopped naming a version it never measured

R6, and all three findings are the same shape: something true, recorded
somewhere no one reads it.

**Four evals instruments were referenced by no entry point.** `trace.py`,
`ledger.py`, `judge_findings.py` and `scoring_sheet.py` are the whole
measurement half of the refactor, and `SKILL.md`, `AGENTS.md` and
`prompts/lumi-style-core.md` named none of them — so every one was opt-in for
whoever happened to remember. Both tool-capable entry points now name them,
with what each is for. The prompt tier still names none, and that is correct
rather than an omission: it runs no scripts, and a rule that told it to would
be prescribing a capability the tier does not have.

**The conformance board advertised a version it had never measured anything
at.** Its header read `skill 0.1.502` over a table rendering runs from
`0.1.454`. That is exactly the claim `built_version` exists to stop a *cell*
from making, made by the page the cells sit on. The header now carries both and
the distance between them — *"skill 0.1.503 · newest run 0.1.454 · 48 releases
behind"* — counted in CHANGELOG headings, because the distance that matters is
how many rule revisions have landed since, not how far apart two integers are.

**The word `skill` stays, and stays first.** The obvious edit was to write
`instrument 0.1.503`, which reads better and would have reddened CI the first
time anyone regenerated the board: that line is this file's version stamp and
`check_version_citations` matches `skill {v}` on it. Caught by checking the
pattern against both header forms before shipping, not after — a cosmetic edit
laying a trap in a guard two files away is the coupling this repository keeps
paying for.

**C8-① and C8-② stop promising a condition that was met.** Both rows read
*"temporarily human → machine once the shape vocabulary lands"*. It landed —
206 units, `embed_shapes.py`, `assets/shapes/tags.json` — and the rows sat
unchanged for twenty-four releases. They now state the reason instead:
deciding whether a figure's form matches the comparison its **title** makes
needs the claim, and no checker can read a claim out of markup. The shape
vocabulary made the *form* machine-readable and left the *claim* where it was.
D21 already holds a figure to data it declares; a figure that declares none is
outside what a machine can say about it.

**`check_stale_promises` is structurally blind to this**, and that is recorded
rather than patched. It compares against shipped release numbers, and a promise
naming a *state* has no version to compare. **IDEA-11** carries the two ways to
close it and the argument for the cheap one — require the conditional form to
name a version, which makes the existing guard sufficient — over a
phrase-trigger guard, which is FM-01 in the making by AG-1's own reasoning. Not
built here: it is a convention change and wants a second instance behind it.

## 0.1.502 — on entry path B, completeness had no instrument at all

R5. `references/eval-rubric.md` has specified a reader-visible scope note
carrying `data-omitted` since C5 was written, and **no checker read it.** So the
only place an omission could be declared was an outline file — an artifact the
template path never produces. `check_outline.py` is described in its own
docstring as *"the only defence completeness has"*, and it consumes something
path B has no step to produce. On that path the defence was not weak; it was
absent, and it looked like nothing at all.

**D26 · declared scope** reports two things and gates on neither:

- which of a storyline's typical sections the document neither covers nor
  declares;
- and every `data-omitted` sitting on something a reader cannot see —
  `display:none`, `visibility:hidden`, `hidden`, `aria-hidden`, or an empty
  element. **Reader-visible is the whole mechanism.** A marker only the checker
  can read would do nothing but silence the checker, which is why that case is
  reported as loudly as a missing section.

**Reported and not gating, on evidence rather than on nerve.** C5 is
"declarable, never gating" because structural compliance does not predict
quality and a completeness gate is worth defeating: an author who has to clear
it writes the heading and puts nothing under it. What is decidable is whether
an absence was *declared*, and whether the declaration is one a reader meets.

**The storyline is declared, never inferred.** D26 reads `data-storyline` off
the body; guessing it from the headings would make the report a measurement of
the guess. `new_deck.py --storyline` now emits the attribute, so a scaffolded
document is measurable from the first build. A document that declares nothing
reads *"no data-storyline declared"* rather than passing.

**`.scope-note` ships a rendering.** Convention 5 forbids a rule that mandates
an asset the package does not ship, and a scope note that renders as nothing is
a declaration no reader meets — the exact failure the metric exists to catch,
arriving through the stylesheet.

**A fixture pair, so the metric is seen firing rather than only passing.**
`deck-pass` now carries the reference implementation of a declared omission —
named, reasoned, and where a reader meets it. `deck-broken` carries the same
declaration **hidden**, which is the failing case, and it is the failing case
precisely because a hidden marker is the one thing that defeats the mechanism
rather than merely lacking it.

**And the fixture suite's own accounting was wrong about it.** `check_fixtures`
sorts a metric into `graded` or `reported` by looking for the word *reported*
in its target string — which conflates *does not gate* with *cannot fail*. D26
is neither: it does not gate, and it fails on `deck-broken`. With the original
wording the coverage note said the metric could not fail while a fixture was
failing it. The target now states the property instead of the tier, and the
count reads 43/43 graded verdicts with a failing fixture.

**Found by running it on a real document rather than on the fixture.** The
fixture declares no storyline, so the checklist branch never executed there and
the metric passed its first run with an unbound name in the path nobody took.
One scaffolded document with `--storyline gtm` raised it immediately. Convention
15, again: the material checks the model in a way that reading the code cannot.

## 0.1.501 — the four-beat design's own falsification data was recorded and never read

R4. The guard was planted first, and what it found was worse than the field it
was written for.

**`check_trace_field_readers`** asks a small question of the closed trace
schema: does anything outside the writer read this field? A field nobody reads
is not absent — it is worse, because it looks like coverage. The case that
prompted it was `entry_path`: the owner ruled that entry path B is held to the
current constitution, `trace.py` wrote the field faithfully, and `ledger.py`
read eleven fields and never that one. **A rule with no consumer cannot be
true or false about anything.** (0.1.500 gave `entry_path` its reader, so the
planted red found the rest.)

**Six fields were write-only, and two of them are the four-beat design's own
evidence.** `outline_reviewed` exists, in the design record's own words, so
that skipping beat 4 is *"a countable fact rather than an invisible choice"* —
and nothing counted it, for the whole life of the design it exists to falsify.
`titles_changed_after_approval` is the sharper of the two: a storyline review
that is agreed and then quietly departed from is not a review, and that number
says how far the built document walked from what somebody approved. **Ledger 2c
now reports both**, split by entry path, which is the comparison K2's
self-falsifying clause needs.

`input_tokens` — most of the bill on a long context — and `opened_at` were also
unread; both now appear on the efficiency board, input beside output rather
than folded into it, because the two move for different reasons and one total
hides which.

**`cost_usd` is deleted rather than given a reader.** It is tokens times a
price: a stored derivation that goes stale the day the price does, while the
tokens it derives from sit in the same record. Prefer deleting the number. The
board can compute cost at report time from a dated table when there is one.

**`effort` becomes a closed vocabulary** (low/medium/high), because K1's model
matrix is two model tiers by three effort levels and a free-string column
cannot be grouped. `model` deliberately stays free text one line above it:
model names rot, and an enum of them is a maintenance tax with no defect
behind it.

Deliberate red: the guard went red on all six before any of them had a reader,
and its synthetic-tree tests include the case that would make it vacuous —
counting `trace.py` itself as a reader, which every field would pass.

## 0.1.500 — a build now records what drove it, so "unknown" stops reading as "current"

R3, and the mechanism the owner's entry-path ruling was missing. §6 said both
paths are held to the current rules; nothing could tell whether one was.

**The hole, stated exactly.** A trace's `skill_version` is read from `SKILL.md`
when the trace opens. It therefore always equals the current version and
**cannot be stale by construction**. A build replaying a recipe frozen at
0.1.457 opened a trace stamped with today's version, cleared the checks those
two checkers know how to fail, closed with machine-written verdicts, and left a
record indistinguishable from a document built to the current constitution.
Measured, not supposed.

**`trace.py open --recipe <path>`** now fingerprints the bytes the build was
actually driven by and reads the version stamp that recipe carries. Taken at
open, from what the build was given — computing it later would fingerprint
whatever the recipe had since become, which is the mistake `asked_fingerprint`
exists to avoid one domain over.

**Reused, not invented.** `run_conformance.py` has implemented these semantics
for a different subject since 0.1.435: hash the material that can change a
verdict, read the artifact's own colophon, and mark a cell whose hash no longer
matches rather than reporting an answer to a question nobody is asking. Both
now call one `scripts/lib/fingerprint.py`. A second sha256-of-sorted-json would
have been the `no shadow math` guard's territory, and a fingerprint that
differed between callers is worse than none — both sides would report matches.

**Ledger 2b reports four answers where there was one**, and the fourth is the
point: **current**, **stale** (the recipe names an older version than the rules
that graded it), **none** (no recipe — what path A looks like), and
**unknown** — a recipe carrying no version stamp at all. **Unknown is not
current.** A recipe that never said which rules it was written against has not
told anyone it followed them, and this is not a hypothetical shape: the first
real recipe measured here carries no stamp, because it reads its version out of
`SKILL.md` at build time. It has no vintage of its own, and now that is
something the ledger says instead of something nobody could ask.

**Two prose facts corrected while they were in hand.** `check_trace_schema`'s
docstring said *"the repository ships none"* for three releases after a real
build's trace was committed, which is this file's own drift class occurring
inside the guard that exists to catch it — and its claim that *"the synthetic
tests are what prove this can fail"* pointed at tests of the **library** until
0.1.497 gave the guard tests of its own. The stored trace was migrated to the
widened schema with both new fields null, which is the honest value: that build
named no recipe.

## 0.1.499 — the scaffold reaches the shape library, and a trace can no longer contradict its own document

R2 of the delivery-completion plan: entry path B *is* the template path, and its
only tool was handing authors a document the current rules could not be met from.

**`new_deck.py` did not import `embed_shapes` at all.** Three shipped
deliverables referenced **none** of the 206 units, and the rebuild spec's D1
calls that guaranteed rather than accidental — an agent following the entry
points had no path to the library, and the scaffold's `.fig` was an empty
comment. It now emits **one worked example** and builds the sprite for it, the
same way the globe runtime is built rather than harvested.

It teaches the **mechanics, not the choice.** Which shape a page wants follows
the relation in its content (§4.1) and no scaffold can know that; the library
was mis-curated twice by reading names as classifications, so prescribing a
shape would be that mistake with a friendlier face. What the example does show
is the part with no judgement in it — and one measurement made the case:
**all 206 units have a non-zero viewBox origin. Not most. Every one.** So §4.2's
warning that a bare `<use>` renders shifted off frame is not an edge case an
author might meet, it is the condition every single time, and the `x`/`y`/
`width`/`height` in the example are load-bearing. The labels are written
`style="fill:"` for the same reason: a `fill=` attribute loses to CSS silently.
Both label strings joined `AUTHOR_FILL`, so a figure shipped with them fails
D14 — furniture the placeholder list has not learned is furniture that ships.

**A trace could contradict its own deliverable and nothing could see it.** The
word `geometry` named three unrelated vocabularies with no guard between any
pair: the composition a body declares (`landscape`/`portrait`, what `tokens/`
styles), the stage a trace records (`16x9`/`a4`/`laptop`), and
`inspect_layout.py`'s viewport matrix — which is a test matrix and rightly its
own list. The map between the first two is now declared once, in
`deliverable_registry.py`, and `trace.py close` refuses a trace whose stage
disagrees with the body it is closing over. Deliberate red: an `a4` trace
against a `landscape` document is refused by name; a `16x9` one closes.

**Two vocabulary copies deleted rather than checked.** `trace_schema`'s
`ENUMS["genre"]` was a **sixth literal copy** of the genre list, and
`check_genre_vocabulary` inspects a fixed seven-file list that does not include
it — so adding a genre would have left the newest genre the only one that could
not be traced, with every guard green. It now shares the registry's tuple, as
`storyline` already did, and the geometry enum is derived from the same map.
Preferring impossible to checked is convention 13's spirit one level up.

**`--storyline` seeds the agenda from the storyline's typical sections** — as
furniture to replace, never as a template, which is the registry's own
constraint. A storyline with **no** checklist now says so on the page:
`proposal` shipped for eight releases looking like a storyline whose sections
were all present, because absence printed as silence. That is the same defect
`check_outline.py` carried until 0.1.497, in the other tool.

**One thing deliberately not done.** The plan called for raising the scaffold
from 4 layouts to 6. Declined for now and recorded here rather than silently
dropped: the "≥6 distinct layouts, heaviest under 40%" bar is a criterion for a
**deliverable**, not for a starting point, and the layouts expect different
children — `split` defines two rows, `stack` defines no `.span` — so cycling
them mechanically produces pages that overflow. The benefit is indirect and the
breakage is real. It belongs with a composition pass, not with a generator.

## 0.1.498 — the two entry paths get a home, unshipped work gets a number, and the quote-parity guard is declined on evidence

**Entry path B had no definition.** Its only statement anywhere was a
subordinate clause in a design record — *"entry B is the template path that
exists today"* — and a spec is not a source of rules. Path A fared little
better: beat 2 lived in `references/operating-rules.md` and beats 1, 3 and 4
existed only in specs. Neither path was named in any entry point, so the rule
the owner had just ruled on had nowhere to be true.

`references/operating-rules.md` §6 is now that home, id `OR-2`, and it carries
both paths, the four beats in order, and the sentence the ruling turns on:
**both paths are held to the current constitution, rules and evals — a recipe
is not a licence to reproduce the document it was written for.** Re-running a
source script demonstrates that nothing broke and demonstrates nothing about
what the rules gained since it was written. The case is on record: a rebuild
whose argument sat two research rounds behind its own evidence base while every
gate reported green, and a second that differed from its predecessor by two
lines. Re-flowed by hand into all three entry points, at each one's capability
tier — the prompt tier gets the four beats and not the trace commands, because
it has no tools to run.

**Unshipped work is now a number somebody sees.** Forty releases accumulated on
a branch that was never pushed, had no pull request and had never been seen by
CI, while every local check stayed green. Nothing in the repository could say
otherwise because nothing asked. `scripts/lib/shipping.py` asks, and both
`release.py` and `preflight.py` print the answer.

It counts **versions, never commits**, and the distinction is the whole design.
This repository lands a multi-release branch with `gh pr merge --rebase` —
merge commits are disabled and squashing is forbidden — and a rebase gives every
commit a new hash. A counter asking `origin/main..HEAD` would report the entire
branch as unshipped *immediately after shipping it*. Commit subjects survive a
rebase, which is the same property `check_evidence.py` already leans on to
re-resolve a dangling diff base. The test asserts the trap is real before
asserting the count is right: `rev-list --count` reads 2 where the counter
correctly reads 0. **Reported, never gating** — the problem was never that
somebody chose to wait, it was that nobody was told how long they had waited.

**`claim_sweep.py` now runs inside `release.py`.** Convention 12 says to sweep
restated claims before committing and the only thing holding that was the
sentence saying so — for the defect class twenty-six of this repository's
releases exist to fix. Same reasoning as refusing to commit on a red preflight:
a rule written down and then not followed needs a tool that holds it, not firmer
wording. It reports and does not gate, because the sweep's own contract is that
it reports and never fails, and promoting it here would quietly overrule that.

**The quote-parity guard is declined, as AG-7, on evidence.** It was named in
the P1 plan and then vanished with no record — which is the thing being fixed,
since an undocumented decline gets re-argued. Looked at the material before
writing the pattern, per convention 15: every blockquote in the three entry
points is apparatus — a version stamp, a usage note, a pointer at the file that
owns a rule — and **not one is a verbatim quotation of `references/` prose.**
The entry points restate by design. A guard with an empty subject set is FM-01
by construction: green forever, and counted as covering a drift it never
touched. If an entry point ever does quote a rule verbatim, this becomes
buildable and should be rebuilt.

**Two guards widened, one of them by the same reasoning.**
`check_principle_trace` validated file-level `*Serves:` declarations in **two
hard-coded filenames**, so a clause that does not exist passed in
`operating-rules.md` and failed in `eval-rubric.md`. It now reads every
reference file. Deliberate red, planted first: `*Serves: **P-99**` on the new
§6 fails both the section-level and the file-level arm.

**A drift sweep of `README.md`**, which independently restates the file map:
`references/PRINCIPLES.md` and `references/operating-rules.md` were absent from
it entirely, `assets/shapes` was absent, and it advertised *"the M / D / H eval
rubric"* eleven lines above its own protocol section describing C1–C8.

## 0.1.497 — five checks reported ok where they could not run, and one guard had no test of its own

**Found by a review of the whole refactor, run before merging it.** Three
reviewers worked the diff independently; two of them verified by *mutation* —
replacing a guard's body with `return []` and watching whether the suite
noticed — rather than by reading, which is convention 15's point that reading
uses the same model that produced the code.

**One defect wearing five sets of clothes.** This repository is careful about
the distinction at the point of MEASUREMENT: `n/a` means the metric does not
apply, `not_measured` means it applies and could not be run, and the comment
explaining why they must not collapse is three releases old. Every one of these
five threw the distinction away one level up, at the point of CONSUMPTION.

- **`check_privacy.py`: a typo in `--terms` scored better than omitting the
  flag.** `load_terms` grew a `missing` status; the verdict expression and the
  exit ladder both still asked about `not_attempted` by name. Verified before
  the fix: `--terms /nonexistent/path` exited **0** with `"verdict": "ok"`,
  while passing no `--terms` at all correctly exited 1. The out-of-bounds list
  is engagement data living outside this repository, so a moved or stale path
  is the *expected* failure, and it turned the one gating half of layer 1
  green. The statuses that mean "did not run" are now named once, with a test
  asserting the namer covers everything the loader can produce.
- **`trace.py`: a checker that could not speak was recorded as a checker with
  nothing to say.** `_checker_json` discarded the return code and returned
  `None` on a parse error; `close` skipped any falsy report, so `[]` and a
  crash were one value. The `not_measured` marker fired only when BOTH checkers
  failed. Verified: closing a trace against an unreadable path exited 0 with
  zero gates recorded, and the record passed schema validation. The trigger is
  already in the tree — `check_design.py` prints its blind-gate warning with a
  bare `print()` that `--json` does not suppress, so a deck using `div.page`
  emits prose in front of its JSON. Now recorded **per checker**, which is what
  lets `ledger.py`'s second ledger — the one built to notice a broken
  instrument — work at all.
- **`check_outline.py`: the newest storyline shipped with its gate disarmed.**
  The gating declared-omission check sat inside `if expected:`, and `proposal`
  is the one storyline in `STORYLINES` with no `TYPICAL_SECTIONS` row. Verified:
  the same outline, one word changed, exited **1** under `market-analysis` and
  **0** under `proposal`. The gate now runs for every storyline — whether a
  stated omission carries a reason is a fact about the outline, not about the
  checklist — and a storyline with no checklist reports `not_measured` rather
  than printing nothing.
- **`D24_images_embedded` could not see a relative image.** `_CSS_URL` required
  a scheme or `//` after its `(?!data:)` lookahead, so `url(assets/cover.jpg)`
  matched nothing and passed. That is how a person writes a cover background,
  and it renders correctly on the author's machine because the asset sits
  beside the HTML — so opening the deliverable in its delivery medium does not
  catch it either. The reader receives one HTML file and a blank cover. The
  url() target is now decided in code rather than by a lookahead, after the
  first fix was bypassed by `url( #clip )`: an optional quote class let the
  engine backtrack past the guard, which is not something a lookahead should be
  asked to arbitrate.
- **`check_shape_library` asked the filesystem.** 0.1.496 fixed *the files are
  ignored*; *the directory is gone* was still a pass, because the guard bailed
  on a missing library as an un-ingested one. It now compares the manifest
  against what git TRACKS, and an absent library fails while
  `scripts/build/embed_shapes.py` ships to read it — a build step whose input is
  missing is not an un-ingested library. `assets tracked` keeps its own job and
  its docstring now says which side it is on: it fires on the author's machine,
  before the commit, and is quiet in a clone by construction. Neither is the
  other's substitute.

**And the guard that had no test of its own.** `check_trace_schema` survived
having its body replaced with `return []` while all 593 tests passed. Its
docstring says *"the synthetic tests are what prove this can fail"* and the
entry that introduced it said the same — but that deliberate-red was run
against `trace_schema.validate`, the **library**. The guard's own layer — the
directory walk, the JSON parse, the vacuity floor — had never executed under
test. That is FM-01 recorded as prevented in the entry that introduced it, and
it is the strongest argument in this repository's history for planting the red
first. It now has four synthetic-tree tests, and the same mutation kills two of
them.

**Deliberate-red, planted first, in every case:** each of the five was
reproduced as a failing command before a line was changed, and the shape-library
fix was proved by untracking the library — the fresh-clone condition — and
watching the guard go red where the glob version had been green.

## 0.1.496 — the shape library was never in version control, and every asset guard was reading the wrong thing

**Found by CI, on the first run it was ever given.** Forty releases had
accumulated on a branch that was never pushed, so no workflow had seen any of
them. The first push put all forty in front of the checks at once, and `shape
library` failed on a fresh clone with every one of its 206 units reported as
described-but-not-shipped.

`.gitignore` carries a blanket `*.svg` rule, which is there to keep a
deliverable's renders out of a repository that ships rules. An exception block
below it re-admits the design language's own assets, and that block's own
comment reads *"this is the fourth directory to need saying so"*.
`assets/shapes/` became the fifth and was never added. The library — extracted,
tagged, recoloured, and reachable from both entry points since 0.1.491 —
existed on one machine and in no clone.

**No local check could have found it, and that is the more useful half.**
`check_shape_library` globs `assets/shapes/*.svg`, finds 206 files, and passes.
It is right about what it measures: the files are there. Every asset guard in
this repository reads the working tree, and a working tree cannot distinguish
*shipped* from *present on the author's machine*. Five directories have now
needed the exception, which is four more than a comment can be trusted to hold.

So `assets tracked` asks git rather than the filesystem: any non-dotfile under
`assets/` that `.gitignore` excludes fails the release. A dotfile is exempt —
`.DS_Store` is the platform's litter, not the package's material. A tarball
checkout with no `.git` asserts nothing, since it has no index to ask.

**The deliberate-red run was planted first and is unusually legible.** The guard
was written while the library was still untracked, and in a single run it
reported `FAIL assets tracked` on all 206 units beside `ok shape library`. Those
two lines in one run are the entire argument for the new guard: the old one is
not broken, it is looking at something else. Synthetic-tree tests cover the
tracked tree, the ignored-asset tree, the dotfile exemption and the tarball
case.

One consequence worth stating plainly: **every deliverable this package has
built with a library shape was reproducible only here.** Nothing shipped
wrongly — the sprite embeds at build time from local files — but a second
machine following the entry points would have found `embed_shapes.py` with
nothing to embed.

## 0.1.495 — a comparison may now be a figure, and the proposal is rebuilt with nine shape families and no tables at all

**The rule change first, because the deliverable follows it and not the other
way round.** §4 read *"comparisons always use tables"*. The owner directed that
tables be replaced by figures, and this does not delete the rule — it keeps the
reason and drops the form. A table was the rule because it is precise and cannot
distort. So: **a comparison may be a table or a figure, and either way the reader
must be able to read the values off it.** A figure qualifies when it carries the
values a table would have carried, labelled on the marks rather than implied by
their size. A comparison drawn as unlabelled geometry is decoration wearing a
table's job, and it is worse than the table it replaced.

**The A2UI proposal is rebuilt.** It now carries **12 shape references across 9
distinct library units and no tables at all**, where two releases ago it carried
none of either. Each page's figure comes from a different family and each is
composed with that page's own words and numbers, placed against coordinates
measured off a rendered grid:

- the five wire messages become a **two-out-one-back arrow figure**, which says
  in its geometry what the table said in a column: the return path is the narrow
  one, and it is the only place user intent enters;
- three published versions become a **staircase** with the labels in an aligned
  band beneath it, because the shape has seven treads and no room to letter on;
- the renderer decision becomes a **four-step chain**, each step forced by the
  one before it;
- five seams become **Harvey balls**, four filled and one empty, and the empty
  one is the only new code the proposal asks for;
- five protocols become **five blocks under one question**, each labelled with
  its own versioning scheme;
- what is left out becomes **concentric scope rings**;
- the two renderer options become a **swap ladder**, which is the shipped LUMI
  pattern for exactly this shape of argument;
- and the three asks keep the **flow band with a lime rule** under the single
  one that gates the release.

**All three measurements that were short at 0.1.494 now meet their targets.**
`visual_share_median` 28 → 43 → **50** against a target of 50. Layouts **3 → 6**
distinct with the heaviest falling from 53.8% to **30.8%**, reassigned from the
selection table rather than by taste — a centerpiece wider than 3:1 goes to
`stack`, two parallel items to `columns-2`, load-bearing qualifications to
`sidebar-notes`. Tables **6 → 0**. `inspect_layout --deliverable` exits 0, and the
document's design gates — D12, D14, D15, D19, D20, D21, D22, D24, D25 — all
report ok. The release still carries the standing conformance-freshness waiver,
which concerns the board rather than this document.

**A library defect found by using it.** Seven of the 206 units carry an
invisible `<rect class="BoundingBox">` whose x has overflowed to about -2^31 —
what an export writes when an arc has a zero or full sweep. It draws nothing and
the viewBox crops it, so it is invisible in the preview; it is not invisible to
`getBBox`, and the rendered-geometry check correctly reported a figure as
drawing 3.6 million units outside its own frame. Those rects are LibreOffice
layout scaffolding and are now stripped at embed time, which removes a defect
and a large share of the sprite's bytes together.

**Four composition facts, each learned by watching a page fail.** A figure whose
aspect is wider than 3:1 blows out the grid column it sits in. A `.span` child
does not rescue it: `split` defines two rows, so a third child lands in an
implicit row that overflows, and `stack` does not define `.span` at all. A
`<use>` of a symbol whose viewBox has a non-zero origin renders shifted off
frame unless it declares `x`/`y`/`width`/`height`. And a `fill=` attribute on a
`<text>` loses to CSS, so labels take the stylesheet's colour unless written as
`style="fill:"`. All four are in §4.2 where an author meets them.

## 0.1.494 — embedding a shape no longer imports its hex fallbacks, and four composed figures land in a real document

Found by composing four figures on one page-set. Every unit in the library
ships its colours as `var(--acc-4, #889A82)` so that a shape renders correctly
when opened on its own. In a deliverable the token block is always present, so
the fallback can never fire — but it arrives in the file as a hex literal, and
`D4_palette_literals` counts hex literals. A document that had none reported two
the moment four shapes were embedded.

The fallback is stripped at embed time rather than D4 being loosened: the
library keeps its fallbacks for standalone use, and the deliverable gets the
variable alone. Loosening the check would have made every future literal
invisible in exchange for this one.

**Where the redesign stands, stated as measurements rather than as progress.**
The A2UI proposal now references four library shapes where it referenced none,
each composed with the page's own words and numbers placed against measured
geometry, one of them carrying a lime rule under the single decision that gates
the release. The document's own gates
— D12, D14, D15, D19, D20, D21, D22, D24, D25 — pass, and
`inspect_layout --deliverable` exits 0. The release still carries the standing
conformance-freshness waiver, which is about the board and not about this
document; claiming a clean sweep beside a waiver is the
sentence 0.1.415 taught this repository not to write, and the evidence gate
caught this entry writing it. It matches the phrase literally, so it also caught
the first correction quoting the phrase in order to disown it — blunt, and
right about the file it reads.

Three things are **not** yet where they should be, and naming them is the point
of writing this down: `visual_share_median` reads 28 against a target of 50;
the document draws on 3 of the 16 layouts with one of them carrying 53.8%; and
all four shapes come from a single family, so the figure vocabulary is monotone
in exactly the way D5 exists to notice. None of those is a gate and all three
are real.

Two composition facts learned the hard way, both now in §4.2's territory and
worth the sentence here: a figure whose aspect is wider than 3:1 blows out the
grid column it is placed in — the selection table already says such a
centerpiece belongs in `stack`, and the page that ignored it collided until the
figure moved to the main column. And a `.span` child does not help: `split`
defines two grid rows, so a third child lands in an implicit row that overflows,
and `stack` does not define `.span` at all.

## 0.1.493 — imagery is allowed and gated, and a library shape becomes a starting geometry rather than a finished figure

Two owner directions, taken together because they are the same instruction: the
rules that limit what a page can be made of are lifted, and what replaces them
is a condition rather than an absence.

**Imagery — `design-rules.md` §9, `DR-15`.** The old clause read *"without a
professional photo library, never set text directly on imagery"*. That is a
CONDITION, and it had hardened into a ban applied to every kind of image — which
is convention 5's failure, recorded in convention 5's own words about this same
sentence. §9 is the condition being met. An image carries an argument the page
cannot make otherwise, or it is not on the page; the test is §6's test for icons,
*what does the reader now know that they did not*. Four rules, all checkable:
embedded as a `data:` URI and never linked; source and terms named on the page;
tinted into the accent ladder so it is not a foreign object beside the palette;
and text never on raw photography — the surviving half of the old clause, kept on
its merits. The stock tells are banned by name — the handshake, the glass tower
at dusk, the team around a laptop, the lone figure at a whiteboard, the abstract
network of glowing dots — because an image that would fit any deck about any
subject is not evidence.

**Two new gates make that safe rather than hopeful.** **D24** fails any `<img>`,
SVG `<image>` or CSS `url()` pointing anywhere but at an embedded payload: a
deliverable is one self-contained file, and a linked image breaks the first time
it is read offline while telling its host who is reading. **D25** fails an image
whose terms are not named in words a person wrote — "all imagery used
appropriately" is the sentence that gets written when nobody checked, and it does
not pass. A document with no images passes D25 and says "no images" rather than
reading `n/a`, because `check_design` treats an unmeasurable gate as a failure on
purpose and applying that to an optional element would fail every text-and-vector
deliverable this package has produced.

**Composition — §4.2, `DR-14`.** A shape from the library is a starting geometry.
192 of its 206 units carry no text, so composing this page's own words and
numbers onto them is the work and not a gap in the library — the opposite
conclusion was drawn one release ago and was wrong. Labels go against measured
coordinates: render the unit once under a coordinate grid, read where its
segments actually fall, place the text there. Layering, retinting within the
accent ladder, and transforming are all in scope, with one limit — the relation
has to survive the transform, and a transform that makes a shape mean something
it did not is the same defect as choosing the wrong shape.

The two traps from the first real use are written down where an author meets
them: a `<use>` of a symbol whose viewBox has a **non-zero origin** renders
shifted, and far enough off renders outside the visible box entirely, unless the
`<use>` declares `x`, `y`, `width` and `height`; and a `fill=` presentation
attribute on a `<text>` **loses to any CSS rule** that styles figure text, so a
label written that way silently takes the stylesheet's colour.

C8 gains two evidence items — whether a shape was composed or dropped in, and
whether an image is evidence or atmosphere — and the reviewer's sheet carries
both in the language she reads.

**The `gating claims` guard earned its keep during this release.** Adding two
gates turned four prose sites red within seconds of the metrics landing —
`AGENTS.md`, `CLAUDE.md`, `references/brand.md` and `references/eval-rubric.md`
all enumerated seven. That is the drift class this repository has shipped
twenty-six fixes for, caught before the commit rather than four releases later.
The fifth site, `design-rules.md`, stayed silent because it took the
`AUTHORITY_NAMED` form one release ago and no longer counts.

Both gates were planted red on a real fixture first, four ways: a linked `<img>`,
a CSS `url()` to a CDN, an embedded image with no terms, and an embedded image
with terms named. Twenty tests, including that a vague gesture at licensing does
not pass and that each gate's row declares `(gates)` in its own target string.

Phase 0 of `specs/2026-08-17-rebuild-deliverables-to-current-standard-design.md`
continues here: the rules a document is rebuilt against are settled before the
document is rebuilt, which is convention 7's direction of authority.

## 0.1.492 — the shape sprite was being injected into a stylesheet comment, so every shape in every document resolved to nothing

Found by building one. `embed_shapes.py` inserted its sprite after the first
match of `<body[^>]*>` in the file. A deliverable's preamble explains the
one-geometry rule in a CSS comment inside its `<style>` block, and that comment
contains the literal text `` `<body data-geometry="landscape">` `` — several
hundred characters ahead of the real tag. **So the sprite went inside a
stylesheet comment**, the browser never parsed it, and every `<use href="#shape-…">`
in the document resolved to nothing and rendered as blank space.

**Three checks said the document was correct while it was blank.**
`embed_shapes.py --check` said the sprite was current, `--list` named the shape,
and D19 confirmed every reference resolved — all three read the file, and the
file was fine. Only a screenshot showed the empty space. That is convention 8's
case in its purest form so far: a metric that passes is not a verified document,
and the eye is not a slower version of the checks but a different instrument.

The injector now computes comment, `<style>` and `<script>` spans first and
takes the first `<body>` outside all of them, raising rather than guessing when
there is none. Eight tests, including the dangerous middle case — a decoy and no
real tag, where silently injecting into the comment IS the bug — and one that
anchors on `new_deck.preamble()` itself, so if the scaffold ever stops quoting a
`<body>` the test says the real-world case is gone instead of passing on a decoy
that no longer exists.

**A second finding from the same page, kept because it will recur.** A `<use>`
of a symbol whose viewBox has a non-zero origin — which is most of this library,
the units being extracted at their source coordinates — renders **shifted off
frame** unless the `<use>` carries explicit `x`, `y`, `width` and `height`. It
does not fail; it draws in the wrong place, and with a tall enough offset it
draws entirely outside the visible box. And a `fill="…"` presentation attribute
on a `<text>` loses to any CSS rule that styles figure text, so a label written
that way silently takes the stylesheet's colour: labels use `style="fill:…"`.

The first working use of the shape library in a deliverable is on page 5 of the
A2UI proposal: `p052-flow-3-title-01`, a three-segment chevron, labelled
AGENT / WIRE / CLIENT at the segment centres measured off a rendered coordinate
grid rather than assumed. **The labels are the point** — the library ships
geometry, and 192 of its 206 units carry no text at all, so composing the words
and numbers onto the shape is the document's job and not a gap in the library.

## 0.1.491 — the entry points had no path to the shape library, which is why three deliverables used none of its 206 units

The owner rebuilt a deliverable and reported it was almost identical to the
previous one. It was: stripped of version numbers, the rebuild differed from its
predecessor by **two lines**, used **none of the 206 shapes**, and drew on 4 of
the 16 layouts. The build was honest — a source script was re-run, not an output
patched — and that is the point. **A recipe written before the refactor
reproduces the document it was written for**, and re-running it proves only that
nothing broke.

**The root cause is in this package, not in the document.** `SKILL.md` and
`AGENTS.md` both carry the instruction to embed the vendored assets rather than
improvising, and both list the font, the icons and `assets/vectors/` — **neither
names `embed_shapes.py`**. Only `references/operating-rules.md` and
`design-rules.md` do. An agent following an entry point had no path to the shape
library at all, so zero usage across three deliverables was the guaranteed
outcome rather than an oversight. Both entry points now name it, and both carry
the selection rule with it: choose by the RELATION the content has, never by how
the shape looks.

**GAP-012 closes without an owner decision, because the rules had already made
it.** `design-rules.md:539` says comparisons still take tables and *"a table
page still wants its visual weight from a figure or a band beside it"*. So
`visual_absent` and §4 agree: the five flagged table pages are owed a figure or
band **beside** the table, never a shape replacing it. The probe is not widened.
The class-vocabulary worry that opened the entry was mistaken and is recorded so
it is not re-opened — the eight selectors are absent from `tokens/` but all
eight are defined in `new_deck.py`'s preamble, which is what a deliverable is
built from.

**GAP-013 closes, and closing it found something larger.** `proposal` is added
as a storyline, template first: a name in the tuple with no skeleton in the
rules is a label with nothing behind it. But **not one of the six existing
storyline names appeared anywhere in `references/`** — the axis had been a
closed enum in code since the two-axis split shipped, so an author choosing a
storyline had nothing to read and the name meant whatever the last person to
type it assumed. A roster now names all seven with the shape of argument each
makes. Five still carry a one-line shape rather than a full skeleton; that is
stated in the roster and queued as IDEA-10, because writing five skeletons with
no document to write them against is the speculative rule-making convention 2
forbids.

Two guards, both planted red before being believed. The new **`storyline
vocabulary`** guard holds the roster and the tuple to each other in both
directions — a name only in code fails, a name only in the rules fails — with
synthetic-tree tests including the vacuous-pass case an empty tuple would
create. The **`gating claims`** guard grew an `AUTHORITY_NAMED` form: a site may
stop enumerating and point at `check_design.py`'s `(gates)` target string
instead, and the guard then checks the opposite thing — that a list has not
grown back into the sentence. `design-rules.md` was the first site to take it,
because it said "one of the five checks" and then listed seven. Convention 13
says delete the number rather than correct it; the entry stays so the site stays
watched, which is how it rotted the first two times.

This is phase 0 of
`specs/2026-08-17-rebuild-deliverables-to-current-standard-design.md`, which
records why the entry points are fixed before any document is rebuilt: doing it
the other way produces a document that again uses nothing, with the cause still
sitting in the file the next agent reads.

## 0.1.490 — a real build through the checks: one document defect, one checker false positive, and two closed vocabularies that had no name for this document

The first deliverable built end-to-end since the refactor, run through every
check. It was entered on **path B** — materials supplied, no discussion — and
that is what its trace records, because the four-beat discussion path opens with
the user's own free statement and simulating it would write `entry_path=A` for a
conversation that did not happen. That falsehood is precisely what the trace
exists to prevent.

Four findings, and the useful part is that they are of four different kinds.

**A defect in the document, caught by a metric added two releases ago.**
`D23_font_count` reported three typefaces against a ceiling of two. The third
was `font-family: var(--body)` on the figure footnote class — **a custom
property nothing defines**, in `tokens/` or in the document, so every footnote
inside every figure fell back to the browser's default face. Fixed at source.

**A false positive in a checker, caught by the document.** `D6_footer` reported
all fifteen pages missing their provenance. The colophon read *"every claim
traces to the research report of 2026-08-11"* — provenance stated in plain
English, in a phrase the pattern did not list. The failure direction matters:
the cheapest way to clear it is to edit correct prose until the pattern matches,
which is the checker writing the document. The vocabulary was widened, with a
test asserting **both** directions — nine phrasings recognised, three colophons
with no provenance still failing — because widening a pattern is the move that
quietly disables a check. The test caught its own first draft, which had
`derives from` and not `derive from`.

**A gate that is right and wrong on the same run — GAP-012.** `visual_absent`
fired on 6 of 11 content pages. It reads visual presence from a class list, so a
page whose argument is carried by a ruled comparison table with a highlighted
row counts as carrying nothing visual at all. Screenshots of two flagged pages
settle it: one is genuinely empty and the gate is right; the other is a
well-formed comparison table and the gate is measuring a vocabulary rather than
the page. **Five of the six are tables, so this single question decides whether
the document ships.** It is not widened here, because whether a table is visual
is a design-language decision and not a bug — counting tables makes the gate
weaker in exactly the way 0.1.339's fill floor was gamed by stretching table
rows. It goes to the owner with the evidence.

**A closed vocabulary with no name for a real document type — GAP-013.** The
trace refused to open: the storyline vocabulary has no entry for "here is a
decision, here is what I recommend and why". The refusal is the schema working;
the gap is that the document cannot be traced at all. A vocabulary entry needs a
narrative skeleton behind it, so this is a `storyline-templates.md` change and
not a tuple edit.

Both gaps are the same shape, and it is the one `CLAUDE.md` names: a probe that
keys on class names is asserting a vocabulary, and a closed enum is asserting a
taxonomy. Each was calibrated against the documents that existed when it was
written. A third document found the edge of both on its first run — which is the
argument for building documents rather than reasoning about them.

The build also needed two path repairs in its own source: `scripts/` was
reorganised into `lib/ ops/ check/ build/ render/` during this refactor, and a
source script written before it imported `new_deck` and shelled out to
`scripts/globe_svg.py`. Its output now carries a run number as well as a
version, through `output_dir.next_run_name`.

## 0.1.489 — C3 splits into C3 and C8 on the owner's ruling, and the scoring sheet stops handing a machine's checklist to a human

**GAP-011, closed by owner ruling: split.** C3 carried six evidence items about
four different objects — the page's single claim, its title's assertion, its
elements' relevance, and its figures — so a text-only page could satisfy at most
three of six and scored 3 on a dimension it may have been answering perfectly.
The three figure items become **C8 · Figure quality**, and a document with no
figures scores C8 `n/a` rather than 1.

**The numbering does not shift.** C4 through C7 keep their meanings and the new
dimension is C8, because a dimension id is a name and not an address —
renumbering would leave the recorded scores ambiguous about which dimension they
measured. This is the frozen-rule-id rule applied to the dimension set.
`reviews/scores.json` moves to schema 3; no schema-2 record had ever been
written, so nothing was migrated and nothing was back-filled.

**The scoring sheet was built on a misread of its own evidence, and this
corrects it.** The rubric justified ticking binary items by citing a measurement
that fine-grained binary checklists agree with human judgement far better than
holistic scoring does. **That is a finding about building an automated judge. In
the study the humans were the reference — the humans were not ticking
checklists.** Handing the checklist to the reviewer inverted it: it made her
slower without making the measurement more accurate, because the reviewer IS the
accuracy the checklist approximates.

So the instrument now splits by who is answering. A machine judge ticks the
items; **the human gives one 1–5 rating and one sentence per dimension** — eight
answers instead of fifty-eight. Each dimension states, on the sheet, **what it
protects against**, **where to look** (an instruction that ends in a finite
amount of reading — "sample three pages", never "read the document"), and **an
example answer including its number**, because "give a rating and a sentence" is
an instruction and an example is a demonstration. The evidence items still ship,
folded, marked as prompts to consult when stuck rather than rows to fill.

The three additions are what the owner reported missing after filling the
previous sheet in: a question that does not say what it is for cannot tell her
whether it is hard because the document is bad or because she has misread the
question. The "I cannot read this question" answer (`看不懂`) survives in
place of a rating, and it is
now printed on every dimension rather than once in the header — that is where a
reviewer is standing when they get stuck.

The `scoring sheet parity` guard grew two branches: every dimension must carry
all three prose fields, and no prose field may name a dimension that is gone.
**Deliberate-red, three ways**: a missing PURPOSE, a missing EXAMPLE, and a
`DIMENSION_NA` entry for a dimension that does not exist — each failed with the
dimension named. Two tests that asserted the old checkbox layout were rewritten
against the properties they protected rather than deleted: no arithmetic is
asked for anywhere, and the unreadable answer appears on every dimension.

Both changes fall under `specs/2026-08-15-principles-and-evals-refactor-design.md`
(decision D8, the C-dimension set), which is amended by this release rather than
re-litigated: the design was right that the dimensions are ticked from evidence
items, and wrong about who does the ticking.

## 0.1.488 — five items the reviewer could not read were counted as document failures

**The sheet was used on a real document for the first time, and most of what it
measured was itself.** Of the marks that came back, **five said the item could
not be understood** — and with three states there was nowhere to put that, so
they landed in `否`, which is indistinguishable from the document failing.
**Two of them dragged a dimension to 1 that the document had not earned.**

**A fourth state.** `看不懂` leaves the denominator and does not score: an item
nobody can read is a defect in the item. The count is reported, because a
dimension scored on two of its five items is a weaker measurement than one
scored on five and the reader of the score should be told.

**The five items are rewritten, and all seven dimension names with them.** The
names were the field's own vocabulary — "governing message", "actionability",
"type completeness" — and the reviewer reported two of them unreadable in a
sheet whose own rule says a term is explained where it appears. They are now
**questions in the words a reader uses**: does the reader see the conclusion
first; do the titles read as one argument; does each page hold one claim.
A noun phrase makes the reviewer translate before they can answer. `MECE 抽查（相互独立、完全穷尽）` is
rewritten too, and for a better reason than readability: the reviewer's
objection was that **exhaustiveness cannot be shown**, so the item asked for
something nobody can do. It now asks only for the half that is doable — find one
overlap or one gap — and says that not finding one is not proof there is none.

**The sheet no longer asks the reviewer to compute anything.** It had a
`satisfied ÷ applicable = ____` line under a table that already held the
answers, and every row came back with satisfied greater than applicable, because
a "Yes" written in the not-applicable column is a perfectly reasonable way to
say "yes, it does not apply". The table is marked; the score is computed here.
That is the same rule as machine-written verdicts, applied everywhere in this
package except, until now, the one form a person fills in.

**What the run did produce, and it is the part worth keeping**: four defects in
the document itself, each specific enough to fix — a title mismatch between the
agenda page and the part openers, source lines with no metadata pointer,
limitations not visible where a reader meets them, and supporting material that
never reached an appendix. **The prose reasons were more useful than the
numbers**, which is now said on the sheet.

**A1's scores are not recorded.** Two dimensions carry unreadable items, so the
numbers would be partly a measurement of this sheet, and putting that in
`reviews/scores.json` would file noise as data.

## 0.1.487 — a checkbox with two states called an inapplicable item a failure, and nothing said how ticks became a score

**The owner read the sheet and could not tell how to answer it.** The analysis
agreed with her, and found three separate faults rather than one.

**Ten of the twenty-nine items are conditional and the sheet had two states.**
Three of C1's five ask about an executive summary; three of C3's six only apply
to a page carrying a figure. With tick-or-not-tick, **a document with no
executive summary could reach at most two of C1's five** and nothing said the
other three were never in play — an inapplicable item read exactly like a failed
one. Items now carry three states — yes, no, and **not applicable** — and each
conditional item **prints its condition**, so the third state is a judgement the
reviewer makes rather than a box they quietly skip.

**Nothing said how ticks became a score.** The sheet said "arrive at the number
by ticking the items" and stopped there, so the same ticks could produce
different numbers on two readings — and an agreement study built on that is
measuring the reviewer's mood. The rule is now written down: **satisfied ÷
applicable**, inapplicable items out of the denominator, mapped through a stated
band table; a dimension where nothing applies is **not scored** rather than
scored 1.

**Its assumption is printed, not buried**: items inside one dimension weigh
equally. That is unlikely to be exactly true, and the sheet says it is the first
thing to overturn if the scores stop matching what a reader feels.

**`CONDITION` joins `WORDING` under the parity guard**, because a condition is a
second list keyed the same way and drifts the same way — a caveat left behind
for a withdrawn item would ask about something the sheet no longer asks.

**One fault is left open on purpose.** C3 carries six items about **four
different objects** — the page's claim, its title, its elements, and its
figures — so it is two dimensions sharing a name, and a text-only page tops out
at three of six. Splitting it changes the dimension set and the score schema,
which is the owner's decision and not a formatting one. Recorded rather than
quietly patched.

## 0.1.486 — the sheet is written in the reviewer's language, and the rule requiring that is put back

**A rule was deleted at 0.1.463 and its absence surfaced here.** The old H
section's heading carried "anchors must be written in the reviewer's language,
not internal jargon", and replacing that heading with C1–C7 took the rule with
it. **That is the second rule lost inside a dimension migration** — the first
was old H3's "clear without the body text", restored as C3-⑥ at 0.1.463 itself.

The rule is back in the C section, and it matters more now rather than less: an
anchor was a sentence a reviewer read once, and an evidence item is a line they
tick twenty-nine times.

**`scripts/ops/scoring_sheet.py` emits the sheet in the reviewer's language**,
with the wording table and the rubric parser in `scripts/lib/rubric_items.py`.
The items are parsed out of `eval-rubric.md` and never restated; the wording is
a translation of them, which makes it rule DATA of the same kind as
`check_prose.py`'s Chinese ban list — and why that file, not the CLI, is on the
english-only allowlist. **Repository prose stays English; what a reviewer reads
does not.**

**`scoring sheet parity` guard.** A translation is a second copy, and a second
copy of anything is this repository's oldest defect. The guard fails on an item
with no wording and on a wording naming an item that is gone. **The last sheet
described H1–H6 for two releases after they were replaced**, and nothing caught
it because nothing held the sheet to the rubric.

**Where the shared definition lives was decided by a test, not by taste.** The
first version had `check_repo` load the wording out of `scripts/ops/`, and the
emergency-closure test failed it: an emergency merge would then run the pull
request's own copy of the file being checked. It moved to `scripts/lib/`, which
is where `trace_schema.py` went for the same reason and for the same test.

The sheet also states its own discipline in that language: no mechanical number
appears on it, because a reader who has seen the machine's answer is no longer
an independent measurement.

**Writing it in Chinese found a gating defect in M6.** The metric decides that a
range is an enumeration label rather than an unsourced measurement by looking
for a counting noun BEFORE the number — which is where English puts it. Chinese
puts the measure word after, so the number leads and the counter follows it. So no Chinese enumeration
could match, and what saved most cases was the short-block fallback — meaning
**the same phrase was a label in a short block and an unsourced range in a long
one**. M6 fails the run, so every long Chinese block naming a scale or a group
size was a blocked build, in one of this package's two output languages.

The Chinese measure words now match after the number, and a real unsourced range
is still caught. This is part of E1's execution, under
`specs/2026-08-15-principles-and-evals-refactor-design.md`. **It was found by running the package's own checkers over a
document the package had just written in Chinese** — the first time that had
happened.

## 0.1.485 — a build gets a run number, and the scoring sheet is built from the rubric rather than typed beside it

**Two builds of one version used to land on the same filename.** The second
replaced the first silently, so "the 0.1.483 build" named whichever ran last and
the only way to tell two generations apart was the file timestamp — which is not
something a document carries. `output_dir.next_run_name()` returns
`<stem>.<version>.r<n>.<suffix>`, with `.en.` still inside the suffix so the
language convention the checkers read off a filename keeps working.

**The counter is the directory, not a stored integer.** A saved counter drifts
from the files it numbers the moment one is deleted or copied, and the question
being answered — what is the next unused name — is what the directory already
knows. A test deletes `r1` and asserts `r1` comes back.

**`scripts/ops/scoring_sheet.py`** emits a blind C1–C7 sheet whose evidence
items are **read out of `references/eval-rubric.md`** rather than restated, so a
sheet cannot describe a rubric that no longer exists — the previous sheet
outlived H1–H6 by two releases. Struck items are omitted, because asking a
reviewer to re-check something a gate already holds spends the scarcest resource
in this process on nothing.

**No mechanical number appears on it**, and the sheet says why: a reader who has
seen the machine's answer is no longer an independent measurement, and the
agreement study exists only because that independence does.

This is part of E1's execution, recorded under
`specs/2026-08-15-principles-and-evals-refactor-design.md`.

## 0.1.484 — M13 said "reported" in its target and failed the run in its verdict, for two releases

**The rule text and the code disagreed, and the code was wrong.** M13's target
string has read `=0 (reported)` since it shipped, the rubric describes it as
reported, and 0.1.464's entry says "reported, never gating, and deliberately
narrow" with the reason: a quantity legitimately changes, and **a gate here
would have an author edit correct prose to silence it**. Its verdict was
computed all along, so a document with one flagged contradiction exited
non-zero.

The verdict is now hard-coded `True`, which is how M1 — the other genuinely
reported prose metric — has always expressed the same thing. A test reads the
row out of the source and asserts it.

**Found while updating a deliverable, not by reading the checker.** The E1
rebuild needed the current count of prose metrics that block a run, and getting
that number honestly meant reading all thirteen verdict expressions rather than
trusting the target strings. Twelve could fail; the rule text says eleven should.

**One correction to my own earlier reporting**: `check_prose` and
`check_design` express gating differently. In the design checker a metric gates
only if its target carries `(gates)`; in the prose checker **any** FAIL row
exits non-zero, and `(gates)` on M12 is emphasis rather than mechanism. A count
taken from the design convention and applied to the prose checker is wrong, and
I had taken one.

## 0.1.483 — the new font check fired on both accepted deliverables, and it was the check that was wrong

**D23 counted an `@font-face` declaration as a third typeface.** A face block
*declares* a face; it does not use one. Both accepted deliverables —
`signal-radar-ops-guide` and `adopting-lumi-style` — use exactly the two voices
the tokens define, and the check reported three on each.

**It was found by running the new metrics against real work before believing
them.** The E1 baseline step measures existing deliverables under the changed
rule set, and the first thing it produced was a defect in the newest check
rather than a finding about the documents. A reported metric that fires on
correct work teaches an author to ignore the reported section, and a gating one
would have had them edit the document to silence it — which is the failure this
repository has shipped before and now tests for by default.

Both documents now read 2 used against a ceiling of 2, and the false-positive
case is a test.

## 0.1.482 — the figure grammar moves out of the token file, and the proof changes shape with it

**GAP-010 closes.** How a globe or region map is composed — what the graticule
is for, why a bloc is quieter on the globe than on the flat map, what a label on
a sphere cannot rely on — was comment prose inside a generated token file.
**Half that file was prose: 7086 characters against 14010.** A token file is
read by the build, not by a person forming a judgement, so none of it reached a
reader of `references/` or the `principle trace` guard.

Eighteen grammar blocks are now `design-rules.md` §1.2. The generator emits a
one-line label per rule and one pointer at the top; the token file's prose fell
to 3944 characters, and what stays is the generated-file banner and notes about
CSS mechanics at the site that needs them.

**The proof had to change shape, and saying so is the point.** GAP-007's moves
were content-frozen and provable by comparing the multiset of non-heading lines.
This one crosses formats — CSS comment to markdown — where a line multiset
cannot survive. So the measurement is sentence conservation instead: **41 source
sentences, 39 verbatim, 2 differing only in case** (the CSS comments shouted two
headings in capitals), **0 missing**.

This is GAP-010, opened by 0.1.480's closure of GAP-006 rather than folded into
it, and it belongs to the same refactor as the rest:
`specs/2026-08-15-principles-and-evals-refactor-design.md`.

**And it caught me.** The first draft had reworded two sentences into headings —
"A bloc's FULL membership, outlined when a reader selects it" became "Selecting
a bloc outlines its full membership". Both are restored verbatim. **A move that
rewords is not a move**, and the difference is only visible if the proof is run
rather than assumed.

## 0.1.481 — the two halves of P-1 that nothing held, and a verdict that had been hard-coded to pass

**GAP-008 closes.** P-1 says the brand pack is the single source of visual
identity; what was actually held was the palette.

**D22 · layout vocabulary (gates).** A page claiming a layout `tokens/` does not
define now fails, on the same reasoning as D19 — it is decidable rather than a
judgement about design. **D9 had been collecting exactly this for releases**:
every page whose layout class the tokens do not define went into an `unknown`
list, and then the verdict was hard-coded to `True`. The list was read by
nothing.

**The failing subject was already in the tree.** `deck-degenerate` carries
fourteen pages with no layout class at all, and the suite reported it clean on
that metric the whole time. Nothing had to be planted — which is the clearest
possible statement of what a verdict hard-coded to pass costs.

**D23 · font count (reported).** Distinct font stacks against what the tokens
declare, and **the ceiling is derived, not written**: design-rules says two
voices and the tokens declare two, so a literal `2` in the checker would be
quietly wrong the day a third is added. A test asserts the ceiling moves with
the tokens rather than with the code.

**What is honestly still not covered under P-1**, recorded in the closure rather
than implied away: whether a page's composition is any *good*. That is a
judgement, it belongs to C7 and to the eye, and no metric here claims it.

Adding a seventh gate went red in five files at once — `AGENTS.md`,
`CLAUDE.md`, `brand.md`, `design-rules.md` and the rubric — and the same guard
caught the re-wording breaking the pattern it keys on, which is the failure mode
where a claim quietly stops being checked.

## 0.1.480 — two ledger entries close, and the five rules that had no source get one

**GAP-007 closes, measured rather than recalled.** Each of the four symptoms it
named was checked against the files: `design-rules.md`'s top-level sections read
1–8 with its chart rules 6..14 after the inline 1–5; `storyline-templates.md`
has its four templates adjacent; `eval-rubric.md` carries one gating notation
and one paragraph explaining what gates — the two other appearances of
`(gates)` quote `check_design.grade()`'s own target string where that format is
being discussed, which is a citation rather than a second vocabulary. The
durable half of the closure is the `section citations` guard, built when the
re-flow found twenty-one live citations pointing at moved sections while all
twenty-nine guards stayed green.

**GAP-006 closes with a distinction it had not made.** Two of its families were
already homed by this refactor's other work — the capability-tier rule is P-2's
closing sentence, colophon placement is in `storyline-templates.md`. The
remaining five share a category: **they are rules about how the agent works, not
about what a deliverable is**, which is why none of them fitted the five
existing reference files. `references/operating-rules.md` is their home: the
debug-log contract, the parallel-build protocol and its merge gate,
questions-come-once, scaffold-never-fixture, and generate-a-world-figure-rather-
than-draw-it. It serves **P-2**, because each answers one question — what makes
the result trustworthy rather than merely finished.

**Why they needed a home at all**, since the entry points already stated them:
an entry point is a hand-written restatement by design. A rule whose only home
is one has no source — the restatements have nothing to be checked against, and
the rule means whatever the last edit of that file left behind.

**The false claim is corrected rather than made true.** `CLAUDE.md` called the
core prompt "a strict subset of `references/`" while it carried rules of its
own. It is now described as a derived restatement that may carry
prompt-tier-only rules, and those are named. Making the claim true would have
meant deleting rules that exist because a prompt-tier agent has no tools — a
worse answer than an accurate sentence.

**GAP-010 opens for the residue rather than folding it into a closure.** The
globe and map figure grammar is still comment prose inside
`tokens/region-palette.css` — design rules in a token file, invisible to every
reader of `references/` and to the `principle trace` guard. It is the same
defect one file along, and it is recorded as its own entry.

## 0.1.479 — the fix that was reported and not made, and twenty-four rounds of proving the other one

**Correction to 0.1.476.** That entry said the release tool's stamp positions
"are now a shared `TOKEN_STAMPS` constant". **Half of that was true and the half
that mattered was not.** The constant was created and `check_versions` reads it;
`release.py` was never wired to it and still carried its own eight-row table.
The claim was written from the intention rather than from the code, which is
exactly what convention 14 forbids, and it was found by the owner asking whether
the fix was real.

**Now it is.** `release.py` derives its stamp positions from `ENTRY_STAMP` and
`TOKEN_STAMPS` — the guards' own authority on the same fact — and replaces the
literal version string rather than carrying per-file patterns it cannot invert.
Eight positions, derived, matching the eight that were hand-listed.

**A test now holds it, because a note did not.** `test_release_tool.py` fails if
that file names a stamped path as a bare literal anywhere in it. Its own first
version scanned only from `stamped_files()` downward and a probe inserting the
table **above** that point passed — a test with a blind spot certifies the
region it does not look at. Rewritten to scan the whole file, then red-tested
from three positions: before, after, and at the end.

**The second finding, verified across every stamp rather than the one that
failed.** `references/PRINCIPLES.md` carried a version from 0.1.459 and sat in
no table, so a stamp naming a real EARLIER release passed silently while only a
stamp naming a version that does not exist was caught. Registered at 0.1.476 —
and this release checks **all eight declared positions, three ways each**: a
stale-but-real version, a version that does not exist, and the stamp line
deleted outright. **Twenty-four rounds, twenty-four reds, and the untouched tree
green.** That matrix is what makes the table's completeness a measurement rather
than a claim.

## 0.1.478 — the last seventy shapes are classified by the only method that has not been wrong here: looking at them

**GAP-009 closes.** 70 of the 206 shapes carried no relation, so a third of the
library could not be reached by selection-by-relation — usable, but not findable
by the thing that finds shapes. All 70 are now classified, and `relation_from`
records how: **`looked-at`**, meaning the rendered preview was opened and the
shape classified from what it draws.

**Two earlier attempts classified from the tags and from the page names, and
both were wrong.** The extraction's tags are sparse, and going by them dropped
the `flow-2` … `flow-6` and `cycle-2` … `cycle-8` families. The names lie
outright: `box` is a 2×2 grid with a four-arrow cycle through it, `surround` is
a large directional arrow, and **`p012-footnotesource` is a 3×3×3 cube**. Three
attempts, and the one that worked is the one where somebody looked.

**What looking found that no name would have.** Two of the six contact sheets
are almost entirely **chart primitives** — sorted bars, stacked areas over time,
grouped columns, pie, histogram, scatter, Harvey balls — which is Zelazny's
comparison set in drawable form, and none of it was tagged. And
`p157-illustrative` and `p158-disguised-client-example` are a set of
**"illustrative / preliminary draft / for discussion only" stamps**: exactly
what C4-③ asks a document to carry where an estimate appears, sitting unlabelled
in a library nobody had opened.

**Two categories were added rather than forcing everything into a relation.**
`element` is a basic form that asserts no relation by itself — a plain block, a
single circle — and composes into figures. `apparatus` serves the document
rather than the argument: legend swatches, the disclosure stamps. **Neither is a
reject**, and inventing a relation for either would have been the same mistake
one level along.

The `shape library` guard accepts `looked-at` alongside the other three, and
`unclassified` stays legal because marking one is the alternative to guessing.

## 0.1.477 — the two small globe marks are withdrawn, and the lock they sat under is re-stamped rather than bypassed

**`globe-mark.svg` and `globe-mark-small.svg` are deleted** — the owner judged
them no longer fit for purpose. `build_brand.py` no longer emits them, the brand
README no longer lists them, and `LOCKED.json` no longer carries their hashes.

**What is deliberately untouched**: the field globe (`globe-field.svg`, the
default cover and closing mark), the cover pair, and `assets/vectors/`. That
last one matters — it was checked before anything was deleted, and it is not a
few stale drawings but the data behind `check_globe.py`, `build_brand.py`,
`build_region_palette.py`, D18's region labels and the `data-globe` runtime
D19 resolves. Removing it would have been a capability withdrawal rather than a
cleanup, so the scope was confirmed first and narrowed to the two marks.

**The brand lock fired, which is the mechanism working.** `build_brand.py` is
itself a locked file, so editing it failed the `brand lock` guard. The lock is
**re-stamped with the reason recorded in its own `why` field**, not edited
around: a lock that can be worked past protects nothing, and the record of what
changed and why is the entire point of having one.

## 0.1.476 — the shape library is complete, because both curations of it were wrong

**All 206 units ship.** 0.1.475 shipped 68 of them, curated by the rule that a
shape enters only if its relation serves the chart rules. The rule is right and
the application was wrong, twice over.

**The relation tags are sparse, not authoritative.** 138 units carry none, and
among them are `flow-2` … `flow-6` and `cycle-2` … `cycle-8` — one relation at
several arities, which is the most useful thing a shape library holds, because
the real question at the point of choosing is "how many steps do I have". The
curation dropped all of them.

**The exclusions were made from page names, and the two checked against a
rendered preview were both wrong.** `box` is a 2×2 quadrant grid with a
four-arrow cycle through it, not a text box. `surround` is a large directional
arrow. **A name does not tell you what a drawing is** — and the 2560px preview
of every unit had been rendered days earlier and never opened. Convention 15
says to look at a real instance before writing a rule that keys on its shape;
this is the third time in this run that not doing so produced a wrong model, and
the first time it discarded work rather than shipping a broken check.

**So nothing is excluded.** An absent shape cannot be chosen by anything, while
an unclassified one merely carries no recommendation. `tags.json` gives each
shape its family, relation, `relation_from` (`tag` / `page-name` /
`unclassified`), slot count, metaphor flag and preview path. 68 classified from
the extraction's own semantics, 68 from the template's page titles, **70 left
unclassified and marked as such** rather than guessed at.

**The extraction audit was run, and so was a new one for the ingestion.**
`assets-staging/tools/verify_all.py` follows geometry from source page to
rendered pixel across six checks — coverage, conservation, route choice,
recolour drift, rendered ink, 3D validity — and passes on all 206. It had never
been run against this ingestion. A second check confirms the copy: 206 files,
byte-identical to the staging library, manifest and files the same set, every
tree parses. The half that can live in this repository is now the **`shape
library` guard**: manifest and files are one set, `relation_from` is one of
three legal values, and **no shipped shape is an empty frame** — a file can
exist, parse and render as nothing, which this library produced twice during
extraction. Deliberate-red both ways.

**GAP-009 reopens**, narrowed to those 70: they need a person to look at the
preview, which is the step whose absence caused both wrong curations.

**Two version-stamp findings, from re-reviewing the release tool.**
`references/PRINCIPLES.md` has carried a version stamp since 0.1.459 and was
**never added to `ENTRY_STAMP`**, which `CLAUDE.md` requires — so a stamp naming
a real earlier release passed silently, and only a stamp naming a version that
does not exist was caught. Verified by planting both. It is registered now.
And `release.py`'s own stamp table was a **third copy** of where the stamps
live; the token positions are now a shared `TOKEN_STAMPS` constant, because a
second list of stamp positions arriving through the door marked "release
tooling" is this repository's own worst defect class.

## 0.1.475 — the shape library is curated and ingested: 68 of 206, by one rule applied mechanically

**GAP-009 closes.** 206 figure units were extracted, recoloured to bind design
tokens and verified; what had not happened was curation, and it is a judgement
about the design language rather than a script. It is now done, by the rule
`design-rules.md` §4.1 already stated: **a shape enters only if the relation it
encodes serves the chart rules.**

Applied mechanically: a unit is in if it carries an explicit relation tag —
composition (24), order (39), process (42), hierarchy (12), correlation (3),
degree (2). **68 are in; the other 138 draw no relation** and are page
furniture, single-primitive fragments and label art. Ingesting them would have
produced a second figure vocabulary standing next to §4 rather than a library
serving it.

**The obvious basis for curation was noise, and using it would have been
arbitrary.** The extraction carries a `family_label` per unit, and it looks like
a taxonomy — 134 distinct values. It is OCR'd slide text: "Label 1",
"New entrant", and a CJK source-line label. Curating by it would have grouped a source-line
template with a hierarchy diagram. The relation tags are the real basis, and
checking that before writing the selection was what stopped it.

**Two units were set aside for a person rather than dropped silently.**
`p124-process-objectives-01` and `p109-change-vision-01` are large enough to be
real diagrams and carry no relation tag; their slide labels suggest what they
are, and a slide label is exactly the evidence just shown to be noise. They
stay out until someone looks.

**The selectivity is worth its number.** A deliverable referencing two shapes
embeds 37 KB. The library is 1852 KB. Inlining it would have put fifty times the
geometry a document uses into every document, which is the reason
`embed_shapes.py` exists and the reason it emits only what was referenced.

`assets/shapes/SOURCE.md` records provenance, the licence position and the
selection rule; `tags.json` carries relation, family words, slot count and the
metaphor flag for each shape.

This closes T2 of
`specs/2026-08-15-principles-and-evals-refactor-design.md`.

## 0.1.474 — the release flow becomes a tool, because the rule it broke had already been written down

**`scripts/ops/release.py`.** The release flow was six to eight commands run by
hand, and chaining them in a shell put a commit behind a pipe:

    python3 scripts/preflight.py 2>&1 | tail -2 && git commit ...

`&&` reads the exit status of the **last stage of a pipeline**, and `tail`
always succeeds. Preflight failed, the chain proceeded, and a red release was
committed — **twice in one session, after the lesson had already been recorded
in a previous one**.

A rule that has been written down and then broken does not need writing down
more firmly. It needs a tool that holds it, which is exactly why
`check_evidence.py` executes the command and writes the result itself: a human
typing "pass" is not evidence. So this stamps, regenerates, gathers evidence,
runs preflight and commits — **and refuses to commit when preflight fails, with
no flag to override it**. Nothing is piped anywhere; every exit code is read
from the process that produced it.

Two smaller things it removes. The commit subject is taken **from** the newest
CHANGELOG heading rather than typed beside it, so `check_commit_convention`
cannot be violated by a typo. And a stamp it cannot find stops the release
rather than being guessed at.

**A convention, for the other failure this session kept producing.** Six first
implementations were wrong in the same way: each encoded an assumption about the
material — that a label precedes its number in English, that a figure is
`<figure>`, that a summary keeps its distinctive word — and reading the code
could not find any of them, because reading uses the model that produced them.
`CLAUDE.md` convention 15 now says: **look at a real instance before writing a
pattern that keys on its shape, and run the planted failure first rather than
last.** Five of the six would have died in minutes.

Both conventions and this tool belong to
`specs/2026-08-15-principles-and-evals-refactor-design.md`, which is the
refactor whose execution produced the two failures they answer.

**And this script's own first run found a bug in it**: re-running after
writing a waiver destroyed the waiver, because `--init` rebuilds the
evidence file from the diff. A waiver records that somebody looked at an
unconfirmed thing; losing it loses the only evidence of that. Waivers are
now carried across.

## 0.1.473 — the shape pipeline's last mile, and the one step in it that is a judgement rather than a script

**`scripts/build/embed_shapes.py`.** A deliverable is one self-contained file
and the library is hundreds of figure units, so both obvious approaches fail:
inlining it makes every document megabytes of unused geometry, and pasting a
shape in by hand bypasses the recolour layer and lands on D20. This emits a
sprite of **only the symbols the document referenced**, rebuilt rather than
appended to — a shape that stops being used stops travelling.

Two things follow without new machinery. **D19 becomes this pipeline's
correctness check**: a reference resolving to no symbol already fails, so a
shape referenced and not embedded is caught by a gate that has run for releases.
And **brand purity stops being a discipline and becomes an engineering fact** —
only the recoloured library is a source, so original-palette geometry has no
path into a deliverable for anyone to remember to avoid.

**`design-rules.md` §4.1 — choosing a figure.** Choose by the relation the
content has, never by how a shape looks: a funnel whose values do not decrease
and a 2×2 whose axes are not independent are drawings asserting something the
data does not. Metaphor families are marked with a decoration risk, because each
of them can carry an argument and most of them get used to fill a page.

**GAP-009 · what has not happened, said plainly.** 206 units are extracted,
recoloured and verified in a staging area. **Curation has not happened, and it
is not a mechanical step**: deciding which families' relation semantics serve
the chart rules is a judgement about the design language, and ingesting without
it would put a second figure vocabulary in competition with §4 — the state this
package has spent releases leaving. Vendoring megabytes of third-party geometry
is also a decision the owner should make rather than inherit.
`embed_shapes.py` refuses to run against an absent library **and says why**, so
the gap is loud rather than latent.

This is T2 of `specs/2026-08-15-principles-and-evals-refactor-design.md`, with
its ingestion step named as an owner decision rather than quietly skipped.

## 0.1.472 — a figure may declare the data it draws, and is then held to it

**D21 · the data contract.** A figure can carry the data it draws in a JSON
block beside it, and the numbers on the drawing, the numbers in its caption and
the declared data become three views of one thing. Disagreement between them is
then decidable rather than a matter of reading carefully. This is the structural
half of the figure-text hallucination problem: M13 catches a document
contradicting itself in prose, D21 catches a drawing contradicting its own data.

**Opt-in, and gating once opted in.** A figure that declares nothing is not
failed — most figures in flight declare nothing, and a check that failed them
all would be switched off within a day. **A declaration that contradicts the
drawing is a different thing**: a false contract is worse than no contract, so
that gates.

**Two mistakes of mine, both structural rather than fiddly.** The first version
matched `<figure>` elements; this package's figures are `<div class="fig">`, so
it matched nothing on any real fixture — **I wrote the markup I assumed rather
than the markup in use**. The scan now starts at each declaration and walks back
to the nearest figure container, which works for both. The second: the
declaration was part of what it was checked against, so **every declared value
found itself** and figures whose data flatly contradicted their drawing passed.

**A new gating metric needs a fixture that fails it**, and the suite refuses one
without: a graded metric no fixture can fail cannot be told from a metric
rewritten to return ok. `deck-broken` now carries a figure declaring a series
that is nowhere on it.

**`gating claims` did its whole job.** Adding a sixth gate went red in five
files at once — `AGENTS.md`, `CLAUDE.md`, `brand.md`, `design-rules.md` and the
rubric — each of which states the gating set in its own words. Every one is now
correct, and the guard also caught my re-wording breaking the pattern it keys
on, which is the failure mode where a claim quietly stops being checked.

This is T3 of `specs/2026-08-15-principles-and-evals-refactor-design.md`.

## 0.1.471 — a language model may object to a sentence, and must be able to quote it

**`scripts/ops/judge_findings.py`.** A judge that scores is fooled by fluent
verbosity — that is measured, and it is why C1–C7 is ticked rather than rated.
But a judge that points at a specific sentence and says what is wrong with it
does something no metric can: it reads register, which is the half of P-3 that
will not mechanise.

**Every finding carries a verbatim quotation, and the quotation must appear in
the document.** Not resemble, not paraphrase — appear. **This is where a
hallucinated finding dies**: a model that cannot produce the sentence it objects
to has not found anything. The match is made after flattening whitespace and
stripping tags, because the model saw the rendered text and must not be held to
markup it never read; a real quotation survives that and an invented one does not.

**There is no field for a score**, and a finding carrying one is rejected rather
than trimmed. A fragment shorter than three words is rejected too — it would
match almost any document.

**Reported, never gating.** These are opinions with evidence attached, and
gating on them would have an author editing a document to satisfy a model's
taste, which is the register this whole rule set exists to keep out.

Exercised against a real fixture with four findings: the true quotation was
accepted, and an invented objection, a one-word fragment and a finding carrying
a score were all dropped for their own reasons.

This is P3.5, completing P3 of
`specs/2026-08-15-principles-and-evals-refactor-design.md`.

## 0.1.470 — the ledger reads the traces, drafts candidates, and ratifies nothing

**`scripts/ops/ledger.py`.** `trace.py` records what happened; this reads the
accumulated record and keeps three ledgers. Which metric keeps failing — the
same bar missed repeatedly is either a real weakness or a bar set wrong. Which
**instrument** is suspect — a metric more often unmeasurable than measured, or
one that never fails on anything. And what the constitution recorded: refusals
to emit, which clause yields, and how many builds were abandoned.

**Instruments are checked before thresholds, and rank above them in the queue.**
Three of this repository's last five findings were instrument defects, and a
wrong ruler contaminates every measurement taken after it.

**It ratifies nothing.** Every candidate is a draft carrying its trace ids and
counts. The whole input to this loop comes from the agent being measured, and an
automated path from "the numbers moved" to "the rules changed" would let a bad
instrument rewrite the rules it is failing.

**The queue has all three rules**, because one without them fakes health:
drafted per N pieces of the same evidence rather than on a schedule; ordered
instrument-first; and **nothing is dropped** — over capacity a candidate is
marked deferred and printed, since a queue that silently empties reports health
it does not have.

**The efficiency board admits only runs that passed the quality line**, because
a thin deck is cheap and worthless and a board that ranked one would reward the
exact behaviour every other check here exists to catch. Discussion and outline
are not charged: the thinking a user was asked to do is not the pipeline's cost,
and charging it would push everyone back toward the template path.

**Running it found a distinction I had collapsed.** The trace recorded `n/a` —
a Chinese ban list on an English deck — as `not_measured`, so the first run
reported three perfectly healthy metrics as broken instruments. They are three
states, not two: does not apply, applies but could not run, and ran. The fix is
in `trace.py`, and it is the same discipline as "not measured is not zero", one
level along.

**An empty ledger prints that it is empty and says so is not a clean bill of
health** — an empty ledger and a healthy one look identical from here.

**The conformance board is now formally stale, and this release says so.**
Fourteen releases changed SKILL.md'''s pre-delivery steps, replaced H1-H6 with
C1-C7 and added two checkers a conforming agent must run. Whether each agent
still follows the skill is **unknown, not passing**. Refreshing the board drives
real agents through the harness, which needs credentials this repository does
not hold — an operator step the owner schedules, not something a release can
satisfy on her behalf. Recorded as a named waiver rather than carried forward
quietly.

This is T1's analysis half and P5 of
`specs/2026-08-15-principles-and-evals-refactor-design.md`.

## 0.1.469 — the storyline beat gets a machine half, and a script that prints the titles without judging them

**`scripts/check/check_outline.py`.** The fourth beat agrees titles, order and
the logic joining them before anything is built, and it is **the only defence
completeness has** — C5 reports and never gates, so a missing section is caught
there or not at all. This is the cheap half of that beat.

**What it decides**: topic-label titles ("Market overview" asserts nothing, and
a deck of labels cannot read as an argument however good the pages are); group
size, two to five; and whether a section the storyline typically carries is
neither named nor declared. **An outline may declare an omission** —
`omitted: <section> — <reason>` — which is the whole distinction between having
forgotten a section and having decided against it. A declaration without a
reason fails, because a bare one separates nothing from nothing.

**What it refuses to decide**: whether the titles in order are an argument. It
prints them as one paragraph and says nothing about whether they cohere. That
judgement is the point of the beat, and a checker pretending to make it would
replace the beat rather than serve it — a test asserts no finding claims to.

**Its completeness comparison can be gamed, and it says so.** The check is a
substring match against the titles, and an author could satisfy it by naming a
section in a title that is not about it. **That is precisely why it reports and
does not gate**: gaming a reported line costs effort and buys nothing, while
gaming a gate buys a green run. A completeness gate would be worth defeating.

`TYPICAL_SECTIONS` joins the registry as **a checklist applied at the end,
never a template to start from** — the evidence against template-first work is
why the pipeline was turned around, and this list used as a starting point
would reintroduce exactly what that turn was for.

This is P3.6 of `specs/2026-08-15-principles-and-evals-refactor-design.md`.

## 0.1.468 — the score store moves to C1–C7 and finally requires the key its own study joins on

**`reviews/scores.json` schema 2.** Dimensions are C1–C7, and **`corpus_id` is
required on every new record**. The agreement study joins a machine reading to a
human score on that key, and neither existing record carries one — which is the
entire reason that study has never had a single joinable row. Requiring it is
the smallest change that makes K3 reachable at all.

**History is kept verbatim rather than back-filled.** The two schema-1 records
keep their H1–H6 shape and carry `"schema": 1`; the validator branches on it.
Inventing a corpus id for a document nobody can re-measure would put a
**fabricated join key into the evidence**, which is worse than the gap it hides.

**Two steps become permanent CI.** `review_scores.py --check` and
`eval_agreement.py --report` now run on every release, so the study's state is
visible rather than remembered. **`--report` exits 0 on purpose**: the study's
blocker today is an open ledger entry, and a release does not gate on a known
gap — it records it. Without `--report` the script still fails loudly, because
a study nobody can run should be loud when someone runs it.

**The prediction map was re-derived, not transliterated.** `PREDICTS` moved from
H to C by asking what each machine reading is actually a proxy for — C2 is the
storyline read through the titles, C3 the argument on one page, C4 sourcing —
and gained two entries. They are **hypotheses the study exists to test**, not
findings; a mapping that never disagrees with its dimension is either right or
measuring the same thing twice.

The blind scoring sheet follows the new dimensions, so a reviewer is not handed
a form for a rubric that no longer exists.

This is P3.2 and P3.3 of
`specs/2026-08-15-principles-and-evals-refactor-design.md`.

## 0.1.467 — what this product is, written down, and a brand registry that is not allowed to grow rules

**`specs/2026-08-16-product-definition.md`.** Every other file in `specs/`
records a decision already taken; this one states what the product is, and is
meant to be read before them. One sentence, who it is for, what it does in the
order a user meets it, what it refuses to do, and the five criteria for telling
whether it works — all written as outcomes rather than as work completed.

Two of those criteria carry their own knife. **K2 is self-falsifying**: if
documents from the discussion path do not score better than documents from the
template path, the four-beat design goes back for review rather than being
defended. **K4 promises measurable and specifically not cheaper**, because
without a baseline that claim is unavailable.

**`brands/registry.json` + the `brand registry` guard.** One record per brand,
answering which asset pack and which wordmark — and **nothing else**. The guard
rejects a record carrying a palette or a rule, because a brand record that
started holding either would become the fifth surface restating them: the exact
defect this refactor exists to remove, arriving through a new door. Every path a
record names must exist, since a registry pointing at a missing asset pack is
worse than no registry — a build reads it and produces a cover with nothing on it.

**The two checkers caught each other on the day the second one shipped.** The
`secrets` guard failed on `check_privacy`'s own test fixture, which contains
AWS's documented example key to prove layer 1 can fire. Waived by path with the
reason, which is what that table is for — never by narrowing the pattern.

This is P2.1 and P2.5 of
`specs/2026-08-15-principles-and-evals-refactor-design.md`.

## 0.1.466 — P-5's other half gets an implementation, and a third layer that says it is not one

**`scripts/check/check_privacy.py`.** "Every page states how it may be handled"
has been D12 for a long time. "Sensitive information does not leave the document
boundary" had **nothing behind it at all**. Three layers, because sensitivity is
not one kind of question:

**Layer 1 gates** — credential shapes, and terms declared out of bounds for this
engagement. Both are yes/no facts about the text. It searches the whole file: a
token in a `data-` attribute has left the boundary just as surely as one in a
paragraph.

**Layer 2 reports** — an email address, a direct phone number, a private-range
host, a home directory path. A deliverable legitimately carries a contact
address, and a gate here would teach authors to delete real content to silence a
checker.

**Layer 3 is not mechanised, and the script says so.** Whether a passage of
commercial analysis is sensitive is a judgement. It is named at the pre-delivery
step as a question for a person. A script that implied it had covered layer 3
would be worse than one that stops at layer 2.

**Not attempted is not passed.** With no `--terms` list the term half reports
NOT ATTEMPTED and exits non-zero, on the same reasoning that keeps
`not_measured` distinct from zero everywhere else here.

**The out-of-bounds list never enters this repository.** It is read from a path
the operator gives, held for one run, and written nowhere — **the findings do
not echo the term itself**, which a test asserts. A file of a client's forbidden
words is the most engagement-specific data there is, and red line 9 says this
repository holds none.

**Layer 2's first version produced six phone numbers on a clean fixture, none of
them a phone number.** They were the geography SVG's `data-arcs` attribute, a
few hundred indices in which "104 105 1061" is phone-shaped. The fix was
structural rather than a tighter pattern: layer 1 searches the whole file
because a credential anywhere has escaped, layer 2 searches only what a reader
sees because contact details are the only thing it is about. **A reported
section that cries wolf is a reported section nobody reads**, and eight of the
twelve tests are false-positive tests for that reason.

**Two of this release's own bugs are worth recording.** The trailing guard on
the phone pattern excluded punctuation, so a phone number at the end of a
sentence — the normal case — was never found. And a comment added to the pattern
landed **inside** the raw string, making the regex require its own explanatory
text; it matched nothing at all. Both were found by running it, neither by
reading it.

This is P2.4 of `specs/2026-08-15-principles-and-evals-refactor-design.md`.

## 0.1.465 — genre stops answering two questions, and the tier is derived from behaviour rather than asserted

**`genre` was carrying two jobs**: which thresholds and prose rules apply, and
what shape the argument has. A market analysis and a status report are the same
tier and different stories, and one field answering both is why five scripts
once held five different genre lists.

**The split.** `genre` keeps the rule tier. A new `storyline` axis carries the
narrative skeleton, with a closed vocabulary in the registry and in the trace
schema — a trace naming a storyline the registry does not define is refused,
because a closed schema that accepts anything is not closed.

**The tier table is derived, not invented.** Three tiers, and each is a claim
about code that already exists: `internal` is the tier `check_prose`'s
`DASH_BANNED` leaves exempt, and `training` is the tier `inspect_layout`'s
`VISUAL_SHARE_TARGET` puts at 30 where everything else is 50.

**`two-axis vocabulary` guard** holds the table to those two facts. Change
`DASH_BANNED` or `VISUAL_SHARE_TARGET` without changing `TIERS` and it fails —
otherwise the tier becomes a label with nothing behind it, which is exactly the
state `genre` was in before the split. Deliberate red both ways, plus a test
that an empty storyline vocabulary fails rather than passing as decorative.

**The obligation that worried everyone does not multiply.** Accepted references
hang off the **tier**, so there are three to accumulate. Six storylines add
none, and `tier_of()` raises loudly rather than defaulting — a genre resolving
to a default tier would grade a document against rules that are not its own and
report it green.

This is P2.2 of `specs/2026-08-15-principles-and-evals-refactor-design.md`.

## 0.1.464 — the first check that asks whether a document contradicts itself, and the version of it that did not work

**M13 · one quantity, one value.** Until now a deliverable could state
"4.2 million" and "4.5 million" of the same thing on two pages and every metric
stayed green. This is the most direct hold there is on figure-text
hallucination, and nothing held it.

**The first implementation found nothing on a document written to contradict
itself.** It took the words immediately BEFORE a number as the quantity's
label, which in English gathers verbs and prepositions — "stood at", "put it
at" — rather than the name of the thing being measured. Two mentions of the
same quantity produced two different labels and no conflict. The rewrite
anchors on a **repeated two-word noun phrase** and looks **forward** for the
number, which is the order the language actually uses.

**It is reported, never gating, and deliberately narrow.** A qualifier anywhere
near either mention silences it — a year, a quarter, target/actual, a region,
a phase — because those are different quantities rather than a contradiction.
Four of the seven tests are false-positive tests for exactly that reason: a
checker confident enough to make an author edit correct prose is the failure
this repository has already shipped once, and the cost of a false pass here is
a missed contradiction while the cost of a false failure is the prose itself.

**Verified against every fixture and a real deliverable** before it shipped:
zero findings on all of them, and a planted contradiction found.

This is P3.4 of `specs/2026-08-15-principles-and-evals-refactor-design.md`,
and it closes C4-②.

## 0.1.463 — H1–H6 becomes C1–C7, scored by ticking evidence rather than by forming an impression

**The rubric's human half is replaced.** Six dimensions written as anchors a
reviewer read and rated are now seven dimensions scored by **ticking binary
evidence items**. Two measurements decided the form: fine-grained binary
checklists agree with human judgement far better than holistic scoring, and LLM
judges are reliably fooled by fluent verbosity. The items count things; they do
not rate feelings.

**Only what a machine cannot decide is on the list.** Items a gate already holds
are struck through and name the gate — asking a reviewer to re-check something
already gated spends the scarcest resource in this process on nothing. Each item
also says whether it can run at the **outline stage**, which is what a storyline
review can check before the document exists.

**Scoring and release are separated, and the dividing line is decidability
rather than importance.** C1–C7 score quality; P-5 and P-6 are pass/fail at the
pre-delivery gate. Every clause from P-1 to P-5 is a MUST — what differs is that
"did it leak" is a decidable binary fact while "how well sourced is it" is a
matter of degree.

**One evidence item is restored that the earlier mapping lost.** Old H3 read
"every figure's message is clear **without the body text**", and the three items
it was mapped onto cover form-fit, family semantics and sourcing — none of which
asks that. Verified in code: `check_design.py` has no axis, unit or legend check,
and `design-rules.md` does not contain those words. It returns as C3-⑥.

**Completeness gains its third option.** It reports, and the document may
**declare** a gap with a reader-visible scope note carrying `data-omitted`.
Reader-visible is the whole point — every precedent prints the declaration for
the reader — and a checker that decided section existence by grepping headings
would be enforcing the one thing those standards decline to enforce.

**Two stale numbers went with it.** The design-diagnostics heading said "four
named exceptions" while the table gates five (D12, D14, D15, D19, D20); the
count is gone rather than corrected. And `H1–H6` is re-flowed out of `SKILL.md`,
`README.md`, `AGENTS.md` and the core prompt — the two places it survives are
field-test anecdotes, which now say which dimension replaced it.

**One thing this release caught in its own draft**: a CJK character in an
English rule file, from a keyboard slip. The english-only red line found it.

This is P3.1 with P0.4 folded in, of
`specs/2026-08-15-principles-and-evals-refactor-design.md`.

## 0.1.462 — a trace whose verdicts the measured agent cannot write, and which opens before the build rather than after

**`scripts/ops/trace.py`.** Every claim this repository has made about its own
quality has come from whichever agent was being measured; 0.1.415 reported all
gates passing having run eight of seventeen. `check_evidence.py` answered that
for releases by executing the command and machine-writing the result. A trace is
the same discipline applied to a build, and three properties are enforced by the
shape of the tool rather than by whoever runs it:

**Verdicts are transcribed, never supplied.** `close` runs `check_prose.py` and
`check_design.py` with `--json` and copies their `verdicts` and readings. **There
is no flag for stating a result** — a test asserts that `--gate`, `--verdict`,
`--pass` and `--result` appear nowhere in the CLI, which is the same reason
`check_evidence.py`'s schema has no verdict field.

**A trace opens when the storyline is agreed, not when the deliverable is
finished.** A record written only at the end never captures an abandoned build,
and that bias runs one way: toward success. An open record with no `closed_at`
is itself the evidence that a build was abandoned.

**No free text anywhere.** Every field is closed-vocabulary or a number, and the
tool refuses to write a record that fails validation. `principle_yields` names
two clauses and a stage; `refused_to_emit` names the clauses that collided and
the stage — **the reasoning goes to the debug log, which never leaves the
delivery directory**. Red line 9 is held by a schema rather than by intentions.

**`trace schema` guard**, which **imports the schema from `trace.py` rather than
restating it** — a guard carrying its own copy of a field list would be the
purest instance of the defect this repository spends most of its releases
fixing. An empty `evals/traces/` is a legal state rather than a vacuous pass:
the repository ships no traces, and the synthetic tests are what prove the guard
can fail. Deliberate red: a stored trace carrying a free-text field fails.

**One correction found by running it.** The first transcription assumed the
checkers emit `rows` with an `id` and a `verdict`. They emit a list of one
record per file carrying `verdicts` and `targets`, where a gate is marked by
`(gates)` in the target string. Written from the assumption, the collector
crashed on the first real deliverable — which is the cheap version of the
failure this whole mechanism exists to prevent.

**The schema lives in `scripts/lib/`, not beside the CLI.** A test caught the
first placement: `check_repo.py` importing from `scripts/ops/` would make the
emergency-merge path execute the pull request's own copy of the thing it is
checking. Moving it to `lib/` also put it under the no-shadow-math rule, which
is where a shared definition belongs.

This is P2.3 of `specs/2026-08-15-principles-and-evals-refactor-design.md`.

## 0.1.461 — rule ids that are names rather than addresses, which is the whole point and which the first version got backwards

**Twenty-seven rule families now carry a stable id** (`BR-`, `DR-`, `WR-`,
`ST-`, `ER-`), declared beside the clause each family serves. The id is what a
parent declaration, a trace and a future candidate proposal attach to, and it is
what makes the next structural reorder cheap: a section can move without
anything that cites the family breaking.

**The first version derived the id from the section number, which defeats the
entire purpose.** An id derived from position moves when position moves — the
reorder two releases ago would have renumbered all of them — and §1.1 and §1.2
collapsed to `DR-11` and `DR-12`, which collide with a future eleventh section.
Ids are now assigned in document order once and **frozen**: an id is a name, not
an address.

**`rule ids` guard**: ids are unique, every family that declares a parent also
declares an id, and **no id that has existed may vanish** — a cited id that stops
existing is the same class of breakage as a moved section citation, one level up.
The frozen set lives in the guard as the code side of the parity, which is this
repository's pattern for a count that must not rot.

**Deliberate red, both ways**: a duplicated id fails, and a deleted id fails
twice over — once for the family that now has no id, once for the id that
vanished from the frozen set.

This is P0.5, completing P0 of
`specs/2026-08-15-principles-and-evals-refactor-design.md`.

## 0.1.460 — the summary that may reword but may not drop a rule, and P-1's coverage gap written down instead of implied

**`red line parity` guard.** `SKILL.md` is the red lines' home and the generated
entry points already lift the block from it. `AGENTS.md` restates them by hand
on purpose — it is a file people read, and assembled prose is worse prose — so
it gets a parity guard rather than generation. The guard checks the count on
both sides and, for each red line, that the summary keeps at least one of the
words that distinguish that rule from the others. **The anchor words are derived
from `SKILL.md`, never listed in the guard**: a guard that hand-lists what it
checks becomes a third copy of the thing it exists to keep in sync.

**Its first version was wrong in the most instructive way.** It demanded the
single longest distinguishing word and immediately failed on `AGENTS.md` saying
"standard Chinese term" where `SKILL.md` says "established Chinese term" — the
same rule in different words. The available "fix" was to insert a word into
`AGENTS.md` for no reader's benefit, which is a checker editing prose to satisfy
itself. Asking for any one anchor instead lets a real paraphrase through while a
dropped rule still fails. **The limit that leaves is written into the guard**:
a summary that rewords every distinguishing word of one rule reads exactly like
a summary that dropped it, and that is the right side to err on — a false pass
costs a stale summary, a false failure costs the prose.

**A red-team run that silently planted nothing.** The first deliberate-red for
this guard replaced a sentence that contains a line break, so the replacement
never matched, the violation was never planted, and the run reported no failure —
which reads identically to a guard that cannot fail. Caught by checking that the
edit had actually happened. Both directions then fired: a dropped rule, and a
seventh red line added to `SKILL.md` while both summaries still said six.

**GAP-008 · P-1 is stated wider than anything checks it.** The palette is held
by D20 and its neighbours; typography and layout are only partly covered, and an
agent inventing a seventeenth page layout is caught by nothing — verified in
code rather than assumed. A principle should be wider than the checks of the
day; recording the difference is what stops it being read as coverage.

This is P1.4–P1.5 of
`specs/2026-08-15-principles-and-evals-refactor-design.md`, completing P1.

## 0.1.459 — the constitution ships, and the guard that holds every rule to a parent it must name

**`references/PRINCIPLES.md`.** Six clauses (P-1 brand consistency, P-2 grounded,
P-3 plain language, P-4 figures over prose, P-5 safety and compliance, P-6
accountability), each carrying its own obligation strength. **There is no
ordering between clauses**, and the file says why: no major professional code
ranks its own principle set, a strict order is only lossless where each
criterion outweighs the sum of all below it, and with continuous scores the
lower clauses are never reached at all. Irreversibility of harm is why a clause
has the strength it has — it is not a ranking between clauses. The file opens by
saying what it constrains: **how rules are made and where they belong, not the
writing of any individual document.** A constitution that restated the rules
would be the worst instance of this repository's dominant defect, and it
restates none.

**The conflict exit, at both places it has to exist.** When two MUST clauses
cannot both be satisfied after the rule has been read as precisely as it can be:
record the conflict and the reasoning, refuse to emit, hand it to a person. It
is written into `SKILL.md`'s pre-delivery step and `storyline-templates.md`'s
critic gate, because **a procedure that exists only in the constitution is not
executed at the moment it applies**. Both copies say it is rare by construction
and is not a way out of an inconvenient rule.

**`principle trace` guard.** Every rule family in `references/` declares the
clause it serves, or `GOAL` — which means it serves the product's purpose rather
than a constitutional clause, and is a legitimate parent rather than an orphan.
The clause set is read out of `PRINCIPLES.md` rather than hard-coded, so a
seventh clause needs no edit to the guard and a citation of a clause that does
not exist fails. Twenty-seven declarations ship with it.

**The guard's limit is written into the guard.** It verifies that a declaration
exists and names a real clause. **It cannot verify the right parent was chosen** —
that stays human judgement, in the same class as every other semantic drift
between prose copies. A guard that looks stronger than it is will be trusted for
more than it does.

**Deliberate red, three ways**: a family with its declaration deleted fails; a
family declaring a clause `PRINCIPLES.md` does not define fails; and removing
`PRINCIPLES.md` itself fails rather than passing vacuously. This is P1.1–P1.3.

This is P1.1–P1.3 of `specs/2026-08-15-principles-and-evals-refactor-design.md`.

**Recorded as still owed**: the chart-rule family in `design-rules.md` §4 serves
three clauses at once (form selection P-4, accent colour P-1, source line P-2)
and declares P-4 with the other two named in prose. P0.5's rule IDs split it.

## 0.1.458 — the four templates now sit together, and the plan item that would have edited the same prose twice was moved out of P0

**The move.** `storyline-templates.md` ran Template 1, cover-and-closing,
part-openers, Template 2, Template 3, Template 4, shared discipline — two
universal sections wedged between the first template and the rest. The four
templates are now adjacent and the three universal sections follow them.
Content-frozen, proved the same way as 0.1.457: the multiset of non-heading
lines is identical.

The plan had said "move the shared apparatus ahead of the templates". Reading
the file changed the answer: an agent arrives knowing its scenario, so the four
templates being adjacent is what makes the file findable, and material that
applies to all of them reads better after them than before. Recorded here
because the plan is the artefact that was wrong, not the file.

**P0.4 is withdrawn from P0 and folded into P3.1**, for two reasons found by
executing rather than by planning. Collapsing `eval-rubric.md`'s three
descriptions of what gates is **rewording**, and P0's entire safety property is
that its commits are content-frozen and prove it — mixing the two is on this
repository's own do-not-do list. And P3.1 rewrites that file anyway when H1–H6
becomes C1–C7; doing it now would edit the same prose twice and put the two
edits in conflict.

**The evidence file for 0.1.457 gained its `spec` field.** The gate asks any
release changing more than 150 lines of `scripts/`, `references/` or `tokens/`
to name the spec it implements, and this refactor has one.

## 0.1.457 — the reference file a person could not read in order: five sections moved, nine chart rules renumbered, and the citation guard that should have existed for it

**The reorder (GAP-007's check, first half).** `design-rules.md` ran its sections
1, 1c, 1d, 2, 3, 4, 4b, 5, **7, 6** — section 6 physically after section 7 — and
numbered its chart rules 1-5, 6, 7, 7b, 7c, 7d, 7e, 8, 8b, 9. It now runs 1
(with 1.1 and 1.2), 2 … 8, with the chart rules 1-5 then 6..14. Nothing was
reworded: the commit proves it by comparing the multiset of non-heading lines
before and after, which is identical. The Contents block was regenerated from
the headings rather than hand-edited, because a hand-edited index is the class
of defect that shipped dead anchors at 0.1.441.

**The citation guard this release exists to add.** Twenty-one live citations
across `SKILL.md`, four scripts and two token files pointed at the moved
sections, and **every one of the twenty-nine guards stayed green** — `check_links`
only sees markdown link syntax, so a §-citation in prose or in a code comment
was invisible to it. The implementation plan for this work had named the link
guard as its safety net; that assumption was wrong and was found by testing it
rather than by reading it. `section citations` now resolves every
`<reference>.md §N` against the sections that file actually has. `CHANGELOG.md`
and `specs/` are exempt by construction: both cite the numbering that was true
when they were written, and history is not re-flowed.

**Deliberate red, both directions**: a citation to a section that never existed
(§99) fails, and a citation left at the pre-reorder number (§1d) fails — the
second is the exact mistake the reorder invites. Five synthetic-tree tests ship
with it, including one asserting the guard reports an error rather than passing
vacuously when it finds no reference files at all.

**One code citation was to a rule number, not a section.** `inspect_layout.py`
cited "design-rules §4 rule 9" for the mark-proportionality rule, which the
renumbering moved to 14. Rule-number citations are not covered by the new guard
and are recorded as such rather than claimed.

This is P0.1 and P0.2 of the refactor recorded in
`specs/2026-08-15-principles-and-evals-refactor-design.md`, whose plan file
decomposes the rest.

Rule revisions come only from review retrospectives (divergence ≥2 → retrospective
→ revision), recorded here with a version bump.

## 0.1.456 — the owner read the rule set and could not follow it; the sweep that checked found ten contradictions and seventy code-only numbers

The owner read `references/` end to end and said the evaluation's categories and
order are scattered, patched together across iterations, with no main line a
person can follow. **The skeletons agree with her**: design-rules' section order
is 1, 1c, 1d, 2, 3, 4, 4b, 5, 7, 6 — section six sits after section seven — and
its chart section numbers its rules 1-5, 6, 7, 7b, 7c, 7d, 7e, 8, 8b.
storyline-templates wedges its shared apparatus between Template 1 and
Template 2. The rubric describes three gating surfaces in three places with
three vocabularies, and its author (this one) patched it twice the day before
rather than restructuring it. The cause is structural and recorded as GAP-007:
convention 2 admits rules only from per-defect retrospectives, so every rule
lands as a patch at the site of its wound, and no structural release has ever
run. The disorder is the bill for a process that optimises each sentence's
truthfulness and never the reader's path. The decisions, and the two declined,
are in `specs/2026-08-14-rule-consolidation-design.md`.

**The full sweep behind the answer.** Two exhaustive passes — one over every
code constant, one over every prose rule outside `references/` — found roughly
one hundred and eighty quantitative constraints on a deliverable, some seventy
of them stated in no reference file, whole rule families whose only home is an
entry point or a CSS comment (the debug-mode contract appears nowhere in
`references/`; the globe and map figure grammar lives as comments in
`region-palette.css`), and **ten contradictions between copies of one rule**,
including one inside a single file: `lumi-theme.css`'s header comment said
display weight 400 five lines above `--w-display: 700`. GAP-006 records the
homeless-rules half; the numeric half is closed below.

**`references/eval-inventory.md`, generated.** Every metric row with its target
and tier, every rendered-layout verdict, every discovered module constant with
its own comment and a cross-check column saying which reference file states the
number — where **CODE ONLY** is the finding, not a formatting choice. Generated
rather than hand-copied, because the hand-copy was tried and measured:
twenty-six releases of this repository fix a prose copy disagreeing with its
code, and a hand-written inventory of the checkers' numbers would be the
largest such copy ever created. `--check` joins CI, and the constants are
discovered rather than listed, so a new one appears on the next build without
anyone remembering it. This is the one owner-directed exception to
"references/ stays hand-written", and CLAUDE.md's architecture section now says
so beside the convention it excepts.

**Ten contradictions, resolved by the standing rule that tokens win.** Display
weight is 700 (design-rules said 400; the token file's own header agreed with
the wrong copy). The part-opener display is 80px on the slide and 72 on the
sheet, and the cover sets SMALLER at 58 (brand.md and the core prompt both said
"80/50" and folded the cover in). Support lines are 17px (brand said 16).
`eyebrow_latin` tracking is .08em (the JSON mirror still said the .3em the deck
retired). The colophon lives on the closing page only (storyline-templates
still listed it among the cover's contents, releases after SKILL.md moved it —
a reader had rejected the duplication). AGENTS' red line 4 regains the
one-frame-under-60% clause its siblings carry. The Chinese label for
illustrative values (`示意`) moves from an entry point into writing-rules §4 as
rule data. SKILL's map/globe citation pointed at §6, which is "Numbers are the
copy"; the split lives in §1d. The rubric's twelve-item enumeration of the
`--deliverable` verdicts — which five files counted four different ways — now
names `deliverable_verdicts` as the list and the inventory as its render.

**A withdrawn rule was still printing, and an unargued one was flagging the
accepted document.** `check_design` carried the 40% layout-share cap 0.1.340
withdrew — the retired register records the withdrawal, and the checker went on
printing an advisory against it for a hundred releases. Beside it sat a
five-distinct-layouts floor no retrospective ever argued, and it fired on the
document the owner accepted (3 distinct layouts across 28 pages): an advisory
that flags the accepted reference is measuring its own taste. Both are gone;
D9 states the numbers and a reader judges them.

Carried in the same release: the agreement study's tooling — 
`scripts/ops/eval_agreement.py` (blind scoring first, the machine half cached,
the output a disagreement list rather than a coefficient, because ten documents
cannot power a correlation and the useful product is the pages where machine and
reader part company), an optional `document` field on review records that admits
only corpus ids and refuses filenames (red line 9 holds by shape, not by
discipline), and `eval_corpus --json` keeping its stdout parseable — its notes
had been landing in the stream, which is the same defect the debug log fixed
two days ago.

## 0.1.455 — an Evals suite that measures a document against one that was accepted, and the four faults found while building its foundation

The owner stopped a multi-agent comparison and asked for the thing that should
have come first: **define what "good" is, from the document that meets the
product requirement, before comparing anything to anything.** She is right, and
the reason is measurable — every gate and `=0` check the accepted document takes,
it clears with a zero count, so they prove the checkers RUN rather than that they
DISCRIMINATE. A deck she rejected cleared every design verdict too. The decisions,
and the three that were declined, are in
`specs/2026-08-14-evals-foundation-design.md`.

**So the Evals sit on the quantities that separate the two**, and none of them
had a threshold before:

| | accepted (training) | rejected (sales) |
|---|---|---|
| content pages with nothing visual | **0.0%** | 45.5% |
| figures per content page | **0.957** | 0.227 |
| list items per content page | **0.739** | 4.409 |
| median visual share | **81%** | 16.5% |

`evals/thresholds.json` carries the bars per genre and — the point of the file —
**the evidence that set each one**: `calibrated` only for the two genres with a
document on record, `inherited` where a rule already stated the number,
`provisional` where it is reasoned and unmeasured, `declined` where a bar would
be wrong. This package withdrew an invented threshold once (0.1.339's 82% fill
floor, met by stretching table rows, its reader scoring three dimensions at 1),
and that withdrawal is why the field exists. How many cells hold each level is in
the file and deliberately not repeated here — a count in prose is what this
package keeps finding one release behind, and the first draft of this sentence
was already wrong by two.

`scripts/ops/eval_corpus.py` scores one document or the recorded corpus. The
accepted document clears every bar; the rejected one misses every bar.

**And none of it gates, which is the release's own finding against itself.** A
red-team pass took the rejected document and cleared all four bars with two
mechanical rewrites that add no fact and no idea: every `<li>` re-tagged as
`.vows` markup — the same words under a class `VISUAL_BLOCKS` counts — and one
decorative rect-only SVG per prose page. `rect_only_share` and `shape_kinds_min`
saw it (0.667 and 1) and an earlier draft of this table had demoted exactly those
two for not separating a two-document corpus. **Dropping a metric because a small
corpus does not fail it removes the lock and leaves the door**; they are printed
beside the figure bar now, with that history.

Both are recorded rather than left in prose: **GAP-004** (the bars are gameable and calibrated on two documents; the agreement study is the check that would close it), **GAP-005** (three of the four categories have no accepted reference, and product introduction has no genre at all), **FM-14** (a metric demoted for not failing a small corpus was the lock on one that gates) and **FM-15** (overruling a written refusal without citing it).

Worse, two of the four numbers had already been examined and refused as gates in
writing, by the checkers they come from. `check_design`'s D16: *"A floor here
would be satisfied by pasting a small block on every page, which is the same
failure with a different number, so this reports and a reviewer decides."* The
red team pasted an EMPTY block. `inspect_layout`'s visual share: *"Reported
against a target of about half the page, never gated: the withdrawn 82% fill
floor is the standing lesson that a satisfiable number ends the looking."* And
`references/` states 50/30 as a **target**, which this table had turned into a
floor — CLAUDE.md convention 4, the class this repository has shipped three
regressions from. Overruling a written refusal needs a documented case; there is
none, and none was cited. The bars report.

**The corpus sweep corrected the table twice before it shipped** — which is what
a corpus is for. Three component demos of one to four content pages read as
0.0 figures per page, because a globe lives in `.markcell` and D5 counts `.fig`:
a ratio over four pages is one page's opinion, so `min_content_pages` is 8 and
the caveat is written down. And `internal` lost its figure floor entirely — a
real design document carries 0.273 figures per content page and passes every
checker, so a floor there would fail a document for being what internal analysis
is. Two metrics that separated the two documents yesterday no longer do, because
the rejected document's build script was repaired in between; they are listed as
`reported_not_thresholded` with that history, since a metric that never fails is
not a metric everyone passes.

**Four faults found while laying this foundation.**

*`D20_palette_fidelity` said it gated and did not.* Its row declared
`"=0 (gates)"`, five documents were made to say five gates because
`check_repo`'s guard reads that string — and the exit decision was a
hand-written tuple of four. **A document failing D20 alone exited 0.** Yesterday
that was masked because the one real D20 failure co-occurred with a D12 failure.
The tuple is gone: the exit decision reads the rows, and so does the summary
sentence that was the fourth hand-written copy of the same list. Two tests, one
measuring the real fixture rather than a stub — a stub of the checker's inputs
would be another hand-maintained copy, which is the defect being fixed.

*The rubric had two words for three tiers.* Six rows described as `reported` are
graded against a hard predicate and print `FAIL` without failing the run. The
tier table is written down now, and **the graded tier is where an Evals threshold
belongs**: a number that can already fail, but on a document rather than on the
run.

*Five scripts carried five different genre vocabularies.* `check_prose` 3,
`new_deck` 4, `inspect_layout` 5, `review_scores` 5, `export_pdf` "three plus a
hand-appended consulting". Not cosmetic: a consulting deliverable could be
scaffolded, layout-graded and review-scored, while `check_prose --genre
consulting` refused the value — so its prose had to be graded under a genre it is
not, which makes a genre-keyed Evals suite impossible. The names live in
`deliverable_registry` now; the behaviour keyed on them stays with each script,
because visual-share targets and the dash ban genuinely differ. A `genre
vocabulary` guard holds all of it, with three deliberate-red exercises: a second
list, a genre with no visual-share target, and a scaffold for a genre the
registry does not know. `new_deck` declares `SCAFFOLDED` as an explicit subset —
`marketing` has no skeleton of its own — and a subset is allowed where a
superset is not.

*The environment is proven before a verdict is attributed to anything.*
`environment_check` reads the registry's own install path and refuses to drive an
agent that cannot reach `tokens/`, `references/`, `scripts/` and `assets/` — or
whose platform declares no way to be handed them. This is the mechanism that was
missing yesterday, when three runs were recorded as agent failures and the
agent's own transcript said it had been unable to read the rules. A skipped run
records `environment` and scores `not earned`, never `fail`.

## 0.1.454 — the harness drives the agents, which it had claimed to do and never done

`run_conformance.py` opens by saying it runs the same tasks through every agent
CLI on this machine. Until this release it did not run anything: `run` created
directories, wrote a `PROMPT.txt`, and printed *"invoke each agent against its
PROMPT.txt"*. Every row this board has ever carried was earned by an operator
typing the command themselves — which is how a newly installed binary once
turned a hand-driven afternoon into a sentence claiming the tasks had run
non-interactively. That sentence was corrected at 0.1.452. This is the other
half: build the thing, in that order. The decisions, and the three that were
declined, are in `specs/2026-08-13-conformance-driver-design.md`.

**`run --drive`.** Each platform that can be driven declares a `drive` argv in
the registry — `claude -p --permission-mode acceptEdits`, `cursor-agent -p
--force` — beside the `probe` argv that was already there. The existing `invoke`
field stays what it always was, prose for a person ("say 'in LUMI style…'"), and
a driver built on it would try to execute a sentence.

**The working directory is outside this repository, and that is the load-bearing
part.** An agent started inside the tree reads this repo's maintenance
`CLAUDE.md` and behaves like a maintainer of the skill rather than a consumer of
it: it has the rules, the checkers and this changelog in front of it, and the
task stops measuring what the task is for. Each run gets a bare temporary
directory and whatever the platform installed at its own skill path; the
deliverable and the transcript come back, the agent's scratch does not. A test
asserts the working directory, because that is the property a refactor loses
silently.

**A timeout, which the file had nowhere except the 20 seconds on its `--version`
probe.** Thirty minutes by default, `--timeout` to change it, and an abandoned
task records `timeout` rather than hanging a session. `--task` runs one task, so
proving the driver works does not cost a twelve-page deck.

**`--model` records what it was.** Left off, each CLI picks its own default and
the run records that it did rather than leaving the field blank: a board cell
saying nothing about the model reads as a claim about the agent rather than
about one of its configurations. Pinned, the model goes in the record — which is
what a comparison between two agents needs and what a check of "what does a user
actually get" does not.

**Driving is not scoring, and `--drive` does not gate a release.** It exits 0
when the driver ran. Whether the artifacts pass is `score`'s answer, kept
separate on purpose: this file's own opening paragraph says agent output is
non-deterministic, so a release blocking on it would block on something that is
not the release.

**`report --record` writes the board's table itself.** It used to print, and a
person pasted. That is how `conformance/CONFORMANCE.md` came to carry "What this
table is not" **three times** — the section was re-appended at every refresh and
nobody diffed a document they had just generated. The table now sits between
generated markers; the narrative paragraphs outside them stay hand-written and
survive a refresh. The duplicates are gone, and the older of two versions of the
"Superseded runs" paragraph went with them.

Nine tests cover the outcomes a driver has: it drives, it brings back the
artifact and the transcript, it runs outside the repository, it abandons a hang,
it records a non-zero exit without claiming an artifact, it reports a binary
that will not start instead of raising, it refuses a platform with no `drive`
argv by name, and it records the model either way.

**The first driven run is this release's own evidence, and it is not flattering.**
Six tasks, two agents, all invoked by the harness: T1-deck 699s and 484s, T2 61s
and 53s, T3 50s and 42s. Both agents pass T2 and T3 and **both fail T1-deck, for
unrelated reasons, and neither failure is one of the gates 0.1.453 added** —
`visual_absent` and `figure_distorts` fired on neither deck, which a release that
adds gates and then reports failures owes the reader.

Claude Code built a deck that does not use the LUMI token block at all, so
`check_design.py` reports it `UNMEASURABLE` and the three commercial gates never
ran; beside that, blocks landing on each other on six pages, one role rendering
three ways, and 83.3% of its titles in a single frame against a 60% ceiling.
Cursor fires no gate: its T1 exits 1 on four checks that could not be measured —
each a component the deck does not contain — and on `M2_number_sourcing` at
86.0% against a 90% floor. Two very different documents, one word in the verdict
column.

**Then the owner refused the merge and asked why a run failing on both agents
was being shipped rather than diagnosed.** She was right, and the repository's
own history says so: `KNOWN_GAPS.md`'s GAP-001 is titled "T1-deck fails on both
scored conformance agents", and its diagnosis found the dominant cause in this
package's own tokens rather than in either agent. Both agents failing one task
is the fingerprint of a defect here. Three turned up.

* **The measure-bar window only recognised horizontal bars.** `width < 120 ||
  height < 30 || height > 90` reads width as length and height as thickness, so
  a vertical bar chart — 18 units wide, 180 tall — matched nothing, and Cursor's
  deck was recorded as containing no measure bars at all. Length is now the long
  side whichever way the bar runs, and the thickness floor is 12: 30 was a
  number from the one document the window was written against. The deck goes
  from 0 recognised bars to 17.
* **An empty result from that window counted as `unmeasured` and exited 1.** The
  window is a shape heuristic, and FM-13 — written into the ledger this same
  day — says a proxy may report but must not fail a run. It reports now. That
  alone was the whole of Cursor's T1 failure at four geometries.
* **`--bg` alone decided whether a document used the token block.** A deck
  defining `--tx1..--tx4`, `--ln1..--ln3` and `--acc` was declared
  `UNMEASURABLE` for painting its canvas another way, which took the whole
  design report with it and left three commercial gates reading "never
  reported". The test is the vocabulary now — three of ten core tokens — and it
  is the second false `UNMEASURABLE` this sentinel has produced.

**And then the owner looked at the deck and said the styling was simply not
LUMI's, which no instrument here could see.** Measured: of the colour tokens
each deck shares with `tokens/lumi-theme.css`, Cursor's deck agrees on **36 of
36** and Claude Code's on **0 of 10** — an `--acc` that is teal where LUMI's is
olive, a `--lime` two hues off, the whole rule ladder replaced. Every palette
check in this package passed it, because every one of them grades a document
against the block that document declares. Nothing asked whether that block was
this package's.

**`D20_palette_fidelity` gates.** Every colour token a document declares that
`tokens/` also defines must carry the shipped value, compared as parsed colours
so notation is not a difference, and per palette so dark is held to dark.
**Colours only** — and that line is principled rather than convenient: "one
colour, one meaning" is a red line, while 0.1.340 withdrew the type floor and
SKILL.md's first rule is to design per page. Measured on a compliant deck, the
only tokens that differ from the shipped set are six `--fs-*` sizes and one
ground opacity; gating on those would fail a document for obeying rule 1.

Deliberate-red: the offending deck fails naming ten tokens and both values;
three known-good documents and the passing fixture report zero; a second
`:root` overriding the accent is planted in `deck-degenerate.en.html` through
the generator. Five unit tests, including one proving `#FFF` and `#FFFFFF` are
one colour and one proving sizes are ignored.

**An interrupted run does not earn a verdict, and now the harness knows it.**
Re-driving T1 to check the fixes, Claude Code hit its ceiling at 1500s — the
same task it had finished in 699s an hour earlier — and was killed while
writing. It left a half-file with no accent token and no footers, and `score`
graded it exactly like a finished deck: nine palette mismatches, twenty-four
missing footers, a `fail` row for an agent that had not been allowed to finish.
The board withdrew a recorded `fail` by hand for this at 0.1.450 and the rule
has lived in a person's judgement ever since; `run --drive` can now produce the
situation automatically, so the rule is code. A task whose `driver.json` reports
`timeout`, `could not start` or `no driver` scores `not earned`, carries its
fingerprint like any other entry, and the roll-up excludes it the way it already
excluded `not attempted` — folding either into `fail` is how a board reports a
timeout as a model's defect. Five tests, including one proving a hand-driven
task with no driver record is scored exactly as before.

**The harness was locking the agent out of the skill, and three runs were
mis-attributed before anyone saw it.** Driven with `-p` in a temporary directory
— which this release chose deliberately, so an agent does not read the
maintenance `CLAUDE.md` and start behaving like a maintainer — a CLI confines
its reads to that directory. So an agent got `SKILL.md`, which the platform
surfaces, and could not open the `tokens/`, `references/`, `scripts/` and
`assets/` beside it. One said so in its own transcript: *"blocked from reading …
I'll rebuild the palette inside the file"*. Three runs of it each invented a
palette, and the board recorded three agent failures.

The driver hands over the registry's own install path now
(`--add-dir ~/.claude/skills/lumi-style`), declared per platform rather than
assumed, so a run reproduces what a reader has instead of something only this
harness arranges. Re-driven with it, the same agent on the same task produced
the shipped palette exactly — `--acc #48633E`, `--seal #C8102E`, `--lime
#B8FF00`, `--tx1 rgba(43,46,51,.92)` — twelve commercial footers, D12 and D20
both green, and a document three times the size of its locked-out attempts.

*Two smaller faults fell out of the same fix.* `--add-dir` is variadic, so
appending it made the prompt another directory and the CLI exited in a second
with "Input must be provided"; it is inserted after the binary now, and a test
uses a real executable rather than `python -c` because only a real one can
demonstrate the ordering. And the flag was added, then verified on a
twelve-page deck for thirty-one minutes before anyone ran the thirty-five-second
task that would have caught it — the cheap chain check now precedes the
expensive one.

*The `gating claims` guard added at 0.1.452 earned itself here.* Adding D20
made five prose sites wrong at once, and it named all five before a commit —
the same class of drift that had stood for eight releases the day before. Its
patterns are now count-agnostic: a pattern keyed on the word "four" would need
editing at exactly the moment the guard is meant to fire.

## 0.1.453 — two checks that had never measured anything, and a drawing that can now be caught contradicting its own numbers

The owner compared two 30-page decks built from these same rules — one by
Claude Code, one by Cursor — and said the second one's figures were much worse.
They are, and the interesting part is that **the second deck passed every check
in this package.** The instruments could not tell the two apart.
The decisions, and the two that were declined, are in
`specs/2026-08-13-figure-instruments-design.md`.

| | Claude Code | Cursor |
|---|---|---|
| visual share, median | 67.5% | **0.0%** |
| content pages with nothing visual | 0 of 23 | **10 of 22** |
| figures | 22 | 5 |
| figures made only of rectangles | 0 | 3 |
| figures carrying arrows | 12 | 1 |
| bullet items | 17 | **97** |

The speed difference had the same source: 97 list items instead of 74 drawings.
The checkers were the *slower* half of that run.

**Two of the checks that should have seen it had never measured anything.**

The caption budget — word count, sentence count, and whether a caption repeats
its own page — read `.cap .d` and skipped any caption without one. **Nothing has
ever emitted `.d`**: not the scaffold, not the passing fixture, not either
shipped deliverable. Seventy-four captions across three documents, zero. The
stylesheet even carries a rendering for the class, added *because this probe
asserted it*, with a comment noting the vocabulary guard has a hole where an
inline `querySelector` reaches. So the class was shipped, the probe went on
finding none, and a caption count was printed beside a measurement of nothing.
It now reads the caption's own text minus its number and its source line —
which is what rule 7b says a caption is — and measures 22 and 5 captions on the
two decks where it measured 0.

`M2_number_sourcing` reported `n/a` on a deck carrying 161, 88 and 32, with the
note *"too little data: 270 sentences"*. The verdict was right and the reason
was false: M2's window is percentages and currency, and that deck has neither.
This is the same reassuring line M12 used to print, one metric over. **The
window itself is deliberately not widened** — measured, the wide net finds 172
"numbers" in that deck, most of them HTML entity codes (`8217` is a right quote,
`8594` an arrow), page numbers and years. A metric that flags those is one
reviewers learn to skip. The n/a now states its own reason instead.

**A drawing can now be caught contradicting its own numbers.** `figure_distorts`
gates: a mark that declares the quantity it encodes must be drawn in proportion
to it. The case that produced the rule floored every bar at 48px so short bars
would not vanish — drawing 1 and 4 as the same bar, a 7.4× overstatement, and
stretching a 4 to 2.1× on the page whose caption read *"Europe stays hollow at
four."* The true values were already in the markup, one attribute away from the
width that ignored them.

This required shipping the convention before gating on it (maintenance rule 5):
`data-datum` had been a `.field` mark's identity, and design-rules §4 rule 9 now
states the quantitative form and the proportionality it obliges. The tolerance
is 2px or 4% of the largest mark — rounding and a stroke are not distortion.

**`visual_absent` gates a document that is mostly not drawn on.** A ceiling on
content pages carrying nothing visual, not a target for the rest, set at one
third. Calibration needed no argument: the two decks above sit at 0% and 45.5%,
so any line between them separates them, and this one is set where a document
has to be mostly undrawn before it fails. Openers, covers, closings and declared
apparatus pages are excluded — they legitimately carry no data figure.

*Its gaming move, written down because 0.1.339's fill floor was met by
stretching table rows:* put one token drawing on every page. `figure_distorts`
is the pair to it — a drawing that encodes nothing cannot be checked, but one
that encodes wrongly now fails — and D5's shape-vocabulary spread still reports
a document whose figures are all the same rectangle.

Deliberate-red for both, on real documents rather than only fixtures: the thin
deck fails both and exits 1; the deck the owner called good passes both; so does
`fixtures/deck-pass.en.html`. The distortion is planted in
`fixtures/deck-degenerate.en.html` through the generator, on an existing page
rather than a new one — that fixture fails `M8_length_cv` by 0.003, and a new
page's title moved it enough to flip. Seven verdict-level tests, including one
proving the ceiling does not count openers and covers.

The owner's own build script is fixed in the same breath: the floor is gone, the
full-width track under each bar is gone — it stated a share against a total the
bars were 55% of — and a zero line and axis maximum are drawn so a value can be
read off the figure rather than only off its label. Its viewBox heights were
hardcoded while the helper returned the height it had computed, so adding a
baseline clipped the drawing; they are computed now. Rebuilt, the bars read
1 → 6px, 4 → 26px, 80 → 520px, and `figure_distorts` passes. `visual_absent`
still fails it, correctly: ten of its pages draw nothing, and that is a
writing job rather than a helper bug.

## 0.1.452 — the count that was wrong in nine places, and the two guards that will not let it be wrong again

0.1.451 fixed a stale count in two files and reported it as a tidy-up. It was
live in **eight more**, and one of them sits in `AGENTS.md` eighty-six lines
below the line that release had just corrected — beside that file's own written
confession about this exact drift: *"This line claimed 'D1–D4 and D6 gate' for
eight releases… A restatement nothing compares against is the drift this file
exists to concentrate, not to escape."* The owner read that as a delivery that
leaks. The measurement agrees with her rather than with the release notes.
The decisions, and the three that were declined, are in
`specs/2026-08-13-drift-prevention-design.md`.

**The rate, counted rather than felt.** Twenty-six of this repository's releases
have carried a fix for a prose copy that disagreed with its code. Five of them
are in the last ten. Two whole releases — 0.1.360 and 0.1.429 — exist only to do
this work. Where an entry says how long the drift had stood, it is four to
eleven releases. Every prevention written for it so far ends in the words "stays
a review duty".

**Two guards, one of which needs nothing declared.**

`metric id ranges` reads the highest metric id each checker actually defines —
out of its row table, with `ast`, never by importing it — and fails any range
written from 1 that stops somewhere else. A range from 1 claims a whole family,
which is what makes it decidable; `M8-M11` names a subset on purpose and is left
alone. **Nothing is registered**, so a claim written tomorrow is covered the day
it is written. That is the difference between this and the list it replaces.

`gating claims` is the declared half: the sites that name *which* design checks
fail a run, each with the pattern that captures the ids it names, held to the
rows whose target says `(gates)`. A site whose pattern stops matching is an
error and not a skip — if rewording a sentence could retire the check on it, the
guard would protect only the sentences nobody edits. Deliberately not a search
for sentences *about* gating: deciding that from English is the phrase-trigger
guard AG-1 declined in 0.1.422, and this does not re-propose it.

Deliberate-red: both guards were written before anything was corrected, and went
red on the tree that created them — nine counted claims and five gating claims
across ten files. Ten synthetic-tree tests hold them to failing for the right
reason, including one proving a reworded claim fails rather than silently
passing, and one proving a checker that stops parsing is reported rather than
skipped.

**What they found, all of it now true.** The gating set is named correctly in
`AGENTS.md`, `CLAUDE.md`, `references/eval-rubric.md`, `references/design-rules.md`
and `references/brand.md`; `d12_commercial_footer`'s own docstring had called
itself "the one design check that fails the run" while the module docstring 780
lines above it named four. Ranges ending at 17 or 11 are gone from six files —
mostly by **deleting the number and naming the authority**, which `preflight.py`
has modelled since 0.1.429 ("how many is whatever the workflow says today, never
a number written here"). The eval rubric's D-table had no row for D18 or D19;
`check_design.py`'s own metric table omitted D13 and D18; `scripts/README.md`
calls itself the map of `scripts/` and had never listed `debug_log.py`. Two code
comments still carried the layout-gate count that 0.1.443 re-synced in four
prose files and missed here. `CLAUDE.md` described `check_prose.py` as
English-only, which stopped being true at 0.1.390. The region palette's
"asserts all four" asserts three floors; the fourth number is a generation input
nothing asserts. Two `file:line` citations pointed at lines that had moved.

**One correction is to a claim this session's author wrote.** 0.1.450's entry
said Cursor's conformance tasks "ran non-interactively like any other".
`run_conformance.py` invokes no agent and never has: `run` prepares a prompt
directory and prints *"invoke each agent against its PROMPT.txt"*. What changed
that day was `shutil.which` finding a newly installed binary, so the `cli` column
printed a version where it had printed `driven by hand`. The operator drove those
tasks. The entry, the conformance board's narrative and the Cursor record's
capability waiver all say so now. In a package whose thesis is that a verdict is
earned or it is not recorded, that was an overclaim.

**`claim_sweep.py`, which reports and never fails.** It lists every counted claim
next to a name this repository defines, and every `file.py:123` self-citation
whose line has moved — nothing validated a line number before, and two had
drifted. Advisory by construction rather than by timidity: AG-1 declined a *gate*
that reads English, and this is the same reading handed to a person, where being
wrong costs nothing. Its first cut reported 1115 sentences, which is the whole
package and teaches a reader to skip the list; narrowing it to counts adjacent to
names this repository owns, dropping quantifiers ("every guard" survives a new
guard, "three guards" does not) and skipping generated copies brings it to 197.

Three maintenance conventions land with it, each pointing at a command rather
than at a good intention: sweep the restatements of any fact you change, prefer
deleting a number to maintaining it, and do not write a claim about behaviour you
have not read in the code.

## 0.1.451 — a third-party debug log, read: a dead globe nothing gated, and a length standing in for a rule

The owner built a deliverable on another platform under debug mode on 0.1.449
and handed over the log. It is the first execution record this package has from
an agent it did not drive, and reading it — plus one defect the owner found by
eye — produced four repository defects and one new gate. The decisions, and the
two that were declined, are in
`specs/2026-08-13-third-party-debug-log-design.md`.

**The mark that does not turn is now a failed check.** The cover and closing
globes on that deliverable were still frames. The document carried
`[data-globe]` on both and no runtime at all: the build script had tried to
harvest the runtime out of `fixtures/deck-pass.en.html` with a regex, matched
nothing — that fixture carries the drawing and deliberately carries no script —
and emitted an empty `<script></script>`. All three checkers passed it. The
brand contract has said since 0.1.442 that this mark is "embedded live … so it
rotates" and that a still globe is the fallback, not the design, and nothing
enforced it.

`data-globe` is a reference: it is the runtime's selector and nothing else
reads it. So this is **D19's fourth assertion**, next to an icon `<use>`
pointing at no symbol — a reference that does not resolve inside the document
it appears in. Motion is not measured and could not be; the runtime is in the
file or it is not, and `createGlobe` is the same word `embed_globe.py`'s own
`check()` looks for, read from the other end rather than spelled a second way.

*The direction is the whole design.* A MARK obliges a RUNTIME, never the
reverse. Asserting that a globe drawing obliges `data-globe` would have failed
`fixtures/deck-pass.en.html` on its first run — the mistake D19's own first cut
and the withdrawn `_grid_arity` both made. A cover globe with no mark is
reported instead. Deliberate-red: the owner's deliverable fails the new
assertion (`D19_vocabulary 1`, exit 1) where it exited 0 before; a healthy
deliverable with its runtime stripped fails; the same file untouched passes;
`fixtures/deck-pass.en.html` passes. Four unit tests, one of which exists only
to stop someone reversing the direction later.

`SKILL.md`'s assembly protocol now says the runtime is **built, never
harvested** — and names why the merge gate missed it: that gate refuses
leftover placeholders, and a substitution resolving to the empty string is not
a leftover.

**M6 counted a truthful sentence, and its author reworded a correct line to get
past it.** "Answer confirmation questions in blocks 1–3 and cross-region" is an
enumeration label — the numbers identify blocks, they do not measure anything.
The script exempted such labels by asking whether the block was 40 characters
or fewer. `writing-rules.md` §4 rule 6 has never mentioned a length: it asks
whether the pair has quantitative context. The proxy let go twice in one
metric — it was written for GAP-001's short label, then it counted this
61-character sentence.

The test is semantic now: a figure-shaped number anywhere in the block counts
(that branch stays first, or the one fixture that fails M6 stops failing it); a
counting noun in front of the pair reads as a label; length survives only as a
backstop under both, which is what still catches a bare `Plastics (1–2).` cell.
The rules state the test, `references/eval-rubric.md` restates it, and
`check_prose.py` now prints what it exempted — the list existed in the JSON and
was never shown, so an author could not tell a range that passed from a range
this metric never saw. Deliberate-red: the label was planted in
`fixtures/deck-pass.en.html` through the generator first, the passing fixture
went `M6_unsourced_ranges FAIL` on a correct sentence, and the new
classification returned it to `ok` while `deck-degenerate.en.html` kept failing
on its unsourced `62–78%`. Seven unit tests in a new
`tests/test_check_prose_units.py`; there had been none for this script.

**Debug mode recorded five errors and three of them said nothing.** A nonzero
exit writes its own error entry from the last twenty lines of output — right
for a crash, wrong for a checker, because every check script prints its
thresholds last, so the tail of a `--json` failure is the schema footer. The
log knew something had failed and could not say what, which is the one thing it
exists to say. `debug_log.py` now parses the output when it is JSON and records
the verdicts that are not `ok`, in both shapes the checkers emit — a list of
per-file documents, or one dict with `verdicts` at the top — falling back to the
tail for anything it cannot read. `n/a` is not a failure, and "nonzero with
nothing failing" says so rather than printing a blank. Re-running the owner's
own failing command through it turns twenty lines of thresholds into
`D19_vocabulary FAIL`. Four tests, including the non-JSON fallback.

**Two failure modes recorded, both visible only because the log kept
snapshots.** `FM-12` — removing 36 em dashes to satisfy M9 drove M11 title
uniformity from 40.0 to 56.0 against a ceiling of 60.0; the dashes had been
carrying the structural variety in the titles, three checkers reported green,
and none of them mentioned that one fix had spent sixteen points of a
neighbour's margin. `FM-13` — a threshold standing in for the rule's own test,
which is M6 above, and the reason a false positive that edits prose is worse
than a miss.

**The matrix was switched off from the command line.** That deliverable was
checked at 16:9 alone, and its content-spill fix left one pixel of clearance
under a gate that fires above one pixel. `inspect_layout.py` already runs the
points a document's `data-geometry` implies — four for landscape, two for
portrait; passing a single `--geometry` overrides that. Its own help text had
been advertising a default of three geometries since the default became five at
0.1.390, which is the enumeration rot this repository keeps finding in itself.
The rule is now "do not narrow the matrix", stated in `design-rules.md` §7 with
a palette axis beside it — `--dark` is a second run, not a matrix point — and
re-flowed into all three entry points. It is a rule and not a gate, by owner
decision.

Two stale counts fixed along the way: `SKILL.md` and `AGENTS.md` both said
`check_design.py` gates on three things and listed D12, D14 and D15. D19 has
gated since 0.1.443.

## 0.1.450 — the board is re-earned after fifteen releases, and three of its own instruments were wrong

Two debts the 0.1.443–0.1.449 series left open, both discharged, and the work
of discharging them found more than it fixed.

**The conformance board.** It had stood at 0.1.434 while the checkers changed
under it, so nothing recorded measured the instruments this package now
ships. Refreshed at 0.1.450: **two agents, three tasks each, all six pass.**
Cursor's row changed shape — `cursor-agent` was installed on this machine
during the run, so the probe succeeded and the `cli` column printed a version
where it had printed `driven by hand`.

*Corrected at 0.1.452.* The sentence that stood here also said Cursor's "tasks
ran non-interactively like any other", and no code supports that: `run` prepares
directories and prints "invoke each agent against its PROMPT.txt", and nothing
in this repository has ever invoked an agent. What changed was `shutil.which`,
not the harness. The operator drove those tasks. In a document whose whole
thesis is not overclaiming, that was an overclaim.

Earning those six verdicts took three corrections, none of them in either
agent:

* **A recorded `fail` was withdrawn.** The first Claude Code attempt died
  mid-run on a transport error while it was still fixing its own findings, so
  the artifact scored was a draft. The rows were reverted and the artifact
  kept at `conformance/results/interrupted-claude-code-20260813/`. A verdict
  is earned or it is not recorded.
* **An agent that passed the task it was given was rolled up as `fail`,**
  because two tasks nobody had driven scored as missing deliverables. `score`
  now separates `not attempted` — nothing was ever written into that task's
  directory — from `no deliverable`, and the roll-up reads `partial: N of M
  driven, all pass`. The board's prose has drawn this line for absent AGENTS
  since 0.1.390 ("printing the two identically made the board read as ten
  pieces of pending work when only six are"); the roll-up had never drawn it
  for absent RUNS.
* **T3 scored a correct answer wrong on its grammatical number.**
  `\bhuman\b` refused "Licensed humans" and passed "a licensed human" — the
  same fact, failed for an `s`. The patterns take an optional plural now,
  which changes the task fingerprint, so earlier T3 rows read `stale` until
  re-earned.

**The scaffold taught less than the checks require, in three places** — found
by reading what a failing agent had actually written, and confirmed against
`new_deck.py` itself rather than against that run. `SKILL.md` names `.card` +
`.ledname` in prose and D19 GATES on it, while SAMPLES shipped worked examples
for four block patterns and not that one; the colophon read "Built with
lumi-style VERSION." and stopped, which trips D6 — the check that asks the
DOCUMENT where its numbers came from — on every page at once; and a sample
labelled `.gd` "the tier-one callout" while D3 budgets `.key` and `.red`,
teaching the wrong class for the rule it named. Every entry in
BLOCK_CONTRACTS now has a worked example, the colophon carries a provenance
slot (and that slot is in D14's list, held by the scaffold-slots guard), and
the callout sample says which tier it is.

**D19 counted a paint class as a block.** `\bcard\b` matched `f-card`, the
SVG fill class every drawing uses, so a figure-rich 30-page document with
four correct `.card` blocks and seventy-five painted rects reported thirteen
cards missing `.ledname`. This is D18's `rg-` bug in the other checker, and
it means the conformance failure that started the scaffold investigation was
itself partly a false positive: the fixes stand on their own evidence, the
diagnosis did not. Token-boundary matching both ways, three tests.

**The ten-minute target has its first from-scratch measurement**, and it does
not meet it. A 30-page A4 training handbook built from nothing through the
parallel protocol — four authors, real content sourced entirely from this
repository — took **27 minutes end to end** to a document that passes every
gate: 50 seconds to fix the storyline, scaffold and split; 24m49s for the
slowest of four parallel authors; 2m21s to assemble, fix three real defects
and clear the gates, of which the checkers themselves are 25 seconds. Single
page cost is about 1.6 minutes and it is the RULES' price, not the agent's
pace: every content page owes a drawn figure, a second content block, a
marked key point and a traceable number, and the four authors produced 74
SVGs between them. Against the hour-plus a 34-page serial build cost before
the protocol, that is a 2.2x improvement and not the 2.7x further one the
target asks for. Three ways to close it — raise parallelism to eight, set the
target per genre (training is the most expensive; 16:9 sales and consulting
are not), or restate the number as a measured range — are the owner's to
choose, and SKILL.md keeps saying ten until she does. The handbook is not
committed here: deliverables live outside this repository.

## 0.1.449 — the squash subject is a release subject, and main's own CI said so

Merging the retrospective series turned main red on the commit that landed
it. `check_commit_convention` holds a CHANGELOG-touching commit's subject to
`X.Y.Z — summary` AND to the newest heading in that same commit; a squash
merge inherits the PR title, and PR #94's title was written before the branch
shipped its last release, so `0.1.443–0.1.447` arrived on a tree whose
CHANGELOG said 0.1.448. Both halves of the guard fired, correctly, on main.

**And the subject was the smaller half.** `check_evidence.py --init` finds the
previous release by looking for a commit whose subject starts with that
version — and squashing collapsed eight release commits into one, so 0.1.449
could not compute its own diff base and had to be told the squash commit by
hand. The release machinery here assumes one commit per release, in two
independent places, and a squash of a multi-release branch breaks both.

So rule 3 now says both things: a squash merge takes the NEWEST version in
its subject — not the range it covers, not the PR title, which is stale by
construction if the branch shipped after it was written — and a branch
carrying several releases is better merged than squashed, because the
per-release commits are what the evidence gate walks. Recorded because the
failure is invisible until it is on main, where fixing it costs a release
rather than an amend: `main` forbids force pushes, which is right.

## 0.1.448 — a five-lens review of the retrospective, and the checks it added get checked

Five specialist reviews over 0.1.443–0.1.447 (general, silent-failure,
test-coverage, comment-accuracy, schema design), against the series' own spec
`specs/2026-08-12-owner-review-retrospective-design.md`. They found real defects in
the release series that exists to find real defects — including, twice, a new
check that could not see the thing it was written for. Every finding below
was reproduced before it was fixed.

**The debug log dropped evidence under the very protocol it shipped beside.**
Eight parallel `run` calls — the shape SKILL.md step 1 puts in flight — left
one entry of eight, and the file itself came back unparseable: read-modify-
write with a truncating save. Writes are now atomic (`tmp` + `os.replace`)
under a cross-platform `O_CREAT|O_EXCL` lock, and eight concurrent writers
keep eight records, proven by test. Three more shapes of the same defect
closed: a command that could not START (a typo'd path) reached no record at
all and `validate` called the log clean; a nonzero exit wrote no `errors`
entry, so the first real log had one failure and no account of it; and
`attach` overwrote per kind, so a build that failed a check and then passed
it kept only the passing document. `run` now digests stdout AND stderr, the
way `check_evidence.py` does — stdout alone gave every crash the same
empty-output digest.

**`validate` reached less far than the writers, which is backwards** — a log
arrives at an evaluator as a file, not as a sequence of subcommand calls. A
score of 9, a self-scored 5 as the string `"5"`, a `stdout_sha256` reading
`not-a-digest`, a step with no provenance, an unknown platform and an EMPTY
log all passed. All refused now; the empty-log case had been encoded as an
expectation by a test named `..._clean_log_passes`. What `validate` still
cannot do — prove a digest is the digest of what that command produced — the
docstring now says instead of implying otherwise. The engagement-fact claim
is corrected the same way: the closed key set means no field INVITES a client
fact, but four free-text channels exist and red line 9 binds the author in
them; `reviews/scores.json`'s defence is that it has no free-text field at
all, and this schema cannot borrow what it did not copy.

**The footer-baseline gate fired at 3px and went silent at 12px.** Its probe
returned null when no two runs shared the first line — which is what a LARGE
displacement produces — and every consumer read `null or 0`, so the report
printed "one line, one baseline" for a visibly broken footer. The probe now
returns what happened (`runs`, `split`), a split footer is the finding one
size up, a single-run footer is n/a rather than ok, and a wrapped footer is
not reported twice under two names. Deliberate red: the 12px case the old
probe passed now fails the gate.

**Two verdicts were emitted and asserted by nobody** — `footer_baseline` from
the release that added it, `starved_column` since 0.1.412 — because
`fixtures/expected.json` was walked key by declared key. Both declared now,
and the class is closed: `check_fixtures.py` fails any verdict a checker
emits that the table does not name. It immediately found two more
(`M4zh_banned_hits`, `M5_zh_punctuation`). Two literal "ten"s in that file
went the way of the other enumerations.

**The 0.1.447 globe fix was right about the symptom and wrong about the
cause.** Its comment said the `.gl-*` rules and the `.trade` palette "live
nowhere in `tokens/`". They do — `tokens/region-palette.css` and
`region-palette-trade.css`, both generated, both `--check`ed. What had gone
wrong was narrower: the trade palette was the one generated file the fixture
preamble did not include. Keeping a copy inside the SVG cured it and froze a
generated file inside a LOCKED asset where no regeneration check can see it
drift. The preamble includes both palettes now — the same answer figure 9's
black rectangles got in 0.1.391 — the hand-written CSS brace scanner is
deleted with its four silent-failure modes (comment braces, at-rule nesting,
selector lists, unbalanced input), and `tests/test_new_deck.py` holds the
invariant that matters: every region class the mark uses has a binding and a
variable in what the scaffold ships. Deliberate red: remove the trade palette
from the preamble and that test goes red, which is BUG#1 stated as a machine
check instead of a paragraph.

**D14 knew two of the scaffold's slots.** An author who fixed both still
shipped a cover reading "One sentence saying what this is." All nine are
listed now, and a new `check_repo` guard holds the list against what the
scaffold actually emits in both directions — a string the scaffold no longer
writes is stale, and a scaffold that still trips D14 after every declared
slot is substituted has furniture the list has not learned.

**D18's regex fix was half of one.** It stopped the globe's `gl-rg-label`
furniture reading as a region, and left the flat map's `rg-full` /
`rg-outline-<id>` — written by this package's own emitter — inventing two.
Regions are now read from the class list, keyed on the bare `rg` marker.

**And the numbers.** `--acc` was documented at 5.94:1 where it measures 6.71
(the repo's own §1 ledger already said so; 5.94 is a transposition of
`--on-acc`'s 5.93) — it had reached all three fixtures. A portrait comment
cited a clearance measured at a mark ceiling the same release replaced. The
launch-cost arithmetic said 17s where 13 × 1.4 is 18.2. `assets/brand/README`
instructed the exact reading `new_deck.py` records as the defect. The
reverse palette walk recognised three colour syntaxes and would have skipped
an `oklch()` token silently; it now asks what is NOT a colour. `scripts/README`
gained the two import edges this series added, and `new_deck.py` a note that
its fixture read must stay lazy or the fixture generator cannot import.

29 tests added (294).

## 0.1.447 — the mark gets its colours back, the sheet gets its voice, and the table finally ships

Second round of the owner review, on the rebuilt handbook
(spec: `specs/2026-08-12-owner-review-retrospective-design.md`, decisions D2
and D5 extended). Five reports; two of them opened repository faults larger
than the page that showed them.

**The brand mark was embedded with its component rules thrown away.** 0.1.443's
`brand_globe()` stripped the vendored globe's entire `<style>`, reasoning that
"the document's token block paints the classes". It does not: the `.gl-*`
rendering and the `.trade` region palette live in that block and nowhere in
`tokens/`, so every trade region filled with the UA default and the owner
asked where the colours went. The strip is now surgical — only the blocks
that would redefine the HOST's palette (`:root`, `body.dark`, `.dark`) come
out, and a comma inside the prose above a selector no longer hides it from
the stripper. All eight blocs paint again, at the component's own 42%.

**D4 could see one of this package's two region palettes.**
`region-palette.css` declares on `:root` and passed; `region-palette-trade.css`
declares the same kind of generated values on `.trade` and every one of its
fifty hexes read as a stray literal — on documents that had done exactly what
`SKILL.md` tells an author to do. A shipped deliverable in the workspace had
been failing D4 on all fifty since it was built, and nothing had looked. The
token-block list now matches what `tokens/` ships; four tests hold both
directions (a `.trade` value is not a literal, a real stray still fires).

**`tokens/` shipped no table.** "A table is for values" and "comparisons
always use tables" have been rules since 1.2, and the token files styled no
table at all — three deliverables in one workspace each hand-wrote the same
block at three different type sizes, and a document built from the tokens
alone rendered browser defaults on the pages the rules push hardest toward
tables. FM-11 at its largest. The reviewed rendering is promoted, and with it
the feedback table's scale column: `1 · 2 · 3 · 4 · 5` had broken across two
lines, which reads as two ranges to a reader circling a number (BUG#2).

**The sheet was set as a smaller slide.** 0.1.443 scaled the portrait display
tiers down by the stage ratio — opener 50, cover 42 — and the owner read the
result as flat beside a 16:9 deck at 80/58. A cover and a part opener exist to
land one statement, so the sheet now takes the SAME ink as the slide (72/58)
and gains impact from the narrower measure; content titles do not move,
because a content page's job is its evidence. The mark's ceiling follows from
34svh to 44svh — the brand README forbids restyling a mark from outside, so
what changes is its size, never its ink. Measured: 55px above the mark, 50px
below the attribute strip, no page over its box, on both marked pages.

**Two block renderings corrected from the page.** The vow's ordinal now sits
on its title's line — stacked, it put four orphaned two-digit fragments down
a page instead of a numbered set — and the card carries `--card-bg`, opaque
in both palettes, because the page's ground ran its waterline straight
through the one block whose job is to hold a self-contained answer.

## 0.1.446 — the owner's hunch about 16:9 proportion measures out, and the rule gets its receipts

The 0.1.442 review's item 8 was a suspicion stated without evidence — figures
and key numbers not sitting right on the 16:9 stage — and the owner asked for
an investigation, not a rule
(spec: `specs/2026-08-12-owner-review-retrospective-design.md` D10). Measured
across two shipped landscape decks with the aspect probe and a tier census:
one 30-page deck carried a 2.7:1 figure in a 1.28:1 cell and a 3.8:1 figure
in a 1.59:1 cell — each rendering under half its cell — and a 15-page deck
ran three of five figures past 1.2× their cell; across all 45 landscape
pages, `--fs-lead-xl` and the 54px SVG numeral were used ZERO times, so the
largest number on most pages was a 43px band value. The hunch was right,
twice over — the two-document threshold for promotion is met.

What promotes is provenance, not a gate: design-rules §4's drawn-for-the-cell
targets gain the measured case as their 16:9 receipt, and the decision NOT to
gate the aspect probe is re-recorded with eval-rubric's standing reason — a
number satisfiable without improving the page ends the looking. The same
sweep found both decks failing the new `footer_baseline` gate, confirming the
0.1.443 footer defect was systemic across every shipped document, not one
build's slip.

## 0.1.445 — debug mode: the build writes its own evidence, in one schema on every platform

The owner's product ask from the 0.1.442 review
(spec: `specs/2026-08-12-debug-mode-design.md`): on the words "debug mode",
the skill writes `<stem>.debug.json` beside the deliverable — errors,
performance, and a quality assessment — so a later session can run a real
eval from the log alone.

**One helper is the schema.** `scripts/ops/debug_log.py` (standard library
only): `init` stamps skill version, platform (validated against the
registry), machine and date; `run -- <command>` EXECUTES the command and
machine-writes exit code, stdout digest and timing — the evidence-gate
principle, no verdict field for a human to type; `attach` embeds the three
checkers' `--json` verbatim; `assess` records H1–H6 with a mandatory reason
and REFUSES a self-scored 5 (review_scores' standing rule); `error`, `note`,
and `validate`, which fails an unknown top-level key (the closed-set
engagement-fact defence, borrowed from reviews/scores.json) and any CJK
content (English-only by owner requirement).

**Platforms cost nothing new.** Full-tier platforms run the script — same log
from Claude Code, Codex, Cursor, Gemini, Pi, OpenClaw, Hermes; the prompt
tier writes what it can into the delivery note and names what it owes, the
degradation contract the checkers already use. `adapters/` is untouched on
purpose: a per-platform debug note would be a restated rule, which the
registry's own header forbids. macOS/Windows is `pathlib` + the deliverable's
own folder — no new OS surface.

Ten tests, both directions (FM-01 discipline): the run recorder proven to
pass exit codes through, the self-5 refused, validate red on an unknown key,
on CJK, and on a hand-written command entry with no digest. Deliberate red
recorded: `validate` on a log carrying `"client"` and Chinese notes exits 1
naming both. The first argparse cut of `run` swallowed `--label` into the
executed command (REMAINDER's stdlib sharp edge) — caught by the test, fixed
by splitting at `--` before parsing, and kept in the file as a comment.

## 0.1.444 — the render gate stops paying for thirteen browsers and one quadratic line

The owner's performance complaint (an hour for 34 pages, ceiling ten minutes;
spec: `specs/2026-08-12-owner-review-retrospective-design.md` D8) split into
measured parts: the scripts account for four to eight minutes and the rest is
the instructed serial authoring loop. Both halves move.

**The scripts' two structural costs are gone.** `ground_report`'s canvas
detection ran `max(set(px), key=px.count)` — `.count` is O(N) per unique
colour, measured at ~2.6s per page, ~90s per geometry on a 34-page document,
the single largest cost in the file — and is now one `Counter` pass whose
unique keys feed the contrast loop too. And every probe opened its own
`sync_playwright()` and launched its own Chromium — three per geometry plus
one per file, thirteen launches for a default landscape run, ~1.4s each —
and they now share one process-wide browser closed at exit. Measured on the
18-page pass fixture, full default run: **57.8s → 22.4s**, report output
byte-identical (characterization diff, zero hunks).

**The authoring hour gets its protocol.** "Work in parallel where the
platform allows" was one sentence with no mechanism, three times. SKILL.md
step 1 now carries the parallel build protocol, formalized from the
convention every hand-built deliverable's `_sources/` already proved:
orchestrator fixes storyline, scaffolds, splits content into `body-N.html`
parts carrying `FOOT_<n>`/asset placeholders; part authors run in parallel
writing page markup only; an assembler stitches and substitutes and REFUSES
the merge on any unreplaced placeholder; the gate stack runs once, on the
assembled document. AGENTS.md and the core prompt restate it. The owner's
ten-minute ceiling is named as the target and the say-so-first clause keeps
its meaning for serial platforms.

The local timing baseline is re-recorded (warn-only by design, AG-3).

## 0.1.443 — the owner reads 34 pages, and seven defects turn out to be three root causes

An owner review of a 34-page A4-portrait deliverable built at 0.1.442 reported
seven defects. Forensics traced them to three roots, and each fix landed with
the mechanism that stops its recurrence
(spec: `specs/2026-08-12-owner-review-retrospective-design.md`).

**Root one: the document was hand-copied from the test fixture, not scaffolded.**
Its 1,781-line style block was byte-identical to `fixtures/deck-pass.en.html`,
its title still read `REPLACE ME`, its 34 footers carried the fixture's
`www.example.org`, and it shipped zero `<script>` and zero `@font-face`. The
scaffold is now the stated start (`SKILL.md`, `AGENTS.md`, `new_deck.py`'s own
docstring), `new_deck.py` embeds the display face itself (a separate
embedding step was skipped by two deliverables in one week), and D14 gained
the scaffold's own unbracketed slots — `REPLACE ME` and the literal
`lumi-style VERSION` — including the head, which the per-page walk never saw.
Deliberate red: an unfilled scaffold now exits 1 on D14 with both slots named
(run recorded this release). The fixture-site string stays uncaught by
decision, not oversight: IDEA-9.

**Root two: renderings the owner had verified existed only in single documents'
DOC_CSS, so the next build lost them.** Recorded as FM-11, and everything it
names is promoted into `tokens/`: the cover `.attrs` key is bold in the ink
tone and its value holds one line with an ellipsis (verified on a shipped 16:9
deliverable, reported lost as two defects); `.band .v .u` steps the unit down;
`.band .v.acc` and the lime `.first` panel ship; the print page-break block
rides in the tokens instead of every assemble script. The portrait block also
gains the `--fs-cover: 42px` override the theme's comment had claimed existed
(a cover title shipped at the landscape 58px on a 794px sheet), and
`--genre training` appends Template 4's reference page (`dl.gloss`,
`data-role="apparatus"`).

**Root three: the repo's own green rules contradicted each other, and the token
mirror had a blind side.** `brand.md` said figures take the forest; the theme
file said the live green; the paint classes bound the forest — so one document
ran three unrelated greens and the owner saw all three (two defects reported).
The merged rule ships in both files: one accent meaning, two measured inks —
`--acc` as text, `--acc-live` in figures (`f-acc`/`s-acc`, the geo layer and
the legend swatch now bind to it; `--on-acc` measures 4.61 on it, above the
floor). The cover/closing subject word moves to the owner-chosen lime-on-dark
chip (`.subj`: lime on `--on-lime`, 16.44:1, `box-decoration-break: clone`),
with D13 carving out exactly that pairing and nothing else. `--acc-live` and
`--acc-tint` join `design-tokens.json`, and `check_palette_parity` now walks
BOTH directions — a CSS colour the JSON never heard of fails (deliberate red:
un-mapping `accent_live` produced four errors naming the hole; the one-way
walk had passed it for dozens of releases).

**The brand mark is now an asset, not an instruction.** The owner named the
FIELD globe the default cover/closing mark; it is vendored at
`assets/brand/lumivate/globe-field.svg` and locked — as are the cover pair,
which had been unlocked since the lock existed. `new_deck.py` embeds it on
both marked pages (its own `<style>` stripped: inline SVG shares the
document's scope), marks the cells `data-globe`, and appends the runtime, so
the scaffold's globe TURNS (verified: land paths mutate frame to frame;
reduced-motion and no-JS fall back to the static frame). The fixtures embed
the same mark statically. D18 accepts the component's `data-bloc-label`
anchor and stops reading `gl-rg-label/n/p` as three regions named "label",
"n" and "p" (a `\b` that matched after a hyphen).

**The footer's runs now share a baseline, and a probe holds it.** `.terms` had
no rule anywhere and `.conf`'s baseline came from its 12px shield icon, so the
handling terms rode 2px above the page number on every page (measured 2.41px;
0.00 after `display: contents` + baseline alignment with the icon opted out).
`inspect_layout.py` gains `footer_baseline` — text-run bottoms as a ratio of
the line box, gated under `--deliverable` at 0.08 (half the shipped defect) —
with a planted 3px lift in the degenerate fixture as its failing case. The
`--deliverable` findings list was re-synced everywhere it is enumerated: four
files carried four different counts of it (FM-05 live), so the lists now match
the code's `deliverable_verdicts` and name it as the authority.

**And the wordmark is the literal string "LUMI Style"** (owner directive) —
carried until now only by template markup, stated nowhere in prose; both
generators, both fixtures, `storyline-templates.md` and `brand.md` now agree.
Entry points re-flowed by hand, which also caught four stale restatements:
the core prompt's display weight (400 — the exact counterexample the token
comment names), the SAME 400 inside `design-tokens.json`'s own typography
block (the mirror restating the mistake beside the CSS that names it), the
core prompt's amber/dark-seal hexes, and design-rules' §1 ledger row for the
same two. 14 tests added.

## 0.1.442 — the review breaks into the emergency path twice, and both doors get bricked up

A four-lens review of PR #92 (the audit's six releases) found its most
serious findings where they hurt most: the emergency merge path — the code
that runs with maintainer credentials when CI is down. Both were
DEMONSTRATED, not argued (spec: `specs/2026-08-13-audit-restructure-design.md`).

**The two demonstrated breaks.** (1) `check_repo`'s review-scores guard
SUBPROCESSES `ops/review_scores.py` — and the trusted closure did not carry
it, so the emergency run executed the PR's own copy of that file. The
closure is now the EXECUTION closure (imports + the subprocess), and the
regression test parses the shell script's actual array and holds it to
check_repo's real imports both directions — no hand-copied list to drift.
(2) The bootstrap appended the scripts ROOT before lib/, so a PR planting
`scripts/color_math.py` at the root outranked the trusted overwritten copy
in lib/ — arbitrary code at import time, shown live in a sandbox. Three
layers now: the drawer order is lib-first/root-last in every block, the
emergency sequence purges root-level *.py from the temp tree outright, and
a canary test plants the exact shadow and asserts it never runs. The
unchecked `cp`/`mkdir` in the trust-establishing step gained `|| die` (a
failed copy used to fall through to executing the PR's checker).

**The guards grow the teeth the review found missing**: check_bootstrap
reads the block's load-bearing CODE (append line + canonical drawer order),
not the marker comment a stub could fake, and holds SIBLING_MODULES to
lib/'s actual contents; SCRIPT_PATH_WAIVERS is keyed by (file, citation) so
waiving one illustrative line no longer exempts the whole emergency
runbook; the frozen zone narrows so the LIVE perf baseline is scanned;
`scripts/README.md` joins the pattern; validate_maps refuses dangling
DIRECTORY prefixes, not only files.

**28 of 0.1.441's 35 Contents anchors were dead on GitHub** — '·' in a
heading slugs to a DOUBLE hyphen (the dot vanishes, both spaces survive)
and the hand slugger collapsed them. check_links now resolves in-page and
cross-file anchors with a faithful slugger (it reproduced all 28 before the
fix); the four TOCs are regenerated through it.

**Prose set straight**: the runbook's closure label says what the closure
IS (imports + subprocess + one prophylactic); the "audit found broken"
claims cite the spec rather than a date that postdates the commits;
scripts/README's import-edge claims match measurement (two of build/ on
geo_*, GENRES imported directly by two ops tools, "no script imports ops/");
NOTICE's Lucide line matches the vendored LICENSE; conftest explains why
tests deliberately insert(0) where the block appends. 12 tests added (233).

## 0.1.441 — a public repo says what it is, and its licenses tell the truth

R5 of the audit (`specs/2026-08-13-audit-restructure-design.md`) — the
outward-facing pass, aligned with the published skill-authoring conventions.

**README**: CI and license badges; the License section stops saying only
"MIT" — the repository redistributes D-DIN (SIL OFL 1.1), Lucide (ISC) and
Natural Earth (public domain), inventoried in NOTICE, and a reader who only
reads README now learns that; the "three entry points" line tells the whole
truth (three hand-written, three generated); the tree block points at
scripts/README.md for the drawer map. **The ISC license text now travels
with the vendored icons** (`assets/icons/lucide/LICENSE`) instead of only
being cited from NOTICE.

**CONTRIBUTING.md** turns the maintenance conventions into a page an
outside contributor can follow — documented cases, the version lockstep,
preflight-before-push, generated-files discipline, deliberate-red runs, the
ledgers, and red line 9. **SECURITY.md** routes findings to GitHub Security
Advisories, privately.

**SKILL.md** gains the `compatibility` field the spec provides for exactly
this case (Python 3.12+, optional local Playwright + Pillow for the two
rendering tools), and its one pointer into `specs/` — engineering history
reached from skill payload — now cites the rule file instead. The four
references/ files over the authoring guides' size threshold carry a
Contents block. The plugin manifest gains `repository` and `keywords`
through the builder, never by hand.

## 0.1.440 — the last drawer closes, and the tree gets its map

R4 of the audit (`specs/2026-08-13-audit-restructure-design.md`): the seven
operator tools — run_conformance, export_pdf, output_dir, new_deck,
review_scores, and the CI-outage pair ci_wait.sh / emergency_merge.sh —
move to `scripts/ops/`, completing the reorganization. `preflight.py` stays
at the top level on purpose: the front door above five drawers.

The move's own two shell scripts were the fiddliest piece by design —
`$SCRIPT_DIR` now points inside ops/, so the trusted-check and closure
paths gained a `../`, and the emergency destination grew the check/ drawer.
The output-default guard's registered site and its name-comparison special
case moved together (the pair the plan flagged as a same-commit-or-broken
edit); the constructed subprocess paths in check_fixtures (export_pdf) and
check_repo (review_scores) were caught by the constructed-path reader added
one release earlier — the guard teaching its own migration.

**Finalization**: `scripts/README.md` gives the architect the map — five
drawers, the import edges, and where the one-copy registries live; the
timing baseline was re-recorded (every ci.yml command hash changed across
the three move releases); the final grep audit over the non-frozen tree
finds zero flat-era paths. The full battery holds: 225 tests, 25 guards,
23 CI steps, PYTHONSAFEPATH green from the new layout.

## 0.1.439 — the checkers take their drawer, and a second invisible path shape gets a reader

R3 of the audit (`specs/2026-08-13-audit-restructure-design.md`): the eight
checkers — check_repo, check_evidence, check_js, check_fixtures,
check_globe, check_design, check_prose, inspect_layout — move to
`scripts/check/`. The registry's one `_DRAWER` knob turns, which is the
0.1.437 dedupe paying out: two consumers followed without an edit.

The move surfaced the same two families as R2, each caught mechanically:
ROOT's `parent.parent` in all eight movers (fixed with the depth-agnostic
walk), and `$SCRIPT_DIR`-prefixed shell references the string sweep cannot
see (emergency_merge's trusted-check path, ci_wait's checker call — both
fixed, the emergency destination now creates the check/ drawer). The
synthetic guard tests' stub trees moved their fake checkers into the same
drawer the guards now read, and one test derived the scripts root from
check_repo's own location — made drawer-agnostic the same way ROOT was.
The locked JS assets cited checker paths in comments; swept, re-embedded,
re-locked with the reason recorded.

Verified beyond the battery: the evidence gate DEMANDED layout-fixtures and
globe-js for this diff (the moved TOUCH_MAP entries firing — an obligation
that failed to appear for a moved trigger file would have been the
stop-ship); PYTHONSAFEPATH runs green from the new path; the emergency
closure test exercises the new layout end to end.

## 0.1.438 — twenty files change drawers, and every net the last release strung held

R2 of the audit (`specs/2026-08-13-audit-restructure-design.md`):
`scripts/lib/` (the five shared libraries plus the checker
registry), `scripts/render/` (globe_svg, regionmap_svg, sea_route) and
`scripts/build/` (seven builders, four embedders) exist; twenty files moved
by `git mv`, bare-name imports untouched — the bootstrap block did its job
without an edit.

**What the move actually broke, and what caught it**: `ROOT` computed as
`parent.parent` pointed one level wrong from inside a drawer — the first
regenerator run created a stray `scripts/assets/` tree before the second
crashed loudly on a missing upstream file. Fourteen scripts now compute
ROOT by walking up to the scripts/ root, the same depth-agnostic idiom as
the bootstrap. Everything else was nets holding: the script-paths guard
enumerated all 68 files carrying old path mentions (docs, tokens comments,
generated artifacts, the locked JS assets' own comment citations); every
one of the eleven generator `--check`s proved the swept sources and the
regenerated artifacts byte-identical; the evidence gate's map self-check
forced the four TOUCH_MAP renames; the brand lock was re-keyed by hand
BEFORE `lock.py --update` (its `--update` raises on a missing path — the
ordering the plan called out) and re-locked with the move recorded.

The emergency closure now copies from `scripts/lib/`; the regression test
runs the sequence under PYTHONSAFEPATH against the new layout. Deliberate
reds: a tampered byte in `scripts/render/globe_svg.py` failed the lock
naming the NEW path; a planted mention of the OLD globe_svg path failed the
script-paths guard; both reverted by re-editing.

## 0.1.437 — before anything moves, everything that could fail silently learns to shout

R1 of the audit (`specs/2026-08-13-audit-restructure-design.md`) — and the
release that fixes a live defect the planning itself found: **the emergency
merge path has been broken since 0.1.420.** `PYTHONSAFEPATH=1` strips the
script directory from the import path, and check_repo had gained sibling
imports — so the trusted single-file copy died on `import color_math`
before running one guard, and the last-resort path (the one that runs when
CI is down) would have misdiagnosed EVERY PR as "real defect in the PR".
Recorded before fixing: the 0.1.436 tree exits with ModuleNotFoundError.
The trusted copy is now the whole closure (check_repo + the lib four, all
pure-stdlib underneath), each file overwriting the PR's version at the same
path; a permanent regression test simulates the emergency sequence under
SAFEPATH.

**Two guards arrive for the reorganization ahead.** `script paths`: every
`scripts/<path>` string in live tracked text must resolve to a file —
~180 prose and config mentions had no machine watching them, and none of a
move's documentation debt can rot silently now (CHANGELOG, specs/ and
tests' synthetic fixtures are excluded as frozen or fabricated; the guard
tripped three times during its own development — on the bootstrap comment's
hypothetical hijack path and on its own waiver reason — which is the
pattern working). `bootstrap`: any script importing a sibling must carry
the canonical path-bootstrap block (append-only, layout-agnostic, the
marker joined at runtime so the guard cannot satisfy itself).

**The rest of the hardening**: the no-shadow-math and ledger guards scan
recursively (a subdirectory could previously empty them silently); the CLI
--help floor discovers scripts at any depth; the evidence gate refuses a
TOUCH_MAP entry or OBLIGATIONS command that points at nothing (the
ENTRY_STAMP lesson); the duplicated checker map in check_fixtures and
run_conformance collapses into `deliverable_registry.py` (FM-07 closed —
the drawer the checkers live in is now encoded in exactly one knob);
conftest and mypy_path know every future drawer, keeping the strict-typing
ratchet's bare names valid forever. The bootstrap block landed in 19
scripts; brand-locked build_brand and globe_svg re-locked with the reason
recorded. 13 tests added (223 total). Deliberate reds: a dangling doc path,
a dead TOUCH_MAP entry, a deep-tree shadow def, and a stripped annotation
each turned their gate red and were reverted — by re-editing, not by
`git checkout`, which claimed one uncommitted fix during the exercise and
taught the lesson again.

## 0.1.436 — the audit's first pass: what a repo accretes, named and removed

R0 of the audit (`specs/` record follows with R1). Four findings from a
full-tree inventory, each with its story:

**A file named `1`, empty, tracked since 0.1.387** — a shell-redirect typo
swept up by a broad `git add`, sitting at the top of the GitHub file listing
for six days. Deleted. **The 298KB rendered deck at the old
`Pipeline/ideas-prd.en.html`** — created when the backlog became a deck at
0.1.386, superseded when the markdown source was restored at 0.1.422, cited
by nothing, and a deliverable committed to a repo whose own ignore rules
declare deliverables barred (it escaped because `*.html` was never in the
list). Deleted; the ignore hole is closed. **Four contact sheets in
`fixtures/_layout/` both tracked and gitignored** — indexed one day before
the ignore rule arrived, contradicting it ever since. Untracked; renders are
renders, and the evidence gate owns the record-keeping the tracking once
approximated. **`scripts/new_deck.py`, referenced by nothing** — kept and
documented in the Checks block with its own docstring's words; a deliberate
tool should not need archaeology to be discovered.

**`Pipeline/` is now `backlog/`** — the only capitalized directory in the
tree, and a name that read as CI plumbing to an outside reader when the
content is a ranked idea backlog. Every live reference moved with it
(guards, tests, docs, ignore rules); CHANGELOG and specs/ keep the old name
as frozen history. A retention line for `releases/evidence/` is written
down: kept forever, small, the audit trail — the gate only reads the
current file, so there is nothing to prune for.

## 0.1.435 — a score row pins its instruments (IDEA-8): "the skill changed" stops rendering as "the agent is flaky"

IDEA-8 ships, on the owner's instruction, with GAP-001's misread as its
documented case. `task_hash` pinned the question; nothing pinned the ruler
or the artifact's vintage, and the cost was measured twice this week: the
archived T1 failures hung on the board for three weeks reading as agent
incapacity when they were verdicts about a pre-0.1.380 skill, and merging
old and new runs rendered "3 runs UNSTABLE" — a true sentence about mixed
skill versions wearing the costume of agent flakiness.

**The record half**: every `score` entry now carries `instrument_version`
(the skill/checker version doing the scoring) and `built_version` (read
from the deliverable's own colophon line; markdown answers without one stay
honestly unknown). `report --record` copies both onto history rows.

**The render half**: `cell_spread` (extracted pure and tested both ways)
decides what a verdict conflict means. A conflict that ALIGNS with
different builds — every build one verdict, more than one build, all builds
known — renders as "skill changed between builds: fail@0.1.364, pass@0.1.433"
with the LATEST build's verdict governing, symmetric in both directions (a
new build failing where the old passed is a named regression). Any conflict
builds cannot explain — same build disagreeing, or a vintage unknown —
stays UNSTABLE, which errs toward the uncomfortable reading. Eight tests,
including numeric-not-lexical version ordering.

The 2026-08-13 runs were re-scored to carry the fields (instrument 0.1.434,
deck built 0.1.433, verdicts unchanged) and re-recorded; the scoreboard's
superseded-runs note now points at the mechanism instead of promising it.

## 0.1.434 — GAP-001 closes: both agents pass T1-deck against the rules that fixed it

The verdict is re-earned, not re-argued. T1-deck was re-run on both scored
agents against the 0.1.433 rules: **Cursor, hand-driven by the operator —
pass**; **Claude Code, driven clean with the skill — pass** (T2 and T3 also
pass, giving that row all three tasks). Scored with `run_conformance.py`,
recorded with `report --record`; the history rows pin skill 0.1.433, which
is what lets this closure say precisely what was measured against what.
**GAP-001 → fixed**, one diagnosis and one re-run after it was opened — the
ledger's second full entry-to-closure cycle.

**The scoreboard now renders the current-skill runs** and names the
2026-08-08/09 runs as superseded: they measured a skill that shipped a
colliding media block in its own tokens until 0.1.380, with instruments
added after the decks were built (the GAP-001 diagnosis). Merging them into
the current cells produced "3 runs UNSTABLE" — a true sentence about mixed
skill versions misread as agent flakiness — so the table answers "does the
CURRENT skill conform" and `history.json` keeps every row with its version.
IDEA-8 (a score row pins its instruments) remains the structural fix.

**Operator observations recorded** (review protocol input, not rules):
Cursor needed multiple repair rounds before its deck passed — first-pass
yield is a real cost the scoreboard does not yet see; and the clean Claude
Code run's own verification loop caught and fixed four layout defects and
one prose-frame failure before delivery, which is the pre-delivery gate
doing its job. The operator's read: "basically in place; small issues to
optimize later."

## 0.1.433 — the ledgers do their first real work: GAP-001 diagnosed, GAP-003 closed, and the backlog audited

The post-merge sweep of everything the ledgers held, driven by the owner's
"merge, then handle the leftovers" (owner directive, 2026-08-12; spec:
`specs/2026-08-12-engineering-quality-design.md`).

**GAP-001 diagnosed to root cause — and the dominant failure was the skill's
own.** Every archived T1-deck verdict was reproduced with today's checkers.
The collision failures on BOTH agents trace, causally (neutralizing the one
block clears every collision; the rival hypotheses were falsified first), to
a window-keyed media block that sat in `tokens/lumi-layouts.css` itself
until 0.1.380 — both agents copied it verbatim, comment included. The decks
were built at 0.1.364-0.1.371 and scored by instruments created at
0.1.368-0.1.390: true verdicts about stale artifacts. Two LIVE skill defects
found in the process, both fixed here as rule revisions with this diagnosis
as their documented case:

- `references/storyline-templates.md` mandated `[TO FILL]` contact slots
  while D14 gates a finished document at zero placeholders — a fully
  compliant agent could not satisfy both (Cursor obeyed the template to the
  letter, caveat sentence included, and failed the gate for it). The closing
  template now says: real contacts from the user, or omit the slots and name
  the owning role in prose; brackets belong only in drafts.
- `scripts/check_prose.py` M6 counted "Plastics (1–2)" — an enumeration
  label naming resin types — as an unsourced numeric range. A dashed pair in
  a short block carrying no figure-shaped number anywhere is now reported as
  a label, never counted; anything with quantitative context still counts.
  The Cursor deck's M6 goes to 0 on the truthful label; the broken fixture's
  planted range still fails (coverage stays 34/34).
- `references/design-rules.md` §7 still told authors to "provide
  height-based media queries" off a `min-height:100svh` rationale that died
  at 0.1.343 — the exact sentence both agents obeyed when they invented
  their colliding blocks. It now says what the check proves (the fixed
  stage SCALES) and bans window-keyed restyling of the stage's insides.

The five remaining findings are agent-capability, not rule material
(overspent title reserves against a stated ceiling, inline role overrides,
an overfull closing page shipped against the agent's own screenshot, a
1-unit descender clip, one unsourced page). GAP-001 stays OPEN with its
closure step recorded: the frozen artifacts cannot flip by any repo edit —
T1 must be re-run on ≥2 agents against current main and re-scored, and
Cursor is hand-driven, so the re-run needs the operator. The diagnosis also
seeded **IDEA-8** (a score row should pin its instruments: `task_hash` pins
the question, nothing pins the ruler).

**GAP-003 closed.** `tests/test_record_producer.py` drives the real
`report --record` against a synthetic registry: one row per agent, digest
pinning, idempotency, accumulation-not-overwrite. Closing it found the
defect the ledger predicted category-wise: a corrupt scores.json crashed
the report merge loop with a traceback BEFORE the --record block's own
"does not parse" guard could fire — that guard was unreachable dead code,
now reachable and tested.

**Guard test waves 2 and 3**: the remaining fourteen `check_repo` guards
get synthetic pass+fail trees (61 new tests; suite now 202). Wave 2 covers
output-default through probe-vocabulary; wave 3 covers media-only through
brand-lock, including the subprocess-delegating and import-delegating
guards, each by the least-magic seam available.

**The backlog audit.** Item-by-item verification against the tree found
the restored survey mostly absorbed by later releases: IDEA-1 and IDEA-5
shipped at 0.1.390 (`0145bfb`), IDEA-6's acceptance is the registry's
`population_note` (the written-waiver branch), IDEA-7 shipped at 0.1.427.
The one genuine survivor is IDEA-2 (Chinese as a supported output path).
The status block now says so, with the correction itself recorded — a
restored ledger that silently carries a stale state is drift wearing a
ledger's clothes.

## 0.1.432 — a hash is not a name: the evidence gate survives its first rebase

The first merge to `main` (PR #87, rebase-merged to keep the sixteen release
commits individual) rewrote every commit hash — and turned each evidence
file's `diff_base` into a dangling pointer. `check_evidence.py --check`
reddened main exactly as 0.1.431 hardened it to ("does not resolve in a
full-history checkout"): the gate was right that something did not resolve,
and wrong about what that meant.

The recorded SHA is rebase-fragile by construction; the commit SUBJECT is
not — a rebase preserves messages, and the commit-convention guard makes
release subjects reliable. `--check` now re-resolves an unresolvable base by
finding the previous release's `X.Y.Z — ` subject before calling anything a
finding, printing the re-resolution as a note. The failure remains for the
case that deserves it: a base that resolves by neither hash nor subject.
The test that asserted "bogus SHA fails" split into the honest pair: bogus
SHA with a subject-matching predecessor re-resolves and passes; bogus SHA
with no matching subject fails naming both misses.

## 0.1.431 — the review turns its findings on the gate that was built to catch them

A four-lens review of PR #87 — the migration of
`specs/2026-08-12-engineering-quality-design.md`, reviewed for correctness,
test coverage, silent failures and comment accuracy — found the migration's
own gates carrying three of the
failure shapes they were built to end, plus a sweep of smaller holes. All
closed here; every fix carries a test that fails against the shipped code.

**The three that mattered.** (1) The `conformance-freshness` obligation
could be discharged by recording its `validate` command — which exits 0 on a
STALE board; the code's own comment said a recorded run "would prove
nothing", and the code accepted exactly that. `record` now refuses the id;
the only satisfactions are a fresh board or a waiver. (2) A blank or bogus
`diff_base` in the evidence file switched off the obligation recompute AND
the spec rule with only a stdout note — the audited artifact could disarm
its auditor. Now: unresolvable base in a full-history checkout is a FAILURE;
the degradation survives only where it is legitimate (a genuinely shallow
clone, detected as such and still named). (3) `check_commit_convention` was
disarmed on merge commits — `git diff-tree` prints nothing for a merge
without `-m --first-parent`, and the PR checkout CI judges is always a
merge; the one path CI takes was the one path untested. Fixed, with merge
and merely-"Merge "-titled commits both covered by new tests.

**The rest of the sweep**: `_compare_port` now refuses a short or empty JS
result list (zip truncates silently — an empty backend response previously
read as agreement on 1300 samples); `check_js` discovers probes by naming
convention instead of a hand tuple (the exact rot this migration removed
from ci.yml, reintroduced twelve files away); `check_secrets` distinguishes
a tarball (exempt) from a git failure inside a checkout (a finding); the
ledger guard catches near-miss headings ("## GAP 003") that previously fell
out of every structural check — and the first version of that catch had a
broken kind-extraction the new tests refused, which is the discipline
working; presumed version stamps are now named per run instead of silently
filtered; a corrupt conformance history reads as stale (fail-closed) instead
of crashing; preflight coerces baseline numbers and declines to record a
baseline from a failed run; `run_conformance --record` fails loudly on a
corrupt scores.json.

**Coverage the review demanded**: `tests/test_check_evidence.py` gives the
gate its synthetic-tree suite (15 tests — the eight failure shapes plus the
stamp filter both ways); 31 tests added in all, 136 total. The GitHub token
patterns get fixtures; weak assertions were strengthened; the
freshness-ignores-verdicts property became a real assertion. The
`report --record` producer path stays untested and is LEDGERED as GAP-003
with its mitigations, rather than left as folklore.

**Prose drift the review caught**: check_globe.py's own docstring still
described the pre-0.1.426 world ("nothing in this repository can compile
JavaScript") — rewritten; the "--help floor over every CLI" claim narrowed
to what the test actually enforces (argparse CLIs); AG-3 cited a flag that
does not exist (`--timing` → `--timing-update`); the evidence gate's dates
and two hand counts corrected; CLAUDE.md's guard list marked as
representative with the CHECKS tuple named as the authority.

## 0.1.430 — the type checker's verdict depended on which machine asked

The migration's first CI run failed on a step every local run had passed:
mypy red on `import PIL` — Pillow is an optional local dependency
(inspect_layout's pixel audit, check_globe's browser half) that exists on
the operator's machine and not on a clean runner, and the playwright
override in `pyproject.toml` had no PIL sibling. A tool configuration that
resolves imports from whatever happens to be installed is FM-06 wearing a
new coat: "local green" and "CI green" were briefly different claims again,
one config line apart. Both optional dependencies now carry explicit
`ignore_missing_imports` overrides, with the comment saying why.

## 0.1.429 — the documentation catches up with the migration it documents

The closing release of the engineering-quality migration
(`specs/2026-08-12-engineering-quality-design.md`, R1-R12 shipped as
0.1.416-0.1.428). What changed here is prose, and the prose is load-bearing:
drift between what the repo does and what its documents say it does is this
repo's named main hazard.

**CLAUDE.md**: the Checks section gains the new commands (check_js,
check_evidence, pytest/ruff/mypy), the step-count is deleted rather than
corrected ("seventeen" here and "fifteen" in preflight's docstring were both
somebody's memory of the workflow), the guard inventory gains its four new
members, the "no JavaScript toolchain" paragraph is rewritten for a world
where CI verifies the port under bare node, the evidence gate replaces
"verdicts are recorded in the release notes", and two maintenance
conventions arrive: **rule 10** (state lives in the ledgers — deferral names
an id, dangling citations fail CI, declined gates go to Abandoned gates)
and **rule 11** (a new gate ships with a deliberate-red run and
failing-fixture tests). **README** file map: tests/, releases/evidence/,
the ledgers, the shared modules, the restored backlog.

The three entry points and prompts restate style rules, not engineering
process, and were re-read rather than edited — no engineering claim lives in
them to drift.

## 0.1.428 — a secrets guard that preflight can run, a --help floor, and a timing baseline that only warns

Release R12 of the engineering-quality migration
(`specs/2026-08-12-engineering-quality-design.md`) — the closing sweep.

**`check_secrets` is the 23rd guard.** Five high-signal patterns (AWS keys,
private-key blocks, GitHub tokens, credential-shaped assignments) over every
tracked text file, with a reasoned waiver table for rule data. A guard
rather than a marketplace action because preflight runs what CI runs, and a
gate living only in a workflow is invisible to the local half of that
contract (AG-5). Each pattern is written so it cannot match its own source.
Tested both ways on synthetic git trees, including the binary-skip and the
waiver path; the live tree is clean.

**Every argparse CLI answers `--help` or the suite is red.** The cheapest behavioral
floor there is: an import-time crash, broken argparse wiring, or a missing
module-scope dependency in any of the operator scripts now surfaces in the
test suite instead of mid-release.

**preflight grows a local timing floor.** `--timing-update` records per-step
wall time to `releases/perf-baseline.json` (keyed by command digest, so
reordering steps cannot misalign a comparison); every later run prints
`WARN slow` for a step exceeding max(2x baseline, baseline + 5s). Warn-only
and local-only by design: a baseline is one machine's number, and a
cross-machine fail-gate fails for reasons unrelated to the code — AG-3
records the declined stronger version.

## 0.1.427 — the conformance board gets a memory, and freshness becomes an obligation

Release R11 of the engineering-quality migration
(`specs/2026-08-12-engineering-quality-design.md`) — the IDEA-7 work: making
the multi-agent scoreboard mean something over time.

**`conformance/history.json` is the tracked memory.** The scoreboard in
CONFORMANCE.md is regenerated per release and stamps the CURRENT version, so
"when was this actually measured, against what" was unrecoverable — the
three existing run directories are seeded into history with their version
recorded honestly as pre-history rather than guessed. Going forward
`run_conformance.py report --record` appends one row per scored agent per
run — skill version, date, per-task verdicts, and the digest of the
untracked scores.json, which is what makes a row evidence rather than an
assertion. `validate` (already in CI) refuses a malformed history.

**The evidence gate's `conformance-freshness` obligation is armed.** A
release that changes the rule surface while the board trails head by more
than 15 releases owes fresh rows for at least two agents across all three
tasks, or a written waiver. The gate binds on the RECENCY of measurement,
never on passing: both scored agents currently fail T1-deck, that failure
lives on the ledger as GAP-001, and a pass-gate would block every release
forever while inviting exactly the overclaim this migration exists to kill.

Deliberate reds: a history row stripped of its agent key failed `validate`;
the freshness logic is unit-tested in both directions (two recent agents =
fresh; one recent = stale; pre-history rows = stale by construction).

## 0.1.426 — CI verifies the JavaScript port for the first time

Release R10 of the engineering-quality migration
(`specs/2026-08-12-engineering-quality-design.md`). The golden grid — 1300
projection samples, the ONLY thing holding `assets/geo/projection.js` to the
Python authority — had never been read through JavaScript by any CI run:
the comparison lived behind Playwright, so it ran when an operator
remembered.

`projection.js` is DOM-free maths, and bare `node` can import it.
`check_globe.py` now splits "obtain the JS results" from "compare against
the golden grid" (the compare was always backend-agnostic) and gains a
`--node` backend that pipes the grid through a plain node process. The CI
step becomes `--python-only --node`: the port is verified on every push,
with no browser. A missing node is a FAILURE, never a skip. The remaining
browser checks (renderer parity, painted ink, occlusion) stay operator
steps, recorded through the evidence gate like any other.

Deliberate red: multiplying one `Math.sin` in the port by 1.000001 failed
the node check across the grid; reverting restored agreement on all 1300
samples.

## 0.1.425 — the evidence gate goes red, and GAP-002 is the first ledgered closure

Release R9 of the engineering-quality migration
(`specs/2026-08-12-engineering-quality-design.md`). One release of warn-only
operation proved every failure shape fires (a deleted obligation, a copied
digest, an overclaim phrase beside a waiver — all demonstrated in 0.1.424's
red runs); the `--warn` flag comes off and `check_evidence.py --check` now
blocks.

Verified the way the gate itself demands: the same planted violation that
warned last release **exits non-zero and reddens preflight** now, and the
honest run is green. **GAP-002 flips to fixed** — the five operator checks
are no longer verified by sentences; an execution record with a command,
exit code and output digest is the only thing the gate accepts, and this
CHANGELOG citation is what the ledgers guard requires of a closure. The
ledger's first entry-to-closure cycle completes in three releases, which is
the point of having a ledger.

## 0.1.424 — the evidence gate arrives, warn-only, and writes its own first file

Release R8 of the engineering-quality migration
(`specs/2026-08-12-engineering-quality-design.md`) — the centerpiece, and
the release that starts closing GAP-002.

**`scripts/check_evidence.py` + `releases/evidence/<version>.json`.** What
CI cannot execute — the browser layout gates, the globe's JS half, and (once
armed) conformance freshness — must now be EXECUTED and recorded, never
narrated. The schema's load-bearing decision: **there is no verdict field.**
`record --id <obligation>` runs the canonical command itself and
machine-writes exit code, output digest and date; a human never types
"pass", so an unexecuted claim has no field to live in. Big artifacts stay
local; the tracked file carries command + exit code + digests — re-runnable
evidence in the lumi SOP's R2 sense.

**Obligations are computed, not declared.** `--init` maps the release diff
through a TOUCH_MAP; CI recomputes them from `diff_base` (checkout now
fetches full history), so a hand-deleted obligation is caught. Version-stamp
bumps in the stamped files do not count as touches — a gate that nags on
every release becomes a gate waived on reflex. A nonzero recorded exit must
cite an OPEN KNOWN_GAPS entry (the assert-broken-behavior pattern); two
checks sharing an output digest fail (copied evidence); the spec rule folds
in (>150 changed rule-surface lines require a cited specs/ file or a
reasoned waiver); and the overclaim phrases — "all gates green" and its
family — fail the gate when written in a release that carries waivers.

**Warn-only for exactly this release** (the step ships as `--check --warn`),
because a gate's first exercise should not be able to block the release that
introduces it. Three planted violations were shown to fire under warn: a
deleted obligation, a duplicated digest, and an overclaim phrase beside a
waiver. The gate goes red next release, which is also when GAP-002 flips to
fixed.

## 0.1.423 — the commit subject convention grows teeth, scoped to where it matters

Release R7 of the engineering-quality migration
(`specs/2026-08-12-engineering-quality-design.md`). CLAUDE.md rule 3 has
required `X.Y.Z — summary` subjects for a long time; ~10 of the last 40
commits deviated and nothing noticed, because nothing checked.

**`check_commit_convention` is the 22nd guard**, and its scope is the
lesson: only a commit that TOUCHES `CHANGELOG.md` must carry the version
prefix, and the version must equal the newest heading — specs-only commits,
fixture regens and backlog edits are exempt, which is exactly what the
historical deviations were. A convention enforced wider than its purpose
would have reddened ten legitimate commits to catch zero real defects.
Merge commits are judged by their second parent; a tarball checkout (no
`.git`) asserts nothing; history is not retroactively reddened — only HEAD
is examined. Branch naming stays unenforced, recorded as AG-2.

Tested on synthetic git repositories (conforming passes; missing prefix
fails; subject/heading version mismatch fails — "one of them is lying about
what this release is"; non-CHANGELOG commits and no-git trees are exempt),
and deliberately reddened once on the live repository: a commit touching
CHANGELOG.md with the subject "a subject with no version" failed the guard
and was reset away.

## 0.1.422 — the ledgers: gaps, failure modes, and the backlog comes back from the dead

Release R6 of the engineering-quality migration
(`specs/2026-08-12-engineering-quality-design.md`). Until now this
repository's institutional memory of its own defects lived as prose inside
CHANGELOG entries — vivid, and unqueryable. Three ledgers make it state.

**`KNOWN_GAPS.md`** tracks concrete open defects with machine-checked
structure. Seeded with the two that were living as folklore: **GAP-001**
(both scored conformance agents fail T1-deck — on the scoreboard for months,
tracked toward closure by nothing) and **GAP-002** (the five checks CI
cannot run are verified by sentences in release notes — the gap the
evidence-gate release exists to close, and this entry is how its closure
will be recorded rather than merely claimed). The lumi project's rule
arrives with the file: tracked bugs live in the ledger, and a TODO in a
script citing a GAP id fails CI.

**`FAILURE_MODES.md`** registers the ten escape classes extracted from this
changelog's own history — the check that could not fail, the guard in the
wrong language, prose-copy drift, reverse drift, enumeration rot,
local-green-is-not-CI-green, generator/consumer asymmetry, the number with
no stated direction, the rule mandating an unshipped asset, and
only-the-eye-finds-it — each with detection and prevention pointers, plus
an **Abandoned gates** section recording six declined mechanisms with
reasons, so a declined idea is a decision rather than a quarterly re-debate.

**`Pipeline/ideas-prd.md` is restored** from the commit that deleted it
(`e861df0` left only the 298KB rendered deck), with stable IDEA-ids and a
dated status block: IDEA-3 and IDEA-4 verifiably shipped since the survey,
IDEA-7 is in progress as this migration's conformance work, four remain
open.

**`check_ledgers` is the 21st guard**: id uniqueness, legal statuses,
per-status required keys, a closed entry's release must exist in the
CHANGELOG *and* cite the id, no GAP-citing TODO in scripts/ or references/,
and no dangling GAP/FM/IDEA citation anywhere in CHANGELOG or specs/. What
an entry says stays with the reviewer — a guard judging prose would be
FM-01 in its own registry.

## 0.1.421 — five guards are shown able to fail

Release R5 of the engineering-quality migration
(`specs/2026-08-12-engineering-quality-design.md`).

Until now every guard in `check_repo.py` had run only against the live
repository — which is always in the passing state, so a guard rewritten to
`return []` would have gone unnoticed for as long as the defect it watches
for stayed away. That is precisely how 0.1.390 found three checkers
"incapable of failing" after they had been reporting green.

`tests/test_check_repo_guards.py` (16 tests) puts the first five guards on
synthetic trees, each with a passing fixture AND a failing fixture per
failure mode: **check_versions** (agreement passes; one diverging stamp
fails naming the file; a missing stamp fails rather than being skipped),
**check_english_only** (CJK prose fails; backticked CJK data and the
allowlisted rule files do not), **check_palette_parity** (a diverging hex,
an unmapped JSON key, and a mapped key with no CSS var each fail),
**check_version_citations** (an undefined version fails; a waived one
passes; a stale entry-point stamp naming a real older release fails —
the mode only the stamp-position half can catch), and **check_links**
(a broken relative target fails with file:line; external URLs are proven
never to be resolved). The remaining fourteen guards follow in later waves.

## 0.1.420 — four copies of the color math become one, and a guard keeps it that way

Release R4 of the engineering-quality migration
(`specs/2026-08-12-engineering-quality-design.md`) — the dedup the last two
releases prepared for.

**`scripts/color_math.py` and `scripts/css_tokens.py`** now hold the one
sRGB/WCAG implementation and the one CSS custom-property reader, both under
strict mypy from birth. check_repo, check_design, build_brand,
build_region_palette and inspect_layout import them; their private copies are
deleted. The linearizer threshold is unified at 0.04045 (IEC 61966-2-1, the
WCAG errata value) — a decision made byte-safe by 0.1.419's measurement, and
proven byte-safe here: **every generator `--check` reported its output
current after the switch**, brand SVGs included.

**The build_brand bug died on schedule.** `rule_vars` strips comments and
reads the block to the *matching* brace; the old `_vars` was proven identical
on all six real call sites first (the bug had never fired on production CSS —
which is why no shipped byte ever showed it), then replaced. 0.1.419's two
strict xfails XPASSed exactly as designed and were promoted to plain
regression tests, joined by a new one: an unbalanced brace inside a comment,
which the extraction survives because comments are stripped before the block
is located.

**`check_no_shadow_math` is the 20th guard.** It fails any script that
re-grows a `def` of the shared function names outside the two modules —
imports and calls are fine, a fresh definition is the drift. Tested on
synthetic trees both ways (a clean tree passes, a re-grown `_lin` fails,
prose mentions do not trip it), because a guard shown only passing has not
been shown to work.

**What deliberately did not move**: build_region_palette's
high-precision-coefficient `lab_of` luma (a different formula for a
different purpose — Lab, not WCAG), and check_design's `token_blocks`
(light/dark semantics, not generic parsing). The brand lock was updated for
the `_vars` removal, reason recorded.

## 0.1.419 — the first tests, and a live bug pinned where it lives

Release R3 of the engineering-quality migration
(`specs/2026-08-12-engineering-quality-design.md`). The ~16.4k lines of
scripts/ (16,398 at the 0.1.415 audit) had zero test files; `tests/` now exists and `python3 -m pytest -q` is a CI
step. The suite is deliberately small and aimed, not a coverage drive.

**Characterization before refactor.** `test_color_math.py` and
`test_css_tokens.py` pin the CURRENT behavior of the duplicated color and
CSS-parsing copies — including the exact fact that makes the coming
unification byte-safe: the two linearizer thresholds (0.03928 in
check_design/check_repo, 0.04045 in build_region_palette) agree on **every
integer channel value 0-255** and disagree only on the non-integer mixes
that the alpha-ladder floor produces, by at most 2e-5. R4 can now prove it
changed nothing it did not mean to change.

**The build_brand bug is pinned as a strict xfail, not fixed.** 0.1.415
fixed comment-parsing in `check_repo.css_vars` and the same class stayed
live in `build_brand._vars`. Characterizing it found the repro is narrower
than assumed: the line-anchored `re.match` misses same-line comment
citations harmlessly, and fires when a **multi-line comment's continuation
line begins with a declaration-shaped citation** — verified live,
`{'--bg': '2.71 against white'}` parsed out of a comment. Two
`xfail(strict=True)` tests assert the correct behavior; when R4's shared
module fixes it they will XPASS and force their own promotion. A bug the
suite asserts is a bug that cannot be quietly forgotten (the KNOWN_GAPS
pattern, arriving properly in R6).

**What else is covered**: `check_repo`'s contrast-floor guard against
synthetic palettes (one passing, one failing — proving the guard can fail);
`sea_route`'s grid geometry and pathfinder on a synthetic water world
(round-trips, seam wrap, connected paths, walled-in goal returns None);
`review_scores.validate` shown clean on the shipped store and shown to
refuse a free-text key (the red-line-9 defense), a self-5-without-reader,
and an out-of-anchor score. Deliberately NOT tested: geo_projection (the
1300-sample golden grid owns it), Playwright paths, and the eleven
generator `--check`s (CI owns them) — a duplicated check is a drift source.

**The gate can fail**: a planted `assert 1 == 2` failed the run and was
removed (design rule D8).

## 0.1.418 — the type checker goes from 105 findings to gating

Release R2b of the engineering-quality migration
(`specs/2026-08-12-engineering-quality-design.md`) — the mypy burn-down that
0.1.417 deferred rather than rushed.

**105 findings across 21 files, now zero, and `python3 -m mypy` is a CI
step.** The floor is `check_untyped_defs`: function bodies are type-checked
without requiring 16k legacy lines to be annotated first. Almost everything
was annotation debt — empty containers mypy could not infer
(`out: dict[str, list[str]] = {}`), tuples that widen across a loop,
`Match | None` flowing into `.group()`. The genuinely rotten corner was
`run_conformance.py`'s score/report path, where one name (`seen`) held a
str, a dict and a list at different lines — renamed so each name has one
type, logic untouched.

**The discipline was byte-equivalence, not review confidence.** Every
generator `--check` in the workflow proved its output byte-identical after
the edits; `check_globe.py --python-only`, `check_fixtures.py`,
`check_prose.py` and `check_design.py` on the fixtures produced
byte-identical reports before and after. Narrowing guards were added only
where the `None` state is provably unreachable, and they `raise` rather
than `assert` because ruff's S101 bans asserts outside `tests/`. Two narrow
`# type: ignore[attr-defined]` remain, both in `output_dir.py`'s Windows
registry branch, where typeshed gates `winreg` attributes on the platform
and no annotation can help a darwin/linux run; each carries its reason.

**The gate can fail**: a planted `int`-returned-as-`str` failed the run and
was removed (design rule D8). The brand lock was updated for the annotation
edits to its frozen sources, reason recorded in the lock.

## 0.1.417 — the scripts get a linter, and the linter's first catch is this repo's own failure family

Release R2 of the engineering-quality migration
(`specs/2026-08-12-engineering-quality-design.md`).

**The toolchain.** `pyproject.toml` (tool configuration only — deliberately no
packaging tables; the deliverable path stays standard-library-only) and
`requirements-dev.txt` (exact pins) bring in ruff as linter and security
scanner. CI installs the pinned tools and runs `ruff check .`; `preflight.py`
picks both steps up from the workflow, so local and CI lint with identical
versions by construction. The rule set is curated, not maximal: defaults plus
import order, bugbear, pyupgrade, flake8-bandit (`S` — the Python security
scan) and comprehensions. No `ruff format`: it would rewrite most of 16k lines
and destroy blame on comments that are load-bearing institutional memory.

**62 findings, two of them this repository's own recurring families.**

- `VERSION_CITATION_WAIVERS` in `check_repo.py` defined the keys `"1.4.11"`
  and `"2.5.8"` **twice each** — two releases each added their own WCAG
  waiver, and the literal duplicate silently shadowed the first. Enumeration
  rot inside the very table that exists to manage exceptions; a linted dict
  literal now refuses it.
- A lambda in `check_globe.py`'s winding sweep closed over the loop variables
  `top`/`bottom` late (B023). In today's shape the call happens in the same
  iteration, so no wrong verdict shipped — the binding is now explicit so the
  next edit cannot turn it into one.

The rest: unused imports and variables, a shadowed `ROOT` import in
`globe_svg.py`, ambiguous single-letter names, printf-style formatting, one
semicolon statement. Three rules are deliberately ignored with recorded
reasons in `pyproject.toml`: B905 (21 `zip()` sites — flipping them to
`strict=True` changes runtime behavior and waits for test coverage), S603 and
S607 (every subprocess call runs a repo-controlled argv list; PATH lookup of
`git`/`node`/`python3` is intended). `preflight.py`'s `shell=True` keeps a
targeted S602 ignore pointing at its own justification comment.

**The gate can fail.** A planted unused import failed `ruff check .` and was
removed (design rule D8).

**mypy is configured but not yet gating.** `check_untyped_defs` over
`scripts/` reports 105 findings in 21 files — annotation debt and inference
limits, none a live defect on inspection. Per the plan's stop-loss, the
burn-down is its own next release rather than a rushed appendix to this one;
the CI step lands with it.

## 0.1.416 — a compile list that cannot rot, and the JavaScript gets a syntax gate

The first release of the engineering-quality migration
(`specs/2026-08-12-engineering-quality-design.md`, owner directive 2026-08-12 —
the audit behind it found the deficits; this entry ships the two cheapest).

**The compile list had rotted to 26 of 29.** CI's `py_compile` step enumerated
scripts by hand, and the enumeration was stale in the way this repository's
own conventions predict every enumeration goes stale: it omitted
`review_scores.py`, `sea_route.py` — the 425-line router 0.1.415 shipped —
and `preflight.py` itself, the script whose entire job is guaranteeing that
"local green" and "CI green" are the same claim. A syntax error in the
completeness checker would have shipped without any check noticing. The step
is now `python3 -m compileall -q -f scripts/`: it covers whatever is in the
directory, so there is no list to rot, and `-f` forces recompilation so a
cached `.pyc` can never mask a fresh error.

**The JavaScript had no syntax gate at all.** Eight tracked `.js` runtimes
(2,319 lines) and three browser-side probes embedded as Python strings in
`inspect_layout.py` (~1,150 lines) — `py_compile` reads the latter as prose.
This is the exact gap 0.1.414 named ("the guard shipped in Python, the
runtime is JavaScript"). `scripts/check_js.py` parses both surfaces with
`node --input-type=module --check` on stdin — no package.json, no toolchain,
a bare `node` binary — and a missing `node` is a FAILURE, never a skip
(0.1.386: a check that skips is not a check that passed). The embedded probes
stay embedded: extraction would change inspect_layout's single-file operator
story for zero added checking power.

**The gate was shown able to fail before it shipped** (design rule D8 —
three checks in this repository's history ran green and were later found
incapable of failing). A planted unbalanced brace in `assets/geo/pick.js`
failed the run with `SyntaxError: Unexpected end of input`; a planted error
inside the `PROBE` string passed `py_compile` — the blind spot, demonstrated
— and failed `check_js.py`. Both plants were then removed and the run went
green.

**`preflight.py`'s own docstring carried the failure it exists to prevent.**
It said CI is "FIFTEEN commands" — seventeen at the time of writing, about to
be eighteen. The count is deleted rather than corrected, by the file's own
argument: a hand-maintained idea of "everything" was the original bug.

## 0.1.415 — a lane is drawn over water by construction, and the named parallels stop being graticule

**The lanes.** A trade lane drawn as a great circle goes through the planet. The
first repair named the canals and straits as waypoints, which is what an atlas
does, and it was not enough: the legs BETWEEN the named gaps ran straight across
Spain, France, Mexico, Australia and South Africa. Measured against the shipped
topology, **586 of 1,494 samples on twelve of thirteen lanes were inside a
country polygon**.

The second repair was more waypoints. It went from 39% of samples on land to 14%
and **stopped converging**, because every waypoint you add creates two legs that
each clip something new. Three rounds of that is the whole lesson: hand-placed
waypoints are whack-a-mole, and the shape of the fix was wrong rather than
incomplete.

`scripts/sea_route.py` routes over water **by construction**. It rasterizes the
land polygons into a quarter-degree mask, carves the canals, and runs Dijkstra
over the water cells; a route it returns cannot cross land, because a path
through a land cell does not exist in the graph. That is a different kind of
guarantee than a route that has been checked and found clean.

Two lists, and the distinction between them is the honest part. **Canals** are
open because somebody dug them — no raster of a coastline contains Suez at 200
metres. **Narrows** are open because the raster is coarser than the water:
Gibraltar is 14km against a 28km cell, and the first run of the router returned
NO ROUTE from the Gulf to the Indian Ocean because Hormuz had closed. Raising
the resolution moves that line without removing it.

Re-measured on the geometry that ships: **52 of 1,847 samples, every one of them
one to three points at a quay or inside the Panama cut.** Both correct — a lane
ends at a dock and a ship goes through the canal.

**The check discriminates.** `--check` also measures the naive great circle
between the same ports and requires it to come back dry, 55% to 92% on land. A
check that can only pass has not been shown to distinguish anything, and three
checks in this repository were written, run green, and later found incapable of
failing.

**Two defects found while measuring, both of them mine, both the same family.**
The land count was taken against a route rebuilt from the waypoints rather than
against `lane["points"]`, which is what the document draws — a measurement of a
reconstruction is not a measurement of the artifact, and it disagreed with the
router by 22 samples. And Douglas-Peucker was **undoing the routing**: it
collapsed each coastal detour into the chord the detour existed to avoid, so
every corner was on water and the line between two corners was through Holland.
Simplification is now refused where the shortcut is dry.

**The parallels.** The equator and the tropics are where the planet's axial tilt
puts the sun overhead; the graticule is a grid somebody chose. Drawing them in
the same grey said they were the same kind of thing. They are now gold — antique
rather than leaf, because a metallic gold measures 1.7:1 on the plate and the
stroke floor is 3.0 — and heavier, equator 3 to 5 and tropics 2 to 3.5.

**The dark rule ladder was the light one copied across.** A reader called the
dark edition's inner-page dividers invisible. The ratio understated it: 18%
white on near-black measures 1.71:1, which reads as adequate beside the light
edition's 1.47:1, and is still a line you cannot find. A hairline is judged on
the absolute step in light across it, and there are 29 levels to spend down here
against 255 up there. Raised to .32/.20/.13, above its light counterpart on
purpose rather than matched to it.

**Three parsing and provenance defects, each found by making a change the old
code had never been asked to make.**

`css_vars` in `check_repo.py` never stripped comments. Every token here is
documented in prose beside it and that prose cites token names, so a comment
reading "measured against --bg: 2.71 / 1.82" parsed as a declaration of `--bg`.
It failed loudly, which was luck — the same misparse on a token the JSON does
not carry would have been silently absent.

`build_brand.py` resolved the DARK block against the LIGHT palette. Invisible
for as long as every dark chrome value was a literal, because there was nothing
to resolve. The moment `--gl-equator` became `var(--gold)`, the dark mark would
have been stamped with the light gold at 1.4:1 on a near-black plate — and a
self-contained mark carries resolved literals, so nothing downstream could have
corrected it.

`.cap .d` had **no rendering in `tokens/`**. `inspect_layout.py` has asserted it
since it learned to read caption prose, so a document that added the class got
browser-default serif under a 10px caption. The vocabulary guard did not catch
it because that guard reads the probe's named class lists and this one is
reached by an inline `querySelector` — a hole in the guard, not a licence for
the class. Repaired the way this file's own convention asks: the rendering
ships, rather than the check being relaxed.

**`scripts/preflight.py`: local green and CI green become the same claim.**
This release was verified locally against eight gates, reported as "all gates
green", and failed CI on the ninth. `check_repo.py` is what a person reaches
for and it is **one of seventeen steps**; nothing local invoked the palette
generator's check, so nothing local could have seen the failure. The new script
reads the step list out of `.github/workflows/ci.yml` — never a copy of it,
because a hand-maintained idea of "everything" is exactly what was wrong — and
refuses to run a subset if it cannot parse the workflow. Run second, it caught
a stale fixture set that would have been the next red build.

**The palette generator's build and its check disagreed about "everything".**
A bare `--check` recursed over every shipped registry; a bare write refreshed
only the default one, so the trade palette could be refreshed only by knowing
its three-argument incantation. Shared chrome landed in one file and not the
other. The write now covers what the check covers. The same edit also found
that the scoped instance redefined the light gold and not the dark one, which
looks correct only while the unscoped file happens to be included beside it.

**The brand lock did its job and was re-stamped with authorization.** The frozen
marks carry resolved literals, so they picked up neither the gold nor the
weights; the lock refused the regenerated files and forced the question to the
owner rather than letting the marks drift. Re-cut and re-locked with the reason
recorded in the lock file.

## 0.1.414 — the flash was never fixed: the guard shipped in Python and the runtime is JavaScript

0.1.411 found the flash, named the country, measured the polygon at 3.143e6
against a disc of 3.142e6, guarded it, checked it, and shipped a release note.
The reader saw **no change at all**, and was right to say so.

The guard went into `scripts/geo_projection.py`. The first frame of a globe comes
from there; **every frame after it is drawn by `assets/geo/projection.js`**,
which had no guard. So the emitter's sweep was green, the invariant held over
278 rings at 72 rotations, the release note was accurate about the emitter, and
the figure a reader watches went on flashing on exactly the same schedule.

**This is the second time a repair has reached one side of this hand-maintained
port.** 0.1.405 is the first, and it has its own paragraph in this file saying
precisely that. A paragraph is not a check.

Re-measured on the shipped demo: **eight jumps in eighty seconds, not one.**
`.gl-land` at 30.1s — the Venezuela case, unchanged by the fix — and `.gl-rg`,
the bloc fills, at 15.5s, 40.6s and 75.5s, a layer the first investigation never
watched because it went looking for the country it had already found. After the
port: **zero jumps in eighty seconds.**

The check now drives the RUNTIME through the tangency and measures what it
draws, rather than sweeping the emitter that was green through both failures.
Reverting the JavaScript guard reports it in those words: "the tangent guard is
in scripts/geo_projection.py and not in assets/geo/projection.js, so the emitter
is green and every frame a reader sees is not".

Also in this release, the cover and closing support line gets its own size.
`.sub` shared `--fs-support` with a content page's `.sup`, so it stayed at 17px
when the title came down from 80 to 58 and left the two voices closer together
than they were drawn to be.

## 0.1.413 — the cover mark is contained, not bled

The cover mark took the full height of its cell and ran past the right margin —
`height: 100%`, `max-width: none`, and a six per cent nudge outward — on the
reasoning that a mark grows better than it clips. Measured on a real cover: 602px
inside a 509px column, reaching the viewport edge while the footer rule stopped
90px short of it. A reader asked for half the page, centred, and was right.

It is now bounded by the cell it sits in and centred there, exactly filling its
column. Height-led is kept, because the route across the mark's top is still the
part that carries meaning; what is gone is the licence to grow past the frame.

**Worth recording: two earlier attempts to fix this failed for a reason that was
not visible from the markup.** `min-width: 0` on the item, then `minmax(0, …)`
on the track, then a `max-width` in the document's own stylesheet — all three
were correct and none applied, because a rule shipped in `tokens/` set
`max-width: none` at equal specificity and later in the file. The document was
never going to win that; the rule that said "bleed" had to stop saying it. Three
rounds of fixing the wrong end, and one query to the browser for which rules
actually matched the element ended it.

## 0.1.412 — a column starved to 34px, the standard order, and a green that clears its floors

**`starved_column` gates.** `.swap` renders on `grid-template-columns: 1fr 34px
1fr` and takes THREE children — a before, an arrow, an after. A deliverable
wrote it with two, so the second half landed in the 34px arrow track and wrapped
one word per line. Every gate passed. Its content was trimmed three times across
three rounds of review before anyone measured the box, which was 34px wide the
whole time.

The finding is a block holding a sentence in a column too narrow for it: four or
more words in under 60px, taller than it is wide. Not "narrow" — a chip and a
number legitimately are.

**A first version of this check tried to count children against grid columns and
was deleted the hour it was written**, because CSS grid flows extra children onto
the next row on purpose: `.gr` carries three children in a two-column grid and
renders correctly, so the check failed the reference fixture on its first run.
The property is real and it is not static. A starved column is measurable only
once rendered, which is why it lives in `inspect_layout.py` and not beside D19.

**The scaffold emits the standard order**, which is the default unless a request
says otherwise:

    cover · agenda · Part A opener · content… · Part B opener · content… · closing

The first version emitted cover, one opener, a run of pages and a closing. That
is not a deck, it is a deck's middle. `--parts A,B` is now two by default,
because one part is not a part.

**The cover and closing set at 58px**, not the part opener's 80. A shipped deck
measures 57.6px on both while its openers measure 80.6, and a reader asked for
the cover to match it: an opener is one line of claim on an empty page, while a
cover carries a title, a support line, an attribute strip and a mark, and 80
crowds them. New token, so the opener is untouched.

Their titles carry **two inks**: the claim in ink, the noun the deck is about in
the live green, so the green marks what the page is for rather than decorating
it.

**`--acc-live` #3E7A2E.** `--acc` is legible and reads brown at figure scale;
`--lime` is a surface and D13 correctly refuses it as a stroke on white at
1.21:1. The new green measures **5.21:1 on white and 3.23:1 on the dark ground**,
clearing the label and stroke floors in both palettes, with `--acc-tint` for the
table row wash. Measured, not chosen by eye.

**`.body.cover-grid` takes `minmax(0, …)` on both columns.** A bare `fr` track
keeps an implicit auto minimum, so a mark cell holding an SVG at its intrinsic
size stretched the track past its share — measured at 602px inside a 509px
column — and ran the composition off the page. `min-width: 0` on the item does
not reach the track, which is why it failed to fix this twice.

**`--preset cover` carries every layer.** Its first cut filled trade blocs and
nothing else — no marks, no cities, no lanes, no signals, no terminator — which
is a preset named for the cover that omitted four of the five things the cover
is made of. A reader spotted it in one look.

## 0.1.411 — Venezuela painted over the whole globe, once a minute

Reported as "the screen flashes about every minute". Measured over 70 seconds of
real frames: one layer, `.gl-land`, jumping 2,071 characters and back inside a
tenth of a second. Reproduced in the emitter at lon0 = 20.3, isolated to a
single country, and then measured properly — **Venezuela's clipped polygon
encloses 3.143e6 square units against a disc of 3.142e6.** It is not a flash. It
is Venezuela, drawn over the entire Earth, for six frames, once per revolution.

**The cause is the closure family's fourth appearance and its first without a
special shape.** The others were a hemisphere, a seam-crosser and a ring whose
longitudes were not unwrapped. This one is an ordinary small country that
happens to graze the limb: its single visible run enters and exits at almost the
same azimuth, and which way the closing arc goes between them is decided by
about 1e-12 of angle. Going the long way sweeps the whole cap.

So the repair is not another rule about direction. It is an assertion about the
OUTCOME: a clipped ring cannot enclose more of the sphere than the ring it came
from, plus the sliver a cap arc adds. Where it does, both closure directions are
tried and the smaller kept. Across all 278 rings at 72 rotations the honest
worst case is 0.0000 steradians of excess; a wrong-way closure is 6.28.

**A caller that vouched for its own handedness is exempt**, and finding that out
cost a round trip: the guard's premise is that `signed_area(ring)` bounds the
honest result, and `signed_area` is meaningless within a hair of a hemisphere —
which the day/night terminator exactly is. Applied there it read a false source
area, fired, and re-inverted the night side that 0.1.399 spent a release
correcting.

**The check took three attempts, and the first two are the lesson.**

The first rendered a revolution at 0.6-degree steps and compared adjacent
frames. That is a good description of what a reader sees and a bad test: the
defect occupies about two tenths of a degree, so the sweep stepped over it and
reported ok with the bug reinstated.

The second asserted the right property — the area invariant — but sampled lon0
every five degrees, and missed it for the same reason. A grid cannot find an
event narrower than its spacing, and nobody knows how narrow the next one is.

The third stopped sampling. The failure is not distributed over the rotation: it
happens when a ring GRAZES the limb, and that longitude is computable from the
ring. Each ring is now placed on its own limb and nudged across it in
twentieths of a degree. Reverting the repair fails it in the message above.

## 0.1.410 — the cover globe, and a preset so a document does not have to know four flags

`globe_svg.py --preset cover` is LUMIVATE's own view: Pacific-centred at
lon0=-160, the trade blocs filled, the terminator off. It exists so a document
does not have to carry four flag values to draw the mark, and so every document
that draws it draws the same one. An explicit flag still wins — a preset is a
starting point, not a lock.

`assets/brand/lumivate/` gains **`globe-cover.svg`** and
**`globe-cover.dark.svg`**, that view at cover scale, self-contained in each
palette. **Two files, not one that adapts**: `prefers-color-scheme` follows the
browser rather than the page a mark is dropped on, so a mark that adapts goes
dark on a light deck read in a dark-mode browser.

`assets/brand/README.md` documents the live recipe — the frame, the runtime, and
`data-globe-print-lon0` for a reproducible export — which is what makes the
rotating globe reachable from any agent with the skill installed: no demo
machinery, no build directory, two commands that already ship.

**D19 earned itself on the first document built after it landed.** The rebuilt
proposal referenced `#i-flow`, an icon this package has never had, and the gate
named it before a reader could. The same rebuild then hit the palette split for
the third time in this repository: `--rg-*` variables live in the SCOPED region
palette and the class-to-fill bindings in the UNSCOPED one, so inlining half of
them gave a globe with every variable defined and nothing bound to it — black,
and looking deliberate. The first two were the brand mark and the region map.

## 0.1.409 — D19: a document that cannot render itself does not ship

A deliverable passed `check_design`, `check_prose` and
`inspect_layout --deliverable`, and reached its reader with **no icons anywhere**,
a blank part opener, and a numbered block whose numbers had come away from their
content. Every rule it broke was already written down. Nothing stopped it.

**D19 gates**, beside D12, D14 and D15, and asserts three things a document can
be wrong about decidably:

- **every reference resolves here.** A `<use href="#x">` needs an `id="x"` in
  the same document. The failing deck carried **zero** of them: the icon sprite
  lives in the reference fixture's BODY, and a document assembled by slicing its
  `<head>` gets the whole stylesheet and none of the icons. Thirteen pages of
  handling terms lost their seal-red shield, and the page ground never drew.
  A `<use>` pointing at nothing is valid markup that renders as empty space;
- **every block carries its contract.** `tokens/` renders `.grades` through
  `.gr` and `.gn`, `.band` through `.k` and `.v`, `.swap` through `.no` and
  `.yes`. A class used without the children its rendering assumes silently
  borrows whatever styling it collides with — `.grades` picked up the `.key`
  callout's red outline and left every paragraph outside the box;
- **a part opener carries `class="page opener"`.** The lime opener is a class,
  not a layout. Without it the page renders blank, which is what a reader
  reported.

This is the deliverable-side mirror of `check_repo.py`'s `probe vocabulary`
guard, which says a class a CHECKER asserts must have a rendering in `tokens/`.
The same sentence turned around: a class a DOCUMENT uses must have the rendering
it is asking for, in the document that uses it.

**Two false starts are worth recording, because both would have made it
useless.** The first collected only `<symbol>` ids and so failed the reference
fixture on its first run — the page ground is a `<g id>`, and `<use>` may
reference any element; a gate whose opening move is to fail the fixture is a
gate nobody keeps. The second matched a block's body with a non-greedy
`(.*?)</\1>`, which stops at the first closing tag of that name and truncated a
`.swap` before its second half, reporting a missing `.yes` that was right there.
A gate that cries wolf teaches its reader to skip the line.

**`scripts/new_deck.py` is the positive half.** It emits a skeleton carrying the
complete preamble — token block *and* sprite *and* ground — a cover, a part
opener with its class, one of every block pattern with the markup that renders
it, and a closing. An author edits content into a structure that already works.
Its own preamble bug is instructive: taking the first `<svg>` after `<body>`
left `#g-ground` dangling, because the fixture opens with two hidden SVGs. A
preamble is whatever comes before the content, and guessing how many elements
that is was wrong twice in one hour.

## 0.1.408 — a dark palette that draws the sphere, not just the dark

0.1.407 got the dark palette into a document. It was reachable and it was not
finished, and the difference is worth naming: the chrome indirects to theme
tokens and those redefine under dark, which is true, and it was not sufficient.

`--gl-plate` resolves to `--ln3`, and on a #1D1D1F page `--ln3` sits so close to
the background that the ocean and the page became one black field. The globe
read as a scatter of continents floating on nothing — every value correct, the
figure gone. The comment in the generator said in as many words that the dark
chrome "needs no separate values"; it needed four.

Water on a dark page is not the absence of light, it is a surface with less of
it. The plate lifts just clear of the background and the graticule, the equator
and the tropics lift with it, because a sphere cue nobody can see is not a cue.

**Every deliverable now ships light and dark, from one build.** The two differ
by exactly the body's class and `data-theme`; every figure in them is
byte-identical, because a dark edition maintained separately is a dark edition
that drifts and the reader who compares the two is the one who finds out. The
`.dark.` in the filename is load-bearing: `inspect_layout.py` infers the palette
from it, so the dark edition is graded dark rather than graded twice as light.

The closing page loses its illustration. A closing that restates the cover's
image is a closing that has nothing of its own to say.

## 0.1.407 — the dark palette reaches a document at last, and the mark stops being a second design

**The dark palette had been unreachable since 0.1.333.** `build_fixtures.py`
inlined only the `:root` block from `tokens/lumi-theme.css`, so `body.dark`
never entered a deliverable — adding the class to a shipped document changed
nothing at all, because the values it redefines were not in the file. Nine
releases of a dark palette that no document could express. It is inlined now,
and the globe reads on black without a single new value: the chrome indirects to
theme tokens and the theme tokens redefine.

**The mark is the cover's globe, not a second drawing of it.** 0.1.405 shipped a
monochrome treatment on the reasoning that a logo has to print in one colour.
That reasoning is sound and the answer was still wrong: a company whose figure
and whose mark disagree has two marks. The monochrome styles are deleted
outright and the mark carries the cover's own look, resolved to literals and
inlined, with its own `prefers-color-scheme` dark variant — so one file is
correct on a white page and a black one and needs nothing from `tokens/`.

Building it turned up a defect the same shape as the mark's whole reason for
existing: the first cut read the SCOPED region palette only, and the chrome
variables — `--gl-plate`, `--gl-graticule`, `--gl-equator` — are emitted in the
UNSCOPED file, because a scoped instance is regions-only by design. Every one
resolved to nothing, `fill` became invalid, and an SVG with an invalid fill is a
black SVG. The whole ocean came out black in both palettes and looked
deliberate.

**A stray checkout poisoned every file-scanning guard.** `check_repo.py` walks
the filesystem rather than git's index, so a Claude Code worktree left at
`.claude/worktrees/` — a full copy of this repository at an older version — was
scanned as if it belonged to the tree. Seventeen failures across three guards,
every one of them true of a checkout nobody was editing. Gitignoring it was not
enough: a guard that reads the disk has to be told what the disk is for, so the
walker now skips dot-directories rather than `.git` alone.

**Figures 1 and 2 are kept as LUMIVATE brand images**, written beside the
document rather than into this package. The line is the one the HS codes and the
lane waypoints already fall on: those figures carry 128 tariff codes, 23 ports
and thirteen shipping routes, which are a deliverable's data. lumi-style ships
the component and its own mark; a figure built from a client's tariff list stays
out, and red line 9 is why.

## 0.1.406 — the land in three weights, and an export that is the same twice

**Continents read as continents.** Every land line was one weight, so a
coastline and a provincial border looked alike and the eye had nothing to group
by — on a figure whose stated job is comparing where one trade bloc sits against
another. The shared-arc topology `build_worldmap.py` already builds is the whole
mechanism and it needs no new data: an arc between two countries is stored once
and referenced by both, so its number of users says what it is.

    548 arcs used by one country  -> coast, 2.6px
    196 used by two, different blocs -> bloc edge, 2px
    570 used by two, same bloc    -> border, 0.8px

The fills lose their strokes; all linework moves to those three layers.
Classified in Python once and carried to the runtime in the markup, which is
the standing lesson of 0.1.404 and 0.1.405: those two releases were spent on
one repair applied to one side of a hand-maintained port.

**Oceania is back, and its absence was a regression I introduced.** 0.1.405 made
countries outside a bloc outline-only, and Papua New Guinea, Fiji, the Solomons,
Vanuatu and New Caledonia belong to no bloc — so an entire continent became
1.2px hairlines around small islands. A coast is a coast whether or not it is in
a bloc, so the same change that weights continents puts them back.

**One horizon.** `.gl-equator` was drawn in the graticule's own ink, so the
figure offered four candidate horizons at nearly equal weight. It gets its own
token now. That is `references/brand.md`'s waterline applied to a sphere: one
horizon where the light collects, and exactly one — the tropics stay dashed and
quiet because they are context for the tilt rather than a line to measure from.

**An export is the same twice.** `export_pdf.py` loaded the page and captured
whatever rotation the browser had reached, so two runs on one unchanged document
produced two different PDFs. The component gains `pin(lon0)`: it sets the view,
stops the clock, and — this is the half that took a second attempt — **resets the
signals to where the emitter put them**. The first version stopped the rotation
and left the signals wherever they had drifted, which gave a correctly pinned
longitude and a different picture every time. A pinned frame has to be
reproducible FROM THE MARKUP or it is not pinned.

Which view a document exports is the document's decision, carried as
`data-globe-print-lon0`. A `beforeprint` listener does the same, so Cmd-P in a
browser gives the frame the PDF gives.

**The deck is three pages and the cover is the globe.** The live figure moved
from an interior page to the cover, where `cover-grid` gives it a larger cell
than it had, and Figure 1's page is gone. It opens on the Pacific — the one view
where every lane is visible at once — and exports on Singapore. The legend went
with the page it stood on; what it did, the marks do through their own titles
and hover.

## 0.1.405 — LUMIVATE's mark, a lock with teeth, and the ring's last hiding place

**The brand directory.** `assets/brand/lumivate/` carries two globe marks,
generated by `scripts/build_brand.py` from the same projection and topology as
the figures — so the mark on a cover and the figure inside it are the same
object at two sizes, and cannot drift apart.

They are **self-contained and monochrome**. A figure's palette is built to
recede behind data, and a mark rendered in it disappears at 64px; a mark also
has to survive being dropped into a page that has never heard of `tokens/`, so
each carries its own styles inline in one ink at three strengths. A logo has to
work on a letterhead and in a favicon.

Two sizes, and the small one is not the large one shrunk. Dropping the LAND was
the obvious cut and it was the wrong one — it left a disc with a line through
it, which reads as a prohibition sign. Below 48px a 15-degree graticule falls
closer together than the pixels and turns to moire, while a coastline is a
silhouette, and a silhouette is what survives being small.

**The lock.** `assets/brand/LOCKED.json` holds a SHA-256 for the marks and for
the component that draws them, `LUMI-Globe-Field`. `check_repo.py` fails, and CI
blocks the merge, when a hash does not match without the same commit recording
the new one and a reason.

What a lock in source control can honestly promise is not that a file cannot be
edited — anyone with a checkout can edit anything — but that an edit cannot
arrive SILENTLY. It caught its own component file changing within an hour of
being written, which is the whole mechanism working.

**The ring's last hiding place.** 0.1.404 repaired the unwrap in the Python
emitter and left `projectRing` in `assets/globe/` untouched. The two are a
hand-maintained port; the golden grid holds the projection maths between them
and nothing held the clipping pipeline. So the first frame of every globe was
correct and every frame after it was not — a static check passed, a screenshot
of the loaded page passed, and the defect was visible to anyone who watched the
figure for two seconds.

A check written to guard it was **removed the same hour**: reverting the repair
left it green, because the routes it chose never reached a rotation where the
seam bit. A check that cannot fail is worse than no check, because it is also a
claim. What verified the repair was measuring the shipped demo over thirty
samples of real rotation — worst drawn-to-arc ratio 0.99 against a 1.15 ceiling
— and that is recorded as a measurement rather than a gate.

**A lane is now emitted even when it draws nothing.** A lane whose whole length
was on the far side of the first frame was skipped, so it never existed in the
document and never appeared however far the globe turned. That is the
drifting-dots defect wearing a different hat: the frame is a starting state, not
a filter.

**Two changes the owner asked for.** The axis line added in 0.1.404 came out one
release later — this figure already carries a graticule, an equator, two
tropics, a terminator edge, eight bloc borders and thirteen lanes, and a
fourteenth line through the middle of that reads as one more line rather than as
an axis. And a country in no trade bloc is now an outline rather than a fill:
on a figure whose subject is blocs, filling the rest of the world says the rest
of the world is a category, and it is not one — it is the absence of the eight.

## 0.1.404 — the ring came back, and a tilt nobody could see

**The ring, again, from a different place.** 0.1.403 unwrapped the longitudes
where a lane is BUILT. `split_at_seam` re-expresses them relative to lon0
afterwards, and returned a part spanning 376 degrees for seventeen degrees of
route — so `densify` swept the world filling the gap and the lane closed into a
ring, exactly as before, one stage further down the pipeline. Each part is now
re-unwrapped after the split, which is a no-op for every part that was already
continuous, and that is every coastline and every graticule line.

**The check that could not fail.** 0.1.403 claimed the fix was verified by
sweeping 24 rotations and measuring each lane's drawn width against the disc.
That measurement is incapable of failing: every path is clipped to the visible
cap, so its extent is bounded by the disc by construction. It reported "no ring"
about a figure full of them.

The property that works is LENGTH. A lane's projected length cannot exceed R
times its angular length, whatever produced a sweep and wherever in the pipeline
it happened. Under the old behaviour a Shanghai-to-Singapore lane drew 3.5 times
its own arc. That is now the assertion, over four routes and twenty-four
rotations each, and reverting the repair reports it in those terms.

**A tilt nobody could see.** Reported as "I do not feel the lean". Measured, the
tilt was correct all along: the pole sits 23.44 degrees off vertical, 389 units
right of centre at R=1000. The problem was that a sphere is rotationally
symmetric, so a rotated drawing of one has nothing to be rotated AGAINST — the
graticule turns with the geography and the result reads as a globe seen from
somewhere else.

A desk globe reads as tilted because you see the spindle against the stand. So
the figure now draws the rotation axis through both poles and out past the limb,
and a vertical reference through the centre, emitted outside the tilt group
because a vertical that tilted with everything else would be no reference at
all. The angle between them is the obliquity, and it is now a thing on the page
rather than a claim in a caption.

**Not a defect: the terminator.** Reported as wrong because Beijing and
Singapore fell on opposite sides of it while sharing a time zone. They do, and
they should. A time zone is a political convention — China runs one across sixty
degrees of longitude — while the terminator is astronomical and depends on
latitude at least as much as on the clock. At 06:00 on the June solstice the sun
is 12 degrees above the horizon in Beijing and 14.5 below it in Singapore, which
is why Beijing's midsummer sunrise is around 04:45 and Singapore's is near 07:00
every day of the year. The figure was right; the expectation it was measured
against was not.

## 0.1.403 — a lane that wrapped the world, and routes through the straits

**The bug.** Reported from a rendered globe: several lanes closed into rings
around the sphere as it turned. `great_circle` took its longitudes from atan2,
which returns (-180, 180], so a lane crossing the antimeridian stepped from
-178.6 to +176.1 — a jump of 355 degrees between two samples five degrees
apart. `densify` interpolates linearly in longitude and cannot know that, so it
filled the gap by sweeping the entire world. Every Pacific route did it.

This is the FOURTH time this exact failure has been introduced in this
repository, and the comment in `night_ring` already named the first three. The
check could not see it because it asked the right question about the wrong
thing: coplanarity holds perfectly for a ring whose samples are all on the
correct great circle and merely written in a representation that jumps. Lanes
are now checked for continuity in longitude as well, and reverting the unwrap
reports "jumps 358 degrees of longitude between adjacent samples".

**The routes.** A lane is no longer one great circle. `--links` takes `via`, a
list of waypoints, and the lane becomes a sequence of legs — each still the
shortest path, so the geometry stays honest at the scale it is claimed at, but
the claim is now a shipping lane rather than a line on a sphere. Shanghai to
Rotterdam goes Luzon, Malacca, Bab-el-Mandeb, Suez, Gibraltar; Rotterdam to Los
Angeles goes through Panama, which without it drew straight across Mexico.

The unwrap carries across the leg joints, and the joint point is dropped once,
so a five-leg route is one continuous ring rather than five that happen to
touch. Both are checked: a route that reintroduced the seam at a joint, and a
route that repeated its waypoint, each fail with their own message.

WHICH straits a lane uses is editorial — a claim about shipping rather than
about geometry — so the waypoints are supplied by the document. This package
ships the route maths and no routes.

## 0.1.402 — trade lanes on the sphere, and a signal that carries a real code

The globe takes `--links` and `--codes`. A lane is drawn as the GREAT CIRCLE
between its two ends, which is the shortest path across a sphere — so the
drawing and the claim are one object rather than a picture of one — and because
a lane is just a ring it goes through `_project_ring` and gets limb clipping,
seam splitting and far-side culling without a line of new code. A lane on the
back of the Earth is not drawn because there is nothing there to draw.

Weight is encoded twice, in width and in opacity, and that is deliberate rather
than redundant: the light lanes have to survive being light, and both channels
have a floor because a lane nobody can see is a lane that should not have been
in the data.

**A signal carries a real datum or it does not ship.** `references/brand.md` is
unambiguous — "a shimmer with no data under it is decoration, and decoration is
contention" — so the signal layer emits nothing at all without codes to carry,
and the check says so in those words when the guard is removed. Signals are
EMITTED, not created by the runtime: the same rule marks obey, which also means
a document with JavaScript off shows lanes carrying codes rather than lanes
carrying nothing.

They move on the same clock and under the same gates as the rotation, so
`prefers-reduced-motion` stops them where they are — leaving a legible diagram
instead of an empty one — and the off-screen gate stops them with everything
else.

**What the check had to learn.** The first version asserted that every sample of
a great circle lies on the unit sphere. That is vacuous: every (lon, lat) pair is
on the sphere by construction, so replacing the interpolation with a straight
line in lon/lat — a rhumb line, and not the shortest path at all — passed it. The
real property is that a great circle is the intersection of the sphere with a
PLANE THROUGH ITS CENTRE, and the check now measures the distance from that
plane. The rhumb line misses by 0.87 of a radius.

Three treatments of this layer were prototyped and compared before one was
chosen; the other two are not in this package and never were.

## 0.1.401 — the globe leans right, names its cities, and colours its blocs

Four additions to the globe, and one of them turned up a defect in a kind of
reasoning rather than in a line.

**The pole leans right.** `rotate(-tilt)` carried it left; SVG rotates clockwise
on a positive angle. Which way it leans is a free choice — obliquity is an angle
between an axis and a normal and has no handedness a viewer can see — and it had
shipped leaning one way since 0.1.397 **with nothing asserting it at all**. The
tilt now has a check: the group exists, the angle is the obliquity rather than
the 23.5 everyone quotes, and the sign leans right. Both mistakes fail it.

**Blocs on the sphere.** With `--regions`, the land is routed into one path per
region instead of one path for the world — the same total clipping work, because
a ring is clipped once either way and only the bucket changes. The paths carry
the SHIPPED `rg rg-<id>` classes, so one palette serves the globe and the flat
map and the two cannot disagree about what colour a bloc is. Without `--regions`
nothing changes: a field of marks should not silently gain political fills.

At full strength the eight hues buried the data — Australia read hotter than the
mark on top of it — so `.gl-rg` takes the same hue at 42% and the marks stay the
only saturated thing on the figure.

**Cities, named.** A `--cities` layer that carries visible text, which marks
never have. Text on a sphere needs three things a circle does not: the far-side
rule applied to dot and name together, a side flip so a label near the right limb
runs inward rather than off the edge, and collision culling. Labels are placed
outward from the view centre and one that would land on another is DROPPED, never
nudged — dropping is what keeps the static frame and the live frame agreeing.

**Bloc labels** carry abbreviation, membership and population magnitude —
`AFTA 10 · 0.69B` — and are hidden well before the limb, where the geography
under them is a sliver. Population is a new registry field beside `count`, since
a consumer holding the members should not go elsewhere to say how many people
they are. ASEAN's entry is 690M, not the 530M the founding-era text quotes; both
are right about their own year and a label drawn today has to be right about
this one.

**Two lessons, both about checks that agree with themselves.**

The label placement first compared boxes computed from the same constants it was
verifying. Setting the padding to zero left it green while three European names
rendered as one blot. Overlap is now measured in a browser off the RENDERED
glyphs, and it caught the real defect immediately: the estimate 0.55 em/char was
the MEAN of the shipped face, not an over-estimate of it, and real names run 0.48
to 0.62.

Then the deeper one. Placement was being decided in the earth group's own space
while the labels render TILTED — positions rotate, label boxes stay axis-aligned
to the screen, and at the obliquity a point 700 units above centre moves 280
sideways. The crowded corner of the frame is not the crowded corner of the
picture. Placement now converts to screen space first, and the dot-to-name gap is
stated on screen and converted back, because a plain offset in group space came
out at 23 degrees.

## 0.1.400 — the gate measured ink the viewport never painted

`inspect_layout.py --deliverable` called a correct document NOT SHIPPABLE on two
of its ten gating findings, and both were the same measurement error.

`inkBox` measures an SVG by `getBBox()`, which is the union of the children **in
user space** and knows nothing about the viewport. An SVG with a viewBox clips at
its own edges, so geometry outside it is not painted. The globe's plate carries a
drop-shadow, and a filter region inflates that bbox by a tenth of the viewBox in
every direction — about 50 CSS px at a figure's size. That phantom band collided
with the paragraph above the figure and spilled past the footer below it. Nothing
was out of place on the page; the ruler was longer than the thing it measured.

The box is now the intersection of the bbox with the element's own rect, which is
what a viewport paints. A correct figure pays nothing, because its ink is inside
its box already. Guarded by a planted case in `check_globe.py`'s shared suite,
written as the general property rather than the particular bug: a circle drawn far
larger than the viewBox that frames it. A filter region is one way geometry lands
outside a viewport and an oversized shape is another, and one clamp answers both.

The check also asserts its own case still overflows, so a browser that changes how
`getBBox` treats a filter cannot quietly turn this into a check of nothing.

## 0.1.399 — half of every day was inverted, and a check that swept one axis of a two-axis geometry

Two defects in the day/night terminator, both found by building a deliverable
and looking at it, and neither visible to a check that had reported 0.08% error
nine views running.

**The antipode.** The night side is a cap about the sun's antipode, and the
antipode was computed by a two-branch expression: subtract 180 when the sun is
east, reduce mod 360 when it is west. The western branch returns the sun's OWN
longitude. So for every subsolar point in the western hemisphere — half of every
day — the cap was drawn around the sun and the figure shaded its daylight. One
normalisation replaces both branches.

**The handedness.** `signed_area`'s docstring has said since 0.1.389 that its
sign is meaningless within a hair of a hemisphere, and the terminator is exactly
a hemisphere. Its sign there tracks which pole the cap happens to enclose, so
every cap centred north of the equator was classified backwards on top of the
first defect. `clip_to_cap` now takes an optional handedness, and a ring built
by `cap_point` — whose interior is on the right by construction — passes it.
Country rings, far below the ceiling, still ask as before. Mirrored in
`assets/geo/projection.js`.

**Why the check missed both.** `check_terminator_area` moved the view centre
across nine positions and held the sun at one eastern longitude on one date. The
geometry has two inputs and it swept one. It now sweeps a full day of hours and
both solstices plus an equinox, and each defect fails it on its own: reverting
the antipode reports "night should cover 90.5% of the disc and it covers 2.5%",
reverting the handedness reports "9.9% … and it covers 90.1%".

Also in this release, from the same build-and-look:

- **A globe stating a field no longer draws the registry's place layer.** Those
  four city-states exist because no shape can be filled for them, which is their
  whole job on the flat map; on a globe carrying marks they are a second point
  vocabulary at nearly the same radius. The first demo drew Singapore twice —
  once as a datum of weight 9, once as a place — and no reader could tell which
  circle was the number. Scenery still names places; a field asks with `--nodes`.
- `MARK_R_MIN` rises from 0.008R to 0.011R. Legibility only, and deliberately
  not asserted: the justification that suggested itself — a pointer target — is
  false, because `pick.js` hits on a fixed 12 CSS px radius whatever the mark is
  drawn at. Recorded in the check so the next reader does not add it.
- The trade registry names the five members nothing in the package could name.
  A panel is the intended consumer of a bloc's membership, and one that could
  name 50 of AfCFTA's 55 would print a list shorter than the count above it —
  the 0.1.398 count defect one layer down. Now graded.

## 0.1.398 — trade blocs on a map that cannot fill them, and the count that is a fact about the bloc

A second registry, `assets/vectors/regions-trade.json`, generated by
`scripts/build_trade_registry.py` from eight trade blocs. It does not replace
the geographic `regions.json`, which stays the shipped default: the blocs cover
part of the world and `check_region_coverage` wants every country in exactly one
region. The per-instance registry machinery of 0.1.395 exists for this.

**The blocs overlap, and a fill cannot.** Canada is in USMCA and in CPTPP;
ASEAN's ten sit inside RCEP's fifteen. So each record carries two lists. The
`members` list is a base PARTITION, derived here and never typed, under a rule
stated in the registry itself — smallest containing bloc wins, which is the most
specific true statement about a country, and whose eight sizes are distinct so
the rule is total. The `full` list is the real membership. The frame draws both:
disjoint fills from `members`, and one stroke-only overlay per bloc from `full`,
`display:none` until a reader selects it. Selecting CPTPP outlines all twelve
across four different fills. That is the whole product point of a bloc map, and
no amount of translucent stacking gets there without spending every contrast
floor the palette clears.

**A count is a fact about the bloc, not about the geometry.** Eight members have
no shape at this resolution — Malta, Singapore, Bahrain and five African island
states. The label says 27 for the EU while 26 shapes fill, because a count taken
from what happened to draw is a smaller and different claim than the one the
reader is owed. Now a graded invariant: the check reads the printed number back
out of the frame and compares it against the membership, and reverting it
reports "eu: the label says 26 and the bloc has 27 members".

Also in this release, each found by looking at the rendered map rather than at a
passing check:

- **`.rg-label-n` and `.rg-label-v` had classes and no rules** since labels
  shipped, so a value and a membership count set identically to the bloc name
  beside them. The same class-with-no-rendering defect 0.1.396 found on the
  globe's hover state, one file away.
- **A label at the frame edge was half-drawn.** Mercosur's name is centred on an
  anchor near the right edge, and the half outside the viewBox is simply not
  painted. Labels now clamp into the frame on an estimated width — an
  over-estimate, because the cost of over-estimating is a label a few units off
  its anchor and the cost of under-estimating is a truncated name.
- **Two anchors sat under their own point nodes**, putting a white disc through
  the middle of "AFTA" and "GCC".
- The equator and the tropics, added to the globe in 0.1.397, are now on the
  flat map too, at the same 23.44 the globe tilts by. One world, one set of
  named latitudes.
- A registry that ships now ships its palette: `tokens/region-palette-trade.css`,
  scoped under `.trade`, all four floors cleared in both themes. A bare
  `build_region_palette.py --check` walks every shipped instance, so registering
  a registry in CI is one row in a table.

## 0.1.397 — the globe becomes an Earth, and two lenses of daylight inside the night

The globe carries an axial tilt, the tropics, the equator and a day/night
terminator. **The tilt and the flattening are one SVG group transform, not a
change to the projection** — and that is a decision, not a shortcut. Touching
`unrolled()` would invalidate the 1300-sample golden grid that holds the
JavaScript port to the Python authority, and what it would buy is sub-pixel:
WGS84 flattening is 1/298, so at R=1000 the two axes differ by 3.4 units in a
2000-unit frame, and the geodetic-versus-geocentric latitude difference peaks
at 0.19 degrees. **The flattening is invisible and the owner was told so.** What
makes the figure read as a sphere is the tilt, a graticule at 15 degrees
instead of 30, and the two tropics — which sit at exactly the obliquity the
tilt uses, so one constant serves all three.

**The terminator is the same shape the clip already speaks**: night is a
spherical cap about the antisolar point, so it goes through `_project_area`
like any country and comes back cut at the limb. The sun is fixed in screen
space (owner decision) — the Earth turns under it — which has a consequence
worth stating: the night polygon's projected shape is then INVARIANT under
rotation, so the runtime never redraws it and needs no solar maths at all.

**And it drew two lenses of daylight inside the night side.** Both were
well-formed polygons, both invisible to every markup reader, and both found by
measuring rendered pixels against closed form — a great circle whose pole sits
at angular distance d from the view centre cuts the disc into a night part of
exactly (1 − cos d)/2:

- The terminator ring is a **hemisphere**, the one radius at which
  `signed_area`'s branch flips — 0.1.389 measured it and wrote it down — and
  facing the antisolar point the ring lay exactly ON the limb, leaving the clip
  to decide the winding of a curve coincident with the boundary it was being
  clipped against. It is drawn 0.05 degrees inside now: 5.5 km on the ground,
  an order of magnitude finer than the quarter-degree the solar position itself
  is good to. The terminator is drawn inside its own error bar and the
  degenerate case stops existing.
- `cap_point` returns **unwrapped longitudes**, so the ring stepped through a
  355-degree discontinuity once per circuit and `densify` interpolated straight
  through it, sweeping the whole world into a second lens. This is the third
  time `densify` has been handed a ring whose longitude representation jumps
  with nothing to tell it so.

Worst error over nine views: **13.5% before, 0.08% after**, and the new check
asserts it against the closed form by counting pixels with a ceiling of 0.5%.

**The named circles rotate.** `.gl-equator` and `.gl-tropic` were emitted and
then left out of the runtime's redraw, which would have pinned them to the
frame they were generated in while the world turned underneath.

**Read against a reference.** brila.ai's globe was opened in a browser and
measured: three.js over WebGL2, `cursor: grab`, and a drop-shadow under the
sphere. Three of its four ideas cost nothing here — a denser graticule, a
shadow so the globe floats instead of sitting printed on the page, and the grab
cursor, since this component's arcball has worked since it shipped and nothing
ever said so.

## 0.1.396 — the dots that drifted, and the audit that did not find them

**A reader found it; no check could have.** Dots drifted across the rotating
globe in the delivered demo. The cause: **the HTML `hidden` attribute does not
hide an SVG shape.** A `<circle hidden>` computes `display: inline` and keeps
its full bounding box, so every mark and node on the BACK of the sphere kept
drawing — at its orthographic position, which for a far-side point lands INSIDE
the visible disc. Measured on the shipped demo: twelve points moving every
frame, two of them `hidden` throughout while travelling straight across the
visible face.

This is the fifth time one pattern has produced a defect here, and it is worth
naming plainly: **every gate in this package reads markup, and `hidden` reads
correct in markup.** The comment at `globe_svg.py:107` asserted "`hidden` is
honoured" — a sentence that was never true. The fix is `display="none"`, a real
SVG presentation attribute that needs no stylesheet, so the JavaScript-off
frame hides them too. The new check measures `getBoundingClientRect().width` in
a browser and refuses to believe an attribute; reverted, it reports a far-side
mark "still renders 34x34px".

**The audit the owner asked for, against all three specs.** It found the split
shipped well and left six promises unkept, each now closed:

- **`--suite globe` contained zero checks.** The flag shipped in 0.1.394 and its
  contents did not, so the split spec's headline verification promise — field
  frame sanity and renderer parity — had no code behind it.
- **`.is-hover` regressed onto the globe.** Closed for regions in 0.1.391,
  reopened in 0.1.394: the runtime toggled the class on marks and nodes against
  no rule at all. Globe hover worked and showed nothing — the same defect,
  moved rather than eliminated.
- **The event vocabulary was wrong.** A mark click announced itself as
  `nodeselect`, the runtime's own header advertised a `markselect` emitted
  nowhere, and hover used a pair no spec names. A datum and a place are not
  interchangeable to a host that wants to open a panel about one of them.
- **The theme re-read was deleted with the form machinery**, leaving a canvas
  globe holding the light palette through a theme flip and a `readPalette()`
  with no caller.
- **The watchdog could not fire** outside the autorotate branch, so a dragged or
  reduced-motion globe could miss the frame budget forever without pinning; and
  `visibilitychange` resumed a globe that was scrolled out of view.
- **`lon0` accumulated without bound.** An hour of rotation reached five figures
  of degrees, spending precision on a number whose only meaningful part is the
  remainder.

**Dead weight removed from every globe deliverable**: the region layer
`globe_svg.py` has not emitted since the split, `ringsOfRegion`, and the
per-region bounding-box index — which walked every arc of every member on every
boot to build a Map whose only consumer, the hit-test prefilter, died with
`pickRegion`.

**A scoped map announced regions it was not drawing.** `embed_regionmap.py`
boots every figure from one registry, so an Asia-only map built a hidden button
per region of the *shipped* eleven — the same defect the split closed for the
globe. Registries are per-element now, which also exercises the per-element
states path that had shipped untested.

**Six phantom options are corrected in the spec rather than built**
(`class="mk"`, `--gl-mark-r-min/-max`, `data-globe-marks`, three
`createRegionMap` options, host-supplied node values): in each case the shipped
choice is the better one and the spec was simply wrong. `specs/2026-08-10-globe-map-split-design.md` §8
carries the audit, the corrections, and three findings recorded as still open.

## 0.1.395 — the registry stops being a singleton

Release 5 of 5 for the component split, and the one that delivers the owner's
"different regions and colours, different scenarios" in full.

**`build_region_palette.py --regions <path> --out <path> --prefix <cls>`.** A
custom registry gets the same six floors the shipped one gets — the floors are
the contract, not the registry — and a scoped palette: variables and class
joins under the instance's ancestor class, no second copy of the global chrome.
Two maps with different registries coexist on one page, each resolving its own
hues. `--out` is mandatory with `--regions`, because a custom palette must
never overwrite the tokens file the default registry's documents include; and
after writing, the floors are asserted against the registry that was just
written, not the shipped one — asserting the default's floors there would
bless a custom registry that clears nothing.

**Validation before colour.** No double-claimed member (the hue assignment
would be ambiguous), no member missing from the topology (a silent no-draw),
no node naming an absent region. Full topology coverage is OPT-IN
(`--require-full-coverage`): a scoped map — Asia alone — legitimately covers
less than the world, which is why `check_repo`'s coverage guard keeps
guarding the shipped singleton and only that.

**A scoped map fits its regions.** The first cut rendered Asia as a sliver
inside a world-wide viewBox — an ocean of empty graticule on either side,
exactly the reserved-space-nothing-draws-in defect the frame-fill floor
exists to catch. The map's viewBox now fits the ink; the graticule is emitted
last and clipped to it; nodes outside it are skipped. For the shipped
registry the ink box and the world are the same box, minus the empty polar
band above the northernmost coastline, which is an improvement nobody will
mourn.

`--regions` rides through `regionmap_svg.py`, `embed_regionmap.py` and
`geo_frame._load`, with the topology staying shipped throughout: regions group
countries, they do not redraw them. The globe stays on the default registry —
its subject is marks, not groupings.

## 0.1.394 — the globe becomes the field it always claimed to be, and the unroll retires

Release 4 of 5 for the component split. The globe is now one thing: a rotating
sphere carrying a field of marks. `setForm`, `unroll`, `setT`, `--form`, the
`form-*` class toggles and the `formchange`/`unrollstart`/`unrollend` events are
deleted rather than deprecated — a half-retired flag is a standing stale
promise — and `t` is pinned to 0 in the component while the shared projection
core keeps the parameter and every check that sweeps it.

**The field finally has a data path.** It never did: `hostData.marks` was
documented and read by nothing, the emitter's `marks=` parameter had no CLI
flag, and the one delivered demo showed a "field" with zero marks. The
contract is `[{lon, lat, weight, label?, id?}]`; radius scales with the square
root of the normalised weight — area encodes quantity — between a floor and a
ceiling as fractions of R. The radius rule lives in the two renderers and is
parity-held, not in tokens: CSS cannot size a canvas mark, and a knob that
binds one back end is a divergence wearing a token's clothes.

**The canvas back end draws the field and only the field.** Its regions branch
read a `state.form` the public component never set, so it actually keyed on
`view.t > 0.5` — dead divergent code the parity suite could not see, because
the canvas was never in the parity bundle. Deleted with the form. It draws
marks now, from data, with the emitter's exact radius rule.

**Renderer parity moved to the field, and covers more than it did.** The old
check compared the eleven region paths; the land path it compares now runs
every ring in the topology through the shared clip — a superset of the same
rings grouped differently — plus the three sample marks' positions. The region
side has nothing left to diverge: its runtime never touches geometry.

**The a11y layer speaks the figure it decorates.** One visually-hidden entry
per mark (name and weight — a datum is read, not operated), one button per
registry node (a place is selected). The region buttons left for the map
component in 0.1.393; the field figure that announced eleven regions it was
not showing is gone. `pickRegion` and its even-odd crossing test retired from
`pick.js` with no caller left — 30 lines of dead code in every deliverable is
not a keepsake.

`check_globe.py` gains `--suite shared|globe|map`. The t∈(0,1) sweeps sit in
`shared`, because they are the 0.1.389 winding guard and outlive the pinned
products; CI's `--python-only` invocation is unchanged.

## 0.1.393 — the region map becomes its own instrument

Release 3 of 5 for the component split. `assets/regionmap/` and its emitter
`scripts/regionmap_svg.py` are new code beside the untouched globe — the
sequencing constraint from the spec, so no commit exists in which the
repository can draw no region map.

**The map runtime touches no geometry, and everything follows from that.** A
flat map does not rotate, unroll or animate, so the frame the emitter bakes is
complete and what remains for a runtime is state: classes, values, labels,
hover, focus, the accessibility layer. Creation is synchronous; hit testing is
the browser's own pointer events on real path elements rather than an inverse
projection; and the embed block inlines the registry and NOT the 68 KB world
topology the globe must carry to re-project every frame — 11 KB against the
globe's 122. The planned render-map.js does not exist because there is nothing
for it to render; one module is what the design turned out to need.

**The registry's `anchor` and `z` are finally read.** Declared since the
registry existed, consumed by nothing: the emitter now places each region's
label at its anchor, in English from `n` or Chinese from `z` (set in the
default stack per 0.1.391's type decision), with the value beside it when the
data carries one. Each label carries `data-region-label`, the vocabulary D18
counts, so a document using this frame satisfies the label rule without
hand-authoring a legend. Label size is an attribute scaled to the frame's R —
a fixed CSS pixel size inside a 2000-unit viewBox rendered at seven effective
pixels, which is why the tokens rule now carries family and weight only.

**Two of the audit's defects die here by design.** The aria vocabulary is name
with VALUE ("Europe, 63") where a value exists — the globe's frame said
"Europe, live" while the page showed the number — and the renderer keeps it
current on setData, where the old one wrote it once and let it lie. The
one-button-per-region accessibility layer lives in this component and will
leave the globe in the next release, ending the field figure that announced
eleven regions it was not showing.

**A trap found by the component's own first test page.** The runtime applied
its host data unconditionally, so embedding without data "corrected" a frame
with baked states to all-zero within minutes of the module existing. Initial
state now comes from the markup — the classes and aria values the emitter
wrote — and host data overrides it. No data given is not data.

`check_globe.py` gains the map frame's contract: ink inside the declared
viewBox, every drawn region labelled, every emitted class bound in
`tokens/region-palette.css` (a black map is now a checked failure, not a
surprise), and the aria vocabulary — each mutation-tested.

## 0.1.392 — the shared geometry core gets its own directory, and nothing else moves

Release 2 of 5 for the component split. `assets/geo/` now holds the one library
both components stand on — `projection.js`, `worlddata.js`, `pick.js` — and
`assets/globe/` keeps what is the globe's own. `scripts/geo_frame.py` is the
Python side of the same cut: the frame assembly both static emitters will share
(load, ring decode, the clip-split-project order 0.1.389 established, the pole
close, the guard, the rounding rule, the extent), extracted from `globe_svg.py`
unchanged.

The whole release is a re-layout, and the proof is the point: the emitted SVG
is byte-identical across three reference views (both forms, three values of t),
the 1300-sample golden grid is untouched, and the full browser suite — port
parity and renderer parity included — runs green on the moved tree. A re-layout
that cannot demonstrate byte-identity is a rewrite wearing its clothes.

## 0.1.391 — the split is decided, the palette becomes usable, and Chinese type gets its honest answer

**The one-figure-two-forms decision is reversed** (owner directive, 2026-08-10 —
the documented case is the audit of the first delivered demo, recorded in
`specs/2026-08-10-globe-map-split-design.md`). The globe and the region map
become two components, separately designed, developed and verified, each
configurable per instance. The audit found the coupling was where every defect
lived: one of the two forms never had a data path at all (`hostData.marks`
documented, read by nothing), `setForm` toggled classes no stylesheet defines,
the canvas back end branched on a state the runtime never set, and the unroll —
the feature the coupling exists to serve — was unreachable, because nothing in
the package emits a control and the first real deliverable authored none. The
split lands over four further releases; this one ships the spec and the two
decisions that are independently useful today.

**`tokens/region-palette.css` ships the bindings, not only the values.** The
variables shipped for three releases with no rule joining them to the classes
the emitters write, so any document that did not hand-copy ~90 rules drew every
region in the UA default — black — and every metric passed, because no check
reads rendered colour. The generator now emits, beside the hues: the `.rg-<id>`
fill and stroke bindings, the state classes (`.is-out` and `.is-partial` take
the standing status colours deliberately — they are status, not identity),
`.is-hover` (toggled by the runtime since the globe shipped, defined by nothing,
so hovering worked and showed nothing), `:focus-visible` (the first demo shipped
`outline:none` on a `tabindex="0"` element), and the `--gl-*`/`.gl-*` figure
chrome the canvas back end has read since it was written and no host ever
defined. The fixture's private copy of the join is deleted — a reference
implementation should not need a private companion to render. `.is-live` is the
unmarked state, and the file says so rather than shipping a rule that restates
the binding above it.

**Chinese deliverables use the default stack** (owner decision). No CJK face is
vendored and none will be: a comparable-quality face is one to two orders of
magnitude larger than the Latin pair. The embed rule is scoped to the faces the
package ships, and the design rules now state the fallback chain and its cost —
CJK rendering depends on the reader's machine — instead of keeping a sentence
that could not be kept for half the documents this package exists to produce.
This also unblocks the rendered Chinese fixture that item 2 filed under a
licence question; building it is its own change.

## 0.1.390 — the backlog, and the instruments that could not fail

The seven items in the tracked ideas backlog, in the order it set. What they had
in common turned out to be sharper than the backlog knew: **five of the seven
were not missing features but missing verification**, and three of them were
guards that had been written, documented, and never wired.

**Item 3 · A suite that could not tell a working checker from `return "ok"`.**
Thirteen of eighteen design verdicts and four of seven prose verdicts read `ok`
on BOTH fixtures. Ten of them could not be given a failing case in
`deck-broken` without destroying it as a worked example — four are document-WIDE
prose properties (every sentence the same length, every title the same shape)
that cannot be confined to one labelled page — so `deck-degenerate` is a third
fixture whose only job is to fail. Coverage is now **computed**: the checkers
emit their targets, and `check_fixtures.py` refuses a graded verdict no fixture
fails. 30 of 30 today, against 8 of 18 before.

Three defects in the checkers, all found by using them. `KNOWN_FLAT_CLOSURES`
documented a two-way lock whose second half **was never implemented** — the
pairs seen were collected into a variable nothing read. The flat-segment probe's
loop sat OUTSIDE the per-path loop and examined one path per frame of twelve. And
`inspect_layout --json` printed a note to **stdout ahead of the JSON**, so any
deliverable that declares no `data-geometry` emitted a stream no parser could
read — which the conformance harness had been recording as "layout emitted no
parseable report", a defect in the deliverable rather than in us.

**Item 5 · Two viewports the rules name and nothing ran.** `laptop` and
`16x9-hd` were absent from the default list, and widening that list would still
not have reached a deliverable: the declared-geometry branch narrowed to two
geometries, which is where they were actually being lost. Running them found
`footer_wrap` firing on all 18 pages of the PASSING fixture at 1920×1080 — the
probe compared a rect in **device space** against `parseFloat(lineHeight) || 14`,
and `line-height: normal` does not parse, so a good footer measured 22.5 against
a threshold of 22.4. It counts line boxes now, and `deck-degenerate` carries a
real two-line footer so the fix is proven to still fire.

**Item 1 · M6, M2, M1 — the three metrics standing behind a fact red line.**
Half the rubric's prose metrics had no code and three of the six stood behind
"every number carries its source", so a deliverable could break all three and
pass every check shipped. The window each one measures in is now stated in
`writing-rules.md` §4 rule 6 — the page for an ordinary figure, the block for a
range, because a range must trace to a SINGLE source — and a new `source-marker
parity` guard holds the script's vocabulary to the rules'. The window was
settled by measurement, not preference: a block window scores a correctly built
deck at 0%. **M1 reports and never gates.** Its predicate is a proxy for a
judgement, and a proxy that gates is one authors write toward; the first cut
scored a well-formed deck at 18.8% because it read only digits, which is exactly
the line a reviewer learns to skip.

**Item 2 · The Chinese half had rules across four sections and machinery for
none of them.** Phase 1, the parity guard, went first because it is a guard
rather than a feature: it closes the drift channel before there is new code to
drift. Phase 2 gives Chinese documents the banned-phrase list and the
punctuation pass. A Chinese document used to come back UNMEASURABLE, and that
was the real reason this checker was English-only underneath the docstring
saying so — the word splitter needs spaces. Phase 3 was filed as blocked on a
font licence because a fixture has to render; that is true of the RENDERED half
only, and `check_prose.py` renders nothing, so a Chinese prose fixture pair
ships now and the licence question is unchanged for anything a browser must
open. M3, M7 and the de-translationese pass are recorded as **not mechanized**
with reasons: the first two need a per-document term registry this package does
not ship, and inventing one would be a rule nobody wrote.

**Item 4 · The half that iterates had no memory.** Six dimensions, a protocol
where a divergence of two forces a retrospective, and not one stored score —
every number lived as a sentence in a release note. `reviews/scores.json` and
`scripts/review_scores.py` store and print the series, backfilled from the two
rounds the changelog records as prose. The schema has **no free-text field**,
which is the engagement-fact defence rather than an omission, so an unknown key
is an error. The protocol's own rule against self-scoring 5 before a reader has
is enforced in the tooling, because a number series invites optimising it.

**Item 6 · The capability tier was the one registry claim nothing verified.**
Install path, docs URL and CLI probe each carry a verification field and a waiver
when unverified. `capability` had none — and it is the claim that decides whether
an agent may call a deliverable *verified*. Running every probe on this machine:
one of twelve is installed. So `capability_verified` is true for `claude-code`
alone, eleven waivers name what is unconfirmed, and each is **published in the
install note** rather than kept in the registry. The `files` tier stays, marked
unpopulated: it describes a real shape, and the way to fill it is to exercise an
agent, never to reclassify one from reading its documentation.

**Item 7 · A board reporting one sample as though that were the method.** An
unreferenced results directory sat on disk — a second Claude Code run nobody had
scored, which is the repeat the board most needed. `scored.update()` made a
repeat OVERWRITE its predecessor, so "n=1 per agent" was a property of that one
line and not of the harness. Repeats accumulate now and a cell carries its
spread: `2 runs, all fail` is a different claim from `2 runs UNSTABLE`. And
absence has two kinds — six rows are a machine away, four can never answer a CLI
probe at all, and printing them identically made ten pieces of pending work out
of six.

**And an eighth thing, found by looking at the sheet.** With the geometry matrix
widened, the contact sheet showed figure 9 of the PASSING fixture as four solid
black rectangles — at every geometry, for as long as that figure has existed.
`globe_svg.py` emits `class="rg rg-europe is-live"`, `region-palette.css` ships
`--rg-europe` and its stroke and wash, and **nothing in `tokens/` joins the
two**, so every region fell back to the UA default. `D18_region_labels`,
`D5_drawn_share` and `D5_figure_parity` all passed, because no check in this
package reads rendered colour. Convention 8, again, and the third release
running that it found something the instruments could not.

The fixture paints its regions now, generated from the palette so a new region
cannot leave a black shape. **Whether `tokens/` should ship that binding itself
is left open**: `design-rules.md` §1 puts painting on the document, but a
document currently has to write eleven regions by hand to draw a region map, and
that is the shape of a rule mandating an asset the package does not ship. It is
a design decision, so it is recorded here rather than taken.

Three things the backlog proposed and this release did not do, all recorded
rather than dropped: a Chinese fixture anything must RENDER still waits on a
font licence; one mutation of the spherical clip — a run linking to its own
entry instead of the next run's — produces a result too small to trip the area
invariant and nothing catches it; and `M1`'s proxy scores a well-formed deck at
43.8%, which is information about the proxy as much as the deck and is why it
reports rather than gates.

## 0.1.389 — winding carried through the clip, and the two defects the eye found after the checks went green

**The clip moved to the sphere, which is the whole change.** 0.1.388 recorded
three flat closures and one renderer divergence under one diagnosis: the limb
walk picks the arc that is shorter BY INDEX, and the correct arc is the one that
keeps the polygon's interior on the correct side. That diagnosis was right and
incomplete, and implementing only what it names makes the figure worse — a
prototype of exactly that took the flat closures from one per frame to **114**.

The half that was missing: **the projected cap is not a closed curve.** The
renderers sampled the cap in azimuth and projected each sample, and `unrolled`
wraps longitude into `(-180, 180]` before mixing in the plane term, so the
sampled boundary jumps the full width of the seam twice at every `t > 0` — 511
units at `t=0.25`, 1004 at `t=0.5`, against `R=1000`. Every flat closure
recorded in 0.1.388 was one of those jumps. The index-shortest rule was not
merely wrong; it was **accidentally suppressing a second defect** by rarely
walking far enough to meet one.

So the clip happens before projection now, on the sphere, where the cap is a
circle in azimuth with no seam in it. `clip_to_cap` closes a ring along that
circle in the ring's own winding and **links its runs to each other** rather
than closing each on itself. The direction is derived, not chosen: the topology
carries real winding — of 278 rings, 277 score positive by signed spherical area
and the one negative is South Africa's second, the hole that is Lesotho — and
azimuth increasing traverses the cap with the same handedness, so a positive
ring walks forward and a hole walks back. It depends on no sampling, which is
why both renderers now make the same decision and the recorded divergence is
gone.

**That measure must never be applied to the cap itself.** Its branch wraps at a
hemisphere: a cap of 91 degrees scores negative where one of 89 scores positive.
The visible cap is larger than a hemisphere for every `t > 0`, so deriving its
handedness from its own area would have inverted the walk across the entire
animated range. Written down in the function, because it is invisible until `t`
leaves zero.

`_pole_close` was restricted to `t=1` and measured against `x = cx ± R`. Both
were symptoms of an unmodelled boundary: at `lon_rel = ±180` the sphere term
vanishes at every latitude, so **the seam is a pair of vertical lines at
`x = cx ± tR`**, and a pole is a point on the sphere and a segment at
`y = cy ∓ R(1 - t/2)`. Both are exact, both are real at every `t > 0`.

**Two defects survived every check and were found by looking.** The checks went
green, the recorded entries were removed, and the contact sheet showed
Antarctica painted over the entire disc at `t=0`. Natural Earth closes it along
the `lat = -90` edge of its rectangular source map, so 181 of its 433 densified
points are a pole artifact; where the cap passes through the poles they evaluate
to `±6.1e-17` and read as interior. A point ON the boundary is not INSIDE it.
Then the same figure at a Pacific-centred view filled again, for an unrelated
reason: two runs meeting exactly at that artificial break, and a guard that read
a zero-length arc as a full wrap. Both produce a closed path whose every point
lies on or inside the cap with its winding intact — **which is to say both
satisfied all six invariants written that morning.** Convention 8 is not a
suggestion.

The seventh invariant is the one that would have caught them: **a clip can only
remove area.** A closure that walks the whole cap returns 6.2965 sr from a
0.2985 sr input. Every invariant here was mutation-tested — the fix reverted,
the check confirmed to fail — because a metric with no failing case is the
defect this release found in its own checker.

**Three defects in the checker, all found while using it.** `KNOWN_FLAT_CLOSURES`
claimed a two-way lock — a fourth fails, and so does fixing one without removing
its line — and **the second half was never implemented**: the set of pairs seen
was collected and never compared against anything, so all three could have
healed in silence. The flat-segment probe's loop sat OUTSIDE the per-path loop,
so it read whatever the last path left behind and examined one path per frame,
of twelve for the region layer. And the JS land layer was drawn without its
`view`, so no closure and no guard ran on it at all.

`geo_projection.limb_walk` took the same shorter arc and now takes the winding.
`build_geography.py`'s eight hand-authored rings have accidental winding —
`australia` and `maritime-se-asia` score negative with no hole to justify it —
so the globe normalises them; both come back geometrically identical, which
confirms the static assets were never affected. The canvas back end closed a
clipped fill with a bare `closePath`, a chord straight across the sphere, while
the SVG side walked a boundary; it shares the clip now. Its densify cache was
keyed on arrays `splitAtSeam` allocates fresh every frame, so it never once hit
and grew unboundedly at 60 frames a second — removed rather than repaired.

Recorded and not fixed: the projection **folds** at intermediate `t`. The visible
set admits a strip of the far side that maps back over the front, so at `t=0.5`
content is drawn out to radius 90.1 while the curve everything is clipped against
sits at 76.6–79.3. `invert` has always documented this from the inverse side; the
forward consequence had not been written down. Moving the threshold to the fold
crease changes `unrolled`'s visibility flag, which regenerates the 1300-sample
golden grid — the only thing holding the JS port to the Python — so it is its own
change. `specs/2026-08-10-winding-clip-design.md` carries the measurements.

## 0.1.388 — the runtime reaches the deliverable, and the closures that only a filled figure shows

**0.1.387 shipped a component no deliverable could run.** Seven ES modules,
verified over HTTP in a harness, and a demo deck carrying a static frame and no
JavaScript at all. A deliverable is opened over `file://`, where the browser
refuses ES modules as cross-origin, so `<script type="module" src=...>` there
does not merely break self-containment — it does not run. There was no inlining
path and the gap was not visible from inside the repository, because everything
here is checked against markup.

`scripts/embed_globe.py` closes it: the modules concatenated in dependency
order, the geometry as JSON, one call, no fetch and no module graph. Its
`--check` refuses to emit a block containing an unresolved import, a surviving
export, a dynamic import or a fetch, and refuses a duplicate top-level
declaration — `projection.js` and `controls.js` both declare `D2R`, correct as
modules and a SyntaxError once concatenated, which in a deliverable shows as a
still figure and one line in a console the reader never opens.

**Form and t were bound together and should not have been.** `setForm('regions')`
forced the flat map, so a document could not have the figure this component
exists for: a turning globe with its trade regions coloured. `form` now selects
which layer is painted and `t` the geometry, and rotation depends on `t < 1`
rather than on which layer is showing.

**The accessibility layer relied on the host to hide it.** A deliverable that had
not been told to style `.gl-a11y` got eleven bulleted buttons under the figure.
A visually-hidden element carries its own hiding.

**Closures that cut straight across instead of following the boundary.** Fixed:
the pole-edge close fired on the globe, where the boundary is a disc and not a
rectangle; the limb walk ran from the wrong end, so its first point sat beside
the start of the run instead of beside the end; runs were cut between samples
rather than exactly on the boundary, so the walk could not match them — the same
failure `build_geography.py` recorded when it was written; and the two renderers
rounded coordinates by different rules, Python half-to-even and JavaScript
half-away-from-zero.

**Two defects remain, both recorded and both measured.** The limb walk picks the
arc that is shorter BY INDEX, and the correct arc is the one that keeps the
polygon's interior on the correct side — a winding question, not a distance one.
Where they differ the fill spills across the polar cap. `check_globe.py` carries
the three flat closures and the one renderer divergence this produces as named
exceptions, so a fourth fails and so does fixing one without removing its line.
Carrying winding through the clip is the standard spherical polygon-clipping
problem and it is its own change.

**A new check, because nothing here could see a filled defect.** Every gate in
this package reads markup, and a band across a globe is a correctly-formed path.
`check_globe.py` now looks for long perfectly horizontal segments: after
projection a parallel is a curve, so a run of constant y is a closure that took
a straight line. It is also what found the three that remain.

`check_design.py`'s `token_blocks` kept the last `:root` block and dropped the
rest, so any document appending `tokens/region-palette.css` lost its whole token
block and reported UNMEASURABLE. Blocks accumulate now, the way CSS does, and
`d4_palette` reads them separately because it strips them by verbatim match.

## 0.1.387 — the globe: region hue by owner directive, labels carry identity, and the mark kept apart from the map

**A world figure that states data has to be generated from data.** Two reference
sites were reverse-engineered before anything was written. Both run the same
engine; their methods are opposite. One generates its geometry at runtime from
GeoJSON, the other loads a model authored in a 3D tool. A figure carrying a
number must be the first kind, because changing the number has to change the
picture without reopening a modelling tool. Neither library fits a
self-contained deliverable — half a megabyte compressed — so the geometry, the
projection and the renderer are this package's own, in the standard library and
in vanilla modules.

**Hue encodes region identity, which is the single exception to one colour one
meaning.** An owner directive, and it is safe only because these hues are
declared to carry no data meaning, exactly as `light_ramp` already is. Two
proposals were made and rejected on the way, and both are recorded because the
numbers are the reason:

* an 8-hue ceiling. Rejected: the map layer needs more regions than that.
* a ΔE00 floor of 20 over *all* pairs. Unsatisfiable at every N — the best
  achievable is 18.1 at N=8 and 6.8 at N=20. The floor now binds adjacent pairs
  only, and the label rule covers the rest.

A four-band construction was built, measured clean, and then withdrawn on
looking at it: it satisfied the adjacent floor while putting three of eleven
regions inside one narrow window, so Europe and Southeast Asia measured ΔE00 5.0
apart and rendered as one colour on the same map. Even spacing with a
max-separation assignment gives 12.0 over all pairs, 23.0/20.8 between adjacent
ones, and needs no constraint on the registry at all. **Adjacency counts regions
within 1500 km as well as regions that share a border**, because an ocean strait
is not a visual separation — Europe and North America face each other across 300
km at Greenland and the first version gave them the same hue.

**Every coloured region carries a label or a legend entry, whatever the hue
count.** At the theoretical maximum separation of 90 degrees, deuteranopia
collapses two adjacent regions to ΔE00 9.6 and protanopia to 8.5, and a real map
runs at 60 or less. Hue separates neighbours at a glance; text carries identity.
D18 checks for the text and never counts hues, because a threshold is exactly
what the measurement does not support.

**A canvas is invisible to every gate this package owns.** `d5_drawn_share`
counts a figure as drawn only if it holds an `<svg>`, `d5_figure_parity` and
`d17_export_weight` read markup, and `inspect_layout` cannot see inside one. So
the deliverable renderer emits SVG and the runtime mutates that markup rather
than replacing it: the file on disk is a complete no-JavaScript fallback, the
gates can still read the figure, and a screen reader's tree does not churn under
animation. The canvas back end exists for pages where no gate applies.

**Two geographies now ship and they disagree about where a coastline is.** The
hand-written two-degree coastlines are a *mark*; Natural Earth 110m is a *map*.
A document may use either and must never place both in one view. Re-deriving the
coarse set would change the shipped cover mark byte for byte, so it is deferred
with its own retrospective.

Nine defects were found only by putting the thing on screen, and none of them
was visible to any metric when it was found: a renderer that wiped the hover class sixty times a
second, a drag with the longitude sign backwards, an unroll that never arrived
because it eased asymptotically, a viewBox that stayed square while the map went
2:1, clipped rings closed with a chord instead of along the limb, and a form
switch into an empty map because the runtime cannot create markup it was not
given. And three separate causes of a line drawn across the whole flat map: the
two inserted seam crossings landing on the same edge because lon0+180 wraps to
-180; source vertices sitting exactly on the antimeridian, which has no side, next
to a neighbour at 177.99; and a last-piece/first-piece join that is right for an
ordinary ring and wrong for one that wraps the world. Fifteen such segments
became one. CLAUDE.md 8 governs, and it earned its place again.

**One defect is open and recorded rather than tolerated quietly.** A subpath in
the oceania region still starts on one edge of the flat map and continues to the
other, drawing a hairline across the equator at t=1 and nowhere else. No oceania
ring spans the seam, so the cause is not the seam split and is not yet known.
`check_globe.py` measures the class of defect and carries this one instance as a
named exception, so a second one fails the check and fixing this one also fails
it until the record is removed. Reproduce with
`scripts/globe_svg.py --form regions --t 1`.

Export weight, corrected against a measurement rather than a guess: a globe page
does **not** move D17 much. D17 counts polygon points and `<path` ELEMENTS, and
the globe is about a dozen elements carrying very long `d` strings — a demo deck
with two globe figures reported 14 nodes. The weight is real and it is in bytes,
not in that metric: a static globe frame is 45 KB and a flat region map 68 KB,
integer coordinates included. Say the file size; D17 will not say it for you.

## 0.1.386 — a viewBox that does not parse is a defect, not an absence of one

**A drawing whose viewBox the browser cannot read now fails the run.** Three
numbers instead of four is legal as an attribute and meaningless as a value: the
browser discards it and lays the drawing out against a box nobody chose. Found
while building an internal document, where a six-row figure rendered three rows
and left half a page empty — with every check green, because the clipping probe
added one release earlier read the unparsed box as *nothing to measure* and
skipped it silently. That is the same shape as the defect it was written to
catch, one level up: the probe could not tell a drawing it had checked from a
drawing it had given up on. Tenth `--deliverable` gate, with a planted case in
the broken fixture so it has failed once before anyone trusts it.

The lesson generalises past this probe and is worth stating: **a check that
skips is not a check that passed.** Every `continue` in a probe is a claim that
the thing skipped was not a subject, and that claim needs to be true.

## 0.1.385 — deliverables leave the package's own directory, and the sheet's figure ceiling stops contradicting the figure rule

**A deliverable lands in the reader's workspace, not wherever the input happened
to sit.** The default had been the input file's own directory since the export
axis was written, which is fine for one person working on one document and wrong
for everything else: several agents working at once, several people sharing a
machine, and — the case that found it — an input that lives inside the package,
which put finished client documents in the skill's own install tree. The default
is now one named place under the user's own documents folder, the same place on
every platform this package claims, and **the agent asks before creating it**.
Two things deliberately do not change: an export still lands beside the document
it was made from, because a deliverable's HTML and PDF belong together, and a
directory the user names still wins. A shared folder does put one new obligation
on a filename — it now carries its own identity, name and version, because two
documents that share a stem no longer merely sit side by side.

**The portrait figure ceiling and the figure-aspect rule had been contradicting
each other.** §4 says a full-width A4 cell is about 0.85:1 and asks for a drawing
built to that shape. The sheet's own `max-height` capped a figure at 52svh, which
in a 682px column means no drawing under about 1.17:1 can render at all without
being clamped short and pillarboxed. So the rule asked for a proportion the
tokens forbade, and the best page in the first handbook designed for the sheet
sat exactly on the cap. The ceiling now clears the cells it has to hold. It is
still a ceiling and not a target, and the page box remains the real bound —
`--deliverable` fails a page that exceeds it. *Measured by redrawing every figure
of that handbook to the shape §4 asks for: twenty-one drawings that had run 1.18
to 2.80:1 in cells of 0.78 to 1.10, filling 43 to 82 percent of their cell and
leaving empty bands of 12 to 35 percent, now sit within a few points of their
cell and fill 80 to 98 percent of it, with bands of 2 to 9. The redraw is the
thing §4 already prescribed; what had been missing was permission to land it.*
The redraw also confirmed the rule's own wording about how: a figure that is
already a vertical stack does not get taller boxes, it gets **another line of
real content per row** — a criterion, a consequence, a worked example. Stretching
the chrome would have hit the same number and taught the reader nothing.

**An unknown genre is now unmeasured rather than quietly graded as sales.** The
share probe read `data-genre` with a pattern that accepts any word and checked it
against nothing, so a misspelling scored a training handbook against the sales
target and said nothing. It now grades only a genre the package declares and
reports the rest as not measured. `internal` gained the entry it had been falling
through, and the help text for `--deliverable` caught up with the ninth gate that
shipped in 0.1.384.

## 0.1.384 — the caption found its figure, the table stopped stretching, and the sheet was asked to carry more than the slide

One review of the first handbook designed for the sheet, four findings. Three
were mechanical and one is a rule the package did not have.

**A caption centres on its figure.** §4 had said the caption aligns with the
drawing's left edge so the eye returns to where the figure began — a reasonable
rule that nothing measured, and that the shipped CSS had never implemented. The
caption aligned with the *cell's* left edge, which is the same edge only while
the figure's box is unclamped; the moment `max-height` bites, the drawing is
pillarboxed to the middle of its box and the caption stays behind at the margin.
The rule now says the caption block centres on the drawing, and a probe reports
the offset between the rendered caption's centre and the figure's ink, so the
next divergence is visible rather than inferred. One boundary comes with it: a
drawing whose ink is not centred inside its own viewBox cannot be aligned by
CSS at all, and gets redrawn.

**A table keeps the row height its content asks for.** A table in a centerpiece
cell was given the cell's height and distributed it across its own rows, capped
only for tables of three rows or fewer — a threshold that appears in no
retrospective and was never argued. Stretching table rows is the package's own
canonical example of satisfying a measurement without improving a page: it is
why the 82 percent fill floor was withdrawn in 0.1.340. It should not have
survived as a mechanism after being named as a defect. Tables now sit at their
natural height and the cell's slack stays in the cell, which is an honest empty
band rather than a disguised one.

**A cell holding a grid aligns to the top, and a drawing that leaves its own
viewBox is now a gate.** Two findings the table change surfaced. With the stretch
gone, a centred table put 280px of nothing between the support line and the header
row — read as a missing section on a page, and as a missing question on a scoring
form the reader writes on — so a cell holding a table starts under the title and
lets its slack collect at the bottom, where it is room to write. And measuring
figures for the caption rule turned up three drawings whose text ran past the
right edge of their own viewBox: a root `svg` clips there, so those sentences were
never rendered at all, with no overflow, no collision and no spill for any other
probe to see. That is the defect CLAUDE.md rule 8 names as the reason a person has
to look at the render, and it is decidable, so it does not need one — it is the
ninth `--deliverable` gate.

**The stat band ships its own rendering.** `.band` carried a cross-axis rule and
no `display` at all, so every document that used one re-invented the box —
the orphan-role failure this package has now recorded four times. The base is
column auto-flow, because a band carries as many tiles as its page has data and
a fixed column count breaks the first page that disagrees.

**A page on the sheet carries more than a page on the slide.** New rule, and the
first per-geometry statement in this package about *content* rather than
composition: an A4 portrait content page carries a second content block beside
its centerpiece — what to notice in the figure, the steps, the caution, the
worked example — and at least one highlighted key point. It is a floor on the
page's blocks and deliberately not on the support line, which stays at one to
three sentences; a page that cannot hold both becomes two pages, because the
sheet is fixed and type is never nudged to make room. *Provenance: the first
handbook designed for the sheet gave nine of twenty-one content pages a second
block and left the other twelve running a 24 to 33 percent empty band under the
figure. Its reader asked why the printed page said less than the projected one.
The layout rules had all been applied; none of them was about how much a page
should say.*

Also: the vertical layout family now states which of its rows absorbs the slack,
because the one whose flexible track sits in the *middle* had been picked for a
figure-led page and put the whole sheet's leftover height between the band and
the drawing. And two files still counted the design metrics as D1–D16 after D17
shipped.

## 0.1.383 — three things the sheet taught, once a document was actually designed for it

**The visual share is graded at the geometry the document declares.** It asked
"is this render A4", which was right while portrait was always a second edition
and wrong the moment a handbook declared the sheet as its own stage: the
training target was reported and never applied on the only geometry that
mattered. It now grades the declared one and reports elsewhere.

**Stacked cells centre on the sheet.** Side-by-side cells top-align so a reader
can cross between them; on the sheet those same cells are stacked rows, where
there is nothing to cross and the rule only pushed every page's slack to the
bottom edge. Measured on the handbook: the boundaries page carried a 37 percent
empty band and the glossary 49, which centring took to 20 and 26.

**A figure is drawn for the geometry it will sit in**, and §4 now says what the
cells actually are: about 2.5:1 full width on the slide and 0.85:1 on the sheet,
1.3:1 and 1.0:1 in two columns. A 1.5:1 drawing in a 0.85:1 cell fills a little
over half its height however it is scaled. *Provenance: the first handbook
designed for the sheet drew its figures at 1.4:1 to 2.2:1 and ran a 24 to 39
percent empty band against 5 to 27 on a landscape deck built the same week.
Redrawing one figure's four gates from a row into a two-by-two took it from 47
to 76 percent of its cell, which is the fix the rule now names: portrait figures
stack what landscape figures place side by side.*

## 0.1.382 — the window stopped deciding the design, and the declaration reader stopped reading its own documentation

Producing the first document actually designed for the sheet put the 0.1.380
portrait work under load, and it found four defects in an hour. Every one of
them was invisible until a portrait deliverable existed.

**The type scaled with the reader's window while the page did not.** The
display tiers were `clamp(min, Nvw, max)`, written before the page became a
fixed box. With a `zoom`-scaled stage, `vw` resolves against the window and the
box does not move, so one document set its titles at one size on a laptop and
another on a wide monitor. Measured on the handbook: the cover's display type
nearly doubled between the sheet and an 1800px window, and its ascenders
landed on the wordmark. The tiers are now **fixed per stage** — the values the
old clamps resolved to at each design geometry, so nothing moved at the
geometry each was drawn for — with the portrait block carrying the sheet's own
set. `zoom` stays viewport-relative, because scaling the whole stage to the
window is the one thing that should follow it.

**The reserve and the datum asked the window which geometry it was.** Both read
`window.innerWidth >= window.innerHeight`, so a portrait handbook opened wide
was told its released reserve was overspent and its released datum was lost.
They now read the document's declaration, which is the thing that decides
composition since 0.1.380.

**The declaration reader read the stylesheet's own documentation.** 0.1.379
matched `data-geometry` in the CSS *selectors*; 0.1.381 anchored on the `<body>`
tag and then matched the worked example inside a token file's *comment*, which
graded a portrait handbook as landscape. Both readers now strip style blocks and
comments before looking, because what is left is markup. Second instance of one
defect, and this note is here so there is no third.

**The cover typeblock shipped a zero gap under leading of .92.** Display glyphs
stand taller than their line box, so the title's ascenders reached the wordmark
above them: a 3px overlap on the cover and the closing, which the collision
check catches and a reader sees as a smudge. The typeblock now carries a 12px
gap, and the workaround a deliverable had added locally is deleted.

## 0.1.381 — the apparatus exemption, declared rather than inferred; and a scope the audit did not know

Two owner decisions from the 0.1.380 review, both closing a gap that had already
made a real deliverable work around a check instead of satisfying it.

**A reference page is exempt from the visual-share target, and it says so.** A
glossary, a scoring page, a boundaries page and a how-to-use-this-deck page are
reference the reader returns to rather than claims the deck advances; asking
them to carry a figure produces decoration, which is what every rule in §4
exists to prevent. They now carry `data-role="apparatus"` and drop out of both
halves of D16.

**Declared, never inferred** — that is the whole design. An inferred exemption
is the escape hatch that empties the metric; a declared one is auditable, and
the pages that claimed it are named in the report. The test is the claim: a
content page advances one and owes its visual block, an apparatus page carries
none and owes nothing. A page that merely failed to earn a figure is not
apparatus. The share carries **a ceiling of about one content page in five**,
because past that a deck has stopped arguing and become a handbook — reported,
never gated, like the rest of D16. Both fixtures exercise it in opposite
directions: the passing one holds a prose-only page that declares itself and
must not be listed, the broken one keeps an undeclared prose-only page that
must.

**`.tag` joins `.no`'s shipped scopes in the consistency audit.** `tokens/` has
shipped `.tag.no` — the refused status chip — since 0.1.375, while the audit
knew only `.swap .no`, so a document using the chip was reported as inventing a
rendering it had not. A scoped audit that does not know every scope the
stylesheet declares manufactures the split it exists to find. The evidence that
this mattered: the 0.1.379 deliverable worked around the finding by choosing a
different chip, which is a check shaping a document rather than measuring it.

## 0.1.380 — one document, one geometry; and the blend mode that cost ten times the render

A reader opened the A4 edition of a landscape sales deck and found five defects.
All five were real, four of them had one root cause, and the fifth was measured
rather than guessed.

**A deliverable is designed for one geometry, and it says which.** The two
stages were window-shape media queries, so a landscape deck in a tall window —
or exported at A4 — silently became a portrait composition nobody had designed:
dead half-pages, a figure starved to 188px in a 682px column, and a footer
wrapped on all 31 pages. None of it was visible at the geometry the deck was
built for. The stage now hangs off `<body data-geometry="landscape">` or
`"portrait"`, the portrait composition applies because the document *says* it is
portrait rather than because a window happened to be tall, `inspect_layout.py`
grades the declared geometry, and `export_pdf.py` **refuses** the other one. The
genre still picks the default — sales, marketing and consulting lead landscape,
training leads portrait — and **when a request settles neither the genre nor the
format, the skill asks before generating.** That is the one question worth a
round trip, because the answer changes every page. A second geometry is a second
*composition*, in its own file.

**The footer wrapped because the page frame shipped nowhere.** `.page` had no
rule in `tokens/`: every document invented its own `position`, `display` and
padding, and a document writing `padding: 44px 92px` overrode the sheet's 56px
margin, leaving the footer 610px where it had 682. The fix is not a smaller
font, it is shipping the frame — the same defect as the missing
`.foot { display: flex }` of 0.1.366, and the footer's own type now ships too
(`--fs-foot`), because "footer terms" has been an audited role since 0.1.350
while every deck declared its own size. **A wrapped footer is the eighth gating
finding**: it is furniture overflowing its frame, which is decidable.

**Two portrait rules were reserving space the content did not have.** The
collapsed split used `minmax(0,3fr) minmax(0,2fr)`, so a short first cell left a
dead band measured at a third of a sheet; the cells now hug their content and
the centerpiece absorbs the slack. The portrait figure cap rose from 36svh to
52svh, where a wide drawing had been rendering at a quarter of the page. The
short-narrow and short-height media queries were removed outright: they predate
the zoom stage, and a small window now shows a smaller page rather than a
narrower one, so collapsing its columns answered a problem the stage had already
solved.

**A figure's name holds one line.** 14 of 17 captions wrapped at A4 and 7 of 17
at 1280, because nothing bounded the name. It is a ceiling, not a target — about
100 characters on the slide, about 60 on the sheet — and a name that overruns
gets shortened, never set smaller. `inspect_layout.py` counts wrapped captions.

**The visual-share target follows the genre** (owner directive): about half the
content area for sales, marketing and consulting, where the page argues
visually; about a third for training, where a learner needs the words beside the
drawing. The document declares its genre and the checks grade against that
number. Both remain review triggers, never floors.

**And the PDF: `mix-blend-mode: multiply` cost an order of magnitude.** A 513 KB
31-page export took 4515ms to render; removing the blend on five opener pages
alone brought it to 448ms. One blended element forces the reader to composite the
whole page. Baking the ground's alpha per tier and cutting its node count by 44%
changed the file size and nothing else measurable, so the fix is the mode, not
the geometry: on the lime field the ground darkens the field, which is a colour —
its strokes take the field's own foreground — and the look is identical.
`check_design.py` gains **D17, export weight**, reporting blend modes, filters
and vector nodes, and `export_pdf.py` warns when a PDF it just wrote carries a
blend mode.

## 0.1.379 — the four-agent review of 0.1.375–0.1.378, closed

The owner ran a four-way review over the whole unpushed line — general
quality, comment accuracy, test coverage, silent failures — before trusting
it. Two findings arrived from two reviewers independently, which is what put
them first.

**The export tool now settles before it captures.** `export_pdf.py` had
reintroduced the pattern `inspect_layout.py` was rewritten to kill: a bare
300ms sleep, no wait on `document.fonts.ready`, no `pageerror` listener — and
with `font-display: swap` on the embedded face, a capture racing the font is
*guaranteed* to ship fallback metrics under an `ok` line. Worse here than
there: the inspector mis-measures, the exporter mis-delivers. It now waits on
the fonts (5s, explicit FAIL on timeout), fails the file whose own script
threw, refuses a second input whose stem would clobber the first's output,
warns when stale higher-numbered pages from a longer earlier export survive
beside fresh ones, reconciles the PDF's own page count against the section
count, and one bad file no longer aborts the batch (per-file FAIL, browser
closed in `finally`).

**Guards that guarded one of two carriers now guard both.** The 0.1.378
ENTRY_STAMP union fix had reopened its own hole one level up: a stamp file
declared only in ENTRY_STAMP — exactly the scoreboard — could be renamed away
and skipped under a comment crediting the manifest guard, which never covered
it. A missing non-registry stamp file now fails by name, and the negative path
was exercised before shipping. The visual vocabulary's second carrier —
`check_design.py`'s `VISUAL_BLOCKS`, which 0.1.378's own rationale overlooked
while calling the probe's `VIS` "the sole carrier" — is now read by the
probe-vocabulary guard and held set-equal to `VIS`; "a guard that covers one
of two callers is a guard with a blind spot the shape of the other" now has
its caller count right. The genre vocabulary lives once, in
`check_prose.py`'s `GENRES`, imported by `run_conformance.py` and
`export_pdf.py` instead of hand-copied thrice; `export_pdf.py` also gains
`--genre`, so a training deck exported with defaults now ships its primary A4
edition rather than the projection one its help text used to promise and its
default used to violate.

**The proven regressions are pinned.** D10's eyebrow count — which shipped a
zero-count twice, keyed first to `<div>` and then to attribute order — is now
element- and order-agnostic, matches `ic` as a whole class token, and emits a
per-page `D10_detail` that the pass fixture asserts (`contains: p3`); revert
either form of the regression and CI fails. `D16_detail` carries the whole
dict so the pass fixture can assert `"prose_only": []`, closing the
false-positive direction reported verdicts cannot see. `check_fixtures.py`
learns suffixed runs (`prose@training`, `prose@internal`) so M9's training
binding and internal exemption each have an asserted run, and it smoke-tests
the export floor — `--scale 1` must exit 2 naming the floor, checked in CI
with no browser since the check sits ahead of the playwright import.

**Absence is no longer reported as measurement.** `visualPct` is null, not
0%, on a page with no body or a lede taller than it, and the share lines skip
what was never measured; a ground wrapped inside another element — which the
page census counts and the contrast audit cannot isolate — now reports GROUND
UNMEASURED and counts as unmeasured instead of letting the same report say
"continuous on all pages" and "no page draws one" about one document. The
`.grades` and `.field` blocks join the fill-rule exclusion chains before the
chain wins a tenth argument: both declare their own direction and gap, and
only fixture accident had them nested where the chain could not reach them.

**Facts corrected where reviewers caught the prose lying**: six of the eight
svg type classes declare fills, not four of six (comment and changelog both);
the ground generator now draws sixteen genuinely distinct widths, making its
"no two sharing a width" docstring true instead of half-true; the conformance
tuple rejected `training` for two releases, not one; D15's scope sentence
counts four genres; the handling marker's token is `--seal-t` (text-safe on
both canvases), not `--seal`, in both places the prose said otherwise; the
marker sits *inside* `.foot .conf`, not ahead of it; the opener's "nothing
else" scopes to its content area, since its footer legitimately keeps the
inverted marker; the self-contained core prompt finally lists `cover-grid`,
the layout its own frame rule requires; and the fill-chain tally names its
fourth victim (the closenote's 12px) so the "sixth through ninth" arithmetic
can be reconstructed.

## 0.1.378 — what the two audits found in the three releases before it

The owner asked for the 0.1.375–0.1.377 line to be audited before trusting it.
Two independent passes ran: an adversarial audit of the eleven directives
against the shipped state, and a rendered review that read computed styles in a
headless browser. CI was green through both, which is the finding behind every
finding: each defect below sat in the space the green run does not cover. This
release closes them.

**Rendered defects in the promoted vocabulary.**

- The `svg .f-*` paint classes lost to the `svg` type classes by source order —
  every selector is (0,1,1), six of the eight type classes also declare a fill, and
  the explicit win-back list covered `huge`/`mid` only. `class="sm f-acc"`
  rendered ladder-grey; `class="cap-w f-seal"` never turned red; the palette
  guard saw nothing because no literal colour was involved. The paint set now
  sits after the type set, which is the ordering that cannot develop the gap.
  Inherited faithfully from the reference deck, where it is also present.
- The cover-grid and opener children shipped as (0,3,0) rules under the fill
  rule's (0,13,1) `:not()` chain — the typeblock's `gap: 0`, the attrs column's
  3px and the openframe's 26px all computed 14px, the sixth through ninth time
  that chain has quietly won an argument. The five new children join both
  chains, and the chain's comment now states the mirror rule: a new
  `.body > div` child joins it or its declarations are dead on arrival.
- `.sub` was half-shipped: promoted out of the waiver list with a rendering
  scoped to `.cover` alone, so the closing's subtitle fell through to generic
  paragraph styling. Cover and closing are the same kind of page; the rule now
  says so.
- The dark ground ramp was inverted — mid at .24 against strong's .20, a part
  opener denser than the cover — surviving from before the tiers were held to
  a ratio, and left in place when 0.1.375 restated that ratio one palette up.
  Dark mid takes .15 (the same ≈0.76 ratio the light tiers hold); dark strong
  is unchanged.

**Metrics that could not see their own subject.**

- D10 keyed the eyebrow count to `<div class="eyebrow">`, so the fixtures'
  `<p>` eyebrows counted zero and were silently reclassified as figure icons.
  The selector is element-agnostic now and counts 14 where it counted 0.
- The `VIS` list — the sole carrier of the visual-share target — was outside
  `PROBE_CENSUS_LISTS`, so a rename in `tokens/` would have dropped the share
  toward zero with CI green. It joins the guard.
- A deck with no ground read the same as a deck that had been checked
  ("ground: no page carries one", neutral). It now reports GROUND MISSING,
  still never gating: a document outside the brand may be quiet on purpose.
- The 50% visual-share target was ungradeable at A4 — the portrait tokens cap
  a figure at 36svh, and every page of the package's own fixture sat "under
  target" there while healthy. The sheet now reports shares without grading
  them; the target binds in landscape, where it is reachable.
- `check_version_citations` iterated the platform registry's entry files only,
  so ENTRY_STAMP's conformance entry was dead code and the scoreboard's stamp
  sat at 0.1.371 for six releases while the entry's own comment claimed to be
  the check that sees it. The guard now walks the union, and the stamp is
  current.

**The harness catches up with the genre model.** `run_conformance.py` rejected
`training`, the genre 0.1.376 created — the four-genre model had reached the
rules, the checker and all three entry points and stopped at the cross-agent
harness. It accepts it now; T1 also gains the `D15_footer_path` requirement,
which is a gate of equal standing with D12/D14 and was missing from the task's
require list. `export_pdf.py` gains `--genre`: its help text stated the
primary-geometry rule while its default violated it, so a training deck
exported with defaults shipped the projection edition. The raster floor now
binds rasters only — a PDF is vector and has no scale to be under.

**The fixtures exercise what they advertise.** Both now draw the ground —
sixteen deterministic lines, defined once and instantiated per page with
`<use>`, no two sharing a width, amplitude, wavelength or phase, measured
under the 1.40:1 ceiling in all three geometries (1.251 / 1.354 / 1.312 at
the loudest) — plus a `.field` with one mark per datum and its `data-count`,
the graded ladder on one page, the glossary on another, and status chips in
the page-9 table. Until now the suite shipped the brand's signature devices
and rendered neither.

**Prose drift found while auditing, fixed:** the 4K/2K export rule reached
only one of three entry points (now in `AGENTS.md` and the core prompt); the
shield marker was missing from SKILL.md alone of the four restatements; "first
principles" and "the blue team" are now written where their substance already
was; CLAUDE.md's checks list, genre note, scenario list and rubric line;
eval-rubric's M1–M8 heading over a table running to M12, and its D-table's
missing D13 and drawn-share rows; brand.md crediting D13 with enforcement when
only D12/D14/D15 gate; SKILL.md counting four entry points while naming three;
the core prompt counting four block patterns while listing seven.

**Recorded no-changes, so the next audit does not reopen them:** the pass
fixture keeps its 7-page opener runs — the pacing target stays a review
trigger, and the reference deck itself runs longer parts; and `check_prose.py`
still has no `consulting` genre flag — consulting inherits the sales dash ban
by default, which has produced no defect case yet and gets no speculative
flag without one.

## 0.1.377 — the export path ships with its floor in code, and the workflow learns to ask once

The last of three releases carrying the owner's consolidated directive
(2026-08-09). The rules that name tools now have the tools (rule 5), and the
workflow gains the interaction discipline the directive asked for.

**`scripts/export_pdf.py` ships.** §7 has named "PDF export" as a destination
since the geometry axis existed, with no exporter behind it — the exact gap
rule 5 exists to close. The tool renders at the fixed stages and nowhere else:
PDF as one vector page per `.page` (no resolution to pick), and page rasters
at a device-pixel multiplier on the stage — **default 3, which is 4K from the
landscape stage; floor 2 (2K), refused in code** rather than advised in prose,
because a 1x export looks fine on the machine that made it and soft on every
dense display. The scale never touches the CSS stage: every `clamp()` in
`tokens/` is written against the stage, and the HTML edition adapts to the
reader's window and pixel density natively, which is where "auto-adjusting
resolution" honestly lives. Output lands beside the input file, matching the
new output-directory default. Same dependency posture as `inspect_layout.py`:
local, Playwright, py_compile only in CI.

**The workflow learns the interaction rules.** The directive asked for two
things that pull against each other — interrogate the input deeply, and let
one clear prompt produce a finished document — and the arbitration is now
written down: study everything supplied first, work from the reader's side,
and **ask once or not at all** — a missing required input or a genuine
conflict batches every question into one round before generation; anything
less than that becomes a stated assumption in the delivery note. Outputs land
in the input file's directory unless the user names another. Pages compose in
parallel where the platform allows, and a generation expected to pass ten
minutes is announced before it starts. **The red-team pass rides the critic
gate**: the half that built the document argued for it, so the other half
reads it as its most skeptical reader before the self-score — and over-design
is a finding there, not a virtue, which is the directive's own guard against
this skill answering "more expressive" with "more decorated".

All of it re-flowed by hand into `AGENTS.md` and `prompts/lumi-style-core.md`,
where the checklist grows its red-team item and the dash rule names training.

## 0.1.376 — the page anatomy becomes a contract, and training becomes a genre

The second of three releases carrying the owner's consolidated directive
(2026-08-09). 0.1.375 shipped the vocabulary; this one writes the rules that
vocabulary serves, and none of the new numbers gates — each one states its
direction (rule 4) and the two that could have been floors are review triggers
instead, because the withdrawn 82% fill floor is what happens otherwise.

**The deck frame is standardized.** The closing now carries the same single
vector mark as the cover, under the same truth test — a cover and a closing are
the same kind of page, and the closing restates rather than claims anew
(storyline-templates). **Every part boundary gets a lime opener page**, in the
composition the tokens ship; **about five content pages between openers is a
pacing target**, reported by `inspect_layout.py` as the longest run between
openers, never a floor — a target read as a quota would force openers where the
argument has no seam. The opener count line itself stays an observation.

**The eyebrow becomes a contract** (design-rules §3): the page's subject icon,
then `PART <letter> · <this page's own label>`. Deliberately uniform and exempt
from the parallel-structure caution — the eyebrow is apparatus, like the page
number — while titles stay governed by the title contract and M11, which counts
h1/h2 only and never the eyebrow.

**D16, visual presence and share, reported.** The directive's strongest ask —
"more than half of every page should be figure" — is precisely the shape of the
withdrawn fill floor, so it lands as two reported halves instead of one gate:
`check_design.py` D16 lists content pages carrying no visual block at all
(figures, stat bands, display leads and the comparison patterns count; tables
deliberately do not), and `inspect_layout.py` reports each page's rendered
visual area against a 50%-of-content-area **target**. Both are review triggers
for a human; neither can be satisfied by stretching anything, because they
count classified blocks rather than ink. The broken fixture plants a
prose-only page and `check_fixtures.py` asserts the detail names it.

**Training is the fourth genre** (storyline-templates Template 4): for enabling
a team to do something rather than decide something — concept pages, worked
examples, the swap as its workhorse, reference pages a learner returns to.
`check_prose.py --genre training` binds the em-dash rule as sales does, because
training is quoted onward. **And the primary geometry now follows the genre**
(design-rules §7): sales, marketing and consulting design 16:9 first; training
designs A4 portrait first, since it is printed, annotated and bound. The
two-geometry matrix is unchanged — the non-primary geometry is still composed
and verified as the second edition.

**The handling marker becomes a rule** (design-rules §4b): the seal shield
ahead of the terms is the standard rendering on every page. D12 is unchanged —
it gates on the terms, and a page whose terms arrive without the icon has a
style defect, not a compliance one.

**The fixtures now exemplify all of it**: cover and closing on `cover-grid`
with the globe as their shared mark, two lime openers in the shipped
composition, contract-form eyebrows with real Lucide icons via
`embed_icons.sprite()`, the shield in every footer, and a colophon that reads
its version from SKILL.md so it can never drift. The old fixture numbered two
pages `09` and skipped `16`; the rebuilt one numbers 1-18 cleanly.

Stale counts fixed in passing: `check_design.py`'s own docstring said two
metrics gate; eval-rubric's D-table now includes D12 and D16 and its heading no
longer stops at D10; README's rubric line said D1–D6.

## 0.1.375 — the vocabulary the reference deck used now ships, and the dense cover returns

The owner reviewed the recent output trajectory, named the 3.4.0-built deck from
0.1.374's comparison as the reference for how a deliverable should look, and
issued a consolidated directive (2026-08-09). That directive is the documented
case behind this release and the two that follow it: this one ships the
*vocabulary* the reference deck composed with, so that the rules landing next
never mandate a rendering the package does not ship (rule 5).

**Promoted into `tokens/lumi-layouts.css`, generalized and renamed to the
canonical tokens** (the deck's private `--accent`/`--card`/`--seal-text` are
`--acc`/`--card-bg`/`--seal-t` here — a validation artifact is never the
reference for conventions, rule 7; its *design patterns*, owner-designated, are
the facts being imported):

- **`cover-grid`, the sixteenth layout** — the cover/closing grid with its
  `typeblock` / `markcell` / `attrs` / `closenote` cells, plus the `wordmark`,
  `spec`, `sub` and `colophon` furniture. 0.1.370 removed it as a portrait-only
  orphan rather than completing it, explicitly because nobody had asked for a
  sixteenth layout. Somebody has now, so it returns *completed*: base rendering,
  portrait variant, header count, §3 selection row and `check_design.py`'s
  `LAYOUTS` in one change, which is the state `check_layout_parity` forces.
- **The part-opener composition** — `openframe` / `openpart` / `openclaim` /
  `openrun` on the lime field, with the inverted footer. §3's opener bullet now
  describes the three-line composition instead of "one line and nothing else".
- **The geography paint** — `geo-*` classes for the two `assets/vectors/` marks,
  with the cover/closing emphasis weights, plus `geolegend`. The coverage rule
  is unchanged: a region drawn is a region claimed.
- **The figure paint and figure type vocabulary** — the full `f-*`/`s-*` fill
  and stroke set and the `svg` type tiers (`lbl`/`sm`/`cap-w`/`huge`/`mid`),
  replacing the two-class `f-acc`/`f-lime` stub, so no literal colour ever
  reaches a drawing.
- **Block furniture** — the `tag` status chips, the `legend`, the glossary
  `dl.gloss`, and the `grades`/`gr` graded ladder. The ladder was removed in
  0.1.370 as speculative; the owner-named reference uses it on a live page,
  which is the documented case rule 2 requires, so its base rendering ships.
- The `.eyebrow` becomes a flex row and `svg.ic` ships, so the subject icon the
  rules already require has a rendering that needs no per-use nudging.
- **The handling marker** — a seal-red `shield` (the existing reserved binding)
  ahead of `.foot .conf`, at the owner's ask, inverting with the opener field.
  §1's ledger records the extension: the handling line is a standing warning to
  the reader, which is why the warning colour may mark it.

`PROBE_NOT_SHIPPED` shrinks from thirteen waivers to three — `openpart`,
`openclaim`, `openrun`, `grades`, `gr`, `gloss`, `geo-flat`, `sub`, `tag` and
`wordmark` all ship now, and the guard names a satisfied waiver the moment its
class lands, so the deletions ride the same change.

**The ground's strong tier returns to .25 (light, landscape), mid to .19.**
This reverses 0.1.350, which lowered the tier to .20 after the strong ground
broke its 1.40:1 ceiling at A4 on two documents. The owner asked for the dense
cover back, and the reversal was measured before it shipped, on the reference
deck's own ground: at .25 it renders 1.344 against the canvas at 1280x720 —
under the ceiling, because it is drawn with `preserveAspectRatio="xMidYMid
slice"` rather than the `"none"` stretching that caused the 0.1.350 breach —
and 1.413/1.423 at 794x1123, because a cropped ground still concentrates its
densest band on a narrower page. So the sheet takes its own value: portrait
steps the strong tier down to .23, which measures 1.38 on the same deck.
brand.md now names the tier strategy in the owner's terms (dense / medium /
sparse), states that a document defines its ripple drawing once and
instantiates it per page, and requires `slice`. The ceiling itself is
unchanged, measured on the rendered page in both geometries — the tiers stay
ceilings on loudness, and quieter is always allowed.

Ridden along, four drift fixes found while auditing: CLAUDE.md and
design-rules §4b said two `check_design.py` metrics gate when D12/D14/D15 are
three; README still credited "the eight semantic icons" from before the Lucide
library landed; and `prompts/lumi-style-core.md` quoted display-tier clamps
that match no token — its `--fs-lead` carried the stat band's numbers — so the
core prompt now restates the four tiers as `tokens/lumi-theme.css` defines
them.

## 0.1.374 — the step called "Visuals and charts" had stopped mentioning charts

A reader compared a deck built by **3.4.0** against one built by **0.1.373** and
called the newer one less professional. They were right, and the gap is
measurable.

| | 3.4.0 (30pp) | 0.1.373 (14pp) |
|---|---|---|
| drawn figure SVGs | **24** | **1** |
| `.fig` blocks holding a drawing | 14 of 14 | **1 of 5** |
| `<text>` inside SVG | **410** | 8 |
| tables | 4 | **0** |
| figure titles stating a conclusion | 14 of 14 | **1 of 5** |

**The skill had not lost the craft.** §4's five chart rules and its complete
form-selection paragraph were untouched; the icon library, the vectors and the
display face all still shipped. The better deck was made with *fewer* rules. What
had changed is where the path of least resistance led, and three things led it:

**`SKILL.md` step 3 was a gate checklist wearing the title "Visuals and charts".**
552 words in which "figure" or "chart" appeared **once** and checker scripts
appeared four times, running 19 forbidding verbs against 10 making ones. Its only
concrete *compose with* instruction pointed at the four HTML block patterns added
in 0.1.369. An agent following it literally lays out and then verifies, and never
draws. Rewritten as **form → draw → compose**, with form selection first, the
shape vocabulary and figure parity stated inline, and **every gate moved to step
4**, where the other pre-delivery checks already live. It now mentions figures ten
times and checkers none.

**The only worked example in the package drew nothing.** `fixtures/deck-pass` was
**11 of 11 rect-only** — three unlabelled rectangles per page, precisely what D5
exists to flag as weak. Its figure now carries an axis, labelled values, a dashed
bar for the class with no measurement, a conclusion in the caption and a source
line. The broken fixture keeps one rect-only figure so D5 still has a subject.

**Twenty-four consecutive releases of brakes.** `brand.md` set this diagnostic at
0.1.345 — 272 restricting lines to 12 inviting, "nearly five times more braked
than the ratio that already produced bland" — and named inverting the order as
the biggest single quality jump on record. Measured today across `SKILL.md` and
`references/`: **431 brakes to 26 invites**. The ratio improved only because
accelerators were added; the absolute braking load grew **59%**, and `SKILL.md`
itself ran 44 to 3. Step 3 now opens by sending the reader to `brand.md` §3,
which it never reached before.

**D5 gains a reported companion: how many `.fig` blocks hold a drawing.** Nothing
in the package could tell a figure from a layout, which is why a deck of HTML
blocks measured clean on every gate. **Reported, never a floor** — a share here
would be satisfied by drawing badly, which is D7's withdrawn fill floor in a new
costume.

**Two findings from the same week, both the class this release is about.** `.say`
ships as `.lead .say` and nowhere else, so a bare `.say` carried the class the
probe audits and none of the type the token file names; a display claim rendered
at body size on two real deliverables and their pages reported as having no entry
point. It joins the scoped-role audit beside `.k`, `.v`, `.no` and `.yes`. And
**`.field`, the brand's signature device, was missing from `inspect_layout.py`'s
ink census** — measured on a real deliverable, both columns began at the same
pixel while the probe reported 339px of skew, because it could not see the field
and found the caption instead. The fixture has never drawn a `.field`, which is
why nobody had looked.

## 0.1.373 — the language guard existed, and it pointed inward

A Cursor run filed a retrospective on 0.1.371 after shipping three reader-visible
defects while `check_design`, `check_prose --genre sales` and `inspect_layout
--deliverable` all exited 0. It is a good note: it declares itself a retrospective
input rather than a patch, refuses to invent subjective floors, proposes
report-first for its weakest case, and lists what not to do. Two of its three
cases land here as gates; the third lands as a report.

**M12 — an English deliverable must be in English. Gates.** This is the sharp
one, and sharper than the note framed it. `references/writing-rules.md` §0 has set
the output language since 0.1.333, and `check_repo.py:check_english_only` has
enforced the identical red line **on this repository's own prose** for as long —
CJK legal only inside backticks, as quoted data. So the package has a working
language guard, pointed inward, and had never once measured the same rule on a
deliverable. A file named `*.en.html`, carrying `lang="en"`, shipped
`已回收 15/15 题` in a page lede and passed every metric in this package.

The exemption is the repository's own: CJK quoted as **data** — `<code>`, `<pre>`,
backticks, fences — is fine, and nothing else is. No allowlist file, because a
name that must appear in Chinese is quoted, and quoting it is a decision a reader
can see rather than a line in a config nobody reads. The language is read from
`--lang`, then the document's `lang` attribute, then the `*.en.*` filename
convention; when none of the three answers, M12 is `n/a` **and says so** rather
than assuming English.

**D15 — no footer may cite a file path. Gates.** A deliverable poured
`resources/…目录-20260730.zh.html` into the footer of almost every content page,
and D6, D12 and D14 all passed it. **This is the second instance of one defect:**
`.foot .src` was removed from `tokens/` in 0.1.366 after the first deliverable to
meet it printed a build path on every client page. Removing the styling did not
stop the span. Two documents is what this repository promotes to a rule.

Deliberately **not** the genre fork the note proposed. Per-page sourcing is
legitimate for consulting and internal analysis, and an English one-line source
there is apparatus rather than a defect a reader sees; what no genre wants is a
path. Banning the path needs no `--genre` plumbed into `check_design.py` and
catches the thing the reader actually saw. The site D12 *requires* and any URL are
not paths, and the check says so by construction: two segments and a file
extension.

**OPENER INSET — reported, not gated.** An opener set its claim hard against the
page edge while the footer stayed inset, so one page read as two left margins.
`frameSkewPx` compares `.foot` to `.body` and cannot see it — proved, not assumed:
on a fixture with the defect inside the body, the new probe reports 92px while
`frame` reports all seventeen pages sharing one width and centre.

Measured **without a vocabulary**. The note proposed keying on `.openframe`, a
class that ships in no token file — keying a probe on an unshipped name is the
reverse drift `check_probe_vocabulary` exists to stop, and it would see nothing on
a document that names the block anything else. Text ink on an opener may not sit
outside the footer's own edges; `.bleed` is excluded, because running past the
content margin is what that shipped class is for. Report-first is the note's own
recommendation and 0.1.372's rule: one deliverable is one case.

**And the fixture had never rendered a part opener.** `.page.opener` has been
styled since 0.1.345, named in `brand.md`, and counted since 0.1.368 — while no
fixture carried one, so the count was always zero and the new probe would have had
nothing to measure. The same trap as the block patterns in 0.1.369. Adding one
immediately broke two probes that were treating an opener as a content page:

- the **datum** counted it, reporting "content starts at 2 different heights" on a
  deck whose fourteen content pages all start at 202px — a true measurement of the
  wrong set. An opener holds no datum for the reason a cover does not: it is a
  composition, and D8 has exempted it from the support-line rule on those grounds
  since that metric was written;
- the **focal** check excluded its title, reporting a page whose title *is* the
  composition as having no entry point. The exclusion now applies only where the
  frame reserves a title block, which asks the layout rather than naming the three
  page kinds.

Both were found by making the fixture exercise a pattern the package ships.

Two things in the note that do not land: `scripts/verify_gates.py` does not exist —
mutation testing here is done by hand, once per guard, when the guard is added —
and `M5` (zh punctuation) remains in the rubric with no implementation, which is
the same class of gap and is not this release.

## 0.1.372 — a recorded no-change: the column-top skew was the probe, not the page

0.1.371 left one question open. Its passing deck had **three of six multi-column
pages out of line by up to 19px** — the skew a reader once called "the left and
right are not level" — and `COLUMN TOPS` is reported rather than gated. One run
is not a retrospective, so nothing changed. This is the second run, and the
retrospective it makes possible ends in **no change**, which the review protocol
lists as one of its three outcomes and which is recorded here rather than left
as a decision nobody wrote down.

**The columns were never out of line.** Measured directly on the first deck,
every cell box on the three flagged pages starts at exactly the same y —
2408/2408, 3848/3848, 6008/6008. All three findings come from where the **ink**
begins inside those identical boxes:

| page | left cell | right cell | reported |
|---|---|---|---|
| p4 | a filled panel: fill at the box top, first glyph 24px in | SVG drawing starts 6px into its viewBox | 18px |
| p6 | plain `.listhead` text at the box top | SVG drawing starts 17px in | 17px |
| p9 | a bordered `.card` at the box top | SVG drawing starts 6px in | 6px |

Two structural causes, both legitimate: a **painted** block whose visible edge is
the line the eye reads while its first glyph sits inside its own padding, and an
SVG whose drawing begins a few pixels inside its box.

**And it does not recur.** A second deck, same agent, same prompt, same CLI
version: four multi-column pages, **all level**. The check ran and found nothing,
so this is not the absent-subject trap — the skew depends on whether a painted
block or a drawing happens to land at the top of a column, not on whether the
composition is correct.

**So `COLUMN TOPS` stays reported.** Gated, the first deck would have failed on
three findings a reader would call level while the second passed — a gate that
flips on composition rather than on correctness is a gate people learn to route
around. That is the same argument that withdrew D7 in 0.1.340, arriving from the
other side.

**The probe is not changed either, and that is the harder call.** The diagnosis
above suggests a real refinement — when a cell's first element paints a
background or a border, its *edge* is the alignment reference, not its first
glyph. `inspect_layout.py`'s hard-won rule is *ask the ink, never the box*,
written because a grown SVG box reported 0px skew on six visibly crooked pages;
that rule is right for an unpainted box and backwards for a painted one. But this
repository promotes a lesson to a rule **once it has appeared across two
documents**, and this one appeared in one. A probe that has caught 132px of real
skew is not reshaped on a single deck's false positives.

Neither deck is defect-free, and the record should say so: the second carries its
own reported finding — one of its two tables holds prose rather than values.
Neither observation is about the rules.

## 0.1.371 — the first CLI-driven agent through the harness, and the board that erased it

Five releases sharpened the instruments. This one points them at something.

**Claude Code `2.1.226`, headless, through all three tasks.** Run with `claude -p`
in a working directory **outside this repository**, deliberately: run it inside
and the agent reads this repo's own `CLAUDE.md`, which is maintenance
instructions for a rules package and not guidance for producing a deliverable.
The only thing steering it was the skill.

**All three pass.** T1's twelve-page deck clears every design metric including
both gates, every prose metric its genre grades, and **all seven `--deliverable`
findings**. T2 clears the banned-phrase requirement it declares. T3 recalls 5 of
5. That is the first row on the scoreboard earned by a CLI rather than driven by
hand, and it is the first evidence the package's central claim has ever had.

Read as evidence, and the caveats in `run_conformance.py`'s own docstring
govern: one run, one CLI version, one machine, one date. A green row means the
artifact is well-formed and free of the defects we can express as arithmetic. It
does not mean the deck is good — but the contact sheet was read, and the two
pages where the Grok deliverable failed hardest are the two that came back
right: the cover is set in the display register with the wordmark and the
attribute strip, and the closing carries the H1–H6 scoring table, the colophon
and the version stamp.

**Recording it nearly erased the run before it.** `report` built the whole board
from a single `--run` directory, so publishing Claude Code turned Cursor's row
from a measured `fail` into `not installed` — a result that was taken reading as
one that was never taken, in the document whose closing paragraph says absences
are listed rather than omitted. `--run` is now repeatable and merges, later
winning on a collision so a re-run replaces its own cells and nobody else's.
`run` and `score` still act on one directory and say so rather than silently
taking the first.

**One observation that is not a rule change, because one run is not a
retrospective.** The deck passes every gate and still has **three of its six
multi-column pages out of line by up to 19px** — the column-top skew a reader
once described as "the left and right are not level". `COLUMN TOPS` is reported
and not gated, decided that way in 0.1.368, and this run is the first evidence
either way. It cuts both ways: a bordered callout at the top of a column
legitimately starts its ink lower than plain text beside it, which is exactly
what happened on this repository's own fixture in 0.1.369. Whether the gating set
should grow is a judgement, and it needs a second case.

## 0.1.370 — the general form of the last three releases, as two guards

0.1.369 fixed seven font-sizes that existed only inside a media query. This one
asks the question underneath: **why was that state reachable at all?**

**`check_media_only_rules`.** No class may be styled only inside a `@media`
block. A rule that exists in one geometry and nowhere else is a rendering the
package half-ships — the document gets `tokens/`'s value on the sheet and
whatever it invented at 1280 — and it is invisible by construction, because the
consistency audit run at the design geometry finds nothing to compare. One honest
exception, waived with its reason: the landscape/portrait figure pair, where a
figure is drawn twice and each geometry hides one. That is what those two classes
*are*.

It found three things 0.1.369 had left:

- **`.tight` meant nothing at 1280.** The only rule reading the modifier lived in
  the portrait block, so a document adding the class saw no change at the design
  geometry and a quiet one on the sheet. It now tightens spacing in both, and the
  fixture uses it.
- **`.grades` and `.gr .gc` are removed rather than completed.** Neither had a
  base rendering, `references/` never named either, and no fixture drew one —
  three orphan declarations styling a block this package does not ship.
  Inventing a graded-criterion design to justify them is the speculative
  rule-making CLAUDE.md rule 2 forbids.
- **`.body.cover-grid` is removed.** A *sixteenth* layout, declared only in
  portrait, missing from the token file's own "fifteen page layouts" header,
  missing from §3's selection table, and missing from `check_design.py`'s
  `LAYOUTS` — so D9 read a page using it as using no shipped layout at all.

**`check_layout_parity`** keeps that last one from recurring: the layouts
`tokens/` defines and the layouts `check_design.py` grades are one list, checked
in both directions.

**And the vocabulary guard was reading one caller of two.** `check_prose.py` keys
on class names too — five `(wrapper, item)` pairs it counts as enumerations for
M10 — and 0.1.368's guard never looked at it. Widened, it immediately named
`.grades`, `.gr` and `.gloss` as asserted-and-unshipped. All three are **census**
assertions in the 0.1.368 sense: they ask to be counted, not to be rendered, so
they are waived with a reason rather than given a design. *A guard that covers
one of two callers has a blind spot the shape of the other.*

**That widening also found a live bug.** The tuple matched every item as
`class="…item…"`, and a glossary's items are `<dt>` **elements** — so the
`("gloss", "dt")` pair counted zero on every definition list ever written, and
M10 silently sampled one enumeration shape fewer than it claimed. The pair now
says which kind each item is; measured on a three-term glossary, 0 became 3.

## 0.1.369 — the portrait block stated the rule and broke it in the next twenty lines

`tokens/lumi-layouts.css` carries this, above its portrait overrides:

> What tightens here is SPACING, never the type of a named role… a page that no
> longer fits gets its CONTENT trimmed, never its type nudged.

**Seven rules immediately below it set a font-size.** `.notes li` at 12px, a notes
table at 11.5px, `.key` at 12px, `.no`/`.yes` at 12px and 11.5px, `.ledname` at
18px, `.card dd` at 12.5px — and **not one of those classes had a base rendering
anywhere in `tokens/`**. The portrait value was therefore the only value the
package shipped: every one of them rendered one way at A4 and whatever a document
invented at 1280. One role, two renderings, from the file that carries the rule
against them. Eighteen releases, and the same trap that caught `.gd` in 0.1.350.

0.1.368's probe-vocabulary guard is what surfaced it, by asking a question nobody
had asked: what does `tokens/` actually *ship*? Twelve waived class names turned
out to be four repeating block patterns that this package has audited for four
releases and never rendered.

**All four now ship a base rendering**, and every size is an existing tier chosen
by what the thing is rather than invented — block body text is `--fs-fig-title`,
the size `.gd` has occupied since 0.1.350 and the same voice; a card's name is
`--fs-support`; a vow's number is `--fs-fine`. No new token, because a new tier is
a design decision and nothing asked for one.

- **tier-1 callout** — `.key`, and `.red` for a red line. `check_design.py` has
  named both as `TIER1_CLASSES` since D3 was written while `tokens/` shipped
  neither.
- **card** — `.card`, `.ledname`, `.verdict`, and the `dl`/`dt`/`dd` inside it.
- **swap** — `.swap` with `.no` and `.yes`, scoped for the reason `.band .k` is:
  those are the two most collidable class names in the vocabulary. Scoping them
  means auditing outside the scope, so they join the unscoped-role audit.
- **vow** — `.vow` with `.vn`, `.vt`, `.vw`.

**`.duo` too**, found the same way from the other end: its base grid existed only
inside the media query that collapses it, so at the design geometry it was a plain
block and its children stacked — 12px past the footer rule on the first fixture
page to use one. *A container that exists only in the geometry that undoes it is
the same defect as a font-size that exists only there.*

Every text role here carries `margin: 0`, for 0.1.367's reason: a role is one
rendering **including its box**. Measured on the vow grid before the fix — 30px
between a vow's title and its body where the block asks for 6.

**The fixture used none of these blocks**, which is why the defect could sit
still for eighteen releases: nothing in this repository ever rendered one. Four
pages now do — a `sidebar-notes` page with the callout and two swaps, a `stack`
page of cards, a `stack` page of vows, and a red-line callout on a fourth. It
also exercises `.lead.row`, which nothing had rendered either.

**Both fixture pages overran, and `--deliverable` said so before anything was
committed** — 44px past the footer rule at 1280 and 135px at A4. The rule for a
page that does not fit is that its *content* is trimmed, so the content was
trimmed: a page about four commitments does not also carry a bullet list and a
display number. That is the gate shipped in 0.1.368 doing its job on this
repository's own work, one release later.

**And moving a fixture page broke a planted defect.** Page 5 became a cards page
with no `.gd`, so the D4 literal-colour plant vanished with it and D4 came back
`ok` on the fixture whose job is to make it fire. `check_fixtures.py` caught it.
*A defect that stops being planted is indistinguishable from a check that stopped
working.*

Still not shipped, and recorded rather than invented: `.grades`/`.gr`/`.gc` and
`.body.cover-grid`, which have the same portrait-only shape but set no type — and
`cover-grid` is a sixteenth layout absent from `check_design.py`'s `LAYOUTS`.

## 0.1.368 — a gate nothing invokes is not a gate

Three releases of finding defects the instruments could not see, and this one
turns the instruments on. It closes the vocabulary class and makes the one tool
that renders a page able to fail.

**`check_probe_vocabulary` — the reverse-drift rule, mechanized.** A probe that
keys on a class name is asserting a vocabulary, and this repository has shipped
that defect three times: 0.1.349 audited ten roles against six names that
appeared nowhere in `tokens/`; 0.1.361 shipped `.cap .srcline` and not
`.foot .src`, so a comparison between them could never run; 0.1.366 found
`.cover h1` and `.closing h2` audited as two of three title registers and shipped
by nothing. The guard reads `inspect_layout.py` with `ast.parse` — never by
importing it — and separates two kinds of selector:

- **contract** (`ROLES`, `SCOPED`) claims a role renders exactly one way. A claim
  about rendering must have a rendering behind it, so these **may not be waived**.
  All of them resolve today, which is what 0.1.366 and 0.1.367 bought.
- **census** (`INK`, `TSEL`, `DSEL`, `CENTER`) asks only to be counted and
  over-reaches on purpose. Twenty-two of these ship nowhere, each now listed in
  `PROBE_NOT_SHIPPED` with a written reason.

**Shipped means a BASE rendering.** Seven of those twenty-two — `.key`, `.red`'s
partner, `.card`, `.swap`, `.vow`, `.no`, `.yes`, `.ledname` — are styled by
`tokens/lumi-layouts.css` **only inside the portrait media query**, which tightens
a font-size the file never declares at 1280. The stylesheet overrides a rendering
it does not ship. Accepting a media-query appearance as "shipped" would have let
the guard report the vocabulary complete on the strength of a portrait override,
so it does not. Those base renderings are a design decision and are not invented
here (CLAUDE.md rule 2); the guard records the debt where the next reader will
find it.

**`inspect_layout.py --deliverable`.** Its design judgements still gate nothing —
that is `SKILL.md` rule 4 and D7's withdrawal, and it stands. What gates is the
subset that is **decidable rather than aesthetic**: collision, content spill,
page height, hidden content, an overspent title reserve, a role split, a lost
datum. Focal weight, column balance, caption distance, centerpiece scale, empty
band and the new part-opener count stay reported, because the fix for each is a
design decision and a number satisfiable without improving the page ends the
looking. Without the flag, behaviour is unchanged. Every predicate is defined
once and read twice — by the report and by the gate — because a gate that
disagrees with the text printed above it is worse than no gate.

**Part openers are reported, never floored.** `.page.opener` has been styled in
`lumi-layouts.css` and named in `brand.md` while nothing required, reported or
checked it, so a deck with six read identically to a deck with none. How many
part divisions a document wants belongs to its storyline; a minimum here would
grow openers to satisfy the number.

**The harness had never run the instrument that renders the page.**
`run_conformance.py` scored prose and design only. `layout` joins `SCRIPTS`, runs
with `--deliverable`, and `T1-deck` gains it — along with `D14_placeholders`,
`collision` and `content_hidden` in its `require` block. A task naming a scoring
kind nothing can run now fails validation instead of raising `KeyError` halfway
through a scoreboard and discarding every row already graded.

**And `--json` was the mode whose exit code lied.** All three report functions
*return* what they could not measure, and `main()` called them only when not
emitting JSON — so the machine-readable mode, the one a harness consumes, counted
zero unmeasured checks forever. Measured: a deck with three `NOT MEASURED` lines
exited **0** under `--json` and **1** without it. The functions now always run
and their output is swallowed instead. "A check that did not run is not a check
that passed" cannot be true only in the mode a person is watching.

**Re-scored, and the transition is the evidence.** The recorded Cursor run moves
from `pass` to `fail (design exited 1, layout exited 1, D14_placeholders=FAIL,
collision=FAIL)`. Five of the seven layout findings fire on it — collision,
content spill, an overspent reserve, a role split and a lost datum — on an
artifact this repository had already published as conformant.

**One near-miss worth recording, because it nearly shipped a gate people would
learn to ignore.** The hidden-content check first flagged **26 of 30 pages** of a
real deliverable, every one of them the eyebrow's `<svg class="ic">`: SVG carries
`overflow: hidden` from the UA stylesheet, and an icon is not text however close
to the title it sits. Scoping it to text-bearing, non-SVG boxes then swung too
far the other way — asking for an element's *own* text nodes excused the `.lede`
container, which is exactly where the clamp that deleted three title lines sat.
It asks for text anywhere beneath a non-SVG box. **A gating finding has to be
falsified in both directions**: once that it fires on the defect, and once that
it stays quiet on a clean document. The first version passed the first test.

## 0.1.367 — the overlap was a reserve overspent, and the fix hid the text

The overlapping text on the Grok 4.5 deliverable turned out to be one page, one
rule, and one wrong answer to it. Its closing page was authored as a **body**
page, so it inherited the title reserve meant for content pages; its title ran to
four lines in a two-line reserve; and `lumi-layouts.css` states the rule in the
direction that matters — *a title needing three lines does not get a taller
reserve, it gets shorter text.* The agent added `-webkit-line-clamp: 2;
overflow: hidden`.

**Three of four title lines and the tail of a support sentence never render.**
Deleted content on a client page, and **every geometric probe in this package
passed it**: clamped text produces no spill, no collision and no page overflow.
The rule was right and the agent broke it — but the skill gave it no way to find
out.

Two signals, both measured on the rendered page and neither keyed to a class
name:

- **the reserve is overspent** — what a `.lede`'s children need against what the
  block reserves;
- **content is being hidden** — a clamp or a hidden overflow inside one, which is
  never legitimate there.

A deep diagnosis had proposed comparing `scrollHeight` to `clientHeight` element
by element. **Verified before acting, and it is wrong**: `h2.t` is a 35px box
holding 42px of ink, because `--fs-title` resolves to 34.56px against a
line-height of 1.02. That is the tight leading this design uses on purpose, and
such a check fires on every correctly-set title in the system.

**Then the probe found the defect in the package that ships it.** Run on this
repository's own fixture it reported ten of fourteen title blocks over their
reserve, by 31px each. `.body .lede` declares `gap: 10px` and `justify-content:
flex-start` — the `+ 20px` in the reserve formula is two of those gaps — and
neither had applied for four releases, because `.body > div:not(…)` reaches
(0,7,1) against this rule's (0,2,0). The named roles also carried the UA's `<p>`
margins: `<p class="eyebrow">` and `<p class="sup">` added 58px the formula never
knew about, a third of the block. **A role is one rendering including its box.**
Both fixed; `.eyebrow`, `.sup`, `.listhead` and `.gd` now ship `margin: 0`, and
the column-top skew on the fixture went from 12px to zero as a side effect.

Adding `:not(.lede)` to that fill rule then broke the multi-column rule that
depends on carrying one more class than it — column skew jumped from 12px to
107px inside one edit, and the probe caught that too. **Fifth time this chain has
quietly decided an argument.** Both chains now carry the exclusion.

**`--accent` was referenced by `tokens/lumi-layouts.css` and defined in neither
token file.** The semantic accent has been `--acc` since the palette existed, so
the footer origin line and the emphasis inside a display number inherited
whatever colour sat above them. Same shape as the `var(--display, var(--sans))`
defect fixed in 0.1.352, and a name read out of a deliverable's private CSS.
`check_repo.py` gains **`check_token_references`**: every `var()` in `tokens/`
must resolve, recursively through its fallbacks, or be waived with a reason.
That is half of what 0.1.366 promised for this release — the custom-property
half. The class-selector half, `check_probe_vocabulary`, moves to 0.1.368
because the overlap diagnosis took priority.

**A scoped role audit hides its own subject.** `.band .k` and `.band .v` report
"one rendering" on a document whose `.k` and `.v` render five ways each, every
one of them outside a band, where `tokens/` says nothing and the author
necessarily invented the rendering. The scoping is not the error — a band value
and a lead value are two roles on purpose — reporting only the scoped uses is.
Uses outside the shipped scope are now counted and named.

**D14: no slot the author left for themselves may reach the reader.** The
deliverable shipped four `[TO FILL]` markers on its closing page, beside its own
callout saying they must not ship. It **gates**, for D12's reason: it is not a
judgement about whether a page is well made, it asks whether the document is
finished, and that is decidable. Nothing else could see one — a placeholder is
not a banned phrase, not a colour, and occupies exactly as much room as the text
that should have replaced it. Bracketed ellipsis is deliberately not a marker.

**And `check_design.py`'s own summary was a lie by construction.** It counted
rows whose verdict was `"note"` — a value `grade()` has never produced — so the
counter was always zero and the last line of every run read **"nothing flagged"**,
including under a report carrying two FAIL rows. That is the exact sentence
quoted at the top of the 0.1.366 entry as evidence that every instrument in this
repository passed a broken document. The instrument was not wrong about the
metrics; it was wrong about itself. A summary is a claim about what is above it.

The fixtures carry both halves: the broken deck now plants a `[TO FILL]`, and the
footer drops the `.src` span that 0.1.366 removed from the token file and left
behind in the reference implementation of its own rules.

**Verified on the real deliverable**, at each stage: `check_design.py` moves from
`nothing flagged`, exit 0, to `D14_placeholders FAIL` on three named slots, exit
1. Both fixtures were re-run at all three geometries with no new `NOT MEASURED`
and no verdict change except the intended ones — the column-top skew closing to
zero and the collision on the broken deck's overlong support line disappearing,
both consequences of the margins the roles now own.

## 0.1.366 — the fixture was never loading the stylesheet it was testing

A deliverable built in Cursor with Grok 4.5 came back with its cover and closing
set in the wrong face, an internal build path printed in every page footer, and
page numbers wrapped onto their own line. **`check_design.py` reported "nothing
flagged" and `check_prose.py` reported "all metrics pass", both exit 0.**
`inspect_layout.py` found six real problems and exited 0 too, because design
judgements gate nothing — and `run_conformance.py` never runs it at all. Every
instrument in this repository said the document was fine.

**The fixture inlined the `:root` block and reimplemented everything else.** Its
own `.body.split`, `.lede`, `.eyebrow`, `.sup`, `.listhead`, `.gd`, `.band`,
`.lead`, `.cap .n`, `.foot` — every one of which ships in `lumi-layouts.css`. So
the shipped layout stylesheet **was never loaded by anything in this
repository**, and its gaps were invisible by construction. A fixture that
reimplements what it is testing is testing itself. It now inlines
`tokens/lumi-layouts.css` in full and keeps only what a document legitimately
decides for itself.

Three gaps that had been hiding behind it:

**`.foot` never got `display: flex`.** `.foot .site` has carried
`margin-right: auto` since the footer existed — a property that does nothing
outside a flex container. The rule was inert, the spans ran inline, and the page
number wrapped. Shipped now.

**`.cover h1` and `.closing h2` appeared zero times in `tokens/`**, while the
consistency probe has audited them as two of its three title registers since
0.1.352. A deliverable wrote its own, without a `font-family`. The audit called it
clean, because **one rendering is what it checks and one rendering is what it
got** — consistency is not correctness. Both registers ship now.

**`.foot .src` is removed.** It shipped in 0.1.361 with styling and no rule about
what it was for, and the first deliverable to meet it filled every client page
with a source path and three processing dates. `design-rules.md` already says
sales and marketing state provenance once for the document, in the closing
colophon; a per-page source slot contradicted the rule and existed only because a
probe compared against it. The source-echo audit now compares a figure's source
line against the document colophon. **Shipping an asset with no rule is the mirror
of CLAUDE.md rule 5, and costs the same.**

This is the third instance of the same class — 0.1.349 audited ten roles against
six unshipped names, 0.1.361 shipped one half of a compared pair — and the pattern
is now explicit: **the skill has been auditing a larger vocabulary than it ships.**
0.1.367 mechanizes the check that stops a fourth.

## 0.1.365 — the task said what it was and nothing carried the word to the checker

Cursor's twelve-page deck failed `M9_dashes` on two em-dashes in a term-and-
definition list. `references/writing-rules.md` 8 bans the dash in **sales and
marketing** deliverables and says in the same breath that it *"does not bind
internal analysis documents"*. T1 has called itself an internal analysis deck in
its title since the day it was added.

**The harness never passed the genre.** `check_prose.py` has taken `--genre` since
it was written; `score_checks` built its argv without it, so every deliverable
this scoreboard has ever graded was graded as sales material whatever it was. A
task could declare its nature in a title and in no way that reached the checker.

Genre is a field now, `score_checks` passes it, `load_tasks` rejects a genre
`check_prose.py` does not accept, and it is part of the run fingerprint — it
changes the verdict, so a run scored under a different genre is stale rather than
comparable. Cursor's deck, graded as what the task says it is: **three of three
pass**, with M11 at 58.3 against a 60 ceiling — the first time that metric has
been exercised by any agent, because the six-page version of this task could never
reach its eight-title floor.

This is the third defect the Cursor run has found, and none of the three was
Cursor's: an em-dash placeholder in a table cell, a task shorter than the floor of
the metric scoring it, and now a genre that existed only in prose. **We had never
run these checkers against output we did not write**, and every fixture in the
repository was authored by the hand that authored the checks. Each of these was
invisible to a suite that only ever read its own homework.

## 0.1.364 — a result is a result of a question, and the question had changed

0.1.363 recorded Cursor at three of three, and in the same release changed T1 from
six pages to twelve. The scoreboard went on showing the six-page `pass` with
nothing to indicate it was answering a prompt the repository no longer contained
— and the change was not cosmetic, since twelve pages move M11 from ungraded to
graded. The recorded verdict was for a strictly easier task than the one on disk.

`score` now fingerprints **the prompt the agent was actually shown**, read from
the `PROMPT.txt` in the run directory, and `report` marks a cell
`stale: task changed` when that fingerprint no longer matches the task. A stale
cell is neither a pass nor a failure; it is a result that has to be re-earned.

Fingerprinting the *task* rather than the prompt was the obvious first cut and it
was wrong: scoring re-reads the artifact from disk, so hashing the current task
stamped a fresh fingerprint onto an old answer and called it current — the six-page
deck went on reporting `pass` against the twelve-page task. The hash has to come
from the question that was asked, not from the question being asked now.

Only fields that can change a verdict are hashed: `prompt`, `deliverable`,
`score`, `require`, `answers`, `input`. `title` and `note` are documentation, and
rewording them must not invalidate a run — verified in all three directions.

Cursor's T2 and T3 still read `pass`; those tasks are unchanged and their results
stand. T1 reads `stale`, which is the honest state until it is re-run.

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
