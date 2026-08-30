# The client-name scan must say when it did not run

Date: 2026-08-30 · Status: design revised after a two-reviewer red-team;
ready to implement. The release that implements it will cite this file.
Roadmap item R12 (GAP-047).

## What was found (verified in code this session)

`check_secrets` (`check_repo.py:3323`) has two halves. The **credential-shape**
half (`SECRET_PATTERNS`) runs unconditionally and is not at issue. The
**client-name** half — red line 9, "no engagement term in a tracked file" —
reads the operator's out-of-bounds lists through `_operator_terms()`
(`check_repo.py:3315`):

```python
def _operator_terms():
    terms, status = check_privacy.load_terms(None)
    if status != "loaded":
        return []            # <- the hole
    return [check_privacy.term_pattern(t) for t in terms]
```

`load_terms(None)` (`check_privacy.py:151`) returns `not_attempted` when
`~/.lumi/terms/` yields no `*.terms.txt`. So `_operator_terms()` returns `[]`,
the term loop iterates over nothing, and `check_secrets` **reports green having
scanned for no client names at all.**

**This is FM-24 — two answers where there must be three.** Green from this half
means either "scanned the tracked tree and found no engagement term" or "had no
list, so looked for nothing," and the two are the same empty list. The 2026-08-20
audit found a city name in **eight** tracked files — exactly what this half
catches — and it was caught only because that machine happened to have a list.

**The same list, read by its other reader, mostly refuses to be silent.**
`check_privacy` calls the identical `load_terms` and, on `not_attempted`, prints
`FAIL layer 1 · declared terms: NOT ATTEMPTED` and exits non-zero: "A check
nobody ran is not a check that found nothing." The two readers disagree on what
the list's absence means. R12 makes `check_secrets` agree — and, as the red-team
found, closes a matching blind spot in `check_privacy` itself.

## The constraint that makes this a design, not a one-liner

`check_secrets` runs in CI, and **CI legitimately has no `~/.lumi/terms`** —
engagement terms are secrets; they cannot live in the repo or the CI
environment. A blunt "fail when no list" turns CI permanently red. The comment
already in `check_secrets` records the current position: CI's structural absence
is delegated to `check_privacy` (on the deliverable) and to `publish.sh` step-0
(which refuses to publish with no list). So the fix may not simply hard-fail.

## The axis of the fix — "were there terms to search FOR", not "does a file exist"

The first draft of this spec split on `TERMS_DIR.is_dir()` after a
`not_attempted` status. **The red-team killed that:** a `*.terms.txt` that
*exists* but holds only comments or blank lines loads as status `"loaded"` with
**zero terms** (`_read_terms`, `check_privacy.py:146`, strips `#`/blank lines;
verified: a comment-only file gives `load_terms(None) -> ([], "loaded")`). That
routes into the scan branch, scans for nothing, and reports green — the same
FM-24 hole, relocated from "no file" to "empty file." An `is_dir()` split never
visits it, because it sits on the `status != "loaded"` branch.

So the gating question is **`len(terms) == 0`**, not the presence of a directory
or a file. Three real outcomes for the client-name half, all keyed on the term
list actually obtained:

1. **Terms obtained, an engagement term is present in the tree** → finding, fail.
2. **Terms obtained, none present in the tree** → clean, `[]`.
3. **No terms obtained, but `~/.lumi/terms/` exists** (empty dir, or a file with
   no usable terms) → **finding, fail** — the operator is provisioned for terms
   but the scan has nothing to search for and must not read as coverage.
4. **No terms obtained and `~/.lumi/terms/` does not exist** → structural absence
   (CI, fresh checkout): return `[]`, the one delegated silence.

Keying on `len(terms)` collapses the first draft's "empty dir" and the reviewer's
"empty file" into one outcome 3, which is correct: both mean *provisioned but
nothing to search for*.

## Where the code changes — and where it deliberately does NOT

- **`_operator_terms()` owns the three-way classification**, returning
  `(patterns, status3)` with `status3 ∈ {loaded, provisioned_empty, no_dir}`:
  `loaded` when `terms` is non-empty; else `provisioned_empty` when
  `check_privacy.TERMS_DIR.is_dir()`; else `no_dir`. One function owns it, and
  `check_secrets`'s body stays clean.
- **`load_terms` is left UNCHANGED — on purpose.** Two existing tests pin its
  vocabulary: `test_check_privacy.py:189` asserts an empty *directory* returns
  `([], "not_attempted")`, and `test_check_privacy.py:143` is a parity test
  ("a seventh status added to load_terms must not default to a pass") guarding
  `DID_NOT_RUN` and the `main()` exit ladder. Adding an `empty` status there
  would touch `DID_NOT_RUN` (`check_privacy.py:133`), the verdict expression, the
  print ladder, and that parity test — a materially larger blast radius for no
  gain, since keying on `len(terms)` in the two *readers* covers every case
  without a new status. Both readers already resolve `TERMS_DIR` from the same
  module global at call time, so they cannot drift.
- **`check_secrets` emits a finding for outcome 3**, worded like the credential
  findings: "`~/.lumi/terms/` is present but yields no usable `*.terms.txt`; the
  client-name scan has nothing to search for. Add or populate the list, point
  `LUMI_TERMS_DIR` at it, or remove the directory to take the documented
  structural skip." The term itself is never echoed (engagement data). *(Message
  safety verified: it contains no `scripts/…` path and no `~<letter>` sequence,
  so it cannot trip `check_script_paths` or `check_local_paths` — checked against
  `LOCAL_PATH_RE` at `check_repo.py:4175`.)*
- **`check_privacy` gets the SAME `len(terms)`-keyed guard in `main()`.** The
  red-team confirmed check_privacy is blind to the identical empty-file case: a
  comment-only loaded list makes it print `ok · 0 declared term(s), none present`
  and exit 0 (`check_privacy.py:246,277`). Because the whole thesis is *the two
  readers must agree on what an absent list means*, `main()` treats
  "obtained zero terms while a scan was expected" as a did-not-run (the same
  non-zero FAIL it already prints for `not_attempted`). This is a bounded change
  to `main()`'s verdict logic only — it does **not** add a status or touch
  `DID_NOT_RUN`, so the parity test `:143` stays green.
- **`_read_terms` one-line correctness fix while open** (LOW, red-team #6):
  `ln.startswith("#")` (`check_privacy.py:148`) keeps an *indented* `# comment`
  as a live term; make it `ln.strip().startswith("#")`. Not the absence bug, but
  it silently turns a comment into a bogus scan term.

## Outcome 4 is a delegated silence, NOT full FM-24 satisfaction — stated honestly

The red-team was right to push here. `check_repo`'s harness is binary per guard
(`check_repo.py:5246`: empty list → `ok`, else `FAIL`); there is **no channel
for a guard to print a non-failing note.** So in the no-`~/.lumi/terms`
environment, the client-name half returns `[]` and prints `ok secrets` — the
same string a clean scan prints. This is not the tarball branch (which skips the
*entire* guard); it skips *one half* while the guard keeps reporting `ok`.

The honest position, which the spec now states rather than papering over: **the
third answer is reachable only where the harness can express it** — `check_privacy`
on deliverables (hard FAIL on absent/empty list) and `publish.sh` step-0 (refuses
to publish with no list). In `check_repo`/CI the client-name half is
*structurally best-effort*. To make outcome 4 at least visible rather than a mute
code comment, **`check_secrets` writes a one-line note to stderr** when it takes
the no-dir skip ("client-name half skipped: no `~/.lumi/terms/` on this machine")
— it does not change the exit code, but a CI reader sees the skip happened. This
is the most the binary harness allows without failing CI, and it is named as a
limitation, not sold as a fix.

## The residual this does NOT close — named precisely (corrected)

The first draft named `CHANGELOG.md` as the poster child. **That was wrong and is
corrected:** `shipped.side_of("CHANGELOG.md")` is `consumer` — it crosses into
the projection and IS scanned by `publish.sh` step-3 with the real terms list.
The genuine residual is the **dev-side** tracked files that `shipped.json` keeps
out of the projection: `specs/`, `KNOWN_GAPS.md`, `CLAUDE.md`, `FAILURE_MODES.md`.
On a machine with no `~/.lumi/terms`, an engagement term in one of those is caught
by nothing: `check_privacy` scans deliverables not the repo (verified: its
`main()` takes argv files only, never walks the tree), `publish.sh` step-3 scans
the projection which excludes them, and CI structurally has no list. Those files
never reach the public repo, but they sit in the tracked source repo on GitHub,
which red line 9 covers.

Closing it fully needs the client-name scan to be **obligatory before push, with
the list present** — an operator obligation recorded and checked (the evidence
gate's pattern), not a scan that runs only if a list happens to be around. That
is larger than R12's mechanical core and is registered, not attempted here:

- **GAP-047 is updated** to record what this release closes (outcome 3, both
  reader-halves) and what remains (outcome 4 / the dev-side-file residual).
- A follow-up entry captures the "client-name scan obligatory before push"
  design, co-scoped with the axiom that the scan intrinsically depends on an
  uncontrolled external list (client names cannot ship in-repo), so the right
  move is to make the dependency's absence *loud at the moment it matters*, not
  to remove it.

## What ships

- `scripts/check/check_repo.py`: `_operator_terms` returns the three-way status;
  `check_secrets` fails outcome 3, takes the documented skip + stderr note on
  outcome 4.
- `scripts/check/check_privacy.py`: `main()` fails a loaded-but-zero-terms scan
  (reader parity); `_read_terms` indented-comment fix.
- `tests/test_secrets_guard.py`: every case **pins `check_privacy.TERMS_DIR`**
  (monkeypatch that module attribute — it is read at call time; setting the env
  var post-import is a no-op) so the tests stop reading the host's real
  `~/.lumi/terms` (the GAP-050 fragility the red-team confirmed). New cases:
  outcome 3 as an **empty directory** AND as a **comment-only file** (two
  fixtures — the deliberate-red must visit the empty-file path, not just the
  empty-dir path); outcome 4 (no dir) → `[]`; a planted engagement term with a
  real list → fails.
- `tests/test_check_privacy.py`: a loaded-but-zero-terms list → non-zero verdict.
- `KNOWN_GAPS.md`: GAP-047 updated (closed part / residual part); a new entry for
  the obligatory-scan follow-up.
- `CHANGELOG.md`: records the deliberate-red run and the FM-24 exercise — what the
  guard prints on each of the four outcomes, shown to differ (outcome 4's `ok` +
  stderr note named as the delegated-silence limit, not a pass).

## Verification

- **Deliberate red planted first** (convention 15): on a pinned tmp `TERMS_DIR`
  that is (a) an empty directory and (b) a directory holding only a comment-only
  `*.terms.txt`, `check_secrets` must go red in BOTH; remove the plant → green.
  The empty-file fixture is the one the first draft would have missed.
- **FM-24, three answers** (convention 11): outcomes 1/2/3 print three
  distinguishable results; outcome 4 is the declared delegated silence, made
  visible on stderr and named as a limitation — not reported as a clean pass.
- Both readers agree: the same empty-list input fails `check_secrets` and
  `check_privacy`.
- Synthetic-tree tests with `TERMS_DIR` pinned (environment-independent);
  `test_check_privacy.py:189`/`:143` left green (load_terms untouched).
- preflight green; `claim_sweep` clean; one release, one commit.

## Adversarial review — folded in (2026-08-30, two reviewers, verified)

- **[CRITICAL] empty/comment-only `*.terms.txt` loads as `"loaded"`/zero terms**
  → the fix must key on `len(terms)`, not file/dir existence. Recut the whole
  fix axis (above). Verified empirically.
- **[HIGH] residual example wrong**: `CHANGELOG.md` is `consumer`-side and IS
  scanned at publish; the real residual is `specs/`/`KNOWN_GAPS.md`/`CLAUDE.md`/
  `FAILURE_MODES.md`. Corrected.
- **[HIGH] outcome 4 still prints `ok`** (binary harness, no note channel):
  stopped claiming full FM-24 satisfaction; added the stderr note and stated the
  delegated-silence tradeoff honestly.
- **[HIGH] check_privacy blind to the same empty-list case** → added the
  `len(terms)`-keyed reader-parity guard in `main()`.
- **do NOT fix in `load_terms`** (tests `:189`/`:143` + `DID_NOT_RUN` + exit
  ladder): the split lives in the two readers; `load_terms` untouched.
- **tests are environment-dependent** (no `TERMS_DIR` pin) → pin
  `check_privacy.TERMS_DIR` (the correct module attribute) in every case.
- **[LOW] `_read_terms` indented `#`** kept as a term → one-line fix while open.
- Confirmed safe: no third reader of `load_terms`/`term_pattern`; the new failure
  message trips neither path scanner.
