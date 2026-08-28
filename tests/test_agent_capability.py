"""One module owns the vocabulary; three callers ask three different questions.

The point of these is the boundary as much as the behaviour: capability (what
the CLI offers), intent (what we asked for) and observation (what it said it
used) stay three facts, and what is shared is the knowledge around them.
"""
import json

import agent_capability as ac

CURSOR = {"id": "cursor", "drive": ["cursor-agent"],
          "drive_effort_in_model": "{model}-{effort}",
          "efforts": ["low", "medium", "high", "xhigh", "max"]}
HERMES = {"id": "hermes", "drive": ["hermes"], "drive_effort_flag": "--reasoning",
          "efforts": ["none", "minimal", "low", "medium", "high", "xhigh",
                      "max", "ultra"]}
GEMINI = {"id": "gemini-cli", "drive": ["gemini"],
          "efforts_waiver": "no reasoning level exists to enumerate"}


def test_the_three_effort_shapes_are_told_apart():
    assert ac.effort_style(CURSOR) == ac.IN_MODEL
    assert ac.effort_style(HERMES) == ac.FLAG
    assert ac.effort_style(GEMINI) == ac.NONE


def test_a_level_is_answered_from_the_registry_not_from_a_shared_tuple():
    """Hermes accepts eight. The tuple this harness records is five, and that
    is a different question — see the driver, which asks both."""
    assert ac.effort_refusal(HERMES, "ultra") is None


def test_an_agent_with_no_effort_concept_is_not_refused():
    """A horse race passes one `--effort` to four CLIs, and the one with no
    reasoning level must still run — pinning nothing and recording so."""
    assert ac.effort_refusal(GEMINI, "high") is None
    assert ac.effort_style(GEMINI) == ac.NONE


def test_an_effort_the_cli_does_not_have_is_refused_with_the_list():
    fam = {**CURSOR, "efforts": ["low", "medium", "high", "xhigh"]}
    why = ac.effort_refusal(fam, "max")
    assert why and "does not accept effort 'max'" in why


def test_a_composed_id_reports_the_level_it_carries():
    assert ac.effort_in_model(CURSOR, "cursor-grok-4.6-high") == "high"
    assert ac.effort_in_model(CURSOR, "cursor-grok-4.6-xhigh") == "xhigh"


def test_a_version_number_is_not_an_effort_level():
    """`cursor-grok-4.6` ends in `4.6`; the first version read it as a level."""
    assert ac.effort_in_model(CURSOR, "cursor-grok-4.6") is None
    assert ac.effort_in_model(HERMES, "anything-high") is None   # not in-model


def test_composition_pins_both_axes_or_says_it_did_not():
    assert ac.compose_model(CURSOR, "cursor-grok-4.6", "high") == \
        ("cursor-grok-4.6-high", True)
    assert ac.compose_model(HERMES, "m", "high") == ("m", True)
    assert ac.compose_model(GEMINI, "m", "high") == ("m", False)


def _vocab(tmp_path, doc):
    (tmp_path / "conformance").mkdir(parents=True, exist_ok=True)
    (tmp_path / "conformance/vocabularies.json").write_text(
        json.dumps(doc), encoding="utf-8")
    return tmp_path


def test_a_pin_is_refused_against_a_recorded_vocabulary(tmp_path):
    root = _vocab(tmp_path, {"cursor": {"ids": ["cursor-grok-4.6-high"]}})
    assert ac.validate_pin(CURSOR, "cursor-grok-4.6-high", root)[0] == ac.OK
    state, why = ac.validate_pin(CURSOR, "cursor-grok-4.6-max", root)
    assert state == ac.REFUSED and "does not offer" in why


def test_an_agent_nobody_probed_is_not_judged_and_says_so(tmp_path):
    """No evidence is not evidence of absence — but it is not `ok` either.

    Both returned `(True, "")` and printed nothing, so the check working and
    the check not running looked identical at the point the driver's own
    comment says the check matters most.
    """
    root = _vocab(tmp_path, {})
    state, why = ac.validate_pin(CURSOR, "anything-at-all", root)
    assert state == ac.UNVALIDATED and "no recorded vocabulary" in why
    assert ac.offered("cursor", root) == (None, None)


def test_a_damaged_entry_is_not_the_honest_absence_it_used_to_join(tmp_path):
    """A damaged entry is NOT the honest absence it used to join silently."""
    root = _vocab(tmp_path, {"hermes": {"ids": None}})
    ids, problem = ac.offered("hermes", root)
    assert ids is None and problem and "damaged entry" in problem
    assert ac.validate_pin(HERMES, "anything", root)[0] == ac.UNVALIDATED


def test_a_store_that_cannot_be_read_is_named_not_ignored(tmp_path):
    (tmp_path / "conformance").mkdir(parents=True, exist_ok=True)
    (tmp_path / "conformance/vocabularies.json").write_text("<<<<<<< HEAD",
                                                            encoding="utf-8")
    doc, problem = ac.recorded_vocabularies(tmp_path)
    assert doc == {} and problem and "could not be read" in problem
    for body in ("null", "[]"):
        (tmp_path / "conformance/vocabularies.json").write_text(body,
                                                                encoding="utf-8")
        _doc, problem = ac.recorded_vocabularies(tmp_path)
        assert problem and "not a map" in problem


def test_the_fast_twins_carry_their_level(tmp_path):
    """Eight of Cursor's twenty-three recorded ids are `-fast` twins, and
    reading only the last segment found the level on none of them."""
    for model, level in (("cursor-grok-4.6-high-fast", "high"),
                         ("cursor-grok-4.6-medium-fast", "medium"),
                         ("cursor-grok-4.6-fast", None)):
        assert ac.effort_in_model(CURSOR, model) == level


def test_a_changed_vocabulary_is_named_on_both_sides(tmp_path):
    root = _vocab(tmp_path, {"cursor": {"ids": ["a", "b"]}})
    lines = ac.record_vocabularies({"cursor": {"ids": ["b", "c"]}}, root)
    assert len(lines) == 1
    assert "gone ['a']" in lines[0] and "new ['c']" in lines[0]
    assert ac.offered("cursor", root) == (["b", "c"], None)


def test_an_unchanged_vocabulary_says_nothing(tmp_path):
    root = _vocab(tmp_path, {"cursor": {"ids": ["a"]}})
    assert ac.record_vocabularies({"cursor": {"ids": ["a"]}}, root) == []


def test_a_damaged_store_refuses_the_write_rather_than_losing_the_probes(tmp_path):
    """`prior.update()` on a damaged store threw away probes already paid for."""
    import pytest
    (tmp_path / "conformance").mkdir(parents=True, exist_ok=True)
    (tmp_path / "conformance/vocabularies.json").write_text("{oops",
                                                            encoding="utf-8")
    with pytest.raises(SystemExit):
        ac.record_vocabularies({"cursor": {"ids": ["a"]}}, tmp_path)


def test_the_effort_waiver_is_returned_and_not_only_the_refusal(tmp_path):
    """The second channel of `declared_efforts`, asserted nowhere until a
    review looked: without it no caller can say WHY a platform has none."""
    levels, waiver = ac.declared_efforts(GEMINI)
    assert levels is None and waiver and "no reasoning level" in waiver
    assert ac.declared_efforts(HERMES)[1] is None


def test_the_model_comparator_keeps_its_three_answers():
    assert ac.same_model("cursor-grok-4.6-high", "Cursor Grok 4.6 High") is True
    assert ac.same_model("cursor-grok-4.6-high", "cursor-grok-4.6") is None
    assert ac.same_model("grok", "composer") is False
    assert ac.same_model(None, "anything") is None


def test_the_probe_answers_waived_with_the_registry_reason():
    state, detail = ac.probe_models({"id": "x", "models_waiver": "no listing"})
    assert state == "waived" and detail == "no listing"


def test_the_probe_answers_absent_for_a_binary_that_is_not_here():
    state, detail = ac.probe_models(
        {"id": "x", "models": ["definitely-not-installed-xyz", "--list"]})
    assert state == "absent" and "one install away" in detail
