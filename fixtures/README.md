# Fixtures

Three synthetic deliverables that exist so the check scripts can be tested. Before
0.1.355 they never had been: `check_prose.py`, `check_design.py` and
`inspect_layout.py` all measure a *deliverable*, and the only deliverables this
repository had access to sat in the gitignored `docs/`.

- `deck-pass.en.html` — well-formed; every graded metric must pass.
- `deck-broken.en.html` — the same deck with one named defect per page. This is
  the fixture that matters: a suite proving only that clean input passes cannot
  tell a working check from one that returns `ok` unconditionally. It is also a
  worked example, and it is kept readable as one.
- `deck-degenerate.en.html` — **not an example.** Its only job is to fail. Ten
  metrics could not be given a failing case in `deck-broken` without destroying
  its readability: four are document-WIDE prose properties (every sentence the
  same length, every title the same shape) that cannot be confined to one
  labelled page, and six more design defects on a deck already carrying eight
  would have stopped it teaching anything. Added in 0.1.390.

**Coverage is computed, not claimed.** `check_fixtures.py` reports how many
graded verdicts have a fixture that fails them and refuses the ones that do not.
Before 0.1.390 thirteen of eighteen design verdicts and four of seven prose
verdicts read `ok` on both fixtures, so a checker rewritten to `return "ok"`
would have passed the suite whose stated purpose is to catch exactly that.

**The renderer is in the suite too**, behind an availability check:
`inspect_layout.py`'s gating findings (`deliverable_verdicts` is the list —
a count written here said "ten" while the code carried fourteen) are
asserted where a headless Chromium
exists and the run says loudly, with a count, when it skipped them. That is why
the suite takes a couple of minutes locally — three fixtures at four geometries
each — and why it still cannot run in CI.

Three rules, and each has already been paid for elsewhere in this repository:

1. **Never edit a fixture to make a check pass.** If a check fails on
   `deck-pass`, either the check or the deck is wrong; decide which, and say so in
   the changelog. Editing the evidence to match the verdict is how a metric
   becomes decorative.
2. **Never import a real deliverable.** Red line 9 bars client names, project
   figures and engagement facts. Everything here is invented — a fictional
   metering programme, `www.example.org` as the origin. The temptation to make a
   fixture "realistic" by copying a live deck is exactly how that red line gets
   crossed.
3. **Both files are generated** by `scripts/build/build_fixtures.py`, which lifts the
   `:root` token block from `tokens/`. A fixture grading a document against a
   palette the skill no longer ships is worse than no fixture. `--check` runs in
   CI.

`expected.json` is hand-written and asserts verdicts, not values.
