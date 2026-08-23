"""The recipe a trace fingerprints is what drove the build, not the plan.

`new_deck.py` passed the OUTLINE as `--recipe` and set `--entry-path` from
whether an outline existed at all. Two consequences, both measured on real
records at 0.1.591:

  * an outline carries no version stamp, so every such build lands in the
    ledger as `unknown` vintage — permanently, and `unknown` is not `current`;
  * the file that actually produced every page (`build_deck.py`, which DOES
    carry a VERSION) was fingerprinted by nothing.

Two replays of one frozen build script were recorded as path-A original builds
with identical outline hashes, which is the exact record `--recipe` exists to
make impossible.
"""
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TRACE = ROOT / "scripts" / "ops" / "trace.py"


def _run(args, **kw):
    return subprocess.run([sys.executable, str(TRACE), *args],
                          capture_output=True, text=True, cwd=ROOT, **kw)


def _open(tmp_path, *extra):
    env = {"LUMI_TRACES": str(tmp_path)}
    import os
    e = dict(os.environ, **env)
    r = subprocess.run([sys.executable, str(TRACE), "open", "--genre", "internal",
                        "--storyline", "market-analysis", "--entry-path", "B",
                        "--geometry", "16x9", *extra],
                       capture_output=True, text=True, cwd=ROOT, env=e)
    assert r.returncode == 0, r.stderr
    return r.stdout.strip(), e


def test_annotate_records_the_builder_after_open(tmp_path):
    """The build script does not exist when the trace opens, so it must be
    recordable afterwards — computed from the file, never typed."""
    tid, env = _open(tmp_path)
    builder = tmp_path / "build_deck.py"
    builder.write_text('VERSION = "0.1.591"\nprint("built")\n')
    r = subprocess.run([sys.executable, str(TRACE), "annotate", "--id", tid,
                        "--recipe", str(builder)],
                       capture_output=True, text=True, cwd=ROOT, env=env)
    assert r.returncode == 0, r.stderr
    rec = json.loads((tmp_path / f"{tid}.json").read_text())
    assert rec["recipe_hash"], "the builder was not fingerprinted"
    assert rec["recipe_version"] == "0.1.591", (
        "the version stamp the builder carries is the whole point of "
        f"fingerprinting it, got {rec['recipe_version']!r}")


def test_new_deck_does_not_guess_the_entry_path():
    """Presence of an outline is not what separates path A from path B."""
    src = (ROOT / "scripts" / "ops" / "new_deck.py").read_text()
    assert '"A" if outline else "B"' not in src, (
        "new_deck.py still infers the entry path from whether an outline was "
        "given; an outline is used on both paths")


def test_new_deck_does_not_call_the_outline_a_recipe():
    src = (ROOT / "scripts" / "ops" / "new_deck.py").read_text()
    assert 'argv += ["--recipe", str(outline)]' not in src, (
        "new_deck.py still fingerprints the outline as the recipe")


def test_the_driver_passes_the_entry_path_through():
    """`build.py` is the main path. Requiring the flag in `new_deck.py` without
    threading it through the driver would have turned "the entry path is
    declared" into "no build opens a trace at all"."""
    src = (ROOT / "scripts" / "ops" / "build.py").read_text()
    assert '"--entry-path"' in src, "the driver defines no --entry-path"
    assert 'argv_nd += ["--entry-path", a.entry_path]' in src, (
        "the driver accepts --entry-path and does not hand it to the scaffold")
