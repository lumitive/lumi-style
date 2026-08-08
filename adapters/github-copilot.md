# Loading in GitHub Copilot

Copilot reads the Agent Skills standard. Agent skills are a **different
mechanism** from `.github/copilot-instructions.md` — you do not need the latter.

```bash
ln -s ~/src/lumi-style ~/.agents/skills/lumi-style      # shared, preferred
# or ~/.copilot/skills/lumi-style
# or, to scope it to one repository, .github/skills/lumi-style
```

Works in the Copilot CLI, the cloud agent, code review, and agent mode in VS Code
and JetBrains IDEs. The skill reads `references/` and `tokens/` on demand.
