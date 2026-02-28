# I2V 表情动图测试：提示词复用 + AI 生成提示词 + 多模型批量跑（方案大纲）

## 目标与问题
你现在的 I2V（image-to-video）测试主要依赖 `data/test_prompt*.py` 里的硬编码提示词 + `debug/*` 脚本串行跑模型（例如 `debug/debug_sync_i2v_3mdls.py`、`debug/run_mvp_i2v_test.py`）。
新增/维护提示词与案例需要手动改代码，成本高。

本次要达成两类诉求：
1) 复用已有提示词：选模型 -> 生成视频/动图用于测试
2) 让 AI 生成提示词：你给图片路径 + 选择全部/部分模型 -> 批量生成视频/动图用于测试

## 现状梳理（与本次需求直接相关）
- 多模型批跑入口：`debug/debug_sync_i2v_3mdls.py:def debug_sync_i2v_mdls(...)`
  - 统一上传一次图片（`upload_file_to_oss`）
  - 用硬编码 `model_configs` 串行调用：
    - wan（`debug/debug_sync_wan_i2v.py:debug_synx_i2v_wan22`）
    - doubao（`test/test_i2v_doubao.py:debug_seedance_i2v`）
    - minimax（`test/test_i2v_minimax.py:debug_minimax_i2v`）
- 提示词来源：`data/test_prompt.py` / `data/test_prompt_mvp.py` 的常量
- Gradio UI：`gradio/video_demo_gradio.py` 目前主要覆盖 DashScope 的几个视频能力 Tab，不覆盖你现在的 I2V 三模型批跑与“表情动图”场景
- 缺口：没有“提示词库/案例库”的数据结构；没有“从 mp4 产出 gif”的统一能力；没有“AI 生成 I2V 提示词”的模块化入口

## 总体方案（推荐）
把“提示词管理/批跑/产物格式化”从 `debug/*` 迁移到一个可复用的正式模块（保留 debug 脚本做 thin wrapper），并提供两个入口：CLI +（可选）Gradio 新 Tab。

### A. 结构调整（新增核心模块）
1) 新增 I2V 批跑核心：`core/i2v/`
- `core/i2v/models.py`
  - 定义统一的 I2V 模型适配器接口（输入 image_url + prompt + params，输出 video_url + 本地路径 + 元信息）
  - 为现有三家模型实现 adapter（直接复用你现有的 `debug_seedance_i2v` / `debug_minimax_i2v` / `debug_synx_i2v_wan22` 或抽出公共逻辑）
- `core/i2v/runner.py`
  - `run_i2v_batch(image_path, prompt_text, models=[...], output={mp4,gif}, ...)`
  - 负责：一次上传图片、依次/并行跑模型、统一落盘结果、汇总结构化结果（JSON）

2) 新增提示词库（从代码常量迁移到数据文件）：`data/prompt/i2v_prompts.(yaml|json)`
- 每条 prompt 结构建议：
  - `id`: 稳定标识（例如 `steam_rage`）
  - `title`: 中文名称
  - `prompt`: 文本提示词（可多语言）
  - `tags`: [rage, cry, meme]
  - `defaults`: {duration, resolution, camera_fixed, watermark, ...}
  - `notes/examples`: 可选
- 配套读取工具：`core/prompt_library/i2v_prompt_library.py`
  - `list_prompts()` / `get_prompt(id)` / `search(tags, keyword)`

3) 新增“动图输出”能力：`util/media_gif.py`（或扩展 `util/media.py`）
- `mp4_to_gif(input_mp4, output_gif, fps, scale, loop)`
- 注意：ffmpeg 参数需要统一（质量/体积折中），并且作为可选开关，不强制所有任务都转 gif

4) 新增“AI 生成 I2V 提示词”模块：`core/prompt_generation/i2v_prompt_generator.py`
- 输入：
  - 图片（本地路径 -> 上传 OSS -> 传给支持视觉/多模态的 LLM 或者先做图片理解）
  - 目标情绪/动作（例如“委屈大哭”）
  - 输出约束（时长、镜头固定、不要变形、不要新增人物等）
- 输出：
  - `prompt_text`
  - 可选：`negative_prompt`（如果各模型支持）
  - 可选：`params`（duration/resolution…）
- 实现路径建议（二选一或先做简版）：
  - 简版：纯文本生成（你给“图片描述”或“关键词”，AI 只负责生成 I2V prompt）
  - 完整版：自动从图片提取关键信息（复用你已有的图片理解 prompt 体系 `config/prompt_default.py`），再生成 I2V prompt

### B. 两个诉求如何落地
#### 诉求 1：复用已有提示词 + 选择模型生成动图测试
- UI/CLI 选择 prompt：从 `i2v_prompts.yaml` 选 `prompt_id`
- 选择模型：从模型 registry 选择（全部或子集）
- 选择输出：mp4 必出；gif 可选
- 执行：`run_i2v_batch(image_path, prompt_id, models, to_gif=True)`

#### 诉求 2：AI 生成提示词 + 你给图片路径 + 全部/部分模型批量生成动图
- 先调用 `i2v_prompt_generator.generate(image_path, goal=..., constraints=...)` 得到 prompt
- 再调用 `run_i2v_batch(..., prompt_text=generated_prompt, models=..., to_gif=...)`
- 可选增强：运行成功后询问是否把 prompt 写入 `i2v_prompts.yaml`（形成“半自动沉淀”）

## 入口形态（建议优先级）
### 1) CLI（优先做，最省改动、最稳定）
新增 `tools/i2v_batch_run.py` 支持：
- `--image /path/to.png`
- `--prompt-id steam_rage` 或 `--prompt-text "..."`
- `--models wan-2.2-i2v-plus,doubao-seedance-1-lite,MiniMax-Hailuo-02` 或 `--all-models`
- `--gif` / `--gif-fps` / `--gif-scale`

输出：
- `data/Data_results/video_results/<task_id>/<model>.mp4`
- `data/Data_results/video_results/<task_id>/<model>.gif`
- `data/Data_results/video_results/<task_id>/summary.json`

### 2) Gradio 新 Tab（第二阶段）
在 `gradio/video_demo_gradio.py` 增加一个 Tab：
- 输入：上传图片、选择 prompt_id 或“AI 生成 prompt”、勾选模型、勾选输出 gif
- 输出：表格（每行一个模型：耗时、mp4、gif）、以及 summary.json 下载

## 与现有代码的衔接策略（避免大改）
- 保留 `debug/debug_sync_i2v_3mdls.py` 与 `debug/run_mvp_i2v_test.py`，但改为调用 `core/i2v/runner.py`（thin wrapper），不再自己维护 model_configs。
- `test/test_i2v_doubao.py` / `test/test_i2v_minimax.py` 可逐步抽出为 adapter，测试文件保留。

## 关键设计点（需要确认）
1) 提示词库文件格式：YAML（可读性好） vs JSON（更严格）
2) “动图”定义：最终统一产出 GIF 还是 APNG/WebP（gif 体积大但兼容最好）
3) AI 生成提示词的模式：
- 先做简版（你给目标情绪/动作，AI 直接输出 prompt）
- 再做完整版（自动读图 -> 生成更贴脸 prompt）
4) 批跑策略：默认串行（稳定）还是并发（更快但要控速/重试）

## 交付拆分（建议分两步）
- Step 1（先满足诉求 1）：提示词库 + I2V runner + gif 输出 + CLI
- Step 2（满足诉求 2）：AI prompt generator +（可选）Gradio Tab + prompt 沉淀写回
