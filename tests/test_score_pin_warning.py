"""Re-scoring silently invalidated every history row's digest pin.

`report --record` writes `scores_sha256` into each row, and the code that does
it says why: the run directory lives outside this repository and is gitignored,
so **the digest is the whole of what makes a row evidence rather than an
assertion**. `score --run <dir>` rewrites `scores.json` and every pinned digest
stops resolving, in a command whose output is otherwise all success.

Found by doing it — refreshing the board's held counts broke all four rows of
the 2026-08-26 run at once, and the verdicts were identical, which is exactly
when such a break goes unnoticed.

Everything below holds `_pin_guard` to one rule: **a check that could not look
must never print what a clean check prints.** Its first version broke that rule
three separate ways, and a review found all three.
"""
import hashlib
import json
import os
import pathlib

import run_conformance


def _tree(tmp_path, monkeypatch, pinned="match", rows=None):
    """A synthetic ROOT with one run directory and one history row.

    `pinned="match"` pins the digest of the scores.json actually on disk, which
    is the state a real recorded run is in and the one a re-score breaks.
    """
    run = tmp_path / "run1"
    run.mkdir(exist_ok=True)
    scores = run / "scores.json"
    scores.write_text('{"a1/T1": {"verdict": "pass"}}', encoding="utf-8")
    digest = hashlib.sha256(scores.read_bytes()).hexdigest()
    (tmp_path / "conformance").mkdir(exist_ok=True)
    body = rows if rows is not None else [
        {"agent": "a1", "run_dir": str(run), "date": "2026-08-26",
         "scores_sha256": digest if pinned == "match" else pinned,
         "skill_version": "0.1.605", "instrument_version": "0.1.605",
         "tasks": {"T1": "pass"}}]
    (tmp_path / "conformance" / "history.json").write_text(
        body if isinstance(body, str) else json.dumps(body), encoding="utf-8")
    monkeypatch.setattr(run_conformance, "ROOT", tmp_path)
    return run


# ------------------------------------------------------- what it must report

def test_a_row_pinning_the_file_about_to_be_replaced_is_reported(tmp_path,
                                                                 monkeypatch):
    run = _tree(tmp_path, monkeypatch)
    lines = run_conformance._pin_guard(run)
    assert lines, "the re-score was about to break a pin and said nothing"
    assert "about to replace" in lines[0]
    assert "TODAY's skill version" in lines[1], (
        "the note must warn that --record is not the remedy")


def test_the_bytes_are_kept_rather_than_recommended(tmp_path, monkeypatch):
    """The advice used to arrive after the file it names was gone.

    `_pin_guard` runs before the write, so it can copy the file instead of
    telling an operator they should have.
    """
    run = _tree(tmp_path, monkeypatch)
    lines = run_conformance._pin_guard(run)
    kept = run / "scores.0.1.605-instruments.json"
    assert kept.exists(), "the pinned bytes were not preserved"
    assert kept.read_bytes() == (run / "scores.json").read_bytes()
    assert kept.name in " ".join(lines)


def test_keeping_twice_does_not_overwrite_the_first_copy(tmp_path, monkeypatch):
    run = _tree(tmp_path, monkeypatch)
    run_conformance._pin_guard(run)
    kept = run / "scores.0.1.605-instruments.json"
    original = kept.read_bytes()
    (run / "scores.json").write_text('{"changed": true}', encoding="utf-8")
    run_conformance._pin_guard(run)
    assert kept.read_bytes() == original


def test_an_already_broken_pin_is_not_reported_as_this_command_breaking_it(
        tmp_path, monkeypatch):
    """"I just broke this" and "this broke in August" are different findings.

    The first version compared the CURRENT file against the recorded digests,
    so it claimed "a re-score replaced the bytes" on every later invocation
    too — flattening the one signal that tells an operator whether their own
    command is the cause.
    """
    run = _tree(tmp_path, monkeypatch, pinned="0" * 64)
    lines = run_conformance._pin_guard(run)
    assert lines and "already pinned a different" in lines[0]
    assert "about to replace" not in " ".join(lines)


# -------------------------------------------------- what it must not swallow

def test_an_unreadable_history_says_unknown_not_clean(tmp_path, monkeypatch):
    """`JSONDecodeError` subclasses `ValueError`.

    One `except` around the parse turned "this file is a merge conflict" into
    "nothing is wrong" — on a tracked file two branches both append to, which
    makes it the likeliest thing here to arrive unparseable.
    """
    run = _tree(tmp_path, monkeypatch, rows="{ not json")
    lines = run_conformance._pin_guard(run)
    assert lines and "UNKNOWN, not clean" in lines[0]


def test_json_that_is_not_a_list_says_so_rather_than_crashing(tmp_path,
                                                              monkeypatch):
    """`null`, a number and an object all parse as valid JSON.

    The list comprehension raised `TypeError` on the first two, AFTER the
    scores file had been overwritten — a stack trace, a destroyed pin and no
    note. A test titled "silent not fatal" planted only the two shapes that
    fail to parse.
    """
    for body in ("null", "7", '{"rows": []}', '"a string"'):
        run = _tree(tmp_path, monkeypatch, rows=body)
        lines = run_conformance._pin_guard(run)
        assert lines and "not a list of rows" in lines[0], body


def test_a_run_directory_that_cannot_be_resolved_does_not_crash(tmp_path,
                                                                monkeypatch):
    """`expanduser()` raises RuntimeError on `~nosuchuser`, not OSError.

    The fallback branch written for "a path this machine cannot resolve"
    caught neither that nor the ValueError `resolve()` raises on an embedded
    NUL.
    """
    run = _tree(tmp_path, monkeypatch, rows=[
        {"agent": "a1", "run_dir": "~nosuchuser42/x", "date": "2026-08-26",
         "scores_sha256": "0" * 64, "skill_version": "0.1.605",
         "tasks": {"T1": "pass"}}])
    assert run_conformance._pin_guard(run) == []


def test_a_missing_scores_file_is_not_a_replacement(tmp_path, monkeypatch):
    run = _tree(tmp_path, monkeypatch)
    (run / "scores.json").unlink()
    lines = run_conformance._pin_guard(run)
    assert lines and "no longer has" in lines[0]


def test_no_history_is_silent(tmp_path, monkeypatch):
    run = _tree(tmp_path, monkeypatch)
    (tmp_path / "conformance" / "history.json").unlink()
    assert run_conformance._pin_guard(run) == []


def test_rows_for_another_run_are_not_accused(tmp_path, monkeypatch):
    run = _tree(tmp_path, monkeypatch, rows=[
        {"agent": "a1", "run_dir": str(tmp_path / "some-other-run"),
         "date": "2026-08-26", "scores_sha256": "0" * 64,
         "skill_version": "0.1.605", "tasks": {"T1": "pass"}}])
    assert run_conformance._pin_guard(run) == []


def test_a_row_with_no_run_dir_is_not_this_run(tmp_path, monkeypatch):
    run = _tree(tmp_path, monkeypatch, rows=[
        {"agent": "a1", "date": "2026-08-26", "scores_sha256": "0" * 64,
         "skill_version": "0.1.605", "tasks": {"T1": "pass"}}])
    assert run_conformance._pin_guard(run) == []


# --------------------------------------------------------- path spellings

def test_the_same_directory_written_two_ways_still_matches(tmp_path,
                                                           monkeypatch):
    """`_portable` collapses only `$HOME`, so `./x` and `x` differ as strings.

    Measured on the real `conformance/history.json`: thirteen different
    spellings across its rows, eighteen of them relative. Passing this the path
    in the exact form that file records was the case that found nothing.

    The path is built as a STRING: `pathlib` collapses `.` while constructing,
    so `run.parent / "." / run.name` is just `run` and plants nothing. The first
    version of this test did that and passed against the defect it names.
    """
    run = _tree(tmp_path, monkeypatch, rows=[
        {"agent": "a1", "run_dir": f"{run_dir_str(tmp_path)}",
         "date": "2026-08-26", "scores_sha256": "0" * 64,
         "skill_version": "0.1.605", "tasks": {"T1": "pass"}}])
    assert run_conformance._pin_guard(run), (
        "the same directory spelled two ways was read as two directories")


def run_dir_str(tmp_path):
    run = tmp_path / "run1"
    return f"{run.parent}{os.sep}.{os.sep}{run.name}"


def test_a_relative_row_resolves_against_the_repo_not_the_shell(tmp_path,
                                                               monkeypatch):
    """`conformance/results/latest` was written from the repository root.

    `.resolve()` resolves a relative path against the process's directory, so
    `score` run from anywhere else turned eighteen real rows into phantoms.
    """
    run = tmp_path / "conformance" / "results" / "latest"
    run.mkdir(parents=True)
    (run / "scores.json").write_text('{"a1/T1": {"verdict": "pass"}}',
                                     encoding="utf-8")
    digest = hashlib.sha256((run / "scores.json").read_bytes()).hexdigest()
    (tmp_path / "conformance" / "history.json").write_text(json.dumps([
        {"agent": "a1", "run_dir": "conformance/results/latest",
         "date": "2026-08-26", "scores_sha256": digest,
         "skill_version": "0.1.605", "instrument_version": "0.1.605",
         "tasks": {"T1": "pass"}}]), encoding="utf-8")
    monkeypatch.setattr(run_conformance, "ROOT", tmp_path)
    monkeypatch.chdir(pathlib.Path(tmp_path).parent)
    assert run_conformance._pin_guard(run), (
        "a row recorded relative to the repository root was not matched")


# ------------------------------------------------- through `score` itself
#
# Everything above calls `_pin_guard` directly, and a review showed what that
# misses: moving the call back to AFTER the write leaves every one of them
# green. The defect it found lives entirely in the wiring — `scores.json` is
# replaced first, and the `if not scores` early return leaves the branch before
# the note. That is the case where the pin is destroyed COMPLETELY rather than
# partially, and it was the one case the check could never reach.


def _scorable(tmp_path, monkeypatch, with_artifact=True):
    (tmp_path / "SKILL.md").write_text(
        '---\nmetadata:\n  version: "0.1.999"\n---\n', encoding="utf-8")
    (tmp_path / "adapters").mkdir()
    (tmp_path / "adapters" / "platforms.json").write_text(json.dumps(
        {"platforms": [{"id": "a1", "name": "Agent One", "capability": "prompt"}]}),
        encoding="utf-8")
    tasks = tmp_path / "conformance" / "tasks"
    tasks.mkdir(parents=True)
    (tasks / "T1.json").write_text(json.dumps(
        {"id": "T1", "prompt": "write answers.md", "min_capability": "prompt",
         "score": ["recall"], "deliverable": "*.md",
         "answers": {"the output language": [r"\benglish\b"]}}),
        encoding="utf-8")
    run = tmp_path / "run1"
    if with_artifact:
        (run / "a1" / "T1").mkdir(parents=True)
        (run / "a1" / "T1" / "answers.md").write_text(
            "the output language is English\n", encoding="utf-8")
    else:
        run.mkdir()
    scores = run / "scores.json"
    scores.write_text('{"a1/T1": {"verdict": "pass"}}', encoding="utf-8")
    digest = hashlib.sha256(scores.read_bytes()).hexdigest()
    (tmp_path / "conformance" / "history.json").write_text(json.dumps([
        {"agent": "a1", "run_dir": str(run), "date": "2026-08-26",
         "scores_sha256": digest, "skill_version": "0.1.605",
         "instrument_version": "0.1.605", "tasks": {"T1": "pass"}}]),
        encoding="utf-8")
    for attr, value in (("ROOT", tmp_path),
                        ("TASKS", tasks),
                        ("RESULTS", tmp_path / "conformance" / "results")):
        monkeypatch.setattr(run_conformance, attr, value)
    return run


def test_score_prints_the_note_and_keeps_the_bytes(tmp_path, monkeypatch,
                                                   capsys):
    run = _scorable(tmp_path, monkeypatch)
    run_conformance.main(["score", "--run", str(run)])
    out = capsys.readouterr().out
    assert "about to replace" in out, out[-500:]
    assert (run / "scores.0.1.605-instruments.json").exists(), (
        "score replaced the pinned bytes without keeping them")


def test_score_reports_the_pin_on_the_empty_exit_too(tmp_path, monkeypatch,
                                                     capsys):
    """The total destruction, which the partial-case check could not reach.

    A `--run` pointing one directory too high, or at a tidied results tree,
    matches no agent and no task. `scores.json` becomes `{}` and the command
    returns before the note — so every row pinning that run is unresolvable,
    permanently, and nothing says a word about evidence.
    """
    run = _scorable(tmp_path, monkeypatch, with_artifact=False)
    assert run_conformance.main(["score", "--run", str(run)]) == 1
    out = capsys.readouterr().out
    assert "NOT MEASURED" in out
    assert (run / "scores.json").read_text(encoding="utf-8").strip() == "{}"
    assert "about to replace" in out, (
        "the pin was destroyed completely and the command said nothing")
    assert (run / "scores.0.1.605-instruments.json").exists()
