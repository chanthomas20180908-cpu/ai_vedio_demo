"""\
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: storyboard（scene 列表，含 start/end 与 image_path）、音频 wav
Output: mp4 视频（不烧字幕），可用于后续剪映导入
Pos: 工作流 - 图片+音频合成视频（taskgroup，可复用）

说明（保持最简单）：
- 以 scene 为单位：每个 scene 一张图，持续 duration 秒
- 每个 scene 使用轻微 zoompan（Ken Burns）制造“移动动画”
- 不包含字幕：字幕仅用于确定 scene 的 start/end

注意：剪映工程格式没有稳定公开规范；第一版只产出标准 mp4 + 资产清单，保证可导入、可替换素材。
"""

from __future__ import annotations

import json
import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional


@dataclass
class ComposeVideoParams:
    width: int = 1080
    height: int = 1920
    fps: int = 30
    # zoompan: subtle (increase for stronger motion)
    zoom_start: float = 1.0
    zoom_end: float = 1.12


def _run(cmd: list[str], *, cwd: Optional[Path] = None) -> str:
    p = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        text=True,
        capture_output=True,
    )
    if p.returncode != 0:
        # 附带少量 stderr/stdout 头部，便于你在主流程日志里快速定位
        stdout_head = (p.stdout or "").splitlines()[:30]
        stderr_head = (p.stderr or "").splitlines()[:60]
        raise RuntimeError(
            "Command failed:\n"
            f"cmd={' '.join(cmd)}\n"
            f"returncode={p.returncode}\n"
            f"stdout(head)=\n" + "\n".join(stdout_head) + "\n\n"
            f"stderr(head)=\n" + "\n".join(stderr_head) + "\n"
        )
    return p.stdout


def _load_storyboard(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    return json.loads(path.read_text(encoding="utf-8"))


def compose_video_from_storyboard_001(
    *,
    storyboard_json: str | Path,
    audio_path: str | Path,
    out_mp4: str | Path,
    tmp_dir: str | Path,
    params: ComposeVideoParams = ComposeVideoParams(),
    ffmpeg_bin: str = "ffmpeg",
    crf: int = 18,
    preset: str = "medium",
    transition_fade_s: float = 0.25,
    max_scenes: Optional[int] = None,
    logger: Optional[logging.Logger] = None,
) -> Path:
    """按 scene 逐段生成视频片段，再 concat，最后与音频合成。

    这么做的好处：
    - 每段 duration 精确（通过固定帧数输出，避免 zoompan 放大时长）
    - 每段可独立替换图片 / 重渲染

    max_scenes: 调试用，仅处理前 N 个 scene（避免跑全量卡住）
    """

    storyboard_json = Path(storyboard_json)
    audio_path = Path(audio_path)
    out_mp4 = Path(out_mp4)
    tmp_dir = Path(tmp_dir)

    tmp_dir.mkdir(parents=True, exist_ok=True)
    out_mp4.parent.mkdir(parents=True, exist_ok=True)

    sb = _load_storyboard(storyboard_json)
    scenes = sb.get("scenes") or []
    if not scenes:
        raise ValueError(f"storyboard scenes 为空: {storyboard_json}")

    if max_scenes is not None:
        if max_scenes <= 0:
            raise ValueError(f"max_scenes 必须 > 0: {max_scenes}")
        scenes = scenes[: int(max_scenes)]

    if logger:
        logger.info(
            "compose_video: start "
            f"scenes={len(scenes)} audio={audio_path} storyboard={storyboard_json} "
            f"out={out_mp4} tmp_dir={tmp_dir}"
        )

    seg_paths: list[Path] = []

    # 1) render each segment as mp4
    for i, sc in enumerate(scenes, start=1):
        sid = int(sc.get("scene_id"))
        start_s = float(sc.get("start_s", 0.0))
        end_s = float(sc.get("end_s", 0.0))
        duration = max(0.05, end_s - start_s)

        img = sc.get("image_override") or sc.get("image_path")
        if not img:
            raise ValueError(f"scene_{sid:03d} 缺少 image_path/image_override")
        img_path = Path(img)
        if not img_path.exists():
            raise FileNotFoundError(str(img_path))

        seg_out = tmp_dir / f"seg_{sid:03d}.mp4"
        seg_paths.append(seg_out)

        if logger:
            logger.info(
                f"compose_video: render seg {i}/{len(scenes)} scene_id={sid} "
                f"duration={duration:.3f}s img={img_path.name} -> {seg_out.name}"
            )

        # zoompan: use linear zoom from zoom_start to zoom_end
        # 关键：必须“固定输出帧数”，否则当输入是 duration 秒的循环图片时，zoompan 会把时长放大。
        z0 = params.zoom_start
        z1 = params.zoom_end
        frames = int(round(duration * params.fps))
        if frames < 2:
            frames = 2

        # on 是输出帧序号；zoom 使用 smoothstep 缓动，并做“先放大再缩小/交替”变化
        # u: 0->1->0（ping-pong），ease: smoothstep(u)
        half = max(1.0, (frames - 1) / 2.0)
        u = f"if(lte(on,{half:.6f}), on/{half:.6f}, ({(frames - 1):.6f}-on)/{half:.6f})"
        ease = f"({u})*({u})*(3-2*({u}))"

        # ping-pong zoom (in then out) for this scene
        zoom_core = f"{z0}+({z1}-{z0})*({ease})"
        zoom_expr = f"min({max(z0, z1)},{zoom_core})"

        # transitions (no black cut): keep a background base image always visible;
        # fade foreground alpha in/out over it.
        fade_s = float(transition_fade_s or 0.0)
        if fade_s <= 0.0 or duration <= 0.12:
            fade_in_fg = ""
            fade_out_fg = ""
        else:
            # keep it safe for short scenes, and keep fades shorter to reduce "hard cut" feeling
            fade_s = min(fade_s, max(0.02, duration / 2.0))
            fade_out_st = max(0.0, duration - fade_s)
            fade_in_fg = f",fade=t=in:st=0:d={fade_s:.3f}:alpha=1"
            fade_out_fg = f",fade=t=out:st={fade_out_st:.3f}:d={fade_s:.3f}:alpha=1"

        # IMPORTANT: split FIRST, then blur only background branch.
        bg_chain = (
            f"scale={params.width}:{params.height}:force_original_aspect_ratio=decrease,"
            f"pad={params.width}:{params.height}:(ow-iw)/2:(oh-ih)/2:color=black,"
            f"boxblur=10:1"
        )
        fg_chain = (
            f"scale={params.width}:{params.height}:force_original_aspect_ratio=decrease,"
            f"pad={params.width}:{params.height}:(ow-iw)/2:(oh-ih)/2:color=black,"
            f"zoompan=z='{zoom_expr}':x='(iw-ow)/2':y='(ih-oh)/2':d=1:s={params.width}x{params.height},"
            f"fps={params.fps},format=rgba"
            f"{fade_in_fg}{fade_out_fg}"
        )

        vf = (
            f"split=2[bgsrc][fgsrc];"
            f"[bgsrc]{bg_chain}[bg];"
            f"[fgsrc]{fg_chain}[fg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2:format=auto,format=yuv420p"
        )

        cmd = [
            ffmpeg_bin,
            "-y",
            "-loop",
            "1",
            "-i",
            str(img_path),
            "-vf",
            vf,
            "-frames:v",
            str(frames),
            "-an",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-crf",
            str(crf),
            "-preset",
            preset,
            str(seg_out),
        ]
        _run(cmd)

    # 2) concat segments (demuxer)
    concat_list = tmp_dir / "concat_list.txt"
    concat_list.write_text(
        "\n".join([f"file '{p.as_posix()}'" for p in seg_paths]) + "\n",
        encoding="utf-8",
    )

    video_no_audio = tmp_dir / "video_no_audio.mp4"
    cmd_concat = [
        ffmpeg_bin,
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_list),
        "-c",
        "copy",
        str(video_no_audio),
    ]
    if logger:
        logger.info(f"compose_video: concat {len(seg_paths)} segs -> {video_no_audio.name}")
    _run(cmd_concat)

    # 3) mux audio (keep video length as-is; trim audio if longer)
    cmd_mux = [
        ffmpeg_bin,
        "-y",
        "-i",
        str(video_no_audio),
        "-i",
        str(audio_path),
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-shortest",
        str(out_mp4),
    ]
    if logger:
        logger.info(f"compose_video: mux audio -> {out_mp4.name}")
    _run(cmd_mux)

    if logger:
        try:
            size_mb = out_mp4.stat().st_size / (1024 * 1024)
            logger.info(f"compose_video: DONE out={out_mp4} size={size_mb:.2f}MB")
        except Exception:
            logger.info(f"compose_video: DONE out={out_mp4}")

    return out_mp4
