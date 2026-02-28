#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Ensure pythonProject/ is on sys.path so `component.*` imports work when running from debug/.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from component.muti.synthesis_gemini_pro_image_preview_rest import (
    gemini_3_pro_image_preview_generate_rest,
)

# =========================
# IDE 调试：只改这几行
# =========================
ASPECT_RATIO = "9:16"  # 1:1, 16:9, 9:16, ...
IMAGE_SIZE = "1K"  # 1K / 2K / 4K

PROMPT = (
    """
{
  "style_guide": {
    "core_aesthetic": "Absurd sports crossover / surreal paparazzi flash realism。真实运动抓拍质感 + 世界线错乱事故现场 + “两人长得像到系统崩溃”的核心梗。",
    "darkness_level": "整体偏暗的夜景舞台感；背景70%为深色阴影与雾，主体被闪光灯强行打亮，像热搜爆图，人物脸必须比背景更亮更清晰。",
    "single_highlight": "唯一高光：相机闪光灯直打。两人脸部必须清晰可辨识、五官细节完整、皮肤纹理真实；禁止任何遮挡脸部的装备（护目镜不许遮眼、帽檐不许挡眉眼、手臂不许挡脸）。背景只保留极弱场馆灯轮廓，不得形成第二主光。",
    "fog_dust": "荒诞颗粒：球馆里飘雪粉（像室内下雪），雪粉与木地板扬尘同时在闪光灯下可见；空气里有冷雾翻涌，像系统崩溃后的物理错误。",
    "look_keywords": [
      "surreal sports crossover",
      "paparazzi flash",
      "absurd realism",
      "worldline glitch accident scene",
      "volumetric haze",
      "snow particles indoors",
      "high clarity faces",
      "uncanny resemblance story",
      "tabloid viral photo",
      "no face obstruction"
    ]
  },
  "subject": {
    "character": "必须严格使用两张参考图的人物身份，不得混脸、不许平均化五官：人物A=参考图NBA球员（戈登），人物B=参考图滑雪冠军（谷爱凌）。两人要“像到离谱”的故事核心必须被视觉强化：在同一瞬间做同款困惑半笑、同款抬眉、同款嘴角弧度，甚至连头部微倾角度都高度一致，让观众第一眼以为是同一个人。项目互换但服装也互换到反差最大：戈登穿篮球球衣/护臂/篮球鞋但脚踩雪板在雪道上做专业滑雪急停漂移（雪粉炸开）；谷爱凌穿滑雪外套/雪裤/雪地手套但在球馆里完成夸张标准的单手扣篮（身体腾空、动作像职业扣将）。禁止遮挡脸：戈登不戴遮脸头盔，谷爱凌护目镜只能挂在头顶或脖子且不能挡眼眉。两人都必须正面或三分之二侧正对镜头，脸占画面核心区域，清晰可认。",
    "background": "事故现场式荒诞融合：以室内篮球馆为主（木地板、篮筐结构、观众席轮廓），但球馆中央“长出”一条真实雪道斜坡，像施工事故把木地板顶裂、拱起、掀开，露出冰雪层与压雪纹理。球场线条油漆纹理被雪道挤压扭曲，像世界在报错。远处观众席是一群模糊剪影在举手机拍，像围观超自然事故，强化“热搜现场”。",
    "vibe": "荒诞叙事：世界线错接导致身份与项目对调，但更离谱的是两人长得太像——狗仔闪光灯一打，所有人都以为看见了“同一个人同时在滑雪和扣篮”。",
    "story": "故事核心：戈登在雪道上做专业滑雪急停漂移（雪粉炸开); 谷爱凌在扣篮",
    "focus": "两人极其相似的脸"
  },
  "technical_specs": {
    "camera": "中近景为主（认人优先）：两张脸合计占画面高度至少40%，眼睛必须在清晰对焦平面；允许裁到腰部，但必须看到关键互换道具（戈登脚下雪板与雪粉、谷爱凌手中篮球与扣篮动作上半身姿态）。严格避免运动模糊与糊脸，背景可略虚但结构可读。",
    "lighting": "严格单一主光：相机闪光灯。两人阴影方向一致、接地阴影一致；只允许极弱场馆环境光作远处轮廓，不得形成第二主光。"
  },
  "negative_constraints": [
    "禁止文字",
    "禁止水印",
    "禁止卡通风",
    "禁止明显AI脸崩坏",
    "禁止强畸变与鱼眼",
    "禁止拼贴感",
    "禁止P上去的贴图感",
    "禁止把两个人脸融合成一个（no face blending / no identity merge）",
    "禁止平均化五官导致不像参考图（no generic face）",
    "禁止遮挡脸（no helmet covering face, no goggles covering eyes, no hands blocking face）",
    "禁止额外第三张脸或多余肢体",
    "禁止过度磨皮塑料感"
  ]
}
"""
)

IMAGE_PATHS = [
    # '/Users/test/Library/Mobile Documents/com~apple~CloudDocs/my_mutimedia/my_images/下载原图/老詹/排云掌.jpeg'
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Gemini 3 Pro Image Preview (REST) generator")
    parser.add_argument("prompt", nargs="?", default=None, help="提示词（可选；不传则使用文件顶部 PROMPT）")
    parser.add_argument(
        "--image",
        dest="images",
        action="append",
        default=[],
        help="本地图片路径；可重复传参：--image a.png --image b.jpg",
    )
    parser.add_argument(
        "--no-image",
        dest="no_image",
        action="store_true",
        help="不传参考图（纯文本生成）；启用后将忽略 --image 与文件顶部 IMAGE_PATHS",
    )
    parser.add_argument(
        "--aspect-ratio",
        dest="aspect_ratio",
        default=None,
        help="宽高比，例如 1:1、16:9；不传则使用文件顶部 ASPECT_RATIO",
    )
    parser.add_argument(
        "--image-size",
        dest="image_size",
        default=None,
        help="分辨率档位（imageSize）：1K/2K/4K；不传则使用文件顶部 IMAGE_SIZE",
    )
    parser.add_argument(
        "--max-retries",
        dest="max_retries",
        type=int,
        default=6,
        help="遇到 503/429/5xx 或网络异常时的自动重试次数（总尝试次数=1+max_retries），默认 6",
    )
    parser.add_argument(
        "--retry-base-delay",
        dest="retry_base_delay",
        type=float,
        default=2.0,
        help="重试指数退避的基础延迟（秒），默认 2.0",
    )
    parser.add_argument(
        "--retry-max-delay",
        dest="retry_max_delay",
        type=float,
        default=60.0,
        help="重试等待的最大延迟（秒），默认 60.0",
    )

    args = parser.parse_args()

    prompt = args.prompt or PROMPT
    if args.no_image:
        images = []
    else:
        images = args.images if args.images else IMAGE_PATHS
    aspect_ratio = args.aspect_ratio if args.aspect_ratio is not None else ASPECT_RATIO
    image_size = args.image_size if args.image_size is not None else IMAGE_SIZE

    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../env/default.env"))

    print("model: gemini-3-pro-image-preview (REST)")
    print("aspect_ratio:", aspect_ratio)
    print("image_size:", image_size)
    print("retry:", f"max_retries={args.max_retries}, base_delay={args.retry_base_delay}s, max_delay={args.retry_max_delay}s")
    print("prompt:")
    print(prompt)
    print("images:")
    for p in images:
        print(p)

    saved_paths, meta = gemini_3_pro_image_preview_generate_rest(
        prompt=prompt,
        image_paths=images,
        aspect_ratio=aspect_ratio,
        image_size=image_size,
        api_key=os.getenv("GEMINI_API_KEY"),
        max_retries=args.max_retries,
        base_delay_seconds=args.retry_base_delay,
        max_delay_seconds=args.retry_max_delay,
    )

    if meta.get("text_parts"):
        print("text_parts:")
        for t in meta["text_parts"]:
            print(t)

    if meta.get("attempts_used") is not None:
        print("attempts_used:", meta.get("attempts_used"))
    if meta.get("elapsed_seconds") is not None:
        print("elapsed_seconds:", meta.get("elapsed_seconds"))

    print("saved_paths:")
    for p in saved_paths:
        print(p)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
