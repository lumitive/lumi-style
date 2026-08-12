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

import color_math  # noqa: E402 — after the bootstrap, deliberately
from css_tokens import css_block, css_vars  # noqa: E402, F401 — css_block is API for tests/tools

ROOT = next(p for p in pathlib.Path(__file__).resolve().parents
            if p.name == "scripts").parent

# CJK is permitted only where it is rule *data* for Chinese-language output.
# Anywhere else it breaks the English-only repository red line.
CJK_ALLOWED = {
    "AGENTS.md",
    "SKILL.md",
    "prompts/lumi-style-core.md",
    "references/writing-rules.md",
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
    for name, pattern in (
        ("tokens/lumi-theme.css", r"LUMI visual theme\s*·\s*v(\d+\.\d+\.\d+)"),
        ("tokens/design-tokens.json", r"LUMI design tokens v(\d+\.\d+\.\d+)"),
        ("tokens/lumi-layouts.css", r"LUMI page layouts\s*·\s*v(\d+\.\d+\.\d+)"),
    ):
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
# Every entry here is a CENSUS selector — one of INK / TSEL / DSEL / CENTER,
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
    * **census** — `INK`, `TSEL`, `DSEL`, `CENTER`, and `check_prose.py`'s M10
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
    """
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
ENTRY_STAMP = {
    "SKILL.md": r'^\s*version:\s*"{v}"',
    "AGENTS.md": r"\*\*lumi-style {v}\.?\*\*",
    "prompts/lumi-style-core.md": r"\*\*{v}\*\* snapshot",
    # The scoreboard carries a first-class skill stamp on line 1. Scoping the
    # third-party exemption to its table rows re-enabled the *citation* check
    # there, which by construction cannot see staleness — a stale stamp names a
    # real release and stays legal forever. This is the check that sees it.
    "conformance/CONFORMANCE.md": r"skill {v}",
}

# A version string may name something other than a release only with a reason.
# Same contract as check_prose.py's NOT_MECHANIZED: a documented exception is a
# reviewable state; an undocumented one is a mistake nobody noticed.
# Files that legitimately carry version numbers belonging to other projects.
THIRD_PARTY_VERSION_LINES = {"conformance/CONFORMANCE.md": re.compile(r"^\|")}

VERSION_CITATION_WAIVERS = {
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
# references/design-rules.md §7 and the other three restate it; scripts/ops/output_dir.py
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
}

# High-signal only: on a prose-heavy repository a chatty secret scanner is a
# scanner people stop reading. Each pattern is written so it cannot match its
# own source here.
SECRET_PATTERNS = (
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("private key block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("GitHub token", re.compile(r"\bghp_[A-Za-z0-9]{36}\b")),
    ("GitHub fine-grained token", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{22,}\b")),
    ("API secret assignment", re.compile(
        r"(?i)\b(?:api|secret)[_-]?key\s*[:=]\s*['\"][A-Za-z0-9+/_-]{20,}['\"]")),
)


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
    for relpath in p.stdout.splitlines():
        if not relpath or relpath in SECRET_WAIVERS:
            continue
        path = ROOT / relpath
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue  # binary assets carry no greppable credential
        for name, pattern in SECRET_PATTERNS:
            m = pattern.search(text)
            if m:
                line = text[:m.start()].count("\n") + 1
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


CHECKS = (
    ("version stamps", check_versions),
    ("output default", check_output_default),
    ("version citations", check_version_citations),
    ("english-only red line", check_english_only),
    ("markdown link targets", check_links),
    ("stale promises", check_stale_promises),
    ("platform manifest", check_platform_manifest),
    ("retired values", check_retired_values),
    ("token palette parity", check_palette_parity),
    ("token references", check_token_references),
    ("region coverage", check_region_coverage),
    ("probe vocabulary", check_probe_vocabulary),
    ("media-only rules", check_media_only_rules),
    ("layout parity", check_layout_parity),
    ("ban-list parity", check_ban_list_parity),
    ("zh ban-list parity", check_zh_ban_list_parity),
    ("review scores", check_review_scores),
    ("source-marker parity", check_source_marker_parity),
    ("brand lock", check_brand_lock),
    ("no shadow math", check_no_shadow_math),
    ("ledgers", check_ledgers),
    ("commit convention", check_commit_convention),
    ("secrets", check_secrets),
    ("script paths", check_script_paths),
    ("bootstrap", check_bootstrap),
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
