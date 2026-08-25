"""D26 · the reader-visible half of C5, which no checker read until 0.1.502.

`references/eval-rubric.md` specifies a scope note carrying `data-omitted` and
says reader-visible is the whole mechanism. Nothing implemented it, so the only
place an omission could be declared was an outline file — an artifact the
template path never produces. On entry path B, completeness had no instrument
at all.

REPORTED, never gating, and that is a decision with evidence: C5 is
"declarable, never gating" because structural compliance does not predict
quality, and a completeness gate is worth defeating — an author who has to
clear it writes the heading and nothing under it.
"""
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "check"))

import check_design as cd  # noqa: E402

GTM = '<body data-storyline="gtm"><h2>positioning</h2><h2>channel</h2>{extra}</body>'


def _scope(html):
    return cd.d26_declared_scope(html, cd._storyline_of(html))


def test_a_section_neither_covered_nor_declared_is_reported():
    r = _scope(GTM.format(extra=""))
    assert "target customer" in r["missing"]


def test_a_declared_section_is_not_reported_missing():
    r = _scope(GTM.format(
        extra='<p class="scope-note" data-omitted="target segment">Commissioned '
              'separately.</p>'))
    assert "target segment" not in r["missing"]
    assert r["hidden"] == []


@pytest.mark.parametrize("attrs", [
    'style="display:none"', 'style="visibility: hidden"', 'hidden',
    'aria-hidden="true"'])
def test_a_declaration_a_reader_cannot_see_is_reported(attrs):
    """A marker only the checker can read would do nothing but silence the
    checker. That is the one thing this metric refuses."""
    r = _scope(GTM.format(
        extra=f'<p class="scope-note" {attrs} data-omitted="pricing">x</p>'))
    assert "pricing" in r["hidden"]


def test_an_empty_declaration_is_not_a_declaration():
    r = _scope(GTM.format(
        extra='<p class="scope-note" data-omitted="pricing"></p>'))
    assert "pricing" in r["hidden"]


def test_a_document_declaring_no_storyline_is_not_measured_rather_than_passed():
    r = _scope("<body><h2>anything</h2></body>")
    assert r["storyline"] is None and r["missing"] is None


def test_a_storyline_with_no_checklist_says_so_rather_than_reporting_none_missing():
    r = _scope('<body data-storyline="proposal"><h2>x</h2></body>')
    assert r["storyline"] == "proposal" and r["missing"] is None


def test_the_scope_note_class_has_a_rendering_it_can_be_seen_with():
    """A rule may not prescribe an asset the package does not ship."""
    css = (ROOT / "tokens" / "lumi-theme.css").read_text(encoding="utf-8")
    assert ".scope-note" in css


def test_d26_does_not_gate_but_can_fail():
    """Two properties, and the pair is the point. C5 is declarable and never
    gating, so D26 must not appear in the gating set — and a metric that could
    not fail at all would be FM-01, so a fixture has to fail it."""
    r = cd.measure(ROOT / "fixtures" / "deck-broken.en.html")
    rows = {n: (tgt, v) for n, _, tgt, v in cd.grade(r)}
    target, verdict = rows["D26_declared_scope"]
    assert "(gates)" not in target, "C5 is declarable, never gating"
    assert verdict == "FAIL", (
        "deck-broken hides a declaration; a metric only ever seen passing is "
        "the failure mode this repository has shipped three times")


def test_deck_pass_demonstrates_a_declaration_a_reader_meets():
    r = cd.measure(ROOT / "fixtures" / "deck-pass.en.html")
    rows = {n: v for n, _, _, v in cd.grade(r)}
    assert rows["D26_declared_scope"] == "ok"
    assert "pricing" in r["D26_declared_scope"]["declared"]


# 0.1.524: the undeclared count reaches the reader as its own row (D31), and
# one note may declare several absences. The audit found a pitch deck covering
# six of eleven typical sections with nothing declared, D26 "ok", and
# check_deliverable printing "0 graded findings": the mechanism computed the
# list and then dropped it.

def test_one_note_may_declare_several_absences():
    raw = ('<body data-storyline="gtm"><p class="scope-note" '
           'data-omitted="target customer, value proposition; channels">'
           'Three sections are out of scope.</p></body>')
    r = cd.d26_declared_scope(raw, "gtm")
    assert r["declared"] == ["channels", "target customer", "value proposition"]
    assert "target customer" not in r["missing"]


# The D31 row itself is held by check_fixtures: deck-pass declares its six
# absences in one sentence and reads ok; deck-broken carries the same absences
# undeclared and reads FAIL.


# --- the corpus, and what a declaration is for (0.1.600) --------------------
# Two defects at one line. D26 built its corpus with `strip_tags`, which keeps
# what is BETWEEN tags — including a stylesheet's own text — and it consulted
# the whole document before it consulted `declared`, so a scope note covered
# the very sections it declared out of scope. Both were found by reading the
# code during the round-6 retrospective; both reds were planted first.

def test_a_stylesheet_comment_does_not_cover_a_section():
    """The corpus is what a READER meets.

    `markup.reader_text` was written for exactly this at 0.1.594, when a CSS
    comment containing "screenshot of" silenced D25's image-provenance gate. It
    never reached this call site, so a rule about coverage could be satisfied
    by a sentence in a file no reader opens.
    """
    css = ('<style>/* target customer and channel economics are styled '
           'here */</style>')
    r = _scope(GTM.format(extra=css))
    assert "target customer" in r["missing"], (
        "a stylesheet comment covered a section the document never wrote")


def test_a_scope_note_declares_rather_than_covers():
    """The note's own body must not satisfy what the note excludes.

    Otherwise `data-omitted` is decorative: removing the attribute changes
    nothing, because the sentence beneath it already names the section. That is
    FM-01's shape — a branch that has never been load-bearing — sitting inside
    the metric.
    """
    prose = ('<p class="scope-note">This deck states no target customer: it '
             'was commissioned separately.</p>')
    r = _scope(GTM.format(extra=prose))
    assert "target customer" in r["missing"], (
        "prose naming an omission counted as covering it")


def test_the_declaration_is_what_clears_the_section():
    """The counter-red: a real declaration must still clear it."""
    note = ('<p class="scope-note" data-omitted="target customer">This deck '
            'states no target customer: it was commissioned separately.</p>')
    r = _scope(GTM.format(extra=note))
    assert "target customer" not in r["missing"]
    assert "target customer" in r["declared"]


def test_the_report_carries_a_number_the_trace_can_record():
    """D31 could never become an instrument suspect, structurally.

    `trace.py`'s close step records a threshold reading only when the report
    dict carries a key named for the metric — `value = row.get(mid)` — and the
    only key here was `D26_declared_scope`, whose value is a dict. So D31 sat
    at the top of the ledger's failing table with no threshold history at all,
    and "a real weakness, or a bar set wrong" was a question the ledger was
    unable to answer about it in either direction.
    """
    import json
    import subprocess
    import sys
    out = subprocess.run(
        [sys.executable, str(ROOT / "scripts/check/check_design.py"),
         str(ROOT / "fixtures/deck-broken.en.html"), "--json"],
        capture_output=True, text=True, cwd=ROOT)
    row = json.loads(out.stdout)
    row = row[0] if isinstance(row, list) else row
    assert "D31_undeclared_sections" in row, (
        "the report has no key named for D31, so no trace can record its value")
    assert isinstance(row["D31_undeclared_sections"], int), (
        "the value must be a number: trace.py records int/float and nothing else")
