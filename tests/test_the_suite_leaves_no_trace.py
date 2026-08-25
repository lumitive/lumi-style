"""The suite must not write into the store it is measuring.

`tests/test_fewer_round_trips.py` drives `build.py` through a helper that
passes no environment, so `LUMI_TRACES` was unset and every run of the suite
wrote a `source: build` trace of a two-page scaffold into the TRACKED store.
`preflight.py` runs the suite and `release.py` stages with `git add -A`, so
they reached commits: 0.1.604 committed four, and the store had been
collecting them across sixteen `skill_version`s before anyone looked.

**The cost is that the leak became the denominator.** 182 of the store's 199
build records are that one scaffold — `pages: 0`, entry path B, no recipe,
never closed — so `ledger.py` reported `4 of 251 build(s) record a reviewed
outline` about a corpus of seventeen real builds, where the honest reading is
four of seventeen, and `203 abandoned build(s)` about roughly twenty. Those
lines are read as findings about how this package is used. They were mostly
findings about pytest.

(What it does NOT touch, because an earlier draft of this docstring claimed it
did: `bar_replay.py` reads `evals/thresholds.json` and never opens the trace
store, and the shape distribution a bar would be drafted from is `n=2` either
way — the leaked scaffolds record no figures and no layouts at all.)
"""
import json
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
TRACKED = ROOT / "evals" / "traces"


def test_the_trace_store_is_redirected_for_every_test():
    """Autouse, suite-wide, and asserted rather than assumed.

    A per-file fixture would leave the next file that drives a build free to
    write into the store, which is exactly how this arrived: the leak was one
    helper in one file, and the defence belongs where any file inherits it.
    """
    redirected = os.environ.get("LUMI_TRACES")
    assert redirected, "LUMI_TRACES is unset: a driven build writes into evals/traces/"
    assert pathlib.Path(redirected).resolve() != TRACKED.resolve()


def test_opening_a_trace_from_the_suite_adds_nothing_to_the_tracked_store():
    """The OUTCOME, not the setting.

    The first version of this file asserted only that `LUMI_TRACES` pointed
    somewhere else, which is the mechanism rather than the effect — it would
    pass just as happily if `trace.py` stopped reading the variable. This one
    runs the real command the way a test would, inheriting whatever environment
    conftest has arranged, and counts the tracked directory on both sides.
    """
    before = sorted(p.name for p in TRACKED.glob("*.json"))
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "ops" / "trace.py"), "open",
         "--genre", "internal", "--geometry", "16x9",
         "--storyline", "market-analysis", "--entry-path", "B"],
        capture_output=True, text=True, cwd=ROOT)
    assert proc.returncode == 0, proc.stderr
    after = sorted(p.name for p in TRACKED.glob("*.json"))
    assert after == before, (
        "opening a trace from the suite wrote into the tracked store: "
        f"{sorted(set(after) - set(before))}")

    # And it did land somewhere — a redirect that silently dropped the record
    # would pass the assertion above for the wrong reason.
    store = pathlib.Path(os.environ["LUMI_TRACES"])
    written = [p for p in store.glob("*.json")
               if json.loads(p.read_text()).get("trace_id") in proc.stdout]
    assert written, f"no trace landed in the redirected store; stdout={proc.stdout!r}"
