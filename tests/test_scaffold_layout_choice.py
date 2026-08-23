"""The scaffold does not hand every content page the one layout the rule rules out.

`references/storyline-templates.md` states it plainly — "A `split` page gives
the figure half the area ... so it cannot reach this number however the words
are trimmed. A figure-led page is `stack` or `split-wide` with the drawing in
the wide cell" — and until 0.1.592 `new_deck.py` emitted `body split` on every
content page it produced.

Measured on the emitted scaffold, before and after:

  * visual share: 10 of 11 content pages under the 50% internal target, worst
    37%  ->  4 of 11, worst 46% (37 is the SCAFFOLD's worst page; the 35% that
    appears elsewhere belongs to the field deck, and an earlier draft of this
    docstring merged the two documents into one row);
  * layout spread: top share 71.4%  ->  42.9%. GAP-024 records the owner
    rejecting a deck at 70.0% and accepting one at 33.3%, so the scaffold's own
    default was worse than the document she faulted.
"""
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts" / "ops"))

import new_deck  # noqa: E402


def _scaffold(*extra):
    argv = [sys.executable, str(ROOT / "scripts/ops/new_deck.py"),
            "--storyline", "market-analysis", "--genre", "internal",
            "--no-trace", *extra]
    if "--pages" not in extra:
        argv += ["--pages", "10", "--parts", "A,B,C"]
    r = subprocess.run(argv, capture_output=True, text=True, cwd=ROOT, check=True)
    return r.stdout


def _layouts(html):
    # `class="body split no-lede"` must not read as an unmatched page: a
    # regex anchored on a single class is the token-boundary defect this repo
    # has already paid for. Take the whole attribute and drop the `body` token.
    out = []
    for attr in re.findall(r'<div class="body ([^"]*)"', html):
        names = [t for t in attr.split() if t and t != "no-lede"]
        out.append(names[0] if names else "body")
    return out


def test_no_content_page_uses_plain_split():
    lays = _layouts(_scaffold())
    assert "split" not in lays, (
        "the scaffold emits `body split`, the one layout "
        "storyline-templates.md rules out for a figure-led page")


def test_the_scaffold_varies_its_layouts():
    """One layout on every page is what the owner faulted by eye."""
    body = [name for name in _layouts(_scaffold()) if name != "cover-grid"]
    top = max(body.count(name) for name in set(body)) / len(body)
    assert top < 0.6, f"top layout carries {top:.0%} of the pages"


def test_the_rotation_survives_a_plan_whose_pages_repeat_one_move(tmp_path):
    """The plan-driven path is the main one, and the first rotation collapsed on it.

    `figure_layout` began by giving any unit too thin for the figure box `stack`
    whatever its turn. `shape_for` resolves `compare` to a unit that inks 6.7%
    of the box and `position` to one that inks 38.4%, so an outline repeating
    one move put EVERY content page in `stack` — a 100% top share, worse than
    the 71.4% this release set out to remove, reached through the package's own
    main door. Measured, not reasoned: this test failed on the first attempt.
    """
    o = tmp_path / "outline.md"
    o.write_text("# Plan\n\n## Part A\n\n" + "".join(
        f"- Title {i} carrying a 4{i}% fact\n"
        f"  analysis: {'compare' if i % 2 else 'position'} | finding: f{i} |"
        f" implication: i{i}\n" for i in range(1, 7)), encoding="utf-8")
    body = [name for name in _layouts(_scaffold("--pages", "6", "--parts", "A",
                                                "--outline", str(o)))
            if name != "cover-grid"]
    top = max(body.count(name) for name in set(body)) / len(body)
    assert top < 0.6, (
        f"a plan whose pages repeat one analytical move puts {top:.0%} of them "
        f"in one layout")


def test_thinness_does_not_decide_the_layout():
    """The parameter is accepted and unused on purpose; pin that it stays so."""
    thin = "p156-very-attractiveaveragevery-unattractive-01"
    fill = new_deck.shape_fill(thin)
    assert fill is not None and fill < 55, "this fixture is no longer a thin unit"
    assert [new_deck.figure_layout(i, thin) for i in range(4)] == \
           [new_deck.figure_layout(i, None) for i in range(4)], \
           "a thin unit steers the rotation again"


def test_an_unknown_or_absent_shape_still_rotates():
    for shape in (None, "", "no-such-unit"):
        assert [new_deck.figure_layout(i, shape) for i in range(4)] == \
               list(new_deck.FIGURE_LAYOUTS) * 2


def test_stack_pages_keep_the_centerpiece_in_the_1fr_row():
    """`.body.stack` declares two rows. A third child starves the figure — it
    rendered at 3% of the page before the child structure followed the class."""
    html = _scaffold()
    for m in re.finditer(r'<div class="body stack">(.*?)\n  </div>', html, re.S):
        assert m.group(1).count('<div class="fill"') == 1, (
            "a stack page emits more than one cell, so the figure lands in an "
            "implicit auto row")


def test_every_content_page_stays_div_balanced():
    html = _scaffold()
    for m in re.finditer(r'<section class="page" id="(p\d+)"[^>]*>(.*?)</section>',
                         html, re.S):
        body = m.group(2)
        assert len(re.findall(r"<div\b", body)) == len(re.findall(r"</div>", body)), \
            f"{m.group(1)} is not div-balanced"
