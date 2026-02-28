"""Experimental REST caller for Gemini 3 Pro Image Preview.

Why:
- In the current environment, `google.genai.types.ImageConfig` does NOT expose `image_size`,
  so Python SDK config construction fails before any request is sent.
- The official REST API supports `generationConfig.imageConfig.imageSize` for
  `gemini-3-pro-image-preview`.

This module intentionally does NOT modify any existing flash/pro SDK code.
"""

from __future__ import annotations

import base64
import os
import random
import sys
import time
from pathlib import Path
from typing import Any

import requests
from requests import Response
from requests.exceptions import RequestException
from dotenv import load_dotenv

import config.config as config
from config.logging_config import get_logger

logger = get_logger(__name__)


_ALLOWED_ASPECT_RATIOS = {
    "1:1",
    "2:3",
    "3:2",
    "3:4",
    "4:3",
    "4:5",
    "5:4",
    "9:16",
    "16:9",
    "21:9",
}

_ALLOWED_IMAGE_SIZES = {"1K", "2K", "4K"}


def _resolve_api_key(api_key: str | None) -> str:
    if api_key:
        return api_key

    try:
        load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../env/default.env"))
    except Exception:
        pass

    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise ValueError("未找到 GEMINI_API_KEY，请设置环境变量或在函数参数中传入 api_key")
    return key


def _guess_mime_type(path: str) -> str:
    p = path.lower()
    if p.endswith(".png"):
        return "image/png"
    if p.endswith(".jpg") or p.endswith(".jpeg"):
        return "image/jpeg"
    if p.endswith(".webp"):
        return "image/webp"
    # fallback
    return "image/jpeg"


def _ext_for_mime(mime: str | None) -> str:
    if mime == "image/png":
        return "png"
    if mime == "image/webp":
        return "webp"
    # default jpeg
    return "png"


def gemini_3_pro_image_preview_generate_rest(
    *,
    prompt: str,
    image_paths: list[str] | None = None,
    aspect_ratio: str = "1:1",
    image_size: str = "2K",
    api_key: str | None = None,
    save_dir: Path | str | None = None,
    timeout_seconds: int = 120,
    max_retries: int = 6,
    base_delay_seconds: float = 2.0,
    max_delay_seconds: float = 60.0,
) -> tuple[list[str], dict[str, Any]]:
    """Call REST API for gemini-3-pro-image-preview with imageSize.

    Args:
        prompt: prompt text
        image_paths: optional local images (will be sent as inlineData base64)
        aspect_ratio: e.g. 1:1, 16:9
        image_size: e.g. 1K, 2K, 4K
        api_key: optional API key override
        save_dir: output directory (default config.PICTURE_RESULTS_DIR)
        timeout_seconds: HTTP timeout
        max_retries: max retry attempts for transient failures (total attempts = 1 + max_retries)
        base_delay_seconds: base delay for exponential backoff
        max_delay_seconds: upper bound for backoff delay

    Returns:
        (saved_paths, meta)
    """

    if not prompt or not prompt.strip():
        raise ValueError("prompt 不能为空")

    if aspect_ratio not in _ALLOWED_ASPECT_RATIOS:
        raise ValueError(f"aspect_ratio 不支持：{aspect_ratio}，允许值：{sorted(_ALLOWED_ASPECT_RATIOS)}")

    if image_size not in _ALLOWED_IMAGE_SIZES:
        raise ValueError(f"image_size 不支持：{image_size}，允许值：{sorted(_ALLOWED_IMAGE_SIZES)}")

    key = _resolve_api_key(api_key)
    out_dir = Path(save_dir) if save_dir is not None else Path(config.PICTURE_RESULTS_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    if max_retries < 0:
        raise ValueError("max_retries 不能为负数")
    if base_delay_seconds <= 0:
        raise ValueError("base_delay_seconds 必须 > 0")
    if max_delay_seconds <= 0:
        raise ValueError("max_delay_seconds 必须 > 0")

    image_paths = image_paths or []

    parts: list[dict[str, Any]] = []
    # Keep prompt first (as docs examples)
    parts.append({"text": prompt})

    for p in image_paths:
        with open(p, "rb") as f:
            data_b64 = base64.b64encode(f.read()).decode("utf-8")
        parts.append(
            {
                "inlineData": {
                    "mimeType": _guess_mime_type(p),
                    "data": data_b64,
                }
            }
        )

    payload: dict[str, Any] = {
        "contents": [
            {
                "parts": parts,
            }
        ],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
            "imageConfig": {
                "aspectRatio": aspect_ratio,
                "imageSize": image_size,
            },
        },
    }

    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-image-preview:generateContent"
    headers = {
        "x-goog-api-key": key,
        "Content-Type": "application/json",
    }

    # NOTE: Fail-fast mode. We intentionally do NOT retry here to make failures visible
    # and avoid long waits caused by repeated attempts.
    def _request_once() -> tuple[Response, float, int, float]:
        total_start = time.time()
        start = time.time()
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=timeout_seconds)
            elapsed = round(time.time() - start, 3)
            total_elapsed = round(time.time() - total_start, 3)
            # attempts_used is always 1 in fail-fast mode
            return resp, elapsed, 1, total_elapsed
        except RequestException as e:
            elapsed = round(time.time() - start, 3)
            # attempts_used is always 1 in fail-fast mode
            raise RuntimeError(f"Gemini REST 请求异常（不重试，elapsed={elapsed:.3f}s）：{repr(e)}") from e

    logger.info(
        "Gemini REST generate - model=%s, images=%d, aspect_ratio=%s, image_size=%s, max_retries=%s",
        "gemini-3-pro-image-preview",
        len(image_paths),
        aspect_ratio,
        image_size,
        max_retries,
    )

    resp, elapsed, attempts_used, total_elapsed = _request_once()
    print(
        f"[retry] attempts_used={attempts_used} (max_retries={max_retries})",
        file=sys.stderr,
        flush=True,
    )
    print(
        f"[timing] http_total_elapsed={total_elapsed:.3f}s (last_request_elapsed={elapsed:.3f}s)",
        file=sys.stderr,
        flush=True,
    )

    meta: dict[str, Any] = {
        "model": "gemini-3-pro-image-preview",
        "prompt": prompt,
        "input_image_paths": list(image_paths),
        "requested_aspect_ratio": aspect_ratio,
        "requested_image_size": image_size,
        "elapsed_seconds": total_elapsed,
        "last_request_elapsed_seconds": elapsed,
        "attempts_used": attempts_used,
        "http_status": resp.status_code,
        "saved_paths": [],
        "text_parts": [],
    }

    if resp.status_code != 200:
        # include body for debugging
        raise RuntimeError(f"Gemini REST 请求失败 status={resp.status_code}: {resp.text[:2000]}")

    data = resp.json()

    saved_paths: list[str] = []

    # Typical structure: candidates[0].content.parts[*]
    candidates = data.get("candidates") or []
    for cand in candidates:
        content = (cand.get("content") or {})
        for part in (content.get("parts") or []):
            if part.get("text") is not None:
                meta["text_parts"].append(part["text"])
                continue

            inline = part.get("inlineData")
            if inline and inline.get("data"):
                mime = inline.get("mimeType")
                ext = _ext_for_mime(mime)
                blob = base64.b64decode(inline["data"])
                file_path = out_dir / f"gemini_3_pro_image_preview_{int(time.time())}_{len(saved_paths)}.{ext}"
                with open(file_path, "wb") as f:
                    f.write(blob)
                saved_paths.append(str(file_path))

    meta["saved_paths"] = list(saved_paths)

    if not saved_paths:
        raise RuntimeError(
            "Gemini REST 未返回图片结果（saved_paths 为空）。"
            "请检查：prompt 是否有效、模型是否可用、API Key 是否正确、以及输入图片是否合规。"
        )

    return saved_paths, meta
