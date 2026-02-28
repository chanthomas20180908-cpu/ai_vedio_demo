# 问题与目标
你要一个可验证概念的本地 CLI“共创代理工具”，重点是“IP 原文库 + 混搭创作（多轮共创→收敛成稿）”，并能一键调用现有端到端 activity 产出视频；实现目标优先、越简单越好，避免一开始大量调试。
# 关键结论（是否需要 Agent 框架）
不依赖任何复杂 agent 框架是最稳妥的：MVP 用“状态文件 + 规则化提示词 + 可重复执行的 CLI 命令”即可实现多轮共创与混搭。
如果后续需要更强的工具编排/记忆/插件生态，再考虑引入框架（例如 LangGraph/LlamaIndex 等）。但在 MVP 阶段引入框架会显著增加调试与耦合成本，并不必要。
# 当前状态（已知）
已存在可用的端到端渲染流水线脚本：workflow/story_video_001/activities/activity_script_001.py（按输入稿生成音频/字幕/分镜/图/视频等）。
已创建 mvp 目录与决策文档：mvp_story_agent/docs/DECISIONS.md。
# 提议的 MVP 范围（先出“有手感”的成果）
第一阶段先保证：
* 你能在一个 workspace 里添加/管理“原文片段（passages）”
* 你能选择多个 passages 进行“混搭创作”，产出 draft/input.md（可直接喂给渲染流水线）
* 你能一条命令 render，把 draft/input.md 交给现有 activity 生成视频
* 全过程产物与日志可追溯（runs/ 记录输入、选取的 passage_ids、渲染输出路径）
# 目录与数据模型（最小可用）
在 pythonProject/mvp_story_agent 下实现：
* cli.py：CLI 入口
* core/workspace.py：workspace 路径/读写/约定
* core/kb.py：知识库（sources/passages/derived）读写
* core/compose.py：混搭创作→生成 draft/input.md
* core/render.py：调用现有 activity（当黑盒）
workspace 建议结构（每个 workspace 一个故事项目）：
* workspace.json（元信息：标题、默认 profile、创建时间等）
* kb/
    * sources.jsonl（书/文章来源等）
    * passages.jsonl（原文片段：source_id, text, tags, loc 等）
    * derived.jsonl（可选：实体/母题等“派生信息”，必须带 evidence_passage_ids）
* draft/
    * brief.md（你写的创作目标/限制）
    * input.md（最终喂渲染的口播稿/分镜指令等）
* sessions/
    * session_YYYYMMDD_HHMM.jsonl（多轮共创对话记录：每轮的 user/assistant/selected_passage_ids/decisions）
* runs/
    * run_YYYYMMDD_HHMM.json（一次 render 的记录：input.md hash、profile、activity out_root、manifest 路径、最终 mp4 路径等）
# CLI 命令设计（先做最少的 4 个）
1) init-workspace
* 输入：workspace 路径、标题、可选默认 profile
* 输出：创建上述目录结构 + 写入 workspace.json + 写入 kb 模板文件（空 jsonl）
2) kb-add-source / kb-add-passage
* 输入：必要字段（source title/author/url；passage source_id/text/tags/loc）
* 输出：追加写入 jsonl；返回生成的 source_id / passage_id
（先支持手工添加，避免自动抓取/切分带来调试成本）
3) compose
* 输入：选择 passage_ids（逗号分隔）+ 你的 brief（可选：直接传字符串或读取 brief.md）
* 输出：生成/覆盖 draft/input.md
* 规则：input.md 必须显式列出“证据”：引用 passage_id 列表与摘录（避免 AI 瞎编）
4) render
* 输入：workspace 路径 + profile（可选；默认 workspace.json）+ 可选 flags（max_scenes/skip_images/only_video 等）
* 动作：调用 activity_script_001.py（黑盒）
* 输出：写 runs/run_*.json，记录 out_root/manifest/final mp4
# 混搭创作能力（MVP 的实现方式：简单且可控）
不做复杂“自治代理”，而是做可重复的“合成器”：
* 输入材料：brief + passages（原文证据）
* 产出：结构化口播稿（按镜头/段落）
* 约束：所有关键设定必须能追溯到 passages（或你显式写入 brief 的新增设定）
实现上：
* compose 先生成一个稳定的模板（含章节：世界观、角色、冲突、分段口播、镜头建议、引用证据）
* 如果接入模型（Gemini/其他）用于润色/扩写，先做“可选开关”，默认也能不调用模型直接把模板+摘录拼成 input.md，保证最小可跑
# 里程碑（按“尽快看到成果”排序）
里程碑 A（最快可见）：
* init-workspace + kb-add-passage + compose（纯模板拼接）→ 立刻得到 draft/input.md
里程碑 B（端到端产出）：
* render 调通现有 activity → 产出 runs 记录 + 最终视频
里程碑 C（更像共创）：
* sessions 记录 + 一个简单的“chat 追加轮次”命令（把每轮决策写入 session.jsonl，然后 compose 时汇总）
# 风险与对策（MVP 视角）
* 风险：渲染流水线依赖外部工具/模型/环境导致调试重
    * 对策：render 只做最薄封装；优先保证 A 里程碑先让你“有手感”；B 里程碑再对齐 profile/参数
* 风险：知识库结构过早复杂化
    * 对策：MVP 只做 sources/passages + 可选 derived，derived 必须 evidence 化
# 需要你拍板的 2 个点（影响实现但都可后改）
1) workspace 的根目录放哪：是统一放到某个固定目录，还是每次 init-workspace 你手动指定路径？
2) compose 的 input.md 结构：你更希望它偏“纯口播稿”，还是“口播稿+镜头/分镜指令”一体？
# 执行方式（遵守你的确认规则）
我可以先只做代码与目录的新增/修改提案（不落盘），你确认后我再开始创建文件与写代码；每次会产生外部效果的动作前，我会按你给的三行固定格式发执行预告并等你回复确认词。