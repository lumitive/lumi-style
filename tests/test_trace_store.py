"""The writer and the readers resolve one trace store.

`trace.py` honoured `LUMI_TRACES` and `ledger.py` did not, so setting the
variable sent the writer somewhere the reader never looked. Neither side was
wrong on its own, and the ledger reported an EMPTY store rather than an error —
which is why no guard caught it and why this is a test rather than a guard.
"""
import importlib
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _fresh(name):
    sys.modules.pop(name, None)
    return importlib.import_module(name)


def test_writer_and_ledger_agree_under_the_override(tmp_path, monkeypatch):
    monkeypatch.setenv("LUMI_TRACES", str(tmp_path))
    monkeypatch.syspath_prepend(str(ROOT / "scripts" / "ops"))
    monkeypatch.syspath_prepend(str(ROOT / "scripts" / "lib"))
    tr, store = _fresh("trace"), _fresh("trace_store")
    # `ledger.TRACES` was the second half of this assertion until 0.1.620, when
    # the loader moved to `trace_store` and the constant became a name nothing
    # read. The claim is unchanged and is now made against the module that
    # actually resolves the store for every reader.
    assert tr.TRACES == store.traces_dir() == tmp_path
    led = _fresh("ledger")
    assert led.load() == [], (
        "the ledger reads the store the override names, and it is empty")


def test_the_default_is_the_tracked_directory_when_there_is_one(tmp_path, monkeypatch):
    """A trace that is not kept is not a record — so a checkout that HAS the
    tracked directory keeps writing into it, and no release moves an operator's
    file. A checkout that does not (an installed skill, whose projection
    carries no `evals/`) falls to the state directory instead; 0.1.571."""
    monkeypatch.delenv("LUMI_TRACES", raising=False)
    monkeypatch.setenv("LUMI_STATE", str(tmp_path / "state"))
    monkeypatch.syspath_prepend(str(ROOT / "scripts" / "lib"))
    store = _fresh("trace_store")
    assert store.traces_dir(tmp_path) == tmp_path / "state" / "traces"
    (tmp_path / "evals" / "traces").mkdir(parents=True)
    assert store.traces_dir(tmp_path) == tmp_path / "evals" / "traces"


def test_the_store_is_not_importable_as_the_stdlib_name(monkeypatch):
    """`import trace` under the canonical bootstrap gets the STANDARD LIBRARY's
    trace module, because the bootstrap appends. A reader reaching for the
    obvious name would fail in a way that has nothing to do with traces, which
    is why the shared resolver carries a distinct one."""
    out = subprocess.run(
        [sys.executable, "-c",
         f"import sys; sys.path.append({str(ROOT / 'scripts' / 'ops')!r}); "
         f"import trace; print(trace.__file__)"],
        capture_output=True, text=True, check=True).stdout
    assert "scripts/ops" not in out
