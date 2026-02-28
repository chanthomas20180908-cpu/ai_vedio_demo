"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 文本/参数
Output: 图片文件
Pos: 图片合成功能
"""

import json
import os
import time
from datetime import time as datetime_time
from http import HTTPStatus
from urllib.parse import urlparse, unquote
from pathlib import PurePosixPath

from dashscope import MultiModalConversation, ImageSynthesis
import requests
import dashscope
from dotenv import load_dotenv

from util.util_file import download_file_from_url
from util.util_url import upload_file_to_oss
from config.logging_config import get_logger
import config.config as config


# 项目启动时初始化日志
logger = get_logger(__name__)


def synthesis_picture_with_wan(
    api_key="",
    prompt="",
    model_name="wan2.5-t2i-preview",
    negative_prompt=None,
    images=None,
    sketch_image_url=None,
    workspace=None,
    extra_input=None,
    task=None,
    function=None,
    strength=None,
    base_image_url=None,
    mask_image_url=None,
    n=1,
    size='1024*1024',
    similarity=None,
    sketch_weight=10,
    realisticness=5,
    prompt_extend=True,
    watermark=False,
    seed=12345,
    ref_img=None,
    save_dir="Downloads",

):
    """
    使用wan模型生成图片

    :param api_key: API密钥
    :param prompt: 图片生成的提示词
    :param model_name: 使用的模型名称，参考 Models
    :param negative_prompt: 负面提示词，默认为None
    :param images: 输入的图片URL列表，目前不支持
    :param sketch_image_url: 仅适用于wanx-sketch-to-image-v1，可以是本地文件，默认为None
    :param workspace: dashscope工作区ID
    :param extra_input: 额外的输入参数
    :param task: API的任务类型，参考文档
    :param function: 要实现的具体功能，如：colorization,super_resolution,expand,remove_watermaker,doodle, description_edit_with_mask,description_edit,stylization_local,stylization_all
    :param strength: 和base图片的相似性，取值范围[0.0, 1.0]，默认值为0.5
    :param base_image_url: 目标编辑图片的URL地址
    :param mask_image_url: 用户标记区域的图片URL，应与base_image_url的图像分辨率一致
    :param n: 生成图片的数量
    :param size: 输出图片的尺寸(宽*高)
    :param similarity: 输出图片与输入图片的相似度
    :param sketch_weight: 输入草图对输出图片的影响程度[0-10]，仅适用于wanx-sketch-to-image-v1，默认10
    :param realisticness: 输出图片的真实感[0-10]，仅适用于wanx-sketch-to-image-v1，默认5
    :param prompt_extend: 是否扩展提示词
    :param watermark: 是否添加水印
    :param seed: 生成的随机种子
    :param ref_img: 参考图，仅wanx-v1支持
    :param save_dir: 保存目录
    :return: 图片路径列表和URL列表
    """
    logger.info(f"开始使用{model_name}模型生成图片")
    logger.info(f"提示词: {prompt}")

    try:
        # 构建调用参数
        call_params = {
            'api_key': api_key,
            'model': model_name,
            'prompt': prompt,
            'n': n,
            'size': size,
            'prompt_extend': prompt_extend,
            'watermark': watermark,
            'seed': seed
        }

        # 添加可选参数
        if negative_prompt is not None:
            call_params['negative_prompt'] = negative_prompt
        if images is not None:
            call_params['images'] = images
        if sketch_image_url is not None:
            call_params['sketch_image_url'] = sketch_image_url
        if workspace is not None:
            call_params['workspace'] = workspace
        if extra_input is not None:
            call_params['extra_input'] = extra_input
        if task is not None:
            call_params['task'] = task
        if function is not None:
            call_params['function'] = function
        if strength is not None:
            call_params['strength'] = strength
        if base_image_url is not None:
            call_params['base_image_url'] = base_image_url
        if mask_image_url is not None:
            call_params['mask_image_url'] = mask_image_url
        if similarity is not None:
            call_params['similarity'] = similarity
        if sketch_weight != 10:  # Only add if not default
            call_params['sketch_weight'] = sketch_weight
        if realisticness != 5:  # Only add if not default
            call_params['realisticness'] = realisticness
        if ref_img is not None:
            call_params['ref_img'] = ref_img

        rsp = ImageSynthesis.call(**call_params)

        logger.info(f"API响应: {rsp}")

        if rsp.status_code == HTTPStatus.OK:
            picture_paths = []
            picture_urls = []

            # 保存图片到本地
            for i, result in enumerate(rsp.output.results):
                file_name = PurePosixPath(unquote(urlparse(result.url).path)).parts[-1]
                file_path = os.path.join(save_dir, file_name)

                # 确保保存目录存在
                os.makedirs(save_dir, exist_ok=True)

                # 下载并保存图片
                with open(file_path, 'wb+') as f:
                    f.write(requests.get(result.url).content)

                picture_paths.append(file_path)
                picture_urls.append(result.url)
                logger.info(f"图片已保存: {file_path}")

            return picture_paths, picture_urls
        else:
            logger.error(f'图片生成失败, status_code: {rsp.status_code}, code: {rsp.code}, message: {rsp.message}')
            return None, None

    except Exception as e:
        logger.error(f"图片生成过程中发生错误: {e}")
        return None, None



def synthesis_picture_with_qwen(api_key="", prompt="", model_name="qwen-image", save_dir="Downloads"):
    """
    使用AI生成生成图片
    :param api_key:
    :param prompt:
    :param model_name:
    :param save_dir:
    :return:
    """
    messages = [
        {
            "role": "user",
            "content": [
                {"text": prompt}
            ]
        }
    ]

    response = MultiModalConversation.call(
        api_key=api_key,
        model=model_name,
        messages=messages,
        result_format='message',
        stream=False,
        watermark=True,
        prompt_extend=True,
        negative_prompt='',
        size='1328*1328'
    )

    if response.status_code == 200:
        logger.info(json.dumps(response, ensure_ascii=False))
        picture_url = response["output"]["choices"][0]["message"]["content"][0]["image"]
        logger.info(f"图片生成完成，图片访问链接为:{picture_url}")
        # 获取任务id作为文件唯一索引
        request_id = response["request_id"]
        # 保存图片到本地
        picture_path = download_file_from_url(picture_url, save_dir, f"my_picture_{request_id}.png")

        return picture_path, picture_url

    else:
        logger.info(f"HTTP返回码：{response.status_code}")
        logger.info(f"错误码：{response.code}")
        logger.info(f"错误信息：{response.message}")
        logger.info("请参考文档：https://help.aliyun.com/zh/model-studio/developer-reference/error-code")
        return None, None


def call_wan21_imageedit(api_key: str = "", image_url: str = "", function: str = "", prompt: str = "", save_dir: str = None):
    """
    图片编辑
    """
    if save_dir is None:
        save_dir = config.PICTURE_RESULTS_DIR
    
    logger.info(f"图片编辑任务: {prompt}")
    logger.info(f"输入图片: {image_url}")
    
    # 调用通用函数
    picture_paths, picture_urls = synthesis_picture_with_wan(
        api_key=api_key,
        prompt=prompt,
        model_name="wanx2.1-imageedit",
        function=function,
        base_image_url=image_url,
        n=1,
        save_dir=save_dir
    )
    
    if picture_paths and picture_urls:
        logger.info(f"图片编辑完成，共 {len(picture_paths)} 张")
        for path, url in zip(picture_paths, picture_urls):
            logger.info(f"保存图片到：{path}")
            logger.info(f"图片URL：{url}")
        return picture_paths, picture_urls
    else:
        logger.error("图片编辑失败")
        return None, None


def call_wan25_i2i_preview(api_key: str = "", images_url: list = [], function: str = "", prompt: str = "", negative_prompt: str = "",
                         save_dir: str = None):
    """
    图片编辑
    """
    if save_dir is None:
        save_dir = config.PICTURE_RESULTS_DIR

    logger.info(f"图片编辑任务: {prompt}")
    logger.info(f"输入图片: {images_url}")

    # 调用通用函数
    picture_paths, picture_urls = synthesis_picture_with_wan(
        api_key=api_key,
        prompt=prompt,
        negative_prompt=negative_prompt,
        model_name="wan2.5-i2i-preview",
        n=1,
        save_dir=save_dir
    )

    if picture_paths and picture_urls:
        logger.info(f"图片编辑完成，共 {len(picture_paths)} 张")
        for path, url in zip(picture_paths, picture_urls):
            logger.info(f"保存图片到：{path}")
            logger.info(f"图片URL：{url}")
        return picture_paths, picture_urls
    else:
        logger.error("图片编辑失败")
        return None, None


if __name__ == "__main__":
    from config.logging_config import setup_logging

    # 项目启动时初始化日志
    setup_logging()

    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../env/default.env"))
    api_key = os.getenv("DASHSCOPE_API_KEY")

    folder_path = "/Users/test/Code/Python/AI_vedio_demo/pythonProject/data/upload"  # 📁 需要上传的文件夹路径
    expire_time = 600          # ⏳ 链接有效期（秒）

    url_list = []

    # 遍历文件夹上传所有文件
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        if os.path.isfile(file_path):
            try:
                url = upload_file_to_oss(file_path, expire_time)
                url_list.append(url)
            except Exception as e:
                print(f"❌ 上传失败: {file_name} - {e}")

    # 轮询调用 sample_sync_call_imageedit
    print("\n🚀 开始轮询调用 sample_sync_call_imageedit ...\n")
    for url in url_list:
        print(f"📡 调用 sample_sync_call_imageedit: {url}")
        call_wan21_imageedit(api_key=api_key, image_url=url, function="remove_watermark", prompt="去除文字水印")
        time.sleep(5)  # 控制调用节奏，防止API限流

