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

Reachability follows imports AND `scripts/<drawer>/<name>.py` strings, because
this package's scripts invoke each other by subprocess as often as they import
each other, and a boundary that saw only imports would cut a live edge.
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
# trace store, and the only one of its kind. It is exactly the assembled path
# the SCRIPT_REF comment says the regex was added to catch, and SCRIPT_REF
# cannot see it: there is no `scripts/<drawer>/` in the string.
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
    seeds = set(SKILL_INVOCATION.findall(skill.read_text(encoding="utf-8"))) \
        if skill.exists() else set()
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
    """-> "consumer", "dev", or None when no rule claims it.

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

    A bare `startswith` let the `NOTICE` rule claim `NOTICE_TO_MAINTAINERS.md`
    and the `LICENSE` rule claim `LICENSE-AUDIT-NOTES.md` — two maintainer
    files published by a partition that reported itself total. This repository
    has now shipped that same missing-boundary bug five times, `\bcard\b`
    matching `f-card` among them, so the comparison is spelled out rather than
    left to a prefix test.
    """
    if relpath == prefix:
        return True
    if prefix.endswith("/"):
        # The DIRECTORY ITSELF as well as what is under it: a script naming
        # `ROOT / "reviews"` names something the projection does not carry, and
        # comparing only the slashed form answered "no rule claims this".
        return relpath.startswith(prefix) or relpath == prefix.rstrip("/")
    return relpath.startswith(prefix + "/")
