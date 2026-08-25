"""Which file a run is scored on is decided by the task, not by the alphabet.

Both call sites took `produced[0]` off a sorted glob. A deliverable pattern is
`*.html` on purpose — the prompt names the file and the harness accepts what
arrives — so several matches is the ordinary case for any agent that shows its
work, and the scored artifact was whichever name sorted first.

The shape that nearly fired is the fixture below: Claude Code hit the hour cap
on T1-deck in the 0.1.605 round having written `deck.en.html` plus four working
files, and `_s2.html` sorts first. It is a shape sprite. The timeout is what
kept it off the board, which is not a defence.
"""
import pathlib

import run_conformance

T1 = {"deliverable": "*.html",
      "prompt": "produce a twelve-page 16:9 HTML deck … Write the file to "
                "deck.en.html in the working directory."}


def _paths(*names):
    return [pathlib.Path("/run/T1-deck") / n for n in sorted(names)]


def test_the_only_match_is_the_one():
    one, why = run_conformance.scored_file(_paths("deck.en.html"), T1)
    assert one is not None
    assert one.name == "deck.en.html" and why == "the only match"


def test_the_prompt_decides_when_the_glob_does_not():
    """The real timed-out run: five files, and the sprite sorts first."""
    produced = _paths("deck.en.html", "_scaffold.html", "_shapes.html",
                      "_s3.html", "_s2.html")
    assert produced[0].name == "_s2.html", "the fixture no longer has its point"
    one, why = run_conformance.scored_file(produced, T1)
    assert one is not None, "refused to score a run the prompt disambiguates"
    assert one.name == "deck.en.html", f"scored {one} instead"
    assert "the prompt names" in why


def test_nothing_matching_is_undecidable_rather_than_a_guess():
    produced = _paths("draft.html", "notes.html")
    one, why = run_conformance.scored_file(produced, T1)
    assert one is None
    assert "draft.html" in why and "notes.html" in why


def test_two_named_files_are_undecidable_too():
    task = {**T1, "prompt": "write a.html and also b.html"}
    one, why = run_conformance.scored_file(_paths("a.html", "b.html"), task)
    assert one is None and "more than one" in why


def test_no_deliverable_at_all():
    one, why = run_conformance.scored_file([], T1)
    assert one is None and "nothing matched" in why


def test_the_shipped_tasks_all_name_their_deliverable():
    """A task whose prompt names no filename can never be disambiguated.

    Not a hard requirement — a one-file run scores fine either way — but a task
    added without one silently gives up the tie-break, so it is worth failing
    here rather than discovering it on a run that mattered.
    """
    root = pathlib.Path(__file__).resolve().parents[1]
    for f in sorted((root / "conformance" / "tasks").glob("*.json")):
        import json
        task = json.loads(f.read_text(encoding="utf-8"))
        suffix = task["deliverable"].lstrip("*")
        assert suffix in task["prompt"], (
            f"{f.name}: the prompt names no {suffix} file, so a run that "
            f"writes two cannot be scored")


def test_a_tail_of_the_named_file_is_not_the_named_file():
    """`p.name in prompt` refused a run that produced the right deliverable.

    A stray `en.html` beside `deck.en.html` made both "named", and the selector
    refused — the FM-13 direction inside the repair for one.
    """
    one, why = run_conformance.scored_file(_paths("deck.en.html", "en.html"), T1)
    assert one is not None, why
    assert one.name == "deck.en.html"


def test_a_task_with_no_prompt_says_so():
    """The diagnosis must name the side that is missing.

    With no prompt every multi-file run refuses, and the message said the
    prompt "names none of" the files — sending a reader to look at the run.
    """
    one, why = run_conformance.scored_file(
        _paths("a.html", "b.html"), {"deliverable": "*.html", "prompt": ""})
    assert one is None
    assert "declares no prompt" in why
