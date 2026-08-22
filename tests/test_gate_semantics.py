"""What the adversarial review found in the gate semantics themselves.

The split and the guards were the first two halves. This is the third: what a
verdict MEANS, and whether a document can escape one.
"""
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
PASS = ROOT / "fixtures" / "deck-pass.en.html"


def _prose(doc, *args):
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts/check/check_prose.py"), str(doc), *args],
        capture_output=True, text=True)


def _with_cjk(tmp_path, name, declared=True):
    raw = PASS.read_text(encoding="utf-8")
    raw = re.sub(r"(<h2[^>]*>)", r"\1客户在三个月内完成了全部迁移 ", raw, count=1)
    if not declared:
        raw = raw.replace('<html lang="en"', "<html")
    p = tmp_path / name
    p.write_text(raw, encoding="utf-8")
    return p


def test_visible_chinese_fails_a_declared_english_document(tmp_path):
    assert _prose(_with_cjk(tmp_path, "a.en.html")).returncode == 1


def test_deleting_the_language_does_not_buy_an_exemption(tmp_path):
    """The measured escape: one attribute took M12 from FAIL to `n/a`, and
    `check_deliverable` then printed nothing at all. `gate_registry.held`
    settled the same question one field over — an absent stamp must not become
    an exemption, because the cheapest escape would otherwise be to omit the
    line that says what you are."""
    out = _prose(_with_cjk(tmp_path, "b.html", declared=False))
    assert out.returncode == 1, out.stdout
    assert "blind" in out.stdout and "declares no language" in out.stdout


def test_an_undeclared_document_with_no_chinese_is_untouched(tmp_path):
    """It does not GUESS the language. A document with no CJK has nothing for
    M12 to find and is honestly n/a."""
    p = tmp_path / "c.html"
    p.write_text(PASS.read_text(encoding="utf-8").replace('<html lang="en"', "<html"),
                 encoding="utf-8")
    out = _prose(p)
    assert out.returncode == 0
    assert "n/a   M12_visible_cjk" in out.stdout


def test_the_chinese_pair_states_its_real_reason(tmp_path):
    """They came back "too little data: 149 sentences" on a document with 149
    sentences. The true reason is that the document is not Chinese, and the
    register has said so in `na_means` since it shipped."""
    out = _prose(ROOT / "fixtures" / "deck-degenerate.en.html")
    for row in ("M4zh_banned_hits", "M5_zh_punctuation"):
        line = next(x for x in out.stdout.splitlines() if row in x)
        assert "reads Chinese output only" in line, line
        assert "too little data" not in line, line


def _deliverable(doc, *args):
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts/ops/check_deliverable.py"),
         str(doc), "--fast", "--json", *args],
        capture_output=True, text=True)


def test_a_gate_newer_than_the_document_leaves_the_gating_bucket(tmp_path):
    """`since` was cosmetic: the block filed the finding under `not held` and
    the run still failed on it, because the exit was inherited from the
    instrument — which grades against HEAD by construction and knows nothing
    about `since`. The summary then read "exit 1 · 0 gating findings", a
    summary contradicting the block above it."""
    raw = re.sub(r"(<h2[^>]*>)", r"\1[TO FILL] ",
                 PASS.read_text(encoding="utf-8"), count=1)
    old = tmp_path / "old.en.html"
    old.write_text(re.sub(r"lumi-style \d+\.\d+\.\d+",
                          "lumi-style 0.1.360", raw), encoding="utf-8")
    new = tmp_path / "new.en.html"
    new.write_text(raw, encoding="utf-8")

    o = json.loads(_deliverable(old).stdout)
    n = json.loads(_deliverable(new).stdout)
    assert not [g for g in o["gating"] if "D14" in g], o["gating"]
    assert any("D14" in g for g in n["gating"]), n["gating"]
    assert any("D14" in g for g in o["not_held"]), o["not_held"]
