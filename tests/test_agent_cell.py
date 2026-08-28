"""The cell, as a type — and the four hand-built shapes it replaced.

`conformance/agent-evals.json` declared the unit of measurement and no code read
it; the unit was computed four times in three shapes instead. These assert the
constructor's rules and, at the end, that the shapes it now produces are the
ones the old code produced.
"""
import json

import agent_cell
import pytest
import trace_schema


def test_a_cell_is_the_three_declared_axes():
    c = agent_cell.cell("cursor", "cursor-grok-4.6-high", "high")
    assert c.key() == ("cursor", "cursor-grok-4.6-high", "high")
    assert agent_cell.AXES == ("agent", "model", "effort")


def test_the_axes_are_producer_facts():
    """A cell says who made the artifact, never what the artifact is."""
    assert set(agent_cell.AXES) <= trace_schema.PRODUCER_FIELDS


def test_the_register_and_the_constructor_are_one_statement():
    """The parity `check_cell_axes` enforces, asserted here too so a reader of
    this file sees the contract without reading the guard."""
    import pathlib
    root = next(p for p in pathlib.Path(__file__).resolve().parents
                if (p / "SKILL.md").exists())
    reg = json.loads((root / "conformance" / "agent-evals.json")
                     .read_text(encoding="utf-8"))
    assert reg["cell"] == list(agent_cell.AXES)


def test_an_absent_agent_is_not_a_cell():
    """`cell_note` opens with it: an agent id alone is not a configuration —
    and neither is a configuration without one."""
    for missing in (None, "", "   "):
        with pytest.raises(agent_cell.CellError):
            agent_cell.cell(missing, "m", "high")


def test_a_display_sentence_is_refused_in_every_axis():
    """`(not pinned)` and `(the CLI's default)` are prose for a person. As a
    key they would pool every unpinned run of different models into one cell —
    which is why the driver handles them by hand at three sites today."""
    for field in ("model", "effort"):
        with pytest.raises(agent_cell.CellError):
            agent_cell.cell("cursor", **{field: "(not pinned)"})


def test_empty_and_whitespace_are_absences_not_values():
    """`close --cli-version ""` stores `""`; the schema type-checks the field
    and nothing else, and the board prints `""` and None alike as a dash — so
    one configuration rendered as two rows with two medians."""
    c = agent_cell.cell("cursor", "", "  ")
    assert c.model is None and c.effort is None


def test_the_ruler_is_beside_the_cell_not_inside_it():
    m = agent_cell.measured_of_trace(
        {"agent": "cursor", "model": "m", "effort": "high",
         "skill_version": "0.1.643", "cli_version": "2026.08.25"})
    assert m.cell == agent_cell.Cell("cursor", "m", "high")
    assert m.ruler == agent_cell.Ruler("0.1.643", "2026.08.25")
    # The 5-tuple the board groups medians on, in the order it used by hand.
    assert m.pooled_key() == ("cursor", "m", "high", "0.1.643", "2026.08.25")


def test_an_empty_cli_version_pools_with_an_absent_one():
    """The normalization that used to live at one call site, now in the type."""
    a = agent_cell.measured_of_trace({"agent": "x", "cli_version": ""})
    b = agent_cell.measured_of_trace({"agent": "x", "cli_version": None})
    assert a.pooled_key() == b.pooled_key()


def test_the_matrix_projection_is_named_and_spells_absence_as_a_question_mark():
    assert agent_cell.Cell("?", "m", "high").drop_agent() == ("m", "high")
    assert agent_cell.Cell("?", None, None).drop_agent() == ("?", "?")


def test_the_config_join_reads_the_ask_never_the_answer():
    """`model` on a score entry is a display sentence; joining on those is the
    defect 0.1.623 fixed."""
    conf = {"model": "Cursor Grok 4.6 High (asked cursor-grok-4.6-high)",
            "model_asked": "cursor-grok-4.6-high", "effort": "high"}
    assert agent_cell.cell_of_config("cursor", conf) == \
        agent_cell.Cell("cursor", "cursor-grok-4.6-high", "high")


def test_a_task_with_nothing_pinned_matches_nothing():
    for conf in ({}, None, {"model_asked": "m"}, {"effort": "high"},
                 {"model_asked": "(the CLI's default)", "effort": "high"}):
        assert agent_cell.cell_of_config("cursor", conf) is None


def test_cells_are_values_so_two_asks_of_one_shape_are_one_key():
    assert agent_cell.cell("a", "m", "high") == agent_cell.cell("a", " m ", "high")
    assert len({agent_cell.cell("a", "m"), agent_cell.cell("a", "m")}) == 1


def test_the_live_store_pools_exactly_as_it_did_before():
    """The safety net for 0.1.643: the boards must not move.

    Recomputes today's grouping the way `cells()` did by hand and asserts the
    type produces the same set over the real trace store.
    """
    import agent_runs
    import trace_store
    traces = trace_store.load()
    admitted = {r["trace_id"]: r for r in agent_runs.board(traces)}
    by_hand = set()
    for t in traces:
        if admitted.get(t.get("trace_id")) is None or not t.get("agent"):
            continue
        cli = (t.get("cli_version") or "").strip() or None
        by_hand.add((t["agent"], t.get("model"), t.get("effort"),
                     t.get("skill_version"), cli))
    by_type = {agent_cell.measured_of_trace(t).pooled_key() for t in traces
               if admitted.get(t.get("trace_id")) is not None and t.get("agent")}
    assert by_type == by_hand


# 0.1.644 — the CLI spelling of a cell. It replaced two flags whose values had
# to agree by convention, and which could not express one agent at two levels.

@pytest.mark.parametrize("text,want", [
    ("opus@high",                    (None, "opus", "high")),
    ("cursor=cursor-grok-4.6@high",  ("cursor", "cursor-grok-4.6", "high")),
    ("@high",                        (None, None, "high")),
    ("claude-code=opus",             ("claude-code", "opus", None)),
    ("  opus@high  ",                (None, "opus", "high")),
    ("a=b@c@high",                   ("a", "b@c", "high")),
])
def test_the_cell_spelling(text, want):
    known = {"cursor", "claude-code", "a"}
    assert agent_cell.parse_pin(text, known, ("low", "high")) == want


@pytest.mark.parametrize("text,says", [
    ("",                 "pins nothing"),
    ("   ",              "pins nothing"),
    ("typo=opus",        "no platform in the registry"),
    ("opus@enormous",    "not one of"),
    ("high",             "did you mean `@high`"),
    ("=",                "neither a model nor a level"),
])
def test_a_cell_that_cannot_be_built_says_why(text, says):
    with pytest.raises(agent_cell.CellError) as exc:
        agent_cell.parse_pin(text, {"cursor", "a"}, ("low", "high"))
    assert says in str(exc.value)


def test_one_agent_at_two_levels_is_two_pins_not_the_last_one():
    """The defect the flag replaced: `--effort cursor=low --effort cursor=high`
    kept `high` and said nothing, so one agent could never be asked for two."""
    known = {"cursor"}
    pins = [agent_cell.parse_pin(t, known, ("low", "high"))
            for t in ("cursor=m@low", "cursor=m@high")]
    assert len(set(pins)) == 2


def test_the_level_vocabulary_is_the_callers(tmp_path):
    """`allowed_efforts` is passed in, because what a TRACE can record is a
    smaller question than what a CLI accepts — Hermes takes eight levels."""
    assert agent_cell.parse_pin("m@ultra", {"a"}, ())[2] == "ultra"
    with pytest.raises(agent_cell.CellError):
        agent_cell.parse_pin("m@ultra", {"a"}, ("low", "high"))
