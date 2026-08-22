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
    tr, led = _fresh("trace"), _fresh("ledger")
    assert tr.TRACES == led.TRACES == tmp_path


def test_the_default_is_the_tracked_directory(tmp_path, monkeypatch):
    """A trace that is not kept is not a record."""
    monkeypatch.delenv("LUMI_TRACES", raising=False)
    monkeypatch.syspath_prepend(str(ROOT / "scripts" / "lib"))
    store = _fresh("trace_store")
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
