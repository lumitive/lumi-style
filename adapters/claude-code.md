# Loading in Claude Code

```bash
git clone https://github.com/lumitive/lumi-style ~/src/lumi-style
ln -s ~/src/lumi-style ~/.claude/skills/lumi-style
```

Restart the session or run `/reload-skills`; invoke with `/lumi-style <task>`, or
simply say "in LUMI style…". The skill reads `references/` and `tokens/` on
demand — no need to attach them manually.

**Symlink rather than copy.** This note said `git clone` straight into the skills
directory until 0.1.352, which contradicted `README.md` and re-introduced the
defect the README's warning exists for: an installed copy silently stranded at
0.1.334 while the repo reached 0.1.337, and a deck was built against three
versions of superseded rules. A symlink cannot go stale.
