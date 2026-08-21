"""What may be deleted from the delivery folder, and what may never be.

The tool's whole authority is `is_render`, so this file is mostly that
function held against the shapes the real folder contains. The case that
matters most is the one the first real run got wrong: two thumbnails under
`_sources/` that a recipe READS were proposed for deletion because they are
PNGs. A raster is a render because of where it is, not only what it is.
"""
import housekeeping as hk


def _touch(path, body="x"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def test_a_page_raster_is_a_render(tmp_path):
    assert hk.is_render(_touch(tmp_path / "deck.en-16x9-hd-light-cover.png"))


def test_a_contact_sheet_is_a_render(tmp_path):
    assert hk.is_render(_touch(tmp_path / "deck.en-sheet-16x9-hd-light.html"))


def test_the_deliverable_itself_is_never_a_render(tmp_path):
    # Every document this package makes is HTML. A rule matching on the suffix
    # alone would propose deleting the work.
    assert not hk.is_render(_touch(tmp_path / "adopting-lumi-style.0.1.515.r2.en.html"))
    assert not hk.is_render(_touch(tmp_path / "deck.dark.en.html"))


def test_a_pdf_is_never_a_render(tmp_path):
    assert not hk.is_render(_touch(tmp_path / "adopting-lumi-style.en-portrait.pdf"))


def test_an_image_under_the_source_tree_is_an_input(tmp_path):
    # THE ONE THE FIRST REAL RUN GOT WRONG. These two exist because a recipe
    # reads them, and the 2026-08-18 cleanup kept them for that reason.
    thumb = _touch(tmp_path / "_sources" / "adopting-16x9" / "thumbs" / "p3.png")
    assert not hk.is_render(thumb)
    assert hk.renders_in(tmp_path) == []


def test_a_sheet_under_the_source_tree_is_also_left_alone(tmp_path):
    # The input-tree test comes first for a reason: it is about the location,
    # so it has to outrank both of the shape tests, not just the raster one.
    sheet = _touch(tmp_path / "_sources" / "x" / "deck.en-sheet-wide-light.html")
    assert not hk.is_render(sheet)


def test_renders_are_listed_newest_first(tmp_path):
    import os
    old = _touch(tmp_path / "a-16x9-light-cover.png")
    new = _touch(tmp_path / "b-16x9-light-cover.png")
    os.utime(old, (1, 1))
    assert hk.renders_in(tmp_path) == [new, old]


def test_a_missing_delivery_folder_is_a_skip_not_a_failure(monkeypatch, tmp_path):
    # CI has no delivery folder. A guard that failed there would be red on every
    # machine that is not the owner's; one that printed ok would be claiming it
    # had looked.
    monkeypatch.setattr(hk.output_dir, "output_dir", lambda: tmp_path / "absent")
    folder, why = hk.resolve_folder()
    assert folder is None and "does not exist" in why
    assert hk.main(["--check"]) == 0


def test_check_fails_when_a_render_is_there(monkeypatch, tmp_path, capsys):
    _touch(tmp_path / "deck.en-16x9-hd-light-cover.png")
    monkeypatch.setattr(hk.output_dir, "output_dir", lambda: tmp_path)
    assert hk.main(["--check"]) == 1
    assert "FAIL" in capsys.readouterr().out


def test_apply_removes_renders_and_leaves_records(monkeypatch, tmp_path):
    raster = _touch(tmp_path / "deck.en-16x9-hd-light-cover.png")
    sheet = _touch(tmp_path / "deck.en-sheet-wide-light.html")
    doc = _touch(tmp_path / "deck.en.html")
    thumb = _touch(tmp_path / "_sources" / "thumbs" / "p1.png")
    monkeypatch.setattr(hk.output_dir, "output_dir", lambda: tmp_path)
    assert hk.main(["--apply"]) == 0
    assert not raster.exists() and not sheet.exists()
    assert doc.exists(), "a deliverable was deleted"
    assert thumb.exists(), "a recipe input was deleted"
