"""Unit tests for check_prose's M6 classification.

Same discipline as tests/test_check_design_units.py: each behaviour is proven
able to pass AND to fail on synthetic input, because a check only ever seen
passing is FM-01. The fixtures exercise M6 at the verdict level — deck-pass
carries a planted enumeration label, deck-degenerate a real unsourced range —
and these pin the pattern level: which dashed pair is read as a label, which
is not, and why.

The question M6 answers is not "how long is this block". It was, at forty
characters, and that proxy let go twice (FM-13): once for the short label it
was written for, and once against a truthful 61-character sentence in a
shipped deliverable whose author rewrote the sentence to satisfy it.
"""
import pathlib

import check_prose

# Enough prose that `measure` has something to average; M6's window is the
# block, so the padding cannot reach the sentence under test.
PAD = ("<p>The programme ran for two cycles. Crews were briefed each week. "
       "Nothing else about the schedule changed.</p>")


def _measure(tmp_path, sentence, genre="sales"):
    path = tmp_path / "doc.en.html"
    path.write_text(
        f"<html lang='en'><body><section class='page' id='p1'>"
        f"{PAD}<p>{sentence}</p>{PAD}</section></body></html>",
        encoding="utf-8")
    return check_prose.measure(path, genre)


# The counting noun — the pair identifies things rather than measuring them.

def test_m6_a_long_enumeration_label_is_reported_not_counted(tmp_path):
    # The shipped false positive, verbatim. 61 characters, so the old
    # short-block backstop could not reach it, and the author reworded a
    # correct sentence to get past the gate.
    s = "Answer confirmation questions in blocks 1&#8211;3 and cross-region."
    r = _measure(tmp_path, s)
    assert r["M6_unsourced_ranges"] == 0
    assert r["M6_label_enumerations"], "the label must be reported, not silent"


def test_m6_other_counting_nouns_read_the_same_way(tmp_path):
    s = "Read the meters on rows 4&#8211;9 of the schedule and log the result."
    assert _measure(tmp_path, s)["M6_unsourced_ranges"] == 0


# Quantitative context still counts — this branch is first on purpose.

def test_m6_a_percentage_range_still_counts(tmp_path):
    # deck-degenerate's plant. If this stops failing, M6 loses the only
    # fixture that fails it and check_fixtures' coverage report goes red.
    s = "Rural read success runs 62&#8211;78% depending on terrain."
    assert _measure(tmp_path, s)["M6_unsourced_ranges"] == 1


def test_m6_a_counting_noun_does_not_rescue_a_percentage(tmp_path):
    # The order of the tests is the point: quantitative context wins over the
    # noun in front of it, or "pages 10&#8211;20% of target" would walk through.
    s = "Coverage across sites 3&#8211;7 reached 44% before the second cycle."
    assert _measure(tmp_path, s)["M6_unsourced_ranges"] == 1


def test_m6_a_plain_unsourced_range_still_counts(tmp_path):
    # No figure shape, no counting noun, too long for the backstop.
    s = "Volumes ran 12&#8211;18 above the plan across the two regions this year."
    assert _measure(tmp_path, s)["M6_unsourced_ranges"] == 1


# The backstop the counting noun does not cover.

def test_m6_gap_001s_short_label_is_still_exempt(tmp_path):
    # "Plastics (1&#8211;2)." has no counting noun in front of the pair, so it
    # survives only on the short-block backstop. Removing that rule would
    # reopen GAP-001.
    r = _measure(tmp_path, "Plastics (1&#8211;2).")
    assert r["M6_unsourced_ranges"] == 0
    assert r["M6_label_enumerations"]


def test_m6_a_sourced_range_is_never_counted(tmp_path):
    # The metric's actual subject: a range that names where it came from.
    s = "Throughput held at 40&#8211;60 units per shift (source: the meter log)."
    assert _measure(tmp_path, s)["M6_unsourced_ranges"] == 0


# M8's splitter measures sentences, not source lines. Until this fix, a
# physical newline was a sentence boundary, so a long sentence soft-wrapped
# across source lines inside one <p> counted as several short fragments — an
# author had to keep every long sentence on ONE physical line to be measured
# honestly, which is compliance with the instrument rather than the rule.

def _lengths(tmp_path, name, content):
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return check_prose.sentences(check_prose.extract(path)[0])


def test_m8_a_wrapped_sentence_is_one_sentence(tmp_path):
    # 45 words, soft-wrapped across three source lines inside one <p>. The
    # wrap is editor formatting, not punctuation; it must not split.
    words = " ".join(f"word{i}" for i in range(45))
    parts = words.split(" ")
    wrapped = " ".join(parts[:15]) + "\n" + " ".join(parts[15:30]) + "\n" + " ".join(parts[30:]) + "."
    lengths = _lengths(
        tmp_path, "doc.en.html",
        f"<html lang='en'><body><section class='page'><p>{wrapped}</p>"
        f"</section></body></html>")
    assert lengths == [45], f"one 45-word sentence, got {lengths}"


def test_m8_block_boundaries_still_split(tmp_path):
    # Two <p> blocks with no terminal punctuation are still two sentences:
    # the injected block boundary, not the newline, is what separates them.
    lengths = _lengths(
        tmp_path, "doc.en.html",
        "<html lang='en'><body><section class='page'>"
        "<p>four words here now</p><p>four more words here</p>"
        "</section></body></html>")
    assert lengths == [4, 4], f"two 4-word sentences, got {lengths}"


def test_m8_markdown_blank_line_splits_wrap_does_not(tmp_path):
    # A blank line is a paragraph boundary; a single newline is a soft wrap.
    lengths = _lengths(
        tmp_path, "doc.md",
        "one paragraph of five words\n\nanother paragraph of five words\n")
    assert lengths == [5, 5], f"two paragraphs, got {lengths}"
    lengths = _lengths(
        tmp_path, "doc.md",
        "a single sentence wrapped by the editor\nacross two source lines with no break\n")
    assert lengths == [14], f"one wrapped sentence, got {lengths}"


def test_m8_cv_floor_is_050_and_a_035_rhythm_now_fails():
    FIXTURES = pathlib.Path(__file__).resolve().parents[1] / "fixtures"
    """The floor moved 0.35 -> 0.50 at 0.1.508, replayed against the rebuilt
    corpus first, and re-measured after the splitter stopped reading a
    source-line wrap as a sentence boundary: real documents sit 0.639-0.854
    and the degenerate fixture at 0.332, so 0.35 separated nothing real from
    anything. A document whose rhythm sits between the two floors is the case
    the raise exists to catch — uniform enough to read machine-made, and green
    under the old number."""
    import contextlib
    import io
    import json
    with contextlib.redirect_stdout(io.StringIO()) as buf:
        check_prose.main([str(FIXTURES / "deck-degenerate.en.html"), "--json"])
    r = json.loads(buf.getvalue())[0]
    assert r["M8_length_cv"] < 0.50
    assert r["verdicts"]["M8_length_cv"] == "FAIL"
    assert ">=0.50" in r["targets"]["M8_length_cv"]


# ── zh blind spots found on the first real Chinese deliverable (0.1.519) ──────
# Each of these fired on the 2026-08 roadshow build (the first real Chinese
# deliverable) before the fix:
# the deliberate-red run is the real artifact, per convention 15.

def test_title_frame_reads_full_width_colon_and_question():
    # A Chinese colon title read as "plain", so thirteen zh titles counted as
    # one frame and M11 failed a deck whose frames genuinely varied.
    assert check_prose.title_frame("数据分层：只认主数据") == "colon"
    assert check_prose.title_frame("大厂做了怎么办？") == "question"
    assert check_prose.title_frame("Plain assertion title") == "plain"


def test_m8_is_not_measured_for_a_chinese_document(tmp_path):
    # The English word-splitter cannot measure zh sentence rhythm; it measured
    # the Latin fragments instead and failed a Chinese deck at cv 0.23. The
    # module's own design note says M8 stays n/a for Chinese.
    path = tmp_path / "doc.zh-Hans.html"
    body = "".join(f"<p>这是第 {i} 句中文正文，说明一件事。</p>" for i in range(40))
    path.write_text(f"<html lang='zh-Hans'><body><section class='page' id='p1'>"
                    f"{body}</section></body></html>", encoding="utf-8")
    r = check_prose.measure(path, "sales")
    assert r["M8_length_cv"] is None


def test_m2_accepts_a_chinese_source_marker(tmp_path):
    # "来源：Momentum Works" carried the source and was still counted
    # unsourced, because SOURCE_MARKERS was English-only.
    s = "市场规模为 $1,330 亿。来源：行业研究。"
    r = _measure(tmp_path, s)
    assert r["M2_detail"] == []


# ── M15: the prose a content page asks a reader to read (0.1.521) ─────────────
# The exclusions are the metric. A page must not be penalised for carrying the
# title contract's lede, D28's takeaway or D12's footer, and SVG label text is
# what the visual-share rule wants MORE of.

def _prose_page(cls, body):
    return (f'<section class="page {cls}" id="p1"><div class="body">'
            '<div class="lede"><p class="eyebrow">Part A</p>'
            '<h2 class="t">A title of exactly seven words here</h2>'
            '<p class="sup">A support line that is also prose.</p></div>'
            f'<div class="fill">{body}</div>'
            '<p class="take">The line the reader carries away.</p></div>'
            '<div class="foot"><span>01 / 01</span></div></section>')


def test_m15_counts_only_the_prose_beside_the_drawing():
    doc = "<html><body>" + _prose_page("", "<p>alpha beta gamma delta</p>") + "</body></html>"
    r = check_prose.m15_page_prose(doc)
    assert r is not None
    assert r["pages"] == 1
    assert r["median"] == 4          # the lede, take and footer are excluded


def test_m15_ignores_svg_labels_and_the_caption():
    body = ('<p>alpha beta gamma delta</p>'
            '<div class="fig"><svg><text>one two three four five</text></svg>'
            '<div class="cap"><span class="n">Figure 1</span> A conclusion drawn</div></div>')
    doc = "<html><body>" + _prose_page("", body) + "</body></html>"
    r = check_prose.m15_page_prose(doc)
    assert r is not None
    assert r["median"] == 4


def test_m15_skips_covers_closings_and_openers():
    doc = ("<html><body>"
           + _prose_page("cover", "<p>a b c</p>")
           + _prose_page("opener", "<p>d e f</p>")
           + _prose_page("closing", "<p>g h i</p>") + "</body></html>")
    assert check_prose.m15_page_prose(doc) is None


def test_m15_is_na_on_chinese_because_the_unit_does_not_transfer():
    doc = "<html><body>" + _prose_page("", "<p>这是一段中文正文，没有空格。</p>") + "</body></html>"
    assert check_prose.m15_page_prose(doc, is_zh=True) is None
