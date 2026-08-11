"""Tests for review_scores.validate — the schema keeper of the H1-H6 score
store, including proof that it can fail (a validator that cannot fail is this
repository's most-shipped defect family).
"""
import copy
import json
import pathlib

import review_scores

ROOT = pathlib.Path(__file__).resolve().parent.parent


def _store():
    return json.loads((ROOT / "reviews" / "scores.json").read_text("utf-8"))


def test_shipped_store_validates_clean():
    assert review_scores.validate(_store()) == []


def test_wrong_dimensions_short_circuit():
    store = _store()
    store["dimensions"] = ["H1"]
    errors = review_scores.validate(store)
    assert len(errors) == 1 and "H1-H6" in errors[0]


def test_free_text_key_is_refused():
    """The red-line-9 defense: the store has no free-text field on purpose,
    and a new key is how a client name would arrive."""
    store = _store()
    store["reviews"][0]["notes"] = "great client, Acme Corp"
    errors = review_scores.validate(store)
    assert any("schema does not define" in e for e in errors)


def test_self_five_without_reader_is_refused():
    store = _store()
    rec = copy.deepcopy(store["reviews"][0])
    rec["self"] = dict.fromkeys(["H1", "H2", "H3", "H4", "H5", "H6"], 5)
    rec["reader"] = dict.fromkeys(["H1", "H2", "H3", "H4", "H5", "H6"])
    store["reviews"].append(rec)
    errors = review_scores.validate(store)
    assert any("never self-score 5" in e for e in errors)


def test_score_out_of_anchor_range_is_refused():
    store = _store()
    rec = copy.deepcopy(store["reviews"][0])
    rec["reader"] = dict(rec["reader"], H1=0)
    store["reviews"].append(rec)
    errors = review_scores.validate(store)
    assert any("anchors run" in e for e in errors)
