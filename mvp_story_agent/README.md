# mvp_story_agent

最小可用 MVP：本地 workspace + 原文片段库（JSONL）+ 混搭 compose 生成 `draft/input.md`。

## 快速开始

从 `pythonProject` 目录运行（确保用 python3）：

- 创建 workspace
- 添加 source + passages
- compose 生成 `draft/input.md`

CLI 入口：`python3 -m mvp_story_agent.cli --help`

## Warp 编排用法（底层角色脚本）

这些脚本只负责“执行单步并写入工作区状态”，上层编排交给 Warp 的 Agent/Workflow。

```bash
# 1) 选择素材（passage_id 或文件路径）
python3 -m mvp_story_agent.roles.select --ws "<workspace>" --session s001 --add "pas_123,./para001.md"

# 2) 文档读取 → materials.json
python3 -m mvp_story_agent.roles.reader --ws "<workspace>" --session s001

# 3) 灵感生成 → ideas.json
python3 -m mvp_story_agent.roles.ideator --ws "<workspace>" --session s001 --count 3

# 4) 故事撰写 → story.md
python3 -m mvp_story_agent.roles.writer --ws "<workspace>" --session s001 --idea-index 0 --input "改成开放式结尾"

# 5) 故事审阅 → review.json
python3 -m mvp_story_agent.roles.reviewer --ws "<workspace>" --session s001
```

输出结构（版本永不删除）：

```
<workspace>/sessions/<id>/versions/v001/
  selection.json
  materials.json
  ideas.json
  story.md
  story.meta.json
  review.json
```
