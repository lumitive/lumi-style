"""The content interface, and every refusal that makes it one.

Each test below is a defect the scaffold used to let through silently, because
the author's only interface to the words was regex surgery on emitted markup.
A refusal here is an INPUT SHAPE, not a gate: the deck cannot be built from
content that fails one, so none of them can be satisfied by adding a token.
"""
import json
import subprocess
import sys

import deck_content as dc
import pytest

GOOD = {
    "cover": {"title": "A claim about the", "subject": "subject"},
    "parts": [{"claim": "The transport is finished", "run": "Two pages."}],
    "agenda": [{"run": "Development path"}],
    "pages": [{"title": "A page", "layout": "dense",
               "figlead": "What to look for.",
               "finds": [{"head": "One", "body": "and why", "sem": "built"}]}],
}


def _write(tmp_path, obj, **files):
    for name, body in files.items():
        (tmp_path / name.replace("__", ".")).write_text(body)
    p = tmp_path / "content.json"
    p.write_text(json.dumps(obj))
    return p


def test_a_complete_file_loads(tmp_path):
    obj = json.loads(json.dumps(GOOD))
    obj["pages"][0]["figure"] = "fig.svg"
    content, base = dc.load(_write(tmp_path, obj, fig__svg="<svg></svg>"))
    assert base == tmp_path
    assert content["pages"][0]["figlead"] == "What to look for."


def test_a_typo_in_a_field_name_stops_the_build(tmp_path):
    """The interface reproducing its own defect would be a field the author
    wrote that never reaches the page — silently, exactly as before."""
    obj = json.loads(json.dumps(GOOD))
    obj["pages"][0]["titel"] = "oops"
    with pytest.raises(dc.ContentError, match="'titel'"):
        dc.load(_write(tmp_path, obj))


def test_an_unknown_section_stops_the_build(tmp_path):
    with pytest.raises(dc.ContentError, match="not a section"):
        dc.load(_write(tmp_path, dict(GOOD, apendix=[])))


def test_a_figure_that_is_not_there_stops_the_build(tmp_path):
    """Emitting the placeholder instead puts a finished-looking page in front
    of a reader with the drawing silently missing."""
    obj = json.loads(json.dumps(GOOD))
    obj["pages"][0]["figure"] = "figures/absent.svg"
    with pytest.raises(dc.ContentError, match="not beside"):
        dc.load(_write(tmp_path, obj))


def test_dense_without_findings_stops_the_build(tmp_path):
    obj = json.loads(json.dumps(GOOD))
    obj["pages"][0]["finds"] = []
    with pytest.raises(dc.ContentError, match="gives no\\s+findings"):
        dc.load(_write(tmp_path, obj))


def test_five_findings_stop_the_build(tmp_path):
    obj = json.loads(json.dumps(GOOD))
    obj["pages"][0]["finds"] = [{"head": f"{i}"} for i in range(5)]
    with pytest.raises(dc.ContentError, match="row\\s+holds 4"):
        dc.load(_write(tmp_path, obj))


def test_a_free_text_meaning_stops_the_build(tmp_path):
    """Colour is meaning here: `one colour one meaning` governs data, so there
    is no free-text option and no index-named one."""
    obj = json.loads(json.dumps(GOOD))
    obj["pages"][0]["finds"][0]["sem"] = "teal"
    with pytest.raises(dc.ContentError, match="the meanings are"):
        dc.load(_write(tmp_path, obj))


def test_the_agenda_row_cannot_carry_its_own_claim(tmp_path):
    """D27 holds the agenda to the titles the document carries. An author who
    may write the claim twice writes it twice differently — measured, on the
    first content file built through this interface."""
    obj = json.loads(json.dumps(GOOD))
    obj["agenda"][0]["claim"] = "Something else entirely"
    with pytest.raises(dc.ContentError, match="'claim'"):
        dc.load(_write(tmp_path, obj))


def test_content_with_nowhere_to_go_stops_the_scaffold(tmp_path):
    """Convention 17's measured failure: eleven facts lost between two builds
    of one document, every gate green, nothing to compare against."""
    obj = json.loads(json.dumps(GOOD))
    obj["pages"] = [{"title": f"Page {i}"} for i in range(4)]
    obj["pages"][0] = json.loads(json.dumps(GOOD))["pages"][0]
    path = _write(tmp_path, obj)
    r = subprocess.run(
        [sys.executable, "scripts/ops/new_deck.py", "--no-trace", "--pages", "2",
         "--parts", "A", "--content", str(path)],
        capture_output=True, text=True)
    assert r.returncode != 0
    assert "would be dropped" in r.stderr


def test_pages_defaults_to_what_the_content_carries(tmp_path):
    """An author who says how many pages of content there are has already said
    how many pages the deck has."""
    obj = json.loads(json.dumps(GOOD))
    obj["pages"] = [dict(obj["pages"][0], title=f"Page {i}") for i in range(3)]
    r = subprocess.run(
        [sys.executable, "scripts/ops/new_deck.py", "--no-trace", "--parts", "A",
         "--content", str(_write(tmp_path, obj))],
        capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert r.stdout.count('class="body dense"') == 3
