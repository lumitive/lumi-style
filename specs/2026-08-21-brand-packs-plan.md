# Brand packs · plan

Date 2026-08-22 · Design: `2026-08-21-brand-packs-design.md` (revision 4) · Status: **proposed**
· Code baseline: `main` at **0.1.553** — every citation below is a function or constant name,
never a line number (ten releases landed while this plan was reviewed and every number rotted).

> For agentic workers: execute step-by-step with `superpowers:subagent-driven-development`
> or `superpowers:executing-plans`. Read the design first; this file argues from it and does
> not restate its decisions (D1–D15).

**Goal.** lumi-style becomes a multi-brand skill: LUMIVATE ships as the reference pack
`brands/lumivate/`, a user's brand lives at `~/.lumi/brands/<id>/`, every producer and checker
resolves the brand through one module, and `tokens/` / `assets/` dissolve into pack `theme/` +
engine `layouts/` / `library/` through compatibility pairs.

**Architecture.** `scripts/lib/brand.py` is the only module that knows where a brand lives;
producers call `active()`, checkers call `declared(html)`, CI guards loop `shipped(root)`.
Engine facts never live in a pack file (design §1.1), so inheritance is file-level over
`INHERITABLE = ("compliance.md",)` and nothing merges. Every move is a pair: new path live +
old path held by a parity guard, then delete.

**Tech.** Python standard library on the deliverable path. Dev tools: pytest, ruff, mypy;
Playwright for operator steps.

## Global constraints (every step inherits them)

- **One commit per release**, cut by `scripts/ops/release.py` (preflight green; no override).
  **One branch per PR, created from `main` after the previous PR is merged and pulled**
  (`brand-packs-<first step>`); never stacked, never reused — a rebase merge rewrites SHAs.
  Rebase-merged, never squashed. Versions are assigned at landing; this file names steps.
- Release with `release.py --spec specs/2026-08-21-brand-packs-plan.md` whenever the diff
  exceeds `check_evidence.SPEC_LINE_THRESHOLD`; the CHANGELOG entry cites that path.
- Every new gate ships with a planted red, planted **first** (conventions 11, 15). The
  entry's red-run paragraph opens **Planted red first.**, names the file and line planted,
  quotes the guard's failure line, and names the test that pins it (the shape of the 0.1.541
  and 0.1.545 entries).
- Guards get synthetic-tree tests (`tests/test_check_repo_guards.py`:
  `monkeypatch.setattr(check_repo, "ROOT", tmp)`); a guard that reads through `brand.py`
  passes `ROOT` into `brand.shipped(root=…)` so the same patch reaches it.
- A new `scripts/lib` module joins `SIBLING_MODULES` in `check_repo.py` and carries the
  canonical bootstrap block; a new guard is a function plus a `CHECKS` row; every argparse
  script under `scripts/` is discovered by `tests/test_cli_contracts.py` and must exit 0 on
  `--help` before touching the environment.
- Repository prose is English only; no engagement facts; `BRAND.md` examples are synthetic.
- `check_path_mentions` (Step 1) and `claim_sweep.py` run before every commit; verification
  commands are never piped.
- Evidence: `check_evidence.py --init`, then `record --id X` per obligation; a prefix enters
  `TOUCH_MAP` only in the release that creates its directory (`validate_maps` refuses a
  missing one).
- New ledger entries are named by **title** and get ids when opened in Step 1 (the `ledgers`
  guard scans `specs/`): GAP "Gemini CLI is supported by construction and validated by
  nothing"; abandoned mechanism "Silent auto-update of the installed skill"; IDEAs "The review
  entry path", "Re-tune the type register for non-D-DIN faces", "CI checks for user packs",
  "`.cursor/rules/lumi-style.mdc` has no YAML frontmatter", "CVD check for a brand-named chart
  triple". Next id = highest existing + 1 in each ledger.
- Counts in this file are not rules; the authorities are `gallery.json`, the interview file,
  and `git ls-files`.

Each step lists **change · interfaces · red run · tests · ledger · evidence**.

---

## Step 1 · R1a — the resolver, the path guard, the synthetic pack

- change:
  - **Create `scripts/lib/brand.py`** (interfaces below). `registry()` is **new** and reads
    `brands/registry.json` — `build_entrypoints.registry()` reads `adapters/platforms.json`
    and is untouched. Today's only readers of the brand registry are `new_deck.wordmark()`
    and `check_brand_registry`.
  - **`check_path_mentions`** in `check_repo.py`, generalising `check_script_paths` (same
    `git ls-files` walk, same `SCRIPT_PATH_FROZEN`):
    `PATH_MENTION_RE = re.compile(r"(?<![\w./-])(tokens|assets|references|adapters|layouts|library|brands|rules|platforms)/[\w./-]*\w")`
    — the lookbehind removes `.cursor/rules/…`, URL fragments and `tests/fixtures/brands/…`
    hits. **Run the regex over the tree before writing the guard** (convention 15): today it
    leaves four non-resolving mentions — `check_design.py` `url(assets/cover.jpg)`,
    `check_evidence.py` and `check_repo.py` string literals, `ledger.py` `tokens/page` — which
    seed `PATH_MENTION_WAIVERS: dict[tuple[str, str], str]` with reasons, plus the three
    `assets/marks/…` keys of `ASSET_BRIDGE` in `brand.py` ("pack-relative key resolved by
    `Pack.path`"). `PATH_MENTION_WARN_PREFIXES: tuple[str, ...] = ()` holds the old half of
    a live pair (printed `WARN`, not a failure). CHECKS row `("path mentions", check_path_mentions)`.
  - `brands/registry.json` → `{"$comment": …, "schema": 2, "default": "lumivate",
    "brands": {"lumivate": {"path": "brands/lumivate"}}}`; `check_brand_registry`:
    `ALLOWED = {"path"}`, `path` must be a directory. Rewrite its tests (the existing
    `_brand_tree` helper in `test_check_repo_guards.py` builds records with `wordmark`/`assets`
    /`cover_mark`; it is rewritten here and keeps its name).
  - **`brands/lumivate/brand.json`**, exactly:
    `schema 1 · id lumivate · name LUMIVATE · wordmark "LUMI Style" · site www.lumivate.io ·
    language_default en · output_dir "LUMI-Style" · cover_mark assets/marks/globe-field.svg ·
    fonts` = the four entries of design §1 (D-DIN ×2 `face: body`, IBM Plex Mono ×2
    `face: mono`, matching `embed_font.FACES`) · `engine_version` = the **current** SKILL.md
    version (pre-bump; `release.py` swaps it). Omit `logo`, `policies`, `compliance`,
    `locked`. `engine_version` is written before any other version-shaped string.
  - `("brands/lumivate/brand.json", r'"engine_version":\s*"(\d+\.\d+\.\d+)"')` joins
    `TOKEN_STAMPS` in `check_repo.py` **now** (a stamp with no declared position fails,
    CLAUDE.md convention 3); `release.py` bumps it from then on.
  - **`brands/lumivate/BRAND.md`** (identity only; no `BR-*` ids, no `Serves:` lines):
    "# LUMIVATE — LUMIVATE is the reference brand this package ships. The one idea: the
    consulting document as a surface of still water — findings rise to it, nothing below is
    hidden. Two devices carry it: the **waterline** (the rule that separates a page's claim
    from its evidence) and the **field** (the globe mark that locates the work). Palette,
    type and marks are the values in `theme/` and `assets/`; the rules that use them are the
    engine's, in `../../references/brand.md`."
  - **`tests/fixtures/brands/acme/`**: `brand.json` (`id acme · name "Acme Analytics" ·
    site www.acme.example · output_dir Acme · fonts` = one body face `Acme-Regular.woff2`
    weight 400 **and** the mono pair copied from LUMIVATE · no `logo`, no `cover_mark`, no
    `locked` · `engine_version` current); `theme/theme.css` = `tokens/lumi-theme.css` `:root`
    + `body.dark` copied verbatim with `--bg/--nw/--acc` replaced by `#FAF7F2 / #1A1A2E /
    #7A1F3D`, every `rgba(<LUMIVATE ink triple>, a)` → `rgba(26,26,46, a)` and every
    `rgba(<accent triple>, a)` → `rgba(122,31,61, a)` by literal substitution; `--din`/`--mono`
    deleted; `--face-body: 'D-DIN'`, `--face-mono: "IBM Plex Mono"` added; the portrait
    `--ground-strong` override kept (pack value); `.scope-note` dropped (engine, Step 3);
    `theme/theme.json` = `design-tokens.json`'s `palette`, `palette_default`, `chart`,
    `contrast.measured`, `font` with the same substitutions and `"_comment": "measured values
    copied from LUMIVATE, not re-measured; Step 12 derives them"`; `assets/fonts/`
    (`Acme-Regular.woff2` = copy of `D-DIN.woff2`, the two Plex files, `COPYING.txt`);
    `legal/privacy.md` (one URL line); `voice.md` (`## Never` two phrases, `## Favour` one);
    `compliance.md`; `BRAND.md` with one `BR-*` id. **No lock file** (Step 7).
    **`tests/fixtures/brands/acme-broken/`**: `privacy-terms.txt`; `logo.light` naming a
    missing file; `theme.json` with one hex differing from its CSS; `theme.css` declaring
    `--din`; no `--face-mono`.
  - `.gitignore`: `brands/*`, `!brands/lumivate/`, `!brands/registry.json`,
    `!brands/lumivate/**/*.svg`, `!brands/lumivate/**/*.woff2`, `!tests/fixtures/brands/**`
    (verified with `git check-ignore -v` in a scratch repo: pack files and the fixtures track,
    `brands/acme/*` is ignored).
  - `scripts/ops/new_deck.py`: `wordmark()` and `foot()` read `brand.active().json()`
    (`wordmark`, `site`); `BRAND_GLOBE` (module constant) becomes the function
    `brand_globe_path()` evaluated **inside** the generator — `test_new_deck.py` runs `main()`
    in-process after the fixture sets the environment. `build_fixtures.py` calls
    `new_deck.brand_globe()` at module scope; it keeps working through `ASSET_BRIDGE`.
  - Registry `wordmark` readers swept: `new_deck.py` (three sites), `references/storyline-templates.md`,
    `references/brand.md`.
  - `check_privacy.py`: `TERMS_DIR = Path(os.environ.get("LUMI_TERMS_DIR") or brand.home() / "terms")`
    (D2: one root; `LUMI_TERMS_DIR` still wins).
  - `SKILL.md` "Cross-platform" gains: "**Which brand.** Producers resolve the brand in this
    order: `--brand`, then `LUMI_BRAND`, then the id in `~/.lumi/brand`, then the registry
    default (LUMIVATE); each holds an id, never a path, and `LUMI_BRAND_HOME` moves the
    `~/.lumi` root. Run `python3 scripts/lib/brand.py --print` before the first build: exit 0
    prints the brand, exit 2 names the missing pointer and the build stops there. An agent
    never reads a pack file and never chooses a brand or a palette by hand — the scaffold
    carries it." `CLAUDE.md` checks list gains
    `python3 scripts/lib/brand.py --print      # the active brand and where it lives; exit 2 names the missing pointer`.
  - Ledger entries opened (titles above; drafts in §Ledger); design §10 cites the ids.
- interfaces (produced):
  ```python
  # scripts/lib/brand.py — stdlib; bootstrap block; in SIBLING_MODULES
  INHERITABLE = ("compliance.md",)
  THEME_BRIDGE = {  # shipped pack only; deleted in Step 3 (its planted red)
      "theme/theme.css": "tokens/lumi-theme.css",
      "theme/theme.json": "tokens/design-tokens.json",
      "theme/region-palette.css": "tokens/region-palette.css",
      "theme/region-palette-trade.css": "tokens/region-palette-trade.css",
  }
  ASSET_BRIDGE = {  # shipped pack only; deleted in Step 7 (its planted red)
      "assets/marks/globe-field.svg": "assets/brand/lumivate/globe-field.svg",
      "assets/marks/globe-cover.svg": "assets/brand/lumivate/globe-cover.svg",
      "assets/marks/globe-cover.dark.svg": "assets/brand/lumivate/globe-cover.dark.svg",
      "assets/fonts/": "assets/fonts/",          # prefix key: any rel under it maps to the same rel
  }
  class BrandError(Exception): ...
  class Unmeasurable(Exception): ...             # .reason
  @dataclass(frozen=True)
  class Pack:
      id: str; root: Path; shipped: bool
      def json(self) -> dict: ...                # brand.json; fonts → default pack's entries when absent (D7); no identity defaults (D10)
      def path(self, rel: str) -> Path: ...      # own file → INHERITABLE fallback → bridge (shipped) → BrandError
  def home() -> Path: ...                        # $LUMI_BRAND_HOME or ~/.lumi, evaluated per call
  def registry(root: Path | None = None) -> dict: ...
  def shipped(root: Path | None = None) -> list[Pack]: ...
  def default(root: Path | None = None) -> Pack: ...
  def resolve(brand_id: str, root: Path | None = None) -> Pack: ...   # registry → home()/brands/<id>; a path-shaped id → BrandError
  def active(flag: str | None = None, root: Path | None = None) -> Pack: ...  # flag → $LUMI_BRAND → home()/brand → default(); BrandError
  def declared(html: str, root: Path | None = None) -> Pack: ...      # <meta name="brand" content="id">; else Unmeasurable
  def meta_tag(pack: Pack) -> str: ...           # '<meta name="brand" content="{id}">'
  # CLI: python3 scripts/lib/brand.py --print [--brand ID]
  #   0: 'brand: <id>  home: <abs>  engine_version: <v>'   2: one line (missing pointer, missing id, or a path where an id belongs)
  ```
  ```python
  # tests/conftest.py (adds ROOT and this fixture; LUMI_BRAND_HOME=tests/fixtures also works read-only)
  @pytest.fixture
  def acme_pack(tmp_path, monkeypatch):
      home = tmp_path / ".lumi"
      shutil.copytree(ROOT / "tests/fixtures/brands/acme", home / "brands" / "acme")
      monkeypatch.setenv("LUMI_BRAND_HOME", str(home))
      monkeypatch.setenv("LUMI_BRAND", "acme")
      return home / "brands" / "acme"
  ```
- red run (planted first): `see tokens/old-theme.css` planted in AGENTS.md →
  `python3 scripts/check/check_repo.py` fails `path mentions` naming the line;
  `H=$(mktemp -d); mkdir -p $H/brands; echo /abs/path > $H/brand; LUMI_BRAND_HOME=$H python3 scripts/lib/brand.py --print`
  → exit 2 "an id, not a path"; `LUMI_BRAND=ghost … --print` → exit 2 naming `$H/brands/ghost`.
- tests: `tests/test_brand.py` (resolution order; path-shaped id; missing id; `declared()`
  without meta; `Pack.path` fallback only for `INHERITABLE`; both bridges resolve for
  `lumivate`; `--print` by subprocess, both exit codes); `test_check_repo_guards.py`
  (`check_path_mentions` pass / fail / warn-prefix trees; registry guard with `path` only and
  with an extra key; `check_versions` with the new stamp row); **`tests/test_gitignore.py`**
  (`git check-ignore -q brands/acme/x` true; `brands/registry.json` and
  `tests/fixtures/brands/acme/brand.json` false); `test_new_deck.py` under `acme_pack`:
  footer carries `www.acme.example`, `main()` in-process.
- ledger: opens the seven entries. · evidence: `SKILL.md` → `conformance-freshness` if the
  board trails.

## Step 2 · R1b — the pack guard, logo and legal, the manifest and privacy holes

- change:
  - **`check_brand_pack`** (`("brand packs", check_brand_pack)`), looping
    `brand.shipped(ROOT)`: required keys; every declared path resolves pack-relative;
    `policies.*` is an existing file or a URL that parses; `logo.*` exist iff declared; no
    file matching `*terms*` under the pack; `engine_version == SKILL.md`; every pack file is
    tracked — a **new helper** comparing `git ls-files -z -- <pack>` to `os.walk` (the
    synthetic-tree test does `git init && git add -A`, the pattern `test_check_repo_guards.py`
    already uses for tracked-file guards). Lock and generated-file rows arrive in Steps 3/7.
  - `build_brand.py --wordmark --brand ID`: `assets/logo/wordmark.svg` and `wordmark.dark.svg`
    as `<text font-family="var(--face-body)">` with the body face embedded as a data-URI
    `@font-face` inside the SVG's own `<style>` (deterministic bytes so `build_brand --check`
    regenerates identically); `mark.svg` = the field globe's static frame from `globe_svg.py`.
    `build_brand.py` is hash-locked → `python3 scripts/lib/lock.py --update "wordmark
    generator"` in the same commit. `brand.json` gains `logo`; `policies` only if the owner
    names URLs, else omitted and the entry says so.
  - `check_platform_manifest`: every `capabilities.<tier>.ships` entry resolves.
  - `check_privacy.py`: before `reader_text()`, scan `<meta name="brand" content=…>` and every
    `content="…"` attribute for `/Users/`, `/home/`, `C:\`, `~/`.
  - **`scripts/build/build_brand_inventory.py`** (the `build_eval_inventory.py` pattern):
    rows per `check_design` metric id (`gating.metric_ids`) and per shipped-theme custom
    property; classification: engine = metric in `gating.METRIC_AUTHORITIES` or token under
    `typography`/`layout`/`retired`; brand = token under `palette`/`chart`/`font`; brand-with-
    floor = palette token named in `contrast.floor_*`. Writes `references/brand-inventory.md`;
    `--check` in `ci.yml` and `release.GENERATORS`.
  - `check_evidence`: `TOUCH_MAP += ("brands/", ("conformance-freshness",))`;
    `STAMPED_PREFIXES += ("brands/lumivate/brand.json", 2)`.
- interfaces: `check_brand_pack() -> list[str]`; `build_brand.py --wordmark --brand ID`;
  `build_brand_inventory.py [--check]`.
- red run (planted first): a synthetic tree whose registry names `acme-broken` → three
  findings (terms file, dangling logo, missing `--face-mono`); delete `legal/privacy.md` with
  `policies.privacy` declared → red; `ships: ["nonexistent/"]` → manifest red;
  `<meta name="brand" content="/Users/x/b">` in a fixture copy → privacy finding; hand-edit
  the inventory → `--check` red.
- tests: guard tests as above; `tests/test_check_privacy.py` meta-path case;
  `tests/test_build_brand_inventory.py`.
- ledger: the `.mdc` IDEA cited as seen, not fixed. · evidence: `conformance-freshness` if stale.

## Step 3 · R2a-i — `layouts/` and the pack theme; the scaffold assembles its head

- change:
  - **`layouts/register.css`** (stamp `/* LUMI register · vN */`): `--fs-*`, `--w-*`, `--lh-*`,
    `--ls-*`, `--din: var(--face-body), "PingFang SC", "Hiragino Sans GB", "Noto Sans SC", Arial, sans-serif`,
    `--mono: var(--face-mono), "SFMono-Regular", Menlo, monospace`, `.scope-note`.
    **`layouts/engine-tokens.json`** (`"version"`): `retired`, `layout`, `typography` (incl.
    `chart_scale_px`), `contrast.floor_*`, region parameters, ladder alphas, and `assets`
    (until Step 7). `git mv tokens/lumi-layouts.css layouts/layouts.css`, then a tracked copy
    re-added at `tokens/lumi-layouts.css` for the pair.
  - **`brands/lumivate/theme/theme.css`** (no stamp): everything §1.1 assigns to the pack,
    including the ground tiers and their portrait override, `--face-body`, `--face-mono`;
    **`theme.json`**: `palette`, `palette_default`, `chart`, `contrast.measured`, `font`.
    `tokens/lumi-theme.css` and `tokens/design-tokens.json` stay as the old half.
  - `build_region_palette.py --brand ID`: ink/bg via `css_tokens.rule_vars` on
    `Pack.path("theme/theme.css")`; writes the pack's `theme/region-palette*.css`; `--check`
    loops `shipped(ROOT)`; `oklch_to_srgb`, `lab_of`, `ciede2000`, `max_chroma` lifted into
    `color_math.py` first, and `check_no_shadow_math`'s `owners` dict gains them. Acme's
    palettes generated with `LUMI_BRAND_HOME=$PWD/tests/fixtures` so they land in the fixture;
    acme's `contrast.measured` re-measured at the same time.
  - `new_deck.preamble()`: emits `brand.meta_tag(pack)`, then `<style>` blocks in the order
    theme.css, register.css, layouts.css, region-palette.css, region-palette-trade.css, then
    `embed_font.css()`; the fixture is no longer sliced.
  - `check_design.py` D20: `pack = brand.declared(html)`; `Unmeasurable` → `UNMEASURABLE`,
    non-zero; compares against `pack.path("theme/theme.css")`. D23: declared face set =
    that theme ∪ `layouts/register.css` (so `--din`/`--mono` still count); same UNMEASURABLE
    rule; `fixtures/expected.json` unchanged. `build_fixtures.shipped_css()` lifts
    `brand.default().path("theme/theme.css")` + `layouts/*.css` and writes `meta_tag`;
    fixtures regenerated; `git diff --stat fixtures/` shows only the head block;
    `check_fixtures.py` green (said explicitly, convention 17).
  - `brand.py`: `THEME_BRIDGE` deleted (`ASSET_BRIDGE` stays until Step 7).
  - New guard `("tokens pair", check_tokens_pair)`: `css_vars(tokens/lumi-theme.css) ==
    css_vars(theme.css) | css_vars(register.css)` and `tokens/lumi-layouts.css` byte-identical
    to `layouts/layouts.css`. `PATH_MENTION_WARN_PREFIXES = ("tokens/",)`.
  - `check_evidence`: `TOUCH_MAP += layouts/, brands/lumivate/theme/ → layout-fixtures`;
    `STAMPED_PREFIXES` += the three `layouts/` files; `spec_lines_changed` += `layouts/`,
    `brands/lumivate/theme/`.
- interfaces: `color_math.oklch_to_srgb(L, C, h) -> tuple[int, int, int]`,
  `color_math.ciede2000(lab1, lab2) -> float`, `color_math.lab_of(rgb)`, `color_math.max_chroma(L, h)`;
  `build_region_palette.py --brand ID [--check]`.
- red run (planted first): scaffold under `acme_pack` → `check_design` D20 `compared > 0,
  differs 0`, `grep -c lumivate` = 0; acme's `:root` block pasted into a document declaring
  `lumivate` → D20 fails on values; meta removed → UNMEASURABLE, non-zero;
  `mv tokens/lumi-theme.css /tmp/` → D20 on a LUMIVATE document still green (and `tokens
  pair` red, as expected during the experiment); one hex edited in `tokens/lumi-theme.css`
  only → `tokens pair` red; acme ground set to `#FFFFFF` without regeneration →
  `build_region_palette --check` red.
- tests: `test_new_deck.py` every test also under `acme_pack`, head order asserted;
  `test_check_design_units.py` D20 three-way, D23 union; `test_build_region_palette.py`
  `--brand` against acme (an off-white ground re-measures); `test_color_math.py` against
  `build_region_palette`'s recorded values; guard test for `tokens pair`.
- evidence: `layout-fixtures`; `conformance-freshness` if stale. The CHANGELOG entry states
  that every existing deliverable is UNMEASURABLE on D20 until rebuilt (design §3).

## Step 4 · R2a-ii — every reader of `tokens/` rewired

- change: `check_versions` reads `ENGINE_STAMPS` (`layouts/register.css`, `layouts/layouts.css`,
  `layouts/engine-tokens.json` `"version"`, plus the `brand.json` row from Step 1);
  `release.py`'s import and `tests/test_release_tool.py`'s authority-set assertion renamed in
  the same commit; `check_palette_parity` loops `shipped(ROOT)` (floors from
  `engine-tokens.json`, measured from each `theme.json`); `check_token_references` —
  `layouts/*.css` ∪ one shipped theme ∪ that pack's `region-*.css`, plus the one-declaration
  rule (per file); `check_retired_values`, `check_media_only_rules`, `_shipped_classes`,
  `check_layout_parity`, `check_region_coverage`, **`check_role_weights`** (reads
  `tokens/lumi-layouts.css`; added at 0.1.549), `build_eval_inventory.py`; **the three CI
  readers**: `recolor_shapes.py` (`TOKENS` at import), `build_brand.py` (theme + both region
  palettes; hash-locked → relock in this commit), `check_globe.check_regionmap_frame`
  (`tokens/region-palette.css`). `TOKEN_STAMPS` removed.
- interfaces: `ENGINE_STAMPS: tuple[tuple[str, str], ...]` in `check_repo.py`, imported by
  `release.py`.
- red run (planted first): stamp drift in `register.css`; `retired` removed from
  `engine-tokens.json` → red, not vacuous; `acme-broken`'s `--din` → var guard red; its hex
  mismatch → parity red; `var(--nothing)` in `layouts.css`; `mv tokens /tmp` → the four CI
  generators/checkers still green (`recolor_shapes --check`, `build_brand --check`,
  `check_globe --python-only --node`, `check_repo`).
- tests: `_version_tree`/`_palette_tree` helpers rewritten to the new layout; `_brand_tree`
  extended (registry + `brands/lumivate/{brand.json, theme/…}` + `layouts/*` + SKILL.md
  stamp); **`test_guards_ignore_the_active_pointer`**: `monkeypatch.setenv("LUMI_BRAND",
  "acme")` and every guard's output unchanged; `test_release_tool.py` updated.
- evidence: none new.

## Step 5 · R2a-iii — the surfaces that restate paths

- change: `run_conformance.SKILL_SURFACE` from `brand.default()` + `layouts/`;
  `build_entrypoints.render_note` / `render_pointer` name `layouts/` and the pack, artifacts
  regenerated; `platforms.json` `capabilities.*.ships` → `layouts/`, `brands/lumivate/`; prose
  sweep of `SKILL.md`, `AGENTS.md`, `prompts/lumi-style-core.md`, `README.md`, `scripts/README.md`,
  `references/design-rules.md`, and CLAUDE.md convention 3's sentence → "the `engine_version`
  stamp in each shipped `brand.json` and the three `layouts/` stamps"; `release.py`'s
  `tokens/` comment. The external recipes under `~/Documents/LUMI-Style/_sources` are the
  operator's: done = `ledger.py` reports zero stale recipes.
- red run: one `tokens/` mention left → `path mentions` WARN (the pair is live);
  `run_conformance.py validate` green.
- tests: `test_conformance_driver.py` `SKILL_SURFACE` case; `build_entrypoints --check`.
- evidence: changing `SKILL_SURFACE` changes the surface fingerprint, so
  `conformance-freshness` **fires and needs a driven run on ≥ 2 agents** (Claude Code +
  Hermes) to close — operator time, recorded through the gate.

## Step 6 · R2b — `tokens/` deleted

- change: `git rm -r tokens/`; `check_tokens_pair` and its tests removed; `"tokens/"` leaves
  `PATH_MENTION_WARN_PREFIXES`; `TOUCH_MAP` / `STAMPED_PREFIXES` / `spec_lines_changed` lose
  their `tokens/` rows; `.gitignore` comment pruned.
- red run: after `git rm`, re-add one `tokens/` mention in a docstring → `path mentions` FAIL.
- tests: guard test that a former warn prefix now fails. · evidence: none new.

## Step 7 · R3a-i — `library/` and two locks

- change: `git mv` of `assets/{icons,shapes,vectors,geo,globe,regionmap,logos,frameworks.json}`
  → `library/` with tracked copies left under `assets/` for the pair; `assets/fonts/` (five
  files) and `assets/brand/lumivate/*` → `brands/lumivate/assets/{fonts,marks}`;
  `lock.py`: `verify(lock_path: Path, base: Path) -> list[str]`, `update(lock_path, base, why)`;
  engine lock `library/LOCKED.json` (runtime `.js`, `build_brand.py`, `globe_svg.py`); pack
  lock `brands/lumivate/assets/LOCKED.json` (marks, logo, fonts) and acme's (fonts);
  `check_brand_lock` → **`check_engine_lock`**; `check_brand_pack` gains the pack-lock row;
  `brand.py`: `ASSET_BRIDGE` deleted; `check_assets_tracked` scoped to `library/` ∪ shipped
  packs; `.gitignore` re-admits `library/**`; `TOUCH_MAP` `library/geo|globe/`,
  `brands/lumivate/assets/` added (old `assets/…` rows kept for the pair);
  `PATH_MENTION_WARN_PREFIXES += ("assets/",)`; an `assets pair` guard (byte-identical trees).
  `engine-tokens.json` loses its `assets` key.
- red run: move `library/globe/globe.js` → engine lock red; edit a mark → pack lock red;
  an untracked svg under `library/icons/`; `brand_globe_path()` under `lumivate` resolves
  to `brands/lumivate/assets/marks/` with the bridge gone.
- tests: `tests/test_lock.py` (two locks, two bases); guard tests; `test_brand.py` bridge
  test inverted.
- evidence: `globe-js`, `layout-fixtures`.

## Step 8 · R3a-ii — generators learn the pack

- change: `embed_font.py` faces from `active().json()["fonts"]` (`face` key selects the CSS
  family), sizes from the pack lock; `build_brand.py --brand ID` emits `brand-mark` classes and
  `aria-label` from `brand.json.name`, `--relock "<why>"` rewrites the pack lock and refuses if
  the engine lock is red; marks regenerated — "pixels untouched" shown by `diff <(grep -v
  '^<!--' old) <(grep -v '^<!--' new)` per mark; `recolor_shapes.py` writes `var(--token)` with
  no literal fallback, mapping computed once against `brand.default()`; `lumivate-*` → `brand-*`
  in `layouts.css`, fixtures, `inspect_layout.py` probes.
- red run: acme → one body `@font-face` + the mono pair; generated mark under acme contains no
  `lumivate`; a shape with a literal hex → `recolor_shapes --check` red; `--relock` with a
  planted engine-lock drift → refuses.
- tests: `tests/test_embed_font.py`, `test_recolor_shapes.py` fallback case,
  `test_build_brand.py`.
- evidence: `globe-js`, `layout-fixtures`.

## Step 9 · R3a-iii — output directory and prose

- change: `output_dir.py`: `FOLDER` removed; the leaf from `active().json()["output_dir"]`,
  the parent from `documents_dir()`; `check_output_default` holds the five sites to "the
  pack's `output_dir`" wording and `output_dir.py` to the call; prose sweep for `assets/`;
  `run_conformance._results_root` unchanged (LUMIVATE's leaf is `LUMI-Style`). External
  recipes reading `assets/…` are the operator's, as in Step 5.
- red run: a site naming a literal folder → red; `output_dir.py` under `acme_pack` ends in
  `Documents/Acme` on a default-locale machine.
- tests: `test_output_dir.py` under both packs; guard test. · evidence: none new.

## Step 10 · R3b — `assets/` deleted

- change: `git rm -r assets/`; `assets pair` guard removed; warn → fail; `.gitignore` loses
  its `!assets/…` re-admissions; evidence rows dropped. **Readers to rewire in this commit**
  (each currently hard-codes `assets/`): `check_globe.py` (seven sites), `embed_globe.py`,
  `embed_icons.py`, `embed_shapes.py`, `embed_regionmap.py`, `build_worldmap.py`,
  `build_trade_registry.py`, `build_geography.py`, `build_region_palette.py`, `geo_frame.py`,
  `globe_svg.py`, `new_deck.py` (four sites), and in `check_repo.py`: `CJK_ALLOWED`,
  `check_stale_promises`, `check_shape_library`, `check_frameworks`.
- red run: the flip; every `--check` in `ci.yml` green with `assets/` gone.
- evidence: `globe-js`.

## Step 11 · R4 — voice, compliance, the brand prose moves

- change: `brands/lumivate/{voice.md,compliance.md}`; `check_prose.py` adds the declared
  pack's `## Never` phrases as `M4b_pack_bans` (literal, case-insensitive; `n/a` with no
  brand); `check_ban_list_parity` gains the per-pack half; `references/brand.md` §1–2b and §4
  + `README.md`'s brand block move into `brands/lumivate/BRAND.md` with their `BR-*` ids and
  `Serves:` lines, examples made synthetic (the "40 of 161 sources" class of number goes);
  `check_rule_ids` and `check_principle_trace` glob `references/*.md` ∪ shipped `BRAND.md`;
  `SKILL.md`/`AGENTS.md` "read brand.md first" → the pack's `BRAND.md`; `references/brand.md`
  keeps §3 and §5 as engine.
- red run: a phrase in acme's `voice.md` with no pattern → parity red; remove `BR-2` from
  `BRAND.md` → rule-id red; a document under `acme_pack` using an acme-banned phrase → M4b.
- tests: `test_check_prose_units.py` voice case; guard tests. · evidence: `conformance-freshness`.

## Step 12 · R5-i — the interview and `new_brand.py`

- change: **`references/brand-interview.md`** (design §4); **`scripts/lib/palette_derive.py`**
  — `derive(ground, ink, accent, *, accent_live=None, seal=None, dark=None, chart=None) -> Theme`:
  ladders from engine alphas, ramp by OKLCH lightness steps, `on-*` by floor, **lime / amber /
  brass from the accent ramp and seal = the engine's red when not given** (required values,
  design §1.1), dark palette derived and measured (D15), a brand-named `chart` triple
  **reported, not CVD-checked**; every pair measured against `floor_text`/`floor_ui`, a failing
  pair reported and left empty; **`scripts/ops/new_brand.py`** (`--from brand.json | --answers
  answers.json`, `--out ABS_DIR` — relative refused, `--check`, `--upgrade` — refuses a shipped
  pack, `--activate` writes `~/.lumi/brand`; writes the pack, runs `build_region_palette
  --brand`, refuses on a floor miss with exit 3 and the two-inks offer, prints every absolute
  path, prints the OR-8 terms instruction and writes nothing there, renders one preview page
  from the fixture's content).
- interfaces: `palette_derive.Theme` (`css() -> str`, `json() -> dict`, `report: list[str]`,
  `dark: bool`); `new_brand.py` exit 0 / 3.
- red run: an accent failing 4.5:1 as text → exit 3, nothing written, the pair named; a
  relative `--out` → refused; `--upgrade lumivate` → refused; `--upgrade` on a user pack whose
  `engine_version` trails → regenerated from `answers`, `--check` green.
- tests: `tests/test_palette_derive.py` (floors hit and missed; dark disabled when it cannot
  clear; required tokens always present); `tests/test_new_brand.py`.
- ledger: the register re-tune IDEA cited. · evidence: none new.

## Step 13 · R5-ii — per-brand generation, the driver, T4-brand, the re-flow

- change: `prompts/lumi-style-core.md` gains `<!-- brand:begin -->…<!-- brand:end -->` around
  its palette and identity sentences; `check_prompt_parity` skips inside them;
  `build_entrypoints.py --brand ID` writes `core-prompt.md` (the fenced spans regenerated from
  the pack) and `BRAND-POINTER.md` under `home()/brands/<id>/generated/`, refusing any target
  whose `resolve()` is under `ROOT`; `run_conformance.drive()`: `env={**os.environ,
  **expanded}` where `expanded` substitutes `${WORKDIR}` after `mkdtemp`, and when
  `LUMI_BRAND_HOME` is named copies `tests/fixtures/brands/<LUMI_BRAND>` to
  `$LUMI_BRAND_HOME/brands/<id>`; `history.json` rows gain an optional `note` printed by
  `report`; **`conformance/tasks/T4-brand.json`** (design §4c); `SKILL.md`, `AGENTS.md`, the
  core prompt re-flowed (interview pointer, D11 stop rule, "never hand-type the meta", the
  logo/PDF handover); `PROMPT_MUST_CARRY` gains the meta sentence; T1's prompt gains "scaffold
  with `new_deck.py`".
- red run (on one real agent before the task ships): `LUMI_BRAND_HOME` at a missing path →
  `--print` exits 2, the agent stops, the transcript names the pointer;
  `build_entrypoints --brand` with `LUMI_BRAND_HOME` under the checkout → refused.
- tests: `tests/test_build_entrypoints_brand.py` (nothing lands under `ROOT`; markers
  round-trip); `test_conformance_driver.py` env expansion + copy + T4 validation;
  `test_check_repo_guards.py` prompt-parity skip.
- operator: T4-brand `run --drive` on Claude Code, Hermes, Cursor; `report --record`.
- evidence: `conformance-freshness`.

## Step 14 · R6-i — `doctor.py`, the trace field

- change: **`scripts/ops/doctor.py`** (design §3: `--platform`, `--force`; Chromium / fonts /
  brand / version; `.git` → `git fetch --dry-run` with `timeout=5`, `GIT_TERMINAL_PROMPT=0`,
  else one line naming the platform's updater; stamp `home()/last-update-check`;
  `quota_limited` from the registry record — `platforms.json` gains that optional boolean,
  `true` on gemini-cli; always exit 0); `trace_schema.FIELDS += brand: (str, NoneType)` **and
  every tracked `evals/traces/*.json` migrated with `"brand": null` in the same commit**;
  `trace.py open` writes `active().id`; `ledger.py --board` groups by it; `SKILL.md` step 0
  runs `brand.py --print` every session and `doctor.py` on a session's first build; the
  abandoned-mechanism entry's body finalised in `FAILURE_MODES.md`.
- red run: fonts dir missing → reported; network cut via
  `GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=url.http://127.0.0.1:9/.insteadOf GIT_CONFIG_VALUE_0=https://`
  → one line, exit 0, under 5 s; one trace left unmigrated → `trace schema` red.
- tests: `tests/test_doctor.py` (subprocess, `HOME` redirected, elapsed asserted);
  `test_trace.py` brand field; `trace field readers` guard green.
- evidence: none new.

## Step 15 · R6-ii — gallery, README, the end-to-end script

- change: `brands/lumivate/examples/` — the scene sources `gallery.json` lists (synthetic
  facts); **`scripts/ops/build_gallery.py`** (renders cover + p1 via `export_pdf.py` at the
  design viewport, 1×; runs `check_deliverable`; writes rows: scene, source, evidence id,
  SHA-256 over source html + `theme.css` + `layouts/*.css` + each font in `brand.json.fonts`
  order); **`check_gallery`** (index ↔ PNGs ↔ digests, no render); **`scripts/ops/verify_brand_packs.py`**
  runs design §8's machine lines and is `OBLIGATIONS["brand-e2e"]`; `OBLIGATIONS["gallery"]` =
  `build_gallery.py --check-render`; **`check_readme_brand_prose`**; README rewritten in the
  design §5 order; `SKILL.md` gains the first-document flow and the default/on-request table
  (design §4b); `.gitignore` `!brands/lumivate/examples/*.png`.
- red run: edit a scene html without rebuilding → gallery red; a PNG with no row; a second
  brand paragraph in README → red; `verify_brand_packs.py` with a planted D20 default → red.
- tests: `tests/test_check_gallery.py`; guard test for the README rule;
  `tests/test_verify_brand_packs.py` (each line can fail).
- operator: `record --id gallery`, `record --id brand-e2e`; open each scene over `file://`.
- evidence: `gallery`, `brand-e2e`, `layout-fixtures` if a layout moved.

## Step 16 · R7 — `references/ → rules/`, `adapters/ → platforms/` (two pairs)

Each pair on the Step 3/6 template. Size note: `references/` is mentioned in ~46 tracked
files, most of them generated (`evals/rule-coverage.json`, the fixtures — which then owe
`layout-fixtures` evidence); regenerate rather than edit. Sites the pair guard alone will not
find, so the "a" commit does not ship them green: `ENTRY_STAMP`'s `references/PRINCIPLES.md`
key, `check_ledgers`' TODO glob, `PLATFORMS`, `check_evidence.spec_lines_changed` and the
`TOUCH_MAP` rows for `references/` and `prompts/`, `build_entrypoints.targets()`,
`check_rule_ids`/`check_principle_trace` globs. Red run per "b": a planted stale path.

---

## Ledger drafts (opened in Step 1, each in its file's own format; ids assigned then)

- **GAP · Gemini CLI is supported by construction and validated by nothing** — status open ·
  surface `adapters/platforms.json` (gemini-cli), `conformance/tasks/T4-brand.json` · symptom:
  D11 and the resolver hold for Gemini on paper; its file tools cannot leave the workspace and
  the available key is free-tier (0.1.539: 663 s of quota errors, nothing produced) · check:
  one T4-brand row for gemini-cli in `conformance/history.json` on a paid key.
- **AG · Silent auto-update of the installed skill** — declined: traces record
  `skill_version`, `ledger.py` reports stale recipes, convention 17 diffs rebuilds, the `full`
  tier executes `scripts/` so an unattended pull across ten agents is the supply-chain shape
  this repository refuses, and marketplaces update their own plugins. `doctor.py` compares once
  per session, read-only, and names the pull command.
- **IDEA · The review entry path** — a third path beside A and B with its own form/content
  line; acceptance: its own design spec and a `<meta name="brand">` reader in the reviewer.
- **IDEA · Re-tune the type register for non-D-DIN faces** — reported by `new_brand.py --check`,
  never gated.
- **IDEA · CI checks for user packs** — local `new_brand.py --check` only; acceptance: a
  decision recorded either way.
- **IDEA · `.cursor/rules/lumi-style.mdc` has no YAML frontmatter** — Cursor applies it only
  when `@`-mentioned; `render_pointer` should emit `description` + `alwaysApply: false` and
  `check_platform_manifest` parse it. Independent of brands.
- **IDEA · CVD check for a brand-named chart triple** — `palette_derive` reports a named
  triple and checks nothing; a CVD simulation would need a model the package does not ship.

## Order and dependencies

1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12 → 13 → 14 → 15 → 16. Hard edges: 3 needs
1's `brand.py` and deletes `THEME_BRIDGE`; 4 needs 3's files; 6 needs 4 (the three CI readers);
7 deletes `ASSET_BRIDGE`; 10 needs 7–9; 12 needs 3's `color_math` lift; 13 needs 3's
`preamble()` and 12's `new_brand.py`; 15 needs 14's `doctor.py`. PR boundaries: {1,2} ·
{3,4,5} · {6} · {7,8,9} · {10} · {11} · {12,13} · {14,15} · {16}. Strictly sequential; the
clock is build time plus three operator-gated waits (Step 5's driven conformance run, Step
13's three driven agents — Hermes needs its TCC grant — and Step 15's Chromium renders).

## Verification at each step

`python3 scripts/preflight.py`; `python3 scripts/check/claim_sweep.py` read for the counts
touched; `python3 scripts/check/check_evidence.py --init` then `record` per obligation; the
step's planted red reproduced before its code and its removal recorded in the CHANGELOG
entry. Fresh-clone check on the steps that touch `.gitignore` (1, 3, 7, 10, 15):
`D=$(mktemp -d) && git clone -q . "$D/lumi-style" && python3 "$D/lumi-style/scripts/preflight.py"`.
Design §8 is run by `verify_brand_packs.py` after Step 15 and recorded as `brand-e2e`; its
browser lines are the operator's.
