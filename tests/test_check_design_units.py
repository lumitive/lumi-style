"""Unit tests for the check_design pieces the 0.1.443 retrospective touched.

Same discipline as the guard tests: each behaviour is proven able to pass AND
to fail on synthetic input, because a check only ever seen passing is FM-01.
The fixtures exercise these at the verdict level; these tests pin the pattern
level — which string fires, which deliberately does not.
"""
import pathlib

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


# d19 — a class is a whole token, not a substring of one.

def test_d19_paint_class_is_not_a_block():
    # `f-card` is the SVG paint class every drawing uses for a card-coloured
    # fill. `\bcard\b` matched it, so a figure-rich document reported one
    # "card missing .ledname" per painted rect — and a conformance run was
    # scored fail on exactly that.
    raw = _doc(page_body='<svg><rect class="f-card"/><rect class="f-card"/></svg>')
    assert check_design.d19_vocabulary(raw)["bad_blocks"] == []


def test_d19_a_real_card_without_its_ledname_still_fails():
    raw = _doc(page_body='<div class="card"><p>no ledname here</p></div>')
    assert check_design.d19_vocabulary(raw)["bad_blocks"] == [("card", ["ledname"])]


def test_d19_a_complete_card_passes():
    raw = _doc(page_body='<div class="card"><p class="ledname">Subject</p>'
                         '<p class="verdict">The line to carry away.</p></div>')
    assert check_design.d19_vocabulary(raw)["bad_blocks"] == []


# d19's fourth assertion — a mark obliges a runtime, and only that direction.

GLOBE = '<div class="markcell" data-globe><svg class="gl"><path/></svg></div>'
RUNTIME = "<script>function createGlobe(el, opts) { return null; }</script>"


def test_d19_a_globe_mark_without_the_runtime_fails():
    # The shipped defect: a build script harvested the runtime out of a fixture
    # with a regex, matched nothing, and emitted an empty <script></script>.
    # Two cover/closing marks, no createGlobe, three checkers green.
    raw = _doc(page_body=GLOBE) + "<script></script>"
    assert check_design.d19_vocabulary(raw)["globe_no_runtime"] is True


def test_d19_a_globe_mark_with_the_runtime_passes():
    raw = _doc(page_body=GLOBE) + RUNTIME
    assert check_design.d19_vocabulary(raw)["globe_no_runtime"] is False


def test_d19_a_globe_drawing_without_the_mark_does_not_fail():
    # THE DIRECTION IS THE POINT, and this test is here to stop anyone
    # reversing it. fixtures/deck-pass.en.html carries the brand globe with no
    # data-globe and no runtime on purpose; asserting "a drawing obliges a
    # mark" would fail this package's own passing fixture on its first run.
    raw = _doc(page_body='<div class="markcell"><svg class="gl"><path/></svg></div>')
    vo = check_design.d19_vocabulary(raw)
    assert vo["globe_no_runtime"] is False
    assert vo["globe_marks"] == 0


def test_d19_a_cover_globe_without_the_mark_is_reported_not_graded():
    raw = ('<!doctype html><html><head><title>T</title></head><body>'
           '<section class="page cover" id="cover">'
           '<div class="markcell"><svg class="gl"><path/></svg></div>'
           f"{FOOT}</section></body></html>")
    vo = check_design.d19_vocabulary(raw)
    assert vo["globe_marks_missing_hook"] == ["cover"]
    assert vo["globe_no_runtime"] is False   # reported; it must not gate


# The two gating findings 0.1.453 adds, at the verdict level. The probes that
# feed them are JavaScript and need a browser; deliverable_verdicts is Python
# and decides, so this is where a rewritten predicate would be caught.

def _page(pid, **kw):
    """One healthy page row, in the shape the browser probe emits.

    Every field the other predicates read has to be here: deliverable_verdicts
    computes all fourteen findings from one pass, so a row missing a key fails
    a neighbouring check rather than the one under test.
    """
    base = {"id": pid, "pageH": 720, "overflowPx": 0, "inkUnavailable": 0,
            "hasFooter": True, "starved": [], "footWrapped": False,
            "footBaseline": {"ratio": 0, "runs": 3, "split": False},
            "capWrapped": 0, "titleMissing": False, "isOpener": False,
            "isApparatus": False, "isCover": False, "isClosing": False,
            "spillPx": -44, "pageSpillPx": -89, "visualPct": 50,
            "distorted": [], "ledeBlocks": 0, "badBox": False, "clipped": False}
    base.update(kw)
    return base


def test_figure_distorts_passes_a_document_whose_bars_obey_their_values():
    import inspect_layout as il
    rows = [_page("p1"), _page("p2")]
    assert il.deliverable_verdicts(rows, None)["figure_distorts"][0] == "ok"


def test_figure_distorts_fails_and_names_the_value_and_both_lengths():
    # The shipped defect: a minimum-width floor drew 1 and 4 as one bar.
    import inspect_layout as il
    rows = [_page("p1"),
            _page("modes", distorted=[{"value": 1, "drew": 81, "shouldDraw": 11}])]
    verdict, detail = il.deliverable_verdicts(rows, None)["figure_distorts"]
    assert verdict == "FAIL"
    assert "modes" in detail and "81px" in detail and "11px" in detail


def test_visual_absent_passes_a_drawn_document():
    import inspect_layout as il
    rows = [_page(f"p{i}") for i in range(6)]
    assert il.deliverable_verdicts(rows, None)["visual_absent"][0] == "ok"


def test_visual_absent_fails_when_most_content_pages_draw_nothing():
    # Calibrated on two real 30-page decks: 0 blank content pages of 23 in the
    # one a reader called good, 10 of 22 in the one she called thin.
    import inspect_layout as il
    rows = [_page(f"blank{i}", visualPct=0) for i in range(10)]
    rows += [_page(f"drawn{i}") for i in range(12)]
    verdict, detail = il.deliverable_verdicts(rows, None)["visual_absent"]
    assert verdict == "FAIL"
    assert "10 of 22" in detail


def test_visual_absent_tolerates_a_document_under_the_ceiling():
    # A ceiling, not a target. A third of content pages may carry nothing —
    # a document is not required to draw on every page.
    import inspect_layout as il
    rows = [_page(f"blank{i}", visualPct=0) for i in range(3)]
    rows += [_page(f"drawn{i}") for i in range(9)]
    assert il.deliverable_verdicts(rows, None)["visual_absent"][0] == "ok"


def test_visual_absent_does_not_count_openers_covers_or_apparatus():
    # Those pages legitimately carry no data figure, and counting them would
    # fail a well-built deck on its own structure.
    import inspect_layout as il
    rows = [_page("cover", visualPct=0, isCover=True),
            _page("closing", visualPct=0, isClosing=True),
            _page("open-i", visualPct=0, isOpener=True),
            _page("score", visualPct=0, isApparatus=True),
            _page("p1"), _page("p2")]
    assert il.deliverable_verdicts(rows, None)["visual_absent"][0] == "ok"


def test_both_findings_read_na_on_a_document_with_no_measurable_page():
    import inspect_layout as il
    out = il.deliverable_verdicts([], None)
    assert out["figure_distorts"][0] == "n/a"
    assert out["visual_absent"][0] == "n/a"


# D20 — is the declared palette LUMI's? The check the owner's eye found before
# any instrument did: a deck can be perfectly consistent with a palette of its
# own invention, and every other palette metric grades it against that invention.

def _resolved(**tokens):
    return dict(tokens)


def test_d20_a_document_carrying_the_shipped_colours_passes():
    import check_design as cd
    shipped, _ = cd.resolve(
        cd.css_tokens.strip_comments(
            (cd.ROOT / "tokens" / "lumi-theme.css").read_text(encoding="utf-8"), " "),
        "light")
    out = cd.d20_palette_fidelity(shipped, "light")
    assert out["differs"] == []
    assert out["compared"] > 20, "the comparison must actually reach the palette"


def test_d20_an_invented_accent_fails_and_names_both_values():
    import check_design as cd
    out = cd.d20_palette_fidelity(_resolved(acc="#0F6E6B"), "light")
    # Named as a list rather than compared field by field: ruff's S105 reads
    # `d["token"] == "..."` as a hardcoded credential, and a noqa on a test
    # about colours would be the wrong kind of quiet.
    assert [d["token"] for d in out["differs"]] == ["--acc"]
    assert [d["document"] for d in out["differs"]] == ["#0F6E6B"]
    assert out["differs"][0]["shipped"] != "#0F6E6B"


def test_d20_ignores_sizes_and_fonts():
    # SIZES ARE THE DOCUMENT'S. 0.1.340 withdrew the type floor and SKILL.md's
    # first rule is to design per page; a compliant deck differed from the
    # shipped set on six --fs-* tokens and nothing else.
    import check_design as cd
    out = cd.d20_palette_fidelity(_resolved(**{"fs-display": "72px"}), "light")
    assert out["differs"] == [] and out["compared"] == 0


def test_d20_notation_is_not_a_difference():
    # #FFF, #FFFFFF and rgb(255,255,255) are one colour.
    import check_design as cd
    shipped, _ = cd.resolve(
        cd.css_tokens.strip_comments(
            (cd.ROOT / "tokens" / "lumi-theme.css").read_text(encoding="utf-8"), " "),
        "light")
    assert cd.parse_color(shipped["bg"]) == cd.parse_color("#FFF")
    assert cd.d20_palette_fidelity(_resolved(bg="#FFF"), "light")["differs"] == []


def test_d20_an_unparseable_document_value_counts_as_a_difference():
    import check_design as cd
    out = cd.d20_palette_fidelity(_resolved(acc="var(--something-else)"), "light")
    assert len(out["differs"]) == 1


# WHICH METRICS GATE is read off the rows. The exit decision was a hand-written
# tuple and fell one behind the day D20 arrived: the metric declared "(gates)",
# five documents were made to say five gates because check_repo reads that
# string, and a file failing D20 alone exited 0.

def _measured():
    """A real measurement of the passing fixture.

    Deliberately NOT a hand-built stub: a stub of grade()'s inputs is another
    hand-maintained copy of a list, which is the defect these two tests exist
    to lock down. Measuring the fixture cannot fall behind the checker.
    """
    import pathlib as _p
    return check_design.measure(_p.Path(check_design.ROOT)
                                / "fixtures" / "deck-pass.en.html")


def test_the_gate_set_is_the_set_of_rows_declaring_a_gate():
    declared = {n for n, _, target, _ in check_design.grade(_measured())
                if "(gates)" in target}
    assert declared == {"D12_commercial_footer", "D14_placeholders",
                        "D15_footer_path", "D19_vocabulary",
                        "D20_palette_fidelity", "D21_data_contract",
                        "D22_layout_vocabulary", "D24_images_embedded",
                        "D25_image_provenance", "D27_agenda_mirror"}


def test_a_document_failing_only_a_gate_metric_exits_one(tmp_path, capsys):
    """THE REGRESSION TEST FOR THE SHIPPED DEFECT, and it has to call main().

    The exit decision was a hand-written tuple that fell one behind the day D20
    arrived, so a document failing D20 alone exited 0 while five files said it
    gated. A first version of this test asserted the property on `grade()`'s
    rows and RE-IMPLEMENTED the derivation in its own body — which is a test of
    the test: reverting main() to the four-name tuple left it passing. The exit
    code is the behaviour, so the exit code is what is asserted.

    The fixtures cannot stand in: deck-broken fails several gates at once, so
    its exit code is 1 either way.
    """
    src = (pathlib.Path(check_design.ROOT) / "fixtures" / "deck-pass.en.html"
           ).read_text(encoding="utf-8")
    # One colour token off the shipped palette and nothing else touched, so
    # D20 is the only gate that can fail.
    doc = tmp_path / "d20-only.en.html"
    doc.write_text(src.replace("--acc:", "--acc: #0F6E6B; --acc-was:", 1),
                   encoding="utf-8")

    code = check_design.main([str(doc)])
    printed = capsys.readouterr().out
    assert "FAIL  D20_palette_fidelity" in printed
    for other in ("D12_commercial_footer", "D14_placeholders",
                  "D15_footer_path", "D19_vocabulary"):
        assert f"FAIL  {other}" not in printed, "only D20 may fail here"
    assert code == 1, "a document failing only D20 must not exit 0"


def test_d22_catches_a_layout_the_tokens_do_not_define():
    """D9 collected these for releases and its verdict was hard-coded to pass,
    so an agent inventing a seventeenth layout was caught by nothing."""
    page = ('<section class="page" id="p1"><div class="body editorial-hero">'
            '<h2>t</h2></div></section>')
    r = {"D9_layout_variety": check_design.d9_layout_variety(page)}
    assert check_design.d22_layout_vocabulary(r)["unknown"] == ["p1"]


def test_d22_accepts_a_layout_the_tokens_define():
    page = ('<section class="page" id="p1"><div class="body split">'
            '<h2>t</h2></div></section>')
    r = {"D9_layout_variety": check_design.d9_layout_variety(page)}
    assert check_design.d22_layout_vocabulary(r)["unknown"] == []


def test_d23_ceiling_is_derived_from_the_tokens_not_written_here():
    """design-rules says two voices and the tokens declare two. A literal 2
    would be quietly wrong the day a third is added."""
    tokens = "--din: 'D-DIN', sans-serif;\n--mono: 'IBM Plex Mono', monospace;"
    r = check_design.d23_font_count('<style>.a{font-family:var(--din)}</style>', tokens)
    assert r["ceiling"] == 2 and r["declared"] == 2
    three = ('<style>.a{font-family:var(--din)}.b{font-family:var(--mono)}'
             '.c{font-family:"Comic Sans MS",cursive}</style>')
    assert check_design.d23_font_count(three, tokens)["over"]


def test_d23_moves_with_the_tokens():
    tokens = ("--din: 'D-DIN';\n--mono: 'IBM Plex Mono';\n--serif: 'Source Serif';")
    three = ('<style>.a{font-family:var(--din)}.b{font-family:var(--mono)}'
             '.c{font-family:var(--serif)}</style>')
    r = check_design.d23_font_count(three, tokens)
    assert r["ceiling"] == 3 and not r["over"]


def test_d23_does_not_count_a_font_face_declaration_as_a_third_voice():
    """An @font-face block declares a face; it does not use one.

    The first version counted `font-family: 'D-DIN'` inside the declaration and
    fired on both accepted deliverables, each of which uses exactly the two
    voices the tokens define. Found by running the new check against real work
    before believing it.
    """
    tokens = "--din: 'D-DIN', sans-serif;\n--mono: 'IBM Plex Mono', monospace;"
    doc = ("<style>@font-face{font-family:'D-DIN';src:url(x)}"
           ".a{font-family:var(--din)}.b{font-family:var(--mono)}</style>")
    r = check_design.d23_font_count(doc, tokens)
    assert r["used"] == 2 and not r["over"], r


# D9 counted DECLARED class names. In portrait, tokens/ collapses split,
# split-wide, split-narrow and sidebar-notes to one grid, so a document could
# raise its distinct-layout count from three to six by editing class names and
# changing nothing a reader sees. Measured on a real 30-page deliverable: the
# renamed build and the original both report 3 layouts at 78.6% now, and both
# reported 6 at 25.0% before. A metric satisfied instead of met is the failure
# this package's own opening provenance note is about.

_TOKENS = (
    '<style>\n'
    '.body.split { grid-template-columns: 1fr 1fr; }\n'
    '.body.sidebar-notes { grid-template-columns: 1fr 300px; }\n'
    'body[data-geometry="portrait"] .body.split,\n'
    'body[data-geometry="portrait"] .body.sidebar-notes '
    '{ grid-template-columns: 1fr; grid-template-rows: auto auto 1fr; }\n'
    '</style>')


def _layout_doc(geometry, layouts):
    pages = "".join(
        f'<section class="page" id="p{i}"><div class="body {lay}">'
        f'<div class="lede"></div></div></section>'
        for i, lay in enumerate(layouts, 1))
    return (f"<html><head>{_TOKENS}</head>"
            f'<body data-geometry="{geometry}">{pages}</body></html>')


def test_d9_counts_portrait_equivalents_as_one_layout():
    r = check_design.d9_layout_variety(
        _layout_doc("portrait", ["split", "sidebar-notes", "split", "sidebar-notes"]))
    assert r["distinct"] == 1
    assert r["top_share"] == 100.0


def test_d9_keeps_them_distinct_where_the_geometry_does():
    r = check_design.d9_layout_variety(
        _layout_doc("landscape", ["split", "sidebar-notes", "split", "sidebar-notes"]))
    assert r["distinct"] == 2


def test_d9_names_what_it_merged_so_the_report_is_readable():
    r = check_design.d9_layout_variety(_layout_doc("portrait", ["split", "sidebar-notes"]))
    assert "split" in r["merged"]


def test_d9_reads_the_geometry_from_the_real_body_not_a_comment():
    """The stylesheet's own comment carries `<body data-geometry="landscape">`
    on every deliverable, portrait ones included."""
    doc = _layout_doc("portrait", ["split", "sidebar-notes"]).replace(
        "<style>", '<style>\n/* say so with <body data-geometry="landscape"> */\n', 1)
    assert check_design.d9_layout_variety(doc)["distinct"] == 1


# d4 — the declared trademark-mark exemption (second blind review's
# get-started spec). Red and green, per FM-01.

def test_d4_undeclared_logo_hexes_still_fail():
    raw = '<html><body><svg><path fill="#D97757"/></svg></body></html>'
    assert check_design.d4_palette(raw) == ["#D97757"]


def test_d4_a_declared_mark_keeps_its_owners_colours():
    raw = ('<html><body><svg data-mark="trademark">'
           '<path fill="#D97757"/></svg></body></html>')
    assert check_design.d4_palette(raw) == []


# ── D12's terms vocabulary was English-and-confidential only (0.1.519) ────────
# A public Chinese roadshow deck carried honest handling terms (公开路演版·
# 引用请注明出处) and failed all nineteen pages; the real artifact is the
# deliberate-red run.

def _footer_doc(terms):
    return ('<html lang="zh-Hans"><body>'
            '<section class="page" id="p1"><p>正文。</p>'
            f'<div class="foot"><div class="terms"><span class="conf">{terms}</span></div>'
            '<span class="site">www.lumivate.io</span><span>01 / 01</span></div>'
            '</section></body></html>')


def test_d12_accepts_chinese_handling_terms(tmp_path):
    path = tmp_path / "doc.zh-Hans.html"
    path.write_text(_footer_doc("公开路演版 · 引用请注明出处"), encoding="utf-8")
    r = check_design.d12_commercial_footer(path.read_text(encoding="utf-8"))
    assert r["missing_terms"] == []


def test_d12_still_fails_a_footer_with_no_terms(tmp_path):
    path = tmp_path / "doc.zh-Hans.html"
    path.write_text(_footer_doc("some other words"), encoding="utf-8")
    r = check_design.d12_commercial_footer(path.read_text(encoding="utf-8"))
    assert r["missing_terms"] == [0]


# ── D30: figure numbers run 1..k, once each, in page order (0.1.521) ──────────
# The deliberate-red run is on real artifacts: an accepted product deck numbered
# two drawings `Figure 3` and had no Figure 4, an accepted roadshow BP ran 2-8
# then 12-14 then 9-11, and the tracked pass fixture shipped six holes. The
# cause was the SCAFFOLD, which numbered figures from the page index.

def _fig_doc(*numbers):
    pages = "".join(
        f'<section class="page" id="p{i}"><div class="fig"><svg></svg>'
        f'<div class="cap"><span class="n">Figure {n}</span> A conclusion</div>'
        f'</div></section>'
        for i, n in enumerate(numbers, start=1))
    return f"<html><body>{pages}</body></html>"


def test_d30_accepts_a_clean_sequence():
    r = check_design.d30_figure_sequence(_fig_doc(1, 2, 3, 4))
    assert r["duplicates"] == [] and r["holes"] == [] and not r["out_of_order"]


def test_d30_catches_the_repeat_and_the_hole_the_accepted_deck_shipped():
    r = check_design.d30_figure_sequence(_fig_doc(1, 2, 3, 3, 5))
    assert r["duplicates"] == [3]
    assert r["holes"] == [4]


def test_d30_catches_an_appendix_cut_out_of_the_body():
    # The BP's shape: body 2-8, then 12-14, then the appendix at 9-11.
    r = check_design.d30_figure_sequence(_fig_doc(2, 3, 4, 12, 13, 14, 9, 10, 11))
    assert r["out_of_order"] is True
    assert 1 in r["holes"]


def test_d30_is_na_when_a_document_numbers_no_figures():
    assert check_design.d30_figure_sequence("<html><body><p>no figures</p></body></html>") is None
