# scripts/ is deliberately not a package (the scripts are operator commands,
# not a library), so tests import them by bare name with every drawer on
# sys.path. UNLIKE the canonical bootstrap block (which APPENDS so stdlib
# and the caller's environment win), tests insert(0) on purpose: the suite
# must test THIS repo's modules even when site-packages carries a same-named
# package (`lock` is a real pypi name). The threat the append order defends
# against — PR-controlled trees — does not exist in the test environment.
import pathlib
import sys

_SCRIPTS = pathlib.Path(__file__).resolve().parent.parent / "scripts"
for _sub in ("", "lib", "render", "check", "build", "ops"):
    sys.path.insert(0, str(_SCRIPTS / _sub) if _sub else str(_SCRIPTS))


# THE SUITE MUST NOT WRITE INTO THE STORE IT IS MEASURING. `trace.py` resolves
# `LUMI_TRACES` first and falls back to this checkout's `evals/traces/`, so any
# test that drives `build.py` or `new_deck.py` without an environment of its own
# wrote a `source: build` trace of a throwaway scaffold into the TRACKED store.
# `preflight.py` runs the suite and `release.py` stages with `git add -A`, so
# they reached commits — 0.1.604 committed four, and the store had been
# collecting them across sixteen different `skill_version`s before anyone
# noticed.
#
# The cost is not disk, and it is not what the first draft of this comment said
# (`bar_replay.py` reads `evals/thresholds.json` and never opens the store).
# It is that the LEAK IS THE DENOMINATOR. 182 of the store's 199 build records
# are the same two-page scaffold — `pages: 0`, path B, no recipe, never closed —
# so `ledger.py` reported "4 of 251 build(s) record a reviewed outline" for a
# corpus of 17 real builds where the true figure is 4 of 17, and "203 abandoned
# build(s)" for about twenty. Those lines exist to be read as findings about
# how this package is used, and they were mostly findings about pytest.
#
# Autouse and suite-wide on purpose. The leak was one helper in one file, and a
# fix in that helper would leave the next file that drives a build free to do it
# again. A test that wants a real store still sets its own `LUMI_TRACES`, which
# several already do.
# AT IMPORT, NOT IN A FIXTURE. conftest is imported before the test modules
# are, and a module that resolves the store at import — several do, because the
# path is a constant to them — would otherwise read the tracked one and the
# redirect would arrive too late to mean anything.
import os  # noqa: E402
import tempfile  # noqa: E402

_TRACE_SCRATCH = tempfile.TemporaryDirectory(prefix="lumi-traces-")
os.environ.setdefault("LUMI_TRACES", _TRACE_SCRATCH.name)
