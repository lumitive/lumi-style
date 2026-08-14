# Consolidating the scattered rule surface — design record

Date: 2026-08-14 · Status: settled, implementing at 0.1.456 · Owner ask: the
rubric and the reference files read as scattered patches with no main line;
verify her reading critically, find every hidden metric constraint, and collect
them into `references/`.

## The verdict on her reading

Correct, with the blame distributed unevenly. The skeletons are the evidence:
`design-rules.md` orders its sections 1, 1c, 1d, 2, 3, 4, 4b, 5, **7, 6** and
numbers its chart rules 1-5, 6, 7, 7b, 7c, 7d, 7e, 8, 8b; the rubric's own
author patched it twice the day before rather than restructuring
(a "the table below is known wrong, read the checker" paragraph written INTO
the table). `writing-rules.md` and `brand.md` are largely coherent. The cause
is the repository's own convention 2: rules enter only through per-defect
retrospectives, so each lands as a patch at the site of its wound. The process
optimises every sentence's truthfulness and never the reader's path, and no
structural release has ever run.

## What the sweep found

- ~180 quantitative constraints on a deliverable; ~70 stated in no reference
  file (the dense clusters: `inspect_layout`'s probe tolerances, the prose
  population floors, the globe's entire numeric surface, the Evals bars).
- Whole rule families homed outside `references/`: the debug-mode contract
  (no occurrence of "debug" in any reference file), the parallel-build
  protocol, the figure grammar living as `region-palette.css` comments.
- Ten contradictions between copies, including one inside a single file.
- One withdrawn rule still printing (the 40% layout cap) and one never-argued
  advisory that fired on the accepted reference document.

## Decisions

**D1 — The numeric consolidation is generated, never hand-copied.**
`references/eval-inventory.md` is built by `scripts/build/build_eval_inventory.py`
from the checkers' own row tables (measured on the passing fixture), the
`deliverable_verdicts` source, discovered module constants, the thresholds file
and the token declarations, with a cross-check column naming which reference
file states each number — `CODE ONLY` being the finding the owner asked about.
The alternative was measured before being rejected: 26 releases fix a prose copy
disagreeing with code, and a hand-written inventory would be the largest such
copy ever created. Constants are DISCOVERED (regex over module-level ALL_CAPS
literals), not listed, so the generator has no hand list to rot.

**D2 — One exception to "references/ is hand-written", named where the
convention lives.** The convention's reason — assembled prose is worse prose —
does not apply to a table. CLAUDE.md states the carve-out beside the convention
it excepts, on the owner's instruction.

**D3 — Contradictions resolve by the standing rule: tokens win.** All ten
fixed; each fix quotes what the wrong copy said, because a silent correction of
a long-standing error reads as having always been right.

**D4 — The withdrawn 40% cap and the unargued five-layouts floor are removed,
not annotated.** A withdrawn rule that still prints is not withdrawn; an
advisory that flags the document the owner accepted is measuring its own taste.
D9 states the numbers; a reader judges.

**D5 — The prose-rule half of the scatter is recorded, not rushed.** GAP-006
(rules homed outside references/, and the now-false "strict subset" claim about
the core prompt) and GAP-007 (the structural reorder, content-frozen, with the
parity guards as the safety net) are ledger entries with named checks. Moving
the debug contract or reordering design-rules tonight would mean re-flowing
every §-citation under time pressure, which is how re-flows have historically
gone wrong here.

## Declined

**Renumbering design-rules' sections in this release.** Every checker and entry
point cites sections by number (§1c, §4, §7); a reorder is a pure-move release
of its own or it is a drift generator. Recorded as GAP-007's check.

**Putting the Chinese scoring sheet in the repo tree.** The english-only guard
caught it; it moved to the owner's documents folder where her local artefacts
live.
