"""D24 and D25: an image ships inside the file, and it names its terms.

Both opened at 0.1.493 when the owner lifted the imagery restriction. The old
clause read "without a professional photo library, never set text directly on
imagery" — a CONDITION that had been read as a ban and applied to every kind of
image, which is convention 5's failure recorded in convention 5's own words.
Lifting it needs the two things that make imagery safe to ship rather than an
apology for having banned it.
"""
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "check"))
sys.path.insert(0, str(ROOT / "scripts" / "lib"))

import check_design  # noqa: E402

PIX = "data:image/gif;base64,R0lGODlhAQABAAAAACw="


def _doc(*body):
    return ('<!doctype html><html lang="en"><body>' + "".join(body) + "</body></html>")


# ---- D24 · embedded, never linked -----------------------------------------

@pytest.mark.parametrize("markup", [
    '<img src="https://example.com/a.png" alt="x">',
    '<img src="./local/a.png" alt="x">',
    '<image href="https://cdn.example.com/b.svg"/>',
    '<image xlink:href="//cdn.example.com/c.png"/>',
    '<div style="background:url(https://cdn.example.com/d.jpg)"></div>',
])
def test_a_linked_image_fails(markup):
    got = check_design.d24_images_embedded(_doc(markup))
    assert got["external"], f"a linked image passed: {markup}"


@pytest.mark.parametrize("markup", [
    f'<img src="{PIX}" alt="x">',
    '<use href="#shape-x"/>',            # an internal reference is not a request
    '<div style="background:url(data:image/gif;base64,AA)"></div>',
])
def test_an_embedded_or_internal_reference_passes(markup):
    assert check_design.d24_images_embedded(_doc(markup))["external"] == []


# ---- D25 · the terms are named --------------------------------------------

def test_an_image_with_no_terms_fails():
    got = check_design.d25_image_provenance(_doc(f'<img src="{PIX}" alt="x">'))
    assert got["rasters"] == 1 and not got["licence_named"]


@pytest.mark.parametrize("terms", [
    "public domain", "CC0", "CC BY 4.0", "CC-BY-SA", "Unsplash",
    "used under a research licence", "own work", "screenshot of the console",
])
def test_named_terms_pass(terms):
    got = check_design.d25_image_provenance(
        _doc(f'<img src="{PIX}" alt="x">', f'<p class="colophon">Plate: {terms}</p>'))
    assert got["licence_named"], f"{terms!r} was not recognised as naming terms"


def test_a_document_with_no_images_passes_rather_than_reading_na():
    """check_design treats an unmeasurable GATE as a failure on purpose. Applied
    to an optional element that would fail every text-and-vector deliverable
    this package has produced, so absence has to be a pass and say so."""
    got = check_design.d25_image_provenance(_doc("<p>no pictures here</p>"))
    assert got["rasters"] == 0 and got["licence_named"]


def test_a_vague_gesture_is_not_naming_terms():
    """The sentence that gets written when nobody checked."""
    got = check_design.d25_image_provenance(
        _doc(f'<img src="{PIX}" alt="x">',
             '<p class="colophon">All imagery used appropriately.</p>'))
    assert not got["licence_named"]


def test_both_gate_and_say_so_in_their_target():
    """The `(gates)` string is check_design's only authority on what gates, and
    the `gating claims` guard reads it. A gate whose target does not say so is
    the contradiction that exited non-zero for two releases with M13."""
    src = (ROOT / "scripts" / "check" / "check_design.py").read_text(encoding="utf-8")
    for metric in ("D24_images_embedded", "D25_image_provenance"):
        i = src.index(f'rows.append(("{metric}"')
        assert "(gates)" in src[i:i + 400], f"{metric} does not declare that it gates"
