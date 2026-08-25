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
# It is that the LEAK IS THE DENOMINATOR. Measured when this was written: 182
# of the store's 199 build records were the same two-page scaffold, so
# `ledger.py` reported "4 of 251 build(s) record a reviewed outline" over a
# store holding seventeen real builds. Those lines exist to be read as findings
# about how this package is used, and they were mostly findings about pytest.
#
# AT IMPORT, NOT IN A FIXTURE — and not autouse, which an earlier version of
# this comment claimed four lines above stating the opposite. conftest is
# imported before the test modules are, and a module that resolves the store at
# import — several do, because the path is a constant to them — would read the
# tracked one before any fixture could run. Suite-wide because the leak was one
# helper in one file, and fixing that helper leaves the next file free to
# repeat it.
#
# ASSIGNED, NOT `setdefault`. Yielding to an ambient value looks conservative
# and is the hole: `references/operating-rules.md` documents `LUMI_TRACES` as
# the operator's own redirect, so someone who exports it at a real corpus and
# then runs pytest gets the original defect pointed at a store that matters,
# with every test passing because the store merely is not `evals/traces/`. It
# also protected nothing — the tests that want a real store set it per
# subprocess through `env=`, which overrides this regardless.
import os  # noqa: E402
import sys as _sys  # noqa: E402
import tempfile  # noqa: E402

_TRACE_SCRATCH = tempfile.TemporaryDirectory(prefix="lumi-traces-")
_INHERITED = os.environ.get("LUMI_TRACES")
os.environ["LUMI_TRACES"] = _TRACE_SCRATCH.name
if _INHERITED and _INHERITED != _TRACE_SCRATCH.name:
    print(f"conftest: LUMI_TRACES was {_INHERITED!r}; the suite writes to a "
          f"scratch store instead, because it must not write into any store "
          f"whose numbers are read.", file=_sys.stderr)
