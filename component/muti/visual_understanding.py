#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 图像/视频
Output: 理解结果文本
Pos: 视觉理解功能
"""

"""
视觉理解模块 - 图片和视频理解
使用通义千问视觉理解模型 (Qwen-VL)
"""
import requests
from pathlib import Path
from typing import Union, List
from config.logging_config import get_logger
from util.util_url import upload_file_to_oss
import math
# 使用以下命令安装Pillow库：pip install Pillow
from PIL import Image

logger = get_logger(__name__)


def token_calculate(image_path):
    # 打开指定的PNG图片文件
    image = Image.open(image_path)

    # 获取图片的原始尺寸
    height = image.height
    width = image.width

    # Qwen3-VL、qwen-vl-max-0813以后和qwen-vl-plus-0815以后更新的模型：将宽高都调整为32的整数倍以后更新的模型：将宽高都调整为32的整数倍
    # 其余模型：将宽高都调整为28的整数倍
    h_bar = round(height / 32) * 32
    w_bar = round(width / 32) * 32

    # 图像的Token下限：4个Token
    min_pixels = 32 * 32 * 4
    # 图像的Token上限：1280个Token
    max_pixels = 1280 * 32 * 32

    # 对图像进行缩放处理，调整像素的总数在范围[min_pixels,max_pixels]内
    if h_bar * w_bar > max_pixels:
        # 计算缩放因子beta，使得缩放后的图像总像素数不超过max_pixels
        beta = math.sqrt((height * width) / max_pixels)
        # 重新计算调整后的宽高，对于Qwen3-VL、qwen-vl-max-0813以后及qwen-vl-plus-0815以后更新的模型：将宽高都调整为32的整数倍，对于其他模型，确保为28的整数倍
        h_bar = math.floor(height / beta / 32) * 32
        w_bar = math.floor(width / beta / 32) * 32
    elif h_bar * w_bar < min_pixels:
        # 计算缩放因子beta，使得缩放后的图像总像素数不低于min_pixels
        beta = math.sqrt(min_pixels / (height * width))
        # 重新计算调整后的高度，对于Qwen3-VL、qwen-vl-max-0813以后及qwen-vl-plus-0815以后更新的模型，确保为32的整数倍，对于其他模型，确保为28的整数倍
        h_bar = math.ceil(height * beta / 32) * 32
        w_bar = math.ceil(width * beta / 32) * 32

    print(f"缩放后的图像尺寸为：高度为{h_bar}，宽度为{w_bar}")

    # 计算图像的Token数：对于Qwen3-VL、qwen-vl-max-0813以后及qwen-vl-plus-0815以后更新的模型，Token数 = 总像素除以32 * 32，对于其他模型，Token数 = 总像素除以28 * 28
    token = int((h_bar * w_bar) / (32 * 32))
    # 系统会自动添加<|vision_bos|>和<|vision_eos|>视觉标记（各计1个Token）
    print(f"图像的Token数为{token + 2}")


class VisualUnderstandingClient:
    """视觉理解客户端（图片、视频理解）"""
    
    def __init__(self, api_key: str):
        """
        初始化客户端
        
        Args:
            api_key: DashScope API密钥
        """
        self.api_key = api_key
        self.base_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
        self.default_model = "qwen-vl-plus"
        
        logger.info("VisualUnderstandingClient 初始化完成")
    
    def _ensure_url(self, file_path: str) -> str:
        """
        确保文件路径为URL（本地文件自动上传到OSS）
        
        Args:
            file_path: 文件路径或URL
            
        Returns:
            文件的公网URL
        """
        # 如果已经是URL，直接返回
        if file_path.startswith("http://") or file_path.startswith("https://"):
            return file_path
        
        # 本地文件，上传到OSS
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        logger.info(f"检测到本地文件，上传到OSS: {file_path.name}")
        url = upload_file_to_oss(str(file_path), expire_time=300)
        logger.info(f"OSS上传成功: {url}")
        
        return url
    
    def _call_api(self, messages: list, model: str = None) -> dict:
        """
        调用DashScope API
        
        Args:
            messages: 消息列表
            model: 模型名称
            
        Returns:
            API响应
        """
        if model is None:
            model = self.default_model
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "input": {
                "messages": messages
            }
        }
        
        logger.info(f"调用视觉理解API - 模型: {model}")
        
        response = requests.post(
            self.base_url,
            headers=headers,
            json=payload,
            timeout=60
        )
        
        response.raise_for_status()
        result = response.json()
        
        # 记录完整响应到日志
        logger.info(f"API响应: {result}")
        
        return result
    
    def _extract_text(self, response: dict) -> str:
        """
        从API响应中提取文本内容
        
        Args:
            response: API响应
            
        Returns:
            提取的文本
        """
        try:
            return response["output"]["choices"][0]["message"]["content"][0]["text"]
        except (KeyError, IndexError) as e:
            logger.error(f"解析响应失败: {e}")
            return ""
    
    def understand_image(
        self, 
        image_sources: Union[str, List[str]], 
        prompt: str,
        model: str = None
    ) -> str:
        """
        图片理解
        
        Args:
            image_sources: 图片URL或本地路径（单个字符串或列表）
            prompt: 提问内容
            model: 模型名称（默认qwen-vl-plus）
            
        Returns:
            理解结果文本
            
        Examples:
            # 单图理解
            text = client.understand_image("image.jpg", "描述图片内容")
            
            # 多图理解
            text = client.understand_image(
                ["image1.jpg", "image2.jpg"], 
                "这两张图片有什么区别？"
            )
        """
        # 统一转为列表
        if isinstance(image_sources, str):
            image_sources = [image_sources]
        
        logger.info(f"图片理解 - 图片数量: {len(image_sources)}")
        
        # 确保所有图片都是URL
        image_urls = [self._ensure_url(img) for img in image_sources]
        
        # 构建消息内容
        content = []
        for url in image_urls:
            content.append({"image": url})
        content.append({"text": prompt})
        
        messages = [
            {
                "role": "user",
                "content": content
            }
        ]
        
        # 调用API
        response = self._call_api(messages, model)
        
        # 提取文本
        text = self._extract_text(response)
        
        logger.info(f"图片理解完成 - 输出长度: {len(text)} 字符")
        
        return text
    
    def understand_video(
        self, 
        video_source: str, 
        prompt: str,
        model: str = None
    ) -> str:
        """
        视频理解
        
        Args:
            video_source: 视频URL或本地路径
            prompt: 提问内容
            model: 模型名称（默认qwen-vl-plus）
            
        Returns:
            理解结果文本
            
        Examples:
            # 视频理解
            text = client.understand_video("video.mp4", "描述视频中发生了什么")
            
            # 视频问答
            text = client.understand_video("video.mp4", "视频中有几个人？")
        """
        logger.info(f"视频理解 - 视频: {Path(video_source).name}")
        
        # 确保视频是URL
        video_url = self._ensure_url(video_source)
        
        # 构建消息内容
        content = [
            {"video": video_url},
            {"text": prompt}
        ]
        
        messages = [
            {
                "role": "user",
                "content": content
            }
        ]
        
        # 调用API
        response = self._call_api(messages, model)
        
        # 提取文本
        text = self._extract_text(response)
        
        logger.info(f"视频理解完成 - 输出长度: {len(text)} 字符")
        
        return text


def understand_image(
    api_key: str,
    image_sources: Union[str, List[str]],
    prompt: str,
    model: str = None
) -> str:
    """
    图片理解（便捷函数）
    
    Args:
        api_key: DashScope API密钥
        image_sources: 图片URL或本地路径（单个或列表）
        prompt: 提问内容
        model: 模型名称（默认qwen-vl-plus）
        
    Returns:
        理解结果文本
    """
    client = VisualUnderstandingClient(api_key)
    return client.understand_image(image_sources, prompt, model)


def understand_video(
    api_key: str,
    video_source: str,
    prompt: str,
    model: str = None
) -> str:
    """
    视频理解（便捷函数）
    
    Args:
        api_key: DashScope API密钥
        video_source: 视频URL或本地路径
        prompt: 提问内容
        model: 模型名称（默认qwen-vl-plus）
        
    Returns:
        理解结果文本
    """
    client = VisualUnderstandingClient(api_key)

    return client.understand_video(video_source, prompt, model)




if __name__ == "__main__":
    import os
    import time  # 添加时间模块
    from dotenv import load_dotenv
    from config.logging_config import setup_logging

    setup_logging()

    logger.info("📋 初始化配置参数")
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../env/default.env"))
    api_key = os.getenv("DASHSCOPE_API_KEY")

    # 检查API密钥是否成功加载
    if not api_key:
        raise ValueError("未找到DashScope API密钥，请检查环境变量DASHSCOPE_API_KEY是否正确配置")

    # 创建客户端
    client = VisualUnderstandingClient(api_key)

    print("=" * 80)
    print("视觉理解示例")
    print("=" * 80)

    test_image_path = "/Users/thomaschan/Code/My_files/my_files/my_scripts/爆款复刻20251106/segment_test/frames/segment_001_segment_001_frame_0001.jpg"

    # 记录开始时间
    start_time = time.time()

    # 计算图片token
    token_calculate(test_image_path)
    # 记录结束时间并计算运行时间
    end_time = time.time()
    print(f"token_calculate 运行时间: {end_time - start_time:.4f} 秒")

    # 示例1: 图片理解（需要提供实际图片路径）
    start_time = time.time()  # 记录开始时间
    result = client.understand_image(test_image_path, "描述这张图片的内容")
    end_time = time.time()  # 记录结束时间
    print(f"图片理解运行时间: {end_time - start_time:.4f} 秒")
    print(f"\n图片理解结果:\n{result}\n")

    # 示例2: 视频理解（需要提供实际视频路径）
    # start_time = time.time()  # 记录开始时间
    # result = client.understand_video("path/to/video.mp4", "描述视频中发生了什么")
    # end_time = time.time()  # 记录结束时间
    # print(f"视频理解运行时间: {end_time - start_time:.4f} 秒")
    # print(f"\n视频理解结果:\n{result}\n")


