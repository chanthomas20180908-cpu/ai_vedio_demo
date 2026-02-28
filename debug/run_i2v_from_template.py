"""\
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 本地图片路径 + 模板 key
Output: 生成视频 URL + 本地保存路径
Pos: debug/run_i2v_from_template.py

最小脚本（无 CLI）：
- 你只需要修改下面 2 行：IMAGE_PATH / TEMPLATE_KEY
- 从 config/i2v_templates.py 读取模板 prompt + 默认模型/引擎
- 上传图片一次（OSS URL 复用）
- 根据引擎调用现有封装生成视频
- 打印关键日志
"""

import os
import sys
import time
from typing import Tuple

# 让脚本在 debug/ 下也能 import 项目包
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.logging_config import get_logger, setup_logging
from config.i2v_templates import get_template
from util.util_url import upload_file_to_oss

from debug.debug_sync_wan_i2v import debug_synx_i2v_wan22
from test.test_i2v_minimax import debug_minimax_i2v
from test.test_i2v_doubao import debug_seedance_i2v


def _run_by_engine(engine: str, model: str, image_url: str, prompt: str) -> Tuple[str, str]:
    """返回 (video_url, video_path)。"""
    if engine == "wan":
        # 现有封装：内部已固定相关参数
        return debug_synx_i2v_wan22(image_url, prompt)

    if engine == "minimax":
        return debug_minimax_i2v(image_url, prompt)

    if engine == "doubao":
        # 这里按 model 名称判断 lite/pro（最小实现）
        variant = "lite" if "lite" in (model or "").lower() else "pro"
        return debug_seedance_i2v(image_url, prompt, variant)

    raise ValueError(f"Unknown i2v_engine: {engine}")


def run_once(image_path: str, template_key: str) -> Tuple[str, str]:
    setup_logging()
    logger = get_logger(__name__)

    template = get_template(template_key)

    title = template.get("title", "")
    group = template.get("group", "")
    engine = template.get("i2v_engine")
    prompt = template.get("prompt")
    params = template.get("params", {})
    model = params.get("model", "")

    if not engine:
        raise ValueError(f"template[{template_key}] missing i2v_engine")
    if not prompt:
        raise ValueError(f"template[{template_key}] missing prompt")

    logger.info(f"[TEMPLATE] key={template_key} title={title} group={group} engine={engine} model={model}")
    logger.info(f"[INPUT] image_path={image_path}")

    t0 = time.time()
    image_url = upload_file_to_oss(image_path, 300)
    logger.info(f"[UPLOAD] image_url={image_url}")

    t1 = time.time()
    logger.info(f"[RUN] start engine={engine} model={model}")
    video_url, video_path = _run_by_engine(engine=engine, model=model, image_url=image_url, prompt=prompt)
    t2 = time.time()

    logger.info(f"[RESULT] video_url={video_url}")
    logger.info(f"[RESULT] video_path={video_path}")
    logger.info(f"[COST] upload={t1 - t0:.2f}s run={t2 - t1:.2f}s total={t2 - t0:.2f}s")

    return video_url, video_path


# ===== 只改这里 =====
IMAGE_PATH = '/Users/test/Library/Mobile Documents/com~apple~CloudDocs/my_mutimedia/my_vedios/meme_video/黛玉20251229/download_3243213.png'
TEMPLATE_KEY = "self_crown"

# ====================
if __name__ == "__main__":
    run_once(IMAGE_PATH, TEMPLATE_KEY)
