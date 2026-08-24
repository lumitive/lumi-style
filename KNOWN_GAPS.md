# Known gaps

The queryable ledger of known defects and unclosed verification gaps in this
package. One entry per gap, machine-checked by `check_repo.py`'s ledger guard:
ids unique, statuses legal (`open | fixed | declined`), `fixed` entries name
the closing release (whose CHANGELOG entry must cite the id), `declined`
entries carry a reason. Deferred work goes to `backlog/ideas-prd.md`
(IDEA-ids); recurring failure *shapes* go to `FAILURE_MODES.md` (FM-ids);
this file holds concrete, current gaps.

Tracked bugs live here, not in code comments — a `TODO` in a script citing a
GAP id fails CI. (The lumi project's KNOWN_GAPS rule, adopted 0.1.422.)

## GAP-001 · T1-deck fails on both scored conformance agents

- status: fixed
- opened: 0.1.422
- closed: 0.1.434
- surface: conformance/CONFORMANCE.md, references/storyline-templates.md,
  scripts/check/check_prose.py, tokens/lumi-layouts.css (historical)
- symptom: both agents ever scored (Claude Code, Cursor) fail the T1-deck
  task. DIAGNOSED at 0.1.433 by reproducing every verdict: the dominant
  failure (collision, both agents) was the skill's own window-keyed media
  block in tokens/lumi-layouts.css — both decks copied it verbatim — removed
  at 0.1.380, AFTER the decks were built; the instruments that see it
  (0.1.368/0.1.385/0.1.390) also postdate the builds. Two live skill defects
  found and fixed at 0.1.433: the [TO FILL] template-vs-D14 contradiction
  and M6 counting enumeration labels as ranges. The five remaining findings
  are agent-capability (unfit title reserves, inline role overrides, an
  overfull closing page shipped against the agent's own screenshot, a
  1-unit descender clip, one unsourced page).
- check: EXECUTED 2026-08-13 — T1 re-run on both agents against the 0.1.433
  rules: Cursor hand-driven by the operator (pass), Claude Code driven clean
  with the skill (pass; T2/T3 also pass). Scored with run_conformance.py,
  recorded via report --record (history rows pin skill 0.1.433); the
  scoreboard renders the current-skill runs and names the superseded ones.

## GAP-012 · `visual_absent` cannot see a table, and five of six flagged pages are tables

- status: fixed
- opened: 0.1.489
- surface: scripts/check/inspect_layout.py, the `VIS` selector list in the page probe
- symptom: the gate reads visual presence from a CLASS LIST —
  `.fig, .band, .lead, .swaps, .vows, .duo, .grades, .field` — so a page whose
  argument is carried by a ruled comparison table with a highlighted row counts
  as carrying **nothing visual at all**. A 15-page internal proposal failed the
  gate on 6 of 11 content pages; **five of the six carry substantial tables**
  and one (p12) is genuinely empty. Screenshots of both are in
  `_layout/…0.1.489.r2…-p8.png` and `-p12.png`: the gate is right about p12 and
  is measuring a vocabulary rather than the page on p8.
- why it is not simply widened: whether a table is visual is a **design-language
  decision, not a bug**. Counting tables makes the gate weaker — 0.1.339's fill
  floor was met by stretching table rows, which is exactly this move — and not
  counting them fails every table-driven analytical document. The owner decides
  which, and the decision belongs in `references/design-rules.md` before it
  belongs in the probe.
- this is the hazard CLAUDE.md names: a probe keying on class names asserts a
  vocabulary, and that vocabulary has to ship in `tokens/` or it is borrowed
  from whatever document the probe was developed against. It was calibrated on
  two documents.
- check: once ruled, the probe reads the ruling, and a synthetic fixture with a
  table-only page asserts the chosen verdict in both directions.
- closed: 0.1.491
- resolution: **the rules had already ruled it; no owner decision was needed.**
  `references/design-rules.md:539` reads "comparisons still take tables, a table
  is still for values and never for what a chart says better, and **a table page
  still wants its visual weight from a figure or a band beside it**". So
  `visual_absent` agrees with §4: a table alone is not the page's visual weight,
  and the five flagged table pages are owed a figure or band BESIDE the table —
  never a shape replacing it. The probe is not widened. What this gap actually
  found is that the rule was written and the deliverable did not follow it,
  which is a document defect and is fixed in the rebuild.
- the class-vocabulary worry that opened this entry was mistaken and is recorded
  so nobody re-opens it: the eight selectors are not in `tokens/lumi-theme.css`,
  but `scripts/ops/new_deck.py`'s preamble defines all eight among its 211
  classes, and the scaffold is what a deliverable is built from.

## GAP-032 · `correlate` is in the move vocabulary and in no framework

- status: open
- opened: 0.1.589
- surface: assets/frameworks.json, references/analysis-rules.md
- symptom: the five analytical moves are compare, decompose, position,
  **correlate** and bridge. `assets/frameworks.json` carries frameworks for
  four of them — `correlate` has no entry at all, so `new_deck.shape_for
  ("correlate")` returns nothing and a page declaring it arrives with an empty
  figure slot while its four siblings arrive with a shape.
- found by: making D32 per-page (0.1.589). A page declaring `correlate` would
  have failed the new gate through no fault of its author, so the gate holds a
  page only when its move is one the library can draw — and the exemption is
  printed, which is how this became visible.
- why it is not simply filled: which framework draws a correlation is a design
  question (scatter with a fitted line? a quadrant with two measured axes? a
  matrix?), and inventing one to close a gap is convention 6's warning. It
  needs the same treatment the other four had: a question, a framework, a
  shape, and a misuse note.
- check: `D32_shape_use` prints `<move> not held (no framework in
  assets/frameworks.json names a shape)` for every such move it meets

## GAP-030 · Red line 5 asks every figure for a source line and nothing reads it

- status: open
- opened: 0.1.587
- corrected: 0.1.589 — **the entry's evidence was written backwards.** It said
  "ten figures, zero `.cap .srcline` elements", as though the absence of a
  source line in the caption were the defect. Zero is what D37 REQUIRES: the
  source is the drawing's own last text node (design-rules section 4 rule 17),
  and D37 gates a caption that carries one. The conclusion held; the evidence
  named the wrong thing, which is convention 14 in the ledger this repository
  keeps to catch exactly that.
- surface: scripts/check/check_design.py, scripts/check/inspect_layout.py,
  tokens/lumi-layouts.css
- symptom: restated correctly at 0.1.589 — two measured deliverables carry a source
  **nowhere** — not in the caption, where D37 forbids it, and not inside the
  drawing, where rule 17 asks for it. Red line 5 says every figure carries a
  source line and no check looks in the place the rule names.
- and the two halves contradict each other: `inspect_layout` looks for a source
  by pairing `.cap .srcline` with the colophon — the arrangement D37 gates
  against — so a document that follows the rule reports `source: NOT MEASURED`.
  `tokens/lumi-layouts.css` still styles `.cap .srcline`, which is the third
  copy of the disagreement. Since 0.1.588 an absent subject no longer fails the
  run, so this costs a reading rather than a release; the contradiction remains.
- why it is not simply gated: a figure that states no data arguably owes no
  source, so the population is "figures that state a number", which is D29's
  question and D29 reports. Needs a real-instance sweep before the pattern is
  written (convention 15).
- check: none

## GAP-031 · A deck can delete its takeaway rung and every gate stays green

- status: open
- opened: 0.1.587
- surface: scripts/check/check_design.py D28, scripts/check/check_outline.py
- symptom: `new_deck.py` seeds every content page with a `.take` line; a
  2026-08 build emitted **ten content pages and zero `.take` elements**, having
  substituted the tier-1 `.key` callout on five of them and nothing on the other
  five. D28 is `n/a` for the internal genre, so it said nothing.
  `check_outline --against` DID report "10 of 10 planned implications are not in
  their page's takeaway" — the right finding, in a line that reads as a note.
  AR-2's implication rung was deleted wholesale and the document was green.
- why it is not simply gated: `.take` is required of EXTERNAL content pages, and
  the genre exemption is deliberate. What is not deliberate is that an outline
  declaring an implication for every page can lose every one of them without a
  gating verdict. The candidate is on `check_outline --against`: a planned
  implication that reached no page at all, in any element, rather than only "not
  in the takeaway".
- check: none (check_outline reports it)

## GAP-029 · `gating.py` read one checker's convention into the other

- status: fixed
- opened: 0.1.557
- closed: 0.1.559
- surface: scripts/lib/gating.py, scripts/check/check_prose.py,
  scripts/ops/check_deliverable.py, scripts/ops/run_conformance.py
- symptom: **the asymmetry itself was never the gap and was never news** —
  `tests/test_m13_reported.py` had asserted it since it was written: in
  `check_design` the `(gates)` marker IS the mechanism, in `check_prose` any
  failing row exited non-zero and the marker on M12 was emphasis. The gap was
  the consequence for everything reading `gating.py`, which applies the design
  convention to both. `gating.metric_ids("M")` returned `{M12}`,
  `run_conformance`'s `all-gating` block demanded nothing of the rest, and
  `check_deliverable` printed them as `note` — beside an exit code that failed
  the build on them. Measured on `fixtures/deck-degenerate.en.html`:
  check_design exited 1 with 7 of its 13 failures marked; check_prose exited 1
  with 0 of its 6.
- resolution: the owner chose the split on 2026-08-22 and it is now one
  sentence rather than a list: **a prose row gates if and only if its target is
  zero and it does not say `(reported)`.** M4, M4zh, M5, M6 and M9 join M12;
  M2, M8, M10 and M11 are graded, and M1, M13, M14 and M15 stay reported.
  `check_prose` exits on its gating failures the way `check_design` does, and
  an unmeasurable document still fails. M9 was not in the recommendation as
  first written and belongs by the rule: its target is zero, and a first scan
  that showed it failing four accepted documents was an artifact of not passing
  their declared `data-genre=internal`, under which every one reads `n/a`.
- check: `tests/test_m13_reported.py` — three tests replace the one that
  asserted the old asymmetry: that the two checkers now express gating the same
  way, that every zero-targeted row gates and no share-targeted row does (read
  from the checker's own report, not from a second list), and that a document
  failing only directions exits zero and says so.

## GAP-028 · A rule drawn in the leading between two text lines measures as no overlap

- status: open
- opened: 0.1.551
- surface: scripts/check/inspect_layout.py (the stroke-through-text arm of the
  `collision` scan)
- symptom: the owner marked three green arrow rules on a conformance deck as
  overlapping the text beneath them. Measured at a 0.5px threshold, the overlap
  is ZERO: the arrows sit at y=80/150/220 and the labels they crowd have their
  boxes starting at y=80, so the strokes run in the LEADING between two lines
  and touch neither. What she is seeing is clearance, not collision — the rule
  has no breathing room above the label, so at reading size it reads as
  striking through it.
- why it is not gated: the discriminating measurement would be a minimum
  clearance between a stroke and a nearby glyph run, and the accepted reference
  carries a legitimate 194x17px rule sitting exactly on a text line (p18, a
  caption rule spanning the line it underlines). Any clearance floor that
  catches the arrows also fails that, and a gate that fails the calibration
  anchor is measuring the wrong thing. The `oy > height * 0.9` guard in the
  stroke arm exists to let the reference's case through.
- what would close it: a second accepted document, so a clearance floor can be
  set from two rather than invented from one — the same condition GAP-024 and
  GAP-025 wait on.
- check: MEASURED 0.1.551 — a probe comparing every `.fig svg` stroked mark
  against every `.fig svg text` box reports 0 overlaps on the conformance deck
  the owner marked and 1 on the accepted reference. Re-run it before setting any
  floor.

## GAP-027 · Documents built before 0.1.552 embed no mono face

- status: open
- opened: 0.1.551
- surface: assets/fonts/, scripts/build/embed_font.py, tokens/lumi-theme.css
  (`--mono`)
- symptom: `--mono` named "IBM Plex Mono", "SF Mono", Menlo and Consolas and
  this package shipped D-DIN and nothing else, so every mono role in every
  deliverable — the cover and closing key column, figure captions, the footer,
  the colophon, the part-opener label — rendered in whatever mono the reader's
  machine happened to have, at whatever that face called weight 700. An owner
  review read the key column as "not bold" twice, five releases apart, on a
  rule that measures as 700 both times.
- what was done at 0.1.552 (owner authorised): IBM Plex Mono Regular and Bold
  are vendored and embedded, under SIL OFL 1.1 — the same licence as D-DIN,
  permitting commercial use, embedding and redistribution. Taken from the
  official `@ibm/plex@6.4.0` package and subset locally to the 254 Latin
  codepoints these roles measurably use: 33.7 KB for the pair against 92 KB
  complete, chosen by measuring every character in a mono role across the
  accepted reference in both languages and a conformance deck, with zero
  misses. `D36_font_family` reads 0 on a deck built from current tokens.
- why it stays open: the documents already on the machine still carry the old
  block. The reference deck reports one unembedded primary (`ibm plex mono`)
  and will until it is rebuilt. `D36_font_family` therefore reports and does
  not gate — a gate here would fail every document produced before this
  release, for a defect that was in the tokens.
- **a second gate now depends on the same rebuild.** `figure_axis_named`
  (0.1.554) fails every figure that scales numbers and names no axis, and the
  classes it wants shipped at 0.1.551 — so the accepted reference fails it on
  10 of its 10 scaled figures and an accepted intro deck on 4 of 4. The owner
  ruled on 2026-08-22 that it gates anyway, knowing the cost, because the
  documents are being rebuilt for the font anyway. **Until that rebuild the
  reference is not the calibration anchor for THIS gate** (it remains the anchor
  for every other one).
- what would close it: rebuild the delivered documents, then promote D36 to a
  gate.
- check: `python3 scripts/check/check_design.py <deck>` prints the D36 row;
  `python3 scripts/build/embed_font.py --check` verifies all four vendored
  files against their recorded sizes and prints their digests.

## GAP-026 · The globe's trade labels overlap by construction and are exempt from `collision`

- status: open
- opened: 0.1.551
- surface: scripts/check/inspect_layout.py (the `svg.gl` filter in the SVG-text
  collision scan)
- symptom: `collision` learned to read SVG text at 0.1.551, and the first thing
  it found was the brand globe. Its signal labels are HS codes printed along
  trade arcs, and on the cover and closing of every deck built with the globe —
  the accepted reference included — five or more of them overlap each other
  (`392310` over `481920`, `392329` over `401693`, and so on). The chain is
  `text -> g.gl-sig -> svg.gl`, so the existing `.ground` filter does not reach
  them.
- why it is exempt and not fixed: the labels are placed by the globe runtime
  from real coordinates, and which ones collide depends on the rotation the
  page happens to render. Gating them would fail page 1 of the document this
  package calibrates every other gate against, for a defect the runtime and not
  the author controls. Exempting them is the lesser wrong, and naming the
  exemption here is what keeps it from reading as "nothing was found".
- what would close it: label decluttering in the globe runtime — suppress a
  signal label whose box overlaps one already drawn, the way a map renderer
  does. That is a change to `scripts/render/` and its JS port, not to the
  checker, and it wants the golden-grid test extended first.
- check: MEASURED 0.1.551 — with the `svg.gl` filter removed, the accepted
  reference reports collisions on its cover and closing and nothing else; with
  it in place, zero collisions on all 23 pages. Re-measure by deleting the
  filter and running `inspect_layout.py <reference> --deliverable --no-sheet`;
  the gap closes when that run is clean without the filter.

## GAP-025 · Figure-structure repetition is measured and cannot be gated on one document

- status: open
- opened: 0.1.546
- surface: scripts/check/inspect_layout.py (`_repeated_figure_shapes`,
  `FIGURE_SHAPE_REPEAT`)
- symptom: the owner reviewed three conformance decks and reported that the
  figures repeat — one design reused rather than a drawing per argument. The
  measurement confirms it: the deck she faulted draws ONE skeleton on four of
  its seven figure pages, against the accepted reference's 21 drawings in 21
  distinct structures and a passing deck's 7 in 7.
- why it is reported and not gated: the reference **also** repeats. Counted by
  page, it reuses one skeleton across p7/p10/p21/p22/p23 — five pages — while
  still carrying 21 structures overall. A ceiling of three pages fails the
  document the owner has accepted; a ceiling of six passes the deck she
  rejected. What separates them is not a count but a SHARE: four of seven
  figure pages against five of twenty-one. One accepted document cannot set
  that ratio, and 0.1.339's invented page-fill floor is what convention 6 was
  written for.
- first reading was wrong in a way worth recording: it counted DRAWINGS, so
  the reference's p4 — four small charts of one kind sitting side by side as a
  single composition — read as four repeats. Counting pages is the fix; the
  remaining disagreement with the reference is real rather than an artefact.
- **0.1.595 built the contradiction form and could not gate it.** The share
  this entry is stuck on can be avoided entirely by asking a question with no
  threshold in it: two pages that declare DIFFERENT analytical moves and draw
  the SAME skeleton contradict themselves. It is now measured — the browser
  probe carries each page's `data-analysis`, which it never did, so the two
  facts needed to ask the question stopped living in different checkers.
  **It does not gate, for two measured reasons.** The two judged documents on
  record — one accepted, one rejected — declare no `data-analysis` at all, both
  predating the convention, so neither can exercise it, and a gate no accepted
  document can exercise is FM-01 waiting to happen. And on the two decks that do
  declare moves, every clash came from a figure that is nothing but text, which
  is the absence of structure rather than a structure two pages share; excluding
  those leaves **zero** clashes on both. So the check has no failing case
  anywhere yet.
- a caution that belongs with the number: that zero is not evidence the drawings
  agree with their declared moves. It is a deck whose figures are almost all
  text blobs — three of one deck's four signatures are 90%+ text. The count is
  recorded beside `text_only_figures` for exactly this reason, because
  `move_skeleton_clashes: 0` alone reads as the stronger claim.
- what it does instead: the count goes into the trace's `shape` block with the
  other readings, so the corpus accumulates one per build and
  `scripts/ops/bar_replay.py` can be pointed at it once documents an owner has
  judged actually carry declared moves.
- check: judged documents that DECLARE their analytical moves. Until then this
  gap is waiting on material, not on a decision — which is a different state
  from the one it was in, and worth the distinction.

## GAP-024 · Layout variety is measured, reported, and cannot fail

- status: open
- opened: 0.1.543
- surface: scripts/check/check_design.py (`D9_layout_spread`)
- symptom: the row's pass condition is the literal `True`. It prints "N
  layouts, top X%" and no value of X has ever failed anything, so a deck that
  runs one layout on every page reads identically to one that varies. The
  owner opened three conformance decks on 2026-08-21 and named this first —
  most pages are the same left/right split, and the deck is not varied enough.
  The metric had already measured exactly that and said nothing.
- what is known, and it is two points: the accepted reference deck
  (LUMI-Commercial-Agent-BP-chengdu.0.1.522.r11) runs **6 layouts, top share
  33.3%**; the deck the owner rejected runs **3 layouts, top share 70.0%**.
  A third, from Cursor, runs 6 layouts at 30.0% and the owner did not fault
  its layouts.
- why it is not gated here and now: a threshold between 33% and 70% would be
  a number invented from one accepted document. This package has done that
  once — 0.1.339's 82% page-fill floor, which a deliverable met by stretching
  table rows and whose reader scored three dimensions at 1 — and convention 6
  exists because of it. `evals/thresholds.json` is where a ratio with an
  `evidence` level belongs, not a design row with a hardcoded constant.
- **0.1.592 tried the bar and the corpus refused it.** Three more documents now
  carry a verdict: two market-analysis decks built from one source at 0.1.591 —
  one faulted by eye for figures that were too small at **64.3%**, one not
  faulted at **28.6%** — and the scaffold's own output, which was emitting
  **71.4%** before that release and **42.9%** after. Ordered, that looked like a
  clean separation with an empty band from 33.3 to 64.3, and a `provisional`
  bar of 50 was drafted into `evals/thresholds.json`. Then it was measured
  against A1, the corpus's own accepted anchor: **78.6%** — 22 of its 30 pages
  are `split`. **A1 is not the deck this entry calls accepted above**: that one
  is the landscape roadshow deck at 33.3%, which uses `split` zero times. Two
  accepted documents disagreeing this hard about one layout is itself the
  finding. **The accepted document scores worse than both documents an
  owner faulted**, so top share does not order these documents by quality and
  any bar drawn here fails the reference. Scoping the bar to decks was
  considered and declined: A1 is landscape too, and inventing a distinction to
  rescue a number is the move convention 6 exists to stop. The bar was removed
  and the metric moved to `reported_not_thresholded` with the counter-example
  recorded beside it.
- what 0.1.592 did instead, and it needed no threshold: `new_deck.py` was
  emitting `body split` on EVERY content page — the layout
  `storyline-templates.md` already rules out for a figure-led page. The fix is
  the scaffold obeying a written rule, not a new gate. Visual share on the
  emitted scaffold went from 10 of 11 content pages under target (worst 37%) to
  4 of 11 (worst 46%). The 35% quoted elsewhere is the FIELD DECK's worst page,
  not the scaffold's; the two were merged into one row in a first draft.
- **0.1.595 made the refutation mechanical.** `scripts/ops/bar_replay.py` takes
  a metric and a proposed bar, replays it against every document carrying an
  owner verdict, and reports which ones it would have contradicted. Pointed at
  the withdrawn bar it reproduces the answer this entry reached by hand — and
  finds a second disagreement the hand pass missed: R1, which the owner
  REJECTED, sits at 42.9 and the bar of 50 would have passed it. The bar is not
  merely wrong about A1; it orders these two documents backwards.
- what is still missing is material, not method: only two documents carry both
  an owner verdict and a measured reading. Every build now records its own
  shape (`trace.py`'s `shape` block, reported by `ledger.py`), so the corpus
  grows without anyone remembering to reopen anything — which is the condition
  this entry has actually been waiting on since 0.1.543.
- check: this gap now needs something other than a top-share bar. The open
  question is what property separates A1 at 78.6 from the deck rejected at 70.0,
  given both run one layout on most pages — the answer is probably not variety
  at all, and the gap may be mis-framed. GAP-021's re-baseline of A1 is still
  the material that would settle it.

## GAP-023 · A driven agent's `new_deck.py` runs write build traces into the installed skill

- status: open
- opened: 0.1.540
- surface: scripts/ops/trace.py (`TRACES`), scripts/ops/new_deck.py,
  scripts/ops/run_conformance.py (`drive`)
- symptom: `TRACES` is `LUMI_TRACES` or `ROOT / "evals" / "traces"`, and
  `ROOT` comes from `__file__` — the *install* directory, never the caller's.
  So when a conformance agent runs the scaffold, as the skill tells it to,
  the trace lands in the package rather than beside the agent's work. The
  2026-08-21 run measured it: Cursor's single T1-deck task opened **three**
  `source: build` traces in this repository (17:44:29, 17:45:21, 17:49:01),
  all left open, none of them a build of anything this repository ships.
  Two harms, one mechanical and one statistical. `release.py` stages with
  `git add -A`, so a stranger's traces are one release away from being
  committed as the owner's. And `ledger.py --board` reads every stored trace,
  so an agent's runs enter the efficiency median beside the owner's builds
  and nothing in the file distinguishes them.
- not the same as GAP-022, which is an agent writing its *deliverable*
  outside the working directory. This is the package's own tooling writing
  into the package, and it happens however well-behaved the agent is.
- check: `drive()` sets `LUMI_TRACES` into the agent's environment, pointing
  at the task's run directory, so a driven agent's traces land with the run
  that produced them; and `ledger.py --board` states which store it read.
  The escape hatch already exists and is simply not used on this path.

## GAP-022 · An agent can write its deliverable outside the working directory, and the run records nothing

- status: open
- opened: 0.1.540
- surface: scripts/ops/run_conformance.py (`drive`), conformance/results
- symptom: Gemini CLI's T1-deck run on 2026-08-21 exited 0 after 663.7s and
  its own transcript says the deck was *"written to `deck.en.html` in the
  working directory"*. It was not: the file landed in the **skill directory**
  — `~/.agents/skills/lumi-style`, a symlink to this repository — 571KB of
  finished deck, at the repository root. `drive()` globs the task's
  `deliverable` pattern in the temporary working directory only, so
  `produced` was `[]`, the conformance trace was left open as "the drive did
  not finish", and the board cell reads as an agent that wrote nothing. The
  agent wrote a deck. It also wrote it somewhere a consumer of this package
  would not want it: with the skill path handed to the CLI as a workspace
  directory, "the working directory" is ambiguous to the agent and the
  installed skill is writable.
- **the "no verdict is withheld" line was wrong, and Hermes disproved it
  three releases later.** Written at 0.1.540 from the Gemini case alone,
  where the misplaced deck failed on its own merits (D19_vocabulary 9,
  D6_footer 12, M11_title_uniformity 91.7% against a 60% ceiling) so nothing
  turned on where it sat. Hermes's misplaced T1 deck (2026-08-21) passes
  `check_design` and `check_prose` with no failure and `inspect_layout
  --deliverable` with exit 0 and 136 ok lines — the cleanest artifact any
  agent has produced for this suite — and the board recorded it as an agent
  that wrote nothing. A generalisation from one case, in a ledger entry whose
  whole job is to be read later.
- Hermes's variant is not the same mechanism. Gemini wrote into the installed
  skill believing it was the working directory; Hermes writes every file to
  the user's HOME whatever cwd the driver starts it in. `--in` does not move
  it and neither does `--no-restore-cwd`; a prompt naming an absolute path
  does, so the tool can write there and simply does not resolve "the working
  directory" the way a process's cwd does. Whether that is the agent's defect
  (the task says "in the working directory") or this harness's assumption
  (every other driven CLI honours cwd) is genuinely open, which is why the
  run now names it rather than scoring it either way.
- partially closed at 0.1.542: `drive()` sweeps HOME, the declared
  `skill_paths` roots and this package's root — non-recursively, by mtime
  inside the run window — and records `verdict: misplaced` with the path.
  `score` folds it into `not earned`, so it neither credits the agent nor
  blames it. **The file is never copied in and scored**, which would launder
  a run that missed the task's own instruction into a pass.
- the two boards were separated at 0.1.543, because the first matrix run
  showed the cost of conflating them: two of the first four cells were
  misplaced, contributed no trace, and the matrix the runs existed for could
  not be filled by the runs that were filling it. The conformance verdict
  asks whether the agent did the task AS STATED and the task states the
  working directory, so a misplaced run stays `not earned` there. The cost
  trace asks how many output tokens a model at an effort spent per content
  page, and a file's location cannot change that answer — so it now closes
  against the misplaced artifact. No field of a trace is about location, and
  `ledger.py --board` drops any run with a failing gate before computing
  anything, so nothing is laundered into a pass. A timeout is still refused:
  its file is a draft wherever it sits.
- check: a driven agent whose artifact reliably lands in the working
  directory, or a task contract that states an absolute path and is therefore
  answerable by every agent alike. The 0.1.542 sweep is a report, not a fix,
  and this entry stays open until one of those two exists.

## GAP-021 · The only accepted reference fails a gate introduced after its acceptance

- status: open
- opened: 0.1.534
- surface: evals/thresholds.json (corpus A1), scripts/check/check_design.py (D27)
- symptom: A1 — the one document the owner has accepted, and the calibration
  source for five of the twenty threshold cells — fails `D27_agenda_mirror`,
  a gate shipped at 0.1.514: its agenda paraphrases its part openers
  rather than quoting them. The instrument is right (the paraphrase is
  real) and the anchor is right (the acceptance stands), and the package
  now carries an accepted reference its own gate stack would not ship. It
  cannot be rebuilt to pass without ceasing to be the document that was
  accepted.
- owner ruling (2026-08-20, default taken): **calibration-only**. A1 keeps
  its role for the cells that cite it, its corpus entry says it is not
  shippable under the current gates, and no gate is loosened for it.
  Re-baselining — a document built under the current rules, accepted
  through a blind review, and then replacing A1 in the threshold table —
  is the close condition, and it is the owner's to start.
- check: a second accepted document on the `training` tier (or A1's
  re-acceptance of a rebuilt edition) recorded in `evals/thresholds.json`,
  and the calibrated cells re-derived from it.

## GAP-014 · The cost instrument has never produced a reading

- status: fixed
- opened: 0.1.529
- closed: 0.1.531
- surface: scripts/ops/trace.py (`--phase`, `--usage`), scripts/ops/ledger.py (`--board`), evals/traces/
- symptom: the four-phase clock, the token fields and the model×effort matrix
  all exist, and all nine stored traces carry `phase_seconds = {}`,
  `input_tokens = null`, `effort = null`. `ledger.py --board` reports "0 of 9
  run(s) qualify". K1 of the product definition (six matrix cells with a
  quality and a cost column) has zero cells, and the refactor design's own
  falsification test for the four-beat workflow — "if the four-beat group's
  total usage is not lower than the control group's, its economic argument is
  void" — cannot be run, because no build stamps a phase and no run records
  its effort. The instrument was built and never wired into the loop that
  would feed it.
- check: at least one trace whose `phase_seconds` was written by the tooling
  (not typed), and `run --drive` recording `model` and `effort` per run.
  Closed at 0.1.531: the scaffold opens the trace and starts the build clock,
  `check_deliverable.py` stops it and records its own duration, `run --drive`
  pins `--effort` through a registry-declared flag and reads the API's usage
  from a JSON transcript into a `source: conformance` trace. The six cells
  themselves are an operator step recorded through the evidence gate; until
  they run, `ledger.py --board` still reads "0 qualify", and that is now a
  statement about runs not made rather than about an instrument not wired.

## GAP-015 · Privacy layer 3 is not the designed T3, and says so only in its own docstring

- status: open
- opened: 0.1.529
- surface: scripts/check/check_privacy.py (layer 3)
- symptom: the refactor design specified a third, report-only layer that
  treats the user's supplied source material as an allow-list and reports
  every organisation-shaped proper noun in the deliverable that the material
  never mentions — "catches an invented name, not a name from the wrong
  engagement", stated as anti-hallucination rather than anti-contamination.
  What shipped is a line of text saying layer 3 is not mechanised. That is a
  defensible re-decision (the allow-list check needs the material path as an
  input and the design itself expected early false positives), but it was recorded
  nowhere, so the design reads as delivered.
- check: either build the allow-list report (input: `--material <dir>`;
  output: reported, never gating) with a fixture that fails it, or record
  the decline in FAILURE_MODES' abandoned gates with the reason, and change
  this entry's status accordingly.

## GAP-016 · `check_outline.py` mechanises three of the thirteen outline-stage evidence items

- status: open
- opened: 0.1.529
- surface: scripts/check/check_outline.py, references/eval-rubric.md (`[outline]` tags)
- symptom: the rubric tags thirteen evidence items `[outline]` — runnable on
  a title-only skeleton before the document exists — and the checker
  mechanises three (C2-② label titles, C2-③ group size, C5-① typical
  sections) plus the mirror gate and the analysis-move check the design did
  not ask for. C2-① (read-through) is refused with a written reason. The
  other nine (C1-①②④⑤, C2-④, C5-③④, C6-①②) are neither built nor marked
  as human-only, so the tag promises a machine that is not there. The
  design's rule was "the list changes, the implementation range follows";
  neither direction was kept.
- check: each `[outline]` item either has a predicate in `check_outline.py`
  with a failing fixture, or is re-tagged `[outline · human]` in the rubric
  with one line saying why a machine cannot decide it.

## GAP-017 · The shape library cannot be regenerated from the tokens inside this repository

- status: fixed
- opened: 0.1.529
- closed: 0.1.532
- surface: assets/shapes/, scripts/build/ (no recolour tool)
- symptom: the 206 recoloured units in `assets/shapes/` were produced by a
  tool outside the repository (`_refactor/tools/recolor_lumi.py`, in the
  owner's review directory) from originals that are not vendored. A change
  to a palette token therefore cannot be re-flowed into the library by any
  script a clone carries, and no `--check` holds the committed SVGs to the
  tokens they claim to follow — the only such guard this package has for
  every other vendored asset. The design's step 3 ("move the recolour layer
  into `scripts/build/` and connect it to the token source") was not done
  and not recorded.
- check: a recolour tool under `scripts/build/` reading the token values
  through `css_tokens.py`, the originals vendored beside the output, and a `--check`
  in `ci.yml` that fails on one edited byte. Closed at 0.1.532:
  `scripts/build/recolor_shapes.py`, `assets/shapes/source/`, and the first
  `--check` against the committed library was byte-identical.

## GAP-018 · AGENTS.md grew while the design said it would shrink

- status: fixed
- opened: 0.1.529
- closed: 0.1.536
- surface: AGENTS.md
- symptom: the refactor design's D1 was a substantial slimming of AGENTS.md — the Codex
  entry point restates part of `references/`, is the largest hand-written
  restatement surface in the tree, and has carried withdrawn rules for up to
  four versions before. Across the refactor it went from 210 to 286 lines
  (+95/−19). Nothing holds its length, and the `red line parity` guard holds
  only the six red lines inside it.
- check: the file returns to load order + red lines + capability tier +
  version, citing `references/` for what it now restates, and a guard holds
  its line count to a ceiling recorded beside the guard. Closed at 0.1.536:
  286 → 125 lines, a map of `references/` with section citations; the
  `entry restatement ceiling` guard holds 150.

## GAP-019 · Forty megabytes of unreferenced conformance results were never cleaned

- status: fixed
- opened: 0.1.529
- closed: 0.1.529
- surface: conformance/results/ (gitignored, local)
- symptom: the design's D2 was a P0 item with no dependency — remove the
  fourteen result directories the board does not reference. It was dropped
  from the in-repo plan without a note. The directory is gitignored, so a
  clone never sees it; what the omission cost was the 0.1.522 situation in
  which `results/latest` held a deck from one run under a driver record from
  another, because every drive reused one directory.
- check: closed by 0.1.528's dated per-run directories and cleared task
  directories rather than by a deletion — the mechanism that let one
  directory accumulate several runs is gone, and the old directories are
  the operator's to delete (they are on one machine and in no clone).

## GAP-020 · The trace schema dropped the `feedback` field with no recorded decision

- status: open
- opened: 0.1.529
- surface: scripts/lib/trace_schema.py
- symptom: the refactor design's schema listed `feedback?` as the last
  optional field (a pointer to a reader-feedback record, the N5 channel).
  The shipped schema has no such field and no comment saying why, unlike
  `cost_usd`, whose removal is reasoned in place. The N5 channel itself was
  deferred to the last phase, so the field may have been dropped as
  premature — but a field that was designed, not shipped and not explained
  is the shape IDEA-11 describes.
- check: either add the field as an id-only pointer into a reviews record
  (no free text; the schema guard already forbids it) or write the reason
  for its absence where `cost_usd`'s reason is written.

## GAP-013 · the storyline vocabulary has no entry for a proposal

- status: fixed
- opened: 0.1.489
- surface: scripts/lib/deliverable_registry.py `STORYLINES`
- symptom: opening a trace for an internal design proposal that recommends a
  decision was refused — the closed vocabulary is `market-analysis`, `gtm`,
  `status-report`, `due-diligence`, `product-intro`, `training-curriculum`, and
  none of them is "here is a decision, here is what I recommend and why". The
  refusal is the schema working; the gap is that a real document type has no
  name, so its trace cannot be opened at all.
- check: either add a `proposal` / `recommendation` skeleton to
  `references/storyline-templates.md` and the vocabulary together — a storyline
  is a narrative skeleton, so a vocabulary entry without a template is a name
  with nothing behind it — or rule that a proposal IS one of the existing six
  and say which in the templates file.
- closed: 0.1.491
- resolution: **`proposal` added, template first.** Template 5 in
  `references/storyline-templates.md` carries the skeleton; the tuple in
  `scripts/lib/deliverable_registry.py` follows it.
- what closing it turned up is larger than the gap: **not one of the six
  existing storyline names appeared anywhere in `references/`.** The vocabulary
  was a closed enum in code with no prose behind it, so an author had nothing to
  choose from. A roster now names all seven with the shape of argument each
  makes, and the `storyline vocabulary` guard holds the roster and the tuple to
  each other in both directions. Five of the seven still have only a one-line
  shape rather than a full skeleton; that is stated in the roster and queued as
  a backlog item, not hidden.


## GAP-011 · C3 is two dimensions sharing one name

- status: fixed
- opened: 0.1.487
- surface: references/eval-rubric.md C3, scripts/lib/rubric_items.py
- symptom: C3's six evidence items address four different objects — the page's
  single claim, its title's assertion, its elements' relevance, and the figures
  on it. Three of the six apply only to a page carrying a figure, so **a
  text-only page can satisfy at most three of six** and scores 3 on a dimension
  it may be answering perfectly. The owner found it by trying to fill the sheet
  in: the items read as choices from different dimensions, so it was unclear
  what a tick meant.
- check: either split C3 into page-argument and figure-quality — which changes
  the dimension set from seven to eight and needs another `scores.json` schema
  version — or keep one dimension and say in the rubric why a figure item and a
  page-argument item belong to one number. **Both are decisions for the owner**;
  the current state is neither, which is why this is recorded rather than
  patched. The conditional-item work at 0.1.487 makes the present state
  survivable: those three items are marked not-applicable on a text page instead
  of counting against it.
- closed: 0.1.489
- resolution: **split**, by owner ruling. C3 keeps the three page-argument items; the three figure items become **C8 · Figure quality**, and a document with no figures scores C8 `n/a` rather than 1. The numbering does not shift — C4 through C7 keep their meanings, because a dimension id is a name and not an address and renumbering would leave every recorded score ambiguous. `reviews/scores.json` moves to schema 3; no schema-2 record had been written, so nothing was migrated.

## GAP-006 · Rules whose only home is outside references/, and a subset claim that is false

- status: fixed
- opened: 0.1.456
- closed: 0.1.480
- surface: references/operating-rules.md, SKILL.md, AGENTS.md,
  prompts/lumi-style-core.md, CLAUDE.md
- symptom: whole rule families were stated nowhere in `references/` — the
  debug-mode contract, the parallel-build protocol and its merge gate, the
  questions-come-once rule, the colophon-placement rule, the
  scaffold-never-fixture rule, the world-figure generation rule, the
  capability-tier rule, and the globe/map figure grammar living as comments in
  `region-palette.css`. And `CLAUDE.md` called `prompts/lumi-style-core.md` "a
  strict subset of `references/`" while that file carried rules of its own.
- check: **two of the families were homed by this refactor's other work before
  this entry was reached** — the capability-tier rule is now P-2's closing
  sentence in `PRINCIPLES.md`, and colophon placement is in
  `storyline-templates.md`. The remaining five share a category the original
  entry did not name: **they are all rules about how the agent works, not about
  what a deliverable is**, which is why none of them fitted the five existing
  reference files. `references/operating-rules.md` is their home, under P-2
  because each answers the same question — what makes the result trustworthy
  rather than merely finished.
- the false claim is corrected rather than made true: the core prompt is now
  described as **a derived restatement that may carry prompt-tier-only rules**,
  and those are named. Making it a strict subset would have meant deleting rules
  that exist because a prompt-tier agent has no tools, which is a worse answer
  than an accurate sentence.
- what is NOT closed by this: the globe/map figure grammar is still comments in
  `tokens/region-palette.css`. It is design prose in a token file, which is the
  same defect one file along, and it is recorded as **GAP-010** rather than
  quietly folded into a closure.

## GAP-010 · The globe and map figure grammar lives as comments in a token file

- status: fixed
- opened: 0.1.480
- closed: 0.1.482
- surface: tokens/region-palette.css, references/design-rules.md §1.2
- symptom: how a globe or region map is composed — what the graticule is for,
  why a bloc is quieter on the globe than on the map, what a label on a sphere
  cannot rely on — was comment prose inside a generated token file. Half that
  file was prose: **7086 characters of it against 14010 total.** A token file is
  read by the build, not by a person forming a judgement, so none of it was
  visible to a reader of `references/` or to the `principle trace` guard.
- check: eighteen grammar blocks moved into `design-rules.md` §1.2, and the
  generator now emits a one-line label per rule plus one pointer at the top.
  The token file's prose fell from 7086 characters to 3944, and what remains is
  either the generated-file banner or a note about the CSS mechanics at the
  site that needs it.
- **the proof is sentence conservation, not a byte diff.** GAP-007's moves were
  content-frozen and provable by comparing the multiset of lines; this one
  crosses formats, where a line multiset cannot survive. So the check is that
  every sentence does: **41 source sentences, 39 verbatim, 2 differing only in
  case** (the CSS comments shouted two headings in capitals), **0 missing.**
  Two sentences had been reworded in the first draft and were restored — a move
  that rewords is not a move, and the measurement is what caught it.

## GAP-009 · The shape library's relation classification is a third unclassified

- status: fixed
- opened: 0.1.473
- closed: 0.1.478
- surface: assets/shapes/tags.json
- symptom: the library shipped complete — all 206 units — but 70 carried
  `relation_from: unclassified`, so a third of it could not be reached by
  selection-by-relation. Usable, but not findable by the thing that finds
  shapes.
- check: all 70 are classified, and by the one method that has not been wrong
  here — **the rendered previews were opened and each shape classified from what
  it draws**. Contact sheets of twelve at a time; `relation_from: looked-at`.
  Two earlier attempts classified from the extraction's tags and from the page
  names, and both were wrong: the tags are sparse (they dropped the `flow-2`…
  `flow-6` and `cycle-2`…`cycle-8` families), and the names lie — `box` is a 2×2
  grid with a four-arrow cycle, `surround` is a large directional arrow, and
  `p012-footnotesource` is a 3×3×3 cube.
- what looking found that no name would have: the fourth and fifth sheets are
  almost entirely **chart primitives** — sorted bars, stacked areas over time,
  grouped columns, pie, histogram, scatter, Harvey balls — which is Zelazny's
  comparison set in drawable form. And `p157-illustrative` / `p158-disguised-
  client-example` are a set of **"illustrative / preliminary draft / for
  discussion only" stamps**, which is exactly what C4-③ asks a document to carry
  where an estimate appears.
- two categories were added rather than forcing everything into a relation:
  **`element`** is a basic form asserting no relation by itself (a plain block, a
  single circle) and **`apparatus`** serves the document rather than the argument
  (legend swatches, the disclosure stamps). Neither is a reject.

## GAP-008 · P-1 is stated wider than anything checks it

- status: fixed
- opened: 0.1.460
- closed: 0.1.481
- surface: references/design-rules.md §1-§2, scripts/check/check_design.py
- symptom: P-1 says the brand pack is the single source of visual and verbal
  identity. What was held was the palette. **Typography had no check at all**
  (verified: `check_design.py` contained no occurrence of `font-family`), and
  **layout was collected but not judged** — D9 gathered every page whose layout
  class the tokens do not define into an `unknown` list, and then its verdict
  was hard-coded to `True`. An agent inventing a seventeenth layout was caught
  by nothing.
- check: **D22 layout vocabulary (gates)** — a page claiming a layout `tokens/`
  does not define fails, on the same reasoning as D19: it is decidable, not a
  judgement about design. **D23 font count (reported)** — distinct font stacks
  against what the tokens declare, and **the ceiling is derived rather than
  written**: design-rules says two voices and the tokens declare two, so a
  literal `2` here would be quietly wrong the day a third is added. A test
  proves the ceiling moves with the tokens.
- the failing subject was already in the tree: `deck-degenerate` has fourteen
  pages carrying no layout class at all, and D9 had been collecting them for
  releases while reporting the run clean. **The evidence of the hole was sitting
  inside the fixture the whole time**, which is what a verdict hard-coded to
  pass does — it is the shape this repository calls a check that has only ever
  been seen passing.
- what remains under P-1 and is honestly not covered: whether a page's
  composition is *good*. That is a judgement, it belongs to C7 and to the eye,
  and no metric here claims it.

## GAP-007 · The reference files read as accretion, not as documents

- status: fixed
- opened: 0.1.456
- closed: 0.1.480
- surface: references/design-rules.md, references/storyline-templates.md,
  references/eval-rubric.md
- symptom: the owner read the rule set end to end and said a person cannot form
  a correct judgement from it, and the skeletons agreed: design-rules ran
  1, 1c, 1d, 2, 3, 4, 4b, 5, **7, 6** with its chart rules numbered 1-5, 6, 7,
  7b, 7c, 7d, 7e, 8, 8b; storyline-templates wedged its shared apparatus between
  Template 1 and Template 2; eval-rubric described three gating surfaces in
  three places with three vocabularies.
- check: **each of the four symptoms measured against the files, not recalled.**
  design-rules' top-level sections now read 1 2 3 4 5 6 7 8 and its chart rules
  6..14 after the inline 1-5 (0.1.457, content-frozen — the multiset of
  non-heading lines was identical before and after, and the same proof was run
  for storyline-templates at 0.1.458, whose four templates are now adjacent with
  the three universal sections following them). eval-rubric carries one gating
  notation in its target columns and **one** paragraph explaining what gates;
  the two other appearances of `(gates)` are quoting `check_design.grade()`'s
  own target string where that format is being discussed, which is a citation
  rather than a second vocabulary.
- what the reorder produced that the entry did not anticipate: the citation
  re-flow found **twenty-one live citations pointing at moved sections while all
  twenty-nine guards stayed green**, because `check_links` only sees markdown
  link syntax. The `section citations` guard was built for it and is the
  durable half of this closure — the next reorder cannot repeat this.

## GAP-004 · The Evals thresholds are gameable and calibrated on two documents

- status: open
- opened: 0.1.455
- surface: evals/thresholds.json, scripts/ops/eval_corpus.py
- symptom: a red-team pass cleared all four bars on the rejected corpus
  document with two mechanical rewrites that add no content — every `<li>`
  re-tagged as `.vows` markup, and one decorative rect-only SVG per prose page.
  The two metrics that saw it (`rect_only_share` 0.667, `shape_kinds_min` 1)
  had been demoted to reported for not separating a two-document corpus.
  Separately: the sales column is calibrated from a REJECTED document only —
  there is no accepted sales document — so those cells say where a bar could
  sit, not where it should. The bars therefore report and do not gate.
- check: the agreement study. Score the deliverables already on the operator's
  machine against the owner's recorded H1-H6 review scores and publish the
  correlation per threshold. A bar that does not track her judgement across ten
  documents is not measuring what she measures, however cleanly it separates
  two. `references/eval-rubric.md`'s own promotion rule asks for the same
  thing: two releases of real documents read against a metric before it gates.

## GAP-005 · Three of the owner's four deliverable categories have no accepted reference

- status: open
- opened: 0.1.455
- surface: evals/thresholds.json, references/storyline-templates.md
- symptom: (reworded at the audit remediation to the two-axis model of
  0.1.465) accepted references attach to the **rule tier**, not to the storyline, and only three
  tiers differ — `training`, `internal`, and everything else with `sales` as
  its representative. Of the three, only `training` has a document on record
  as meeting the product requirement (A1); `sales` has a rejected one (R1);
  `internal` has none. Product introduction is a storyline (`product-intro`,
  templated since 0.1.513) on the `sales` tier and carries no obligation of
  its own. Nine of twenty threshold cells therefore read `provisional`, and
  `internal`'s figure floor is `declined` because the only real internal
  document argues in prose and clears every gate. A1 itself fails a gate
  introduced after its acceptance (D27) — a separate entry records that.
- check: an accepted document for each of the two tiers without one, through
  the owner's blind review. Until then the provisional cells are reasoned,
  not measured, and the file says so per cell.

## GAP-003 · The conformance history's producer path has no automated test

- status: fixed
- opened: 0.1.431
- closed: 0.1.433
- surface: scripts/ops/run_conformance.py (report --record)
- symptom: conformance_fresh() is tested against hand-written rows, but
  nothing tests that `report --record` produces rows of that shape — the
  agent/task key split, the digest pinning, the idempotency claim. A
  one-sided producer/consumer contract is FM-07's shape. Mitigations that
  keep this a 5-not-an-8: `validate` schema-checks the history in CI, and a
  malformed or under-grouped row reads as stale (fail-closed).
- check: python3 -m pytest tests/test_record_producer.py — drives the real
  main() against a synthetic ROOT (stubbed registry, task, run dir); closing
  it found one defect: a corrupt scores.json crashed the report merge loop
  with a traceback before the --record block's own does-not-parse guard could
  fire, so that guard was unreachable (fixed with the test)

## GAP-002 · Five checks CI cannot run are verified by prose

- status: fixed
- opened: 0.1.422
- closed: 0.1.425
- surface: scripts/check/inspect_layout.py, scripts/check/check_prose.py,
  scripts/check/check_design.py, scripts/check/check_globe.py, scripts/ops/run_conformance.py
- symptom: the layout gates, full-deliverable prose/design modes, the globe's
  JS half and conformance runs need a browser or an operator; their results
  were recorded as sentences in release notes — claims, not evidence. 0.1.415
  reported "all gates green" on eight of seventeen.
- check: python3 scripts/check/check_evidence.py --check (red in CI since 0.1.425:
  an operator check is a recorded execution with a digest, or the release
  does not ship)
