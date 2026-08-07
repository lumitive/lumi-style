# LUMI Style — Agent Instructions (Codex entry)

You are producing content in LUMI's design language and writing style. LUMI is an
AI-native consulting firm serving a global audience. **The default output language
is American English** (since 1.3.0) and the default canvas is **light**; produce
another language or a dark canvas only when the user asks.

**Load order** (all files are in this repository):

1. `references/writing-rules.md` — wording red lines, banned phrases, punctuation,
   number discipline, LUMI voice, de-AI-flavor checklist. Non-negotiable.
2. `references/storyline-templates.md` — pick the narrative skeleton by scenario
   (sales = value & future; consulting = PwC frame with assertive subtitles;
   internal analysis). Do this before writing.
3. `references/design-rules.md` + `tokens/` — visual rules and design tokens for
   any HTML/slides/chart output. Text uses the `--tx1..--tx4` ladder only;
   `--ln1..--ln3` is for rules, borders and fills and never carries text. Nothing
   below 11px. Pick a page layout from the §3 selection table (15 ship in
   `tokens/lumi-layouts.css`); a page fills at least 82% of its height, and if it
   cannot, the layout is wrong rather than the padding. Embed the vendored assets rather than improvising:
   `scripts/embed_font.py`, `scripts/embed_icons.py`, `assets/vectors/`.
4. `references/eval-rubric.md` — pre-delivery critic gate (structure before polish),
   D1–D6 design metrics and H1–H6 self-scoring. Never self-score 5 before a reader
   has scored it, and always give the reason for the score, not just the number.

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
