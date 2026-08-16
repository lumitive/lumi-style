"""The storyline roster and the STORYLINES tuple are held to each other.

Synthetic trees, so each direction is proven to FAIL as well as pass — a guard
only ever seen passing is FM-01. The case it was written from: `STORYLINES` had
been a closed tuple since the two-axis split shipped and not one of its six
names appeared anywhere in `references/`, so an author choosing a storyline had
nothing to read.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "check"))

import check_repo  # noqa: E402

ROSTER = """# LUMI Storyline Templates

## The storyline vocabulary

| storyline | the shape of the argument | full skeleton |
|---|---|---|
| `market-analysis` | the market is this | — |
| `proposal` | here is a decision | Template 5 |

## Template 1 · something else
"""

REGISTRY = '''STORYLINES = ("market-analysis", "proposal")
'''


def _tree(tmp_path, roster=ROSTER, registry=REGISTRY):
    (tmp_path / "references").mkdir(parents=True, exist_ok=True)
    (tmp_path / "scripts" / "lib").mkdir(parents=True, exist_ok=True)
    (tmp_path / "references" / "storyline-templates.md").write_text(
        roster, encoding="utf-8")
    (tmp_path / "scripts" / "lib" / "deliverable_registry.py").write_text(
        registry, encoding="utf-8")
    return tmp_path


def _run(tmp_path, **kw):
    original = check_repo.ROOT
    check_repo.ROOT = _tree(tmp_path, **kw)
    try:
        return check_repo.check_storyline_vocabulary()
    finally:
        check_repo.ROOT = original


def test_a_matching_pair_passes(tmp_path):
    assert _run(tmp_path) == []


def test_a_name_in_code_and_not_in_the_roster_fails(tmp_path):
    errors = _run(tmp_path,
                  registry='STORYLINES = ("market-analysis", "proposal", "gtm")\n')
    assert any("'gtm'" in e and "not in the roster" in e for e in errors), errors


def test_a_name_in_the_roster_and_not_in_code_fails(tmp_path):
    roster = ROSTER.replace("| `proposal` |",
                            "| `postmortem` | what went wrong | — |\n| `proposal` |")
    errors = _run(tmp_path, roster=roster)
    assert any("'postmortem'" in e and "not in STORYLINES" in e for e in errors), errors


def test_a_missing_roster_section_fails(tmp_path):
    errors = _run(tmp_path, roster="# LUMI Storyline Templates\n\n## Template 1\n")
    assert errors and "no storyline roster" in errors[0], errors


def test_an_empty_tuple_fails_rather_than_passing_vacuously(tmp_path):
    """The shape that makes a guard useless: nothing on one side, nothing to
    compare, green."""
    errors = _run(tmp_path, registry="STORYLINES = ()\n")
    assert errors and "vacuously" in errors[0], errors
