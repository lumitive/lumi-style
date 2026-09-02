#!/usr/bin/env python3
"""Break this release's own code on purpose, and see whether the tests notice.

**Why this is a release step rather than a review note.** The pre-merge review
of 0.1.677 planted 46 defects across eight changed files and the suite could
not see 32 of them. That is the highest find rate of any instrument this
package has, and it was the only one nobody ran automatically — so it found
those 32 once, by hand, on one branch.

A test suite that passes tells you the code runs. Only a surviving mutation
tells you the suite is watching.

**Bounded by construction, because an unbounded one gets switched off.** It
mutates only the files THIS release changed, only in mechanical ways, and runs
only the tests that reach the mutated module — the whole suite takes seven
minutes and a per-mutation seven minutes is a step nobody keeps. Measured on a
six-file release: a few dozen seconds.

    python3 scripts/check/mutation_probe.py                 # since the last release
    python3 scripts/check/mutation_probe.py --base <ref>
    python3 scripts/check/mutation_probe.py --file <one module>

**A survivor fails the run.** The two honest answers are to kill it — write the
test that catches it — or to record it in `evals/mutation-waivers.json` with a
reason. A third answer, "it is only a report", is how the last ten FM-24
instances shipped.

Standard library only.
"""
from __future__ import annotations

import argparse
import ast
import json
import pathlib

# --- scripts path bootstrap (canonical; the bootstrap guard enforces this) ---
import pathlib as _bs_pathlib  # noqa: E402
import re
import subprocess
import sys
import sys as _bs_sys  # noqa: E402

_SCRIPTS_ROOT = next(p for p in _bs_pathlib.Path(__file__).resolve().parents
                     if p.name == "scripts")
for _sub in ("lib", "render", "check", "build", "ops", ""):
    _p = str(_SCRIPTS_ROOT / _sub) if _sub else str(_SCRIPTS_ROOT)
    if _p not in _bs_sys.path:
        _bs_sys.path.append(_p)
del _bs_pathlib, _bs_sys, _SCRIPTS_ROOT, _sub, _p

import repo_files  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]
WAIVERS = ROOT / "evals" / "mutation-waivers.json"

# How many mutations one release is worth. A ceiling, not a target: past this
# the step stops finishing inside a release and starts being skipped.
BUDGET = 24

# The operator flips. Chosen because each is a defect a careless edit makes,
# and each changes BEHAVIOUR rather than syntax — a mutation the code shrugs
# off teaches nothing.
FLIP = {ast.Lt: "GtE", ast.LtE: "Gt", ast.Gt: "LtE", ast.GtE: "Lt",
        ast.Eq: "NotEq", ast.NotEq: "Eq"}


def changed_files(base: str) -> list[pathlib.Path]:
    """-> the .py files under scripts/ this release touched."""
    code, out = repo_files.run_git("diff", "--name-only", base, "--", "scripts",
                                   root=ROOT)
    if code != 0:
        return []
    return [ROOT / f for f in out.split()
            if f.endswith(".py") and (ROOT / f).is_file()]


def tests_reaching(module: str) -> list[str]:
    """-> the test files that import this module, by name.

    DISCOVERED, never listed. A hand-written map of module to test file is
    short the day it is written (FM-20), and the mutation this step exists to
    catch is exactly the one whose test nobody remembered to add.
    """
    want = re.compile(rf"^\s*(import|from)\s+{re.escape(module)}\b", re.M)
    return [str(p.relative_to(ROOT)) for p in sorted((ROOT / "tests").glob("test_*.py"))
            if want.search(p.read_text(encoding="utf-8", errors="replace"))]


# The shared path-bootstrap block. Identical in every module, held by
# `check_repo`'s own `bootstrap` guard rather than by tests, so mutating it
# reports a survivor in every file that carries it. Skipped by RANGE rather
# than waived per file: a waiver list with one row per module is the
# hand-written inventory FM-20 refuses.
_BOOTSTRAP_OPEN = "--- scripts path bootstrap"
_BOOTSTRAP_CLOSE = "del _bs_pathlib"
# The `ROOT = ...` idiom is the same boilerplate in a second form, outside the
# marked block, and it is held by the same guard.
_BOILERPLATE_LINE = 'if p.name == "scripts")'


def _boilerplate(lines) -> set[int]:
    """-> the 1-based line numbers no test is responsible for."""
    out, inside = set(), False
    for i, text in enumerate(lines, 1):
        if _BOOTSTRAP_OPEN in text:
            inside = True
        if inside:
            out.add(i)
        if _BOILERPLATE_LINE in text:
            out.add(i)
        if inside and _BOOTSTRAP_CLOSE in text:
            inside = False
    return out


def mutations(path: pathlib.Path):
    """-> (line, description, old_source, new_source) for each mutation."""
    src = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return
    lines = src.splitlines(keepends=True)
    skip_lines = _boilerplate(lines)

    for node in ast.walk(tree):
        # a comparison operator, flipped
        if isinstance(node, ast.Compare) and len(node.ops) == 1:
            op = type(node.ops[0])
            if (op in FLIP and hasattr(node, "lineno")
                    and node.lineno not in skip_lines):
                text = lines[node.lineno - 1]
                sym = {"Lt": "<", "LtE": "<=", "Gt": ">", "GtE": ">=",
                       "Eq": "==", "NotEq": "!="}
                was = sym[op.__name__]
                now = sym[FLIP[op]]
                if text.count(was) == 1:
                    yield (node.lineno, f"{was} -> {now}", text,
                           text.replace(was, now, 1))
        # a container constant, emptied
        if isinstance(node, ast.Assign) and isinstance(
                node.value, (ast.Dict, ast.Tuple, ast.List, ast.Set)):
            names = [t.id for t in node.targets if isinstance(t, ast.Name)]
            if (names and names[0].isupper()
                    and node.lineno not in skip_lines
                    and node.lineno == getattr(node.value, "end_lineno",
                                               node.lineno)):
                text = lines[node.lineno - 1]
                indent = text[: len(text) - len(text.lstrip())]
                yield (node.lineno, f"{names[0]} emptied", text,
                       f"{indent}{names[0]} = type({names[0]})()\n"
                       if False else f"{indent}{names[0]} = {{}}\n"
                       if isinstance(node.value, ast.Dict) else
                       f"{indent}{names[0]} = ()\n")


def run(tests: list[str]) -> bool:
    """-> True when the tests pass."""
    if not tests:
        return True
    r = subprocess.run([sys.executable, "-B", "-m", "pytest", "-q", "-x", *tests],
                       cwd=ROOT, capture_output=True, text=True,
                       env={"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin",
                            "HOME": str(pathlib.Path.home())})
    return r.returncode == 0


def waived() -> dict:
    try:
        return json.loads(WAIVERS.read_text(encoding="utf-8")).get("survivors", {})
    except (OSError, ValueError):
        return {}


def probe(files: list[pathlib.Path]) -> tuple[list[str], int, int]:
    """-> (survivor descriptions, tried, killed)."""
    skip = waived()
    survivors, tried, killed = [], 0, 0
    for path in files:
        module = path.stem
        tests = tests_reaching(module)
        rel = str(path.relative_to(ROOT))
        if not tests:
            survivors.append(f"{rel}: no test file imports `{module}` — every "
                             f"mutation of it survives by construction")
            continue
        original = path.read_text(encoding="utf-8")
        for line, what, old, new in mutations(path):
            if tried >= BUDGET:
                break
            # KEYED ON THE SOURCE LINE, NEVER ON ITS NUMBER. A waiver keyed
            # `file:line` stops matching the moment anything above it moves,
            # and worse, silently comes to waive a DIFFERENT mutation. That is
            # the citation-drift class this repository fixed the same week, in
            # the mechanism written to stop that class.
            key = f"{rel} :: {what} :: {old.strip()}"
            if key in skip:
                continue
            tried += 1
            path.write_text(original.replace(old, new, 1), encoding="utf-8")
            try:
                if run(tests):
                    survivors.append(
                        f"{rel}:{line} {what} — {', '.join(tests)} still "
                        f"pass\n         waive with: {key}")
                else:
                    killed += 1
            finally:
                path.write_text(original, encoding="utf-8")
    return survivors, tried, killed


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", default="HEAD~1",
                    help="what to diff against; default the previous commit")
    ap.add_argument("--file", action="append",
                    help="mutate this file instead of the diff")
    a = ap.parse_args(argv)

    files = ([ROOT / f for f in a.file] if a.file
             else changed_files(a.base))
    if not files:
        # A SCAN THAT VISITED NOTHING is not a clean scan. It is the answer
        # this whole script exists to stop a check from giving.
        print("note  no changed .py under scripts/ — nothing was mutated, "
              "which is not the same as nothing surviving")
        return 0

    survivors, tried, killed = probe(files)
    print(f"note  {tried} mutation(s) across {len(files)} changed file(s): "
          f"{killed} killed, {len(survivors)} alive")
    for s in survivors:
        print(f"      {s}")
    if survivors:
        print("FAIL  a surviving mutation is a defect the suite cannot see. "
              "Write the test that catches it, or record it in "
              "evals/mutation-waivers.json with a reason.")
        return 1
    print("ok    every mutation was caught")
    return 0


if __name__ == "__main__":
    sys.exit(main())
