#!/usr/bin/env python3
"""The C1–C7 evidence items, and their wording in the reviewer's language.

Two things live here because they must not drift apart:

`items()` reads the item SET out of `references/eval-rubric.md`. The rubric is
the authority on which items exist, and a scoring sheet that carried its own
list would outlive the rubric — the previous sheet described H1–H6 for two
releases after C1–C7 replaced them.

`WORDING` is the Chinese rendering, keyed by (dimension, marker) so it says
nothing about which items exist. It is the price of writing the sheet in the
language the reviewer reads; the parity guard in `check_repo.py` is the price
of the wording table, and it fails on an item with no wording and on a wording
whose item is gone.

It lives in `scripts/lib/` rather than beside the CLI for the reason the trace
schema does: the guard imports it, and `check_repo` may not reach into
`scripts/ops/` — the emergency-merge path would then run the pull request's own
copy of the thing being checked.

The prose follows P-3: plain, calm, concrete, and a term explained where it
appears rather than assumed. That is why 连读, MECE and so-what each carry their
explanation inline instead of in a glossary the reader has to hold in their head.
"""
from __future__ import annotations

import pathlib
import re

# Tolerant on purpose: the parity guard executes this module inside a synthetic
# tree that may carry no SKILL.md, and a module that refuses to load there would
# make the guard report "does not load" for a tree that is fine.
ROOT = next((p for p in pathlib.Path(__file__).resolve().parents
             if (p / "SKILL.md").exists()),
            pathlib.Path(__file__).resolve().parents[2])

DIM_TITLE = {
    "C1": "统领信息 —— 读者先知道结论",
    "C2": "故事线完整性 —— 标题连起来是一条论证",
    "C3": "页面论证 —— 一页立一个论点",
    "C4": "证据与来源",
    "C5": "类型完备性",
    "C6": "可行动性",
    "C7": "专业完成度与读者效率",
}

WORDING = {
    ("C1", "①"): "第一个正文页上，能一句话引用出全篇的统领结论",
    ("C1", "②"): "证据出现之前，读者已经知道它在回答哪个问题（先摆结论，或先讲清情境再提问，两种都算）",
    ("C1", "③"): "执行摘要一页以内，两分钟读完",
    ("C1", "④"): "摘要的每一条都对应正文的一节，条数相同、顺序一致",
    ("C1", "⑤"): "没有只报数量的摘要条目 —— 不写“存在三个问题”而不说是哪三个",
    ("C2", "①"): "连读检验：把全部标题按顺序抄下来连着读，是一条没有缺口、没有重复、没有跳跃的论证",
    ("C2", "②"): "论证主体里，只报主题不下判断的标题（“市场概览”这类）数量为零",
    ("C2", "③"): "每一组是两到五条同类同层级的观点，而且你能说出这一组是按什么排序的",
    ("C2", "④"): "MECE 抽查（相互独立、完全穷尽）：试着指出任意一组里的重叠或缺漏，记下找到或没找到",
    ("C3", "①"): "一页一个论点：说不出这一页在论证的第二个独立结论",
    ("C3", "②"): "标题里的断言（包括其中的数字）能在本页的证据里被验证",
    ("C3", "③"): "so-what 检验（“所以呢”）：页面上每个元素都能用一句话说清它怎么支撑标题，说不出来的元素数量为零",
    ("C3", "④"): "图形的形式对得上标题所做的比较：比构成、比排序、比时序、比频率、比相关",
    ("C3", "⑤"): "非数据图形的族语义在内容上成立：漏斗的值确实递减，两轴矩阵的两个轴确实相互独立",
    ("C3", "⑥"): "每张图脱离正文也能读懂：标题即结论、坐标轴与单位齐备、图例可辨、数量级标明",
    ("C4", "①"): "来源行具名到数据集或报告，不只写“分析”",
    ("C4", "③"): "估计值与实际值在视觉上可区分，关键假设写在估计出现的地方",
    ("C4", "⑤"): "局限与边界写在读者会遇到它的位置，不省略、不集中丢进附录",
    ("C5", "①"): "对照这一类文档的典型结构清单逐项核对（只报告，不拦发布）",
    ("C5", "②"): "支撑性材料进附录，正文没有凑页数的内容",
    ("C5", "③"): "状态类文档：每个红灯或黄灯项都配一个具体的请求",
    ("C5", "④"): "结尾是带负责人和时间的下一步，不是把前面复述一遍",
    ("C6", "①"): "每条建议都指明谁做、做什么、什么时间或多大量级",
    ("C6", "②"): "文档明说它在请求读者什么：批准、决策、拨款，还是知悉",
    ("C6", "③"): "对建议的主要风险或反面意见被点名并回应",
    ("C6", "④"): "建议配了成功度量或检查点",
    ("C6", "⑤"): "写下一个决策者一定会问、而文档没有回答的问题；写不出来就算通过",
    ("C7", "①"): "任意一页大约一分钟内可理解（抽五页计时）",
    ("C7", "②"): "术语统一：每个关键概念全篇只有一个叫法（抽查三个）",
}

_MARKERS = "①②③④⑤⑥⑦⑧"


def items(rubric: pathlib.Path | None = None):
    """-> [(dimension, title, [(marker, english), ...])], struck items dropped.

    A struck item names the gate that already holds it, and asking a reviewer to
    re-check something a gate holds spends the scarcest resource in this process
    on nothing.
    """
    path = rubric or (ROOT / "references" / "eval-rubric.md")
    text = path.read_text(encoding="utf-8")
    start = text.index("## Human dimensions")
    end = text.index("### 7.3") if "### 7.3" in text else len(text)
    out = []
    for m in re.finditer(r"^### (C\d) · ([^\n·]+)(?:·[^\n]*)?$(.*?)(?=^### C\d|\Z)",
                         text[start:end], re.M | re.S):
        rows = []
        for row in re.finditer(rf"^\| ([{_MARKERS}]) (.+?) \|", m.group(3), re.M):
            body = re.sub(r"\*\*|`|\[outline\]", "", row.group(2)).strip(" ·")
            rows.append((row.group(1), body))
        if rows:
            out.append((m.group(1), m.group(2).strip(), rows))
    return out


def dimensions(rubric: pathlib.Path | None = None):
    """-> [(dimension, title, ["<marker> <english>", ...])].

    The marker-prefixed form the guard and the sheet both read. `items()` keeps
    the pair form for anything that wants the two apart.
    """
    return [(did, title, [f"{marker} {english}" for marker, english in rows])
            for did, title, rows in items(rubric)]
