"""The trace schema is closed, and the tool refuses to write an illegal record.

The point of these tests is not that the happy path works. It is that the three
disciplines the design record names — machine-written verdicts, a trace opened
before the build rather than after, and no free text — are properties of the
code rather than of whoever runs it.
"""
import json
import os
import pathlib
import re
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
               gates={}, graded={}, thresholds={}, shape={},
               principle_yields=[],
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


def test_the_blind_gate_case_now_speaks_clean_json_with_the_warning_inside(tmp_path):
    """0.1.497 fixed the CONSUMER (a silent checker is recorded, not skipped);
    this release fixed the ROOT: check_design's blind-gate warning printed even
    under --json, so the one document it fires on emitted prose over the JSON.
    The warning now travels IN the report as `blind_gates`, and the channel
    stays parseable."""
    src = (ROOT / "fixtures" / "deck-pass.en.html").read_text(encoding="utf-8")
    doc = tmp_path / "divpage.html"
    doc.write_text(src.replace('<section class="page', '<div class="page')
                      .replace("</section>", "</div>"), encoding="utf-8")
    parsed, spoke = _trace_tool._checker_json("check_design.py", doc)
    assert spoke is True, "the channel must stay clean on the very case the warning fires on"
    assert parsed and parsed[0].get("blind_gates"), "the warning belongs in the report"


def test_a_healthy_deliverable_is_recorded_as_having_spoken():
    parsed, spoke = _trace_tool._checker_json(
        "check_design.py", ROOT / "fixtures" / "deck-pass.en.html")
    assert spoke is True
    assert parsed


def test_a_silent_checker_leaves_a_not_measured_marker(tmp_path):
    """End to end: open, close against a document whose design half cannot be
    transcribed, and assert the trace SAYS so. The old trigger (div.page prose
    over the JSON) was fixed at the root, so the silence is planted directly:
    a document of raw bytes no checker can read as markup."""
    env = {**os.environ, "LUMI_TRACES": str(tmp_path)}
    doc = tmp_path / "divpage.html"
    doc.write_bytes(b"\x00\x01\x02\x03\x04")
    tid = subprocess.run(
        [sys.executable, str(TRACE_PY), "open", "--genre", "internal",
         "--storyline", "proposal", "--entry-path", "B", "--source", "build"],
        capture_output=True, text=True, env=env, cwd=ROOT).stdout.strip()
    try:
        subprocess.run([sys.executable, str(TRACE_PY), "close", "--id", tid,
                        "--deliverable", str(doc)],
                       capture_output=True, text=True, env=env, cwd=ROOT, check=True)
        # LUMI_TRACES is honoured since 0.1.531 (it was passed here for
        # releases before that and silently ignored), so the record is in
        # tmp_path and the tracked store is untouched.
        rec = json.loads((tmp_path / f"{tid}.json").read_text(encoding="utf-8"))
        # Raw bytes make prose answer "unmeasurable" and design answer an
        # empty report — both SPOKE, honestly, so the per-checker silence
        # marker rightly stays absent and the whole-build marker fires: a
        # build that was never graded says so.
        assert rec["thresholds"].get("_checkers") == "not_measured"
        assert not rec["gates"] and not rec["graded"]
    finally:
        (tmp_path / f"{tid}.json").unlink(missing_ok=True)


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


def test_annotate_writes_the_link_fields_and_only_those(tmp_path):
    """corpus_id and review_ref are addresses, not verdicts — the one pair
    annotate may write after close, because the verdict fields still have no
    flag anywhere."""
    tid = _open(tmp_path, "16x9")
    try:
        p = subprocess.run(
            [sys.executable, str(TRACE_PY), "annotate", "--id", tid,
             "--corpus-id", "D15", "--review-ref", "reviews/scores.json 0.1.508 D15"],
            capture_output=True, text=True, cwd=ROOT)
        assert p.returncode == 0, p.stderr
        rec = json.loads((ROOT / "evals" / "traces" / f"{tid}.json").read_text())
        assert rec["corpus_id"] == "D15"
        assert rec["review_ref"].startswith("reviews/scores.json")
    finally:
        (ROOT / "evals" / "traces" / f"{tid}.json").unlink(missing_ok=True)


# --phase wrote strings until 0.1.524. argparse handed both elements of the
# pair over as str, close() stored them as written, the schema typed the phase
# NAME and not the value, and ledger.py sums the values. No trace had ever
# carried a phase, so the TypeError had never fired; the audit read the code.

def test_phase_seconds_value_must_be_a_number():
    rec = _legal()
    rec["phase_seconds"] = {"build": "12"}
    assert any("phase_seconds['build']" in e for e in trace.validate(rec))
    rec["phase_seconds"] = {"build": 12, "checks": 3.5}
    assert trace.validate(rec) == []


def test_close_parses_phase_seconds_as_numbers_and_ledger_can_sum_them(tmp_path):
    tid = _open(tmp_path, "16x9")
    try:
        p = subprocess.run(
            [sys.executable, str(TRACE_PY), "close", "--id", tid,
             "--deliverable", str(ROOT / "fixtures" / "deck-pass.en.html"),
             "--phase", "build", "12", "--phase", "checks", "3.5"],
            capture_output=True, text=True, cwd=ROOT)
        assert p.returncode == 0, p.stderr
        rec = json.loads((ROOT / "evals" / "traces" / f"{tid}.json")
                         .read_text(encoding="utf-8"))
        assert rec["phase_seconds"] == {"build": 12, "checks": 3.5}
        assert sum(v for k, v in rec["phase_seconds"].items()
                   if k in ("build", "checks")) == 15.5
    finally:
        (ROOT / "evals" / "traces" / f"{tid}.json").unlink(missing_ok=True)


def test_close_refuses_a_phase_that_is_not_a_number(tmp_path):
    tid = _open(tmp_path, "16x9")
    try:
        p = subprocess.run(
            [sys.executable, str(TRACE_PY), "close", "--id", tid,
             "--deliverable", str(ROOT / "fixtures" / "deck-pass.en.html"),
             "--phase", "build", "twelve"],
            capture_output=True, text=True, cwd=ROOT)
        assert p.returncode != 0 and "not a number" in p.stderr
    finally:
        (ROOT / "evals" / "traces" / f"{tid}.json").unlink(missing_ok=True)


# 0.1.531 — the loop writes the phases itself: the scaffold starts the build
# clock, check_deliverable stops it and records its own duration as `checks`,
# and the trace id rides in the body. GAP-014's close condition.

def test_scaffold_then_check_deliverable_leaves_machine_written_phases(tmp_path):
    env = {**os.environ, "LUMI_TRACES": str(tmp_path)}
    deck = tmp_path / "deck.en.html"
    scaffold = subprocess.run(
        [sys.executable, str(ROOT / "scripts/ops/new_deck.py"), "--storyline", "gtm",
         "--genre", "internal", "--pages", "2", "--entry-path", "B"],
        capture_output=True, text=True, env=env, cwd=ROOT, check=True)
    deck.write_text(scaffold.stdout, encoding="utf-8")
    m = re.search(r'data-trace="(t-[0-9a-f]{12})"', scaffold.stdout)
    assert m, "the scaffold carries no data-trace"
    tid = m.group(1)
    assert (tmp_path / ".phases" / f"{tid}.json").exists()
    # A scaffold is not a finished deliverable, so check_deliverable will not
    # exit 0 and will not close; stop the clock and close the way it would,
    # with the same two commands, to hold the shape end to end.
    stop = subprocess.run([sys.executable, str(TRACE_PY), "phase", "stop", "build",
                           "--id", tid], capture_output=True, text=True, env=env, cwd=ROOT)
    assert stop.returncode == 0, stop.stderr
    close = subprocess.run([sys.executable, str(TRACE_PY), "close", "--id", tid,
                            "--deliverable", str(deck), "--phase", "checks", "7"],
                           capture_output=True, text=True, env=env, cwd=ROOT)
    assert close.returncode == 0, close.stderr
    rec = json.loads((tmp_path / f"{tid}.json").read_text(encoding="utf-8"))
    assert rec["phase_seconds"]["build"] >= 1
    assert rec["phase_seconds"]["checks"] == 7
    assert rec["closed_at"]
    assert not (tmp_path / ".phases" / f"{tid}.json").exists()


def test_phase_stop_without_start_is_refused(tmp_path):
    env = {**os.environ, "LUMI_TRACES": str(tmp_path)}
    tid = subprocess.run(
        [sys.executable, str(TRACE_PY), "open", "--genre", "internal",
         "--storyline", "proposal", "--entry-path", "B"],
        capture_output=True, text=True, env=env, cwd=ROOT, check=True).stdout.strip()
    p = subprocess.run([sys.executable, str(TRACE_PY), "phase", "stop", "checks",
                        "--id", tid], capture_output=True, text=True, env=env, cwd=ROOT)
    assert p.returncode != 0 and "never started" in p.stderr


def test_a_declared_trace_that_resolves_to_nothing_is_not_a_record(tmp_path):
    """An id is a promise that a record exists, and `--fast` never checked it.

    A delivery round already caught this by accident: `trace.py close` fails on
    an id it cannot find, prints `no such trace: t-…` and carries a nonzero exit
    back. But the close step is skipped under `--fast`, which is the author's
    inner loop — so a deck naming a trace stored nowhere ran the whole loop
    clean, exit 0, with the word `trace` appearing nowhere in the output.
    Measured on three real decks from one validation round.

    THE TEST RUNS `--fast` FOR THAT REASON. Without it the close step supplies
    the failure and the test passes against unfixed code.
    """
    import markup
    deck = tmp_path / "dangling.en.html"
    src = (ROOT / "fixtures" / "deck-pass.en.html").read_text(encoding="utf-8")
    assert "data-trace" not in src, "the fixture already declares a trace"
    # Patch the tag `body_attr` actually reads — the file carries an earlier
    # `<body` lookalike, and replacing that one injects an attribute the
    # parser never sees (which is how the first draft of this test passed
    # against unfixed code).
    tag = markup.body_tag(src)
    assert tag, "no body tag found in the fixture"
    patched = tag.group(0).replace("<body ", '<body data-trace="t-000000000000" ', 1)
    deck.write_text(src[:tag.start()] + patched + src[tag.end():], encoding="utf-8")
    assert markup.body_attr(deck.read_text(encoding="utf-8"),
                            "data-trace") == "t-000000000000"
    env = {**os.environ, "LUMI_TRACES": str(tmp_path / "empty-store")}
    p = subprocess.run(
        [sys.executable, str(ROOT / "scripts/ops/check_deliverable.py"),
         str(deck), "--fast"],
        capture_output=True, text=True, cwd=ROOT, env=env)
    assert "t-000000000000" in p.stdout, (
        "the dangling id is not named under --fast:\n" + p.stdout[-1500:])
    assert p.returncode != 0, (
        "a --fast round passed a deck naming a trace that does not exist")


def test_check_deliverable_reports_a_missing_trace_as_unmeasured():
    p = subprocess.run(
        [sys.executable, str(ROOT / "scripts/ops/check_deliverable.py"),
         str(ROOT / "fixtures" / "deck-pass.en.html"), "--skip-layout"],
        capture_output=True, text=True, cwd=ROOT)
    assert "trace: none" in p.stdout
    assert p.returncode != 0


def test_a_trace_opened_before_the_shape_field_still_closes(tmp_path):
    """A migration is not done until both sides of it are.

    `trace_schema` was taught that an absent `shape` means "not recorded", and
    `cmd_close` was not: it assumed `cmd_open` had written the key and died
    with KeyError on any build open across the 0.1.595 boundary — losing the
    trace entirely, for 135 stored records and every build in flight.
    """
    env = {**os.environ, "LUMI_TRACES": str(tmp_path)}
    tid = subprocess.run(
        [sys.executable, str(TRACE_PY), "open", "--genre", "internal",
         "--storyline", "market-analysis", "--entry-path", "B",
         "--geometry", "16x9"],
        capture_output=True, text=True, env=env, cwd=ROOT, check=True).stdout.strip()
    stored = tmp_path / f"{tid}.json"
    rec = json.loads(stored.read_text())
    del rec["shape"]                      # a record written before the field
    stored.write_text(json.dumps(rec))
    p = subprocess.run(
        [sys.executable, str(TRACE_PY), "close", "--id", tid, "--deliverable",
         str(ROOT / "fixtures" / "deck-pass.en.html")],
        capture_output=True, text=True, env=env, cwd=ROOT)
    assert p.returncode == 0, p.stderr[-600:]
    assert isinstance(json.loads(stored.read_text()).get("shape"), dict)
