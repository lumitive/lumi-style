# The gate set becomes a declaration · design

Date 2026-08-23 · Status: **approved by the owner; Phases A–C shipped
0.1.556–0.1.567. D, E and F open.**

Successor to `2026-08-22-rules-equal-conformance-design.md`, which established
that agents converge on what gates and diverge everywhere else. This record is
about the gate set itself.

## The owner's complaint

```text
请深入分析这 40 多道 Gating，我希望要将这些门槛进行归类，整合和验证，如果之前你
是每次都增加一条新的，没有分析，抽象和归类，这些门槛终将会被撑爆
```

Translated to what it claims: gates were added one at a time, in response to
individual defects, with no classification. A set that grows that way cannot be
reasoned about, and eventually cannot be maintained.

## What was measured

| | |
|---|---|
| Verdicts one document can receive | **78** |
| Of those, able to fail a run | **49** (design 17 + prose 5 + layout 27) |
| The classification mechanism | whether a display string contained the SUBSTRING `(gates)` |
| Readers of that substring | **4**, using **3** different matching rules |
| Fields on a gate beyond its id | none — no family, no tier, no scope, no introducing version, no severity |
| Files to edit to add one | the checker + **5 hand-written prose sites** + a fixture + a registry |

Three rows were misclassified in production, and each in a different direction:

- `M4zh_banned_hits` gated in `check_prose`'s exit code and was invisible to
  `gating.py`, whose pattern `(M\d+)_` cannot match `M4zh_`. The conformance
  harness's `all-gating` requirement set did not contain the one gate that fails
  a **Chinese** deliverable, in a package whose decks are largely Chinese.
- `D37_caption_name_len` and `D38_agenda_run_echo` say `reported` in their own
  targets and were counted as gates by every consumer, because `gating.py` keyed
  on the `D\d+` PREFIX.
- `check_privacy` is the fiftieth gate, promoted in `check_deliverable`'s code,
  and appeared in no registry at all.

## The decisions the owner took

1. **`since`, and an old document reports `not held`** — never a failure. Her
   framing corrected a real error of mine: she never asked for delivered
   documents to be upgraded. Calibration (read-only, against documents she has
   accepted) stays; migration (editing them) was out of scope and had no
   business being proposed.
2. **The repository splits in two** — a consumer repository and a development
   one. Phase D.
3. **Declare the set, and merge the overlapping families.**

## What the data did to decision 3

The plan said 49 gates would merge to about 30. Measured against the fixtures,
the families that look redundant discriminate:

- `reserve_overspent` fails while `content_hidden` passes — a title block can
  overspend its reserve without being clipped.
- `band_escape` fails while `page_height` and `content_spill` pass.
- `collision` fails while `figure_ink_collision` passes: one reads page blocks,
  the other reads inside a drawing.

**Merging them would have deleted assertions to reach a number.** The count was
the wrong target. The classification — `family`, shipped in `evals/gates.json` —
is what the owner's complaint actually needed, and what the report now groups
by. Recorded so this is not re-debated: a future session reading "49 gates,
should be 30" should read this paragraph first.

## What declaring the set found

Nine defects, none of them predicted, all of them from writing the set down in
a form that could be compared to the code. That result is the substance of
FM-22: **a set with no enumerable form cannot be found wrong.** The register
earns its place only because it is compared to reality by a parity guard and
because it REMOVED readers that kept their own copies — a register that is a
second copy is a second thing to rot.

The same question asked of the prose sites found three more (0.1.566, 0.1.567),
the worst of which told an author that `figure_axis_named` reports when it
gates.

## What remains

**Phase D — the split, by projection rather than by cutting.** The development
repository is unchanged; the public one is a mechanical `git filter-repo`
projection of its history. Two alternatives were tested and rejected: a nested
consumer checkout is scanned as a development tree by `check_repo.md_files()`
(the `.claude/worktrees/` failure, deliberately re-run), and a sibling directory
breaks every script's `ROOT`, which resolves relative to the script's own file.

Prerequisites, all of them before any file moves:
- `ledger.py:53` hard-codes `ROOT/evals/traces` while `trace.py:52` honours
  `LUMI_TRACES`; setting the variable silently splits writer from reader.
- `conformance/CONFORMANCE.md:4` carries an absolute path containing the
  owner's username, and the public repository would publish it.
- `check_shipped_closure` (the manifest must PARTITION the tracked tree — a
  list can omit silently, a partition cannot) and `check_cross_boundary_paths`,
  both landing **before** the moves so their first red enumerates the real
  residue instead of my grep.
- Consumer writes move to `$LUMI_STATE`, following `check_privacy.py`'s
  existing `LUMI_TERMS_DIR` precedent, creating directories only on an explicit
  write.

**The footprint, measured 2026-08-23 rather than estimated.** 2,975 tracked
files, ~12.5 MB. The owner saw 244 MB on disk; 197 MB of that is gitignored and
has never been pushed, and a fresh clone is 8.28 MiB. So the case for the split
is not clone size — it is that a consumer reads none of it.

| | tracked | note |
|---|---|---|
| `assets/shapes/source/` | **2.77 MB** | 207 VENDORED ORIGINALS. Input to `recolor_shapes.py`; no deliverable reads them |
| `assets/shapes/*.svg` | 2.9 MB | the built library — consumer |
| `assets/icons`, `vectors`, `brand`, `logos`, `fonts` | 2.3 MB | consumer |
| `scripts/` | 1.67 MB | mixed: the checkers ship, the repo guards do not |
| `fixtures/` | 795 KB | consumer, deliberately — see below |
| `tests/` | 530 KB | development |
| `specs/`, `evals/`, `releases/`, `conformance/`, `backlog/` | 767 KB | development |

`assets/shapes/source/` alone is **22% of the tracked repository and a build
input**, which is the single largest item on the wrong side of the boundary and
was not in the original estimate.

Three assignments that read backwards and are deliberate: `fixtures/` ships to
the consumer because `new_deck.py` takes the scaffold from it as the reference
implementation; `CHANGELOG.md` ships because `check_versions` binds four stamps
to its newest heading; `evals/rule-coverage.json` and `thresholds.json` ship
because doing so puts both generators in the same repository as their only
input.

**Phase E — SKILL.md's hierarchy.** It passes every mandatory check in
skill-creator's validator and exceeds one prose guideline: 594 lines against a
suggested 500, with `## Workflow` holding 440 of them under a single H2 and no
H3 at all. The prescription is a level of hierarchy and a pointer, not deletion.

**Phase F — a red/blue adversarial review**, owner-requested, before automatic
mode. Red team attacks in three directions: an assertion lost to a merge, a
document that `since` should have held and did not, and a file that is green
locally and red in a fresh clone.

## Standing constraints

- No delivered document is edited. Calibration is read-only, and a red on a
  document the owner has accepted means **the check is wrong**.
- No assertion is deleted to reduce a count.
- One release per commit, rebase-merged, never squashed: two guards depend on
  it.
- Every new gate is planted red on real material FIRST (convention 15), because
  reading the code uses the same model that produced the code.
