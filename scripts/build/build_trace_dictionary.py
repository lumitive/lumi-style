#!/usr/bin/env python3
"""The trace store's dictionary and index, generated from the schema and the store.

**Why generated rather than written.** A hand-written description of thirty
fields is the drift class this repository has fixed twenty-six times — and the
trace schema is the worst candidate for it, because every field's meaning
currently lives in a comment inside `scripts/lib/trace_schema.py` where no
reader outside this repository will ever look.

**Two artifacts, two readers, one derivation.**

* `evals/traces/README.md` — what each field means, its type, which of the three
  populations it belongs to, and whether a person may edit it. For someone
  opening the directory for the first time.
* `evals/traces/index.jsonl` — one JSON object per line, one line per trace,
  carrying the summary fields and NOT the verdict blocks. For a query, a script,
  or an analysis service that should not have to reimplement this package's
  filters to get a correct denominator.

**The preface is the load-bearing part.** The store holds far more files than it
holds records: `trace_store.suite_artifact()` sets aside build traces that pytest
leaked into the tracked directory before 2026-08-26, and that rule lives in code
and in CHANGELOG prose and nowhere a consumer would find it. A reader who counts
the files gets a denominator three times too large — which is not hypothetical:
`ledger.py` once reported "4 of 251 builds" over a store holding seventeen. The
index carries `suite_artifact` as a column so the filter travels with the data.
"""
import argparse
import collections
import json
import pathlib
import pathlib as _bs_pathlib  # noqa: E402 — the bootstrap's, see below
import sys
import sys as _bs_sys  # noqa: E402 — the bootstrap's, see below

# --- scripts path bootstrap (canonical; the bootstrap guard enforces this) ---
_SCRIPTS_ROOT = next(p for p in _bs_pathlib.Path(__file__).resolve().parents
                     if p.name == "scripts")
for _sub in ("lib", "render", "check", "build", "ops", ""):
    _p = str(_SCRIPTS_ROOT / _sub) if _sub else str(_SCRIPTS_ROOT)
    if _p not in _bs_sys.path:
        _bs_sys.path.append(_p)
del _bs_pathlib, _bs_sys, _SCRIPTS_ROOT, _sub, _p

import trace_schema  # noqa: E402
import trace_store  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]
TRACES = ROOT / "evals" / "traces"
DICT_OUT = TRACES / "README.md"
INDEX_OUT = TRACES / "index.jsonl"

# WHAT A PERSON MAY EDIT BY HAND, and it is deliberately short. `trace.py` has
# no flag for supplying a verdict, which is the same discipline
# `check_evidence.py` enforces one layer up — a human never types "pass". These
# three are the ones a person is the AUTHORITY on: what a build was for, which
# review it belongs to, and what the operator wants to remember about it.
# Everything else is a measurement, and hand-editing a measurement is not an
# edit, it is a forgery.
HAND_EDITABLE = ("corpus_id", "review_ref", "annotations")

# The columns the index carries. Verdict blocks are excluded on purpose: they
# are 44% of the store's bytes and they belong in the trace, which the index
# points at.
INDEX_FIELDS = ("trace_id", "path", "opened_at", "closed_at", "source", "agent",
                "model", "effort", "cli_version", "skill_version", "genre",
                "storyline", "entry_path", "geometry", "pages", "content_pages",
                "output_tokens", "input_tokens", "charged_seconds",
                "fail_count", "tags", "note", "suite_artifact")


def _schema_lines() -> dict[str, int]:
    """-> field name to the line in trace_schema.py that declares it.

    A citation rather than a copy of the comment beside it: the comment is the
    authority and duplicating it here would create the second copy this whole
    file exists to avoid.
    """
    src = (ROOT / "scripts" / "lib" / "trace_schema.py").read_text(encoding="utf-8")
    out: dict[str, int] = {}
    inside = False
    for n, line in enumerate(src.splitlines(), 1):
        if line.startswith("FIELDS"):
            inside = True
        elif inside and line.startswith("}"):
            break
        elif inside:
            for name in trace_schema.FIELDS:
                if f'"{name}":' in line and name not in out:
                    out[name] = n
    return out


def _type_name(spec) -> str:
    if isinstance(spec, tuple):
        return " | ".join(t.__name__ if t is not type(None) else "null"
                          for t in spec)
    return getattr(spec, "__name__", str(spec))


def _side(name: str) -> str:
    for label, members in (("document", trace_schema.DOCUMENT_FIELDS),
                           ("producer", trace_schema.PRODUCER_FIELDS),
                           ("run", trace_schema.RUN_FIELDS)):
        if name in members:
            return label
    return "—"


def _example(name: str, records: list[dict]) -> str:
    """-> one real value from the store, or `—` when nothing carries it.

    Real rather than invented, so a reader learns the SHAPE the field takes in
    practice — `2026.08.25-3e8eec8` teaches more than `str` does.
    """
    for rec in records:
        v = rec.get(name)
        if v in (None, "", [], {}):
            continue
        text = json.dumps(v, ensure_ascii=False)
        return f"`{text[:44]}…`" if len(text) > 46 else f"`{text}`"
    return "—"


def index_rows(records: list[dict]) -> list[dict]:
    """-> one summary object per trace, ordered by when it was opened.

    Ordered by time rather than by id: the ids are uuid4-derived and sort
    randomly, so the directory listing tells a reader nothing about sequence and
    this is the only place sequence appears.
    """
    rows = []
    for rec in records:
        tid = rec.get("trace_id")
        if not tid:
            continue
        phases = rec.get("phase_seconds") or {}
        fails = sum(1 for bucket in ("gates", "graded")
                    for v in (rec.get(bucket) or {}).values()
                    if str(v).upper() == "FAIL")
        row = {k: rec.get(k) for k in INDEX_FIELDS
               if k not in ("path", "charged_seconds", "fail_count",
                            "tags", "note", "suite_artifact")}
        # FLATTENED into two columns, because the index is one object per line
        # and a nested block in it defeats grep — which is the whole reason a
        # human opens this file rather than the trace.
        ann = rec.get("annotations") or {}
        row["tags"] = ann.get("tags") or []
        row["note"] = ann.get("note")
        row["path"] = f"evals/traces/{tid}.json"
        row["charged_seconds"] = sum(
            v for k, v in phases.items() if k in ("build", "checks")) or None
        row["fail_count"] = fails if rec.get("closed_at") else None
        row["suite_artifact"] = trace_store.suite_artifact(rec)
        rows.append({k: row[k] for k in INDEX_FIELDS})
    return sorted(rows, key=lambda r: (r["opened_at"] or "", r["trace_id"]))


def render_index(records: list[dict]) -> str:
    return "".join(json.dumps(r, ensure_ascii=False, sort_keys=False) + "\n"
                   for r in index_rows(records))


def render_dictionary(records: list[dict]) -> str:
    kept = [r for r in records if not trace_store.suite_artifact(r)]
    aside = len(records) - len(kept)
    closed = sum(1 for r in kept if r.get("closed_at"))
    lines_at = _schema_lines()
    by_source = collections.Counter(r.get("source") for r in kept)
    fill: collections.Counter = collections.Counter()
    for rec in kept:
        for k, v in rec.items():
            if v not in (None, "", [], {}):
                fill[k] += 1

    out = [
        "# The trace store — what is in it and what each field means",
        "",
        "**GENERATED by `scripts/build/build_trace_dictionary.py` — do not "
        "edit.** The field meanings live in `scripts/lib/trace_schema.py`'s "
        "comments and are cited below by line rather than copied, because a "
        "second copy of thirty descriptions is the drift this repository has "
        "fixed twenty-six times. `--check` in CI refuses a stale render.",
        "",
        "## Read this before you count anything",
        "",
        f"The directory holds **{len(records)} JSON files** and "
        f"**{len(kept)} records**. The difference — {aside} files — is build "
        "traces that pytest leaked into the tracked store before 2026-08-26, "
        "set aside by `trace_store.suite_artifact()`.",
        "",
        "**A reader who counts files instead of records gets a denominator "
        "several times too large.** That is not hypothetical: `ledger.py` once "
        "reported \"4 of 251 build(s) record a reviewed outline\" over a store "
        "holding seventeen real builds. `evals/traces/index.jsonl` carries "
        "`suite_artifact` as a column so the filter travels with the data "
        "instead of living only in this package's code.",
        "",
        f"Of the {len(kept)} records, **{closed} are closed** — a trace is "
        "opened when a build starts and closed when its checks are "
        "transcribed, so an open one is a build that was abandoned or is still "
        "running. Only closed traces carry verdicts, tokens or timings.",
        "",
        "By source: " + ", ".join(f"`{k}` {v}" for k, v in
                                  sorted(by_source.items(),
                                         key=lambda kv: -kv[1])) + ".",
        "",
        "## Where to start",
        "",
        "| file | what it is |",
        "|---|---|",
        "| `index.jsonl` | one line per trace, summary fields only, ordered by "
        "`opened_at`. The ids sort randomly, so this is the only place "
        "sequence appears. |",
        "| `t-<id>.json` | one trace, whole, including the three verdict "
        "blocks the index omits. |",
        "| `.phases/` | local clock state for phases that have started. "
        "Gitignored, not part of the record. |",
        "",
        "## The fields",
        "",
        "**Three populations, and the partition is enforced.** A trace records "
        "facts about the DOCUMENT that was built, the PRODUCER that built it, "
        "and the RUN itself; `check_trace_schema` asserts the three are "
        "disjoint and together exhaust the schema, so a new field must be "
        "assigned a side. What a reader may do across the line is stated in "
        "`conformance/README.md`.",
        "",
        "**`annotations` may be written in any language.** `evals/` is "
        "development-side, so no trace reaches a reader of the published "
        "package, and an operator's note about their own run is neither rule "
        "prose nor rule data — it is the one place in this repository exempt "
        "from the English-only red line, and `check_repo`'s english-only guard "
        "excludes `evals/traces/` for exactly that reason. Every other field "
        "is a measurement with no natural language in it.",
        "",
        "**Hand-editable** marks the fields a person is the authority on. "
        "Everything else is a measurement, and `trace.py` has no flag for "
        "supplying one — the same discipline `check_evidence.py` enforces one "
        "layer up, where a human never types \"pass\".",
        "",
        "| field | type | population | hand-editable | present in | example | "
        "declared at |",
        "|---|---|---|---|---|---|---|",
    ]
    for name in sorted(trace_schema.FIELDS):
        spec = trace_schema.FIELDS[name]
        enum = trace_schema.ENUMS.get(name)
        typ = _type_name(spec)
        if enum:
            typ += " — one of " + ", ".join(f"`{v}`" for v in enum)
        if name == "shape":
            typ += " — keys: " + ", ".join(f"`{k}`" for k in trace_schema.SHAPE_KEYS)
        later = " *(optional; added after records existed)*" \
            if name in trace_schema.ADDED_LATER else ""
        out.append(
            f"| `{name}` | {typ}{later} | {_side(name)} | "
            f"{'**yes**' if name in HAND_EDITABLE else 'no'} | "
            f"{fill.get(name, 0)} of {len(kept)} | {_example(name, kept)} | "
            f"`trace_schema.py:{lines_at.get(name, 0)}` |")
    out += [
        "",
        "## What is not here",
        "",
        "* **Traces do not ship.** `adapters/shipped.json` puts `evals/` on the "
        "development side, so the published package carries none of this. A "
        "service reads the development repository.",
        "* **A field's meaning is not restated here.** The `declared at` column "
        "cites the line; the comment there is the authority.",
        "* **The index is only as fresh as its last regeneration.** `--check` "
        "makes staleness loud rather than impossible, which is the bargain "
        "every generated artifact here takes.",
        "",
    ]
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true",
                    help="verify the tracked renders are current (CI)")
    args = ap.parse_args(argv)

    records = trace_store.load(include_suite_artifacts=True)
    want = {DICT_OUT: render_dictionary(records),
            INDEX_OUT: render_index(records)}

    # A LABEL, not a path computation. `relative_to` RAISES when the artifact
    # is somewhere else — a test, an operator's copy — and the one thing these
    # branches must not do is crash while reporting a mismatch.
    def where(p: pathlib.Path) -> str:
        return str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p)

    if args.check:
        stale = [p for p, text in want.items()
                 if (p.read_text(encoding="utf-8") if p.exists() else "") != text]
        if stale:
            print("FAIL  " + ", ".join(where(p) for p in stale)
                  + " is stale or missing; re-run without --check")
            return 1
        print(f"ok    the trace dictionary and index are current "
              f"({len(records)} file(s))")
        return 0

    for path, text in want.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    print(f"wrote {where(DICT_OUT)} and {where(INDEX_OUT)} "
          f"({len(records)} file(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
