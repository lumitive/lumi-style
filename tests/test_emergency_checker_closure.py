"""The emergency-merge trusted checker runs under PYTHONSAFEPATH.

The 2026-08-13 audit found the emergency path broken: check_repo gained
sibling imports at 0.1.420, PYTHONSAFEPATH strips the script's directory
from sys.path, and the single-file trusted copy left `import color_math`
unresolvable — so the last-resort merge path would have misdiagnosed every
PR as "real defect in the PR". This test simulates the emergency copy
sequence permanently: a temp copy of the tree, the trusted closure copied
over it, SAFEPATH on.
"""
import os
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Must mirror TRUSTED_CLOSURE in scripts/emergency_merge.sh.
CLOSURE = ("check/check_repo.py", "lib/color_math.py", "lib/css_tokens.py",
           "lib/lock.py", "lib/deliverable_registry.py")


def test_closure_list_matches_the_shell_script():
    text = (ROOT / "scripts" / "emergency_merge.sh").read_text(encoding="utf-8")
    for name in CLOSURE:
        assert name.split("/")[-1] in text, (name, "missing from emergency_merge.sh — the "
                              "closure lists must not drift apart")


def test_trusted_checker_runs_under_safepath(tmp_path):
    work = tmp_path / "repo"
    # The pieces check_repo reads: enough of the real tree to run every guard.
    for entry in ("scripts", "tokens", "references", "adapters", "fixtures",
                  "conformance", "assets", "prompts", "backlog", "reviews",
                  "releases", "tests", ".github", "specs"):
        src = ROOT / entry
        if src.exists():
            shutil.copytree(src, work / entry,
                            ignore=shutil.ignore_patterns("__pycache__",
                                                          "results", "_layout"))
    for md in ROOT.glob("*.md"):
        shutil.copy(md, work / md.name)
    for name in ("pyproject.toml", "requirements-dev.txt", ".gitignore",
                 "NOTICE", "LICENSE"):
        if (ROOT / name).exists():
            shutil.copy(ROOT / name, work / name)
    # The emergency copy step: trusted closure overwrites the "PR's" files.
    for name in CLOSURE:
        shutil.copy(ROOT / "scripts" / name, work / "scripts" / name)
    env = dict(os.environ, PYTHONSAFEPATH="1")
    p = subprocess.run([sys.executable,
                        str(work / "scripts" / "check" / "check_repo.py")],
                       capture_output=True, text=True, env=env, timeout=300)
    # No .git in the temp tree: the git-dependent guards return clean by
    # design. What this asserts is that the checker RUNS — no
    # ModuleNotFoundError, no crash — and reports per-guard verdicts.
    assert "ModuleNotFoundError" not in p.stderr
    assert "checks failed" in p.stdout or "checks pass" in p.stdout, p.stdout[-400:]
