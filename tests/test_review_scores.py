"""Tests for review_scores.validate — the schema keeper of the C1-C8 score
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
    store["dimensions"] = ["C1"]
    errors = review_scores.validate(store)
    assert len(errors) == 1 and "C1-C8" in errors[0]


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
    rec["self"] = dict.fromkeys(["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"], 5)
    rec["reader"] = dict.fromkeys(["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"])
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


def test_corpus_id_is_required_on_a_new_record():
    """The agreement study joins on it, and the records that predate the rule
    have none — which is why that study has never had one joinable row."""
    store = _store()
    store["reviews"] = [{
        "release": store["reviews"][0]["release"], "genre": "sales",
        "outcome": store["reviews"][0]["outcome"],
        "self": dict.fromkeys(store["dimensions"]),
        "reader": dict.fromkeys(store["dimensions"], 3),
    }]
    assert any("corpus_id is required" in e for e in review_scores.validate(store))


def test_a_schema_one_record_is_history_and_keeps_its_H_dimensions():
    """History is kept verbatim, not back-filled. Inventing a corpus id for a
    document nobody can re-measure would put a fabricated join key in the
    evidence, which is worse than a gap."""
    store = _store()
    store["reviews"][0] = {
        "schema": 1, "release": store["reviews"][0]["release"],
        "genre": "sales", "outcome": store["reviews"][0]["outcome"],
        "self": dict.fromkeys(["H1", "H2", "H3", "H4", "H5", "H6"]),
        "reader": dict.fromkeys(["H1", "H2", "H3", "H4", "H5", "H6"], 3),
    }
    assert review_scores.validate(store) == []
