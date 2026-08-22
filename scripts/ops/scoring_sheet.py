#!/usr/bin/env python3
"""Emit a blind scoring sheet for C1–C8, in the language the reviewer reads.

**Blind means no mechanical number appears on it.** Someone who has seen the
machine's answer is no longer an independent measurement, and the agreement
study — the only reason a human score is recorded at all — exists because that
independence does. A test asserts the sheet leaks no metric id, no percentage
and no verdict.

The items come from `scripts/lib/rubric_items.py`, which reads the set out of
the rubric and holds the wording beside it. A sheet carrying its own item list
outlives the rubric: the previous one described H1–H6 for two releases after
C1–C8 replaced them.

Usage
  scoring_sheet.py deck-a.en.html deck-b.en.html > sheet.md
  scoring_sheet.py --corpus-id A1 deck.en.html
"""
from __future__ import annotations

import argparse
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

from rubric_items import (  # noqa: E402
    CONDITION,
    DIM_TITLE,
    DIMENSION_NA,
    EXAMPLE,
    PURPOSE,
    WHERE,
    WORDING,
    items,
)


def sheet(files, corpus_ids):
    lines = [
        "# 打分清单 · C1–C8",
        "",
        "**每个维度只要两样：一个分数，一句话。** 八个维度，大约十五分钟。",
        "",
        "分数用 1 到 5，锚点是这三个，中间的 2 和 4 你自己拿捏：",
        "",
        "| 分 | 意思 |",
        "|---|---|",
        "| **5** | 这一条上没有可挑的地方 |",
        "| **3** | 还行，但有具体的毛病 |",
        "| **1** | 这一条上不行 |",
        "",
        "两个可以代替分数的答案：",
        "",
        "- **不适用** —— 这个维度对这份文档不成立（例如文档里没有图，C8 就不适用）。"
        "记不适用，不记一分；",
        "- **看不懂** —— 这道题在问什么，我读不出来。"
        "**这是给我的反馈，不是给文档的**：一道你读不懂的题，错在题不在文档，我会重写它。",
        "",
        "**那一句话比分数有用。** 分数只说“有问题”，一句话说的是改哪里。"
        "第一次真实使用时，「Agenda 页的标题和过渡页的标题不一致」这一句"
        "当天就能动手修，而分数不能。",
        "",
        "**打分之前不要打开检查器的输出。** 看过机器答案的人不再是一次独立的测量，"
        "而把人的分数记下来的全部意义，正在于它独立于机器。"
        "所以这份清单上不出现任何机器测出的数字。",
        "",
        "每个维度末尾折着几条提示。**它们是卡住的时候翻的，不是要你逐条回答的表格。**"
        "上一版清单要求逐条打勾，那是把给机器裁判用的方法用到了人身上——"
        "在原始研究里，人本来就是基准，人没有在勾清单。",
        "",
    ]
    dims = items()
    for path, cid in zip(files, corpus_ids):
        p = pathlib.Path(path)
        lines += [f"## {cid} · {p.stem}", "", f"`file://{p.resolve()}`", ""]
        for did, title, rows in dims:
            na = DIMENSION_NA.get(did)
            lines += [
                f"### {did} · {DIM_TITLE.get(did, title)}",
                "",
                f"- **这一条防的是**：{PURPOSE.get(did, '')}",
                f"- **看哪里**：{WHERE.get(did, '')}",
                f"- **这样答就够**：{EXAMPLE.get(did, '')}",
            ]
            if na:
                lines.append(f"- **{na}**，这个维度直接写「不适用」。")
            lines += [
                "",
                "**分数**：　　　　　（1–5，或「不适用」「看不懂」）",
                "",
                "**一句话**：",
                "",
                "<details><summary>卡住的时候可以翻这几条（不用逐条回答）</summary>",
                "",
            ]
            for marker, english in rows:
                text = WORDING.get((did, marker), english)
                cond = CONDITION.get((did, marker))
                if cond:
                    text = f"（{cond}）{text}"
                lines.append(f"- {text}")
            lines += ["", "</details>", ""]
        lines += ["---", ""]
    lines += [
        "## 打完之后",
        "",
        "把清单发回来就行。八个分数、八句话，我转写进评分库"
        "（`review_scores.py --check` 会打印它在这台机器上的位置），"
        "带上上面的 corpus id —— **那个 id 是一致性研究（比对机器指标与人的打分是否吻合）"
        "用来做关联的键**，没有它的记录无法和任何东西比较。",
        "",
        "**标了「看不懂」的维度请告诉我。** 那是这份清单自己的缺陷清单，"
        "上一版有五条被这样标出，其中两条把一个维度拖到了一分，而那份文档并没有欠下这一分。",
        "",
    ]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("files", nargs="+")
    ap.add_argument("--corpus-id", action="append", dest="corpus_ids",
                    help="one per file, in order; defaults to A1, A2, …")
    a = ap.parse_args()
    ids = a.corpus_ids or [f"A{i}" for i in range(1, len(a.files) + 1)]
    if len(ids) != len(a.files):
        sys.exit("give one --corpus-id per file, in order")
    print(sheet(a.files, ids))


if __name__ == "__main__":
    main()
