"""Two documents about different things must not arrive as the same drawings.

An owner compared three platforms' round-5 decks and said the figures looked
alike. They did, and it was not the agents: `shape_for` returned `shapes[0]` of
the first matching framework — deterministic on the analytical MOVE alone — and
the alternatives it offered in the scaffold comment were siblings of that same
unit. Across the four moves an outline can declare, the library offers 25
shapes and the scaffold emitted four, the same four to everyone. Of 206 units
in the library, 1.9% were reachable.
"""
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "ops"))

import new_deck  # noqa: E402

MOVES = ("compare", "position", "decompose", "bridge")
TITLES = ("AP2 as the base layer", "Mastercard is a channel",
          "Verified server-side", "Three adapters one seam",
          "What the mandate signs")


def test_one_move_no_longer_means_one_drawing():
    """The whole complaint, as an assertion: the same move on different pages
    must be able to produce different figures."""
    for move in MOVES:
        got = {new_deck.shape_for(move, "", seed=f"{t}|{move}")[0] for t in TITLES}
        assert len(got) > 1, (
            f"{move} still yields one shape for five different titles: {got}")


def test_the_choice_is_stable_for_one_page():
    """Content-derived, never random: the same outline must rebuild the same
    deck, and `build_fixtures --check` gates on exactly that."""
    for move in MOVES:
        picks = {new_deck.shape_for(move, "", seed=f"a title|{move}")[0]
                 for _ in range(8)}
        assert len(picks) == 1, f"{move} is not reproducible: {picks}"


def test_an_empty_seed_keeps_the_first_shape():
    """A caller with no content yet is unchanged."""
    for move in MOVES:
        assert new_deck.shape_for(move, "")[0] == \
               new_deck.shape_for(move, "", seed="")[0]


def test_the_pool_spans_every_framework_that_draws_the_move():
    """It was one framework's first row. `position` has three frameworks and
    ten shapes between them; nine were unreachable."""
    import json
    fw = json.loads((ROOT / "assets" / "frameworks.json").read_text(encoding="utf-8"))
    entries = fw.get("frameworks", fw)
    for move in MOVES:
        available = {x for v in entries.values()
                     if isinstance(v, dict) and v.get("move") == move
                     for x in (v.get("shapes") or [])
                     if (ROOT / "assets" / "shapes" / f"{x}.svg").exists()}
        reached = {new_deck.shape_for(move, "", seed=f"t{i}|{move}")[0]
                   for i in range(200)}
        assert reached == available, (
            f"{move}: {len(reached)} of {len(available)} shapes reachable; "
            f"missing {sorted(available - reached)}")


def _deck(outline: pathlib.Path) -> str:
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts/ops/new_deck.py"),
         "--storyline", "market-analysis", "--genre", "internal",
         "--pages", "4", "--parts", "A", "--no-trace", "--outline", str(outline)],
        capture_output=True, text=True, cwd=ROOT, check=True).stdout


def _shapes(html: str) -> set:
    import re
    return set(re.findall(r'href="#shape-([a-z0-9-]+)"', html))


def _outline(path: pathlib.Path, subject: str) -> pathlib.Path:
    path.write_text("# Plan\n\n## Part A\n\n" + "".join(
        f"- {subject} {i} carrying a 4{i}% fact\n"
        f"  analysis: {m} | finding: f{i} | implication: i{i}\n"
        for i, m in enumerate(MOVES, 1)), encoding="utf-8")
    return path


def test_two_documents_with_the_same_moves_get_different_drawings(tmp_path):
    """The end-to-end form of the owner's observation."""
    a = _shapes(_deck(_outline(tmp_path / "a.md", "Payments rail")))
    b = _shapes(_deck(_outline(tmp_path / "b.md", "Memory subsystem")))
    assert a != b, f"two unrelated documents drew the same figures: {a}"
    assert len(a - b) >= 2, (
        f"only {len(a - b)} figure(s) differ between two unrelated documents: "
        f"{sorted(a)} vs {sorted(b)}")
