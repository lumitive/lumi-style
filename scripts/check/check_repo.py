#!/usr/bin/env python3
"""Mechanical guards for the invariants this repo maintains by hand.

Covers only what a machine can decide. Whether a rule change was re-flowed into
the three entry points is a reading task and stays with the reviewer.
"""

import ast
import json
import pathlib

# --- scripts path bootstrap (canonical; the bootstrap guard enforces this) ---
# Bare-name sibling imports must resolve from any drawer depth: walk up to
# the scripts/ root and APPEND it and its drawers to sys.path — append,
# never insert(0), so the standard library and the caller's environment
# always win. Drawer order is lib-first and the scripts ROOT LAST on
# purpose: the emergency path overwrites a PR's lib/ files with trusted
# copies, and lib-first means a file PLANTED at the scripts root can never
# outrank them (the shadowing the PR #92 review demonstrated).
import pathlib as _bs_pathlib  # noqa: E402
import re
import subprocess
import sys
import sys as _bs_sys  # noqa: E402
import traceback
from typing import cast

_SCRIPTS_ROOT = next(p for p in _bs_pathlib.Path(__file__).resolve().parents
                     if p.name == "scripts")
for _sub in ("lib", "render", "check", "build", "ops", ""):
    _p = str(_SCRIPTS_ROOT / _sub) if _sub else str(_SCRIPTS_ROOT)
    if _p not in _bs_sys.path:
        _bs_sys.path.append(_p)
del _bs_pathlib, _bs_sys, _SCRIPTS_ROOT, _sub, _p
# --- end bootstrap ---

import check_privacy  # noqa: E402 — the OR-8 terms reader, shared
import color_math  # noqa: E402 — after the bootstrap, deliberately
import deliverable_registry  # noqa: E402 — the storyline vocabulary, for prompt parity
import gating  # noqa: E402
import secret_patterns  # noqa: E402 — the one credential table, shared with check_privacy
import stamps  # noqa: E402 — after the bootstrap
import trace_schema  # noqa: E402 — the one definition, shared with scripts/ops/trace.py
from css_tokens import css_block, css_vars  # noqa: E402, F401 — css_block is API for tests/tools

ROOT = next(p for p in pathlib.Path(__file__).resolve().parents
            if p.name == "scripts").parent

# CJK is permitted only where it is rule *data* for Chinese-language output.
# Anywhere else it breaks the English-only repository red line.
CJK_ALLOWED = {
    "AGENTS.md",
    # The skill's own trigger phrase, "按 LUMI 风格", so a Chinese-speaking user
    # can invoke it. Rule DATA in the strictest sense: it is the string a user
    # types. These three are GENERATED from SKILL.md's description, so the
    # phrase has one origin and three restatements — allowing the artifacts
    # without allowing the source would fail the file nobody can edit.
    ".claude-plugin/marketplace.json",
    ".claude-plugin/plugin.json",
    ".well-known/skills/index.json",
    # The geography registries' bilingual names. Every `z` field is what
    # `regionmap_svg.py --labels zh` and the globe render onto a Chinese map,
    # so they are rule data for Chinese-language output in the most literal
    # sense the red line allows: the string a Chinese reader sees on the
    # figure. Deleting them would not make the repository more English; it
    # would make the Chinese map wrong.
    "assets/vectors/regions-trade.json",
    "assets/vectors/regions.json",
    "assets/vectors/world-110m.json",
    "SKILL.md",
    "prompts/lumi-style-core.md",
    "references/writing-rules.md",
    # The reviewer-facing wording of the C1-C7 evidence items. Rule DATA in the
    # same sense as the Chinese ban list above: eval-rubric.md requires the
    # items to be written in the reviewer's language, so the sheet's text is
    # part of the rule rather than repository prose.
    "scripts/lib/rubric_items.py",
}
CJK = re.compile(r"[㐀-䶿一-鿿豈-﫿]")

# design-tokens.json palette key -> the CSS custom property that carries it.
# A new palette key on either side must be added here, which is what forces the
# two files to be edited together.
PALETTE_KEY_TO_VAR = {
    "bg": "bg",
    "ink": "nw",
    "accent": "acc",
    "accent_deep": "acc-deep",
    "accent_inbox": "acc-inbox",
    "accent_wash": "acc-wash",
    "on_accent": "on-acc",
    "seal": "seal",
    "seal_text": "seal-t",
    "seal_wash": "seal-wash",
    "amber": "amber",
    "amber_wash": "amber-wash",
    "brass": "brass",
    "brass_wash": "brass-wash",
    "light_ramp_5": "acc-5",
    "light_ramp_4": "acc-4",
    "light_ramp_3": "acc-3",
    "light_ramp_2": "acc-2",
    "light_ramp_1": "acc-1",
    "on_light_ramp_5": "on-acc-5",
    "on_light_ramp_low": "on-acc-lo",
    "lime": "lime",
    "on_lime": "on-lime",
    "data_blue": "d-blue",
    "data_red": "d-red",
    "data_teal": "d-teal",
    "card_bg": "card-bg",
    "accent_live": "acc-live",
    "accent_tint": "acc-tint",
}
PALETTE_NON_COLOR = {"ladder_base", "note", "text_ladder", "rule_ladder"}

# v0.1.338: the ladder is two ladders, and each palette carries its own alphas.
# Until 0.1.337 one shared alpha list served both canvases, and this guard enforced
# the sharing — which is how a ladder measuring 1.81:1 on light shipped as the
# colour of every page number in a deck. Ladder name -> (json key, css prefix).
LADDERS = {"text": ("text_ladder", "tx"), "rule": ("rule_ladder", "ln")}

VERSION = re.compile(r"\b(\d+\.\d+\.\d+)\b")


# Prose this repository publishes, whatever it is written in. Markdown was the
# only answer until 0.1.386, when a rule document was converted to HTML and
# silently left the english-only and stale-promise guards behind — a conversion
# that reduces coverage is a conversion that should have said so.
PROSE_GLOBS = ("*.md",)  # the one tracked backlog render was deleted at 0.1.436


def md_files():
    seen: dict[pathlib.Path, None] = {}
    for pattern in PROSE_GLOBS:
        for p in ROOT.rglob(pattern) if "/" not in pattern else ROOT.glob(pattern):
            # Skip .git AND every other dot-directory. This walks the
            # filesystem rather than git's index, so anything checked out under
            # the tree is scanned as if it belonged to it — and a Claude Code
            # worktree at .claude/worktrees/ is a full copy of this repository
            # at an older version. It failed the version-citation, english-only
            # and stale-promise guards seventeen ways at once, all of them true
            # of a checkout nobody was editing. gitignoring it was not enough:
            # a guard that reads the disk has to be told what the disk is for.
            if any(part.startswith(".") for part in p.relative_to(ROOT).parts[:-1]):
                continue
            seen[p] = None
    return sorted(seen)


def rel(path):
    return str(path.relative_to(ROOT))


# css_block / css_vars moved to css_tokens.py (0.1.420) — one CSS reader,
# fixed once; the 0.1.415 comment-stripping story lives on its docstring.


def check_versions():
    """One version across the repo: SKILL.md, CHANGELOG, and all three tokens/
    headers carry the same number, so a rule revision bumps all five together."""
    errors = []
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    m = re.search(r"^\s*version:\s*[\"']?(\d+\.\d+\.\d+)", skill, re.M)
    if not m:
        return ["SKILL.md: no metadata.version found in frontmatter"]
    skill_version = m.group(1)

    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    released = re.findall(r"^##\s+(\d+\.\d+\.\d+)", changelog, re.M)
    if not released:
        return ["CHANGELOG.md: no '## X.Y.Z' release headings found"]

    if skill_version != released[0]:
        errors.append(
            f"SKILL.md metadata.version ({skill_version}) != newest CHANGELOG "
            f"entry ({released[0]}); a rule revision bumps both together"
        )

    token_versions = {}
    for name, pattern in TOKEN_STAMPS:
        text = (ROOT / name).read_text(encoding="utf-8")
        found = re.search(pattern, text)
        if not found:
            errors.append(f"{name}: no version stamp found in its header")
            continue
        token_versions[name] = found.group(1)

    if len(set(token_versions.values())) > 1:
        errors.append(
            f"the tokens/ files carry different versions ({token_versions}); they "
            f"mirror one design language, so they bump together"
        )
    for name, version in token_versions.items():
        if version not in released:
            errors.append(f"{name}: version {version} has no CHANGELOG entry")
        elif version != skill_version:
            errors.append(
                f"{name}: version {version} != skill version {skill_version}; "
                f"tokens carry the skill version, so all five stamps bump together"
            )
    return errors


def _strip_code(line, in_fence):
    """Remove fenced and inline code from a line, returning (prose, in_fence).

    Code spans are where a rule file quotes a string as *data*: a banned phrase,
    a punctuation example, the source text of a thesis. Prose is everything else.
    """
    if line.lstrip().startswith("```"):
        return "", not in_fence
    if in_fence:
        return "", in_fence
    return re.sub(r"`[^`]*`", " ", line), in_fence



# The one exempt field, matched WHOLE. `.endswith(".quote")` also
# matched `rules[0].notes.quote`, a key nothing in the register reads.
REGISTER_QUOTE = re.compile(r"\$\.rules\[\d+\]\.quote")


def _json_manifests():
    """-> the tracked .json files this repository writes by hand or generates.

    Tracked, so a local scratch file is not scanned; and json only, because the
    prose globs already cover markdown. Traces are excluded: `evals/traces/`
    is machine-written against a closed schema that has nowhere to put prose.
    """
    if not (ROOT / ".git").exists():
        return []
    p = subprocess.run(["git", "ls-files", "-z", "--", "*.json"],
                       cwd=ROOT, capture_output=True, text=True)
    if p.returncode != 0:
        return []
    out = []
    for f in p.stdout.split("\0"):
        if not f or f.startswith("evals/traces/"):
            continue
        out.append(ROOT / f)
    return sorted(out)



def _walk_strings(node, where="$"):
    """-> (key path, string) for every string value anywhere in a JSON tree."""
    if isinstance(node, str):
        yield where, node
    elif isinstance(node, dict):
        for k, v in node.items():
            yield from _walk_strings(v, f"{where}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _walk_strings(v, f"{where}[{i}]")


def check_english_only():
    """Repository language is English. CJK appears only as quoted data.

    The allowlist used to be per file, which is too coarse in both directions: it
    let prose drift into an allowlisted file, and it forced a whole file onto the
    list for one quoted line. Outside the allowlist, CJK is now permitted inside
    backticks or a fenced block and nowhere else — which is exactly the
    distinction the red line always meant. `references/brand.md` quotes the
    source text of the brand thesis that way; every sentence around it is
    English, so the file stays readable on a platform that renders CJK poorly.
    """
    errors = []
    # TRACKED JSON MANIFESTS TOO, not markdown alone. `check_stale_promises`
    # learned this one guard over — "every text scan in this file globs *.md",
    # so a registry promised work that had already landed, unread — and the
    # lesson was not carried across. `assets/shapes/tags.json` carried 70
    # Chinese descriptions of shapes in a repository whose first red line is
    # that it is written in English. Not rule data for Chinese output: notes
    # about geometry, in a tracked file, invisible to the guard that exists to
    # find exactly that.
    for path in _json_manifests():
        if rel(path) in CJK_ALLOWED:
            continue
        # PARSED, not scanned. A raw text scan misses `\u6837\u5f0f` — valid
        # JSON for the same characters, with no CJK byte in the file — which is
        # how a manifest could hold Chinese prose and read as English to the
        # guard. Line numbers are lost and the key path replaces them; for a
        # manifest that is the more useful address anyway.
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue                      # the parse guards report their own
        for where, value in _walk_strings(doc):
            if not CJK.search(value):
                continue
            # ONE EXEMPTION, AND IT IS VERIFIED SOMEWHERE ELSE. The rule
            # register's `quote` field holds a VERBATIM substring of the rule
            # line it cites, and two of the rules it covers are about Chinese
            # output — the zh ban list and the one permitted collocation. A
            # quote of rule data is rule data. Refusing it would not remove
            # Chinese from this repository; it would remove those two rules
            # from the register, which is the coverage map, in the one place
            # coverage is hardest to see.
            #
            # THE EXEMPTION IS EXACTLY `$.rules[N].quote`, matched whole. It
            # was `.endswith(".quote")` at any depth, so a nested
            # `rules[0].notes.quote` — a key the register's own reader ignores
            # — carried a paragraph of Chinese prose through both guards. And it
            # holds only for a quote cited out of a PROSE RULE FILE: `source`
            # was unrestricted, so a sentence lifted from a Chinese HTML fixture
            # passed too, which is deliverable prose and not rule data at all.
            #
            # With both narrowed it is not a hole: `check_rule_coverage.py`
            # fails the build unless every quote is still a substring of the
            # line it names, and the line has to be in a file the markdown half
            # of this guard already reads. Nothing else in the file is exempt —
            # the `gist` is this repository's own English and is scanned.
            if (rel(path) == "evals/rule-coverage.json"
                    and REGISTER_QUOTE.fullmatch(where)):
                continue
            errors.append(
                f"{rel(path)}: CJK at {where} — a manifest is not rule "
                f"data for Chinese output; the repository language is "
                f"English.")
    for path in md_files():
        name = rel(path)
        if name in CJK_ALLOWED:
            continue
        in_fence = False
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            prose, in_fence = _strip_code(line, in_fence)
            if CJK.search(prose):
                errors.append(
                    f"{name}:{lineno}: CJK in prose (repository language is English; "
                    f"quote it in backticks if it is rule data)"
                )
    return errors


def _gh_slug(heading):
    """GitHub's anchor slugger, the parts that matter here: lowercase, strip
    everything but word characters/spaces/hyphens, spaces to hyphens WITHOUT
    collapsing runs — '0 · Output language' becomes '0--output-language'
    (the '·' vanishes, its two flanking spaces both survive as hyphens).
    Getting this wrong is how 0.1.441 shipped 28 dead Contents anchors."""
    s = re.sub(r"[^\w\s-]", "", heading.strip().lower())
    return re.sub(r"\s", "-", s)


def _anchors_of(path):
    text = path.read_text(encoding="utf-8")
    slugs = set()
    for m in re.finditer(r"^#{1,6}\s+(.*)$", text, re.M):
        slugs.add(_gh_slug(m.group(1)))
    return slugs


# Rule-family ids, frozen at 0.1.461. An id names a family for as long as the
# family exists; it is never reused for a different one and never renumbered
# when sections move. Adding a family adds an id here and in the reference file.
FROZEN_RULE_IDS = (
    "BR-1", "BR-2", "BR-3", "BR-4", "BR-5", "BR-6",
    "DR-1", "DR-2", "DR-3", "DR-4", "DR-5", "DR-6", "DR-7", "DR-8", "DR-9", "DR-10", "DR-11",
    "WR-1", "WR-2", "WR-3", "WR-4", "WR-5", "WR-6", "WR-7", "WR-8", "WR-9",
    "ST-1", "ER-1", "OR-1", "OR-2", "OR-7", "OR-8", "OR-9", "OR-10",
)

def check_trace_schema():
    """Every stored trace validates against the schema `trace.py` defines.

    The schema is IMPORTED from scripts/lib/trace_schema.py rather than
    restated here — and it lives in lib/ rather than beside the CLI so the
    emergency-merge closure does not have to reach into scripts/ops/.
    A second copy of a field list is the defect this repository spends most of
    its releases fixing, and a schema guard that carried its own copy would be
    the purest instance of it.

    An empty evals/traces/ is a legal state, not a vacuous pass. **The
    repository now ships one**, from the first real build to open a trace; the
    sentence here said it shipped none for three releases after that stopped
    being true, which is the drift this file exists to catch happening inside
    the file that catches it. A trace is safe to ship because the schema is
    closed — genre, storyline, machine-written verdicts and nothing a client
    could be named in. What must not happen is a stored trace carrying free
    text or a verdict nobody measured, which is red line 9 held by a schema
    instead of by good intentions. The synthetic tests in
    tests/test_check_repo_guards_wave4.py are what prove this can fail; for
    two releases that claim pointed at tests of the LIBRARY instead.
    """
    if not trace_schema.FIELDS:
        return ["trace_schema defines no FIELDS — the guard would pass vacuously"]

    traces = ROOT / "evals" / "traces"
    if not traces.exists():
        return []
    errors = []
    for path in sorted(traces.glob("*.json")):
        try:
            rec = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{rel(path)}: not valid JSON ({exc})")
            continue
        for problem in trace_schema.validate(rec):
            errors.append(f"{rel(path)}: {problem}")
    return errors

def check_rule_ids():
    """Every rule family carries a unique, position-independent id.

    The point of the id is that it does NOT move when sections do. The first
    version derived it from the section number, which defeats that exactly —
    a reorder would have renumbered every id, and §1.1 and §1.2 collapsed to
    `DR-11` and `DR-12`, colliding with a future eleventh section. Ids are now
    assigned in document order once and frozen: an id is a name, not an address.

    This checks uniqueness and format, and that no id already recorded in
    FROZEN_RULE_IDS has vanished — a cited id that stops existing is the same
    class of breakage as a moved section citation, one level up.
    """
    ids: dict[str, str] = {}
    errors = []
    for ref in sorted((ROOT / "references").glob("*.md")):
        text = ref.read_text(encoding="utf-8")
        for m in re.finditer(r"^\*Serves:.*?· id `([A-Z]{2}-\d+)`", text, re.M):
            rid = m.group(1)
            lineno = text.count("\n", 0, m.start()) + 1
            if rid in ids:
                errors.append(f"{rel(ref)}:{lineno}: rule id {rid} is already used by "
                              f"{ids[rid]}")
            ids[rid] = f"{rel(ref)}:{lineno}"
        for m in re.finditer(r"^\*Serves:(?!.*· id `)", text, re.M):
            lineno = text.count("\n", 0, m.start()) + 1
            errors.append(f"{rel(ref)}:{lineno}: rule family declares a parent but no id")
    if not ids:
        return ["no rule ids found — the guard would pass vacuously"]
    missing = sorted(set(FROZEN_RULE_IDS) - set(ids))
    if missing:
        errors.append(f"rule id(s) that existed and no longer do: {missing}. "
                      f"An id is frozen once assigned; retire it in the ledger "
                      f"rather than deleting it.")
    return errors

def check_red_line_parity():
    """AGENTS.md's hand-written red-line summary still covers SKILL.md's list.

    SKILL.md is the home; the generated entry points already lift the block
    from it rather than restating it. AGENTS.md is deliberately hand-written
    (assembled prose is worse prose, and it is a file people read), so it gets
    a parity guard instead of generation.

    The anchor terms are DERIVED from SKILL.md, never listed here: a guard that
    hand-lists the things it checks becomes a third copy of the very thing it
    exists to keep in sync. For each red line, the anchor is the longest word
    of six letters or more that appears in that line and in no other, which is
    the words a summary cannot ALL drop and still be about the same rule.

    It asks for ANY one of them, not a specific one. The first version demanded
    the single longest and immediately fired on a summary that says "standard
    Chinese term" where SKILL.md says "established Chinese term" — the same rule
    in different words. Tightening a checker until a correct paraphrase fails
    turns it into a machine that edits prose to satisfy itself, and the "fix"
    would have been to insert a word into AGENTS.md for no reader's benefit.

    The limit this leaves: a summary that rewords EVERY distinguishing word of
    one rule reads to this guard exactly like a summary that dropped it. That
    is the price of tolerating paraphrase, and it is the right side to err on —
    a false pass costs a stale summary, a false failure costs the prose itself.
    """
    skill = ROOT / "SKILL.md"
    agents = ROOT / "AGENTS.md"
    if not (skill.exists() and agents.exists()):
        return ["SKILL.md or AGENTS.md is missing — the parity guard has no sides"]
    st = skill.read_text(encoding="utf-8")
    m = re.search(r"^## (\w+) non-negotiable red lines.*?$(.*?)(?=^## )",
                  st, re.M | re.S)
    if not m:
        return ["SKILL.md has no red-line block — the parity guard would pass vacuously"]
    items = re.findall(r"^\d+\. (.+?)(?=^\d+\. |\Z)", m.group(2), re.M | re.S)
    if not items:
        return ["SKILL.md's red-line block lists no numbered items"]

    errors = []
    spelled = {2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six",
               7: "Seven", 8: "Eight", 9: "Nine"}.get(len(items))
    if m.group(1) != spelled:
        errors.append(f"SKILL.md says '{m.group(1)} non-negotiable red lines' "
                      f"but lists {len(items)}")

    at = agents.read_text(encoding="utf-8")
    ah = re.search(r"\*\*(\w+) hard red lines\*\*", at)
    # Scope the search to the summary paragraph. Searching the whole file made
    # the drop test unfireable: AGENTS.md is long enough that some word from
    # any red line turns up somewhere else in it, so a summary could lose a
    # rule entirely and still pass — a check that cannot fail for the thing it
    # exists to catch (FM-01).
    block = ""
    if ah:
        rest = at[ah.start():]
        end = rest.find("\n\n")
        block = rest[:end if end > 0 else len(rest)]
    if not ah:
        errors.append("AGENTS.md has no '**N hard red lines**' summary to check")
    elif ah.group(1) != spelled:
        errors.append(f"AGENTS.md says '{ah.group(1)} hard red lines' but SKILL.md "
                      f"lists {len(items)}")

    words = [{w.lower() for w in re.findall(r"[A-Za-z]{6,}", it)} for it in items]
    low = block.lower()
    for i, ws in enumerate(words, 1):
        unique = ws - set().union(*(w for j, w in enumerate(words, 1) if j != i))
        if not unique:
            continue                      # no word distinguishes it; nothing to anchor on
        if not any(w in low for w in unique):
            shown = ", ".join(sorted(unique, key=len, reverse=True)[:5])
            errors.append(f"AGENTS.md's summary drops red line {i}: none of "
                          f"SKILL.md's distinguishing words appear in it ({shown})")
    return errors

def check_principle_trace():
    """Every rule family in references/ declares the clause it serves.

    The clause set is read from PRINCIPLES.md rather than hard-coded, so adding
    a seventh clause needs no edit here and citing a clause that does not exist
    fails. `GOAL` is a legitimate parent — it means the family serves the
    product's purpose rather than a constitutional clause, and forcing those
    families under a clause would produce strained parentage and a traceability
    chain worth nothing.

    THE LIMIT, stated here because a guard that looks stronger than it is will
    be trusted for more than it does: this verifies that a declaration exists
    and names a real clause. **It cannot verify the right parent was chosen.**
    It stops orphans, not misclassification — which stays a human judgement, in
    the same class as every other semantic drift between prose copies.
    """
    principles = ROOT / "references" / "PRINCIPLES.md"
    if not principles.exists():
        return ["references/PRINCIPLES.md is missing — the trace has no root"]
    clauses = set(re.findall(r"^\*\*(P-\d+) · ", principles.read_text(encoding="utf-8"), re.M))
    if not clauses:
        return ["references/PRINCIPLES.md declares no clauses — "
                "the guard would pass vacuously"]
    valid = clauses | {"GOAL"}

    errors = []
    declared_any = False
    for ref in sorted((ROOT / "references").glob("*.md")):
        if ref.name in ("PRINCIPLES.md", "eval-inventory.md"):
            continue          # the constitution itself; the inventory is generated
        text = ref.read_text(encoding="utf-8")
        lines = text.split("\n")
        file_level = any(ln.startswith("*Serves:") for ln in lines[:12])
        for i, line in enumerate(lines):
            m = re.match(r"^#{2,3} (\d+(?:\.\d+)?[a-z]?) · ", line)
            if not m:
                continue
            window = "\n".join(lines[i + 1:i + 4])
            got = re.search(r"^\*Serves: \*\*(P-\d+|GOAL)\*\*", window, re.M)
            if not got:
                if file_level:
                    continue   # the whole file declared one parent
                errors.append(f"{rel(ref)}:{i + 1}: §{m.group(1)} declares no parent "
                              f"(add `*Serves: **P-n**.*` or `*Serves: **GOAL**.*`)")
                continue
            declared_any = True
            if got.group(1) not in valid:
                errors.append(f"{rel(ref)}:{i + 1}: §{m.group(1)} serves "
                              f"{got.group(1)}, which PRINCIPLES.md does not define")
    # EVERY reference file's declarations, not two named ones. The hard-coded
    # pair meant a file-level `*Serves: **P-99**` in operating-rules.md — a
    # clause that does not exist — passed, while the identical plant in
    # eval-rubric.md failed. A guard with a file list is a guard that stops
    # covering the next file somebody adds.
    for ref in sorted((ROOT / "references").glob("*.md")):
        if ref.name in ("PRINCIPLES.md", "eval-inventory.md"):
            continue
        for m in re.finditer(r"\*Serves: \*\*([A-Za-z0-9-]+)\*\*",
                             ref.read_text(encoding="utf-8")):
            declared_any = True
            if m.group(1) not in valid:
                errors.append(f"{rel(ref)}: a declaration names {m.group(1)}, "
                              f"which PRINCIPLES.md does not define")
    if not declared_any:
        errors.append("no rule family declares a parent — the guard would pass vacuously")
    return errors

def check_section_citations():
    """Every `<reference>.md §N` citation names a section that exists.

    P0's reorder of design-rules.md moved five sections and renumbered the
    chart rules, and every guard stayed green while twenty-one citations
    across SKILL.md, four scripts and two token files pointed at the wrong
    section. `check_links` only sees markdown link syntax; a §-citation in
    prose or in a code comment is invisible to it. CHANGELOG.md is exempt by
    construction: its entries cite the numbering that was true when they were
    written, and history is not re-flowed. specs/ is exempt for the same
    reason — a spec is a record of a decision, not a live pointer. `tests/` is
    exempt because its fixtures cite broken sections ON PURPOSE: the test that
    proves this guard can fail has to contain the citation it rejects, and a
    checker that edits its own evidence is worse than no checker.
    """
    import collections
    sections = collections.defaultdict(set)
    for ref in sorted((ROOT / "references").glob("*.md")):
        for m in re.finditer(r"^#{2,4} (\d+(?:\.\d+)?[a-z]?) ", ref.read_text(encoding="utf-8"), re.M):
            sections[ref.name].add(m.group(1))
    if not sections:
        return ["no reference files found — the citation guard would pass vacuously"]

    # Citations live in prose, in script comments and in token-file comments,
    # so this walks more than md_files() does — same dot-directory rule.
    candidates = []
    for suffix in ("*.md", "*.py", "*.css", "*.json"):
        for q in ROOT.rglob(suffix):
            if any(part.startswith(".") for part in q.relative_to(ROOT).parts[:-1]):
                continue
            candidates.append(q)

    errors = []
    cite = re.compile(r"([a-z-]+\.md)[^\n]{0,40}?§\s*(\d+(?:\.\d+)?[a-z]?)")
    for path in sorted(set(candidates)):
        rel = path.relative_to(ROOT).as_posix()
        if rel == "CHANGELOG.md" or rel.startswith(("specs/", "tests/")):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for m in cite.finditer(text):
            fname, sec = m.group(1), m.group(2)
            if fname not in sections:
                continue
            if sec not in sections[fname]:
                lineno = text.count("\n", 0, m.start()) + 1
                errors.append(f"{rel}:{lineno}: cites {fname} §{sec}, which has no such section")
    return errors

def check_links():
    """Relative link targets exist — and since 0.1.442, in-page and
    cross-file ANCHORS resolve too (the class check_links was blind to when
    the 0.1.441 Contents blocks shipped dead)."""
    errors = []
    for path in md_files():
        text = path.read_text(encoding="utf-8")
        for m in re.finditer(r"\]\(([^)]+)\)", text):
            target = m.group(1).split()[0]
            lineno = text.count("\n", 0, m.start()) + 1
            if re.match(r"^(https?:|mailto:)", target):
                continue
            if target.startswith("#"):
                if target[1:] not in _anchors_of(path):
                    errors.append(f"{rel(path)}:{lineno}: in-page anchor "
                                  f"{target} matches no heading")
                continue
            base, _, frag = target.partition("#")
            resolved = (path.parent / base).resolve()
            if not resolved.exists():
                errors.append(f"{rel(path)}:{lineno}: link target does not exist: {target}")
            elif frag and resolved.suffix == ".md" and frag not in _anchors_of(resolved):
                errors.append(f"{rel(path)}:{lineno}: anchor #{frag} matches "
                              f"no heading in {base}")
    return errors


def check_palette_parity():
    """Every palette value in design-tokens.json must be the value the CSS
    actually resolves to, accounting for body.dark inheriting from :root."""
    errors = []
    tokens = json.loads((ROOT / "tokens/design-tokens.json").read_text(encoding="utf-8"))
    css = (ROOT / "tokens/lumi-theme.css").read_text(encoding="utf-8")

    light_vars = css_vars(css_block(css, ":root {"))
    dark_vars = dict(light_vars)
    dark_vars.update(css_vars(css_block(css, "body.dark {")))
    resolved = {"light": light_vars, "dark": dark_vars}

    for palette_name, palette in tokens["palette"].items():
        if not isinstance(palette, dict):
            continue
        variables = resolved[palette_name]
        for key, value in palette.items():
            if key in PALETTE_NON_COLOR:
                continue
            var = PALETTE_KEY_TO_VAR.get(key)
            if var is None:
                errors.append(
                    f"tokens/design-tokens.json: palette.{palette_name}.{key} has no CSS "
                    f"counterpart mapped in {pathlib.Path(__file__).name}"
                )
                continue
            actual = variables.get(var)
            if actual is None:
                errors.append(
                    f"tokens/lumi-theme.css: --{var} is not defined for the "
                    f"{palette_name} palette (design-tokens.json expects {value})"
                )
            elif actual.lower() != value.lower():
                errors.append(
                    f"palette.{palette_name}.{key}: design-tokens.json says {value}, "
                    f"tokens/lumi-theme.css --{var} says {actual}"
                )

        base = re.match(r"rgba\(([\d,\s]+),ALPHA\)", palette["ladder_base"])
        if not base:
            errors.append(
                f"tokens/design-tokens.json: palette.{palette_name}.ladder_base is not "
                f"in the form rgba(r,g,b,ALPHA)"
            )
            continue
        channels = base.group(1).replace(" ", "")
        for ladder, (json_key, prefix) in LADDERS.items():
            alphas = palette.get(json_key)
            if not alphas:
                errors.append(
                    f"tokens/design-tokens.json: palette.{palette_name}.{json_key} is "
                    f"missing; each palette carries its own {ladder} ladder since 0.1.338"
                )
                continue
            for i, alpha in enumerate(alphas, 1):
                var = f"{prefix}{i}"
                actual = variables.get(var)
                if actual is None:
                    errors.append(
                        f"tokens/lumi-theme.css: --{var} missing for the {palette_name} "
                        f"{ladder} ladder (design-tokens.json lists alpha {alpha})"
                    )
                    continue
                got = re.match(r"rgba\(([\d,\s]+),\s*(0?\.\d+|1|0)\)",
                               actual.replace(" ", ""))
                if not got or got.group(1) != channels or float(got.group(2)) != alpha:
                    errors.append(
                        f"tokens/lumi-theme.css: --{var} is {actual}, expected "
                        f"rgba({channels},{alpha}) for the {palette_name} {ladder} ladder"
                    )
    # The reverse direction (0.1.443). This guard walked JSON→CSS only, so a
    # colour the CSS defined and the JSON never heard of was invisible to it:
    # --acc-live and --acc-tint shipped in the theme through dozens of releases
    # while design-tokens.json, whose job is to mirror the palette, carried
    # neither — and the 0.1.442 owner review traced a three-greens defect
    # straight through that hole. Every colour-valued custom property the
    # theme's palette blocks declare must be reachable from the JSON: through
    # the key map or as a generated ladder step. A mirror runs both ways.
    mapped_vars = set(PALETTE_KEY_TO_VAR.values())
    ladder_step = re.compile(r"^(tx|ln)\d$")
    # WHAT IS NOT A COLOUR, rather than what is. An allow-list of colour
    # syntaxes (`#`, `rgb(`, `rgba(`) would skip a token written as `oklch()`,
    # `hsl()` or `color-mix()` — and this package already uses `color-mix` in
    # its layout file, so one such token in a palette block would slip the
    # mirror silently: the same one-way blindness this walk was added to close.
    not_colour = re.compile(r"^(-?[\d.]+(px|em|rem|svh|vh|vw|%|s|ms)?$|var\(|"
                            r"['\"]|normal$|none$|inherit$|[\w-]+,)")
    for opener, palette_name in ((":root {", "light"), ("body.dark {", "dark")):
        for var, value in css_vars(css_block(css, opener)).items():
            if not_colour.match(value.strip()):
                continue
            if var in mapped_vars or ladder_step.match(var):
                continue
            errors.append(
                f"tokens/lumi-theme.css: --{var} ({palette_name}: {value}) is a "
                f"colour design-tokens.json does not carry — the mirror runs "
                f"both ways"
            )
    errors.extend(_check_contrast_floor(tokens))
    return errors


def _check_contrast_floor(tokens):
    """Every text-ladder step must clear the documented floor against both
    surfaces of its own palette. This is the guard that would have caught the
    0.1.337 defect: the alphas were legal, they were simply unreadable."""
    floor = tokens["contrast"]["floor_text"]
    errors = []
    for palette_name, palette in tokens["palette"].items():
        if not isinstance(palette, dict):
            continue
        base = cast(re.Match[str],
                    re.match(r"rgba\(([\d,\s]+),ALPHA\)", palette["ladder_base"]))
        ink = tuple(int(c) for c in base.group(1).replace(" ", "").split(","))
        for surface_key in ("bg", "card_bg"):
            surface = color_math.hex_to_rgb(palette[surface_key])
            ls = color_math.luma255(surface)
            for i, alpha in enumerate(palette["text_ladder"], 1):
                mixed = color_math.mix255(ink, surface, alpha)
                lm = color_math.luma255(mixed)
                ratio = color_math.contrast_from_luma(ls, lm)
                if ratio < floor:
                    errors.append(
                        f"contrast: palette.{palette_name}.text_ladder[{i - 1}] "
                        f"(--tx{i}, alpha {alpha}) measures {ratio:.2f}:1 on "
                        f"{surface_key}, below the {floor}:1 text floor"
                    )
    return errors


# A custom property may be referenced without being defined only with a reason.
# Same contract as check_prose.py's NOT_MECHANIZED and the waiver dicts below: a
# documented exception is a reviewable state, an undocumented one is a defect
# nobody noticed. Empty on purpose — every knob tokens/ reaches for today either
# ships or carries a literal fallback.
UNDEFINED_VAR_WAIVERS: dict[str, str] = {}


def _css_without_comments(css):
    """Blank the comments and keep the line count. Collapsing a block comment to
    one space shifts every line number after it — and the comments in tokens/ are
    longer than the rules, so the first version of this pointed 40 lines above
    the defect it had found."""
    return re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group(0).count("\n"), css, flags=re.S)


def _var_calls(css):
    """Every var() in `css` as (name, fallback, offset), with nesting preserved.

    Written by hand rather than as one regex because the fallback may itself
    contain a var(), and that nesting is precisely the case this guard exists
    for: `var(--display, var(--sans))` is invalid when *neither* name resolves,
    and a regex that stops at the first `)` cannot see the inner one.
    """
    out = []
    for m in re.finditer(r"var\(", css):
        depth, i = 1, m.end()
        while depth and i < len(css):
            if css[i] == "(":
                depth += 1
            elif css[i] == ")":
                depth -= 1
            i += 1
        inner = css[m.end():i - 1]
        name, _, fallback = inner.partition(",")
        out.append((name.strip(), fallback.strip(), m.start()))
    return out


def check_token_references():
    """Every var() in tokens/ resolves to a custom property tokens/ defines.

    An undefined custom property with no fallback is not a soft default — the
    declaration is invalid at computed-value time and the property inherits,
    silently, whatever was above it. This repository has now shipped that defect
    twice: `var(--display, var(--sans))` on the one number that IS the page
    (0.1.352, both names undefined, so the fallback chain saved nothing), and
    `var(--accent)` on the footer origin line and on the emphasis inside a
    display number (0.1.367 — the accent has been `--acc` since the palette
    existed). Both names were read out of a deliverable's private CSS, which is
    the reverse drift CLAUDE.md names, spelled in custom properties instead of
    class selectors.

    A fallback is honoured, and honoured recursively: `var(--x, 22deg)` declares
    an optional knob and is fine, `var(--x, var(--y))` is fine only if --y
    resolves. Nothing here reads a *deliverable* — a document is free to define
    its own names; these two files are the palette, and they may not reach for a
    name the package does not ship.
    """
    files = sorted((ROOT / "tokens").glob("*.css"))
    if not files:
        return ["tokens/: no CSS to check; this guard would pass vacuously"]

    sources = {rel(p): _css_without_comments(p.read_text(encoding="utf-8")) for p in files}
    defined = set()
    for css in sources.values():
        defined.update(re.findall(r"(--[\w-]+)\s*:", css))

    def resolves(name, fallback):
        if name in defined or name in UNDEFINED_VAR_WAIVERS:
            return True
        if not fallback:
            return False
        nested = _var_calls(fallback)
        if not nested:
            return True                    # a literal fallback always resolves
        return all(resolves(n, f) for n, f, _ in nested)

    errors, seen = [], set()
    for name, css in sources.items():
        for var, fallback, offset in _var_calls(css):
            if resolves(var, fallback):
                continue
            lineno = css.count("\n", 0, offset) + 1
            if (name, var) in seen:
                continue
            seen.add((name, var))
            errors.append(
                f"{name}:{lineno}: var({var}) — no tokens/ file defines {var} and the "
                f"reference carries no literal fallback, so the declaration is invalid "
                f"at computed-value time and the property silently inherits"
            )
    # A waiver earns its place only while its cause is live: the name must be
    # referenced AND still undefined. Written as a plain set difference this read
    # the second half backwards and kept quiet about a waiver whose property had
    # since been shipped — the one state where the waiver is certainly dead.
    referenced = {v for css in sources.values() for v, _, _ in _var_calls(css)}
    for waived in sorted(UNDEFINED_VAR_WAIVERS):
        if waived in referenced and waived not in defined:
            continue
        why = ("no tokens/ file references it" if waived not in referenced
               else "tokens/ now defines it")
        errors.append(
            f"UNDEFINED_VAR_WAIVERS excuses {waived}, but {why}; a waiver that "
            f"outlives its cause is a standing permission nobody re-reads"
        )
    return errors


# A class a probe names may go unshipped only with a reason. Same contract as
# check_prose.py's NOT_MECHANIZED: a documented exception is a reviewable state,
# an undocumented one is a defect nobody noticed.
#
# Every entry here is a CENSUS selector — one of the PROBE_CENSUS_LISTS above,
# whose job is "if the document has one of these, count it as ink, as text, as
# something drawn". Those lists deliberately over-reach, because a probe that
# cannot see a block reports the column holding it as empty and its neighbour as
# misaligned. They assert nothing about how the thing renders.
#
# The CONTRACT selectors are the other kind — ROLES and SCOPED, which claim "this
# role renders exactly one way" — and those may not be waived at all. That
# distinction is the whole guard: 0.1.349 audited ten roles against six names
# that shipped nowhere, and 0.1.366 found two more, because nothing separated a
# claim about rendering from a request to be counted.
# Twelve entries left when 0.1.369 shipped the four block patterns this dict had
# been excusing — `.key`, `.red`, `.card`, `.ledname`, `.verdict`, `.swap`,
# `.no`, `.yes`, `.vow`, `.vn`, `.vt`, `.vw`. The guard named each one the moment
# it started shipping ("tokens/ now ships it; delete the waiver"), which is the
# half of a waiver mechanism that usually goes missing.
PROBE_NOT_SHIPPED = {
    # Ten more entries left when 0.1.375 promoted the cover, opener, geography
    # and ladder vocabulary out of the reference deck and into tokens/ —
    # `.openpart`, `.openclaim`, `.openrun`, `.grades`, `.gr`, `.gloss`,
    # `.geo-flat`, `.sub`, `.tag`, `.wordmark`. The guard named each one the
    # moment it started shipping, same as the 0.1.369 batch.
    "note": "a single note inside `.notes`, which does ship with a voice of its "
            "own; the inner element is the document's.",
    "tick": "an axis or timeline label inside a figure.",
    "who": "an attribution line; a document's own furniture.",
}

# The class-carrying lists inside scripts/check/inspect_layout.py, by kind. Read out of
# the source with ast.parse and a regex and NEVER by importing it: importing to
# inspect it is how a guard ends up running the thing it is checking.
# `TSEL` became `TEXT_SEL` in 0.1.373 when the collision scan and the new
# opener-inset scan both needed it. The rename left this tuple pointing at a
# constant that had become an alias holding no selectors, and the guard duly
# reported five waivers as orphans — which is the rename being caught, one
# release after the guard was written to catch exactly it.
# `VIS` joined in 0.1.378: it is the sole carrier of the visual-share target,
# and outside this tuple a rename in tokens/ would drop the measured share
# toward zero with CI green — the exact failure this guard exists to stop.
PROBE_CENSUS_LISTS = ("CENTER", "INK", "TEXT_SEL", "DSEL", "VIS")


def _probe_sources():
    """The two probe strings from inspect_layout.py, or an explanatory failure."""
    tree = ast.parse((ROOT / "scripts/check/inspect_layout.py").read_text(encoding="utf-8"))
    out = {}
    for node in tree.body:
        if (isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)
                and isinstance(node.targets[0], ast.Name)):
            out[node.targets[0].id] = node.value.value
    for needed in ("PROBE", "CONSISTENCY_PROBE"):
        if needed not in out:
            raise ValueError(f"inspect_layout.py no longer defines {needed} as a "
                             f"module-level string; this guard reads nothing")
    return out


def _prose_wrappers():
    """The (wrapper, item) class pairs `check_prose.py` counts as enumerations.

    A second checker keying on class names, and the guard read only the first one
    until 0.1.370 — so `.grades`, `.gr` and `.gloss` were asserted by M10 and
    shipped by nothing, entirely outside the check written to stop exactly that.
    A guard that covers one of two callers is a guard with a blind spot the
    shape of the other.

    Only the CLASS assertions come back. The tuple's third field says whether an
    item is a class or an element name, and an element is not a vocabulary this
    package ships — `dt` is `dt` in every document ever written.

    The tuple is a literal inside `extract()`, so this walks the function body
    rather than the module's top level.
    """
    tree = ast.parse((ROOT / "scripts/check/check_prose.py").read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.For) or not isinstance(node.target, ast.Tuple):
            continue
        names = [n.id for n in node.target.elts if isinstance(n, ast.Name)]
        if names != ["wrapper", "item", "kind"] or not isinstance(node.iter, ast.Tuple):
            continue
        out = []
        for row in node.iter.elts:
            wrapper, item, kind = (cast(ast.Constant, e).value
                                   for e in cast(ast.Tuple, row).elts)
            out.append((wrapper, item if kind == "class" else None))
        if out:
            return out
    raise ValueError("check_prose.py no longer iterates a (wrapper, item, kind) "
                     "tuple of class names; this half of the guard reads nothing")


def _design_visual_blocks():
    """The VISUAL_BLOCKS tuple out of check_design.py, by ast.

    The visual vocabulary has TWO carriers: the probe's `VIS` (the rendered
    share) and check_design.py's `VISUAL_BLOCKS` (the static presence half of
    D16). 0.1.378 put the first under this guard and missed the second — "a
    guard that covers one of two callers is a guard with a blind spot the
    shape of the other", with the caller count corrected upward once again.
    """
    tree = ast.parse((ROOT / "scripts/check/check_design.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if (isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "VISUAL_BLOCKS"):
            return {cast(ast.Constant, e).value
                    for e in cast(ast.Tuple, node.value).elts}
    raise ValueError("check_design.py no longer defines VISUAL_BLOCKS at module "
                     "level; the static half of the visual vocabulary reads nothing")


def _js_const(source, name):
    """The text of `const NAME = ...;`, concatenation and all."""
    m = re.search(rf"\bconst {name}\s*=(.*?);", source, re.S)
    if not m:
        raise ValueError(f"no `const {name}` in the probe; the guard would check "
                         f"a vocabulary that has moved or been renamed")
    return m.group(1)


def _classes(selector_text):
    return set(re.findall(r"\.([A-Za-z][\w-]*)", selector_text))


def _shipped_classes():
    """Class names tokens/ gives a BASE rendering, media-query blocks excluded.

    The distinction is load-bearing. `.key` is styled only inside
    `@media (max-aspect-ratio: 1/1)`, where the portrait block tightens a
    font-size the file never declares at 1280 — so the stylesheet overrides a
    rendering it does not ship, which is the one-rendering rule broken by the
    token file that carries it. Counting that as "shipped" would let this guard
    report the vocabulary as complete on the strength of a portrait override.
    """
    base = set()
    for path in sorted((ROOT / "tokens").glob("*.css")):
        css = _css_without_comments(path.read_text(encoding="utf-8"))
        out, k = [], 0
        while k < len(css):
            m = re.compile(r"@media[^{]*\{").search(css, k)
            if not m:
                out.append(css[k:])
                break
            out.append(css[k:m.start()])
            depth, i = 1, m.end()
            while depth and i < len(css):
                depth += 1 if css[i] == "{" else -1 if css[i] == "}" else 0
                i += 1
            k = i
        base |= _classes("".join(out))
    return base


def check_role_weights():
    """`inspect_layout.ROLE_WEIGHTS` says what weight `tokens/` gives a role.

    A number in one file claiming to quote another is this repository's most
    fixed defect class, so the claim is held to the stylesheet rather than
    trusted. The gate reads the rendered weight; this reads the declared one;
    if they ever describe different numbers, the gate is enforcing a value
    nothing ships.
    """
    css = (ROOT / "tokens" / "lumi-layouts.css").read_text(encoding="utf-8")
    src = (ROOT / "scripts" / "check" / "inspect_layout.py").read_text(
        encoding="utf-8")
    m = re.search(r"^ROLE_WEIGHTS = \{(.*?)\}", src, re.S | re.M)
    if not m:
        return ["inspect_layout.py declares no ROLE_WEIGHTS table"]
    table = dict(re.findall(r'"([^"]+)":\s*(\d+)', m.group(1)))
    if not table:
        return ["ROLE_WEIGHTS parsed to nothing; a guard that reads no rows "
                "passes every stylesheet by construction"]
    errors = []
    for sel, want in sorted(table.items()):
        # The last declaration wins in a stylesheet, so read them all.
        blocks = re.findall(re.escape(sel) + r"\s*\{([^}]*)\}", css)
        weights = [w for b in blocks
                   for w in re.findall(r"font-weight:\s*(\d+)", b)]
        if not weights:
            errors.append(
                f"ROLE_WEIGHTS names {sel!r} at {want}, and "
                f"tokens/lumi-layouts.css declares no font-weight for it")
        elif weights[-1] != want:
            errors.append(
                f"ROLE_WEIGHTS says {sel!r} is {want}; "
                f"tokens/lumi-layouts.css ships {weights[-1]}")
    return errors


def check_ground_ceiling():
    """The ground's contrast ceiling, held to `tokens/` in every file that says it.

    `--ground-ceiling` is the authority and the number lives in six other
    places: `inspect_layout.GROUND_CEILING`, `tokens/lumi-layouts.css`'s comment,
    `references/brand.md`, `references/design-rules.md`, and the two generated
    pages. The register now records that TWO rules state it for every page and
    neither knew about the other; this is the mechanical half of the same
    finding, on the `role weights` pattern — a number in one file claiming to
    quote another is this repository's most fixed defect class.

    The generated pages are not read: they are rebuilt from their sources and
    `--check` already holds them.
    """
    theme = (ROOT / "tokens" / "lumi-theme.css").read_text(encoding="utf-8")
    m = re.search(r"--ground-ceiling:\s*([\d.]+)", theme)
    if not m:
        return ["tokens/lumi-theme.css declares no --ground-ceiling"]
    want = m.group(1).rstrip(".")
    errors = []
    src = (ROOT / "scripts" / "check" / "inspect_layout.py").read_text(
        encoding="utf-8")
    code = re.search(r"^GROUND_CEILING\s*=\s*([\d.]+)", src, re.M)
    if not code:
        errors.append("inspect_layout.py declares no GROUND_CEILING")
    elif float(code.group(1)) != float(want):
        errors.append(f"tokens ships --ground-ceiling {want}; "
                      f"inspect_layout.GROUND_CEILING is {code.group(1)}")
    # WHAT THIS CHECKS AND WHAT IT DOES NOT. Each prose file must state the
    # shipped number as a ratio; a change in `tokens/` therefore reddens every
    # file that quotes it until somebody sweeps them, which is the failure this
    # guard exists for (`1.40` is written in six places and nothing joined
    # them).
    #
    # It deliberately does NOT try to prove no other ratio appears. The first
    # version did, by reading ratios off any line mentioning "ground", and it
    # failed on `brand.md:193` — "5.21:1 on white, 3.23:1 on the dark ground",
    # two contrast figures for the LIME, on a line that happens to say ground —
    # while missing `design-rules.md:1461`, where the word "Ground" is on the
    # line above the number. One grep at the real material, per convention 15.
    for rel in ("references/brand.md", "references/design-rules.md",
                "tokens/lumi-layouts.css"):
        text = (ROOT / rel).read_text(encoding="utf-8")
        if f"{want}:1" not in text:
            errors.append(f"{rel} does not state the ground ceiling as "
                          f"{want}:1; tokens/lumi-theme.css ships {want}")
    return errors


def _privacy_branch_gates(src: str) -> bool:
    """-> whether check_deliverable's privacy branch puts its line in `gating`.

    Read as a BRANCH, not as two strings anywhere in the file. The first
    version asked whether `'if kind == "privacy":'` and `"gating.append"` both
    appeared in the source; in the real file they are eighteen lines and one
    scope apart — `gating.append(line)` belongs to the METRIC loop, and the
    privacy branch appends through `(gating if held else not_held)`. The guard
    was passing on evidence from unrelated code, so demoting the fiftieth gate
    left it green.
    """
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if not (isinstance(node, ast.If) and isinstance(node.test, ast.Compare)
                and isinstance(node.test.left, ast.Name)
                and node.test.left.id == "kind"
                and node.test.comparators
                and isinstance(node.test.comparators[0], ast.Constant)
                and node.test.comparators[0].value == "privacy"):
            continue
        for inner in ast.walk(node):
            if not (isinstance(inner, ast.Call)
                    and isinstance(inner.func, ast.Attribute)
                    and inner.func.attr == "append"):
                continue
            target = inner.func.value
            names = {n.id for n in ast.walk(target) if isinstance(n, ast.Name)}
            if "gating" in names:
                return True
    return False


def check_gate_declarations():
    """`evals/gates.json` says what each verdict is; the checkers say the same.

    The register carries two things no checker knows — `family` (the concept a
    verdict belongs to) and `since` (the release that introduced it) — and two
    it must not be allowed to invent: `checker` and `severity`. Those are read
    back out of the checkers here, so the register can add knowledge and cannot
    contradict.

    This is `check_rule_coverage`'s discipline one layer down: that guard holds
    the RULE register to `gating`'s AST reader; this holds the GATE register to
    the checkers' own row tables. A register nobody compares is a second copy,
    and a second copy of a contract is what put `M4zh_banned_hits` in one
    reader's gate set and not another's.
    """
    import gate_registry
    try:
        declared = gate_registry.load(ROOT)
    except (OSError, ValueError) as exc:
        return [f"{gate_registry.REGISTER} does not parse: {exc}"]
    if not declared:
        return [f"{gate_registry.REGISTER} declares nothing; an empty register "
                f"agrees with every checker by construction"]

    # What the checkers themselves say, read the way each one spells it.
    #
    # ROWS, not every tuple in the module. Reading every tuple made the answer
    # depend on `ast.walk` order: a three-element tuple in an unrelated helper
    # (`("D12_commercial_footer", "design-rules.md", "section 6")`) overwrote
    # the real row and the guard reported the REGISTER as the liar, which would
    # have talked an operator into demoting a live commercial gate. A row is an
    # element of the `rows` list literal or an argument to `rows.append`, which
    # is how both checkers actually build them.
    actual: dict[str, tuple[str, str]] = {}
    errors = []
    for kind, script in (("design", "check_design.py"), ("prose", "check_prose.py")):
        src = (ROOT / "scripts" / "check" / script).read_text(encoding="utf-8")
        tree = ast.parse(src)
        seen_rows = False
        for node in ast.walk(tree):
            elements: list = []
            found_table = False
            if (isinstance(node, ast.Assign)
                    and any(isinstance(x, ast.Name) and x.id == "rows"
                            for x in node.targets)
                    and isinstance(node.value, (ast.List, ast.Tuple))):
                elements, found_table = list(node.value.elts), True
            elif (isinstance(node, ast.AnnAssign)
                  and isinstance(node.target, ast.Name)
                  and node.target.id == "rows"):
                # `rows: list[...] = []` is an AnnAssign, which is how
                # check_design actually opens its table.
                found_table = True
                if isinstance(node.value, (ast.List, ast.Tuple)):
                    elements = list(node.value.elts)
            elif (isinstance(node, ast.Call)
                  and isinstance(node.func, ast.Attribute)
                  and node.func.attr in ("append", "extend")
                  and isinstance(node.func.value, ast.Name)
                  and node.func.value.id == "rows"):
                elements, found_table = list(node.args), True
            if not found_table:
                continue
            # The table was FOUND. Whether it holds rows here is a different
            # question — an empty literal is still the table, and demanding
            # elements made every synthetic tree look like a missing one.
            seen_rows = True
            for el in elements:
                # A LIST row is a row. Restricting to ast.Tuple let a
                # `rows.append([...])` emit a verdict that blocks delivery
                # while the register never had to declare it.
                if not (isinstance(el, (ast.Tuple, ast.List)) and len(el.elts) >= 3):
                    continue
                name_node, target = el.elts[0], el.elts[2]
                if not (isinstance(name_node, ast.Constant)
                        and isinstance(name_node.value, str)):
                    # A NAME BUILT AT RUNTIME cannot be compared to anything.
                    # Skipping it silently is how an undeclared gate ships, so
                    # it is a finding about the CHECKER rather than a pass.
                    errors.append(
                        f"{script} builds a row name at runtime "
                        f"(line {getattr(el, 'lineno', '?')}); a verdict whose "
                        f"name is not a literal cannot be declared in "
                        f"{gate_registry.REGISTER}, and an undeclared verdict "
                        f"that blocks delivery is what the register exists to "
                        f"prevent")
                    continue
                row = name_node.value
                if not re.match(r"[DM]\d+z?h?_", row):
                    continue
                # A TARGET MAY BE AN F-STRING, and reading only `ast.Constant`
                # made two of them look graded when their own text says
                # "(reported)" — the guard's first run said so, and the guard
                # was the half that was wrong. The classifying words are
                # literal parts of the JoinedStr, so the literals are joined.
                if isinstance(target, ast.Constant):
                    text = str(target.value)
                elif isinstance(target, ast.JoinedStr):
                    text = "".join(v.value for v in target.values
                                   if isinstance(v, ast.Constant)
                                   and isinstance(v.value, str))
                else:
                    # NOT "graded". An unreadable target used to be read as the
                    # weakest severity, so moving a target into a constant
                    # demoted a live gate AND the guard then demanded the
                    # register agree with the demotion.
                    errors.append(
                        f"{script}: {row}'s target is not a literal, so its "
                        f"severity cannot be read from the checker. Spell the "
                        f"target inline — the register is held to this, and a "
                        f"target it cannot read silently became 'graded'")
                    continue
                sev = ("gate" if "(gates)" in text
                       else "reported" if "reported" in text else "graded")
                if row in actual and actual[row] != (kind, sev):
                    errors.append(
                        f"{script}: {row} is declared twice with different "
                        f"severities ({actual[row][1]} and {sev})")
                actual[row] = (kind, sev)
        if not seen_rows:
            errors.append(
                f"{script}: no `rows` table was found, so nothing was compared. "
                f"A guard that read nothing is not a guard that agreed")
    if errors:
        return errors
    for name in gating.layout_verdicts(ROOT):
        actual[name] = ("layout", "gate")
    # THE FIFTIETH GATE, which fits no row table. `check_privacy` reports one
    # `verdict` per FILE rather than a verdicts map, and `check_deliverable`
    # promotes a non-ok one into the gating bucket in code — so it failed
    # builds while `gating.py`, this register and `run_conformance`'s require
    # set all had no idea it existed. Its parity is asserted where its gating
    # actually lives: the promotion in check_deliverable's own source.
    try:
        promoter = (ROOT / "scripts" / "ops" / "check_deliverable.py").read_text(
            encoding="utf-8")
    except OSError:
        promoter = ""           # a synthetic tree has no promoter to read
    if _privacy_branch_gates(promoter):
        actual["privacy_terms"] = ("privacy", "gate")

    errors = []
    for name in sorted(set(declared) - set(actual)):
        errors.append(f"{gate_registry.REGISTER} declares {name!r}, which no "
                      f"checker emits — it was renamed or withdrawn")
    for name in sorted(set(actual) - set(declared)):
        errors.append(f"{name!r} is emitted by check_{actual[name][0]} and is "
                      f"not in {gate_registry.REGISTER}; every verdict a "
                      f"deliverable can receive is declared, or the register is "
                      f"a partial map and reading it teaches the wrong set")
    for name in sorted(set(declared) & set(actual)):
        want_checker, want_sev = actual[name]
        got = declared[name]
        if got.get("checker") != want_checker:
            errors.append(f"{name}: register says checker={got.get('checker')!r}, "
                          f"emitted by check_{want_checker}")
        if got.get("severity") != want_sev:
            errors.append(f"{name}: register says severity={got.get('severity')!r}, "
                          f"the checker's own target says {want_sev!r}")
        if got.get("severity") not in gate_registry.SEVERITIES:
            errors.append(f"{name}: severity {got.get('severity')!r} is not one of "
                          + "|".join(gate_registry.SEVERITIES))
        if not (got.get("family") or "").strip():
            errors.append(f"{name}: no family. A verdict with no concept behind "
                          f"it is how this set grew one verdict at a time")
        since = got.get("since")
        if since != gate_registry.ALWAYS and not re.fullmatch(r"\d+\.\d+\.\d+", since or ""):
            errors.append(f"{name}: since {since!r} is neither a version nor "
                          f"{gate_registry.ALWAYS!r}")
    return errors


def check_probe_vocabulary():
    """A probe that keys on a class name is asserting a vocabulary; ship it.

    This is CLAUDE.md's reverse-drift rule mechanized, and it exists because the
    repository has now shipped the same defect three times. 0.1.349 audited ten
    roles against six class names that appeared nowhere in `tokens/`, read out of
    a validation deck. 0.1.361 shipped `.cap .srcline` and not `.foot .src`, so a
    comparison between them could never run. 0.1.366 found `.cover h1` and
    `.closing h2` audited as two of three title registers and shipped by nothing,
    which is how a real deliverable came back set in the wrong face while the
    consistency audit called it clean.

    Two kinds of selector, two strengths:

    * **contract** — `ROLES` and `SCOPED` claim a role renders exactly one way.
      A claim about rendering must have a rendering behind it, so these may not
      be waived.
    * **census** — every list named in `PROBE_CENSUS_LISTS`, and `check_prose.py`'s M10
      enumeration wrappers, ask only to be counted and over-reach on purpose.
      These may be waived in `PROBE_NOT_SHIPPED`, one written reason each.
    """
    try:
        probes = _probe_sources()
        shipped = _shipped_classes()
        roles = re.findall(r"\[\s*'[^']*'\s*,\s*'([^']+)'",
                           _js_const(probes["CONSISTENCY_PROBE"], "ROLES"))
        scoped = re.findall(r"\[\s*'([^']+)'\s*,\s*\[([^\]]*)\]\s*\]",
                            _js_const(probes["CONSISTENCY_PROBE"], "SCOPED"))
        census = {name: _js_const(probes["PROBE"], name) for name in PROBE_CENSUS_LISTS}
        # A list that parses to no class selectors reads as a list that asserts
        # nothing, and every waiver behind it then looks like an orphan. Say the
        # list went empty instead, which is the actual fault.
        for name, text in census.items():
            if not _classes(text):
                raise ValueError(f"`const {name}` in the probe holds no class "
                                 f"selectors; the guard would check an empty "
                                 f"vocabulary and report every waiver as stale")
        census["check_prose M10"] = " ".join(
            f".{w}" + (f" .{i}" if i else "") for w, i in _prose_wrappers())
        visual_static = _design_visual_blocks()
    except (OSError, ValueError, SyntaxError) as exc:
        return [f"could not read the probe vocabulary: {exc}"]

    if not roles or not scoped:
        return ["ROLES or SCOPED parsed to nothing; a guard that reads no "
                "selectors passes every document by construction"]

    contract = set()
    census_classes: dict[str, list[str]] = {}
    for sel in roles:
        contract |= _classes(sel)
    for sel, scopes in scoped:
        contract |= _classes(sel) | _classes(scopes)
    for name, text in census.items():
        for cls in _classes(text):
            census_classes.setdefault(cls, []).append(name)

    errors = []
    for cls in sorted(contract - shipped):
        errors.append(
            f"inspect_layout.py asserts .{cls} as part of a ROLES/SCOPED contract, "
            f"and no tokens/ file gives it a base rendering. A role that claims one "
            f"rendering must ship one; this may not be waived"
        )
    for cls in sorted(contract & set(PROBE_NOT_SHIPPED)):
        errors.append(
            f"PROBE_NOT_SHIPPED waives .{cls}, but ROLES/SCOPED asserts it as a "
            f"contract — waive the census use or drop the claim, not both"
        )
    for cls in sorted(set(census_classes) - shipped - set(PROBE_NOT_SHIPPED)):
        errors.append(
            f"inspect_layout.py's {'/'.join(census_classes[cls])} names .{cls}, which "
            f"no tokens/ file gives a base rendering; add the rule or list it in "
            f"PROBE_NOT_SHIPPED with a reason"
        )
    named = set(census_classes) | contract
    for cls in sorted(PROBE_NOT_SHIPPED):
        if cls not in named:
            errors.append(f"PROBE_NOT_SHIPPED excuses .{cls}, which no probe names; "
                          f"a waiver that outlives its cause is a standing permission "
                          f"nobody re-reads")
        elif cls in shipped:
            errors.append(f"PROBE_NOT_SHIPPED excuses .{cls}, which tokens/ now ships; "
                          f"delete the waiver")
    # D16's two halves must agree on what "visual" means: the probe's VIS
    # measures the rendered share, check_design's VISUAL_BLOCKS the static
    # presence, and a block added to one list only splits the metric silently
    # — a page carrying the new pattern gets listed prose-only while its share
    # reads healthy, or the reverse.
    vis_probe = _classes(census.get("VIS", ""))
    if vis_probe != visual_static:
        errors.append(
            f"the visual vocabulary has diverged: inspect_layout.py VIS = "
            f"{sorted(vis_probe)}, check_design.py VISUAL_BLOCKS = "
            f"{sorted(visual_static)} — one metric, two carriers, and D16's "
            f"halves now disagree about what is visual")
    return errors


# A class may be styled ONLY inside a media query with a reason, and there is
# exactly one honest reason: the rule is a geometry switch whose whole purpose is
# to differ per geometry.
# Empty since 0.1.380, when the geometry stopped being a window-shape media
# query and became the document's own declaration: `.land` and `.port` are now
# base rules under `body[data-geometry=...]`, so the pair that needed the only
# honest waiver no longer needs one.
MEDIA_ONLY_WAIVERS: dict[str, str] = {}


def check_media_only_rules():
    """No class may be styled only inside a media query.

    A rule that exists in one geometry and nowhere else is a rendering the
    package half-ships: the document gets `tokens/`'s value on the sheet and
    whatever it invented at 1280, which is one role rendering two ways — the
    thing `brand.md` and the role vocabulary both forbid. It is invisible by
    construction, because the consistency audit run at the design geometry finds
    nothing to compare.

    0.1.369 found seven font-sizes in that state, plus `.duo`, whose base grid
    existed only in the geometry that collapses it, and the fixture page using it
    ran 12px past the footer rule. This is the general form, so there is no
    eighth.
    """
    base, media = set(), set()
    files = sorted((ROOT / "tokens").glob("*.css"))
    if not files:
        return ["tokens/: no CSS to check; this guard would pass vacuously"]
    for path in files:
        css = _css_without_comments(path.read_text(encoding="utf-8"))
        out, k = [], 0
        while k < len(css):
            m = re.compile(r"@media[^{]*\{").search(css, k)
            if not m:
                out.append(css[k:])
                break
            out.append(css[k:m.start()])
            depth, i = 1, m.end()
            while depth and i < len(css):
                depth += 1 if css[i] == "{" else -1 if css[i] == "}" else 0
                i += 1
            media |= _classes(css[m.end():i - 1])
            k = i
        base |= _classes("".join(out))

    errors = []
    for cls in sorted(media - base - set(MEDIA_ONLY_WAIVERS)):
        errors.append(
            f"tokens/: .{cls} is styled only inside a @media block and has no base "
            f"rendering, so the package ships it in one geometry and not the other; "
            f"give it a base rule, remove it, or waive it in MEDIA_ONLY_WAIVERS"
        )
    for waived in sorted(MEDIA_ONLY_WAIVERS):
        if waived in base:
            errors.append(f"MEDIA_ONLY_WAIVERS excuses .{waived}, which now has a base "
                          f"rendering; delete the waiver")
        elif waived not in media:
            errors.append(f"MEDIA_ONLY_WAIVERS excuses .{waived}, which no tokens/ file "
                          f"styles at all; a waiver that outlives its cause is a "
                          f"standing permission nobody re-reads")
    return errors


def check_layout_parity():
    """The layouts `tokens/` defines and the layouts `check_design.py` grades are
    one list.

    D9 reports a page whose `.body` class is not a shipped layout as using none,
    so a layout present in the stylesheet and absent from `LAYOUTS` reads as an
    author's typo. `.body.cover-grid` was exactly that for eleven releases —
    declared in the portrait block, missing from this file's own "fifteen page
    layouts" header, missing from §3's selection table, and missing from the
    checker. Removed in 0.1.370; this keeps the two sides from parting again.
    """
    try:
        css = "".join(_css_without_comments(p.read_text(encoding="utf-8"))
                      for p in sorted((ROOT / "tokens").glob("*.css")))
        tree = ast.parse((ROOT / "scripts/check/check_design.py").read_text(encoding="utf-8"))
    except (OSError, SyntaxError) as exc:                   # noqa: BLE001
        return [f"could not compare the layout lists: {exc}"]

    graded = None
    for node in tree.body:
        if (isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "LAYOUTS"):
            graded = {cast(str, cast(ast.Constant, e).value)
                      for e in cast(ast.Set, node.value).elts}
    if graded is None:
        return ["check_design.py no longer defines LAYOUTS at module level; the "
                "layout list cannot be compared"]

    shipped = set(re.findall(r"\.body\.([\w-]+)", css)) - {"no-lede", "top"}
    errors = []
    for name in sorted(shipped - graded):
        errors.append(f"tokens/ defines the layout .body.{name}, which check_design.py's "
                      f"LAYOUTS does not grade — D9 reads a page using it as using no "
                      f"shipped layout")
    for name in sorted(graded - shipped):
        errors.append(f"check_design.py grades the layout {name!r}, which no tokens/ "
                      f"file defines; the stylesheet is the source, not the checker")
    return errors


def _rules_ban_phrases():
    """The [en-output] phrases from writing-rules.md section 2, normalized."""
    text = (ROOT / "references/writing-rules.md").read_text(encoding="utf-8")
    # Scope to section 2 first: "[en-output]" also appears in section 0, where it
    # is named as a marker rather than introducing the list.
    section = re.search(r"^## 2 [^\n]*\n(.*?)(?=^## )", text, re.S | re.M)
    if not section:
        raise ValueError("could not locate section 2 in writing-rules.md")
    block = re.search(r"\*\*\[en-output\].*", section.group(1), re.S)
    if not block:
        raise ValueError("could not locate the [en-output] block inside section 2")

    # The eight groups form one paragraph; the attribution note that follows is a
    # separate one and must not be read as banned phrases.
    listing = next((p for p in block.group(0).split("\n\n")
                    if re.match(r"^\d+\.\s+\*\*", p)), None)
    if listing is None:
        raise ValueError("could not locate the numbered groups in section 2")

    phrases = set()
    # "N. **Group name**[, qualifier] — item · item · item.", wrapped across lines.
    for group in re.split(r"\n(?=\d+\.\s+\*\*)", listing):
        body = re.sub(r"\s+", " ", group).strip()
        if "—" not in body:
            continue
        for item in body.split("—", 1)[1].split("·"):
            item = item.split("→")[0]              # filler entries carry their fix
            item = re.sub(r"\s+", " ", item.replace('"', "")).strip().rstrip(".").strip()
            if item:
                phrases.add(item.lower())
    return phrases


def _script_ban_phrases():
    """(matched, waived) phrase sets declared in check_prose.py, read via AST.

    Parsed rather than imported: this guard must not execute the other script.
    """
    tree = ast.parse((ROOT / "scripts/check/check_prose.py").read_text(encoding="utf-8"))
    matched, waived = set(), set()
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        name = getattr(node.targets[0], "id", None)
        if name == "BANNED":
            for element in cast(ast.List, node.value).elts:
                phrase = cast(ast.Constant, cast(ast.Tuple, element).elts[1])
                matched.add(cast(str, phrase.value).lower())
        elif name == "NOT_MECHANIZED":
            for key in cast(ast.Dict, node.value).keys:
                waived.add(cast(str, cast(ast.Constant, key).value).lower())
    return matched, waived


def check_ban_list_parity():
    """check_prose.py's list is a second copy of the rules; hold them together.

    Every phrase section 2 bans must be either matched by a pattern or waived
    with a reason, so a rule added to the prose without deciding what the machine
    does about it fails here instead of going quietly unenforced.
    """
    try:
        rules = _rules_ban_phrases()
        matched, waived = _script_ban_phrases()
    except (OSError, ValueError, SyntaxError, AttributeError) as exc:
        return [f"could not compare the ban lists: {exc}"]

    errors = []
    for phrase in sorted(rules - (matched | waived)):
        errors.append(
            f"writing-rules.md section 2 bans {phrase!r}, but check_prose.py neither "
            f"matches it nor lists it in NOT_MECHANIZED with a reason"
        )
    for phrase in sorted((matched | waived) - rules):
        errors.append(
            f"check_prose.py declares {phrase!r}, which writing-rules.md section 2 "
            f"does not list — the rules are the source, not the script"
        )
    for phrase in sorted(matched & waived):
        errors.append(f"{phrase!r} is both matched and waived in check_prose.py")
    return errors


def check_review_scores():
    """The human half of the loop has a memory now; keep it valid and clean.

    Delegated to scripts/ops/review_scores.py so the schema lives in one place.
    The reason this runs in CI at all is red line 9: a score store is exactly
    the shape that carries a client name into the repository, and the defence is
    that the schema has no field to put one in. A guard that is not run is a
    comment.

    **An absent store is a finding HERE even though it is not one for the
    script.** `review_scores.py --check` returns 0 when there is no store,
    which is right for a freshly installed skill — nobody has reviewed anything
    yet. It is not right for THIS repository, which tracks the store: an absent
    one means the tracked file was deleted, and the guard would report `ok`
    having read nothing at all.
    """
    store = ROOT / "reviews" / "scores.json"
    if not store.exists():
        return [f"{rel(store)} is gone. It is a TRACKED file here, so its "
                f"absence is a deletion rather than a fresh install — and this "
                f"guard would otherwise pass having validated nothing"]
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "ops" / "review_scores.py"), "--check"],
        capture_output=True, text=True)
    if proc.returncode == 0:
        return []
    return [line[6:] for line in proc.stdout.splitlines()
            if line.startswith("FAIL  ")] or [proc.stdout.strip() or "unknown failure"]


def check_zh_ban_list_parity():
    """The [zh-output] list is rule data too, and it had no machine counterpart.

    Phase 1 of the Chinese item, and it is first because it is a GUARD rather
    than a feature: the English ban list has been held to the rules since
    0.1.377 while the Chinese list could drift with nothing noticing. Closing
    the drift channel costs least and is the only part of that work that does
    not wait on a font licence.
    """
    try:
        text = (ROOT / "references/writing-rules.md").read_text(encoding="utf-8")
        section = re.search(r"^## 2 [^\n]*\n(.*?)(?=^## )", text, re.S | re.M)
        if not section:
            raise ValueError("could not locate section 2 in writing-rules.md")
        listing = re.search(r"\*\*\[zh-output\]\*\*\s*rule data:(.*?)\.\s*\n",
                            section.group(1), re.S)
        if not listing:
            raise ValueError("could not locate the [zh-output] rule data in section 2")
        rules = {p.strip() for p in listing.group(1).split("·") if p.strip()}
        # The qualified ban is stated as prose rather than in the list, so it is
        # named here explicitly. Its label in the script carries the collocations
        # it excepts, which is the part a reader of either file needs.
        qualified = re.search(r"^Qualified ban \(rule data\): (\S+) is allowed",
                              section.group(1), re.M)
        if not qualified:
            raise ValueError("could not locate the qualified ban in section 2")
        rules.add(qualified.group(1))

        src = (ROOT / "scripts/check/check_prose.py").read_text(encoding="utf-8")
        tree = ast.parse(src)
        script = None
        for node in ast.walk(tree):
            if (isinstance(node, ast.Assign)
                    and any(getattr(t, "id", None) == "BANNED_ZH"
                            for t in node.targets)):
                script = {lbl for _pat, lbl in ast.literal_eval(node.value)}
        if script is None:
            raise ValueError("check_prose.py declares no BANNED_ZH")
    except (OSError, ValueError, SyntaxError) as exc:
        return [f"could not compare the zh ban lists: {exc}"]

    # A label may carry its exception ("赋能 outside 销售赋能 / 市场赋能"), so a
    # rule phrase is covered when a label STARTS with it. Substring anywhere
    # would let 赋能 stand in for a phrase that merely contains it.
    errors = []
    for phrase in sorted(rules):
        if not any(lbl.startswith(phrase) for lbl in script):
            errors.append(f"writing-rules.md section 2 [zh-output] bans {phrase!r}, "
                          f"which check_prose.py's BANNED_ZH does not match")
    for label in sorted(script):
        if not any(label.startswith(phrase) for phrase in rules):
            errors.append(f"check_prose.py bans {label!r}, which writing-rules.md "
                          f"section 2 [zh-output] does not list — the rules are the "
                          f"source, not the script")
    return errors


def check_source_marker_parity():
    """check_prose.py's SOURCE_MARKERS is a second copy of the rules; hold them.

    M2 and M6 measure "every number carries its source", so what counts AS a
    source is a rule, not an implementation detail. Section 4 rule 6 states the
    markers and this guard holds the script to them — the same discipline as
    `ban-list parity`, added for the same reason: a metric that invents its own
    vocabulary is a second rule nobody wrote down, and it drifts silently.
    """
    try:
        text = (ROOT / "references/writing-rules.md").read_text(encoding="utf-8")
        section = re.search(r"^## 4 [^\n]*\n(.*?)(?=^## )", text, re.S | re.M)
        if not section:
            raise ValueError("could not locate section 4 in writing-rules.md")
        rule6 = re.search(r"^6\.\s+\*\*What counts as a source marker.*?"
                          r"(?=\n\s*\*\*The window)", section.group(1), re.S | re.M)
        if not rule6:
            raise ValueError("could not locate rule 6's marker list in section 4")
        # Each marker is the first backticked token on its own bullet.
        rules = {m.group(1).strip().lower()
                 for m in re.finditer(r"^\s*-\s+`([^`]+)`", rule6.group(0), re.M)}
        src = (ROOT / "scripts/check/check_prose.py").read_text(encoding="utf-8")
        tree = ast.parse(src)
        script = None
        for node in ast.walk(tree):
            if (isinstance(node, ast.Assign)
                    and any(getattr(t, "id", None) == "SOURCE_MARKERS"
                            for t in node.targets)):
                script = {s.lower() for s in ast.literal_eval(node.value)}
        if script is None:
            raise ValueError("check_prose.py declares no SOURCE_MARKERS")
    except (OSError, ValueError, SyntaxError) as exc:
        return [f"could not compare the source-marker lists: {exc}"]

    errors = []
    for marker in sorted(rules - script):
        errors.append(f"writing-rules.md section 4 rule 6 lists the source marker "
                      f"{marker!r}, which check_prose.py does not match")
    for marker in sorted(script - rules):
        errors.append(f"check_prose.py matches {marker!r} as a source marker, which "
                      f"writing-rules.md section 4 rule 6 does not list — the rules "
                      f"are the source, not the script")
    return errors


PLATFORMS = ROOT / "adapters" / "platforms.json"

# entry point -> the regex its version stamp must match, with {v} the version.
# A position, not a substring: the first version of this guard asked only whether
# the string appeared anywhere in the file, and AGENTS.md satisfied it with the
# sentence explaining that it used to be unstamped. A file that merely mentions
# the current version is not a file that declares it. An entry point with no
# pattern here fails rather than being skipped.
# Where the token files carry the version. A module constant rather than a
# literal inside check_versions, because scripts/ops/release.py writes these
# stamps and must not carry its own copy of where they are — a second list of
# stamp positions is this repository's own worst defect class, arriving through
# the door marked "release tooling".
# The two stamp tables live in `scripts/lib/stamps.py` — three readers held
# three copies of "which files carry the version stamp" and they had already
# diverged; see that module for what it cost. Imported under their own names
# so every use site below reads the same way it always did.
TOKEN_STAMPS = stamps.TOKEN_STAMPS
ENTRY_STAMP = stamps.ENTRY_STAMP

# A version string may name something other than a release only with a reason.
# Same contract as check_prose.py's NOT_MECHANIZED: a documented exception is a
# reviewable state; an undocumented one is a mistake nobody noticed.
# Files that legitimately carry version numbers belonging to other projects.
THIRD_PARTY_VERSION_LINES = {"conformance/CONFORMANCE.md": re.compile(r"^\|")}

VERSION_CITATION_WAIVERS = {
    # An upstream npm package version, pinned so the vendored marks can be
    # re-fetched byte-for-byte. It is somebody else's release number, and the
    # pattern this guard scans with cannot tell whose a version belongs to.
    "1.94.0": "the pinned @lobehub/icons-static-svg release the model-family "
              "marks in assets/logos/models/ were fetched from, recorded in "
              "assets/logos/SOURCES.md so they can be re-fetched exactly",
    "1.0.0": "names the first release of the retired 1.x-3.x scheme, in the prose "
             "that explains why the scheme was retired",
    "3.4.0": "names the last release of the retired scheme, and the commit subject "
             "git history still carries; both are quoted deliberately",
    # WCAG success criteria are numbered like releases and are not releases. The
    # pattern this guard scans with cannot tell them apart, and a design record
    # that cites the criterion it was measured against is doing the right thing.
    # (Each key appeared twice here until 0.1.417 — two releases each added
    # their own waiver and the literal duplicate silently shadowed the first.
    # A linted dict literal now refuses that.)
    "1.4.11": "WCAG 2.1 SC 1.4.11 'Non-text Contrast': an accessibility "
              "success criterion cited in design records and in specs/ as the "
              "authority for the region boundary stroke — not a release",
    "2.5.8": "WCAG 2.2 SC 2.5.8 'Target Size (Minimum)': an accessibility "
             "success criterion cited in design records and in specs/ as the "
             "authority for the 24px pick target — not a release",
    # Forward references to planned work, deleted the release they ship. The
    # comment here used to claim this made a stale promise a CI failure. It did
    # not: this guard fails a citation only when NO heading defines it, so
    # shipping made a promise MORE legal, and it scanned *.md only, so the
    # registry's own promises were never read at all. check_stale_promises()
    # below is the check that claim described.
}


def _load_platforms():
    """The platform registry, or an explanatory failure. Never a silent {}."""
    raw = PLATFORMS.read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data.get("platforms"), list) or not data["platforms"]:
        raise ValueError("platforms.json declares no platforms")
    return data


# A retired value may appear without a withdrawal marker only with a reason.
# (relative path, retired value, distinctive fragment of the sentence) -> why.
# Empty on purpose, and the guard reports a waiver nothing matches so it stays
# that way. The first cut needed one — a sentence sizing an icon against an 11px
# caption — but once each retired value carried `context` phrases, the icon
# sentence stopped looking like a floor claim at all. A waiver that survives its
# cause is a standing permission nobody re-reads.
RETIRED_VALUE_WAIVERS: dict[tuple[str, str, str], str] = {}

# The words this repository actually uses when it retires something, harvested
# rather than invented: a retirement written in a phrasing not listed here is a
# retirement the guard cannot see, and the guard says so instead of passing.
WITHDRAWAL_MARKERS = (
    "withdrew", "withdrawn", "retired", "no longer", "there is no", "no fill floor",
    "no size floor", "no type floor", "without an ask", "never a floor", "not a floor",
    "no layout-share cap",
    # A provenance paragraph saying the rule was *invented* is plainly not
    # asserting it; "invented without an ask" is this repository's own phrase for
    # a rule that should never have existed.
    "invent",
)


def check_retired_values():
    """A number the rules withdrew may not be restated as though it still binds.

    This is the repository's documented worst drift, and it shipped: the 82% page
    fill floor and the 11px type floor were withdrawn in 0.1.340 and went on
    living in AGENTS.md and prompts/lumi-style-core.md for four more versions,
    invisible because nothing compared the copies. The register in
    tokens/design-tokens.json is the authority for what was withdrawn — a
    withdrawn number has to be *stated* somewhere or no machine can tell it from
    a number deleted by accident.

    Every sentence restating a retired value must mark it as retired. What the
    guard cannot do is tell whether a rule's polarity changed while its digits
    stayed: "3-6 word headline" as a ceiling and as a target are the same
    characters, and CLAUDE.md rule 4 exists because that has cost three
    regressions. That stays with the reviewer.
    """
    try:
        tokens = json.loads((ROOT / "tokens/design-tokens.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:                    # noqa: BLE001
        return [f"tokens/design-tokens.json: {exc}"]

    retired = {r["value"]: r for r in tokens.get("retired", [])}
    if not retired:
        return ["tokens/design-tokens.json: the `retired` register is empty; if "
                "nothing has been withdrawn, say so rather than omitting it"]

    errors, used_waivers = [], set()
    for path in md_files():
        name = rel(path)
        if name.startswith("CHANGELOG"):
            continue          # the changelog is the record OF withdrawals, not a restatement
        # Paragraph-scoped, not line-scoped. This prose is hard-wrapped, so
        # "Withdrawn in 0.1.340 … the 11px type floor" routinely straddles two
        # lines and a line-scoped check reported the second half as an unmarked
        # restatement. A sentence is the unit a reader reads; it is the unit the
        # marker has to be found in.
        para: list[str] = []
        in_fence, start = False, 1
        paragraphs = []
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            prose, in_fence = _strip_code(line, in_fence)
            if prose.strip():
                if not para:
                    start = lineno
                para.append(prose)
            elif para:
                paragraphs.append((start, " ".join(para)))
                para = []
        if para:
            paragraphs.append((start, " ".join(para)))

        for lineno, prose in paragraphs:
            low = prose.lower()
            for value, record in retired.items():
                if value not in prose:
                    continue
                # A bare number is not a rule. "40%" names the withdrawn D9 share
                # cap in one sentence and "four diagrams rendered at 40% of their
                # cell" in another — opposite claims, identical digits. The value
                # counts as a restatement only alongside one of its context
                # phrases; without a context list it cannot be told apart from
                # arithmetic and the register says so.
                context = record.get("context")
                if not context:
                    errors.append(
                        f"tokens/design-tokens.json: retired value {value!r} has no "
                        f"`context` phrases, so it cannot be distinguished from any "
                        f"other use of the same digits"
                    )
                    continue
                if not any(phrase.lower() in low for phrase in context):
                    continue
                if any(marker in low for marker in WITHDRAWAL_MARKERS):
                    continue
                waiver = next(
                    (k for k in RETIRED_VALUE_WAIVERS
                     if k[0] == name and k[1] == value and k[2].lower() in low),
                    None,
                )
                if waiver:
                    used_waivers.add(waiver)
                    continue
                errors.append(
                    f"{name}:{lineno}: states {value} — the {record['name']}, "
                    f"withdrawn in {record['withdrawn_in']} — without marking it "
                    f"withdrawn, and RETIRED_VALUE_WAIVERS does not excuse it"
                )

    for stale_waiver in sorted(set(RETIRED_VALUE_WAIVERS) - used_waivers):
        errors.append(
            f"RETIRED_VALUE_WAIVERS excuses {stale_waiver[1]} in {stale_waiver[0]} "
            f"({stale_waiver[2]!r}), but nothing there matches any more — delete the "
            f"waiver rather than leaving a permission nobody uses"
        )
    return errors


PROMISE = re.compile(
    # No bare `from`. It matched "carried over from 0.1.352", "survived from
    # 0.1.340", "renumbered from 0.1.328" — retrospective citation is this
    # repository's entire documentation voice, so the guard was one sentence
    # away from failing CI while asserting the opposite of what the sentence
    # said. Every alternative here is future-tense.
    r"v?(\d+\.\d+\.\d+)", re.I)
FUTURE = re.compile(r"\b(will|planned|plan to|scheduled|upcoming|coming|to be|"
                    r"TODO|forthcoming|due)\b", re.I)


def check_stale_promises():
    """A promise of future work may not name a release that already shipped.

    This is the check `VERSION_CITATION_WAIVERS` used to claim to be and was not.
    A note reading "planned for 0.1.354" is correct until 0.1.354 ships and
    misleading forever after, and the citation guard cannot see it — once the
    heading exists the citation is legal, so the promise gets *more* valid the
    moment it goes stale.

    Registry JSON is scanned too. `adapters/platforms.json` is declared the
    single source of platform facts and promised two releases of work that had
    already landed, entirely unread by any guard, because every text scan in
    this file globs `*.md`.
    """
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    shipped = set(re.findall(r"^##\s+(\d+\.\d+\.\d+)", changelog, re.M))
    errors = []
    scanned = (list(md_files()) + [PLATFORMS]
               + [ROOT / p for p in (".cursor/rules/lumi-style.mdc",
                                     ".well-known/skills/index.json",
    # The geography registries' bilingual names. Every `z` field is what
    # `regionmap_svg.py --labels zh` and the globe render onto a Chinese map,
    # so they are rule data for Chinese-language output in the most literal
    # sense the red line allows: the string a Chinese reader sees on the
    # figure. Deleting them would not make the repository more English; it
    # would make the Chinese map wrong.
    "assets/vectors/regions-trade.json",
    "assets/vectors/regions.json",
    "assets/vectors/world-110m.json",
                                     ".claude-plugin/plugin.json",
                                     ".claude-plugin/marketplace.json")])
    scanned = [p for p in scanned if p.exists()]
    for path in scanned:
        name = rel(path)
        if name.startswith("CHANGELOG"):
            continue        # the record of what shipped, written in the past tense
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            # Inverted: any shipped version named in a FUTURE-TENSE sentence,
            # rather than an inventory of verb phrases. The inventory both
            # over-matched (a bare `from` fired on "carried over from 0.1.352")
            # and under-matched — it missed "ships in", "due in", "scheduled
            # for", "TODO(0.1.361)", and the very sentence it was written for
            # once the bare `from` was removed.
            if not FUTURE.search(line):
                continue
            for version in PROMISE.findall(line):
                if version in shipped:
                    errors.append(
                        f"{name}:{lineno}: promises work in {version}, which has "
                        f"already shipped; the promise is now a false statement "
                        f"about the present")
    return errors


def check_platform_manifest():
    """Every platform this repo claims is described, and every description resolves.

    The registry is the single source of platform facts. Before it existed the
    same facts lived in four hand-written notes and a README table, and they had
    already disagreed: adapters/claude-code.md said `git clone` into the skills
    directory while README.md insisted on a symlink *because a copy had stranded
    at an old version*. Two files, one fact, opposite instructions.

    Nothing here checks that a platform actually loads the skill — CI cannot
    launch Gemini CLI. It checks that every claim we publish has a file behind it
    and every unverified claim says so.
    """
    try:
        data = _load_platforms()
    except (OSError, ValueError) as exc:                    # noqa: BLE001
        return [f"adapters/platforms.json: {exc}"]

    errors = []
    capabilities = data.get("capabilities", {})
    seen_ids, claimed_notes = set(), set()

    for entry in data["platforms"]:
        pid = entry.get("id")
        if not pid:
            errors.append("adapters/platforms.json: a platform has no id")
            continue
        if pid in seen_ids:
            errors.append(f"adapters/platforms.json: duplicate platform id {pid!r}")
        seen_ids.add(pid)

        if entry.get("capability") not in capabilities:
            errors.append(
                f"adapters/platforms.json: {pid} declares capability "
                f"{entry.get('capability')!r}, which the capabilities table does not "
                f"define; a tier that means whatever its first platform needed is "
                f"not a tier"
            )

        for field in ("entry_file", "notes_path"):
            target = entry.get(field)
            if not target:
                errors.append(f"adapters/platforms.json: {pid} has no {field}")
            elif not (ROOT / target).exists():
                errors.append(
                    f"adapters/platforms.json: {pid} {field} {target!r} does not exist"
                )
            elif field == "notes_path":
                claimed_notes.add(target)

        # Every unverified claim carries its own reason, in the file, under review.
        for flag, waiver, what in (
            ("path_verified", "path_waiver", "install path"),
            ("docs", "docs_waiver", "documentation URL"),
            ("probe", "probe_waiver", "CLI probe"),
            # The tier was the ONE claim here with no verification field, and it
            # is the claim that decides whether an agent may call a deliverable
            # verified. Ten records asserted `full` — "the agent runs the
            # checkers itself" — and nothing had ever watched one do it.
            ("capability_verified", "capability_waiver", "capability tier"),
        ):
            value = entry.get(flag)
            # Explicit true, or it is unverified. This read absence as
            # verification, so deleting one optional field silently stripped the
            # published "Unverified" warning from an install note and turned a
            # path the repository admits is a guess into an apparently-checked
            # instruction. Empty string and empty list are absence too: `probe:
            # []` satisfied `is None` here while detect() read it as no probe,
            # so the two files disagreed about what "has a probe" means.
            missing = (value is not True
                       if flag in ("path_verified", "capability_verified")
                       else (not value))
            if flag == "probe" and value and not (
                    isinstance(value, list) and all(isinstance(x, str) for x in value)):
                errors.append(
                    f"adapters/platforms.json: {pid} probe must be a list of strings; "
                    f"a string is indexed character-wise and publishes an installed "
                    f"agent as not installed")
            if missing and not entry.get(waiver):
                errors.append(
                    f"adapters/platforms.json: {pid} has no {what} and no {waiver} "
                    f"explaining why — an unverified claim must say so"
                )

    # No orphans: an install note nobody points at is a note nobody maintains.
    on_disk = {rel(p) for p in (ROOT / "adapters").glob("*.md")}
    for orphan in sorted(on_disk - claimed_notes):
        errors.append(
            f"{orphan}: no platform in platforms.json claims this note; add the "
            f"platform or delete the file"
        )
    return errors


def check_version_citations():
    """Two things, both derived from CHANGELOG.md rather than from a list.

    1. Every entry point named in the registry carries the current version. Until
       0.1.352 only SKILL.md's frontmatter was checked: AGENTS.md carried no stamp
       at all, and the core prompt's self-declared snapshot line was unverified.
       Both had already shipped four versions of drift.
    2. Every version cited anywhere resolves to a release. CLAUDE.md calls a
       citation naming a version no heading defines "the drift this repo is worst
       at catching", and there are 165 such citations across references/, tokens/,
       scripts/ and the entry points.
    """
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    headings = set(re.findall(r"^##\s+(\d+\.\d+\.\d+)", changelog, re.M))
    if not headings:
        return ["CHANGELOG.md: no '## X.Y.Z' release headings found"]
    newest = re.search(r"^##\s+(\d+\.\d+\.\d+)", changelog, re.M)
    if newest is None:  # unreachable: findall above matched this same pattern
        return ["CHANGELOG.md: no '## X.Y.Z' release headings found"]
    current = newest.group(1)

    errors = []
    try:
        data = _load_platforms()
    except (OSError, ValueError) as exc:                    # noqa: BLE001
        return [f"adapters/platforms.json: {exc}"]

    # The union, not the registry alone. ENTRY_STAMP's conformance entry matched
    # no platform's entry_file, so the pattern was dead code for six releases
    # while the scoreboard's stamp sat at 0.1.371 — and the comment on that
    # entry claimed to be "the check that sees it". A declared stamp position
    # is a promise to check it, wherever the file is registered.
    registry_targets = {e.get("entry_file") for e in data["platforms"] if e.get("entry_file")}
    for target in sorted(registry_targets | set(ENTRY_STAMP)):
        path = ROOT / target
        if not path.exists():
            # A registry target's absence is the manifest guard's finding. A
            # file declared ONLY here matches nothing the manifest knows, so
            # skipping it would re-open the dead-pattern hole one level up:
            # rename the scoreboard and its stamp guard evaporates, green.
            if target not in registry_targets:
                errors.append(
                    f"{target}: named in ENTRY_STAMP but the file does not exist; "
                    f"a stamp position pointing at nothing checks nothing")
            continue
        pattern = ENTRY_STAMP.get(target)
        if pattern is None:
            errors.append(
                f"{target}: is an entry point with no stamp pattern in ENTRY_STAMP; "
                f"declare where its version lives, or it cannot be checked"
            )
            continue
        if not re.search(pattern.format(v=re.escape(current)),
                         path.read_text(encoding="utf-8"), re.M):
            errors.append(
                f"{target}: carries no {current} version stamp in its declared stamp "
                f"position; an entry point that cannot say which rules it encodes is "
                f"one a reader cannot date"
            )

    # A version may be cited only if some release defines it.
    cite = re.compile(r"(?<![\d.])(\d+\.\d+\.\d+)(?![0-9A-Za-z])")
    for path in md_files():
        name = rel(path)
        # The conformance scoreboard records THIRD-PARTY CLI versions — "Claude
        # Code 2.1.225" — which change on every run and name somebody else's
        # release, not one of ours. Waiving them individually would mean editing
        # this file every time an agent updates, which is churn that teaches
        # people to edit waivers without reading them.

        in_fence = False
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            prose, in_fence = _strip_code(line, in_fence)
            # Scoped to the lines that carry third-party versions — the
            # scoreboard's table rows — not the whole file. Exempting the file
            # also exempted the skill's own version stamp on its first line.
            skip = THIRD_PARTY_VERSION_LINES.get(name)
            if skip and skip.search(line):
                continue
            for found in cite.findall(prose):
                if found in headings or found in VERSION_CITATION_WAIVERS:
                    continue
                errors.append(
                    f"{name}:{lineno}: cites version {found}, which no CHANGELOG "
                    f"heading defines and VERSION_CITATION_WAIVERS does not excuse"
                )
    return errors


# Where a deliverable goes, declared once per entry point. The rule lives in
# references/design-rules.md §8 and the other three restate it; scripts/ops/output_dir.py
# resolves it in code. That is five copies of one string, and a default that
# lives only in prose is exactly the drift that produced the defect this guard
# was written for — the package wrote finished client documents into its own
# install tree for four releases while every check stayed green.
#
# Adding an entry point, or moving the rule, means adding it here. A file that
# does not carry the literal fails rather than being skipped.
OUTPUT_DEFAULT = "Documents/LUMI-Style"
OUTPUT_DEFAULT_SITES = (
    "references/design-rules.md",     # the source of truth
    "SKILL.md",
    "AGENTS.md",
    "prompts/lumi-style-core.md",     # the prompt tier: no tools, so the literal is all it has
    "scripts/ops/output_dir.py",          # the resolver must agree with the prose
)


def check_output_default():
    """Every statement of the output default names the same literal directory."""
    errors = []
    for name in OUTPUT_DEFAULT_SITES:
        path = ROOT / name
        if not path.is_file():
            errors.append(f"{name}: declared in OUTPUT_DEFAULT_SITES and missing")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        # output_dir.py builds the path from two constants rather than writing it
        # out, so the literal is assembled the same way the script does.
        if name == "scripts/ops/output_dir.py":
            found = re.search(r'^DOCUMENTS\s*=\s*"([^"]+)"', text, re.M)
            folder = re.search(r'^FOLDER\s*=\s*"([^"]+)"', text, re.M)
            if not found or not folder:
                errors.append(f"{name}: DOCUMENTS and FOLDER are the resolver's "
                              f"half of this contract and one of them is gone")
                continue
            built = f"{found.group(1)}/{folder.group(1)}"
            if built != OUTPUT_DEFAULT:
                errors.append(f"{name}: resolves to {built!r}, the rules say "
                              f"{OUTPUT_DEFAULT!r}")
            continue
        if OUTPUT_DEFAULT not in text:
            errors.append(f"{name}: states the output default without naming "
                          f"{OUTPUT_DEFAULT!r} — an entry point that describes a "
                          f"different directory sends deliverables somewhere the "
                          f"others do not")
    return errors



def check_region_coverage():
    """Every country in the topology belongs to exactly one region.

    A country that reaches the renderer with no region is a hole in the map, and
    a silent one: it draws in the default fill and reads as deliberate. The
    registry is data and the topology is data, so this is decidable, so it is
    checked rather than remembered. The same guard catches the opposite mistake,
    a country claimed by two regions, which would make the four-colouring
    ambiguous rather than merely wrong.
    """
    topo_path = ROOT / "assets" / "vectors" / "world-110m.json"
    reg_path = ROOT / "assets" / "vectors" / "regions.json"
    for path in (topo_path, reg_path):
        if not path.exists():
            return [f"{rel(path)} is missing; run scripts/build/build_worldmap.py"]
    topo = json.loads(topo_path.read_text(encoding="utf-8"))
    reg = json.loads(reg_path.read_text(encoding="utf-8"))
    countries = {c["a"] for c in topo["countries"]}
    seen: dict[str, str] = {}
    errors = []
    for region in reg["regions"]:
        for code in region["members"]:
            if code in seen:
                errors.append(f"regions.json: {code} is claimed by both "
                              f"{seen[code]} and {region['id']}")
            seen[code] = region["id"]
            if code not in countries:
                errors.append(f"regions.json: {region['id']} names {code}, "
                              f"which is not in the topology")
    for code in sorted(countries - set(seen)):
        errors.append(f"regions.json: {code} belongs to no region")
    for node in reg.get("nodes", []):
        if node["region"] not in {r["id"] for r in reg["regions"]}:
            errors.append(f"regions.json: node {node['id']} names region "
                          f"{node['region']}, which does not exist")
    return errors


def check_brand_lock():
    """Every locked file still hashes to what the lock records.

    assets/brand/LOCKED.json names LUMIVATE's published marks and the component
    that draws them. This guard is what gives the lock teeth: without a gate,
    "locked" is a word in a README.

    It does not prevent an edit — nothing in a git repository can — it prevents
    an edit from arriving SILENTLY. Changing a published company mark becomes a
    deliberate act with a reason attached, recorded in the same commit, which
    is the only thing a lock in source control can honestly promise.
    """
    import lock as brand_lock  # resolved by the module-level bootstrap
    return brand_lock.verify()


# Phrases the prompt tier is allowed to omit, with the reason. Empty on
# purpose at creation: the audit found eighteen missing with no reason, and
# the fix was to add them, not to waive them.
NOT_IN_PROMPT: dict[str, str] = {}

# Sentences the prompt tier must carry verbatim (lower-cased comparison),
# each with the reason it is load-bearing for an agent that runs no scripts.
PROMPT_MUST_CARRY: tuple[tuple[str, str], ...] = (
    ("the number first",
     "the 0.1.521 rule; the full tier's scaffold enforces it, the prompt tier has only the sentence"),
    ("may not call a deliverable verified",
     "OR-9's prohibition half; the registry carries it, and the prompt tier is the one that never runs a check"),
)


# AGENTS.md's line ceiling. The number lives HERE, beside the guard that
# reads it, never in prose: convention 13. It was 286 lines at 0.1.522 after
# a design item that said it would shrink (GAP-018); the rewrite at 0.1.536
# made it a map of references/ at 125 lines, and the ceiling leaves room for
# a paragraph, not for a second rulebook. Raising it is a decision recorded
# in the CHANGELOG, the way a threshold is.
AGENTS_LINE_CEILING = 150


def check_entry_restatement_ceiling():
    """AGENTS.md stays a map. A hand-written entry point that restates rules
    is a copy per rule, and this one carried withdrawn rules for four versions
    and grew by a third during a refactor whose design said it would shrink.
    The ceiling is the mechanical half; what the lines SAY stays with the
    reviewer, as every other restatement does."""
    path = ROOT / "AGENTS.md"
    if not path.exists():
        return ["AGENTS.md is missing"]
    n = len(path.read_text(encoding="utf-8").splitlines())
    if n > AGENTS_LINE_CEILING:
        return [f"AGENTS.md is {n} lines, over the {AGENTS_LINE_CEILING}-line "
                f"ceiling — it is a map of references/, and a rule that belongs "
                f"in it belongs in references/ with a citation here"]
    return []


def check_prompt_parity():
    """The prompt tier carries what the full tier gates on.

    `prompts/lumi-style-core.md` is the self-contained file for agents with
    no tools. Nothing held it to the rules: the 2026-08-20 audit found it
    missing the number-first rule, six of eight storyline names and eighteen
    of sixty banned phrases, while `ban-list parity` held check_prose to
    writing-rules and never looked here. This holds it to three sources —
    the storyline vocabulary, the checker's ban list (or NOT_IN_PROMPT with
    a reason), and the sentences in PROMPT_MUST_CARRY.
    """
    path = ROOT / "prompts" / "lumi-style-core.md"
    if not path.exists():
        return ["prompts/lumi-style-core.md is missing"]
    text = path.read_text(encoding="utf-8")
    low = text.lower()
    errors = []
    for name in deliverable_registry.STORYLINES:
        if f"`{name}`" not in text:
            errors.append(f"prompt tier does not name storyline `{name}` — an agent "
                          f"that cannot read deliverable_registry has no other source")
    try:
        import check_prose
        banned = [phrase for _, phrase in check_prose.BANNED]
    except Exception as exc:  # noqa: BLE001 — a broken import is a finding
        return errors + [f"could not read check_prose.BANNED: {exc}"]
    for phrase in banned:
        if phrase.lower() in low or phrase in NOT_IN_PROMPT:
            continue
        errors.append(f"prompt tier omits banned phrase {phrase!r} and NOT_IN_PROMPT "
                      f"gives no reason")
    for phrase in NOT_IN_PROMPT:
        if phrase not in banned:
            errors.append(f"NOT_IN_PROMPT waives {phrase!r}, which check_prose does not ban")
    for sentence, _why in PROMPT_MUST_CARRY:
        if sentence not in low:
            errors.append(f"prompt tier does not carry {sentence!r}")
    return errors


def check_rubric_unbuilt_claims():
    """A sentence in eval-rubric.md saying a check is not built must cite the
    ledger entry that tracks it.

    The 2026-08-20 audit found `references/eval-rubric.md` listing D23 and
    D27 in its metric table while two rows of the same file said "there is no
    font-count check" and "agenda existence is checked by nothing today" —
    both written true, both false within a handful of releases, neither with
    anything to hold it. A claim of absence that names a GAP or IDEA is
    checked by the ledger guard (the id must exist) and read when the entry
    closes; one that names nothing rots in place. This is IDEA-11's shape —
    a promise conditional on a state — applied to the file that had it twice.
    """
    path = ROOT / "references" / "eval-rubric.md"
    if not path.exists():
        return []
    claim = re.compile(r"(?i)\bnot built\b|checked by nothing|there is no [\w -]{1,40}? check\b"
                       r"|\bunbuilt\b|\bnot yet built\b")
    cite = re.compile(r"\b(?:GAP|IDEA)-\d+\b")
    errors = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if claim.search(line) and not cite.search(line):
            errors.append(f"references/eval-rubric.md:{n}: says a check is not "
                          f"built and cites no GAP/IDEA — a claim of absence "
                          f"with nothing to hold it is how D23 and D27 were "
                          f"described as missing after they shipped")
    return errors


def check_no_shadow_markup():
    """No script re-grows a private strip-tags. The operation is
    `markup.strip_tags` / `markup.visible_text` / `markup.join_cjk`.

    The 2026-08-20 audit found four private strip-tags regexes
    and two of the CJK-space rule, each a little different, in a tree whose
    markup.py docstring lists the defects that class of duplication produced.
    """
    errors = []
    tag_re = re.compile(r"""re\.(?:sub|compile)\(\s*r?["']<\[\^>\]\+>["']""")
    cjk_re = re.compile(r"""\(\?<=\[\\u4e00-\\u9fff\]\) \(\?=\[\\u4e00-\\u9fff\]\)""")
    for path in sorted(p for p in (ROOT / "scripts").rglob("*.py")
                       if "__pycache__" not in p.parts):
        if path.name == "markup.py":
            continue
        text = path.read_text(encoding="utf-8")
        for regex, what in ((tag_re, "a private strip-tags"),
                            (cjk_re, "a private CJK-space rule")):
            for m in regex.finditer(text):
                line = text[:m.start()].count("\n") + 1
                errors.append(f"{rel(path)}:{line}: {what} — the shared "
                              f"implementation is scripts/lib/markup.py")
    return errors


def check_secret_patterns_parity():
    """One credential table. The repo guard and the deliverable checker both
    import scripts/lib/secret_patterns.py; a `re.compile(` anywhere else under
    scripts/ that spells a credential shape is a second table starting.

    Two tables existed until 0.1.525, neither a superset of the other, after a
    design that had forbidden exactly that. The markers are assembled at
    runtime so this guard's own source does not carry them whole.
    """
    errors = []
    for path in sorted(p for p in (ROOT / "scripts").rglob("*.py")
                       if "__pycache__" not in p.parts):
        if path.name == "secret_patterns.py":
            continue
        text = path.read_text(encoding="utf-8")
        for m in re.finditer(r"re\.compile\(\s*r?[\"'](.*?)[\"']", text, re.S):
            body = m.group(1)
            for marker in secret_patterns.MARKERS:
                if marker in body:
                    line = text[:m.start()].count("\n") + 1
                    errors.append(f"{rel(path)}:{line}: a credential regex "
                                  f"({marker!r}) outside scripts/lib/"
                                  f"secret_patterns.py — import PATTERNS, "
                                  f"do not start a second table")
    for name in ("scripts/check/check_repo.py", "scripts/check/check_privacy.py"):
        if "import secret_patterns" not in (ROOT / name).read_text(encoding="utf-8"):
            errors.append(f"{name} does not import secret_patterns")
    return errors


def check_no_shadow_math():
    """No script re-grows a private copy of the shared color or CSS readers.

    0.1.415's escape shape: a fix landed in one of several duplicated
    implementations while the same class stayed live in the others. 0.1.420
    extracted the one implementation into color_math.py / css_tokens.py; this
    guard is what keeps "one" true. It scans for the definition names — an
    import or a call is fine, a fresh `def` is the drift.
    """
    shared = {"color_math.py", "css_tokens.py"}
    owners = {
        "_lin": "color_math.py", "_luma": "color_math.py",
        "srgb_linear": "color_math.py", "srgb_encode": "color_math.py",
        "luma255": "color_math.py", "contrast255": "color_math.py",
        "contrast_hex": "color_math.py", "contrast_from_luma": "color_math.py",
        "css_vars": "css_tokens.py", "css_block": "css_tokens.py",
        "rule_vars": "css_tokens.py", "strip_comments": "css_tokens.py",
        "_vars": "css_tokens.py",
    }
    errors = []
    for path in sorted(p for p in (ROOT / "scripts").rglob("*.py")
                       if "__pycache__" not in p.parts):
        if path.name in shared:
            continue
        text = path.read_text(encoding="utf-8")
        for name, owner in owners.items():
            if re.search(rf"^\s*def {re.escape(name)}\(", text, re.M):
                errors.append(
                    f"{rel(path)} defines {name}() — the shared implementation "
                    f"lives in scripts/{owner}; import it instead of copying it")
    return errors


def check_ledgers():
    """The three ledgers stay parseable, closed entries stay honest, and no
    citation dangles.

    KNOWN_GAPS.md holds concrete gaps (GAP-ids), FAILURE_MODES.md holds
    escape classes (FM-ids), backlog/ideas-prd.md holds the backlog
    (IDEA-ids). Mechanically checkable: id uniqueness, legal statuses,
    per-status required keys, a `fixed`/`declined` entry's closing release
    exists in the CHANGELOG *and* that release's entry cites the id, no
    tracked bug hides in a code comment, and every id cited in CHANGELOG or
    specs/ exists in its ledger. What an entry SAYS stays with the reviewer —
    a guard pretending to judge prose would be FM-01 in this repo's own
    registry.
    """
    errors = []
    gaps_text = (ROOT / "KNOWN_GAPS.md").read_text(encoding="utf-8")
    fm_text = (ROOT / "FAILURE_MODES.md").read_text(encoding="utf-8")
    ideas_text = (ROOT / "backlog/ideas-prd.md").read_text(encoding="utf-8")
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    releases = re.findall(r"^##\s+(\d+\.\d+\.\d+)", changelog, re.M)

    def section_of(version):
        m = re.search(rf"^##\s+{re.escape(version)}\b.*?(?=^##\s|\Z)",
                      changelog, re.M | re.S)
        return m.group(0) if m else ""

    gap_ids = re.findall(r"^## (GAP-\d+)", gaps_text, re.M)
    fm_ids = re.findall(r"^## (FM-\d+)", fm_text, re.M)
    idea_ids = re.findall(r"^## (IDEA-\d+)", ideas_text, re.M)
    # A near-miss heading ("## GAP 003", "##GAP-4", "## gap-005") would fall
    # out of every structural check below — invisible, not validated. Catch
    # the shape that meant to be an id and is not one.
    for name, text_, strict in (("KNOWN_GAPS.md", gaps_text, r"^## GAP-\d+"),
                                ("FAILURE_MODES.md", fm_text, r"^## FM-\d+"),
                                ("backlog/ideas-prd.md", ideas_text,
                                 r"^## IDEA-\d+")):
        # "^## GAP-\d+" -> "GAP". The former slice (strict[6:index("-")])
        # produced "P"/""/"EA", so the detection below could never fire —
        # found by the tests this comment now cites (test_ledgers_guard.py).
        kind = strict.split()[1].split("-")[0]
        for m in re.finditer(rf"^##.*\b{kind}\b.*$", text_, re.M | re.I):
            line = m.group(0)
            if not re.match(strict, line) and "·" not in line.split(kind)[0]:
                # Prose headings that merely mention the word pass; a heading
                # SHAPED like an entry that does not parse as one fails.
                if re.match(rf"^##\s*{kind}[\s-]*\d", line, re.I):
                    errors.append(f"{name}: heading {line!r} looks like an "
                                  f"entry id but does not parse as one")
    for name, ids in (("KNOWN_GAPS.md", gap_ids), ("FAILURE_MODES.md", fm_ids),
                      ("backlog/ideas-prd.md", idea_ids)):
        dupes = {i for i in ids if ids.count(i) > 1}
        if dupes:
            errors.append(f"{name}: duplicate ids {sorted(dupes)}")

    for m in re.finditer(r"^## (GAP-\d+)[^\n]*\n(.*?)(?=^## |\Z)",
                         gaps_text, re.M | re.S):
        gid, body = m.group(1), m.group(2)
        keys = dict(re.findall(r"^- (\w+):\s*(.+)$", body, re.M))
        status = keys.get("status", "").split()[0] if keys.get("status") else ""
        if status not in ("open", "fixed", "declined"):
            errors.append(f"KNOWN_GAPS.md {gid}: status {status!r} is not "
                          f"open|fixed|declined")
            continue
        for req in ("status", "opened", "surface", "symptom", "check"):
            if req not in keys:
                errors.append(f"KNOWN_GAPS.md {gid}: missing '- {req}:'")
        needed = {"fixed": ("closed",), "declined": ("closed", "reason"),
                  "open": ()}[status]
        for req in needed:
            if req not in keys:
                errors.append(f"KNOWN_GAPS.md {gid}: status {status} requires "
                              f"'- {req}:'")
        if "closed" in keys and status != "open":
            closed = keys["closed"].strip()
            if closed not in releases:
                errors.append(f"KNOWN_GAPS.md {gid}: closed: {closed} names no "
                              f"CHANGELOG heading")
            elif gid not in section_of(closed):
                errors.append(f"KNOWN_GAPS.md {gid}: the {closed} CHANGELOG "
                              f"entry does not cite {gid} — a closure the "
                              f"release notes do not record")

    for m in re.finditer(r"^## (FM-\d+)[^\n]*\n(.*?)(?=^## |\Z)",
                         fm_text, re.M | re.S):
        fid, body = m.group(1), m.group(2)
        for req in ("detection", "prevention"):
            if not re.search(rf"^- {req}:", body, re.M):
                errors.append(f"FAILURE_MODES.md {fid}: missing '- {req}:'")

    # Tracked bugs live in the ledger, not in code comments.
    todo_re = re.compile(r"(TODO|FIXME)[^\n]*GAP" + r"-\d+")
    for path in sorted(p for p in (ROOT / "scripts").rglob("*.py")
                       if "__pycache__" not in p.parts) + sorted(
            (ROOT / "references").glob("*.md")):
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if todo_re.search(line):
                errors.append(f"{rel(path)}:{n}: a TODO/FIXME cites a GAP id — "
                              f"the ledger is the tracker, the comment is rot")

    known = set(gap_ids) | set(fm_ids) | set(idea_ids)
    cite_re = re.compile(r"\b(?:GAP|FM|IDEA)" + r"-\d+\b")
    for path in [ROOT / "CHANGELOG.md"] + sorted((ROOT / "specs").glob("*.md")):
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for cite in cite_re.findall(line):
                if cite not in known:
                    errors.append(f"{rel(path)}:{n}: cites {cite}, which no "
                                  f"ledger defines")
    return errors


def check_commit_convention():
    """A release commit's subject carries the version it ships.

    CLAUDE.md rule 3 has said `X.Y.Z — summary` for a long time and nothing
    checked it; ~10 of the 40 commits before 0.1.423 deviated. The enforceable
    subset, chosen to fit real history: only a commit that TOUCHES
    CHANGELOG.md must match — specs-only commits, fixture regens and backlog
    edits are exempt, which is exactly what the historical deviations were.
    Only HEAD is examined (history is not retroactively reddened); a merge
    commit is judged by its second parent; a tree with no .git — a tarball
    checkout — has nothing to assert.
    """
    if not (ROOT / ".git").exists():
        return []

    def git(*args):
        p = subprocess.run(["git", *args], cwd=ROOT,
                           capture_output=True, text=True)
        return p.returncode, p.stdout.strip()

    rc, subject = git("log", "-1", "--format=%s")
    if rc != 0:
        return []
    target = "HEAD"
    if subject.startswith("Merge "):
        rc, merged = git("log", "-1", "--format=%s", "HEAD^2")
        if rc == 0:
            target, subject = "HEAD^2", merged
        # A commit merely TITLED "Merge ..." with no second parent falls
        # through and is judged as itself — returning [] here exempted any
        # commit that borrowed the word (found by the PR #87 review).
    # -m --first-parent: without it, diff-tree prints NOTHING for a merge
    # commit, so when the judged target was itself a merge (the shape CI's
    # pull_request checkout produces every time) the guard saw no files and
    # exited clean — disarmed on exactly the event that runs it (same
    # review). With it, a merge reports its files against its first parent.
    rc, files = git("diff-tree", "--no-commit-id", "--name-only", "-r",
                    "-m", "--first-parent", target)
    if rc != 0 or "CHANGELOG.md" not in files.splitlines():
        return []
    m = re.match(r"(\d+\.\d+\.\d+) — ", subject)
    if not m:
        return [f"the commit touches CHANGELOG.md but its subject "
                f"{subject!r} does not follow 'X.Y.Z — summary' "
                f"(CLAUDE.md rule 3)"]
    # The CHANGELOG as of the commit being judged, NOT the working tree:
    # during release prep the next entry exists uncommitted while HEAD is
    # still the previous release, and that window is not a violation.
    rc, committed_changelog = git("show", f"{target}:CHANGELOG.md")
    if rc != 0:
        return []
    newest = re.search(r"^##\s+(\d+\.\d+\.\d+)", committed_changelog, re.M)
    if newest and m.group(1) != newest.group(1):
        return [f"the commit subject says {m.group(1)} but the newest "
                f"CHANGELOG heading is {newest.group(1)} — one of them is "
                f"lying about what this release is"]
    return []


# path -> reason. A hit that is deliberate rule DATA (an example in a rules
# file, a test fixture) is waived here with its reason, never silenced by
# narrowing the pattern.
SECRET_WAIVERS: dict[str, str] = {
    "tests/test_secrets_guard.py":
        "the guard's own failing fixtures: AWS's documented example key, a "
        "synthetic PEM header and a synthetic assignment — the strings that "
        "prove the guard can fail. (Spelling the key here would trip the "
        "guard on its own waiver table, which is how this sentence learned "
        "not to.)",
    "tests/test_check_privacy.py":
        "check_privacy's own failing fixtures: the same documented example key, "
        "used to prove its layer 1 can fire. The two checkers caught each other "
        "on the day the second one shipped, which is the pair working.",
}

# The table lives in scripts/lib/secret_patterns.py, shared with
# check_privacy.py; `secret patterns parity` keeps it the only one.
SECRET_PATTERNS = secret_patterns.PATTERNS


def _operator_terms():
    """-> compiled patterns from every list under the OR-8 directory, or []."""
    terms, status = check_privacy.load_terms(None)
    if status != "loaded":
        return []
    return [check_privacy.term_pattern(t) for t in terms]


def check_secrets():
    """No credential-shaped string ships in a tracked file.

    A check_repo guard rather than a CI action, for the same reason preflight
    exists: preflight runs what CI runs, and a gate that lives only in a
    workflow marketplace action is invisible to the local half of that
    contract (AG-5 in FAILURE_MODES.md records the decline).
    """
    if not (ROOT / ".git").exists():
        return []  # a tarball checkout has no listing to scan (documented)
    p = subprocess.run(["git", "ls-files"], cwd=ROOT,
                       capture_output=True, text=True)
    if p.returncode != 0:
        # A git failure INSIDE a git checkout is a finding, not a skip — the
        # PR #87 review pointed at check_js.py holding the opposite (correct)
        # policy for the identical condition.
        return [f"git ls-files failed ({p.stderr.strip()[:80]}) — the secret "
                f"scan did not run, and a scan that did not run is not a "
                f"scan that passed"]
    errors = []
    # The operator's out-of-bounds lists (OR-8: ~/.lumi/terms/*.terms.txt),
    # when this machine has them, are run over the tracked text too. Red
    # line 9's hard core (no client name in a tracked file) was held by habit
    # alone; the 2026-08-20 audit found a city name in eight tracked files.
    # In CI the directory does not exist and the half is simply not run — a
    # guard returns findings, not verdicts, so its absence is reported by
    # check_privacy on the deliverable side rather than silently here.
    terms = _operator_terms()
    for relpath in p.stdout.splitlines():
        if not relpath or relpath in SECRET_WAIVERS:
            continue
        path = ROOT / relpath
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue  # binary assets carry no greppable credential
        for term_re in terms:
            m = term_re.search(check_privacy.term_text(text))
            if m:
                line = text[:m.start()].count("\n") + 1
                # the term itself is never echoed: it is engagement data
                errors.append(f"{relpath}:{line}: a term the operator declared "
                              f"out of bounds — red line 9")
                break
        seen_lines: set[int] = set()
        for name, pattern in SECRET_PATTERNS:
            m = pattern.search(text)
            if m:
                line = text[:m.start()].count("\n") + 1
                # One finding per line: the shared table's assignment shape
                # overlaps its token shapes (`token = ghp_…` is both), and a
                # chatty scanner is a scanner people stop reading.
                if line in seen_lines:
                    continue
                seen_lines.add(line)
                errors.append(f"{relpath}:{line}: {name} — a credential-shaped "
                              f"string in a tracked file. Rotate it, remove "
                              f"it, or waive it in SECRET_WAIVERS with the "
                              f"reason it is data")
    return errors


# A script-path mention that is deliberate data (a hypothetical example, a
# threat-model illustration) is waived here with its reason, never silenced
# by narrowing the pattern. Starts empty on purpose.
# Keyed by (file, cited path): waiving one illustrative mention must not
# exempt the rest of the file — the PR #92 review found the whole
# emergency runbook outside the guard because of a file-scoped waiver.
SCRIPT_PATH_WAIVERS: dict[tuple[str, str], str] = {
    ("scripts/ops/emergency_merge.sh", "scripts/json" + ".py"):
        "the threat-model comment's HYPOTHETICAL stdlib-shadowing example — "
        "deliberate illustration, not a reference (the key is concatenated "
        "so this table cannot trip the guard on itself)",
}

# Files whose script-path mentions are FROZEN HISTORY and never rewritten,
# plus tests/ — synthetic tree fixtures cite paths that exist only in
# tmp_path by construction.
# releases/evidence/ is frozen history; releases/perf-baseline.json is
# LIVE (re-recorded, read by preflight) and stays scanned.
SCRIPT_PATH_FROZEN = ("CHANGELOG.md", "specs/", "releases/evidence/",
                      "conformance/results/", "tests/")

SCRIPT_PATH_RE = re.compile(r"scripts/[\w./-]+\.(?:py|sh|md)\b")

# The shape the string form cannot see: a path BUILT from pieces,
# `ROOT / "scripts" / "build" / "embed_globe.py"`. The 0.1.438 move broke
# exactly one of these (check_globe subprocessing embed_globe) and neither
# the sweep nor the string guard saw it — the checker crashed at obligation
# time instead. Reconstructed and resolved here so the remaining
# constructions cannot rot through the later moves.
SCRIPT_PATH_CONSTRUCTED_RE = re.compile(
    r'"scripts"(?:\s*/\s*"[\w]+")*\s*/\s*"[\w.]+\.(?:py|sh)"')


def check_script_paths():
    """Every `scripts/<path>` string in live tracked text resolves to a file.

    The scripts/ reorganization's enabling guard: ~180 prose and config
    mentions of script paths had no machine watching them — check_links only
    validates markdown links, and none target scripts/. A moved or renamed
    script would leave every doc mention rotting with CI green. From this
    guard on, a dangling mention is a failure; CHANGELOG and specs/ are
    frozen history and excluded; generated artifacts are scanned too, which
    holds their SOURCE literals honest through the regeneration gate.
    """
    p = subprocess.run(["git", "ls-files"], cwd=ROOT,
                       capture_output=True, text=True)
    if p.returncode != 0:
        return ["git ls-files failed — the script-path scan did not run, and "
                "a scan that did not run is not a scan that passed"]
    errors = []
    for relpath in p.stdout.splitlines():
        if not relpath:
            continue
        if any(relpath.startswith(f) for f in SCRIPT_PATH_FROZEN):
            continue
        path = ROOT / relpath
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for n, line in enumerate(text.splitlines(), 1):
            for match in SCRIPT_PATH_RE.finditer(line):
                cited = match.group(0)
                if (relpath, cited) in SCRIPT_PATH_WAIVERS:
                    continue
                if not (ROOT / cited).is_file():
                    errors.append(
                        f"{relpath}:{n}: cites {cited}, which does not exist "
                        f"— the script moved or was renamed; update the "
                        f"mention, regenerate the artifact, or waive it in "
                        f"SCRIPT_PATH_WAIVERS with a reason")
            for match in SCRIPT_PATH_CONSTRUCTED_RE.finditer(line):
                segments = re.findall(r'"([^"]+)"', match.group(0))
                cited = "/".join(segments)
                if not (ROOT / cited).is_file():
                    errors.append(
                        f"{relpath}:{n}: builds the path {cited}, which does "
                        f"not exist — a constructed script path rotted; "
                        f"update the pieces or waive with a reason")
    return errors


# The bare sibling-module names a scripts/ file may import. An import of one
# of these requires the canonical bootstrap block (the sys.path walk that
# makes bare names resolve from any drawer depth).
SIBLING_MODULES = (
    "geo_projection", "geo_frame", "globe_svg", "regionmap_svg", "sea_route",
    "color_math", "css_tokens", "lock", "deliverable_registry",
    "embed_globe", "embed_icons", "check_prose", "inspect_layout",
    "trace_schema", "rubric_items", "shipping", "fingerprint", "markup",
    "checker_report", "secret_patterns", "corpus", "gating",
    "gate_registry", "stamps", "trace_store", "shipped",
    "state_dir",
)
# Joined at runtime so this constant cannot satisfy the guard for THIS
# file: check_repo imports siblings too and owes the real block.
BOOTSTRAP_MARKER = "scripts path " + "bootstrap"
SIBLING_IMPORT_RE = re.compile(
    r"^\s*(?:import|from)\s+(" + "|".join(SIBLING_MODULES) + r")\b", re.M)


# The block's load-bearing lines: the guard asserts THESE, not the comment
# marker alone — the PR #92 review showed a bare marker comment satisfying
# the old check with no sys.path code behind it.
BOOTSTRAP_TUPLE = '("lib", "render", "check", "build", "ops", "")'
BOOTSTRAP_APPEND = "_bs_sys.path.append(_p)"


def check_bootstrap():
    """A script that imports a sibling carries the canonical bootstrap block
    — the CODE, not just the marker — with the canonical drawer order
    (lib first, scripts root LAST: the emergency path's shadow defense).

    Also holds SIBLING_MODULES to lib/'s actual contents: a new shared
    module whose importers were never checked is enumeration rot wearing a
    guard's clothes.
    """
    errors = []
    lib_stems = {p.stem for p in (ROOT / "scripts" / "lib").glob("*.py")}
    missing = lib_stems - set(SIBLING_MODULES)
    for stem in sorted(missing):
        errors.append(
            f"scripts/lib/{stem}.py is not in SIBLING_MODULES — its "
            f"importers are invisible to this guard")
    for path in sorted(p for p in (ROOT / "scripts").rglob("*.py")
                       if "__pycache__" not in p.parts):
        text = path.read_text(encoding="utf-8")
        m = SIBLING_IMPORT_RE.search(text)
        if not m or path.stem == m.group(1):
            continue
        if BOOTSTRAP_MARKER not in text:
            errors.append(
                f"{rel(path)} imports sibling {m.group(1)!r} without the "
                f"canonical bootstrap block — bare names stop resolving the "
                f"moment this file or its sibling changes drawers")
            continue
        if BOOTSTRAP_APPEND not in text or BOOTSTRAP_TUPLE not in text:
            errors.append(
                f"{rel(path)} carries the bootstrap marker but not the "
                f"canonical block (append line + drawer tuple, lib first "
                f"and root last) — a marker without the code is a vacancy "
                f"wearing a badge")
    return errors


def check_scaffold_slots():
    """D14's scaffold-slot list and what the scaffold actually emits are one list.

    `new_deck.py` hands an author a document that already renders, and the
    price is furniture worded to be replaced. D14 refuses those strings, and
    for one release it knew two of them — so an author who fixed both still
    shipped a cover reading "One sentence saying what this is." The two files
    cannot import each other (a deliverable grader may not depend on the
    scaffold generator, and the generator already reads the fixture), so this
    holds them together from outside, both ways:

      · every string D14 lists must still appear in the scaffold — otherwise
        it is a pattern guarding nothing, and the next reader trusts it;
      · a scaffold with all of them substituted must leave D14 with nothing —
        otherwise the scaffold has furniture the list has not learned.
    """
    import contextlib
    import io

    import check_design
    import new_deck

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), \
            contextlib.redirect_stderr(io.StringIO()), \
            contextlib.suppress(SystemExit):
        new_deck.main(["--genre", "training", "--pages", "2"])
    html = buf.getvalue()
    if "<section" not in html:
        return ["scripts/ops/new_deck.py emitted no scaffold, so D14's slot "
                "list could not be held against it"]
    errors = []
    for slot in check_design.AUTHOR_FILL:
        if slot not in html:
            errors.append(
                f"check_design.AUTHOR_FILL lists {slot!r}, which the scaffold "
                f"no longer emits — a pattern guarding nothing")
    filled = html
    for slot in check_design.AUTHOR_FILL:
        filled = filled.replace(slot, "filled in by the author")
    left = check_design.d14_placeholders(filled)
    if left:
        errors.append(
            f"the scaffold still trips D14 after every declared slot is "
            f"substituted ({left[0]['text']!r} on {left[0]['page']}) — it "
            f"emits furniture check_design.AUTHOR_FILL has not learned")
    return errors


# ── The metric vocabularies, read from the scripts that define them ──────────
# Two guards live on this. They exist because one wrong count — "check_design.py
# gates on three things: D12, D14, D15" — outlived the release that made it wrong
# by eight releases and was found in NINE places, two days running: fixed in two
# files on the first day, still live in eight on the second, one of them in
# AGENTS.md eighty-six lines below the line that had just been corrected, beside
# that file's own written confession about this exact drift. Twenty-six of this
# repository's releases have carried a fix for a prose copy disagreeing with the
# code; five of the last ten have. A number a person maintains by remembering is
# not maintained.

METRIC_AUTHORITIES = gating.METRIC_AUTHORITIES

# WHERE A GATING SET IS CLAIMED IN WORDS, and the pattern that captures the ids
# it names. Same discipline as ENTRY_STAMP: a site declared here whose pattern
# stops matching is an ERROR, never a skip, so rewording a claim cannot silently
# retire the check on it. To add a claim, add a line. To delete one, delete the
# prose — which is the better move whenever the sentence can name the authority
# instead of counting (preflight.py's docstring is the model: "how many is
# whatever the workflow says today, never a number written here").
# The patterns locate the SENTENCE and never its count. A claim reading "four"
# today reads "five" the day a gate is added, and a pattern keyed on the number
# would need editing at exactly the moment the guard is supposed to fire — which
# is how a guard becomes a formality. Every count here is `\w+`.
# A site may declare this instead of a pattern: the prose names
# check_design.py as the authority and enumerates nothing.
AUTHORITY_NAMED = "<authority-named>"
# Each authority-named site declares the sentence that DOES the naming, because
# there is now more than one and they do not share wording. SKILL.md's was
# unwatched entirely and said "gates on four things" while eighteen design
# verdicts gated — in the file an agent actually loads.
AUTHORITY_ANCHORS = {
    "references/design-rules.md":
        r"[^\n]*checks in `check_design\.py` that fail the run[^\n]*(?:\n[^\n]+)*",
    "SKILL.md":
        r"[^\n]*gates on every row its own table marks[^\n]*(?:\n[^\n]+)*",
}

GATING_CLAIM_SITES: dict[str, str] = {
    "AGENTS.md": r"\*\*((?:D\d+(?:,? (?:and )?)?)+) gate; every other D-metric",
    # Re-anchored at 0.1.549: the sentence used to open "Eleven of its metrics"
    # and close "All eleven are", so adding a gate meant editing two count words
    # this guard does not read — a number that can rot while the check stays
    # green. It now names its authority instead (convention 13) and the anchors
    # are the words around the id list rather than the count.
    "CLAUDE.md": r"metrics that \*\*gate\*\*(.*?)Every one of them is",
    "references/eval-rubric.md": r"\*\*\w+ exceptions.*?\*\*(.*?)— all decidable",
    # AUTHORITY_NAMED: this site stopped enumerating and now points at the
    # `(gates)` target string instead. Convention 13's preferred outcome — a
    # sentence that names its authority cannot rot — but the entry STAYS, and
    # the guard now checks the opposite thing: that no id list has grown back
    # into the sentence. Dropping the entry would leave the site unwatched,
    # which is how it rotted the first two times.
    "references/design-rules.md": AUTHORITY_NAMED,
    # SKILL.md is the entry an agent loads, and it carried an unwatched count.
    "SKILL.md": AUTHORITY_NAMED,
    "references/brand.md": r"only ((?:D\d+/?)+) gate",
}


# A range that is QUOTED rather than claimed. The waiver carries its reason, the
# way SCRIPT_PATH_WAIVERS does: a sentence reproducing an error verbatim is the
# only thing in this repository that may state a stale range, because correcting
# the quotation would destroy the record of what was corrected.
METRIC_RANGE_WAIVERS = {
    ("AGENTS.md", "D1–D4"):
        "quotes, inside quotation marks, the wrong claim this line carried for "
        "eight releases; the confession is the value",
    ("scripts/check/check_repo.py", "D1–D4"):
        "this table has to name the string it waives",
}


def _metric_ids(prefix: str) -> tuple[set[str], set[str]]:
    """-> (every id that produces a verdict row, the subset whose target gates).

    One implementation, in `scripts/lib/gating.py`, because a second consumer
    arrived: `run_conformance` holds a conformance deliverable to the same set
    this guard holds the prose to. Two readings of "which metrics gate" is the
    shape `checker_report` was extracted to end.
    """
    return gating.metric_ids(prefix, ROOT)


def check_scoring_sheet_parity():
    """The sheet's reviewer-language wording covers exactly the rubric's items.

    `eval-rubric.md` requires the items to be written in the reviewer's
    language, so the sheet carries its own wording — and a second wording of the
    same list is this repository's oldest defect shape. The parity is the price
    of the translation: an item with no wording, or a wording naming an item
    that is gone, fails here.

    It lives in scripts/lib/ so this guard need not reach into scripts/ops/,
    which would make the emergency-merge path run the pull request's own
    copy of the file being checked.

    The last sheet described H1-H6 for two releases after C1-C8 replaced them.
    Nothing caught it, because nothing held the sheet to the rubric.
    """
    import importlib.util
    path = ROOT / "scripts" / "lib" / "rubric_items.py"
    if not path.exists():
        return ["scripts/lib/rubric_items.py is missing"]
    spec = importlib.util.spec_from_file_location("_rubric_items", path)
    if spec is None or spec.loader is None:
        return ["scripts/lib/rubric_items.py cannot be loaded"]
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    rubric_items = {(did, item.split()[0])
                    for did, _t, items in mod.dimensions() for item in items}
    if not rubric_items:
        return ["the rubric yielded no evidence items — the guard would pass "
                "vacuously, and the sheet would be empty"]
    errors = []
    for key in sorted(rubric_items - set(mod.WORDING)):
        errors.append(f"{key[0]}-{key[1]} is in the rubric and has no wording in "
                      f"rubric_items.py — a reviewer would get the English row")
    # A condition is a second list keyed the same way, and drifts the same way:
    # a condition left behind for a withdrawn item would print a caveat about
    # something the sheet no longer asks.
    for key in sorted(set(getattr(mod, "CONDITION", {})) - rubric_items):
        errors.append(f"{key[0]}-{key[1]} has a condition and is not in the "
                      f"rubric — the sheet would caveat an item it no longer asks")
    for key in sorted(set(mod.WORDING) - rubric_items):
        errors.append(f"{key[0]}-{key[1]} has a wording and is not in the rubric "
                      f"— the sheet describes an item that no longer exists")
    # Since 0.1.489 the sheet asks the reviewer for a rating and a sentence per
    # DIMENSION rather than a tick per item, so the per-dimension prose is now
    # the instrument. Each of the three tables answers one of the three things
    # the owner reported missing, and a dimension short of any of them prints a
    # question that does not say what it is for — which is the defect that
    # forced this rewrite, arriving back through a table nobody held.
    for did in sorted({d for d, _ in rubric_items}):
        if did not in mod.DIM_TITLE:
            errors.append(f"{did} has no dimension title in the sheet")
        for table, what in ((mod.PURPOSE, "what it protects against"),
                            (mod.WHERE, "where to look"),
                            (mod.EXAMPLE, "how to answer it")):
            if not table.get(did):
                errors.append(f"{did} does not say {what} — the sheet would ask "
                              f"a question that never states its purpose")
    for did in sorted(set(mod.PURPOSE) | set(mod.WHERE) | set(mod.EXAMPLE)
                      | set(mod.DIMENSION_NA)):
        if did not in mod.DIM_TITLE:
            errors.append(f"{did} carries sheet prose and is not a dimension — "
                          f"the sheet would describe a dimension that is gone")
    return errors

def check_shape_library():
    """The shape library's manifest and its files are the same set, and every
    shape actually draws something.

    Counting files proves nothing: a file can exist, parse, and render as an
    empty frame — a defect this library produced twice during extraction. The
    staging area has a six-check audit that follows geometry from the source
    page to the rendered pixel; what THIS checks is the half that lives here —
    that the ingestion is complete, that the manifest describes exactly the
    files present, and that no shipped shape is an empty tree.

    It also holds `relation_from` to its three legal values. `unclassified` is
    one of them and is not a failure: 70 units are in that state, they are
    usable, and marking them is the alternative to guessing — two curations of
    this library were wrong precisely because a name was read as a
    classification.
    """
    lib = ROOT / "assets" / "shapes"
    # `not ingested` was a legal state when nothing shipped that reads the
    # library. `embed_shapes.py` does — it is the build step SKILL.md and
    # AGENTS.md tell an author to run — so its presence is the claim that the
    # library ships, and the claim is what makes an absent directory a failure
    # rather than a legal state. Without this, `git rm -r assets/shapes` passed
    # the whole of check_repo.
    embedder = ROOT / "scripts" / "build" / "embed_shapes.py"
    if not lib.exists():
        if embedder.exists():
            return ["assets/shapes/ does not exist, and "
                    "scripts/build/embed_shapes.py ships to read it — a build "
                    "step whose input is missing is not an un-ingested library"]
        return []
    manifest = lib / "tags.json"
    if not manifest.exists():
        return ["assets/shapes/ exists with no tags.json — a library with no "
                "manifest cannot be chosen from"]
    try:
        doc = json.loads(manifest.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"assets/shapes/tags.json does not parse: {exc}"]

    shapes = doc.get("shapes") or {}
    if not shapes:
        return ["assets/shapes/tags.json names no shapes — the guard would pass "
                "vacuously"]
    # ASK GIT, NOT THE FILESYSTEM. The glob version found 206 files and passed
    # while `.gitignore` excluded every one of them, so the library existed on
    # one machine and in no clone — the defect 0.1.496 fixed and this guard
    # could not see. A working tree cannot tell `shipped` from `present here`.
    # A tarball checkout has no index to ask and falls back to the glob.
    files = _tracked_stems("assets/shapes")
    if files is None:
        files = {p.stem for p in lib.glob("*.svg")}
    errors = []
    for missing in sorted(files - set(shapes)):
        errors.append(f"assets/shapes/{missing}.svg is shipped and the manifest "
                      f"does not describe it")
    for dangling in sorted(set(shapes) - files):
        errors.append(f"tags.json describes {dangling}, which is not shipped")
    # A MANIFEST FIELD MAY NOT POINT AT A FILE THE PACKAGE DOES NOT SHIP.
    # Every one of the 206 records carried `"preview": "previews/<id>.png"`,
    # `assets/shapes/previews/` was empty, and `.gitignore` excluded *.png
    # anyway — so the manifest described 206 files that existed on nobody's
    # machine. The rebuild spec's own discipline ("open the preview before
    # using a shape") pointed at them. This is the shape-library defect in
    # miniature, and it survived the release that fixed the library.
    # A path, not "any string with a slash in it". The first version of this
    # matched on the slash alone and read a NOTE — "illustrative / draft / for
    # discussion only stamps" — as a filename. Convention 15 in one line: the
    # pattern was written from the shape of the idea instead of from the
    # material, and one run against the real manifest said so.
    path_like = re.compile(r"^[\w.][\w./-]*\.(?:png|svg|jpe?g|webp|json)$")
    for sid, rec in sorted(shapes.items()):
        for key, value in sorted(rec.items()):
            if not isinstance(value, str) or not path_like.match(value):
                continue
            if not (lib / value).exists():
                errors.append(
                    f"tags.json: {sid}.{key} points at {value!r}, which the "
                    f"package does not ship — a manifest describing a file "
                    f"nobody has is the library defect in miniature")

    # `looked-at` is the strongest of the four and the only one that has never
    # been wrong here: somebody opened the rendered preview. `unclassified`
    # stays legal because marking one is the alternative to guessing.
    LEGAL = {"tag", "page-name", "looked-at", "unclassified"}
    for name, rec in sorted(shapes.items()):
        if rec.get("relation_from") not in LEGAL:
            errors.append(f"{name}: relation_from {rec.get('relation_from')!r} is "
                          f"not one of {sorted(LEGAL)}")
    for path in sorted(lib.glob("*.svg")):
        text = path.read_text(encoding="utf-8", errors="replace")
        if not re.search(r"<(path|rect|circle|ellipse|polygon|polyline|line)\b", text):
            errors.append(f"{rel(path)} carries no geometry — a shape that "
                          f"renders as an empty frame is the defect the "
                          f"extraction audit exists to catch")
    return errors

def check_brand_registry():
    """The brand registry names brands whose assets exist, and it stays thin.

    It answers which asset pack and which wordmark, and nothing else. Palette
    lives in tokens/, rules live in references/, and a brand record that started
    carrying either would become the fifth surface restating them — which is the
    defect this whole refactor exists to remove, arriving through a new door.

    The default brand must be one of the brands, and every path a record names
    must exist: a registry pointing at a missing asset pack is worse than none,
    because a build reads it and produces a deliverable with nothing on the
    cover.
    """
    path = ROOT / "brands" / "registry.json"
    if not path.exists():
        return ["brands/registry.json is missing"]
    try:
        reg = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"brands/registry.json does not parse: {exc}"]

    errors = []
    brands = reg.get("brands") or {}
    if not brands:
        return ["brands/registry.json defines no brands — the guard would pass vacuously"]
    if reg.get("default") not in brands:
        errors.append(f"default brand {reg.get('default')!r} is not one of "
                      f"{sorted(brands)}")
    ALLOWED = {"wordmark", "assets", "cover_mark", "locked", "status"}
    for name, rec in brands.items():
        extra = sorted(set(rec) - ALLOWED)
        if extra:
            errors.append(f"brand {name!r} carries {extra}; the registry answers "
                          f"which assets and which wordmark, and rules and palette "
                          f"stay in references/ and tokens/")
        for key in ("assets", "cover_mark", "locked"):
            target = rec.get(key)
            if target and not (ROOT / target).exists():
                errors.append(f"brand {name!r} {key} -> {target}, which does not exist")
    return errors

def check_two_axis_vocabulary():
    """The rule tier and the storyline stay two axes, each derived, neither faked.

    `genre` used to answer two questions at once — which thresholds apply, and
    what shape the argument has. The split only helps if the two halves stay
    honest, and there are exactly two ways for it to rot.

    **A tier table that does not match what keys on genre.** TIERS is a claim
    about behaviour: that `internal` is the tier exempt from the dash ban and
    `training` is the tier with its own visual-share target. If someone changes
    DASH_BANNED or VISUAL_SHARE_TARGET without changing TIERS, the tier becomes
    a label with nothing behind it, which is the state `genre` was in before the
    split.

    **A storyline vocabulary nobody uses, or one used outside the vocabulary.**
    A trace declaring a storyline the registry does not define means the closed
    schema is not closed.
    """
    errors = []
    try:
        import deliverable_registry as reg
    except Exception as exc:                       # noqa: BLE001
        return [f"deliverable_registry does not import: {exc}"]

    if set(reg.TIERS) != set(reg.GENRES):
        errors.append(f"TIERS covers {sorted(reg.TIERS)} but the genres are "
                      f"{sorted(reg.GENRES)} — every genre needs a tier or it "
                      f"resolves to nothing")
    prose = (ROOT / "scripts" / "check" / "check_prose.py").read_text(encoding="utf-8")
    m = re.search(r"DASH_BANNED = \(([^)]*)\)", prose)
    if not m:
        errors.append("check_prose.py has no DASH_BANNED — the tier table's "
                      "first claim cannot be checked")
    else:
        banned = set(re.findall(r'"([^"]+)"', m.group(1)))
        exempt = {g for g in reg.GENRES if g not in banned}
        claimed = {g for g, t in reg.TIERS.items() if t == "internal"}
        if exempt != claimed:
            errors.append(f"TIERS says the dash-exempt tier is {sorted(claimed)} "
                          f"but DASH_BANNED leaves {sorted(exempt)} exempt")
    layout = (ROOT / "scripts" / "check" / "inspect_layout.py").read_text(encoding="utf-8")
    m = re.search(r"VISUAL_SHARE_TARGET = \{([^}]*)\}", layout)
    if not m:
        errors.append("inspect_layout.py has no VISUAL_SHARE_TARGET — the tier "
                      "table's second claim cannot be checked")
    else:
        targets = dict(re.findall(r'"([^"]+)":\s*(\d+)', m.group(1)))
        odd = {g for g, v in targets.items() if v != "50"}
        claimed = {g for g, t in reg.TIERS.items() if t == "training"}
        if odd != claimed:
            errors.append(f"TIERS says the tier with its own visual-share target "
                          f"is {sorted(claimed)} but the odd targets are {sorted(odd)}")

    if not reg.STORYLINES:
        errors.append("STORYLINES is empty — the second axis would be decorative")
    declared = trace_schema.ENUMS.get("storyline")
    if declared is not None and set(declared) != set(reg.STORYLINES):
        errors.append("the trace schema's storyline vocabulary and the "
                      "registry's have drifted apart")
    return errors

def check_metric_id_ranges():
    """A range written from 1 claims the whole family, so its end is checkable.

    A range ending at 17 said the design checker stopped there, in five files, while D18 and
    D19 both shipped verdict rows — including one sentence that named D19 as a
    gate four words later. This reads only ranges that START at 1, because those
    are the ones claiming completeness; `M8-M11` names a subset on purpose and is
    none of this guard's business.

    Nothing is declared here. The claim sites are found, so a new one written
    tomorrow is covered the day it is written — which is the difference between
    this and the list it replaces.
    """
    tops = {}
    try:
        for prefix in METRIC_AUTHORITIES:
            ids = _metric_ids(prefix)[0]
            # A checker defining no ids of its family has nothing to compare
            # against; that is a question for the guard that reads THAT file,
            # not a reason to stop reading the other one.
            if ids:
                tops[prefix] = max(int(i[1:]) for i in ids)
    except (OSError, SyntaxError) as exc:                           # noqa: BLE001
        return [f"could not read the metric vocabularies: {exc}"]

    listed = subprocess.run(["git", "ls-files"], cwd=ROOT,
                            capture_output=True, text=True)
    if listed.returncode != 0:
        return ["git ls-files failed — the metric-range scan did not run, and a "
                "scan that did not run is not a scan that passed"]
    errors = []
    for relpath in listed.stdout.splitlines():
        # CHANGELOG and specs/ are frozen history: each entry was true when it
        # was written and is not retroactively corrected.
        if not relpath or any(relpath.startswith(f) for f in SCRIPT_PATH_FROZEN):
            continue
        try:
            text = (ROOT / relpath).read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for n, line in enumerate(text.splitlines(), 1):
            for prefix, top in tops.items():
                for m in re.finditer(rf"\b{prefix}1\s*[-–—]\s*{prefix}?(\d+)\b", line):
                    if (relpath, m.group(0)) in METRIC_RANGE_WAIVERS:
                        continue
                    if int(m.group(1)) != top:
                        errors.append(
                            f"{relpath}:{n}: claims {m.group(0)}, but "
                            f"{METRIC_AUTHORITIES[prefix]} defines up to "
                            f"{prefix}{top} — a range written from 1 claims the "
                            f"whole family, so say {prefix}1-{prefix}{top} or "
                            f"name the script as the authority instead")
    return errors


def check_gating_claims():
    """Every sentence naming WHICH metrics gate names the set that gates.

    The one that keeps rotting. `check_design.py` decides this in one place — the
    target string "(gates)" on a row — and the answer has changed twice by a
    release adding a gate and no release changing the prose.

    Deliberately NOT a search for sentences about gating: deciding whether an
    English sentence is making that claim is the phrase-trigger guard AG-1
    declined in 0.1.422 as brittle by construction. The sites are declared and
    the IDS inside them are matched lexically, which is decidable.
    """
    try:
        gating = _metric_ids("D")[1]
    except (OSError, SyntaxError) as exc:                           # noqa: BLE001
        return [f"could not read the gating metrics: {exc}"]

    truth = ", ".join(sorted(gating, key=lambda x: int(x[1:])))
    errors = []
    for name, pattern in sorted(GATING_CLAIM_SITES.items()):
        path = ROOT / name
        if not path.exists():
            errors.append(f"{name} is a declared gating-claim site and does not exist")
            continue
        text = path.read_text(encoding="utf-8")
        if pattern is AUTHORITY_NAMED:
            # The claim is delegated, so the failure to look for is the list
            # coming back. Anchored on the same sentence: three or more metric
            # ids inside one paragraph of it is an enumeration by any reading.
            para = re.search(AUTHORITY_ANCHORS[name], text)
            if not para:
                errors.append(
                    f"{name}: declared as naming check_design.py as the "
                    f"authority, and the sentence that does so is gone")
            elif len(set(re.findall(r"\bD\d+\b", para.group(0)))) >= 5:
                errors.append(
                    f"{name}: names the authority AND enumerates the gates "
                    f"again — that list is what rotted twice. Keep one or the "
                    f"other, and this site is declared as the authority form")
            continue
        found = re.search(pattern, text, re.S)
        if not found:
            errors.append(
                f"{name}: the declared gating claim no longer matches its pattern. "
                f"Re-point it at the sentence, or delete the sentence and name "
                f"check_design.py as the authority — do not drop the entry")
            continue
        claimed = set(re.findall(r"D\d+", found.group(1)))
        if claimed != gating:
            errors.append(
                f"{name}: names {', '.join(sorted(claimed, key=lambda x: int(x[1:]))) or '(none)'}"
                f" as the design checks that gate; check_design.py gates on {truth}")
    return errors


PROSE_GATE_SITES: dict[str, tuple[str, str]] = {
    # The rubric's own metric table. Each row's target cell either says
    # `**gates**` or it does not, and the set of rows that say it is a claim
    # about check_prose.py.
    "references/eval-rubric.md::table":
        (r"^\|\s*(M\d+\w*)\s*\|[^|]*\|([^|]*)\|", "rows"),
    # And the sentence below it, which argues from an EXAMPLE rather than
    # enumerating — so the claim it makes is the weaker one: nothing it calls a
    # gate may fail to be one. Holding it to the full set would be this guard
    # being wrong about its material; it said "M2 and M6 do gate" from the
    # release that wrote it until 0.1.566, and M2 has never carried `(gates)`.
    # The commit that wrote that sentence did not touch M2's code at all —
    # convention 14, in the file that teaches the rubric.
    "references/eval-rubric.md::sentence":
        (r"\*\*((?:M\d+\w*(?:,? (?:and )?)?)+) (?:do|does) gate\*\*", "names"),
}


# A backticked identifier whose family a layout verdict owns, and which names
# no verdict. Both defects this found on its first run had that shape: prose
# had abbreviated `figure_axis_named` to `figure_axis`, and had given the
# `figure axes:` REPORT line — which is not a verdict and which nothing keys on
# — a verdict-shaped name of its own. A reader looking either of them up finds
# nothing, and in this case the surrounding sentence said the unnamed-axis case
# reports when it gates. Waivers, not a looser pattern: a false positive here
# would rewrite prose to match a wrong check.
VERDICT_NAME_FROZEN = ("CHANGELOG.md", "specs/", "releases/evidence/",
                       "conformance/results/", "tests/")
VERDICT_NAME_WAIVERS: dict[tuple[str, str], str] = {}
VERDICT_NAME_RE = re.compile(r"`([a-z][a-z0-9]*(?:_[a-z0-9]+)+)`")


# An absolute path into somebody's home directory, in a TRACKED file. The
# username is the leak; the rest of the path is usually meaningful and stays.
# `~` is the fix at both ends — recorded portably, `expanduser()`d when read
# back — and `run_conformance._portable` is the writer's half.
# Names that are an EXAMPLE rather than a person. `/Users/you` in an install
# instruction is the prose that most naturally names a home directory, and
# failing it accused the author of shipping a username they had not shipped.
LOCAL_PATH_PLACEHOLDERS = ("x", "you", "me", "user", "username", "name",
                           "someone", "yourname", "your-name", "USERNAME")
# A HOME PATH, in either the absolute or the tilde-user form. `~someone/` leaks
# the username exactly as `/Users/someone/` does, and is what a careless author
# writes after reading this guard's own advice to "write it as `~/...`".
_NOT_A_PERSON = r"(?!(?:" + "|".join(LOCAL_PATH_PLACEHOLDERS) + r")\b)"
LOCAL_PATH_RE = re.compile(
    r"/(?:Users|home)/" + _NOT_A_PERSON + r"[A-Za-z0-9][A-Za-z0-9._-]*"
    # The tilde-user form needs the SLASH: without it `~2.6s` in a timing note
    # reads as a home directory, which is how the first draft failed on the
    # CHANGELOG's own performance figures.
    + r"|~" + _NOT_A_PERSON + r"[A-Za-z][A-Za-z0-9._-]*(?=/)")
LOCAL_PATH_WAIVERS: dict[tuple[str, str], str] = {}


def check_shipped_closure():
    """The boundary between the two repositories PARTITIONS the tracked tree.

    A list of what ships can omit a file silently and still look complete; a
    partition cannot. The assertion that matters is that **every tracked file
    is PLACED** — a rule claims it, longest prefix winning, or reachability
    computes its side because it is a script. Not "exactly one rule": no rule
    claims a script at all, and several rules may match one file. Beside it:
    every rule declares a side this code understands and a reason a person can
    read, no rule claims nothing (a dead rule is a boundary decision that has
    stopped being true), every seed and every pin names a script that exists,
    and no consumer script imports a pinned one.

    Scripts are absent from the manifest ON PURPOSE — their side is computed
    from reachability, so a new one is development until something the skill
    can reach imports or invokes it. Wrong in the safe direction: a dev script
    wrongly kept is dead weight, a consumer script wrongly dropped is a broken
    install.
    """
    import shipped
    try:
        decl = shipped.manifest(ROOT)
    except (OSError, ValueError) as exc:                            # noqa: BLE001
        return [f"could not read {shipped.MANIFEST}: {exc}"]

    p = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT,
                       capture_output=True, text=True)
    if p.returncode != 0:
        return [f"git ls-files failed ({p.stderr.strip()[:80]}) — the shipped "
                f"closure did not run, and a scan that did not run is not a "
                f"scan that passed"]
    tracked = [f for f in p.stdout.split("\0") if f]
    consumer = shipped.consumer_scripts(ROOT)
    errors = []
    # A rule whose `side` is misspelled disarms the teeth SILENTLY: `side_of`
    # returns the raw string, this guard only asked whether it was non-None,
    # and `check_cross_boundary_paths` compares against "dev" — so one
    # capitalised letter made a whole directory invisible while the partition
    # still reported itself total. A JSON edit produces exactly that typo.
    for rule in decl["rules"]:
        if rule.get("side") not in ("consumer", "dev"):
            errors.append(
                f"{shipped.MANIFEST}: the rule for `{rule.get('prefix')}` "
                f"declares side {rule.get('side')!r}; it is 'consumer' or 'dev'")
        if not (rule.get("why") or "").strip():
            errors.append(
                f"{shipped.MANIFEST}: the rule for `{rule.get('prefix')}` gives "
                f"no reason. A boundary nobody can explain is a boundary nobody "
                f"can maintain")
    if errors:
        return errors
    claimed: set[str] = set()
    for relpath in tracked:
        side = shipped.side_of(relpath, ROOT, consumer)
        if side is None:
            errors.append(
                f"{relpath} is tracked and no rule in {shipped.MANIFEST} "
                f"claims it. The manifest partitions the tree — add a rule "
                f"naming its side and why, rather than leaving the projection "
                f"to guess")
            continue
        hits = [r["prefix"] for r in decl["rules"]
                if shipped.matches(relpath, r["prefix"])]
        if hits:
            claimed.add(max(hits, key=len))
    for rule in decl["rules"]:
        if rule["prefix"] not in claimed:
            errors.append(
                f"{shipped.MANIFEST}: the rule for `{rule['prefix']}` claims no "
                f"tracked file. A boundary decision that has stopped being true "
                f"is worse than none — delete it or re-point it")
    known = {q.stem for q in
             list(ROOT.glob("scripts/*/*.py")) + list(ROOT.glob("scripts/*.py"))}
    for seed in decl.get("consumer_seeds", []):
        if seed not in known:
            errors.append(
                f"{shipped.MANIFEST}: consumer seed `{seed}` names no script")
    # A pin overrides reachability, so it is AUDITED rather than trusted.
    # Reachability cannot tell a call from a mention — two development tools
    # rode a docstring into the consumer half — but an IMPORT is not a mention,
    # and no consumer script may import something pinned to the other side.
    for pin in decl.get("dev_pins", []):
        stem = pin["stem"]
        if stem not in known:
            errors.append(
                f"{shipped.MANIFEST}: dev pin `{stem}` names no script")
            continue
        importers = shipped.imports_of(stem, ROOT) & consumer
        if importers:
            errors.append(
                f"{shipped.MANIFEST}: `{stem}` is pinned to the development "
                f"side and {', '.join(sorted(importers))} import(s) it. A pin "
                f"may override a MENTION, never a live import — delete the pin "
                f"or break the import")
    return errors


CROSS_BOUNDARY_WAIVERS: dict[tuple[str, str], str] = {}


def check_cross_boundary_paths():
    """A consumer script may not name a file the projection leaves behind.

    The teeth of the split. `check_shipped_closure` proves the boundary is
    total; this proves the consumer half can stand on its own — a script that
    ships while the file it opens does not is a skill that is green here and
    broken in a fresh clone, which is precisely the class `check_assets_tracked`
    exists for.

    It reads the AST rather than the text. The first version matched
    double-quoted literals with a regex, and this repository's lint config
    selects no quote rule — `inspect_layout.py` alone carries five hundred
    single-quoted strings — so half the tree went unscanned, along with triple
    quotes and implicit concatenation. `ast.Constant` sees all of them.

    It also reconstructs `/`-joined constant chains (`ROOT / "conformance" /
    "results" / "index.json"`), counts a dev DIRECTORY as fatal — `(ROOT /
    "tests")` resolves to nothing after the projection — and reports a dynamic
    `import_module("x")`, which is an import the reachability that decides the
    boundary cannot see.

    The limits, stated rather than implied: only literals and `/`-joined
    literal chains are seen, so a path assembled through a variable, `+`, an
    f-string, `.format()` or `os.path.join` is invisible. The neighbouring
    `check_gate_declarations` reads `ast.JoinedStr` for the same reason, so the
    f-string half is a known gap rather than an unconsidered one.
    """
    import shipped
    try:
        shipped.manifest(ROOT)
    except (OSError, ValueError) as exc:                            # noqa: BLE001
        return [f"could not read {shipped.MANIFEST}: {exc}"]
    p = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT,
                       capture_output=True, text=True)
    if p.returncode != 0:
        return [f"git ls-files failed ({p.stderr.strip()[:80]}) — the "
                f"cross-boundary scan did not run, and a scan that did not run "
                f"is not a scan that passed"]
    tracked = {f for f in p.stdout.split("\0") if f}
    consumer = shipped.consumer_scripts(ROOT)
    # A directory is reported only when NOTHING under it ships. `evals/` holds
    # `thresholds.json` and `gates.json`, both consumer, so a script naming
    # `ROOT / "evals" / "thresholds.json"` is naming something that is there.
    wholly_dev = set()
    for d in {a for f in tracked for a in _ancestors(f)}:
        under = [f for f in tracked if f.startswith(d + "/")]
        if under and all(shipped.side_of(f, ROOT, consumer) == "dev" for f in under):
            wholly_dev.add(d)
    scripts = {q.stem: q for q in
               list(ROOT.glob("scripts/*/*.py")) + list(ROOT.glob("scripts/*.py"))}
    errors = []
    for stem in sorted(consumer):
        path = scripts.get(stem)
        if path is None:
            continue
        name = rel(path)
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError) as exc:                       # noqa: BLE001
            errors.append(f"{name} could not be parsed for the boundary scan: {exc}")
            continue
        found: set[str] = set()
        # Constants used AS A PATH — the right side of a `/` join, or anything
        # carrying a separator. A bare word is not: `trace_schema.py` declares
        # the enum value "conformance", which is not the directory of that name.
        as_path: set[str] = set()
        # A path named ONLY as `state_dir.store(in_repo=...)`'s fallback is not
        # a dependency — it is the thing that is ALLOWED to be absent, and the
        # resolver falls to the operator state directory when it is. Excluded
        # by construction rather than by a waiver, because a waiver would have
        # to be re-written for every store.
        fallback: set[str] = set()
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            for kw in node.keywords:
                if kw.arg != "in_repo" or not isinstance(kw.value, ast.Tuple):
                    continue
                parts = [e.value for e in kw.value.elts
                         if isinstance(e, ast.Constant) and isinstance(e.value, str)]
                for i in range(len(parts)):
                    fallback.add("/".join(parts[:i + 1]))
                fallback.update(parts)
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                found.add(node.value)
                if "/" in node.value:
                    as_path.add(node.value)
            elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
                if (isinstance(node.right, ast.Constant)
                        and isinstance(node.right.value, str)):
                    as_path.add(node.right.value)
                chain = _slash_chain(node)
                if chain:
                    found.add(chain)
                    as_path.add(chain)
            elif (isinstance(node, ast.Call)
                  and isinstance(node.func, ast.Attribute)
                  and node.func.attr == "import_module"
                  and node.args
                  and isinstance(node.args[0], ast.Constant)
                  and isinstance(node.args[0].value, str)):
                mod = node.args[0].value
                for drawer in ("lib", "ops", "check", "build", "render"):
                    cand = f"scripts/{drawer}/{mod}.py"
                    if (cand in tracked
                            and shipped.side_of(cand, ROOT, consumer) == "dev"):
                        errors.append(
                            f"{name} ships to the consumer and imports `{mod}` "
                            f"dynamically; `{cand}` does not ship. A dynamic "
                            f"import is invisible to the reachability that "
                            f"decides the boundary — import it plainly, or move "
                            f"the module")
        hits = (found & tracked) | (as_path & wholly_dev)
        for cand in sorted(hits - fallback):
            if shipped.side_of(cand, ROOT, consumer) != "dev":
                continue
            if (name, cand) in CROSS_BOUNDARY_WAIVERS:
                continue
            kind = "file" if cand in tracked else "directory"
            errors.append(
                f"{name} ships to the consumer and names the {kind} `{cand}`, "
                f"which does not. After the split it is not there — move it to "
                f"the consumer side, resolve it through `state_dir`, or waive "
                f"it in CROSS_BOUNDARY_WAIVERS with the reason it is safe")
    return errors


def _ancestors(relpath: str) -> set[str]:
    """-> every directory prefix of a tracked path, without a trailing slash."""
    parts = relpath.split("/")[:-1]
    return {"/".join(parts[:i + 1]) for i in range(len(parts))}


def _slash_chain(node) -> str | None:
    """-> `"a/b/c"` for `<anything> / "a" / "b" / "c"`, else None.

    Two segments were all the first version reconstructed, so a three-segment
    join walked past it.
    """
    parts: list[str] = []
    cur = node
    while (isinstance(cur, ast.BinOp) and isinstance(cur.op, ast.Div)
           and isinstance(cur.right, ast.Constant)
           and isinstance(cur.right.value, str)):
        parts.append(cur.right.value)
        cur = cur.left
    if isinstance(cur, ast.Constant) and isinstance(cur.value, str):
        parts.append(cur.value)
    return "/".join(reversed(parts)) if len(parts) >= 2 else None


def check_local_paths():
    """No tracked file outside `tests/` and `releases/evidence/` names an
    operator's home directory.

    Those two are excluded by construction: a synthetic tree's fixtures name
    paths that exist only in `tmp_path`, this guard's own tests must plant the
    string it looks for, and evidence files are frozen history.

    Two reasons, and the second is why this is a gate rather than a note. It is
    a privacy leak: `conformance/CONFORMANCE.md` carried the owner's username
    on its fourth line, written there by `report --record`, and the board is a
    tracked file. And it is a correctness leak: a path that resolves on one
    machine is a dangling reference on every other, so a recorded run id could
    not be reopened by anyone but its author.

    `/Users/you` and its friends are excluded by the pattern rather than by a
    waiver: an install instruction is the prose that most naturally names a home
    directory, and a placeholder in an example is not a person. The tilde-user
    form is IN scope — `~someone/` leaks the username exactly as the absolute form
    does, and it is what a careless author writes after reading the advice
    below.
    """
    p = subprocess.run(["git", "ls-files"], cwd=ROOT,
                       capture_output=True, text=True)
    if p.returncode != 0:
        # A git failure inside a checkout is a finding, not a skip — the same
        # policy check_secrets holds for the identical condition.
        return [f"git ls-files failed ({p.stderr.strip()[:80]}) — the local-path "
                f"scan did not run, and a scan that did not run is not a scan "
                f"that passed"]
    errors = []
    for name in p.stdout.splitlines():
        # tests/ by construction: a synthetic tree's fixtures name paths that
        # exist only in tmp_path, and this guard's OWN tests must plant the
        # string it looks for. releases/evidence/ is frozen history.
        # SCRIPT_PATH_FROZEN excludes tests/ for the identical reason, and
        # missing it here shipped a guard that failed on its own tests the
        # moment they were tracked — the scan reads git, so it saw nothing
        # while they were still untracked.
        if not name or name.startswith(("tests/", "releases/evidence/")):
            continue
        try:
            text = (ROOT / name).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue  # binary assets carry no greppable path
        for lineno, line in enumerate(text.splitlines(), 1):
            for hit in LOCAL_PATH_RE.findall(line):
                if (name, hit) in LOCAL_PATH_WAIVERS:
                    continue
                errors.append(
                    f"{name}:{lineno} names {hit}, a path into someone's home "
                    f"directory. Write it as `~/...` with nothing after the "
                    f"tilde — it stays meaningful, it resolves on the machine "
                    f"that can resolve it at all, and it does not ship a "
                    f"username. A placeholder ({', '.join(LOCAL_PATH_PLACEHOLDERS[:4])}"
                    f", …) is allowed; anything else needs LOCAL_PATH_WAIVERS")
    return errors


def _identifiers_in_code() -> set[str]:
    """-> the identifiers this package's own code uses.

    The repository as its own dictionary. Walks the Python under `scripts/` for
    names, attributes, arguments, function and class names, dict KEYS and string
    subscripts — keys and subscripts rather than every string constant, because
    harvesting prose let this guard's own docstring enter the dictionary and pull
    its teeth. The JavaScript under `assets/` and the JSON under `evals/` and
    `tokens/` are read by regex, because a report key is as real as a variable.

    It globs the filesystem rather than asking git, and it returns names of any
    shape, not only snake_case — both are fine for a dictionary, whose only job
    is to answer "is this a real thing".
    """
    found: set[str] = set()
    word = re.compile(r"\b([a-z][a-z0-9]*(?:_[a-z0-9]+)+)\b")
    for path in sorted(ROOT.glob("scripts/**/*.py")) + \
            sorted(ROOT.glob("assets/**/*.js")) + \
            sorted(ROOT.glob("evals/*.json")) + sorted(ROOT.glob("tokens/*.json")):
        try:
            src = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if path.suffix == ".py":
            try:
                tree = ast.parse(src)
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    found.add(node.id)
                elif isinstance(node, ast.Attribute):
                    found.add(node.attr)
                elif isinstance(node, ast.keyword) and node.arg:
                    found.add(node.arg)
                elif isinstance(node, ast.arg):
                    found.add(node.arg)
                elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    found.add(node.name)
                elif isinstance(node, ast.Dict):
                    # KEYS, never prose: harvesting every string constant let
                    # this guard's own docstring — which cites `figure_axis` as
                    # the thing it exists to catch — enter the dictionary and
                    # pull the guard's teeth.
                    found.update(k.value for k in node.keys
                                 if isinstance(k, ast.Constant)
                                 and isinstance(k.value, str))
                elif (isinstance(node, ast.Subscript)
                      and isinstance(node.slice, ast.Constant)
                      and isinstance(node.slice.value, str)):
                    found.add(node.slice.value)
        elif path.suffix == ".json":
            # KEYS ONLY. `evals/rule-coverage.json` stores verbatim quotes of
            # reference prose, so reading the whole file let a wrong verdict
            # name written into a reference sentence whitelist itself against
            # the guard policing that same sentence. Nothing is masked today —
            # one snake_case token lives in those quotes — but the circularity
            # is the defect, not its current reach.
            try:
                doc = json.loads(src)
            except json.JSONDecodeError:
                continue
            stack = [doc]
            while stack:
                node = stack.pop()
                if isinstance(node, dict):
                    found.update(k for k in node if isinstance(k, str))
                    stack.extend(node.values())
                elif isinstance(node, list):
                    stack.extend(node)
        else:
            found.update(word.findall(src))
    return found


def check_verdict_names():
    """Prose may not name a layout verdict that does not exist.

    Narrow on purpose, and narrowed AGAIN after an adversarial review found it
    would fail 23 real identifiers. The families include ordinary English —
    `page`, `content`, `role`, `title`, `figure`, `visual` — so "first word a
    verdict owns" caught `visual_share_median` and `page_share`, which are real
    output keys of `eval_corpus.py` and `check_design.py`. The message told the
    author to rename correct code, which is the wrong-gate-edits-prose failure
    this repository already has on record.

    So the repository is its own dictionary: an identifier that EXISTS in the
    tracked code is a real thing, whatever it is named. What remains is a name
    in the verdict families that exists nowhere — which is what an abbreviation
    (`figure_axis`) or a half-remembered name (`figure_axes`) actually is.
    """
    import gate_registry
    try:
        reg = gate_registry.load(ROOT)
    except (OSError, ValueError) as exc:                            # noqa: BLE001
        return [f"could not read the gate declarations: {exc}"]

    names = set(reg)
    layout = {n for n, row in reg.items() if row["checker"] == "layout"}
    if not layout:
        # NOT a pass. `[]` means "checked and found nothing" in this file, and
        # a register with no layout verdict cannot be true — it means this
        # guard had nothing to hold prose to.
        return [f"{gate_registry.REGISTER} declares no layout verdict, so this "
                f"guard had nothing to compare prose against"]
    families = {n.split("_", 1)[0] for n in layout}
    real = _identifiers_in_code()
    errors = []
    for path in md_files():
        name = rel(path)
        if any(name == f or name.startswith(f) for f in VERDICT_NAME_FROZEN):
            continue
        for lineno, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), 1):
            for ident in VERDICT_NAME_RE.findall(line):
                if ident in names or ident.split("_", 1)[0] not in families:
                    continue
                if ident in real:
                    continue        # a real identifier, whatever it is named
                if (name, ident) in VERDICT_NAME_WAIVERS:
                    continue
                closer = sorted(n for n in layout if n.startswith(ident + "_"))
                near = ", ".join(closer or sorted(
                    n for n in layout
                    if n.startswith(ident.split("_", 1)[0] + "_")))
                errors.append(
                    f"{name}:{lineno} names `{ident}`, which is no verdict. "
                    f"The verdicts in that family are {near}. Name one of them, "
                    f"say plainly that this is not a verdict, or add it to "
                    f"VERDICT_NAME_WAIVERS with a reason — a reader who looks "
                    f"it up finds nothing")
    return errors


def check_prose_gating_claims():
    r"""The same claim as `gating claims`, for the metrics check_prose.py gates.

    It had no guard at all, and both of its claim sites were wrong when one was
    written: the table omitted M4zh entirely, so the one gate that fails a
    CHINESE deliverable was absent from the document a reader learns the metrics
    from — in a package whose decks are largely Chinese.

    Two claim shapes, because the sites make two different claims. A table of
    metrics enumerates, so its `**gates**` marks must equal the gate set. A
    sentence arguing from an example names a subset, and what it may not do is
    call something a gate that is not one.

    The truth comes from `evals/gates.json` by NAME rather than from the id
    prefix. `gating.metric_ids("M")` cannot see `M4zh_banned_hits`: its pattern
    is `M\d+_`, and `M4zh_` does not match it. A guard built on the prefix
    reader would have confidently reported the table correct.
    """
    import gate_registry
    try:
        reg = gate_registry.load(ROOT)
    except (OSError, ValueError) as exc:                            # noqa: BLE001
        return [f"could not read the gate declarations: {exc}"]

    truth = {name.split("_", 1)[0] for name, row in reg.items()
             if name.startswith("M") and row["severity"] == "gate"}
    errors = []
    for site, (pattern, kind) in sorted(PROSE_GATE_SITES.items()):
        path = ROOT / site.split("::", 1)[0]
        if not path.exists():
            errors.append(f"{site} is a declared gating-claim site and does not exist")
            continue
        text = path.read_text(encoding="utf-8")
        if kind == "rows":
            found = re.findall(pattern, text, re.M)
            if not found:
                errors.append(f"{site}: the metric table is gone or no longer "
                              f"matches its pattern; re-point the entry")
                continue
            claimed = {mid for mid, target in found if "**gates**" in target}
        else:
            hit = re.search(pattern, text, re.S)
            if not hit:
                errors.append(
                    f"{site}: the declared gating claim no longer matches its "
                    f"pattern. Re-point it at the sentence, or delete the "
                    f"sentence and name check_prose.py as the authority — do "
                    f"not drop the entry")
                continue
            claimed = set(re.findall(r"M\d+\w*", hit.group(1)))
            wrong = claimed - truth
            if wrong:
                errors.append(
                    f"{site}: calls {', '.join(sorted(wrong))} a metric that "
                    f"gates; check_prose.py gates on "
                    f"{', '.join(sorted(truth))}")
            continue
        if claimed != truth:
            missing = ", ".join(sorted(truth - claimed)) or "(none)"
            extra = ", ".join(sorted(claimed - truth)) or "(none)"
            errors.append(
                f"{site}: names {', '.join(sorted(claimed)) or '(none)'} as the "
                f"prose metrics that gate; check_prose.py gates on "
                f"{', '.join(sorted(truth))} (missing: {missing}; "
                f"claimed and does not gate: {extra})")
    return errors


def check_storyline_vocabulary():
    """The storyline names in code and the roster in the rules are one list.

    Written after the closing of GAP-013 turned up something larger than the gap:
    `STORYLINES` had been a closed tuple since the two-axis split shipped, and
    **not one of its six names appeared anywhere in `references/`**. An author
    choosing a storyline had nothing to read; a name with no prose behind it
    means whatever the last person to type it assumed, which is how a closed
    vocabulary becomes a private convention.

    The roster is the prose side and the tuple is the code side — the parity
    pattern this repository already uses for the ban list and the metric ids,
    with code as one side so the guard cannot drift with the document.

    It deliberately does NOT require a full narrative skeleton per name: five of
    the seven have only a one-line shape, that is recorded in the roster itself,
    and a guard demanding templates would have blocked the release that made the
    vocabulary readable at all.
    """
    registry = ROOT / "scripts" / "lib" / "deliverable_registry.py"
    templates = ROOT / "references" / "storyline-templates.md"
    for path in (registry, templates):
        if not path.exists():
            return [f"{path.relative_to(ROOT)} is missing"]

    m = re.search(r"^STORYLINES = \(([^)]*)\)", registry.read_text(encoding="utf-8"),
                  re.M | re.S)
    if not m:
        return ["deliverable_registry.py declares no STORYLINES tuple"]
    code = set(re.findall(r'"([a-z-]+)"', m.group(1)))
    if not code:
        return ["the STORYLINES tuple parsed empty — the guard would pass "
                "vacuously, which is the failure mode it exists to prevent"]

    text = templates.read_text(encoding="utf-8")
    start = text.find("## The storyline vocabulary")
    if start < 0:
        return ["references/storyline-templates.md carries no storyline roster; "
                "the vocabulary would again be readable only in code"]
    end = text.find("\n## ", start + 5)
    roster = set(re.findall(r"^\| `([a-z-]+)` \|",
                            text[start:end if end > 0 else len(text)], re.M))

    errors = []
    for name in sorted(code - roster):
        errors.append(f"storyline {name!r} is in STORYLINES and not in the "
                      f"roster — an author has no way to know it exists")
    for name in sorted(roster - code):
        errors.append(f"storyline {name!r} is in the roster and not in "
                      f"STORYLINES — trace.py would refuse a name the rules offer")
    return errors


def check_genre_vocabulary():
    """One set of genre names, and every consumer keyed on it.

    Five scripts carried five different lists — check_prose 3, new_deck 4,
    inspect_layout 5, review_scores 5, export_pdf "check_prose's 3 plus a
    hand-appended consulting". The consequence was not cosmetic: a consulting
    deliverable could be scaffolded, layout-graded and review-scored, while
    `check_prose.py --genre consulting` refused the value, so its prose had to
    be graded under a genre it is not. One of the five had already drifted once
    before (0.1.379 records export_pdf; 0.1.378's case was run_conformance,
    which is not one of these five).

    Every genre-keyed table in the package is held to the registry's names, and
    the list of them lives here rather than in a count: no script may re-declare
    the vocabulary or bind it to something unverifiable; `inspect_layout`'s
    visual-share targets and `evals/thresholds.json`'s bars must cover it
    exactly (a genre missing from the first makes inspect_layout print NOT
    MEASURED and exit 1; missing from the second means a document scored against
    nothing); `check_prose`'s DASH_BANNED must decide every genre, because one
    it does not decide has M9 skipped and explained as "(exempt for internal
    documents)", which is false for it; and `new_deck`'s SCAFFOLDED must be a
    subset, never a superset.

    Read with `ast`, so no script is imported.
    """
    absent = object()
    try:
        source = {name: ast.parse((ROOT / name).read_text(encoding="utf-8"))
                  for name in ("scripts/lib/deliverable_registry.py",
                               "scripts/check/check_prose.py",
                               "scripts/check/inspect_layout.py",
                               "scripts/ops/new_deck.py",
                               "scripts/ops/review_scores.py",
                               "scripts/ops/export_pdf.py",
                               "scripts/ops/eval_corpus.py")}
    except (OSError, SyntaxError) as exc:                           # noqa: BLE001
        return [f"could not read the genre vocabularies: {exc}"]

    def literal(tree, name):
        """-> the value | `absent` (no such name) | None (present, not a literal).

        Three states, because two of them used to be one. `GENRES = _G` is not
        a literal, so it returned None — the same answer as "this file does not
        declare GENRES", which the caller read as compliance. That is the exact
        indirection the guard exists to catch, wearing the shape the guard
        treated as proof. And every binding is scanned rather than the first:
        a literal later in the file is the value that wins at runtime.
        """
        found = absent
        for node in ast.walk(tree):
            if (isinstance(node, ast.Assign) and node.targets
                    and isinstance(node.targets[0], ast.Name)
                    and node.targets[0].id == name):
                try:
                    return ast.literal_eval(node.value)
                except (ValueError, TypeError, SyntaxError, MemoryError,
                        RecursionError):
                    # Not pinned to one interpreter's error taxonomy: a guard
                    # whose blind spot is an exception class stops going red
                    # quietly.
                    found = None
        return found

    authority = literal(source["scripts/lib/deliverable_registry.py"], "GENRES")
    if authority is absent or authority is None or not authority:
        return ["scripts/lib/deliverable_registry.py no longer declares GENRES; "
                "the genre vocabulary has no authority"]
    errors = []
    known = set(authority)

    for name, tree in source.items():
        if name.endswith("deliverable_registry.py"):
            continue
        own = literal(tree, "GENRES")
        if own is None:
            # Bound to a NAME rather than a literal. That is legitimate for
            # exactly two shapes: the registry's own name imported under an
            # alias, and a local list this guard checks separately. Anything
            # else is a vocabulary nobody can verify, which is the indirection
            # the guard exists to catch — `GENRES = _G` reads identically to
            # "this file declares nothing".
            allowed = {a.asname or a.name for node in ast.walk(tree)
                       if isinstance(node, ast.ImportFrom)
                       and node.module == "deliverable_registry"
                       for a in node.names} | {"SCAFFOLDED"}
            bound = {node.value.id for node in ast.walk(tree)
                     if isinstance(node, ast.Assign) and node.targets
                     and isinstance(node.targets[0], ast.Name)
                     and node.targets[0].id == "GENRES"
                     and isinstance(node.value, ast.Name)}
            if not bound or not bound <= allowed:
                errors.append(
                    f"{name} binds GENRES to something this guard cannot "
                    f"verify ({', '.join(sorted(bound)) or 'an expression'}); "
                    f"the vocabulary it actually uses is unverifiable. Import "
                    f"the registry's name, or bind a list this guard checks.")
        elif own is not absent:
            errors.append(
                f"{name} declares its own GENRES {tuple(own)!r}; import it from "
                f"deliverable_registry instead — five copies of this list is "
                f"what the guard exists for")

    targets = literal(source["scripts/check/inspect_layout.py"],
                      "VISUAL_SHARE_TARGET")
    if targets is None:
        errors.append("inspect_layout.py no longer declares VISUAL_SHARE_TARGET")
    else:
        for genre in sorted(known - set(targets)):
            errors.append(
                f"inspect_layout.py has no visual-share target for {genre!r}; a "
                f"document declaring it prints NOT MEASURED and exits 1, so the "
                f"whole run stops on a genre nobody gave a target")
        for genre in sorted(set(targets) - known):
            errors.append(
                f"inspect_layout.py targets {genre!r}, which is not a genre "
                f"deliverable_registry knows")

    banned = literal(source["scripts/check/check_prose.py"], "DASH_BANNED")
    if banned in (None, absent):
        errors.append("check_prose.py no longer declares DASH_BANNED as a "
                      "literal; the dash ban's genre list is unverifiable")
    else:
        for genre in sorted(set(banned) - known):
            errors.append(f"check_prose.py bans the dash for {genre!r}, which is "
                          f"not a genre deliverable_registry knows")
        # A genre in neither list gets M9 skipped and PRINTED as "(exempt for
        # internal documents)" — a sentence that is false for it. Silence with
        # a wrong label is worse than silence.
        undecided = sorted(known - set(banned) - {"internal"})
        if undecided:
            errors.append(
                f"check_prose.py has no dash decision for "
                f"{', '.join(undecided)}; M9 is skipped for them and explained "
                f"as '(exempt for internal documents)', which is not true of "
                f"them. Add each to DASH_BANNED or beside `internal` with a "
                f"reason.")

    try:
        table = json.loads((ROOT / "evals" / "thresholds.json").read_text(
            encoding="utf-8"))
    except (OSError, ValueError) as exc:                            # noqa: BLE001
        errors.append(f"evals/thresholds.json does not parse: {exc}")
    else:
        for metric, spec in table["metrics"].items():
            for genre in sorted(known - set(spec["genres"])):
                errors.append(
                    f"evals/thresholds.json metric {metric!r} has no entry for "
                    f"genre {genre!r}; eval_corpus reports 'no bar' and the "
                    f"document is scored against nothing. A bar deliberately "
                    f"not set is `value: null` with a `why`.")

    scaffolded = literal(source["scripts/ops/new_deck.py"], "SCAFFOLDED")
    if scaffolded in (None, absent):
        errors.append("new_deck.py no longer declares SCAFFOLDED")
    else:
        for genre in sorted(set(scaffolded) - known):
            errors.append(
                f"new_deck.py scaffolds {genre!r}, which is not a genre "
                f"deliverable_registry knows")
    return errors


def _tracked_stems(reldir, suffix=".svg"):
    """-> {stem} for files git TRACKS under `reldir`, or None with no git.

    None is not an empty set: a tarball checkout has no index to ask, and a
    caller that conflated the two would report every shipped file missing.
    """
    if not (ROOT / ".git").exists():
        return None
    p = subprocess.run(["git", "ls-files", "-z", "--", f"{reldir}/*{suffix}"],
                       cwd=ROOT, capture_output=True, text=True)
    if p.returncode != 0:
        return None
    return {pathlib.PurePosixPath(f).stem for f in p.stdout.split("\0") if f}


def check_assets_tracked():
    """Every asset this package ships is in version control.

    `.gitignore` carries a blanket `*.svg`/`*.png`/`*.woff2` rule to keep a
    deliverable's renders out, and an exception block below it re-admits the
    design language's own assets. That block's own comment says "this is the
    fourth directory to need saying so" — and `assets/shapes/` became the fifth
    without being added, so all 206 units of the shape library were never
    committed. CI found it on a fresh clone; nothing local could have.

    Nothing local could have because every asset guard reads the WORKING TREE.
    `check_shape_library` globs `assets/shapes/*.svg`, finds 206 files, and
    passes — the files are right there. A guard that reads the filesystem is
    structurally blind to the difference between "shipped" and "present on the
    author's machine", and that is the whole defect class.

    So this one asks git instead. A dotfile is exempt: `.DS_Store` is the
    platform's litter, not the package's material.

    **It fires on the author's machine, and that is where it has to fire.** In a
    clone there are no ignored files to list, so this guard is quiet there by
    construction — it is a pre-commit hold, not a post-merge one. The clone-side
    half of the same question is `check_shape_library`, which compares the
    manifest against what git TRACKS and so fails in CI when the library stops
    shipping. Neither is the other's substitute.
    """
    if not (ROOT / ".git").exists():
        return []                    # a tarball checkout has nothing to assert
    p = subprocess.run(["git", "ls-files", "-o", "-i", "-z",
                        "--exclude-standard", "assets/"],
                       cwd=ROOT, capture_output=True, text=True)
    if p.returncode != 0:
        # A repository that has git and cannot be asked is not a repository
        # with nothing to report. Returning [] here would rebuild the exact
        # blind spot this guard exists to close, one level down.
        return [f"could not ask git which assets are ignored "
                f"(git ls-files exited {p.returncode}) — this guard did not "
                f"run, which is not the same as finding nothing"]
    errors = []
    for path in sorted(f for f in p.stdout.split("\0") if f):
        if pathlib.Path(path).name.startswith("."):
            continue
        errors.append(
            f"{path} is on disk and .gitignore excludes it — an asset the "
            f"package ships may not be one `git add -f` away from existing")
    # The other direction: a manifest row describing a file git does not
    # have. 0.1.504's shape manifest described 206 preview files nobody had;
    # the 2026-08-20 audit found two SOURCES.md files describing 37 assets
    # that were on disk and untracked — which the ignore-list check above
    # cannot see, because untracked-and-not-ignored is neither state it asks
    # about. A manifest is the package's word about what it ships.
    tracked = subprocess.run(["git", "ls-files", "-z", "assets/"], cwd=ROOT,
                             capture_output=True, text=True)
    if tracked.returncode != 0:
        return errors + ["could not list tracked assets (git ls-files failed) — "
                         "the manifest half of this guard did not run"]
    have = {f for f in tracked.stdout.split("\0") if f}
    row = re.compile(r"^\|\s*`?([\w./-]+\.(?:svg|png|woff2|ttf|otf|json))`?\s*\|")
    for manifest in sorted((ROOT / "assets").rglob("SOURCES.md")):
        rel_dir = manifest.parent.relative_to(ROOT)
        for n, line in enumerate(manifest.read_text(encoding="utf-8").splitlines(), 1):
            m = row.match(line)
            if not m:
                continue
            name = m.group(1)
            candidate = str(rel_dir / name)
            if candidate not in have:
                errors.append(
                    f"{manifest.relative_to(ROOT)}:{n} describes {name}, which "
                    f"git does not track — a manifest row for a file nobody has "
                    f"(0.1.504's shape)")
    return errors



def check_trace_field_readers():
    """No field the trace schema declares is write-only.

    A field nobody reads is a fact nobody uses, and it is worse than an absent
    one: it looks like coverage. `entry_path` was the case that made this
    guard — the owner ruled that entry path B is held to the current
    constitution, `trace.py` wrote the field faithfully, and `ledger.py` read
    eleven fields and never that one. The rule had no consumer, so it could
    not be true or false about anything.

    A reader is any mention outside the schema and the writer. That is a loose
    definition on purpose: a tighter one (an actual subscript) would miss
    `rec.get(k)` in a loop, and this guard's job is to catch a field with NO
    downstream at all, not to grade how it is used.
    """
    fields = getattr(trace_schema, "FIELDS", None)
    if not fields:
        return ["trace_schema declares no FIELDS — the guard would pass vacuously"]
    written_by = {"scripts/lib/trace_schema.py", "scripts/ops/trace.py"}
    corpus = []
    for path in sorted((ROOT / "scripts").rglob("*.py")):
        if rel(path) in written_by:
            continue
        corpus.append(path.read_text(encoding="utf-8"))
    blob = "\n".join(corpus)
    unread = [f for f in fields if f not in blob]
    return [f"trace field {f!r} is declared and nothing outside trace.py reads "
            f"it — a field with no consumer is not coverage, it is a fact "
            f"nobody uses" for f in sorted(unread)]


def check_frameworks():
    """The framework dictionary resolves, and every entry can be used.

    assets/frameworks.json is the generation-side complement to the shape
    library (analysis-rules.md AR-4): each framework names the analytical
    question it answers and binds the shape ids that draw it. Two failure
    shapes, both shipped classes in this repo: a bound id the library does
    not define (the dangling-reference class D19 gates in documents), and an
    entry missing the fields that make it usable — a framework without its
    misuse line is exactly the "rule that hands out numbers without the
    limit" convention 6 bans.
    """
    import json as _json
    fw_path = ROOT / "assets" / "frameworks.json"
    tags_path = ROOT / "assets" / "shapes" / "tags.json"
    try:
        fw = _json.loads(fw_path.read_text(encoding="utf-8"))
        tags = _json.loads(tags_path.read_text(encoding="utf-8"))["shapes"]
    except (OSError, _json.JSONDecodeError, KeyError) as exc:
        return [f"frameworks: could not read the two dictionaries: {exc}"]
    errors = []
    moves = {"compare", "decompose", "position", "correlate", "bridge"}
    for name, entry in (fw.get("frameworks") or {}).items():
        for field in ("question", "move", "slots", "misuse"):
            if not entry.get(field):
                errors.append(f"frameworks.{name}: missing {field!r}")
        if entry.get("move") not in moves:
            errors.append(f"frameworks.{name}: move {entry.get('move')!r} is "
                          f"not one of the five analytical moves "
                          f"(analysis-rules.md AR-1)")
        for sid in entry.get("shapes") or []:
            if sid not in tags:
                errors.append(f"frameworks.{name}: shape {sid!r} is not in "
                              f"the library — a binding the sprite cannot "
                              f"resolve")
        if not entry.get("shapes") and entry.get("drawn") != "native":
            errors.append(f"frameworks.{name}: binds no shapes and does not "
                          f"declare drawn:'native' — an entry an author can "
                          f"neither embed nor draw")
    if not (fw.get("frameworks") or {}):
        errors.append("frameworks.json declares no frameworks at all")
    return errors


CHECKS = (
    ("assets tracked", check_assets_tracked),
    ("genre vocabulary", check_genre_vocabulary),
    ("storyline vocabulary", check_storyline_vocabulary),
    ("two-axis vocabulary", check_two_axis_vocabulary),
    ("brand registry", check_brand_registry),
    ("shape library", check_shape_library),
    ("frameworks", check_frameworks),
    ("scoring sheet parity", check_scoring_sheet_parity),
    ("metric id ranges", check_metric_id_ranges),
    ("gating claims", check_gating_claims),
    ("prose gating claims", check_prose_gating_claims),
    ("verdict names", check_verdict_names),
    ("local paths", check_local_paths),
    ("shipped closure", check_shipped_closure),
    ("cross-boundary paths", check_cross_boundary_paths),
    ("version stamps", check_versions),
    ("output default", check_output_default),
    ("version citations", check_version_citations),
    ("english-only red line", check_english_only),
    ("markdown link targets", check_links),
    ("section citations", check_section_citations),
    ("principle trace", check_principle_trace),
    ("red line parity", check_red_line_parity),
    ("rule ids", check_rule_ids),
    ("trace schema", check_trace_schema),
    ("trace field readers", check_trace_field_readers),
    ("stale promises", check_stale_promises),
    ("platform manifest", check_platform_manifest),
    ("retired values", check_retired_values),
    ("token palette parity", check_palette_parity),
    ("token references", check_token_references),
    ("region coverage", check_region_coverage),
    ("probe vocabulary", check_probe_vocabulary),
    ("role weights", check_role_weights),
    ("ground ceiling", check_ground_ceiling),
    ("gate declarations", check_gate_declarations),
    ("media-only rules", check_media_only_rules),
    ("layout parity", check_layout_parity),
    ("ban-list parity", check_ban_list_parity),
    ("zh ban-list parity", check_zh_ban_list_parity),
    ("review scores", check_review_scores),
    ("source-marker parity", check_source_marker_parity),
    ("brand lock", check_brand_lock),
    ("no shadow math", check_no_shadow_math),
    ("secret patterns parity", check_secret_patterns_parity),
    ("no shadow markup", check_no_shadow_markup),
    ("rubric unbuilt claims", check_rubric_unbuilt_claims),
    ("prompt parity", check_prompt_parity),
    ("entry restatement ceiling", check_entry_restatement_ceiling),
    ("ledgers", check_ledgers),
    ("commit convention", check_commit_convention),
    ("secrets", check_secrets),
    ("script paths", check_script_paths),
    ("bootstrap", check_bootstrap),
    ("scaffold slots", check_scaffold_slots),
)


def main():
    failed = 0
    for label, check in CHECKS:
        # A guard that raises used to take every guard after it with it, and the
        # output said nothing: five ok lines then a traceback, with no way to
        # tell "three checks did not run" from "the run ended". A crash is that
        # check's failure, not the suite's abort.
        try:
            errors = check()
        except Exception as exc:                            # noqa: BLE001
            errors = [f"the guard itself raised {exc.__class__.__name__}: {exc}",
                      traceback.format_exc().strip().splitlines()[-2].strip()]
        if errors is None:
            # A guard that returns nothing at all is not a guard that found
            # nothing, and `if errors:` could not tell them apart.
            errors = ["the guard returned no verdict at all"]
        if errors:
            failed += 1
            print(f"FAIL  {label}")
            for error in errors:
                print(f"        {error}")
        else:
            print(f"ok    {label}")
    if failed:
        print(f"\n{failed} of {len(CHECKS)} checks failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
