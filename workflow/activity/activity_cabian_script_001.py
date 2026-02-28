"""\
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 单个文稿文件（md/txt）
Output: 在输入同目录下创建 <stem>_script_<run_id>/ 并输出口播稿、图提示词、图片、音频、字幕等
Pos: activity - 单文稿端到端编排（以文件管理为核心）

约定：
- 结果目录：<stem>_script_<run_id>/
- run_id: YYYYMMDD_HHMMSS_mmm
- 参考图固定：DEFAULT_REF_IMAGE
- 只保留“规范命名”的 wav/srt；不保留内部时间戳原始命名

cabian 版本说明：
- 口播提示词/生图提示词默认留空：你后续手动填写/或运行时传参
- TTS model 保持不变；默认配置 cloned_voice_id（voice id）
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar


# 允许从任意工作目录运行：把项目根目录加入 sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.logging_config import get_logger, setup_logging
from config import config as cfg
from data import test_prompt_script

from workflow.taskgroup.spoken_script_cabian_001 import spoken_script_cabian_001
from workflow.taskgroup.taskgroup_image_prompts_sync_001 import (
    image_prompts_sync_001,
    write_image_prompts_json,
)


DEFAULT_REF_IMAGE = (
    "/Users/test/Library/Mobile Documents/com~apple~CloudDocs/BEAST_BEING/"
    "my_mutimedia/my_scripts/JPM口播视频/葡萄架/三/gemini_3_pro_image_preview_1769081815_0.png"
)

# voice id（不是 model）
DEFAULT_CLONED_VOICE_ID = "cosyvoice-v3-flash-gualiu002-c0d8bae2fe1342e0a2df480501e75921"

NANOBANANA_SCRIPT = str(PROJECT_ROOT / "debug" / "nanobanana" / "run_gemini_flash_generate.py")
TTS_SCRIPT = str(PROJECT_ROOT / "debug" / "story_audio" / "run_md_to_story_audio_with_clone.py")
CLEAN_SRT_SCRIPT = str(PROJECT_ROOT / "tools" / "clean_srt_profanity_same_len.py")


@dataclass
class Paths:
    root: Path
    input_dir: Path
    spoken_dir: Path
    prompts_dir: Path
    images_dir: Path
    audio_dir: Path
    subtitles_dir: Path


def _now_run_id() -> str:
    t = time.time()
    base = time.strftime("%Y%m%d_%H%M%S", time.localtime(t))
    ms = int((t - int(t)) * 1000)
    return f"{base}_{ms:03d}"


def _safe_stem(p: Path) -> str:
    s = p.stem
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"[^0-9A-Za-z_\-\u4e00-\u9fff]", "_", s)
    return s or "input"


def _path_hash8(p: Path) -> str:
    h = hashlib.sha1(str(p).encode("utf-8")).hexdigest()
    return h[:8]


def _mkdirs(base: Path) -> Paths:
    input_dir = base / "00_input"
    spoken_dir = base / "01_spoken"
    prompts_dir = base / "02_image_prompts"
    images_dir = base / "03_images"
    audio_dir = base / "04_audio"
    subtitles_dir = base / "05_subtitles"

    for d in (input_dir, spoken_dir, prompts_dir, images_dir, audio_dir, subtitles_dir):
        d.mkdir(parents=True, exist_ok=True)

    return Paths(
        root=base,
        input_dir=input_dir,
        spoken_dir=spoken_dir,
        prompts_dir=prompts_dir,
        images_dir=images_dir,
        audio_dir=audio_dir,
        subtitles_dir=subtitles_dir,
    )


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


T = TypeVar("T")


def _run(cmd: list[str], *, cwd: Optional[Path] = None) -> str:
    p = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        text=True,
        capture_output=True,
    )
    if p.returncode != 0:
        raise RuntimeError(
            "Command failed:\n"
            f"cmd={' '.join(cmd)}\n"
            f"returncode={p.returncode}\n"
            f"stdout=\n{p.stdout}\n"
            f"stderr=\n{p.stderr}\n"
        )
    return p.stdout


def _call_with_retry(
    fn: Callable[[], T],
    *,
    what: str,
    logger,
    max_retries: int = 2,
    base_sleep_s: float = 2.0,
) -> T:
    last: Optional[BaseException] = None
    for attempt in range(max_retries + 1):
        try:
            if attempt > 0:
                logger.info(f"retry {attempt}/{max_retries}: {what}")
            return fn()
        except Exception as e:
            last = e
            if attempt >= max_retries:
                break
            time.sleep(base_sleep_s * (2**attempt))
    assert last is not None
    raise last


def _parse_nanobanana_saved_paths(stdout: str) -> list[Path]:
    lines = stdout.splitlines()
    saved: list[str] = []
    in_block = False
    for ln in lines:
        if ln.strip() == "saved_paths:":
            in_block = True
            continue
        if in_block:
            v = ln.strip()
            if not v:
                continue
            if v.endswith(":") and v in {
                "prompt:",
                "images:",
                "input_image_oss_urls:",
                "oss_uploads:",
                "saved_paths:",
                "stderr:",
                "stdout:",
            }:
                break
            saved.append(v)

    return [Path(s).expanduser() for s in saved]


def _move_images(saved_paths: list[Path], images_dir: Path, *, start_index: int = 0) -> tuple[list[str], int]:
    images_dir.mkdir(parents=True, exist_ok=True)

    moved: list[str] = []
    idx = start_index
    for p in saved_paths:
        src = p
        if not src.is_absolute():
            src = (Path.cwd() / src).resolve()
        if not src.exists():
            continue

        idx += 1
        ext = src.suffix.lower() or ".png"
        dst = images_dir / f"img_{idx:03d}{ext}"
        if dst.exists():
            dst = images_dir / f"img_{idx:03d}_{int(time.time())}{ext}"
        shutil.move(str(src), str(dst))
        moved.append(str(dst))

    if not moved:
        raise RuntimeError("未发现 nanobanana 输出图片（saved_paths 为空或文件不存在）")

    return moved, idx


def _pick_latest(dir_path: Path, pattern: str) -> Path:
    items = list(dir_path.glob(pattern))
    if not items:
        raise RuntimeError(f"未找到输出文件: dir={dir_path} pattern={pattern}")
    items.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return items[0]


def _normalize_tts_outputs(*, raw_out_dir: Path, out_wav: Path, out_srt: Path) -> tuple[str, str]:
    raw_wav = _pick_latest(raw_out_dir, "*.wav")
    raw_srt = _pick_latest(raw_out_dir, "*.srt")

    out_wav.parent.mkdir(parents=True, exist_ok=True)
    out_srt.parent.mkdir(parents=True, exist_ok=True)

    if out_wav.exists():
        out_wav.unlink()
    if out_srt.exists():
        out_srt.unlink()

    shutil.move(str(raw_wav), str(out_wav))
    shutil.move(str(raw_srt), str(out_srt))

    for p in raw_out_dir.glob("*.wav"):
        try:
            p.unlink()
        except Exception:
            pass
    for p in raw_out_dir.glob("*.srt"):
        try:
            p.unlink()
        except Exception:
            pass

    return str(out_wav), str(out_srt)


def _rename_clean_srt(subtitles_dir: Path, run_id: str, stem: str) -> Path:
    clean_candidates = list(subtitles_dir.glob("*_clean_*.srt"))
    if not clean_candidates:
        raise RuntimeError("未找到 clean srt 输出（工具未生成？）")

    clean_candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    src = clean_candidates[0]

    dst = subtitles_dir / f"{stem}_{run_id}_clean.srt"
    if dst.exists():
        dst.unlink()

    shutil.move(str(src), str(dst))
    return dst


def main() -> int:
    setup_logging()
    logging.getLogger().setLevel(logging.INFO)
    logger = get_logger(__name__)

    ap = argparse.ArgumentParser(description="activity: cabian 单文稿端到端脚本（结果目录统一管理）")
    ap.add_argument("--input", required=True, help="输入文稿路径（md/txt）")
    ap.add_argument(
        "--output_root",
        default=str(cfg.SCRIPT_RESULTS_DIR),
        help="统一输出根目录（默认 data/Data_results/script_results）",
    )

    # 生图
    ap.add_argument("--aspect_ratio", default="9:16")
    ap.add_argument("--ref_image", default=DEFAULT_REF_IMAGE)

    ap.add_argument("--num_images", type=int, default=5)

    # cabian 生图提示词：默认使用 test_prompt_script（仍可 CLI 覆盖）
    ap.add_argument(
        "--img_prompt_system",
        default=getattr(test_prompt_script, "CABIAN_IMAGE_PROMPT_SYNC_PROMPT_001", ""),
        help="生图提示词生成的 system prompt（cabian）",
    )
    ap.add_argument(
        "--img_prompt_user_template",
        default=(
            "请根据下面口播稿，生成 {num_images} 条分镜生图任务。\n"
            "要求：只输出 JSON 数组（不要 markdown 代码块，不要解释）。\n\n"
            "口播稿：\n{text}\n"
        ),
        help="user prompt 模板（支持 {text} 和 {num_images}）",
    )

    # cabian 口播提示词：默认使用 test_prompt_script（仍可 CLI 覆盖）
    ap.add_argument(
        "--spoken_system_1",
        default=getattr(test_prompt_script, "CABIAN_SYS_PROMPT_001_01", ""),
        help="口播生成 system prompt #1（cabian）",
    )
    ap.add_argument(
        "--spoken_user_1_template",
        default="{raw_text}",
        help="口播生成 user prompt 模板 #1（支持 {raw_text}）",
    )
    ap.add_argument("--spoken_system_3", default="", help="TTS 清洗 system prompt #3（cabian，可空）")
    ap.add_argument(
        "--spoken_user_3_template",
        default="",
        help="TTS 清洗 user prompt 模板 #3（支持 {final_script}；可空）",
    )

    # TTS 参数（model 不变；默认配置 voice id）
    ap.add_argument("--tts_model", default="cosyvoice-v3-flash")
    ap.add_argument("--use_cloned_voice", action="store_true")
    ap.add_argument("--cloned_voice_id", default=DEFAULT_CLONED_VOICE_ID)
    ap.add_argument("--speech_rate", type=float, default=1.0)
    ap.add_argument("--pitch_rate", type=float, default=1.0)
    ap.add_argument("--no_break", action="store_true")
    ap.add_argument("--instruction", default="我想体验一下自然的语气。")

    args = ap.parse_args()

    input_path = Path(args.input).expanduser().resolve()
    if not input_path.exists():
        raise FileNotFoundError(str(input_path))

    raw_text = _read_text(input_path)
    if not raw_text:
        raise ValueError("输入文件为空")

    run_id = _now_run_id()
    stem = _safe_stem(input_path)
    ph = _path_hash8(input_path)

    output_root = Path(args.output_root).expanduser().resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    out_root = output_root / f"{stem}__{ph}_script_{run_id}"
    paths = _mkdirs(out_root)

    shutil.copy2(str(input_path), str(paths.input_dir / input_path.name))

    manifest: dict[str, Any] = {
        "input": str(input_path),
        "output_root": str(output_root),
        "stem": stem,
        "run_id": run_id,
        "out_root": str(out_root),
        "steps": {},
    }

    logger.info(f"input={input_path}")
    logger.info(f"output_root={output_root}")
    logger.info(f"out_root={out_root}")

    try:
        # =========================
        # Step 1: spoken script (cabian)
        # =========================
        t0 = time.time()
        spoken = _call_with_retry(
            lambda: spoken_script_cabian_001(
                raw_text,
                system_prompt_1=str(args.spoken_system_1),
                user_prompt_1_template=str(args.spoken_user_1_template),
                system_prompt_3=str(args.spoken_system_3),
                user_prompt_3_template=str(args.spoken_user_3_template) or "{final_script}",
            ),
            what="spoken_script_cabian_001",
            logger=logger,
        )
        spoken_path = paths.spoken_dir / f"{stem}_spoken_{run_id}.txt"
        spoken_path.write_text(spoken, encoding="utf-8")
        logger.info(f"spoken -> {spoken_path}")
        manifest["steps"]["spoken"] = {
            "ok": True,
            "output": str(spoken_path),
            "elapsed_s": round(time.time() - t0, 3),
        }

        # =========================
        # Step 2: image prompts JSON
        # =========================
        t0 = time.time()
        res = _call_with_retry(
            lambda: image_prompts_sync_001(
                spoken,
                system_prompt=str(args.img_prompt_system),
                user_prompt_template=str(args.img_prompt_user_template),
                num_images=int(args.num_images),
            ),
            what="image_prompts_sync_001",
            logger=logger,
        )

        prompts_path = paths.prompts_dir / f"{stem}_image_prompts_{run_id}.json"
        write_image_prompts_json(
            prompts_path,
            prompts=res.prompts,
            meta={
                "source": str(spoken_path),
                "num_images": int(args.num_images),
            },
        )
        logger.info(f"image_prompts -> {prompts_path}  count={len(res.prompts)}")
        manifest["steps"]["image_prompts"] = {
            "ok": True,
            "output": str(prompts_path),
            "count": len(res.prompts),
            "elapsed_s": round(time.time() - t0, 3),
        }

        # =========================
        # Step 3: nanobanana generate images (per prompt)
        # =========================
        t0 = time.time()
        ref_image = Path(args.ref_image).expanduser().resolve()
        if not ref_image.exists():
            raise FileNotFoundError(f"参考图不存在: {ref_image}")

        img_index = 0
        moved_all: list[str] = []
        image_items: list[dict[str, Any]] = []

        for i, prompt_str in enumerate(res.prompts, start=1):
            logger.info(f"image[{i}/{len(res.prompts)}] generating...")

            item: dict[str, Any] = {"i": i, "ok": False}
            try:
                stdout = _run(
                    [
                        sys.executable,
                        NANOBANANA_SCRIPT,
                        "--aspect-ratio",
                        str(args.aspect_ratio),
                        "--image",
                        str(ref_image),
                        prompt_str,
                    ],
                    cwd=paths.root,
                )

                saved_paths = _parse_nanobanana_saved_paths(stdout)
                moved, img_index = _move_images(saved_paths, paths.images_dir, start_index=img_index)
                moved_all.extend(moved)

                item.update({
                    "ok": True,
                    "moved": moved,
                })
                logger.info(f"image[{i}] moved={len(moved)} total={len(moved_all)}")

            except Exception as e:
                logger.warning(f"image[{i}] failed: {type(e).__name__}: {e}")
                item["error"] = {"type": type(e).__name__, "message": str(e)}

            image_items.append(item)

        (paths.images_dir / "images_manifest.json").write_text(
            json.dumps(
                {
                    "prompts_json": str(prompts_path),
                    "moved_images": moved_all,
                    "items": image_items,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        manifest["steps"]["images"] = {
            "ok": len(moved_all) > 0,
            "count": len(moved_all),
            "dir": str(paths.images_dir),
            "items": image_items,
            "elapsed_s": round(time.time() - t0, 3),
        }

        # =========================
        # Step 4: TTS (audio + srt)
        # =========================
        t0 = time.time()
        raw_tts_dir = paths.audio_dir / "_raw"
        raw_tts_dir.mkdir(parents=True, exist_ok=True)

        # 如果给了 voice id，则自动开启 use_cloned_voice（保持最简单）
        use_cloned_voice = bool(args.use_cloned_voice or args.cloned_voice_id)

        tts_cmd = [
            sys.executable,
            TTS_SCRIPT,
            "--input",
            str(spoken_path),
            "--model",
            str(args.tts_model),
            "--speech_rate",
            str(args.speech_rate),
            "--pitch_rate",
            str(args.pitch_rate),
            "--out_dir",
            str(raw_tts_dir),
        ]

        if args.no_break:
            tts_cmd.append("--no_break")

        if args.instruction:
            tts_cmd.extend(["--instruction", str(args.instruction)])

        if use_cloned_voice:
            tts_cmd.append("--use_cloned_voice")
            if args.cloned_voice_id:
                tts_cmd.extend(["--cloned_voice_id", str(args.cloned_voice_id)])

        _call_with_retry(
            lambda: _run(tts_cmd, cwd=PROJECT_ROOT),
            what="tts_generation",
            logger=logger,
        )

        out_wav = paths.audio_dir / f"{stem}_{run_id}.wav"
        out_srt = paths.subtitles_dir / f"{stem}_{run_id}.srt"

        wav_path, srt_path = _normalize_tts_outputs(
            raw_out_dir=raw_tts_dir,
            out_wav=out_wav,
            out_srt=out_srt,
        )

        try:
            shutil.rmtree(raw_tts_dir)
        except Exception:
            pass

        logger.info(f"tts wav -> {wav_path}")
        logger.info(f"tts srt -> {srt_path}")

        manifest["steps"]["tts"] = {
            "ok": True,
            "wav": wav_path,
            "srt": srt_path,
            "elapsed_s": round(time.time() - t0, 3),
        }

        # =========================
        # Step 5: clean srt
        # =========================
        t0 = time.time()
        _call_with_retry(
            lambda: _run(
                [
                    sys.executable,
                    CLEAN_SRT_SCRIPT,
                    "--root",
                    str(paths.subtitles_dir),
                    "--apply",
                ],
                cwd=PROJECT_ROOT,
            ),
            what="clean_srt",
            logger=logger,
        )

        clean_srt = _rename_clean_srt(paths.subtitles_dir, run_id, stem)
        logger.info(f"clean_srt -> {clean_srt}")

        manifest["steps"]["clean_srt"] = {
            "ok": True,
            "clean_srt": str(clean_srt),
            "elapsed_s": round(time.time() - t0, 3),
        }

        (paths.root / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        logger.info(f"OK: out_root={paths.root}")
        return 0

    except Exception as e:
        logger.exception(e)
        manifest["error"] = {"type": type(e).__name__, "message": str(e)}
        try:
            (paths.root / "manifest.json").write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass
        raise


if __name__ == "__main__":
    raise SystemExit(main())
'''
/Users/test/code/Python/AI_vedio_demo/pythonProject/.venv/bin/python3 /Users/test/code/Python/AI_vedio_demo/pythonProject/workflow/activity/activity_cabian_script_001.py --input "/Users/test/Library/Mobile Documents/com~apple~CloudDocs/BEAST_BEING/my_mutimedia/my_scripts/rpt口播视频/05_merged_segments_fixed_20260212_143836/0001_第十六回_seg001_三女共事一.md"
'''


'''
/Users/test/code/Python/AI_vedio_demo/pythonProject/.venv/bin/python3 \
  /Users/test/code/Python/AI_vedio_demo/pythonProject/workflow/activity/activity_cabian_script_001.py \
  --input "/path/to/xxx.md" \
  --output_root "/Users/test/code/Python/AI_vedio_demo/pythonProject/data/Data_results/script_results" \
  --ref_image "/Users/test/Library/Mobile Documents/com~apple~CloudDocs/BEAST_BEING/my_mutimedia/my_scripts/JPM口播视频/葡萄架/三/gemini_3_pro_image_preview_1769081815_0.png" \
  --cloned_voice_id "cosyvoice-v3-flash-gualiu002-c0d8bae2fe1342e0a2df480501e75921" \
  --spoken_system_1 "(TODO)" \
  --spoken_user_1_template "(TODO) {raw_text}" \
  --img_prompt_system "(TODO)" \
  --use_cloned_voice
'''
