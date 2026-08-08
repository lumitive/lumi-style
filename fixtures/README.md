# Fixtures

Two synthetic deliverables that exist so the check scripts can be tested. Before
0.1.355 they never had been: `check_prose.py`, `check_design.py` and
`inspect_layout.py` all measure a *deliverable*, and the only deliverables this
repository had access to sat in the gitignored `docs/`.

- `deck-pass.en.html` — well-formed; every graded metric must pass.
- `deck-broken.en.html` — the same deck with one named defect per metric. This is
  the fixture that matters: a suite proving only that clean input passes cannot
  tell a working check from one that returns `ok` unconditionally.

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
3. **Both files are generated** by `scripts/build_fixtures.py`, which lifts the
   `:root` token block from `tokens/`. A fixture grading a document against a
   palette the skill no longer ships is worse than no fixture. `--check` runs in
   CI.

`expected.json` is hand-written and asserts verdicts, not values.
