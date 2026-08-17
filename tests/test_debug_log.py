"""debug_log.py proven able to pass AND to fail (FM-01 discipline).

The log is the debug mode's whole product, so each promise gets both sides:
what a subcommand writes, and what `validate` refuses. The refusals matter
more than the writes — a log arrives at an evaluator as a file, not as a
sequence of subcommand calls, so anything only the writer enforces is a
promise the artifact does not keep.
"""
import concurrent.futures as cf
import json
import subprocess
import sys

import debug_log
import pytest


def _init(tmp_path, name="doc.en.html"):
    deliverable = tmp_path / name
    deliverable.write_text("<html></html>")
    rc = debug_log.main(["init", str(deliverable), "--platform", "claude-code"])
    assert rc == 0
    return tmp_path / (name.split(".")[0] + ".debug.json")


def _run(path, *command, label="step"):
    return debug_log.main(["run", str(path), "--label", label, "--", *command])


def _read(path):
    return json.loads(path.read_text())


# init

def test_init_writes_the_closed_shape(tmp_path, capsys):
    log = _read(_init(tmp_path))
    assert set(log) == debug_log.TOP_KEYS
    assert log["deliverable"] == "doc.en.html"
    assert log["platform"] == "claude-code"


def test_init_refuses_a_platform_the_registry_does_not_claim(tmp_path):
    deliverable = tmp_path / "doc.en.html"
    deliverable.write_text("x")
    with pytest.raises(SystemExit):
        debug_log.main(["init", str(deliverable), "--platform", "hermas"])


def test_init_refuses_to_overwrite_a_build_s_evidence(tmp_path, capsys):
    path = _init(tmp_path)
    _run(path, sys.executable, "-c", "print(1)")
    with pytest.raises(SystemExit):
        debug_log.main(["init", str(tmp_path / "doc.en.html"),
                        "--platform", "claude-code"])
    assert _read(path)["commands"], "the refused init must not have cleared it"


def test_init_restart_replaces_it_on_purpose(tmp_path, capsys):
    path = _init(tmp_path)
    _run(path, sys.executable, "-c", "print(1)")
    assert debug_log.main(["init", str(tmp_path / "doc.en.html"),
                           "--platform", "claude-code", "--restart"]) == 0
    assert _read(path)["commands"] == []


# run

def test_run_records_machine_written_evidence(tmp_path, capsys):
    path = _init(tmp_path)
    # `--label` BEFORE `--`: the regression lock for the argparse REMAINDER
    # bug that once made the label the executable.
    assert _run(path, sys.executable, "-c", "print('hello')", label="greet") == 0
    log = _read(path)
    entry = log["commands"][0]
    assert entry["exit_code"] == 0
    assert debug_log.DIGEST.fullmatch(entry["stdout_sha256"])
    assert log["steps"][0] == {"label": "greet", "seconds": entry["seconds"],
                               "source": "run"}


def test_run_passes_the_exit_code_through(tmp_path, capsys):
    path = _init(tmp_path)
    assert _run(path, sys.executable, "-c", "raise SystemExit(3)") == 3
    assert _read(path)["commands"][0]["exit_code"] == 3


def test_a_failure_writes_its_own_record(tmp_path, capsys):
    path = _init(tmp_path)
    _run(path, sys.executable, "-c",
         "import sys; print('the reason', file=sys.stderr); raise SystemExit(1)")
    log = _read(path)
    assert log["errors"], "a nonzero exit must not leave the log silent"
    assert "the reason" in log["errors"][0]["message"]
    assert "the reason" in log["commands"][0]["tail"]


def test_stderr_is_digested_too(tmp_path, capsys):
    # Two commands that differ only on stderr must not share one digest: a
    # crashed command's whole story is usually on the stream stdout ignores.
    path = _init(tmp_path)
    _run(path, sys.executable, "-c", "import sys; print('a', file=sys.stderr)")
    _run(path, sys.executable, "-c", "import sys; print('b', file=sys.stderr)")
    a, b = _read(path)["commands"]
    assert a["stdout_sha256"] != b["stdout_sha256"]


def test_a_command_that_cannot_start_is_still_recorded(tmp_path, capsys):
    path = _init(tmp_path)
    with pytest.raises(SystemExit):
        _run(path, str(tmp_path / "no_such_tool"), label="build")
    log = _read(path)
    assert log["commands"][0]["exit_code"] is None
    assert log["errors"][0]["stage"] == "build"


# the parallel build protocol this package ships

def test_concurrent_writers_all_survive(tmp_path):
    """Eight agents, one log — the shape SKILL.md step 1 puts in flight.

    Before the lock: one entry survived of eight, and the file came back as
    unparseable JSON. Separate processes, not threads, because that is what
    the protocol actually spawns and a thread lock would prove nothing.
    """
    path = _init(tmp_path)

    def one(i):
        return subprocess.run(
            [sys.executable, str(debug_log.__file__), "run", str(path),
             "--label", f"part-{i}", "--", sys.executable, "-c", f"print({i})"],
            capture_output=True).returncode

    with cf.ThreadPoolExecutor(8) as ex:
        assert list(ex.map(one, range(8))) == [0] * 8
    log = _read(path)          # parses at all, which it did not before the lock
    assert len(log["commands"]) == 8
    assert {s["label"] for s in log["steps"]} == {f"part-{i}" for i in range(8)}


# attach

def test_attach_keeps_every_run_not_just_the_last(tmp_path, capsys):
    path = _init(tmp_path)
    for verdict in ("FAIL", "ok"):
        report = tmp_path / f"{verdict}.json"
        report.write_text(json.dumps({"verdicts": {"D1": verdict}}))
        debug_log.main(["attach", str(path), "--kind", "design",
                        "--json-file", str(report)])
    docs = _read(path)["checks"]["design"]
    assert [d["doc"]["verdicts"]["D1"] for d in docs] == ["FAIL", "ok"]


def test_attach_refuses_an_unparseable_report(tmp_path, capsys):
    path = _init(tmp_path)
    broken = tmp_path / "broken.json"
    broken.write_text("")          # a checker that crashed writes nothing
    with pytest.raises(SystemExit):
        debug_log.main(["attach", str(path), "--kind", "design",
                        "--json-file", str(broken)])


def test_an_attached_report_carrying_cjk_fails_validate(tmp_path, capsys):
    # `attach` is the one door outside content enters through.
    path = _init(tmp_path)
    _run(path, sys.executable, "-c", "print(1)")
    report = tmp_path / "r.json"
    report.write_text(json.dumps({"note": "这不是英文"}, ensure_ascii=False),
                      encoding="utf-8")
    debug_log.main(["attach", str(path), "--kind", "prose",
                    "--json-file", str(report)])
    assert debug_log.main(["validate", str(path)]) == 1


# assess

def test_assess_refuses_a_self_scored_five(tmp_path, capsys):
    path = _init(tmp_path)
    with pytest.raises(SystemExit):
        debug_log.main(["assess", str(path), "--dim", "C1", "--score", "5",
                        "--reason", "perfect"])
    assert _read(path)["quality"] == {}, "the refusal must not have written"


def test_assess_refuses_an_empty_reason(tmp_path, capsys):
    path = _init(tmp_path)
    with pytest.raises(SystemExit):
        debug_log.main(["assess", str(path), "--dim", "C1", "--score", "4",
                        "--reason", "   "])
    assert _read(path)["quality"] == {}


# validate — the schema for the file that arrives

def _worked(tmp_path):
    path = _init(tmp_path)
    _run(path, sys.executable, "-c", "print(1)")
    debug_log.main(["assess", str(path), "--dim", "C1", "--score", "4",
                    "--reason", "holds"])
    return path


def test_validate_passes_a_log_that_records_real_work(tmp_path, capsys):
    assert debug_log.main(["validate", str(_worked(tmp_path))]) == 0


def test_validate_fails_an_empty_log(tmp_path, capsys):
    # An agent that crashed before running anything produced a file the first
    # version of this function blessed — and SKILL.md tells the author to point
    # the reader at it.
    assert debug_log.main(["validate", str(_init(tmp_path))]) == 1


def test_validate_fails_an_unknown_key(tmp_path, capsys):
    path = _worked(tmp_path)
    log = _read(path)
    log["client"] = "somebody"
    path.write_text(json.dumps(log))
    assert debug_log.main(["validate", str(path)]) == 1


def test_validate_fails_cjk_content(tmp_path, capsys):
    path = _worked(tmp_path)
    log = _read(path)
    log["notes"].append("这不是英文")
    path.write_text(json.dumps(log, ensure_ascii=False), encoding="utf-8")
    assert debug_log.main(["validate", str(path)]) == 1


@pytest.mark.parametrize("mangle", [
    pytest.param(lambda log: log["commands"].append(
        {"command": "checks all pass", "exit_code": 0}), id="no-digest"),
    pytest.param(lambda log: log["commands"].append(
        {"command": "x", "exit_code": 0, "stdout_sha256": "not-a-digest",
         "date": "2026-08-12T00:00:00+00:00"}), id="fake-digest"),
    pytest.param(lambda log: log["commands"].append(
        {"command": "x", "exit_code": 0, "stdout_sha256": "a" * 64,
         "date": "whenever"}), id="unparseable-date"),
    pytest.param(lambda log: log["quality"].__setitem__(
        "C2", {"score": 9, "reason": "great"}), id="score-out-of-range"),
    pytest.param(lambda log: log["quality"].__setitem__(
        "C2", {"score": "5", "reason": "perfect"}), id="stringly-typed-five"),
    pytest.param(lambda log: log["quality"].__setitem__("C3", "good"),
                 id="quality-not-an-object"),
    pytest.param(lambda log: log["steps"].append({"label": "x", "seconds": 3}),
                 id="step-without-provenance"),
    pytest.param(lambda log: log["checks"].__setitem__("design", {"verdicts": {}}),
                 id="checks-not-a-list"),
    pytest.param(lambda log: log.__setitem__("platform", "invented"),
                 id="unknown-platform"),
])
def test_validate_refuses_a_hand_assembled_log(tmp_path, capsys, mangle):
    path = _worked(tmp_path)
    log = _read(path)
    mangle(log)
    path.write_text(json.dumps(log))
    assert debug_log.main(["validate", str(path)]) == 1


def test_validate_names_the_right_problem_for_a_malformed_quality_entry(
        tmp_path, capsys):
    path = _worked(tmp_path)
    log = _read(path)
    log["quality"]["C3"] = "good"
    path.write_text(json.dumps(log))
    debug_log.main(["validate", str(path)])
    out = capsys.readouterr().out
    assert "not a {score, reason} object" in out
    assert "self-scored 5" not in out, "there is no 5 here to search for"


def test_a_missing_or_damaged_log_fails_with_a_line_not_a_traceback(tmp_path):
    with pytest.raises(SystemExit):
        debug_log.main(["validate", str(tmp_path / "absent.debug.json")])
    damaged = tmp_path / "damaged.debug.json"
    damaged.write_text('{"debug_log": "1", "commands": [')
    with pytest.raises(SystemExit):
        debug_log.main(["validate", str(damaged)])


# What a FAILING CHECKER records. The tail of a --json run is the threshold
# footer every check script prints last, so the first third-party log this
# package collected held five errors of which three said nothing at all.

def _emit(payload, code=1):
    """A fake checker: prints `payload` as JSON on stdout, then exits `code`."""
    return [sys.executable, "-c",
            f"import json; print(json.dumps({payload!r})); raise SystemExit({code})"]


def test_a_failing_checker_records_which_check_failed(tmp_path, capsys):
    # check_prose.py / check_design.py: a LIST of per-file documents.
    doc = [{"file": "deck.en.html",
            "verdicts": {"M4_banned_hits": "ok", "M6_unsourced_ranges": "FAIL",
                         "M12_visible_cjk": "n/a"},
            "targets": {"M6_unsourced_ranges": "=0"}}]
    path = _init(tmp_path)
    _run(path, *_emit(doc), label="check_prose")
    log = _read(path)
    message = log["errors"][0]["message"]
    assert "M6_unsourced_ranges" in message
    assert "M4_banned_hits" not in message, "an ok verdict is not a failure"
    assert "M12_visible_cjk" not in message, "n/a means ungraded, not failed"
    assert log["commands"][0]["failing"] == ["deck.en.html: M6_unsourced_ranges FAIL"]


def test_a_failing_layout_run_records_its_verdicts_and_unmeasured(tmp_path, capsys):
    # inspect_layout.py --deliverable --json: ONE dict, verdicts at the top.
    doc = {"results": [], "unmeasured": 2,
           "verdicts": {"collision": "ok", "content_spill": "FAIL"}}
    path = _init(tmp_path)
    _run(path, *_emit(doc), label="inspect")
    message = _read(path)["errors"][0]["message"]
    assert "content_spill" in message
    assert "2 check(s) could not be measured" in message


def test_a_nonzero_exit_with_no_failing_verdict_says_so(tmp_path, capsys):
    # check_design drops an unmeasurable file from the JSON and still exits 1,
    # so "nothing failed" is a real answer and must not read as an empty line.
    path = _init(tmp_path)
    _run(path, *_emit([]), label="check_design")
    message = _read(path)["errors"][0]["message"]
    assert "no failing verdict" in message


def test_a_non_json_failure_still_records_its_tail(tmp_path, capsys):
    # The fallback has to hold: a crash, or any tool that is not one of ours.
    path = _init(tmp_path)
    _run(path, sys.executable, "-c",
         "import sys; print('Traceback: it died here', file=sys.stderr); "
         "raise SystemExit(2)")
    log = _read(path)
    assert "it died here" in log["errors"][0]["message"]
    assert "failing" not in log["commands"][0]
