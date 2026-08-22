"""One vocabulary for "which page is the agenda", where there were two.

`check_design._is_agenda_page` matched the id case-insensitively OR any of
`("agenda", "议程", "目录")` in the eyebrow. `inspect_layout`'s probe matched the
id OR the ENGLISH word alone — `/agenda/i`. So a Chinese deck whose agenda page
is named by its eyebrow rather than its id was found by the design checker and
missed by the layout one, which then reported `deck_structure` FAIL — "this deck
has openers and no agenda" — about a deck that has one.

The words are rule DATA for Chinese output, which is what the English-only red
line permits, and they reach the browser as JSON so the probe string stays ASCII.
"""
import json
import pathlib
import subprocess
import sys
import tempfile

import markup
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_the_rule_reads_both_languages():
    assert markup.is_agenda_page("Agenda", "")
    assert markup.is_agenda_page("p2", '<p class="eyebrow">议程</p>')
    assert markup.is_agenda_page("p2", '<p class="eyebrow">目录</p>')
    assert not markup.is_agenda_page("p2", '<p class="eyebrow">Market size</p>')


def test_the_design_checker_reads_the_shared_rule():
    sys.path.insert(0, str(ROOT / "scripts" / "check"))
    import check_design
    assert check_design._is_agenda_page is markup.is_agenda_page
    assert check_design.AGENDA_WORDS is markup.AGENDA_WORDS


def test_the_probe_is_handed_the_words_rather_than_spelling_them():
    """A vocabulary written in two places is a vocabulary that diverges in one
    of them — which is what happened. The probe gets the list substituted in,
    the way ROLE_WEIGHT_SELECTORS already is."""
    src = (ROOT / "scripts" / "check" / "inspect_layout.py").read_text(
        encoding="utf-8")
    assert "__AGENDA_WORDS__" in src, "the probe spells its own vocabulary again"
    assert "json.dumps(list(markup.AGENDA_WORDS))" in src
    assert "/agenda/i.test" not in src, (
        "the English-only regex is back; a Chinese agenda page would be missed")


def _both_checkers(raw):
    with tempfile.TemporaryDirectory() as d:
        doc = pathlib.Path(d) / "zh.en.html"
        doc.write_text(raw, encoding="utf-8")
        des = json.loads(subprocess.run(
            [sys.executable, str(ROOT / "scripts/check/check_design.py"),
             str(doc), "--json"], capture_output=True, text=True).stdout)[0]
        lay = json.loads(subprocess.run(
            [sys.executable, str(ROOT / "scripts/check/inspect_layout.py"),
             str(doc), "--deliverable", "--json", "--no-sheet", "--iterate"],
            capture_output=True, text=True).stdout)
        return des, lay


def test_a_chinese_agenda_page_is_found_by_both_checkers():
    """The measured case. Before this, `deck_structure` failed a deck that has
    an agenda, because the probe could not read the word naming it.

    Skipped where Playwright is absent, which includes CI: `inspect_layout.py`
    renders. The half that CAN run everywhere is above — the probe is handed
    `markup.AGENDA_WORDS` rather than spelling a vocabulary of its own — and it
    is what actually fails if the two readers drift apart again. This one is
    the end-to-end proof, and it belongs to whoever has a browser.
    """
    pytest.importorskip(
        "playwright", reason="inspect_layout.py renders; see SKILL.md's browser step")
    raw = (ROOT / "fixtures" / "deck-pass.en.html").read_text(encoding="utf-8")
    raw = raw.replace('<section class="page" id="agenda">',
                      '<section class="page" id="p2">'
                      '<p class="eyebrow">议程</p>', 1)
    des, lay = _both_checkers(raw)
    assert des["D35_agenda_exclusive"]["found"] == "p2"
    assert lay["verdicts"]["deck_structure"] == "ok", (
        "the layout checker still cannot see a Chinese agenda page")
