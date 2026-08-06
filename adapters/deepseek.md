# DeepSeek 装载

同 Kimi:使用 `prompts/lumi-style-core.md` 单文件核心版。

- API:放入 `messages[0]`(role=system);
- 网页版:作为对话第一条消息发送;
- 长任务建议每次新会话重新注入,避免规则被上下文挤出。

core 自含、零工具假设;与 references/ 冲突时以 references/ 为准。
