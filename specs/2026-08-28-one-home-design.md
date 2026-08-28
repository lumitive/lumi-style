# One home per fact, and a guard that keeps it one

Date: 2026-08-28 · Status: implemented across 0.1.634–0.1.638, whose
CHANGELOG entries cite this file.

## What was asked

The owner read 0.1.633's `detect --models --record` and asked whether the model
vocabulary it stores is obtained by the same function as the model and effort
recorded in `evals/traces/` and `conformance/history.json`. It is not — they are
three independent paths. She asked for one function, on the ground that fewer
implementations mean fewer defects and less to operate, and then asked the
question that matters more: **check the whole tree for the same design fault —
the same information acquired by several separately-written functions.**

Asked for the scope, she chose **all of it, tier 1 and tier 2**, and on the
models question she chose **one module owning the vocabulary, with three callers
asking three different questions** rather than one merged function.

## Why a rule, and not only a cleanup

Extraction without a guard has a half-life in this repository. 0.1.621's README
generator re-derived a selection rule that had already been consolidated, in the
one file that reaches a user, and dropped both of the caveats the tool existed
to state. A one-time consolidation would be undone by the next author who needs
the same fact and does not know where it lives.

**The mechanism already existed and was under-used.** `check_no_shadow_math`
says it in the right words — *"0.1.415's escape shape: a fix landed in one of
several duplicated implementations while the same class stayed live in the
others… an import or a call is fine, a fresh `def` is the drift"* — and guarded
thirteen names across two modules. Beside it sat `check_no_shadow_markup`, a
hand-written second copy of the same idea for a different fact. **Consolidating
a fact meant writing a third guard**, which is the fault being fixed, one layer
up. So the guard becomes a register: `evals/single-source.json` maps fact →
owner → the names and shapes it owns, and adding a fact is a JSON entry.

## What the audit found, measured rather than suspected

**Tier 1 — divergence demonstrated on real inputs:**

1. **The skill version: seven implementations, five parse rules, three failure
   behaviours.** Given a SKILL.md carrying another `*_version:` key above the
   stamp, three readers return the wrong number and four the right one — one
   file, two answers. Failure differs too: `SystemExit`, `"unknown"`, and an
   uncaught `IndexError`. A canonical `fingerprint.skill_version()` already
   exists with **one** caller. `trace.py`'s `"unknown"` is not inert: it is
   written into a trace's `skill_version`, which feeds (2).
2. **Version ordering: three implementations, three behaviours.** On five
   inputs, one raises where another returns `()`, and a third is different
   again.
3. **`_releases_between`: two same-named functions**, different regex and
   different SIGN — one returns signed, the other `abs`.
4. **The CHANGELOG release list: six independent `re.findall`s**, one of which
   returns a set and so cannot answer "newest".
5. **`evals/gates.json`: `build_card._gates()`** parses it directly and imports
   no `gate_registry` — a fourth answer in the file whose own module comment
   records "three functions with three different answers to the same broken
   file".

**Tier 2 — same fact, many spellings, not yet diverged:** `platforms.json`
parsed five ways; `history.json` read four ways with the careful reader's own
discipline unshared; two `ROOT` forms that return a wrong path instead of
raising; some eighteen git invocations.

**Models and effort are three different facts, and merging them would be the
mistake.** `vocabulary()` asks what a CLI OFFERS (capability); the pin records
what we ASKED (intent); `model_ran` is what the CLI SAID (observation).
Collapsing them is precisely the defect 0.1.614, 0.1.623 and 0.1.625 each fixed.
What is genuinely duplicated is the vocabulary knowledge around them:

* `drive()` reads capability keys off the registry and never consults
  `vocabulary()`. **Nothing validates a pin before driving** — `--effort max`
  against Cursor composes a model id the CLI does not have, and the CLI is what
  finds out.
* **There is no `efforts` probe at all.** `trace_schema.ENUMS["effort"]`'s five
  levels are Claude Code's vocabulary generalised: Cursor has four, inside the
  model id; Hermes accepts eight; Gemini has none. `adapters/hermes.md` and
  `adapters/cursor.md` already state this correctly — **in prose the code cannot
  read**.
* Cursor's effort is recorded twice (inside `model` and in `effort`) and
  sometimes once: two traces carry `cursor-grok-4.6-high` with `effort: null`
  beside ten with `effort: high`. Same configuration, two shapes, two board
  cells.

## The work

### 1. The rule first — `check_one_home`

`evals/single-source.json`: fact → `owner` → `defs` it owns, `retired_defs` the
extraction removed, `patterns` for shapes that are not `def`s, `why`, and
waivers that name a reason. Doing the rule first is deliberate: every extraction
below then lands under a guard that already exists, and the last commit is not
the one that has to remember to add protection.

Two things the register carries that the old guard could not: **patterns as well
as names**, because six `json.loads(...)["platforms"]` sites are not `def`s; and
a **`selftest` per pattern**, because a regex that has quietly stopped matching
prints exactly what a clean tree prints (FM-24).

### 2. `scripts/lib/version.py` — the fact with seven owners

`skill_version()`, `ver_key()`, `releases()`, `releases_between()`. Reuse
`fingerprint.skill_version()`'s anchored regex, the strictest of the seven and
the only one that cannot match a neighbouring key. **Decide the failure
behaviour once, in the open**: raise, and let the one caller that wants "record
it even if unknown" pass an explicit default — because `"unknown"` reaching a
trace is what makes (2)'s comparator diverge.

### 3. `scripts/lib/platform_registry.py` — the registry with five parsers

`load()`, `agents()`, `by_id()`. Replaces the copy inside the driver (which is
the coupling the analysis must not import), and the four others.

### 4. `scripts/lib/agent_capability.py` — one module owns the vocabulary

Three callers, three questions, three facts kept apart: what does this agent
OFFER, what should I RUN it as, are these two names the same model. It also owns
what nothing owns today — `efforts` / `efforts_waiver` in the registry on the
`models` pattern, `accepts_effort()`, and `validate_pin()` called by `drive()`
before it builds argv. Recording stays split, and the module's docstring says
why, citing the three releases that paid for the distinction. **Also fix the
double-recording**: when the effort is composed into the model id, record it in
`effort` too.

### 5. `scripts/lib/history.py` and the smaller tier-2 items

One reader for `conformance/history.json` carrying the careful reader's
discipline — absent, unreadable and not-a-list are three answers, not one — used
by all four readers. Then `build_card` onto `gate_registry`; the two bare
`parents[2]` ROOT forms onto the guarded form; a `git` helper.

## Verification

* `python3 scripts/preflight.py` after each commit.
* **The rule is proven before it is trusted**: for each register entry, plant a
  duplicate `def` in an unrelated script, watch `check_one_home` name the owner,
  remove it.
* **And the second question** (FM-24): what it prints when a register entry
  names a module that does not exist, a name nothing defines, or a pattern that
  no longer matches its own selftest. An owner that cannot be found is a
  finding, not a silent pass.
* Per extraction, assert the OLD divergence is gone by reproducing it.
* For §4: drive one cursor task with `--effort max` and confirm it is refused
  before argv is built, naming the levels that model actually has.
* `agent_evals.py board --check` and `build_readme_configs.py --check` must
  still pass — the two `effort: null` cursor traces merging into their siblings
  changes the board, and that change should be visible and explained.

## What this does not do

* **It does not merge capability, intent and observation.** Three files keep
  three facts.
* **It does not touch the ROOT idioms beyond the two that can be wrong.** A
  bootstrap fact cannot itself be imported, and three of the five carry comments
  explaining their form.
* **It does not claim the register is complete.** It claims that anything in it
  cannot quietly grow a second implementation, and that adding a fact is one
  entry.
