"""The PowerPoint export: one full-bleed page raster per slide.

The file it writes is a real OOXML package, so the tests below open it as one —
a zip whose every XML part parses, with a slide and an image per page. What
they cannot do is open PowerPoint, so the assertions are about the package's
structure and about the two refusals that decide whether a wrong deck ships.
"""
import xml.dom.minidom as minidom
import zipfile

import export_pptx

# A one-pixel PNG. The bytes are the content; nothing here reads them.
PIXEL = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010802000000907753"
    "de0000000c4944415408d763f8cfc0000003010100189dd0e10000000049454e"
    "44ae426082")


def _pngs(tmp_path, n):
    out = []
    for i in range(1, n + 1):
        p = tmp_path / f"p{i:02d}.png"
        p.write_bytes(PIXEL)
        out.append(p)
    return out


def test_every_part_of_the_package_parses(tmp_path):
    target = tmp_path / "deck.pptx"
    export_pptx.build(_pngs(tmp_path, 3), target, "landscape")
    with zipfile.ZipFile(target) as z:
        assert z.testzip() is None
        for name in z.namelist():
            if name.endswith((".xml", ".rels")):
                # The input is a file this test just wrote, so S318's
                # untrusted-XML concern does not apply here.
                minidom.parseString(z.read(name))  # noqa: S318 — self-written
        slides = [n for n in z.namelist() if n.startswith("ppt/slides/slide")]
        media = [n for n in z.namelist() if n.startswith("ppt/media/")]
    assert len(slides) == 3 and len(media) == 3


def test_the_picture_fills_the_slide_exactly(tmp_path):
    """A letterboxed slide is the export reading as a smaller document than the
    one that was composed. The picture's extent is the slide's, both axes."""
    target = tmp_path / "deck.pptx"
    export_pptx.build(_pngs(tmp_path, 1), target, "landscape")
    cx, cy = export_pptx.SLIDE["landscape"]
    with zipfile.ZipFile(target) as z:
        slide = z.read("ppt/slides/slide1.xml").decode()
        pres = z.read("ppt/presentation.xml").decode()
    assert f'<a:ext cx="{cx}" cy="{cy}"/>' in slide
    assert f'<p:sldSz cx="{cx}" cy="{cy}"/>' in pres


def test_portrait_uses_the_a4_slide(tmp_path):
    target = tmp_path / "deck.pptx"
    export_pptx.build(_pngs(tmp_path, 1), target, "portrait")
    with zipfile.ZipFile(target) as z:
        pres = z.read("ppt/presentation.xml").decode()
    cx, cy = export_pptx.SLIDE["portrait"]
    assert f'<p:sldSz cx="{cx}" cy="{cy}"/>' in pres
    assert cy > cx, "portrait is taller than it is wide"


def test_a_missing_raster_fails_and_writes_nothing(tmp_path, monkeypatch, capsys):
    """THE HARD STOP. A deck quietly missing page 7 is the export a reader
    presents from, and nothing downstream can tell a twelve-slide deck built
    from twelve pages from one built from thirteen."""
    doc = tmp_path / "deck.en.html"
    doc.write_text('<html><body data-geometry="landscape">'
                   + "".join(f'<section class="page" id="p{i}"></section>'
                             for i in range(1, 4))
                   + "</body></html>")

    def short_export(path, geometry, scale, png, out_dir, seen, only=None):
        _pngs(out_dir, 2)          # two rasters for three pages
        return 0

    monkeypatch.setattr(export_pptx.export_pdf, "export", short_export)
    rc = export_pptx.main([str(doc), "--out", str(tmp_path)])
    assert rc == 1
    assert "declares 3 pages and 2 raster(s)" in capsys.readouterr().out
    assert not list(tmp_path.glob("*.pptx"))


def test_a_complete_run_writes_one_slide_per_page(tmp_path, monkeypatch, capsys):
    doc = tmp_path / "deck.en.html"
    doc.write_text('<html><head><style>.page { color: red }</style></head>'
                   '<body data-geometry="landscape">'
                   '<!-- <section class="page"> in a comment -->'
                   + "".join(f'<section class="page" id="p{i}"></section>'
                             for i in range(1, 4))
                   + "</body></html>")

    def full_export(path, geometry, scale, png, out_dir, seen, only=None):
        _pngs(out_dir, 3)
        return 0

    monkeypatch.setattr(export_pptx.export_pdf, "export", full_export)
    assert export_pptx.main([str(doc), "--out", str(tmp_path)]) == 0
    assert "3 slides" in capsys.readouterr().out
    written = list(tmp_path.glob("*.pptx"))
    assert len(written) == 1


def test_the_stylesheet_and_the_comments_are_not_pages(tmp_path):
    """Counting either would report a MISSING slide on a complete deck — the
    refusal firing on the document it exists to protect."""
    doc = tmp_path / "d.html"
    doc.write_text('<html><head><style>.page{} section.page{}</style></head>'
                   '<body><!-- <section class="page"> --> '
                   '<section class="page"></section>'
                   '<section class="page opener"></section></body></html>')
    assert export_pptx.page_count(doc) == 2


def test_exporting_the_other_geometry_is_refused(tmp_path, capsys):
    """export_pdf's refusal, for its reason: a deliverable is designed for ONE
    geometry, and exporting the other presents a composition nobody designed."""
    doc = tmp_path / "d.html"
    doc.write_text('<html><body data-geometry="landscape">'
                   '<section class="page"></section></body></html>')
    assert export_pptx.main([str(doc), "--geometry", "portrait"]) == 1
    assert "Build a portrait edition" in capsys.readouterr().out


def test_a_document_with_no_pages_fails(tmp_path, capsys):
    doc = tmp_path / "d.html"
    doc.write_text("<html><body><p>Prose.</p></body></html>")
    assert export_pptx.main([str(doc)]) == 1
    assert "no pages" in capsys.readouterr().out


def test_a_file_that_is_not_there_fails(capsys):
    assert export_pptx.main(["no-such-deck.html"]) == 1
    assert "no such file" in capsys.readouterr().out


def test_the_mail_ceiling_is_a_note_and_not_a_refusal(tmp_path, monkeypatch,
                                                      capsys):
    """The operator may well want the 4K edition for a projector. A tool that
    refuses the thing it was asked for teaches people to work around it."""
    doc = tmp_path / "d.html"
    doc.write_text('<html><body data-geometry="landscape">'
                   '<section class="page"></section></body></html>')

    def one(path, geometry, scale, png, out_dir, seen, only=None):
        _pngs(out_dir, 1)
        return 0

    monkeypatch.setattr(export_pptx.export_pdf, "export", one)
    monkeypatch.setattr(export_pptx, "MAIL_CEILING_MB", 0.0)
    assert export_pptx.main([str(doc), "--out", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "past what most mail systems accept" in out
    assert list(tmp_path.glob("*.pptx")), "the note did not stop the write"


# --- the package is well formed, not merely readable ------------------------

REQUIRED_RELS = {
    "ppt/_rels/presentation.xml.rels": ["slideMaster", "theme", "slide"],
    "ppt/slides/_rels/slide1.xml.rels": ["image", "slideLayout"],
    "ppt/slideLayouts/_rels/slideLayout1.xml.rels": ["slideMaster"],
    "ppt/slideMasters/_rels/slideMaster1.xml.rels": ["slideLayout", "theme"],
}


def test_every_part_declares_the_relationships_the_format_requires(tmp_path):
    """The defect this is written from: every slide shipped with only its
    image, and PowerPoint answers a slide part with no `slideLayout`
    relationship with the "found a problem with content" repair prompt.

    It went out called verified, because the instrument used — a library that
    opens the package and reports its slides and their size — resolves that
    relationship lazily and never raised. The claim was true about what was
    measured and silent about what was not."""
    target = tmp_path / "deck.pptx"
    export_pptx.build(_pngs(tmp_path, 2), target, "landscape")
    with zipfile.ZipFile(target) as z:
        for part, kinds in REQUIRED_RELS.items():
            rels = z.read(part).decode()
            for kind in kinds:
                assert f"/relationships/{kind}" in rels, \
                    f"{part} declares no {kind} relationship"


def test_every_slide_carries_its_layout_not_only_the_first(tmp_path):
    target = tmp_path / "deck.pptx"
    export_pptx.build(_pngs(tmp_path, 4), target, "landscape")
    with zipfile.ZipFile(target) as z:
        for i in range(1, 5):
            rels = z.read(f"ppt/slides/_rels/slide{i}.xml.rels").decode()
            assert "/relationships/slideLayout" in rels, f"slide {i}"


def test_the_landscape_slide_is_the_widescreen_size_a_reader_expects(tmp_path):
    """LITERAL NUMBERS, not the module's own constant. The mutation review set
    `SLIDE["landscape"]` to a 4:3 box and both size tests stayed green, because
    each read the value it was asserting — the deck would have opened 4:3 with
    every 16:9 raster stretched across it."""
    target = tmp_path / "deck.pptx"
    export_pptx.build(_pngs(tmp_path, 1), target, "landscape")
    with zipfile.ZipFile(target) as z:
        pres = z.read("ppt/presentation.xml").decode()
    # 13.333 x 7.5 inches at 914400 EMU per inch, which is 16:9.
    assert '<p:sldSz cx="12191970" cy="6858000"/>' in pres
    assert abs(12191970 / 6858000 - 16 / 9) < 0.001


def test_the_portrait_slide_is_a4(tmp_path):
    target = tmp_path / "deck.pptx"
    export_pptx.build(_pngs(tmp_path, 1), target, "portrait")
    with zipfile.ZipFile(target) as z:
        pres = z.read("ppt/presentation.xml").decode()
    assert '<p:sldSz cx="7560000" cy="10692000"/>' in pres
