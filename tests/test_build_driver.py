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


def test_the_driver_passes_the_language_through(tmp_path):
    """The refusal lives in new_deck.py, which writes the declaration; a second
    copy here would be a rule with two owners."""
    out = _build("--deck", str(tmp_path / "d.html"), "--lang", "zh-Hans",
                 "--fast", "--pages", "2")
    assert out.returncode != 0
    assert "asked for" in (out.stdout + out.stderr)


def test_a_quoted_ask_reaches_the_document(tmp_path):
    deck = tmp_path / "d.html"
    _build("--deck", str(deck), "--fast", "--pages", "2",
           "--lang", "zh-Hans", "--lang-asked", "\u7528\u4e2d\u6587\u5199\u8fd9\u4efd\u62a5\u544a")
    raw = deck.read_text(encoding="utf-8")
    assert '<html lang="zh-Hans"' in raw
    assert "data-lang-ask-quote=" in raw


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


def test_the_log_survives_a_second_round(tmp_path):
    """A build is N rounds; the driver was throwing N-1 of them away.

    `--debug-log` restarted the log every round and carried only the C1-C8
    self-score, so every exit code, timing, digest and attached checker report
    from the earlier rounds was destroyed by the round that followed. Both
    agents of the 2026-08-25 validation round archived each round's log by hand
    to work around it, and this driver's own source records the author doing the
    same nine times on one build.
    """
    deck = tmp_path / "d.html"
    _build("--deck", str(deck), "--fast", "--pages", "2", "--debug-log")
    log = tmp_path / (deck.stem + ".debug.json")
    first = json.loads(log.read_text(encoding="utf-8"))
    assert first["steps"], "the first round recorded nothing"
    _build("--deck", str(deck), "--fast", "--pages", "2", "--debug-log")
    second = json.loads(log.read_text(encoding="utf-8"))
    assert second["rounds"] == 2
    assert len(second["steps"]) > len(first["steps"]), (
        "the second round replaced the first's record instead of continuing it")
    assert {s.get("round") for s in second["steps"]} == {1, 2}


def test_a_new_build_starts_a_new_record(tmp_path):
    """The counter-red: destroying the record must stay possible, and explicit.

    `--keep-log` used to mean "let init refuse", which killed the driver before
    a stage ran. The destructive act is the one that should need a flag.
    """
    deck = tmp_path / "d.html"
    _build("--deck", str(deck), "--fast", "--pages", "2", "--debug-log")
    out = _build("--deck", str(deck), "--fast", "--pages", "2", "--debug-log",
                 "--new-build")
    # The flag must EXIST: argparse exits 2 on an unknown one, and a test that
    # reads the first round's log afterwards would pass without noticing.
    assert "unrecognized arguments" not in (out.stdout + out.stderr)
    log = json.loads((tmp_path / (deck.stem + ".debug.json")).read_text(encoding="utf-8"))
    assert log["rounds"] == 1
    assert {s.get("round") for s in log["steps"]} == {1}
