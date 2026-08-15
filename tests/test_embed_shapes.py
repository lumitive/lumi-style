"""Selective shape embedding: only what a document references.

The library is hundreds of figure units. Inlining it makes every deliverable
megabytes of unused geometry; pasting a shape in by hand bypasses the recolour
layer and lands on D20. This emits the intersection, and nothing else.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "build"))

import embed_shapes as es  # noqa: E402

DOC = ('<!doctype html><html><body>'
       '<svg><use href="#shape-chevron-3"/></svg>'
       '<svg><use href="#shape-chevron-3"/><use href="#shape-funnel-4"/></svg>'
       '</body></html>')


def _library(tmp_path, names=("chevron-3", "funnel-4", "unused-9")):
    lib = tmp_path / "assets" / "shapes"
    lib.mkdir(parents=True)
    for n in names:
        (lib / f"{n}.svg").write_text(
            f'<svg viewBox="0 0 10 10"><path id="{n}" d="M0 0h10v10H0z"/></svg>',
            encoding="utf-8")
    return lib


def test_references_are_deduped_and_ordered(monkeypatch, tmp_path):
    monkeypatch.setattr(es, "LIBRARY", _library(tmp_path))
    assert es.referenced(DOC) == ["chevron-3", "funnel-4"]


def test_only_referenced_shapes_are_embedded(monkeypatch, tmp_path):
    """A library shape nobody used must not travel with the document."""
    monkeypatch.setattr(es, "LIBRARY", _library(tmp_path))
    out = es.apply(DOC)
    assert 'id="shape-chevron-3"' in out
    assert 'id="shape-funnel-4"' in out
    assert "unused-9" not in out


def test_embedding_is_idempotent(monkeypatch, tmp_path):
    monkeypatch.setattr(es, "LIBRARY", _library(tmp_path))
    once = es.apply(DOC)
    assert es.apply(once) == once


def test_a_removed_reference_drops_its_symbol(monkeypatch, tmp_path):
    """The sprite is rebuilt, not appended to: a shape that stopped being used
    stops travelling."""
    monkeypatch.setattr(es, "LIBRARY", _library(tmp_path))
    once = es.apply(DOC)
    trimmed = once.replace('<use href="#shape-funnel-4"/>', "")
    assert "shape-funnel-4" not in es.apply(trimmed)


def test_referencing_a_shape_the_library_lacks_is_refused(monkeypatch, tmp_path):
    """An id resolving to nothing renders as empty space — the failure D19
    exists to catch, refused here rather than shipped."""
    monkeypatch.setattr(es, "LIBRARY", _library(tmp_path))
    try:
        es.apply(DOC.replace("funnel-4", "not-in-library"))
    except FileNotFoundError:
        return
    raise AssertionError("a missing shape was embedded as nothing")


def test_a_document_referencing_no_shapes_is_untouched(monkeypatch, tmp_path):
    monkeypatch.setattr(es, "LIBRARY", _library(tmp_path))
    plain = "<!doctype html><html><body><p>no figures</p></body></html>"
    assert es.apply(plain) == plain
