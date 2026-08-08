# Loading in OpenClaw

OpenClaw finds `SKILL.md` anywhere under a configured root, up to six levels
deep:

```bash
ln -s ~/src/lumi-style ~/.agents/skills/lumi-style     # shared location
# or <workspace>/skills/lumi-style
```

The slash command comes from the `name` frontmatter field, so the skill is
`/lumi-style`. Symlinked targets need explicit trust via
`skills.load.allowSymlinkTargets` in `openclaw.json`; if the skill does not
appear, that setting is the first thing to check.
