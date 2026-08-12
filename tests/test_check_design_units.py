"""Unit tests for the check_design pieces the 0.1.443 retrospective touched.

Same discipline as the guard tests: each behaviour is proven able to pass AND
to fail on synthetic input, because a check only ever seen passing is FM-01.
The fixtures exercise these at the verdict level; these tests pin the pattern
level — which string fires, which deliberately does not.
"""
import check_design

FOOT = ('<div class="foot"><span class="conf">Confidential</span>'
        '<span class="site">www.example.org</span><span>01 / 02</span></div>')


def _doc(head_extra="", page_body="Fine prose."):
    return (f"<!doctype html><html><head><title>A finished title</title>"
            f"{head_extra}</head><body>"
            f'<section class="page" id="p1"><div class="body">{page_body}'
            f"</div>{FOOT}</section></body></html>")


# d14 — the scaffold's own slots (REPLACE ME, lumi-style VERSION).

def test_d14_clean_document_passes():
    assert check_design.d14_placeholders(_doc()) == []


def test_d14_replace_me_in_the_title_is_found_as_head():
    raw = _doc().replace("A finished title", "REPLACE ME")
    found = check_design.d14_placeholders(raw)
    assert any(f["page"] == "(head)" and "REPLACE ME" in f["text"] for f in found)


def test_d14_unfilled_colophon_version_is_found():
    raw = _doc(page_body='<p class="colophon">Built with lumi-style VERSION.</p>')
    found = check_design.d14_placeholders(raw)
    assert any("lumi-style VERSION" in f["text"] for f in found)


def test_d14_filled_colophon_is_not_a_slot():
    raw = _doc(page_body='<p class="colophon">Built with lumi-style 0.1.443.</p>')
    assert check_design.d14_placeholders(raw) == []


def test_d14_prose_about_replacing_things_is_not_a_slot():
    # Case-sensitive on purpose: the slot is the scaffold's literal output.
    raw = _doc(page_body="Please replace me with a better sentence.")
    assert check_design.d14_placeholders(raw) == []


def test_d14_bracketed_markers_still_fire():
    raw = _doc(page_body="The number is [TO FILL] units.")
    found = check_design.d14_placeholders(raw)
    assert any("[TO FILL]" in f["text"] for f in found)


# d18 — the globe component's own label anchor counts, and its furniture
# classes are not regions.

def _globe(labels=True):
    label = ' data-bloc-label="eu"' if labels else ""
    return (f'<svg class="gl"><path class="rg rg-eu"/>'
            f'<g class="gl-rg-label"{label}><text class="gl-rg-n">EU</text>'
            f'<path class="gl-rg-p"/></g></svg>')


def test_d18_bloc_labelled_region_passes():
    got = check_design.d18_region_labels(_doc(page_body=_globe()))
    assert got is not None and got["unlabelled"] == []


def test_d18_component_furniture_is_not_three_regions():
    got = check_design.d18_region_labels(_doc(page_body=_globe()))
    # gl-rg-label / gl-rg-n / gl-rg-p must not be read as regions named
    # "label", "n" and "p" — the 0.1.443 regex fix.
    assert got["regions"] == 1


def test_d18_unlabelled_region_fails():
    got = check_design.d18_region_labels(_doc(page_body=_globe(labels=False)))
    assert got["unlabelled"] == ["eu"]


# d13 — the lime-on-dark chip carve-out.

def test_d13_bare_lime_text_on_light_fails():
    css = ".limetext { color: var(--lime); }"
    assert check_design.d13_lime_never_light_text(css, {}, "light")


def test_d13_lime_with_its_own_dark_chip_passes():
    css = (".subj { background: var(--on-lime); color: var(--lime); "
           "padding: 0 .16em; }")
    assert check_design.d13_lime_never_light_text(css, {}, "light") == []


def test_d13_chip_must_be_in_the_same_rule():
    # An ancestor providing the backing is not the carve-out: the pairing has
    # to be inseparable from the colour or the check cannot see it.
    css = (".chip { background: var(--on-lime); }\n"
           ".chip span { color: var(--lime); }")
    assert check_design.d13_lime_never_light_text(css, {}, "light")
