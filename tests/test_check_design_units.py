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


# d4 — which blocks this package's tokens actually live in.

def _doc_css(css):
    return f"<html><head><style>{css}</style></head><body>" \
           f'<section class="page" id="p1"><div class="body">x</div>{FOOT}' \
           f"</section></body></html>"


def test_d4_root_tokens_are_not_literals():
    assert check_design.d4_palette(_doc_css(":root { --acc: #48633E; }")) == []


def test_d4_trade_palette_is_a_token_block():
    # region-palette-trade.css declares on `.trade`, not `:root` — the same
    # kind of generated palette as its sibling, and D4 read all fifty of its
    # values as stray literals until 0.1.447.
    css = (".trade { --rg-eu: #5FB0A0; --rg-eu-stroke: #396F64; }\n"
           "body.dark .trade { --rg-eu: #63B6A7; }")
    assert check_design.d4_palette(_doc_css(css)) == []


def test_d4_still_catches_a_literal_outside_the_token_blocks():
    css = ":root { --acc: #48633E; }\n.fig rect { fill: #FF0000; }"
    assert check_design.d4_palette(_doc_css(css)) == ["#FF0000"]


def test_d4_catches_a_literal_in_markup_too():
    raw = _doc_css(":root { --acc: #48633E; }").replace(
        "<div class=\"body\">x</div>", '<div class="body"><svg><rect fill="#123456"/></svg></div>')
    assert check_design.d4_palette(raw) == ["#123456"]


def test_d13_chip_must_be_in_the_same_rule():
    # An ancestor providing the backing is not the carve-out: the pairing has
    # to be inseparable from the colour or the check cannot see it.
    css = (".chip { background: var(--on-lime); }\n"
           ".chip span { color: var(--lime); }")
    assert check_design.d13_lime_never_light_text(css, {}, "light")


# inspect_layout's footer-baseline probe: the nulls are not all the same.

def test_footer_baseline_null_is_not_read_as_aligned():
    import inspect_layout as il
    # A single-run footer has nothing to compare — n/a, not clean.
    one_run = [{"hasFooter": True, "footBaseline": {"ratio": None, "runs": 1,
                                                    "split": False}}]
    assert il._footer_misaligned(one_run) == []
    assert il._footer_baseline_gradable(one_run) == []   # n/a, never ok


def test_footer_baseline_split_runs_are_a_finding_not_an_absence():
    import inspect_layout as il
    # Displaced past 0.6 of a line box: no two runs share the first line, the
    # probe can compute no ratio, and reading that as zero is what let a
    # footer 12px out of true report "one line, one baseline".
    split = [{"hasFooter": True, "id": "p3",
              "footBaseline": {"ratio": None, "runs": 3, "split": True}}]
    assert il._footer_misaligned(split) == split
    assert il._footer_baseline_gradable(split) == split


def test_a_wrapped_footer_is_not_also_reported_as_a_baseline_defect():
    import inspect_layout as il
    wrapped = [{"hasFooter": True, "id": "p4", "footWrapped": True,
                "footBaseline": {"ratio": None, "runs": 3, "split": True}}]
    assert il._footer_misaligned(wrapped) == []
