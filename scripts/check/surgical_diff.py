#!/usr/bin/env python3
"""Every changed line traces to the request — convention 17, mechanised.

WHY THIS EXISTS. Four times in three releases a tracked JSON file was written
back with a different indent than it had, and the commit carried hundreds or
thousands of changed lines of which a handful were the change:

    0.1.673  evals/gates.json           1136 lines changed,   8 once whitespace is ignored
    0.1.673  evals/rule-coverage.json   9960 lines changed, 384
    0.1.674  evals/rule-coverage.json   9990 lines changed, 144   (putting 0.1.673's back)
    0.1.681  adapters/shipped.json       499 lines changed,   5

`git diff --numstat` against `git diff -w --numstat` — the second ignores
whitespace — is the whole measurement, and it was run on the last thirty
commits before this was written: it names those four and none of the other
twenty-six. Nothing had been watching: the tree had `json.dump` at twenty-six
sites with two indents between them and no shared writer. AG-4 refused to
reformat the tree on purpose, because a mass rewrite destroys `git blame` on
comments that are institutional memory; this is the guard that holds that
refusal, one commit at a time.

WHAT IT MEASURES. For every file in a diff: lines changed, and lines changed
once whitespace is ignored. A file with at least MIN_LINES changed of which at
most 1/RATIO survive `-w` has been reformatted, not edited. Language-agnostic —
a re-indented YAML or a re-wrapped Markdown would trip it the same way, and
should.

THREE ANSWERS, never two (FM-24). Clean; a reformat found; could not look — not
a git tree, git failed, a revision that does not exist. The third exits 2 and
prints a sentence saying what it could not do, so it never reads as the first.

WAIVERS. `evals/reformat-waivers.json` — a reformat done on purpose is a
decision with an address: the file, the release it belongs to, and why. A
waiver is live only while its release is the newest CHANGELOG heading. After
that it is dead, and a dead waiver IS a finding, so the table cannot become a
list of things nobody looks at.

Two callers. `release.py` runs it on the working tree against HEAD before
committing, where the author can still fix it; `check_repo.py` runs it on
HEAD~1..HEAD in CI, so a commit made around the release tool is judged the
same way.
"""
from __future__ import annotations

# --- scripts path bootstrap (canonical; the bootstrap guard enforces this) ---
import pathlib as _bs_pathlib  # noqa: E402
import sys as _bs_sys  # noqa: E402

_SCRIPTS_ROOT = next(p for p in _bs_pathlib.Path(__file__).resolve().parents
                     if p.name == "scripts")
for _sub in ("lib", "render", "check", "build", "ops", ""):
    _p = str(_SCRIPTS_ROOT / _sub) if _sub else str(_SCRIPTS_ROOT)
    if _p not in _bs_sys.path:
        _bs_sys.path.append(_p)
del _bs_pathlib, _bs_sys, _SCRIPTS_ROOT, _sub, _p

import argparse  # noqa: E402
import dataclasses  # noqa: E402
import json  # noqa: E402
import pathlib  # noqa: E402
import sys  # noqa: E402

import repo_files  # noqa: E402
import versioning  # noqa: E402

# The release that introduced the gate. A commit whose committed CHANGELOG is
# older than this predates the rule and is not judged by it — history is not
# retroactively reddened, and 0.1.681 carries the very reformat that prompted
# this. The working tree has no such exemption: it is always this release.
SINCE = "0.1.682"

# Chosen against real history, not by feel: every threshold pair that names
# the four instances above and none of the other twenty-six commits in the
# same window sits in a wide band, and these are the round numbers inside it.
# MIN_LINES is a floor on how much has to change before the ratio means
# anything — a three-line file that is re-indented is not what this is for.
MIN_LINES = 60
RATIO = 5

WAIVERS = pathlib.Path("evals/reformat-waivers.json")
CHANGELOG = pathlib.Path("CHANGELOG.md")


@dataclasses.dataclass(frozen=True)
class Reformat:
    path: str
    total: int      # lines changed
    real: int       # lines changed once whitespace is ignored

    def sentence(self) -> str:
        return (f"{self.path}: {self.total} lines changed, {self.real} once "
                f"whitespace is ignored — this is a reformat, not an edit")


def numstat(root: pathlib.Path, base: str, target: str | None,
            *, ignore_whitespace: bool) -> tuple[dict[str, tuple[int, int]] | None, str | None]:
    """-> ({path: (added, deleted)}, None) or (None, why git could not say).

    Binary files (`-` counts) are skipped: whitespace means nothing there.
    """
    args = ["diff", "--numstat"]
    if ignore_whitespace:
        args.append("-w")
    args.append(base)
    if target is not None:
        args.append(target)
    rc, out = repo_files.run_git(*args, root=root)
    if rc != 0:
        return None, (f"git {' '.join(args)} failed (exit {rc}): "
                      f"{out.strip().splitlines()[-1] if out.strip() else 'no output'}")
    rows: dict[str, tuple[int, int]] = {}
    for line in out.splitlines():
        parts = line.split("\t", 2)
        if len(parts) != 3 or parts[0] == "-":
            continue
        rows[parts[2]] = (int(parts[0]), int(parts[1]))
    return rows, None


def reformats(root: pathlib.Path, base: str, target: str | None = None,
              *, min_lines: int = MIN_LINES, ratio: int = RATIO
              ) -> tuple[list[Reformat], str | None]:
    """-> (the files that were reformatted rather than edited, None) or ([], why not measured)."""
    full, problem = numstat(root, base, target, ignore_whitespace=False)
    if problem:
        return [], problem
    lean, problem = numstat(root, base, target, ignore_whitespace=True)
    if problem:
        return [], problem
    if full is None or lean is None:
        return [], "git diff returned nothing to read"
    found = []
    for path, (a, d) in sorted(full.items()):
        total = a + d
        la, ld = lean.get(path, (0, 0))
        real = la + ld
        if total >= min_lines and real * ratio <= total:
            found.append(Reformat(path, total, real))
    return found, None


def newest_release(root: pathlib.Path) -> str | None:
    """-> the newest CHANGELOG version in the working tree, through the one reader."""
    try:
        text = (root / CHANGELOG).read_text(encoding="utf-8")
    except OSError:
        return None
    found = versioning.releases(text=text)
    return found[0] if found else None


def in_force_at(root: pathlib.Path, rev: str) -> bool:
    """-> whether the gate binds the commit `rev`: its CHANGELOG is at or past SINCE.

    Read from the COMMIT, not the working tree, for the same reason
    `check_commit_convention` does: during release prep the next entry exists
    uncommitted while HEAD is still the previous release. A commit with no
    CHANGELOG, or one whose newest heading is not a version, is judged — an
    absent stamp must not become an exemption (the rule `evals/gates.json`
    already states for deliverables).
    """
    rc, text = repo_files.run_git("show", f"{rev}:{CHANGELOG}", root=root)
    if rc != 0:
        return True
    found = versioning.releases(text=text)
    if not found:
        return True
    try:
        return versioning.ver_key(found[0]) >= versioning.ver_key(SINCE)
    except ValueError:
        return True


def waivers(root: pathlib.Path) -> tuple[dict[str, dict], list[str], str | None]:
    """-> (live waivers by path, the dead ones as sentences, None) or ({}, [], why not read).

    A missing table is an empty table — there is nothing to waive until someone
    writes one. An unreadable table is the third answer.
    """
    path = root / WAIVERS
    if not path.exists():
        return {}, [], None
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {}, [], f"{WAIVERS} could not be read ({exc})"
    table = doc.get("waivers")
    if not isinstance(table, dict):
        return {}, [], f"{WAIVERS} has no `waivers` object"
    newest = newest_release(root)
    live, dead = {}, []
    for file, entry in table.items():
        if not isinstance(entry, dict) or not entry.get("why") or not entry.get("release"):
            dead.append(f"{WAIVERS}: the waiver for {file} needs both `release` and `why`")
            continue
        if entry["release"] != newest:
            dead.append(f"{WAIVERS}: the waiver for {file} belongs to {entry['release']} "
                        f"and the newest release is {newest} — a dead waiver is removed, "
                        f"not kept")
            continue
        live[file] = entry
    return live, dead, None


def judge(root: pathlib.Path, base: str, target: str | None = None
          ) -> tuple[list[Reformat], list[str], str | None]:
    """-> (unwaived reformats, dead-waiver sentences, None) or ([], [], why not measured)."""
    found, problem = reformats(root, base, target)
    if problem:
        return [], [], problem
    live, dead, problem = waivers(root)
    if problem:
        return [], [], problem
    return [f for f in found if f.path not in live], dead, None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", default="HEAD",
                    help="revision to diff from (default HEAD: the working tree "
                         "against the last commit, which is what release.py asks)")
    ap.add_argument("--target", default=None,
                    help="revision to diff to (omit for the working tree)")
    ap.add_argument("--root", default=None, help="repository root (default: this one)")
    a = ap.parse_args(argv)
    root = pathlib.Path(a.root).resolve() if a.root else repo_files.repo_root()
    if not (root / ".git").exists():
        print(f"could not look: {root} is not a git tree, so nothing was measured")
        return 2
    found, dead, problem = judge(root, a.base, a.target)
    if problem:
        print(f"could not look: {problem}")
        return 2
    span = f"{a.base}..{a.target}" if a.target else f"{a.base}..working tree"
    if not found and not dead:
        print(f"ok    surgical diff — no file in {span} was reformatted rather than edited")
        return 0
    for f in found:
        print(f"FAIL  {f.sentence()}")
    for d in dead:
        print(f"FAIL  {d}")
    if found:
        print("      A reformat that is meant needs an entry in "
              f"{WAIVERS} naming the file, this release and why. One that is not "
              "meant is undone by writing the file back the way it was — "
              "scripts/lib/jsonio.py keeps a JSON file's own indent.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
