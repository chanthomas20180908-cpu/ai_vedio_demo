# debug/story_audio 目录说明

**⚠️ 一旦我所属的文件夹有所变化，请更新我。**

## 目标
输入一个 Markdown（当前约定：文件内容为纯文字，不包含 Markdown 符号），输出：
- 有声书音频：`*.mp3`
- 字幕文件：`*.srt`
- 自动生成的 SSML：`*.ssml`（用于检查自动插入的 `<break>`）

## 约定
- 语速默认 1.3 倍（`--speech_rate 1.3`）。
- 音频生成尽量连贯：优先整篇一次输入（超过 20000 字符才拆分成多个“音频块”）。
- 字幕按标点切分：
  - 强分割：`。！？!?`、`……`、`——`（连续破折号）
  - 弱分割：`，,、；;：:`
- 默认不做长度限制（`--subtitle_max_len 0`），如需限制可设置为 >0。
- 默认会自动插入 SSML `<break>` 增加停顿/气口（可用 `--no_break` 关闭）。
- 字幕时间轴为估算：按每个音频块内“字幕字符数占比”分配该块总时长。

## 文件
- `run_md_to_story_audio.py`：入口脚本，负责读取 md、切段、调用 component 生成分段音频、拼接音频、生成 srt（默认带自动 `<break>`）。
- `run_md_to_story_audio_with_timestamps.py`：新增方法：使用 DashScope 返回的时间戳生成更精准的 srt（实现简单，不影响原脚本；默认不做 `<break>`）。
- `run_md_to_story_audio_minimax.py`：MiniMax 版：可选音色克隆（得到 voice_id），再用异步 TTS 合成长文本；字幕时间轴为估算（按字符占比）。

## 输出目录
- `output/`：保存最终产物（mp3 + srt）。
- 文件名会附带运行时间戳，保证唯一性：`<输入文件名>_YYYYMMDD_HHMMSS.(mp3|srt|ssml)`

## 运行方式
示例：
- `python3 debug/story_audio/run_md_to_story_audio.py --input /path/to/book.md`

可选参数：
- `--voice`：默认 `longgaoseng`
- `--model`：默认 `cosyvoice-v2`
- `--speech_rate`：默认 `1.3`
- `--sleep_s`：默认 `0.05`（每个音频块合成后等待）
- `--no_break`：关闭自动 SSML `<break>`
- `--gap_ms`：音频块之间静音间隔（默认 0）
- `--subtitle_max_len`：默认 `0`（不限制）
- `--audio_max_chars`：默认 `20000`
