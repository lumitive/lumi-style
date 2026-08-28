"""One reader for the version, and the divergences it replaced, reproduced.

Each case here is a document or an input on which the old implementations gave
different answers. The point is not that the new function is correct in the
abstract — it is that the disagreement is gone, and that the two callers who
needed DIFFERENT behaviour still get it.
"""
import gate_registry
import pytest
import versioning

NEIGHBOURED = '''---
name: lumi-style
cli_version: "9.9.9"
metadata:
  version: "0.1.634"
---
'''


def test_a_neighbouring_version_key_does_not_win(tmp_path):
    """The document three of the seven readers got wrong.

    An unanchored `version: "([\\d.]+)"` matches inside `cli_version:`, so the
    same SKILL.md answered 9.9.9 to three readers and 0.1.634 to four.
    """
    assert versioning.skill_version_in(NEIGHBOURED) == "0.1.634"


def test_a_stampless_document_answers_none_rather_than_a_neighbour():
    assert versioning.skill_version_in("name: lumi-style\n") is None


def test_skill_version_raises_rather_than_recording_unknown(tmp_path):
    """One failure behaviour, chosen. `"unknown"` used to be written into a
    trace's `skill_version` and later compared as a version."""
    (tmp_path / "SKILL.md").write_text("name: lumi-style\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        versioning.skill_version(tmp_path)


def test_the_stamp_is_read_from_the_tree_it_is_told_about(tmp_path):
    (tmp_path / "SKILL.md").write_text(NEIGHBOURED, encoding="utf-8")
    assert versioning.skill_version(tmp_path) == "0.1.634"


def test_ordering_is_numeric_not_lexicographic():
    assert versioning.ver_key("0.1.100") > versioning.ver_key("0.1.99")
    assert max(["0.1.99", "0.1.100"], key=versioning.sort_key) == "0.1.100"


def test_the_two_keys_differ_on_garbage_and_that_is_the_point():
    with pytest.raises(ValueError):
        versioning.ver_key("not-a-version")
    assert versioning.sort_key("not-a-version") == ()
    assert versioning.sort_key(None) == ()
    assert sorted(["0.1.2", "", "0.1.10"], key=versioning.sort_key)[0] == ""


def test_an_unparseable_stamp_is_not_an_exemption():
    """`gate_registry.held` catches the strict key's error and answers held.

    A tolerant key here would have compared `() >= (0, 1, 449)` — False — and
    exempted a document from every gate by giving it a broken stamp.
    """
    name = next(iter(gate_registry.load()))
    assert gate_registry.held(name, "not-a-version") is True
    assert gate_registry.held(name, None) is True


CHANGELOG = """## 0.1.634 — a summary

body

## 0.1.633 — another

## 0.1.632 — and another
"""


def test_releases_are_newest_first():
    assert versioning.releases(text=CHANGELOG) == ["0.1.634", "0.1.633", "0.1.632"]


def test_releases_between_answers_none_when_either_side_is_unknown(tmp_path):
    (tmp_path / "CHANGELOG.md").write_text(CHANGELOG, encoding="utf-8")
    assert versioning.releases_between("0.1.632", "0.1.634", tmp_path) == 2
    assert versioning.releases_between("0.1.634", "0.1.632", tmp_path) == -2
    assert versioning.releases_between("0.1.999", "0.1.634", tmp_path) is None
    assert versioning.releases_between(None, "0.1.634", tmp_path) is None


def test_the_newest_heading_carries_its_summary(tmp_path):
    (tmp_path / "CHANGELOG.md").write_text(CHANGELOG, encoding="utf-8")
    assert versioning.newest_heading(tmp_path) == ("0.1.634", "a summary")


def test_a_heading_with_no_summary_is_not_a_heading():
    assert versioning.newest_heading(text="## 0.1.634\n") is None
    assert versioning.releases(text="## 0.1.634\n") == ["0.1.634"]


def test_the_live_tree_agrees_with_itself():
    assert versioning.skill_version() == versioning.releases()[0]
