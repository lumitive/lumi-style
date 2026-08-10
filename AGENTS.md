# LUMI Style — Agent Instructions (Codex entry)

> **lumi-style 0.1.405.** This file restates part of `references/`; where they
> disagree, `references/` wins. The stamp is checked against `CHANGELOG.md` — it
> went unstamped and unchecked until 0.1.352, and had already carried four
> versions of withdrawn rules.

You are producing content in LUMI's design language and writing style. LUMI is an
AI-native consulting firm serving a global audience. **The default output language
is American English** (since 0.1.333) and the default canvas is **light**; produce
another language or a dark canvas only when the user asks.

**One colour, one meaning — with one stated exception.** In the globe's region
form, hue says *which region*, and nothing else. That is an owner directive; it
works only because those hues are declared to carry no data meaning, the way the
light ramp already is, and because every coloured region also carries a label or
a legend entry. Semantic colour is untouched. Outside that figure, a colour that
means two things is a defect.

**Commit first, clarify second.** Land the concept fully, then apply the red
lines and the craft rules to make it clear. Starting inside the constraints and
decorating outward is measurably how you get work that is correct and lifeless:
through 0.1.344 this rule set ran 272 restricting lines against 12 inviting ones.

**Study the input first; questions come once or not at all.** Read everything
the user supplied and work from the reader's side of the deliverable — the
first-principles question is what this reader does differently after reading. When a
required input is missing or two requirements conflict, batch every question
into one round before generating; otherwise state your assumptions in the
delivery note and proceed — one clear prompt should normally produce a finished
document. Write a finished document to `Documents/LUMI-Style/` under the user's
home directory unless the user names another, and **ask before creating that
folder**; an export lands beside the document it was made from, and because the
folder is shared, a filename carries the document's own name and version. Run independent pages in parallel where your platform allows, and when
expected generation time passes ten minutes, say so before starting. Before
delivery, the **red-team pass** rides the critic gate: read the draft as its
most skeptical reader, and treat over-design as a finding, not a virtue.

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
   internal analysis; training = enabling a team to do something). Do this before
   writing. A deck opens with a cover and ends with a closing page, each carrying
   the same single vector mark, and **every part boundary gets a lime opener
   page** — about five content pages between openers is a pacing target, reported
   and never gated.
3. `references/design-rules.md` + `tokens/` — visual rules and design tokens for
   any HTML/slides/chart output. Text uses the `--tx1..--tx4` ladder only;
   `--ln1..--ln3` is for rules, borders and fills and never carries text. Choose
   a page layout for the content (16 ship in `tokens/lumi-layouts.css`; §3's table
   is a reference, not a lookup). **Give every page one focal element** — a
   display number, a claim at display size, or a figure composed to dominate;
   which one is a decision for that page. **Every content page carries at least
   one visual block, and the target share of its area follows the genre — about
   half for sales, marketing and consulting, about a third for training** — the
   checks report both, and neither is a floor. A reference page (glossary,
   scoring, boundaries) is exempt and declares it with `data-role="apparatus"`,
   up to about one content page in five. **A page on the sheet carries more than
   a page on the slide**: a portrait content page adds a second content block
   beside its centerpiece — what to notice, the steps, the caution, the worked
   example — and one marked key point at the standard tier, which does not raise
   the tier-one callout budget. A floor on the page's blocks, never on
   the support line, and a page that cannot hold both becomes two pages.
   A figure's name holds one line. **A table is for values**: prose in a
   grid is a layout error, so draw what the content actually is. Under a figure
   goes the number, its conclusion name and the source line, and nothing else.
   Embed the vendored assets rather than improvising: `scripts/embed_font.py`,
   `scripts/embed_icons.py`, `assets/vectors/`. **No size or fill floors** —
   0.1.340 withdrew the 82% page-fill floor and the 11px type floor, both invented
   without an ask, and the fill floor was satisfiable by stretching a table while
   four diagrams rendered at 40% of their cell.
4. `references/eval-rubric.md` — pre-delivery critic gate (structure before polish),
   the D-series and `inspect_layout.py` diagnostics (**design judgements
   reported, never gating** — but an unmeasurable check exits 1 and says what it
   could not find, and `--deliverable` exits 1 on the ten findings that are
   decidable rather than aesthetic),
   and H1–H6 self-scoring. Never self-score 5 before a reader has scored it, and
   always give the reason for the score, not just the number.

**Every page carries a commercial footer**: the seal-red `shield` handling
marker, the confidentiality terms and the organisation's site on the left,
`N / total` on the right (the marker inverts on the lime opener).
`check_design.py`'s D12 is one of three checks there that fail the run, because
it is a requirement on the artifact rather than a judgement about a page. Two others join it: **D14, no slot you left for
yourself may reach the reader** — `[TO FILL]`, `[TBD]`, `{{name}}`, an empty
bracket pair — and **D15, no footer may cite a file path**, because a source line
names something a reader can act on and not a file on the machine that built the
deck. **And an English deliverable must be in English**: `check_prose.py`'s M12
fails on Chinese in reader-visible text when the document declares English, with
`<code>` the exemption for a name that must appear in Chinese. It asks whether the document is finished, and nothing else
in this package can see one: a placeholder is not a banned phrase, not a colour,
and takes up exactly as much room as the text that should have replaced it.
**Sales and marketing state
provenance once for the document** (cover and closing), not on every page;
consulting and internal analysis keep per-page sourcing. **One table per page** —
two grids side by side share no axis and can never align.

**A page is a fixed box.** Landscape is a 1280×720 stage, A4 a 794×1123 sheet,
each scaled to fit the window and letterboxed — never a box that takes the
window's shape. **A deliverable is designed for ONE geometry and declares it**
(`<body data-geometry="landscape">`): sales, marketing and consulting lead 16:9,
training leads A4 portrait, and **when the request settles neither the genre nor
the format, ask before generating.** A second geometry is a second composition
in its own file, never the same file viewed sideways. **Exports render at the stage**
(`scripts/export_pdf.py`): PDF is vector, one page per `.page`; rasters take a
device-pixel multiplier — **default 3 (4K from the landscape stage), floor 2
(2K), refused below** — and the scale never changes the CSS stage, whose zoom
adapts to the reader's window and pixel density natively. State the source once per page: on a single-figure page the line
under the figure is the page's source and the footer carries the page number.

**Rendered geometry decides, not declared CSS.** Run
`python3 scripts/inspect_layout.py <file>` and look at the contact sheet it
builds; before handing the file over, run it again with **`--deliverable`**,
which exits non-zero on collision, content spill, page height, hidden content, a
wrapped footer, an overspent title reserve, a role split and a lost datum. A clean run there is not
a verified document — it means nothing measurable is broken. A rule that loses on specificity is indistinguishable from no rule: one
had been in the layout file since 0.1.339, had never once applied, and left twelve
of fifteen multi-column pages with their columns out of line. Worse: a probe that
establishes the condition it verifies proves nothing — the page-height check
made the viewport 1280×720 and then measured the page against it, and reported
success for two releases while every page was 4:3 in a 4:3 window.

**And a check with nothing to examine must not report a pass.** Use the role
vocabulary `tokens/lumi-layouts.css` declares — `.eyebrow`, `h2.t`, `.sup`,
`.listhead`, `.gd`, `.cap .n`, `.band .k`, `.band .v`, and the block
patterns `.key`/`.red`, `.card`/`.ledname`/`.verdict`, `.swap .no`/`.swap .yes`,
`.vow`/`.vn`/`.vt`/`.vw`, `.tag`, `.grades`, `dl.gloss` — or the consistency
audit silently has nothing to compare. **The eyebrow follows its contract**: the
page's subject icon, then `PART <letter> · <this page's own label>` — apparatus,
deliberately uniform, never counted as a title. The probe now prints `NOT MEASURED` with the
selector it wanted and exits 1; those lines come before every green one. Its
design judgements still gate nothing.

**A title block that does not fit gets shorter text, never a clamp.** `.lede`
reserves its height and the reserve is a ceiling: a title needing three lines
gets rewritten, not a taller block. `-webkit-line-clamp` or `overflow: hidden`
there deletes lines from a client page while leaving every geometric check clean,
because hidden text produces no spill, no collision and no overflow. The probe
reports the overspend and the clamp separately.

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
deliverable. **D12, D14 and D15 gate; every other D-metric is reported for you to
judge** — a page is done when a human reads it as intentional, and a threshold
satisfiable without improving the page ends the looking. (This line claimed
"D1–D4 and D6 gate" for eight releases, naming four metrics that never did and
omitting the one that always has. A restatement nothing compares against is the
drift this file exists to concentrate, not to escape.)

Rule changes go through the feedback-review loop only (see `references/eval-rubric.md`)
and are recorded in `CHANGELOG.md` with a version bump.
