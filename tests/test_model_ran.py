"""What was pinned and what ran are different facts, and only one was kept.

`--model x` is a request. With nothing pinned the record read `(the CLI's
default)`, which describes the ASK. Cursor's stream announces `"model":"Auto"`
on its `system`/`init` line, and **Auto routes** — so a board cell said
"default" over a run whose model nobody could name afterwards, on a board whose
whole argument is that a cell states what produced it.

Found when the owner asked which model a verification run had used. The answer
was in the transcript, in a field the driver had never read. Recovering it from
the transcripts still on disk then retracted a published claim: a three-row
timing table in 0.1.605 compared 1813s / 1004s / 677s as one agent improving,
and the 1813s row is `Cursor Grok 4.6 Extra High` while the other two are
`Auto`. The largest drop was the step where the model changed.
"""
import json

import run_conformance

INIT = {"type": "system", "subtype": "init", "model": "Auto",
        "session_id": "x", "cwd": "somewhere"}


def _stream(*objs):
    return "\n".join(json.dumps(o) for o in objs)


def test_the_model_is_read_off_the_stream():
    text = _stream(INIT, {"type": "user", "message": {"role": "user"}})
    assert run_conformance._model_from_transcript(text) == "Auto"


def test_a_single_object_transcript_works_too():
    """Claude Code's `--output-format json` is one object, not NDJSON."""
    assert run_conformance._model_from_transcript(
        json.dumps({"model": "claude-opus-5", "usage": {}})) == "claude-opus-5"


def test_a_trailing_cli_warning_does_not_hide_it():
    """The transcript is stdout AND stderr; the usage reader learned this first."""
    text = json.dumps({"model": "claude-opus-5"}) + "\nno stdin data received\n"
    assert run_conformance._model_from_transcript(text) == "claude-opus-5"


def test_the_session_announcement_wins_over_a_later_per_message_model():
    """The init line is the session's own answer; a later one is one turn's.

    The fixture puts a per-message `model` on an EARLIER line than the init
    record, because a stream that happens to be in the convenient order proves
    nothing about which rule is being applied — the first version of this test
    had them the other way round and passed against a scan that took whatever
    came first.
    """
    text = _stream({"type": "assistant", "model": "some-other-model"}, INIT)
    assert run_conformance._model_from_transcript(text) == "Auto"


def test_a_cli_that_says_nothing_returns_none():
    """None means "not returned", never a guess. Gemini and Hermes say nothing."""
    assert run_conformance._model_from_transcript("plain text output") is None
    assert run_conformance._model_from_transcript("") is None
    assert run_conformance._model_from_transcript(
        _stream({"type": "system", "subtype": "init"})) is None
    assert run_conformance._model_from_transcript(
        _stream({"type": "system", "subtype": "init", "model": "   "})) is None


def test_an_unparseable_line_does_not_stop_the_scan():
    text = "not json at all\n" + json.dumps(INIT)
    assert run_conformance._model_from_transcript(text) == "Auto"


def test_the_cell_prefers_what_ran():
    """`Auto` routing to a model is not the same claim as pinning that model."""
    cell = run_conformance._model_cell
    assert cell({"model": "(the CLI's default)", "model_ran": "Auto"}) == "Auto"
    assert cell({"model": "cursor-grok-4.6-high",
                 "model_ran": "cursor-grok-4.6-high"}) == "cursor-grok-4.6-high"
    assert cell({"model": "opus", "model_ran": "claude-opus-5"}) == \
        "claude-opus-5 (asked opus)"


def test_an_unconfirmed_ask_never_prints_as_an_answer():
    """FM-24, in the release written immediately after FM-24 was written.

    A model PINNED with no answer from the CLI printed exactly what a confirmed
    one prints — `deepseek-v4-flash` either way — so a request read as a
    measurement, on the column this release exists to make truthful. Gemini and
    Hermes announce no model at all, so this is the ordinary case for two of
    the four agents on the board, not an edge.

    The ask is still the only thing known and is still worth printing. It is
    printed as an ask.
    """
    cell = run_conformance._model_cell
    unconfirmed = cell({"model": "deepseek-v4-flash", "model_ran": None})
    confirmed = cell({"model": "deepseek-v4-flash",
                      "model_ran": "deepseek-v4-flash"})
    assert unconfirmed != confirmed, (
        "a pinned model nobody confirmed reads exactly like a confirmed one")
    assert unconfirmed == "asked deepseek-v4-flash, unconfirmed"
    assert confirmed == "deepseek-v4-flash"


def test_an_unpinned_silent_run_is_unconfirmed_too():
    """The half the first fix left behind, and a test of mine had blessed it.

    Repairing the pinned case left the unpinned one returning `(the CLI's
    default)` — the exact string this release exists to abolish, byte-identical
    to what the pre-fix board printed, and the ordinary case for two of the four
    agents on it. A review caught it; the test that stood here asserted the
    defect as correct behaviour, which is worse than not having covered it.
    """
    cell = run_conformance._model_cell
    assert cell({"model": "(the CLI's default)", "model_ran": None}) == \
        "unconfirmed"
    assert cell({}) == "unconfirmed"
    assert cell({"model": None, "model_ran": "Auto"}) == "Auto"
    assert "(the CLI's default)" not in str(
        cell({"model": "(the CLI's default)", "model_ran": None}))


def test_every_shape_reads_differently():
    """Six states, six strings — the column has to be readable as evidence."""
    cell = run_conformance._model_cell
    seen = [cell(r) for r in (
        {"model": "(the CLI's default)", "model_ran": "Auto"},
        {"model": "x", "model_ran": "X Display Name"},
        {"model": "x", "model_ran": "x"},
        {"model": "x", "model_ran": None},
    )]
    assert len(set(seen)) == len(seen), seen
    # The two unconfirmed-and-unpinned shapes collapse deliberately: a record
    # with no ask and one whose ask was "nothing was pinned" know the same
    # amount, which is nothing.
    assert cell({"model": "(the CLI's default)", "model_ran": None}) == \
        cell({}) == "unconfirmed"


def test_score_writes_the_model_that_ran_into_the_scores_file(tmp_path,
                                                              monkeypatch):
    """End to end, because the extractor could be perfect and never called.

    Deleting the line that puts `model_ran` into `driver.json` leaves every
    unit test above green — the field would exist and reach no record, which is
    the shape this file is about one level up.
    """
    (tmp_path / "SKILL.md").write_text(
        '---\nmetadata:\n  version: "0.1.999"\n---\n', encoding="utf-8")
    (tmp_path / "adapters").mkdir()
    (tmp_path / "adapters" / "platforms.json").write_text(json.dumps(
        {"platforms": [{"id": "a1", "name": "Agent One", "capability": "prompt"}]}),
        encoding="utf-8")
    tasks = tmp_path / "conformance" / "tasks"
    tasks.mkdir(parents=True)
    (tasks / "T1.json").write_text(json.dumps(
        {"id": "T1", "prompt": "write answers.md", "min_capability": "prompt",
         "score": ["recall"], "deliverable": "*.md",
         "answers": {"the output language": [r"\benglish\b"]}}),
        encoding="utf-8")
    run = tmp_path / "run1"
    (run / "a1" / "T1").mkdir(parents=True)
    (run / "a1" / "T1" / "answers.md").write_text(
        "the output language is English\n", encoding="utf-8")
    (run / "a1" / "T1" / "driver.json").write_text(json.dumps(
        {"verdict": "driven", "model": "(the CLI's default)",
         "model_ran": "Auto", "seconds": 1}), encoding="utf-8")
    for attr, value in (("ROOT", tmp_path),
                        ("REGISTRY", tmp_path / "adapters" / "platforms.json"),
                        ("TASKS", tasks),
                        ("RESULTS", tmp_path / "conformance" / "results")):
        monkeypatch.setattr(run_conformance, attr, value)
    run_conformance.main(["score", "--run", str(run)])
    scored = json.loads((run / "scores.json").read_text(encoding="utf-8"))
    assert scored["a1/T1"]["model"] == "Auto", scored["a1/T1"]


def test_a_driver_record_that_cannot_be_read_says_so(tmp_path, monkeypatch,
                                                     capsys):
    """`—` is what a HAND-DRIVEN task prints; an unreadable record is not that.

    The scorer `continue`d in silence on a `driver.json` it could not parse, so
    a run killed at its hard cap — which leaves a truncated file — rendered
    identically to a task nobody drove. FM-24's `history.json` instance, one
    file over, in the release that touched the line.
    """
    (tmp_path / "SKILL.md").write_text(
        '---\nmetadata:\n  version: "0.1.999"\n---\n', encoding="utf-8")
    (tmp_path / "adapters").mkdir()
    (tmp_path / "adapters" / "platforms.json").write_text(json.dumps(
        {"platforms": [{"id": "a1", "name": "Agent One", "capability": "prompt"}]}),
        encoding="utf-8")
    tasks = tmp_path / "conformance" / "tasks"
    tasks.mkdir(parents=True)
    (tasks / "T1.json").write_text(json.dumps(
        {"id": "T1", "prompt": "write answers.md", "min_capability": "prompt",
         "score": ["recall"], "deliverable": "*.md",
         "answers": {"the output language": [r"\benglish\b"]}}),
        encoding="utf-8")
    run = tmp_path / "run1"
    (run / "a1" / "T1").mkdir(parents=True)
    (run / "a1" / "T1" / "answers.md").write_text(
        "the output language is English\n", encoding="utf-8")
    (run / "a1" / "T1" / "driver.json").write_text(
        '{"verdict": "driven", "model', encoding="utf-8")   # truncated mid-write
    for attr, value in (("ROOT", tmp_path),
                        ("REGISTRY", tmp_path / "adapters" / "platforms.json"),
                        ("TASKS", tasks),
                        ("RESULTS", tmp_path / "conformance" / "results")):
        monkeypatch.setattr(run_conformance, attr, value)
    run_conformance.main(["score", "--run", str(run)])
    assert "does not parse" in capsys.readouterr().out
    scored = json.loads((run / "scores.json").read_text(encoding="utf-8"))
    assert scored["a1/T1"]["model"] == "driver record unreadable"


def test_the_whole_configuration_reaches_the_scores_file(tmp_path, monkeypatch):
    """`effort` reached `driver.json` and the trace and nothing else.

    So the board could say which model ran and never at what reasoning tier —
    and `report --record`, which reads `scores.json`, had nothing to carry into
    a history row. The three fields ride in the SAME pass as `model`, for the
    reason that pass's own comment gives: a cell whose model is present because
    one branch remembered and whose effort is missing because another forgot is
    worse than a column that is not there.
    """
    (tmp_path / "SKILL.md").write_text(
        '---\nmetadata:\n  version: "0.1.999"\n---\n', encoding="utf-8")
    (tmp_path / "adapters").mkdir()
    (tmp_path / "adapters" / "platforms.json").write_text(json.dumps(
        {"platforms": [{"id": "a1", "name": "Agent One", "capability": "prompt"}]}),
        encoding="utf-8")
    tasks = tmp_path / "conformance" / "tasks"
    tasks.mkdir(parents=True)
    (tasks / "T1.json").write_text(json.dumps(
        {"id": "T1", "prompt": "write answers.md", "min_capability": "prompt",
         "score": ["recall"], "deliverable": "*.md",
         "answers": {"the output language": [r"\benglish\b"]}}),
        encoding="utf-8")
    run = tmp_path / "run1"
    (run / "a1" / "T1").mkdir(parents=True)
    (run / "a1" / "T1" / "answers.md").write_text(
        "the output language is English\n", encoding="utf-8")
    (run / "a1" / "T1" / "driver.json").write_text(json.dumps(
        {"verdict": "driven", "model": "cursor-grok-4.6-high",
         "model_ran": "Cursor Grok 4.6", "effort": "high",
         "trace_id": "t-abcdef012345", "seconds": 1}), encoding="utf-8")
    for attr, value in (("ROOT", tmp_path),
                        ("REGISTRY", tmp_path / "adapters" / "platforms.json"),
                        ("TASKS", tasks),
                        ("RESULTS", tmp_path / "conformance" / "results")):
        monkeypatch.setattr(run_conformance, attr, value)
    run_conformance.main(["score", "--run", str(run)])
    cell = json.loads((run / "scores.json").read_text(encoding="utf-8"))["a1/T1"]
    assert cell["model"] == "Cursor Grok 4.6 (asked cursor-grok-4.6-high)"
    assert cell["effort"] == "high"
    assert cell["model_asked"] == "cursor-grok-4.6-high"
    assert cell["trace_id"] == "t-abcdef012345"


def _score_one(tmp_path, monkeypatch, driver):
    """Drive `score` over one synthetic task carrying the given driver record."""
    (tmp_path / "SKILL.md").write_text(
        '---\nmetadata:\n  version: "0.1.999"\n---\n', encoding="utf-8")
    (tmp_path / "adapters").mkdir(exist_ok=True)
    (tmp_path / "adapters" / "platforms.json").write_text(json.dumps(
        {"platforms": [{"id": "a1", "name": "Agent One", "capability": "prompt"}]}),
        encoding="utf-8")
    tasks = tmp_path / "conformance" / "tasks"
    tasks.mkdir(parents=True, exist_ok=True)
    (tasks / "T1.json").write_text(json.dumps(
        {"id": "T1", "prompt": "write answers.md", "min_capability": "prompt",
         "score": ["recall"], "deliverable": "*.md",
         "answers": {"the output language": [r"\benglish\b"]}}),
        encoding="utf-8")
    run = tmp_path / "run1"
    (run / "a1" / "T1").mkdir(parents=True, exist_ok=True)
    (run / "a1" / "T1" / "answers.md").write_text(
        "the output language is English\n", encoding="utf-8")
    (run / "a1" / "T1" / "driver.json").write_text(json.dumps(driver),
                                                   encoding="utf-8")
    for attr, value in (("ROOT", tmp_path),
                        ("REGISTRY", tmp_path / "adapters" / "platforms.json"),
                        ("TASKS", tasks),
                        ("RESULTS", tmp_path / "conformance" / "results")):
        monkeypatch.setattr(run_conformance, attr, value)
    run_conformance.main(["score", "--run", str(run)])
    return json.loads((run / "scores.json").read_text(encoding="utf-8"))["a1/T1"]


def test_an_unpinned_effort_is_carried_as_written_not_dropped(tmp_path,
                                                              monkeypatch):
    """`(not pinned)` is an answer and reaches the cell as one.

    Dropping it would make "nobody pinned an effort" and "this scores file
    predates the field" the same absence — two states, one string, which is the
    shape FM-24 names. The first version of this test re-implemented the
    attaching loop in the test body and so tested a copy of the logic rather
    than the logic; it passed against a `score` that carried nothing.
    """
    cell = _score_one(tmp_path, monkeypatch, {
        "verdict": "driven", "model": "(the CLI's default)",
        "model_ran": "Auto", "effort": "(not pinned)", "seconds": 1})
    assert cell["effort"] == "(not pinned)"
    assert cell["model"] == "Auto"


def test_a_driver_record_predating_the_field_carries_no_effort_key(tmp_path,
                                                                   monkeypatch):
    """Absent, not invented — the other side of the same distinction."""
    cell = _score_one(tmp_path, monkeypatch, {
        "verdict": "driven", "model": "(the CLI's default)",
        "model_ran": "Auto", "seconds": 1})
    assert "effort" not in cell
    assert "trace_id" not in cell


def test_the_trace_id_is_recorded_into_the_driver_record(tmp_path, monkeypatch):
    """The join key, written where it is the only thing that knows it.

    The trace holds what a run COST; `history.json` holds what it EARNED. The
    join was `(agent, date)`, which is wrong the first time two agents run on
    one day. `_conformance_trace` opens the trace and knew the id, and returned
    only a sentence about it.

    Reachable without driving an agent: the helper shells out to `trace.py`
    itself, so a task with a storyline and a redirected store exercises the real
    path. Every other test here hand-writes `driver.json` and so cannot see this
    line at all — deleting it left them all green.
    """
    store = tmp_path / "traces"
    store.mkdir()
    monkeypatch.setenv("LUMI_TRACES", str(store))
    wd = tmp_path / "wd"
    wd.mkdir()
    record = {"verdict": "driven", "produced": [], "seconds": 3,
              "model": "m", "effort": "high"}
    run_conformance._conformance_trace(
        {"id": "a1"},
        {"id": "T1", "deliverable": "*.md", "storyline": "market-analysis",
         "genre": "internal"},
        wd, record)
    tid = record.get("trace_id")
    assert tid, "the id the helper opened was not recorded"
    assert isinstance(tid, str) and tid.startswith("t-")
    written = list(store.glob("*.json"))
    assert written, "no trace was opened"
    assert json.loads(written[0].read_text())["trace_id"] == tid
