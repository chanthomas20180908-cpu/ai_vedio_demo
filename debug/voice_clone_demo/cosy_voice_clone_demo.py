"""CosyVoice 声音复刻（声音克隆）最小 Demo

目标：本地参考音频 -> 上传到 OSS（去重）-> 创建音色 -> 轮询状态 -> 用音色合成文本 -> 保存 mp3。

约束：
- 只使用 python3 执行
- API Key 读取：优先加载项目 env/default.env 中的 DASHSCOPE_API_KEY
- 参考音频通过 util.util_url.upload_file_to_oss_dedup_with_meta 上传为公网可访问 URL

用法：
python3 debug/voice_clone_demo/cosy_voice_clone_demo.py

可选参数：
python3 debug/voice_clone_demo/cosy_voice_clone_demo.py \
  --mp3 "/path/to/ref.mp3" \
  --text "要合成的文本" \
  --prefix yueniao \
  --model cosyvoice-v3-plus
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import dashscope
from dotenv import load_dotenv

from dashscope.audio.tts_v2 import SpeechSynthesizer, VoiceEnrollmentService

# 允许从任意工作目录运行：把项目根目录加到 sys.path，确保能 import config/util
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from config.logging_config import get_logger
from util.util_url import upload_file_to_oss_dedup_with_meta

logger = get_logger(__name__)


DEFAULT_REF_MP3 = (
    "/Users/test/Library/Mobile Documents/com~apple~CloudDocs/BEAST_BEING/"
    "my_mutimedia/my_scripts/JPM口播视频/月娘上香20260129/月娘上香/月娘上香.MP3"
)

DEFAULT_TEXT = (
    "你想象一间屋子：灯芯发黄，火苗一抖一抖的，像有人在暗处眨眼。"
    "空气闷得发黏，连呼吸都像被一层旧布捂住。"
    "窗纸吸了潮气，贴在指尖上是凉的，可屋里的人心是热的、急的、带刺的。"
    "今天这个故事，你别当成风月，它更像一把钝刀，慢慢割人——"
    "割到你最后才反应过来：原来从一开始，就没有“正常”。"
)


def _now_compact() -> str:
    return time.strftime("%Y%m%d_%H%M%S", time.localtime())


def _voice_registry_path() -> Path:
    return _project_root() / "debug" / "voice_clone_demo" / "cosy_voices_clone.json"


def _load_voice_registry(path: Path) -> dict:
    if not path.exists():
        return {"by_id": {}, "by_name": {}}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"by_id": {}, "by_name": {}}

    if not isinstance(data, dict):
        return {"by_id": {}, "by_name": {}}

    data.setdefault("by_id", {})
    data.setdefault("by_name", {})

    if not isinstance(data.get("by_id"), dict):
        data["by_id"] = {}
    if not isinstance(data.get("by_name"), dict):
        data["by_name"] = {}

    return data


def _save_voice_registry(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def _register_voice(
    *,
    voice_id: str,
    voice_name: str,
    target_model: str,
    ref_mp3_path: str,
    oss_meta: dict,
) -> None:
    reg_path = _voice_registry_path()
    reg = _load_voice_registry(reg_path)

    # voice_id 作为唯一标识
    reg["by_id"][voice_id] = {
        "voice_id": voice_id,
        "voice_name": voice_name,
        "target_model": target_model,
        "ref_mp3_path": ref_mp3_path,
        "oss_meta": oss_meta,
        "created_at": _now_compact(),
    }
    reg["by_name"][voice_name] = voice_id

    _save_voice_registry(reg_path, reg)


def _resolve_voice_id_from_name(voice_name: str) -> tuple[str | None, dict | None]:
    reg_path = _voice_registry_path()
    reg = _load_voice_registry(reg_path)

    voice_id = reg.get("by_name", {}).get(voice_name)
    if not voice_id:
        return None, None

    info = reg.get("by_id", {}).get(voice_id)
    return voice_id, info


def _project_root() -> Path:
    # .../pythonProject/debug/voice_clone_demo/cosy_voice_clone_demo.py -> parents[2] == .../pythonProject
    return Path(__file__).resolve().parents[2]


def _load_dashscope_api_key() -> str:
    root = _project_root()
    env_path = root / "env" / "default.env"

    # 按你项目习惯：加载 env/default.env
    try:
        load_dotenv(dotenv_path=str(env_path))
    except Exception as e:
        logger.warning("load_dotenv 失败（将继续尝试直接读取环境变量）: %s", e)

    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError(
            "未找到 DASHSCOPE_API_KEY。请在 env/default.env 配置或 export 环境变量。"
        )
    return api_key


def run_demo(
    ref_mp3_path: str,
    text: str,
    voice_prefix: str,
    target_model: str,
    oss_expire_seconds: int,
    out_dir: str,
    poll_interval_seconds: int,
    max_attempts: int,
    voice_id: str | None,
    voice_name: str | None,
) -> tuple[str, dict]:
    # 1) API Key
    dashscope.api_key = _load_dashscope_api_key()

    meta: dict = {
        "mode": None,
        "target_model": target_model,
        "voice_id": None,
        "voice_name": None,
        "voice_registry": str(_voice_registry_path()),
    }

    # 2) 确定要用的 voice_id
    if voice_id:
        # 直接用传入 ID
        meta["mode"] = "use_voice_id"
        meta["voice_id"] = voice_id
        meta["voice_name"] = voice_name
        logger.info("Mode: 直接使用 voice_id=%s", voice_id)
    elif voice_name:
        # 优先从本地注册表解析；若不存在则把它当成“要创建的新音色名字”
        vid, info = _resolve_voice_id_from_name(voice_name)
        if vid:
            # 模型一致性检查（避免后续合成失败）
            if info and info.get("target_model") and info.get("target_model") != target_model:
                raise ValueError(
                    f"voice_name={voice_name} 记录的 target_model={info.get('target_model')} 与本次 --model={target_model} 不一致。"
                )

            meta["mode"] = "use_voice_name"
            meta["voice_id"] = vid
            meta["voice_name"] = voice_name
            logger.info("Mode: 使用 voice_name=%s -> voice_id=%s", voice_name, vid)
            voice_id = vid
        else:
            meta["mode"] = "create_new"
            logger.info("Mode: voice_name 不存在，将创建新音色并保存 name=%s", voice_name)
    else:
        # 走创建流程
        meta["mode"] = "create_new"

        ref_mp3 = Path(ref_mp3_path)
        if not ref_mp3.exists():
            raise FileNotFoundError(f"参考音频不存在: {ref_mp3}")

        # 2.1) 上传参考音频到 OSS（去重）
        logger.info("Step 0: 上传参考音频到 OSS (dedup) - %s", ref_mp3)
        audio_url, up_meta = upload_file_to_oss_dedup_with_meta(str(ref_mp3), oss_expire_seconds)
        logger.info("参考音频 OSS URL: %s", audio_url)
        logger.info("OSS meta: %s", up_meta)

        # 2.2) 创建音色
        logger.info(
            "Step 1: 创建音色 (voice enrollment) - model=%s, prefix=%s",
            target_model,
            voice_prefix,
        )
        service = VoiceEnrollmentService()
        created_voice_id = service.create_voice(
            target_model=target_model,
            prefix=voice_prefix,
            url=audio_url,
            language_hints=["zh"],
        )
        logger.info("创建音色请求已提交. request_id=%s", service.get_last_request_id())
        logger.info("voice_id=%s", created_voice_id)

        # 2.3) 轮询状态
        logger.info("Step 2: 轮询音色状态")
        last_status = None
        for attempt in range(max_attempts):
            info = service.query_voice(voice_id=created_voice_id)
            status = info.get("status")
            last_status = status
            logger.info("poll %d/%d: status=%s", attempt + 1, max_attempts, status)

            if status == "OK":
                break
            if status == "UNDEPLOYED":
                raise RuntimeError(f"音色审核不通过/不可用: status={status}, info={info}")

            time.sleep(poll_interval_seconds)
        else:
            raise RuntimeError(
                f"轮询超时：音色在 {max_attempts * poll_interval_seconds}s 内未就绪，last_status={last_status}"
            )

        # 2.4) 写入本地注册表
        final_voice_name = voice_name or f"{voice_prefix}_{_now_compact()}"
        _register_voice(
            voice_id=created_voice_id,
            voice_name=final_voice_name,
            target_model=target_model,
            ref_mp3_path=str(ref_mp3),
            oss_meta=up_meta,
        )
        logger.info("已写入本地音色注册表: %s", _voice_registry_path())
        logger.info("voice_name=%s -> voice_id=%s", final_voice_name, created_voice_id)

        meta["voice_id"] = created_voice_id
        meta["voice_name"] = final_voice_name
        voice_id = created_voice_id

    # 5) 合成
    logger.info("Step 3: 使用复刻音色合成")
    synthesizer = SpeechSynthesizer(model=target_model, voice=voice_id)
    audio_data = synthesizer.call(text)
    meta["synthesis_request_id"] = synthesizer.get_last_request_id()
    logger.info("合成成功. request_id=%s", meta["synthesis_request_id"])

    # 6) 保存
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    out_file = out_path / "my_custom_voice_output.mp3"
    out_file.write_bytes(audio_data)
    logger.info("已保存: %s", out_file)

    meta["output_file"] = str(out_file)
    return str(out_file), meta


def _read_text_file(path: str) -> str:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"文本文件不存在: {p}")
    txt = p.read_text(encoding="utf-8")
    txt = txt.strip()
    if not txt:
        raise ValueError(f"文本文件内容为空: {p}")
    return txt


def main() -> None:
    parser = argparse.ArgumentParser(description="CosyVoice 声音复刻 + 合成最小 Demo")
    parser.add_argument("--mp3", default=DEFAULT_REF_MP3, help="参考音频路径（本地 mp3）")
    parser.add_argument("--text", default=DEFAULT_TEXT, help="要合成的文本")
    parser.add_argument("--md", default=None, help="从 markdown/txt 文件读取要合成的文本（优先级高于 --text）")
    parser.add_argument("--prefix", default="yueniao", help="音色前缀（英数下划线，尽量短）")
    parser.add_argument("--model", default="cosyvoice-v3-plus", help="驱动音色的语音合成模型")

    # 复用模式（二选一 / 可都不传）
    parser.add_argument("--voice-id", default=None, help="直接指定要使用的 voice_id（最高优先级）")
    parser.add_argument(
        "--voice-name",
        default=None,
        help=(
            "使用本地注册表中的 voice_name（来自 cosy_voices_clone.json）。"
            "如未传 voice-id 且 voice-name 不存在，将报错。"
        ),
    )
    parser.add_argument("--oss-expire", type=int, default=3600, help="OSS signed URL 有效期（秒）")
    parser.add_argument(
        "--out-dir",
        default=str(_project_root() / "debug" / "voice_clone_demo" / "output"),
        help="输出目录",
    )
    parser.add_argument("--poll-interval", type=int, default=10, help="轮询间隔（秒）")
    parser.add_argument("--max-attempts", type=int, default=30, help="最大轮询次数")
    args = parser.parse_args()

    text = _read_text_file(args.md) if args.md else args.text

    out_file, meta = run_demo(
        ref_mp3_path=args.mp3,
        text=text,
        voice_prefix=args.prefix,
        target_model=args.model,
        oss_expire_seconds=args.oss_expire,
        out_dir=args.out_dir,
        poll_interval_seconds=args.poll_interval,
        max_attempts=args.max_attempts,
        voice_id=args.voice_id,
        voice_name=args.voice_name,
    )

    # 兼容你后续接入：输出尽量包含关键字段
    print(out_file)
    if meta.get("voice_id"):
        print(f"voice_id={meta['voice_id']}")
    if meta.get("voice_name"):
        print(f"voice_name={meta['voice_name']}")
    if meta.get("voice_registry"):
        print(f"voice_registry={meta['voice_registry']}")


if __name__ == "__main__":
    main()
