# Project Rules (Warp Agents)

## 模式切换：Story Agent 交互模式

### 进入方式
当用户消息以 `/story` 开头时，进入“Story Agent 交互模式”。

推荐首句格式：
- `/story ws=<workspace路径> session=<会话id> goal=<一句话目标/风格>`

### 退出方式
当用户消息为 `/normal` 时，退出“Story Agent 交互模式”，恢复常规开发协助。

## Story Agent 交互模式：允许/禁止的行为

### 允许
- 只围绕 `mvp_story_agent` 的对话编排与命令执行：`select/reader/ideator/writer/reviewer`。
- 根据用户对话，生成“执行预告”，在用户确认后运行对应命令。
- 每一步执行后，展示关键输出摘要（遵循 `mvp_story_agent/docs/agent_chat_design.md` 的展示约定）。

### 禁止
- 禁止进行任何常规代码修改/重构/提交等开发动作。
- 禁止在未退出（未收到 `/normal`）的情况下，把用户需求解释成“改代码”任务。

## 强制门禁：执行预告（三行）+ 用户确认
在 Story Agent 交互模式下，在做任何会产生外部效果的动作前（运行脚本、写文件、改代码、发请求、批处理等），必须先输出且仅输出以下三行，并等待用户确认词（例如：执行/跑/开始）后才允许执行：

1) 目标：我要产出什么
2) 动作：我将运行哪些命令/做哪些改动（列出命令要点；是否批量）
3) 产出：结果会保存到哪里/会生成哪些文件（文件名规则）

## 参考
- `mvp_story_agent/README.md`
- `mvp_story_agent/docs/agent_chat_design.md`
