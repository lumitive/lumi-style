"""The prose gating claim, both shapes and both directions.

The guard this exercises found two live defects on its first run against the
real repository: the rubric's table omitted M4zh — the gate that fails a
Chinese deliverable, absent from the document a reader learns the metrics from
— and the sentence below it had called M2 a gate since the release that wrote
it, in a repository where M2 has never carried `(gates)`.
"""
import json
import subprocess

import check_repo

REG = {
    "M4_banned_hits": {"checker": "check_prose", "family": "banned-phrase",
                       "severity": "gate", "since": "always"},
    "M4zh_banned_hits": {"checker": "check_prose", "family": "banned-phrase",
                         "severity": "gate", "since": "always"},
    "M2_number_sourcing": {"checker": "check_prose", "family": "sourcing",
                           "severity": "graded", "since": "always"},
}
TABLE = ("| id | Metric | Target | Predicate |\n"
         "|---|---|---|---|\n"
         "| M2 | Number-sourcing rate | >=90% | share |\n"
         "| M4 | Banned phrases | =0 — **gates** | hits |\n"
         "| M4zh | Banned phrases (zh) | =0 — **gates** | hits |\n")
SENTENCE = "**M4 does gate**, because its predicate is decidable.\n"


def _repo(tmp_path, rubric, reg=None):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / "evals").mkdir()
    (tmp_path / "evals" / "gates.json").write_text(
        json.dumps({"schema": 1, "gates": reg if reg is not None else REG}))
    (tmp_path / "references").mkdir()
    (tmp_path / "references" / "eval-rubric.md").write_text(rubric)
    return tmp_path


def test_a_table_that_marks_the_gate_set_passes(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, TABLE + SENTENCE))
    assert check_repo.check_prose_gating_claims() == []


def test_a_table_missing_one_gate_fails_and_names_it(tmp_path, monkeypatch):
    """The measured defect: M4zh gates and had no row."""
    monkeypatch.setattr(check_repo, "ROOT", _repo(
        tmp_path, TABLE.replace("| M4zh | Banned phrases (zh) | =0 — **gates** | hits |\n", "")
        + SENTENCE))
    errors = check_repo.check_prose_gating_claims()
    assert len(errors) == 1
    assert "::table" in errors[0] and "missing: M4zh" in errors[0]


def test_a_table_marking_a_reported_metric_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _repo(
        tmp_path, TABLE.replace("| M2 | Number-sourcing rate | >=90% |",
                                "| M2 | Number-sourcing rate | >=90% — **gates** |")
        + SENTENCE))
    errors = check_repo.check_prose_gating_claims()
    assert len(errors) == 1
    assert "claimed and does not gate: M2" in errors[0]


def test_a_sentence_naming_a_subset_passes(tmp_path, monkeypatch):
    """A sentence arguing from an example is not enumerating, and holding it to
    the full set would be the guard being wrong about its material."""
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, TABLE + SENTENCE))
    assert check_repo.check_prose_gating_claims() == []


def test_a_sentence_calling_a_reported_metric_a_gate_fails(tmp_path, monkeypatch):
    """The other measured defect: "M2 and M6 do gate"."""
    monkeypatch.setattr(check_repo, "ROOT", _repo(
        tmp_path, TABLE + "**M2 and M4 do gate**, because they are decidable.\n"))
    errors = check_repo.check_prose_gating_claims()
    assert len(errors) == 1
    assert "::sentence" in errors[0] and "calls M2" in errors[0]


def test_a_deleted_sentence_fails_rather_than_passing_silently(tmp_path, monkeypatch):
    """Dropping the claim must not drop the watch — that is how the D-family
    sites rotted the first two times."""
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, TABLE))
    errors = check_repo.check_prose_gating_claims()
    assert len(errors) == 1
    assert "no longer matches its pattern" in errors[0]
