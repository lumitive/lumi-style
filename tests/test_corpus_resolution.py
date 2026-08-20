"""A scored document resolves to a file or to an archived record (OR-10).

The two documents carrying the first C1–C8 scores were deleted within a week
of being scored; nothing said so until the audit read the corpus file. This is
the check that says it, and the reader that lets an entry record the loss.
"""
import json

import corpus
import review_scores


def _store(*ids):
    return {"dimensions": [f"C{i}" for i in range(1, 9)],
            "reviews": [{"release": "0.1.508", "genre": "sales", "corpus_id": i,
                         "self": {}, "reader": {}, "outcome": "no-change"} for i in ids]}


def _local(tmp_path, monkeypatch, mapping):
    f = tmp_path / "corpus.local.json"
    f.write_text(json.dumps(mapping), encoding="utf-8")
    monkeypatch.setattr(corpus, "LOCAL_CORPUS", f)
    return f


def test_absent_corpus_file_is_not_attempted_never_ok(tmp_path, monkeypatch):
    monkeypatch.setattr(corpus, "LOCAL_CORPUS", tmp_path / "absent.json")
    assert review_scores.corpus_resolution(_store("D15")) == ([], "not attempted")


def test_a_scored_id_whose_file_is_gone_and_unarchived_fails(tmp_path, monkeypatch):
    _local(tmp_path, monkeypatch, {"D15": str(tmp_path / "gone.html")})
    errors, status = review_scores.corpus_resolution(_store("D15"))
    assert status == "failed" and "OR-10" in errors[0]


def test_an_archived_loss_is_a_fact_not_a_failure(tmp_path, monkeypatch):
    _local(tmp_path, monkeypatch, {"D15": {"path": str(tmp_path / "gone.html"),
                                            "archived": {"sha256": None, "pages": None,
                                                         "removed_before": "2026-08-20"}}})
    assert review_scores.corpus_resolution(_store("D15")) == ([], "ok")


def test_an_archive_naming_neither_sha_nor_date_fails(tmp_path, monkeypatch):
    _local(tmp_path, monkeypatch, {"D15": {"path": str(tmp_path / "gone.html"),
                                            "archived": {"pages": 12}}})
    errors, _ = review_scores.corpus_resolution(_store("D15"))
    assert errors and "neither a sha256 nor a removed_before" in errors[0]


def test_a_file_on_disk_passes_and_an_unregistered_id_fails(tmp_path, monkeypatch):
    here = tmp_path / "here.html"
    here.write_text("<html></html>", encoding="utf-8")
    _local(tmp_path, monkeypatch, {"D18": str(here)})
    assert review_scores.corpus_resolution(_store("D18")) == ([], "ok")
    errors, _ = review_scores.corpus_resolution(_store("D99"))
    assert errors and "does not register" in errors[0]


def test_corpus_paths_skips_archived_entries(tmp_path, monkeypatch):
    _local(tmp_path, monkeypatch, {"A1": str(tmp_path / "a.html"),
                                   "D15": {"archived": {"removed_before": "2026-08-20"}}})
    assert list(corpus.paths()) == ["A1"]
