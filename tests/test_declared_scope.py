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
    assert "target segment" in r["missing"]


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
