"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 一个 .md 文件（当前约定：内容为纯文字，不包含 Markdown 符号）
Output: 最终 mp3 + srt（字幕按标点切分；时间轴为估算）
Pos: debug/story_audio/run_md_to_story_audio_minimax.py

目标（最简可用版 / 方案A）：
- 可选：用参考音频做 MiniMax 音色快速复刻（得到 voice_id）
- 用 voice_id 走 MiniMax 异步长文本 TTS（t2a_async_v2）生成 mp3
- 生成 srt：按标点切句 + 按字符占比分配音频总时长（估算版，稳）

用法：
1) 第一次：克隆 + 合成（会写 voice_id cache）
python3 debug/story_audio/run_md_to_story_audio_minimax.py \
  --input /path/to/book.md \
  --clone_audio /path/to/ref.mp3 \
  --voice_id my_voice_001

2) 后续：只合成（复用 voice_id）
python3 debug/story_audio/run_md_to_story_audio_minimax.py \
  --input /path/to/book.md \
  --voice_id my_voice_001

3) 或者：不传 --voice_id，自动从 cache 读取
python3 debug/story_audio/run_md_to_story_audio_minimax.py --input /path/to/book.md

环境变量：
- MINIMAX_API_KEY（优先从 env/default.env 加载）
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv
from pydub import AudioSegment


# 允许直接运行该脚本：把项目根目录加入 sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.logging_config import setup_logging


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_minimax_api_key() -> str:
    root = _project_root()
    env_path = root / "env" / "default.env"
    try:
        load_dotenv(dotenv_path=str(env_path))
    except Exception:
        pass

    api_key = os.getenv("MINIMAX_API_KEY")
    if not api_key:
        raise ValueError("MINIMAX_API_KEY 未配置")
    return api_key


def _read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _normalize_text(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


# 强分割：句末标点 + 省略号 + 连续破折号
_STRONG_PUNC_RE = re.compile(r"(.*?(?:[。！？!?]+|……+|—{2,}))")
# 弱分割：逗号/顿号/分号/冒号等
_WEAK_PUNC_RE = re.compile(r"([^，,、；;：:]*[，,、；;：:]+)")


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
    """字幕切分：按标点断句（强+弱），不保留换行。"""
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


def _write_srt_estimated(srt_path: Path, subtitle_lines: list[str], total_audio_ms: int) -> None:
    if not subtitle_lines:
        raise ValueError("未生成任何字幕行（请检查输入文本）")

    lens = [len(s.strip()) for s in subtitle_lines]
    total = sum(lens)

    durations_ms: list[int] = []
    if total <= 0:
        per = max(1, int(total_audio_ms / len(subtitle_lines)))
        durations_ms = [per] * len(subtitle_lines)
        # 修正最后一条对齐总时长
        durations_ms[-1] = max(1, total_audio_ms - sum(durations_ms[:-1]))
    else:
        remain = int(total_audio_ms)
        for i, l in enumerate(lens):
            if i == len(lens) - 1:
                dur = max(1, remain)
            else:
                dur = max(1, int(total_audio_ms * (l / total)))
                remain -= dur
            durations_ms.append(dur)

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


def _cache_write_voice_id(cache_path: Path, voice_id: str) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps({"voice_id": voice_id}, ensure_ascii=False, indent=2), encoding="utf-8")


def _cache_read_voice_id(cache_path: Path) -> Optional[str]:
    if not cache_path.exists():
        return None
    try:
        obj = json.loads(cache_path.read_text(encoding="utf-8"))
        v = obj.get("voice_id")
        return str(v) if v else None
    except Exception:
        return None


def _minimax_headers(api_key: str) -> dict:
    return {"Authorization": f"Bearer {api_key}"}


def minimax_upload_file(api_key: str, file_path: Path, purpose: str) -> str:
    url = "https://api.minimaxi.com/v1/files/upload"
    headers = _minimax_headers(api_key)

    with open(file_path, "rb") as f:
        files = [("file", (file_path.name, f))]
        data = {"purpose": purpose}
        resp = requests.post(url, headers=headers, data=data, files=files, timeout=300)

    resp.raise_for_status()
    j = resp.json()
    file_id = (j.get("file") or {}).get("file_id")
    if not file_id:
        raise RuntimeError(f"上传失败：未返回 file_id，resp={j}")
    return str(file_id)


def _as_int_if_digits(x: Optional[str]):
    if x is None:
        return None
    s = str(x).strip()
    if s.isdigit():
        try:
            return int(s)
        except Exception:
            return s
    return s


def minimax_voice_clone(
    api_key: str,
    voice_id: str,
    clone_audio_file_id: str,
    model: str,
    prompt_audio_file_id: Optional[str] = None,
    prompt_text: Optional[str] = None,
    preview_text: Optional[str] = None,
) -> dict:
    url = "https://api.minimaxi.com/v1/voice_clone"
    headers = {**_minimax_headers(api_key), "Content-Type": "application/json"}

    # 文档示例里包含 text 字段（用于生成试听/校验）。这里给一个默认值，尽量避免 voice 未真正创建。
    if not preview_text:
        preview_text = "大兄弟，听您口音不是本地人吧，头回来天津卫，待会您可甭跟着导航走。"

    payload: dict = {
        "file_id": _as_int_if_digits(clone_audio_file_id),
        "voice_id": str(voice_id),
        "text": preview_text,
        "model": model,
    }

    if prompt_audio_file_id:
        payload["clone_prompt"] = {
            "prompt_audio": _as_int_if_digits(prompt_audio_file_id),
            "prompt_text": prompt_text or "",
        }

    resp = requests.post(url, headers=headers, json=payload, timeout=300)
    resp.raise_for_status()
    return resp.json()


def minimax_tts_async_create(
    api_key: str,
    text: str,
    model: str,
    voice_id: str,
    speed: float,
    vol: int,
    pitch: float,
    audio_format: str,
    sample_rate: int,
    bitrate: int,
    channel: int,
) -> str:
    """创建异步 TTS 任务。

    为了尽量稳 + 简单：
    - 先只发送最小必需字段（model/text/voice_setting）
    - audio_setting 容易触发 invalid params，默认先不传
    """
    url = "https://api.minimaxi.com/v1/t2a_async_v2"
    headers = {**_minimax_headers(api_key), "Content-Type": "application/json"}

    # speed/pitch 在文档示例里为整数；这里尽量用 int，避免服务端严格校验
    voice_setting = {
        "voice_id": voice_id,
        "speed": int(round(speed)),
        "vol": int(vol),
        "pitch": int(round(pitch)),
    }

    payload = {
        "model": model,
        "text": text,
        "language_boost": "auto",
        "voice_setting": voice_setting,
    }

    # 预留：如需强制音频参数，可按需打开（先保持最简）
    _ = (audio_format, sample_rate, bitrate, channel)

    resp = requests.post(url, headers=headers, json=payload, timeout=300)
    resp.raise_for_status()
    j = resp.json()

    base = j.get("base_resp") or {}
    if base and base.get("status_code") not in (None, 0):
        raise RuntimeError(f"创建 TTS 任务失败：{base.get('status_msg')} (code={base.get('status_code')}), resp={j}")

    task_id = j.get("task_id") or (j.get("data") or {}).get("task_id")
    # task_id==0 通常表示失败
    if not task_id:
        raise RuntimeError(f"创建 TTS 任务失败：未返回 task_id，resp={j}")
    return str(task_id)


def minimax_tts_async_query(api_key: str, task_id: str) -> dict:
    url = f"https://api.minimaxi.com/v1/query/t2a_async_query_v2?task_id={task_id}"
    headers = {**_minimax_headers(api_key), "content-type": "application/json"}
    resp = requests.get(url, headers=headers, timeout=60)
    resp.raise_for_status()
    return resp.json()


def minimax_wait_tts_done(api_key: str, task_id: str, poll_interval_s: int, max_wait_s: int, dump_query_json: bool) -> str:
    start = time.time()
    last = None
    while time.time() - start < max_wait_s:
        j = minimax_tts_async_query(api_key, task_id)
        last = j

        if dump_query_json:
            print(json.dumps(j, ensure_ascii=False, indent=2))

        # 兼容多种可能字段
        status = (
            j.get("status")
            or j.get("task_status")
            or (j.get("data") or {}).get("status")
            or (j.get("data") or {}).get("task_status")
        )

        # 常见完成值
        if status in ("Success", "SUCCESS", "finished", "FINISHED", "Done", "DONE"):
            file_id = j.get("file_id") or (j.get("data") or {}).get("file_id")
            if not file_id:
                raise RuntimeError(f"任务已完成但未返回 file_id：resp={j}")
            return str(file_id)

        # 常见失败值
        if status in ("Failed", "FAIL", "Fail", "failed", "error", "ERROR"):
            raise RuntimeError(f"TTS 任务失败：resp={j}")

        time.sleep(max(1, int(poll_interval_s)))

    raise RuntimeError(f"TTS 任务超时（{max_wait_s}s）：last={last}")


def minimax_download_file_content(api_key: str, file_id: str) -> bytes:
    url = f"https://api.minimaxi.com/v1/files/retrieve_content?file_id={file_id}"
    headers = {**_minimax_headers(api_key), "content-type": "application/json"}
    resp = requests.get(url, headers=headers, timeout=300)
    resp.raise_for_status()
    return resp.content


def main() -> int:
    parser = argparse.ArgumentParser(description="md(纯文本) -> MiniMax 音色克隆(可选) + 异步TTS -> mp3 + srt(估算)")
    parser.add_argument("--input", required=True, help="输入 md 文件路径（当前约定：纯文字）")

    # 克隆相关（可选）
    parser.add_argument("--clone_audio", default="", help="用于克隆的参考音频路径（mp3/m4a/wav；不传则不克隆）")
    parser.add_argument("--prompt_audio", default="", help="可选：增强克隆效果的 prompt 音频（<8s）")
    parser.add_argument("--prompt_text", default="", help="可选：prompt 音频对应的文本")

    # voice_id：优先使用 --voice_id；若不传则读 cache；若传 clone_audio 则会写 cache
    parser.add_argument("--voice_id", default="", help="音色 id（克隆输出/或已存在）")
    parser.add_argument(
        "--voice_cache",
        default=str(Path(__file__).parent / "output" / "minimax_voice_id.json"),
        help="voice_id 缓存文件（json）",
    )

    # TTS 参数（保持简单：给常用几项）
    parser.add_argument("--model", default="speech-2.8-hd", help="MiniMax 语音模型")
    parser.add_argument("--speed", type=float, default=1.0, help="语速")
    parser.add_argument("--vol", type=int, default=10, help="音量")
    parser.add_argument("--pitch", type=float, default=1.0, help="音高")

    parser.add_argument("--format", default="mp3", choices=["mp3", "wav"], help="输出音频格式")
    parser.add_argument("--sample_rate", type=int, default=32000, help="采样率")
    parser.add_argument("--bitrate", type=int, default=128000, help="比特率")
    parser.add_argument("--channel", type=int, default=2, help="声道")

    parser.add_argument("--subtitle_max_len", type=int, default=0, help="字幕单条最大长度（默认 0=不限制）")

    parser.add_argument("--poll_interval_s", type=int, default=5, help="异步任务轮询间隔（秒）")
    parser.add_argument("--max_wait_s", type=int, default=900, help="异步任务最大等待（秒）")
    parser.add_argument("--dump_query_json", action="store_true", help="调试：打印 query JSON")
    parser.add_argument("--dump_clone_json", action="store_true", help="调试：打印 clone JSON")

    parser.add_argument(
        "--out_dir",
        default=str(Path(__file__).parent / "output"),
        help="最终输出目录（mp3 + srt）",
    )

    args = parser.parse_args()

    setup_logging()

    api_key = _load_minimax_api_key()

    input_path = Path(args.input).expanduser().resolve()
    if not input_path.exists():
        raise FileNotFoundError(str(input_path))

    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    voice_cache_path = Path(args.voice_cache).expanduser().resolve()

    # 1) 读取文本
    raw_text = _read_text_file(input_path)
    raw_text = raw_text.strip()
    if not raw_text:
        raise ValueError("输入文件为空")

    # 2) 确定 voice_id（最简单优先级）
    voice_id = (args.voice_id or "").strip()

    # 2.1) 如果需要克隆：上传音频 -> voice_clone
    if args.clone_audio:
        clone_path = Path(args.clone_audio).expanduser().resolve()
        if not clone_path.exists():
            raise FileNotFoundError(str(clone_path))

        if not voice_id:
            raise ValueError("使用 --clone_audio 时必须同时提供 --voice_id（用于保存/复用）")

        clone_file_id = minimax_upload_file(api_key, clone_path, purpose="voice_clone")

        prompt_file_id = None
        if args.prompt_audio:
            prompt_path = Path(args.prompt_audio).expanduser().resolve()
            if not prompt_path.exists():
                raise FileNotFoundError(str(prompt_path))
            prompt_file_id = minimax_upload_file(api_key, prompt_path, purpose="prompt_audio")

        clone_resp = minimax_voice_clone(
            api_key=api_key,
            voice_id=voice_id,
            clone_audio_file_id=clone_file_id,
            model=args.model,
            prompt_audio_file_id=prompt_file_id,
            prompt_text=args.prompt_text,
            preview_text=args.prompt_text or None,
        )

        if args.dump_clone_json:
            print(json.dumps(clone_resp, ensure_ascii=False, indent=2))

        # 有些情况下服务端会返回真正可用于合成的 voice_id，这里优先用返回值。
        returned_voice_id = (
            clone_resp.get("voice_id")
            or (clone_resp.get("data") or {}).get("voice_id")
            or (clone_resp.get("voice") or {}).get("voice_id")
        )
        if returned_voice_id:
            voice_id = str(returned_voice_id)

        # 写 cache
        _cache_write_voice_id(voice_cache_path, voice_id)

    # 2.2) 如果没给 voice_id：读 cache
    if not voice_id:
        voice_id = _cache_read_voice_id(voice_cache_path) or ""

    if not voice_id:
        raise ValueError("未指定 voice_id：请传 --voice_id，或先用 --clone_audio 生成并写入 cache")

    # 3) 异步 TTS
    task_id = minimax_tts_async_create(
        api_key=api_key,
        text=raw_text,
        model=args.model,
        voice_id=voice_id,
        speed=args.speed,
        vol=args.vol,
        pitch=args.pitch,
        audio_format=args.format,
        sample_rate=args.sample_rate,
        bitrate=args.bitrate,
        channel=args.channel,
    )

    file_id = minimax_wait_tts_done(
        api_key=api_key,
        task_id=task_id,
        poll_interval_s=args.poll_interval_s,
        max_wait_s=args.max_wait_s,
        dump_query_json=args.dump_query_json,
    )

    audio_bytes = minimax_download_file_content(api_key, file_id)

    run_ts = time.strftime("%Y%m%d_%H%M%S")
    base_name = input_path.stem

    out_audio = out_dir / f"{base_name}_{run_ts}.{args.format}"
    out_srt = out_dir / f"{base_name}_{run_ts}.srt"

    out_audio.write_bytes(audio_bytes)

    # 4) 估算 SRT（读取音频总时长）
    audio = AudioSegment.from_file(out_audio)
    total_ms = int(len(audio))

    subs = _split_subtitles(raw_text, max_len=args.subtitle_max_len)
    _write_srt_estimated(out_srt, subtitle_lines=subs, total_audio_ms=total_ms)

    print(f"OK: {out_audio}")
    print(f"OK: {out_srt}")
    print(f"voice_id: {voice_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
