# Driving the agents — design record

Date: 2026-08-13 · Status: settled, implementing at 0.1.454 · Owner ask: validate
every new release on the Cursor agent CLI automatically, at the same standard as
Claude Code, with no manual step. Owner decision: run on every release.

## What was actually there

`run_conformance.py`'s `run` subcommand created directories, wrote `PROMPT.txt`
and `input.md`, and printed *"invoke each agent against its PROMPT.txt"*. It
invoked nothing. There is no agent invocation anywhere in the repository, and
there never was — the only `subprocess` calls are the `--version` probe and the
check scripts. Every scored row on the conformance board was produced by an
operator driving an agent by hand and dropping the artifact into the run
directory.

The `cli` column reports the probe. When `cursor-agent` was installed on this
machine at 0.1.450 the column flipped from `driven by hand` to a version string
with no code change, and the release notes said the tasks "ran
non-interactively like any other". Corrected at 0.1.452; built here.

## Decisions

**D1 — `drive` is an argv in the registry, separate from `invoke`.**
The registry already carries `invoke`, and it is prose for a human — Cursor's is
`say "in LUMI style…"`. A driver built on that field would try to execute a
sentence. `drive` is a list of arguments, present only for platforms that can be
driven, and its absence is a first-class outcome (`no driver`) rather than a
crash. IDEs and API-only models keep the hand-driven path they always had.

**D2 — The working directory is outside the repository.** This is the decision
most likely to be undone by someone tidying up, so it has a test asserting it.
An agent started inside the tree reads the maintenance `CLAUDE.md`, and then it
is a maintainer of the skill rather than a consumer of it — with the rules, the
checkers and the changelog open in front of it, which is not the thing the task
measures. The agent gets a bare temporary directory and whatever the platform
installed at its own skill path. The deliverable and the transcript come back;
the scratch is deleted.

**D3 — A timeout, and a task filter.** The file had exactly one timeout, on the
20-second probe, and `score_checks` had none. Thirty minutes per task by
default. `--task` exists because the suite's first task is a twelve-page deck
and proving the driver works should not cost one.

**D4 — Driving does not gate the release.** Owner chose "run on every release"
and explicitly not "a failing run blocks the release". That is also the correct
engineering answer: `score` exits non-zero on any non-pass, and this file's own
opening paragraph states that agent CLIs are non-deterministic and drift weekly.
A release gated on that blocks on something that is not the release. `--drive`
exits 0 when the driver ran; the verdict is `score`'s.

**D5 — Record the model either way.** Owner chose "record both". Unpinned runs
record `(the CLI's default)` rather than leaving the field empty: a board cell
that says nothing about the model reads as a claim about the agent rather than
about one of its configurations. `--model` pins it for a comparison.

**D6 — `report --record` writes the table.** It printed, and a person pasted,
and `CONFORMANCE.md` accumulated three copies of "What this table is not"
because a re-appended section is invisible to whoever just generated it. The
table now lives between generated markers; the narrative outside them is
hand-written and survives.

## Declined

**CI.** Restated rather than re-argued: no API keys, no network, no vendor SDKs,
and `cursor-agent` needs a logged-in account. The module docstring and `ci.yml`
both say so, and neither changes. This runs on the operator's machine.

**Folding the driver's exit code into the release gates.** See D4.

**A scheduler.** The repository has no scheduling surface of any kind — one
workflow file, no `schedule:` key, no cron, no hooks. Adding the first one to
run agents on a timer is a larger decision than this release, and per-release
driving is what was asked for.

## Known boundary

The timeout kills the process the driver started. If an agent CLI spawns
children that outlive it and keep the output pipe open, the wait can outlast the
deadline. The tested case is a direct child, because that is the case that can
be demonstrated; killing a process group instead is the standard remedy and is
deliberately NOT added here, since this repository's own rule is that a
mechanism ships with a run that proves it was needed. Recorded rather than
silently carried: if a driven run ever hangs past its timeout, this paragraph is
the diagnosis.

## Not done here

The figure comparison the driver was built to make possible — the same T1 deck
through both agents, compared on figures alone — is a use of this release, not
part of it. The first driven run is recorded with the release as its own
evidence.
