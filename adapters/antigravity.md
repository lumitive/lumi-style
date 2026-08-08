# Loading in Google Antigravity

Two locations, and the workspace one is **not** the shared `.agents/skills/`
convention — Antigravity uses `.agent/`, singular:

```bash
# global, all projects
mkdir -p ~/.gemini/antigravity/skills
ln -s ~/src/lumi-style ~/.gemini/antigravity/skills/lumi-style

# or per workspace
ln -s ~/src/lumi-style .agent/skills/lumi-style
```

**Restart the agent session after installing** so Antigravity re-detects the
skill. It then reads `references/` and `tokens/` on demand.

Antigravity ships as an IDE rather than a CLI on `PATH`, so the conformance
harness cannot invoke it headlessly; release conformance tables record it as not
exercised rather than as passing.
