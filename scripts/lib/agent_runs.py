"""What a configuration costs to produce a page that cleared the bar.

**This is an AGENT evaluation, and it had been living inside a document one.**
`ledger.py` answers three questions about DOCUMENTS — which metric keeps
failing, which instrument is suspect, what to change next. The model x effort
cost matrix answers a different one, and it sat in that file only because the
traces it reads were already open there. The owner asked for the two to stop
being one tool; this module is the agent half. The tool that will own it is the
next stage — until then `ledger.py --board` still renders through here.

**The qualification argument moves with the code, because losing it is the
expensive half.** A run with a failing gate is not on this board at all. A thin
deck is cheap and worthless, and an efficiency board that admitted one would
reward exactly the behaviour every other check in this package exists to catch.
So the DOCUMENT's verdict is the admission ticket to the AGENT's board — which
is the one direction this seam runs: a document fact may QUALIFY a run, and a
producer fact may never GRADE a document.

Prices stay an operator's file with a date on it, and no derivation of them is
stored: `cost_usd` was a trace field once and was deleted, because a stored
derivation goes stale the day the price does.
"""
import collections
import json
import pathlib
import pathlib as _bs_pathlib  # noqa: E402 — the bootstrap's, see below
import statistics
import sys
import sys as _bs_sys  # noqa: E402 — the bootstrap's, see below

# --- scripts path bootstrap (canonical; the bootstrap guard enforces this) ---
# The two aliased imports sit above with the rest rather than under this marker:
# the sorter interleaves them either way, and a marker line introducing imports
# that are not there reads worse than a marker introducing the block that is.

_SCRIPTS_ROOT = next(p for p in _bs_pathlib.Path(__file__).resolve().parents
                     if p.name == "scripts")
for _sub in ("lib", "render", "check", "build", "ops", ""):
    _p = str(_SCRIPTS_ROOT / _sub) if _sub else str(_SCRIPTS_ROOT)
    if _p not in _bs_sys.path:
        _bs_sys.path.append(_p)
del _bs_pathlib, _bs_sys, _SCRIPTS_ROOT, _sub, _p
# isort: on

# The effort vocabulary is the schema's, never retyped here — a second literal
# copy is the drift the genre enum already grew once, one domain over.
import state_dir  # noqa: E402 — one answer for operator-owned stores
from trace_schema import ENUMS  # noqa: E402

ROOT = next((p for p in pathlib.Path(__file__).resolve().parents
             if (p / "SKILL.md").exists()),
            pathlib.Path(__file__).resolve().parents[2])

# NOT tracked (.gitignore, beside the other two .local.json files): a price is
# an operator machine's fact with a date on it, not the package's.
PRICES = state_dir.store("prices.local.json", root=ROOT,
                         in_repo=("evals", "prices.local.json"))


def board(traces):
    """Cost per content page — and only for runs that passed the quality line.

    A thin deck is cheap and worthless. An efficiency board that admitted one
    would reward exactly the behaviour every other check here exists to catch,
    so a run with a failing gate is not on the board at all.
    """
    rows = []
    for t in traces:
        if not t.get("closed_at"):
            continue
        if any(str(v).upper() == "FAIL" for v in (t.get("gates") or {}).values()):
            continue
        pages = t.get("content_pages") or 0
        out = t.get("output_tokens")
        if not pages or out is None:
            continue
        # Input tokens are most of the bill on a long context and were recorded
        # and read by nothing. Reported beside output rather than folded into
        # it: the two move for different reasons, and a single total hides
        # which one a change moved.
        inp = t.get("input_tokens")
        phases = t.get("phase_seconds") or {}
        # discussion and outline are not charged: the thinking a user was asked
        # to do is not the pipeline's cost, and counting it would push everyone
        # back toward the template path.
        charged = sum(v for k, v in phases.items() if k in ("build", "checks"))
        rows.append({"trace_id": t["trace_id"], "model": t.get("model"),
                     "effort": t.get("effort"), "content_pages": pages,
                     "tokens_per_page": round(out / pages, 1),
                     "input_tokens": inp, "output_tokens": out,
                     "opened_at": t.get("opened_at"),
                     "charged_seconds": charged})
    return rows


def matrix(traces):
    """-> (models, efforts, cells): the model × effort matrix (K1).

    Rows are models — free strings, '?' for a run that recorded none. Columns
    are the schema's effort vocabulary in its own order, plus '?'. A cell is
    the list of qualifying board rows, and qualification is `board()`'s: one
    implementation of the quality line, so a thin deck that cannot be on the
    board cannot set a median here either.
    """
    efforts = (*ENUMS["effort"], "?")
    cells: dict[tuple[str, str], list[dict]] = collections.defaultdict(list)
    for r in board(traces):
        cells[(r["model"] or "?", r["effort"] or "?")].append(r)
    models = sorted({m for m, _ in cells})
    return models, efforts, dict(cells)


def cell_cost(rows, price):
    """-> (median cost per content page, n) over the rows that recorded BOTH
    token counts; (None, 0) when none did.

    Computed here, at report time, and stored nowhere: `cost_usd` was deleted
    from the schema because a stored derivation goes stale the day the price
    does, while the tokens it derives from do not. Input tokens are most of
    the bill on a long context, so a row without them is excluded from the
    cost median rather than counted at zero — an understated cost reads as a
    cheaper build than the one that happened.
    """
    costs = []
    for r in rows:
        if r.get("input_tokens") is None:
            continue
        usd = (r["input_tokens"] * price["input_per_mtok"]
               + r["output_tokens"] * price["output_per_mtok"]) / 1e6
        costs.append(usd / r["content_pages"])
    if not costs:
        return None, 0
    return statistics.median(costs), len(costs)


def load_prices():
    """-> the local price table, or None when there is none.

    None is a state the caller must STATE, never imply — a board with no cost
    column and no explanation reads as a board that measured cost and found
    nothing. A table that exists but cannot be parsed is a hard exit for the
    same reason in the other direction.
    """
    if not PRICES.exists():
        return None
    try:
        return json.loads(PRICES.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"{PRICES} exists but is not JSON (line {e.lineno}: {e.msg}) "
                 f"— refusing to render a cost column from a table that "
                 f"cannot be read.")


def render_matrix(traces, prices):
    """-> printable lines for the matrix. Separated from main() so the two
    states a reader must be able to tell apart — an empty cell (drawn as —)
    and an absent price table (said in words) — are testable rather than
    trusted."""
    models, efforts, cells = matrix(traces)
    if not models:
        return []
    width = max(14, max(len(m) for m in models) + 2)
    colw = 20
    lines = ["", "model × effort — median output tokens per content page "
                 "(n = qualifying runs)", "",
             "  " + "model".ljust(width) + "".join(e.ljust(colw) for e in efforts)]
    for m in models:
        row = "  " + m.ljust(width)
        for e in efforts:
            cell_rows = cells.get((m, e))
            if cell_rows:
                med = statistics.median(r["tokens_per_page"] for r in cell_rows)
                row += f"{med:.1f} t/p (n={len(cell_rows)})".ljust(colw)
            else:
                row += "—".ljust(colw)
        lines.append(row)
    if prices is None:
        lines += ["", "  cost per page is not computed: no price table at "
                      "evals/prices.local.json. The traces store tokens, "
                      "never a cost, so without a price table there is no "
                      "cost to state."]
        return lines
    lines += ["", "  cost per content page — computed now from "
                  "evals/prices.local.json, stored nowhere"]
    for m in models:
        price = prices.get(m)
        if not price:
            lines.append(f"  {m.ljust(width)}no price for this model in the "
                         f"table")
            continue
        row = "  " + m.ljust(width)
        for e in efforts:
            cell_rows = cells.get((m, e))
            if not cell_rows:
                row += "—".ljust(colw)
                continue
            med, n = cell_cost(cell_rows, price)
            if med is None:
                row += "no input recorded".ljust(colw)
            else:
                row += f"${med:.2f}/page (n={n})".ljust(colw)
        lines.append(row + f"  priced {price.get('date', '?')}")
    return lines
