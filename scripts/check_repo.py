#!/usr/bin/env python3
"""Mechanical guards for the invariants this repo maintains by hand.

Covers only what a machine can decide. Whether a rule change was re-flowed into
the three entry points is a reading task and stays with the reviewer.
"""

import ast
import json
import pathlib
import re
import sys
import traceback

ROOT = pathlib.Path(__file__).resolve().parent.parent

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


def md_files():
    return sorted(p for p in ROOT.rglob("*.md") if ".git" not in p.parts)


def rel(path):
    return str(path.relative_to(ROOT))


def css_block(css, opener):
    """Return the declarations inside `opener { ... }`."""
    start = css.index(opener) + len(opener)
    depth = 1
    for i in range(start, len(css)):
        if css[i] == "{":
            depth += 1
        elif css[i] == "}":
            depth -= 1
            if depth == 0:
                return css[start:i]
    raise ValueError(f"unterminated block: {opener}")


def css_vars(block):
    return {m.group(1): m.group(2).strip()
            for m in re.finditer(r"--([\w-]+)\s*:\s*([^;]+);", block)}


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


def check_links():
    errors = []
    for path in md_files():
        text = path.read_text(encoding="utf-8")
        for m in re.finditer(r"\]\(([^)]+)\)", text):
            target = m.group(1).split()[0]
            if re.match(r"^(https?:|mailto:|#)", target):
                continue
            resolved = (path.parent / target.split("#")[0]).resolve()
            if not resolved.exists():
                lineno = text.count("\n", 0, m.start()) + 1
                errors.append(f"{rel(path)}:{lineno}: link target does not exist: {target}")
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
    def _lin(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    def _luma(rgb):
        r, g, b = (_lin(x) for x in rgb)
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    def _hex(value):
        v = value.lstrip("#")
        return tuple(int(v[i:i + 2], 16) for i in (0, 2, 4))

    floor = tokens["contrast"]["floor_text"]
    errors = []
    for palette_name, palette in tokens["palette"].items():
        if not isinstance(palette, dict):
            continue
        base = re.match(r"rgba\(([\d,\s]+),ALPHA\)", palette["ladder_base"])
        ink = tuple(int(c) for c in base.group(1).replace(" ", "").split(","))
        for surface_key in ("bg", "card_bg"):
            surface = _hex(palette[surface_key])
            ls = _luma(surface)
            for i, alpha in enumerate(palette["text_ladder"], 1):
                mixed = tuple(ink[c] * alpha + surface[c] * (1 - alpha) for c in range(3))
                lm = _luma(mixed)
                hi, lo = max(ls, lm), min(ls, lm)
                ratio = (hi + 0.05) / (lo + 0.05)
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
UNDEFINED_VAR_WAIVERS = {}


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
PROBE_NOT_SHIPPED = {
    # Block patterns a document composes for itself. tokens/ tightens their
    # SPACING in the portrait block and never declares a base rendering, which
    # is its own defect and is recorded in CHANGELOG 0.1.368 — but it is a
    # missing rule, not a missing count, and inventing seven block designs to
    # satisfy a guard is exactly the speculative rule-making CLAUDE.md rule 2
    # forbids.
    "card": "portrait-only in tokens/; no base rendering ships. A census entry.",
    "key": "portrait-only in tokens/; the tier-1 callout pair `.key`/`.red` has "
           "no base rendering. check_design.py names both as TIER1_CLASSES.",
    "red": "the seal-coloured half of the tier-1 callout pair; ships nowhere at all.",
    "ledname": "portrait-only in tokens/; no base rendering ships.",
    "swap": "portrait-only in tokens/; no base rendering ships.",
    "vow": "portrait-only in tokens/; no base rendering ships.",
    "no": "the losing side of a `.swap`; portrait-only in tokens/.",
    "yes": "the winning side of a `.swap`; portrait-only in tokens/.",
    # Composition vocabulary. `.page.opener` ships and what a document puts
    # inside one is its own composition; TSEL lists these so opener text is
    # counted as text, not to fix how an opener renders.
    "openpart": "part-opener composition; `.page.opener` ships, its contents compose freely.",
    "openclaim": "part-opener composition; see .openpart.",
    "openrun": "part-opener composition; see .openpart.",
    # Document-local blocks with no design claim behind them.
    "geo-flat": "a flat-map figure a document may draw; CENTER/DSEL count it as a "
                "centerpiece and a drawing, and say nothing about it.",
    "note": "a marginal note inside `.notes`, which does ship; the inner element "
            "is the document's own.",
    "sub": "a subtitle under a cover or opener title; composition, not a role.",
    "tag": "a small status chip; a document's own furniture.",
    "tick": "an axis or timeline label inside a figure.",
    "verdict": "a card's conclusion line; part of `.card`, above.",
    "vn": "the number on a `.vow`; part of `.vow`, above.",
    "vt": "the title of a `.vow`; part of `.vow`, above.",
    "vw": "the body of a `.vow`; part of `.vow`, above.",
    "who": "an attribution line; a document's own furniture.",
    "wordmark": "the organisation's mark on a cover; an asset, not a type role.",
}

# The class-carrying lists inside scripts/inspect_layout.py, by kind. Read out of
# the source with ast.parse and a regex and NEVER by importing it: importing to
# inspect it is how a guard ends up running the thing it is checking.
PROBE_CENSUS_LISTS = ("CENTER", "INK", "TSEL", "DSEL")


def _probe_sources():
    """The two probe strings from inspect_layout.py, or an explanatory failure."""
    tree = ast.parse((ROOT / "scripts/inspect_layout.py").read_text(encoding="utf-8"))
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
    * **census** — `INK`, `TSEL`, `DSEL`, `CENTER` ask only to be counted, and
      over-reach on purpose. These may be waived in `PROBE_NOT_SHIPPED`, one
      written reason each.
    """
    try:
        probes = _probe_sources()
        shipped = _shipped_classes()
        roles = re.findall(r"\[\s*'[^']*'\s*,\s*'([^']+)'",
                           _js_const(probes["CONSISTENCY_PROBE"], "ROLES"))
        scoped = re.findall(r"\[\s*'([^']+)'\s*,\s*\[([^\]]*)\]\s*\]",
                            _js_const(probes["CONSISTENCY_PROBE"], "SCOPED"))
        census = {name: _js_const(probes["PROBE"], name) for name in PROBE_CENSUS_LISTS}
    except (OSError, ValueError, SyntaxError) as exc:
        return [f"could not read the probe vocabulary: {exc}"]

    if not roles or not scoped:
        return ["ROLES or SCOPED parsed to nothing; a guard that reads no "
                "selectors passes every document by construction"]

    contract, census_classes = set(), {}
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
    tree = ast.parse((ROOT / "scripts/check_prose.py").read_text(encoding="utf-8"))
    matched, waived = set(), set()
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        name = getattr(node.targets[0], "id", None)
        if name == "BANNED":
            for element in node.value.elts:
                matched.add(element.elts[1].value.lower())
        elif name == "NOT_MECHANIZED":
            for key in node.value.keys:
                waived.add(key.value.lower())
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
RETIRED_VALUE_WAIVERS = {}

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
        in_fence, para, start = False, [], 1
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
        ):
            value = entry.get(flag)
            # Explicit true, or it is unverified. This read absence as
            # verification, so deleting one optional field silently stripped the
            # published "Unverified" warning from an install note and turned a
            # path the repository admits is a guess into an apparently-checked
            # instruction. Empty string and empty list are absence too: `probe:
            # []` satisfied `is None` here while detect() read it as no probe,
            # so the two files disagreed about what "has a probe" means.
            missing = (value is not True) if flag == "path_verified" else (not value)
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
    current = re.search(r"^##\s+(\d+\.\d+\.\d+)", changelog, re.M).group(1)

    errors = []
    try:
        data = _load_platforms()
    except (OSError, ValueError) as exc:                    # noqa: BLE001
        return [f"adapters/platforms.json: {exc}"]

    for target in sorted({e.get("entry_file") for e in data["platforms"] if e.get("entry_file")}):
        path = ROOT / target
        if not path.exists():
            continue                                        # reported by the manifest guard
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


CHECKS = (
    ("version stamps", check_versions),
    ("version citations", check_version_citations),
    ("english-only red line", check_english_only),
    ("markdown link targets", check_links),
    ("stale promises", check_stale_promises),
    ("platform manifest", check_platform_manifest),
    ("retired values", check_retired_values),
    ("token palette parity", check_palette_parity),
    ("token references", check_token_references),
    ("probe vocabulary", check_probe_vocabulary),
    ("ban-list parity", check_ban_list_parity),
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
