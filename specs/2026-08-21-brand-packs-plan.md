# Brand packs · plan

Date 2026-08-22 · Design: `2026-08-21-brand-packs-design.md` (revision 3) · Status: **proposed**

> For agentic workers: execute task-by-task with `superpowers:subagent-driven-development`
> or `superpowers:executing-plans`. Steps use `- [ ]` checkboxes. Read the design first; this
> file argues from it and does not restate its decisions (D1–D15).

**Goal.** lumi-style becomes a multi-brand skill: LUMIVATE ships as the reference pack
`brands/lumivate/`, a user's brand lives at `~/.lumi/brands/<id>/`, every producer and checker
resolves the brand through one module, and `tokens/` / `assets/` dissolve into pack `theme/` +
engine `layouts/` / `library/` through compatibility pairs.

**Architecture.** `scripts/lib/brand.py` is the only module that knows where a brand lives;
producers call `active()`, checkers call `declared(html)`, CI guards loop `shipped()`. Engine
facts never live in a pack file (three-way split, design §1.1), so inheritance is file-level
over an explicit `INHERITABLE` list and nothing merges. Every move is a pair: new path live
+ old path held by a parity guard, then delete.

**Tech.** Python standard library only on the deliverable path (CLAUDE.md). Dev tools:
pytest, ruff, mypy, Playwright for operator steps.

## Global constraints (from the design and CLAUDE.md; every step inherits them)

- One commit per release, cut by `scripts/ops/release.py` (preflight green, no override);
  branch `brand-packs` off `main`; rebase-merged, never squashed. Versions are assigned at
  landing; this file names steps, never version numbers.
- Every new gate ships with a planted red recorded in its CHANGELOG entry (convention 11),
  planted **first** (convention 15). Guards get synthetic-tree tests with a failing fixture
  (`tests/test_check_repo_guards.py` pattern: `monkeypatch.setattr(check_repo, "ROOT", tmp)`).
- A new `scripts/lib` module is added to `SIBLING_MODULES` (`check_repo.py:2528`) and uses
  the canonical bootstrap block; a new guard is a function + a `CHECKS` row
  (`check_repo.py:3458`); every argparse script inherits the `--help` floor automatically.
- Repository prose is English only. No engagement facts; `BRAND.md` examples are synthetic.
- `check_path_mentions` (Step 1) runs before every later commit; `claim_sweep.py` is run and
  read for counts.
- Evidence: `check_evidence.py --init` then `record --id X` for each obligation the diff
  triggers; a prefix enters `TOUCH_MAP` only in the release that creates its directory.
- New ledger entries are named by **title** here and get their ids when opened in Step 1
  (the `ledgers` guard scans `specs/`, so an id may be cited only once it exists): the GAP
  "Gemini CLI is supported by construction and validated by nothing", the abandoned
  mechanism "Silent auto-update of the installed skill", and the IDEAs "The review entry
  path", "Re-tune the type register for non-D-DIN faces", "CI checks for user packs", and
  "`.cursor/rules/lumi-style.mdc` has no YAML frontmatter". The design's §10 line is edited
  to cite the ids in the same commit.

Each step lists **change · interfaces · red run · tests · ledger · evidence**.

---

## Step 1 · R1a — the resolver, the path guard, the synthetic pack

- change:
  - **Create `scripts/lib/brand.py`** (stdlib; bootstrap block; added to `SIBLING_MODULES`).
  - **Create `scripts/check/check_repo.py::check_path_mentions`** by generalising
    `check_script_paths` (`check_repo.py:2476-2525`): same `git ls-files` walk, same
    `SCRIPT_PATH_FROZEN` exclusions, regex
    `PATH_MENTION_RE = re.compile(r"\b(tokens|assets|references|adapters|layouts|library|brands|rules|platforms)/[\w./-]*[\w]")`,
    `PATH_MENTION_WAIVERS: dict[tuple[str, str], str] = {}`, `PATH_MENTION_WARN_PREFIXES:
    tuple[str, ...] = ()` (a mention under a warn prefix is printed as `WARN` and does not
    fail). A mention resolving to neither file nor directory fails naming file:line. CHECKS row
    `("path mentions", check_path_mentions)`.
  - `brands/registry.json` → `{"$comment": …, "schema": 2, "default": "lumivate",
    "brands": {"lumivate": {"path": "brands/lumivate"}}}`; `check_brand_registry` `ALLOWED =
    {"path"}`, its path loop checks `path` is a directory.
  - **Create `brands/lumivate/brand.json`** (design §1 schema; `policies` omitted until
    Step 2 names URLs; `engine_version` = current SKILL.md version) and a short
    `brands/lumivate/BRAND.md` (name, the one idea in one synthetic paragraph, the two devices
    named, link to `references/brand.md` — no `BR-*` ids until Step 11).
  - **Create `tests/fixtures/brands/acme/`**: `brand.json` (`id: acme`, `name: Acme Analytics`,
    `site: www.acme.example`, `output_dir: Documents/Acme`, one font, no `logo`, no
    `cover_mark`, `engine_version` current), `theme/theme.css` + `theme/theme.json` (ground
    `#FAF7F2`, ink `#1A1A2E`, accent `#7A1F3D`; same variable names as LUMIVATE, different
    values; **no** `--din`), `assets/fonts/Acme-Regular.woff2` (copy of `D-DIN.woff2`) +
    `COPYING.txt`, `legal/privacy.md` (one URL line), `voice.md` (`## Never` two phrases,
    `## Favour` one), `compliance.md`, `BRAND.md` with one `BR-*` id, `assets/LOCKED.json`
    (written by `lock.update`). **And `tests/fixtures/brands/acme-broken/`**: `privacy-terms.txt`,
    `logo.light` pointing at a missing file, `theme.json` with one hex differing from its CSS,
    `theme.css` declaring `--din`.
  - `.gitignore`: `brands/*`, `!brands/lumivate/`, `!brands/registry.json`,
    `!brands/lumivate/**/*.svg`, `!brands/lumivate/**/*.woff2`, `!tests/fixtures/brands/**`.
  - `scripts/ops/new_deck.py`: `wordmark()` (`:198`) and `foot()` (`:382`) read
    `brand.active().json()["wordmark"]` / `["site"]`; `BRAND_GLOBE` (`:212`) becomes
    `brand.active().path("assets/marks/globe-field.svg")` through the bridge.
  - Ledger entries (ids above) in their files' formats; design §10 cites them.
  - `CLAUDE.md` checks list: `brand.py --print`; one paragraph in `SKILL.md` "Cross-platform"
    with the resolution order as prose and D11's stop rule.
- interfaces (produced; later steps rely on these names exactly):
  ```python
  # scripts/lib/brand.py
  INHERITABLE = ("compliance.md", "assets/fonts/")
  TOKENS_BRIDGE = {  # shipped pack only; deleted in Step 3
      "theme/theme.css": "tokens/lumi-theme.css",
      "theme/theme.json": "tokens/design-tokens.json",
      "theme/region-palette.css": "tokens/region-palette.css",
      "theme/region-palette-trade.css": "tokens/region-palette-trade.css",
      "assets/marks/globe-field.svg": "assets/brand/lumivate/globe-field.svg",
      "assets/marks/globe-cover.svg": "assets/brand/lumivate/globe-cover.svg",
      "assets/marks/globe-cover.dark.svg": "assets/brand/lumivate/globe-cover.dark.svg",
      "assets/fonts/": "assets/fonts/",
  }
  class BrandError(Exception): ...
  class Unmeasurable(Exception): ...          # carries .reason
  @dataclass(frozen=True)
  class Pack:
      id: str; root: Path; shipped: bool
      def json(self) -> dict: ...             # brand.json; fonts default to D-DIN (D7); no identity defaults (D10)
      def path(self, rel: str) -> Path: ...   # own file; INHERITABLE → default pack; bridge for shipped; else BrandError
  def home() -> Path: ...                     # $LUMI_BRAND_HOME or ~/.lumi
  def registry() -> dict: ...                 # brands/registry.json (moved here from build_entrypoints.registry)
  def shipped() -> list[Pack]: ...
  def default() -> Pack: ...
  def resolve(brand_id: str) -> Pack: ...     # registry, then home()/brands/<id>; a path-shaped id → BrandError
  def active(flag: str | None = None) -> Pack: ...  # flag → $LUMI_BRAND → home()/brand → default(); raises BrandError
  def declared(html: str) -> Pack: ...        # <meta name="brand" content="id">; else raises Unmeasurable
  def meta_tag(pack: Pack) -> str: ...        # '<meta name="brand" content="{id}">'
  # CLI: python3 scripts/lib/brand.py --print [--brand ID]
  #   exit 0: 'brand: <id>  home: <abs>  engine_version: <v>'   exit 2: one line naming the missing pointer
  ```
- red run (planted first): a stale line `see tokens/old-theme.css` in AGENTS.md → `path
  mentions` red naming the line; `~/.lumi/brand` holding `/abs/path` → `active()` raises
  "an id, not a path"; `LUMI_BRAND=ghost` → `--print` exits 2 naming `~/.lumi/brands/ghost`;
  `acme-broken` is not in the registry, so nothing reads it yet (it is Step 2's red).
- tests: `tests/test_brand.py` — resolution order (flag > env > pointer > default), path-shaped
  id refused, missing id raises, `declared()` without meta raises `Unmeasurable`,
  `Pack.path` falls back only for `INHERITABLE`, bridge resolves for `lumivate`, `--print`
  via subprocess with `LUMI_BRAND_HOME=tmp_path` and both exit codes; `tests/conftest.py`
  gains `acme_pack` (copies the tracked fixture to `tmp_path/.lumi/brands/acme`, sets
  `LUMI_BRAND_HOME`, `LUMI_BRAND`); `tests/test_check_repo_guards.py` — `check_path_mentions`
  passing tree, failing tree, warn-prefix tree; registry guard with `path` only and with an
  extra key; `tests/test_housekeeping.py` — `git check-ignore brands/acme/x` is ignored,
  `brands/registry.json` and `tests/fixtures/brands/acme/brand.json` are not; `test_new_deck.py`
  runs the scaffold under `acme_pack` and asserts the footer carries `www.acme.example`.
- ledger: opens the six entries named above (drafts in §Ledger below).
- evidence: `SKILL.md` touched → `conformance-freshness` if the board trails; nothing else.

## Step 2 · R1b — the pack guard, logo and legal, the manifest and privacy holes

- change:
  - **`check_brand_pack`** (CHECKS row `("brand packs", check_brand_pack)`): for each
    `brand.shipped()`: required keys `schema id name site output_dir engine_version`; every
    declared path resolves (pack-relative); `policies.*` is an existing file or a URL that
    parses; `logo.*` exist iff declared; no file matching `*terms*` anywhere under the pack;
    `engine_version` equals SKILL.md's; every pack file appears in `git ls-files`
    (`_tracked_stems` at `:3293` is the pattern). Lock and generated-file rows arrive in
    Steps 3 and 7.
  - `scripts/build/build_brand.py --wordmark`: renders `assets/logo/wordmark.svg`,
    `wordmark.dark.svg` (text-set from `brand.json.wordmark`, the pack's face, `--nw` / dark
    ink) and `mark.svg` (the field globe's static frame via `globe_svg.py`); `build_brand.py`
    is hash-locked → `python3 scripts/lib/lock.py --update "wordmark generator"` in the same
    commit. `brand.json` gains `logo` and `policies` (URLs the owner names; if none are named
    at execution time, `policies` stays omitted and this is recorded in the CHANGELOG entry).
  - `check_platform_manifest` (`:1697`): every `capabilities.<tier>.ships` entry resolves to
    a file or directory.
  - `check_privacy.py`: before `reader_text()` strips tags (`:107`), scan
    `<meta name="brand" content="…">` and every `content="…"` attribute for
    `/Users/`, `/home/`, `C:\`, `~/` — a hit is a finding.
  - **Create `scripts/build/build_brand_inventory.py`** on the `build_eval_inventory.py`
    pattern: one row per `check_design` metric id (from `gating.metric_ids`) and per custom
    property in the shipped theme, classified `engine` / `brand` / `brand with engine floor`
    by where its authority file lives; writes `references/brand-inventory.md`; `--check` in
    `ci.yml` and `release.py` `GENERATORS`.
  - `check_evidence.TOUCH_MAP` += `("brands/", ("layout-fixtures", "conformance-freshness"))`.
- interfaces: `check_brand_pack() -> list[str]`; `build_brand.py --wordmark --brand ID`;
  `build_brand_inventory.py [--check]`.
- red run (planted first): point the registry at `tests/fixtures/brands/acme-broken` in a
  temp tree → three findings (terms file, dangling logo, — the hex mismatch is Step 4's);
  delete `legal/privacy.md` with `policies.privacy` declared → red; `ships: ["nonexistent/"]`
  → manifest red; `<meta name="brand" content="/Users/x/b">` in a fixture copy →
  `check_privacy` finding; hand-edit `references/brand-inventory.md` → `--check` red.
- tests: `test_check_repo_guards.py` — `check_brand_pack` on a synthetic tree with
  `acme` (green) and `acme-broken` (each finding named), manifest `ships` case;
  `tests/test_check_privacy.py` meta-path case; `tests/test_build_brand_inventory.py`
  (`--check` detects a hand edit).
- ledger: none new; CHANGELOG cites the `.mdc` frontmatter IDEA (seen here, not fixed here).
- evidence: `brands/` → `layout-fixtures` (records green in seconds; nothing rendered
  changed).

## Step 3 · R2a-i — `layouts/` and the pack theme; the scaffold assembles its head

- change:
  - **Create `layouts/register.css`** (stamp `/* LUMI register · vN */`): `--fs-*`, `--w-*`,
    `--lh-*`, `--ls-*`, `--din: var(--face-body), "PingFang SC", "Hiragino Sans GB", "Noto Sans SC", Arial, sans-serif`,
    `--mono: var(--face-mono), "SFMono-Regular", Menlo, monospace`, `--ground-ceiling`,
    `.scope-note`. **Create `layouts/engine-tokens.json`** (`"version"`): `retired`,
    `layout`, `typography`, `contrast.floor_*`, region parameters, `text_ladder` /
    `rule_ladder` alphas. **`git mv tokens/lumi-layouts.css layouts/layouts.css`** and re-add
    a tracked copy at `tokens/lumi-layouts.css` for the pair.
  - **Create `brands/lumivate/theme/theme.css`** (no stamp; palette light + dark, ladders,
    ramp, washes, `on-*`, `lime`/`seal`/`amber`/`brass`, chart triple, `--face-body: 'D-DIN'`,
    `--face-mono: "IBM Plex Mono"`) and **`theme.json`** (`palette`, `palette_default`,
    `chart`, `chart_scale_px`, `contrast.measured`). `tokens/lumi-theme.css` and
    `tokens/design-tokens.json` stay as the pair's old half.
  - `scripts/build/build_region_palette.py --brand ID`: ink/bg from `Pack.path("theme/theme.css")`
    via `css_tokens.rule_vars`; writes `theme/region-palette*.css` into the pack; `--check`
    loops `shipped()`; its `oklch_to_srgb`, `lab_of`, `ciede2000`, `max_chroma` move into
    `scripts/lib/color_math.py` first (the `no shadow math` guard). Acme's palettes generated
    into the fixture.
  - `scripts/ops/new_deck.py::preamble()` (`:335-372`): stops slicing the fixture; emits
    `brand.meta_tag(pack)` then `<style>` blocks in the order theme.css, register.css,
    layouts.css, region-palette.css, region-palette-trade.css, then `embed_font.css()`.
  - `check_design.py` D20 (`:1697-1746`): `pack = brand.declared(html)`; `Unmeasurable` →
    `UNMEASURABLE`, exit non-zero; compares against `pack.path("theme/theme.css")`. D23
    (`:1451`) reads the same file. `build_fixtures.py` (`:186-244`) lifts
    `brand.default().path("theme/theme.css")` + `layouts/*.css` and writes `meta_tag`;
    fixtures regenerated; `expected.json` unchanged.
  - `brand.py`: `TOKENS_BRIDGE` deleted.
  - New guard `("tokens pair", check_tokens_pair)`: `css_vars(tokens/lumi-theme.css) ==
    css_vars(theme.css) | css_vars(register.css)` and `tokens/lumi-layouts.css` byte-identical
    to `layouts/layouts.css`. `PATH_MENTION_WARN_PREFIXES = ("tokens/",)`.
  - `check_evidence`: `TOUCH_MAP` += `layouts/`, `brands/lumivate/theme/` → `layout-fixtures`;
    `STAMPED_PREFIXES` += the new stamped files; `spec_lines_changed` += `layouts/`.
- interfaces: `brand.declared()` now consumed by `check_design`; `build_region_palette.py
  --brand ID [--check]`; `color_math.oklch_to_srgb(L, C, h) -> tuple[int,int,int]`,
  `color_math.ciede2000(lab1, lab2) -> float`.
- red run (planted first): scaffold under `acme_pack` → D20 `compared > 0, differs 0`,
  `grep -c lumivate` = 0; copy acme's `theme.css` block into a document declaring `lumivate`
  → D20 fails on values; remove the meta → UNMEASURABLE, exit non-zero; delete
  `tokens/lumi-theme.css` → D20 on a LUMIVATE document still green (it no longer reads it);
  edit one hex in `tokens/lumi-theme.css` only → `tokens pair` red; acme ground changed to
  `#FFFFFF` and palettes not regenerated → `build_region_palette --check` red.
- tests: `test_new_deck.py` every existing test also under `acme_pack`; head order asserted;
  `test_check_design_units.py` D20 three-way + D23 one-face; `test_build_region_palette.py`
  `--brand` against the acme fixture (floors hold; an off-white ground re-measures);
  `test_color_math.py` for the lifted functions against `build_region_palette`'s recorded
  values; guard test for `tokens pair`.
- ledger: none.
- evidence: `layout-fixtures` (fixtures regenerated), `conformance-freshness` if stale.
  The CHANGELOG entry states that every existing deliverable is UNMEASURABLE on D20 until
  rebuilt (design §3 "Existing deliverables"); `ledger.py` reports it.

## Step 4 · R2a-ii — guards rewired to the new files

- change: `check_versions` (`:158`) reads `ENGINE_STAMPS` — `layouts/register.css`,
  `layouts/layouts.css`, `layouts/engine-tokens.json` (`"version"`), plus one row per shipped
  pack `brand.json` (`"engine_version":\s*"(\d+\.\d+\.\d+)"`); `release.py:49` import and
  `tests/test_release_tool.py:30` renamed in the same commit; `check_palette_parity`
  (`:626`) loops `shipped()`, floors from `engine-tokens.json`, measured from each
  `theme.json`; `check_token_references` (`:795`) — `layouts/*.css` ∪ one shipped theme at a
  time, plus the one-declaration rule (a name defined in both sides is red);
  `check_retired_values` (`:1534`), `check_media_only_rules` (`:1131`), `_shipped_classes`
  (`:993`), `check_layout_parity` (`:1185`), `check_region_coverage` (`:1931`),
  `build_eval_inventory.py:214` → the new files; `TOKEN_STAMPS` removed.
- interfaces: `ENGINE_STAMPS: tuple[tuple[str, str], ...]` (path, regex) in `check_repo.py`,
  imported by `release.py`.
- red run (planted first): stamp drift in `register.css`; `retired` block removed from
  `engine-tokens.json` → red not vacuous; `--din` declared in `acme-broken`'s theme → var
  guard red; acme-broken's hex mismatch → parity red; a `var(--nothing)` in `layouts.css`.
- tests: every `_version_tree`/`_palette_tree` helper in `test_check_repo_guards.py` rewritten
  to the new layout; a `_brand_tree(tmp_path)` helper (registry + one pack) joins them;
  `test_release_tool.py` authority-set assertion updated.
- ledger: none. · evidence: none new.

## Step 5 · R2a-iii — the surfaces that restate paths

- change: `run_conformance.SKILL_SURFACE` (`:131`) from `brand.default()` + `layouts/`;
  `build_entrypoints.render_note` (`:144`) and `render_pointer` (`:187`) name `layouts/` and
  the pack, regenerate all artifacts; `platforms.json` `capabilities.*.ships` → `layouts/`,
  `brands/lumivate/`; prose sweep of `SKILL.md`, `AGENTS.md`, `prompts/lumi-style-core.md`,
  `README.md`, `CLAUDE.md` (convention 3's "three `tokens/` files" sentence), `scripts/README.md`,
  `references/design-rules.md`; the 14 external recipes under `~/Documents/LUMI-Style/_sources`
  migrated by the operator (`ledger.py` reports them stale until then).
- red run: after the sweep, one deliberately left `tokens/` mention → `path mentions` WARN
  (not fail — the pair is live); `run_conformance.py validate` green.
- tests: `test_conformance_driver.py` `SKILL_SURFACE` case; `build_entrypoints --check`.
- ledger: none. · evidence: `conformance-freshness`.

## Step 6 · R2b — `tokens/` deleted

- change: `git rm -r tokens/`; `check_tokens_pair` removed; `"tokens/"` leaves
  `PATH_MENTION_WARN_PREFIXES`; `TOUCH_MAP`/`STAMPED_PREFIXES`/`spec_lines_changed` lose
  their `tokens/` rows; `.gitignore` comment pruned.
- red run: a `tokens/` mention left in a docstring → `path mentions` FAIL.
- tests: guard test that a former warn prefix now fails. · evidence: none new.

## Step 7 · R3a-i — `library/` and two locks

- change: `git mv` of `assets/{icons,shapes,vectors,geo,globe,regionmap,logos,frameworks.json}`
  → `library/`, tracked copies left under `assets/` for the pair; `assets/fonts/` and
  `assets/brand/lumivate/*` → `brands/lumivate/assets/{fonts,marks}`; `scripts/lib/lock.py`:
  `verify(lock_path: Path, base: Path) -> list[str]`, `update(lock_path, base, why)`; engine
  lock `library/LOCKED.json` (runtime `.js`, `build_brand.py`, `globe_svg.py`); pack lock
  `brands/lumivate/assets/LOCKED.json` (marks, logo); `check_brand_lock` → **`check_engine_lock`**;
  `check_brand_pack` gains the pack-lock row; `check_assets_tracked` (`:3308`) scoped to
  `library/` ∪ shipped packs; `.gitignore` re-admits `library/**` (svg, woff2); `TOUCH_MAP`
  `assets/geo|globe/` → `library/geo|globe/` (old rows kept for the pair);
  `PATH_MENTION_WARN_PREFIXES += ("assets/",)`; an `assets pair` guard (byte-identical trees).
- red run: move `library/globe/globe.js` → engine lock red; edit a mark → pack lock red;
  an untracked svg under `library/icons/`.
- tests: `tests/test_lock.py` (two locks in one tmp tree, both bases); guard tests.
- evidence: `globe-js` (runtime moved), `layout-fixtures`.

## Step 8 · R3a-ii — generators learn the pack

- change: `embed_font.py` faces from `active().json()["fonts"]`, sizes from the pack lock;
  `build_brand.py --brand ID` emits `brand-mark` classes and `aria-label` from
  `brand.json.name`; `--relock "<why>"` rewrites the pack lock and refuses if the engine lock
  is red; marks regenerated; `recolor_shapes.py` writes `var(--token)` without literal
  fallback, mapping computed once against `brand.default()`; `lumivate-*` classes → `brand-*`
  in `layouts.css`, fixtures, `inspect_layout.py` probes.
- red run: acme (one face) → one `@font-face`, D23 ceiling 1; generated mark under acme
  contains no `lumivate`; a shape with a literal hex → `recolor_shapes --check` red;
  `--relock` with a planted engine-lock drift → refuses.
- tests: `tests/test_embed_font.py` (new), `test_recolor_shapes.py` fallback case,
  `test_build_brand.py` (class and label under acme).
- evidence: `globe-js`, `layout-fixtures`.

## Step 9 · R3a-iii — output directory and prose

- change: `output_dir.py` reads `active().json()["output_dir"]`; `FOLDER` removed;
  `check_output_default` (`:1889`) holds the five sites to "the pack's `output_dir`" wording
  and `output_dir.py` to the call; prose sweep for `assets/`; `run_conformance._results_root`
  unchanged (LUMIVATE's dir is `Documents/LUMI-Style`, D14).
- red run: a site naming a literal folder → red; `output_dir.py` under `acme_pack` prints
  `…/Documents/Acme`.
- tests: `test_output_dir.py` under both packs; guard test. · evidence: none new.

## Step 10 · R3b — `assets/` deleted

Mirror of Step 6: `git rm -r assets/`, pair guard removed, warn → fail, `.gitignore` loses
its eleven `!assets/…` lines, evidence rows dropped. Red run: the flip.

## Step 11 · R4 — voice, compliance, the brand prose moves

- change: `brands/lumivate/{voice.md,compliance.md}`; `check_prose.py` adds the declared
  pack's `## Never` phrases as `M4b_pack_bans` (literal, case-insensitive; `n/a` with no
  brand); `check_ban_list_parity` (`:1279`) gains the per-pack half (every `voice.md` phrase
  has a pattern); `references/brand.md` §1–2b and §4 + `README.md:143-171` move into
  `brands/lumivate/BRAND.md` with their `BR-*` ids and `Serves:` lines, examples made
  synthetic; `check_rule_ids` (`:386`) and `check_principle_trace` (`:484`) glob
  `references/*.md` ∪ shipped `BRAND.md`; `SKILL.md`/`AGENTS.md` "read brand.md first" →
  the pack's `BRAND.md`; `references/brand.md` keeps §3 (accelerators) and §5 (provenance)
  as engine.
- red run: a phrase in acme's `voice.md` with no pattern → parity red; remove `BR-2` from
  `BRAND.md` → rule-id red; a document under `acme_pack` using an acme-banned phrase → M4b.
- tests: `test_check_prose_units.py` voice case; guard tests.
- ledger: none. · evidence: `conformance-freshness`.

## Step 12 · R5-i — the interview and `new_brand.py`

- change: **Create `references/brand-interview.md`** (design §4: seven questions + 3b,
  parent-principle column, LUMIVATE example per question, plain-language wording);
  **create `scripts/lib/palette_derive.py`** (`derive(ground, ink, accent, *, accent_live=None,
  seal=None, dark=None) -> Theme`: ladders from engine alphas, ramp by OKLCH lightness
  steps, `on-*` by floor, dark palette derived and measured (D15), every pair measured
  against `floor_text`/`floor_ui`; a failing pair reported and left empty — never
  substituted); **create `scripts/ops/new_brand.py`** (`--from brand.json | --answers
  answers.json`, `--out ABS_DIR` (relative refused), `--check`, `--upgrade`; writes the pack,
  runs `build_region_palette --brand`, refuses on a floor miss, prints every absolute path,
  writes `~/.lumi/brand` only with `--activate`, renders one preview page from the fixture's
  content).
- interfaces: `palette_derive.Theme` (`css() -> str`, `json() -> dict`, `report ->
  list[str]`); `new_brand.py` exit 0 / 3 (floor miss, with the two-inks offer in the output).
- red run: an accent failing 4.5:1 as text → exit 3, nothing written, the report names the
  pair; a relative `--out` → refused; `--upgrade` on a pack whose `engine_version` trails →
  regenerated from `answers`, `--check` green.
- tests: `tests/test_palette_derive.py` (floors hit and missed; dark disabled when it cannot
  clear); `tests/test_new_brand.py` (answers → pack → `check_brand_pack` green in a tmp
  tree; refusal paths).
- ledger: the register re-tune IDEA cited (reported by `--check`). · evidence: none new.

## Step 13 · R5-ii — per-brand generation, the driver, T4-brand, the re-flow

- change: `build_entrypoints.py --brand ID` writes `core-prompt.md` (token-block and
  identity substitution over `prompts/lumi-style-core.md`) and `BRAND-POINTER.md` under
  `home()/brands/<id>/generated/`, refusing any target whose `resolve()` is under `ROOT`;
  `run_conformance.drive()` (`:368`) passes `env={**os.environ, **task.get("environment", {})}`;
  **create `conformance/tasks/T4-brand.json`** (design §4c); `SKILL.md`, `AGENTS.md`,
  `prompts/lumi-style-core.md` re-flowed (interview pointer, D11 stop rule, "never hand-type
  the meta"); `PROMPT_MUST_CARRY` gains the meta sentence; T1's prompt gains "scaffold with
  `new_deck.py`".
- red run (on one real agent before the task ships): `LUMI_BRAND_HOME` at a missing path →
  the agent stops and the transcript names it; no brand → UNMEASURABLE and no `lumivate`
  meta; `build_entrypoints --brand` with `LUMI_BRAND_HOME` under the checkout → refused.
- tests: `tests/test_build_entrypoints_brand.py` (nothing lands under `ROOT`);
  `test_conformance_driver.py` env case and T4 validation.
- operator: T4-brand `run --drive` on Claude Code, Hermes, Cursor; `report --record`.
- evidence: `conformance-freshness` (owed and recorded).

## Step 14 · R6-i — `doctor.py`, the trace field

- change: **create `scripts/ops/doctor.py`** (design §3 row: `--platform`, `--force`;
  Chromium/fonts/brand/version; `.git` → `git fetch --dry-run` with `timeout=5`,
  `GIT_TERMINAL_PROMPT=0`; else one line naming the platform's updater; stamp
  `home()/last-update-check`; `quota_limited` from the registry record — `platforms.json` gains that optional boolean, `true` on gemini-cli; always exit 0);
  `trace_schema.FIELDS` += `brand: (str, NoneType)`; `trace.py open` writes `active().id`;
  `ledger.py --board` groups by it; `SKILL.md` step 0 runs `doctor.py` on a session's first
  build; the abandoned-mechanism entry body finalised in `FAILURE_MODES.md`.
- red run: fonts dir missing → reported; `GIT_SSH_COMMAND=false` remote → one line, exit 0,
  under 5 s; a trace with `brand: 3` → schema red.
- tests: `tests/test_doctor.py` (subprocess, `HOME` redirected, elapsed asserted);
  `test_trace.py` brand field; `trace field readers` guard green.
- evidence: none new.

## Step 15 · R6-ii — gallery, README

- change: `brands/lumivate/examples/` — seven scene sources (synthetic facts), **create
  `scripts/ops/build_gallery.py`** (renders cover + p1 via `export_pdf.py` at the design
  viewport, 1×; runs `check_deliverable`; writes `gallery.json` rows: scene, source, evidence
  id, SHA-256 over source html + `theme.css` + `layouts/*.css` + each font in order);
  **`check_gallery`** (index ↔ PNGs ↔ digests, no render); `OBLIGATIONS["gallery"]` =
  `build_gallery.py --check-render`; `OBLIGATIONS["fresh-clone"]` = `git clone . $TMP &&
  preflight` keyed on `.gitignore`; **`check_readme_brand_prose`**; README rewritten in the
  design §5 order; `SKILL.md` gains the first-document flow (three user facts into the sales
  scene, checks, graded report; files/prompt tiers name the checks they owe) and the
  default/on-request table of design §4b; `.gitignore` `!brands/lumivate/examples/*.png`.
- red run: edit `examples/sales.html` without rebuilding → gallery red; a PNG with no row; a
  second brand paragraph in README → red; remove a `.gitignore` re-admission → fresh-clone
  obligation records non-zero.
- tests: `tests/test_check_gallery.py`; guard test for the README rule.
- operator: `record --id gallery`, `record --id fresh-clone`; open each scene over `file://`.
- evidence: `gallery`, `fresh-clone`, `layout-fixtures` if a layout moved.

## Step 16 · R7 — `references/ → rules/`, `adapters/ → platforms/` (four commits)

Each pair on the Step 3/6 template. Sites the pair guard alone will not find, listed so the
"a" commit does not ship them green: `ENTRY_STAMP["references/PRINCIPLES.md"]` (`:1463`),
`check_ledgers`' TODO glob (`:2273`), `PLATFORMS` (`:1428`), `check_evidence.spec_lines_changed`
(`:249`) and `TOUCH_MAP` rows for `references/`, `build_entrypoints.targets()` (`:230`),
`SCRIPT_PATH_FROZEN` unaffected. Red run per "b": a planted stale path.

---

## Ledger drafts (opened in Step 1, in each file's own format; ids assigned then)

- **GAP (next id) · Gemini CLI is supported by construction and validated by nothing** — status
  open · surface `adapters/platforms.json` (gemini-cli), `conformance/tasks/T4-brand.json` ·
  symptom: D11 and the resolver hold for Gemini on paper; its file tools cannot leave the
  workspace and the available key is free-tier (0.1.539: 663 s of quota errors, nothing
  produced) · check: one T4-brand row for gemini-cli in `conformance/history.json` on a paid key.
- **AG (next id) · Silent auto-update of the installed skill** — declined: traces record
  `skill_version`, `ledger.py` reports stale recipes, convention 17 diffs rebuilds, the `full`
  tier executes `scripts/` so an unattended pull across ten agents is the supply-chain shape
  this repository refuses, and marketplaces update their own plugins. `doctor.py` compares
  once per session, read-only, and names the pull command.
- **IDEA · The review entry path** — a third path beside A and B with its own form/content
  line; acceptance: its own design spec and a `<meta name="brand">` reader in the reviewer.
- **IDEA · Re-tune the type register for non-D-DIN faces** — reported by
  `new_brand.py --check`, never gated.
- **IDEA · CI checks for user packs** — local `new_brand.py --check` only; acceptance: a
  decision recorded either way.
- **IDEA · `.cursor/rules/lumi-style.mdc` has no YAML frontmatter** — Cursor applies it
  only when `@`-mentioned; `render_pointer` should emit `description` + `alwaysApply: false`
  and `check_platform_manifest` parse it. Independent of brands.

## Order and dependencies

1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12 → 13 → 14 → 15 → 16. Hard edges: 3
needs 1's `brand.py` and deletes its bridge; 4 needs 3's files; 7 needs 6 (one pair live at a
time keeps `check_path_mentions` readable); 12 needs 3's `color_math` lift; 13 needs 3's
`preamble()` and 12's `new_brand.py`; 15 needs 14's `doctor.py` for the first-run flow it
documents. PR boundaries: {1,2} · {3,4,5} · {6} · {7,8,9} · {10} · {11} · {12,13} · {14,15} ·
{16}. Merge the PR after its last step's CI is green; `main` takes pull requests only.

## Verification at each step

`python3 scripts/preflight.py` (never piped); `python3 scripts/check/claim_sweep.py` read for
the counts touched; `python3 scripts/check/check_evidence.py --init` then `record` for each
obligation; the step's planted red reproduced before its code and its removal recorded in the
CHANGELOG entry; `git -C $(mktemp -d) clone` + preflight on the steps that touch `.gitignore`
(1, 3, 7, 10, 15) until the `fresh-clone` obligation exists at 15. Design §8 is the end-to-end
list run after Step 15 and recorded as a whole in that release's evidence file.
