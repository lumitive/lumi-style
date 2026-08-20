"""The shape library is regenerable from its vendored originals and the
tokens, and --check can go red (GAP-017).
"""
import shutil

import recolor_shapes as rs


def test_the_committed_library_is_a_regeneration():
    done, differs = rs.regenerate(write=False)
    assert done == 206 and differs == []


def test_every_unit_binds_tokens_not_literals():
    out = rs.recolor(rs.SRC / "p002-page2-01.svg")
    assert out and "var(--" in out
    for _name, fallback in rs.RAMP + [rs.INK, rs.COLD_WHITE, rs.LIME]:
        assert fallback.startswith("#")


def test_one_edited_byte_is_caught(tmp_path, monkeypatch):
    out = tmp_path / "shapes"
    shutil.copytree(rs.OUT, out, ignore=shutil.ignore_patterns("source"))
    victim = out / "p002-page2-01.svg"
    victim.write_text(victim.read_text(encoding="utf-8").replace("var(--acc-5", "var(--acc-4", 1),
                      encoding="utf-8")
    monkeypatch.setattr(rs, "OUT", out)
    assert rs.main(["--check"]) == 1
    done, differs = rs.regenerate(write=False)
    assert differs == ["p002-page2-01.svg"]


def test_regenerate_writes_the_difference_back(tmp_path, monkeypatch):
    out = tmp_path / "shapes"
    shutil.copytree(rs.OUT, out, ignore=shutil.ignore_patterns("source"))
    victim = out / "p003-page3-01.svg"
    victim.write_text("broken", encoding="utf-8")
    monkeypatch.setattr(rs, "OUT", out)
    assert rs.main([]) == 0
    assert rs.regenerate(write=False)[1] == []
