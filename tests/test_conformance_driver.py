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
import pathlib
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
    import platform_registry
    agents = [a for a in platform_registry.platforms() if a.get("drive")]
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


def test_a_task_that_dies_inside_a_driver_thread_is_counted_and_fails(
        tmp_path, monkeypatch, capsys):
    """`threading.excepthook` ignores SystemExit and prints the rest into
    interleaved output; neither counter moved either way, so a run where every
    task died reported `drove 0 task(s)` and exited 0."""
    skill = tmp_path / "skill"
    (skill / "references").mkdir(parents=True)
    (skill / "tokens").mkdir()
    for rel in ("SKILL.md", "AGENTS.md", "references/brand.md",
                "tokens/lumi-theme.css"):
        (skill / rel).write_text("x", encoding="utf-8")
    agents = [{"id": "fake", "name": "Fake", "capability": "full",
               "drive": ["/bin/true"], "probe": ["true"],
               "skill_paths": [str(skill)]}]
    tasks = [{"id": "T3-recall", "prompt": "answer", "deliverable": "*.md",
              "min_capability": "prompt", "score": ["recall"],
              "answers": {"q": ["a"]}}]
    monkeypatch.setattr(rc, "load_agents", lambda: agents)
    monkeypatch.setattr(rc, "load_tasks", lambda: tasks)
    monkeypatch.setattr(rc, "detect", lambda a: (True, "fake 1.0"))
    monkeypatch.setattr(rc, "environment_check", lambda a: [])

    def boom(*_a, **_k):
        raise RuntimeError("the driver fell over")
    monkeypatch.setattr(rc, "drive", boom)
    code = rc.main(["run", "--drive", "--run", str(tmp_path / "run")])
    out = capsys.readouterr().out
    assert "CRASHED" in out and "the driver fell over" in out
    assert code == 1


def test_a_run_where_every_task_was_refused_does_not_report_success(
        tmp_path, monkeypatch, capsys):
    """A refusal is a task that did not run, and `NOTHING RAN` keys on that.

    0.1.640 made the refusal visible and left it counting as nothing, so a run
    where every task was refused printed `drove 0 task(s)` and exited 0 — the
    half of the finding the fix did not close.
    """
    skill = tmp_path / "skill"
    (skill / "references").mkdir(parents=True)
    (skill / "tokens").mkdir()
    for rel in ("SKILL.md", "AGENTS.md", "references/brand.md",
                "tokens/lumi-theme.css"):
        (skill / rel).write_text("x", encoding="utf-8")
    agents = [{"id": "fake", "name": "Fake", "capability": "full",
               "drive": ["/bin/true"], "drive_effort_in_model": "{model}-{effort}",
               "probe": ["true"], "skill_paths": [str(skill)]}]
    tasks = [{"id": "T3-recall", "prompt": "answer", "deliverable": "*.md",
              "min_capability": "prompt", "score": ["recall"],
              "answers": {"q": ["a"]}}]
    monkeypatch.setattr(rc, "load_agents", lambda: agents)
    monkeypatch.setattr(rc, "load_tasks", lambda: tasks)
    monkeypatch.setattr(rc, "detect", lambda a: (True, "fake 1.0"))
    monkeypatch.setattr(rc, "environment_check", lambda a: [])
    code = rc.main(["run", "--drive", "--cell", "@high",
                    "--run", str(tmp_path / "run")])
    out = capsys.readouterr().out
    assert "driver refused" in out and "NOTHING RAN" in out
    assert code == 1


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


NO_CACHE = {"cache_read_tokens": None, "cache_write_tokens": None}


def test_usage_is_read_from_a_json_transcript_and_only_when_both_counts_are_integers():
    tail = '{"result": "ok", "usage": {"input_tokens": 1200, "output_tokens": 340}}'
    assert rc._usage_from_transcript("noise\n" + tail) == {
        "input_tokens": 1200, "output_tokens": 340, **NO_CACHE}
    assert rc._usage_from_transcript('{"usage": {"input_tokens": 1}}') is None
    assert rc._usage_from_transcript("plain text transcript") is None


def test_the_cache_counts_are_read_in_both_vendors_spellings():
    """Read off the real transcripts, not invented: Cursor writes
    `cacheReadTokens`/`cacheWriteTokens`, Claude Code writes
    `cache_read_input_tokens`/`cache_creation_input_tokens`. Every stored
    transcript of both carries them, and until 0.1.648 neither was read."""
    assert rc._token_counts({"inputTokens": 7814, "outputTokens": 1389,
                             "cacheReadTokens": 899968,
                             "cacheWriteTokens": 0}) == {
        "input_tokens": 7814, "output_tokens": 1389,
        "cache_read_tokens": 899968, "cache_write_tokens": 0}
    assert rc._token_counts({"input_tokens": 192, "output_tokens": 55499,
                             "cache_read_input_tokens": 12036950,
                             "cache_creation_input_tokens": 174275}) == {
        "input_tokens": 192, "output_tokens": 55499,
        "cache_read_tokens": 12036950, "cache_write_tokens": 174275}


def test_a_missing_cache_count_is_none_and_never_zero():
    """A CLI that reports no cache line is not one that read nothing from
    cache. Zero would be a claim; None is the honest answer, and it is the
    difference between the two that GAP-044 turned on."""
    got = rc._token_counts({"input_tokens": 1, "output_tokens": 2})
    assert got == {"input_tokens": 1, "output_tokens": 2, **NO_CACHE}
    assert got["cache_read_tokens"] is None  # absent cache reads are None, not 0


def test_an_unreadable_cache_count_does_not_take_the_required_pair_down():
    """The two originals are required and the cache pair is not, so a garbage
    cache value must not turn a readable bill into no bill at all."""
    assert rc._token_counts({"inputTokens": 5, "outputTokens": 6,
                             "cacheReadTokens": "lots"}) == {
        "input_tokens": 5, "output_tokens": 6, **NO_CACHE}


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

    A VERDICT, NOT `sys.exit`, since 0.1.640: this runs in a driver thread, and
    `threading.excepthook` ignores SystemExit — so the refusal printed nothing,
    moved neither counter, and the run reported `drove 0 task(s)` and exited 0.
    """
    argv = [sys.executable, "-c",
            "import sys,pathlib; pathlib.Path('a.md').write_text(' '.join(sys.argv[1:]))"]
    agent = dict(_agent(argv), drive_effort_in_model="{model}-{effort}")
    out = rc.drive(agent, TASK, tmp_path, effort="high")
    assert out["verdict"] == "driver refused"
    # THE FLAG IT NAMES HAS TO EXIST. This asserted `"no --model" in detail`,
    # so it went on passing after 0.1.644 deleted `--model` — the sentence was
    # still telling the operator to pass a flag that exits 2, and the test was
    # pinning the wrong half of it. It names the spelling now.
    assert "no model was named" in out["detail"]
    assert "--cell" in out["detail"] and "--model" not in out["detail"]
    assert not (tmp_path / "a.md").exists()      # nothing was driven


def test_effort_with_a_model_still_composes(tmp_path):
    """The refusal must not swallow the case it exists to protect."""
    argv = [sys.executable, "-c",
            "import sys,pathlib; pathlib.Path('a.md').write_text(' '.join(sys.argv[1:]))"]
    agent = dict(_agent(argv), drive_effort_in_model="{model}-{effort}")
    out = rc.drive(agent, TASK, tmp_path, model="cursor-grok-4.6", effort="high")
    assert out["effort"] == "high"
    assert out["model"] == "cursor-grok-4.6-high"


def test_the_top_efforts_are_expressible(tmp_path, monkeypatch):
    """`--effort` accepted only low|medium|high, so the highest level a
    comparison could ask for was `high` — on agents whose CLIs document `xhigh`
    and `max`, and on Cursor whose Grok 4.6 tops out at `xhigh`."""
    import contextlib
    import io
    # `run` creates a results directory before it fails on the unknown agent;
    # pin it to tmp_path so the test never writes into the real
    # ~/Documents/LUMI-Style/_conformance/ (GAP-050 part 2 — it broke there on a
    # dangling `latest` symlink left by a hand-deleted results dir).
    monkeypatch.setattr(rc, "RESULTS", tmp_path)
    for level in ("xhigh", "max"):
        buf = io.StringIO()
        with contextlib.suppress(SystemExit), contextlib.redirect_stderr(buf):
            rc.main(["run", "--cell", f"@{level}", "--agent", "no-such-agent"])
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


def test_an_unpinned_run_is_attributed_by_what_actually_ran(tmp_path, monkeypatch):
    """GAP-046: an unpinned run records `(the CLI's default)` as its model, which
    the close drops to null — so it pooled into a junk (agent, None, None) cost
    cell. The close now falls back to `model_ran` (what the CLI's stream said it
    used), attributing the cost. Deliberate-red: before the change no --model is
    passed for this record."""
    calls: list = []
    def _rec(argv, **kw):
        calls.append(argv)
        return _ok("t-abc")
    monkeypatch.setattr(rc.subprocess, "run", _rec)
    record = {"verdict": "misplaced", "produced": [], "seconds": 9,
              "misplaced": [str(tmp_path / "elsewhere" / "deck.en.html")],
              "model": "(the CLI's default)", "model_ran": "grok-4.6",
              "effort": "(not pinned)"}
    rc._conformance_trace({"id": "cursor"}, _trace_task(), tmp_path, record)
    closed = calls[-1]
    assert "--model" in closed and "grok-4.6" in closed, (
        "an unpinned run with a model_ran must be attributed by it, not dropped")
    assert "--effort" not in closed, "an unpinned effort stays honest-null"


def test_a_platform_that_reports_no_model_stays_null(tmp_path, monkeypatch):
    """Hermes/Gemini announce no model; with no pin and no model_ran there is
    nothing to attribute, and the trace stays honestly model-null."""
    calls: list = []
    def _rec(argv, **kw):
        calls.append(argv)
        return _ok("t-abc")
    monkeypatch.setattr(rc.subprocess, "run", _rec)
    record = {"verdict": "misplaced", "produced": [], "seconds": 9,
              "misplaced": [str(tmp_path / "elsewhere" / "deck.en.html")],
              "model": "(the CLI's default)", "model_ran": None,
              "effort": "(not pinned)"}
    rc._conformance_trace({"id": "hermes"}, _trace_task(), tmp_path, record)
    assert "--model" not in calls[-1], "no pin and no model_ran -> honest null"


def test_a_pin_still_outweighs_what_ran_at_close(tmp_path, monkeypatch):
    """A pinned run records the config the operator chose to measure; the
    fallback only fires when there is no pin."""
    calls: list = []
    def _rec(argv, **kw):
        calls.append(argv)
        return _ok("t-abc")
    monkeypatch.setattr(rc.subprocess, "run", _rec)
    record = {"verdict": "misplaced", "produced": [], "seconds": 9,
              "misplaced": [str(tmp_path / "elsewhere" / "deck.en.html")],
              "model": "claude-opus-5", "model_ran": "something-else", "effort": "high"}
    rc._conformance_trace({"id": "claude-code"}, _trace_task(), tmp_path, record)
    closed = calls[-1]
    assert "claude-opus-5" in closed and "something-else" not in closed


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
        "input_tokens": 24, "output_tokens": 26911, **NO_CACHE}


def test_usage_is_read_when_a_warning_follows_the_object():
    # The real shape, taken from a 2026-08-21 matrix run.
    text = RESULT + "\nWarning: no stdin data received in 3s, proceeding without it.\n"
    assert rc._usage_from_transcript(text) == {
        "input_tokens": 24, "output_tokens": 26911, **NO_CACHE}


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
    assert out["usage"] == {"input_tokens": 17952, "output_tokens": 12,
                            **NO_CACHE}


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
    # THIS FIXTURE CARRIED `cacheReadTokens` ALL ALONG and the assertion said
    # it was dropped, which is what the code did and what GAP-044 was about:
    # the count was in front of the test that proved it was thrown away.
    text = ('{"type":"result","result":"ok","usage":'
            '{"inputTokens":19051,"outputTokens":73,"cacheReadTokens":2944}}')
    assert rc._usage_from_transcript(text) == {
        "input_tokens": 19051, "output_tokens": 73,
        "cache_read_tokens": 2944, "cache_write_tokens": None}


def test_snake_case_still_wins_when_both_are_present():
    # Not a real shape, but the order must be deterministic rather than
    # whichever key the dict happens to yield first.
    assert rc._token_counts({"input_tokens": 1, "output_tokens": 2,
                             "inputTokens": 9, "outputTokens": 9}) == {
        "input_tokens": 1, "output_tokens": 2, **NO_CACHE}


def test_a_usage_file_of_bare_counts_is_read(tmp_path):
    p = tmp_path / "u.json"
    p.write_text('{"inputTokens": 5, "outputTokens": 6}', encoding="utf-8")
    assert rc._usage_from_file(p) == {"input_tokens": 5, "output_tokens": 6,
                                      **NO_CACHE}


def test_partial_counts_are_refused():
    assert rc._token_counts({"inputTokens": 5}) is None
    assert rc._token_counts({"input_tokens": 5, "output_tokens": None}) is None


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



def test_three_agents_are_driven_at_once_rather_than_back_to_back(
        tmp_path, monkeypatch, capsys):
    """Three agents on one task ran back to back for 74 minutes on 2026-08-21.

    They share nothing — separate CLIs, separate temporary directories,
    separate accounts — so serial was never a requirement, it was the shape of
    a `for` loop. Each fake agent here sleeps two seconds; serial is six.
    """
    run_dir = tmp_path / "run"
    sleeper = [sys.executable, "-c",
               "import pathlib, time; time.sleep(2); "
               "pathlib.Path('answers.md').write_text('done')"]
    agents = [{"id": f"a{i}", "name": f"A{i}", "capability": "full",
               "drive": list(sleeper), "probe": ["true"]} for i in range(3)]
    tasks = [{"id": "T3-recall", "prompt": "answer", "deliverable": "*.md",
              "min_capability": "prompt", "score": ["recall"], "answers": {}}]
    monkeypatch.setattr(rc, "load_agents", lambda: agents)
    monkeypatch.setattr(rc, "load_tasks", lambda: tasks)
    monkeypatch.setattr(rc, "detect", lambda a: (True, "fake 1.0"))
    monkeypatch.setattr(rc, "environment_check", lambda a: [])
    monkeypatch.setattr(rc, "_conformance_trace", lambda *a, **k: "")

    started = time.monotonic()
    rc.main(["run", "--drive", "--run", str(run_dir)])
    spent = time.monotonic() - started
    printed = capsys.readouterr().out
    assert "concurrently" in printed
    assert spent < 5, f"they ran back to back: {spent:.1f}s for 3 x 2s"
    for i in range(3):
        record = json.loads((run_dir / f"a{i}" / "T3-recall" / "driver.json")
                            .read_text(encoding="utf-8"))
        assert record["verdict"] == "driven", record


def test_one_agents_lines_are_not_split_by_another(tmp_path, monkeypatch, capsys):
    """Interleaved line by line, three concurrent agents produce a transcript
    nobody can attribute. Each agent's block is printed under one lock."""
    run_dir = tmp_path / "run"
    agents = [{"id": f"a{i}", "name": f"A{i}", "capability": "full",
               "drive": [sys.executable, "-c",
                         "import pathlib; pathlib.Path('answers.md').write_text('x')"],
               "probe": ["true"]} for i in range(3)]
    tasks = [{"id": "T3-recall", "prompt": "answer", "deliverable": "*.md",
              "min_capability": "prompt", "score": ["recall"], "answers": {}}]
    monkeypatch.setattr(rc, "load_agents", lambda: agents)
    monkeypatch.setattr(rc, "load_tasks", lambda: tasks)
    monkeypatch.setattr(rc, "detect", lambda a: (True, "fake 1.0"))
    monkeypatch.setattr(rc, "environment_check", lambda a: [])
    monkeypatch.setattr(rc, "_conformance_trace", lambda *a, **k: "")
    rc.main(["run", "--drive", "--run", str(run_dir)])
    lines = [ln for ln in capsys.readouterr().out.splitlines() if ln.strip()]
    for i in range(3):
        head = next(n for n, ln in enumerate(lines) if ln.startswith(f"  a{i} on "))
        assert lines[head + 1].startswith("    driven"), (
            f"a{i}'s verdict did not follow its own header: {lines[head:head + 2]}")


def test_each_agent_can_be_pinned_to_its_own_model(tmp_path, monkeypatch, capsys):
    """A horse race between three CLIs has three different model ids.

    One global `--model` could not say that, so three agents had to be driven in
    three invocations — and the concurrency added in 0.1.556 had nothing to do.
    """
    run_dir = tmp_path / "run"
    echo = [sys.executable, "-c",
            "import sys, pathlib; "
            "pathlib.Path('answers.md').write_text(' '.join(sys.argv[1:]))"]
    agents = [{"id": f"a{i}", "name": f"A{i}", "capability": "full",
               "drive": list(echo), "probe": ["true"]} for i in range(3)]
    tasks = [{"id": "T3-recall", "prompt": "answer", "deliverable": "*.md",
              "min_capability": "prompt", "score": ["recall"], "answers": {}}]
    monkeypatch.setattr(rc, "load_agents", lambda: agents)
    monkeypatch.setattr(rc, "load_tasks", lambda: tasks)
    monkeypatch.setattr(rc, "detect", lambda a: (True, "fake 1.0"))
    monkeypatch.setattr(rc, "environment_check", lambda a: [])
    monkeypatch.setattr(rc, "_conformance_trace", lambda *a, **k: "")

    rc.main(["run", "--drive", "--run", str(run_dir),
             "--cell", "house-default", "--cell", "a1=its-own"])
    want = {"a0": "house-default", "a1": "its-own", "a2": "house-default"}
    for agent, model in want.items():
        record = json.loads((run_dir / agent / "T3-recall" / "driver.json")
                            .read_text(encoding="utf-8"))
        assert record["model"] == model, f"{agent}: {record['model']}"


def test_a_pin_for_an_agent_that_does_not_exist_stops_the_run(tmp_path,
                                                              monkeypatch,
                                                              capsys):
    agents = [{"id": "a0", "name": "A0", "capability": "full",
               "drive": ["/bin/true"], "probe": ["true"]}]
    monkeypatch.setattr(rc, "load_agents", lambda: agents)
    monkeypatch.setattr(rc, "load_tasks", lambda: [])
    monkeypatch.setattr(rc, "detect", lambda a: (True, "fake 1.0"))
    # A RETURN, NOT AN EXIT, since 0.1.644: the parse lives in `agent_cell`,
    # which raises rather than exiting — a library that exits cannot be unit
    # tested, and the CLI decides what to print.
    code = rc.main(["run", "--drive", "--run", str(tmp_path / "r"),
                    "--cell", "typo=opus"])
    assert code == 1
    assert "no platform in the registry" in capsys.readouterr().out


def test_an_effort_level_that_is_not_a_level_stops_the_run(tmp_path, monkeypatch,
                                                           capsys):
    agents = [{"id": "a0", "name": "A0", "capability": "full",
               "drive": ["/bin/true"], "probe": ["true"]}]
    monkeypatch.setattr(rc, "load_agents", lambda: agents)
    monkeypatch.setattr(rc, "load_tasks", lambda: [])
    monkeypatch.setattr(rc, "detect", lambda a: (True, "fake 1.0"))
    code = rc.main(["run", "--drive", "--run", str(tmp_path / "r"),
                    "--cell", "a0=enormous@enormous"])
    assert code == 1
    assert "not one of" in capsys.readouterr().out


def test_the_effort_vocabulary_has_exactly_one_definition():
    """It had two, and they drifted in one release.

    0.1.554 widened the harness to `xhigh` and `max` and left
    `trace_schema.ENUMS["effort"]` at three, so a run could be DRIVEN at xhigh
    and could not be RECORDED at it: on 2026-08-22 the only agent that passed
    all three conformance tasks tried to close its trace with `--effort xhigh`,
    argparse rejected the value, and the run contributed no row to the cost
    board it was driven to fill.

    Asserting the values would be a third copy. What this asserts is that the
    harness reads the schema's tuple rather than owning one — the property that
    makes the drift impossible instead of checked.
    """
    import trace_schema
    source = pathlib.Path(rc.__file__).read_text(encoding="utf-8")
    assert 'trace_schema.ENUMS["effort"]' in source, (
        "run_conformance names its own effort levels again; import them")
    assert '"low", "medium", "high"' not in source, (
        "a literal effort tuple is back in run_conformance")
    # And the shared tuple actually covers what the CLIs accept.
    for level in ("xhigh", "max"):
        assert level in trace_schema.ENUMS["effort"], level


def test_the_trace_id_reaches_the_driver_record_on_disk(tmp_path, monkeypatch):
    """The join key must survive the FILE, which is the only thing `score`
    reads.

    `_conformance_trace` puts the trace id into `record`, and until 0.1.624 the
    caller had already serialized `driver.json` — so the id reached memory and
    never reached disk, and the first round driven after 0.1.617 shipped it
    carried a `trace_id` in no score cell at all. The test that was supposed to
    hold this called the helper directly and read the returned dict, which is
    exactly the seam the defect lived on.

    Driven end to end through `run --drive`, against a fake CLI that writes a
    deck, for the reason the test above this one gives about call sites.
    """
    run_dir = tmp_path / "run"
    store = tmp_path / "traces"
    store.mkdir()
    monkeypatch.setenv("LUMI_TRACES", str(store))
    fake = tmp_path / "fake-cli"
    fake.write_text(
        '#!/bin/sh\nprintf "<html><body>deck</body></html>" > deck.en.html\n',
        encoding="utf-8")
    fake.chmod(0o755)
    # The whole SKILL_SURFACE, because `environment_check` requires all of it
    # and a blocked agent is never driven at all — which is a different test's
    # subject and would make this one pass for the wrong reason.
    skill = tmp_path / "skill"
    for rel in rc.SKILL_SURFACE:
        target = skill / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.suffix:
            target.write_text("stub\n", encoding="utf-8")
        else:
            target.mkdir(exist_ok=True)

    agents = [{"id": "faker", "name": "Faker", "capability": "full",
               "drive": [str(fake), "-p"], "drive_skill_flag": "--add-dir",
               "skill_paths": [str(skill)], "probe": ["true"]}]
    tasks = [{"id": "T1-deck", "prompt": "build", "deliverable": "*.html",
              "min_capability": "full", "score": ["design"],
              "storyline": "market-analysis", "genre": "internal"}]
    monkeypatch.setattr(rc, "load_agents", lambda: agents)
    monkeypatch.setattr(rc, "load_tasks", lambda: tasks)
    monkeypatch.setattr(rc, "detect", lambda a: (True, "fake 1.0"))

    rc.main(["run", "--drive", "--run", str(run_dir)])
    record = json.loads((run_dir / "faker" / "T1-deck" / "driver.json")
                        .read_text(encoding="utf-8"))
    written = list(store.glob("*.json"))
    assert written, "the drive opened no trace, so this proves nothing"
    assert record.get("trace_id"), (
        "driver.json carries no trace_id; `score` reads this file, so the "
        "join key never reaches a score cell")
    assert record["trace_id"] == json.loads(
        written[0].read_text(encoding="utf-8"))["trace_id"]


def test_the_cli_build_reaches_the_trace(tmp_path, monkeypatch):
    """`agent` names a platform, `model` names what it was pointed at, and
    until 0.1.626 nothing said which BINARY did the work — while the binary
    updates on its own schedule. Two rounds of one configuration a week apart
    ran under `2026.08.11-e8db854` and `2026.08.25-3e8eec8`, so a difference
    between them had a third cause nothing had recorded.

    Taken from the probe this run already made BEFORE driving, never re-probed
    at close: asking a CLI its version afterwards answers about now.
    """
    run_dir = tmp_path / "run"
    store = tmp_path / "traces"
    store.mkdir()
    monkeypatch.setenv("LUMI_TRACES", str(store))
    fake = tmp_path / "fake-cli"
    fake.write_text(
        '#!/bin/sh\nprintf "<html><body>deck</body></html>" > deck.en.html\n',
        encoding="utf-8")
    fake.chmod(0o755)
    skill = tmp_path / "skill"
    for rel in rc.SKILL_SURFACE:
        target = skill / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.suffix:
            target.write_text("stub\n", encoding="utf-8")
        else:
            target.mkdir(exist_ok=True)

    agents = [{"id": "faker", "name": "Faker", "capability": "full",
               "drive": [str(fake), "-p"], "drive_skill_flag": "--add-dir",
               "skill_paths": [str(skill)], "probe": ["true"]}]
    tasks = [{"id": "T1-deck", "prompt": "build", "deliverable": "*.html",
              "min_capability": "full", "score": ["design"],
              "storyline": "market-analysis", "genre": "internal"}]
    monkeypatch.setattr(rc, "load_agents", lambda: agents)
    monkeypatch.setattr(rc, "load_tasks", lambda: tasks)
    monkeypatch.setattr(rc, "detect", lambda a: (True, "2026.08.25-3e8eec8"))

    rc.main(["run", "--drive", "--run", str(run_dir)])
    written = list(store.glob("*.json"))
    assert written, "the drive opened no trace, so this proves nothing"
    trace = json.loads(written[0].read_text(encoding="utf-8"))
    assert trace.get("cli_version") == "2026.08.25-3e8eec8", (
        f"the probed build did not reach the trace: {trace.get('cli_version')!r}")


def test_an_unprobeable_agent_is_never_driven_so_the_cli_column_cannot_lie(
        tmp_path, monkeypatch, capsys):
    """`detect` returns `(False, "not installed")` and that string is a
    DIAGNOSIS, not a version — writing it would put "not installed" in a column
    headed `cli` on a row that plainly ran.

    It cannot happen, and this pins WHY rather than pinning the guard: an agent
    whose probe fails is not driven at all, so there is no trace to mislabel.
    The first version of this test asserted the guard's effect on a trace and
    failed because no trace exists — which is the answer, not the problem.
    """
    run_dir = tmp_path / "run"
    store = tmp_path / "traces"
    store.mkdir()
    monkeypatch.setenv("LUMI_TRACES", str(store))
    fake = tmp_path / "fake-cli"
    fake.write_text(
        '#!/bin/sh\nprintf "<html><body>deck</body></html>" > deck.en.html\n',
        encoding="utf-8")
    fake.chmod(0o755)
    skill = tmp_path / "skill"
    for rel in rc.SKILL_SURFACE:
        target = skill / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.suffix:
            target.write_text("stub\n", encoding="utf-8")
        else:
            target.mkdir(exist_ok=True)
    agents = [{"id": "faker", "name": "Faker", "capability": "full",
               "drive": [str(fake), "-p"], "drive_skill_flag": "--add-dir",
               "skill_paths": [str(skill)], "probe": ["true"]}]
    tasks = [{"id": "T1-deck", "prompt": "build", "deliverable": "*.html",
              "min_capability": "full", "score": ["design"],
              "storyline": "market-analysis", "genre": "internal"}]
    monkeypatch.setattr(rc, "load_agents", lambda: agents)
    monkeypatch.setattr(rc, "load_tasks", lambda: tasks)
    monkeypatch.setattr(rc, "detect", lambda a: (False, "probe failed: OSError"))

    rc.main(["run", "--drive", "--run", str(run_dir)])
    assert not list(store.glob("*.json")), (
        "an agent whose CLI could not be probed was driven anyway, and its "
        "trace can now carry a diagnosis where a version belongs")
    assert "nothing to prepare" in capsys.readouterr().out, (
        "the harness must SAY it drove nothing rather than passing quietly")


def test_the_whole_probe_banner_is_recorded_not_a_board_column_of_it(
        tmp_path, monkeypatch):
    """`detect` sliced its answer to 40 characters — a board column's width
    applied at the source. Since 0.1.626 that string is also `cli_version`, and
    Hermes' banner is 89 characters whose discriminating half is the tail:
    `Hermes Agent v0.20.5 (2026.8.19) · upstr` drops `upstream 8d30c204 · local
    057dcdf2`, so two builds carrying one version tag land in one cell.
    """
    run_dir = tmp_path / "run"
    store = tmp_path / "traces"
    store.mkdir()
    monkeypatch.setenv("LUMI_TRACES", str(store))
    fake = tmp_path / "fake-cli"
    fake.write_text(
        '#!/bin/sh\nprintf "<html><body>deck</body></html>" > deck.en.html\n',
        encoding="utf-8")
    fake.chmod(0o755)
    skill = tmp_path / "skill"
    for rel in rc.SKILL_SURFACE:
        target = skill / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.suffix:
            target.write_text("stub\n", encoding="utf-8")
        else:
            target.mkdir(exist_ok=True)
    long_banner = ("Hermes Agent v0.20.5 (2026.8.19) · upstream 8d30c204 · "
                   "local 057dcdf2 (+1 carried commit)")
    assert len(long_banner) > 40, "the fixture must exceed the old slice"

    agents = [{"id": "faker", "name": "Faker", "capability": "full",
               "drive": [str(fake), "-p"], "drive_skill_flag": "--add-dir",
               "skill_paths": [str(skill)], "probe": ["true"]}]
    tasks = [{"id": "T1-deck", "prompt": "build", "deliverable": "*.html",
              "min_capability": "full", "score": ["design"],
              "storyline": "market-analysis", "genre": "internal"}]
    monkeypatch.setattr(rc, "load_agents", lambda: agents)
    monkeypatch.setattr(rc, "load_tasks", lambda: tasks)
    monkeypatch.setattr(rc, "detect", lambda a: (True, long_banner))

    rc.main(["run", "--drive", "--run", str(run_dir)])
    written = list(store.glob("*.json"))
    assert written
    assert json.loads(written[0].read_text())["cli_version"] == long_banner


def test_a_named_agent_whose_probe_failed_says_the_build_was_not_recorded(
        tmp_path, monkeypatch, capsys):
    """`--agent x` drives whether or not the probe answered — the selection
    consults `probed` only when no agent was named. The build was then dropped
    in silence and the run joined the "nobody recorded which binary" cell,
    beside runs that predate the field. Different facts; the console says which.
    """
    run_dir = tmp_path / "run"
    store = tmp_path / "traces"
    store.mkdir()
    monkeypatch.setenv("LUMI_TRACES", str(store))
    fake = tmp_path / "fake-cli"
    fake.write_text(
        '#!/bin/sh\nprintf "<html><body>deck</body></html>" > deck.en.html\n',
        encoding="utf-8")
    fake.chmod(0o755)
    skill = tmp_path / "skill"
    for rel in rc.SKILL_SURFACE:
        target = skill / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.suffix:
            target.write_text("stub\n", encoding="utf-8")
        else:
            target.mkdir(exist_ok=True)
    agents = [{"id": "faker", "name": "Faker", "capability": "full",
               "drive": [str(fake), "-p"], "drive_skill_flag": "--add-dir",
               "skill_paths": [str(skill)], "probe": ["true"]}]
    tasks = [{"id": "T1-deck", "prompt": "build", "deliverable": "*.html",
              "min_capability": "full", "score": ["design"],
              "storyline": "market-analysis", "genre": "internal"}]
    monkeypatch.setattr(rc, "load_agents", lambda: agents)
    monkeypatch.setattr(rc, "load_tasks", lambda: tasks)
    monkeypatch.setattr(rc, "detect",
                        lambda a: (False, "probe failed: TimeoutExpired"))

    rc.main(["run", "--drive", "--run", str(run_dir), "--agent", "faker"])
    printed = capsys.readouterr().out
    assert "the CLI build was not recorded" in printed, printed
    record = json.loads((run_dir / "faker" / "T1-deck" / "driver.json")
                        .read_text(encoding="utf-8"))
    assert "cli_version" not in record
    assert "TimeoutExpired" in record["cli_version_note"]


def test_detect_returns_the_whole_banner_and_the_board_shortens_it(tmp_path,
                                                                   monkeypatch):
    """Driven through the REAL `detect`, against a real probe binary.

    The test above this one monkeypatches `detect`, so it cannot see the slice
    that used to live inside it — a planted red proved exactly that by staying
    green. Truncation belongs where a thing is displayed; the same string is
    recorded as `cli_version`, and a build id cut to a column's width cannot
    tell two builds apart.
    """
    banner = ("Hermes Agent v0.20.5 (2026.8.19) · upstream 8d30c204 · "
              "local 057dcdf2 (+1 carried commit)")
    probe = tmp_path / "probe"
    probe.write_text(f'#!/bin/sh\necho "{banner}"\necho "second line"\n',
                     encoding="utf-8")
    probe.chmod(0o755)
    ok, note = rc.detect({"id": "faker", "probe": [str(probe)]})
    assert ok
    assert note == banner, f"the banner was altered: {note!r}"
    assert len(note) > 40, "the fixture must exceed the old slice"
    assert rc._short(note) == banner[:39] + "…", "the board column is unbounded"
    assert rc._short("short one") == "short one"
