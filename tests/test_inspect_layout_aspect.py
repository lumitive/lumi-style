"""The aspect probe's target is the document's DECLARED stage.

Until 0.1.524 the call site passed the matrix loop's variable after the loop
had finished, which for a landscape document is its last point — "wide",
1.8:1 — so every correct 16:9 page (1.778:1) read off-shape on every window,
23 of 23, for every landscape deliverable built during the 0.1.521–0.1.522
campaign. aspect_report's own docstring records the first arrival of this bug
(16:9 hard-coded, a portrait handbook failing 30 of 30); this was the second,
from the other direction. The choice is a function now so it can be held here
without a browser.
"""
import inspect_layout


def test_landscape_document_is_held_to_16x9_not_to_the_last_matrix_point():
    assert inspect_layout.aspect_stage(
        "landscape", ["16x9", "16x9-hd", "laptop", "wide"]) == "16x9"


def test_portrait_document_is_held_to_a4():
    assert inspect_layout.aspect_stage("portrait", ["a4", "wide"]) == "a4"


def test_undeclared_document_is_held_to_the_first_point_it_was_run_at():
    assert inspect_layout.aspect_stage(None, ["laptop", "wide"]) == "laptop"
    assert inspect_layout.aspect_stage(None, []) == "16x9"


def test_the_call_site_no_longer_reads_the_loop_variable():
    src = (inspect_layout.__file__ and open(inspect_layout.__file__, encoding="utf-8").read())
    assert "aspect_report(path.as_uri(), dark, geometry)" not in src
    assert "aspect_stage(decl_geo, file_geometries)" in src
