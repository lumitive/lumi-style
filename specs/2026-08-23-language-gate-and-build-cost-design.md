# The output language becomes a record, and the build becomes one command · design

Date 2026-08-23 · Status: **approved by the owner; shipped 0.1.587.**

Written from a production validation run on the Hermes Terminal Agent
(DeepSeek V4), the first on real hardware with an owner-supplied source
document. Two defects came out of one build, and they are unrelated except in
their shape: in both, the cheap path won.

## The owner's complaint

```text
1，我在 Hermes Terminal APP 实际验证，采用 Deepseek V4 slash 模型，我发现
LUMI Style Skill 输出有几个严重BUG
- 输入是英文，LUMI Style 默认要求也是英文，为什么输出的是中文
- 消耗太多 Tokens，就 10 页的 Slides 消耗太过的费用
2. 我的要求是：检查 Skill 的工作流程，我感觉是有大量的重复工作导致消耗大量
Tokens。我希望的目标是：Token 节省 90%，时间节约 90%
```

## What was measured

The source document is **54 KB of English with zero CJK characters**. The
owner's instruction was typed in Chinese. The deck came out wholly Chinese,
`<html lang="zh-Hans">`.

Read from the host's own session store (`~/.hermes/state.db`), not estimated:

| | |
|---|---|
| API calls | **460** (main 338 · background_review 30 · approval 85 · other 7) |
| cache_read tokens | **105,400,000** |
| Mean context per main-task call | **292,000** |
| terminal tool calls | **389** |
| `inspect_layout.py` invocations | **64**, at 22.0s each |
| `check_deliverable.py` invocations | **6** |
| Loop flags used across 70 expensive renders | **0** |
| Wall clock, first command to last check | **~50 minutes** |
| Billed, build segment only | **¥4.35** |

Reading before the first page is written, if SKILL.md is followed literally:
**322 KB ≈ 98,000 tokens**, or ≈148,000 with the two files it pressures the
agent into. Every call re-sends it.

## Defect 1 · The language rule lost to the gate that enforced half of it

The rule is correct and forceful in four places, and catalogued as **FM-18**
after the first time it broke. This was the second.

The build **was** stopped. `M12` fired — visible Chinese in a document
declaring `lang="en"`. The recorded fix was to change the attribute to
`lang="zh-Hans"`. `check_prose.py` computes `cjk = visible_cjk(...) if
language == "en" else None`, so a document declaring Chinese is `n/a` to M12.
One attribute, and a gating failure became a pass.

Nothing else in the package asked whether the document should have been
English. `evals/rule-coverage.json` RC-431 claimed it did — mapping "Write in
American English when the user specifies no language" to **M12, gates: yes** —
and `references/page-contracts.md` printed that claim, so an agent reading the
generated contract index was told a machine held a rule no machine could see.

The proximate trigger was outside this repository: a machine-curated companion
skill on that host carried `Chinese input + Chinese-speaking user -> zh-Hans
output` as an operational instruction. That is worth recording precisely
because it is not fixable from here. A host can re-curate one tomorrow.

**So the fix has to be mechanical.** A rule survives only in the packages that
read it; a gate survives whatever else the host is loading.

### The design

A deliverable in any language but English **records the ask** —
`data-lang-asked="<code>"` on `<body>`, written by `new_deck.py --lang <code>
--lang-asked` — and **M16** fails one that does not. English carries no record
because English is the default, and reads `ok` rather than `n/a`: a metric that
goes quiet on the ordinary case teaches a reader to skip the row.

Relabelling stops being an escape and becomes a move between two questions.

Rejected: making M12 itself refuse Chinese. That would ban Chinese output,
which is a legitimate deliverable the owner asks for regularly. The question is
not which language, it is whether anybody asked.

## Defect 2 · The workflow prescribed the expensive path

`check_deliverable.py` already runs prose, design, layout, privacy and the
Evals in one process, with the browser rendering while the text checks run.
SKILL.md recommended it and then described each instrument again in the
imperative, so an agent following the file ran both. `check_privacy` was
prescribed as a standalone step *and* run inside — a duplicate the skill
specified.

The `inspect_layout` count has a structural cause that is ours:
`check_deliverable` forced `--no-sheet`, so the contact sheet — the artifact
this package calls the last gate — was unreachable from the one-command path,
and the only way to get it was to run the slow instrument again.

`--iterate` and `--no-sheet` appear nowhere in SKILL.md, `references/` or
`AGENTS.md`. The sentence beside the command read "Pass it the file and nothing
else", written about `--geometry` and followed as a ban on every flag.

And nothing in `scripts/` ran scaffold → fill → embed → check, so each stage
cost an API round trip whether or not anything had changed. Debug mode added
one turn per command on top, by contract.

### The design

- `scripts/ops/build.py` runs the four stages in one process and writes the
  debug log as a side effect. It invents **no** page-content format: the fill
  script is the author's own, which is what real builds converged on. A schema
  designed without a real instance in front of it is convention 15's warning.
- `check_deliverable.py --sheet`, and `inspect_layout`'s JSON returns the sheet
  path, which it never did — the one-command path could otherwise build the
  last gate and not say where it landed.
- `references/build-card.md`, generated from the registers and the tokens:
  the decidable half of the rules at ≈5,900 tokens, `--check` in CI, every line
  carrying its `file:line`. It states on its own face that it is not the rules
  and that an agent reading only it will produce a document that passes
  everything and says nothing — which is what five conformance rounds produced.
- `debug_log.py validate` fails when a command's last run is red and nothing
  ran it clean afterwards, unless an error cites an OPEN `KNOWN_GAPS` entry.
  The build above recorded two `exit 1` commands as its final readings and its
  report called them green.
- `new_deck.py --pages` defaults to the outline's section count. It defaulted
  to 6 whatever the plan said, so a ten-title outline silently emitted six
  content pages.

## What this does not fix

Recorded rather than claimed. The deck the run produced is formally immaculate
and analytically thin: ten figures with no source line at all (red line 5, and
nothing reads it — **GAP-030**), the `.take` implication rung deleted from all
ten content pages while every gate stayed green (**GAP-031**), seven of ten
figures carrying zero text, one shape construct used ten times, visual share at
26 against a floor of 50, and `M11` at 66.7% — which is red line 4 and reports
rather than gates.

Those are the next round's material. This one is about the two the owner named.
