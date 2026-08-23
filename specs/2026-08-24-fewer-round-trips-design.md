# The calls the package was charging for · design

Date 2026-08-24 · Status: **approved by the owner; shipped 0.1.590.**

## The owner's target

```text
我的目标是将 Claude code API 调用的次数比 Hermes 更少，因为 Claude code 的模型能力
和 Harness 的能力都比 Hermes + Deepseek V4 要强，如果达不到，你就要找原因！
```

The premise turned out to be half a measurement error, and finding that was the
first result. Her own instruction settled the order: fix the measurement, then
set the target.

## What the numbers actually were

| | reported | true |
|---|---|---|
| Claude Code API calls | 187 | **70** (build window), 76 (session) |
| Claude Code output tokens | 496,752 | **177,238** |
| Claude Code cache_read | 66.0M | **27.0M** |
| Hermes API calls | 37 | **130** (two sessions, whole table) |

Claude Code writes **one JSONL record per content block**, each repeating the
same `usage`; a per-record sum multiplies everything by the blocks-per-response
ratio, 2.67 on that build. Hermes keeps per-`(model, task)` rows and the reading
named the main row of one of two sessions.

Counted alike: **76 against 130**, tool calls 121 against 117, output 195k
against 325k. The target was already met on calls and on output. What Claude
Code genuinely lost was wall clock — 55 minutes against about 30 — and it did
that in ten rounds where Hermes took one.

`scripts/ops/session_cost.py` reads both platforms and states both traps in its
docstring. Its first run corrected this author's own hand-summed comparison,
which is the argument for it existing.

## Why ten rounds

Not the tools: **161 seconds of machine time across all ten**, against 1,604
seconds of model work between them. The gate-fixing loop was r1→r4 — three
rounds, exactly the owner's budget. Six more followed after the deck was green,
one of them a regression, and nothing in the package could tell the agent that a
round had moved nothing. The debug log records only errors, so a green round
leaves no trace of what it checked.

## The design

Every item is a round trip the **package** forced. That distinction is the whole
of it: an exhortation to be faster is not a fix, and the agent that spent those
calls was following the file.

The ten are listed in the CHANGELOG entry with what each cost. Three deserve the
reasoning kept:

**The figure box.** The scaffold's 640x239 is `p009-arrow-3d-01`'s proportion.
160 of the 206 units ink under 55% of it and the median fills 43% — the number
both round-3 decks reported as their visual share, and the page an owner picked
out by eye. The fix is to **say the number when the shape is chosen**, not to
resize anything: a scaffold that stretched the unit to move the metric would be
0.1.339's withdrawn fill floor in another costume, and this package exists partly
to remember that.

**The version placeholder.** A gating slot whose value the package always knew.
Removing it also removes the pattern from `AUTHOR_FILL`, because the
`scaffold slots` guard is explicit that a pattern guarding nothing misleads the
next reader — and a colophon naming no version is not unguarded, since
`gate_registry.held` reads it and an absent stamp is held to every gate.

**The brief.** It concatenates; it does not summarise. The card's own warning —
that an agent composing from it alone produces a document that passes everything
and says nothing — is repeated at the end of the brief, because the failure it
names is exactly the one a one-command brief invites.

## What this does not claim

That the wall clock will halve. Twenty of the fifty-five minutes were the model
authoring a 767-line fill script twice, and nothing here writes that script. The
`--emit-fill` scaffold considered for this release was left out: a skeleton
designed without a second real instance in front of it is convention 15's
warning, and there is now a geometry manifest to design it against. It is the
next round's work, and the round-4 numbers should say whether it is needed.
