"""What an agent can be RUN AS, asked the way it is asked whether it is there.

`detect` answers presence. Nothing answered configuration, so every board this
package has published named an agent id — and an id is not a thing anybody can
run. Measured 2026-08-27: one of the twelve registered platforms can answer
read-only (`cursor-agent --list-models`, 23 ids), and the other eleven cannot,
for three different reasons that a table would otherwise print identically.

The three states are the point. `waived` is the registry's own reason, `asked`
is what the CLI returned, and `failed` is a declared probe that did not answer
HERE — which is neither of the other two.
"""
import subprocess

import run_conformance as rc


class _Ran:
    def __init__(self, code=0, out="", err=""):
        self.returncode, self.stdout, self.stderr = code, out, err


def _cli(monkeypatch, result, installed=True):
    monkeypatch.setattr(rc.shutil, "which",
                        lambda _n: "/bin/x" if installed else None)
    monkeypatch.setattr(rc.subprocess, "run", lambda *a, **k: result)


_ARGV = {"id": "cursor", "models": ["cursor-agent", "--list-models"]}
_REAL = ("Available models\n\nauto - Auto (default)\n"
         "cursor-grok-4.6-high - Cursor Grok 4.6\n"
         "cursor-grok-4.6-xhigh - Cursor Grok 4.6 Extra High\n")


def test_a_declared_probe_that_answers_returns_the_ids(monkeypatch):
    _cli(monkeypatch, _Ran(out=_REAL))
    state, detail = rc.vocabulary(_ARGV)
    assert state == "asked"
    assert detail == "auto, cursor-grok-4.6-high, cursor-grok-4.6-xhigh"


def test_the_heading_line_is_not_recorded_as_a_model_called_available(
        monkeypatch):
    """Written against the real output rather than an imagined one — convention
    15. `Available models` carries no ` - ` and would otherwise have become an
    id, and every reader of this vocabulary would have carried it forever."""
    _cli(monkeypatch, _Ran(out=_REAL))
    _state, detail = rc.vocabulary(_ARGV)
    assert "Available" not in detail


def test_no_probe_is_the_registry_s_own_reason_verbatim(monkeypatch):
    state, detail = rc.vocabulary(
        {"id": "hermes", "models": None,
         "models_waiver": "`hermes model` opens a picker."})
    assert state == "waived" and detail == "`hermes model` opens a picker."


def test_a_declared_probe_whose_binary_is_absent_is_waived_not_failed(
        monkeypatch):
    _cli(monkeypatch, _Ran(), installed=False)
    state, detail = rc.vocabulary(_ARGV)
    assert state == "waived" and "not installed here" in detail


# THE THREE WAYS IT CANNOT LOOK, each of which returned a clean-looking answer
# in some earlier instrument in this repository (FM-24). None may be silent and
# none may be reported as `waived`, because a waiver is a REASON and these are
# accidents.

def test_a_probe_that_exits_nonzero_is_failed_and_quotes_the_cli(monkeypatch):
    _cli(monkeypatch, _Ran(code=2, err="not logged in"))
    state, detail = rc.vocabulary(_ARGV)
    assert state == "failed" and "exited 2" in detail and "not logged in" in detail


def test_a_probe_that_raises_is_failed_and_names_the_exception(monkeypatch):
    monkeypatch.setattr(rc.shutil, "which", lambda _n: "/bin/x")

    def _boom(*_a, **_k):
        raise subprocess.TimeoutExpired("cursor-agent", 60)

    monkeypatch.setattr(rc.subprocess, "run", _boom)
    state, detail = rc.vocabulary(_ARGV)
    assert state == "failed" and "TimeoutExpired" in detail


def test_a_probe_that_answers_nothing_parseable_is_failed_not_an_empty_set(
        monkeypatch):
    """An empty vocabulary from an exit-0 probe is a PARSE failure. Reported as
    `asked` with nothing in it, it would say the CLI offers no models — the
    exact shape of every check in this repository that reported clean because it
    could not look."""
    _cli(monkeypatch, _Ran(out="Available models\n\n"))
    state, detail = rc.vocabulary(_ARGV)
    assert state == "failed" and "parse" in detail


def test_the_registry_declares_a_vocabulary_state_for_every_platform():
    """The guard in `check_repo` says the same thing; this says it from the
    consumer's side, so a platform added with neither field fails here too."""
    agents = rc.load_agents()
    for a in agents:
        assert a.get("models") or a.get("models_waiver"), (
            f"{a['id']} declares neither a models probe nor a reason for "
            f"having none")
