# The 13 uncontrolled dependencies, ruled

Date: 2026-08-30 · Status: rulings CONFIRMED by the owner 2026-08-30 and recorded — the
negative rule is `OR-8c`, IDEA-23 is resolved, GAP-049 is the one follow-up.
Roadmap item R13 (IDEA-23). The axiom this serves: "depend on nothing outside its own control."

## The frame that decides most of it

The axiom bites hardest at the layer that ships. **The deliverable path is
standard-library-only** (CLAUDE.md:53) — nothing in the render of a deck reaches
outside this repository. So the deliverable already depends on nothing
uncontrolled; the axiom is satisfied where it matters most.

Every one of the 13 uncontrolled dependencies lives in the **dev / eval / publish
/ operator** paths, not the deliverable. For those, "control" has two honest
forms, and the ruling for each dep is which one applies:

- **controlled** — bring it in-repo or generate it, so the tool owns it; OR
- **material** — the tool READS it but does not RELY on its continued existence:
  its absence either degrades to an in-repo fallback, or is made to FAIL LOUDLY
  (never a silent pass). A material dep is a decision, not a leak — the skill
  reads a fact source it does not own, and says so.

The failure mode the axiom actually forbids is **silent** reliance: a dep whose
absence quietly changes a verdict. So the test each ruling applies is: *when this
dep is gone, does the tool degrade to a controlled fallback, fail loudly, or
silently mislead?* The third is the only unacceptable answer.

## The rulings

| # | Dependency | Path | Ruling | Basis |
|---|---|---|---|---|
| 1 | `~/.lumi/terms` (client-name lists) | gate (check_privacy, check_secrets, publish) | **material-by-necessity, made loud** | Cannot be controlled — client names cannot ship in-repo (red line 9). Correctly handled by loud failure: check_privacy `not_attempted`, publish step-0 refusal, and check_secrets' loud half (R12/GAP-047). |
| 2 | `node` | dev/CI (check_js, check_globe node half) | **material** | Verification tool, not deliverable-path. check_js syntax-checks tracked `.js`; absence is a skipped/loud check, never a silent pass. |
| 3 | Playwright / Chromium | operator (inspect_layout, export_pdf, check_globe browser half) | **material** | Browser checks are operator steps recorded through the **evidence gate**, not CI — their absence cannot green a release silently. R2's render-mode redesign will re-decide HOW it's used, not WHETHER it's owned. |
| 4 | publish remote (lumi-style-skill) | publish | **material** | Publish is an operator-invoked, say-so-gated action; the skill never needs the remote to function. |
| 5 | git-filter-repo | publish | **material** | Same — publish-only tool; `publish.sh` checks for it and refuses loudly if absent. |
| 6 | `~/.lumi/traces` (operator trace store) | eval (GAP-049) | **material — but its silence is the one real gap** | The in-repo `evals/traces/` is the controlled copy; `~/.lumi/traces` degrades to it. BUT GAP-049 records it is held by no check — so a divergence between the two is currently silent. This is the one ruling with an action (below). |
| 7 | corpus.local | eval | **material** | Operator-local owner-review corpus; the in-repo `reviews/` + `evals/thresholds.json` are the controlled sources gates read. |
| 8 | prices.local | eval | **material** | Model pricing for a cost display; `cost_usd` was already declined (FM), so nothing gates on it. Absent → the cost is a token count, not a dollar figure. |
| 9 | `~/Documents/.../` delivery dir | operator | **material** | The operator's workspace; `output_dir.py` needs the owner's say-so to create it. The skill produces a deck to stdout/a path; it does not depend on the dir existing. |
| 10 | `~/Documents/.../_corpus` | eval | **material** | Validation corpus; the eval pipeline degrades to in-repo fixtures. |
| 11 | `~/Documents/.../_conformance` (results) | eval | **material** | Degrades to `IN_REPO_RESULTS` (`run_conformance.py:120`). GAP-050 part 2 (0.1.654) just stopped a test from writing to the real one. |
| 12 | platform CLIs (claude, cursor, hermes, gemini) | eval | **material** | Needed only to DRIVE conformance — a rare operator step (big-version iterations only). The skill produces deliverables without any of them. |
| 13 | the vendored asset originals (shape/font source) | build | **controlled (already in-repo)** | `assets/shapes/source/` and the font source are tracked; the recolor/embed builds run from them with `--check` in CI. Owned. |

## What this means for the axiom

Eleven of the thirteen are **material** and already handled correctly — they
degrade to an in-repo fallback or fail loudly, and none silently changes a
verdict. One (#13) is already controlled. One (#1, terms) cannot be controlled by
its nature and is correctly made loud. **No dependency needs to be "brought
in-repo"** — the architecture already satisfies the axiom, because the layer that
ships owns everything and the tooling layer either degrades to what it owns or
refuses out loud.

The rule the census actually earns is therefore a **negative** one, and it is
worth writing down: *a tool may read an uncontrolled fact source, but its absence
must degrade to a controlled fallback or fail loudly — never silently change a
verdict.* That is one sentence for `operating-rules.md`, and the census is its
evidence.

## The one action this surfaces
Every dep passes the "loud-or-degrades" test except **#6, `~/.lumi/traces`**
(GAP-049): a check reads `evals/traces/` only, so if the operator store diverges
nothing says so. That is the single concrete follow-up — it is already its own
ledger id (GAP-049), and it is the lone instance where the axiom is not yet met.
It is small and independent; it can be its own release.

## Owner confirmation — GIVEN 2026-08-30
The owner confirmed all three:
1. The **material** classification for #1–#12 is accepted (bringing any in-repo
   has no defect behind it, convention 2, and #1/#12 cannot be).
2. The negative rule is promoted to `references/operating-rules.md` as `OR-8c`
   (degrade-or-be-loud, never silently mislead).
3. GAP-049 (#6) is the one follow-up worth its own release.

IDEA-23 is resolved to these rulings (0.1.657); GAP-049 stays open as the single
place the rule is not yet met.
