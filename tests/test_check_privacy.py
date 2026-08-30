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

# The cross-engagement terms directory is read from LUMI_TERMS_DIR when set;
# every test here points it at an empty directory so a list on the developer's
# machine cannot turn "not attempted" into "loaded" under the suite.
import os  # noqa: E402

import check_privacy as cp  # noqa: E402

_EMPTY = pathlib.Path(__file__).parent / "_no_terms_here"
os.environ["LUMI_TERMS_DIR"] = str(_EMPTY)
cp.TERMS_DIR = _EMPTY


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


# The term half must fail LOUDLY when it could not run — including the shape
# nobody thought of. `load_terms` grew a "missing" status; the verdict
# expression and the exit ladder both still asked about "not_attempted" by
# hand, so a typo in --terms scored BETTER than omitting the flag: exit 0,
# verdict "ok", on the one gating half of layer 1.

def _run(*args):
    p = subprocess.run([sys.executable,
                        str(ROOT / "scripts" / "check" / "check_privacy.py"),
                        str(ROOT / "fixtures" / "deck-pass.en.html"), *args],
                       capture_output=True, text=True)
    return p.returncode, p.stdout


def test_terms_file_that_does_not_exist_fails_rather_than_passing():
    code, out = _run("--terms", "/nonexistent/typo.txt", "--json")
    assert code == 1, "a typo in --terms must not be scored better than no --terms"
    assert '"verdict": "missing"' in out


def test_no_terms_at_all_still_fails():
    code, out = _run("--json")
    assert code == 1
    assert '"verdict": "not_attempted"' in out


def test_a_real_terms_file_with_no_hits_passes(tmp_path):
    lst = tmp_path / "terms.txt"
    lst.write_text("a-term-that-appears-nowhere\n")
    code, out = _run("--terms", str(lst), "--json")
    assert code == 0
    assert '"verdict": "ok"' in out


def test_a_loaded_but_empty_list_fails_rather_than_passing(tmp_path):
    """A *.terms.txt that exists but is comment-only loads as ([], 'loaded') —
    the scan had nothing to search for and must not read as clean (GAP-047,
    the reader-parity half: check_secrets and check_privacy must agree)."""
    lst = tmp_path / "terms.txt"
    lst.write_text("# every term commented out\n\n")
    code, out = _run("--terms", str(lst), "--json")
    assert code == 1, "a loaded-but-empty list must not be scored as a pass"
    assert '"verdict": "no_terms"' in out


def test_a_loaded_but_empty_list_says_so_in_human_output_too(tmp_path):
    """The human-mode print ladder must NOT reprint the reassuring
    'ok · 0 declared term(s), none present' for a loaded-but-empty list — that
    is FM-24 (prints clean when blind) in the operator-facing channel. Guards
    the declared_terms==0 branch, which the --json test alone leaves untested."""
    lst = tmp_path / "terms.txt"
    lst.write_text("# every term commented out\n\n")
    code, out = _run("--terms", str(lst))  # human mode: no --json
    assert code == 1
    assert "no usable terms" in out
    assert "none present" not in out  # the clean-looking line must not appear


def test_every_did_not_run_status_load_terms_can_return_is_handled():
    """A seventh status added to load_terms must not default to a pass.

    This is the parity half: the statuses that mean "did not run" are named
    once, and this asserts the namer covers what the loader can produce.
    """
    import check_privacy as cp
    produced = {"not_attempted", "missing", "loaded"}
    assert set(cp.DID_NOT_RUN) | {"loaded"} == produced


# 0.1.526 — IDEA-15 and the cross-engagement home.

def test_a_short_latin_term_does_not_fire_inside_embedded_base64():
    font = ("@font-face{src:url(data:font/woff2;base64,"
            "d09GMgABAAAAAARayTh2AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "RayTh2RayTh2RayTh2RayTh2RayTh2RayTh2RayTh2==)}")
    l1, _ = _kinds(f"<style>{font}</style><p>clean prose</p>", terms=["Ray"])
    assert l1 == []


def test_a_real_name_in_visible_prose_still_fires(tmp_path):
    l1, _ = _kinds("<p>We met Ray at the plant.</p>", terms=["Ray"])
    assert l1 == ["declared out of bounds"]


def test_a_latin_term_matches_on_word_boundaries_only():
    l1, _ = _kinds("<p>Rayleigh scattering</p>", terms=["Ray"])
    assert l1 == []


def test_a_cjk_term_matches_as_a_substring():
    l1, _ = _kinds("<p>与三花的合作</p>", terms=["三花"])
    assert len(l1) == 1


def test_the_terms_directory_is_read_when_no_path_is_given(tmp_path, monkeypatch):
    (tmp_path / "a.terms.txt").write_text("Ray\n# comment\n", encoding="utf-8")
    (tmp_path / "b.terms.txt").write_text("三花\n", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("ignored\n", encoding="utf-8")
    monkeypatch.setattr(cp, "TERMS_DIR", tmp_path)
    terms, status = cp.load_terms(None)
    assert status == "loaded" and sorted(terms) == ["Ray", "三花"]


def test_an_empty_terms_directory_is_not_attempted(tmp_path, monkeypatch):
    monkeypatch.setattr(cp, "TERMS_DIR", tmp_path)
    assert cp.load_terms(None) == ([], "not_attempted")
