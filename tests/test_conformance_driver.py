"""The conformance driver, proven able to drive, to time out, and to refuse.

Until 0.1.454 nothing in this repository invoked an agent: `run` wrote a prompt
file and asked a person to do it. So this file is the first test of a code path
that did not exist, and the discipline is the usual one — every outcome is
demonstrated, not just the good one, because a driver only ever seen succeeding
is FM-01 with a subprocess in it.

No real agent is invoked here. The registry's `drive` argv is replaced with a
python one-liner that behaves like an agent would: writes the deliverable, or
hangs, or exits non-zero, or is not on PATH at all.
"""
import ast
import json
import sys

import run_conformance as rc

TASK = {"id": "T-test", "prompt": "write the file", "deliverable": "*.md"}


def _agent(argv):
    return {"id": "fake", "capability": "full", "drive": argv}


def _writes(name="answers.md", body="done"):
    return [sys.executable, "-c",
            f"import pathlib,sys; pathlib.Path({name!r}).write_text({body!r}); "
            f"print('wrote', {name!r})"]


def test_a_driven_task_returns_its_artifact_and_its_transcript(tmp_path):
    out = rc.drive(_agent(_writes()), TASK, tmp_path)
    assert out["verdict"] == "driven"
    assert out["exit_code"] == 0
    assert out["produced"] == ["answers.md"]
    assert (tmp_path / "answers.md").read_text() == "done"
    # The transcript is the evidence that a run happened at all.
    assert "wrote" in (tmp_path / "transcript.txt").read_text()


def test_the_agent_runs_outside_this_repository(tmp_path):
    # THE ONE THAT MATTERS. An agent started inside the tree reads this repo's
    # maintenance CLAUDE.md and behaves like a maintainer of the skill rather
    # than a consumer of it.
    argv = [sys.executable, "-c",
            "import pathlib; pathlib.Path('cwd.md').write_text(str(pathlib.Path.cwd()))"]
    rc.drive(_agent(argv), TASK, tmp_path)
    where = (tmp_path / "cwd.md").read_text()
    assert str(rc.ROOT) not in where, f"the agent ran inside the repository: {where}"


def test_a_hanging_agent_is_abandoned_and_says_so(tmp_path):
    slow = [sys.executable, "-c", "import time; time.sleep(30)"]
    out = rc.drive(_agent(slow), TASK, tmp_path, timeout=1)
    assert out["verdict"] == "timeout"
    assert out["exit_code"] is None


def test_a_failing_cli_is_a_driver_failure_not_a_driven_run(tmp_path):
    # `exit_code` was recorded and never read, so a CLI that rejected its own
    # arguments — a renamed flag, expired auth, a rate limit — completed in a
    # second having written nothing and was recorded as "driven". `score` then
    # found no deliverable and put an agent-shaped failure on the board for an
    # invocation that never reached the agent.
    out = rc.drive(_agent([sys.executable, "-c", "raise SystemExit(3)"]), TASK, tmp_path)
    assert out["verdict"] == "driver failed"
    assert out["exit_code"] == 3
    assert "exited 3" in out["detail"]
    assert out["produced"] == [], "a failed run must not claim an artifact"


def test_an_agent_that_cannot_start_is_reported_not_raised(tmp_path):
    out = rc.drive(_agent([str(tmp_path / "no_such_binary")]), TASK, tmp_path)
    assert out["verdict"] == "could not start"


def test_a_platform_with_no_drive_argv_is_refused_by_name(tmp_path):
    out = rc.drive({"id": "an-ide", "capability": "full"}, TASK, tmp_path)
    assert out["verdict"] == "no driver"
    assert "an-ide" in out["detail"] and "by hand" in out["detail"]


def test_a_pinned_model_is_passed_through_and_recorded(tmp_path):
    argv = [sys.executable, "-c",
            "import sys,pathlib; pathlib.Path('m.md').write_text(' '.join(sys.argv[1:]))"]
    out = rc.drive(_agent(argv), TASK, tmp_path, model="a-model")
    assert out["model"] == "a-model"
    assert "--model a-model" in (tmp_path / "m.md").read_text()


def test_an_unpinned_run_records_that_it_was_unpinned(tmp_path):
    # Not blank: a board cell that says nothing about the model reads as a
    # claim about the agent rather than about one of its configurations.
    out = rc.drive(_agent(_writes()), TASK, tmp_path)
    assert "default" in out["model"]


def test_every_shipped_driver_is_an_argv_list_driven_non_interactively(tmp_path):
    # The registry's `invoke` field is prose for a human ("say 'in LUMI
    # style…'"), and driving on it would try to execute a sentence.
    #
    # Not a hand-kept list of platform ids: the set is every record that
    # declares a driver, so adding one to the registry brings it under this
    # test instead of past it.
    agents = [a for a in json.loads(
        rc.REGISTRY.read_text(encoding="utf-8"))["platforms"] if a.get("drive")]
    assert len(agents) >= 3, "the shipped drivers went missing from the registry"
    for a in agents:
        argv = a["drive"]
        assert isinstance(argv, list) and argv, f"{a['id']} declares no drive argv"
        assert all(isinstance(x, str) for x in argv)
        # Non-interactive is the whole point, and the flag that does it is
        # either in the argv (a positional prompt: Claude Code, Cursor) or
        # declared as the flag the prompt is the VALUE of (Gemini).
        assert "-p" in argv or a.get("drive_prompt_flag"), \
            f"{a['id']} must be driven non-interactively"


def test_a_declared_prompt_flag_lands_immediately_before_the_prompt(tmp_path):
    # Gemini's `-p` takes the prompt as its value, and the prompt is appended
    # last. Put the flag in the registry's `drive` argv and every optional flag
    # — `--model` above all — lands between them, so the CLI receives the model
    # NAME as its prompt and the real prompt as an interactive-mode positional:
    # a run that reaches the model, answers the wrong question, and reports
    # exit 0. The flag therefore belongs where the driver puts it, not where
    # the registry lists it.
    argv = [sys.executable, "-c",
            "import sys,pathlib; pathlib.Path('a.md').write_text(repr(sys.argv[1:]))"]
    agent = dict(_agent(argv), drive_prompt_flag="-p")
    rc.drive(agent, TASK, tmp_path, model="a-model")
    got = ast.literal_eval((tmp_path / "a.md").read_text())
    assert got[-2:] == ["-p", TASK["prompt"]], got
    assert "--model" in got and got.index("--model") < got.index("-p")


# An interrupted run does not earn a verdict. The board withdrew a recorded
# `fail` by hand at 0.1.450 for exactly this — an agent killed mid-run, scored
# on the draft it left — and the rule lived only in a person's judgement until
# `run --drive` began producing the situation automatically.

def _run_tree(tmp_path, driver=None, deliverable="answers.md"):
    task_dir = tmp_path / "run" / "an-agent" / "T3-recall"
    task_dir.mkdir(parents=True)
    (task_dir / "PROMPT.txt").write_text("the prompt", encoding="utf-8")
    if deliverable:
        (task_dir / deliverable).write_text("1. english\n", encoding="utf-8")
    if driver is not None:
        (task_dir / "driver.json").write_text(json.dumps(driver), encoding="utf-8")
    return tmp_path / "run"


def _score(run_dir, monkeypatch, capsys):
    monkeypatch.setattr(rc, "RESULTS", run_dir.parent)
    rc.main(["score", "--run", str(run_dir)])
    capsys.readouterr()
    return json.loads((run_dir / "scores.json").read_text(encoding="utf-8"))


def test_a_timed_out_task_is_not_earned_rather_than_failed(tmp_path, monkeypatch, capsys):
    run = _run_tree(tmp_path, driver={"verdict": "timeout", "seconds": 1500.0})
    entry = _score(run, monkeypatch, capsys)["an-agent/T3-recall"]
    assert entry["verdict"] == "not earned"
    assert "timeout" in entry["detail"] and "draft" in entry["detail"]


def test_a_task_that_could_not_start_is_not_earned_either(tmp_path, monkeypatch, capsys):
    run = _run_tree(tmp_path, driver={"verdict": "could not start"})
    assert _score(run, monkeypatch, capsys)["an-agent/T3-recall"]["verdict"] == "not earned"


def test_a_completed_run_is_still_scored_normally(tmp_path, monkeypatch, capsys):
    # The gate must not swallow real results: a driver that finished says so.
    run = _run_tree(tmp_path, driver={"verdict": "driven", "exit_code": 0,
                                      "seconds": 12.0})
    assert _score(run, monkeypatch, capsys)["an-agent/T3-recall"]["verdict"] in ("pass", "fail")


def test_a_hand_driven_task_needs_no_driver_record(tmp_path, monkeypatch, capsys):
    # Every row this board carried before 0.1.454 was hand-driven and has no
    # driver.json at all; the gate must be invisible to them.
    run = _run_tree(tmp_path, driver=None)
    assert _score(run, monkeypatch, capsys)["an-agent/T3-recall"]["verdict"] in ("pass", "fail")


def test_a_half_written_driver_record_is_not_earned(tmp_path, monkeypatch, capsys):
    # A process killed while writing leaves a half driver.json as easily as a
    # half deliverable, and treating the unparseable case as "no record" turned
    # that into the outcome the not-earned guard exists to prevent: a draft
    # scored as a result.
    task_dir = tmp_path / "run" / "an-agent" / "T3-recall"
    task_dir.mkdir(parents=True)
    (task_dir / "PROMPT.txt").write_text("the prompt", encoding="utf-8")
    (task_dir / "answers.md").write_text("1. english\n", encoding="utf-8")
    (task_dir / "driver.json").write_text("{not json", encoding="utf-8")
    entry = _score(tmp_path / "run", monkeypatch, capsys)["an-agent/T3-recall"]
    assert entry["verdict"] == "not earned"
    assert "killed mid-write" in entry["detail"]


def test_the_skill_directory_is_handed_to_the_agent(tmp_path):
    # The defect this exists to stop: a CLI driven with -p in a temporary
    # directory confines its reads to that directory, so an agent gets SKILL.md
    # from the platform and cannot open the tokens/ beside it. Three runs of one
    # agent invented a palette each and said why in their transcripts, and the
    # harness recorded it as the agent's doing.
    # A real executable, because the flag is INSERTED after the binary rather
    # than appended: `claude --help` declares --add-dir variadic, so appending
    # it makes the prompt a directory and the CLI exits in a second. A fake
    # built from `python -c` cannot test that ordering — the insertion would
    # land between the interpreter and its own flag.
    fake = tmp_path / "fake-cli"
    fake.write_text('#!/bin/sh\necho "$@" > "$(dirname "$0")/a.md"\n', encoding="utf-8")
    fake.chmod(0o755)
    agent = {"id": "fake", "capability": "full", "drive": [str(fake), "-p"],
             "drive_skill_flag": "--add-dir",
             "skill_paths": ["~/.somewhere/skills/lumi-style"]}
    rc.drive(agent, TASK, tmp_path)
    passed = (tmp_path / "a.md").read_text()
    assert passed.startswith("--add-dir "), \
        f"the flag must come first or it swallows the prompt: {passed!r}"
    assert "~" not in passed, "the path must be expanded, not handed over as a tilde"
    assert "/skills/lumi-style" in passed
    assert passed.rstrip().endswith(TASK["prompt"]), "the prompt must survive"


def test_a_platform_declaring_no_skill_flag_is_driven_unchanged(tmp_path):
    fake = tmp_path / "fake-cli"
    fake.write_text('#!/bin/sh\necho "$@" > "$(dirname "$0")/b.md"\n', encoding="utf-8")
    fake.chmod(0o755)
    rc.drive({"id": "fake", "capability": "full", "drive": [str(fake), "-p"],
              "skill_paths": ["~/x"]}, TASK, tmp_path)
    assert "--add-dir" not in (tmp_path / "b.md").read_text()


# The environment is PROVEN clear before a verdict is attributed to anything.
# Three runs were published as agent failures on 2026-08-13 before anyone read
# the transcript saying the agent could not open tokens/ at all.

def test_a_reachable_skill_passes_the_environment_check(tmp_path):
    for rel in rc.SKILL_SURFACE:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.mkdir() if "." not in target.name else target.write_text("x")
    agent = {"id": "fake", "skill_paths": [str(tmp_path)],
             "drive_skill_flag": "--add-dir"}
    assert rc.environment_check(agent) == []


def test_an_unreachable_surface_is_named_with_its_path(tmp_path):
    # The live failure: SKILL.md arrives through the platform, tokens/ does not.
    (tmp_path / "SKILL.md").write_text("x")
    agent = {"id": "fake", "skill_paths": [str(tmp_path)],
             "drive_skill_flag": "--add-dir"}
    errors = rc.environment_check(agent)
    assert errors and "cannot reach the skill" in errors[0]
    assert str(tmp_path) in errors[0], "the path it tried must be named"


def test_a_platform_that_cannot_be_handed_its_skill_is_refused(tmp_path):
    # Reachable on disk is not the same as reachable BY THE AGENT: without the
    # flag the driver cannot pass the directory, which is exactly the shape of
    # the original defect.
    for rel in rc.SKILL_SURFACE:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.mkdir() if "." not in target.name else target.write_text("x")
    errors = rc.environment_check({"id": "fake", "skill_paths": [str(tmp_path)]})
    assert errors and "drive_skill_flag" in errors[0]


def test_a_platform_with_no_skill_path_is_refused(tmp_path):
    errors = rc.environment_check({"id": "an-ide"})
    assert errors and "nothing to prove reachable" in errors[0]


def test_an_environment_skip_is_not_earned_rather_than_failed(tmp_path, monkeypatch, capsys):
    run = _run_tree(tmp_path, driver={"verdict": "environment",
                                      "detail": "cannot reach tokens/"})
    entry = _score(run, monkeypatch, capsys)["an-agent/T3-recall"]
    assert entry["verdict"] == "not earned"


def test_a_blocked_agent_is_never_driven(tmp_path, monkeypatch, capsys):
    """The call site, not just the function.

    Deleting the eight-line block in `run --drive` left all tests passing: the
    four unit tests above call `environment_check` directly and the fifth writes
    driver.json by hand, so the only thing making it a gate rather than a dead
    function was unproven. That is convention 11's failure shape verbatim.
    """
    run_dir = tmp_path / "run"
    marker = tmp_path / "the-agent-ran"
    fake = tmp_path / "fake-cli"
    fake.write_text(f'#!/bin/sh\ntouch "{marker}"\n', encoding="utf-8")
    fake.chmod(0o755)

    agents = [{"id": "blocked", "name": "Blocked", "capability": "full",
               "drive": [str(fake), "-p"], "drive_skill_flag": "--add-dir",
               # an empty directory: the skill is not here
               "skill_paths": [str(tmp_path / "nothing")],
               "probe": ["true"]}]
    tasks = [{"id": "T3-recall", "prompt": "answer", "deliverable": "*.md",
              "min_capability": "prompt", "score": ["recall"], "answers": {}}]
    monkeypatch.setattr(rc, "load_agents", lambda: agents)
    monkeypatch.setattr(rc, "load_tasks", lambda: tasks)
    monkeypatch.setattr(rc, "detect", lambda a: (True, "fake 1.0"))

    rc.main(["run", "--drive", "--run", str(run_dir)])
    printed = capsys.readouterr().out
    assert "SKIPPED" in printed
    assert not marker.exists(), "a blocked agent must not be invoked at all"
    record = json.loads((run_dir / "blocked" / "T3-recall" / "driver.json")
                        .read_text(encoding="utf-8"))
    assert record["verdict"] == "environment"


def test_a_run_where_nothing_could_be_driven_does_not_report_success(
        tmp_path, monkeypatch, capsys):
    # `driven` counts only successes and skipped agents incremented nothing, so
    # a run blocked on every task printed its SKIPPED lines and returned 0. Agent
    # RESULTS are non-deterministic and must not gate; the harness being unable
    # to invoke anything is deterministic and operator-fixable.
    run_dir = tmp_path / "run"
    agents = [{"id": "blocked", "name": "Blocked", "capability": "full",
               "drive": ["/bin/true"], "drive_skill_flag": "--add-dir",
               "skill_paths": [str(tmp_path / "nothing")], "probe": ["true"]}]
    tasks = [{"id": "T3-recall", "prompt": "answer", "deliverable": "*.md",
              "min_capability": "prompt", "score": ["recall"], "answers": {}}]
    monkeypatch.setattr(rc, "load_agents", lambda: agents)
    monkeypatch.setattr(rc, "load_tasks", lambda: tasks)
    monkeypatch.setattr(rc, "detect", lambda a: (True, "fake 1.0"))
    code = rc.main(["run", "--drive", "--run", str(run_dir)])
    assert "NOTHING RAN" in capsys.readouterr().out
    assert code == 1


# 0.1.531 — the effort axis, recorded as what was PINNED, and a conformance
# trace per driven task (GAP-014's second half: the matrix reads real rows).

def _echo_argv():
    return [sys.executable, "-c",
            "import pathlib,sys; pathlib.Path('answers.md').write_text(' '.join(sys.argv[1:]))"]


def test_effort_is_passed_only_through_a_declared_flag_and_recorded_as_pinned(tmp_path):
    agent = {**_agent(_echo_argv()), "drive_effort_flag": "--effort"}
    out = rc.drive(agent, TASK, tmp_path, effort="low")
    assert out["effort"] == "low"
    assert "--effort low" in (tmp_path / "answers.md").read_text()


def test_effort_on_an_agent_with_no_flag_is_recorded_as_not_pinned(tmp_path):
    out = rc.drive(_agent(_echo_argv()), TASK, tmp_path, effort="low")
    assert out["effort"] == "(not pinned)"
    assert "--effort" not in (tmp_path / "answers.md").read_text()


def test_a_driven_task_with_a_storyline_leaves_a_closed_conformance_trace(tmp_path, monkeypatch):
    import os
    import pathlib
    store = tmp_path / "traces"
    monkeypatch.setenv("LUMI_TRACES", str(store))
    wd = tmp_path / "wd"
    wd.mkdir()
    deck = pathlib.Path(rc.ROOT / "fixtures" / "deck-pass.en.html")
    (wd / "deck.en.html").write_text(deck.read_text(encoding="utf-8"), encoding="utf-8")
    task = {"id": "T1-deck", "genre": "internal", "storyline": "status-report",
            "deliverable": "*.html"}
    record = {"verdict": "driven", "seconds": 12.4, "produced": ["deck.en.html"],
              "model": "claude-sonnet-5", "effort": "low"}
    note = rc._conformance_trace({"id": "fake"}, task, wd, record)
    assert "closed (source: conformance)" in note, note
    recs = [json.loads(p.read_text()) for p in store.glob("t-*.json")]
    assert len(recs) == 1
    rec = recs[0]
    assert rec["source"] == "conformance" and rec["closed_at"]
    assert rec["phase_seconds"] == {"build": 12}
    assert rec["model"] == "claude-sonnet-5" and rec["effort"] == "low"
    assert os.environ["LUMI_TRACES"] == str(store)


def test_a_drive_that_did_not_finish_leaves_its_trace_open(tmp_path, monkeypatch):
    store = tmp_path / "traces"
    monkeypatch.setenv("LUMI_TRACES", str(store))
    task = {"id": "T1-deck", "genre": "internal", "storyline": "status-report",
            "deliverable": "*.html"}
    note = rc._conformance_trace({"id": "fake"}, task, tmp_path,
                                 {"verdict": "timeout", "produced": []})
    assert "left open" in note
    rec = json.loads(next(store.glob("t-*.json")).read_text())
    assert rec["closed_at"] is None


def test_a_task_without_a_storyline_opens_no_trace(tmp_path, monkeypatch):
    monkeypatch.setenv("LUMI_TRACES", str(tmp_path / "traces"))
    note = rc._conformance_trace({"id": "fake"}, TASK, tmp_path,
                                 {"verdict": "driven", "produced": ["answers.md"]})
    assert "declares no storyline" in note
    assert not (tmp_path / "traces").exists()


def test_usage_is_read_from_a_json_transcript_and_only_when_both_counts_are_integers():
    tail = '{"result": "ok", "usage": {"input_tokens": 1200, "output_tokens": 340}}'
    assert rc._usage_from_transcript("noise\n" + tail) == {"input_tokens": 1200,
                                                          "output_tokens": 340}
    assert rc._usage_from_transcript('{"usage": {"input_tokens": 1}}') is None
    assert rc._usage_from_transcript("plain text transcript") is None


def test_a_usage_dump_reaches_the_trace(tmp_path, monkeypatch):
    import pathlib
    store = tmp_path / "traces"
    monkeypatch.setenv("LUMI_TRACES", str(store))
    wd = tmp_path / "wd"
    wd.mkdir()
    deck = pathlib.Path(rc.ROOT / "fixtures" / "deck-pass.en.html")
    (wd / "deck.en.html").write_text(deck.read_text(encoding="utf-8"), encoding="utf-8")
    task = {"id": "T1-deck", "genre": "internal", "storyline": "status-report",
            "deliverable": "*.html"}
    record = {"verdict": "driven", "seconds": 3, "produced": ["deck.en.html"],
              "model": "m", "effort": "high",
              "usage": {"input_tokens": 1200, "output_tokens": 340}}
    assert "closed" in rc._conformance_trace({"id": "fake"}, task, wd, record)
    rec = json.loads(next(store.glob("t-*.json")).read_text())
    assert (rec["input_tokens"], rec["output_tokens"]) == (1200, 340)


def test_a_run_outside_results_never_touches_the_latest_link(tmp_path, monkeypatch):
    """Ten CI runs went red at 0.1.528: `run` tried to repoint
    results/latest inside a directory CI does not have. A --run elsewhere
    is the caller's directory and gets no link; a link failure is a note."""
    monkeypatch.setattr(rc, "RESULTS", tmp_path / "results-absent")
    run_dir = tmp_path / "elsewhere"
    run_dir.mkdir()
    code = rc.main(["run", "--run", str(run_dir), "--agent", "fake"]) \
        if hasattr(rc, "main") else 0
    assert code in (0, 1)
    assert not (tmp_path / "results-absent" / "latest").exists()
