import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
from config.logging_config import get_logger
from util.util_url import upload_file_to_oss


# 项目启动时初始化日志
logger = get_logger(__name__)

DASHSCOPE_BASE = "https://dashscope.aliyuncs.com/api/v1"
SUBMIT_URL = DASHSCOPE_BASE + "/services/aigc/image2image/image-synthesis"

def submit_remove_watermark(api_key: str, base_image_url: str, prompt: str) -> str:
    logger.info("🚀 提交去水印任务")
    logger.info(f"模型: wanx2.1-imageedit | function: remove_watermark")
    logger.info(f"prompt: {prompt}")
    logger.info(f"base_image_url: {base_image_url}")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-DashScope-Async": "enable",
    }
    payload = {
        "model": "wanx2.1-imageedit",
        "input": {
            "function": "remove_watermark",
            "prompt": prompt,
            "base_image_url": base_image_url,
        },
        "parameters": {"n": 1},
    }

    r = requests.post(SUBMIT_URL, headers=headers, json=payload, timeout=60)
    logger.debug(f"提交响应: HTTP {r.status_code}")
    r.raise_for_status()
    data = r.json()

    task_id = data["output"]["task_id"]  # 按最常见结构写死，简单
    logger.info(f"✅ 提交成功 task_id: {task_id}")
    return task_id


def poll_result_url(api_key: str, task_id: str) -> str:
    url = DASHSCOPE_BASE + f"/tasks/{task_id}"
    headers = {"Authorization": f"Bearer {api_key}"}

    logger.info(f"⏳ 开始轮询任务: {task_id}")

    last_status = None
    while True:
        r = requests.get(url, headers=headers, timeout=60)
        r.raise_for_status()
        data = r.json()

        status = data["output"]["task_status"]
        if status != last_status:
            logger.info(f"📡 任务状态: {status}")
            last_status = status

        if status == "SUCCEEDED":
            result_url = data["output"]["results"][0]["url"]
            logger.info(f"✅ 任务完成 result_url: {result_url}")
            return result_url
        if status == "FAILED":
            logger.error(f"❌ 任务失败: {data}")
            raise RuntimeError(f"task failed: {data}")
        time.sleep(1)


def download_to(url: str, out_path: Path) -> str:
    logger.info(f"⬇️  下载结果图到本地: {out_path}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    r = requests.get(url, timeout=120)
    logger.debug(f"下载响应: HTTP {r.status_code}")
    r.raise_for_status()
    out_path.write_bytes(r.content)
    logger.info(f"✅ 已保存: {out_path}")
    return str(out_path)

def main():
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../env/default.env"))
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise RuntimeError("missing DASHSCOPE_API_KEY")

    watch_dir = Path("/Users/test/Code/Python/AI_vedio_demo/pythonProject/data/upload")  # 监听目录
    out_dir = Path("data/watermark_removed")  # 输出目录
    expire_time = 600
    prompt = "去除图像中的文字"

    logger.info("🧩 debug_remove_watermark 启动")
    logger.info(f"watch_dir: {watch_dir}")
    logger.info(f"out_dir: {out_dir}")
    logger.info(f"expire_time: {expire_time}s")

    seen = set()

    while True:
        for p in watch_dir.iterdir():
            if not p.is_file():
                continue
            if p.suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp"):
                continue
            if str(p) in seen:
                continue
            seen.add(str(p))

            logger.info(f"🖼️  发现新文件: {p}")

            # 1) 上传拿 http 链接
            logger.info("☁️  上传到OSS获取URL...")
            img_url = upload_file_to_oss(str(p), expire_time)
            logger.info(f"🔗 OSS URL: {img_url}")

            # 2) 提交任务
            task_id = submit_remove_watermark(api_key, img_url, prompt)

            # 3) 轮询拿结果图 url
            result_url = poll_result_url(api_key, task_id)

            # 4) 下载到本地，输出路径（放到 out_dir，不污染 upload 目录）
            out_path = out_dir / f"{p.stem}_removed.png"
            local_path = download_to(result_url, out_path)
            logger.info(f"📁 本地输出: {local_path}")
            print(local_path)

        time.sleep(2)

if __name__ == "__main__":
    from config.logging_config import setup_logging, get_logger

    # 项目启动时初始化日志
    setup_logging()
    main()
