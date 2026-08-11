# Failure modes — the escape-class registry

The recurring shapes of this repository's shipped defects, extracted from
CHANGELOG history so the next occurrence is recognized as a *class*, not
discovered as a novelty. Each entry names how the class is detected and what
now prevents it. The format is machine-checked (unique FM ids, every entry
carries `detection` and `prevention` lines); the content is for people — no
guard pretends to enforce prose.

The second half records **abandoned gates**: enforcement mechanisms that were
considered and declined, with reasons, so they are not re-proposed from
scratch (the lumi project's D10 convention).

## FM-01 · The check that could not fail

- detection: a guard or metric that has only ever been observed passing; a
  fixture suite where a verdict has no fixture that fails it
- prevention: every new gate ships with a deliberate-red run (spec D8);
  fixtures must fail every graded verdict (check_fixtures coverage, 0.1.390);
  guards get synthetic failing-tree tests (tests/test_check_repo_guards.py)

Shipped instances: 0.1.390 (three checkers found incapable of failing),
0.1.403-0.1.404, 0.1.386 ("a check that skips is not a check that passed"),
0.1.368, 0.1.361, 0.1.358.

## FM-02 · The guard in the wrong language or layer

- detection: a fix verified in the layer that was easy to check rather than
  the layer that renders — Python green while the JavaScript runtime carries
  the defect
- prevention: check_js.py parses both JS surfaces (0.1.416); the golden grid
  holds the JS port to the Python authority, in CI under bare node

Shipped instance: 0.1.414 ("the flash was never fixed: the guard shipped in
Python, the runtime is JavaScript") — measured, guarded, release-noted, and
the reader saw no change.

## FM-03 · Prose-copy drift

- detection: re-reading all three entry points and README after any
  references/ change finds a restatement that no longer matches
- prevention: the mechanical half is guarded (version stamps, palette parity,
  ban-list parity); the semantic half stays a review duty — CLAUDE.md names
  it this repo's main hazard precisely because no check sees it

Shipped instances: pre-0.1.332 hexes in prompts/lumi-style-core.md, the
Simplified-Chinese default in AGENTS.md, 0.1.360 ("the documentation catches
up with six releases").

## FM-04 · Reverse drift: a check asserting a vocabulary the repo never shipped

- detection: a probe keying on class names (or any identifier) that exists in
  no tokens/ file and no written waiver
- prevention: the probe-vocabulary guard; prefer checks that read the shipped
  tokens, and make a check name what it failed to find

Shipped instances: 0.1.349 (ten roles audited against six class names that
existed nowhere), 0.1.415 (`.cap .d` asserted with no base rendering).

## FM-05 · Enumeration rot

- detection: any hand-maintained list of "everything" — files, steps, stamps
  — that a change can silently miss
- prevention: replace the list with a glob or a generated source (compileall
  over scripts/, 0.1.416; preflight reads ci.yml instead of holding a copy);
  where a table must exist, a guard forces additions (check_versions'
  tuple, ENTRY_STAMP)

Shipped instances: the "five places and they are the only ones" version rule
(wrong for six releases), the py_compile list at 26 of 29, preflight's own
"fifteen commands" docstring, the duplicate keys in
VERSION_CITATION_WAIVERS (0.1.417).

## FM-06 · Local green is not CI green

- detection: a release verified on a subset of the gates and reported whole
- prevention: preflight.py runs exactly what ci.yml runs and refuses subsets;
  the evidence gate makes non-CI verification a recorded execution rather
  than a sentence

Shipped instance: 0.1.415 (verified on eight of seventeen, failed CI on a
generator check nothing local had invoked).

## FM-07 · Generator/consumer asymmetry

- detection: a generator whose bare write covers fewer files than its bare
  check, or a measurement taken on a rebuilt artifact rather than the one
  that ships
- prevention: `--check` in CI for every generator; measure the shipped
  artifact (0.1.415's lane re-measurement on `lane["points"]`)

Shipped instances: 0.1.415 (palette generator write/check asymmetry — the
incident that produced preflight.py; land-crossing counted against a rebuilt
route, off by 22 samples).

## FM-08 · A number whose direction was never stated

- detection: a rule value read as a target that was meant as a ceiling or
  floor; an author optimizing toward it
- prevention: CLAUDE.md maintenance rule 4 — every number states floor,
  ceiling, or target; review for the optimization

Shipped instances: 0.1.332 (headline ceiling read as target), 0.1.336
(sentence variance driven to zero), 0.1.337 (every title folded in half).

## FM-09 · A rule mandating an asset the package does not ship

- detection: a rule whose satisfaction requires something absent from
  assets/ or tokens/
- prevention: CLAUDE.md maintenance rule 5 — ship it, or scope the ban to
  the actual risk

Shipped instances: 0.1.332 (required display face, shipped none — rendered
nothing until 0.1.337), §5 icons (zero icons until 0.1.338).

## FM-10 · Only the eye finds it

- detection: a metric all-clear on a figure a person can see is broken
  (clipped band, black rectangles, invisible hover)
- prevention: screenshot every figure page at the design viewport and look;
  inspect_layout's contact sheet exists for a person; the evidence gate
  records that the look happened

Shipped instances: 0.1.387-0.1.390 (four releases of "defects only the eye
found after the checks went green"; four solid black rectangles in the
passing fixture, invisible to three passing metrics).

---

# Abandoned gates

Declined enforcement mechanisms, recorded with reasons so they are not
re-proposed. (Declining is a decision; an undocumented decline gets re-argued
every quarter.)

## AG-1 · "Every CHANGELOG deferral must cite a ledger id" as a mechanical gate

Declined 0.1.422. Deciding what prose constitutes a deferral is a
phrase-trigger guard, brittle by construction (FM-01 in the making). The
mechanical part that survives: any `GAP-`/`FM-`/`IDEA-` id cited in
CHANGELOG.md or specs/ must exist in its ledger (the dangling-reference
check). The rest is a prose rule in CLAUDE.md.

## AG-2 · Branch-naming enforcement

Declined 0.1.422. Near-zero value for a single-maintainer repository; the
commit-subject convention (which feeds release tooling) is enforced instead.

## AG-3 · CI-side step-timing enforcement and per-deliverable render timing

Declined 0.1.422. A timing baseline is one machine's number; a cross-machine
fail-gate fails for reasons unrelated to the code — FM-01 inverted. The
floor that shipped is local, warn-only, in preflight (`--timing`). GitHub's
UI already reports job duration.

## AG-4 · ruff format over the existing tree

Declined 0.1.417. It would rewrite most of 16k lines and destroy `git blame`
on comments that are load-bearing institutional memory, for no defect class
the linter does not already catch.

## AG-5 · gitleaks-action for secret scanning

Declined 0.1.422. CI-only, invisible to preflight's "run what CI runs"
contract; a check_repo guard runs in both places with zero new dependencies.

## AG-6 · Hardening preflight.py's shell=True

Declined 0.1.417. The input is this repository's own tracked workflow;
splitting the commands would make preflight run something other than what CI
runs — the one failure that file exists to prevent. Kept with a targeted
`noqa: S602` pointing at the in-file justification.
