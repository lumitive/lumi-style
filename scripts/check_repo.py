#!/usr/bin/env python3
"""Mechanical guards for the invariants this repo maintains by hand.

Covers only what a machine can decide. Whether a rule change was re-flowed into
the three entry points is a reading task and stays with the reviewer.
"""

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
    "on_accent": "on-acc",
    "seal": "seal",
    "seal_text": "seal-t",
    "data_blue": "d-blue",
    "data_teal": "d-teal",
    "card_bg": "card-bg",
}
PALETTE_NON_COLOR = {"ladder_base", "note"}

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
    """SKILL.md and CHANGELOG move together; a tokens/ header records the last
    version that changed that file, so it may lag but must still be real."""
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

    def as_tuple(v):
        return tuple(int(p) for p in v.split("."))

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
        elif as_tuple(version) > as_tuple(skill_version):
            errors.append(
                f"{name}: version {version} is ahead of the skill version {skill_version}"
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
        for alpha in tokens["palette"]["ladder_alpha"]:
            var = f"w{f'{alpha:.2f}'[2:]}"
            actual = variables.get(var)
            if actual is None:
                errors.append(
                    f"tokens/lumi-theme.css: --{var} missing for the {palette_name} "
                    f"ladder (design-tokens.json lists alpha {alpha})"
                )
                continue
            got = re.match(r"rgba\(([\d,\s]+),\s*(0?\.\d+|1|0)\)", actual.replace(" ", ""))
            if not got or got.group(1) != channels or float(got.group(2)) != alpha:
                errors.append(
                    f"tokens/lumi-theme.css: --{var} is {actual}, expected "
                    f"rgba({channels},{alpha}) for the {palette_name} ladder"
                )
    return errors


CHECKS = (
    ("version stamps", check_versions),
    ("english-only red line", check_english_only),
    ("markdown link targets", check_links),
    ("token palette parity", check_palette_parity),
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
