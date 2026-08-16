"""A build gets a run number, so two builds of one version are distinguishable.

Before this, the second build of a version silently replaced the first and the
only way to tell two generations apart was the file timestamp — which is not
something a document carries.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "ops"))

import output_dir  # noqa: E402


def test_first_run_is_r1(tmp_path):
    p = output_dir.next_run_name("deck", "0.1.1", outdir=tmp_path)
    assert p.name == "deck.0.1.1.r1.en.html"


def test_the_number_advances_past_what_is_on_disk(tmp_path):
    (tmp_path / "deck.0.1.1.r1.en.html").write_text("x", encoding="utf-8")
    (tmp_path / "deck.0.1.1.r2.en.html").write_text("x", encoding="utf-8")
    assert output_dir.next_run_name("deck", "0.1.1", outdir=tmp_path).name \
        == "deck.0.1.1.r3.en.html"


def test_versions_number_independently(tmp_path):
    (tmp_path / "deck.0.1.1.r1.en.html").write_text("x", encoding="utf-8")
    assert output_dir.next_run_name("deck", "0.1.2", outdir=tmp_path).name \
        == "deck.0.1.2.r1.en.html"


def test_the_language_convention_survives_the_run_number():
    """The checkers read the language off a `*.en.*` filename; the run number
    sits before that suffix so it still does."""
    import re
    name = output_dir.next_run_name("deck", "0.1.1",
                                    outdir=pathlib.Path("/nonexistent")).name
    assert re.search(r"\.en\.", name)


def test_the_counter_is_the_directory_not_a_stored_number(tmp_path):
    """A stored counter drifts from the files it numbers the moment one is
    deleted. Removing r1 makes r1 the next name again, which is correct."""
    (tmp_path / "deck.0.1.1.r1.en.html").write_text("x", encoding="utf-8")
    assert output_dir.next_run_name("deck", "0.1.1", outdir=tmp_path).name.endswith("r2.en.html")
    (tmp_path / "deck.0.1.1.r1.en.html").unlink()
    assert output_dir.next_run_name("deck", "0.1.1", outdir=tmp_path).name.endswith("r1.en.html")
