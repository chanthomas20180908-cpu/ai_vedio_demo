"""\
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 单个文稿文件（md/txt）
Output: 在统一输出根目录下创建 <stem>__<hash>_script_<run_id>/ 并输出口播稿、storyboard、图片、音频、字幕、视频
Pos: story_video_001 - activity - 单文稿端到端编排（以文件管理为核心）

链路（7 步）：
1) Step 1：口播稿（文本）
2) Step 2：TTS → 生成 wav + srt
3) Step 3：clean_srt（清理文本用）
4) Step 4：用 srt 生成 storyboard
5) Step 5：根据 storyboard 的 scenes 生成每幕的图片 prompt
6) Step 6：按 scene 生图
7) Step 7：按 storyboard 合成视频

约束（按当前结论）：
- CLI 只定义通用参数；差异默认值来自 profile（由 case 传入）
- spoken 仅暴露 system_prompt_1/user_prompt_1_template；system3 写死在 task 内
- 不提供图片缓存逻辑
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar

# 允许从任意工作目录运行：把项目根目录加入 sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import config as cfg
from config.logging_config import get_logger, setup_logging

from workflow.story_video_001.tasks.task_spoken_001 import task_spoken_001
from workflow.story_video_001.tasks.task_image_prompts_sync_002 import image_prompts_sync_002
from workflow.story_video_001.tasks.task_storyboard_from_srt_001 import (
    build_storyboard_from_srt_001,
    storyboard_to_dict,
    write_storyboard_json,
)
from workflow.story_video_001.tasks.task_compose_video_from_storyboard_002 import (
    ComposeVideoParams,
    compose_video_from_storyboard_002,
)

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
    video_dir: Path


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
    video_dir = base / "06_video"

    for d in (input_dir, spoken_dir, prompts_dir, images_dir, audio_dir, subtitles_dir, video_dir):
        d.mkdir(parents=True, exist_ok=True)

    return Paths(
        root=base,
        input_dir=input_dir,
        spoken_dir=spoken_dir,
        prompts_dir=prompts_dir,
        images_dir=images_dir,
        audio_dir=audio_dir,
        subtitles_dir=subtitles_dir,
        video_dir=video_dir,
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


def _move_one_image(saved_paths: list[Path], dst_path: Path) -> str:
    dst_path.parent.mkdir(parents=True, exist_ok=True)

    picked: Optional[Path] = None
    for p in saved_paths:
        src = p
        if not src.is_absolute():
            src = (Path.cwd() / src).resolve()
        if src.exists():
            picked = src
            break

    if picked is None:
        raise RuntimeError("未发现 nanobanana 输出图片（saved_paths 为空或文件不存在）")

    if dst_path.exists():
        dst_path.unlink()
    shutil.move(str(picked), str(dst_path))
    return str(dst_path)


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

    # 清理残留
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


def _resolve_profile_value(profile: dict[str, Any], key: str, cli_value: Any) -> Any:
    """CLI 允许覆盖；若 CLI 没传（空字符串），使用 profile 默认值。"""
    if isinstance(cli_value, str):
        if cli_value.strip() != "":
            return cli_value
    if cli_value is not None:
        # 对于数值型/布尔型，argparse 总会给值，这里直接用 cli_value 覆盖
        return cli_value
    return profile[key]


def _validate_profile(profile: dict[str, Any]) -> None:
    required = [
        "name",
        "style",
        "spoken_system_1",
        "spoken_user_1_template",
        "img_prompt_system",
        "img_prompt_user_template",
        "img_prompt_base",
        "img_prompt_batch_size",
        "aspect_ratio",
        "ref_image",
        "tts_model",
        "use_cloned_voice",
        "cloned_voice_id",
        "speech_rate",
        "pitch_rate",
        "no_break",
        "instruction",
        "video_width",
        "video_height",
        "video_fps",
        "ffmpeg_bin",
    ]
    for k in required:
        if k not in profile:
            raise RuntimeError(f"profile 缺少字段: {k}")
        if profile[k] is None:
            raise RuntimeError(f"profile 字段不允许为 None: {k}")


def build_arg_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="story_video_001: activity_script_001")
    ap.add_argument("--input", required=True, help="输入文稿路径（md/txt）")
    ap.add_argument(
        "--output_root",
        default=str(cfg.SCRIPT_RESULTS_DIR),
        help="统一输出根目录（默认 data/Data_results/script_results）",
    )

    # 快速测试/复用
    ap.add_argument("--max_scenes", type=int, default=0, help="仅处理前 N 个 scene（0 不限制）")
    ap.add_argument("--skip_images", action="store_true")
    ap.add_argument("--skip_video", action="store_true")
    ap.add_argument("--only_video", default="", help="仅合成视频：传入历史 out_root 目录")

    # 覆盖 profile 默认值（不覆盖则用 profile）
    ap.add_argument("--aspect_ratio", default="")
    ap.add_argument("--ref_image", default="")
    ap.add_argument("--spoken_system_1", default="")
    ap.add_argument("--spoken_user_1_template", default="")
    ap.add_argument("--img_prompt_system", default="")

    # tts
    ap.add_argument("--tts_model", default="")
    ap.add_argument("--use_cloned_voice", action="store_true")
    ap.add_argument("--cloned_voice_id", default="")
    ap.add_argument("--speech_rate", type=float, default=0.0)
    ap.add_argument("--pitch_rate", type=float, default=0.0)
    ap.add_argument("--no_break", action="store_true")
    ap.add_argument("--instruction", default="")

    # 视频
    ap.add_argument("--video_width", type=int, default=0)
    ap.add_argument("--video_height", type=int, default=0)
    ap.add_argument("--video_fps", type=int, default=0)
    ap.add_argument("--zoom_end", type=float, default=None)
    ap.add_argument("--ffmpeg_bin", default="")

    return ap


def main(*, profile: dict[str, Any]) -> int:
    setup_logging()
    logger = get_logger(__name__)

    _validate_profile(profile)

    ap = build_arg_parser()
    args = ap.parse_args()

    # only_video
    if args.only_video:
        out_root = Path(args.only_video).expanduser().resolve()
        if not out_root.exists():
            raise FileNotFoundError(str(out_root))

        video_dir = out_root / "06_video"
        tmp_dir = video_dir / "_tmp"
        prompts_dir = out_root / "02_image_prompts"
        audio_dir = out_root / "04_audio"

        storyboard_path = _pick_latest(prompts_dir, "*_storyboard_*.json")
        wav_path = _pick_latest(audio_dir, "*.wav")

        out_mp4 = video_dir / f"resume_{_now_run_id()}.mp4"

        width = int(args.video_width) if int(args.video_width) > 0 else int(profile["video_width"])
        height = int(args.video_height) if int(args.video_height) > 0 else int(profile["video_height"])
        fps = int(args.video_fps) if int(args.video_fps) > 0 else int(profile["video_fps"])
        ffmpeg_bin = args.ffmpeg_bin.strip() or str(profile["ffmpeg_bin"])

        _vp_kwargs = {"width": width, "height": height, "fps": fps, "zoom_start": 1.0}
        if args.zoom_end is not None:
            _vp_kwargs["zoom_end"] = float(args.zoom_end)
        video_params = ComposeVideoParams(**_vp_kwargs)

        logger.info(f"only_video: storyboard={storyboard_path}")
        logger.info(f"only_video: wav={wav_path}")

        compose_video_from_storyboard_002(
            storyboard_json=storyboard_path,
            audio_path=wav_path,
            out_mp4=out_mp4,
            tmp_dir=tmp_dir,
            params=video_params,
            ffmpeg_bin=str(ffmpeg_bin),
            xfade_transition="fade",
            logger=logger,
        )
        logger.info(f"FINAL MP4 READY: {out_mp4}")
        return 0

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
        "profile": str(profile.get("name")),
        "input": str(input_path),
        "output_root": str(output_root),
        "stem": stem,
        "run_id": run_id,
        "out_root": str(out_root),
        "steps": {},
    }

    try:
        (paths.root / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

    # resolve defaults (CLI can override)
    aspect_ratio = args.aspect_ratio.strip() or str(profile["aspect_ratio"])
    ref_image = args.ref_image.strip() or str(profile["ref_image"])

    spoken_system_1 = args.spoken_system_1.strip() or str(profile["spoken_system_1"])
    spoken_user_1_template = args.spoken_user_1_template.strip() or str(profile["spoken_user_1_template"])

    img_prompt_system = args.img_prompt_system.strip() or str(profile["img_prompt_system"])
    img_prompt_user_template = str(profile["img_prompt_user_template"])
    img_prompt_base = profile["img_prompt_base"]
    img_prompt_batch_size = int(profile["img_prompt_batch_size"])

    tts_model = args.tts_model.strip() or str(profile["tts_model"])
    use_cloned_voice = bool(args.use_cloned_voice) or bool(profile["use_cloned_voice"])
    cloned_voice_id = args.cloned_voice_id.strip() or str(profile["cloned_voice_id"])

    speech_rate = float(args.speech_rate) if float(args.speech_rate) > 0 else float(profile["speech_rate"])
    pitch_rate = float(args.pitch_rate) if float(args.pitch_rate) > 0 else float(profile["pitch_rate"])

    instruction = args.instruction if args.instruction.strip() else str(profile["instruction"])
    no_break = bool(args.no_break) or bool(profile["no_break"])

    video_width = int(args.video_width) if int(args.video_width) > 0 else int(profile["video_width"])
    video_height = int(args.video_height) if int(args.video_height) > 0 else int(profile["video_height"])
    video_fps = int(args.video_fps) if int(args.video_fps) > 0 else int(profile["video_fps"])
    ffmpeg_bin = args.ffmpeg_bin.strip() or str(profile["ffmpeg_bin"])

    logger.info(f"profile={profile.get('name')} input={input_path}")
    logger.info(f"out_root={out_root}")
    logger.info(
        "params="
        f"aspect_ratio={aspect_ratio} ref_image={ref_image} max_scenes={args.max_scenes} "
        f"skip_images={args.skip_images} skip_video={args.skip_video} "
        f"tts_model={tts_model} use_cloned_voice={use_cloned_voice} "
        f"video={video_width}x{video_height}@{video_fps}"
    )

    try:
        # =========================
        # Step 1: spoken
        # =========================
        logger.info("step[1/7] spoken: start")
        t0 = time.time()

        spoken = _call_with_retry(
            lambda: task_spoken_001(
                raw_text,
                system_prompt_1=spoken_system_1,
                user_prompt_1_template=spoken_user_1_template,
            ),
            what="task_spoken_001",
            logger=logger,
        )

        spoken_path = paths.spoken_dir / f"{stem}_spoken_{run_id}.txt"
        spoken_path.write_text(spoken, encoding="utf-8")
        manifest["steps"]["spoken"] = {"ok": True, "output": str(spoken_path), "elapsed_s": round(time.time() - t0, 3)}
        logger.info(f"step[1/7] spoken: done elapsed_s={manifest['steps']['spoken']['elapsed_s']} output={spoken_path}")

        # =========================
        # Step 2: TTS (audio + srt)
        # =========================
        logger.info("step[2/7] tts: start")
        t0 = time.time()
        raw_tts_dir = paths.audio_dir / "_raw"
        raw_tts_dir.mkdir(parents=True, exist_ok=True)

        tts_cmd = [
            sys.executable,
            TTS_SCRIPT,
            "--input",
            str(spoken_path),
            "--model",
            str(tts_model),
            "--speech_rate",
            str(speech_rate),
            "--pitch_rate",
            str(pitch_rate),
            "--out_dir",
            str(raw_tts_dir),
        ]

        effective_no_break = bool(no_break) or bool(instruction)
        if effective_no_break:
            tts_cmd.append("--no_break")
        if instruction:
            tts_cmd.extend(["--instruction", str(instruction)])

        if use_cloned_voice:
            tts_cmd.append("--use_cloned_voice")
            if cloned_voice_id:
                tts_cmd.extend(["--cloned_voice_id", str(cloned_voice_id)])

        _call_with_retry(lambda: _run(tts_cmd, cwd=PROJECT_ROOT), what="tts_generation", logger=logger)

        out_wav = paths.audio_dir / f"{stem}_{run_id}.wav"
        out_srt = paths.subtitles_dir / f"{stem}_{run_id}.srt"
        wav_path, srt_path = _normalize_tts_outputs(raw_out_dir=raw_tts_dir, out_wav=out_wav, out_srt=out_srt)
        try:
            shutil.rmtree(raw_tts_dir)
        except Exception:
            pass

        manifest["steps"]["tts"] = {"ok": True, "wav": wav_path, "srt": srt_path, "elapsed_s": round(time.time() - t0, 3)}
        logger.info(f"step[2/7] tts: done elapsed_s={manifest['steps']['tts']['elapsed_s']} wav={wav_path} srt={srt_path}")

        # =========================
        # Step 3: clean srt
        # =========================
        logger.info("step[3/7] clean_srt: start")
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

        try:
            clean_srt = _rename_clean_srt(paths.subtitles_dir, run_id, stem)
            clean_meta = {"fallback_to_original": False}
        except RuntimeError as e:
            if "未找到 clean srt 输出" not in str(e):
                raise
            clean_srt = Path(srt_path)
            clean_meta = {"fallback_to_original": True, "used": str(clean_srt)}
            logger.info(f"clean_srt: no output generated, fallback to original srt -> {clean_srt}")

        manifest["steps"]["clean_srt"] = {"ok": True, "clean_srt": str(clean_srt), "elapsed_s": round(time.time() - t0, 3), "meta": clean_meta}
        logger.info(f"step[3/7] clean_srt: done elapsed_s={manifest['steps']['clean_srt']['elapsed_s']} clean_srt={clean_srt}")

        # =========================
        # Step 4: storyboard from srt (use original timing srt)
        # =========================
        logger.info("step[4/7] storyboard: start")
        t0 = time.time()
        scenes = build_storyboard_from_srt_001(
            srt_path,
            target_sec=15.0,
            min_sec=10.0,
            max_sec=22.0,
            gap_sec=0.8,
        )
        payload = storyboard_to_dict(
            scenes,
            meta={
                "source_srt": srt_path,
                "clean_srt": str(clean_srt),
                "target_sec": 15.0,
                "min_sec": 10.0,
                "max_sec": 22.0,
                "gap_sec": 0.8,
            },
        )
        storyboard_path = paths.prompts_dir / f"{stem}_storyboard_{run_id}.json"
        write_storyboard_json(storyboard_path, payload)
        manifest["steps"]["storyboard"] = {"ok": True, "output": str(storyboard_path), "scene_count": len(payload.get("scenes") or []), "elapsed_s": round(time.time() - t0, 3)}
        logger.info(f"step[4/7] storyboard: done elapsed_s={manifest['steps']['storyboard']['elapsed_s']} scenes={manifest['steps']['storyboard']['scene_count']} output={storyboard_path}")

        # =========================
        # Step 5: prompts aligned with scenes (batched)
        # =========================
        logger.info("step[5/7] scene_prompts: start")
        t0 = time.time()
        scene_list = payload.get("scenes") or []
        if not scene_list:
            raise RuntimeError("storyboard scenes 为空，无法生成图片")

        if int(args.max_scenes) > 0:
            orig_n = len(scene_list)
            scene_list = scene_list[: int(args.max_scenes)]
            payload["scenes"] = scene_list
            logger.info(f"max_scenes applied: {len(scene_list)}/{orig_n}")

        res = _call_with_retry(
            lambda: image_prompts_sync_002(
                scene_list,
                system_prompt=str(img_prompt_system),
                user_prompt_template=str(img_prompt_user_template),
                base_prompt=img_prompt_base,
                batch_size=int(img_prompt_batch_size),
            ),
            what="image_prompts_sync_002_for_scenes",
            logger=logger,
        )
        if len(res.prompts) != len(scene_list):
            raise RuntimeError(f"prompts 数量不匹配：got={len(res.prompts)} expected={len(scene_list)}")

        prompts_path = paths.prompts_dir / f"{stem}_scene_prompts_{run_id}.json"
        prompts_path.write_text(
            json.dumps({"prompts": res.prompts, "meta": {"storyboard": str(storyboard_path)}}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        manifest["steps"]["scene_prompts"] = {"ok": True, "output": str(prompts_path), "count": len(res.prompts), "elapsed_s": round(time.time() - t0, 3)}
        logger.info(f"step[5/7] scene_prompts: done elapsed_s={manifest['steps']['scene_prompts']['elapsed_s']} count={manifest['steps']['scene_prompts']['count']} output={prompts_path}")

        # =========================
        # Step 6: generate images per scene (no cache)
        # =========================
        if bool(args.skip_images):
            logger.info("step[6/7] images: SKIP (skip_images=1)")
            manifest["steps"]["images"] = {"ok": True, "skipped": True}
        else:
            logger.info(f"step[6/7] images: start scenes={len(scene_list)}")
            t0 = time.time()
            ref_image_path = Path(ref_image).expanduser().resolve()
            if not ref_image_path.exists():
                raise FileNotFoundError(f"参考图不存在: {ref_image_path}")

            image_items: list[dict[str, Any]] = []
            for idx, (sc, prompt_str) in enumerate(zip(scene_list, res.prompts), start=1):
                sid = int(sc["scene_id"])
                dst = paths.images_dir / f"scene_{sid:03d}.png"
                item: dict[str, Any] = {"scene_id": sid, "ok": False}

                logger.info(f"image scene[{idx}/{len(scene_list)}] scene_id={sid} generating...")
                try:
                    # 落盘保存完整 prompt（便于复跑）
                    try:
                        prompt_txt = paths.images_dir / f"scene_{sid:03d}.prompt.txt"
                        prompt_txt.write_text(prompt_str or "", encoding="utf-8")
                    except Exception as e:
                        logger.warning(f"prompt save failed scene[{sid}]: {type(e).__name__}: {e}")

                    stdout = _run(
                        [
                            sys.executable,
                            NANOBANANA_SCRIPT,
                            "--aspect-ratio",
                            str(aspect_ratio),
                            "--image",
                            str(ref_image_path),
                            prompt_str,
                        ],
                        cwd=paths.root,
                    )
                    saved_paths = _parse_nanobanana_saved_paths(stdout)
                    moved = _move_one_image(saved_paths, dst)
                    item.update({"ok": True, "image": moved})
                    logger.info(f"image scene[{idx}/{len(scene_list)}] scene_id={sid} OK -> {dst}")

                    sc["prompt"] = prompt_str
                    sc["image_path"] = moved
                except Exception as e:
                    logger.warning(f"scene[{sid}] image failed: {type(e).__name__}: {e}")
                    item["error"] = {"type": type(e).__name__, "message": str(e)}
                image_items.append(item)

            images_manifest_path = paths.images_dir / "images_manifest.json"
            images_manifest_path.write_text(
                json.dumps({"storyboard": str(storyboard_path), "items": image_items, "scenes": scene_list}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            manifest["steps"]["images"] = {"ok": any(x.get("ok") for x in image_items), "items": image_items, "elapsed_s": round(time.time() - t0, 3)}
            ok_cnt = sum(1 for x in image_items if x.get("ok"))
            logger.info(f"step[6/7] images: done elapsed_s={manifest['steps']['images']['elapsed_s']} ok={ok_cnt}/{len(image_items)} manifest={images_manifest_path}")

            write_storyboard_json(storyboard_path, payload)
            logger.info(f"storyboard updated: {storyboard_path}")

        # =========================
        # Step 7: compose video
        # =========================
        if bool(args.skip_video):
            logger.info("step[7/7] video: SKIP (skip_video=1)")
            manifest["steps"]["video"] = {"ok": True, "skipped": True}
            (paths.root / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
            logger.info(f"OK: out_root={paths.root}")
            return 0

        logger.info("step[7/7] video: start")
        t0 = time.time()
        out_mp4 = paths.video_dir / f"{stem}_{run_id}.mp4"
        tmp_dir = paths.video_dir / "_tmp"

        _vp_kwargs = {"width": video_width, "height": video_height, "fps": video_fps, "zoom_start": 1.0}
        if args.zoom_end is not None:
            _vp_kwargs["zoom_end"] = float(args.zoom_end)
        video_params = ComposeVideoParams(**_vp_kwargs)

        compose_video_from_storyboard_002(
            storyboard_json=storyboard_path,
            audio_path=wav_path,
            out_mp4=out_mp4,
            tmp_dir=tmp_dir,
            params=video_params,
            ffmpeg_bin=str(ffmpeg_bin),
            xfade_transition="fade",
            logger=logger,
        )
        manifest["steps"]["video"] = {"ok": True, "mp4": str(out_mp4), "elapsed_s": round(time.time() - t0, 3)}
        logger.info(f"step[7/7] video: done elapsed_s={manifest['steps']['video']['elapsed_s']} mp4={out_mp4}")

        (paths.root / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info(f"FINAL MP4 READY: {out_mp4}")
        logger.info(f"OK: out_root={paths.root}")
        return 0

    except Exception as e:
        logger.exception(e)
        manifest["error"] = {"type": type(e).__name__, "message": str(e)}
        try:
            (paths.root / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass
        raise


if __name__ == "__main__":
    raise RuntimeError(
        "请通过 case 入口运行：\n"
        "- workflow/story_video_001/cases/case_kesulu_001.py\n"
        "- workflow/story_video_001/cases/case_cabian_001.py"
    )
