"""One reader for the platform roster, and the discipline it inherited.

The five parsers this replaced differed in exactly one way that mattered: only
`check_repo`'s checked that what came back was a non-empty list. So these
assert the careful behaviour on the shared reader, and that the tools which
depend on the registry now get it too.
"""
import json

import platform_registry as pr
import pytest


def _tree(tmp_path, doc):
    (tmp_path / "adapters").mkdir(parents=True, exist_ok=True)
    (tmp_path / "adapters/platforms.json").write_text(
        json.dumps(doc), encoding="utf-8")
    return tmp_path


GOOD = {"platforms": [{"id": "alpha", "tier": "full"},
                      {"id": "beta", "tier": "prompt"}]}


def test_the_roster_is_read_in_registry_order(tmp_path):
    assert [p["id"] for p in pr.platforms(_tree(tmp_path, GOOD))] == ["alpha", "beta"]
    assert pr.platform_ids(tmp_path) == {"alpha", "beta"}
    assert pr.platform_by_id(tmp_path)["beta"]["tier"] == "prompt"


def test_a_registry_that_declares_nothing_is_a_failure_not_an_empty_roster(tmp_path):
    """The four careless readers returned `[]` here, which reads as a
    repository with no platforms rather than a broken registry."""
    empty: list[dict] = [{"platforms": []}, {"platforms": {}}, {"schema": 1}]
    for doc in empty:
        with pytest.raises(ValueError):
            pr.platforms(_tree(tmp_path, doc))


def test_an_unparseable_registry_raises(tmp_path):
    (tmp_path / "adapters").mkdir(parents=True, exist_ok=True)
    (tmp_path / "adapters/platforms.json").write_text("{not json", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        pr.registry_doc(tmp_path)


def test_the_live_registry_reads_and_agrees_with_its_notes():
    ids = pr.platform_ids()
    assert len(ids) == len(pr.platforms())        # no id recorded twice
    assert "claude-code" in ids
