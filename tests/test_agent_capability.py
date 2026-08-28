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
    assert ac.validate_pin(CURSOR, "cursor-grok-4.6-high", root)[0] is True
    ok, why = ac.validate_pin(CURSOR, "cursor-grok-4.6-max", root)
    assert ok is False and "does not offer" in why


def test_an_agent_nobody_probed_is_not_judged(tmp_path):
    """No evidence is not evidence of absence — the whole reason the probe
    keeps `waived` and `failed` apart from an empty list."""
    root = _vocab(tmp_path, {})
    assert ac.validate_pin(CURSOR, "anything-at-all", root) == (True, "")
    assert ac.offered("cursor", root) is None


def test_a_waived_probe_records_nothing_rather_than_an_empty_set(tmp_path):
    root = _vocab(tmp_path, {"hermes": {"ids": None}})
    assert ac.offered("hermes", root) is None


def test_a_changed_vocabulary_is_named_on_both_sides(tmp_path):
    root = _vocab(tmp_path, {"cursor": {"ids": ["a", "b"]}})
    lines = ac.record_vocabularies({"cursor": {"ids": ["b", "c"]}}, root)
    assert len(lines) == 1
    assert "gone ['a']" in lines[0] and "new ['c']" in lines[0]
    assert ac.offered("cursor", root) == ["b", "c"]


def test_an_unchanged_vocabulary_says_nothing(tmp_path):
    root = _vocab(tmp_path, {"cursor": {"ids": ["a"]}})
    assert ac.record_vocabularies({"cursor": {"ids": ["a"]}}, root) == []


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
