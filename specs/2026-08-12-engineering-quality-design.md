# Engineering quality: toolchain, tests, ledgers, and the evidence gate — design

Date: 2026-08-12 · Written against 0.1.415 · Status: approved by the owner
(owner directive, 2026-08-12 — a documented case under maintenance
convention 2). Companion plan: `2026-08-12-engineering-quality-plan.md`.

---

## 1 · The case

The owner's finding: this repository has serious software-engineering gaps —
omissions, forgotten steps, and code-quality debt — and the engineering
discipline of her other project (the lumi product repo, whose
`docs/prd-to-merge-sop.md` distills a shipped-broken retrospective into
"a requirement is built only when its declared check has been EXECUTED, with
linked evidence") should be migrated here.

The audit that scoped this design confirmed the finding with this repo's own
history. The specific deficits, each traceable to a shipped defect:

1. **The scripts have no tests.** 29 Python files, 16,398 lines, zero test
   files. CI's only script-quality gate is `py_compile` over a hand-maintained
   26-file list that omits three scripts — including `preflight.py`, whose
   whole job is guaranteeing CI completeness, and `sea_route.py`, the newest
   release's 425-line router. The guard functions in `check_repo.py` run only
   against the live repo, so a guard that silently passes everything is
   invisible — the exact failure family 0.1.390 documented three times over
   ("a checker rewritten to `return 'ok'` would have passed").
2. **No lint, no type-check.** The 0.1.415 escape (a comment-stripping CSS
   parse bug) and the 0.1.414 escape (a guard shipped in Python for a
   JavaScript runtime) are both classes that static tooling narrows.
3. **The JavaScript is unchecked entirely.** 8 tracked files (2,319 lines)
   plus ~1,150 lines of JS embedded as Python strings in `inspect_layout.py`
   have no syntax check. The JS projection port is verified by no CI at all —
   the golden grid comparison needs Chromium, so it runs only on an operator's
   machine, and only when remembered.
4. **Duplicated implementations have already diverged.** The sRGB linearizer
   exists in four places with two different thresholds (0.03928 vs 0.04045);
   CSS custom-property parsing exists in three, and the comment-stripping fix
   shipped in 0.1.415 landed in only one of them — `build_brand.py` carries
   the same bug today.
5. **What CI cannot run is verified by prose.** Five checks need a browser or
   an operator (layout gates, deliverable prose/design mode, the globe JS
   half, conformance runs). Their results are recorded as sentences in release
   notes — claims, not evidence. 0.1.415 was verified on eight of seventeen
   gates and reported "all gates green".
6. **No queryable ledgers.** The backlog's Markdown source was deleted
   (commit `e861df0`), leaving a rendered HTML deck; deferred items and known
   gaps live as prose inside CHANGELOG entries; review findings have no
   closure tracking. The commit-message convention is stated in one line of
   CLAUDE.md and enforced by nothing.

## 2 · Decisions

Three were made by the owner explicitly; the rest follow from them.

**D1 — Full dev toolchain (owner decision).** pytest, ruff, mypy, and
`node --check`, as dev/CI tools only. "Standard library only, no
dependencies" narrows to: *the skill package's deliverable path runs on the
standard library alone*; development tooling is declared separately
(`requirements-dev.txt`) and installed only by CI and by developers.
Precedent: Playwright is already an optional local dependency for
`inspect_layout.py`.

**D2 — Full scope (owner decision).** Script tests and toolchain; the
evidence-based acceptance flow; dedup refactor; defect/backlog ledgers; plus
security scanning, multi-agent conformance as routine practice, and a
performance floor.

**D3 — Evidence acceptance at full mechanical gating strength (owner
decision).** A CI script, not a prose rule. The lumi SOP's own retrospective
is the argument: gates that existed only as advisory prose were skipped, and
the release that skipped them shipped broken.

**D4 — The evidence schema has no verdict field.** `check_evidence.py record`
executes the canonical command itself and machine-writes exit code, output
digest, and date. A human never types "pass"; an unexecuted claim has no
field to live in. This is the structural form of the SOP's D7 rule (a shipped
row without evidence fails) rather than a linted form of it.

**D5 — Gates on manual-cost surfaces bind on freshness, never on passing.**
Conformance runs cost money and hands, and both scored agents currently fail
T1-deck. A pass-gate would block every release forever and invite overclaim;
the gate instead requires the *measurement* to be recent (within 15 versions
of head when a rule surface changed), and failures feed the KNOWN_GAPS
ledger.

**D6 — Pragmatic tool strictness, ratcheted.** ruff with a curated rule set
(defaults + import order + bugbear + pyupgrade + flake8-bandit `S` for
security); mypy non-strict with `check_untyped_defs` as the floor and
strictness ratcheted per module — new shared libraries are strict from
birth. Not lumi's repo-wide strict mode: annotating 16.4k legacy lines before
any value lands is a multi-week diff with real regression risk. No
`ruff format`: it would rewrite most of the tree and destroy `git blame` on a
repo whose comments are load-bearing institutional memory.

**D7 — Characterization tests land before the refactor they protect.** The
dedup extraction (color math, CSS token parsing) is gated on byte-identical
output from every generator `--check`; the tests that prove it are written
against the *current* copies first.

**D8 — Every new gate ships with a deliberate-red run.** Plant a violation,
watch the gate fail, remove it, record the exercise in the CHANGELOG entry.
This repo has shipped three checks that were later found incapable of
failing; a gate's first proof is that it can go red.

## 3 · Declined mechanisms (recorded so they are not re-proposed)

- **"Every CHANGELOG deferral must cite a ledger id" as a mechanical gate** —
  deciding what prose constitutes a deferral is a phrase-trigger guard,
  brittle by construction. It becomes a prose rule; the mechanical part is
  the dangling-reference check (any cited `GAP-`/`FM-`/`IDEA-` id must exist).
- **Branch-naming enforcement** — near-zero value for a single maintainer.
- **CI-side step-timing enforcement / per-deliverable render timing** — the
  baseline is one machine's number; a cross-machine fail-gate fails for
  reasons unrelated to the code. The floor is local, warn-only, in
  `preflight.py`.
- **`ruff format`** — see D6.
- **gitleaks-action for secret scanning** — CI-only, invisible to
  `preflight.py`'s "run what CI runs" contract; a `check_repo.py` guard runs
  in both places with zero new dependencies.
- **Hardening `preflight.py`'s `shell=True`** — the input is this repo's own
  tracked workflow; splitting the commands would make preflight run something
  other than what CI runs, which is the one failure the file exists to
  prevent. Kept, with a targeted `noqa` pointing at the file's own argument.

## 4 · What this does not change

Deliverables stay zero-dependency. `references/` stays the single source of
rule prose; nothing in this design adds or edits a content rule. The existing
verification assets — the fixtures regression system, the golden grid, the
19 guards, the conformance harness — are extended, not replaced.
