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
}

# A version string may name something other than a release only with a reason.
# Same contract as check_prose.py's NOT_MECHANIZED: a documented exception is a
# reviewable state; an undocumented one is a mistake nobody noticed.
VERSION_CITATION_WAIVERS = {
    "1.0.0": "names the first release of the retired 1.x-3.x scheme, in the prose "
             "that explains why the scheme was retired",
    "3.4.0": "names the last release of the retired scheme, and the commit subject "
             "git history still carries; both are quoted deliberately",
    # Forward references to planned work. Each is deleted from this dict the
    # release it ships, which makes the dict a ratchet: a note still promising
    # something "in 0.1.354" after 0.1.354 has shipped becomes a CI failure
    # rather than stale documentation nobody re-reads.
    "0.1.355": "planned: tracked fixtures and check_fixtures.py. Remove when shipped.",
    "0.1.356": "planned: the cross-agent conformance harness. Remove when shipped.",
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
            missing = (value is False) if flag == "path_verified" else (value is None)
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
        in_fence = False
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            prose, in_fence = _strip_code(line, in_fence)
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
    ("platform manifest", check_platform_manifest),
    ("retired values", check_retired_values),
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
