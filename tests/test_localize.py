"""`localize.py` proven able to derive AND to refuse.

The command exists because three validation rounds, on two platforms and two
models, produced Chinese from a wholly English source — and the third one
happened *after* M16 shipped, because M16's record was a boolean the agent typed
on the same command line as the language it was attesting to.

So the tests here are mostly refusals. What the command produces is a copy with
three declarations; what it is FOR is the four things it will not do.
"""
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
LOCALIZE = ROOT / "scripts/ops/localize.py"
PASS = ROOT / "fixtures" / "deck-pass.en.html"


def _run(*args):
    return subprocess.run([sys.executable, str(LOCALIZE), *args],
                          capture_output=True, text=True)


def test_it_derives_and_records_all_three_declarations(tmp_path):
    src = tmp_path / "deck.en.html"
    src.write_text(PASS.read_text(encoding="utf-8"), encoding="utf-8")
    out_path = tmp_path / "deck.zh-Hans.html"
    out = _run(str(src), "--lang", "zh-Hans", "--asked", "请把报告写成中文",
               "--out", str(out_path), "--skip-source-check")
    assert out.returncode == 0, out.stdout + out.stderr
    raw = out_path.read_text(encoding="utf-8")
    assert '<html lang="zh-Hans"' in raw
    assert 'data-lang-asked="zh-Hans"' in raw
    assert 'data-lang-ask-quote="请把报告写成中文"' in raw
    assert 'data-localized-from="deck.en.html"' in raw


def test_it_says_out_loud_what_it_cannot_verify(tmp_path):
    """The one thing that matters is the one thing no script can check, and the
    owner reads this line."""
    src = tmp_path / "deck.en.html"
    src.write_text(PASS.read_text(encoding="utf-8"), encoding="utf-8")
    out = _run(str(src), "--lang", "zh-Hans", "--asked", "请把报告写成中文",
               "--out", str(tmp_path / "d.zh.html"), "--skip-source-check")
    assert "No script can verify it came from the user" in out.stdout


def test_a_fragment_is_not_a_quotation(tmp_path):
    src = tmp_path / "deck.en.html"
    src.write_text(PASS.read_text(encoding="utf-8"), encoding="utf-8")
    out = _run(str(src), "--lang", "zh-Hans", "--asked", "zh",
               "--out", str(tmp_path / "d.zh.html"), "--skip-source-check")
    assert out.returncode != 0
    assert "would match anything" in (out.stdout + out.stderr)


def test_it_refuses_to_derive_from_a_red_english_deck(tmp_path):
    """A localized deck inherits every defect of its source and adds a
    translation. This is the precondition the script CAN verify, so it does."""
    src = tmp_path / "deck.en.html"
    src.write_text((ROOT / "fixtures/deck-broken.en.html").read_text(encoding="utf-8"),
                   encoding="utf-8")
    out = _run(str(src), "--lang", "zh-Hans", "--asked", "请把报告写成中文",
               "--out", str(tmp_path / "d.zh.html"))
    assert out.returncode == 1, out.stdout
    assert "does not pass its own checks" in (out.stdout + out.stderr)
    assert not (tmp_path / "d.zh.html").exists()


def test_it_refuses_to_derive_from_a_derivative(tmp_path):
    """Deriving Chinese from Chinese loses the original, which is the artifact
    the default exists to guarantee."""
    src = tmp_path / "deck.zh-Hans.html"
    src.write_text('<html lang="zh-Hans"><body></body></html>', encoding="utf-8")
    out = _run(str(src), "--lang", "ja", "--asked", "日本語でお願いします",
               "--out", str(tmp_path / "d.ja.html"), "--skip-source-check")
    assert out.returncode != 0
    assert "not English" in (out.stdout + out.stderr)


def test_english_is_not_something_to_derive(tmp_path):
    src = tmp_path / "deck.en.html"
    src.write_text(PASS.read_text(encoding="utf-8"), encoding="utf-8")
    out = _run(str(src), "--lang", "en", "--asked", "in English please",
               "--out", str(tmp_path / "d2.en.html"))
    assert out.returncode != 0
    assert "already emits" in (out.stdout + out.stderr)


def test_the_derived_document_passes_m16(tmp_path):
    """End to end: the whole point is that this path is the one that goes
    green, and typing the attribute by hand is the one that does not."""
    src = tmp_path / "deck.en.html"
    src.write_text(PASS.read_text(encoding="utf-8"), encoding="utf-8")
    out_path = tmp_path / "deck.zh-Hans.html"
    _run(str(src), "--lang", "zh-Hans", "--asked", "请把报告写成中文",
         "--out", str(out_path), "--skip-source-check")
    prose = subprocess.run(
        [sys.executable, str(ROOT / "scripts/check/check_prose.py"),
         str(out_path), "--genre", "sales"], capture_output=True, text=True)
    assert "ok    M16_language_asked" in prose.stdout, prose.stdout
