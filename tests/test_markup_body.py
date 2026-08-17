"""Where a deliverable's real markup begins.

One sentence in this package's own stylesheet has cost four defects:

    /* ... a document says so with <body data-geometry="landscape"> ... */

It sits hundreds of characters ahead of the real tag, in every deliverable,
and it contains a literal `<body …>` with a literal `data-geometry` value.
Anything reaching for the first match finds the comment — the sprite went into
it at 0.1.492, and D9's geometry lookup read its `landscape` on a portrait
document at 0.1.505, while its author was reading the comment about the first.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "lib"))

import markup  # noqa: E402

DECOY = (
    '<html><head><style>\n'
    '/* a document says so with <body data-geometry="landscape"> */\n'
    '</style></head>\n'
    '<body class="deck" data-geometry="portrait" data-genre="training">\n'
    '<section class="page"></section></body></html>')


def test_a_body_tag_inside_a_style_comment_is_not_the_body():
    assert markup.body_attr(DECOY, "data-geometry") == "portrait"


def test_the_attribute_comes_from_the_real_tag():
    assert markup.body_attr(DECOY, "data-genre") == "training"


def test_a_body_inside_a_script_is_skipped_too():
    html = ('<script>const s = \'<body data-geometry="landscape">\';</script>'
            '<body data-geometry="portrait"></body>')
    assert markup.body_attr(html, "data-geometry") == "portrait"


def test_a_document_with_no_body_reads_none_rather_than_guessing():
    assert markup.body_attr("<div data-geometry='portrait'></div>",
                            "data-geometry") is None


def test_an_undeclared_attribute_is_none():
    assert markup.body_attr(DECOY, "data-storyline") is None


def test_the_real_fixture_reads_its_own_geometry():
    raw = (ROOT / "fixtures" / "deck-pass.en.html").read_text(encoding="utf-8")
    assert markup.body_attr(raw, "data-geometry") == "landscape"
