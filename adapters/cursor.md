# Loading in Cursor

```bash
git clone https://github.com/lumitive/lumi-style ~/src/lumi-style
ln -s ~/src/lumi-style ~/.cursor/skills/lumi-style
```

Ask for work in natural language ("in LUMI style…"). Cursor reads `references/`
and `tokens/` on demand.

A `.cursor/rules/lumi-style.mdc` pointer file is planned for 0.1.354 for projects
that want the rules loaded for the whole workspace rather than on demand. It is a
convenience — the skill path above already works.

**Symlink rather than copy**, so the install cannot strand at an old version.
