#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Batch call DashScope wan2.6-image (edit mode) and download results.

- Region: Beijing
- Endpoint: https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation
- Mode: parameters.enable_interleave = false

Input file format: JSON Lines (one JSON object per line)
Required fields per line:
  - prompt: string
  - images: [string, ...]   # 1~4 image URLs or base64 data URLs
Optional:
  - size: "WIDTH*HEIGHT"    # e.g. "1280*1280"
  - n: int                 # 1~4, default from CLI
  - negative_prompt: string
  - seed: int

Env:
  - DASHSCOPE_API_KEY must be set

This script intentionally keeps checks minimal; it logs key steps and saves images.
"""

from __future__ import annotations

import argparse
import base64
import json
import math
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

import requests
from dotenv import load_dotenv

ENDPOINT_BJ = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
MODEL = "wan2.6-image"


def _ts() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def log(msg: str) -> None:
    print(f"[{_ts()}] {msg}", flush=True)


def read_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            yield lineno, json.loads(s)


def _guess_mime(path: Path) -> str:
    suf = path.suffix.lower()
    if suf in (".jpg", ".jpeg"):
        return "image/jpeg"
    if suf == ".png":
        return "image/png"
    if suf == ".webp":
        return "image/webp"
    if suf == ".bmp":
        return "image/bmp"
    # Default fallback
    return "application/octet-stream"


def _sips_get_size(path: Path) -> tuple[int, int] | None:
    """Return (width, height) using macOS `sips`, or None if unavailable."""
    try:
        p = subprocess.run(
            ["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(path)],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except Exception:
        return None

    if p.returncode != 0:
        return None

    w = h = None
    for line in p.stdout.splitlines():
        line = line.strip()
        if line.startswith("pixelWidth"):
            # pixelWidth: 500
            try:
                w = int(line.split(":", 1)[1].strip())
            except Exception:
                w = None
        elif line.startswith("pixelHeight"):
            try:
                h = int(line.split(":", 1)[1].strip())
            except Exception:
                h = None

    if isinstance(w, int) and isinstance(h, int):
        return w, h
    return None


def _sips_resize(path: Path, out_path: Path, *, width: int, height: int) -> bool:
    """Resize using macOS `sips` into out_path."""
    try:
        p = subprocess.run(
            ["sips", "-z", str(height), str(width), str(path), "--out", str(out_path)],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except Exception:
        return False
    return p.returncode == 0 and out_path.exists()


def _ensure_min_dimensions(path: Path, *, min_dim: int = 384) -> Path:
    """If image is smaller than min_dim on either side, upscale it.

    DashScope requires input image width/height in [384, 5000].
    We keep this dependency-free by using macOS `sips` when available.

    Returns: original path or a temp resized path.
    """
    size = _sips_get_size(path)
    if not size:
        return path

    w, h = size
    if w >= min_dim and h >= min_dim:
        return path

    scale = max(min_dim / max(w, 1), min_dim / max(h, 1))
    new_w = int(math.ceil(w * scale))
    new_h = int(math.ceil(h * scale))

    tmp_dir = Path(tempfile.gettempdir())
    out_path = tmp_dir / f"wan26_upscaled_{path.stem}_{new_w}x{new_h}{path.suffix.lower()}"

    if _sips_resize(path, out_path, width=new_w, height=new_h):
        return out_path
    return path


def _to_image_input(s: str) -> str:
    """Return an image string accepted by DashScope: URL or data URL.

    If s looks like a local file path, encode to base64 data URL.
    If the local image is smaller than 384px on either side, we upscale it first.
    """
    if s.startswith("http://") or s.startswith("https://"):
        return s
    if s.startswith("data:"):
        return s

    p = Path(s).expanduser()
    if p.exists() and p.is_file():
        p2 = _ensure_min_dimensions(p, min_dim=384)
        mime = _guess_mime(p2)
        b64 = base64.b64encode(p2.read_bytes()).decode("ascii")
        return f"data:{mime};base64,{b64}"

    # Fallback: pass through (lets you provide other accepted formats)
    return s


def _merge_prompt(base: str, *, prefix: str = "", suffix: str = "") -> str:
    base = base or ""
    p = prefix.strip()
    s = suffix.strip()
    out = base
    if p:
        out = f"{p}，{out}" if out else p
    if s:
        out = f"{out}，{s}" if out else s
    return out


def _merge_negative(base: str | None, *, suffix: str = "") -> str | None:
    s = suffix.strip()
    if not s:
        return base
    if base and str(base).strip():
        return f"{base}，{s}"
    return s


def build_payload(
    job: dict,
    default_size: str | None,
    default_n: int,
    watermark: bool,
    prompt_extend: bool,
    *,
    ref_image: str | None = None,
    prompt_prefix: str = "",
    prompt_suffix: str = "",
    negative_suffix: str = "",
    subject_lock: bool = False,
) -> dict:
    prompt = str(job["prompt"]) if job.get("prompt") is not None else ""

    images = list(job.get("images") or [])
    if ref_image:
        # Prepend reference image for stronger subject consistency.
        if not images or str(images[0]) != ref_image:
            images = [ref_image] + images

    lock_suffix = ""
    lock_negative = ""
    if subject_lock:
        lock_suffix = (
            "主体人物必须与第一张参考图保持严格一致：面部五官、肤色、发型、体型、年龄气质一致，"
            "不要换脸，不要变成其他人，不要改变身份；同时保持高质感电影级光影与细节丰富"
        )
        lock_negative = "不同人, 换脸, 面部变化, 年龄变化, 性别变化, 五官改变"

    prompt2 = _merge_prompt(prompt, prefix=prompt_prefix, suffix=_merge_prompt(prompt_suffix, suffix=lock_suffix))

    content = [{"text": prompt2}]
    for im in images:
        content.append({"image": _to_image_input(str(im))})

    params = {
        "enable_interleave": False,
        "watermark": watermark,
        "prompt_extend": prompt_extend,
        "n": int(job.get("n", default_n)),
    }

    size = job.get("size", default_size)
    if size:
        params["size"] = size

    neg = job.get("negative_prompt")
    neg2 = _merge_negative(neg, suffix=_merge_negative(negative_suffix, suffix=lock_negative) or "")
    if neg2 is not None:
        params["negative_prompt"] = neg2

    if "seed" in job and job["seed"] is not None:
        params["seed"] = int(job["seed"])

    return {
        "model": MODEL,
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": content,
                }
            ]
        },
        "parameters": params,
    }


def extract_image_urls(resp_json: dict) -> list[str]:
    urls: list[str] = []
    output = resp_json.get("output") or {}
    choices = output.get("choices") or []
    for ch in choices:
        msg = (ch.get("message") or {})
        content = msg.get("content") or []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "image" and block.get("image"):
                urls.append(block["image"])
    return urls


def download(url: str, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Using urllib to avoid extra deps; works fine for OSS signed URLs
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as r:
        data = r.read()
    out_path.write_bytes(data)


def run_batch(
    in_path: str | Path = "jobs.jsonl",
    out_dir: str | Path = "out",
    *,
    default_size: str = "1280*1280",
    default_n: int = 1,
    watermark: bool = False,
    prompt_extend: bool = True,
    sleep_s: float = 0.3,
    api_key: str | None = None,
    ref_image: str | None = None,
    prompt_prefix: str = "",
    prompt_suffix: str = "",
    negative_suffix: str = "",
    subject_lock: bool = False,
) -> tuple[int, int]:
    """Run batch requests and download images.

    Returns: (jobs_processed, images_saved)
    """
    # logger.info("📋 初始化配置参数")
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../env/default.env"))

    # 测试Qwen模型
    api_key = os.getenv("DASHSCOPE_API_KEY")

    if not api_key:
        log("ERROR: env DASHSCOPE_API_KEY is not set")
        return 0, 0

    in_path = Path(in_path)
    out_dir = Path(out_dir)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    log(f"Endpoint: {ENDPOINT_BJ}")
    log(f"Input: {in_path}")
    log(f"Output: {out_dir}")
    log(f"Default size: {default_size}, default n: {default_n}, watermark: {bool(watermark)}, prompt_extend: {bool(prompt_extend)}")
    if ref_image:
        log(f"Reference image (prepended): {ref_image}")
    if subject_lock:
        log("Subject lock: ENABLED")

    sess = requests.Session()

    total_jobs = 0
    total_images = 0

    for lineno, job in read_jsonl(in_path):
        total_jobs += 1
        job_id = job.get("id")
        tag = f"job#{total_jobs} (line {lineno}{', id='+str(job_id) if job_id is not None else ''})"

        payload = build_payload(
            job,
            default_size=default_size,
            default_n=default_n,
            watermark=bool(watermark),
            prompt_extend=bool(prompt_extend),
            ref_image=ref_image,
            prompt_prefix=prompt_prefix,
            prompt_suffix=prompt_suffix,
            negative_suffix=negative_suffix,
            subject_lock=subject_lock,
        )

        prompt_preview = str(job.get("prompt", ""))[:60].replace("\n", " ")
        log(f"{tag} -> request (prompt: {prompt_preview!r})")

        t0 = time.time()
        r = sess.post(ENDPOINT_BJ, headers=headers, json=payload, timeout=600)
        dt = time.time() - t0

        try:
            resp_json = r.json()
        except Exception:
            log(f"{tag} <- HTTP {r.status_code} (not json), elapsed={dt:.2f}s")
            log(r.text[:5000])
            continue

        request_id = resp_json.get("request_id")
        if r.status_code != 200:
            log(f"{tag} <- HTTP {r.status_code}, request_id={request_id}, elapsed={dt:.2f}s")
            log(f"error_code={resp_json.get('code')}, message={resp_json.get('message')}")
            continue

        urls = extract_image_urls(resp_json)
        usage = resp_json.get("usage") or {}
        log(f"{tag} <- OK, request_id={request_id}, elapsed={dt:.2f}s, usage.image_count={usage.get('image_count')}, usage.size={usage.get('size')}")
        log(f"{tag} <- images: {len(urls)}")

        for j, url in enumerate(urls, 1):
            out_path = out_dir / f"{total_jobs:04d}_{j:02d}.png"
            log(f"{tag}   download {j}/{len(urls)} -> {out_path}")
            try:
                download(url, out_path)
                total_images += 1
            except Exception as e:
                log(f"{tag}   download FAILED: {e}")

        if sleep_s:
            time.sleep(sleep_s)

    log(f"DONE: jobs={total_jobs}, images_saved={total_images}")
    return total_jobs, total_images


def main() -> int:
    ap = argparse.ArgumentParser(description="Batch wan2.6-image (edit mode) + download")
    ap.add_argument("--in", dest="in_path", default="jobs.jsonl", help="Input JSONL (default: jobs.jsonl)")
    ap.add_argument("--out", dest="out_dir", default="out", help="Output directory (default: out)")
    ap.add_argument("--size", dest="default_size", default="1280*1280", help="Default size (default: 1280*1280)")
    ap.add_argument("--n", dest="default_n", type=int, default=1, help="Default n for each job (default: 1)")
    ap.add_argument("--watermark", action="store_true", help="Enable watermark (default: false)")
    ap.add_argument("--no-prompt-extend", action="store_true", help="Disable prompt_extend (default: enabled)")
    ap.add_argument("--sleep", dest="sleep_s", type=float, default=0.3, help="Sleep seconds between requests (default: 0.3)")
    ap.add_argument("--ref", dest="ref_image", default=None, help="Reference image to prepend for every job (path or URL)")
    ap.add_argument("--subject-lock", action="store_true", help="Force subject identity to match the first reference image")
    ap.add_argument("--prompt-prefix", default="", help="Text prepended to every prompt")
    ap.add_argument("--prompt-suffix", default="", help="Text appended to every prompt")
    ap.add_argument("--negative-suffix", default="", help="Text appended to every negative_prompt")
    args = ap.parse_args()

    jobs, images = run_batch(
        in_path=args.in_path,
        out_dir=args.out_dir,
        default_size=args.default_size,
        default_n=args.default_n,
        watermark=bool(args.watermark),
        prompt_extend=not args.no_prompt_extend,
        sleep_s=float(args.sleep_s),
        ref_image=args.ref_image,
        subject_lock=bool(args.subject_lock),
        prompt_prefix=str(args.prompt_prefix or ""),
        prompt_suffix=str(args.prompt_suffix or ""),
        negative_suffix=str(args.negative_suffix or ""),
    )

    # Preserve previous exit behavior: treat missing key as error.
    if jobs == 0 and images == 0 and not os.environ.get("DASHSCOPE_API_KEY"):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
