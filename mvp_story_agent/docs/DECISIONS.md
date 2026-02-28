# Story Agent MVP（结论记录）

更新时间：2026-02-26

## 0. 背景与目标
目标：做一个“创作故事图文视频”的 Agent 工具 Demo（概念验证）。
呈现形态：Python CLI 终端应用 + 本地文件系统（共享工作区）。

我们已经具备：
- 端到端“原文 -> 视频”的工作流脚本（作为黑盒函数/工具调用）：
  - `workflow/story_video_001/activities/activity_script_001.py`

MVP 本次重点：
- 多轮对话共创（人 + AI）
- IP 原文库/知识库（尽量基于书籍原文，不靠 AI 瞎编）
- 把“共创产出的原文/文稿 input.md”一次性喂给现有端到端 activity，直接产出视频

## 1. 范围与约束（MVP）
1) 必须有 Workspace（共享媒体/数据空间）。
2) Demo 阶段：
   - 默认不支持“activity 中间确认/二次修改”。
   - 认为“原文创作完成后”会由人确认；一旦调用 activity，就一步跑完，不再插入确认点。
3) 现有 activity 脚本是日常工作用的实现，不满足 function/tool 的要求是正常的；MVP 允许再包一层。
4) Agent 的信息记录（对话/选择/引用/运行记录）要单独设计；activity 的 manifest/log 视为下游产物。
5) 不做降级（缺 key/缺依赖就直接失败），先保证链路清晰。
6) 方案目标：越简单越好，功能优先。

## 2. MVP 顶层架构（最简）
整体分 3 层：
- A. Workspace（本地文件夹）：承载人机共创过程与可追溯资产
- B. IP 原文库（本地文件 + 索引）：承载“可引用”的原文片段
- C. Render 黑盒（现有 activity）：把 input 文稿一次性渲染为视频

关系：
- 对话共创 -> 产出 `workspace/input.md`
- `workspace/input.md` -> 调用 activity -> 产出 `out_root/.../06_video/*.mp4`
- 运行结果（out_root / mp4 / manifest 路径）写回 workspace 的 runs 记录

## 3. Workspace 设计（共享工作区）
Workspace 是长期存在的项目目录，用于人/AI 共同读写。

建议目录（最简可用）：
- `workspace/`
  - `chat/chat.log.md`：多轮对话完整记录（追加写）
  - `brief/creative_brief.json`：结构化创作意图（可迭代覆盖写）
  - `draft/input.md`：最终要喂给 activity 的“原文/文稿”（这是调用 activity 的输入）
  - `refs/selected_passages.json`：本次创作选择了哪些原文片段（passage_id 列表 + 少量说明）
  - `runs/<run_id>.json`：每次调用 activity 的运行记录（见第 6 节）

说明：
- `draft/input.md` 是“对话层 -> 渲染层”的唯一硬接口。
- 人工参与：允许人直接编辑 `creative_brief.json` / `draft/input.md`，并再次触发渲染。

## 4. IP 原文库（知识库）— 最简实现（A+B）
结论：MVP 选 A+B。
- A：原文存储形态优先使用 `.md/.txt`（人工可整理/分段）。
- B：AI 辅助标注（entity/motif/tag），但必须能回指原文片段。
- 同时允许人工轻标注（MVP 量不大）。

### 4.1 为什么不做“设定卡优先”
MVP 不希望“凭空设定”。更稳的沉淀方式是：
- 以“原文片段 passage”为最小资产单元
- 所有派生（实体/母题/关系）都能回指 passage（证据链）

### 4.2 数据模型（最小单元）
建议采用三类索引（先用 JSONL/JSON，简单可读）：

1) `sources.jsonl`（原文来源）
- `source_id`
- `title` / `author` / `translator` / `edition`
- `origin_path`（本地原文文件路径）
- `notes`

2) `passages.jsonl`（原文片段）
- `passage_id`
- `source_id`
- `location`（章节/段落编号/页码等，尽力填写）
- `text`（原文摘录）
- `tags`（可选：人物/地点/母题等粗标签）

3) `derived/`（派生层，全部必须带证据 passage_id）
- `entities.jsonl`：人物/地点/物件（每条含 `evidence_passage_ids`）
- `motifs.jsonl`：母题/冲突机制（每条含 `evidence_passage_ids`）
- （可选后续）`relations.jsonl`：实体关系边（同样带 evidence）

### 4.3 混搭的抽象维度（故事创作通用）
MVP 的混搭维度不做“游戏对战设定”，而做更通用的叙事维度：
- 母题（Motif）：禁忌知识、背叛、天命、救赎、献祭、误入、试炼、权力更迭...
- 冲突机制（Conflict Mechanism）：规则型恐怖、道德困境、身份反转、代价交换...
- 关系（Relationship）：师徒、君臣、父子、盟友、宿敌、神与人、人与怪...

这些维度最终会进入 `creative_brief.json` 与 `draft/input.md`，并且每个关键设定尽量能追溯到 passage。

## 5. “共创对话 -> input.md” 的收敛机制（最简）
即使不做 activity 中间确认，也必须在“渲染前”收敛出可执行输入。

建议固定 3 阶段（不强制 UI，只是行为约定）：
1) 发散：基于 brief + passages，产出 2~3 个高概念方案
2) 选择：人从方案中选 1 个，并补充 3 个关键约束
3) 定稿：生成 `creative_brief.json` 与最终 `draft/input.md`

## 6. Render 黑盒（现有 activity）与运行记录
现有脚本：`workflow/story_video_001/activities/activity_script_001.py`
- 输入：单个文稿文件（md/txt）
- 输出：创建 out_root（含 spoken/storyboard/images/audio/subtitles/video + manifest.json）

MVP 要求：把 activity 当“黑盒函数”调用，Agent 侧只做记录与引用。

### 6.1 runs 记录（Agent 侧，机器可读）
建议 `workspace/runs/<run_id>.json` 最少包含：
- `run_id`
- `ts`
- `profile_name`
- `workspace_path`
- `input_md_path` + `input_md_sha256`
- `selected_passage_ids`（本次引用列表）
- `activity_out_root`
- `activity_manifest_path`
- `final_mp4_path`
- `ok` + `error`（失败时写入）

## 7. 与现有 spoken pipeline 的接口对齐
现有 `task_spoken_001(raw_text=...)` 依赖 raw_text 结构与 profile prompt。
为了稳定：
- `draft/input.md` 需要一个固定模板（章节背景/本段目标/原文片段/约束），避免对话产出格式漂移。

备注：具体模板内容与“IP 混搭 prompts”将由 MVP 的 CLI/Agent 层实现时确定。
