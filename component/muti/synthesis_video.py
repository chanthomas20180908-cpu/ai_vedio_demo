"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 文本/图片
Output: 视频文件
Pos: 视频合成功能
"""

import os
import json
import time
from typing import Optional, Tuple, Dict, Any, List
import requests
from datetime import datetime
import config.config as cfg
from dotenv import load_dotenv
from config.logging_config import get_logger
from pathlib import Path

from util.util_file import download_file_from_url, split_mp3, merge_videos
from util.util_url import upload_file_to_oss

import base64
import os
from http import HTTPStatus
from dashscope import VideoSynthesis
import mimetypes
import dashscope


# 项目启动时初始化日志
logger = get_logger(__name__)




def _log_timing_info(result: Dict[Any, Any], model_name: str = ""):
    """
    统一记录时间信息

    Args:
        result (Dict[Any, Any]): 任务结果数据
        model_name (str, optional): 模型名称
    """
    try:
        output = result.get("output", {})
        submit_time_str = output.get("submit_time")
        end_time_str = output.get("end_time")

        if model_name:
            logger.info(f"[{model_name}] 任务完成")

        # 时间信息
        if submit_time_str and end_time_str:
            time_format = "%Y-%m-%d %H:%M:%S.%f"
            submit_time = datetime.strptime(submit_time_str, time_format)
            end_time = datetime.strptime(end_time_str, time_format)
            consume_time = end_time - submit_time
            logger.info(f"耗时: {consume_time}")

        # 视频信息（如果存在）
        usage = result.get("usage", {})
        video_duration = usage.get("video_duration")
        if video_duration:
            logger.info(f"视频时长: {video_duration}秒")

        # 实际提示词（如果存在）
        actual_prompt = output.get("actual_prompt")
        if actual_prompt:
            logger.info(f"实际使用的提示词: {actual_prompt}")

    except Exception as e:
        logger.warning(f"解析时间信息失败: {e}")


class VideoModelClient:
    """视频模型客户端基类"""

    def __init__(self, api_key: str):
        """
        初始化视频模型客户端

        Args:
            api_key (str): DashScope API密钥
        """
        self.api_key = api_key
        self.base_headers = {"Authorization": f"Bearer {api_key}"}

    def _post_request(self, url: str, data: Dict[Any, Any], headers: Dict[str, str]) -> Optional[Dict[Any, Any]]:
        """
        发送POST请求

        Args:
            url (str): 请求URL
            data (Dict[Any, Any]): 请求数据
            headers (Dict[str, str]): 请求头

        Returns:
            Optional[Dict[Any, Any]]: 响应数据，失败时返回None
        """
        try:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code != 200:
                logger.error(f"请求失败: {response.status_code} - {response.text}")
                return None
            return response.json()
        except Exception as e:
            logger.error(f"请求异常: {e}", exc_info=True)
            return None

    def _get_request(self, url: str) -> Optional[Dict[Any, Any]]:
        """
        发送GET请求

        Args:
            url (str): 请求URL

        Returns:
            Optional[Dict[Any, Any]]: 响应数据，失败时返回None
        """
        try:
            response = requests.get(url, headers=self.base_headers)
            if response.status_code != 200:
                logger.error(f"请求失败: {response.status_code} - {response.text}")
                return None
            return response.json()
        except Exception as e:
            logger.error(f"请求异常: {e}", exc_info=True)
            return None

    def _wait_for_completion(self, task_url: str, check_interval: int = cfg.INTERVAL_TIME) -> Optional[Dict[Any, Any]]:
        """
        等待任务完成

        Args:
            task_url (str): 任务查询URL
            check_interval (int, optional): 查询间隔时间(秒). Defaults to 20.

        Returns:
            Optional[Dict[Any, Any]]: 完成的任务结果，失败时返回None
        """
        logger.info("开始轮询任务状态...")

        while True:
            time.sleep(check_interval)
            logger.info("检查任务状态...")

            result = self._get_request(task_url)
            if not result:
                return None

            status = result.get("output", {}).get("task_status")
            logger.info(f"当前状态: {status}")

            if status == "SUCCEEDED":
                logger.info("任务完成成功")
                return result
            elif status in ["FAILED", "CANCELED"]:
                logger.error(f"任务失败: {json.dumps(result, indent=2, ensure_ascii=False)}")
                return None
            elif status in ["PENDING", "RUNNING"]:
                logger.info("任务进行中，继续等待...")
            else:
                logger.warning(f"未知状态: {status}")


class Wan22S2VClient(VideoModelClient):
    """
    万象数字人视频生成客户端
    image_url
    audio_url
    resolution
    """

    def __init__(self, api_key: str):
        """
        初始化万象数字人视频生成客户端

        Args:
            api_key (str): DashScope API密钥
        """
        super().__init__(api_key)
        self.detect_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/image2video/face-detect"
        self.submit_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/image2video/video-synthesis/"
        self.task_url = "https://dashscope.aliyuncs.com/api/v1/tasks/{}"

    def detect_face(self, **kwargs) -> bool:
        """
        检测图像中的人脸

        Args:
            **kwargs: 检测参数
                image_url (str): 图像URL

        Returns:
            bool: 检测是否通过
        """
        image_url = kwargs.get("image_url")
        if not image_url:
            logger.error("缺少必需参数: image_url")
            return False

        headers = {
            **self.base_headers,
            "Content-Type": "application/json",
            "X-DashScope-OssResourceResolve": "enable"
        }

        payload = {
            "model": "wan2.2-s2v-detect",
            "input": {"image_url": image_url}
        }

        logger.info("开始人脸检测...")
        result = self._post_request(self.detect_url, payload, headers)

        if not result:
            return False

        check_pass = result.get("output", {}).get("check_pass", False)
        logger.info(f"人脸检测结果: {'通过' if check_pass else '未通过'}")
        return check_pass

    def generate_video(self, **kwargs) -> Optional[str]:
        """
        生成数字人视频

        Args:
            **kwargs: 生成参数
                image_url (str): 人物图像URL
                audio_url (str): 音频URL
                resolution (str, optional): 视频分辨率. Defaults to "480P".

        Returns:
            Optional[str]: 生成的视频URL，失败时返回None
        """
        image_url = kwargs.get("image_url")
        audio_url = kwargs.get("audio_url")
        resolution = kwargs.get("resolution", "480P")

        # 参数校验
        if not image_url:
            logger.error("缺少必需参数: image_url")
            return None
        if not audio_url:
            logger.error("缺少必需参数: audio_url")
            return None

        # 先进行人脸检测
        if not self.detect_face(image_url=image_url):
            logger.error("人脸检测未通过，终止视频生成")
            return None

        headers = {
            **self.base_headers,
            "Content-Type": "application/json",
            "X-DashScope-Async": "enable",
            "X-DashScope-OssResourceResolve": "enable"
        }

        payload = {
            "model": "wan2.2-s2v",
            "input": {"image_url": image_url, "audio_url": audio_url},
            "parameters": {"resolution": resolution}
        }

        logger.info("提交视频生成任务...")
        logger.info(f"图片URL: {image_url}")
        logger.info(f"音频URL: {audio_url}")

        result = self._post_request(self.submit_url, payload, headers)
        if not result:
            return None

        task_id = result.get("output", {}).get("task_id")
        if not task_id:
            logger.error("未获取到任务ID")
            return None

        logger.info(f"任务ID: {task_id}")

        # 等待任务完成
        task_url = self.task_url.format(task_id)
        completion_result = self._wait_for_completion(task_url)

        if not completion_result:
            return None

        # 获取视频URL
        video_url = completion_result.get("output", {}).get("results", {}).get("video_url")
        if video_url:
            logger.info(f"视频生成完成: {video_url}")
            _log_timing_info(completion_result, "Wan22S2V")

        return video_url


class VideoRetalkClient(VideoModelClient):
    """VideoRetalk视频合成客户端"""

    def __init__(self, api_key: str):
        """
        初始化VideoRetalk视频合成客户端

        Args:
            api_key (str): DashScope API密钥
        """
        super().__init__(api_key)
        self.submit_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/image2video/video-synthesis/"
        self.task_url = "https://dashscope.aliyuncs.com/api/v1/tasks/{}"

    def synthesize_video(self, **kwargs) -> Optional[str]:
        """
        合成视频

        Args:
            **kwargs: 合成参数
                video_url (str): 原始视频URL
                audio_url (str): 音频URL
                ref_image_url (str, optional): 参考图像URL. Defaults to "".
                video_extension (bool, optional): 是否扩展视频. Defaults to False.

        Returns:
            Optional[str]: 合成后的视频URL，失败时返回None
        """
        video_url = kwargs.get("video_url")
        audio_url = kwargs.get("audio_url")
        ref_image_url = kwargs.get("ref_image_url", "")
        video_extension = kwargs.get("video_extension", False)

        # 参数校验
        if not video_url:
            logger.error("缺少必需参数: video_url")
            return None
        if not audio_url:
            logger.error("缺少必需参数: audio_url")
            return None

        headers = {
            **self.base_headers,
            "Content-Type": "application/json",
            "X-DashScope-Async": "enable"
        }

        payload = {
            "model": "videoretalk",
            "input": {
                "video_url": video_url,
                "audio_url": audio_url,
                "ref_image_url": ref_image_url
            },
            "parameters": {
                "video_extension": video_extension
            }
        }

        logger.info("提交VideoRetalk任务...")
        logger.info(f"视频URL: {video_url}")
        logger.info(f"音频URL: {audio_url}")

        result = self._post_request(self.submit_url, payload, headers)
        if not result:
            return None

        task_id = result.get("output", {}).get("task_id")
        if not task_id:
            logger.error("未获取到任务ID")
            return None

        logger.info(f"任务ID: {task_id}")
        logger.info(f"任务提交成功: {json.dumps(result, indent=2, ensure_ascii=False)}")

        # 等待任务完成
        task_url = self.task_url.format(task_id)
        completion_result = self._wait_for_completion(task_url)

        if not completion_result:
            return None

        # 获取视频URL
        video_url = completion_result.get("output", {}).get("video_url")
        if video_url:
            logger.info("视频合成完成")
            logger.info(f"视频下载地址: {video_url}")
            _log_timing_info(completion_result, "VideoRetalk")

        return video_url


class LivePortraitClient(VideoModelClient):
    """LivePortrait视频生成客户端"""

    def __init__(self, api_key: str):
        """
        初始化LivePortrait视频生成客户端

        Args:
            api_key (str): DashScope API密钥
        """
        super().__init__(api_key)
        self.detect_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/image2video/face-detect"
        self.submit_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/image2video/video-synthesis/"
        self.task_url = "https://dashscope.aliyuncs.com/api/v1/tasks/{}"

    def detect_face(self, **kwargs) -> bool:
        """
        检测图像中的人脸

        Args:
            **kwargs: 检测参数
                image_url (str): 图像URL

        Returns:
            bool: 检测是否通过
        """
        image_url = kwargs.get("image_url")
        if not image_url:
            logger.error("缺少必需参数: image_url")
            return False

        headers = {
            **self.base_headers,
            "Content-Type": "application/json"
        }

        payload = {
            "model": "liveportrait-detect",
            "input": {"image_url": image_url}
        }

        logger.info("开始LivePortrait人脸检测...")
        result = self._post_request(self.detect_url, payload, headers)

        if not result:
            return False

        check_pass = result.get("output", {}).get("pass", False)
        logger.info(f"人脸检测结果: {'通过' if check_pass else '未通过'}")
        return check_pass

    def generate_video(self, **kwargs) -> Optional[str]:
        """
        生成LivePortrait视频

        Args:
            **kwargs: 生成参数
                image_url (str): 人物图像URL
                audio_url (str): 音频URL
                template_id (str, optional): 模板ID. Defaults to "normal".
                eye_move_freq (float, optional): 眼睛移动频率. Defaults to 0.5.
                video_fps (int, optional): 视频帧率. Defaults to 30.
                mouth_move_strength (float, optional): 嘴部运动强度. Defaults to 1.0.
                paste_back (bool, optional): 是否粘贴回原图. Defaults to True.
                head_move_strength (float, optional): 头部运动强度. Defaults to 0.7.

        Returns:
            Optional[str]: 生成的视频URL，失败时返回None
        """
        image_url = kwargs.get("image_url")
        audio_url = kwargs.get("audio_url")
        template_id = kwargs.get("template_id", "normal")
        eye_move_freq = kwargs.get("eye_move_freq", 0.5)
        video_fps = kwargs.get("video_fps", 30)
        mouth_move_strength = kwargs.get("mouth_move_strength", 1.0)
        paste_back = kwargs.get("paste_back", True)
        head_move_strength = kwargs.get("head_move_strength", 0.7)

        # 参数校验
        if not image_url:
            logger.error("缺少必需参数: image_url")
            return None
        if not audio_url:
            logger.error("缺少必需参数: audio_url")
            return None

        # 先进行人脸检测
        if not self.detect_face(image_url=image_url):
            logger.error("人脸检测未通过，终止视频生成")
            return None

        headers = {
            **self.base_headers,
            "Content-Type": "application/json",
            "X-DashScope-Async": "enable"
        }

        payload = {
            "model": "liveportrait",
            "input": {
                "image_url": image_url,
                "audio_url": audio_url
            },
            "parameters": {
                "template_id": template_id,
                "eye_move_freq": eye_move_freq,
                "video_fps": video_fps,
                "mouth_move_strength": mouth_move_strength,
                "paste_back": paste_back,
                "head_move_strength": head_move_strength
            }
        }

        logger.info("提交LivePortrait视频生成任务...")
        logger.info(f"图片URL: {image_url}")
        logger.info(f"音频URL: {audio_url}")
        logger.info(f"参数: template={template_id}, fps={video_fps}, mouth_strength={mouth_move_strength}")

        result = self._post_request(self.submit_url, payload, headers)
        if not result:
            return None

        task_id = result.get("output", {}).get("task_id")
        if not task_id:
            logger.error("未获取到任务ID")
            return None

        logger.info(f"任务ID: {task_id}")

        # 等待任务完成
        task_url = self.task_url.format(task_id)
        completion_result = self._wait_for_completion(task_url)

        if not completion_result:
            return None

        # 获取视频URL
        video_url = completion_result.get("output", {}).get("results", {}).get("video_url")
        if video_url:
            logger.info(f"LivePortrait视频生成完成: {video_url}")
            _log_timing_info(completion_result, "LivePortrait")

        return video_url


class Wanx21I2VTurboClient(VideoModelClient):
    """Wanx2.1-I2V-Turbo图生视频客户端"""

    def __init__(self, api_key: str):
        """
        初始化Wanx2.1-I2V-Turbo视频生成客户端

        Args:
            api_key (str): DashScope API密钥
        """
        super().__init__(api_key)
        self.submit_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/video-generation/video-synthesis"
        self.task_url = "https://dashscope.aliyuncs.com/api/v1/tasks/{}"

    def generate_video(self, **kwargs) -> Optional[str]:
        """
        使用wanx2.1-i2v-turbo模型从图片生成视频

        Args:
            **kwargs: 生成参数
                img_url (str): 图片URL
                template (str): 动作模板，例如 "flying"
                resolution (str, optional): 视频分辨率. Defaults to "720P".

        Returns:
            Optional[str]: 生成的视频URL，失败时返回None
        """
        img_url = kwargs.get("img_url")
        template = kwargs.get("template")
        resolution = kwargs.get("resolution", "720P")

        # 参数校验
        if not img_url:
            logger.error("缺少必需参数: img_url")
            return None
        if not template:
            logger.error("缺少必需参数: template")
            return None

        headers = {
            **self.base_headers,
            "Content-Type": "application/json",
            "X-DashScope-Async": "enable"
        }

        payload = {
            "model": "wanx2.1-i2v-turbo",
            "input": {
                "img_url": img_url,
                "template": template
            },
            "parameters": {
                "resolution": resolution
            }
        }

        logger.info("提交Wanx2.1-I2V-Turbo视频生成任务...")
        logger.info(f"图片URL: {img_url}")
        logger.info(f"动作模板: {template}")
        logger.info(f"分辨率: {resolution}")

        result = self._post_request(self.submit_url, payload, headers)
        if not result:
            return None

        task_id = result.get("output", {}).get("task_id")
        if not task_id:
            logger.error("未获取到任务ID")
            return None

        logger.info(f"任务ID: {task_id}")

        # 等待任务完成
        task_url = self.task_url.format(task_id)
        completion_result = self._wait_for_completion(task_url)

        if not completion_result:
            return None

        # 获取视频URL
        video_url = completion_result.get("output", {}).get("video_url")
        if video_url:
            logger.info(f"Wanx2.1-I2V-Turbo视频生成完成: {video_url}")
            _log_timing_info(completion_result, "Wanx21I2VTurbo")

        return video_url


class Wanx21I2VPlusClient(VideoModelClient):
    """Wanx2.1-I2V-Turbo图生视频客户端"""

    def __init__(self, api_key: str):
        """
        初始化Wanx2.1-I2V-Turbo视频生成客户端

        Args:
            api_key (str): DashScope API密钥
        """
        super().__init__(api_key)
        self.submit_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/video-generation/video-synthesis"
        self.task_url = "https://dashscope.aliyuncs.com/api/v1/tasks/{}"

    def generate_video(self, **kwargs) -> Optional[str]:
        """
        使用wanx2.1-i2v-turbo模型从图片生成视频

        Args:
            **kwargs: 生成参数
                img_url (str): 图片URL
                template (str): 动作模板，例如 "flying"
                resolution (str, optional): 视频分辨率. Defaults to "720P".

        Returns:
            Optional[str]: 生成的视频URL，失败时返回None
        """
        img_url = kwargs.get("img_url")
        template = kwargs.get("template")
        resolution = kwargs.get("resolution", "720P")

        # 参数校验
        if not img_url:
            logger.error("缺少必需参数: img_url")
            return None
        if not template:
            logger.error("缺少必需参数: template")
            return None

        headers = {
            **self.base_headers,
            "Content-Type": "application/json",
            "X-DashScope-Async": "enable"
        }

        payload = {
            "model": "wanx2.1-i2v-plus",
            "input": {
                "img_url": img_url,
                "template": template
            },
            "parameters": {
                "resolution": resolution
            }
        }

        logger.info("提交Wanx2.1-I2V-Plus视频生成任务...")
        logger.info(f"图片URL: {img_url}")
        logger.info(f"动作模板: {template}")
        logger.info(f"分辨率: {resolution}")

        result = self._post_request(self.submit_url, payload, headers)
        if not result:
            return None

        task_id = result.get("output", {}).get("task_id")
        if not task_id:
            logger.error("未获取到任务ID")
            return None

        logger.info(f"任务ID: {task_id}")

        # 等待任务完成
        task_url = self.task_url.format(task_id)
        completion_result = self._wait_for_completion(task_url)

        if not completion_result:
            return None

        # 获取视频URL
        video_url = completion_result.get("output", {}).get("video_url")
        if video_url:
            logger.info(f"Wanx2.1-I2V-PLus视频生成完成: {video_url}")
            _log_timing_info(completion_result, "Wanx21I2VPlus")

        return video_url


class Wanx21KF2VPlusClient(VideoModelClient):
    """Wanx2.1-I2V-Turbo图生视频客户端"""

    def __init__(self, api_key: str):
        """
        初始化Wanx2.1-KF2V-Turbo视频生成客户端

        Args:
            api_key (str): DashScope API密钥
        """
        super().__init__(api_key)
        self.submit_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/image2video/video-synthesis"
        self.task_url = "https://dashscope.aliyuncs.com/api/v1/tasks/{}"

    def generate_video(self, **kwargs) -> Optional[str]:
        """
        使用wanx2.1-i2v-turbo模型从图片生成视频

        Args:
            **kwargs: 生成参数
                img_url (str): 图片URL
                template (str): 动作模板，例如 "flying"
                resolution (str, optional): 视频分辨率. Defaults to "720P".

        Returns:
            Optional[str]: 生成的视频URL，失败时返回None
        """
        img_url = kwargs.get("img_url")
        template = kwargs.get("template")
        resolution = kwargs.get("resolution", "720P")

        # 参数校验
        if not img_url:
            logger.error("缺少必需参数: img_url")
            return None
        if not template:
            logger.error("缺少必需参数: template")
            return None

        headers = {
            **self.base_headers,
            "Content-Type": "application/json",
            "X-DashScope-Async": "enable"
        }

        payload = {
            "model": "wanx2.1-kf2v-plus",
            "input": {
                "first_frame_url": img_url,
                "template": template
            },
            "parameters": {
                "resolution": resolution
            }
        }

        logger.info("提交Wanx2.1-KF2V-Plus视频生成任务...")
        logger.info(f"图片URL: {img_url}")
        logger.info(f"动作模板: {template}")
        logger.info(f"分辨率: {resolution}")

        result = self._post_request(self.submit_url, payload, headers)
        if not result:
            return None

        task_id = result.get("output", {}).get("task_id")
        if not task_id:
            logger.error("未获取到任务ID")
            return None

        logger.info(f"任务ID: {task_id}")

        # 等待任务完成
        task_url = self.task_url.format(task_id)
        completion_result = self._wait_for_completion(task_url)

        if not completion_result:
            return None

        # 获取视频URL
        video_url = completion_result.get("output", {}).get("video_url")
        if video_url:
            logger.info(f"Wanx2.1-I2V-PLus视频生成完成: {video_url}")
            _log_timing_info(completion_result, "Wanx21I2VPlus")

        return video_url


class Wanx21VacePlusClient(VideoModelClient):
    """Wanx2.1-Vace-Plus视频生成客户端"""

    def __init__(self, api_key: str):
        """
        初始化Wanx2.1-Vace-Plus视频生成客户端

        Args:
            api_key (str): DashScope API密钥
        """
        super().__init__(api_key)
        self.submit_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/video-generation/video-synthesis"
        self.task_url = "https://dashscope.aliyuncs.com/api/v1/tasks/{}"

    def generate_video(self, function_option: str, **kwargs) -> Optional[str]:
        """
        根据不同功能选项生成视频

        Args:
            function_option (str): 功能选项，可选值包括:
                - "image_reference": 图像参考生视频
                - "video_repainting": 视频重绘
                - "video_edit": 视频编辑
                - "video_extension": 视频扩展
                - "video_outpainting": 视频外绘
            **kwargs: 根据不同功能选项需要的参数:
                image_reference:
                    - prompt (str): 视频描述文本
                    - ref_images_url (list): 参考图像URL列表
                    - obj_or_bg (list, optional): 对象或背景处理选项. Defaults to ["obj", "bg"].
                    - size (str, optional): 视频尺寸. Defaults to "1280*720".
                video_repainting:
                    - prompt (str): 视频描述文本
                    - video_url (str): 原始视频URL
                    - control_condition (str, optional): 控制条件. Defaults to "depth".
                video_edit:
                    - prompt (str): 视频描述文本
                    - mask_image_url (str): 遮罩图像URL
                    - video_url (str): 原始视频URL
                    - mask_frame_id (int): 遮罩帧ID
                    - mask_type (str, optional): 遮罩类型. Defaults to "tracking".
                    - expand_ratio (float, optional): 扩展比例. Defaults to 0.05.
                video_extension:
                    - prompt (str): 视频描述文本
                    - first_clip_url (str): 第一个视频片段URL
                video_outpainting:
                    - prompt (str): 视频描述文本
                    - video_url (str): 原始视频URL
                    - top_scale (float, optional): 顶部扩展比例. Defaults to 1.5.
                    - bottom_scale (float, optional): 底部扩展比例. Defaults to 1.5.
                    - left_scale (float, optional): 左侧扩展比例. Defaults to 1.5.
                    - right_scale (float, optional): 右侧扩展比例. Defaults to 1.5.

        Returns:
            Optional[str]: 生成的视频URL，失败时返回None
        """
        headers = {
            **self.base_headers,
            "Content-Type": "application/json",
            "X-DashScope-Async": "enable"
        }

        # 根据功能选项构建payload
        payload = {
            "model": "wanx2.1-vace-plus",
            "input": {
                "function": function_option
            },
            "parameters": {}
        }

        # 根据不同的功能选项设置输入参数和参数
        if function_option == "image_reference":
            payload["input"]["prompt"] = kwargs.get("prompt")
            payload["input"]["ref_images_url"] = kwargs.get("ref_images_url")
            payload["parameters"]["obj_or_bg"] = kwargs.get("obj_or_bg", ["obj", "bg"])
            payload["parameters"]["size"] = kwargs.get("size", "1280*720")

        elif function_option == "video_repainting":
            payload["input"]["prompt"] = kwargs.get("prompt")
            payload["input"]["video_url"] = kwargs.get("video_url")
            payload["parameters"]["control_condition"] = kwargs.get("control_condition", "depth")

        elif function_option == "video_edit":
            payload["input"]["prompt"] = kwargs.get("prompt")
            payload["input"]["mask_image_url"] = kwargs.get("mask_image_url")
            payload["input"]["video_url"] = kwargs.get("video_url")
            payload["input"]["mask_frame_id"] = kwargs.get("mask_frame_id")
            payload["parameters"]["mask_type"] = kwargs.get("mask_type", "tracking")
            payload["parameters"]["expand_ratio"] = kwargs.get("expand_ratio", 0.05)

        elif function_option == "video_extension":
            payload["input"]["prompt"] = kwargs.get("prompt")
            payload["input"]["first_clip_url"] = kwargs.get("first_clip_url")

        elif function_option == "video_outpainting":
            payload["input"]["prompt"] = kwargs.get("prompt")
            payload["input"]["video_url"] = kwargs.get("video_url")
            payload["parameters"]["top_scale"] = kwargs.get("top_scale", 1.5)
            payload["parameters"]["bottom_scale"] = kwargs.get("bottom_scale", 1.5)
            payload["parameters"]["left_scale"] = kwargs.get("left_scale", 1.5)
            payload["parameters"]["right_scale"] = kwargs.get("right_scale", 1.5)

        else:
            logger.error(f"不支持的功能选项: {function_option}")
            return None

        logger.info(f"提交Wanx2.1-Vace-Plus视频生成任务，功能: {function_option}")
        logger.info(f"输入参数: {payload['input']}")
        logger.info(f"参数: {payload['parameters']}")

        result = self._post_request(self.submit_url, payload, headers)
        if not result:
            return None

        task_id = result.get("output", {}).get("task_id")
        if not task_id:
            logger.error("未获取到任务ID")
            return None

        logger.info(f"任务ID: {task_id}")

        # 等待任务完成
        task_url = self.task_url.format(task_id)
        completion_result = self._wait_for_completion(task_url)

        if not completion_result:
            return None

        # 获取视频URL
        video_url = completion_result.get("output", {}).get("video_url")
        if video_url:
            logger.info(f"Wanx2.1-Vace-Plus视频生成完成: {video_url}")
            _log_timing_info(completion_result, "Wanx21VacePlus")

            # 记录实际使用的提示词
            actual_prompt = completion_result.get("output", {}).get("actual_prompt")
            if actual_prompt:
                logger.info(f"实际使用的提示词: {actual_prompt}")

        return video_url


def synthesis_video(api_key: str, model_type: str, **kwargs):
    """
    通用视频生成函数

    Args:
        api_key (str): DashScope API密钥
        model_type (str): 模型类型 ('wan22s2v', 'videoretalk', 'liveportrait', 'wanx21vaceplus', 'wanx21i2vturbo', 'wanx21i2vplus')
        **kwargs: 模型特定参数

    Returns:
        tuple: (视频URL, 本地文件路径, 日志信息)
    """
    start_time = time.time()
    logger.info(f"任务开始时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")

    # 根据模型类型选择客户端
    if model_type == "wan22s2v":
        client = Wan22S2VClient(api_key)
        result_video_url = client.generate_video(**kwargs)
        model_name = "Wan22S2V"
    elif model_type == "videoretalk":
        client = VideoRetalkClient(api_key)
        result_video_url = client.synthesize_video(**kwargs)
        model_name = "VideoRetalk"
    elif model_type == "liveportrait":
        client = LivePortraitClient(api_key)
        result_video_url = client.generate_video(**kwargs)
        model_name = "LivePortrait"
    elif model_type == "wanx21vaceplus":
        client = Wanx21VacePlusClient(api_key)
        function_option = kwargs.pop("function_option", "image_reference")
        result_video_url = client.generate_video(function_option, **kwargs)
        model_name = "Wanx21VacePlus"
    elif model_type == "wanx21i2vturbo":
        # 模板图生视频
        client = Wanx21I2VTurboClient(api_key)
        result_video_url = client.generate_video(**kwargs)
        model_name = "Wanx21I2VTurbo"
    elif model_type == "wanx21i2vplus":
        # 模板图生视频
        client = Wanx21I2VPlusClient(api_key)
        result_video_url = client.generate_video(**kwargs)
        model_name = "Wanx21I2VTurbo"
    elif model_type == "wanx21kf2vplus":
        # 模板图生视频
        client = Wanx21KF2VPlusClient(api_key)
        result_video_url = client.generate_video(**kwargs)
        model_name = "wanx21kf2vplus"
    else:
        log_info = f"不支持的模型类型: {model_type}"
        logger.error(log_info)
        return None, None, log_info

    end_time = time.time()
    duration = end_time - start_time

    logger.info(f"任务结束时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}")
    logger.info(f"任务总耗时: {duration:.2f}秒")

    if result_video_url:
        filename = f"{model_type}_result_{int(time.time())}.mp4"
        file_path = download_file_from_url(result_video_url, cfg.VIDEO_RESULTS_DIR, filename)
        log_info = f"{model_name}任务完成 - 耗时: {duration:.2f}秒"
        logger.info(log_info)
        return result_video_url, file_path, log_info
    else:
        log_info = f"{model_name}任务失败 - 耗时: {duration:.2f}秒"
        logger.error(log_info)
        return None, None, log_info


def sync_video_with_wan(api_key: str, model: str, image_url: str, audio: bool = False, audio_url: str = "", prompt: str = "",
                          resolution: str = "480P", duration: int = 10,
                          prompt_extend: bool = True, watermark: bool = False,
                          negative_prompt: str = "", seed: int = 12345,
                          save_dir: str = "Downloads", **kwargs) -> Tuple[Optional[str], Optional[str]]:
    """
    使用wan2.5模型生成视频

    Args:
        api_key (str): DashScope API密钥
        model (str): 使用的模型名称
        image_url (str): 图像URL
        audio_url (bool): 是否生成音频 Defaults to False
        audio_url (str): 音频URL
        prompt (str): 视频生成提示词
        resolution (str, optional): 视频分辨率. Defaults to "480P"
        duration (int, optional): 视频时长(秒). Defaults to 10
        prompt_extend (bool, optional): 是否扩展提示词. Defaults to True
        watermark (bool, optional): 是否添加水印. Defaults to False
        negative_prompt (str, optional): 负面提示词. Defaults to ""
        seed (int, optional): 随机种子. Defaults to 12345
        save_dir (str, optional): 保存目录. Defaults to "Downloads"

    Returns:
        Tuple[Optional[str], Optional[str]]: (视频URL, 本地文件路径)，失败时返回(None, None)
    """
    logger.info("开始使用wan2.5-i2v-preview模型生成视频")
    logger.info(f"提示词: {prompt}")
    logger.info(f"图像URL: {image_url}")
    logger.info(f"音频URL: {audio_url}")

    try:
        dashscope.base_http_api_url = 'https://dashscope.aliyuncs.com/api/v1'

        # 构建调用参数，只添加非空参数
        call_params = {
            'api_key': api_key,
            'model': model,
            'img_url': image_url,
            'prompt': prompt,
            'resolution': resolution,
            'duration': duration,
            'prompt_extend': prompt_extend,
            'watermark': watermark,
            'negative_prompt': negative_prompt,
            'seed': seed
        }
        # 只有当audio_url非空时才添加
        if audio:
            call_params['audio'] = audio
        if audio_url:
            call_params['audio_url'] = audio_url

        rsp = VideoSynthesis.call(**call_params)

        logger.info(f"API响应: {rsp}")

        if rsp.status_code == HTTPStatus.OK:
            video_url = rsp.output.video_url
            logger.info(f"视频生成完成: {video_url}")

            # 保存视频到本地
            timestamp = int(time.time())
            file_path = download_file_from_url(video_url, save_dir, f"{model}_{timestamp}.mp4")
            logger.info(f"视频已保存: {file_path}")

            return video_url, file_path
        else:
            logger.error(f'视频生成失败, status_code: {rsp.status_code}, code: {rsp.code}, message: {rsp.message}')
            return None, None

    except Exception as e:
        logger.error(f"视频生成过程中发生错误: {e}")
        return None, None



def main():
    """
    主函数示例
    """
    from config.logging_config import setup_logging

    # 项目启动时初始化日志
    setup_logging()

    logger.info("📋 初始化配置参数")
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../env/default.env"))
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("DASHSCOPE_API_KEY 未配置")


    image_path = "/Users/thomaschan/Code/My_files/my_files/my_images/baby/wan25_t2i_1764748796.png"
    image_url = upload_file_to_oss(image_path, 300)
    print(f"image_url:{image_url}")

    # expire 20251125 12:00:00
    image_temp_url = "https://my-files-csy.oss-cn-hangzhou.aliyuncs.com/auto_uploads%2F1764040754_1761713320.png?OSSAccessKeyId=LTAI5t9pMQmrtoHAsxeQrXxV&Expires=1764043758&Signature=4rLTsssWV%2F%2F2WMLbUA7xluRFwwo%3D"
    video_url, video_path, log_info = synthesis_video(
        api_key=api_key,
        model_type="wanx21i2vplus",
        # model_type="wanx21i2vturbo",
        # model_type="wanx21kf2vplus",
        img_url=image_url,
        # template="flying",
        # template="hanfu-1",
        template="dance4",
        resolution="480P"
    )
    print(f"video_url:{video_url}")
    print(f"video_path:{video_path}")



def test_separate_reetalk():
    # 测试并发VideoRetalk模型
    from config.logging_config import setup_logging

    # 项目启动时初始化日志
    setup_logging()

    logger.info("📋 初始化配置参数")
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../env/default.env"))
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("DASHSCOPE_API_KEY 未配置")

    video_file = "/Users/thomaschan/Code/My_files/my_files/my_vedios/test_video_man_10s_720p.mp4"
    audio_file = "/Users/thomaschan/Code/My_files/my_files/my_audios/test_audio_longlaotie_v2_46s_003.mp3"

    audio_clip_files = split_mp3(audio_file, 10, cfg.AUDIO_RESULTS_DIR)

    result_path_list = []
    n = 1
    for clip in audio_clip_files:
        logger.info(f"开始处理第{n}个音频片段")
        video_url = upload_file_to_oss(video_file, 3000)
        # video_url = ""
        audio_url = upload_file_to_oss(clip, 3000)
        result_url, result_path, log_info = synthesis_video(api_key=api_key,
                                                            model_type="videoretalk",
                                                            video_url=video_url,
                                                            audio_url=audio_url)
        result_path_list.append(result_path)
        logger.info(f"完成处理第{n}个音频片段")

    timestamp = int(time.time())
    output_file_name = f"merged_video_{timestamp}.mp4"
    output_file_path = os.path.join(cfg.VIDEO_RESULTS_DIR, output_file_name)
    merged_result_url = merge_videos(result_path_list, output_path=output_file_path)
    logger.info(f"合并视频完成 - 文件位置: {merged_result_url}")


if __name__ == "__main__":
    main()
    # test_wan25()
