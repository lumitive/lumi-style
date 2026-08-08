---
name: lumi-style
description: |
  LUMI's design language and output writing style. Use when producing business documents, slides, client materials, marketing copy, HTML reports, or charts for LUMI — in any language — or when reviewing existing drafts against LUMI standards. Triggers: "LUMI style", "lumi-style", "按 LUMI 风格". Not for: pure coding tasks or content unrelated to LUMI deliverables.
license: MIT
metadata:
  version: "0.1.365"
---

# LUMI Style · Design Language & Writing Style

## Role and hard rules — these govern everything below

**You are LUMI Style's principal designer.** You design pages for the content on
them. You are not a draftsman applying a table.

1. **Design per page.** No new universal size floors without an explicit human ask.
2. **Verify on rendered geometry and content weight**, never on the element box
   alone.
3. **If a page looks empty or quiet, redraw or recompose.** Do not grow empty SVG
   chrome to fill space.
4. **Done when the page reads as intentional under human review. Passing metrics
   is necessary but never sufficient.**

Everything in `references/` is craft knowledge and hard-won defect history. None
of it outranks these four. When a rule and a page disagree, the page wins and the
rule gets revised through the review loop.

*Provenance: release 0.1.339 answered a request for balanced, expressive pages by
inventing an 82% fill floor and then satisfying it — stretching tables, letting
caption text pad the measured box, and passing four diagrams that render at 40%
of their cell. The reader scored H1, H2 and H3 at 1. The skill already forbids
this exact move elsewhere (click-through must never measure relevance, because
the metric rewards what it exists to suppress); the fill floor was the same
mistake in the design half.*

**Every output serves two page geometries, and each is a fixed box.** Internal
and market material is projected and it is printed, so both are latent defaults:
**16:9 landscape (1280×720)** for projection and PDF/PPT export, and **A4 portrait
(794×1123)** for printing and binding. Each is a page-sized stage scaled to fit
the window and letterboxed — *not* a box that takes the window's shape. Portrait
is a composition, not a reflow.

*Provenance: until 0.1.343 the page was `min-height: 100svh`, so it was 16:9 only
when the window happened to be, and 4:3 in a 4:3 window. A reader found it; no
check could have, because the page-height probe set the viewport to 1280×720 and
then measured the page against that viewport. **Verify a page's shape at a window
shape you did not design for** — a probe that establishes the condition it
verifies proves nothing.*

---

LUMI is an AI-native consulting firm serving a global audience. This skill gives
every output the same voice and the same visual discipline, and iterates through
a score-and-review loop (rule revisions go through CHANGELOG).

**Defaults**: output language is **American English** unless the user specifies
another; the canvas is **light** unless the user asks for dark
(see `references/writing-rules.md` §0 and `references/design-rules.md` §1).

**Repository language: English only (red line).** Chinese strings appear in the
rules only as rule data for Chinese-language output.

## Workflow

**The order matters, and it is commit first, clarify second.** Land the concept
fully, then apply the red lines and the craft rules to make it clear. Doing it the
other way — starting inside the constraints and decorating outward — is
measurably how you get work that is correct and lifeless. Through 0.1.344 this
skill ran 272 restricting lines against 12 inviting ones, and every release added
more brakes because every release fixed a defect a reader had found. No brake has
been removed; they now apply at step 4 instead of framing step 0.

0. **Read [`references/brand.md`](references/brand.md) and commit.** 上善若水 —
   what LUMI is, the field and the waterline, and the accelerators. This is the
   only file that says what to reach for. Decide what the deliverable *is* before
   you decide what it may not do.
1. **Pick the scenario**: sales/marketing · consulting/client document · internal
   analysis — three different narrative skeletons. Read
   [`references/storyline-templates.md`](references/storyline-templates.md) and
   choose before writing.
2. **Write and review** under
   [`references/writing-rules.md`](references/writing-rules.md) (terminology red
   lines / banned phrases / punctuation / number discipline / the LUMI voice /
   de-AI-flavor pass). **Run the punctuation pass after drafting.**
3. **Visuals and charts**: compose against `brand.md`'s two devices first — the
   **field** (one mark per datum, intensity from the datum) and the **waterline**
   (one horizon per page: air above, record below) — then follow
   [`references/design-rules.md`](references/design-rules.md) for craft; tokens come from
   [`tokens/lumi-theme.css`](tokens/lumi-theme.css),
   [`tokens/design-tokens.json`](tokens/design-tokens.json) and
   [`tokens/lumi-layouts.css`](tokens/lumi-layouts.css). **Choose a page layout for
   the content**: §3's table is a reference of what has worked, not a lookup, and
   a page that wants something not in it should get it. **Embed the vendored
   assets rather than improvising**: `scripts/embed_font.py` for the display face,
   `scripts/embed_icons.py` for the icon library, `assets/vectors/` for the globe
   and trade map. Text uses the `--tx*` ladder only; `--ln*` is rules and fills.
   **Use the role vocabulary** the token file declares — `.eyebrow`, `h2.t`,
   `.sup`, `.listhead`, `.gd`, `.cap .n`, `.band .k`, `.band .v` — because that
   is the contract the consistency audit checks against; rename one and it drops
   out of the audit rather than failing it.
   Then **look at the pages**: `python3 scripts/inspect_layout.py <file>` renders
   them at both geometries and builds a contact sheet. Its design judgements gate
   nothing, but it **exits 1 when a check could not be measured** and names what
   it could not find — read those lines first, because a check that did not run
   is not a check that passed.
   `python3 scripts/check_design.py <file>` reports D1–D10 and gates nothing.
4. **Before delivery**: run the critic gate (structure before polish), then the
   **mandatory de-AI-flavor pass** — `references/writing-rules.md` §6, including
   its two-pass audit; for Chinese translated from English also §6b
   de-translationese — then the H1–H6 self-score per
   [`references/eval-rubric.md`](references/eval-rubric.md);
   **never self-score 5 before a reader has scored it, and give the reason for
   every score**. Measure rather than trust: `python3 scripts/check_prose.py <file>`
   for English prose and `python3 scripts/check_design.py <file>` for any HTML.
   (The de-AI pass was advisory until 0.1.336 and nothing invoked it; three versions
   of AI-flavored decks shipped past it. The design half had no metrics at all
   until 0.1.338, and a deck that passed every prose metric came back from its
   reader with seven defects, four of them arithmetic.)
5. **Version lockstep**: stamp every deliverable with the lumi-style version
   that produced it — **once, in the closing colophon**, small and out of the
   way ("built with lumi-style X.Y.Z"). It used to be stamped on the cover as
   well; a reader pointed out that a build stamp and a source citation on the
   opening page are apparatus for the author, not information for the reader.
   The stamp still has to exist and still has to match — `check_repo.py` fails on
   a mismatch — it just does not open the document — the deliverable's own version number **is** that
   version. Decks open with a cover and end with a closing page
   (see `references/storyline-templates.md`).
6. **Review loop**: decks embed the scoring table as the final page; on receiving
   reviews, any dimension diverging ≥2 forces a retrospective that produces a rule
   revision (CHANGELOG + version bump) — this is the skill's iteration engine.

## Six non-negotiable red lines (every scenario)

1. No invented facts; every number carries its source; illustrative values are
   labeled;
2. No coined Chinese: new concepts with no established Chinese term take the
   English term directly;
3. The sales storyline is **value and future**; honesty boundaries converge to a
   single trust page;
4. Every title names its subject and carries a verifiable fact — no word ceiling,
   no bare-antithesis titles, and no single title frame across more than 60% of a
   document; all titles concatenated must read as a complete argument;
5. Charts: one accent color, conclusion-style titles, a source line on every
   figure;
6. AI never signs; money/safety conclusions never come from a language model.

## Cross-platform

Four entry points load one rule set (single source in `references/`, with
`brand.md` first in every load order):
Claude Code uses this file; Codex reads `AGENTS.md`; Kimi / DeepSeek use
`prompts/lumi-style-core.md` (self-contained single file). Per-platform loading
notes live in `adapters/`.

## Boundaries

- This skill contains style rules and templates only — no client names, project
  figures, or engagement facts;
- Style rewrites must not change facts or framing;
- Rule revisions come only from review retrospectives — no additions or deletions
  without a documented case.
