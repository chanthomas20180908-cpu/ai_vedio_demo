"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 测试数据或模块
Output: 测试结果
Pos: 测试文件：test_i2v_doubao.py
"""

from datetime import datetime
import os
import time

from dotenv import load_dotenv
# 通过 pip install 'volcengine-python-sdk[ark]' 安装方舟SDK
from volcenginesdkarkruntime import Ark

from data.test_prompt import TEST_I2V_PROMPT_016, TEST_I2V_PROMPT_019
from config.logging_config import get_logger, setup_logging
from util.util_file import download_file_from_url
from util.util_url import upload_file_to_oss

import config.config as cfg

logger = get_logger(__name__)

# 请确保您已将 API Key 存储在环境变量 ARK_API_KEY 中
# 初始化Ark客户端，从环境变量中读取您的API Key
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../env/default.env"))
api_key = os.getenv("ARK_API_KEY")
if not api_key:
    raise ValueError("ARK_API_KEY 未配置")
client = Ark(
    # 此为默认路径，您可根据业务所在地域进行配置
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    # 从环境变量中获取您的 API Key。此为默认方式，您可根据需要进行修改
    api_key=api_key,
)


def debug_seedance_i2v(image_url, prompt, mdl="lite"):
    # 请确保您已将 API Key 存储在环境变量 ARK_API_KEY 中
    # 初始化Ark客户端，从环境变量中读取您的API Key
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../env/default.env"))
    api_key = os.getenv("ARK_API_KEY")
    if not api_key:
        raise ValueError("DASHSCOPE_API_KEY 未配置")
    client = Ark(
        # 此为默认路径，您可根据业务所在地域进行配置
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        # 从环境变量中获取您的 API Key。此为默认方式，您可根据需要进行修改
        api_key=api_key,
    )

    if mdl == "lite":
        model = "doubao-seedance-1-0-lite-i2v-250428"
    elif mdl == "pro":
        model = "doubao-seedance-1-0-pro-250528"
    else:
        raise ValueError("model 参数错误")

    logger.info("----- create request -----")
    create_result = client.content_generation.tasks.create(
        model=model,
        content=[
            {
                # 文本提示词与参数组合
                "type": "text",
                "text": f"{prompt}  --resolution 480p  --duration 5 --camerafixed false --watermark false"
            },
            {
                # 首帧图片URL
                "type": "image_url",
                "image_url": {
                    "url": image_url
                }
            }
        ]
    )
    logger.info(create_result)

    # 轮询
    logger.info("----- polling task status -----")
    task_id = create_result.id
    while True:
        get_result = client.content_generation.tasks.get(task_id=task_id)
        status = get_result.status
        if status == "succeeded":
            logger.info("----- task succeeded -----")
            logger.info(get_result)
            # 这里从结果中取出 video_url
            try:
                # SDK 结构是 get_result.content.video_url
                if getattr(get_result, "content", None) is not None:
                    video_url = getattr(get_result.content, "video_url", None)
                    # 下载视频
                    video_path = download_file_from_url(
                        video_url,
                        save_dir=cfg.VIDEO_RESULTS_DIR,
                        filename=f"{model}_result{datetime.now().strftime('%Y%m%d%H%M%S')}.mp4"
                    )

                    return video_url, video_path

            except Exception as e:
                logger.exception(f"解析 video_url 失败: {e}")

            return None, None

        elif status == "failed":
            logger.info("----- task failed -----")
            logger.info(f"Error: {get_result.error}")
            # 失败时也返回 None 和完整结果，方便 debug
            return None, None

        else:
            logger.info(f"Current status: {status}, Retrying after 1 seconds...")
            time.sleep(1)


if __name__ == "__main__":
    setup_logging()
    video_url, video_path = debug_seedance_i2v(
        image_url=upload_file_to_oss(
            "/Users/test/Code/My_files/my_files/my_images/baby/wan25_t2i_1764748796.png",
            300
        ),
        prompt=TEST_I2V_PROMPT_019,
        mdl="lite"
    )