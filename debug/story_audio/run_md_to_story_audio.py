"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 一个 .md 文件（当前约定：内容为纯文字，不包含 Markdown 符号）
Output: 最终 mp3 + srt（字幕按标点+max_len 切分；时间轴为估算）
Pos: debug/story_audio/run_md_to_story_audio.py
"""

import argparse
import os
import re
import sys
import time
from pathlib import Path


def _xml_escape_text(s: str) -> str:
    # Escape plain text for SSML XML
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )

# 允许直接运行该脚本：把项目根目录加入 sys.path，确保可 import component/
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
from pydub import AudioSegment

from component.muti.synthesis_audio import synthesis_audio
from config.logging_config import setup_logging


def _read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# 强分割：句末标点 + 省略号 + 连续破折号
_STRONG_PUNC_RE = re.compile(r"(.*?(?:[。！？!?]+|……+|—{2,}))")
# 弱分割：逗号/顿号/分号/冒号等
_WEAK_PUNC_RE = re.compile(r"([^，,、；;：:]*[，,、；;：:]+)")


def _normalize_text(text: str) -> str:
    # 统一换行
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _hard_split(s: str, max_len: int) -> list[str]:
    s = s.strip()
    if not s:
        return []
    if max_len <= 0:
        return [s]
    return [s[i : i + max_len] for i in range(0, len(s), max_len) if s[i : i + max_len].strip()]


def _split_by_re_keep_punc(s: str, r: re.Pattern) -> list[str]:
    s = s.strip()
    if not s:
        return []
    parts = r.findall(s)
    rest = r.sub("", s)
    out: list[str] = []
    for p in parts:
        pp = p.strip()
        if pp:
            out.append(pp)
    rr = rest.strip()
    if rr:
        out.append(rr)
    return out


def _split_subtitles(text: str, max_len: int = 0) -> list[str]:
    """字幕切分：按标点断句（强+弱）。

    规则：
    - 强标点：。！？!?
    - 弱标点：，,、；;：:
    - 默认不做长度限制（max_len<=0 表示不限制）
    - 字幕文本不保留换行（更适合字幕显示）

    说明：
    - 若你将 max_len 设为 >0，则会在弱标点切分后再做硬切。
    """
    t = _normalize_text(text).replace("\n", "")
    if t.strip() == "":
        return []

    strong = _split_by_re_keep_punc(t, _STRONG_PUNC_RE)
    out: list[str] = []
    for seg in strong:
        weak = _split_by_re_keep_punc(seg, _WEAK_PUNC_RE)
        for w in weak:
            ww = w.strip()
            if not ww:
                continue
            if max_len and max_len > 0 and len(ww) > max_len:
                out.extend(_hard_split(ww, max_len))
            else:
                out.append(ww)

    return out


def _split_audio_blocks(text: str, max_chars: int = 20000) -> list[str]:
    """音频输入尽量连贯：优先整篇作为一个 block；超过上限才拆分。

    注意：官方字符计算规则里，汉字按 2 个字符计算。
    这里为了保持实现简单，仍按 Python 的 len() 近似切分。

    拆分策略：在 max_chars 之前，尽量在强标点处截断。
    """
    t = _normalize_text(text)
    if len(t) <= max_chars:
        return [t]

    blocks: list[str] = []
    i = 0
    n = len(t)
    while i < n:
        end = min(n, i + max_chars)
        if end == n:
            blocks.append(t[i:end])
            break

        # 尽量往回找一个合适的断点（强标点/换行）
        window = t[i:end]
        cut = max(window.rfind("。"), window.rfind("！"), window.rfind("？"), window.rfind("!"), window.rfind("?"), window.rfind("\n"))
        if cut <= 0:
            cut = len(window)
        else:
            cut = cut + 1

        blocks.append(window[:cut])
        i = i + cut

    return [b for b in blocks if b.strip()]

def _format_srt_time(ms: int) -> str:
    if ms < 0:
        ms = 0
    h = ms // 3_600_000
    ms %= 3_600_000
    m = ms // 60_000
    ms %= 60_000
    s = ms // 1_000
    ms %= 1_000
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _break_tag(ms: int) -> str:
    return f"<break time=\"{int(ms)}ms\"/>"


def _to_ssml_with_breaks(text: str) -> str:
    """把纯文本转换成 SSML，并按规则插入 break。

    默认停顿规则（可后续参数化）：
    - 段落空行：600ms
    - 单个换行：200ms
    - ……：500ms
    - ——(连续破折号)：300ms
    - 强句末标点：250ms
    - 弱标点：120ms

    返回值包含 <speak>...</speak>
    """
    t = _normalize_text(text)

    out: list[str] = ["<speak>"]

    i = 0
    n = len(t)
    while i < n:
        # 段落空行
        if t.startswith("\n\n", i):
            out.append(_break_tag(600))
            # 吃掉连续空行
            while i < n and t[i] == "\n":
                i += 1
            continue

        # 单个换行
        if t[i] == "\n":
            out.append(_break_tag(200))
            i += 1
            continue

        # 省略号（中文）
        if t.startswith("……", i):
            out.append(_xml_escape_text("……"))
            out.append(_break_tag(500))
            i += 2
            continue

        # 连续破折号
        if t[i] == "—":
            j = i
            while j < n and t[j] == "—":
                j += 1
            dash = t[i:j]
            out.append(_xml_escape_text(dash))
            if (j - i) >= 2:
                out.append(_break_tag(300))
            i = j
            continue

        ch = t[i]

        # 标点停顿
        if ch in "。！？!?":
            out.append(_xml_escape_text(ch))
            out.append(_break_tag(250))
            i += 1
            continue

        if ch in "，,、；;：:":
            out.append(_xml_escape_text(ch))
            out.append(_break_tag(120))
            i += 1
            continue

        # 普通字符
        out.append(_xml_escape_text(ch))
        i += 1

    out.append("</speak>")
    return "".join(out)


def _write_srt(srt_path: Path, subtitle_lines: list[str], durations_ms: list[int]) -> None:
    if len(subtitle_lines) != len(durations_ms):
        raise ValueError("subtitle_lines 与 durations_ms 长度不一致")

    t = 0
    lines: list[str] = []
    for idx, (txt, dur) in enumerate(zip(subtitle_lines, durations_ms), start=1):
        start = t
        end = t + max(1, int(dur))
        t = end

        lines.append(str(idx))
        lines.append(f"{_format_srt_time(start)} --> {_format_srt_time(end)}")
        lines.append(txt)
        lines.append("")

    srt_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="md(纯文本) -> 有声书 mp3 + srt")
    parser.add_argument("--input", required=True, help="输入 md 文件路径（当前约定：纯文字）")
    parser.add_argument("--model", default="cosyvoice-v2", help="DashScope CosyVoice 模型")
    parser.add_argument("--voice", default="longgaoseng", help="音色 voice id")
    parser.add_argument("--speech_rate", type=float, default=1.3, help="语速（默认 1.3 倍）")
    parser.add_argument("--sleep_s", type=float, default=0.05, help="每个音频块合成后的等待时间（秒）")
    parser.add_argument("--no_break", action="store_true", help="禁用自动插入 SSML <break>（默认启用）")
    parser.add_argument("--gap_ms", type=int, default=0, help="音频块与音频块之间静音间隔 (ms)，默认 0")
    parser.add_argument("--subtitle_max_len", type=int, default=0, help="字幕单条最大长度（默认 0=不限制）")
    parser.add_argument("--audio_max_chars", type=int, default=20000, help="单次 TTS 输入最大字符数（默认 20000）")
    parser.add_argument(
        "--out_dir",
        default=str(Path(__file__).parent / "output"),
        help="最终输出目录（mp3 + srt）",
    )

    args = parser.parse_args()

    setup_logging()
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../env/default.env"))

    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("DASHSCOPE_API_KEY 未配置")

    input_path = Path(args.input).expanduser().resolve()
    if not input_path.exists():
        raise FileNotFoundError(str(input_path))

    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    run_ts = time.strftime("%Y%m%d_%H%M%S")

    raw_text = _read_text_file(input_path)
    if raw_text.strip() == "":
        raise ValueError("输入文件为空")

    # 音频：尽量整篇一次输入（超过上限才拆分）
    audio_blocks = _split_audio_blocks(raw_text, max_chars=args.audio_max_chars)
    if not audio_blocks:
        raise ValueError("无法切分出有效音频块")

    # 字幕：按标点 + max_len 切分（每个音频块内生成字幕，时间轴按字符比例估算）
    subtitle_lines: list[str] = []
    subtitle_durations_ms: list[int] = []

    combined = AudioSegment.empty()

    # 生成一份 ssml 文件（用于复现与检查）
    ssml_text = None if args.no_break else _to_ssml_with_breaks(raw_text)
    if ssml_text is not None:
        ssml_path = out_dir / f"{input_path.stem}_{run_ts}.ssml"
        ssml_path.write_text(ssml_text, encoding="utf-8")

    for bi, block_text in enumerate(audio_blocks):
        # 1) 生成该块音频
        tts_text = block_text if args.no_break else _to_ssml_with_breaks(block_text)
        save_path, _, _ = synthesis_audio(
            api_key=api_key,
            model_type="cosyvoice",
            text=tts_text,
            model=args.model,
            voice=args.voice,
            speech_rate=args.speech_rate,
        )
        if not save_path:
            raise RuntimeError("语音合成失败：返回 save_path 为空")

        block_audio = AudioSegment.from_file(save_path, format="mp3")
        combined += block_audio

        # 2) 该块字幕切分
        subs = _split_subtitles(block_text, max_len=args.subtitle_max_len)
        if subs:
            lens = [len(s.strip()) for s in subs]
            total = sum(lens)
            if total <= 0:
                # 兜底：平均分配
                per = max(1, int(len(block_audio) / len(subs)))
                for s in subs:
                    subtitle_lines.append(s)
                    subtitle_durations_ms.append(per)
            else:
                remain = len(block_audio)
                for i, (s, l) in enumerate(zip(subs, lens)):
                    if i == len(subs) - 1:
                        dur = max(1, remain)
                    else:
                        dur = max(1, int(len(block_audio) * (l / total)))
                        remain -= dur
                    subtitle_lines.append(s)
                    subtitle_durations_ms.append(dur)

        # 3) 块间静音
        if bi != len(audio_blocks) - 1 and args.gap_ms and args.gap_ms > 0:
            combined += AudioSegment.silent(duration=args.gap_ms)
            # 把静音算到上一条字幕上（如果存在），保证时间轴和音频一致
            if subtitle_durations_ms:
                subtitle_durations_ms[-1] += args.gap_ms

        # 4) 减少服务端压力
        if args.sleep_s and args.sleep_s > 0:
            time.sleep(args.sleep_s)

    if not subtitle_lines:
        raise ValueError("未生成任何字幕行（请检查输入文本）")

    base_name = input_path.stem
    out_mp3 = out_dir / f"{base_name}_{run_ts}.mp3"
    out_srt = out_dir / f"{base_name}_{run_ts}.srt"

    combined.export(out_mp3, format="mp3")
    _write_srt(out_srt, subtitle_lines=subtitle_lines, durations_ms=subtitle_durations_ms)

    print(f"OK: {out_mp3}")
    print(f"OK: {out_srt}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
