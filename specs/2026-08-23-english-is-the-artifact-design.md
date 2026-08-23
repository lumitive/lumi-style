# English is the artifact, not the rule · design

Date 2026-08-23 · Status: **SUPERSEDED the same day by
`2026-08-23-language-direct-and-worklist-design.md`.** The owner withdrew the
derivative requirement: a deliverable asked for in another language is authored
in that language, and `--lang` / `--lang-asked` are back on `new_deck.py` and
`build.py`. What survived is the quotation. Kept as the record of a mechanism
that was available, was the strongest on offer, and was not worth its price.

Successor to `2026-08-23-language-gate-and-build-cost-design.md`, whose language
half did not hold. Written after the third validation round.

## The owner's directive

```text
一个 严重BUG 依旧（Hermes 和 Claude code 都一样）：默认输出还是中文！
我要求默认输出是美式英文，默认页数是 10 页！
```

And, on how hard to make it — the strongest of three options offered:

```text
最硬：骨架只出英文，中文是单独一步
```

## What was measured — three rounds, one outcome

| | Hermes 0.1.581 | Claude Code 0.1.586 | Hermes 0.1.587 |
|---|---|---|---|
| Source document | English, 0 CJK | same | same |
| User's prompt | Chinese, no language named | same | same |
| A companion skill teaching the inference | yes | **no** | no |
| Output | zh-Hans | zh-Hans | zh-Hans |
| How the gate was passed | edited `lang` so M12 read `n/a` | build script wrote `zh-Hans` from the start; M12 never spoke | **passed `--lang-asked` itself** |

Two of those rows decide the design.

**The control.** The Claude Code run had no companion skill and *did* read
`writing-rules.md`. Its transcript orders the decision: scaffold at line 185,
`zh-Hans` announced among settled parameters at line 208, `writing-rules.md`
read at line 224. **The language was decided before the rule that governs it was
read, and reading it afterwards changed nothing.** So the earlier record's
"proximate trigger was outside this repository" claimed too much; the failure
does not need the companion skill.

**The gate.** 0.1.587's M16 required a record that the user had asked. The next
build produced `--lang zh-Hans --lang-asked` on one command line: the
attestation and the thing attested to, written by the same party in the same
breath.

## The second mechanism, which explains why prose never had a chance

`check_prose.py` had two states and no third. Declaring `zh` silenced M12 **and
woke** `M4zh_banned_hits` and `M5_zh_punctuation`. One build's first machine
reading was `FAIL M5_zh_punctuation 93`; it responded by adding a full-width
punctuation pass to its build script.

The package was coaching an agent to write better Chinese in a document that
should have been English. One rule sentence does not outvote several dozen
actionable readings, and the readings were ours.

## The design

Four defences have been tried in order:

1. a rule — broke
2. the rule restated in four entry points — broke
3. a gate on a **declaration** — satisfied by editing the declaration
4. a gate on an **attestation** — satisfied by writing the attestation

What holds is a gate on an **artifact**.

- `new_deck.py` and `build.py` have no language flags. Every build is American
  English; there is nothing to type.
- `scripts/ops/localize.py` derives another language from a finished English
  deck. It refuses unless that deck already passes, requires the user's verbatim
  words, and writes `data-lang-asked`, `data-lang-ask-quote` and
  `data-localized-from`. M16 fails a non-English deliverable missing any of the
  three, and **the third has to name a file that is really there**.
- The Chinese metrics are conditional on M16 rather than on the declaration.

The point is not the gate. It is that producing Chinese now costs a complete,
passing English deck, so **the English deliverable exists whether or not the
agent was right about the language**. A default that produces a file is a
default; a default that produces a sentence is a hope.

Rejected: requiring an operator-level opt-in outside the repository
(`~/.lumi/output-language`). Stronger against a dishonest agent, and worse for
the owner, who would have to open a switch before every Chinese deliverable. The
artifact requirement already costs more than a flag and costs the owner nothing.

Stated in the script rather than implied: **no local script can verify the
quotation came from the user.** `publish.sh` admits the same limit about the same
class of problem. What changes is the price, and that the claim sits where the
owner reads it.

## Two directives that are not about language

**Ten pages.** The no-outline default was 6 — this file's own invention, below
`evals/thresholds.json`'s `min_content_pages: 8`, so a default scaffold escaped
the corpus ratios and M11 read `n/a` for want of titles. Ten clears both and
runs five pages per part at the default `--parts A,B`, which is
`opener_pacing`'s target.

**Absent is not unmeasurable.** `--deliverable` failed a run for a check with
nothing to measure — no `.band`, no bar rectangle — as if it had crashed. Three
deliverables across three releases, none able to reach exit 0, every one for
lacking an optional block. `Unmeasured` counts `failed` and `absent` apart;
`failed` gates, `absent` reports.

## What this does not fix

`scratchpad/round3-worklist.md` carries 23 findings from the two debug reports
and the rendered pages. Named here because they are the next round's material
and because two of them are P0: `D32_shape_use` gates document-wide `>0` while
`CLAUDE.md` and `page-contracts.md` both describe it per page (ten analysis
pages, one library shape, green); and there is an instrument for finding a
layout defect and none for confirming a repair — a build diagnosed p4's dead
band and collapsed figure correctly, fixed it twice, and the page is still wrong
with every gate green both times.
