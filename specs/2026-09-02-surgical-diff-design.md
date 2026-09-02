# Design: every changed line traces to the request, held by a gate

Date: 2026-09-02. Implemented at 0.1.682. A record of what was decided and
why, written before the work; not a source of rules.

## The case

0.1.681 changed one rule in `adapters/shipped.json` and the commit carried
499 changed lines, because the file was parsed and written back with a
two-space indent where it had one. The first reading was a one-off. The
measurement said otherwise. Over the thirty commits before 0.1.682:

```
git diff --numstat <rev>~1 <rev>     against     git diff -w --numstat <rev>~1 <rev>
0.1.673  evals/gates.json           1136 changed lines,   8 once whitespace is ignored
0.1.673  evals/rule-coverage.json   9960 changed lines, 384
0.1.674  evals/rule-coverage.json   9990 changed lines, 144    (indent 2 back to 1)
0.1.681  adapters/shipped.json       499 changed lines,   5
```

Four instances, three releases, one of them undoing the one before, and no
guard looking. The tree has `json.dump` at twenty-six sites — `indent=1` at
twelve, `indent=2` at fourteen — and no shared writer; of the twenty-two
hand-written JSON files, fourteen are one-space, five two-space, three compact.

Convention 2 promotes a lesson that has appeared across two documents.
Convention 16 says a rule written down and then broken needs a tool that holds
it. Convention 17's surgical-change test — *every changed line traces to the
request* — is the rule; nothing mechanised it.

## Step zero: what was refused before

`precedent.py surgical diff reformat rewrite` and `--body … whitespace
"changed lines"`: no refusal. AG-4 (ruff format over the existing tree) is the
adjacent decision — a mass rewrite destroys `git blame` on load-bearing
comments — and this design enforces it rather than overruling it: it refuses
the accidental mass rewrite and does not perform a deliberate one.

## The decision

**One measurement, two hooks, one writer.**

1. `scripts/check/surgical_diff.py`: for every file in a diff, changed lines
   and changed lines with `-w`. At least 60 changed of which at most a fifth
   survive `-w` is a reformat. Thresholds chosen against the history above:
   they name all four instances and none of the other twenty-six commits.
   Three answers — clean, reformat, could not look (exit 2).
2. `release.py` runs it on the working tree against HEAD, gating, before the
   commit — where the author can still write the file back.
3. `check_repo.py`'s `surgical diff` guard runs it on HEAD~1..HEAD in CI, so a
   commit made around the release tool is judged the same way. It binds only
   commits whose committed CHANGELOG is at or past 0.1.682 — history is not
   retroactively reddened, and 0.1.681 carries the reformat that prompted it.
4. `evals/reformat-waivers.json`: a meant reformat is a decision with an
   address (file, release, why), live only while its release is the newest
   heading. A dead waiver is a finding.
5. `scripts/lib/jsonio.py`: `dump_json` reads the indent the file already has
   and writes with it; new files get one space (the majority). Registered in
   `evals/single-source.json`; `trace.py`'s private `_write_json` is retired
   into its `atomic=True` option; the seven writers of tracked JSON go through
   it.

## Refused within this design

- Unifying the twenty-two hand-written files to one indent: that is AG-4.
- A round-trip guard (every tracked JSON re-serialises to itself): tested on
  all 391 tracked JSON files, 388 round-trip — but a re-indented file
  round-trips too, so the guard cannot see the defect. The diff is the only
  place a reformat is visible.
- A JSON-only check: the ratio is language-agnostic and a re-wrapped Markdown
  or re-indented YAML is the same defect.

## Why the author reached for a rewrite

The session that shipped 0.1.681 ran under a harness directive preferring
shell commands over the dedicated edit tools, so a one-line JSON change went
through parse-and-reserialise. A precise edit does not reformat what it does
not touch. The gate does not care which tool was used; that is the point.

## Verification

- Planted first: the gate was run on the four historical commits before its
  tests existed (all named), and on 0.1.680 (clean).
- `tests/test_surgical_diff.py` holds each answer on synthetic git
  repositories, the SINCE exemption, the waiver lifecycle, and re-runs three
  historical cases against this clone.
- `tests/test_jsonio.py` holds the writer to one-, two-space and compact
  files, new files, the explicit override, and the atomic path.
- `preflight.py` green; the PR's CI `checks` green.
