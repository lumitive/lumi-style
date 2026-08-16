#!/usr/bin/env python3
"""Emit a blind scoring sheet for C1–C7, in the language the reviewer reads.

**Blind means no mechanical number appears on it.** Someone who has seen the
machine's answer is no longer an independent measurement, and the agreement
study — the only reason a human score is recorded at all — exists because that
independence does. A test asserts the sheet leaks no metric id, no percentage
and no verdict.

The items come from `scripts/lib/rubric_items.py`, which reads the set out of
the rubric and holds the wording beside it. A sheet carrying its own item list
outlives the rubric: the previous one described H1–H6 for two releases after
C1–C7 replaced them.

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

from rubric_items import BANDS, CONDITION, DIM_TITLE, WORDING, items  # noqa: E402


def sheet(files, corpus_ids):
    # Words rather than percent signs: plainer, and the sheet asserts it carries
    # no measurement — a threshold written as a percentage reads like one.
    WORDS = {1.0: "全部满足", 0.75: "四分之三及以上", 0.5: "一半及以上",
             0.25: "四分之一及以上", 0.0: "其余"}
    bands = "　".join(f"{WORDS.get(f, f)} → {b} 分" for f, b in BANDS)
    lines = [
        "# 打分清单 · C1–C7",
        "",
        "每条证据项有三个答案：**是 / 否 / 不适用**。",
        "带括号条件的条目（例如“文档有执行摘要时”），条件不成立就选 **不适用** —— "
        "那不是跳过，是一次判断：这一条从来没有进入过这份文档的评判范围。",
        "",
        "**分数由勾选结果算出，不另外拍一个数**：",
        "",
        "> 分数 = 满足数 ÷ **适用数**（不适用的条目不进分母），再按下表取分：",
        f"> {bands}",
        "",
        "一个维度如果所有条目都不适用，这个维度记 **不适用**，不记 1 分。",
        "",
        "**这条规则的假设，写出来而不是藏起来**：同一维度内各条等权。"
        "这不太可能刚好为真 —— 如果分数和你读下来的感受对不上，"
        "它是第一个该被推翻的东西。",
        "",
        "**这份清单上不出现任何机器测出的数字。** 看过机器答案的人，"
        "就不再是一次独立的测量；而把人的分数记下来的全部意义，正在于它独立于机器。"
        "所以打分之前不要打开检查器的输出。",
        "",
        "**已经被 gate（硬性拦住发布的检查）守住的条目不列在这里。** "
        "让你去复核一件机器已经拦住的事，是把这个流程里最稀缺的资源花在已经定了的事情上。",
        "",
        "**协议里的两条**（`references/eval-rubric.md`）：读者打低的维度，"
        "在修它的那一轮自评不得高于三分；自评与你的分相差两分，触发一次复盘。",
        "",
    ]
    dims = items()
    for path, cid in zip(files, corpus_ids):
        p = pathlib.Path(path)
        lines += [f"## {cid} · {p.stem}", "", f"`file://{p.resolve()}`", ""]
        for did, title, rows in dims:
            lines += [f"### {did} · {DIM_TITLE.get(did, title)}", "",
                      "| 证据项 | 是 | 否 | 不适用 |", "|---|---|---|---|"]
            for marker, english in rows:
                text = WORDING.get((did, marker), english)
                cond = CONDITION.get((did, marker))
                if cond:
                    text = f"（{cond}）{text}"
                lines.append(f"| {text} | ☐ | ☐ | ☐ |")
            lines += ["",
                      "满足 ____ ÷ 适用 ____ ＝ **____ 分**　　**一句理由**：", ""]
        lines += ["---", ""]
    lines += [
        "## 打完之后",
        "",
        "把每个维度的「满足／适用」两个数给我就够了，分数我按上面的表算 —— "
        "这样两次打分不会因为心情不同而给出不同的数。理由那一句请一并给，"
        "它比分数更能说明该改什么。",
        "",
        "我会把结果转写进 `reviews/scores.json`，并带上上面的 corpus id。"
        "**那个 id 是 agreement study（一致性研究：比对机器指标与人的打分是否吻合）"
        "用来做关联的键**，没有它的记录无法和任何东西比较。",
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
