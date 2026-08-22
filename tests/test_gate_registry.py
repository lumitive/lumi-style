"""The gate register, and the three misclassifications that made it necessary.

A gate used to be a tuple in a function body, classified by whether its display
string contained `(gates)`. Four readers parsed that string with three different
rules, and the repository shipped three rows in the wrong set because of it. The
register is the declaration those readers now share; `check_repo`'s
`gate declarations` guard holds it to the checkers, so it can add knowledge and
cannot contradict them.

These tests are about the register's own contract. The parity half — that it
agrees with the checkers — is `tests/test_check_repo_guards_wave4.py`'s.
"""
import json
import pathlib

import gate_registry as gr
import gating

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _tree(tmp_path, gates):
    (tmp_path / "SKILL.md").write_text("stub\n")
    (tmp_path / "evals").mkdir(exist_ok=True)
    (tmp_path / "evals" / "gates.json").write_text(
        json.dumps({"schema": 1, "gates": gates}))
    return tmp_path


ROW = {"checker": "design", "family": "brand-mark", "severity": "gate",
       "since": "0.1.560"}


# --- the three rows that were classified wrongly -----------------------------

def test_the_chinese_banned_gate_is_visible():
    """`M4zh_banned_hits` gates in check_prose's own exit and was returned by
    NOBODY: the id pattern `(M\\d+)_` cannot match `M4zh_`, so the Chinese
    banned-phrase gate was absent from `run_conformance`'s `all-gating` require
    set entirely."""
    assert "M4zh_banned_hits" in gr.gates()
    assert gating.gating_metrics({"M4zh_banned_hits": "FAIL"}) == {"M4zh_banned_hits"}
    assert "M4zh" in gating.every_gating_name(), (
        "the rule register cites metrics by id; M4zh needs one or no rule can "
        "name the gate")


def test_a_reported_row_is_not_a_gate_because_its_family_gates():
    """The prefix rule inherited a family's classification onto every row in
    it. Both of these say `reported` in their own targets."""
    for row in ("D38_agenda_run_echo", "D37_caption_name_len"):
        assert gr.load()[row]["severity"] == "reported", row
        assert gating.gating_metrics({row: "ok"}) == set(), row


# --- `since`, and what it must not become ------------------------------------

def test_an_older_document_is_not_held_to_a_later_gate(tmp_path):
    root = _tree(tmp_path, {"G": dict(ROW, since="0.1.560")})
    assert gr.held("G", "0.1.560", root) is True
    assert gr.held("G", "0.1.561", root) is True
    assert gr.held("G", "0.1.522", root) is False


def test_a_document_with_no_version_stamp_is_held_to_everything(tmp_path):
    """An absent stamp must never become an exemption — the cheapest way to
    escape every gate would otherwise be to omit the one line that says which
    rules you were written against."""
    root = _tree(tmp_path, {"G": dict(ROW, since="0.1.560")})
    assert gr.held("G", None, root) is True
    assert gr.held("G", "not-a-version", root) is True


def test_always_binds_every_document(tmp_path):
    """Six gates predate the version history this CHANGELOG keeps, and the
    scheme they were numbered under (1.6.0-3.3.0) sorts ABOVE 0.1.560 — written
    as numbers they would have silenced themselves."""
    root = _tree(tmp_path, {"G": dict(ROW, since=gr.ALWAYS)})
    assert gr.held("G", "0.1.001", root) is True
    assert gr.held("G", None, root) is True
    live = gr.load()
    assert any(g["since"] == gr.ALWAYS for g in live.values())
    assert not any(g["since"][0].isdigit() and int(g["since"].split(".")[0]) > 0
                   for g in live.values()
                   if g["since"] != gr.ALWAYS), (
        "a since under the pre-0.1 scheme sorts above every real version")


def test_an_unknown_name_is_never_silently_exempt(tmp_path):
    root = _tree(tmp_path, {"G": ROW})
    assert gr.held("no-such-gate", "0.1.100", root) is True


# --- the classification itself -----------------------------------------------

def test_every_row_carries_a_family():
    missing = [n for n, g in gr.load().items() if not (g.get("family") or "").strip()]
    assert not missing, f"a verdict with no concept behind it: {missing}"


def test_the_families_are_the_classification_and_are_smaller_than_the_rows():
    """The point of the field: 85 rows that grew one at a time collapse to a
    readable number of concepts. If families ever approach rows one-to-one the
    field has stopped classifying anything."""
    fams = gr.families()
    rows = sum(len(v) for v in fams.values())
    assert rows == len(gr.load())
    assert len(fams) < rows / 2, (
        f"{len(fams)} families for {rows} rows — the classification is not "
        f"grouping")
