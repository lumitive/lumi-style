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


def test_the_driver_has_no_language_flag_at_all(tmp_path):
    """0.1.587 gave it `--lang` and `--lang-asked` and refused the pair when
    they disagreed. A shipped build simply passed both. The flag is gone: every
    build is English, and another language is `scripts/ops/localize.py` over a
    finished English deck."""
    out = _build("--deck", str(tmp_path / "d.html"), "--lang", "zh-Hans")
    assert out.returncode != 0
    assert "unrecognized arguments" in (out.stdout + out.stderr)


def test_every_build_is_english(tmp_path):
    deck = tmp_path / "d.html"
    _build("--deck", str(deck), "--fast", "--pages", "2")
    raw = deck.read_text(encoding="utf-8")
    assert '<html lang="en"' in raw
    assert "data-lang-asked" not in raw


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
