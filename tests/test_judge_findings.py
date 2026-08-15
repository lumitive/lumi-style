"""The judge-finding contract: a quotation that is actually in the document.

This is where a hallucinated finding dies. Every other test here is about
keeping the contract narrow enough that it cannot become a scoring judge.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "ops"))

import judge_findings as jf  # noqa: E402

DOC = "<h2>Install density beats install count</h2><p>Clustering work helps.</p>"


def _f(**kw):
    base = {"where": "p5", "claim": "reads as a slogan",
            "quote": "Install density beats install count"}
    base.update(kw)
    return base


def test_a_real_quotation_is_accepted():
    accepted, rejected = jf.review([_f()], DOC)
    assert len(accepted) == 1 and rejected == []


def test_an_invented_quotation_is_rejected():
    """A model that cannot produce the sentence it objects to has not found
    anything. This is the whole reason the contract exists."""
    _a, rejected = jf.review([_f(quote="we are revolutionising synergy")], DOC)
    assert rejected and "do not appear" in rejected[0][1]


def test_a_paraphrase_is_not_a_quotation():
    _a, rejected = jf.review([_f(quote="install density is better than count")], DOC)
    assert rejected


def test_markup_between_the_words_does_not_break_a_real_quotation():
    """A model saw the rendered text, not the tags; it must not be held to them."""
    doc = "<h2>Install <em>density</em> beats install count</h2>"
    accepted, _r = jf.review([_f()], doc)
    assert len(accepted) == 1


def test_a_fragment_is_rejected():
    _a, rejected = jf.review([_f(quote="the")], DOC)
    assert rejected and "fragment" in rejected[0][1]


def test_there_is_no_field_for_a_score():
    """A judge that scores is fooled by fluent verbosity; that is measured."""
    _a, rejected = jf.review([_f(score=2)], DOC)
    assert rejected and "no field for a score" in rejected[0][1]


def test_a_finding_missing_its_claim_is_rejected():
    f = _f()
    del f["claim"]
    _a, rejected = jf.review([f], DOC)
    assert rejected and "missing" in rejected[0][1]


def test_rejection_is_a_fact_about_the_finding_not_the_document():
    """Nothing here reports on the document itself — the module offers no
    verdict, no score and no exit code that a build could gate on."""
    assert not hasattr(jf, "gate")
    assert "verdict" not in jf.FIELDS
