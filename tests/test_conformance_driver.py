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
import time

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


def test_a_silent_agent_is_collected_at_its_base_budget(tmp_path):
    slow = [sys.executable, "-c", "import time; time.sleep(30)"]
    out = rc.drive(_agent(slow), TASK, tmp_path, base=1)
    assert out["verdict"] == "stall"
    assert out["exit_code"] is None
    # The detail describes the collection, not something else that happened to
    # be true. Until 0.1.555 the verdict was decided first and described last,
    # so a collected run whose file had landed somewhere odd was recorded
    # `timeout` with a detail about a misplaced artifact.
    assert "collected after" in out["detail"]
    assert out["budget"]["ended"] == "stall"


def _budget(tmp_path, body, base=1, grace=2, cap=30, **kw):
    return rc._run_with_budget([sys.executable, "-c", body], tmp_path,
                               base, cap, grace, poll=0.1, **kw)


def test_a_run_that_keeps_talking_outlives_its_base_budget(tmp_path):
    # The measured case this exists for: an agent killed at a fixed ceiling
    # while it was still writing. Signs of life renew the budget.
    talker = ("import sys, time\n"
              "for _ in range(12):\n"
              "    print('{\"type\":\"tool\"}', flush=True); time.sleep(0.2)\n")
    started = time.monotonic()
    code, out, record = _budget(tmp_path, talker)
    assert code == 0, "a run that kept reporting progress must not be collected"
    assert time.monotonic() - started > 1, "it never outlived the base budget"
    assert record["ended"] == "exit"
    assert record["events"] >= 12
    assert out.count(b"tool") == 12


def test_a_run_that_goes_quiet_is_collected_early(tmp_path):
    # And the other half: renewal is not an excuse to wait out the hard cap.
    quiet = ("import time\n"
             "print('{\"type\":\"tool\"}', flush=True)\n"
             "time.sleep(60)\n")
    started = time.monotonic()
    code, _out, record = _budget(tmp_path, quiet, base=1, grace=2, cap=30)
    spent = time.monotonic() - started
    assert code is None
    assert record["ended"] == "stall"
    assert spent < 15, f"it waited for the hard cap instead of the stall: {spent}s"


def test_the_hard_cap_holds_against_a_run_that_never_stops_talking(tmp_path):
    forever = ("import time\n"
               "while True:\n"
               "    print('{\"type\":\"tool\"}', flush=True); time.sleep(0.1)\n")
    started = time.monotonic()
    code, _out, record = _budget(tmp_path, forever, base=1, grace=5, cap=3)
    assert code is None
    assert record["ended"] == "hard cap"
    assert time.monotonic() - started < 25


def test_a_written_file_is_a_sign_of_life_when_nothing_streams(tmp_path):
    # Hermes streams nothing and writes its deck to HOME, so the artifact's
    # mtime is the only evidence from outside the process that it is working.
    where = tmp_path / "out"
    where.mkdir()
    writer = (f"import time, pathlib\n"
              f"for i in range(20):\n"
              f"    pathlib.Path({str(where)!r}, 'answers.md').write_text(str(i))\n"
              f"    time.sleep(0.2)\n")
    code, _out, record = _budget(tmp_path, writer, base=1, grace=2, cap=30,
                                 watch=((where, "answers.md"),),
                                 signal_kind="artifact")
    assert code == 0, "the file kept changing; that is progress"
    assert record["signal"] == "artifact"
    assert record["events"] >= 1


def test_a_collected_run_leaves_no_children_behind(tmp_path):
    # SIGKILL on the parent alone orphaned the browsers these CLIs start. The
    # child here outlives its parent unless the whole group is signalled.
    marker = tmp_path / "orphan.txt"
    parent = (f"import subprocess, sys, time\n"
              f"subprocess.Popen([sys.executable, '-c',\n"
              f"  \"import time, pathlib; time.sleep(3);"
              f" pathlib.Path({str(marker)!r}).write_text('alive')\"])\n"
              f"time.sleep(60)\n")
    code, _out, _record = _budget(tmp_path, parent, base=1, grace=1, cap=20)
    assert code is None
    time.sleep(4)
    assert not marker.exists(), "the grandchild survived the collection"


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


# WROTE NOTHING vs WROTE IT SOMEWHERE ELSE. Two agents have produced the second
# and the board recorded both as the first. The cost is measured: one misplaced
# deck passed check_design, check_prose and inspect_layout --deliverable with no
# failure at all, and its board cell read `no deliverable`.

def _elsewhere(target):
    """An agent that writes its artifact to an absolute path of its own."""
    return [sys.executable, "-c",
            f"import pathlib; pathlib.Path({str(target)!r}).write_text('done')"]


def test_a_file_written_outside_the_workdir_is_named_not_ignored(tmp_path, monkeypatch):
    home = tmp_path / "elsewhere"
    home.mkdir()
    monkeypatch.setattr(rc.pathlib.Path, "home", staticmethod(lambda: home))
    out = rc.drive(_agent(_elsewhere(home / "answers.md")), TASK, tmp_path)
    assert out["verdict"] == "misplaced", out
    assert out["produced"] == [], "a misplaced file is never claimed as produced"
    assert str(home / "answers.md") in out["misplaced"]
    assert str(home / "answers.md") in out["detail"]


def test_a_misplaced_file_is_not_copied_into_the_run(tmp_path, monkeypatch):
    # Scoring it would launder a run that missed the task's own instruction
    # into a pass. The run names the path and imports nothing.
    home = tmp_path / "elsewhere"
    home.mkdir()
    monkeypatch.setattr(rc.pathlib.Path, "home", staticmethod(lambda: home))
    rc.drive(_agent(_elsewhere(home / "answers.md")), TASK, tmp_path)
    assert not (tmp_path / "answers.md").exists()


def test_a_file_that_predates_the_run_is_not_blamed_on_it(tmp_path, monkeypatch):
    # The sweep is by mtime, and a stale `answers.md` someone left in their home
    # directory last year must not become this run's finding.
    home = tmp_path / "elsewhere"
    home.mkdir()
    old = home / "answers.md"
    old.write_text("from another day")
    import os
    os.utime(old, (1, 1))
    monkeypatch.setattr(rc.pathlib.Path, "home", staticmethod(lambda: home))
    out = rc.drive(_agent([sys.executable, "-c", "pass"]), TASK, tmp_path)
    assert out["verdict"] == "driven"
    assert out["misplaced"] == []


def test_a_correct_run_reports_no_misplaced_write(tmp_path, monkeypatch):
    home = tmp_path / "elsewhere"
    home.mkdir()
    monkeypatch.setattr(rc.pathlib.Path, "home", staticmethod(lambda: home))
    out = rc.drive(_agent(_writes()), TASK, tmp_path)
    assert out["verdict"] == "driven"
    assert out["misplaced"] == []


def test_a_file_written_into_the_runs_own_folder_counts_as_produced(tmp_path):
    # An agent told to write "in the working directory", unable to see the
    # driver's cwd, looked for where input.md lives and wrote beside it. That
    # is this folder — the driver leaves a copy of the input here too — and it
    # is where the driver copies the artifact anyway. Before this, `score`
    # graded the file and the driver record beside it said `produced: []`.
    (tmp_path / "input.md").write_text("the input", encoding="utf-8")
    argv = [sys.executable, "-c",
            f"import pathlib; pathlib.Path({str(tmp_path / 'answers.md')!r})"
            f".write_text('done')"]
    out = rc.drive(_agent(argv), TASK, tmp_path)
    assert out["verdict"] == "driven"
    assert out["produced"] == ["answers.md"]
    assert "run's own folder" in out["detail"]
    # The copy step must not copy the file onto itself and truncate it.
    assert (tmp_path / "answers.md").read_text() == "done"


def test_the_input_is_never_mistaken_for_the_artifact(tmp_path):
    # `input.md` matches a `*.md` deliverable, sits in this folder by the
    # driver's own hand, and predates the run. Counting it would report every
    # T2 run as having produced something.
    (tmp_path / "input.md").write_text("the input", encoding="utf-8")
    out = rc.drive(_agent([sys.executable, "-c", "pass"]), TASK, tmp_path)
    assert out["produced"] == []
    assert out["verdict"] == "driven"


def test_effort_in_the_model_id_pins_both_axes(tmp_path):
    # Cursor ships Grok 4.6 as one model id per level — `cursor-grok-4.6-low`,
    # `-medium`, `-high` — so there is no flag for a separate effort to go in.
    # Without the template the matrix gets three model rows at "(not pinned)"
    # effort: a deliberate comparison filed under unknown.
    argv = [sys.executable, "-c",
            "import sys,pathlib; pathlib.Path('a.md').write_text(' '.join(sys.argv[1:]))"]
    agent = dict(_agent(argv), drive_effort_in_model="{model}-{effort}")
    out = rc.drive(agent, TASK, tmp_path, model="cursor-grok-4.6", effort="high")
    assert out["model"] == "cursor-grok-4.6-high"
    assert out["effort"] == "high", "the level was pinned and must be recorded as pinned"
    assert "--model cursor-grok-4.6-high" in (tmp_path / "a.md").read_text()


def test_the_composed_model_does_not_also_get_an_effort_flag(tmp_path):
    # A platform declaring both would otherwise be handed `--effort high` on top
    # of a model id that already says high, which the CLI would reject.
    argv = [sys.executable, "-c",
            "import sys,pathlib; pathlib.Path('a.md').write_text(' '.join(sys.argv[1:]))"]
    agent = dict(_agent(argv), drive_effort_in_model="{model}-{effort}",
                 drive_effort_flag="--effort")
    rc.drive(agent, TASK, tmp_path, model="m", effort="low")
    assert "--effort" not in (tmp_path / "a.md").read_text()


def test_a_flag_platform_is_unaffected(tmp_path):
    argv = [sys.executable, "-c",
            "import sys,pathlib; pathlib.Path('a.md').write_text(' '.join(sys.argv[1:]))"]
    agent = dict(_agent(argv), drive_effort_flag="--reasoning")
    out = rc.drive(agent, TASK, tmp_path, model="m", effort="medium")
    assert out["model"] == "m" and out["effort"] == "medium"
    assert "--reasoning medium" in (tmp_path / "a.md").read_text()


def test_effort_without_a_model_refuses_to_run(tmp_path):
    """The template needs both halves, and from 0.1.554 the driver REFUSES
    rather than recording "(not pinned)" and carrying on.

    The earlier ruling — "recording (not pinned) is the honest outcome;
    inventing a model name to hang the level on is not" — was honest about the
    RECORD and silent on the console. A whole comparison round was then reported
    as "Cursor at high effort" when Cursor had run on the server's default model
    at the server's default level, and the matrix row the flag exists to fill was
    dropped without a word. Owner ruling 2026-08-22: pin it, or fail.
    """
    import pytest
    argv = [sys.executable, "-c",
            "import sys,pathlib; pathlib.Path('a.md').write_text(' '.join(sys.argv[1:]))"]
    agent = dict(_agent(argv), drive_effort_in_model="{model}-{effort}")
    with pytest.raises(SystemExit) as exc:
        rc.drive(agent, TASK, tmp_path, effort="high")
    assert "no --model" in str(exc.value)


def test_effort_with_a_model_still_composes(tmp_path):
    """The refusal must not swallow the case it exists to protect."""
    argv = [sys.executable, "-c",
            "import sys,pathlib; pathlib.Path('a.md').write_text(' '.join(sys.argv[1:]))"]
    agent = dict(_agent(argv), drive_effort_in_model="{model}-{effort}")
    out = rc.drive(agent, TASK, tmp_path, model="cursor-grok-4.6", effort="high")
    assert out["effort"] == "high"
    assert out["model"] == "cursor-grok-4.6-high"


def test_the_top_efforts_are_expressible():
    """`--effort` accepted only low|medium|high, so the highest level a
    comparison could ask for was `high` — on agents whose CLIs document `xhigh`
    and `max`, and on Cursor whose Grok 4.6 tops out at `xhigh`."""
    import contextlib
    import io
    for level in ("xhigh", "max"):
        buf = io.StringIO()
        with contextlib.suppress(SystemExit), contextlib.redirect_stderr(buf):
            rc.main(["run", "--effort", level, "--agent", "no-such-agent"])
        assert "invalid choice" not in buf.getvalue(), level


# THE TWO BOARDS ASK DIFFERENT QUESTIONS. Conformance asks whether the agent did
# the task as stated, and the task states the working directory. The cost trace
# asks how many tokens a model at an effort spent per content page, which a
# file's location cannot change. Of the first four matrix cells driven on
# 2026-08-21, two were misplaced and contributed no trace, so the matrix the
# runs existed for could not be filled by them.

def _trace_task():
    return {"id": "T-trace", "prompt": "make a deck", "deliverable": "*.html",
            "storyline": "status-report", "genre": "internal"}


def test_a_misplaced_artifact_still_closes_its_cost_trace(tmp_path, monkeypatch):
    calls: list = []

    def _record(argv, **kw):
        calls.append(argv)
        return _ok("t-abc")

    monkeypatch.setattr(rc.subprocess, "run", _record)
    record = {"verdict": "misplaced", "produced": [], "seconds": 12,
              "misplaced": [str(tmp_path / "elsewhere" / "deck.en.html")],
              "model": "m", "effort": "high"}
    out = rc._conformance_trace({"id": "a"}, _trace_task(), tmp_path, record)
    assert "closed" in out, out
    closed = calls[-1]
    assert str(tmp_path / "elsewhere" / "deck.en.html") in closed
    assert "--model" in closed and "--effort" in closed


def test_a_timeout_is_still_refused(tmp_path, monkeypatch):
    # Its file is a draft, whatever its location, and a draft is not a result.
    monkeypatch.setattr(rc.subprocess, "run", lambda argv, **kw: _ok("t-abc"))
    record = {"verdict": "timeout", "produced": [], "seconds": 1800,
              "misplaced": [str(tmp_path / "deck.en.html")]}
    out = rc._conformance_trace({"id": "a"}, _trace_task(), tmp_path, record)
    assert "left open" in out


def test_a_misplaced_run_with_no_path_leaves_the_trace_open(tmp_path, monkeypatch):
    monkeypatch.setattr(rc.subprocess, "run", lambda argv, **kw: _ok("t-abc"))
    record = {"verdict": "misplaced", "produced": [], "misplaced": [], "seconds": 5}
    out = rc._conformance_trace({"id": "a"}, _trace_task(), tmp_path, record)
    assert "left open" in out


class _ok:
    def __init__(self, out):
        self.returncode, self.stdout, self.stderr = 0, out, ""


# THE RESULT OBJECT IS NOT ALWAYS LAST. The transcript is stdout AND stderr, and
# Claude Code's JSON result is followed by "Warning: no stdin data received in
# 3s". Every twelve-page run recorded `usage: null` because of that one line —
# a missing row on the cost board, which needs output tokens before it computes.

RESULT = ('{"is_error":false,"num_turns":14,'
          '"usage":{"input_tokens":24,"output_tokens":26911},"session_id":"x"}')


def test_usage_is_read_when_the_object_is_last():
    assert rc._usage_from_transcript("chatter\n" + RESULT) == {
        "input_tokens": 24, "output_tokens": 26911}


def test_usage_is_read_when_a_warning_follows_the_object():
    # The real shape, taken from a 2026-08-21 matrix run.
    text = RESULT + "\nWarning: no stdin data received in 3s, proceeding without it.\n"
    assert rc._usage_from_transcript(text) == {
        "input_tokens": 24, "output_tokens": 26911}


def test_a_transcript_with_no_object_is_still_none():
    # "not returned" must stay distinguishable from zero.
    assert rc._usage_from_transcript("Warning: something\nno json here") is None
    assert rc._usage_from_transcript("{}") is None


def test_a_non_integer_count_is_not_believed():
    assert rc._usage_from_transcript(
        '{"usage":{"input_tokens":"24","output_tokens":26911}}') is None


# SOME CLIS REPORT USAGE TO A FILE. Hermes writes `--usage-file <path>` and says
# nothing about tokens on stdout, so the transcript reader found none and its
# cells carried quality without cost: a clean eight-page deck and no row on the
# efficiency board.

def test_usage_is_read_from_a_file_the_cli_wrote(tmp_path):
    payload = ('{"input_tokens": 17952, "output_tokens": 12, '
               '"estimated_cost_usd": 0.0026, "model": "m"}')
    argv = [sys.executable, "-c",
            "import sys,pathlib;"
            "p=sys.argv[sys.argv.index('--usage-file')+1];"
            f"pathlib.Path(p).write_text({payload!r});"
            "pathlib.Path('answers.md').write_text('done')"]
    agent = dict(_agent(argv), drive_usage_file_flag="--usage-file")
    out = rc.drive(agent, TASK, tmp_path)
    assert out["usage"] == {"input_tokens": 17952, "output_tokens": 12}


def test_a_usage_file_that_was_never_written_is_none(tmp_path):
    agent = dict(_agent(_writes()), drive_usage_file_flag="--usage-file")
    out = rc.drive(agent, TASK, tmp_path)
    assert out["usage"] is None, "absent must stay absent, never zero"


def test_a_usage_file_with_non_integer_counts_is_not_believed(tmp_path):
    p = tmp_path / "u.json"
    p.write_text('{"input_tokens": null, "output_tokens": 12}', encoding="utf-8")
    assert rc._usage_from_file(p) is None
    p.write_text("not json at all", encoding="utf-8")
    assert rc._usage_from_file(p) is None


# TWO SPELLINGS. Cursor reports `inputTokens`/`outputTokens` in the same field of
# the same shape Claude Code fills as `input_tokens`/`output_tokens`. A reader
# that knew one of them reported "no usage" for the other in silence, and those
# runs carried a clean eight-page deck with no row on the cost board.

def test_camel_case_usage_is_read_too():
    text = ('{"type":"result","result":"ok","usage":'
            '{"inputTokens":19051,"outputTokens":73,"cacheReadTokens":2944}}')
    assert rc._usage_from_transcript(text) == {
        "input_tokens": 19051, "output_tokens": 73}


def test_snake_case_still_wins_when_both_are_present():
    # Not a real shape, but the order must be deterministic rather than
    # whichever key the dict happens to yield first.
    assert rc._two_counts({"input_tokens": 1, "output_tokens": 2,
                           "inputTokens": 9, "outputTokens": 9}) == {
        "input_tokens": 1, "output_tokens": 2}


def test_a_usage_file_of_bare_counts_is_read(tmp_path):
    p = tmp_path / "u.json"
    p.write_text('{"inputTokens": 5, "outputTokens": 6}', encoding="utf-8")
    assert rc._usage_from_file(p) == {"input_tokens": 5, "output_tokens": 6}


def test_partial_counts_are_refused():
    assert rc._two_counts({"inputTokens": 5}) is None
    assert rc._two_counts({"input_tokens": 5, "output_tokens": None}) is None


def test_every_flag_lands_before_the_trailing_prompt(tmp_path):
    # The usage-file flag was appended AFTER the prompt flag, so Hermes received
    # `-z --usage-file <path>` and read the flag name as its prompt, exiting in
    # 0.4s — the exact failure `drive_prompt_flag` exists to prevent, committed
    # by the code that implements it.
    argv = [sys.executable, "-c",
            "import sys,pathlib; pathlib.Path('a.md').write_text(repr(sys.argv[1:]))"]
    agent = dict(_agent(argv), drive_prompt_flag="-z",
                 drive_usage_file_flag="--usage-file")
    rc.drive(agent, TASK, tmp_path, model="m")
    got = ast.literal_eval((tmp_path / "a.md").read_text())
    assert got[-2:] == ["-z", TASK["prompt"]], got
    assert "--usage-file" in got and got.index("--usage-file") < got.index("-z")


def test_a_misplaced_artifact_is_kept_in_the_record(tmp_path, monkeypatch):
    # Not copying it in at all left a run directory with a transcript, a driver
    # record and no deliverable: the reviewer could not find what the run made.
    # It goes in a SUBdirectory, so the scorer's non-recursive glob still cannot
    # see it — scoring it would launder a run that missed the instruction.
    home = tmp_path / "elsewhere"
    home.mkdir()
    monkeypatch.setattr(rc.pathlib.Path, "home", staticmethod(lambda: home))
    out = rc.drive(_agent(_elsewhere(home / "answers.md")), TASK, tmp_path)
    assert out["verdict"] == "misplaced"
    assert (tmp_path / "misplaced" / "answers.md").read_text() == "done"
    assert not (tmp_path / "answers.md").exists(), "it must not be scorable"
    assert sorted(p.name for p in tmp_path.glob(TASK["deliverable"])) == []


# THE AGENT'S OWN WORD OUTRANKS THE CLOCK. Three agents driven in parallel can
# all write to HOME and to the checkout, and a sweep that sorts by mtime picks
# whichever landed last. On 2026-08-21 that put another agent's deck into
# Hermes's run record: it was scored as Hermes's and reviewed by the owner as
# Hermes's, while Hermes's real artifact — named in its own transcript, and a
# pass on every gate — sat unexamined.

def test_the_path_the_transcript_names_wins_over_the_newest_file(tmp_path, monkeypatch):
    home = tmp_path / "elsewhere"
    home.mkdir()
    mine, theirs = home / "answers.md", home / "other.md"
    theirs.write_text("someone else's, written later", encoding="utf-8")
    monkeypatch.setattr(rc.pathlib.Path, "home", staticmethod(lambda: home))
    task = dict(TASK, deliverable="*.md")
    argv = [sys.executable, "-c",
            f"import pathlib,os,time; p=pathlib.Path({str(mine)!r});"
            f"p.write_text('mine');"
            f"q=pathlib.Path({str(theirs)!r}); q.write_text('theirs');"
            f"print('wrote {mine}')"]
    out = rc.drive(_agent(argv), task, tmp_path)
    assert out["verdict"] == "misplaced"
    assert out["misplaced"][0] == str(mine), out["misplaced"]
    assert str(mine) in out["detail"]


def test_an_unnamed_candidate_is_still_listed_but_never_first(tmp_path, monkeypatch):
    # A file nobody claimed is a coincidence with a timestamp. It stays in the
    # record — a reviewer may want it — and it does not become the artifact.
    home = tmp_path / "elsewhere"
    home.mkdir()
    monkeypatch.setattr(rc.pathlib.Path, "home", staticmethod(lambda: home))
    task = dict(TASK, deliverable="*.md")
    argv = [sys.executable, "-c",
            f"import pathlib; pathlib.Path({str(home / 'stray.md')!r}).write_text('x')"]
    out = rc.drive(_agent(argv), task, tmp_path)
    assert out["misplaced"] == [str(home / "stray.md")]

