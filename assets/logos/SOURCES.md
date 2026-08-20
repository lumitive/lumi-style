# Platform marks · provenance and terms

Official vector marks, fetched from each platform's own domain on 2026-08-18,
for nominative use on a get-started page (naming the platforms an install
supports). Each mark identifies its owner's product; none implies endorsement.
Tinting into the document palette is NOT applied to these marks — a trademark
keeps its own colours (design-rules §9's tinting rule scopes to imagery, not
marks).

| file | mark | fetched from |
|---|---|---|
| claude.svg | Anthropic Claude | https://claude.ai/favicon.svg |
| cursor.svg | Cursor | https://cursor.com/favicon.svg |
| gemini-sparkle.svg | Google Gemini | https://www.gstatic.com/lamda/images/gemini_sparkle_v002_d4735304ff6292a690345.svg |
| github-mark.svg | GitHub (Copilot rows) | https://github.githubassets.com/favicons/favicon.svg |
| google-g.svg | Google | https://fonts.gstatic.com/s/i/productlogos/googleg/v6/24px.svg |
| mcp.svg | Model Context Protocol | https://raw.githubusercontent.com/modelcontextprotocol/modelcontextprotocol/main/docs/logo/light.svg |
| a2a.svg | A2A (Agent2Agent) | https://raw.githubusercontent.com/a2aproject/A2A/main/docs/assets/a2a-logo-black.svg |
| ap2.svg | AP2 (Agent Payments Protocol) | https://raw.githubusercontent.com/google-agentic-commerce/AP2/main/docs/assets/ap2-logo-black.svg |
| meta.svg | Meta | https://static.xx.fbcdn.net/rsrc.php/yf/r/-7pQO6hUGK_.svg (linked from about.meta.com/brand/resources/meta/company-brand/) |
| reddit.svg | Reddit | https://redditinc.com/hubfs/raw_assets/public/redditinc/images/Reddit_Lockup_Logo.svg |
| x.svg | X | https://about.x.com/content/dam/about-twitter/x/brand-toolkit/x-logo.zip (logo.svg) |
| microsoft.png | Microsoft | https://uhf.microsoft.com/images/microsoft/RE1Mu3b.png |

Google added 2026-08-19 for a business plan's ecosystem page. MCP, A2A and AP2
added 2026-08-19 for that plan's protocol page: each is the official vector in the
protocol's own repository, which is the owner's domain for a spec published that
way. **A2UI** and **UCP** publish only raster org avatars and stay in type.

Not shipped, and why: OpenAI serves brand assets behind a bot check (403 on
every public endpoint tried); DeepSeek and Kimi publish raster favicons only.
The five ecosystem marks were added 2026-08-19 after a second search. Two of
them carry a transformation, recorded here because an unrecorded one is a
falsified mark:

- **x.svg** ships from X's own brand toolkit as the WHITE variant (`fill:
  white`, for dark grounds). The toolkit also publishes a black variant as a
  raster. The fill is set to `#000000` — choosing the correct one of the
  owner's own two monochrome variants for a light page, never a tint into this
  palette.
- **microsoft.png** is a RASTER, 216x46, and it is the only image in any
  deliverable this package has produced. Microsoft publishes no public vector
  from its own domains: the CMS asset endpoint returns 403 and every SVG path
  tried 404s. A raster from the owner's own service is a truer mark than a
  redrawn one, so it ships embedded as a `data:` URI (D24) and the document
  states its terms (D25).

**A2UI** and **UCP** publish only raster organisation avatars, which identify a
GitHub org rather than the protocol, so they stay in type. The earlier note
stands for the record: the Meta asset at `rsrc.php/y1/r/4lCu2zih0ca.svg` is the
**facebook** wordmark and is NOT the Meta mark; the one vendored above is the
Meta infinity mark linked from Meta's own brand-resources page.
Per storyline-templates.md's get-started rule, a platform whose mark is not
shipped gets its name set in type — never a redrawn imitation, which would be
a fabricated trademark.

## Model family marks (`models/`)

Twenty-three marks for the model families the ontology adapts to. All are from
**`@lobehub/icons-static-svg` version 1.94.0**, an MIT-licensed icon set
(<https://github.com/lobehub/lobe-icons>), fetched 2026-08-19 from unpkg at the
pinned version. The MIT licence covers the *icon set*; each mark remains the
trademark of its owner and is used nominatively, which the figure states.

Two marks the roster originally asked for **do not exist in this set and were
not substituted**: there is no Llama mark (Meta's own mark stands for the
family, and is the one drawn) and no Phi mark — the file published as
`microsoft` is Azure's mark, so Phi was dropped rather than shipped under the
wrong logo.

| File | Mark | Upstream path | Fetched |
|---|---|---|---|
| `models/baichuan.svg` | Baichuan | `@lobehub/icons-static-svg@1.94.0/icons/` | 2026-08-19 |
| `models/claude.svg` | Claude | `@lobehub/icons-static-svg@1.94.0/icons/` | 2026-08-19 |
| `models/cohere.svg` | Cohere | `@lobehub/icons-static-svg@1.94.0/icons/` | 2026-08-19 |
| `models/deepseek.svg` | DeepSeek | `@lobehub/icons-static-svg@1.94.0/icons/` | 2026-08-19 |
| `models/doubao.svg` | Doubao | `@lobehub/icons-static-svg@1.94.0/icons/` | 2026-08-19 |
| `models/ernie.svg` | Wenxin | `@lobehub/icons-static-svg@1.94.0/icons/` | 2026-08-19 |
| `models/gemini.svg` | Gemini | `@lobehub/icons-static-svg@1.94.0/icons/` | 2026-08-19 |
| `models/glm.svg` | Zhipu | `@lobehub/icons-static-svg@1.94.0/icons/` | 2026-08-19 |
| `models/grok.svg` | Grok | `@lobehub/icons-static-svg@1.94.0/icons/` | 2026-08-19 |
| `models/hunyuan.svg` | Hunyuan | `@lobehub/icons-static-svg@1.94.0/icons/` | 2026-08-19 |
| `models/internlm.svg` | InternLM | `@lobehub/icons-static-svg@1.94.0/icons/` | 2026-08-19 |
| `models/kimi.svg` | Kimi | `@lobehub/icons-static-svg@1.94.0/icons/` | 2026-08-19 |
| `models/llama.svg` | Meta | `@lobehub/icons-static-svg@1.94.0/icons/` | 2026-08-19 |
| `models/minimax.svg` | Minimax | `@lobehub/icons-static-svg@1.94.0/icons/` | 2026-08-19 |
| `models/mistral.svg` | Mistral | `@lobehub/icons-static-svg@1.94.0/icons/` | 2026-08-19 |
| `models/nvidia.svg` | Nvidia | `@lobehub/icons-static-svg@1.94.0/icons/` | 2026-08-19 |
| `models/openai.svg` | OpenAI | `@lobehub/icons-static-svg@1.94.0/icons/` | 2026-08-19 |
| `models/qwen.svg` | Qwen | `@lobehub/icons-static-svg@1.94.0/icons/` | 2026-08-19 |
| `models/sensenova.svg` | SenseNova | `@lobehub/icons-static-svg@1.94.0/icons/` | 2026-08-19 |
| `models/skywork.svg` | Skywork | `@lobehub/icons-static-svg@1.94.0/icons/` | 2026-08-19 |
| `models/spark.svg` | Spark | `@lobehub/icons-static-svg@1.94.0/icons/` | 2026-08-19 |
| `models/step.svg` | Stepfun | `@lobehub/icons-static-svg@1.94.0/icons/` | 2026-08-19 |
| `models/yi.svg` | Yi | `@lobehub/icons-static-svg@1.94.0/icons/` | 2026-08-19 |

### Entrance-layer marks (added 0.1.522.r8)

Three more from the same pinned set, for the entrance chips on p04. `hermes`,
`workbuddy` and `cowork` have **no mark in this set**, so those chips keep a
koboyo icon and their product name rather than borrowing a logo that belongs to
something else.

| File | Mark |
|---|---|
| `models/cursor.svg` | Cursor |
| `models/copilot.svg` | Copilot |
| `models/openclaw.svg` | OpenClaw |

## Entrance marks with no recorded provenance — declined

Three raster marks (Hermas, Cowork, WorkBuddy) were supplied from a download
folder for the same entrance chips, with no source URL, no fetch date and no
usage basis. This file's rule is that a vendored trademark carries its
provenance beside it, and the `.gitignore` exception for `assets/logos/*.png`
rests on that rule; so the three do not ship. A chip whose mark is not vendored
sets its product name in type (storyline-templates, the get-started rule),
never a redrawn imitation. If provenance arrives, they enter through a row in
the table above like every other mark.

**Spelling:** the product is **Hermas**, per the owner's list. A deck said
"Hermes" for two releases; that was a transcription error.
