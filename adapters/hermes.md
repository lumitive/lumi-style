# Loading in Hermes

**Unconfirmed.** Hermes consumes the same `SKILL.md` format with `name` and
`description` frontmatter, but no documentation we can cite states its discovery
path, so this note records a likely install rather than a verified one:

```bash
ln -s ~/src/lumi-style ~/.agents/skills/lumi-style
```

`~/.agents/skills/` is the shared location that Gemini CLI, GitHub Copilot,
OpenCode, OpenClaw and Pi all read, which makes it the most probable. If you have
Hermes installed and can confirm or correct this, the registry entry in
[`platforms.json`](platforms.json) carries a `path_waiver` recording exactly what
is unverified — replace it with the real path and drop the waiver.

This repository does not claim support it has not checked.
