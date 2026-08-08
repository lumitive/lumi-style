# LUMI Style — Agent Instructions (Codex entry)

> **lumi-style 0.1.364.** This file restates part of `references/`; where they
> disagree, `references/` wins. The stamp is checked against `CHANGELOG.md` — it
> went unstamped and unchecked until 0.1.352, and had already carried four
> versions of withdrawn rules.

You are producing content in LUMI's design language and writing style. LUMI is an
AI-native consulting firm serving a global audience. **The default output language
is American English** (since 0.1.333) and the default canvas is **light**; produce
another language or a dark canvas only when the user asks.

**Commit first, clarify second.** Land the concept fully, then apply the red
lines and the craft rules to make it clear. Starting inside the constraints and
decorating outward is measurably how you get work that is correct and lifeless:
through 0.1.344 this rule set ran 272 restricting lines against 12 inviting ones.

**Load order** (all files are in this repository):

0. `references/brand.md` — **read this first, and commit.** The water thesis, the
   two structural devices (the **field**: one mark per datum; the **waterline**: one horizon per page,
   air above and record below; the **ground**: continuous water and light behind
   the page, which may be decorative only because it cannot be counted),
   and the accelerators — the only place in this repository that says what to
   reach for. A field with nothing behind it is decoration and is checked for.
1. `references/writing-rules.md` — wording red lines, banned phrases, punctuation,
   number discipline, LUMI voice, de-AI-flavor checklist. Non-negotiable.
2. `references/storyline-templates.md` — pick the narrative skeleton by scenario
   (sales = value & future; consulting = PwC frame with assertive subtitles;
   internal analysis). Do this before writing.
3. `references/design-rules.md` + `tokens/` — visual rules and design tokens for
   any HTML/slides/chart output. Text uses the `--tx1..--tx4` ladder only;
   `--ln1..--ln3` is for rules, borders and fills and never carries text. Choose
   a page layout for the content (15 ship in `tokens/lumi-layouts.css`; §3's table
   is a reference, not a lookup). **Give every page one focal element** — a
   display number, a claim at display size, or a figure composed to dominate;
   which one is a decision for that page. **A table is for values**: prose in a
   grid is a layout error, so draw what the content actually is. Under a figure
   goes the number, its conclusion name and the source line, and nothing else.
   Embed the vendored assets rather than improvising: `scripts/embed_font.py`,
   `scripts/embed_icons.py`, `assets/vectors/`. **No size or fill floors** —
   0.1.340 withdrew the 82% page-fill floor and the 11px type floor, both invented
   without an ask, and the fill floor was satisfiable by stretching a table while
   four diagrams rendered at 40% of their cell.
4. `references/eval-rubric.md` — pre-delivery critic gate (structure before polish),
   the D-series and `inspect_layout.py` diagnostics (**judgements reported, never
   gating** — but an unmeasurable check exits 1 and says what it could not find),
   and H1–H6 self-scoring. Never self-score 5 before a reader has scored it, and
   always give the reason for the score, not just the number.

**Every page carries a commercial footer**: confidentiality terms and the
organisation's site on the left, `N / total` on the right. `check_design.py`'s
D12 is the only design check that fails the run, because it is a requirement on
the artifact rather than a judgement about a page. **Sales and marketing state
provenance once for the document** (cover and closing), not on every page;
consulting and internal analysis keep per-page sourcing. **One table per page** —
two grids side by side share no axis and can never align.

**A page is a fixed box.** Landscape is a 1280×720 stage, A4 a 794×1123 sheet,
each scaled to fit the window and letterboxed — never a box that takes the
window's shape. State the source once per page: on a single-figure page the line
under the figure is the page's source and the footer carries the page number.

**Rendered geometry decides, not declared CSS.** Run
`python3 scripts/inspect_layout.py <file>` and look at the contact sheet it
builds. A rule that loses on specificity is indistinguishable from no rule: one
had been in the layout file since 0.1.339, had never once applied, and left twelve
of fifteen multi-column pages with their columns out of line. Worse: a probe that
establishes the condition it verifies proves nothing — the page-height check
made the viewport 1280×720 and then measured the page against it, and reported
success for two releases while every page was 4:3 in a 4:3 window.

**And a check with nothing to examine must not report a pass.** Use the role
vocabulary `tokens/lumi-layouts.css` declares — `.eyebrow`, `h2.t`, `.sup`,
`.listhead`, `.gd`, `.cap .n`, `.band .k`, `.band .v` — or the consistency audit
silently has nothing to compare. The probe now prints `NOT MEASURED` with the
selector it wanted and exits 1; those lines come before every green one. Its
design judgements still gate nothing.

**Six hard red lines**: no invented facts (every number carries its source;
illustrative values are labeled 示意); no invented Chinese coinages (use the
standard Chinese term, or the English term directly when none exists); sales
narrative leads with value & future (honesty boundaries take exactly one page);
titles follow the contract "Topic: assertive subtitle" — each names its subject
and carries a verifiable fact, with no word ceiling and no bare-antithesis
titles, and all titles concatenated must read as a complete argument;
charts use one accent color, conclusion-style titles, and a source line;
AI never signs — money/safety conclusions never come from a language model.

**Workflow note**: after drafting Chinese prose, run a full-width punctuation pass
(Chinese text uses full-width ,:;? — half-width stays only inside code, URLs,
filenames, and pure-English runs). Then run the **mandatory de-AI-flavor pass**
(`references/writing-rules.md` §6 — word, sentence and structural moves plus the
two-pass audit; §6b de-translationese when the Chinese was translated from
English), and only then the pre-delivery checklist in the rubric. Measure both
halves rather than reading them: `python3 scripts/check_prose.py <file>` for
English prose, and `python3 scripts/check_design.py <file>` for any HTML
deliverable. D1–D4 and D6 gate; D5 is reported for you to judge.

Rule changes go through the feedback-review loop only (see `references/eval-rubric.md`)
and are recorded in `CHANGELOG.md` with a version bump.
