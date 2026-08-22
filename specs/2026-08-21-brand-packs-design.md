# Brand packs — design

Revision 4 (2026-08-22), after four review rounds (red/blue on revision 1; a platform
review for Hermes, Cursor and Gemini on revision 2; red and plan-readiness on revision 2b).
Baseline for every code citation: `main` at 0.1.553. §10 records what each round changed and why. Every mechanism here is written so that a
wrong implementation goes **red**, never green-and-LUMIVATE.

## Context

`_refactor/…-v2.md` §1.2 ruled that the rule engine is brand-neutral and "switching brands
= swapping an asset pack + a registry record". The repo never did it: `brands/registry.json`
exists but only `new_deck.py` reads it; D20, D23, palette parity, var-resolution,
`check_versions`, `embed_font`, `build_region_palette`, the evidence gate's obligation table,
the conformance surface and the scaffold footer (`www.lumivate.io` on every page) all
hard-code LUMIVATE by literal path or value — and the scaffold's whole `<head>` is lifted
from the LUMIVATE fixture.

Goal (owner, 2026-08-21): any user installs lumi-style, answers a short interview, and
produces consulting-grade documents in **their** brand; LUMIVATE ships as the reference brand
a new user learns from, with a gallery of scene examples. Modelled on obra/superpowers'
README shape — plus what a design skill needs and a process skill does not: pictures first.

The hazard this file is built against, in the first review's words: *the spec treated a
split that runs through eleven generated artifacts, the evidence gate, the lock, the rule-id
chain, the privacy home, thirty-six named tokens and the build recipes outside the repo as a
directory move plus five rewired checkers.*

### Decisions

| # | Decision |
|---|---|
| D1 | A brand owns the **visual** layer and may **extend** voice and compliance. Storylines and the AI-register ban list are **engine** (red line 3, P-3) — the brainstorm's "all four layers" yielded to the constitution. |
| D2 | A user's brand lives at **`~/.lumi/brands/<id>/`** and nowhere else; the pointer `~/.lumi/brand` holds an **id only**. `LUMI_BRAND_HOME` overrides the `~/.lumi` root for the whole process — packs, the pointer, the update stamp and the OR-8 terms directory alike (`LUMI_TERMS_DIR` still wins for terms). LUMIVATE is the only tracked pack. |
| D3 | Gallery = curated PNGs tracked in-repo under the pack, built from tracked synthetic HTML sources, with a digest rot guard over every render input. |
| D4 | Overlay packs. File-level inheritance applies to an **explicit `INHERITABLE` list** (`compliance.md` only); every other pack file is the pack's own or the producer refuses. Fonts fall back at the **json** level (D7): a pack with no `fonts` key uses the default pack's entries, whose paths resolve in the default pack — one mechanism, not two. Engine facts never live in a pack file, so nothing merges. |
| D5 | `tokens/` dissolves and `assets/` splits, each as a **compatibility pair**; `references/ → rules/`, `adapters/ → platforms/` follow as pairs. |
| D6 | Pack carries a **logo** set and a **legal/** set (privacy + security, text or URL). |
| D7 | D-DIN stays the engine default body face and IBM Plex Mono the default data face; a pack's `fonts` list carries both roles (`face: body|mono`), and both `--face-body` and `--face-mono` are **required** in every theme (the engine's `--mono: var(--face-mono), …` is otherwise invalid at computed-value time and the data voice silently inherits). |
| D8 | First gallery scenes: sales deck, internal analysis, training, investor pitch, A4 report, Chinese deck, dark mode. `gallery.json` is the authority; prose never counts them. |
| D9 | Below the `full` tier the brand reaches the agent by **generation**: `build_entrypoints.py --brand <id>` writes exactly two files under `~/.lumi/brands/<id>/generated/` — `core-prompt.md` (prompt tier, pasted) and `BRAND-POINTER.md` (files tier, read on the operator's instruction). Nothing per-brand is ever written under the checkout or a skill path that resolves into it; **no platform auto-loads a brand file** — a rule loading beside the skill is a second source. The per-brand core prompt is generated from `prompts/lumi-style-core.md`, whose palette and identity sentences gain fenced `<!-- brand:begin -->…<!-- brand:end -->` markers that `check_prompt_parity` skips; the hand-written source stays LUMIVATE's. |
| D10 | **No inherited identity**: `wordmark`, `cover_mark`, `logo` absent means a text wordmark and no mark. A brand never inherits another brand's globe. |
| D11 | **An agent never reads a pack.** The readers are `new_deck.py`, `export_pdf.py`, `new_brand.py`, `build_entrypoints.py --brand`, `build_region_palette.py`, `embed_font.py`, and the checkers through `declared()`; `check_script_paths`' pattern holds that list to the code. `brand.py --print` is a stop-gate: if it fails, the build stops and the report names the missing pointer. The agent may not choose LUMIVATE or any palette by hand (the 2026-08-13 incident). |
| D12 | **Launch platforms are Claude Code, Hermes and Cursor.** Gemini CLI is supported by construction but not validated in this work (file tools cannot leave the workspace; the key is free-tier). GAP entry at R1. |
| D13 | **No provenance digest in a deliverable.** A hash the author computes proves nothing; the defence against a typed `content="lumivate"` is D20's value comparison (a typed id over a foreign palette fails on values; over LUMIVATE's palette it is a LUMIVATE document) plus T4-brand's `grep -c lumivate = 0`. |
| D14 | `brand.json.output_dir` names the **leaf** folder under the platform's Documents directory (`output_dir.py`'s `documents_dir()` supplies the localised parent); LUMIVATE's is `LUMI-Style`, so the owner's corpus and the conformance results root do not move. |
| D15 | A user pack's **dark palette is derived** from the light triple and measured; a dark triple may be given to override; if derivation cannot clear the floors, dark mode is **disabled for that pack** (`theme.json.dark = false`, `new_deck.py --dark` refuses, D-metrics skip the dark block) and the report says so. Shipped packs carry **no `answers`** and `new_brand.py --upgrade` refuses a shipped pack: LUMIVATE's dark palette is hand-tuned and no derivation reproduces it. |

## 1. The pack

```
brands/lumivate/                      tracked reference pack
  BRAND.md            identity at R1 (name, one idea, the two devices named); the prose of
                      references/brand.md §1–2b/§4 + README 143–171 moves in at R4 with its
                      BR-* ids and Serves: lines. Worked examples are synthetic or unitless.
  brand.json          machine facts (schema below); the ONLY stamp in a pack
  theme/              theme.css, theme.json            brand VALUES only (§1.1)
                      region-palette.css, region-palette-trade.css   GENERATED per pack
  assets/
    fonts/            D-DIN.woff2, D-DIN-Bold.woff2, IBMPlexMono-Regular.woff2,
                      IBMPlexMono-Bold.woff2, COPYING.txt
    marks/            globe-field.svg, globe-cover.svg, globe-cover.dark.svg
    logo/             wordmark.svg, wordmark.dark.svg, mark.svg        NEW (§1.3)
    LOCKED.json       pack lock: marks + logo + fonts, pack-relative (arrives with lock.py's base, R3a)
  legal/              privacy.md, security.md — text, or a one-line file holding a URL
  voice.md            [optional] ADDITIVE: `## Never` / `## Favour`, one literal phrase per bullet
  compliance.md       [optional, the one INHERITABLE file] D12 handling terms, origin line, who-may-see-what
  examples/           gallery: <scene>.html, <scene>-cover.png, <scene>-p1.png, gallery.json
```

Absent by design: any `*terms*` file (`~/.lumi/terms/`, OR-8 — `check_brand_pack` fails on
one), storylines, the AI-register ban list, any engine token, any skill stamp other than
`brand.json.engine_version`.

`brand.json` (required: `schema`, `id`, `name`, `site`, `output_dir`, `engine_version`):

```json
{
  "schema": 1, "id": "lumivate", "name": "LUMIVATE",
  "wordmark": "LUMI Style", "site": "www.lumivate.io", "language_default": "en",
  "output_dir": "LUMI-Style",
  "logo": {"light": "assets/logo/wordmark.svg", "dark": "assets/logo/wordmark.dark.svg",
           "mark": "assets/logo/mark.svg"},
  "cover_mark": "assets/marks/globe-field.svg",
  "fonts": [{"file": "assets/fonts/D-DIN.woff2", "weight": 400, "face": "body"},
            {"file": "assets/fonts/D-DIN-Bold.woff2", "weight": 700, "face": "body"},
            {"file": "assets/fonts/IBMPlexMono-Regular.woff2", "weight": 400, "face": "mono"},
            {"file": "assets/fonts/IBMPlexMono-Bold.woff2", "weight": 700, "face": "mono"}],
  "policies": {"privacy": "legal/privacy.md", "security": "legal/security.md"},
  "compliance": {"handling_terms": "…", "origin": "…"},
  "engine_version": "<the version of the release that writes it>",
  "locked": "assets/LOCKED.json"
}
```

`engine_version` precedes every other version-shaped string in the file (`release.py` swaps the first occurrence). User packs additionally carry `answers` (the interview, for `--upgrade`). An optional key that is present must resolve or `check_brand_pack` fails. `wordmark`,
`cover_mark`, `logo` have no default (D10). `brands/registry.json` shrinks to
`{"default": "lumivate", "brands": {"lumivate": {"path": "brands/lumivate"}}}` and
`check_brand_registry.ALLOWED` to `{path}`.

### 1.1 Brand value vs engine fact — the three-way split

| Material | Home | Why |
|---|---|---|
| palette light + dark, ladders, ramp, washes, `on-*`, **`lime`/`on-lime`/`seal`/`amber`/`brass`/`acc-live` (required — `layouts.css` references them 46 times without fallbacks; `palette_derive` writes them when the interview does not name them)**, ground tiers `--ground-strong/-mid/-faint` and their portrait override, `chart` triple, `palette_default`, `contrast.measured`, `font` (face names as `--face-body`, `--face-mono`, both required) | **pack** `theme/theme.css` + `theme.json` | D20 compares them; measured per palette |
| type register `--fs-*`, `--w-*`, `--lh-*`, `--ls-*`, `--din: var(--face-body), <CJK stack>`, `--mono: var(--face-mono), <mono stack>`, `.scope-note` | **engine** `layouts/register.css` | checkers read them; a pack cannot lose `--fs-stat` (the ground *ceiling* is not a token — it is `inspect_layout.GROUND_CEILING`) |
| `retired`, `layout`, `typography` (incl. `chart_scale_px`), contrast **floors**, region **parameters**, ladder alphas; the `assets` key is deleted at R3a | **engine** `layouts/engine-tokens.json` | a pack without `retired` would pass that guard vacuously |
| `lumi-layouts.css` | **engine** `layouts/layouts.css` | structural classes painted through `var()` |
| region palettes, shape fallbacks, marks, `contrast.measured` | **generated per pack** | computed against the pack's ink/ground |

**One declaration per custom property.** `check_token_references` holds that a name defined
in `layouts/` is defined in no pack and vice versa (planted red: declare `--din` in the
synthetic theme), and that every `var()` in `layouts/` **and in each pack's generated `region-*.css`** resolves
against `layouts/` ∪ that theme. "Declared" is per file, so `body.dark` re-declaring `:root`
names inside one theme is not a double declaration. Inclusion order in a document head: `theme.css`, `register.css`,
`layouts.css`, `region-*.css`. `check_palette_parity` reads floors from `engine-tokens.json`
and `measured` from each shipped `theme.json` — two files, said here so it is not a surprise.

### 1.2 Engine after the split

`rules/` (method, storylines, writing-rules with the ban list, operating rules, rubric,
exemplars, the interview, the brand inventory), `layouts/`, `library/` (icons, shapes,
vectors, geo, globe runtime, third-party logos, `LOCKED.json`), `scripts/`, `fixtures/`,
`evals/`, `conformance/`, `platforms/` (later). Engine classes renamed `lumivate-*` →
`brand-*`; `aria-label`s and generator comments in marks name the pack.

### 1.3 Logo and legal (convention 5)

R1 ships the logo: `build_brand.py --wordmark` renders a text-set wordmark from
`brand.json.wordmark` in the pack's face, light and dark; `mark.svg` is the field globe's
static frame. `build_brand.py` is hash-locked, so the same commit re-stamps the lock with the
reason. `legal/*.md` ship as one-line URL files to pages the owner names; until named,
`policies` is omitted and nothing cites it. A logo is an image: `data-mark` (D4), terms (D25).

## 2. Resolution — `scripts/lib/brand.py`

Standard library; the only module that knows where a brand lives. `home()` is a function
(reads `LUMI_BRAND_HOME`, else `~/.lumi`) so tests can redirect it.

- `active() -> Pack`: `--brand` → `LUMI_BRAND` → `~/.lumi/brand` → registry default. Each
  holds an **id**; an absolute path anywhere is refused with the reason; an id with no
  directory under `home()/brands/` or the registry **raises**. Read by **producers only**.
- `declared(html) -> Pack`: from `<meta name="brand" content="<id>">`, resolved through
  the registry (shipped) or `home()/brands/<id>/` (user). No meta, or an unresolvable id →
  `Unmeasurable(reason)`; D20, D23 and `check_prose`'s pack bans report **UNMEASURABLE,
  non-zero**. D22 reads `layouts/` and grades regardless of brand. **Checkers never call
  `active()`** — the owner's preflight cannot go red because her pointer is on a client.
- `shipped() -> list[Pack]`: registry packs; every CI guard loops over these.
- `Pack.path(rel)`: the pack's file; falls back to LUMIVATE's only for `INHERITABLE`; a
  generated file absent → `check_brand_pack` red and the producer refuses.
- `meta_tag(pack)`: the one function that writes the meta; called by `new_deck.py` and
  `build_fixtures.py` — the two generators, never an agent. SKILL.md and every conformance
  prompt: *scaffold with `new_deck.py`; a hand-written `<head>` or a hand-typed meta is a
  failure.* `check_deliverable.py` (an ops script, not a checker) prints the active id beside
  the declared id as information, so a LUMIVATE document built under an acme pointer is
  visible in the report.
- `--print`: exit 0 with one line `brand: <id>  home: <abs path>  engine_version: <v>` and
  nothing else; exit 2 with one line naming the missing pointer. Diagnostic and stop-gate,
  not a data path.

SKILL.md carries the resolution order as prose for agents that cannot import the module.

## 3. Checker, guard and generator changes (decided; planted red per row)

| Today | After | Planted red |
|---|---|---|
| `new_deck.py` lifts `<head>` from the LUMIVATE fixture | `preamble()` assembles it from `active().path("theme/theme.css")` + `layouts/*` + `embed_font.css()`; writes `meta_tag` | scaffold under the synthetic pack: D20 `compared > 0, differs 0`; `grep -c lumivate` = 0 |
| `new_deck.py` globe path + `www.lumivate.io` | from `brand.json`; text wordmark when no logo | scaffold under the synthetic pack carries its site and no mark |
| D20 reads `tokens/lumi-theme.css`; missing → `compared: 0`, passes | reads `declared(doc)`; unreadable or undeclared → UNMEASURABLE | typed `lumivate` over the synthetic palette → fail; theme removed / no meta → UNMEASURABLE |
| D23 font ceiling reads `tokens/lumi-theme.css` | declared set = `declared(doc)` theme ∪ `layouts/register.css` (`--din`/`--mono` live engine-side now); same UNMEASURABLE rule; `fixtures/expected.json` unchanged | a theme lacking `--face-mono` → theme guard red, never a silent inherited font |
| `build_fixtures.py` lifts `tokens/` | lifts `shipped()[default]` theme + `layouts/`; writes `meta_tag`; `expected.json` unchanged | fixtures without the meta → `check_fixtures` red |
| `check_privacy` strips markup before scanning | scans `<meta name="brand">` and every `content=` attribute for path shapes first | a path in the meta → red |
| palette parity: one JSON ↔ one CSS | loop `shipped()`; floors from engine JSON | mismatched hex in `tests/fixtures/brands/acme-broken` |
| var() resolves: `tokens/*.css` glob | §1.1 rule | `--din` declared in the synthetic theme; a layout var no theme defines |
| `check_versions` `TOKEN_STAMPS` + "LUMI" regexes; `release.py` imports the tuple | `ENGINE_STAMPS`: `layouts/register.css` (`LUMI register · vN`), `layouts/layouts.css` (`LUMI page layouts · vN`), `layouts/engine-tokens.json` (`"version"`), plus one row per shipped pack's `brand.json` (`"engine_version":\s*"(\d+\.\d+\.\d+)"`); `release.py` and `tests/test_release_tool.py` renamed in the same commit; user packs exempt | stamp drift in `register.css` |
| `check_retired_values` reads `tokens/design-tokens.json` | reads `layouts/engine-tokens.json` | `retired` removed → red, not vacuous |
| `check_evidence` `TOUCH_MAP`/`STAMPED_PREFIXES`/`spec_lines_changed` key on `tokens/`, `assets/geo|globe/` | each new prefix enters **in the release that creates its directory** (`validate_maps` refuses a missing one): `brands/` → `conformance-freshness` at R1; `layouts/` + `brands/lumivate/theme/` → `layout-fixtures` at R2a; `brands/lumivate/assets/` + `library/geo|globe/` at R3a; `rules/` at R7; `brands/lumivate/brand.json` joins `STAMPED_PREFIXES`. New obligations `gallery` (R6) and **`brand-e2e`** = `scripts/ops/verify_brand_packs.py` (runs §8's machine lines, R6). No `fresh-clone` obligation: tracked files always clone, and `check_assets_tracked` already asks git about ignored-but-wanted files | edit a shipped theme → `--init` obliges `layout-fixtures`; a `BRAND.md` typo does not |
| `claim_sweep.py` sees counts and citations only | **`check_path_mentions`** (generalised `check_script_paths`): every `<dir>/path` mentioned in tracked prose, code, JSON, tests resolves; `WARN_PREFIXES` holds the old half of a live pair; ships in R1 | a stale `tokens/` path in AGENTS.md |
| `check_platform_manifest` ignores `ships` | resolves every `ships` entry | `ships: ["nonexistent/"]` |
| `embed_font.py` D-DIN literals, byte-size asserts | faces from `active().json()["fonts"]`; sizes from the pack lock | one face → one `@font-face` |
| `build_region_palette.py` duplicated ink/bg | `--brand <id>` reads the pack's theme, writes into its `theme/`; `--check` over `shipped()`; floors unchanged; its colour maths lifted into `color_math.py` first (the shadow-math guard) | off-white ground → floors re-measured; a failing hue → `new_brand.py` refuses |
| `recolor_shapes.py` writes LUMIVATE literal fallbacks | `var(--token)` with no literal; mapping computed once against the default shipped pack (the token names are engine facts) | a shape with a literal hex → `--check` red |
| `build_brand.py` bakes `.lumivate-mark` + palette | `--brand <id>`; `brand-mark`; `aria-label` from `brand.json.name`; `--relock "<why>"` rewrites the pack lock and refuses if the engine lock is red (engine first, pack second, same commit) | generated mark contains no `lumivate` |
| `build_eval_inventory.py` reads `tokens/design-tokens.json` | reads `layouts/engine-tokens.json` | existing `--check` |
| one `LOCKED.json`, repo-relative | `lock.verify(lock_path, base)` / `lock.update(...)`; **`check_engine_lock`** (renamed) verifies `library/LOCKED.json` against `ROOT`; `check_brand_pack` verifies each shipped pack's lock against the pack root | move a runtime file → engine red; edit a mark → pack red |
| `check_assets_tracked` scoped to `assets/` | `library/` + every shipped pack | untracked svg under the pack |
| `.gitignore` | re-admit `library/**`, `brands/lumivate/**` (woff2, svg, png), **`!brands/registry.json`**, `!tests/fixtures/brands/**`; ignore `brands/*` otherwise | fresh clone lists the pack; `git check-ignore brands/acme/x` ignored and `brands/registry.json` not |
| `recolor_shapes.py`, `build_brand.py`, `check_globe.py`, `check_role_weights` read `tokens/` at import or in CI | rewired in R2a (all four run in CI; `build_brand.py` is hash-locked → relock in that commit) | `tokens/` removed → all four still green |
| conformance `SKILL_SURFACE`; `render_note`/`render_pointer` texts; `platforms.json ships` | read from `brand.py` / the registry (named: after R2b `environment_check` would otherwise report every platform unreachable) | `validate`; `--check` |
| `run_conformance.drive()` passes no `env=` | tasks may declare `environment: {...}`; the driver expands `${WORKDIR}` (the run's temp dir is created after the task loads), merges over `os.environ`, and when `LUMI_BRAND_HOME` is named copies `tests/fixtures/brands/<LUMI_BRAND>` to `$LUMI_BRAND_HOME/brands/<id>` (the same hole GAP-023 names for `LUMI_TRACES`) | T4-brand with `LUMI_BRAND_HOME` at a missing path → agent stops at `--print` |
| `check_prose` one ban list | adds the declared pack's `voice.md` bans as `M4b_pack_bans`; `n/a` with no brand is not a blind gate because M4 still graded; additive only | phrase in the synthetic `voice.md` with no pattern |
| `check_rule_ids`, `check_principle_trace` glob `references/*.md` | ∪ shipped `BRAND.md` at R4 (R1's `BRAND.md` carries no ids) | remove a `BR-*` id → red |
| `check_output_default` one literal in five sites | sites hold "the pack's `output_dir`" wording; `output_dir.py` reads `active().json()["output_dir"]`; `FOLDER` constant removed and the guard's regex branch rewritten | a site naming a literal folder → red |
| README brand prose | **`check_readme_brand_prose`**: README's brand section is one paragraph ending in a link to `brands/lumivate/BRAND.md` | a second paragraph → red |
| `trace_schema.FIELDS` closed; `validate` reports a missing key | `brand: (str, NoneType)`; every tracked trace migrated with `"brand": null` in the same commit (0.1.500's `recipe_hash` precedent); `trace.py open` writes `active().id`; `ledger.py --board` groups by it | schema test; one unmigrated trace → `trace schema` red |
| **new `check_brand_pack`** | per shipped pack: required keys; every declared path resolves; `policies` file-or-URL; logo iff declared; pack lock; **no `*terms*`**; `engine_version` = SKILL.md; every pack file in `git ls-files`. Presence and lock **only** — "built from this pack's anchors" belongs to `build_region_palette --check` and `build_brand --check` | delete `legal/privacy.md`; plant `privacy-terms.txt` |
| **new `check_gallery`** | `gallery.json` row per PNG: scene, source html, evidence id, SHA-256 over **source html + `theme/theme.css` + `layouts/*.css` + every font `brand.json.fonts` names**, in that order; CI recomputes from tracked inputs (no render); the render is `scripts/ops/build_gallery.py`, the evidence command for `record --id gallery` (Chromium build recorded there) | edit a scene html without rebuilding; a PNG with no row |
| **new `doctor.py`** | `--platform <id>` (else "tier: not determined"); Chromium, fonts, active brand, installed version; `.git` present → `git fetch --dry-run` under 5 s with `GIT_TERMINAL_PROMPT=0`, else one line naming the platform's updater; stamp file `~/.lumi/last-update-check`; `--force`; **always exit 0**; `quota_limited` read from the registry record, never from a vendor's error text | missing font dir → reported; network cut → one line within 5 s |
| **new `build_brand_inventory.py`** (§9) | `rules/brand-inventory.md` generated, `--check` in CI; lands in R1 | hand-edit → `--check` red |

**R1 bridge.** `theme/` first exists at R2a, so R1's `Pack.path()` carries
`TOKENS_BRIDGE = {"theme/theme.css": "tokens/lumi-theme.css", …}` for the shipped pack;
R2a deletes it and that deletion is R2a's planted red. R1's `check_brand_pack` holds required
keys, path resolution, `*terms*` absence and `engine_version` only; its generated-files and
lock rows arrive with their artifacts.

**Stamps.** Engine files carry the skill stamp. A shipped pack's `brand.json.engine_version`
is held to SKILL.md. A user pack's is the version it was generated against;
`new_brand.py --check` reports (never gates) when it trails, and `--upgrade` regenerates from
`brand.json.answers`.

**Existing deliverables.** The day D20 loses its default, every document in the owner's
corpus and every past conformance artifact is UNMEASURABLE on D20 until rebuilt. Accepted
(the token-bump staleness rule already applies); the R2a CHANGELOG entry says so and
`ledger.py` reports it, so nobody "fixes" it.

**Size.** Fourteen PNGs at 105–190 KB/page ≈ 2 MB per refresh against a 6.75 MiB packed
repo; refreshes happen on digest change only. Recorded so it is a decision.

## 4. `init --brand`: the interview

The questions live in `rules/brand-interview.md` with a parent-principle column (v2 §6.4c).
Every tier conducts it; `scripts/ops/new_brand.py` (full tier) writes the pack. Each question
shows LUMIVATE's answer as the example, in the user's language, in plain words. A user may
hand over a logo or brand PDF; the agent reads the answers off it and asks for confirmation
— still asking what the brand *is*, never proposing what it should be (§6.4b).

1. Name, wordmark text, website; logo files if any (skip → text wordmark, no mark)
2. The one idea: what the company does in one sentence; the image it would hang on a wall
   (free text into `BRAND.md`; drives no derivation)
3. **Not skippable.** The page colour, the text colour, the one colour that means "this
   matters". A second emphasis colour goes to figures only (the two-inks split); a third
   is refused with the reason
3b. Optional: a dark triple (else derived, D15)
4. Optional: a colour for warnings (skip → the engine's red)
5. Typeface with an embeddable licence (skip → D-DIN)
6. Who reads the documents; what must never leave the building → `compliance.md`,
   `legal/`; the terms list is created by the OR-8 flow at `~/.lumi/terms/`
7. Voice: three things always said, three never said (skip → nothing added)

**Derive / ask / inherit:**

| Tokens | Source |
|---|---|
| `--bg`, `--nw`, `--acc` (+ `--acc-live` for a second emphasis colour) | asked (Q3) |
| `--seal` | asked (Q4) or engine red |
| text ladder, rule ladder (engine alphas from `engine-tokens.json`), `--card-bg`, ramp `--acc-1..5` (OKLCH lightness steps), `--acc-tint/-wash/-deep`, `--on-acc*`, the dark palette (D15) | **derived and measured** against `floor_text` / `floor_ui`; a failing pair is reported with the two-inks offer and left empty — never substituted |
| `--d-blue/-red/-teal` | inherited (CVD-validated engine default) unless the brand names its own; a named triple is **reported, not CVD-checked** (no CVD model ships; IDEA at R1) |
| `--lime`/`--on-lime`, `--amber`, `--brass`, `--seal` when Q4 is skipped | **derived, never inherited**: lime/amber/brass from the accent ramp, seal = the engine's red copied in; required values because `layouts.css` references them without fallbacks |
| region palette, shape fallbacks, marks, `contrast.measured` | regenerated per pack |

`new_brand.py` refuses a relative `--out`, prints every absolute path it wrote, runs
`build_region_palette --brand` and refuses on a floor miss. Output contract: `new_deck.py`
renders under the new pack with zero `differs`; `--check` green; `~/.lumi/brand` written only with
`--activate` (the user's say-so); the OR-8 terms instruction printed, nothing written there; `build_entrypoints.py --brand` writes the two D9 files; one preview page
from the fixture's content in the new colours.

Tiers: `full` runs all of it. `files` and `prompt` conduct the interview and return
`brand.json`; the operator runs `new_brand.py --from brand.json` once; thereafter the files
tier reads the resolution order from SKILL.md and the prompt tier pastes `core-prompt.md`.
README says so plainly.

## 4b. First run, update check, review hook

**First run.** `doctor.py` (§3) then a **first document**: three facts from the user rendered
into the gallery's sales scene, checks run, graded report shown. Files/prompt tiers run it
without the checks and name the checks they owe.

**Default vs on request.** Every session: `brand.py --print` (no model tokens) and the
update check when the stamp date changed. First session: `doctor.py`'s environment half. On
request: the interview, the first document, the gallery render, `--upgrade`, any fetch.
On a provider the registry marks `quota_limited`: the four-check loop never by default; the
first document replaced by the gallery.

**Creating content.** No mechanism added; the SKILL.md workflow is the reliability story.
README's "basic workflow" states the beats in the user's terms; the build report keeps one
shape — beat reached, gates, grade, what was dropped.

**Update check, never update.** Silent auto-pull declined (AG entry at R1): traces record
`skill_version`, `ledger.py` reports stale recipes, convention 17 diffs rebuilds; the `full`
tier executes `scripts/`; marketplaces update their own plugins. `doctor.py` names the newer
version and the pull command and changes nothing.

**Review hook.** Reviewing an existing document is a third entry path with its own
form/content line — its own spec (IDEA at R1). Brand packs provide the meta it needs.

## 4c. Conformance on a non-default pack (R5)

`conformance/tasks/T4-brand.json`, `min_capability: full`, `environment: {LUMI_BRAND: acme,
LUMI_BRAND_HOME: ${WORKDIR}/.lumi}` — the driver expands `${WORKDIR}` and copies
`tests/fixtures/brands/acme/` to `${WORKDIR}/.lumi/brands/acme/`, inside the directory every
driver already hands the agent. Prompt: *scaffold with
`new_deck.py`, build a six-page deck for a fictional programme, run the checks until clean;
do not name the brand — the skill resolves it.* Expected: meta `acme`, D20
`compared > 0, differs 0`, zero occurrences of `lumivate`, the footer carries acme's site.
Planted red on one real agent before the task ships: `LUMI_BRAND_HOME` at a missing path →
`brand.py --print` exits 2, the agent stops, the transcript names the pointer (with no pointer
there is no scaffold and therefore no document — "no meta → UNMEASURABLE" is the checker's
red, not a driven one). A platform whose transcript shows LUMIVATE instead is recorded as
**not inheriting the environment** in a `note` field on its `history.json` row, printed by
`report`, not as failing the task. Drivers: Claude Code, Hermes, Cursor (D12).

## 5. Gallery and README

Scenes per D8, synthetic data, `check_deliverable`-green through the evidence gate,
rendered by `build_gallery.py` at the design viewport, 1×, cover + one content page.
README order: pitch → gallery → install per platform → the basic workflow → bring your own
brand (pointer to the interview) → what's inside → philosophy → licence. README's brand
prose is one paragraph linking to `BRAND.md` (guard in §3).

## 6. Directory renames (compatibility pairs)

| Now | Then | Pair |
|---|---|---|
| `tokens/` | pack `theme/` + engine `layouts/` | R2a / R2b |
| `assets/` | pack `assets/` + engine `library/` | R3a / R3b |
| `references/` | `rules/` | R7 |
| `adapters/` | `platforms/` | R7 |

**a**: new path live; old path kept as a tracked copy held by a parity guard (`layouts.css`
byte-identical; theme as `css_vars(old) == css_vars(theme) ∪ css_vars(register)`);
`check_path_mentions` WARNs on the old prefix; external recipes migrated (`ledger.py` reports
them stale). **b**: old path deleted, WARN → FAIL, evidence prefixes dropped. Never a symlink.

## 7. Releases

The nine steps below are the shape; the plan names the ~18 commits they decompose into
(one commit per release, rebase-merged, 8–9 PRs). Each commit: `preflight.py`, a planted
red recorded in its CHANGELOG entry, evidence `--init/record`.

1. **R1a** `brand.py` (with the bridge); `check_path_mentions`; registry shrink;
   `.gitignore`; synthetic pack `tests/fixtures/brands/{acme,acme-broken}`; ledger entries
   (GAP Gemini, AG auto-update, IDEA review path / register re-tune / user-pack CI).
2. **R1b** `check_brand_pack` (R1 rows); logo + legal; `build_brand --wordmark` + lock
   re-stamp; `check_platform_manifest` `ships`; `check_privacy` meta scan; `build_brand_inventory`;
   `TOUCH_MAP` `brands/`; `new_deck.py` reads site/wordmark from the pack.
3. **R2a-i** `layouts/` + pack `theme/` + `build_region_palette --brand`; `preamble()`
   assembles; `meta_tag`; D20/D23 undefaulted; bridge deleted; `tokens/` parity guard.
4. **R2a-ii** guard rewiring (versions → `ENGINE_STAMPS` with `release.py` + its test;
   parity; var; retired; layout; media; probe; region; eval-inventory; fixtures; evidence
   prefixes + `spec_lines_changed`).
5. **R2a-iii** conformance surface, entry-point generators, `platforms.json`, prose sweep.
6. **R2b** `tokens/` deleted.
7. **R3a-i** `library/`, two locks, `lock.py` signature, `check_engine_lock`.
8. **R3a-ii** `embed_font`, `build_brand --brand`, `recolor_shapes`, `brand-*` rename,
   mark regeneration + `--relock`, `globe-js` evidence.
9. **R3a-iii** output-dir pattern, prose sweep.
10. **R3b** `assets/` deleted.
11. **R4** voice + compliance; `BRAND.md` prose move with ids; trace widened; `M4b`.
12. **R5-i** interview file, `new_brand.py`, `palette_derive.py` (maths in `color_math`).
13. **R5-ii** `build_entrypoints --brand` (refuses targets under `ROOT`), driver `env=`,
    T4-brand driven on Claude Code / Hermes / Cursor, SKILL.md / AGENTS.md / core prompt
    re-flowed, `PROMPT_MUST_CARRY` gains the meta rule.
14. **R6-i** `doctor.py`, trace `brand` + ledger reader, AG entry, SKILL.md step 0.
15. **R6-ii** gallery, `build_gallery.py`, `check_gallery`, `check_readme_brand_prose`,
    README rewrite, `fresh-clone` obligation.
16. **R7** `references/ → rules/` pair, `adapters/ → platforms/` pair (four commits).

No new brand-shaped design gate lands between R1 and R4 without its inventory row (§9).

## 8. Verification (end to end, after R6)

- Fresh clone; `preflight.py` green; `git check-ignore brands/acme/x` ignored,
  `brands/registry.json` not.
- `new_deck.py` under LUMIVATE → meta `lumivate`, footer lumivate.io, `check_deliverable` green.
- Synthetic pack under `LUMI_BRAND_HOME`: `new_deck.py` → zero `differs`, zero `lumivate`,
  footer carries its site, no mark; region palette re-measured; `check_prose` applies its
  `voice.md`; one `@font-face`; D23 ceiling 1.
- Pointer holding a path → refused. Missing id → raises; `--print` exits 2 naming it. No meta
  → UNMEASURABLE. Typed `lumivate` over the synthetic palette → D20 fails on values.
- Owner's machine with the pointer on the synthetic pack: `preflight.py` green (pinned by a
  test that sets `LUMI_BRAND=acme` and asserts the guards' output is unchanged).
- Edit a scene html, `theme.css`, `layouts.css` or a font without rebuilding → `check_gallery` red.
- `scripts/ops/verify_brand_packs.py` runs every machine-checkable line above and is the
  `brand-e2e` evidence command; the browser lines stay operator steps.
- Engine lock / pack lock reds. `--din` declared in a pack → var guard red.
- `build_entrypoints.py --brand acme` writes two files under `LUMI_BRAND_HOME`; `git status`
  in the checkout unchanged.
- `doctor.py` with the network cut → one line, exit 0, under 5 s; without `.git` → names the
  platform's updater.
- T4-brand green on Claude Code, Hermes, Cursor; the two planted reds recorded.
- Conformance `validate` + one `run --drive` on the default pack.
- Open each gallery HTML over `file://` and look (convention 8).

## 9. Engine/brand inventory (generated)

`scripts/build/build_brand_inventory.py` → `rules/brand-inventory.md`, `--check` in CI: one
row per checker metric and per token — engine, brand, or brand-with-engine-floor — read from
the code. The precondition for any new design gate after R1.

## 10. Review record and non-goals

**Round 1 (red/blue):** no default brand in `declared()`; meta id-only; `privacy_terms` out
of the pack (OR-8); three-way theme split; `check_path_mentions` replaces the `claim_sweep`
claim; `check_evidence` row; two locks; storylines and ban list stay engine; no inherited
identity; generated files never inherited; compatibility pairs; per-brand prompt by
generation; user-pack version story; scaffold head from the pack; checkers never read
`active()`; `brands/*` ignored; the inventory.
**Platform round (Hermes/Cursor/Gemini):** agents never read packs (D11); `--print`;
bounded, non-fatal `doctor.py`; default/on-request split; T4-brand; Gemini deferred (D12).
**Round 3 (red + plan-readiness):** the theme digest **removed** (D13 — a self-computed hash
proves nothing); pointer id-only with `LUMI_BRAND_HOME` (a user id was unresolvable);
D22 off the brand list; R1/R2a re-cut with a bridge and per-release evidence prefixes; §2.1's
Cursor/Hermes slots dropped (Cursor has no user-level rules directory; a sibling Hermes
skill is a second source); `--print` format fixed; `--din` composed engine-side from
pack-side face names; `engine_version` in `brand.json` only with `ENGINE_STAMPS`; lock
verifier named and `--relock`; `check_brand_pack` presence-only; gallery digest over every
render input; fixtures write the meta via `meta_tag`; driver `env=` per task; `quota_limited`
from the registry; README guard; synthetic `BRAND.md` examples; `M4b`; explicit
`INHERITABLE`; `output_dir` explicit (D14); dark palette rule (D15); `fresh-clone`
obligation; ~18 commits named.
**Round 4 (red + blue on spec and plan):** bridge split so the marks survive until R3a; three
CI readers of `tokens/` rewired in R2a; D23 reads theme ∪ register; the four shipped faces; the
"optional" tokens made required derived values (46 fallback-free references); `fresh-clone`
withdrawn, `brand-e2e` added; traces migrated when `brand` joins the schema; `${WORKDIR}` in
the driver; no `answers` on shipped packs; leaf-only `output_dir`; fenced markers in the core
prompt; `LUMI_BRAND_HOME` covers the terms directory; all code citations by function name
against 0.1.553.

**Non-goals** (ledger ids assigned in R1a's CHANGELOG entry and cited here then): multi-brand
in one document; inheritance deeper than pack → LUMIVATE; CI checking user packs; re-tuning
the type register for non-D-DIN faces; per-brand fixtures; a marketplace `metadata.tagline`;
the review entry path; silent auto-update; Gemini validation; the repo's own Cursor `.mdc`
lacking frontmatter (a generated-artifact defect independent of brands — its own IDEA); a CVD
check for a brand-named chart triple (its own IDEA).

## Self-review

No placeholders but the ledger ids (convention 10 assigns them at the release). §1.1, §2, §3
agree on `theme/` values, `layouts/` engine, generated-never-inherited, one declaration per
property. Every §8 line has a §3 row. Counts are measurements or owner decisions whose
authority file is named.
