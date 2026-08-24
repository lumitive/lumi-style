"""The judge-finding contract: a quotation that is actually in the document.

This is where a hallucinated finding dies. Every other test here is about
keeping the contract narrow enough that it cannot become a scoring judge.
"""
import json
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


# --- the finding you took ----------------------------------------------------

DOC_BEFORE = "<p>We are revolutionising how teams unlock value at scale.</p>"
DOC_AFTER = "<p>Seven teams cut settlement time from four days to one.</p>"


def test_a_finding_whose_sentence_was_rewritten_is_rejected_against_the_new_text():
    """The state this change is about: the de-AI pass EXISTS to change the
    sentence, so once it has, the quotation no longer appears and the finding
    that caused the repair is refused. The tool could only ever validate the
    advice you did NOT take."""
    f = [{"where": "p4 title", "claim": "sounds like a press release",
          "quote": "revolutionising how teams unlock value"}]
    accepted, rejected = jf.review(f, DOC_AFTER)
    assert not accepted and rejected


def test_a_fixed_finding_is_checked_against_the_text_it_objected_to():
    """`--before` names the pre-repair snapshot. The contract does not move:
    the quotation must appear VERBATIM in some version — what changes is which
    version it is held to."""
    f = [{"where": "p4 title", "claim": "sounds like a press release",
          "quote": "revolutionising how teams unlock value", "fixed": True}]
    accepted, rejected = jf.review(f, DOC_AFTER, before_text=DOC_BEFORE)
    assert accepted and not rejected, rejected


def test_a_fixed_finding_still_needs_a_real_quotation():
    """A hallucinated quote dies exactly as before — `--before` widens where
    the words may be found, never whether they must exist."""
    f = [{"where": "p4 title", "claim": "invented",
          "quote": "words that were never in either version", "fixed": True}]
    accepted, rejected = jf.review(f, DOC_AFTER, before_text=DOC_BEFORE)
    assert not accepted and rejected


def test_fixed_is_refused_when_no_before_snapshot_was_given():
    """Claiming a repair without producing the text repaired is a claim with
    no evidence, and is refused rather than quietly accepted."""
    f = [{"where": "p4 title", "claim": "sounds like a press release",
          "quote": "revolutionising how teams unlock value", "fixed": True}]
    accepted, rejected = jf.review(f, DOC_AFTER)
    assert not accepted
    assert any("--before" in r[1] for r in rejected), rejected


def test_a_tag_only_quote_is_not_evidence():
    """The word floor ran on the RAW string and the membership test on the
    normalised one, so `<b> <i> <u>` counted as three words, normalised to the
    empty string, and `"" in haystack` is True — a finding quoting nothing,
    printed as `evidence attached`."""
    f = [{"where": "p1", "claim": "tag-only quote", "quote": "<b> <i> <u>"}]
    accepted, rejected = jf.review(f, DOC_AFTER)
    assert not accepted and rejected


def test_fixed_is_refused_when_the_sentence_is_still_there():
    """`fixed` asserts two things and both are checkable: the sentence was
    there, and it is not there now. Accepting on "in either text" let the same
    file be passed as both, so a repair could be declared against an unrepaired
    document and printed as validated."""
    still_there = "<p>We are revolutionising how teams unlock value.</p>"
    f = [{"where": "p4", "claim": "claimed a repair", "fixed": True,
          "quote": "revolutionising how teams unlock value"}]
    # the sentence is in BOTH texts: nothing was repaired
    accepted, rejected = jf.review(f, still_there, before_text=still_there)
    assert not accepted
    assert any("still in the document" in r[1] for r in rejected), rejected


def test_a_dimension_outside_the_rubric_is_refused():
    """The dimension list is imported from `rubric_items`, not retyped — a
    second C1-C8 in this file is the drift that module was extracted to stop,
    and it already outlived one list offering C1-C7 after C8 shipped."""
    f = [{"where": "p1", "claim": "c", "quote": "says something ordinary",
          "dimension": "C9"}]
    accepted, rejected = jf.review(f, "<p>says something ordinary</p>")
    assert not accepted and "C9" in rejected[0][1]


def test_a_finding_may_name_no_dimension():
    """Optional. A finding that points at a sentence is a finding whether or
    not the model could file it."""
    f = [{"where": "p1", "claim": "c", "quote": "says something ordinary"}]
    accepted, _ = jf.review(f, "<p>says something ordinary</p>")
    assert len(accepted) == 1


def test_the_report_groups_by_dimension(tmp_path):
    """Parsed into groups, not grepped for headings.

    A substring check passed a version that printed every heading and listed
    EVERY finding under each of them, and passed a version that reversed the
    order. Headings rendering is not grouping.
    """
    import subprocess
    doc = tmp_path / "d.html"
    doc.write_text("<p>says something ordinary and also mentions a second thing</p>")
    fj = tmp_path / "f.json"
    fj.write_text(json.dumps([
        {"where": "p1", "claim": "alpha", "quote": "says something ordinary",
         "dimension": "C8"},
        {"where": "p2", "claim": "beta", "quote": "mentions a second thing"}]))
    out = subprocess.run(
        [sys.executable, str(ROOT / "scripts/ops/judge_findings.py"), str(fj),
         "--document", str(doc)], capture_output=True, text=True, cwd=ROOT).stdout

    groups: dict[str, list[str]] = {}
    current = None
    for line in out.splitlines():
        if line.strip().startswith("── "):
            current = line.strip()[3:].split(" · ")[0]
            groups[current] = []
        elif current and "note  " in line:
            groups[current].append(line.split(": ", 1)[1].strip())
    assert list(groups) == ["C8", "unfiled"], groups
    assert groups["C8"] == ["alpha"], groups
    assert groups["unfiled"] == ["beta"], groups


def test_the_dimension_list_is_the_rubric_s_own():
    """Imported, not retyped. A second C1-C8 in this file is the drift
    `rubric_items` was extracted to stop, and a retyped list missing C1
    survived every other test."""
    import rubric_items
    assert jf.DIMENSIONS == tuple(rubric_items.DIM_TITLE)


def test_the_judge_still_has_no_field_for_a_score():
    """The contract this file exists for: a judge that scores gets fooled by
    fluent verbosity, and that is measured."""
    f = [{"where": "p1", "claim": "c", "quote": "says something ordinary",
          "score": 3}]
    accepted, rejected = jf.review(f, "<p>says something ordinary</p>")
    assert not accepted and "score" in rejected[0][1]
