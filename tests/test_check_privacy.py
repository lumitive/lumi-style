"""check_privacy — three layers, and the third one says it is not mechanised.

Most of these are false-positive tests. Layer 2 is reported, and a reported
section that cries wolf is a reported section nobody reads: the first version
produced six phone-number findings on a clean fixture, every one of them a
geography attribute full of arc indices.
"""
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "check"))

import check_privacy as cp  # noqa: E402


def _kinds(html, terms=()):
    l1, l2 = cp.scan(html, list(terms))
    return [f["kind"] for f in l1], [f["kind"] for f in l2]


def test_credential_in_prose_gates():
    l1, _ = _kinds("<p>key AKIAIOSFODNN7EXAMPLE here</p>")
    assert "AWS access key id" in l1


def test_credential_in_an_attribute_also_gates():
    """A token in a data- attribute has left the boundary just as surely."""
    l1, _ = _kinds('<div data-x="AKIAIOSFODNN7EXAMPLE">visible</div>')
    assert "AWS access key id" in l1


def test_declared_term_gates_without_being_echoed():
    l1, _ = _kinds("<p>The Northwind rollout is on track.</p>", ["Northwind"])
    assert l1 == ["declared out of bounds"]


def test_a_declared_term_never_appears_in_the_finding():
    """The out-of-bounds list is engagement data; the report must not carry it."""
    findings, _ = cp.scan("<p>Northwind</p>", ["Northwind"])
    assert all("Northwind" not in str(f) for f in findings)


def test_email_is_reported_not_gated():
    l1, l2 = _kinds("<p>Write to ops@example.com.</p>")
    assert l1 == [] and "email address" in l2


def test_phone_at_the_end_of_a_sentence_is_found():
    """The first guard excluded a trailing full stop and found nothing."""
    _l1, l2 = _kinds("<p>Call +1 555 0100.</p>")
    assert "direct phone number" in l2


def test_a_list_of_numbers_is_not_a_phone_number():
    _l1, l2 = _kinds("<p>arc list 104 105 1061 107 108</p>")
    assert l2 == []


def test_markup_attributes_are_not_searched_for_contact_details():
    """Layer 2 asks what a reader could act on; markup is not its business."""
    _l1, l2 = _kinds('<path data-arcs="104 105 1061 107 108"></path>')
    assert l2 == []


def test_a_version_string_is_not_a_phone_number():
    _l1, l2 = _kinds("<p>version 1.2.3 shipped</p>")
    assert l2 == []


def test_no_terms_supplied_is_not_a_pass():
    """A check nobody ran must not read like a check that found nothing."""
    _terms, status = cp.load_terms(None)
    assert status == "not_attempted"
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check" / "check_privacy.py"),
         str(ROOT / "fixtures" / "deck-pass.en.html")],
        capture_output=True, text=True)
    assert proc.returncode != 0
    assert "NOT ATTEMPTED" in proc.stdout


def test_layer_three_is_named_and_not_claimed():
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check" / "check_privacy.py"),
         str(ROOT / "fixtures" / "deck-pass.en.html")],
        capture_output=True, text=True)
    assert "layer 3" in proc.stdout
    assert "does not answer that" in proc.stdout


def test_clean_fixtures_report_nothing_at_layer_two():
    for name in ("deck-pass.en.html", "deck-broken.en.html"):
        raw = (ROOT / "fixtures" / name).read_text(encoding="utf-8")
        _l1, l2 = cp.scan(raw, [])
        assert l2 == [], f"{name} produced layer-2 noise: {l2[:3]}"
