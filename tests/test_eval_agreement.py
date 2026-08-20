"""The agreement study can now produce a row, and its silences say why.

The join it shipped with was disjoint by schema: the measurement cache is keyed
by filename, reader records by a corpus id that review_scores.py validates as
`^[A-Z]\\d{1,3}$` — a corpus id can never equal a filename, so study() returned
[] for every input the schema permits, and CI's --report exited 0 on empty by
design. The first tests here keep that failure reproducible: the same valid
inputs, joined without the corpus map, still yield nothing — and the map is now
the join, its absence stated rather than printed as an empty success.

The blind sheet is the other half: the hardcoded C1-C7 list here outlived the
rubric the moment C8 shipped, so a reader who filled it produced a record
review_scores.py rejects. --sheet now delegates to the rubric-derived source
and carries no dimension list of its own.
"""
import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "ops"))
sys.path.insert(0, str(ROOT / "scripts" / "lib"))

import corpus  # noqa: E402
import eval_agreement  # noqa: E402
import rubric_items  # noqa: E402


def _cache():
    """A measured cache the way measure_all writes one: keyed by FILENAME."""
    return {
        "deck.en.html": {
            "file": "/somewhere/deck.en.html",
            "genre": "training",
            "scores": [
                {"metric": "prose_only_share", "verdict": "ok", "value": 0.0,
                 "bar": 0.333, "direction": "ceiling",
                 "evidence": "calibrated", "unit": "share"},
                {"metric": "visual_share_median", "verdict": "no bar",
                 "detail": "no bar for this genre"},
            ],
        }
    }


def _record(**overrides):
    """A reader record that review_scores.py's schema 3 accepts."""
    rec = {
        "release": "0.1.495", "genre": "training", "corpus_id": "A1",
        "document": "A1", "outcome": "no-change",
        "self": {f"C{i}": None for i in range(1, 9)},
        "reader": {f"C{i}": 4 for i in range(1, 9)},
    }
    rec.update(overrides)
    return rec


def _scored():
    return {"A1": _record()["reader"]}


# --- the join -----------------------------------------------------------------

def test_the_disjoint_join_is_still_reproducible():
    """Red first: without the corpus map, a schema-valid record and a
    filename-keyed cache share no key, which is exactly the state the study
    shipped in — it had never produced a row."""
    result = eval_agreement.study(_cache(), _scored(), {})
    assert result["rows"] == []
    assert result["unjoinable"] == ["deck.en.html"], \
        "the unjoined filename must be named, not dropped"


def test_a_valid_record_joins_through_the_corpus_map():
    result = eval_agreement.study(_cache(), _scored(), {"deck.en.html": "A1"})
    (row,) = result["rows"]
    assert row["corpus_id"] == "A1"
    assert row["document"] == "deck.en.html"
    assert row["metric"] == "prose_only_share"
    assert row["agree"] is True, "ok verdict vs a reader 4 is agreement"


def test_dropped_verdicts_are_counted_not_silent():
    """'no bar', 'too few pages', 'not measured' carry no pass/miss to compare.
    They leave the study, but a study that silently thins its own input reads
    exactly like a clean one — so they are counted per metric."""
    result = eval_agreement.study(_cache(), _scored(), {"deck.en.html": "A1"})
    assert result["left_out"] == {"visual_share_median": {"no bar": 1}}


def test_read_scores_joins_on_corpus_id_and_falls_back_to_document(
        tmp_path, monkeypatch):
    store = {"reviews": [
        _record(),                                       # corpus_id A1
        _record(corpus_id=None, document="A2"),          # fallback: id-shaped
        _record(corpus_id=None, document="deck.en.html"),  # filename: refused
    ]}
    scores = tmp_path / "scores.json"
    scores.write_text(json.dumps(store), encoding="utf-8")
    monkeypatch.setattr(eval_agreement, "SCORES", scores)
    assert set(eval_agreement.read_scores()) == {"A1", "A2"}, \
        "a filename is not a join key; only the corpus id shape is admitted"


def _wire(tmp_path, monkeypatch, *, cache=True, corpus_map=True, scores=True):
    """Point the module's operator files into a temp tree."""
    c = tmp_path / "measured.local.json"
    if cache:
        c.write_text(json.dumps(_cache()), encoding="utf-8")
    monkeypatch.setattr(eval_agreement, "CACHE", c)
    m = tmp_path / "corpus.local.json"
    if corpus_map:
        m.write_text(json.dumps({"A1": "/somewhere/deck.en.html"}),
                     encoding="utf-8")
    monkeypatch.setattr(corpus, "LOCAL_CORPUS", m)
    s = tmp_path / "scores.json"
    if scores:
        s.write_text(json.dumps({"reviews": [_record()]}), encoding="utf-8")
    else:
        s.write_text(json.dumps({"reviews": []}), encoding="utf-8")
    monkeypatch.setattr(eval_agreement, "SCORES", s)


def test_the_full_study_prints_rows_and_the_left_out_note(
        tmp_path, monkeypatch, capsys):
    _wire(tmp_path, monkeypatch)
    assert eval_agreement.main([]) == 0
    out = capsys.readouterr().out
    assert "# Agreement" in out
    assert "left out of the study" in out
    assert "visual_share_median" in out


def test_an_absent_corpus_map_is_stated_not_an_empty_success(
        tmp_path, monkeypatch, capsys):
    _wire(tmp_path, monkeypatch, corpus_map=False)
    assert eval_agreement.main([]) == 1
    out = capsys.readouterr().out
    assert "could not join" in out
    assert "corpus.local.json is absent" in out


def test_report_mode_states_the_missing_join_and_exits_zero(
        tmp_path, monkeypatch, capsys):
    """CI runs --report; a join nobody can make is standing state there, not a
    failure — but the text must say which kind of empty this is."""
    _wire(tmp_path, monkeypatch, corpus_map=False)
    assert eval_agreement.main(["--report"]) == 0
    assert "could not join" in capsys.readouterr().out


def test_report_mode_still_exits_zero_when_nothing_is_scored(
        tmp_path, monkeypatch, capsys):
    _wire(tmp_path, monkeypatch, scores=False)
    assert eval_agreement.main(["--report"]) == 0
    assert "nothing can be compared" in capsys.readouterr().out


def test_report_mode_still_exits_zero_with_no_cache(
        tmp_path, monkeypatch, capsys):
    _wire(tmp_path, monkeypatch, cache=False)
    assert eval_agreement.main(["--report"]) == 0
    assert "no cached measurement" in capsys.readouterr().out


# --- the sheet ----------------------------------------------------------------

def test_the_sheet_comes_from_the_rubric_and_carries_every_dimension(
        tmp_path, monkeypatch, capsys):
    """The hardcoded list stopped at C7 while the rubric had grown C8; the
    sheet is now rendered from rubric_items, so whatever the rubric defines is
    what the sheet asks."""
    doc = tmp_path / "deck.en.html"
    doc.write_text("<html></html>", encoding="utf-8")
    _wire(tmp_path, monkeypatch, corpus_map=False)
    assert eval_agreement.main(["--sheet", str(doc)]) == 0
    out = capsys.readouterr().out
    for did, _title, _rows in rubric_items.items():
        assert f"### {did}" in out, f"the sheet is missing {did}"
    assert "C8" in out


def test_the_sheet_uses_the_corpus_map_ids_when_it_has_them(
        tmp_path, monkeypatch, capsys):
    doc = tmp_path / "deck.en.html"
    doc.write_text("<html></html>", encoding="utf-8")
    m = tmp_path / "corpus.local.json"
    m.write_text(json.dumps({"A7": str(doc)}), encoding="utf-8")
    monkeypatch.setattr(corpus, "LOCAL_CORPUS", m)
    assert eval_agreement.main(["--sheet", str(doc)]) == 0
    assert "A7" in capsys.readouterr().out


def test_the_sheet_with_nothing_to_score_points_at_its_source(
        tmp_path, monkeypatch, capsys):
    _wire(tmp_path, monkeypatch, corpus_map=False)
    assert eval_agreement.main(["--sheet"]) == 1
    assert "scoring_sheet.py" in capsys.readouterr().out


def test_no_dimension_list_survives_in_the_source():
    """The drift class itself: a second copy of the dimensions, anywhere in
    this file, is the defect regrowing. The rubric's titles live in
    rubric_items.py alone."""
    src = (ROOT / "scripts" / "ops" / "eval_agreement.py").read_text(
        encoding="utf-8")
    for leaked in ("governing message", "storyline integrity",
                   '("C1"', '("C7"', '("C8"'):
        assert leaked not in src, f"eval_agreement.py carries {leaked!r}"


# --- measure ------------------------------------------------------------------

def test_measure_with_nothing_resolvable_exits_nonzero_and_writes_no_cache(
        tmp_path, monkeypatch, capsys):
    cache = tmp_path / "measured.local.json"
    monkeypatch.setattr(eval_agreement, "CACHE", cache)
    monkeypatch.setattr(corpus, "LOCAL_CORPUS",
                        tmp_path / "corpus.local.json")
    missing = tmp_path / "never-built.html"
    assert eval_agreement.main(["--measure", str(missing)]) == 1
    out = capsys.readouterr().out
    assert "Nothing was measured" in out
    assert not cache.exists(), \
        "an empty cache with exit 0 is a check nobody ran reading like a " \
        "check that found nothing"


def test_measure_reports_how_many_of_how_many(tmp_path, monkeypatch, capsys):
    cache = tmp_path / "measured.local.json"
    monkeypatch.setattr(eval_agreement, "CACHE", cache)
    monkeypatch.setattr(eval_agreement, "ROOT", tmp_path)
    monkeypatch.setattr(eval_agreement, "measure_all",
                        lambda found: {p.name: {"file": str(p), "scores": []}
                                       for p in found})
    real = tmp_path / "deck.en.html"
    real.write_text("<html></html>", encoding="utf-8")
    gone = tmp_path / "gone.html"
    assert eval_agreement.main(["--measure", str(real), str(gone)]) == 0
    out = capsys.readouterr().out
    assert "measured 1 of 2" in out
    assert "not found, so not measured" in out and "gone.html" in out
    assert cache.exists()


def test_measure_keeps_the_old_cache_when_eval_corpus_returns_nothing(
        tmp_path, monkeypatch, capsys):
    cache = tmp_path / "measured.local.json"
    cache.write_text(json.dumps(_cache()), encoding="utf-8")
    monkeypatch.setattr(eval_agreement, "CACHE", cache)
    monkeypatch.setattr(eval_agreement, "measure_all", lambda found: {})
    real = tmp_path / "deck.en.html"
    real.write_text("<html></html>", encoding="utf-8")
    assert eval_agreement.main(["--measure", str(real)]) == 1
    assert "left as it was" in capsys.readouterr().out
    assert json.loads(cache.read_text(encoding="utf-8")) == _cache(), \
        "a failed run may not clobber a good cache with an empty one"


def test_without_report_an_unjoinable_study_is_loud(
        tmp_path, monkeypatch, capsys):
    """No joinable row without --report is an error, because a study nobody
    can run should be loud when someone runs it."""
    _wire(tmp_path, monkeypatch)
    empty = tmp_path / "corpus.local.json"
    empty.write_text(json.dumps({"A1": "/somewhere/other.html"}),
                     encoding="utf-8")
    assert eval_agreement.main([]) == 1
    out = capsys.readouterr().out
    assert "deck.en.html" in out and "no corpus id" in out


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
