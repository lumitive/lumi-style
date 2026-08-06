# Loading in Kimi

Kimi has no skill mechanism — use the self-contained single-file core:

1. Open `prompts/lumi-style-core.md` and copy it in full;
2. Paste it as the system prompt (API: the `system` field; web: the first message
   of the conversation);
3. Then issue tasks normally ("Following the rules above, write…").

The core is a strict subset of `references/` (self-contained, no file
references); on any conflict, `references/` wins. Re-copy the latest core after
rule updates.
