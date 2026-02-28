---
name: mvp-story-agent-chat
description: 技术/操作手册（命令模板 + 输出展示模板）。业务体验见 PRODUCT_SPEC.md；行为与路由见 AGENTS.md。
---
# 目标
把 `mvp_story_agent/` 的角色脚本当作“可重复调用的单步工具”，以最小闭环完成：summaries → ideas → story → review → rewrite。
# 范围与边界
- 本文只写：怎么执行（命令模板）与怎么展示（界面展示模板）。
- 不写：自然语言意图、对话策略、门禁规则（见 `PRODUCT_SPEC.md` 与 `AGENTS.md`）。
# 约定参数
- ws：workspace 路径（必须是已初始化、包含 workspace.json 的目录）
- session：会话 id（例如 s001）
- 可选模型参数（如适用）：--model-type / --model / --api-key-env / --thinking-level
# 命令模板（python3）
所有命令使用 python3。
## 1) Select：选择素材（selected_items）
命令：
- 添加：`python3 -m mvp_story_agent.roles.select --ws "<ws>" --session <session> --add "pas_xxx,./file.md"`
- 移除：`python3 -m mvp_story_agent.roles.select --ws "<ws>" --session <session> --remove "pas_xxx"`
- 覆盖：`python3 -m mvp_story_agent.roles.select --ws "<ws>" --session <session> --set "pas_a,pas_b"`
- 查看：`python3 -m mvp_story_agent.roles.select --ws "<ws>" --session <session> --list`
界面展示模板：
- selected_items（json）。
## 2) Reader：生成/更新 summaries（按需）
命令（summary）：
- `python3 -m mvp_story_agent.roles.reader --ws "<ws>" --session <session> --mode summary`
- 可选：`python3 -m mvp_story_agent.roles.reader --ws "<ws>" --session <session> --mode summary --use-last-materials`
界面展示模板：
- summaries_written + index 路径（json）。
## 3) Summary（@summary 的等价落地）
说明：`@summary` 只做“查询/更新”。实现上等价为读取 summaries 目录（查询）或触发 reader summary（更新）。
界面展示模板（查询）：
- 按条目展示：题材名 + 主题 1 行 + 文件路径（可选：要素/冲突）。
## 4) Ideator：基于 summaries 生成 ideas
命令：
- 列出 summaries：`python3 -m mvp_story_agent.roles.ideator --ws "<ws>" --session <session> --list-summaries`
- 生成 ideas：`python3 -m mvp_story_agent.roles.ideator --ws "<ws>" --session <session> --summaries "all" --count 3`
界面展示模板：
- 3 个 ideas：编号 + title + angle（提示用户回复编号）。
## 5) Writer：生成/改写 story.md
命令：
- `python3 -m mvp_story_agent.roles.writer --ws "<ws>" --session <session> --idea-index 0 --input "<改写指令>"`
界面展示模板（硬规则）：
- story.md 的文件路径（必要时附 story.meta.json 路径）。
## 6) Reviewer：审阅最新 story.md
命令：
- `python3 -m mvp_story_agent.roles.reviewer --ws "<ws>" --session <session>`
界面展示模板：
- issues/suggestions 各最多 3 条 + 提问是否采纳（采纳则进入 writer 重写循环）。
# 默认飞轮（实现落地）
1) 有 summaries → ideator（3 ideas）
2) 用户选 index → writer（展示 story.md 路径）
3) reviewer（展示建议）→ 采纳则 writer 重写，循环
