"""The framework dictionary guard, red and green (FM-01 discipline).

The dictionary is the generation-side complement to the shape library
(analysis-rules.md AR-4); the guard holds every binding to the library and
every entry to usability. Each failure shape below is one the repo has
shipped in another guise: a dangling reference, a rule without its limit,
a vocabulary word from outside the set.
"""
import json
import subprocess

import check_repo


def _repo(tmp_path, files):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    for name, content in files.items():
        p = tmp_path / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    return tmp_path


TAGS = json.dumps({"shapes": {"p001-unit-01": {"family": "unit",
                                               "relation": ["order"]}}})


def _fw(**entry):
    base = {"question": "q?", "move": "compare", "slots": ["a"],
            "misuse": "m", "shapes": ["p001-unit-01"], "drawn": None}
    base.update(entry)
    return json.dumps({"version": 1, "frameworks": {"probe": base}})


def test_a_resolving_usable_entry_passes(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "assets/frameworks.json": _fw(),
        "assets/shapes/tags.json": TAGS}))
    assert check_repo.check_frameworks() == []


def test_a_dangling_shape_binding_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "assets/frameworks.json": _fw(shapes=["p999-gone-01"]),
        "assets/shapes/tags.json": TAGS}))
    errors = check_repo.check_frameworks()
    assert any("p999-gone-01" in e for e in errors)


def test_a_move_outside_the_five_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "assets/frameworks.json": _fw(move="vibes"),
        "assets/shapes/tags.json": TAGS}))
    assert any("five analytical moves" in e for e in check_repo.check_frameworks())


def test_a_missing_misuse_line_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "assets/frameworks.json": _fw(misuse=""),
        "assets/shapes/tags.json": TAGS}))
    assert any("misuse" in e for e in check_repo.check_frameworks())


def test_shapeless_without_native_declaration_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "assets/frameworks.json": _fw(shapes=[]),
        "assets/shapes/tags.json": TAGS}))
    assert any("native" in e for e in check_repo.check_frameworks())


def test_shapeless_with_native_declaration_passes(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "assets/frameworks.json": _fw(shapes=[], drawn="native"),
        "assets/shapes/tags.json": TAGS}))
    assert check_repo.check_frameworks() == []


# --- frameworks: the move -> framework direction, and the two vocabularies ---
#
# Every check in `check_frameworks` ran framework -> move until 0.1.663: each
# entry names a legal move, binds a resolvable shape, carries its four fields.
# Nothing ran the other way, so `correlate` sat in AR-1 with ZERO entries and
# the guard printed what it prints on a complete registry.

_AR1 = """## 1 · The five moves

1. **Compare** — a value against a reference.
   Input shape: one value plus a reference. Frameworks: {compare}. The tell: x.
2. **Decompose** — the whole into parts.
   Input shape: a total. Frameworks: {decompose}. The tell: x.
3. **Position** — two axes.
   Input shape: items. Frameworks: {position}. The tell: x.
4. **Correlate** — two quantities.
   Input shape: pairs. Frameworks: {correlate}. The tell: x.
5. **Bridge** — two states.
   Input shape: before and after. Frameworks: {bridge}. The tell: x.

## 2 · The insight ladder
"""


def _entry(move, shapes=("s1",), aka=None):
    e = {"question": "q?", "move": move, "slots": ["a"], "misuse": "m",
         "shapes": list(shapes)}
    if not shapes:
        e["drawn"] = "native"
    if aka:
        e["aka"] = list(aka)
    return e


def _fw_tree(tmp_path, frameworks, ar1=None, ar1_text=None):
    root = tmp_path / "tree"
    (root / "assets" / "shapes").mkdir(parents=True)
    (root / "references").mkdir(parents=True)
    (root / "assets" / "frameworks.json").write_text(
        json.dumps({"version": "1", "frameworks": frameworks}), encoding="utf-8")
    (root / "assets" / "shapes" / "tags.json").write_text(
        json.dumps({"shapes": {"s1": {}, "s2": {}}}), encoding="utf-8")
    named = {"compare": "alpha", "decompose": "beta", "position": "gamma",
             "correlate": "delta", "bridge": "epsilon"}
    named.update(ar1 or {})
    (root / "references" / "analysis-rules.md").write_text(
        ar1_text if ar1_text is not None else _AR1.format(**named),
        encoding="utf-8")
    return root


_COMPLETE = {"alpha": _entry("compare"), "beta": _entry("decompose"),
             "gamma": _entry("position"), "delta": _entry("correlate"),
             "epsilon": _entry("bridge")}


def test_moves_a_complete_registry_passes(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _fw_tree(tmp_path, dict(_COMPLETE)))
    assert check_repo.check_moves_served() == []


def test_moves_a_move_with_no_entry_fails(tmp_path, monkeypatch):
    """THE DELIBERATE RED. This is `correlate`'s real state before 0.1.663:
    declared by AR-1, served by nothing, and D32 skipping every page that
    declares it."""
    reg = {k: v for k, v in _COMPLETE.items() if k != "delta"}
    monkeypatch.setattr(check_repo, "ROOT", _fw_tree(tmp_path, reg))
    errs = check_repo.check_moves_served()
    assert any("correlate" in e and "no entry" in e for e in errs), errs


def test_moves_a_move_served_only_natively_passes(tmp_path, monkeypatch):
    """THE REVERSAL, and it is the most important test in this file.

    A first cut FAILED this case: a move whose every framework is
    `drawn: "native"` is invisible to `_drawable_moves`, so D32 holds no page
    to it. But some frameworks are DRAWN rather than lifted — a waterfall, a
    funnel, a benchmark table, a radar, a scatter — and the register says so.
    Four moves survived that demand only because each happens to have a
    shape-bearing sibling; `correlate` has one framework and nothing to hide
    behind, so the guard's author bound the only correlation-tagged near-match
    to satisfy it, without opening the SVG. It was an empty axis frame with a
    single bubble.

    A gate a correct answer cannot satisfy does not get obeyed, it gets
    satisfied. Refused as AG-10; this test is what keeps it refused."""
    reg = dict(_COMPLETE, delta=_entry("correlate", shapes=()))
    monkeypatch.setattr(check_repo, "ROOT", _fw_tree(tmp_path, reg))
    assert check_repo.check_moves_served() == []


def test_moves_a_name_only_the_rules_know_fails(tmp_path, monkeypatch):
    """`scatter`, `benchmark table`, `radar` and `Mekko` were all in AR-1 and
    nowhere else — a rule sending an author to a figure the package cannot
    draw (convention 5)."""
    monkeypatch.setattr(check_repo, "ROOT", _fw_tree(
        tmp_path, dict(_COMPLETE), ar1={"correlate": "delta, sankey"}))
    errs = check_repo.check_moves_served()
    assert any("'sankey'" in e and "no such entry" in e for e in errs), errs


def test_moves_a_name_only_the_registry_knows_fails(tmp_path, monkeypatch):
    """`funnel` and `market-sizing` were in the registry and named by no rule.
    The registry is the dictionary AR-3 sends authors to; an entry the rules
    never offer is one nobody is told about."""
    monkeypatch.setattr(check_repo, "ROOT", _fw_tree(
        tmp_path, dict(_COMPLETE, zeta=_entry("decompose"))))
    errs = check_repo.check_moves_served()
    assert any("'zeta'" in e and "does not name it" in e for e in errs), errs


def test_moves_one_name_under_two_moves_fails(tmp_path, monkeypatch):
    """`waterfall` was filed under decompose AND bridge inside AR-1 itself, and
    `driver tree` was correlate in the rules and decompose in the registry."""
    monkeypatch.setattr(check_repo, "ROOT", _fw_tree(
        tmp_path, dict(_COMPLETE),
        ar1={"decompose": "beta, epsilon", "bridge": "epsilon"}))
    errs = check_repo.check_moves_served()
    assert any("'epsilon'" in e and "two moves" in e for e in errs), errs


def test_moves_an_alias_resolves_rather_than_failing(tmp_path, monkeypatch):
    """`2x2` and `9-box` are what the industry says and `two-by-two` and
    `nine-box` are what the registry keys are. The alias lives ONCE, in the
    registry, rather than as a second mapping inside the guard."""
    monkeypatch.setattr(check_repo, "ROOT", _fw_tree(
        tmp_path, dict(_COMPLETE, gamma=_entry("position", aka=["2x2"])),
        ar1={"position": "2x2"}))
    assert check_repo.check_moves_served() == []


def test_moves_unreadable_rules_do_not_read_as_agreement(tmp_path, monkeypatch):
    """FM-24. A parser that cannot find AR-1's list has compared no names, and
    must not print what a matching pair prints."""
    monkeypatch.setattr(check_repo, "ROOT", _fw_tree(
        tmp_path, dict(_COMPLETE), ar1_text="nothing that looks like AR-1\n"))
    errs = check_repo.check_moves_served()
    assert any("could not read AR-1" in e for e in errs), errs
    assert errs != [], "the blind branch printed what the clean branch prints"


def test_moves_a_partial_parse_is_not_agreement(tmp_path, monkeypatch):
    """FM-24 ONE LEVEL IN, and the sharpest finding of this release's review:
    the guard written to close blindness at the guard layer was blind.

    `_ar1_frameworks` reported unreadable only when NOTHING parsed. A per-item
    miss just dropped that move's key, the comparison loop iterates the moves
    that PARSED, and the served-check iterates the registry — so a dropped move
    was never compared and the guard returned `[]`, literally what a clean tree
    returns. Three ordinary edits to the real `analysis-rules.md` each did it:
    rewording `Framework: scatter.` to `The framework is scatter.`, dropping the
    bold from `4. **Correlate**`, and renaming the move.

    A test asserting "the clean tree passes" cannot catch this, because the
    blind tree passes it too. Only a test of the blind branch can."""
    ar1 = _AR1.format(compare="alpha", decompose="beta", position="gamma",
                      correlate="delta", bridge="epsilon")
    monkeypatch.setattr(check_repo, "ROOT", _fw_tree(
        tmp_path, dict(_COMPLETE),
        ar1_text=ar1.replace("4. **Correlate**", "4. Correlate")))
    errs = check_repo.check_moves_served()
    assert any("parsed as" in e and "correlate" in e for e in errs), errs


def test_moves_a_complete_parse_of_the_real_rules_agrees():
    """The other half, on the SHIPPED file rather than a fixture. The parser
    must read all five moves out of the real `analysis-rules.md`, or the guard
    above is reporting a parse failure on every run and nobody notices."""
    named = check_repo._ar1_frameworks()
    assert named is not None and set(named) == {
        "compare", "decompose", "position", "correlate", "bridge"}, named
