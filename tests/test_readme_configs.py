"""The one table in a consumer file that names vendor model strings.

README ships to users. A hand-written table of model names in it is a rotting
claim with no forcing function, and this repository has spent twenty-six
releases on that class of defect. So the block is generated, `--check` runs in
CI, and every row carries `n`, a date and the skill version its runs read.

What these hold is the SPLICE and the ROW SHAPE. The derivation itself belongs
to `agent_evals.py` and is tested there — one tool owns what a configuration
costs.
"""
import build_readme_configs as brc
import pytest


def _doc(body="old text\n"):
    return f"# LUMI\n\nintro\n\n{brc.MARK}\n{body}{brc.END}\n\ntail\n"


def test_the_block_replaces_itself_rather_than_accumulating():
    once = brc.splice(_doc(), brc.block())
    twice = brc.splice(once, brc.block())
    assert once == twice
    assert once.count(brc.MARK) == 1 and once.count(brc.END) == 1


def test_what_is_outside_the_markers_is_untouched():
    out = brc.splice(_doc(), brc.block())
    assert out.startswith("# LUMI\n\nintro\n\n") and out.endswith("\n\ntail\n")


def test_a_missing_marker_is_a_hard_exit_not_a_silent_append():
    """The two ways a block generator goes wrong. Appending writes a second
    copy on every run; doing nothing reports success while changing nothing.
    Neither may be quiet."""
    with pytest.raises(SystemExit) as caught:
        brc.splice("# LUMI\n\nno markers here\n", brc.block())
    assert "Nothing was written" in str(caught.value)


def test_a_duplicated_marker_is_a_hard_exit(capsys):
    doubled = _doc() + _doc()
    with pytest.raises(SystemExit) as caught:
        brc.splice(doubled, brc.block())
    assert "2 start marker(s)" in str(caught.value)


# --- what a row may and may not say ------------------------------------------

# CELLS ARE INJECTED, because the suite writes to a scratch trace store and the
# real one is EMPTY under pytest. The first version of these called
# `rows_for_readme()` bare: two of them looped over nothing and passed without
# looking, in a file whose whole subject is generators that go quiet.

_CELLS = [
    {"agent": "cursor", "model": "grok-high", "effort": "high", "runs": 5,
     "tokens_per_page": 5398.3, "seconds_per_page": 148.2, "tasks_earned": 3,
     "tasks_attempted": 3, "effort_honoured": True, "measured": "2026-08-26",
     "skill_version": "0.1.614"},
]


def _rows():
    return brc.rows_for_readme(cells=_CELLS, registry=brc.load_registry())


def test_every_registry_platform_gets_a_row():
    """A platform README claims and the block omits reads as a platform that
    was dropped."""
    registry = brc.load_registry()
    rows = _rows()
    assert len(rows) == len(registry)
    for entry in registry:
        assert any(f"**{entry['name']}**" in r for r in rows), entry["id"]


def test_the_two_absences_are_printed_differently():
    """`not measured here` is a machine away; `cannot be measured here` never
    will be. Printing them identically made the platform table read as ten
    pieces of pending work when only six were."""
    rows = "\n".join(_rows())
    assert "not measured here" in rows and "cannot be measured here" in rows


def test_no_row_carries_a_cost_without_its_sample_size():
    """A cost with no `n` beside it reads as a settled number. Nothing here
    repeats a run by design, so most of them are one sample."""
    priced = [r for r in _rows() if "tok/page" in r]
    assert priced, "no row carried a cost; this test would pass on any code"
    for row in priced:
        assert "(n=" in row, row


def test_a_measured_row_names_the_model_the_effort_and_when(capsys):
    row = next(r for r in _rows() if "tok/page" in r)
    for owed in ("grok-high", "effort", "high", "3 of 3", "n=5",
                 "2026-08-26", "0.1.614"):
        assert owed in row, f"{owed!r} is missing from {row!r}"


def test_the_block_says_the_package_cannot_set_a_model():
    """The achievable form of the owner's goal, and the sentence that keeps the
    table from reading as automation. Every platform loads this as a SKILL —
    the agent is already running, with its model fixed, when it reads
    SKILL.md."""
    assert "cannot set your model" in brc.block()


def test_the_block_says_cheaper_is_not_better():
    assert "not a quality ranking" in brc.block()


def test_the_block_reads_no_clock():
    """Every date in it comes from a trace. A `date.today()` would make
    `--check` go red on the day after it was written."""
    text = (brc.ROOT / "scripts" / "build" /
            "build_readme_configs.py").read_text(encoding="utf-8")
    assert "today" not in text and "date.now" not in text
