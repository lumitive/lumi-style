"""`check_fixtures`' own coverage rules, which nothing imported until 0.1.679.

Found by the mutation probe on its first real run: no test file imported
`check_fixtures`, so every mutation of it survived by construction — in a
module that gates in CI and whose whole job is to assert that the other checks
still produce the verdicts the suite expects.
"""
import json
import pathlib

import check_fixtures as cf


def _register(tmp_path, gates):
    (tmp_path / "evals").mkdir()
    (tmp_path / "evals" / "gates.json").write_text(
        json.dumps({"gates": gates}), encoding="utf-8")
    return tmp_path


def _gap(tmp_path, monkeypatch, gates, seen=()):
    monkeypatch.setattr(cf, "ROOT", _register(tmp_path, gates))
    return cf._third_answer_gap(set(seen))


GATE = {"checker": "design", "family": "f", "severity": "gate",
        "since": "0.1.679", "subject": "always"}


def test_a_new_gate_that_says_nothing_about_its_third_answer_fails(tmp_path,
                                                                   monkeypatch):
    """FM-24: a gate that cannot say 'I could not look' prints what a clean
    document prints. Ten instances reached this tree that way."""
    out = _gap(tmp_path, monkeypatch, {"D99_thing": dict(GATE)})
    assert out and "third answer" in out[0]


def test_a_declaration_no_fixture_ever_produced_fails(tmp_path, monkeypatch):
    """Declaring the silence honest is a claim; this holds it to a sighting."""
    gates = {"D99_thing": dict(GATE, na_means="an honest silence")}
    out = _gap(tmp_path, monkeypatch, gates)
    assert out and "no fixture has ever seen it" in out[0]


def test_a_declaration_a_fixture_produced_passes(tmp_path, monkeypatch):
    gates = {"D99_thing": dict(GATE, na_means="an honest silence")}
    assert _gap(tmp_path, monkeypatch, gates, seen=["D99_thing"]) == []


def test_a_gate_that_cannot_be_na_says_why(tmp_path, monkeypatch):
    gates = {"D99_thing": dict(GATE, na_impossible="it grades the document itself")}
    assert _gap(tmp_path, monkeypatch, gates) == []


def test_an_old_gate_is_grandfathered(tmp_path, monkeypatch):
    """Fifty-five gating verdicts predate the rule. A guard that fails on all
    of them the day it ships is a guard someone switches off."""
    gates = {"D01_old": dict(GATE, since="0.1.400")}
    assert _gap(tmp_path, monkeypatch, gates) == []


def test_a_reported_metric_is_not_asked(tmp_path, monkeypatch):
    gates = {"D50_reported": dict(GATE, severity="report")}
    assert _gap(tmp_path, monkeypatch, gates) == []


def test_an_unreadable_register_is_a_finding_not_a_pass(tmp_path, monkeypatch):
    """The rule this whole file is about, applied to itself: a coverage
    computation that could not run is not a coverage computation that
    succeeded."""
    (tmp_path / "evals").mkdir()
    (tmp_path / "evals" / "gates.json").write_text("{not json", encoding="utf-8")
    monkeypatch.setattr(cf, "ROOT", tmp_path)
    out = cf._third_answer_gap(set())
    assert out and "not the same as it being complete" in out[0]


def test_the_cut_version_is_the_one_the_register_can_meet():
    """A literal, not the module's constant. The two newest gates already
    comply, which is what gives the rule teeth without a backfill."""
    assert cf.THIRD_ANSWER_SINCE == "0.1.667"
    register = json.loads(
        (pathlib.Path("evals/gates.json")).read_text(encoding="utf-8"))["gates"]
    bound = [k for k, v in register.items()
             if v.get("severity") == "gate"
             and str(v.get("since", ""))[:1].isdigit()
             and str(v["since"]) >= "0.1.667"]
    assert bound, "the cut binds no gate at all, so the rule is decorative"
