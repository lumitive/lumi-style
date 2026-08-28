"""A second cell driven into an occupied directory is refused, not silent.

`<run>/<agent>/<task>` cannot express two configurations of one agent, and the
driver clears the directory before driving — so the second cell destroyed the
first with no message. The operator's answer has been hand-named run
directories since 2026-08-21 (`r18-low`, `r18-medium`, `r18-high`,
`r18-xhigh`), and `matrix-2026-08-21/` with the level built in by hand.

This is the interim. The per-cell layout removes the collision rather than
reporting it; until then the run stops before a second of budget is spent.

TWO THINGS THIS FILE DID NOT ASK, and 0.1.645 shipped wrong because of it.
Every case pinned `opus` at `high` — a cell that survives composition
unchanged — so nothing here could see that the check compared a RAW ask against
a COMPOSED record. And every case called the function on one directory, so
nothing here could see that the CALLER cleared each directory inside the loop
that was still collecting collisions. Convention 15: the agent whose axes are
transformed is the real instance, and it is the one the check was wrong about.
"""
import json

import run_conformance as rc

# The two registry shapes that matter, by construction rather than by lookup:
# an agent whose CLI takes the level as a flag, and one that composes the level
# into the model id. Cursor is the second, and is why `recorded_axes` exists.
# `efforts` is not decoration: `effort_in_model` will not read a level off an
# id unless the agent DECLARES that level, so a fixture without it silently
# skips the back-fill this file is here to pin. Both lists are the registry's
# own, copied from `load_agents()` rather than invented.
LEVELS = ["low", "medium", "high", "xhigh", "max"]
FLAG = {"id": "a0", "efforts": LEVELS, "drive_effort_flag": "--effort"}
COMPOSED = {"id": "a0", "efforts": LEVELS,
            "drive_effort_in_model": "{model}-{effort}"}
# An agent the registry gives no way to take a level at all — gemini-cli's
# shape, which carries an `efforts_waiver` and neither mechanism.
NEITHER = {"id": "a0", "efforts_waiver": "no reasoning level exists to set"}


def _driven(tmp_path, model, effort, agent="a0"):
    """A driver.json in the shape `drive()` actually writes — convention 15."""
    wd = tmp_path / agent / "T3-recall"
    wd.mkdir(parents=True)
    (wd / "driver.json").write_text(json.dumps({
        "verdict": "driven", "seconds": 12.0, "model": model, "effort": effort,
        "model_ran": None, "pin_state": "unvalidated", "produced": ["a.md"],
    }), encoding="utf-8")
    return wd


def test_a_different_cell_in_the_same_directory_is_named(tmp_path):
    wd = _driven(tmp_path, "opus", "low")
    clash, note = rc.occupied_by_another_cell(FLAG, wd, "opus", "high")
    assert clash and "'low'" in clash and "'high'" in clash
    assert "--replace" in clash
    assert note is None


def test_the_same_cell_is_not_a_collision(tmp_path):
    """Re-running one cell is what the clear is for."""
    wd = _driven(tmp_path, "opus", "high")
    assert rc.occupied_by_another_cell(FLAG, wd, "opus", "high") == (None, None)


def test_an_identical_rerun_of_a_composed_cell_is_not_a_collision(tmp_path):
    """THE CASE 0.1.645 GOT WRONG. `driver.json` records the model
    `compose_model` produced, so an agent that spells the level inside the
    model id records `x-high` for an ask of `x` at `high`. Comparing the raw
    ask against that refused every identical re-run on the one platform the
    design record singles out."""
    wd = _driven(tmp_path, "x-high", "high")
    assert rc.occupied_by_another_cell(COMPOSED, wd, "x", "high") == (None, None)


def test_a_composed_cell_at_a_different_level_still_refuses(tmp_path):
    """The fix must not turn the refusal off — only aim it."""
    wd = _driven(tmp_path, "x-high", "high")
    clash, _ = rc.occupied_by_another_cell(COMPOSED, wd, "x", "low")
    assert clash and "'x-high'" in clash and "'x-low'" in clash


def test_a_level_carried_by_the_model_id_alone_is_not_a_collision(tmp_path):
    """`--cell x-high` with no `@level` back-fills the effort from the id, and
    the record says `high`. The ask and the record are the same cell."""
    wd = _driven(tmp_path, "x-high", "high")
    assert rc.occupied_by_another_cell(
        COMPOSED, wd, "x-high", None) == (None, None)


def test_an_agent_with_no_way_to_take_a_level_is_not_a_collision(tmp_path):
    """A CLI the registry gives neither a flag nor a template cannot be told a
    level, so the drive records `(not pinned)` however loudly it was asked."""
    wd = _driven(tmp_path, "m", "(not pinned)")
    assert rc.occupied_by_another_cell(
        NEITHER, wd, "m", "high") == (None, None)


def test_the_unpinned_sentinels_compare_as_themselves(tmp_path):
    """`drive()` records `(the CLI's default)` and `(not pinned)`, so a run
    that pins nothing twice is the same cell twice."""
    wd = _driven(tmp_path, "(the CLI's default)", "(not pinned)")
    assert rc.occupied_by_another_cell(FLAG, wd, None, None) == (None, None)
    assert rc.occupied_by_another_cell(FLAG, wd, "opus", None)[0] is not None


def test_an_empty_directory_is_not_a_collision(tmp_path):
    wd = tmp_path / "a0" / "T3-recall"
    wd.mkdir(parents=True)
    assert rc.occupied_by_another_cell(FLAG, wd, "opus", "high") == (None, None)


def test_a_record_that_cannot_be_read_says_so_and_does_not_refuse(tmp_path):
    """THE THIRD ANSWER (convention 11). An unreadable record means the
    previous drive left nothing to compare, and clearing it is what the clear
    is for — but returning the same bare `None` as a clean directory made a
    corrupt record, a drive killed mid-write, and an empty directory print
    exactly the same nothing while one of them lost a measurement. Not fatal;
    named."""
    wd = _driven(tmp_path, "opus", "low")
    (wd / "driver.json").write_text("{oops", encoding="utf-8")
    clash, note = rc.occupied_by_another_cell(FLAG, wd, "opus", "high")
    assert clash is None
    assert note and "cannot be read" in note and "cleared, not compared" in note

    (wd / "driver.json").write_text("null", encoding="utf-8")
    clash, note = rc.occupied_by_another_cell(FLAG, wd, "opus", "high")
    assert clash is None
    assert note and "not an object" in note


def test_the_blind_answer_differs_from_the_clean_one(tmp_path):
    """Stated as the literal comparison FM-24 asks for, so that a later change
    collapsing the two fails here rather than in a run directory."""
    empty = tmp_path / "a0" / "T3-recall"
    empty.mkdir(parents=True)
    clean = rc.occupied_by_another_cell(FLAG, empty, "opus", "high")

    blind = _driven(tmp_path, "opus", "low", agent="a1")
    (blind / "driver.json").write_text("{oops", encoding="utf-8")
    assert rc.occupied_by_another_cell(FLAG, blind, "opus", "high") != clean


def test_a_record_from_before_the_pins_existed_is_not_a_refusal(tmp_path):
    """Rows scored before 0.1.617 carry neither; absent stays absent. And it
    is silent rather than noted: there is nothing to disagree with, and a note
    on every such directory trains the operator to read past the ones that
    matter."""
    wd = tmp_path / "a0" / "T3-recall"
    wd.mkdir(parents=True)
    (wd / "driver.json").write_text(json.dumps({"verdict": "driven"}),
                                    encoding="utf-8")
    assert rc.occupied_by_another_cell(FLAG, wd, "opus", "high") == (None, None)


def test_the_ask_is_composed_exactly_once(tmp_path):
    """`recorded_axes` is the single implementation of ask -> recorded, and
    `drive()` uses it too. If a second copy grows, this is where the two
    disagree first."""
    assert rc.recorded_axes(COMPOSED, "x", "high") == ("x-high", "high", True)
    assert rc.recorded_axes(FLAG, "x", "high") == ("x", "high", True)
    assert rc.recorded_axes(NEITHER, "x", "high") == ("x", "high", False)


# --- THE CALLER, which is where the data was actually lost -------------------
#
# Every case above calls the check on ONE directory, and the check was right
# about that directory in all of them. What 0.1.645 got wrong was the loop
# around it: `shutil.rmtree` ran inside the same pass that was still COLLECTING
# collisions, so a clash found on the last agent aborted a run whose earlier
# directories had already been emptied. The refusal reported "nothing was
# driven" — true, and beside the point, because the measurement it existed to
# protect was gone. These call `cmd_run`, which is the seam 0.1.646 bought.

def _args(**kw):
    import argparse
    base = {"cell": [], "budget": "1800:3600", "drive": True, "agent": [],
            "task": None, "replace": False, "run": []}
    base.update(kw)
    return argparse.Namespace(**base)


def _measured(run_dir, agent, task, model, effort):
    """A directory holding a finished measurement: a deliverable and a record."""
    wd = run_dir / agent / task
    wd.mkdir(parents=True)
    (wd / "deliverable.html").write_text("<html>a measurement</html>")
    (wd / "driver.json").write_text(json.dumps(
        {"verdict": "driven", "seconds": 12.0, "model": model,
         "effort": effort, "produced": ["deliverable.html"]}))
    return wd


def test_a_refused_run_leaves_every_other_measurement_on_disk(tmp_path):
    """The one that shipped broken. Two agents, one task; the SECOND agent
    collides, and the first agent's deliverable must survive the refusal."""
    run_dir = tmp_path / "r1"
    keep = _measured(run_dir, "a0", "T3-recall", "opus", "high")
    _measured(run_dir, "a1", "T3-recall", "opus", "low")

    agents = [dict(FLAG, id="a0", capability="full"),
              dict(FLAG, id="a1", capability="full")]
    tasks = [{"id": "T3-recall", "prompt": "p", "min_capability": "full"}]
    probed = {"a0": (True, "", ""), "a1": (True, "", "")}

    code = rc.cmd_run(tasks, agents, probed, [str(run_dir)],
                      _args(cell=["opus@high"]))

    assert code == 1
    assert (keep / "deliverable.html").exists(), (
        "the non-colliding agent's measurement was deleted by a refusal")
    assert (keep / "driver.json").exists()


def test_a_refused_run_writes_no_prompt_anywhere(tmp_path):
    """The tell, stated separately: a `PROMPT.txt` in a directory the run
    refused to drive is the signature of the clear having already happened."""
    run_dir = tmp_path / "r1"
    _measured(run_dir, "a0", "T3-recall", "opus", "high")
    _measured(run_dir, "a1", "T3-recall", "opus", "low")

    agents = [dict(FLAG, id="a0", capability="full"),
              dict(FLAG, id="a1", capability="full")]
    tasks = [{"id": "T3-recall", "prompt": "p", "min_capability": "full"}]
    probed = {"a0": (True, "", ""), "a1": (True, "", "")}

    rc.cmd_run(tasks, agents, probed, [str(run_dir)], _args(cell=["opus@high"]))

    assert list(run_dir.rglob("PROMPT.txt")) == []


# --- one cell per agent, refused rather than merged ---------------------------

def test_a_second_cell_for_one_agent_is_refused_not_merged(tmp_path):
    """`--effort cursor=low --effort cursor=high` kept the last, silently, and
    0.1.644 presented `--cell` as the fix. It is not — the fix is the per-cell
    layout (GAP-045). What `--cell` makes possible is SAYING it; until the
    layout arrives, saying it twice is refused rather than half-honoured."""
    agents = [dict(FLAG, id="a0", capability="full")]
    tasks = [{"id": "T3-recall", "prompt": "p", "min_capability": "full"}]
    code = rc.cmd_run(tasks, agents, {"a0": (True, "", "")}, [str(tmp_path)],
                      _args(cell=["a0=x@low", "a0=x@high"], drive=False))
    assert code == 1


def test_a_half_merge_cannot_invent_a_cell_nobody_asked_for(tmp_path):
    """`--cell opus@high --cell sonnet` resolved to sonnet AT HIGH, because a
    None axis did not clear the previous one. That cell was in neither flag."""
    agents = [dict(FLAG, id="a0", capability="full")]
    tasks = [{"id": "T3-recall", "prompt": "p", "min_capability": "full"}]
    code = rc.cmd_run(tasks, agents, {"a0": (True, "", "")}, [str(tmp_path)],
                      _args(cell=["opus@high", "sonnet"], drive=False))
    assert code == 1


def test_one_cell_each_for_two_agents_is_not_a_repeat(tmp_path):
    """The refusal is per agent, not per flag — a matrix across agents is the
    ordinary case and must stay expressible."""
    agents = [dict(FLAG, id="a0", capability="full"),
              dict(FLAG, id="a1", capability="full")]
    tasks = [{"id": "T3-recall", "prompt": "p", "min_capability": "full"}]
    code = rc.cmd_run(tasks, agents, {"a0": (True, "", ""), "a1": (True, "", "")},
                      [str(tmp_path)],
                      _args(cell=["a0=x@low", "a1=y@high"], drive=False))
    assert code == 0
