"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 测试数据或模块
Output: 测试结果
Pos: 测试文件：debug_sync_wan_i2v.py
"""


import time
import webbrowser
import config.config as cfg
from dotenv import load_dotenv

from component.muti.synthesis_video import sync_video_with_wan
from config.logging_config import get_logger
from util.util_url import upload_file_to_oss

import os


# 项目启动时初始化日志
logger = get_logger(__name__)


def debug_synx_i2v_wan22(image_url, prompt):

    logger.info("📋 初始化配置参数")
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../env/default.env"))
    api_key = os.getenv("DASHSCOPE_API_KEY")
    # api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("DASHSCOPE_API_KEY 未配置")

    video_url, video_path = sync_video_with_wan(
        api_key,
        model="wan2.2-i2v-plus",
        # model="wan2.2-i2v-flash",
        # model="wan2.5-i2v-preview",
        image_url=image_url,
        prompt=prompt,
        audio=False,
        # audio_url=audio_url",
        resolution="480P",
        duration=5,
        prompt_extend=False,
        # seed=88,
        save_dir=cfg.VIDEO_RESULTS_DIR,

    )

    return video_url, video_path


if __name__ == "__main__":
    # 测试并发VideoRetalk模型
    from config.logging_config import setup_logging

    # 项目启动时初始化日志
    setup_logging()

    # 记录开始时间
    start_time = time.time()

    i_path_1 = "/Users/test/Code/My_files/my_files/my_images/baby/wan25_t2i_1764748796.png"  # baby 1
    i_path_2 = "/Users/test/Code/My_files/my_files/my_images/baby/wan25_t2i_1764749118.png"  # baby 2
    i_path_3 = "/Users/test/Code/My_files/my_files/my_images/baby/wan25_t2i_1764749157.png"  # baby 3
    i_path_4 = "/Users/test/Code/My_files/my_files/my_images/baby/wan25_t2i_1764749197.png"  # baby 4

    i_path_5 = "/Users/test/Code/My_files/my_files/my_images/欠男/wan25_t2i_1764831129.png"  # 欠男

    i_path_6 = "/Users/test/code/My_files/my_files/my_images/slave/wan25_t2i_1765247834.png"  # 社畜男 1
    i_path_7 = "/Users/test/code/My_files/my_files/my_images/slave/wan25_t2i_1765248811.png"  # 社畜女 1

    i_path_8 = '/Users/test/code/My_files/my_files/my_images/1:1_girl_image/wan25_t2i_1765263759.png'  # 短发 1
    i_path_9 = '/Users/test/code/My_files/my_files/my_images/1:1_girl_image/wan25_t2i_1765263603.png'
    i_path_10 = '/Users/test/code/My_files/my_files/my_images/1:1_girl_image/wan25_t2i_1765263886.png'

    image_path = i_path_9
    image_url = upload_file_to_oss(image_path, 300)
    prompt = ""

    video_url, video_path = debug_synx_i2v_wan22(image_url, prompt)

    # 记录结束时间并计算运行时间
    end_time = time.time()
    print(f"token_calculate 运行时间: {end_time - start_time:.4f} 秒")

    if video_url and video_path:
        print(f"✅ 生成成功!")
        print(f"   视频URL: {video_url}")
        print(f"   本地路径: {video_path}")
        # 去掉查询参数
        clean_video_path = video_path.split('?')[0]
        # 检查文件是否存在
        if os.path.exists(clean_video_path):
            webbrowser.open(f"file://{clean_video_path}")
        else:
            print("文件不存在，请检查路径是否正确。")
    else:
        print("❌ 生成失败")
