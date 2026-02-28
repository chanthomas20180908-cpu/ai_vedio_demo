"""Unified Gemini image generation helper.

Goal:
- Keep existing flash implementation untouched.
- Provide a minimal unified function that supports:
  - gemini-2.5-flash-image: aspect_ratio
  - gemini-3-pro-image-preview: aspect_ratio + image_size (resolution)

Notes:
- `resolution` (image_size) is ONLY passed when model == "gemini-3-pro-image-preview".
  This avoids pydantic validation errors for models/SDK schemas that don't accept image_size.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from PIL import Image

import config.config as config
from config.logging_config import get_logger
from util.util_url import upload_file_to_oss

logger = get_logger(__name__)


def _resolve_api_key(api_key: str | None) -> str:
    if api_key:
        return api_key

    # Keep project convention: try env/default.env first.
    try:
        load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../env/default.env"))
    except Exception:
        pass

    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise ValueError("未找到 GEMINI_API_KEY，请设置环境变量或在函数参数中传入 api_key")
    return key


def gemini_generate_image(
    prompt: str,
    image_paths: list[str] | None = None,
    api_key: str | None = None,
    save_dir: Path | str | None = None,
    model: str = "gemini-2.5-flash-image",
    aspect_ratio: str | None = None,
    resolution: str | None = None,
    oss_expire_seconds: int = 300,
) -> tuple[list[str], dict[str, Any]]:
    """Unified Gemini image generation (text-to-image / image-to-image).

    Args:
        prompt: prompt text
        image_paths: optional local image paths (multiple allowed)
        api_key: optional GEMINI_API_KEY override
        save_dir: output directory (default: config.PICTURE_RESULTS_DIR)
        model: Gemini model name
        aspect_ratio: image aspect ratio (e.g. "1:1", "16:9")
        resolution: image_size (e.g. "1K", "2K", "4K") - only used for gemini-3-pro-image-preview
        oss_expire_seconds: TTL for uploaded OSS URLs (only for logging/echo)

    Returns:
        (saved_paths, meta)
    """

    # Function-local imports to avoid hard dependency in other modules.
    from google import genai
    from google.genai import types

    if not prompt or not prompt.strip():
        raise ValueError("prompt 不能为空")

    key = _resolve_api_key(api_key)
    out_dir = Path(save_dir) if save_dir is not None else Path(config.PICTURE_RESULTS_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    image_paths = image_paths or []

    meta: dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "input_image_paths": list(image_paths),
        "input_image_oss_urls": [],
        "requested_aspect_ratio": aspect_ratio,
        "requested_resolution": resolution,
        "text_parts": [],
        "saved_paths": [],
    }

    contents: list[Any] = [prompt]

    if image_paths:
        image_url_list = [upload_file_to_oss(image_path, oss_expire_seconds) for image_path in image_paths]
        meta["input_image_oss_urls"] = image_url_list

        pil_images = [Image.open(p) for p in image_paths]
        contents.extend(pil_images)

    client = genai.Client(api_key=key)

    image_config_kwargs: dict[str, Any] = {}
    if aspect_ratio:
        image_config_kwargs["aspect_ratio"] = aspect_ratio

    # IMPORTANT: image_size is only supported by some models (e.g. gemini-3-pro-image-preview).
    if resolution and model == "gemini-3-pro-image-preview":
        image_config_kwargs["image_size"] = resolution

    gen_config = (
        types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"],
            image_config=types.ImageConfig(**image_config_kwargs),
        )
        if image_config_kwargs
        else None
    )

    logger.info(
        "Gemini generate image - model=%s, images=%d, aspect_ratio=%s, resolution=%s",
        model,
        len(image_paths),
        aspect_ratio,
        resolution,
    )

    start = time.time()
    if gen_config is not None:
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=gen_config,
        )
    else:
        response = client.models.generate_content(
            model=model,
            contents=contents,
        )
    meta["elapsed_seconds"] = round(time.time() - start, 3)

    saved_paths: list[str] = []

    for idx, part in enumerate(getattr(response, "parts", []) or []):
        if getattr(part, "text", None):
            meta["text_parts"].append(part.text)
            continue

        if getattr(part, "inline_data", None) is not None:
            try:
                image = part.as_image()
            except Exception as e:
                logger.error("Gemini returned an image part but parsing failed idx=%s: %s", idx, e)
                continue

            file_path = out_dir / f"gemini_{model.replace('/', '_')}_{int(time.time())}_{idx}.png"
            image.save(str(file_path))
            saved_paths.append(str(file_path))

    meta["saved_paths"] = list(saved_paths)

    if not saved_paths:
        raise RuntimeError(
            "Gemini 未返回图片结果（saved_paths 为空）。"
            "请检查：prompt 是否有效、模型是否可用、API Key 是否正确、以及输入图片是否合规。"
        )

    return saved_paths, meta
