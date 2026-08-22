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
    return {d for d in out if d in known}


def consumer_scripts(root: pathlib.Path | None = None) -> set[str]:
    """-> the stems reachable from the skill's own surface."""
    root = root or ROOT
    known = _scripts(root)
    skill = (root / "SKILL.md")
    seeds = set(SKILL_INVOCATION.findall(skill.read_text(encoding="utf-8"))) \
        if skill.exists() else set()
    seeds.update(manifest(root).get("consumer_seeds", []))
    seen: set[str] = set()
    stack = [s for s in seeds if s in known]
    while stack:
        stem = stack.pop()
        if stem in seen:
            continue
        seen.add(stem)
        stack.extend(_edges(known[stem], known))
    return seen


def side_of(relpath: str, root: pathlib.Path | None = None,
            consumer: set[str] | None = None) -> str | None:
    """-> "consumer", "dev", or None when no rule claims it.

    None is the finding `check_shipped_closure` exists for: an unclassified
    file is not a passing file, it is a file the projection cannot place.
    """
    root = root or ROOT
    if relpath.startswith("scripts/"):
        stem = relpath.rsplit("/", 1)[-1].rsplit(".", 1)[0]
        if consumer is None:
            consumer = consumer_scripts(root)
        return "consumer" if stem in consumer else "dev"
    best: tuple[str, str] | None = None
    for rule in manifest(root)["rules"]:
        pre = rule["prefix"]
        if relpath == pre or relpath.startswith(pre):
            if best is None or len(pre) > len(best[0]):
                best = (pre, rule["side"])
    return best[1] if best else None
