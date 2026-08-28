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

import agent_capability  # 0.1.637 — the comparator lives here now
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

def _row(config=None, tasks=None, traces=None, **kw):
    r = {"skill_version": "0.1.620", "agent": "cursor", "date": "2026-08-26",
         "run_dir": "~/x", "scores_sha256": "0" * 64,
         "tasks": tasks or {"T1-deck": "pass"}}
    if config:
        r["config"] = config
    if traces:
        r["traces"] = traces
    r.update(kw)
    return r


# THE SHAPES `score` ACTUALLY WRITES. Every test of this join used a clean model
# id until a review ran the real chain: `scores.json`'s `model` is
# `_model_cell()`'s DISPLAY sentence, and a trace carries the raw pin. The old
# tests passed on a shape the harness never produces, and the join they were
# proving could not have matched one real row.
_DISPLAY = {
    "confirmed, worded differently":
        "cursor-grok-4.6-high (asked cursor-grok-4.6-xhigh)",
    "nothing confirmed it": "asked deepseek-v4-flash, unconfirmed",
    "auto routed": "Auto",
}


def test_a_history_row_predating_the_configuration_field_joins_to_nothing():
    """Thirty-six rows are this case. Pooling them into a cell keyed on the
    agent alone would silently mix runs pinned to different models, which is
    the defect the field was added to end."""
    rows = agent_evals.cells([_trace("t-1", "cursor", "m", "high")], [_row()])
    assert rows[0]["tasks_earned"] is None


def test_an_unconfigured_row_does_not_credit_the_model_unknown_cell():
    """The dangerous half of the same case, and the one a planted red found the
    first test could not see. Five real cells record no model, so a cell keyed
    `(agent, None, None)` EXISTS — and a pre-0.1.618 history row, pooled under
    the agent alone, lands in exactly it."""
    rows = agent_evals.cells([_trace("t-1", "cursor", None, None)], [_row()])
    assert len(rows) == 1 and rows[0]["model"] is None
    assert rows[0]["tasks_earned"] is None


@pytest.mark.parametrize("shape", sorted(_DISPLAY))
def test_the_earned_count_joins_on_the_trace_id_whatever_the_model_reads(shape):
    """The load-bearing one. The join must not depend on the two sides
    spelling one model the same way, because they never do."""
    rows = agent_evals.cells(
        [_trace("t-1", "cursor", "cursor-grok-4.6-xhigh", "xhigh")],
        [_row(traces={"T1-deck": "t-1"},
              config={"T1-deck": {"model": _DISPLAY[shape], "effort": "xhigh"}})])
    assert rows[0]["tasks_earned"] == 1, (
        f"the {shape!r} score cell did not reach its own trace")
    assert rows[0]["tasks_attempted"] == 1


def test_a_row_with_a_configuration_but_no_trace_id_joins_to_nothing():
    """`config` alone is not a key. A row that names what it was run as, and
    not WHICH run, cannot be attributed to a cell without guessing."""
    rows = agent_evals.cells(
        [_trace("t-1", "cursor", "m", "high")],
        [_row(config={"T1-deck": {"model": "m", "effort": "high"}})])
    assert rows[0]["tasks_earned"] is None


def test_a_task_attempted_and_not_passed_is_attempted_not_earned():
    rows = agent_evals.cells(
        [_trace("t-1", "cursor", "m", "high"),
         _trace("t-2", "cursor", "m", "high")],
        [_row(tasks={"T1-deck": "fail", "T2": "pass"},
              traces={"T1-deck": "t-1", "T2": "t-2"},
              config={"T1-deck": {"model": "m", "effort": "high"},
                      "T2": {"model": "m", "effort": "high"}})])
    assert rows[0]["tasks_earned"] == 1 and rows[0]["tasks_attempted"] == 2


def test_a_run_that_announced_a_model_nobody_asked_for_is_flagged():
    """0.1.614's finding, made an axis. Compared against `model_ran`, the raw
    id the CLI announced — comparing a pin to a board's display sentence made
    this `False` for every real shape, invisible only because the join missed
    first."""
    rows = agent_evals.cells(
        [_trace("t-1", "cursor", "grok-4.6-high", "high")],
        [_row(traces={"T1-deck": "t-1"},
              config={"T1-deck": {"model": "composer-2.5 (asked grok-4.6-high)",
                                  "model_ran": "composer-2.5",
                                  "model_asked": "grok-4.6-high",
                                  "effort": "high"}})])
    assert rows[0]["effort_honoured"] is False


def test_a_run_that_did_what_it_was_told_is_honoured():
    rows = agent_evals.cells(
        [_trace("t-1", "cursor", "grok-4.6-high", "high")],
        [_row(traces={"T1-deck": "t-1"},
              config={"T1-deck": {"model": "grok-4.6-high",
                                  "model_ran": "grok-4.6-high",
                                  "model_asked": "grok-4.6-high",
                                  "effort": "high"}})])
    assert rows[0]["effort_honoured"] is True


def test_an_unpinned_run_is_neither_honoured_nor_dishonoured():
    """Three answers. An unpinned run cannot dishonour a pin, and calling it
    `True` would let 'nobody asked for anything' wear the same word as 'the CLI
    did what it was told'."""
    rows = agent_evals.cells(
        [_trace("t-1", "cursor", None, None)],
        [_row(traces={"T1-deck": "t-1"},
              config={"T1-deck": {"model": "Auto"}})])
    assert rows[0]["effort_honoured"] is None


def test_one_dishonoured_run_marks_the_whole_cell():
    rows = agent_evals.cells(
        [_trace("t-1", "cursor", "m", "high"),
         _trace("t-2", "cursor", "m", "high")],
        [_row(tasks={"T1": "pass", "T2": "pass"},
              traces={"T1": "t-1", "T2": "t-2"},
              config={"T1": {"model_ran": "m", "model_asked": "m"},
                      "T2": {"model_ran": "other", "model_asked": "m"}})])
    assert rows[0]["effort_honoured"] is False


def test_earned_outranks_cost():
    rows = agent_evals.cells(
        [_trace("t-1", "a", "cheap", "high", out=100),
         _trace("t-2", "b", "dear", "high", out=90000)],
        [_row(agent="b", traces={"T1-deck": "t-2"},
              config={"T1-deck": {"model": "dear", "effort": "high"}})])
    assert rows[0]["model"] == "dear", (
        "a cell that earned a task outranks a cheaper cell that earned none")


def test_a_cell_missing_an_axis_sorts_last_on_it_rather_than_vanishing():
    rows = agent_evals.cells(
        [_trace("t-1", "a", "unmeasured", "high", out=100),
         _trace("t-2", "b", "earned", "high", out=90000)],
        [_row(agent="b", traces={"T1-deck": "t-2"},
              config={"T1-deck": {"model": "earned", "effort": "high"}})])
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
          "output_tokens": 10, "output_tokens_range": (10, 10),
          "cli_version": None, "reader_score": None, "reader_reads": 0,
          "tokens_per_page_range": (1.0, 1.0),
          "seconds_per_page_range": (1.0, 1.0), "content_pages_range": (10, 10),
          "tasks_earned": None, "tasks_attempted": None,
          "effort_honoured": None, "measured": "2026-08-26",
          "skill_version": "0.1.500"}], _EVALS)
    head = text.split("| agent |")[0]
    assert "0.1.500" not in head, "the header borrowed a row's version"
    assert "no version stamp on this board on purpose" in head
    assert "0.1.500" in text, "the row must still carry its own"


# MOST TASKS OPEN NO TRACE. `trace.py` opens one for a build, and only the deck
# task declares a storyline — the harness says so out loud on every round: "no
# trace: the task declares no storyline". A join on the trace id alone would
# therefore have counted one task per round however many an agent earned, which
# the first real round showed: cursor earned three and could have reported one.

def test_a_task_with_no_trace_joins_its_siblings_run_at_the_same_pins():
    """A history row is ONE round of ONE agent, so two tasks carrying the same
    pins were the same configuration by construction."""
    rows = agent_evals.cells(
        [_trace("t-deck", "cursor", "cursor-grok-4.6-high", "high")],
        [_row(tasks={"T1-deck": "pass", "T2": "pass", "T3": "pass"},
              traces={"T1-deck": "t-deck"},
              config={t: {"model": "Cursor Grok 4.6 High (asked ...)",
                          "model_asked": "cursor-grok-4.6-high",
                          "effort": "high"}
                      for t in ("T1-deck", "T2", "T3")})])
    assert rows[0]["tasks_earned"] == 3 and rows[0]["tasks_attempted"] == 3


def test_a_task_run_at_different_pins_does_not_borrow_its_sibling_s_trace():
    rows = agent_evals.cells(
        [_trace("t-deck", "cursor", "cursor-grok-4.6-high", "high")],
        [_row(tasks={"T1-deck": "pass", "T2": "pass"},
              traces={"T1-deck": "t-deck"},
              config={"T1-deck": {"model_asked": "cursor-grok-4.6-high",
                                  "effort": "high"},
                      "T2": {"model_asked": "composer-2.5",
                             "effort": "low"}})])
    assert rows[0]["tasks_earned"] == 1 and rows[0]["tasks_attempted"] == 1


def test_an_unpinned_sibling_does_not_borrow_a_trace_it_cannot_be_matched_to():
    """Not "every other unpinned task in the row" — that would make an unpinned
    round credit its whole task list to one arbitrary trace. The task that owns
    a trace still counts, because a trace records its own agent, model and
    effort; what cannot be inferred is which OTHER tasks ran the same way."""
    rows = agent_evals.cells(
        [_trace("t-deck", "hermes", "deepseek-v4-flash", "high")],
        [_row(agent="hermes", tasks={"T1-deck": "pass", "T2": "pass"},
              traces={"T1-deck": "t-deck"},
              config={"T1-deck": {"model_pinned": False,
                                  "effort_pinned": False},
                      "T2": {"model_pinned": False, "effort_pinned": False}})])
    assert rows[0]["tasks_earned"] == 1 and rows[0]["tasks_attempted"] == 1, (
        "the traced task counts; its unpinned sibling has nothing to match on")


# ONE MODEL, TWO SPELLINGS — and sometimes two models, one spelling. You pin an
# id and the CLI answers with a display name. Compared literally an honoured pin
# reads as substituted; compared by squashed string, `cursor-grok-4.6-high` and
# `cursor-grok-4.6-high-fast` read as the same model, and `adapters/cursor.md`
# says EVERY id has a `-fast` twin. Three answers is what the material forces.
#
# Every id below is real: from a `driver.json` this repository recorded, or from
# `cursor-agent --list-models` run on 2026-08-27.

@pytest.mark.parametrize("asked,ran,verdict", [
    # The same words. This is the only shape that CONFIRMS anything.
    ("cursor-grok-4.6-high", "Cursor Grok 4.6 High", True),
    # A substitution: `high` is not `xhigh`, in either spelling. The token run
    # must be contiguous or `Extra High` would be reached by stepping over
    # `Extra`, which is the one pair this check exists for.
    ("cursor-grok-4.6-high", "cursor-grok-4.6-xhigh", False),
    ("cursor-grok-4.6-high", "Cursor Grok 4.6 Extra High", False),
    # THE OTHER HALF OF THAT PAIR, and it is a real run: pinned to
    # `cursor-grok-4.6-xhigh`, answered `Cursor Grok 4.6 Extra High`, and the
    # board printed **not honoured** until `Extra High` was read as one
    # spelling of `xhigh` — a value in `trace_schema.ENUMS["effort"]`, which is
    # a tuple this package owns, not a vendor model alias.
    ("cursor-grok-4.6-xhigh", "Cursor Grok 4.6 Extra High", True),
    ("cursor-grok-4.6-low", "Cursor Grok 4.6 Low", True),
    ("cursor-grok-4.6-medium", "Cursor Grok 4.6 Medium", True),
    ("cursor-grok-4.6-xhigh", "cursor-grok-4.6-xhigh-fast", None),
    ("grok-4.6-high", "composer-2.5", False),
    # NOT ESTABLISHED. An alias, a display name that drops the level, and a
    # `-fast` twin are indistinguishable from here — the first two are almost
    # certainly honoured and the third certainly is not, so none of them may
    # claim to be.
    ("opus", "claude-opus-5", None),
    ("cursor-grok-4.6-high", "Cursor Grok 4.6", None),
    ("cursor-grok-4.6-high", "cursor-grok-4.6-high-fast", None),
    ("cursor-grok-4.5-low", "cursor-grok-4.5-low-fast", None),
    ("kimi-k3-low", "Kimi K3", None),
    ("composer-2.5", "Composer 2.5 Fast", None),
    # Nothing to compare is nothing to claim, and neither argument may crash.
    (None, "Cursor Grok 4.6", None),
    ("cursor-grok-4.6-high", None, None),
    ("", "Cursor Grok 4.6", None),
])
def test_a_pin_and_the_name_the_cli_answers_with(asked, ran, verdict):
    assert agent_capability.same_model(asked, ran) is verdict


def test_the_real_rounds_honoured_pin_reads_as_honoured():
    """End of the same argument, through the public path."""
    rows = agent_evals.cells(
        [_trace("t-1", "cursor", "cursor-grok-4.6-high", "high")],
        [_row(traces={"T1-deck": "t-1"},
              config={"T1-deck": {
                  "model": "Cursor Grok 4.6 High (asked cursor-grok-4.6-high)",
                  "model_ran": "Cursor Grok 4.6 High",
                  "model_asked": "cursor-grok-4.6-high", "effort": "high"}})])
    assert rows[0]["effort_honoured"] is True


def test_a_sibling_that_announced_a_different_name_leaves_the_cell_unconfirmed():
    """The committed r17 row is this case: three tasks pinned to
    `cursor-grok-4.6-high`, answered `Cursor Grok 4.6 High` twice and
    `Cursor Grok 4.6` once. The pins are what a configuration IS, so the join
    stands — but the cell must not print `honoured` on the strength of the two
    that agreed while a third said something else."""
    rows = agent_evals.cells(
        [_trace("t-deck", "cursor", "cursor-grok-4.6-high", "high")],
        [_row(tasks={"T1-deck": "pass", "T2": "pass", "T3": "pass"},
              traces={"T1-deck": "t-deck"},
              config={
                  "T1-deck": {"model_asked": "cursor-grok-4.6-high",
                              "model_ran": "Cursor Grok 4.6 High",
                              "effort": "high"},
                  "T2": {"model_asked": "cursor-grok-4.6-high",
                         "model_ran": "Cursor Grok 4.6 High", "effort": "high"},
                  "T3": {"model_asked": "cursor-grok-4.6-high",
                         "model_ran": "Cursor Grok 4.6", "effort": "high"}})])
    assert rows[0]["tasks_earned"] == 3, "the join is on the pins and stands"
    assert rows[0]["effort_honoured"] is True, (
        "two tasks confirmed exactly and the third is compatible rather than "
        "contradictory — compatible must not spend the confirmation, and must "
        "not withdraw it either")


def test_one_task_announcing_a_substitution_marks_the_whole_cell():
    rows = agent_evals.cells(
        [_trace("t-deck", "cursor", "cursor-grok-4.6-high", "high")],
        [_row(tasks={"T1-deck": "pass", "T2": "pass"},
              traces={"T1-deck": "t-deck"},
              config={
                  "T1-deck": {"model_asked": "cursor-grok-4.6-high",
                              "model_ran": "Cursor Grok 4.6 High",
                              "effort": "high"},
                  "T2": {"model_asked": "cursor-grok-4.6-high",
                         "model_ran": "Composer 2.5", "effort": "high"}})])
    assert rows[0]["effort_honoured"] is False


def test_a_cell_whose_every_task_is_only_compatible_claims_nothing():
    rows = agent_evals.cells(
        [_trace("t-deck", "claude-code", "opus", "high")],
        [_row(agent="claude-code", traces={"T1-deck": "t-deck"},
              config={"T1-deck": {"model_asked": "opus",
                                  "model_ran": "claude-opus-5",
                                  "effort": "high"}})])
    assert rows[0]["effort_honoured"] is None, (
        "an alias answering under its full name confirms nothing on its own")


def test_a_re_recorded_round_is_counted_once():
    """`report --record`'s idempotence key includes the score digest, so a
    RE-DRIVE into the same directory appends a second row rather than replacing
    the first. A review appended cursor's earlier r17 row and the board printed
    `6 of 6` for a three-task round."""
    first = _row(traces={"T1-deck": "t-1"}, run_dir="~/runs/r17",
                 config={"T1-deck": {"model_asked": "m", "effort": "high"}})
    again = _row(traces={"T1-deck": "t-1"}, run_dir="~/runs/r17",
                 scores_sha256="1" * 64,
                 config={"T1-deck": {"model_asked": "m", "effort": "high"}})
    rows = agent_evals.cells([_trace("t-1", "cursor", "m", "high")],
                             [first, again])
    assert rows[0]["tasks_earned"] == 1 and rows[0]["tasks_attempted"] == 1


def test_two_agents_in_one_run_directory_are_two_rounds():
    """The key is (agent, run_dir). A round drives several agents into one
    directory and each gets its own row; collapsing on the directory alone
    would erase all but one."""
    rows = agent_evals.cells(
        [_trace("t-1", "cursor", "m", "high"),
         _trace("t-2", "hermes", "m", "high")],
        [_row(agent="cursor", run_dir="~/runs/r17", traces={"T": "t-1"},
              tasks={"T": "pass"},
              config={"T": {"model_asked": "m", "effort": "high"}}),
         _row(agent="hermes", run_dir="~/runs/r17", traces={"T": "t-2"},
              tasks={"T": "pass"},
              config={"T": {"model_asked": "m", "effort": "high"}})])
    assert {r["agent"] for r in rows} == {"cursor", "hermes"}
    assert all(r["tasks_earned"] == 1 for r in rows)


# THE SKILL VERSION IS PART OF A CELL'S IDENTITY. Without it one row averaged
# runs measured under three different rulers and printed the newest version's
# number over all of them — measured on the real store, 12.8% of that cell's
# headline was the ruler rather than the agent.

def test_two_skill_versions_are_two_cells():
    rows = agent_evals.cells(
        [_trace("t-1", "cursor", "m", "high", out=1000, skill_version="0.1.542"),
         _trace("t-2", "cursor", "m", "high", out=9000, skill_version="0.1.623")],
        [])
    assert len(rows) == 2
    assert {r["skill_version"] for r in rows} == {"0.1.542", "0.1.623"}
    assert {r["tokens_per_page"] for r in rows} == {100.0, 900.0}, (
        "pooling would have printed one median for both rulers")


def test_a_cell_reports_the_output_tokens_beside_the_ratio():
    """`output_tokens` is the reference. Over four repeats of one
    configuration, output tokens spread 16.5% and the same measurement divided
    by content pages spread 32.3% — the denominator moves too."""
    rows = agent_evals.cells(
        [_trace("t-1", "cursor", "m", "high", out=40000, pages=8),
         _trace("t-2", "cursor", "m", "high", out=40000, pages=10)], [])
    assert rows[0]["output_tokens"] == 40000
    assert rows[0]["output_tokens_range"] == (40000, 40000)
    assert rows[0]["tokens_per_page_range"] == (4000.0, 5000.0), (
        "identical token counts, and the ratio still moved 25%")
    assert rows[0]["content_pages_range"] == (8, 10)


def test_every_reported_middle_carries_its_range():
    """A median printed alone invites a reader to order two cells that overlap
    completely. `s/page` spread 99.4% over four repeats of one configuration."""
    rows = agent_evals.cells(
        [_trace("t-1", "cursor", "m", "high", out=1000),
         _trace("t-2", "cursor", "m", "high", out=9000)], [])
    for middle, rng in (("output_tokens", "output_tokens_range"),
                        ("tokens_per_page", "tokens_per_page_range"),
                        ("seconds_per_page", "seconds_per_page_range")):
        assert rows[0][rng] is not None, f"{middle} has no range beside it"
        lo, hi = rows[0][rng]
        assert lo <= rows[0][middle] <= hi


def test_the_board_prints_the_range_not_only_the_middle():
    rows = agent_evals.cells(
        [_trace("t-1", "cursor", "m", "high", out=1000),
         _trace("t-2", "cursor", "m", "high", out=9000)], [])
    text = agent_evals.render(rows, _EVALS)
    assert "(100–900)" in text or "(100.0–900.0)" in text, (
        f"the spread is not on the board: {text}")


# ONE RULER PER RECOMMENDATION. Cells carry their skill version now, so an
# agent has one cell per configuration PER RELEASE — and an older cell is not
# an alternative anybody can choose. The first version of `pick()` cited one:
# "cursor-grok-4.6-high at 4 run(s) is dearer per page and better sampled",
# pointing at a measurement of skill 0.1.542's rules.

def _cell(**kw):
    base = {"agent": "cursor", "model": "m", "effort": "high", "runs": 1,
            "tokens_per_page": 1000.0, "seconds_per_page": 10.0,
            "output_tokens": 10000, "output_tokens_range": (10000, 10000),
            "tokens_per_page_range": (1000.0, 1000.0),
            "seconds_per_page_range": (10.0, 10.0),
            "content_pages_range": (10, 10), "cli_version": None,
            "reader_score": None, "reader_reads": 0, "tasks_earned": None,
            "tasks_attempted": None, "effort_honoured": None,
            "measured": "2026-08-27", "skill_version": "0.1.625"}
    base.update(kw)
    return base


def test_the_recommendation_comes_from_the_newest_release_measured():
    rows = [_cell(model="new", skill_version="0.1.625", tokens_per_page=9000.0),
            _cell(model="old", skill_version="0.1.542", tokens_per_page=100.0)]
    _state, best, _c = agent_evals.pick("cursor", rows, _REGISTRY)
    assert best is not None and best["model"] == "new", (
        "the cheaper cell measures rules that no longer exist")


def test_no_caveat_points_at_another_release():
    """Asserted on the NUMBER, not on the version string — the caveats quote a
    tokens-per-page figure and never a release, so checking for "0.1.542" in
    them passed on code that offered the 0.1.542 cell. A planted red found it.
    """
    rows = [_cell(model="new", skill_version="0.1.625", tokens_per_page=9000.0),
            _cell(model=None, skill_version="0.1.542", tokens_per_page=100.0),
            _cell(model="old", skill_version="0.1.542", runs=9,
                  tokens_per_page=50.0)]
    _state, _best, caveats = agent_evals.pick("cursor", rows, _REGISTRY)
    joined = " ".join(caveats)
    for other_release_number in ("100", "50", "old"):
        assert other_release_number not in joined, (
            f"a caveat offered an alternative from another release: {caveats}")


def test_the_sentence_names_the_release_it_was_measured_against():
    _state, detail = agent_evals.suggest("cursor", [_cell()], _REGISTRY)
    assert "skill 0.1.625" in detail
    assert "10,000 output tokens" in detail, "the reference number is missing"


# THE CLI BUILD IS PART OF A CELL'S IDENTITY TOO. `agent` names a platform and
# `model` names what it was pointed at; neither says which binary did the work,
# and a CLI updates on its own schedule. Two rounds of one configuration a week
# apart ran under `2026.08.11-e8db854` and `2026.08.25-3e8eec8`.

def test_two_cli_builds_are_two_cells():
    rows = agent_evals.cells(
        [_trace("t-1", "cursor", "m", "high", out=1000,
                cli_version="2026.08.11-e8db854"),
         _trace("t-2", "cursor", "m", "high", out=9000,
                cli_version="2026.08.25-3e8eec8")], [])
    assert len(rows) == 2
    assert {r["cli_version"] for r in rows} == {"2026.08.11-e8db854",
                                                "2026.08.25-3e8eec8"}


def test_a_run_predating_the_field_is_its_own_cell_not_folded_into_a_named_one():
    """"We did not record which binary" is not the same run as "we did". Folding
    the unrecorded ones into whichever named cell they resemble would invent the
    fact the field was added to stop inventing."""
    rows = agent_evals.cells(
        [_trace("t-1", "cursor", "m", "high", out=1000),
         _trace("t-2", "cursor", "m", "high", out=9000,
                cli_version="2026.08.25-3e8eec8")], [])
    assert len(rows) == 2
    assert None in {r["cli_version"] for r in rows}


def test_the_board_prints_the_cli_build():
    rows = agent_evals.cells(
        [_trace("t-1", "cursor", "m", "high", cli_version="2026.08.25-3e8eec8")],
        [])
    assert "2026.08.25-3e8eec8" in agent_evals.render(rows, _EVALS)


def test_the_newest_release_is_found_by_version_order_not_alphabetically():
    """`0.1.99` outranks `0.1.100` as a string. `versioning.sort_key` exists for exactly
    this and the change that created this call site left it with no callers at
    all, so nothing protected the one place that needed it."""
    rows = [_cell(model="ninety-nine", skill_version="0.1.99",
                  tokens_per_page=100.0),
            _cell(model="one-hundred", skill_version="0.1.100",
                  tokens_per_page=9000.0)]
    _state, best, _c = agent_evals.pick("cursor", rows, _REGISTRY)
    assert best is not None and best["model"] == "one-hundred", (
        "0.1.100 is the newer release; a string comparison says 0.1.99")


def test_an_empty_cli_version_is_an_absence_not_a_second_cell():
    """`close --cli-version ""` stores the empty string — the copy loop tests
    `is not None` and the schema type-checks and no more. `render` prints both
    `""` and `None` as a dash, so one configuration became two rows showing the
    same thing with two different medians."""
    rows = agent_evals.cells(
        [_trace("t-1", "cursor", "m", "high", out=1000, cli_version=""),
         _trace("t-2", "cursor", "m", "high", out=9000, cli_version=None),
         _trace("t-3", "cursor", "m", "high", out=5000, cli_version="  ")], [])
    assert len(rows) == 1 and rows[0]["runs"] == 3
    assert rows[0]["cli_version"] is None


def test_a_padded_cli_version_matches_its_bare_form():
    rows = agent_evals.cells(
        [_trace("t-1", "cursor", "m", "high", cli_version="2026.08.25-3e8eec8"),
         _trace("t-2", "cursor", "m", "high", cli_version=" 2026.08.25-3e8eec8 ")],
        [])
    assert len(rows) == 1, "one build spelled two ways became two cells"


def test_the_board_states_the_spread_its_own_table_shows():
    """The note said 99.4%, which is the spread of RAW charged seconds, under a
    table printing s/page. A block that states a fact about the whole table is a
    claim the table can falsify — 0.1.625 fixed the same shape in README."""
    text = agent_evals.render([], _EVALS)
    assert "spread it 124.0%" in text, (
        "the s/page note must quote the s/page spread, not the raw seconds'")
    # 99.4% still appears, inside the parenthesis recording the correction —
    # asserted on the CLAIM rather than on the absence of a number, because
    # deleting the old figure would delete the record of having been wrong.
    claim = text.split("**`s/page` orders nothing.**")[1].split("(")[0]
    assert "99.4" not in claim


# A HUMAN READ IS THE AXIS THAT ORDERS EVERYTHING ELSE, and 0.1.627 is why:
# twelve decks across four reasoning tiers, every one passing every gating
# check, and the owner reading all twelve reported the CHEAPEST tier as the
# worst. A board ordered on cost recommends exactly that tier.

def _reviews(tmp_path, monkeypatch, reviews):
    path = tmp_path / "scores.json"
    path.write_text(json.dumps({"reviews": reviews}), encoding="utf-8")
    monkeypatch.setattr(agent_evals, "REVIEWS", path)
    return path


def test_a_read_joins_a_trace_by_corpus_id(tmp_path, monkeypatch):
    _reviews(tmp_path, monkeypatch,
             [{"corpus_id": "D15", "reader": {"C1": 2, "C2": 4, "C3": 2}}])
    got = agent_evals.reader_scores(
        [_trace("t-1", "cursor", "m", "high", corpus_id="D15")])
    assert got == {"t-1": 2}


def test_the_agents_self_scores_are_refused(tmp_path, monkeypatch):
    """A producer grading its own work is the one input a quality axis must
    not take. The record carries both; only `reader` is read."""
    _reviews(tmp_path, monkeypatch,
             [{"corpus_id": "D15", "self": {"C1": 5, "C2": 5},
               "reader": {"C1": 1, "C2": 1}}])
    got = agent_evals.reader_scores(
        [_trace("t-1", "cursor", "m", "high", corpus_id="D15")])
    assert got == {"t-1": 1}


def test_a_dimension_the_reader_skipped_is_not_a_zero(tmp_path, monkeypatch):
    """`null` means unscored. Counting it as zero would let an unanswered
    question mark a configuration down — and with four nulls against three
    fours, treating them as zeros moves the median from 4 to 0."""
    _reviews(tmp_path, monkeypatch,
             [{"corpus_id": "D15",
               "reader": {"C1": 4, "C2": None, "C3": 4, "C4": None,
                          "C5": 4, "C6": None, "C7": None}}])
    got = agent_evals.reader_scores(
        [_trace("t-1", "cursor", "m", "high", corpus_id="D15")])
    assert got == {"t-1": 4}, "the unscored dimensions were counted"


def test_a_review_with_no_corpus_id_reaches_no_trace(tmp_path, monkeypatch):
    _reviews(tmp_path, monkeypatch, [{"reader": {"C1": 1}}])
    assert agent_evals.reader_scores(
        [_trace("t-1", "cursor", "m", "high", corpus_id="D15")]) == {}


def test_a_read_outranks_both_cost_and_earned():
    """The whole point, and asserted through `_ordering` on cells that differ
    on all three axes at once — a cheaper cell that earned more, against a
    dearer cell that a person read. The first version sorted the list itself
    after building it, which is how a planted red that swapped the key order
    stayed green."""
    cheap = _cell(model="cheap", reader_score=None, reader_reads=0,
                  tasks_earned=3, tasks_attempted=3, tokens_per_page=100.0)
    read = _cell(model="read", reader_score=4.0, reader_reads=1,
                 tasks_earned=None, tasks_attempted=None,
                 tokens_per_page=90000.0)
    assert sorted([cheap, read], key=agent_evals._ordering)[0]["model"] == "read", (
        "a cheaper cell that earned more outranked one a human actually read")


def test_a_cell_with_no_read_sorts_last_on_it_rather_than_vanishing():
    rows = [_cell(model="unread", reader_score=None, tokens_per_page=100.0),
            _cell(model="read", reader_score=3.0, tokens_per_page=9000.0)]
    rows.sort(key=agent_evals._ordering)
    assert [r["model"] for r in rows] == ["read", "unread"]
    assert len(rows) == 2, "a dropped cell reads as a cell that scored badly"


def test_the_board_prints_a_dash_for_an_unread_configuration():
    text = agent_evals.render([_cell(reader_score=None)], _EVALS)
    # THE CELL, not the word. The right disjunct was always true — the next
    # assertion's own sentence contains "read" — so this proved nothing about
    # the dash it is named for.
    row = next(ln for ln in text.splitlines() if ln.startswith("| cursor "))
    assert "| — |" in row or "| - |" in row
    assert "nobody has read that configuration" in text


def test_the_register_declares_the_axis_and_leads_with_it():
    register = json.loads(agent_evals.EVALS.read_text(encoding="utf-8"))
    assert register["ordering"][0] == "reader_score desc"
    axis = next(a for a in register["axes"] if a["id"] == "reader_score")
    assert axis["direction"] == "higher is better"
    for key in ("threshold", "floor", "ceiling", "target"):
        assert key not in axis, "the Score Evals declare axes, not bars"
