"""`scripts/ops/build.py` proven able to pass AND to refuse.

The driver exists because a 2026-08 build spent 389 terminal commands on a
ten-page deck — one API round trip each — with no script anywhere in the package
that ran scaffold -> fill -> embed -> check. Its value is entirely in what it
does in ONE process, so the tests are about the stages happening and about the
two refusals that must not be negotiable.
"""
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
BUILD = ROOT / "scripts/ops/build.py"


def _build(*args):
    return subprocess.run([sys.executable, str(BUILD), *args],
                          capture_output=True, text=True)


def test_a_non_english_language_without_an_ask_is_refused(tmp_path):
    """The refusal is here rather than three stages later because the fix is a
    question for the user, not an edit to the document (FM-18)."""
    out = _build("--deck", str(tmp_path / "d.html"), "--lang", "zh-Hans")
    assert out.returncode == 1, out.stdout + out.stderr
    assert "never inferred" in (out.stdout + out.stderr)
    assert not (tmp_path / "d.html").exists(), "it refused after scaffolding"


def test_a_recorded_ask_is_accepted_and_lands_on_the_document(tmp_path):
    deck = tmp_path / "d.html"
    out = _build("--deck", str(deck), "--lang", "zh-Hans", "--lang-asked",
                 "--fast", "--pages", "2")
    assert deck.is_file(), out.stdout + out.stderr
    raw = deck.read_text(encoding="utf-8")
    assert '<html lang="zh-Hans"' in raw
    assert 'data-lang-asked="zh-Hans"' in raw


def test_the_loop_and_the_delivery_round_are_not_the_same_run(tmp_path):
    out = _build("--deck", str(tmp_path / "d.html"), "--fast", "--deliver")
    assert out.returncode == 1
    assert "pick one" in (out.stdout + out.stderr)


def test_a_failing_fill_script_stops_before_the_checks(tmp_path):
    """Otherwise the gate stack measures the scaffold and reports on a document
    the author never produced."""
    script = tmp_path / "fill.py"
    script.write_text("import sys; sys.exit(3)\n", encoding="utf-8")
    out = _build("--deck", str(tmp_path / "d.html"), "--script", str(script),
                 "--fast", "--pages", "2")
    assert out.returncode == 1
    assert "measuring the scaffold" in (out.stdout + out.stderr)
    assert "── check" not in out.stdout, "the checks ran anyway"


def test_the_fill_script_receives_the_deck_path(tmp_path):
    deck = tmp_path / "d.html"
    seen = tmp_path / "seen.txt"
    script = tmp_path / "fill.py"
    script.write_text(
        f"import sys, pathlib; pathlib.Path({str(seen)!r}).write_text(sys.argv[1])\n",
        encoding="utf-8")
    _build("--deck", str(deck), "--script", str(script), "--fast", "--pages", "2")
    assert seen.read_text().strip() == str(deck)


def test_debug_mode_costs_no_extra_commands(tmp_path):
    """The log is written as a side effect of running, not by wrapping every
    command in `debug_log.py run` from the outside — which is one API round trip
    per command, and was 16 of them on the build this script was written from."""
    deck = tmp_path / "d.html"
    _build("--deck", str(deck), "--fast", "--pages", "2", "--debug-log")
    log = tmp_path / "d.debug.json"
    assert log.is_file()
    entry = json.loads(log.read_text(encoding="utf-8"))
    labels = [s["label"] for s in entry["steps"]]
    assert "scaffold" in labels and "embed shapes" in labels and "check" in labels
    assert all(s["source"] == "run" for s in entry["steps"]), \
        "a self-reported second is not evidence"
