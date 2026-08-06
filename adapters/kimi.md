# Kimi 装载

Kimi 无技能机制,用单文件核心版:

1. 打开 `prompts/lumi-style-core.md`,整体复制;
2. 作为系统提示(API:system 字段;网页版:对话第一条消息)粘贴;
3. 之后正常下达任务(「按以上规则写一份…」)。

core 是 references/ 的严格子集(自含、无文件引用);细则冲突以本仓库
references/ 为准。规则更新后重新复制最新 core。
