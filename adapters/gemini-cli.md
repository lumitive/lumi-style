# Loading in Gemini CLI

Gemini CLI reads the Agent Skills standard. `~/.agents/skills/` is the shared
cross-agent location and **takes precedence** over Gemini's own directory, so
prefer it — one install there also serves GitHub Copilot, OpenCode, OpenClaw and
Pi.

```bash
git clone https://github.com/lumitive/lumi-style ~/src/lumi-style
ln -s ~/src/lumi-style ~/.agents/skills/lumi-style     # or ~/.gemini/skills/lumi-style
```

Ask for work in natural language ("in LUMI style…"). Gemini calls `activate_skill`
and asks you to confirm the directory it is about to read; approve it once per
session. The skill then reads `references/` and `tokens/` on demand.

**Symlink rather than copy.** An installed copy silently stranded at 0.1.334 while
the repo reached 0.1.337, and a deck was built against three versions of
superseded rules.
