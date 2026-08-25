# LUMI build card · 0.1.602

> **GENERATED** by `scripts/build/build_card.py` from `evals/rule-coverage.json`, `evals/gates.json` and `tokens/`. `--check` runs in CI. Never hand-edit: edit the rule, or the register, and regenerate.

**This card is the decidable half of the rules, for lookup while you compose. It is not the rules.** Everything on it is something a script can fail you for. Nothing on it tells you what to reach for, how a page argues, which figure a relation wants, or what the voice is — that is `brand.md` (read it first, and commit), `design-rules.md`, `analysis-rules.md`, `storyline-templates.md` and `writing-rules.md`. **An agent that reads only this card will produce a document that passes every gate and says nothing**, which is the exact failure five rounds of conformance produced and the owner returned every time. Read the card to avoid re-reading 100 KB of reference for a class name; read the references to have something to say.

## Ask before generating

Three, and they are one must-ask, because each changes every page.

| | Default | Declared on the document as |
|---|---|---|
| **Genre** | none — ask | `<body data-genre="…">` |
| **Geometry** | from the genre | `<body data-geometry="landscape\|portrait">` |
| **Output language** | **American English** | `<html lang>`, plus `<body data-lang-asked>` when the user asked for anything else |

Language is **asked, never inferred** — not from the source material, not from the venue, not from the audience's nationality, and not from the language the user is writing to you in. A language the same user chose for a comparable deliverable outranks every inference, and a language named in an approved plan is still an inference. `M16` fails a deliverable in any language but English with no recorded ask (`FAILURE_MODES.md` FM-18, twice shipped).

## The one command

```
python3 scripts/ops/brief.py --genre <g> --storyline <s>   # read once, not 11 times
python3 scripts/ops/build.py --deck <out.html> --script <fill.py> \
        --outline <outline.md> --genre <g> --geometry <g> \
        --storyline <s> --entry-path A|B \
        --pages <n> --parts A,B,C --lang en --fast
```

**`--entry-path` is not optional in practice.** A is the four-beat discussion, B starts from a recipe. Without it the scaffold opens NO TRACE, which looks exactly like the deliberate `--no-trace` opt-out and is only caught at the end, by `check_deliverable` reporting the build `unmeasured` after every stage has already run. It used to be guessed from whether an `--outline` was present, and an outline is used on both paths, so replays were recorded as original builds.

`--fast` while fixing (the declared stage only, every gate still running); `--deliver` on the last round (full matrix, and the contact sheet whose path it prints — look at it, that is the last gate). `--debug-log` writes the execution log as a side effect rather than one wrapped command per turn.

**Run it as many rounds as the build needs.** The record is the deck's, not the round's: re-running the driver on the same `--deck` continues the debug log (each entry stamped with its round) and reuses the document's trace, so the build clock accumulates and the loop leaves no abandoned record. `--new-build` starts a fresh record on purpose; `--keep-scaffold` re-fills a deck without scaffolding over it, which is what you want when a fill script is what changed.

**Placing labels on a library shape?** `assets/shapes/geometry.json` carries every unit's viewBox, the four `use` attributes that put it on frame, and its aspect. All 206 origins are non-zero, so composing against an estimated one draws outside the viewBox — that is `figure_clipped`, and a rebuild round. It also says what share of the figure box a unit will ink: **160 of the 206 come in under 55%**, and the scaffold says so at the moment you pick one.

**The instruments are already inside it** — prose, design, layout, privacy and the Evals, one process, browser rendering while the text checks run. Run one directly only to re-check ONE finding while you fix it. Running the stack and then the instruments is the same work twice, and the expensive half is a browser.

## The 53 gating verdicts

A gating failure has to be fixed; a graded one is a reading. **A gate binds a document built at or after its `since`** — an older document reports `not held`, which is neither pass nor failure. A document with no version stamp is held to all of them.

| verdict | concept | since | what an `n/a` means |
|---|---|---|---|
| `D12_commercial_footer` | footer | always | — |
| `D14_placeholders` | completeness | 0.1.367 | — |
| `D15_footer_path` | footer | 0.1.373 | — |
| `D19_vocabulary` | self-reference | 0.1.409 | — |
| `D20_palette_fidelity` | colour | 0.1.454 | — |
| `D21_data_contract` | figure-fidelity | 0.1.472 | — |
| `D22_layout_vocabulary` | layout-vocabulary | 0.1.481 | — |
| `D24_images_embedded` | imagery | 0.1.493 | — |
| `D25_image_provenance` | imagery | 0.1.493 | — |
| `D27_agenda_mirror` | agenda | 0.1.514 | — |
| `D32_shape_use` | analysis-shapes | 0.1.533 | no page declares an analysis move |
| `D33_icon_provenance` | icons | 0.1.549 | — |
| `D35_agenda_exclusive` | agenda | 0.1.549 | — |
| `D37_caption_scope` | figure-labelling | 0.1.551 | the document carries no figure caption |
| `D38_agenda_highlight` | agenda | 0.1.554 | — |
| `D38_agenda_page_spans` | agenda | 0.1.554 | — |
| `D39_bookend_mark` | brand-mark | 0.1.560 | the document has no pair of drawn bookends |
| `D40_bookend_is_the_brand` | brand-mark | 0.1.560 | — |
| `M12_visible_cjk` | output-language | 0.1.373 | the document declares a language this metric does not read - Chinese. A document that declares NOTHING and carries CJK is `blind`, not n/a: it fails |
| `M16_language_asked` | output-language | 0.1.587 | the document declares no language at all, so there is nothing to compare an ask against - M12 answers that document as `blind`, which fails. English… |
| `M4_banned_hits` | banned-language | always | — |
| `M4zh_banned_hits` | banned-language | always | the document is not Chinese |
| `M5_zh_punctuation` | punctuation | always | the document is not Chinese |
| `M6_unsourced_ranges` | number-discipline | always | — |
| `M9_dashes` | punctuation | always | — |
| `agenda_run_wrap` | agenda | 0.1.554 | — |
| `band_escape` | fit | 0.1.541 | — |
| `bookend_title_length` | title | 0.1.544 | — |
| `caption_name_wrap` | figure-labelling | 0.1.551 | — |
| `collision` | fit | always | — |
| `content_hidden` | fit | 0.1.368 | — |
| `content_spill` | fit | 0.1.368 | — |
| `datum` | role-consistency | always | — |
| `deck_structure` | deck-shape | 0.1.547 | — |
| `figure_axis_named` | figure-labelling | 0.1.554 | — |
| `figure_axis_orientation` | figure-labelling | 0.1.551 | — |
| `figure_axis_overlap` | figure-labelling | 0.1.551 | — |
| `figure_clipped` | figure-integrity | 0.1.385 | — |
| `figure_distorts` | figure-fidelity | 0.1.453 | — |
| `figure_ink_collision` | figure-integrity | 0.1.543 | — |
| `figure_viewbox` | figure-integrity | 0.1.386 | — |
| `footer_baseline` | footer | 0.1.447 | — |
| `footer_wrap` | footer | 0.1.380 | — |
| `opener_pacing` | deck-shape | 0.1.549 | — |
| `opener_subject_mark` | brand-mark | 0.1.546 | — |
| `page_height` | fit | 0.1.368 | — |
| `privacy_terms` | handling-terms | always | — |
| `reserve_overspent` | fit | 0.1.368 | — |
| `role_split` | role-consistency | 0.1.368 | — |
| `role_weight` | role-consistency | 0.1.551 | — |
| `starved_column` | fit | 0.1.412 | — |
| `title_two_lines` | title | 0.1.543 | — |
| `visual_absent` | visual-weight | 0.1.453 | — |

## What gates, per page

Only the rules a script can fail you for, from the register. The full contract — including the majority of rules that no check reads — is `references/page-contracts.md`.

### Every page (55)

- **`D12`** Carry the handling terms and origin on every page, opening with the seal-red shield handling marker. — `SKILL.md:625`
- **`D12`** Carry the handling terms and the document's origin on every page. — `references/design-rules.md:1050`
- **`D12`** Put the confidentiality line then the organisation's site left of the footer rule. — `references/design-rules.md:1051`
- **`D14`** Let no unreplaced placeholder or author slot survive into the delivered document. — `SKILL.md:264`
- **`D14`** Let no author placeholder reach the reader. — `references/design-rules.md:1087`
- **`D14`** Ship no [TO FILL] placeholder in a finished document. — `references/storyline-templates.md:566`
- **`D15`** Never print a repository or file path in a footer source line. — `references/design-rules.md:1079`
- **`D20`** Copy the shipped token block into the document rather than inventing a palette. — `SKILL.md:395`
- **`D20`** Sizes may be set per page; colour tokens may not be redefined. — `SKILL.md:402`
- **`D20`** Copy the shipped colour token values exactly into the deliverable. — `references/design-rules.md:35`
- **`D20`** Use pure white #FFFFFF for the light canvas and #FAFAFA for cards. — `references/design-rules.md:59`
- **`D20`** Never use warm cream as the canvas. — `references/design-rules.md:60`
- **`D20`** Use #1D1D1F for the dark canvas and #2C2C2E for its cards. — `references/design-rules.md:62`
- **`D22`** Give every page one of the layouts tokens/ defines. — `references/design-rules.md:418`
- **`D22`** Give every page a layout class the shipped tokens define. — `references/design-rules.md:1453`
- **`D24`** Ship every image inside the file as a data: URI, never as a link. — `SKILL.md:437`
- **`D24`** Embed every image in the file as a data: URI rather than linking it. — `references/design-rules.md:1567`
- **`D25`** Name every image's source and licence terms in the document. — `SKILL.md:438`
- **`D25`** Name every image's origin and terms on the page. — `references/design-rules.md:1571`
- **`D25`** Name the licence for any image that is not public domain or CC0. — `references/design-rules.md:1574`
- **`D33`** Take every icon from the two sets this package ships; never draw one ad hoc. — `references/design-rules.md:1138`
- **`D39`** Carry one mark twice — the cover's and the closing's are the same mark. — `references/brand.md:364`
- **`D40`** Carry the locked field globe on the cover and the closing unless the document declares the replacement the owner asked for. — `references/storyline-templates.md:532`
- **`M12`** Keep an English deliverable free of Chinese in text a reader sees. — `references/writing-rules.md:39`
- **`M16`** Default the output language to American English and the canvas to light unless the user asks otherwise. — `SKILL.md:86`
- **`M16`** Write in American English when the user specifies no language. — `references/writing-rules.md:27`
- **`M16`** Deliver in American English by default; author any other language directly, quoting the user's own words. — `references/writing-rules.md:47`
- **`M4`** In English output, use none of the phrases on the banned AI-tell list. — `references/writing-rules.md:137`
- **`M4`** Quote a banned phrase only inside figure ink, never in HTML prose. — `references/writing-rules.md:166`
- **`M4`** Replace copula avoidance (serves as / stands as / boasts / features) with is / are / has. — `references/writing-rules.md:373`
- **`M4`** Delete filler phrases losslessly. — `references/writing-rules.md:379`
- **`M4zh`** In Chinese output, use none of the banned AI-tell phrases on the zh list. — `references/writing-rules.md:129`
- **`M4zh`** Use the fixed industry collocations only for the 'empower' verb the zh ban list restricts; the quoted line names them. — `references/writing-rules.md:132`
- **`M5`** Use full-width punctuation in Simplified-Chinese body text; half-width stays in code, URLs, emails, version strings, filenames and pure English runs. — `references/writing-rules.md:184`
- **`M6`** Trace a range figure to a single source in its own block, or drop it. — `references/writing-rules.md:211`
- **`M6`** Do not treat a dashed pair that is an enumeration label rather than a data range as a range figure. — `references/writing-rules.md:256`
- **`M6`** Decide range-versus-label by what the numbers do, not by sentence length. — `references/writing-rules.md:260`
- **`M9`** Bind the em-dash ban on training material exactly as on sales material. — `references/storyline-templates.md:113`
- **`M9`** Use no em dashes or en dashes in sales, marketing, consulting or training deliverables; internal analysis alone is exempt. — `references/writing-rules.md:391`
- **`M9`** Exempt a digit-to-digit range from the dash ban, but write a letter-digit span as "C1 to C8". — `references/writing-rules.md:399`
- **`collision`** Let nothing land on anything: no text on text and no text on any drawn element. — `references/design-rules.md:1406`
- **`content_hidden`** Never clamp or hide overflow in a title block. — `references/design-rules.md:1433`
- **`content_spill`** Keep the deepest ink on a page above the footer rule. — `references/design-rules.md:1521`
- **`datum`** Start the content area at the same height on every page of a geometry. — `references/brand.md:253`
- **`datum`** Start content at one datum per geometry. — `references/design-rules.md:1372`
- **`deck_structure`** Open a deck with a cover and end it with a closing page, each carrying the single vector mark. — `SKILL.md:663`
- **`deck_structure`** Open a deck with a cover and end it with a closing page. — `references/storyline-templates.md:497`
- **`page_height`** Render every section at exactly the page geometry's height. — `references/design-rules.md:1241`
- **`page_height`** Make each page a fixed box, scaled and letterboxed. — `references/design-rules.md:1522`
- **`privacy_terms`** Carry none of the engagement's out-of-bounds terms in a deliverable, and name the list so the check can be attempted at all. — `references/operating-rules.md:237`
- **`reserve_overspent`** Treat the title block's reserved height as a ceiling. — `references/design-rules.md:1424`
- **`role_split`** Render every repeating role exactly one way across the deck. — `references/brand.md:235`
- **`role_split`** Render each repeated role exactly one way across the document. — `references/design-rules.md:1368`
- **`title_two_lines`** Keep a title to one line where it fits and never past two. — `references/design-rules.md:1175`
- **`title_two_lines`** Set no word ceiling on a title; the only limit is the two-line budget. — `references/storyline-templates.md:633`

### The cover (2)

- **`D19`** Embed the field-globe mark live so it turns, rather than as a still frame. — `references/brand.md:366`
- **`D40`** Use the LUMIVATE field globe as the default cover mark, embedded live with its runtime. — `references/storyline-templates.md:520`

### The agenda (9)

- **`D27`** Derive the agenda from the deck's own page titles rather than paraphrasing them. — `SKILL.md:235`
- **`D27`** Quote the document on the agenda; never paraphrase it. — `references/storyline-templates.md:267`
- **`D27`** Make every agenda claim line one the deck's own titles say. — `references/storyline-templates.md:268`
- **`D35`** Give the agenda page no lede: no title and no support line, and declare body stack no-lede. — `references/storyline-templates.md:237`
- **`D35`** Set body stack no-lede on the agenda so the rows centre in the page. — `references/storyline-templates.md:240`
- **`D35`** Let the agenda page's body hold the launch sequence and optionally its lede, and nothing else. — `references/storyline-templates.md:256`
- **`D38`** Keep page spans out of an agenda row; they are apparatus. — `references/storyline-templates.md:210`
- **`D38`** Mark a phrase in every agenda claim with the lime chip, and keep each run line to one rendered line. — `references/storyline-templates.md:224`
- **`agenda_run_wrap`** Let the agenda run line name what the pages cover, never the page numbers. — `references/storyline-templates.md:218`

### A part opener (7)

- **`opener_pacing`** Target about five content pages between part openers and never run past six without a seam. — `references/storyline-templates.md:593`
- **`opener_subject_mark`** Use the filled koboyo silhouettes for part-opener subject marks only. — `SKILL.md:459`
- **`opener_subject_mark`** Allow at most one oversized filled subject silhouette on a part opener. — `references/design-rules.md:413`
- **`opener_subject_mark`** Use the filled silhouette set only for part-opener subject marks. — `references/design-rules.md:1106`
- **`opener_subject_mark`** Make an opener's subject mark fill-based, never stroke-based. — `references/design-rules.md:1165`
- **`opener_subject_mark`** Permit exactly one oversized filled silhouette, carrying no text, on an opener. — `references/storyline-templates.md:585`
- **`opener_subject_mark`** Give each part opener its own subject silhouette; two parts may not share one. — `references/storyline-templates.md:588`

### A content page (19)

- **`D20`** Retint a library shape only along the accent ladder, never by introducing a colour. — `references/design-rules.md:1036`
- **`D21`** Have every mark that encodes a quantity declare that quantity in the markup. — `references/design-rules.md:826`
- **`D32`** Follow the question to framework to shape chain, drawing a declared move with the library shapes that framework names. — `references/analysis-rules.md:107`
- **`D37`** Keep the caption below a figure to the number and the name; the source line goes inside the drawing. — `references/design-rules.md:710`
- **`D37`** Put the source line inside the drawing, not in the caption beside it. — `references/design-rules.md:711`
- **`caption_name_wrap`** Hold a figure's name to one line at the document's geometry, shortening it rather than setting it smaller. — `references/design-rules.md:699`
- **`content_hidden`** Never clamp or hide overflow on the title block. — `SKILL.md:492`
- **`figure_axis_named`** Name the axes of any figure that puts numbers on a scale, with the shipped classes. — `references/design-rules.md:641`
- **`figure_axis_orientation`** Set the y-axis name upright reading bottom to top at the left of its axis, and the x-axis name level below its line. — `references/design-rules.md:658`
- **`figure_axis_overlap`** Keep both axis names clear of the region the marks occupy. — `references/design-rules.md:663`
- **`figure_clipped`** Keep every drawn element inside its figure's viewBox. — `references/design-rules.md:1343`
- **`figure_distorts`** Draw a mark's length in proportion to its declared value, with no minimum-width floor. — `references/design-rules.md:828`
- **`figure_viewbox`** Edit a figure's viewBox with the shape, so the box a figure declares is the box it draws in. — `references/design-rules.md:1344`
- **`reserve_overspent`** Shorten the title text when the title block does not fit. — `SKILL.md:491`
- **`reserve_overspent`** Treat the title reserve as a ceiling — two title lines plus one support line — and shorten text rather than grow it. — `references/brand.md:260`
- **`role_weight`** Render a repeating block's row name at title weight, not body weight. — `references/design-rules.md:861`
- **`starved_column`** Start side-by-side cells on one line with comparable weight. — `references/design-rules.md:1495`
- **`title_two_lines`** Keep a headline within two lines at the design viewport. — `references/design-rules.md:385`
- **`visual_absent`** Carry at least one visual block on every content page. — `SKILL.md:474`

## Vocabulary

Rename one of these and the block drops OUT of the consistency audit rather than failing it.

**Layouts** (`D22` fails a page claiming one `tokens/` does not define): `.band-hero`, `.columns-2`, `.columns-3`, `.columns-4`, `.cover-grid`, `.diagonal-flow`, `.full-bleed`, `.hero-band`, `.quad`, `.rail`, `.sidebar-notes`, `.split`, `.split-narrow`, `.split-wide`, `.stack`, `.thirds-v`

**Roles**: `.eyebrow`, `.t`, `.sup`, `.lede`, `.take`, `.key`, `.red`, `.card`, `.ledname`, `.verdict`, `.swap`, `.vow`, `.tag`, `.grades`, `.gloss`, `.listhead`, `.gd`, `.cap`, `.srcline`, `.band`, `.stats`, `.stat`, `.fig`, `.fill`, `.field`, `.colophon`, `.closenote`, `.launch`

## Where the judgement lives

| Read | For |
|---|---|
| `references/brand.md` | what to reach for. The only file that says it. Read first, and commit, before deciding what the deliverable may not do |
| `references/analysis-rules.md` | facts becoming findings: the five moves, the outline contract, the implication rung |
| `references/design-rules.md` | colour, type, the chart iron rules, form selection, the shape library, icons, imagery |
| `references/storyline-templates.md` | the narrative skeleton for the storyline you chose |
| `references/writing-rules.md` | output language, terminology red lines, banned phrases, number discipline, the de-AI pass |
| `references/page-contracts.md` | every rule binding one page kind, checked or not, with the line it is written on |
| `references/eval-rubric.md` | the C1–C8 self-score, at the end |

