"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 文本描述
Output: 图像文件
Pos: 图像合成功能
"""

import json
import os
import time
import base64
import mimetypes
from datetime import time as datetime_time
from http import HTTPStatus
from typing import Tuple, Union
from urllib.parse import urlparse, unquote
from pathlib import PurePosixPath, Path

from dashscope import MultiModalConversation, ImageSynthesis
import requests
import dashscope
from dotenv import load_dotenv

from data.test_prompt import TEST_T2I_PROMPT_001, TEST_T2I_PROMPT_002, TEST_T2I_PROMPT_003
from util.util_file import download_file_from_url
from util.util_url import upload_file_to_oss
from config.logging_config import get_logger
import config.config as config


# 项目启动时初始化日志
logger = get_logger(__name__)

# 以下为北京地域url，若使用新加坡地域的模型，需将url替换为：https://dashscope-intl.aliyuncs.com/api/v1
dashscope.base_http_api_url = 'https://dashscope.aliyuncs.com/api/v1'


# ============================================
# 辅助函数
# ============================================

def encode_local_image_to_base64(file_path: str) -> str:
    """
    将本地图片编码为Base64格式（供API调用）
    
    Args:
        file_path: 本地图片路径
        
    Returns:
        Base64编码的图片字符串，格式：data:{MIME_type};base64,{base64_data}
        
    Example:
        >>> encode_local_image_to_base64("./image.png")
        'data:image/png;base64,iVBORw0KG...'
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"图片文件不存在: {file_path}")
    
    mime_type, _ = mimetypes.guess_type(str(file_path))
    if not mime_type or not mime_type.startswith("image/"):
        raise ValueError(f"不支持或无法识别的图像格式: {file_path}")
    
    with open(file_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    
    return f"data:{mime_type};base64,{encoded_string}"


def prepare_image_url(image_source: str) -> str:
    """
    准备图片URL（自动识别格式并转换）
    
    Args:
        image_source: 图片源，支持：
            - 公网URL: "https://example.com/image.png"
            - 本地路径: "./image.png" 或 "/path/to/image.png"
            - file:// URL: "file://./image.png"
            - Base64: "data:image/png;base64,..."
            
    Returns:
        API可接受的图片URL格式
    """
    # 已经是http(s)或data URL，直接返回
    if image_source.startswith(("http://", "https://", "data:")):
        return image_source
    
    # file:// 格式，直接返回
    if image_source.startswith("file://"):
        return image_source
    
    # 本地路径，转换为Base64
    if Path(image_source).exists():
        logger.info(f"检测到本地图片，转换为Base64: {image_source}")
        return encode_local_image_to_base64(image_source)
    
    # 无法识别，返回原值（让API报错）
    logger.warning(f"无法识别的图片格式: {image_source}")
    return image_source


def _log_result(picture_paths, picture_urls, task_name="生成"):
    """统一的结果日志"""
    if picture_paths and picture_urls:
        logger.info(f"{task_name}完成，共 {len(picture_paths)} 张")
        return picture_paths, picture_urls
    else:
        logger.error(f"{task_name}失败")
        return None, None


# ============================================
# Qwen 文生图
# ============================================

def qwen_text_to_image(
        api_key: str,
        prompt: str,
        model_name: str = "qwen-image",
        size: str = "1328*1328",
        save_dir: str = None
) -> tuple[list[str], list[str]]:
    """Qwen文生图

    Args:
        api_key: API密钥
        prompt: 生成提示词
        model_name: 模型名称（qwen-image）
        size: 图片尺寸
        save_dir: 保存目录

    Returns:
        (图片路径列表, 图片URL列表)
    """
    save_dir = save_dir or config.PICTURE_RESULTS_DIR

    logger.info(f"Qwen文生图 - 模型: {model_name}")
    logger.info(f"提示词: {prompt}")

    try:
        messages = [{
            "role": "user",
            "content": [{"text": prompt}]
        }]

        response = MultiModalConversation.call(
            api_key=api_key,
            model=model_name,
            messages=messages,
            result_format='message',
            stream=False,
            watermark=True,
            prompt_extend=True,
            negative_prompt='',
            size=size
        )

        if response.status_code == 200:
            logger.info(f"API响应: {json.dumps(response, ensure_ascii=False)}")
            
            # 检查响应结构
            try:
                picture_url = response["output"]["choices"][0]["message"]["content"][0]["image"]
                request_id = response["request_id"]
            except (KeyError, IndexError) as e:
                logger.error(f"❌ API响应结构异常: {e}")
                logger.error(f"完整响应: {json.dumps(response, ensure_ascii=False)}")
                return None, None

            logger.info(f"✅ Qwen生成成功，图片URL: {picture_url}")
            picture_path = download_file_from_url(
                picture_url,
                save_dir,
                f"qwen_{request_id}.png"
            )

            # 统一返回格式：列表
            return [picture_path], [picture_url]
        else:
            logger.error(f"❌ HTTP返回码: {response.status_code}")
            logger.error(f"错误码: {response.code}")
            logger.error(f"错误信息: {response.message}")
            return None, None

    except Exception as e:
        logger.error(f"生成失败: {e}")
        return None, None


# ============================================
# 万象2.5 文生图
# ============================================


def sync_t2i_wan_v25(
        api_key: str,
        prompt: str,
        negative_prompt: str = "",
        n: int = 1,
        size: str = "1280*720",
        seed: int = 12345,
        save_dir: str = config.PICTURE_RESULTS_DIR
) -> Union[tuple[str, str], tuple[None, None]]:
    """万象2.5文生图

    Args:
        api_key: API密钥
        prompt: 生成提示词
        negative_prompt: 负面提示词
        n: 生成数量
        size: 图片尺寸：总像素在[768*768, 1440*1440]之间 16:9[1280*720；1920*1080]
        seed: 种子,默认1234
        save_dir: 保存目录

    Returns:
        (图片路径列表, 图片URL列表)
    """

    logger.info(f"万象2.5文生图")
    logger.info(f"提示词: {prompt}")

    try:
        params = {
            'api_key': api_key,
            'model': 'wan2.5-t2i-preview',
            'prompt': prompt,
            'n': n,
            'size': size,
            'prompt_extend': True,
            'watermark': False,
            'seed': seed,
        }
        if negative_prompt:
            params['negative_prompt'] = negative_prompt

        rsp = ImageSynthesis.call(**params)

        # 详细的响应日志
        logger.info(f"API响应状态: {rsp.status_code}")
        logger.info(f"API响应码: {getattr(rsp, 'code', 'N/A')}")
        logger.info(f"API响应消息: {getattr(rsp, 'message', 'N/A')}")
        
        # 检查结果数量
        results_count = len(rsp.output.results) if rsp.output and hasattr(rsp.output, 'results') and rsp.output.results else 0
        logger.info(f"结果数量: {results_count}")

        if rsp.status_code == HTTPStatus.OK:
            # 检查 code 字段是否有错误（即使 status_code 是 200）
            if hasattr(rsp, 'code') and rsp.code and rsp.code != 'Success':
                logger.error(f"API返回错误码: {rsp.code}")
                logger.error(f"错误信息: {getattr(rsp, 'message', '未知错误')}")
                return None, None
            
            # 检查 results 是否为空
            if not rsp.output.results:
                logger.error("❌ API返回结果为空！任务可能超时或失败")
                logger.error(f"完整响应: status_code={rsp.status_code}, code={getattr(rsp, 'code', 'N/A')}, message={getattr(rsp, 'message', 'N/A')}")
                return None, None
            
            # 有结果才访问
            image_url = rsp.output.results[0].url
            logger.info(f"✅ 生成成功，图片URL: {image_url}")
            
            image_path = download_file_from_url(
                image_url,
                save_dir,
                f"wan25_t2i_{int(time.time())}.png"
            )
            return image_path, image_url
        else:
            logger.error(f'❌ HTTP请求失败: status_code={rsp.status_code}, code={rsp.code}, message={rsp.message}')
            return None, None

    except Exception as e:
        logger.error(f"❌ 生成异常: {e}")
        logger.exception(e)  # 打印完整堆栈
        return None, None


# ============================================
# 万象2.5 图生图
# ============================================


def sync_i2i_wan_v25(
        api_key: str,
        prompt: str,
        images: list[str] = None,
        negative_prompt: str = "",
        n: int = 1,
        save_dir: str = config.PICTURE_RESULTS_DIR
) -> Union[tuple[str, str], tuple[None, None]]:
    """万象2.5图生图
    
    图片输入格式说明：
    1. 公网URL: "https://example.com/image.png"
    2. 本地文件: "file:///path/to/image.png" 或 "file://./image.png"
    3. Base64编码: "data:image/png;base64,iVBORw0KG..."

    Args:
        api_key: API密钥
        prompt: 生成提示词
        images: 输入图片URL列表，必填（支持上述3种格式）
        negative_prompt: 负面提示词
        n: 生成数量
        save_dir: 保存目录

    Returns:
        (图片URL, 图片路径)
    """
    
    if not images:
        logger.error("图生图必须提供输入图片")
        return None, None

    logger.info(f"万象2.5图生图")
    logger.info(f"输入图片数量: {len(images)}")
    logger.info(f"提示词: {prompt}")

    try:
        # 自动处理图片URL格式（本地路径转为Base64）
        # processed_images = [prepare_image_url(img) for img in images]
        
        params = {
            'api_key': api_key,
            'model': 'wan2.5-i2i-preview',
            'prompt': prompt,
            'images': images,  # 必须参数
            'n': n,
            'watermark': False,
            'seed': 12345,
        }

        if negative_prompt:
            params['negative_prompt'] = negative_prompt

        rsp = ImageSynthesis.call(**params)

        # 详细的响应日志
        logger.info(f"API响应状态: {rsp.status_code}")
        logger.info(f"API响应码: {getattr(rsp, 'code', 'N/A')}")
        logger.info(f"API响应消息: {getattr(rsp, 'message', 'N/A')}")
        
        # 检查结果数量
        results_count = len(rsp.output.results) if rsp.output and hasattr(rsp.output, 'results') and rsp.output.results else 0
        logger.info(f"结果数量: {results_count}")

        if rsp.status_code == HTTPStatus.OK:
            # 检查 code 字段是否有错误（即使 status_code 是 200）
            if hasattr(rsp, 'code') and rsp.code and rsp.code != 'Success':
                logger.error(f"API返回错误码: {rsp.code}")
                logger.error(f"错误信息: {getattr(rsp, 'message', '未知错误')}")
                return None, None
            
            # 检查 results 是否为空
            if not rsp.output.results:
                logger.error("❌ API返回结果为空！任务可能超时或失败")
                logger.error(f"完整响应: status_code={rsp.status_code}, code={getattr(rsp, 'code', 'N/A')}, message={getattr(rsp, 'message', 'N/A')}")
                return None, None
            
            # 有结果才访问
            image_url = rsp.output.results[0].url
            logger.info(f"✅ 图生图成功，图片URL: {image_url}")
            
            image_path = download_file_from_url(
                image_url,
                save_dir,
                f"wan25_i2i_{int(time.time())}.png"
            )
            return image_path, image_url
        else:
            logger.error(f'❌ HTTP请求失败: status_code={rsp.status_code}, code={rsp.code}, message={rsp.message}')
            return None, None

    except Exception as e:
        logger.error(f"❌ 生成异常: {e}")
        logger.exception(e)  # 打印完整堆栈
        return None, None


# ============================================
# 万象2.1 图片编辑
# ============================================

def edit_image_wan_v21(
        api_key: str,
        base_image_url: str,
        prompt: str,
        function: str = "remove_watermark",
        mask_image_url: str = None,
        save_dir: str = None
) -> Union[tuple[str, str], tuple[None, None]]:
    """万象2.1图片编辑

    Args:
        api_key: API密钥
        base_image_url: 输入图片URL
        prompt: 编辑提示词
        function: 编辑功能（remove_watermark/colorization等）
        mask_image_url: 蒙版图片URL（可选）
        save_dir: 保存目录

    Returns:
        (图片路径列表, 图片URL列表)
    """
    save_dir = save_dir or config.PICTURE_RESULTS_DIR

    logger.info(f"万象2.1图片编辑 - 功能: {function}")
    logger.info(f"输入图片: {base_image_url}")
    logger.info(f"提示词: {prompt}")

    try:
        params = {
            'api_key': api_key,
            'model': 'wanx2.1-imageedit',
            'function': function,
            'prompt': prompt,
            'base_image_url': base_image_url,
            'n': 1,
        }

        if mask_image_url:
            params['mask_image_url'] = mask_image_url

        rsp = ImageSynthesis.call(**params)

        # 详细的响应日志
        logger.info(f"API响应状态: {rsp.status_code}")
        logger.info(f"API响应码: {getattr(rsp, 'code', 'N/A')}")
        logger.info(f"API响应消息: {getattr(rsp, 'message', 'N/A')}")
        
        # 检查结果数量
        results_count = len(rsp.output.results) if rsp.output and hasattr(rsp.output, 'results') and rsp.output.results else 0
        logger.info(f"结果数量: {results_count}")

        if rsp.status_code == HTTPStatus.OK:
            # 检查 code 字段是否有错误（即使 status_code 是 200）
            if hasattr(rsp, 'code') and rsp.code and rsp.code != 'Success':
                logger.error(f"API返回错误码: {rsp.code}")
                logger.error(f"错误信息: {getattr(rsp, 'message', '未知错误')}")
                return None, None
            
            # 检查 results 是否为空
            if not rsp.output.results:
                logger.error("❌ API返回结果为空！任务可能超时或失败")
                logger.error(f"完整响应: status_code={rsp.status_code}, code={getattr(rsp, 'code', 'N/A')}, message={getattr(rsp, 'message', 'N/A')}")
                return None, None
            
            # 有结果才访问
            image_url = rsp.output.results[0].url
            logger.info(f"✅ 编辑成功，图片URL: {image_url}")
            
            image_path = download_file_from_url(
                image_url,
                save_dir,
                f"wan21_edit_{int(time.time())}.png"
            )
            return image_path, image_url
        else:
            logger.error(f'❌ HTTP请求失败: status_code={rsp.status_code}, code={rsp.code}, message={rsp.message}')
            return None, None

    except Exception as e:
        logger.error(f"❌ 编辑异常: {e}")
        logger.exception(e)  # 打印完整堆栈
        return None, None


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    from config.logging_config import setup_logging
    import webbrowser

    # 初始化日志
    setup_logging()

    # 加载环境变量
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../env/default.env"))
    api_key = os.getenv("DASHSCOPE_API_KEY")

    # 检查API密钥
    if not api_key:
        raise ValueError("未找到DashScope API密钥，请检查环境变量配置")

    # 测试万象2.5文生图
    print("=" * 50)
    print("测试 sync_t2i_wan_v25 (万象2.5文生图)")
    print("=" * 50)

    prompt2 = TEST_T2I_PROMPT_003

    image_path, image_url = sync_t2i_wan_v25(
        api_key=api_key,
        prompt=prompt2,
        negative_prompt="",
        size="1024*1024",
        n=1
    )

    if image_url and image_path:
        print(f"✅ 生成成功!")
        print(f"   图片URL: {image_url}")
        print(f"   本地路径: {image_path}")
        # 去掉查询参数
        clean_image_path = image_path.split('?')[0]
        # 检查文件是否存在
        if os.path.exists(clean_image_path):
            webbrowser.open(f"file://{clean_image_path}")
        else:
            print("文件不存在，请检查路径是否正确。")

    else:
        print("❌ 生成失败")

