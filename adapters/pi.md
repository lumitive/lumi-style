# Loading in Pi

```bash
ln -s ~/src/lumi-style ~/.agents/skills/lumi-style     # shared location
# or ~/.pi/agent/skills/lumi-style
```

Invoke with `/skill:lumi-style <task>`. Project-level installs go in
`.agents/skills/` and are honoured after project trust is granted.

Pi discovers a directory containing `SKILL.md`; the skill name comes from the
`name` frontmatter field.
