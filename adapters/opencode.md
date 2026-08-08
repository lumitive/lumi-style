# Loading in OpenCode

OpenCode reads three user-level locations; any one works, and it also honours
Claude Code's directory:

```bash
ln -s ~/src/lumi-style ~/.config/opencode/skills/lumi-style
# or ~/.agents/skills/lumi-style   (shared with Gemini CLI, Copilot, OpenClaw, Pi)
# or ~/.claude/skills/lumi-style
```

Project-level equivalents are `.opencode/skills/`, `.agents/skills/` and
`.claude/skills/`, searched upward from the working directory to the git
worktree root. Ask for work in natural language ("in LUMI style…").
