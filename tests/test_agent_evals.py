"""The multi-agent Score Evals, separated from the package's other evals.

The owner asked for the agent evaluation to stop being mixed into the tools
that grade documents. `agent_evals.py` is that tool; these hold it to the two
things a separated tool must not do — invent a bar of its own, and answer in
two states where three are true.

Cells are `(agent, model, effort)` because an agent id is not a configuration:
measured 0.1.614, two runs of one agent id on one task, pinned differently,
produced different outcomes.
"""
import json

import agent_evals
import pytest


def _trace(tid, agent, model, effort, out=1000, pages=10, gates=None, **kw):
    t = {"trace_id": tid, "agent": agent, "model": model, "effort": effort,
         "closed_at": "2026-08-26T00:00:00+00:00",
         "opened_at": "2026-08-26T00:00:00+00:00",
         "skill_version": "0.1.620", "source": "conformance",
         "content_pages": pages, "output_tokens": out, "input_tokens": 10,
         "phase_seconds": {"build": 100, "checks": 20},
         "gates": {"D12_commercial_footer": "ok"} if gates is None else gates}
    t.update(kw)
    return t


_EVALS = {"ordering": ["tasks_earned desc", "tokens_per_page asc"]}


# --- the cell, and what it refuses to pool -----------------------------------

def test_one_agent_pinned_two_ways_is_two_cells():
    rows = agent_evals.cells(
        [_trace("t-1", "cursor", "grok-high", "high"),
         _trace("t-2", "cursor", "grok-low", "low")], [])
    assert len(rows) == 2
    assert {(r["model"], r["effort"]) for r in rows} == {
        ("grok-high", "high"), ("grok-low", "low")}


def test_a_run_that_did_not_clear_the_gate_line_sets_no_median():
    """The bar is BORROWED from evals/gates.json, never invented here. A thin
    deck is cheap, and a cost board that admitted one would order agents by how
    little they wrote."""
    rows = agent_evals.cells(
        [_trace("t-1", "cursor", "m", "high", out=100,
                gates={"D12_commercial_footer": "FAIL"}),
         _trace("t-2", "cursor", "m", "high", out=9000)], [])
    assert len(rows) == 1
    assert rows[0]["runs"] == 1 and rows[0]["tokens_per_page"] == 900.0


def test_a_trace_with_no_agent_is_not_a_cell():
    """A build somebody ran by hand is a real trace and not a configuration
    anybody can be told to repeat."""
    assert agent_evals.cells([_trace("t-1", None, "m", "high")], []) == []


def test_the_median_is_the_median_not_the_mean():
    """One timed-out run would otherwise move a cell more than five clean
    ones."""
    rows = agent_evals.cells(
        [_trace(f"t-{i}", "cursor", "m", "high", out=1000) for i in range(4)]
        + [_trace("t-huge", "cursor", "m", "high", out=100000)], [])
    assert rows[0]["tokens_per_page"] == 100.0


# --- the history join --------------------------------------------------------

def _row(config=None, tasks=None, **kw):
    r = {"skill_version": "0.1.620", "agent": "cursor", "date": "2026-08-26",
         "run_dir": "~/x", "scores_sha256": "0" * 64,
         "tasks": tasks or {"T1-deck": "pass"}}
    if config:
        r["config"] = config
    r.update(kw)
    return r


def test_a_history_row_predating_the_configuration_field_joins_to_nothing():
    """Thirty-six rows are this case. Pooling them into a cell keyed on the
    agent alone would silently mix runs pinned to different models, which is
    the defect the field was added to end."""
    rows = agent_evals.cells([_trace("t-1", "cursor", "m", "high")], [_row()])
    assert rows[0]["tasks_earned"] is None


def test_an_unconfigured_row_does_not_credit_the_model_unknown_cell():
    """The dangerous half of the same case, and the one a planted red found the
    first test could not see. Five real traces record no model, so a cell keyed
    `(agent, None, None)` EXISTS — and a pre-0.1.618 history row, pooled under
    the agent alone, lands in exactly it. The row would then credit tasks to a
    configuration that is not a configuration."""
    rows = agent_evals.cells([_trace("t-1", "cursor", None, None)], [_row()])
    assert len(rows) == 1 and rows[0]["model"] is None
    assert rows[0]["tasks_earned"] is None, (
        "a row that never recorded what it was run as credited the cell whose "
        "model is unknown")


def test_the_earned_count_reaches_the_cell_it_was_configured_as():
    rows = agent_evals.cells(
        [_trace("t-1", "cursor", "m", "high")],
        [_row(config={"T1-deck": {"model": "m", "effort": "high"}})])
    assert rows[0]["tasks_earned"] == 1 and rows[0]["tasks_attempted"] == 1


def test_a_task_attempted_and_not_passed_is_attempted_not_earned():
    rows = agent_evals.cells(
        [_trace("t-1", "cursor", "m", "high")],
        [_row(tasks={"T1-deck": "fail", "T2": "pass"},
              config={"T1-deck": {"model": "m", "effort": "high"},
                      "T2": {"model": "m", "effort": "high"}})])
    assert rows[0]["tasks_earned"] == 1 and rows[0]["tasks_attempted"] == 2


def test_a_run_that_announced_a_model_nobody_asked_for_is_flagged():
    """0.1.614's finding, made an axis: a cell whose runs did not honour their
    pin is not measuring the configuration it is filed under."""
    rows = agent_evals.cells(
        [_trace("t-1", "cursor", "grok-4.6-high", "high")],
        [_row(config={"T1-deck": {"model": "grok-4.6-high", "effort": "high",
                                  "model_asked": "composer-2.5"}})])
    assert rows[0]["effort_honoured"] is False


# --- ordering ----------------------------------------------------------------

def test_earned_outranks_cost():
    rows = agent_evals.cells(
        [_trace("t-1", "a", "cheap", "high", out=100),
         _trace("t-2", "b", "dear", "high", out=90000)],
        [_row(agent="b", config={"T1-deck": {"model": "dear",
                                             "effort": "high"}})])
    assert rows[0]["model"] == "dear", (
        "a cell that earned a task outranks a cheaper cell that earned none")


def test_a_cell_missing_an_axis_sorts_last_on_it_rather_than_vanishing():
    rows = agent_evals.cells(
        [_trace("t-1", "a", "unmeasured", "high", out=100),
         _trace("t-2", "b", "earned", "high", out=90000)],
        [_row(agent="b", config={"T1-deck": {"model": "earned",
                                             "effort": "high"}})])
    assert len(rows) == 2, "a dropped cell reads as a cell that scored badly"


# --- suggest: three answers, never two ---------------------------------------

_REGISTRY: list[dict] = [
    {"id": "cursor", "probe": ["cursor-agent", "--version"], "drive": ["x"]},
    {"id": "codex", "probe": ["codex", "--version"], "drive": ["x"]},
    {"id": "kimi", "probe": None, "probe_waiver": "an API chat model, no CLI"},
]


def test_an_agent_with_a_measured_cell_is_told_what_to_run():
    rows = agent_evals.cells([_trace("t-1", "cursor", "grok-high", "high")], [])
    state, detail = agent_evals.suggest("cursor", rows, _REGISTRY)
    assert state == agent_evals.MEASURED
    assert "grok-high" in detail and "effort high" in detail


def test_an_agent_with_no_run_is_unmeasured_not_unmeasurable():
    state, _d = agent_evals.suggest("codex", [], _REGISTRY)
    assert state == agent_evals.UNMEASURED


def test_an_agent_that_cannot_be_probed_or_driven_is_unmeasurable(capsys):
    """The two absences are different facts. Printed identically, the board
    reads as pending work that will never be done."""
    state, detail = agent_evals.suggest("kimi", [], _REGISTRY)
    assert state == agent_evals.UNMEASURABLE
    assert "no CLI" in detail


def test_an_agent_the_package_does_not_claim_says_so():
    state, detail = agent_evals.suggest("invented", [], _REGISTRY)
    assert state == agent_evals.UNMEASURABLE and "platforms.json" in detail


def test_a_cheapest_cell_that_names_no_model_is_not_the_recommendation():
    """It was, on this command's first run: claude-code's cheapest cell had no
    model and the answer was `effort high`, which no user can act on."""
    rows = agent_evals.cells(
        [_trace("t-1", "cursor", None, "high", out=100),
         _trace("t-2", "cursor", "grok-high", "high", out=9000)], [])
    state, detail = agent_evals.suggest("cursor", rows, _REGISTRY)
    assert state == agent_evals.MEASURED and "grok-high" in detail
    assert "passed over" in detail, (
        "silently skipping the cheaper cell would improve the headline number "
        "without saying so")


def test_an_agent_whose_every_run_forgot_its_model_is_unmeasured():
    rows = agent_evals.cells([_trace("t-1", "cursor", None, "high")], [])
    state, detail = agent_evals.suggest("cursor", rows, _REGISTRY)
    assert state == agent_evals.UNMEASURED and "which model" in detail


def test_a_thin_sample_winning_is_said_out_loud_not_corrected():
    """Adding a minimum-n bar would be inventing a threshold with no case
    behind it. Naming the fact is the honest move available."""
    rows = agent_evals.cells(
        [_trace("t-1", "cursor", "thin", "high", out=100)]
        + [_trace(f"t-{i+2}", "cursor", "thick", "high", out=9000)
           for i in range(5)], [])
    _state, detail = agent_evals.suggest("cursor", rows, _REGISTRY)
    assert "better sampled" in detail and "thick" in detail


# --- the register and the written board --------------------------------------

def test_the_score_evals_declare_no_numbers():
    """The whole separation argument: the bar is evals/gates.json's, borrowed.
    A number here would be a second bar with no documented case behind it."""
    text = agent_evals.EVALS.read_text(encoding="utf-8")
    register = json.loads(text)
    for axis in register["axes"]:
        for key in ("threshold", "floor", "ceiling", "target", "min", "max"):
            assert key not in axis, (
                f"axis {axis['id']} carries a {key}; the Score Evals declare "
                f"axes and an ordering, and the bar is gates.json's")


def test_every_axis_declares_which_way_it_points():
    """CLAUDE.md convention 4: an author optimises toward any number you give
    them, so a number says whether it is a floor, a ceiling or a target."""
    for axis in json.loads(
            agent_evals.EVALS.read_text(encoding="utf-8"))["axes"]:
        assert axis.get("direction"), f"{axis['id']} does not say which way"


# NOT TESTED HERE: that the SHIPPED board equals the shipped derivation. The
# suite writes to a scratch trace store (conftest, deliberately), so a test of
# that here would compare the tracked board against an empty store and fail for
# a reason that has nothing to do with the board. `agent_evals.py board --check`
# is a CI step for exactly that claim.

def test_a_hand_edited_board_fails_the_check(tmp_path, monkeypatch, capsys):
    fake = tmp_path / "CONFIGURATIONS.md"
    fake.write_text("# somebody typed this\n", encoding="utf-8")
    monkeypatch.setattr(agent_evals, "BOARD", fake)
    assert agent_evals.main(["board", "--check"]) == 1
    assert "do not hand-edit" in capsys.readouterr().out


def test_a_missing_board_is_named_rather_than_passing(tmp_path, monkeypatch,
                                                      capsys):
    """FM-24: the file the check compares against is the thing it can fail to
    look at, and an absent one must not read as agreement."""
    monkeypatch.setattr(agent_evals, "BOARD", tmp_path / "gone.md")
    assert agent_evals.main(["board", "--check"]) == 1
    assert "does not exist" in capsys.readouterr().out


def test_the_board_carries_no_clock_reading():
    """Every date on the board comes from a trace. A `date.today()` anywhere in
    it would make `--check` go red on the day after it was written."""
    source = agent_evals.__file__
    with open(source, encoding="utf-8") as fh:
        text = fh.read()
    body = text.split("def render(", 1)[1].split("\ndef ", 1)[0]
    assert "today" not in body and "now()" not in body


def test_an_absent_register_is_a_hard_exit_not_a_default(tmp_path, monkeypatch):
    """A board rendered from a built-in fallback is a board nobody declared."""
    monkeypatch.setattr(agent_evals, "EVALS", tmp_path / "gone.json")
    with pytest.raises(SystemExit) as caught:
        agent_evals.load_evals()
    assert "no built-in copy" in str(caught.value)


def test_an_empty_store_says_so_rather_than_rendering_an_empty_table():
    text = agent_evals.render([], _EVALS)
    assert "No cell has a qualifying run" in text
    assert "about this store, not about the agents" in text


def test_the_board_carries_no_version_stamp(capsys):
    """A stamp would go stale on every release that bumps the version — and
    `--check` did go red on exactly that, once, before this. It would also claim
    a measurement of rules the rows were not measured against, which is the
    misattribution 0.1.605 exists to describe. The rows carry their own."""
    text = agent_evals.render(
        [{"agent": "cursor", "model": "m", "effort": "high", "runs": 1,
          "tokens_per_page": 1.0, "seconds_per_page": 1.0,
          "tasks_earned": None, "tasks_attempted": None,
          "effort_honoured": None, "measured": "2026-08-26",
          "skill_version": "0.1.500"}], _EVALS)
    head = text.split("| agent |")[0]
    assert "0.1.500" not in head, "the header borrowed a row's version"
    assert "no version stamp on this board on purpose" in head
    assert "0.1.500" in text, "the row must still carry its own"
