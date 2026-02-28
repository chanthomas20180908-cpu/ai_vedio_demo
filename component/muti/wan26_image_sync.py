"""wan26_image_sync.py

⚠️ 仅做最小可用实现（保持简单）：
- HTTP 同步调用 wan2.6-image（enable_interleave=false）
- 入参 images 只支持【本地图片路径】(1~4)
- 本地图片若任一边 < 384，使用 macOS sips 等比放大到 >=384
- 上传使用 util.util_url.upload_file_to_oss(path, 300) -> 返回公网可访问URL
- 下载使用 util.util_file.download_file_from_url
- 主体锁默认开启（prompt/negative_prompt 追加短模板）

Input: prompt + local image paths
Output: downloaded png paths + image urls
"""

from __future__ import annotations

import json
import math
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import List, Optional, Tuple

import requests
from dotenv import load_dotenv

import config.config as config
from config.logging_config import get_logger
from util.util_file import download_file_from_url
from util.util_url import upload_file_to_oss

logger = get_logger(__name__)

ENDPOINT_BJ = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
MODEL = "wan2.6-image"


def _load_env_once() -> None:
    # 参照项目写法：尝试加载 env/default.env（若不存在不报错）
    env_path = Path(__file__).resolve().parents[2] / "env" / "default.env"
    if env_path.exists():
        load_dotenv(dotenv_path=str(env_path))


def _sips_get_size(path: Path) -> Optional[Tuple[int, int]]:
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
    """If local image smaller than min_dim on either side, upscale it via sips.

    Returns original path or a temp upscaled path.
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
        logger.info(f"✅ 已放大输入图: {path.name} ({w}x{h} -> {new_w}x{new_h})")
        return out_path

    return path


def _assert_local_images(image_paths: List[str]) -> List[Path]:
    if not image_paths:
        raise ValueError("images 不能为空（必须提供1~4张本地图片路径）")

    out: List[Path] = []
    for s in image_paths:
        if s.startswith(("http://", "https://", "data:", "file://")):
            raise ValueError(f"images 仅支持本地路径，不支持URL/data/file://：{s}")
        p = Path(s).expanduser()
        if not p.exists() or not p.is_file():
            raise FileNotFoundError(f"图片文件不存在: {p}")
        out.append(p)

    if not (1 <= len(out) <= 4):
        raise ValueError(f"images 数量必须在 1~4 之间，当前: {len(out)}")

    return out


def _apply_subject_lock(prompt: str, negative_prompt: str) -> Tuple[str, str]:
    # 极简锁主体模板（默认开启）
    lock_p = "主体人物必须与第一张参考图严格一致（同一人同一脸，不换脸不变人），18岁新秀气质，面部无胡子无胡渣。"
    lock_n = "不同人, 换脸, 面部变化, 年龄变化, 性别变化, 五官改变, 胡子, 胡渣, 络腮胡"

    p = f"{lock_p}{prompt}" if prompt else lock_p
    n = negative_prompt.strip() if negative_prompt else ""
    n = f"{n}, {lock_n}" if n else lock_n
    return p, n


def wan26_generate(
    prompt: str,
    image_paths: List[str],
    *,
    size: str = "720*1280",
    n: int = 1,
    negative_prompt: str = "",
    save_dir: Path | str | None = None,
    oss_ttl: int = 300,
    lock_subject: bool = True,
    api_key: Optional[str] = None,
) -> Tuple[List[str], List[str], Optional[str]]:
    """Sync call wan2.6-image (edit mode) and download results.

    Returns (saved_paths, image_urls, request_id)
    """
    _load_env_once()

    if api_key is None:
        api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("未找到 DASHSCOPE_API_KEY")

    if lock_subject:
        prompt, negative_prompt = _apply_subject_lock(prompt, negative_prompt)

    local_paths = _assert_local_images(image_paths)
    prepared_paths = [_ensure_min_dimensions(p, min_dim=384) for p in local_paths]

    logger.info(f"wan2.6-image 同步调用: images={len(prepared_paths)}, size={size}, n={n}, oss_ttl={oss_ttl}, lock_subject={lock_subject}")

    # upload -> urls
    image_url_list = [upload_file_to_oss(str(p), oss_ttl) for p in prepared_paths]

    content = [{"text": prompt}] + [{"image": u} for u in image_url_list]

    payload = {
        "model": MODEL,
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": content,
                }
            ]
        },
        "parameters": {
            "enable_interleave": False,
            "watermark": False,
            "prompt_extend": True,
            "n": int(n),
            "size": size,
            "negative_prompt": negative_prompt,
        },
    }

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

    t0 = time.time()
    r = requests.post(ENDPOINT_BJ, headers=headers, json=payload, timeout=600)
    dt = time.time() - t0

    try:
        resp = r.json()
    except Exception:
        raise RuntimeError(f"HTTP {r.status_code} 非JSON响应: {r.text[:2000]}")

    request_id = resp.get("request_id")
    if r.status_code != 200:
        raise RuntimeError(
            f"HTTP {r.status_code} request_id={request_id} code={resp.get('code')} message={resp.get('message')}"
        )

    # extract image urls
    urls: List[str] = []
    output = resp.get("output") or {}
    for ch in (output.get("choices") or []):
        msg = (ch.get("message") or {})
        for block in (msg.get("content") or []):
            if isinstance(block, dict) and block.get("type") == "image" and block.get("image"):
                urls.append(block["image"])

    logger.info(f"✅ OK request_id={request_id} elapsed={dt:.2f}s images={len(urls)}")

    if save_dir is None:
        save_dir = config.PICTURE_RESULTS_DIR
    save_dir = Path(save_dir)
    saved_paths: List[str] = []
    for idx, url in enumerate(urls, 1):
        filename = f"wan26_{request_id or int(time.time())}_{idx:02d}.png"
        path = download_file_from_url(url, save_dir, filename)
        saved_paths.append(path)
        logger.info(f"📥 saved: {path}")

    return saved_paths, urls, request_id
