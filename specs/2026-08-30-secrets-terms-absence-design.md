# The client-name scan must say when it did not run

Date: 2026-08-30 · Status: design under owner review; not yet implemented.
The release that implements it will cite this file. Roadmap item R12 (GAP-047).

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

**The same list, read by its other reader, already refuses to be silent.**
`check_privacy` calls the identical `load_terms` and, on `not_attempted`, prints
`FAIL layer 1 · declared terms: NOT ATTEMPTED` and exits non-zero: "A check
nobody ran is not a check that found nothing." The two readers of one list
disagree on what its absence means. R12 is making `check_secrets` agree.

## The constraint that makes this a design, not a one-liner

`check_secrets` runs in CI, and **CI legitimately has no `~/.lumi/terms`** —
engagement terms are secrets; they cannot live in the repo or the CI
environment. A blunt "fail when no list" turns CI permanently red. The comment
already in `check_secrets` records the current position: CI's structural absence
is delegated to `check_privacy` (on the deliverable) and to `publish.sh` step-0
(which refuses to publish with no list). So the fix may not simply hard-fail.

**The root of the collapse:** `load_terms` cannot tell "no directory" (CI, an
un-provisioned machine — structural, legal) from "directory present but no list"
(a machine set up for terms whose list was emptied, renamed, or never written —
an operator misconfiguration that should fail). Both return `not_attempted`.
That distinction is the whole fix.

## The fix — split the collapsed absence; three outcomes, one delegated silence

`check_secrets`' client-name half resolves to exactly these, and they are
distinguishable:

1. **A list loaded, an engagement term is present** → finding, fail. *(today: works)*
2. **A list loaded, no term present** → clean, `[]`. *(today: works)*
3. **`~/.lumi/terms/` exists as a directory but yields no `*.terms.txt`** →
   **finding, fail** — the operator is provisioned for terms but the list is
   missing/empty; the scan cannot run and must not read as coverage. *(today:
   silently `[]` — this is the hole GAP-047's `check:` line names.)*
4. **`~/.lumi/terms/` does not exist** → structural absence (CI, fresh checkout).
   Return `[]`, but this is the **one delegated silence**, documented at the
   call site and backed by `check_privacy` + `publish.sh` step-0.

### Where the code changes

- **`_operator_terms()` stops flattening the two absences.** It returns the
  patterns *and* a status that separates "loaded" / "dir present, no list" /
  "no dir" — either by returning a small result object, or by having
  `check_secrets` consult `check_privacy.TERMS_DIR.is_dir()` directly after a
  `not_attempted`. Preference: keep `load_terms`'s public vocabulary unchanged
  (it is shared with `check_privacy`'s exit ladder, `DID_NOT_RUN`), and do the
  dir-present-vs-absent split in `check_secrets` with one `TERMS_DIR.is_dir()`
  test. Smallest blast radius, no change to `check_privacy`.
- **`check_secrets` emits a finding for outcome 3**, worded like the credential
  findings (what is wrong, what to do): "`~/.lumi/terms/` is present but holds no
  `*.terms.txt`; the client-name scan cannot run. Add the list, point
  `LUMI_TERMS_DIR` at it, or remove the directory to take the documented
  structural skip." The term itself is never echoed (it is engagement data —
  the existing rule).
- **Outcome 4 gets a one-line documented skip** at the call site: the silence is
  a decision (delegated to `check_privacy` + `publish.sh` step-0), not a
  blindness. FM-24's "third answer" is satisfied for any provisioned machine;
  outcome 4 is the declared structural exemption, the way the tarball-checkout
  branch (`if not (ROOT/".git").exists()`) already is.

## The residual this does NOT close — named, not hidden

Outcome 4 leaves a real hole, and the spec states it rather than implying the
fix is total: **on a machine with no `~/.lumi/terms`, an engagement term written
into a development-only tracked file (`CHANGELOG.md`, `specs/`, `KNOWN_GAPS.md`)
is caught by nothing.** `check_privacy` scans deliverables, not the repo;
`publish.sh` step-3 scans the *projection*, which excludes development files by
`shipped.json`; those files never reach the public repo but they do sit in the
tracked source repo on GitHub, which red line 9 covers. This is the 2026-08-20
incident's exact shape.

Closing it fully needs the client-name scan to be **obligatory before push, with
the list present** — an operator obligation recorded and checked (the evidence
gate's pattern), not a scan that runs only if a list happens to be around. That
is larger than R12's mechanical core and is registered, not attempted here:

- **GAP-047 is updated** to record what this release closes (outcome 3) and what
  remains (outcome 4 / dev-file residual), so the ledger is not left claiming the
  whole gap is fixed.
- A follow-up (new GAP or IDEA) captures the "client-name scan is obligatory
  before push" design, co-scoped with the axiom that the scan intrinsically
  depends on an uncontrolled external list (it cannot be otherwise — client names
  cannot ship in-repo) and so the right move is to make the dependency's absence
  *loud at the moment it matters*, not to remove it.

## What ships

- `scripts/check/check_repo.py`: `_operator_terms` / `check_secrets` split the
  two absences; outcome 3 becomes a finding; outcome 4 a documented skip.
- `tests/test_secrets_guard.py`: the tests currently assert `check_secrets() == []`
  with the list absent **without pinning `LUMI_TERMS_DIR`**, so they read the real
  `~/.lumi/terms` of whatever machine runs them (environment-dependent — GAP-050's
  fragility class). The fix **pins `TERMS_DIR` in every case** (monkeypatch to a
  tmp dir), and adds: outcome 3 (dir present, no list) → fails with the new
  message; outcome 4 (no dir) → `[]`; a planted engagement term with a list
  present → fails. The deliberate-red is outcome 3.
- `KNOWN_GAPS.md`: GAP-047 updated (closed part / residual part); a new entry for
  the obligatory-scan follow-up.
- `CHANGELOG.md`: the entry records the deliberate-red run and the FM-24
  three-answers exercise (what the guard prints on each of the four outcomes,
  shown to differ).

## Verification

- **Deliberate red planted first** (convention 15): on a tmp machine with
  `~/.lumi/terms` present but empty, `check_secrets` must go red naming the
  missing list; remove the plant → green. Run before the criterion is trusted.
- **FM-24 third answer** (convention 11): the four outcomes print four
  distinguishable results; outcome 4's silence is documented and delegated, not
  blind — and the spec names the residual it leaves rather than reporting the gap
  closed.
- Synthetic-tree tests, at least one failing fixture; `TERMS_DIR` pinned so they
  are environment-independent.
- preflight green; `claim_sweep` clean; one release, one commit.

## Adversarial review

(To be folded in: pre-implementation red-team on the spec — especially whether
outcome 4's delegated silence is genuinely safe given the dev-file residual, and
whether doing the dir-present-vs-absent split in `check_secrets` rather than in
`load_terms` leaves the two readers able to drift apart again.)
