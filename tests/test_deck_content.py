"""The content interface, and every refusal that makes it one.

Each test below is a defect the scaffold used to let through silently, because
the author's only interface to the words was regex surgery on emitted markup.
A refusal here is an INPUT SHAPE, not a gate: the deck cannot be built from
content that fails one, so none of them can be satisfied by adding a token.
"""
import json
import pathlib
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


# --- a field the schema accepts is a field something renders ----------------

def test_every_accepted_page_field_is_read_by_the_scaffold():
    """THE GENERAL FORM OF THE DEFECT, and the reason this test exists rather
    than one more case. `blocks` sat in `PAGE_FIELDS` for a release and was
    read by nothing: a page carrying it built cleanly and the words never
    reached the reader. That is the `titel` failure in `_keys`' own docstring,
    committed by the module written to refuse it — and no test could see it,
    because every other test asserts about a field that IS rendered.

    Holding the schema to its consumer catches the next one on the day it is
    added instead of on the day a reader notices something missing."""
    src = pathlib.Path("scripts/ops/new_deck.py").read_text(encoding="utf-8")
    unread = [f for f in dc.PAGE_FIELDS
              if f'pg.get("{f}")' not in src
              and f'pg["{f}"]' not in src
              and f'"{f}"' not in src.split("def main")[-1]]
    assert not unread, f"accepted and rendered by nothing: {unread}"


def test_a_takeaway_on_a_dense_page_reaches_the_page(tmp_path):
    """It was accepted by the schema and discarded by the dense branch — the
    author's own closing sentence, gone, exit 0, seven times in one deck.

    The first fix was a refusal, and running it against the real content file
    proved the refusal was the wrong half: every page had written one, because
    the outline plans an implication per page and that IS the takeaway. The
    finding is read off the drawing; the takeaway is what the reader does
    about it."""
    obj = json.loads(json.dumps(GOOD))
    obj["pages"][0]["take"] = "TAKEAWAY-SENTINEL"
    path = _write(tmp_path, obj)
    r = subprocess.run(
        [sys.executable, "scripts/ops/new_deck.py", "--no-trace", "--parts", "A",
         "--content", str(path)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert "TAKEAWAY-SENTINEL" in r.stdout
    assert 'class="take"' in r.stdout


def test_a_takeaway_on_a_stack_page_is_fine(tmp_path):
    obj = json.loads(json.dumps(GOOD))
    obj["pages"][0] = {"title": "A page", "take": "What to keep."}
    content, _ = dc.load(_write(tmp_path, obj))
    assert content["pages"][0]["take"] == "What to keep."


# --- look_for: the branch that decides where the look-for line goes ---------

def test_the_look_for_line_becomes_the_support_line_when_there_is_none():
    """A second paragraph row costs 76px of the drawing on every dense page,
    and the drawing is what the layout exists for."""
    assert dc.look_for({"figlead": "Look here."}) == ("Look here.", "")


def test_both_given_stay_separate():
    """Two sentences the author deliberately wrote as two."""
    assert dc.look_for({"sup": "What this is.", "figlead": "Look here."}) \
        == ("What this is.", "Look here.")


def test_neither_given_yields_neither():
    assert dc.look_for({}) == ("", "")


def test_a_finding_with_no_head_is_refused(tmp_path):
    obj = json.loads(json.dumps(GOOD))
    obj["pages"][0]["finds"] = [{"body": "and why"}]
    with pytest.raises(dc.ContentError, match="has no `head`"):
        dc.load(_write(tmp_path, obj))


def test_a_figure_file_holding_no_svg_is_refused(tmp_path):
    obj = json.loads(json.dumps(GOOD))
    obj["pages"][0]["figure"] = "notes.svg"
    path = _write(tmp_path, obj, notes__svg="just some prose, not a drawing")
    content, base = dc.load(path)
    with pytest.raises(dc.ContentError, match="holds no <svg>"):
        dc.figure_svg(base, "notes.svg")


def test_pages_given_as_a_mapping_is_refused(tmp_path):
    """Iterating a mapping walks its KEYS, so the author's pages become a
    handful of garbage strings and the build still exits 0."""
    obj = json.loads(json.dumps(GOOD))
    obj["pages"] = {"one": {"title": "A page"}}
    with pytest.raises(dc.ContentError, match="must be a list"):
        dc.load(_write(tmp_path, obj))
