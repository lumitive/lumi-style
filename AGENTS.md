# LUMI Style — Agent Instructions (Codex entry)

> **lumi-style 0.1.507.** This file restates part of `references/`; where they
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

**Two entry paths, and the build records which** (`references/operating-rules.md`
§6 is where this is true). **Path A** is a discussion in four beats whose order
cannot be reversed — free statement, questions, advice, **storyline review** —
and beat 4, the review of titles and order before anything is built, is the
only defence completeness has, because C5 reports and never gates. **Path B**
starts from a recipe and is what most real builds use. **Both are held to the
current rules, gates and evals: re-running a recipe shows that nothing broke,
and nothing about what the rules gained since it was written.** Timing starts
at storyline agreement; the discussion is not charged against it. Open the
trace then (`scripts/ops/trace.py open --entry-path A|B --recipe <path> …`)
and close it after the checks — `trace.py close` transcribes verdicts and does
not accept them. **`--recipe` is what makes the ruling checkable**: a trace's
`skill_version` is read at open and can never be stale, so without the recipe's
own stamp a replay is indistinguishable from a current build. `ledger.py`
reports current, stale, or **unknown**, and unknown is not current.

**Study the input first; questions come once or not at all.** Read everything
the user supplied and work from the reader's side of the deliverable — the
first-principles question is what this reader does differently after reading. When a
required input is missing or two requirements conflict, batch every question
into one round before generating; otherwise state your assumptions in the
delivery note and proceed — one clear prompt should normally produce a finished
document. Write a finished document to `Documents/LUMI-Style/` under the user's
home directory unless the user names another, and **ask before creating that
folder**; an export lands beside the document it was made from, and because the
folder is shared, a filename carries the document's own name and version. Run independent pages in parallel where your platform allows —
the protocol is in `SKILL.md` step 1: the orchestrator fixes the storyline,
scaffolds and splits content into `body-N.html` parts carrying `FOOT_<n>` and
asset placeholders; part authors run in parallel writing page markup only; an
assembler stitches, substitutes, and refuses the build on any unreplaced
placeholder; the gate stack runs once on the assembled document. Owner
target: a 30-page document in under ten minutes end-to-end; when the estimate
still passes ten minutes, say so before starting. Before
delivery, the **red-team pass** rides the critic gate: read the draft as its
most skeptical reader, and treat over-design as a finding, not a virtue.
**The evals instruments, named because one nobody can find is one nobody
runs**: `scripts/check/check_outline.py <outline.md>` is the machine half of
the storyline review; `scripts/check/check_privacy.py <file> --terms <list>`
is P-5's other half and reports NOT ATTEMPTED without the list, which is not a
pass; `scripts/ops/scoring_sheet.py` prints the blind C1–C8 sheet, generated
from the rubric so it cannot drift from it; `scripts/ops/review_scores.py`
stores what a reader returns, keyed by `corpus_id`; `scripts/ops/judge_findings.py`
runs the register pass that must quote what it objects to, reported and never
gating; `scripts/ops/ledger.py` reads the closed traces.

**When the request says "debug mode"**, write the execution log beside the
deliverable through `scripts/ops/debug_log.py` (init · run every check through
it · attach the checkers' `--json` · assess C1–C8 with reasons, never a
self-scored 5 · error on any failure · validate) — English-only, no engagement
facts, and only when asked; `SKILL.md`'s Debug mode section is the contract.

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
   the same single vector mark — **by default the locked LUMIVATE field globe
   (`assets/brand/lumivate/globe-field.svg`), embedded live with `data-globe` +
   the inlined runtime so it turns** — the wordmark is the literal string
   "LUMI Style", and **every part boundary gets a lime opener
   page** — about five content pages between openers is a pacing target, reported
   and never gated. **Scaffold with `python3 scripts/ops/new_deck.py` and never
   hand-copy a fixture**: a shipped review carried `REPLACE ME` as its title and
   the fixture's `www.example.org` in every footer, and D14 now refuses both
   slots.
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
   Embed the vendored assets rather than improvising: `scripts/build/embed_font.py`,
   `scripts/build/embed_icons.py`, `scripts/build/embed_shapes.py` (the shape
   library — pick by the RELATION in the content, never by how the shape looks;
   `assets/shapes/tags.json` records it), `assets/vectors/`. **A shape is a starting geometry**: compose this
   page's words and numbers onto it (design-rules §4.2), layer and retint within
   the accent ladder, and give every `<use>` explicit `x`/`y`/`width`/`height`.
   **Imagery is allowed under §9** — evidence not atmosphere, embedded as a
   `data:` URI (D24 gates), terms named (D25 gates), tinted into the palette,
   and never under body text. **The palette is not yours
   to choose either: copy the token block out of `tokens/lumi-theme.css`** — the
   scaffold does it for you. Sizes you may set, colours you may not, and
   `check_design.py`'s D20 fails a document whose colour tokens disagree with
   the shipped ones. The paragraph this replaces said only where
   tokens live, which is a location rather than an instruction. **No size or fill floors** —
   0.1.340 withdrew the 82% page-fill floor and the 11px type floor, both invented
   without an ask, and the fill floor was satisfiable by stretching a table while
   four diagrams rendered at 40% of their cell.
4. `references/eval-rubric.md` — pre-delivery critic gate (structure before polish),
   the D-series and `inspect_layout.py` diagnostics (**design judgements
   reported, never gating** — but an unmeasurable check exits 1 and says what it
   could not find, and `--deliverable` exits 1 on the findings that are
   decidable rather than aesthetic — the code's `deliverable_verdicts` is the
   authority on the list),
   and C1–C8 self-scoring. Never self-score 5 before a reader has scored it, and
   always give the reason for the score, not just the number.

**Every page carries a commercial footer**: the seal-red `shield` handling
marker, the confidentiality terms and the organisation's site on the left,
`N / total` on the right (the marker inverts on the lime opener).
`check_design.py`'s D12 is one of four checks there that fail the run, because
it is a requirement on the artifact rather than a judgement about a page. Three others join it: **D14, no slot you left for
yourself may reach the reader** — `[TO FILL]`, `[TBD]`, `{{name}}`, an empty
bracket pair — **D15, no footer may cite a file path**, because a source line
names something a reader can act on and not a file on the machine that built the
deck — and **D19, every reference resolves inside the document**: an icon
`<use>` pointing at no symbol, or a `data-globe` mark with no runtime shipped
beside it, renders as valid markup and empty space. **And an English deliverable must be in English**: `check_prose.py`'s M12
fails on Chinese in reader-visible text when the document declares English, with
`<code>` the exemption for a name that must appear in Chinese. It asks whether the document is finished, and nothing else
in this package can see one: a placeholder is not a banned phrase, not a colour,
and takes up exactly as much room as the text that should have replaced it.
**Sales and marketing state
provenance once for the document** (cover and closing), not on every page;
consulting and internal analysis keep per-page sourcing. **One table per page** —
two grids side by side share no axis and can never align.

**On portrait, the split family is one composition** — `tokens/` collapses
`split`/`split-wide`/`split-narrow`/`sidebar-notes` to a single grid on the
sheet, and D9 counts them as one there; distinct portrait composition comes
from the vertical and composite families, chosen from the content and checked
on the rendered page (`references/design-rules.md` §3).

**A page is a fixed box.** Landscape is a 1280×720 stage, A4 a 794×1123 sheet,
each scaled to fit the window and letterboxed — never a box that takes the
window's shape. **A deliverable is designed for ONE geometry and declares it**
(`<body data-geometry="landscape">`): sales, marketing and consulting lead 16:9,
training leads A4 portrait, and **when the request settles neither the genre nor
the format, ask before generating.** A second geometry is a second composition
in its own file, never the same file viewed sideways. **Exports render at the stage**
(`scripts/ops/export_pdf.py`): PDF is vector, one page per `.page`; rasters take a
device-pixel multiplier — **default 3 (4K from the landscape stage), floor 2
(2K), refused below** — and the scale never changes the CSS stage, whose zoom
adapts to the reader's window and pixel density natively. State the source once per page: on a single-figure page the line
under the figure is the page's source and the footer carries the page number.

**Rendered geometry decides, not declared CSS.** Run
`python3 scripts/check/inspect_layout.py <file>` and look at the contact sheet it
builds; before handing the file over, run it again with **`--deliverable`**,
which exits non-zero on collision, a starved column, content spill, page height,
hidden content, a wrapped footer, a footer whose runs sit on different
baselines, a viewBox that does not parse, a drawing clipped by its own viewBox,
an overspent title reserve, a role split, a lost datum, a mark drawn out of proportion to the value it declares, and a document whose content pages are mostly not drawn on at all. **Pass it the file and
nothing else**: it reads `data-geometry` and runs the matrix that declaration
implies, and a single `--geometry` switches the matrix off — a 0.1.449
deliverable checked at 16:9 alone left one pixel of clearance under a gate that
fires above one. `--dark` is a second run, not a matrix point. A clean run there is not
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
and carries a verifiable fact, with no word ceiling, no bare-antithesis
titles and no single title frame across more than 60% of a document, and all
titles concatenated must read as a complete argument;
charts use one accent color — the figure green `--acc-live`, which is what the
`f-acc`/`s-acc` paint classes resolve to; `--acc` is the same meaning as text
ink — plus conclusion-style titles and a source line;
AI never signs — money/safety conclusions never come from a language model.

**Workflow note**: after drafting Chinese prose, run a full-width punctuation pass
(Chinese text uses full-width ,:;? — half-width stays only inside code, URLs,
filenames, and pure-English runs). Then run the **mandatory de-AI-flavor pass**
(`references/writing-rules.md` §6 — word, sentence and structural moves plus the
two-pass audit; §6b de-translationese when the Chinese was translated from
English), and only then the pre-delivery checklist in the rubric. Measure both
halves rather than reading them: `python3 scripts/check/check_prose.py <file>` for
English prose, and `python3 scripts/check/check_design.py <file>` for any HTML
deliverable. **D12, D14, D15, D19, D20, D21, D22, D24 and D25 gate; every other D-metric is reported for you
to judge** — a page is done when a human reads it as intentional, and a threshold
satisfiable without improving the page ends the looking. (This line claimed
"D1–D4 and D6 gate" for eight releases, naming four metrics that never did and
omitting the one that always has. A restatement nothing compares against is the
drift this file exists to concentrate, not to escape.)

Rule changes go through the feedback-review loop only (see `references/eval-rubric.md`)
and are recorded in `CHANGELOG.md` with a version bump.
