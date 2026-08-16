"""M6's label path had no Chinese route, so block length decided the verdict.

English puts the counting noun before the number — "blocks 1-3" — and the
pattern looked there. Chinese puts the measure word after it — "1–5 分" — so no
Chinese enumeration could ever match, and what saved most cases was the
short-block fallback. The consequence: the same phrase was a label in a short
block and an unsourced range in a long one, and M6 fails the run.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "check"))

import check_prose as cp  # noqa: E402

LONG = ("在浏览器里打开每份文档，逐条勾选证据项，再由勾出来的结果给出 1–5 分，"
        "顺序是先勾条目后给分，不是先有印象再找理由，这一段刻意写长以超过阈值。")
SHORT = "给出 1–5 分。"


def _m6(text, lang="zh"):
    p = ROOT / "tests" / "_m6_tmp.md"
    p.write_text(f"# t\n\n{text}\n", encoding="utf-8")
    try:
        r = cp.measure(p, genre="internal", lang=lang)
        return r["M6_unsourced_ranges"], len(r.get("M6_label_enumerations", []))
    finally:
        p.unlink(missing_ok=True)


def test_a_chinese_enumeration_is_a_label_in_a_long_block():
    unsourced, labels = _m6(LONG)
    assert unsourced == 0 and labels == 1


def test_it_was_already_a_label_in_a_short_block():
    """The short-block fallback is what hid the gap."""
    unsourced, _ = _m6(SHORT)
    assert unsourced == 0


def test_block_length_no_longer_changes_the_verdict():
    """The same phrase, two block lengths, one answer."""
    assert _m6(LONG)[0] == _m6(SHORT)[0]


def test_a_real_measured_range_is_still_caught():
    """The fix must not turn M6 off for Chinese: a percentage range with no
    source is exactly what this metric exists for."""
    unsourced, _ = _m6("营收在 62–78% 之间波动，这一段同样写得足够长以越过短块阈值。")
    assert unsourced == 1


def test_measure_words_cover_the_common_counters():
    for phrase in ("2–5 条", "3–4 页", "1–5 分", "2–3 个", "4–6 步"):
        assert cp.COUNTING_NOUN_ZH.match(phrase.split(" ", 1)[1]), phrase
