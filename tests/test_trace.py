"""The trace schema is closed, and the tool refuses to write an illegal record.

The point of these tests is not that the happy path works. It is that the three
disciplines the design record names — machine-written verdicts, a trace opened
before the build rather than after, and no free text — are properties of the
code rather than of whoever runs it.
"""
import json
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
TRACE_PY = ROOT / "scripts" / "ops" / "trace.py"
sys.path.insert(0, str(ROOT / "scripts" / "lib"))

import trace_schema as trace  # noqa: E402 — after the path insert, deliberately


def _legal():
    rec = dict.fromkeys(trace.FIELDS)
    rec.update(trace_id="t-0123456789ab", opened_at="2026-08-16T00:00:00+00:00",
               closed_at=None, source="build", skill_version="0.1.462",
               genre="sales", storyline="market-analysis", entry_path="A",
               outline_reviewed=False, titles_changed_after_approval=0,
               geometry="16x9", pages=0, content_pages=0, phase_seconds={},
               gates={}, graded={}, thresholds={}, principle_yields=[],
               refused_to_emit=None)
    return rec


def test_legal_record_validates():
    assert trace.validate(_legal()) == []


def test_free_text_field_is_rejected():
    """Red line 9 held by the schema: a trace carries no prose at all."""
    rec = _legal()
    rec["note"] = "the client asked for this in a hurry"
    assert any("schema is closed" in e for e in trace.validate(rec))


def test_refusal_carries_clauses_and_stage_and_nothing_else():
    rec = _legal()
    rec["refused_to_emit"] = {"clauses": ["P-1", "P-5"], "stage": "checks"}
    assert trace.validate(rec) == []
    rec["refused_to_emit"] = {"clauses": ["P-1"], "stage": "checks",
                              "reason": "the palette fought the handling banner"}
    assert any("nothing else" in e for e in trace.validate(rec))


def test_yield_entry_must_name_real_clauses_and_a_known_stage():
    rec = _legal()
    rec["principle_yields"] = [{"yielded": "P-1", "for": "P-2", "stage": "build"}]
    assert trace.validate(rec) == []
    rec["principle_yields"] = [{"yielded": "brand", "for": "P-2", "stage": "build"}]
    assert any("non-clause" in e for e in trace.validate(rec))
    rec["principle_yields"] = [{"yielded": "P-1", "for": "P-2", "stage": "polish"}]
    assert any("unknown stage" in e for e in trace.validate(rec))


def test_phase_seconds_vocabulary_is_closed():
    rec = _legal()
    rec["phase_seconds"] = {"build": 100, "polish": 20}
    assert any("phase_seconds" in e for e in trace.validate(rec))


def test_genre_outside_the_vocabulary_is_rejected():
    rec = _legal()
    rec["genre"] = "pitch"
    assert any("outside the vocabulary" in e for e in trace.validate(rec))


def test_there_is_no_flag_for_supplying_a_verdict():
    """Verdicts are transcribed from the checkers; the CLI offers no way in.

    check_evidence.py's schema has no verdict field for the same reason: this
    repository once reported all gates passing having run eight of seventeen.
    """
    helptext = subprocess.run([sys.executable, str(TRACE_PY), "close", "--help"],
                              capture_output=True, text=True).stdout
    for forbidden in ("--gate", "--verdict", "--pass", "--result"):
        assert forbidden not in helptext


def test_open_then_close_round_trip(tmp_path, monkeypatch):
    opened = subprocess.run(
        [sys.executable, str(TRACE_PY), "open", "--genre", "sales",
         "--storyline", "market-analysis", "--entry-path", "A"],
        capture_output=True, text=True, cwd=ROOT)
    assert opened.returncode == 0
    tid = opened.stdout.strip()
    stored = ROOT / "evals" / "traces" / f"{tid}.json"
    try:
        rec = json.loads(stored.read_text(encoding="utf-8"))
        assert rec["closed_at"] is None, "an open trace has no closing time — an "\
            "unclosed record is how an abandoned build stays visible"
        assert trace.validate(rec) == []
    finally:
        stored.unlink(missing_ok=True)


# A checker that could not speak must not be recorded as a checker with nothing
# to say. `_checker_json` discarded the return code and returned None on a parse
# error, and `close` skipped a falsy report — so `[]` (an honest empty report)
# and a crash were the same value. One broken checker then left a trace whose
# nine design gates were simply absent, and absence reads as "fine" to every
# consumer, including the ledger built to notice a broken instrument.

import importlib.util  # noqa: E402 — the module name collides with stdlib trace

_spec = importlib.util.spec_from_file_location("lumi_trace", TRACE_PY)
assert _spec is not None and _spec.loader is not None, TRACE_PY
_trace_tool = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_trace_tool)


def test_a_checker_that_emits_prose_before_its_json_is_recorded_as_silent(tmp_path):
    """The real trigger: check_design prints its blind-gate warning with a bare
    print() that --json does not suppress, so a deck built with div.page emits
    prose in front of the JSON. The checker is doing its job; the transcriber
    used to throw the signal away."""
    src = (ROOT / "fixtures" / "deck-pass.en.html").read_text(encoding="utf-8")
    doc = tmp_path / "divpage.html"
    doc.write_text(src.replace('<section class="page', '<div class="page')
                      .replace("</section>", "</div>"), encoding="utf-8")
    parsed, spoke = _trace_tool._checker_json("check_design.py", doc)
    assert spoke is False
    assert parsed is None


def test_a_healthy_deliverable_is_recorded_as_having_spoken():
    parsed, spoke = _trace_tool._checker_json(
        "check_design.py", ROOT / "fixtures" / "deck-pass.en.html")
    assert spoke is True
    assert parsed


def test_a_silent_checker_leaves_a_not_measured_marker(tmp_path):
    """End to end: open, close against a document one checker cannot read, and
    assert the trace SAYS the design half did not run."""
    env = {**os.environ, "LUMI_TRACES": str(tmp_path)}
    src = (ROOT / "fixtures" / "deck-pass.en.html").read_text(encoding="utf-8")
    doc = tmp_path / "divpage.html"
    doc.write_text(src.replace('<section class="page', '<div class="page')
                      .replace("</section>", "</div>"), encoding="utf-8")
    tid = subprocess.run(
        [sys.executable, str(TRACE_PY), "open", "--genre", "internal",
         "--storyline", "proposal", "--entry-path", "B", "--source", "build"],
        capture_output=True, text=True, env=env, cwd=ROOT).stdout.strip()
    try:
        subprocess.run([sys.executable, str(TRACE_PY), "close", "--id", tid,
                        "--deliverable", str(doc)],
                       capture_output=True, text=True, env=env, cwd=ROOT, check=True)
        rec = json.loads((ROOT / "evals" / "traces" / f"{tid}.json")
                         .read_text(encoding="utf-8"))
        assert rec["thresholds"].get("_checker_design") == "not_measured"
        assert rec["gates"], "the prose half still ran and must still be recorded"
    finally:
        (ROOT / "evals" / "traces" / f"{tid}.json").unlink(missing_ok=True)


# A trace that contradicts its own deliverable is worse than no trace. Until
# 0.1.499 the word `geometry` named three unrelated vocabularies — the body's
# composition (landscape/portrait), the trace's stage (16x9/a4/laptop) and
# inspect_layout's viewport matrix — and nothing connected any pair.

def _open(tmp_path, geometry):
    return subprocess.run(
        [sys.executable, str(TRACE_PY), "open", "--genre", "internal",
         "--storyline", "proposal", "--entry-path", "B", "--source", "build",
         "--geometry", geometry],
        capture_output=True, text=True, cwd=ROOT, check=True).stdout.strip()


def _close(tid, doc):
    return subprocess.run(
        [sys.executable, str(TRACE_PY), "close", "--id", tid,
         "--deliverable", str(doc)], capture_output=True, text=True, cwd=ROOT)


def test_a_trace_whose_stage_contradicts_the_document_is_refused(tmp_path):
    tid = _open(tmp_path, "a4")
    try:
        p = _close(tid, ROOT / "fixtures" / "deck-pass.en.html")
        assert p.returncode != 0
        assert "landscape" in p.stderr and "a4" in p.stderr
    finally:
        (ROOT / "evals" / "traces" / f"{tid}.json").unlink(missing_ok=True)


def test_a_trace_whose_stage_agrees_closes(tmp_path):
    tid = _open(tmp_path, "16x9")
    try:
        p = _close(tid, ROOT / "fixtures" / "deck-pass.en.html")
        assert p.returncode == 0, p.stderr
    finally:
        (ROOT / "evals" / "traces" / f"{tid}.json").unlink(missing_ok=True)


def test_the_trace_vocabularies_are_the_registry_s_own_objects():
    """Not equal by luck — the same object. `genre` was a sixth literal copy
    that no guard covered, so a new genre would have been the only one that
    could not be traced."""
    sys.path.insert(0, str(ROOT / "scripts" / "lib"))
    import deliverable_registry as reg
    import trace_schema
    assert trace_schema.ENUMS["genre"] is reg.GENRES
    assert trace_schema.ENUMS["storyline"] is reg.STORYLINES
    assert set(reg.STAGE_OF.values()) <= set(trace_schema.ENUMS["geometry"])


# The recipe fingerprint: what a path-B build was actually driven by, and what
# version that thing was written against. A trace's skill_version is read from
# SKILL.md at open, so it always equals HEAD and can never be stale — which is
# why a replay of a frozen recipe used to be indistinguishable from a build
# made to the current rules.

def _ledger_states(tmp_path):
    sys.path.insert(0, str(ROOT / "scripts" / "ops"))
    import importlib.util as _iu
    spec = _iu.spec_from_file_location("lumi_ledger", ROOT / "scripts" / "ops" / "ledger.py")
    assert spec is not None and spec.loader is not None
    mod = _iu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _open_with(recipe=None, geometry="16x9"):
    cmd = [sys.executable, str(TRACE_PY), "open", "--genre", "internal",
           "--storyline", "proposal", "--entry-path", "B", "--source", "build",
           "--geometry", geometry]
    if recipe is not None:
        cmd += ["--recipe", str(recipe)]
    p = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    return p


def test_a_recipe_is_fingerprinted_and_its_own_version_is_read(tmp_path):
    r = tmp_path / "assemble.py"
    r.write_text("# built with lumi-style 0.1.457\nprint('x')\n")
    tid = _open_with(r).stdout.strip()
    try:
        rec = json.loads((ROOT / "evals" / "traces" / f"{tid}.json").read_text())
        assert rec["recipe_hash"] and len(rec["recipe_hash"]) == 12
        assert rec["recipe_version"] == "0.1.457"
        assert rec["skill_version"] != "0.1.457", (
            "the trace's own version is HEAD; that is the whole reason the "
            "recipe needs a separate one")
    finally:
        (ROOT / "evals" / "traces" / f"{tid}.json").unlink(missing_ok=True)


def test_an_unstamped_recipe_reads_unknown_and_not_current(tmp_path):
    """A recipe that never said which rules it followed has not told us it
    followed them. The first real recipe measured was exactly this case."""
    r = tmp_path / "assemble.py"
    r.write_text("print('no stamp anywhere')\n")
    tid = _open_with(r).stdout.strip()
    try:
        rec = json.loads((ROOT / "evals" / "traces" / f"{tid}.json").read_text())
        assert rec["recipe_hash"] and rec["recipe_version"] is None
        ledger = _ledger_states(tmp_path)
        state = ledger.ledger_recipes([rec])[0]["state"]
        assert state == "unknown"
    finally:
        (ROOT / "evals" / "traces" / f"{tid}.json").unlink(missing_ok=True)


def test_the_ledger_tells_the_four_states_apart(tmp_path):
    ledger = _ledger_states(tmp_path)
    rows = ledger.ledger_recipes([
        {"trace_id": "t-000000000001", "entry_path": "B", "skill_version": "0.1.499",
         "recipe_hash": "abc", "recipe_version": "0.1.457"},
        {"trace_id": "t-000000000002", "entry_path": "B", "skill_version": "0.1.499",
         "recipe_hash": "abc", "recipe_version": None},
        {"trace_id": "t-000000000003", "entry_path": "B", "skill_version": "0.1.499",
         "recipe_hash": "abc", "recipe_version": "0.1.499"},
        {"trace_id": "t-000000000004", "entry_path": "A", "skill_version": "0.1.499",
         "recipe_hash": None, "recipe_version": None},
    ])
    assert [r["state"] for r in rows] == ["stale", "unknown", "current", "none"]


def test_a_recipe_path_that_does_not_exist_is_refused(tmp_path):
    p = _open_with(tmp_path / "gone.py")
    assert p.returncode != 0
    assert "not a file" in p.stderr


# Token counts are machine-written too. `close` used to take
# `--input-tokens N --output-tokens N` — numbers typed by the agent being
# measured, which is the exact shape `check_evidence.py` was built to end.
# A typed token count is a typed verdict about the bill, so `close` now reads
# the API's own usage dump via --usage and the typed flags are gone.

def _close_with(tid, doc, *extra):
    return subprocess.run(
        [sys.executable, str(TRACE_PY), "close", "--id", tid,
         "--deliverable", str(doc), *extra],
        capture_output=True, text=True, cwd=ROOT)


def test_close_reads_the_tokens_from_a_machine_emitted_usage_file(tmp_path):
    """Happy path, end to end: the stored trace carries the dump's integers,
    and the dump's extra keys (an API reports more than two numbers) are
    tolerated rather than refused."""
    usage = tmp_path / "usage.json"
    usage.write_text(json.dumps({"input_tokens": 41000, "output_tokens": 9000,
                                 "service_tier": "standard",
                                 "cache_read_input_tokens": 12000}),
                     encoding="utf-8")
    tid = _open(tmp_path, "16x9")
    stored = ROOT / "evals" / "traces" / f"{tid}.json"
    try:
        p = _close_with(tid, ROOT / "fixtures" / "deck-pass.en.html",
                        "--usage", str(usage))
        assert p.returncode == 0, p.stderr
        rec = json.loads(stored.read_text(encoding="utf-8"))
        assert rec["input_tokens"] == 41000
        assert rec["output_tokens"] == 9000
    finally:
        stored.unlink(missing_ok=True)


def test_a_usage_file_that_is_not_json_is_refused_not_crashed_on(tmp_path):
    usage = tmp_path / "usage.json"
    usage.write_text("not json {", encoding="utf-8")
    tid = _open(tmp_path, "16x9")
    stored = ROOT / "evals" / "traces" / f"{tid}.json"
    try:
        p = _close_with(tid, ROOT / "fixtures" / "deck-pass.en.html",
                        "--usage", str(usage))
        assert p.returncode != 0
        assert "Traceback" not in p.stderr, "a refusal, not a crash"
        assert "not JSON" in p.stderr, "the message names what is wrong"
        rec = json.loads(stored.read_text(encoding="utf-8"))
        assert rec["closed_at"] is None, "a refused close leaves the trace open"
    finally:
        stored.unlink(missing_ok=True)


def test_a_usage_file_missing_a_token_key_is_refused(tmp_path):
    """The defect this test exists to catch: a permissive reader that stores
    None for a key the dump never had, closing a trace that quietly says
    nothing where the bill should be."""
    usage = tmp_path / "usage.json"
    usage.write_text(json.dumps({"input_tokens": 41000}), encoding="utf-8")
    tid = _open(tmp_path, "16x9")
    stored = ROOT / "evals" / "traces" / f"{tid}.json"
    try:
        p = _close_with(tid, ROOT / "fixtures" / "deck-pass.en.html",
                        "--usage", str(usage))
        assert p.returncode != 0
        assert "output_tokens" in p.stderr, "the message names the missing key"
        rec = json.loads(stored.read_text(encoding="utf-8"))
        assert rec["closed_at"] is None
    finally:
        stored.unlink(missing_ok=True)


def test_a_usage_file_with_a_non_integer_count_is_refused(tmp_path):
    usage = tmp_path / "usage.json"
    usage.write_text(json.dumps({"input_tokens": "41000",
                                 "output_tokens": 9000}), encoding="utf-8")
    tid = _open(tmp_path, "16x9")
    stored = ROOT / "evals" / "traces" / f"{tid}.json"
    try:
        p = _close_with(tid, ROOT / "fixtures" / "deck-pass.en.html",
                        "--usage", str(usage))
        assert p.returncode != 0
        assert "Traceback" not in p.stderr
        assert "input_tokens" in p.stderr
    finally:
        stored.unlink(missing_ok=True)


def test_a_usage_file_that_does_not_exist_is_refused(tmp_path):
    tid = _open(tmp_path, "16x9")
    stored = ROOT / "evals" / "traces" / f"{tid}.json"
    try:
        p = _close_with(tid, ROOT / "fixtures" / "deck-pass.en.html",
                        "--usage", str(tmp_path / "gone.json"))
        assert p.returncode != 0
        assert "Traceback" not in p.stderr
        assert "gone.json" in p.stderr, "the message names the file it could not read"
    finally:
        stored.unlink(missing_ok=True)


def test_the_typed_token_flags_are_gone(tmp_path):
    """argparse itself refuses --input-tokens: the flag does not exist, in the
    same way there has never been a flag for a verdict."""
    p = _close_with("t-000000000000", "x.html", "--input-tokens", "5")
    assert p.returncode != 0
    assert "--input-tokens" in p.stderr, "refused as unrecognized, not misparsed"
    helptext = subprocess.run(
        [sys.executable, str(TRACE_PY), "close", "--help"],
        capture_output=True, text=True).stdout
    assert "--input-tokens" not in helptext
    assert "--output-tokens" not in helptext
    assert "--usage" in helptext


def test_the_digest_is_the_one_run_conformance_uses():
    """One implementation. A fingerprint that differed between callers would be
    worse than none, because both sides would report matches."""
    sys.path.insert(0, str(ROOT / "scripts" / "lib"))
    sys.path.insert(0, str(ROOT / "scripts" / "ops"))
    import fingerprint
    import run_conformance
    task = {"prompt": "p", "deliverable": "d", "score": 1, "require": [],
            "answers": None, "input": None, "genre": "internal"}
    assert run_conformance.task_fingerprint(task) == fingerprint.material_hash(task)


def test_the_geometry_cross_check_reads_the_real_body_not_the_decoy(tmp_path):
    """The stylesheet comment carries a literal <body data-geometry="landscape">
    in every deliverable. The cross-check's first run against a real portrait
    document read it and refused a correct trace — the fifth defect from that
    one sentence."""
    doc = tmp_path / "portrait.html"
    doc.write_text(
        '<html><head><style>/* declares with <body data-geometry="landscape"> */'
        '</style></head><body data-geometry="portrait">'
        '<section class="page"></section></body></html>', encoding="utf-8")
    tid = _open(tmp_path, "a4")
    try:
        p = _close(tid, doc)
        assert p.returncode == 0, p.stderr
    finally:
        (ROOT / "evals" / "traces" / f"{tid}.json").unlink(missing_ok=True)
