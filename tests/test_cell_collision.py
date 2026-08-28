"""A second cell driven into an occupied directory is refused, not silent.

`<run>/<agent>/<task>` cannot express two configurations of one agent, and the
driver clears the directory before driving — so the second cell destroyed the
first with no message. The operator's answer has been four hand-named run
directories since 2026-08-21 (`r18-low`, `r18-medium`, `r18-high`,
`r18-xhigh`), and `matrix-2026-08-21/` with the level built in by hand.

This is the interim. The per-cell layout removes the collision rather than
reporting it; until then the run stops before a second of budget is spent.
"""
import json

import run_conformance as rc


def _driven(tmp_path, model, effort):
    """A driver.json in the shape `drive()` actually writes — convention 15."""
    wd = tmp_path / "a0" / "T3-recall"
    wd.mkdir(parents=True)
    (wd / "driver.json").write_text(json.dumps({
        "verdict": "driven", "seconds": 12.0, "model": model, "effort": effort,
        "model_ran": None, "pin_state": "unvalidated", "produced": ["a.md"],
    }), encoding="utf-8")
    return wd


def test_a_different_cell_in_the_same_directory_is_named(tmp_path):
    wd = _driven(tmp_path, "opus", "low")
    clash = rc.occupied_by_another_cell(wd, "opus", "high")
    assert clash and "'low'" in clash and "'high'" in clash
    assert "--replace" in clash


def test_the_same_cell_is_not_a_collision(tmp_path):
    """Re-running one cell is what the clear is for."""
    wd = _driven(tmp_path, "opus", "high")
    assert rc.occupied_by_another_cell(wd, "opus", "high") is None


def test_the_unpinned_sentinels_compare_as_themselves(tmp_path):
    """`drive()` records `(the CLI's default)` and `(not pinned)`, so a run
    that pins nothing twice is the same cell twice."""
    wd = _driven(tmp_path, "(the CLI's default)", "(not pinned)")
    assert rc.occupied_by_another_cell(wd, None, None) is None
    assert rc.occupied_by_another_cell(wd, "opus", None) is not None


def test_an_empty_directory_is_not_a_collision(tmp_path):
    wd = tmp_path / "a0" / "T3-recall"
    wd.mkdir(parents=True)
    assert rc.occupied_by_another_cell(wd, "opus", "high") is None


def test_a_record_that_cannot_be_read_is_not_a_refusal(tmp_path):
    """An unreadable record means the previous drive left nothing to compare,
    and clearing it is what the clear is for. A refusal here would strand a
    directory nobody could reuse."""
    wd = _driven(tmp_path, "opus", "low")
    (wd / "driver.json").write_text("{oops", encoding="utf-8")
    assert rc.occupied_by_another_cell(wd, "opus", "high") is None
    (wd / "driver.json").write_text("null", encoding="utf-8")
    assert rc.occupied_by_another_cell(wd, "opus", "high") is None


def test_a_record_from_before_the_pins_existed_is_not_a_refusal(tmp_path):
    """Rows scored before 0.1.617 carry neither; absent stays absent."""
    wd = tmp_path / "a0" / "T3-recall"
    wd.mkdir(parents=True)
    (wd / "driver.json").write_text(json.dumps({"verdict": "driven"}),
                                    encoding="utf-8")
    assert rc.occupied_by_another_cell(wd, "opus", "high") is None
