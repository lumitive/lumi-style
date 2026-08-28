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
import json
import subprocess

import agent_capability  # 0.1.637 — the probe lives here now
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
    state, detail = agent_capability.probe_models(_ARGV)
    assert state == "asked"
    assert detail == "auto, cursor-grok-4.6-high, cursor-grok-4.6-xhigh"


def test_the_heading_line_is_not_recorded_as_a_model_called_available(
        monkeypatch):
    """Written against the real output rather than an imagined one — convention
    15. `Available models` carries no ` - ` and would otherwise have become an
    id, and every reader of this vocabulary would have carried it forever."""
    _cli(monkeypatch, _Ran(out=_REAL))
    _state, detail = agent_capability.probe_models(_ARGV)
    assert "Available" not in detail


def test_no_probe_is_the_registry_s_own_reason_verbatim(monkeypatch):
    state, detail = agent_capability.probe_models(
        {"id": "hermes", "models": None,
         "models_waiver": "`hermes model` opens a picker."})
    assert state == "waived" and detail == "`hermes model` opens a picker."


def test_a_declared_probe_whose_binary_is_absent_is_its_own_state(monkeypatch):
    """Not `waived`, which is what it returned until a review read the
    docstring against the code. A waiver is a REASON about the platform; a
    missing binary is a fact about this machine that one install changes.
    `detect()` had kept the two apart since it was written."""
    _cli(monkeypatch, _Ran(), installed=False)
    state, detail = agent_capability.probe_models(_ARGV)
    assert state == "absent" and "one install away" in detail


# THE WAYS IT CANNOT LOOK, each of which returned a clean-looking answer
# in some earlier instrument in this repository (FM-24). None may be silent and
# none may be reported as `waived`, because a waiver is a REASON and these are
# accidents.

def test_a_probe_that_exits_nonzero_is_failed_and_quotes_the_cli(monkeypatch):
    _cli(monkeypatch, _Ran(code=2, err="not logged in"))
    state, detail = agent_capability.probe_models(_ARGV)
    assert state == "failed" and "exited 2" in detail and "not logged in" in detail


def test_a_probe_that_raises_is_failed_and_names_the_exception(monkeypatch):
    monkeypatch.setattr(rc.shutil, "which", lambda _n: "/bin/x")

    def _boom(*_a, **_k):
        raise subprocess.TimeoutExpired("cursor-agent", 60)

    monkeypatch.setattr(rc.subprocess, "run", _boom)
    state, detail = agent_capability.probe_models(_ARGV)
    assert state == "failed" and "TimeoutExpired" in detail


def test_a_probe_that_answers_nothing_parseable_is_failed_not_an_empty_set(
        monkeypatch):
    """An empty vocabulary from an exit-0 probe is a PARSE failure. Reported as
    `asked` with nothing in it, it would say the CLI offers no models — the
    exact shape of every check in this repository that reported clean because it
    could not look."""
    _cli(monkeypatch, _Ran(out="Available models\n\n"))
    state, detail = agent_capability.probe_models(_ARGV)
    assert state == "failed" and "parse" in detail


def test_the_registry_declares_a_vocabulary_state_for_every_platform():
    """The guard in `check_repo` says the same thing; this says it from the
    consumer's side, so a platform added with neither field fails here too."""
    agents = rc.load_agents()
    for a in agents:
        assert a.get("models") or a.get("models_waiver"), (
            f"{a['id']} declares neither a models probe nor a reason for "
            f"having none")


# GAP-042: the `vocabulary-changed` trigger was declared and nothing stored a
# vocabulary to compare against — `detect --models` printed the live list and
# dropped it, so the register described a comparison no code could make.

def _detect_tree(tmp_path, monkeypatch, ids, prior=None):
    (tmp_path / "conformance").mkdir(parents=True, exist_ok=True)
    if prior is not None:
        (tmp_path / "conformance" / "vocabularies.json").write_text(
            json.dumps(prior), encoding="utf-8")
    monkeypatch.setattr(rc, "ROOT", tmp_path)
    monkeypatch.setattr(rc, "load_agents", lambda: [
        {"id": "faker", "name": "Faker", "capability": "full",
         "probe": ["true"], "models": ["true"]}])
    monkeypatch.setattr(rc, "load_tasks", lambda: [])
    monkeypatch.setattr(rc, "detect", lambda a: (True, "fake 1.0"))
    monkeypatch.setattr(rc.agent_capability, "probe_models", lambda a: ("asked", ", ".join(ids)))
    return tmp_path / "conformance" / "vocabularies.json"


def test_an_answered_vocabulary_is_recorded(tmp_path, monkeypatch):
    out = _detect_tree(tmp_path, monkeypatch, ["a-1", "b-2"])
    rc.main(["detect", "--models", "--record"])
    doc = json.loads(out.read_text(encoding="utf-8"))
    assert doc["faker"]["ids"] == ["a-1", "b-2"]
    assert doc["faker"]["cli_version"] == "fake 1.0"


def test_a_changed_vocabulary_names_what_moved(tmp_path, monkeypatch, capsys):
    _detect_tree(tmp_path, monkeypatch, ["a-1", "c-3"],
                 prior={"faker": {"ids": ["a-1", "b-2"]}})
    rc.main(["detect", "--models", "--record"])
    printed = capsys.readouterr().out
    assert "CHANGED faker" in printed
    assert "b-2" in printed and "c-3" in printed


def test_an_unchanged_vocabulary_says_nothing(tmp_path, monkeypatch, capsys):
    _detect_tree(tmp_path, monkeypatch, ["a-1"], prior={"faker": {"ids": ["a-1"]}})
    rc.main(["detect", "--models", "--record"])
    assert "CHANGED" not in capsys.readouterr().out


def test_a_waived_agent_records_no_empty_vocabulary(tmp_path, monkeypatch):
    """A waiver and a failed probe are not vocabularies. Recording them as
    empty sets would make "this CLI offers nothing" and "we could not ask" the
    same row — which is the distinction `vocabulary()` has four states for."""
    out = _detect_tree(tmp_path, monkeypatch, [])
    monkeypatch.setattr(rc.agent_capability, "probe_models", lambda a: ("waived", "no CLI to ask"))
    rc.main(["detect", "--models", "--record"])
    assert json.loads(out.read_text(encoding="utf-8")) == {}


def test_record_without_models_is_refused(tmp_path, monkeypatch, capsys):
    """There is nothing to record until the probes have been asked, and
    writing an empty file would look like a measurement."""
    _detect_tree(tmp_path, monkeypatch, ["a-1"])
    assert rc.main(["detect", "--record"]) == 1
    assert "--record needs --models" in capsys.readouterr().out
