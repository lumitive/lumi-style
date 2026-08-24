"""The small refusals and silences that cost an author a round trip.

Each of these was measured in a validation round as a rebuild round or a
sequence of extra calls, and each is a case where the tool was right about the
document and unclear about itself.
"""
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts" / "check"))

import check_outline  # noqa: E402

_PLAN = """# Plan

## Part A

- A title carrying a 41% fact
  analysis: compare | finding: f | implication: i

{omissions}
"""


def _omissions(text):
    parsed = check_outline.parse(_PLAN.format(omissions=text))
    for item in parsed:
        if (isinstance(item, list) and item and isinstance(item[0], dict)
                and "section" in item[0]):
            return {o["section"]: o["reason"] for o in item}
    return {}


def test_an_em_dash_separates_the_reason():
    assert _omissions("omitted: sizing — commissioned separately") == {
        "sizing": "commissioned separately"}


def test_a_spaced_hyphen_separates_the_reason_too():
    """`omitted: sizing - <reason>` reported "declared without a reason" while
    the reason sat right there, and the accepted syntax was written down only
    in the script's own docstring. One rebuild round."""
    assert _omissions("omitted: sizing - commissioned separately") == {
        "sizing": "commissioned separately"}


def test_an_en_dash_separates_the_reason_too():
    assert _omissions("omitted: sizing – commissioned separately") == {
        "sizing": "commissioned separately"}


def test_a_hyphenated_section_name_is_not_split_at_its_own_hyphen():
    """Why the hyphen must be SPACED: a bare one would call this section
    "go" and take the rest as its reason."""
    assert _omissions("omitted: go-to-market — deferred to Q3") == {
        "go-to-market": "deferred to Q3"}


def test_a_bare_omission_still_has_no_reason():
    """Widening the separators must not turn a genuine bare declaration into
    a passing one — that is the finding the gate exists for."""
    assert _omissions("omitted: sizing") == {"sizing": ""}


def test_the_reason_syntax_is_named_in_the_failure():
    """The message said what was wrong and not what the author should type."""
    *_rest, findings = check_outline.review(
        _PLAN.format(omissions="omitted: sizing"))
    bare = [f for f in findings if f.get("check") == "declared omission"]
    assert bare, f"no declared-omission finding: {findings}"
    detail = bare[0]["detail"]
    assert "em dash" in detail and "hyphen" in detail, detail


def test_check_design_help_names_the_json_shape():
    """An agent reading `--json` from a shell has no normaliser; three
    validation rounds each rediscovered the list by crashing on it."""
    out = subprocess.run(
        [sys.executable, str(ROOT / "scripts/check/check_design.py"), "--help"],
        capture_output=True, text=True, cwd=ROOT).stdout
    assert "LIST" in out and "[0]" in out, out


def test_a_licence_phrase_in_a_stylesheet_does_not_name_an_image_s_terms():
    """D25 searched the raw file, so a `<style>` comment containing "screenshot
    of" made a deck with an unattributed linked image report `terms named`.
    The comment that did it was written in the same release, about an unrelated
    defect — which is how cheaply this gate could be silenced."""
    sys.path.insert(0, str(ROOT / "scripts" / "lib"))
    import check_design
    doc = ('<style>/* a screenshot of the figure shows the defect */</style>'
           '<img src="https://example.org/plate.png" alt="a plate">')
    assert not check_design.d25_image_provenance(doc)["licence_named"]


def test_terms_a_reader_can_see_still_count():
    sys.path.insert(0, str(ROOT / "scripts" / "lib"))
    import check_design
    doc = ('<img src="https://example.org/plate.png" alt="a plate">'
           '<p class="fnote">Photograph: own work, used under CC BY 4.0.</p>')
    assert check_design.d25_image_provenance(doc)["licence_named"]
