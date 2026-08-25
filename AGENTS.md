# LUMI Style — Agent Instructions (Codex entry)

> **lumi-style 0.1.601.** This file restates part of `references/`; where they
> disagree, `references/` wins. The stamp is checked against `CHANGELOG.md` — it
> went unstamped and unchecked until 0.1.352, and had already carried four
> versions of withdrawn rules.

You are producing content in LUMI's design language and writing style. LUMI is an
AI-native consulting firm serving a global audience. **The default output language
is American English** (since 0.1.333) and the default canvas is **light**; produce
another language or a dark canvas only when the user asks. **Asks, not implies**:
source material in another language, a venue abroad and the audience's
nationality are evidence about the reader, never an instruction, and a language
this user chose for a comparable deliverable outranks all of it. When the request
does not settle it, ask before generating.


**This file is a map, not a second rulebook.** Until the audit remediation it
restated most of `references/` in its own words and grew by a third while the
design said it would shrink (GAP-018); every restatement was a copy that could
drift, and several did. What follows names the files, in the order to read
them, and the commands to run. The rules are where the links point.

**Capability, and what you may call verified.** `full` runs `scripts/`;
`files` reads and cannot execute; `prompt` gets one pasted context. An agent
that cannot run the checks names the checks it owes and may not call the
deliverable verified (`references/operating-rules.md` OR-9).

## Read, in this order

0. `references/PRINCIPLES.md` — the six clauses and the collision exit.
1. `references/brand.md` — the water thesis; the field, the waterline, the
   ground; the accelerators. Read first and commit: land the concept fully,
   then apply the rules (SKILL.md "Commit first"). One colour, one meaning,
   with the globe's region hues as the one stated exception (design-rules §1).
2. `references/writing-rules.md` — output language (§0), terminology red lines
   (§1), banned phrases (§2), punctuation (§3), numbers (§4), the LUMI voice
   and its register profiles (§5, §5b), the de-AI-flavor pass (§6, §6b), the
   fact red lines (§7). Non-negotiable.
3. `references/storyline-templates.md` — the skeleton by scenario (Templates
   1–11; a storyline is a declaration the document makes, never a gate), then
   the **analysis beat** in `references/analysis-rules.md`: every content
   section declares its move (AR-1), the finding is the title and the
   implication the `.take` (AR-2), the figure comes from `assets/frameworks.json`'s
   question → framework → shape chain (AR-4; name the framework in the
   outline and the scaffold fills the slot), and `references/exemplars/` is
   read here — the one place it can act. The reader-outcome rule (AR-5) binds
   the external genres.
4. `references/design-rules.md` + `tokens/` — colour (§1), type (§2), one
   claim per screen and the layout table (§3), the chart iron rules and form
   selection (§4; the shape library hangs under §4.0–4.2), the commercial
   footer (§5), semantic icons (§6), numbers as the copy (§7, the number
   first), the verification matrix (§8) and imagery (§9). Copy the
   token block, never retype a colour: D20 fails a document whose tokens
   disagree with the shipped ones.
5. `references/operating-rules.md` — debug mode (OR-1), the two entry paths
   and the four beats (OR-2), segmented questioning (OR-3), scaffold-never-
   fixture (OR-4), generated world figures (OR-5), source material as facts
   not sentences (OR-7), the out-of-bounds list's home (OR-8), what "verified"
   may mean (OR-9), a scored document is never deleted (OR-10).
6. `references/eval-rubric.md` — the metric tiers, the pre-delivery critic
   gate, C1–C8. Never self-score 5 before a reader has; give the reason for
   every score.

## Build

Write a finished document to `Documents/LUMI-Style/` under the user's home
(`scripts/ops/output_dir.py` resolves it). Scaffold with
`python3 scripts/ops/new_deck.py --genre … --storyline … --entry-path A|B
[--outline <plan>]` and never hand-copy a fixture: the scaffold carries the
genre's contract, the outline's titles and takes, a shape slot per declared
move, and it opens the build trace (`<body data-trace>`). **No `--entry-path`,
no trace** — A is the four-beat discussion, B starts from a recipe, and the
value used to be guessed from whether an `--outline` was present, which
recorded replays as original builds. Compose. Then **one command runs every
instrument**: `python3 scripts/ops/check_deliverable.py <file>` — the
rendered check, every text instrument, privacy (`check_privacy.py` reads
`~/.lumi/terms/`, OR-8, and reports NOT ATTEMPTED without a list), and one
verdict block to fix in a single pass; it closes the trace and reports a
document with none as unmeasured. Look at the contact sheet last: a page is
done when a person reads it as intentional.

The instruments, each named once so none is the one nobody runs:
`check_outline.py` (the storyline beat's machine half; `--against` holds the
deck to its plan), `check_facts.py` (the build to the facts it was built
from), `check_prose.py`, `check_design.py`, `inspect_layout.py --deliverable`,
`check_privacy.py`, `scoring_sheet.py` (the blind C1–C8 sheet),
`review_scores.py` (what a reader returned), `judge_findings.py` (a register
finding must quote its sentence), `trace.py` and `ledger.py` (the build
record and the ledgers that read it), `export_pdf.py`.

**Debug mode**, when the request says so: `scripts/ops/debug_log.py` writes
the log beside the deliverable; SKILL.md's Debug mode section is the contract.

**Portrait is its own composition** (design-rules §3, §8): the split family
collapses to one layout, a sheet page carries a second block beside its
centerpiece, and rendered geometry — not declared CSS — decides; run
`inspect_layout.py` at the design viewport and look.

**Seven hard red lines**: no invented facts (every number carries its source;
illustrative values are labeled 示意); no invented Chinese coinages (use the
standard Chinese term, or the English term directly when none exists); sales
narrative leads with value & future (honesty boundaries take exactly one page);
titles follow the contract "Topic: assertive subtitle" — each names its subject
and carries a verifiable fact, with no word ceiling, no bare-antithesis
titles and no single title frame across more than 60% of a document, and all
titles concatenated must read as a complete argument;
charts use one accent color — the figure green `--acc-live`, which is what the
`f-acc`/`s-acc` paint classes resolve to; `--acc` is the same meaning as text
ink — plus conclusion-style titles and a source line;
AI never signs — money/safety conclusions never come from a language model.
Output language is American English unless the user asked for another — asked,
never inferred from the source material, from the language the user is writing
in, from the venue or from the audience's nationality — and a deliverable in any
other language records the ask (`data-lang-asked`, which M16 gates).

**Workflow note**: *when the user asked for Chinese* — the default is American English and Chinese is never inferred — after drafting Chinese prose, run a full-width punctuation pass
(Chinese text uses full-width ,:;? — half-width stays only inside code, URLs,
filenames, and pure-English runs). Then run the **mandatory de-AI-flavor pass**
(`references/writing-rules.md` §6 — word, sentence and structural moves plus the
two-pass audit; §6b de-translationese when the Chinese was translated from
English), and only then the pre-delivery checklist in the rubric. Measure both
halves rather than reading them: `python3 scripts/check/check_prose.py <file>` for
English prose, and `python3 scripts/check/check_design.py <file>` for any HTML
deliverable. **D12, D14, D15, D19, D20, D21, D22, D24, D25, D27, D32, D33, D35, D37, D38, D39 and D40 gate; every other D-metric is reported for you
to judge** — a page is done when a human reads it as intentional, and a threshold
satisfiable without improving the page ends the looking. (This line claimed
"D1–D4 and D6 gate" for eight releases, naming four metrics that never did and
omitting the one that always has. A restatement nothing compares against is the
drift this file exists to concentrate, not to escape.)

Rule changes go through the feedback-review loop only (see `references/eval-rubric.md`)
and are recorded in `CHANGELOG.md` with a version bump.
