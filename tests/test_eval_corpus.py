"""The Evals runner, proven able to say each of the things it can say.

`score()` is a pure function over two dicts — the cheapest thing in the release
to test — and it is where the verdicts are decided. It shipped with no test at
all, and the first smoke run found it laundering an unmeasured threshold into a
clean exit.

The discipline is the repository's: every outcome demonstrated, not just the
good one, because a check only ever seen passing is FM-01.
"""
import json

import eval_corpus as ec

TABLE = {
    "min_content_pages": 8,
    "metrics": {
        "a_ceiling": {"direction": "ceiling", "unit": "u", "needs_corpus_size": True,
                      "genres": {"sales": {"value": 0.5, "evidence": "calibrated"}}},
        "a_floor": {"direction": "floor", "unit": "u", "needs_corpus_size": False,
                    "genres": {"sales": {"value": 2.0, "evidence": "provisional"},
                               "internal": {"value": None, "evidence": "declined",
                                            "why": "no accepted document"}}},
    },
}


def _measured(**kw):
    base = {"file": "x", "genre": "sales", "content_pages": 20,
            "a_ceiling": 0.1, "a_floor": 5.0}
    base.update(kw)
    return base


def test_a_ceiling_and_a_floor_run_the_right_way_round():
    # CLAUDE.md convention 4 is exactly this hazard, and anything that is not
    # the literal string "ceiling" silently becomes a floor.
    rows = {r["metric"]: r["verdict"] for r in ec.score(_measured(), TABLE)}
    assert rows == {"a_ceiling": "ok", "a_floor": "ok"}
    over = {r["metric"]: r["verdict"]
            for r in ec.score(_measured(a_ceiling=0.9, a_floor=1.0), TABLE)}
    assert over == {"a_ceiling": "MISS", "a_floor": "MISS"}


def test_a_value_at_the_bar_clears_it():
    rows = {r["metric"]: r["verdict"]
            for r in ec.score(_measured(a_ceiling=0.5, a_floor=2.0), TABLE)}
    assert rows == {"a_ceiling": "ok", "a_floor": "ok"}


def test_an_unmeasured_value_is_not_a_pass():
    rows = {r["metric"]: r["verdict"] for r in ec.score(_measured(a_ceiling=None), TABLE)}
    assert rows["a_ceiling"] == "not measured"


def test_the_render_state_reaches_the_row():
    # A crashed browser and a deliberate --no-render used to print the same
    # sentence, so a missing Chromium read as a choice.
    rows = {r["metric"]: r for r in ec.score(
        _measured(a_ceiling=None, render_state="inspect_layout exited 1"), TABLE)}
    assert "exited 1" in rows["a_ceiling"]["detail"]


def test_a_declined_bar_is_reported_as_such_with_its_reason():
    rows = {r["metric"]: r for r in ec.score(_measured(genre="internal"), TABLE)}
    assert rows["a_floor"]["verdict"] == "no bar"
    assert "no accepted document" in rows["a_floor"]["detail"]


def test_a_small_document_suppresses_only_the_metrics_that_declare_it():
    # The guard used to key on whether the metric's NAME contained
    # "per_content_page", so two ratios escaped it on a spelling.
    rows = {r["metric"]: r["verdict"]
            for r in ec.score(_measured(content_pages=2, a_ceiling=0.9), TABLE)}
    assert rows["a_ceiling"] == "too few pages"
    assert rows["a_floor"] == "ok", "a metric that opts out stays graded"


def test_genre_is_read_from_the_document_and_never_guessed():
    assert ec.genre_of('<body data-genre="training">') == "training"
    assert ec.genre_of('<body data-genre="webinar">') is None
    assert ec.genre_of("<body>") is None


def test_the_shipped_table_parses_and_every_metric_declares_its_direction():
    table = json.loads(ec.THRESHOLDS.read_text(encoding="utf-8"))
    for name, spec in table["metrics"].items():
        assert spec["direction"] in ("ceiling", "floor"), name
        assert "needs_corpus_size" in spec, name
        for genre, bar in spec["genres"].items():
            assert bar["evidence"] in table["evidence_levels"], (name, genre)


def test_a_document_that_cannot_be_scored_does_not_exit_zero(tmp_path, capsys):
    code = ec.main([str(tmp_path / "absent.en.html")])
    assert code == 1
    assert "does not exist" in capsys.readouterr().out


def test_a_document_with_no_genre_is_unmeasurable(tmp_path, capsys):
    doc = tmp_path / "d.en.html"
    doc.write_text("<html><body><section class='page'></section></body></html>",
                   encoding="utf-8")
    assert ec.main([str(doc), "--no-render"]) == 1
    assert "UNMEASURABLE" in capsys.readouterr().out


def test_a_missed_bar_alone_does_not_fail_the_run():
    # The bars REPORT (thresholds.json's status_note): a red-team pass cleared
    # all four with two mechanical rewrites, and two of them were refused as
    # gates in writing by the checkers they come from.
    rows = ec.score(_measured(a_ceiling=0.9), TABLE)
    assert any(r["verdict"] == "MISS" for r in rows)
