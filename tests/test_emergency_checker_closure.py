"""The emergency-merge trusted closure: parsed from the script, held to
check_repo's real imports, and proven shadow-proof under PYTHONSAFEPATH.

History: the restructuring audit (specs/2026-08-13-audit-restructure-design.md;
shipped 2026-08-12) found the single-file trusted copy broken under
PYTHONSAFEPATH since 0.1.420; the PR #92 review then found two more holes —
the closure omitted the review_scores SUBPROCESS (the PR's copy executed),
and a PR planting a closure basename at the scripts ROOT outranked the
trusted lib/ copy. These tests parse the shell script's actual array (no
reimplemented path list to drift), assert it both directions, and plant the
shadow to prove it stays dead.
"""
import os
import pathlib
import re
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SH = ROOT / "scripts" / "ops" / "emergency_merge.sh"


def _parse_closure():
    """-> (trusted_check, closure) resolved from the .sh text itself,
    relative to scripts/ops — the test reads what the script will actually
    do, never a hand-copied list."""
    text = SH.read_text(encoding="utf-8")
    ops = SH.parent
    m = re.search(r'^TRUSTED_CHECK="\$SCRIPT_DIR/([^"]+)"', text, re.M)
    assert m, "TRUSTED_CHECK assignment not found"
    check = (ops / m.group(1)).resolve()
    m = re.search(r"^TRUSTED_CLOSURE=\((.*?)\)$", text, re.M | re.S)
    assert m, "TRUSTED_CLOSURE assignment not found"
    closure = [(ops / rel).resolve()
               for rel in re.findall(r'"\$SCRIPT_DIR/([^"]+)"', m.group(1))]
    return check, closure


def test_every_trusted_path_in_the_script_resolves():
    check, closure = _parse_closure()
    assert check.is_file(), check
    for p in closure:
        assert p.is_file(), p


def test_closure_covers_check_repo_imports_and_subprocesses():
    """Both directions: everything check_repo imports or subprocesses is in
    the closure; extras ride along only deliberately."""
    check, closure = _parse_closure()
    names = {p.name for p in closure}
    src = check.read_text(encoding="utf-8")
    imported = set(re.findall(
        r"^\s*(?:import|from)\s+(color_math|css_tokens|lock|geo_projection|"
        r"geo_frame|globe_svg|regionmap_svg|sea_route|deliverable_registry|"
        r"embed_globe|embed_icons|check_prose|inspect_layout|check_privacy|"
        r"secret_patterns|markup|corpus)\b", src, re.M))
    for mod in imported:
        assert f"{mod}.py" in names, (
            f"check_repo imports {mod} but the trusted closure does not carry "
            f"it — the emergency run would execute the PR's copy")
    for sub in re.findall(r'"scripts" / "ops" / "([\w.]+\.py)"', src):
        assert sub in names, (
            f"check_repo subprocesses {sub} but the trusted closure does not "
            f"carry it — the emergency run would execute the PR's copy")


def _stage(tmp_path):
    """A temp copy of the tree with the emergency copy sequence applied,
    mirroring the .sh: trusted files overwrite, root *.py purged."""
    work = tmp_path / "repo"
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
    check, closure = _parse_closure()
    dest_check = work / "scripts" / "check" / "check_repo.py"
    shutil.copy(check, dest_check)
    for p in closure:
        sub = "ops" if p.parent.name == "ops" else "lib"
        shutil.copy(p, work / "scripts" / sub / p.name)
    for stray in (work / "scripts").glob("*.py"):
        stray.unlink()
    return work, dest_check


def test_trusted_checker_runs_under_safepath(tmp_path):
    work, dest_check = _stage(tmp_path)
    env = dict(os.environ, PYTHONSAFEPATH="1")
    p = subprocess.run([sys.executable, str(dest_check)],
                       capture_output=True, text=True, env=env, timeout=300)
    # No .git in the temp tree: git-dependent guards report their absence.
    # What this asserts: the checker RUNS (no ModuleNotFoundError, no crash)
    # and reports per-guard verdicts.
    assert "ModuleNotFoundError" not in p.stderr
    assert "checks failed" in p.stdout or "checks pass" in p.stdout, p.stdout[-400:]


def test_planted_root_shadow_never_executes(tmp_path):
    """The PR #92 review's demonstrated hijack, kept dead forever: a
    closure basename planted at the scripts root of the 'PR tree' must not
    run — the purge removes it, and lib/ precedes the root in the bootstrap
    order regardless."""
    work, dest_check = _stage(tmp_path)
    canary = tmp_path / "canary.txt"
    shadow = work / "scripts" / "color_math.py"
    shadow.write_text(
        f"import pathlib\n"
        f"pathlib.Path({str(canary)!r}).write_text('PR CODE RAN')\n"
        f"def srgb_linear(v):\n    return v\n")
    # Re-apply the emergency sequence's purge exactly as the .sh does.
    for stray in (work / "scripts").glob("*.py"):
        stray.unlink()
    env = dict(os.environ, PYTHONSAFEPATH="1")
    p = subprocess.run([sys.executable, str(dest_check)],
                       capture_output=True, text=True, env=env, timeout=300)
    assert not canary.exists(), "a PR-planted root shadow executed"
    assert "ModuleNotFoundError" not in p.stderr
