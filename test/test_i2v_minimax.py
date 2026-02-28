"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 测试数据或模块
Output: 测试结果
Pos: 测试文件：test_i2v_minimax.py
"""

import os
import time
import logging

import requests
from dotenv import load_dotenv

from data.test_prompt import TEST_I2V_PROMPT_019
from config.logging_config import setup_logging
from util.util_file import download_file_from_url
from util.util_url import upload_file_to_oss

import config.config as cfg

logger = logging.getLogger(__name__)

def create_video_task(api_key, image_url, prompt):
    """创建视频生成任务，返回 task_id"""
    url = "https://api.minimaxi.com/v1/video_generation"

    payload = {
        "prompt": prompt,
        "first_frame_image": image_url,
        "model": "MiniMax-Hailuo-02",
        "duration": 6,
        "resolution": "512P",
        "prompt_optimizer": False,

    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    resp = requests.post(url, json=payload, headers=headers)
    result = resp.json()
    logger.info(f"创建任务响应: {result}")

    if result.get("base_resp", {}).get("status_code") == 0:
        task_id = result.get("task_id")
        logger.info(f"✅ 任务创建成功，task_id: {task_id}")
        return task_id
    else:
        logger.error(f"❌ 任务创建失败: {result}")
        return None


def query_task_status(api_key, task_id):
    """查询任务状态，原样返回服务端 JSON"""
    url = f"https://api.minimaxi.com/v1/query/video_generation?task_id={task_id}"
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = requests.get(url, headers=headers)
    return resp.json()


def download_video(api_key, file_id, save_dir=cfg.VIDEO_RESULTS_DIR):
    """根据 file_id 下载视频到 save_dir，返回本地路径"""
    url = f"https://api.minimaxi.com/v1/files/retrieve?file_id={file_id}"
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = requests.get(url, headers=headers)
    logger.info(f"视频下载响应: {resp.status_code} {resp.text}")
    if resp.status_code == 200:
        os.makedirs(save_dir, exist_ok=True)
        filename = f"minimax_i2v_{file_id}.mp4"
        video_url = resp.json().get("file", {}).get("download_url")
        video_path = download_file_from_url(
            video_url,
            save_dir=save_dir,
            filename=filename
        )
        logger.info(f"✅ 视频下载成功: {video_path}")
        logger.info(f"🔗 视频URL: {video_url}")
        return video_url, video_path
    else:
        logger.error(f"❌ 视频下载失败: {resp.status_code} {resp.text}")
        return None, None


def wait_for_completion(api_key, task_id, max_wait_time=600, poll_interval=10):
    """轮询任务直到成功/失败/超时，成功则返回 file_id"""
    start = time.time()
    while time.time() - start < max_wait_time:
        res = query_task_status(api_key, task_id)
        status = res.get("status") or res.get("task_status")
        logger.info(f"任务状态: {status} | 响应: {res}")

        if status in ("Success", "SUCCESS", "finished"):
            file_id = res.get("file_id") or (res.get("data") or {}).get("file_id")
            return file_id
        if status in ("Failed", "FAIL", "Fail", "failed", "error"):
            return None

        time.sleep(poll_interval)

    logger.error(f"⏰ 任务超时: {task_id}")
    return None


def debug_minimax_i2v(image_url, prompt):
    # 使用minimax hailuo i2v生成视频

    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../env/default.env"))
    api_key = os.getenv("MINIMAX_API_KEY")
    if not api_key:
        raise ValueError("MINIMAX_API_KEY 未配置")

    # 1) 创建任务
    task_id = create_video_task(api_key, image_url, prompt)
    if not task_id:
        return

    # 2) 轮询直到完成
    file_id = wait_for_completion(api_key, task_id)
    if not file_id:
        logger.error("任务未成功完成，退出")
        return

    # 3) 下载视频
    video_url, video_path = download_video(api_key, file_id, cfg.VIDEO_RESULTS_DIR)

    return video_url, video_path


def main():
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../env/default.env"))
    api_key = os.getenv("MINIMAX_API_KEY")
    if not api_key:
        raise ValueError("MINIMAX_API_KEY 未配置")

    # 测试图片路径
    i_path_8 = '/Users/test/code/My_files/my_files/my_images/1:1_girl_image/wan25_t2i_1765263759.png'
    i_path_9 = '/Users/test/code/My_files/my_files/my_images/1:1_girl_image/wan25_t2i_1765263603.png'
    i_path_10 = '/Users/test/code/My_files/my_files/my_images/1:1_girl_image/wan25_t2i_1765263886.png'

    image_path = i_path_9
    prompt = TEST_I2V_PROMPT_019

    image_url = upload_file_to_oss(image_path, 300)

    # 1) 创建任务
    task_id = create_video_task(api_key, image_url, prompt)
    if not task_id:
        return

    # 2) 轮询直到完成
    file_id = wait_for_completion(api_key, task_id)
    if not file_id:
        logger.error("任务未成功完成，退出")
        return

    # 3) 下载视频
    download_video(api_key, file_id, cfg.VIDEO_RESULTS_DIR)


if __name__ == "__main__":
    setup_logging()
    main()
