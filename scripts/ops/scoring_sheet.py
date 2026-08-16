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

from rubric_items import DIM_TITLE, WORDING, items  # noqa: E402


def sheet(files, corpus_ids):
    lines = [
        "# 打分清单 · C1–C7",
        "",
        "在浏览器里打开每份文档，逐条勾选证据项，**再由勾出来的结果给出一到五分**。",
        "顺序是这样定的：先勾条目、后给分，不是先有印象再补理由。",
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
            lines += [f"### {did} · {DIM_TITLE.get(did, title)}", ""]
            for marker, english in rows:
                lines.append(f"- [ ] {WORDING.get((did, marker), english)}")
            lines += ["", "**分数（一到五）**：____　　**一句理由**：", ""]
        lines += ["---", ""]
    lines += [
        "## 打完之后",
        "",
        "分数回给我时用什么形式都行 —— 勾好的清单、一段话，或者直接按维度写下来。",
        "我会把它转写进 `reviews/scores.json`，并带上上面的 corpus id。",
        "",
        "**那个 id 是 agreement study（一致性研究：比对机器指标与人的打分是否吻合）"
        "用来做关联的键。** 没有它的记录无法和任何东西比较 —— "
        "现有两条旧记录正是因为缺它，那个研究至今一行可关联的数据都没有。",
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
