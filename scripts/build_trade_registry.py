#!/usr/bin/env python3
"""Generate the trade-bloc registry from the bloc memberships.

    python3 scripts/build_trade_registry.py            # write
    python3 scripts/build_trade_registry.py --check    # verify current (CI)

A SECOND registry, beside the geographic `regions.json`, which stays the
shipped default. Trade blocs cover part of the world, not all of it, so
`check_repo.py`'s coverage guard — every country in exactly one region — would
fail on them; the per-instance registry machinery from 0.1.395 exists for
exactly this.

**The blocs overlap, and that is the interesting part.** ASEAN's ten are all
inside RCEP's fifteen; CPTPP shares seven with RCEP and two with USMCA. The
renderer needs a disjoint set to fill from and the reader needs the true
membership, so each record carries both:

    members  the BASE PARTITION — disjoint, one country one bloc, what the
             map fills. Derived here, never typed.
    full     the real membership, overlaps and all. What the label counts and
             what the click-to-highlight overlay draws.

The partition rule is SMALLEST BLOC WINS, and it is a rule rather than a
preference: the smallest bloc containing a country is the most specific true
statement about it. Singapore is ASEAN before it is RCEP, Canada is USMCA
before it is CPTPP, Japan is CPTPP before it is RCEP. The eight sizes are all
distinct, so the rule is total and the output is deterministic.

Ten members cannot be drawn at all — island and micro states below the 110m
geometry's resolution. Three of them (Malta, Singapore, Bahrain) are carried as
point nodes, because `regions.json` already carries them; the other seven are
African island states this topology simply does not draw. THE LABEL COUNTS THE
MEMBERSHIP REGARDLESS, so it says 27 for the EU while 26 shapes fill: the count
is a fact about the bloc, not about the geometry, and a count that quietly
dropped Malta would be the lie.

Standard library only.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOPOLOGY = ROOT / "assets" / "vectors" / "world-110m.json"
GEO_REGIONS = ROOT / "assets" / "vectors" / "regions.json"
OUT = ROOT / "assets" / "vectors" / "regions-trade.json"

# (id, English, Chinese, abbreviation, label anchor [lon, lat], members).
# Memberships are the owner's lists, keyed by the topology's own ADM0_A3.
#
# ADM0_A3 IS NOT ISO 3166-1 ALPHA-3, and two of these differ: South Sudan is
# SDS here and SSD in ISO, Western Sahara is SAH and ESH. Natural Earth's field
# is what build_worldmap.py keyed the topology on, so it is what a registry has
# to say — a record written from the ISO list looks right and draws nothing.
#
# Anchors are chosen so the label sits over the bloc AND clear of the point
# nodes: AFTA's was over Singapore's node and GCC's over Bahrain's, each
# putting a white disc through the middle of its own name.
#
# Order here is display order — the order a legend prints in.
BLOCS = [
    ("eu", "European Union", "欧洲联盟", "EU", [10.0, 50.5], """
        AUT BEL BGR HRV CYP CZE DNK EST FIN FRA DEU GRC HUN IRL ITA LVA LTU
        LUX MLT NLD POL PRT ROU SVK SVN ESP SWE"""),
    ("usmca", "USMCA", "美加墨协定", "USMCA", [-100.0, 40.0], """
        USA CAN MEX"""),
    ("rcep", "RCEP", "区域全面经济伙伴关系协定", "RCEP", [104.0, 35.0], """
        IDN MYS PHL SGP THA BRN VNM LAO MMR KHM CHN JPN KOR AUS NZL"""),
    ("cptpp", "CPTPP", "全面与进步跨太平洋伙伴关系协定", "CPTPP", [134.0, -25.0], """
        JPN SGP VNM MYS BRN AUS NZL CAN MEX PER CHL GBR"""),
    ("asean", "ASEAN", "东盟自由贸易区", "AFTA", [114.0, -1.5], """
        IDN MYS PHL SGP THA BRN VNM LAO MMR KHM"""),
    ("mercosur", "Mercosur", "南方共同市场", "MERCOSUR", [-58.0, -25.0], """
        BRA ARG URY PRY"""),
    ("gcc", "GCC", "海湾阿拉伯国家合作委员会", "GCC", [44.5, 20.0], """
        SAU ARE QAT KWT BHR OMN"""),
    # The African Union's members, which are the AfCFTA's. Listed rather than
    # inferred from geography: "African" is not a property the topology carries.
    ("afcfta", "AfCFTA", "非洲大陆自由贸易区", "AfCFTA", [20.0, 2.0], """
        DZA AGO BEN BWA BFA BDI CMR CPV CAF TCD COM COG COD CIV DJI EGY GNQ
        ERI SWZ ETH GAB GMB GHA GIN GNB KEN LSO LBR LBY MDG MWI MLI MRT MUS
        MAR MOZ NAM NER NGA RWA STP SEN SYC SLE SOM ZAF SDS SDN TZA TGO TUN
        UGA ZMB ZWE SAH"""),
]


# Population, in millions, of each bloc's FULL membership. UN World Population
# Prospects 2024 revision, mid-2024 estimates, summed over the members listed
# above and rounded to the ten million — because this number is a LABEL, and a
# label that read 449.2 would be claiming a precision that summing 27 national
# estimates does not have.
#
# ASEAN's entry is 690, not the 530 million the brief quotes. That figure comes
# with the sentence that dates it — "经过10年的构建，原东盟6国于2002年正式启动
# 自由贸易区" — and ASEAN's ten have grown by about 160 million since. Both
# numbers are right about their own year; a label drawn today has to be right
# about this one, and a 2002 population under a 2024 map is the kind of quiet
# staleness nothing downstream can catch.
#
# It lives here, beside the membership it is a property of, for the same reason
# `count` does: a consumer that has the members should not have to go somewhere
# else to say how many people they are.
POPULATION_M = {
    "eu": 450, "usmca": 510, "rcep": 2300, "cptpp": 590, "asean": 690,
    "mercosur": 310, "gcc": 60, "afcfta": 1450,
}

# The members nothing in the package can name. The topology names every country
# it draws and regions.json names the three point nodes; these five are AfCFTA
# island states that are neither. A consumer building a panel from this registry
# could name 50 of AfCFTA's 55 — which is the 0.1.398 count defect one layer
# down, a list quietly shorter than the number above it. Names only, in the two
# languages the topology carries, because there is no geometry to give them.
UNDRAWN_NAMES = {
    "COM": ("Comoros", "科摩罗"),
    "CPV": ("Cabo Verde", "佛得角"),
    "MUS": ("Mauritius", "毛里求斯"),
    "STP": ("Sao Tome and Principe", "圣多美和普林西比"),
    "SYC": ("Seychelles", "塞舌尔"),
}


def build():
    topo = json.loads(TOPOLOGY.read_text(encoding="utf-8"))
    drawable = {c["a"] for c in topo["countries"]}
    geo = json.loads(GEO_REGIONS.read_text(encoding="utf-8"))

    blocs = [(bid, en, zh, abbr, anchor, sorted(set(codes.split())))
             for bid, en, zh, abbr, anchor, codes in BLOCS]

    # SMALLEST BLOC WINS. Sorted by membership size, so the first bloc to claim
    # a country keeps it. Sizes are distinct, so no tiebreak is needed and the
    # result does not depend on the order above.
    by_size = sorted(blocs, key=lambda b: (len(b[5]), b[0]))
    base: dict[str, list[str]]
    claimed, base = {}, {b[0]: [] for b in blocs}
    for bid, _en, _zh, _abbr, _anchor, codes in by_size:
        for code in codes:
            if code not in claimed:
                claimed[code] = bid
                base[bid].append(code)

    regions, undrawable = [], []
    for bid, en, zh, abbr, anchor, codes in blocs:
        missing = [c for c in codes if c not in drawable]
        undrawable += [(bid, c) for c in missing]
        regions.append({
            "id": bid, "n": en, "z": zh, "abbr": abbr, "anchor": anchor,
            "members": sorted(c for c in base[bid] if c in drawable),
            "full": codes,
            "count": len(codes),
            "pop_m": POPULATION_M[bid],
        })

    missing_pop = sorted({b[0] for b in blocs} - set(POPULATION_M))
    if missing_pop:
        raise SystemExit(f"FAIL  POPULATION_M has no entry for "
                         f"{', '.join(missing_pop)}; a bloc that ships without "
                         f"one puts an empty field on every label")

    nameable = drawable | {n["id"] for n in geo.get("nodes", [])}
    unnameable = {c for _b, c in undrawable} - nameable
    if unnameable != set(UNDRAWN_NAMES):
        raise SystemExit(
            f"FAIL  UNDRAWN_NAMES must be exactly the members this package "
            f"cannot name. Missing: {sorted(unnameable - set(UNDRAWN_NAMES))}; "
            f"stale: {sorted(set(UNDRAWN_NAMES) - unnameable)}")

    noded = {n["id"] for n in geo.get("nodes", [])
             if claimed.get(n["id"])} & {c for _b, c in undrawable}
    return {
        "schema": 1,
        "$comment": (
            "GENERATED by scripts/build_trade_registry.py — do not edit, run the "
            "script. The trade blocs OVERLAP: ASEAN's ten sit inside RCEP's "
            "fifteen, CPTPP shares seven with RCEP and two with USMCA. So each "
            "record carries two lists. `members` is the base partition — "
            "disjoint, derived by SMALLEST BLOC WINS, and what the map fills, "
            "because a fill has to pick one. `full` is the real membership and "
            "is what `count` counts, what the label prints and what the "
            "click-to-highlight overlay outlines. Where they differ, `full` is "
            "the truth about the bloc and `members` is a drawing decision. "
            "This is a SECOND registry: regions.json stays the shipped default "
            "because check_repo's coverage guard wants every country in exactly "
            "one region and trade blocs cover part of the world. "
            f"Below the 110m geometry's resolution, so no shape fills for "
            f"them: {', '.join(sorted({c for _b, c in undrawable}))}. Three are "
            f"carried as point nodes because regions.json already carries them "
            f"({', '.join(sorted(noded))}); the rest are island states this "
            f"topology simply does not draw. THE COUNT STILL INCLUDES THEM — it "
            "is a fact about the bloc, not about the geometry, and a count that "
            "quietly dropped Malta would be the lie."),
        "partition_rule": (
            "smallest bloc wins; membership sizes are distinct so the rule is "
            "total and the output does not depend on declaration order"),
        "regions": regions,
        # Every member this package cannot otherwise name. Keyed by ADM0_A3,
        # [English, Chinese] to match the topology's own n/z fields.
        "names": {c: list(v) for c, v in sorted(UNDRAWN_NAMES.items())},
        # The point layer, taken from the geographic registry so the two agree
        # about where a city-state is, with each node's bloc re-pointed.
        "nodes": [
            {**n, "region": claimed.get(n["id"], None)}
            for n in geo.get("nodes", [])
            if claimed.get(n["id"])
        ],
    }


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    built = json.dumps(build(), indent=1, ensure_ascii=False) + "\n"
    current = OUT.read_text(encoding="utf-8") if OUT.exists() else None
    if args.check:
        if current != built:
            print(f"FAIL  {OUT.relative_to(ROOT)} is stale or missing; "
                  f"re-run without --check")
            return 1
        print(f"ok    {OUT.relative_to(ROOT)} is current")
        return 0
    OUT.write_text(built, encoding="utf-8")
    data = json.loads(built)
    print(f"wrote {OUT.relative_to(ROOT)}  ({len(built):,} bytes)")
    for r in data["regions"]:
        print(f"  {r['abbr']:9} {r['count']:>3} members, "
              f"{len(r['members']):>3} fill the base partition, "
              f"{r['pop_m'] / 1000:.2f}B people")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
