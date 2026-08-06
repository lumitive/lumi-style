# Loading in DeepSeek

Same as Kimi: use `prompts/lumi-style-core.md`, the self-contained single-file
core.

- API: put it in `messages[0]` (role=system);
- Web: send it as the first message of the conversation;
- For long tasks, re-inject at the start of each new session so the rules are
  not pushed out of context.

The core is self-contained with zero tool assumptions; on any conflict,
`references/` wins.
