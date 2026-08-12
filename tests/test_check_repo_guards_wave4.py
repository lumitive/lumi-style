"""Wave 4: the reorganization's enabling guards, both directions."""
import subprocess

import check_repo

BOOTSTRAP_STUB = "# --- scripts path " + "bootstrap (canonical) ---\n"


def _repo(tmp_path, files):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    for name, content in files.items():
        p = tmp_path / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    return tmp_path


def test_script_paths_resolving_mentions_pass(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "scripts/tool.py": "x = 1\n",
        "README.md": "run `python3 scripts/tool.py` to begin\n"}))
    assert check_repo.check_script_paths() == []


def test_script_paths_dangling_mention_fails_with_line(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "scripts/tool.py": "x = 1\n",
        "README.md": "intro\nrun `python3 scripts/gone.py` to begin\n"}))
    errors = check_repo.check_script_paths()
    assert len(errors) == 1
    assert "README.md:2" in errors[0] and "scripts/gone.py" in errors[0]


def test_script_paths_frozen_history_is_excluded(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "scripts/tool.py": "x = 1\n",
        "CHANGELOG.md": "## 0.1.1 — ran scripts/old_name.py back then\n",
        "specs/2026-01-01-x-design.md": "cited scripts/old_name.py\n"}))
    assert check_repo.check_script_paths() == []


def test_script_paths_waiver_silences_with_reason(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "scripts/tool.py": "x = 1\n",
        "threat.md": "imagine a scripts/hijack.py planted by a PR\n"}))
    monkeypatch.setitem(check_repo.SCRIPT_PATH_WAIVERS, "threat.md",
                        "hypothetical illustration, not a reference")
    assert check_repo.check_script_paths() == []


def test_bootstrap_sibling_import_without_block_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "scripts/consumer.py": "import color_math\n",
        "scripts/color_math.py": "def f():\n    return 1\n"}))
    errors = check_repo.check_bootstrap()
    assert len(errors) == 1
    assert "consumer.py" in errors[0] and "color_math" in errors[0]


def test_bootstrap_block_present_passes(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "scripts/consumer.py": BOOTSTRAP_STUB + "import color_math\n",
        "scripts/color_math.py": "def f():\n    return 1\n"}))
    assert check_repo.check_bootstrap() == []


def test_bootstrap_module_does_not_flag_itself(tmp_path, monkeypatch):
    # color_math.py mentioning its own name in a docstring is not an import
    # of a sibling; and a module importing ITSELF is not a thing.
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "scripts/color_math.py": '"""import color_math is how consumers use '
                                 'this."""\nX = 1\n'}))
    assert check_repo.check_bootstrap() == []


def test_live_repo_is_clean():
    assert check_repo.check_script_paths() == []
    assert check_repo.check_bootstrap() == []


def test_script_paths_constructed_path_fails_when_dangling(tmp_path, monkeypatch):
    """The 0.1.438 lesson: `ROOT / "scripts" / "x.py"` is invisible to the
    string form; the constructed form must resolve too."""
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "scripts/tool.py":
            'import subprocess\n'
            'subprocess.run([str(ROOT / "scripts" / "gone.py")])\n'}))
    errors = check_repo.check_script_paths()
    assert len(errors) == 1
    assert "builds the path scripts/gone.py" in errors[0]


def test_script_paths_constructed_path_resolving_passes(tmp_path, monkeypatch):
    monkeypatch.setattr(check_repo, "ROOT", _repo(tmp_path, {
        "scripts/tool.py":
            'import subprocess\n'
            'subprocess.run([str(ROOT / "scripts" / "lib" / "there.py")])\n',
        "scripts/lib/there.py": "x = 1\n"}))
    assert check_repo.check_script_paths() == []
