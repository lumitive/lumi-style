"""Which side of the split a tracked file is on.

The public repository is a mechanical projection of this one, so the boundary
has to be computable. Two halves, and they are deliberately different:

- **Data and prose are DECLARED** in `adapters/shipped.json`, because there is
  no way to compute whether a reader needs `NOTICE`.
- **Scripts are COMPUTED** from reachability, seeded by the scripts SKILL.md
  tells an agent to run. A script nobody can reach from the skill's own surface
  is development by default, which is the safe direction to be wrong in: a dev
  script wrongly kept is dead weight, a consumer script wrongly dropped is a
  broken install.

Reachability follows three things: imports, `scripts/<drawer>/<name>.py`
strings, and `with_name("<name>.py")` sibling references. This package's scripts
invoke each other by subprocess as often as they import each other, and a
boundary that saw only imports would cut a live edge — the third form carries no
`scripts/<drawer>/` for the second to match, and it is `new_deck.py`'s only edge
to the trace store.
"""
from __future__ import annotations

import ast
import json
import pathlib
import re

ROOT = next(p for p in pathlib.Path(__file__).resolve().parents
            if (p / "SKILL.md").exists())
MANIFEST = "adapters/shipped.json"
SCRIPT_REF = re.compile(r"scripts/[a-z]+/([a-z_][a-z0-9_]*)\.py")
# `pathlib.Path(__file__).with_name("trace.py")` — new_deck.py's edge to the
# trace store, and the only one of its kind. The module docstring above calls
# subprocess invocation a live edge; SCRIPT_REF cannot see THIS one, because
# there is no `scripts/<drawer>/` in the string.
SIBLING_FILE = re.compile(r'with_name\(\s*[\'"]([a-z_][a-z0-9_]*)\.py[\'"]')
SKILL_INVOCATION = re.compile(r"scripts/[a-z]+/([a-z_][a-z0-9_]*)\.py")


def manifest(root: pathlib.Path | None = None) -> dict:
    """-> the declaration. `root` is the caller's, for synthetic trees."""
    return json.loads(((root or ROOT) / MANIFEST).read_text(encoding="utf-8"))


def _scripts(root: pathlib.Path) -> dict[str, pathlib.Path]:
    found = {}
    for p in sorted(root.glob("scripts/*/*.py")) + sorted(root.glob("scripts/*.py")):
        found[p.stem] = p
    return found


def _edges(path: pathlib.Path, known: dict) -> set[str]:
    src = path.read_text(encoding="utf-8")
    out: set[str] = set()
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return out
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            out.add(node.module.split(".")[0])
    out.update(SCRIPT_REF.findall(src))
    out.update(SIBLING_FILE.findall(src))
    return {d for d in out if d in known}


def consumer_scripts(root: pathlib.Path | None = None) -> set[str]:
    """-> the stems reachable from the skill's own surface."""
    root = root or ROOT
    known = _scripts(root)
    skill = (root / "SKILL.md")
    if not skill.exists():
        # `ROOT` is DEFINED by SKILL.md existing, so this is unreachable in the
        # real tree and a lie everywhere else. Returning an empty set here made
        # every script development, and both boundary guards stayed green while
        # the projection shipped nothing runnable.
        raise FileNotFoundError(f"{root}/SKILL.md: the consumer boundary is "
                                f"seeded from it and cannot be computed without it")
    seeds = set(SKILL_INVOCATION.findall(skill.read_text(encoding="utf-8")))
    decl = manifest(root)
    seeds.update(decl.get("consumer_seeds", []))
    pinned = {p["stem"] for p in decl.get("dev_pins", [])}
    seen: set[str] = set()
    stack = [s for s in seeds if s in known and s not in pinned]
    while stack:
        stem = stack.pop()
        if stem in seen:
            continue
        seen.add(stem)
        stack.extend(e for e in _edges(known[stem], known) if e not in pinned)
    if not seen and known:
        # AN EMPTY ANSWER IS NOT AN ANSWER. A SKILL.md rewrite that names its
        # commands in prose rather than as `scripts/<drawer>/<name>.py` paths
        # collapses this to nothing; every script then reads as development,
        # `check_shipped_closure` still reports a total partition because "dev"
        # is a valid side, and `check_cross_boundary_paths` scans an empty
        # loop. Measured: fourteen scripts flipped, `new_deck.py` among them,
        # with both guards green.
        raise ValueError(
            f"{root}/SKILL.md names no script this package ships, and "
            f"`consumer_seeds` adds none. The boundary cannot be computed from "
            f"nothing — a scan that did not run is not a scan that passed")
    return seen


def imports_of(stem: str, root: pathlib.Path | None = None) -> set[str]:
    """-> the stems that IMPORT `stem`. Reachability cannot tell a call from a
    mention, so a pin is audited on the half a mention cannot fake."""
    root = root or ROOT
    known = _scripts(root)
    out = set()
    for other, path in known.items():
        if other == stem:
            continue
        src = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import) and any(
                    a.name.split(".")[0] == stem for a in node.names):
                out.add(other)
            elif (isinstance(node, ast.ImportFrom) and node.module
                  and node.level == 0 and node.module.split(".")[0] == stem):
                out.add(other)
    return out


def side_of(relpath: str, root: pathlib.Path | None = None,
            consumer: set[str] | None = None) -> str | None:
    """-> the declared side, or None when nothing places it.

    The string comes back as the rule WROTE it, not from a closed set: a
    misspelled `"Dev"` is returned verbatim, and `check_shipped_closure` is
    what rejects it. A caller comparing `== "dev"` and trusting a three-value
    contract writes the hole that guard exists to close.

    None is the finding `check_shipped_closure` exists for: an unclassified
    file is not a passing file, it is a file the projection cannot place.
    """
    root = root or ROOT
    best: tuple[str, str] | None = None
    for rule in manifest(root)["rules"]:
        pre = rule["prefix"]
        if not matches(relpath, pre):
            continue
        if best is None or len(pre) > len(best[0]):
            best = (pre, rule["side"])
    if best:
        # An explicit rule wins over the computation, which is what lets a
        # NON-SCRIPT under scripts/ be placed at all.
        return best[1]
    if relpath.startswith("scripts/") and relpath.endswith((".py", ".sh")):
        stem = relpath.rsplit("/", 1)[-1].rsplit(".", 1)[0]
        if consumer is None:
            consumer = consumer_scripts(root)
        return "consumer" if stem in consumer else "dev"
    # A DRAWER is not a script. `scripts/check/` holds both sides, so it has no
    # single one, and calling it development reported every consumer script
    # that named its own drawer.
    return None


def matches(relpath: str, prefix: str) -> bool:
    """-> whether `prefix` claims `relpath`, on a PATH boundary.

    A bare `startswith` WOULD let the `NOTICE` rule claim a
    `NOTICE_TO_MAINTAINERS.md`, and `LICENSE` an audit note beside it — a
    partition reporting itself total while publishing a maintainer file.
    Demonstrated on a scratch clone, never shipped. The missing-boundary class
    HAS shipped here before (`\bcard\b` matching `f-card`), which is why the
    comparison is spelled out rather than left to a prefix test.
    """
    if relpath == prefix:
        return True
    if prefix.endswith("/"):
        # The DIRECTORY ITSELF as well as what is under it: a script naming
        # `ROOT / "reviews"` names something the projection does not carry, and
        # comparing only the slashed form answered "no rule claims this".
        return relpath.startswith(prefix) or relpath == prefix.rstrip("/")
    return relpath.startswith(prefix + "/")
