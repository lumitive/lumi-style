#!/usr/bin/env python3
"""Hold `evals/rule-coverage.json` to the rules and to the checkers.

**What this exists for.** Five rounds of multi-agent conformance produced
deliverables that cleared every gate and were returned by the owner with defects
no gate reads. Counting the two sides on 2026-08-22 said why: **175 checkable
rules about a deliverable, 78 measured, 40 gated, 97 with no check of any kind.**
The check set grew from whatever was cheap to measure and had never been audited
against the rule set. An agent iterates to the edge of what it is shown, so the
output converges on the gated rules and diverges on the rest — and the owner's
eye lands on the rest, every round.

`evals/rule-coverage.json` is the register that makes the unchecked rules
visible. This script keeps it honest. **It does NOT gate on coverage** — a
coverage floor becomes a number to polish, which is 0.1.339's withdrawn 82% fill
floor in another costume. It gates on the register not lying:

1. Every `source` still resolves, and its `quote` is still there verbatim. A
   rule that was reworded or moved reddens immediately, instead of the register
   quietly describing a sentence nobody has written since.
2. Every `metric` named is a metric some checker actually emits.
3. Every entry claiming `gates` names a metric that really gates, and every
   entry claiming otherwise names one that really does not — read from the
   checkers by `scripts/lib/gating.py`, never from a list here.
4. **The reverse direction: every gate is cited by at least one rule.** A
   threshold no rule asks for is this package inventing a requirement, which is
   exactly what convention 6 was written for. This one is easy to forget to
   check and is the half that catches the checker overreaching.
5. The register's own shape: unique ids, a known `page_kind`, and an entry with
   no metric saying WHY in `why_unchecked` rather than leaving it blank.

    python3 scripts/check/check_rule_coverage.py            # the report
    python3 scripts/check/check_rule_coverage.py --check    # exit 1 on a lie
"""
from __future__ import annotations

import argparse
import json
import pathlib

# --- scripts path bootstrap (canonical; the bootstrap guard enforces this) ---
import pathlib as _bs_pathlib  # noqa: E402
import sys
import sys as _bs_sys  # noqa: E402

_SCRIPTS_ROOT = next(p for p in _bs_pathlib.Path(__file__).resolve().parents
                     if p.name == "scripts")
for _sub in ("lib", "render", "check", "build", "ops", ""):
    _p = str(_SCRIPTS_ROOT / _sub) if _sub else str(_SCRIPTS_ROOT)
    if _p not in _bs_sys.path:
        _bs_sys.path.append(_p)
del _bs_pathlib, _bs_sys, _SCRIPTS_ROOT, _sub, _p
# --- end bootstrap ---
import gating  # noqa: E402 — after the bootstrap

ROOT = next(p for p in pathlib.Path(__file__).resolve().parents
            if (p / "SKILL.md").exists())
REGISTER = "evals/rule-coverage.json"

# Which kind of page a rule binds. The six sections `page-contracts.md` is built
# from, and the owner's own split: the bookends and the agenda grouped, the
# content pages given a section of their own.
PAGE_KINDS = ("cover", "agenda", "opener", "closing", "content", "all")


def load(root: pathlib.Path) -> dict:
    return json.loads((root / REGISTER).read_text(encoding="utf-8"))


def check_quote(root: pathlib.Path, source: str, quote: str) -> str:
    """-> "" if the quote is still at that file:line, else why not.

    The line number is a hint, not the assertion. A rule that moved by a few
    lines when a paragraph above it grew has not CHANGED, and reddening the
    build for that would train everyone to bump numbers without reading. So:
    the quote must still exist in the file, and the line must still be close to
    where the register says. Only the quote's disappearance is a real finding.
    """
    if ":" not in source:
        return f"{source!r} is not a file:line reference"
    # A RULE LIVES IN A RULE FILE. `source` was unrestricted, so an entry could
    # cite a deliverable — and `check_repo`'s CJK exemption trusts this field,
    # so a sentence of Chinese lifted out of an HTML fixture passed the
    # english-only red line as "rule data".
    if not source.startswith(("references/", "SKILL.md", "AGENTS.md",
                              "prompts/", "CLAUDE.md")):
        return (f"cites {source.rsplit(':', 1)[0]!r}, which is not a rule file; "
                f"a rule lives in references/ or an entry point")
    path_part, _, line_part = source.rpartition(":")
    path = root / path_part
    if not path.is_file():
        return f"{path_part} does not exist"
    if not line_part.isdigit():
        return f"{source!r} has no line number"
    lines = path.read_text(encoding="utf-8").splitlines()
    want = int(line_part)
    if not 1 <= want <= len(lines):
        return f"line {want} is past the end of {path_part} ({len(lines)} lines)"
    if quote in lines[want - 1]:
        return ""
    where = [i + 1 for i, ln in enumerate(lines) if quote in ln]
    if not where:
        return (f"the quote is nowhere in {path_part} any more — the rule was "
                f"reworded or removed, and this entry now describes a sentence "
                f"that does not exist")
    return (f"the quote has moved to line {where[0]} (register says {want}); "
            f"update the line number")


def audit(root: pathlib.Path) -> tuple[list[str], dict]:
    """-> (findings, the counts for the report)."""
    try:
        data = load(root)
    except (OSError, ValueError) as exc:
        return [f"{REGISTER} does not parse: {exc}"], {}
    rules = data.get("rules")
    if not isinstance(rules, list) or not rules:
        return [f"{REGISTER} declares no rules; a register that is empty "
                f"passes every check by construction"], {}

    # The GATE register can be unreadable too, and `gating`'s readers raise
    # rather than answering the empty set. Caught here so a corrupt
    # `evals/gates.json` is a finding this audit reports, not a traceback out
    # of the `--check` step — the rule register eight lines above already gets
    # exactly this treatment.
    try:
        known = gating.every_metric_name(root)
        gates = gating.every_gating_name(root)
    except (OSError, ValueError, KeyError) as exc:
        return [f"the gate register could not be read ({exc}), so no rule "
                f"could be held to a metric"], {}
    findings: list[str] = []
    seen: set[str] = set()
    cited: set[str] = set()
    measured = gated = 0

    for rule in rules:
        rid = rule.get("id", "<no id>")
        if rid in seen:
            findings.append(f"{rid}: two entries carry this id")
        seen.add(rid)
        if rule.get("page_kind") not in PAGE_KINDS:
            findings.append(
                f"{rid}: page_kind {rule.get('page_kind')!r} is not one of "
                f"{', '.join(PAGE_KINDS)}")
        why = check_quote(root, rule.get("source", ""), rule.get("quote", ""))
        if why:
            findings.append(f"{rid}: {why}")

        metric = rule.get("metric")
        if metric is None:
            if not (rule.get("why_unchecked") or "").strip():
                findings.append(
                    f"{rid}: no metric and no why_unchecked. An unchecked rule "
                    f"has to say why, or the register is a list of shrugs")
            if rule.get("gates"):
                findings.append(f"{rid}: claims to gate with no metric")
            continue
        measured += 1
        cited.add(metric)
        if metric not in known:
            findings.append(
                f"{rid}: names metric {metric!r}, which no checker emits")
            continue
        really = metric in gates
        if really:
            gated += 1
        if bool(rule.get("gates")) != really:
            findings.append(
                f"{rid}: says gates={bool(rule.get('gates'))} for {metric!r}, "
                f"but the checker says {really}")

    # THE REVERSE DIRECTION. Everything above asks whether the register tells
    # the truth about the rules; this asks whether the CHECKERS do. A gate no
    # rule asks for is a requirement this package invented, and inventing one
    # is what convention 6 exists to stop.
    #
    # Some of them are legitimate anyway: `bookend_title_length` was calibrated
    # on the accepted reference deck because no sentence in `references/` states
    # a bookend length, and `band_escape` came from a rendering defect nobody
    # had written a rule about. Those are DECISIONS and they go in
    # `orphan_gates` with a reason, on the KNOWN_GAPS pattern and on the same
    # reasoning as the ban-list guard's `NOT_MECHANIZED`. What may not happen is
    # a gate drifting into the set with nobody noticing, so an UNDECLARED orphan
    # is a finding and every declared one is printed on every run.
    # THE FIFTH CHECK: one property, one place it is decided.
    #
    # The owner asked where the design, the execution, the Inspector and the
    # Evals live for the parts every page kind SHARES — she remembered two, the
    # water-ripple ground and the footer. There are more, and the register could
    # not answer because nothing in it said which rules talk about the same
    # thing. Three real collisions were found by reading: the ground's tier is
    # stated in `brand.md` for all pages and again in `storyline-templates.md`
    # for openers; the footer marker's colour is stated once for all pages and
    # THREE times for openers, in two different files; and a rule about titles
    # written for every page cites a gate that measures content pages only.
    #
    # `covers` names the property, `overrides` names the entry this one is
    # written against. The check does not care WHICH relation it is — narrowing,
    # restating, or contradicting on purpose. It cares that a second statement
    # of the same property is deliberate rather than discovered later by
    # somebody chasing a value that changed in one file.
    #
    # It is opt-in: an entry with no `covers` is in no group and is checked as
    # before. Labelling all 485 by property is a hand job with its own error
    # rate, so the count of unlabelled per-kind rules is REPORTED and shrinks
    # release by release — a coverage floor would become a number to polish.
    by_property: dict[str, list[dict]] = {}
    for rule in rules:
        key = (rule.get("covers") or "").strip()
        if key:
            by_property.setdefault(key, []).append(rule)
    for key, group in sorted(by_property.items()):
        ids = {r.get("id") for r in group}
        for rule in group:
            rid = rule.get("id", "<no id>")
            against = (rule.get("overrides") or "").strip()
            if against == rid:
                findings.append(f"{rid}: overrides itself")
            elif against and against not in ids:
                findings.append(
                    f"{rid}: overrides {against!r}, which does not cover "
                    f"{key!r} — an override has to name the entry it is "
                    f"written against")
        # ONE ROOT PER PROPERTY. Every other entry says which one it is written
        # against; the root is the one nothing points away from, and it is
        # where the value is decided. Two roots means two statements of the
        # same property with nothing joining them, which is the shape that put
        # 1.40 in six files. No root means the overrides form a cycle.
        roots = [r for r in group if not (r.get("overrides") or "").strip()]
        if len(roots) > 1:
            findings.append(
                f"{key!r} is stated by "
                f"{', '.join(sorted(r.get('id', '?') for r in roots))} and none "
                f"of them says which is the authority. Give every entry but one "
                f"an `overrides` naming the entry it is written against — "
                f"narrowing it, restating it, or contradicting it on purpose")
        elif not roots:
            findings.append(
                f"{key!r}: every entry overrides another, so the overrides "
                f"form a cycle and no entry decides the value")
    counts_extra = {"properties": len(by_property),
                    "unlabelled_kind_rules": sum(
                        1 for r in rules
                        if r.get("page_kind") not in ("all", "content")
                        and not (r.get("covers") or "").strip())}

    declared = data.get("orphan_gates", {})
    if not isinstance(declared, dict):
        findings.append("orphan_gates must be an object of gate -> reason")
        declared = {}
    for orphan in sorted(gates - cited):
        if not (declared.get(orphan) or "").strip():
            findings.append(
                f"gate {orphan!r} is cited by no rule in the register — either "
                f"a rule states it and belongs here, or it is a threshold "
                f"nothing in references/ asks for and needs an orphan_gates "
                f"entry saying so")
    for stale in sorted(set(declared) - gates):
        findings.append(
            f"orphan_gates declares {stale!r}, which is not a gate — it was "
            f"renamed, withdrawn, or a rule now cites it; drop the entry")
    for covered in sorted(set(declared) & cited):
        findings.append(
            f"orphan_gates declares {covered!r} as having no rule, but a "
            f"register entry now cites it; drop the entry")

    counts = {"rules": len(rules), "measured": measured, "gated": gated,
              "unchecked": len(rules) - measured, "gates": len(gates),
              "gates_cited": len(gates & cited),
              "orphans": len(gates - cited), **counts_extra}
    return findings, counts


def relocate(root: pathlib.Path) -> tuple[int, list[str]]:
    """Move each entry's line number to where its quote actually is.

    -> (how many moved, what could not be moved and why).

    **The quote is the assertion; the line is a pointer.** Editing a paragraph
    above a rule shifts fifty entries without changing one rule, and hand-typing
    fifty new numbers is how a register starts lying. So this only ever follows
    a quote that appears EXACTLY ONCE — an ambiguous or vanished quote is a
    finding for a person, never something to guess at.
    """
    path = root / REGISTER
    data = json.loads(path.read_text(encoding="utf-8"))
    moved, stuck = 0, []
    for rule in data["rules"]:
        source, quote = rule.get("source", ""), rule.get("quote", "")
        if not check_quote(root, source, quote):
            continue
        file_part, _, _ = source.rpartition(":")
        target = root / file_part
        if not target.is_file():
            stuck.append(f"{rule['id']}: {file_part} does not exist")
            continue
        hits = [i + 1 for i, ln
                in enumerate(target.read_text(encoding="utf-8").splitlines())
                if quote in ln]
        if len(hits) != 1:
            stuck.append(
                f"{rule['id']}: the quote appears {len(hits)} times in "
                f"{file_part}; move it by hand")
            continue
        rule["source"] = f"{file_part}:{hits[0]}"
        moved += 1
    if moved:
        path.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n",
                        encoding="utf-8")
    return moved, stuck


def report(root: pathlib.Path, counts: dict) -> None:
    data = load(root)
    print(f"  {counts['rules']} rules · {counts['measured']} measured · "
          f"{counts['gated']} gated · {counts['unchecked']} with no check")
    print(f"  {counts['gates_cited']} of {counts['gates']} gates trace to a "
          f"stated rule")
    by_kind: dict[str, list[str]] = {}
    for rule in data["rules"]:
        if rule.get("metric") is None:
            by_kind.setdefault(rule.get("page_kind", "?"), []).append(
                f"{rule.get('id')} {rule.get('gist', '')}")
    if by_kind:
        print("  unchecked, by the page they bind:")
        for kind in PAGE_KINDS:
            items = by_kind.get(kind, [])
            if items:
                print(f"    {kind:<9} {len(items):>3}")
    # WHERE THE SHARED PARTS ARE DECIDED. The properties every page kind
    # touches — the ground, the footer, the title budget — are the ones a
    # per-kind change can silently contradict, and until this the register had
    # no way to say so. Each line names the entry that decides the value and
    # every entry written against it.
    props: dict[str, list[dict]] = {}
    for rule in data["rules"]:
        key = (rule.get("covers") or "").strip()
        if key:
            props.setdefault(key, []).append(rule)
    if props:
        print(f"  {len(props)} shared propert(ies) with a declared owner:")
        for key, group in sorted(props.items()):
            # `owner`, not `root` — `root` is this function's parameter, and
            # shadowing it typed the repository's path as a rule dict.
            owner = next((r for r in group
                          if not (r.get("overrides") or "").strip()), None)
            others = [r for r in group if r is not owner]
            written = ", ".join(f"{r.get('id')} ({r.get('page_kind')})"
                                for r in others)
            print(f"    {key:<26} {owner and owner.get('id')} "
                  f"({owner and owner.get('page_kind')})"
                  + (f" ← {written}" if others else ""))
    left = counts.get("unlabelled_kind_rules")
    if left:
        print(f"  {left} cover/agenda/opener/closing rule(s) still name no "
              f"property; an overlap they are part of cannot be seen yet")
    orphans = data.get("orphan_gates", {})
    if orphans:
        print(f"  {len(orphans)} gate(s) enforce something no rule states, each "
              f"a written decision:")
        for name, why in sorted(orphans.items()):
            print(f"    {name:<22} {why}")
    print("  Coverage is REPORTED and never gated: a coverage floor becomes a "
          "number to polish.")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true",
                    help="exit 1 when the register disagrees with the rules "
                         "or with the checkers")
    ap.add_argument("--relocate", action="store_true",
                    help="follow each quote to its current line and rewrite the "
                         "register's line numbers. Only ever moves a quote that "
                         "appears exactly once")
    ap.add_argument("--root", type=pathlib.Path, default=ROOT,
                    help="tree to audit (the guard tests point this at a "
                         "synthetic one)")
    args = ap.parse_args(argv)

    if args.relocate:
        moved, stuck = relocate(args.root)
        print(f"ok    followed {moved} quote(s) to their current line")
        for why in stuck:
            print(f"  note  {why}")

    findings, counts = audit(args.root)
    if counts:
        report(args.root, counts)
    for f in findings:
        print(f"  FAIL  {f}")
    if findings:
        print(f"\n{len(findings)} finding(s). The register is the map of what "
              f"this package enforces; a wrong map is worse than none.")
        return 1 if args.check else 0
    print("ok    the register agrees with the rules and with the checkers")
    return 0


if __name__ == "__main__":
    sys.exit(main())
