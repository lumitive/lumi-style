"""0.1.590's removals, each proven to have removed something.

They come from one measurement: a build's cost is `API calls x context`, and the
calls were the half nobody was counting. Every item here is a round trip the
PACKAGE forced — not an agent's habit — so each test names the command that used
to be necessary and shows it no longer is.
"""
import json
import pathlib
import re
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _run(script, *args):
    return subprocess.run([sys.executable, str(ROOT / script), *args],
                          capture_output=True, text=True)


# --- the guaranteed red round ----------------------------------------------

def test_the_scaffold_stamps_its_own_version():
    """`Built with lumi-style VERSION` is a D14 GATING slot, and the version is
    machine-readable. Every build by every user was one red round and one hand
    edit to write a number the package already knew."""
    out = _run("scripts/ops/new_deck.py", "--no-trace")
    assert "lumi-style VERSION" not in out.stdout
    m = re.search(r"Built with lumi-style (\d+\.\d+\.\d+)", out.stdout)
    assert m, "the colophon carries no version at all"
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert f'version: "{m.group(1)}"' in skill


def test_the_scaffold_carries_no_rule_data_in_another_language():
    """0.1.589 printed D6's Chinese provenance words into the genre card, so
    eight CJK characters shipped inside every English deliverable."""
    out = _run("scripts/ops/new_deck.py", "--no-trace")
    body = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", out.stdout, flags=re.S)
    assert not re.findall(r"[一-鿿]", body)


# --- the shape library's own measurements -----------------------------------

def test_every_unit_publishes_the_attributes_a_use_needs():
    """All 206 origins are non-zero. An author composing against an estimated
    one draws outside the viewBox — `figure_clipped`, and a rebuild round."""
    g = json.loads((ROOT / "assets/shapes/geometry.json")
                   .read_text(encoding="utf-8"))["units"]
    svgs = list((ROOT / "assets/shapes").glob("*.svg"))
    assert len(g) == len(svgs), f"{len(g)} measured, {len(svgs)} on disk"
    for name, unit in g.items():
        assert set(unit["use"]) == {"x", "y", "width", "height"}, name
        assert unit["viewBox"][:2] == [unit["use"]["x"], unit["use"]["y"]], name


def test_the_manifest_matches_the_svg_it_measured():
    g = json.loads((ROOT / "assets/shapes/geometry.json")
                   .read_text(encoding="utf-8"))["units"]
    for name in sorted(g)[:5]:
        svg = (ROOT / f"assets/shapes/{name}.svg").read_text(encoding="utf-8")
        m = re.search(r'viewBox="\s*([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)', svg)
        assert m, f"{name} has no viewBox"
        assert [round(float(v), 2) for v in m.groups()] == g[name]["viewBox"], name


def test_the_scaffold_says_when_a_unit_will_ink_a_thin_figure():
    """160 of the 206 units come in under 55% of the figure box, and the median
    fills 43% — which is the visual share two shipped decks reported. It says
    the number; it does NOT stretch the drawing, which would be 0.1.339's
    withdrawn fill floor in another costume."""
    sys.path.insert(0, str(ROOT / "scripts/ops"))
    import new_deck
    wide = new_deck.shape_fill("p009-arrow-3d-01")
    square = new_deck.shape_fill("p005-2x2-cubed-01")
    assert wide is not None and wide > 90
    assert square is not None and square < 55
    assert "inks about" in new_deck.shape_figure("p005-2x2-cubed-01", "a", "b")
    assert "inks about" not in new_deck.shape_figure("p009-arrow-3d-01", "a", "b")


# --- the locating detail ----------------------------------------------------

def test_the_layout_json_keeps_the_detail_that_names_the_page():
    """It was computed and dropped in both JSON emissions, so an author who
    knew WHICH check failed re-ran the renderer to learn WHICH PAGE."""
    pytest.importorskip(
        "playwright",
        reason="inspect_layout.py renders; see SKILL.md's browser step")
    out = _run("scripts/check/inspect_layout.py", "--deliverable", "--no-sheet",
               "--iterate", "--json", str(ROOT / "fixtures/deck-broken.en.html"))
    doc = json.loads(out.stdout)
    assert doc.get("details"), "no details block"
    failing = [k for k, v in doc["verdicts"].items() if v == "FAIL"]
    assert any(k in doc["details"] for k in failing)
    assert any(re.search(r"\bp\d+\b", d) for d in doc["details"].values())


# --- the driver's stages ----------------------------------------------------

def test_the_driver_restarts_its_own_log(tmp_path):
    """`debug_log init` refuses an existing log, and one run of the driver IS
    one build's record. Without the passthrough every iteration after the first
    died before a single stage ran."""
    deck = tmp_path / "d.en.html"
    for _ in range(2):
        out = _run("scripts/ops/build.py", "--deck", str(deck), "--fast",
                   "--pages", "2", "--debug-log")
        assert "already exists" not in (out.stdout + out.stderr)
    log = json.loads((tmp_path / "d.en.debug.json").read_text(encoding="utf-8"))
    assert log["commands"], "the second run recorded nothing"


def test_one_run_leaves_the_evidence_the_contract_asks_for(tmp_path):
    """`attach` and `assess` were in the contract and called by nobody; the
    reports it wanted were gathered in memory and thrown away."""
    deck = tmp_path / "d.en.html"
    _run("scripts/ops/build.py", "--deck", str(deck), "--fast", "--pages", "2",
         "--debug-log", "--assess", "C1=4:storyline declared",
         "--assess", "C2=3:figures thin")
    log = json.loads((tmp_path / "d.en.debug.json").read_text(encoding="utf-8"))
    assert set(log["checks"]) >= {"design", "prose"}, log["checks"]
    assert {"C1", "C2"} <= set(log["quality"])
    assert log["quality"]["C1"]["score"] == 4
    assert not list(tmp_path.glob(".*reports")), "the scratch dir was left behind"


def test_the_second_round_says_whether_the_repair_landed(tmp_path):
    """One session ran six rounds after its last failure, and nothing could
    tell it so."""
    pytest.importorskip(
        "playwright",
        reason="inspect_layout.py renders; see SKILL.md's browser step")
    deck = tmp_path / "d.en.html"
    _run("scripts/ops/build.py", "--deck", str(deck), "--fast", "--pages", "2")
    out = _run("scripts/ops/build.py", "--deck", str(deck), "--fast", "--pages", "2")
    said = out.stdout + out.stderr
    assert "what moved since the last round" in said, said[-2000:]


# --- the brief --------------------------------------------------------------

def test_the_brief_carries_every_file_the_rules_name():
    out = _run("scripts/ops/brief.py", "--genre", "internal",
               "--storyline", "market-analysis")
    assert out.returncode == 0
    for rel in ("references/brand.md", "references/analysis-rules.md",
                "references/writing-rules.md", "references/build-card.md",
                "references/storyline-templates.md"):
        assert rel in out.stdout, rel
    assert "geometry.json" in out.stdout, "the shape geometry is not pointed at"
    assert "says nothing" in out.stdout, "the card's own warning was dropped"


def test_the_brief_is_not_a_summary():
    """It changes how many round trips the reading costs, not what is read."""
    out = _run("scripts/ops/brief.py", "--genre", "internal",
               "--storyline", "market-analysis", "--full")
    brand = (ROOT / "references/brand.md").read_text(encoding="utf-8")
    assert brand.strip()[:400] in out.stdout


# --- the counter ------------------------------------------------------------

def test_the_counter_dedupes_a_claude_transcript(tmp_path):
    """Claude Code writes one record per content block, each repeating the same
    usage — a per-record sum inflated one build's call count from 70 to 187 and
    every token figure by 2.5-3.6x."""
    t = tmp_path / "s.jsonl"
    rec = {"type": "assistant",
           "message": {"id": "msg_1", "usage": {"output_tokens": 100},
                       "content": [{"type": "tool_use", "name": "Bash"}]}}
    t.write_text("\n".join(json.dumps(rec) for _ in range(3)), encoding="utf-8")
    out = _run("scripts/ops/session_cost.py", "--claude", str(t))
    assert "API calls" in out.stdout
    assert "1" in out.stdout.split("API calls")[1][:20], out.stdout
    assert "300" not in out.stdout, "summed per record instead of per message"


def test_a_self_assessment_survives_the_next_round(tmp_path):
    """`--restart` rebuilds the log each round, so assessments passed on round
    9 were gone by round 12 — and the validator said `ok` about the emptiness.
    A self-score is a judgement about the DOCUMENT, not about one round of
    building it, so it carries forward and a later `--assess` overwrites it.
    """
    deck = tmp_path / "d.en.html"
    _run("scripts/ops/build.py", "--deck", str(deck), "--fast", "--pages", "2",
         "--storyline", "gtm", "--entry-path", "B", "--debug-log",
         "--assess", "C1=4:the storyline is declared and mirrored")
    log = tmp_path / (deck.stem.split(".")[0] + ".debug.json")
    logs = list(tmp_path.glob("*.debug.json"))
    assert logs, "no debug log written"
    log = logs[0]
    first = json.loads(log.read_text())["quality"]
    assert "C1" in first, f"the assessment was not written: {first}"

    # a later round, with no --assess of its own
    _run("scripts/ops/build.py", "--deck", str(deck), "--fast", "--pages", "2",
         "--storyline", "gtm", "--entry-path", "B", "--debug-log")
    kept = json.loads(log.read_text())["quality"]
    assert kept.get("C1", {}).get("score") == 4, (
        f"the previous round's self-assessment was lost: {kept}")


def test_a_later_assessment_overwrites_the_carried_one(tmp_path):
    deck = tmp_path / "d.en.html"
    for score in ("4", "2"):
        _run("scripts/ops/build.py", "--deck", str(deck), "--fast", "--pages", "2",
             "--storyline", "gtm", "--entry-path", "B", "--debug-log",
             "--assess", f"C1={score}:a reason worth recording")
    log = list(tmp_path.glob("*.debug.json"))[0]
    assert json.loads(log.read_text())["quality"]["C1"]["score"] == 2


def test_the_brief_parts_rejoin_to_exactly_the_whole(tmp_path):
    """`--out` must be the same bytes stdout would have carried.

    The joined brief is ~87KB and a harness with a single-output ceiling turns
    it into a 2KB preview, so the tool built to save a round trip cost five.
    The split is only safe if it is a split — if `--out` assembled the text a
    second way the two would drift, and the drift would be invisible.
    """
    whole = _run("scripts/ops/brief.py", "--genre", "internal",
                 "--storyline", "market-analysis").stdout
    out = _run("scripts/ops/brief.py", "--genre", "internal",
               "--storyline", "market-analysis", "--out", str(tmp_path))
    parts = sorted(tmp_path.glob("*.md"))
    assert len(parts) > 3, f"the brief did not split: {parts}"
    joined = "".join(p.read_text(encoding="utf-8") for p in parts)
    assert joined == whole, "the parts are not the bytes stdout carries"
    assert str(tmp_path) in out.stdout and "brief written in" in out.stdout


def test_no_single_brief_part_is_larger_than_the_whole_was(tmp_path):
    """The point is the ceiling. A split that leaves one 80KB part has not
    solved anything."""
    _run("scripts/ops/brief.py", "--genre", "internal", "--storyline",
         "market-analysis", "--out", str(tmp_path))
    sizes = [p.stat().st_size for p in tmp_path.glob("*.md")]
    assert max(sizes) < sum(sizes) / 2, (
        f"one part carries most of the brief: {max(sizes)} of {sum(sizes)}")
