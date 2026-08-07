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
    "data_blue": "d-blue",
    "data_red": "d-red",
    "data_teal": "d-teal",
    "card_bg": "card-bg",
}
PALETTE_NON_COLOR = {"ladder_base", "note", "text_ladder", "rule_ladder"}

# v1.8.0: the ladder is two ladders, and each palette carries its own alphas.
# Until 1.7.0 one shared alpha list served both canvases, and this guard enforced
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
    """One version across the repo: SKILL.md, CHANGELOG, and both tokens/ headers
    carry the same number, so a rule revision bumps all four together."""
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
    ):
        text = (ROOT / name).read_text(encoding="utf-8")
        found = re.search(pattern, text)
        if not found:
            errors.append(f"{name}: no version stamp found in its header")
            continue
        token_versions[name] = found.group(1)

    if len(set(token_versions.values())) > 1:
        errors.append(
            "tokens/lumi-theme.css and tokens/design-tokens.json carry different "
            f"versions ({token_versions}); their palettes mirror, so both bump together"
        )
    for name, version in token_versions.items():
        if version not in released:
            errors.append(f"{name}: version {version} has no CHANGELOG entry")
        elif version != skill_version:
            errors.append(
                f"{name}: version {version} != skill version {skill_version}; "
                f"tokens carry the skill version, so all four stamps bump together"
            )
    return errors


def check_english_only():
    errors = []
    for path in md_files():
        name = rel(path)
        if name in CJK_ALLOWED:
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if CJK.search(line):
                errors.append(
                    f"{name}:{lineno}: CJK characters outside the rule-data allowlist "
                    f"(repository language is English only)"
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
                    f"missing; each palette carries its own {ladder} ladder since 1.8.0"
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
    1.7.0 defect: the alphas were legal, they were simply unreadable."""
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


CHECKS = (
    ("version stamps", check_versions),
    ("english-only red line", check_english_only),
    ("markdown link targets", check_links),
    ("token palette parity", check_palette_parity),
    ("ban-list parity", check_ban_list_parity),
)


def main():
    failed = 0
    for label, check in CHECKS:
        errors = check()
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
