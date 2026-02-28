"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 图像数据、生成参数
Output: 视频生成任务结果
Pos: Kling 视频生成模型客户端
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

from core.model_client.kling_model_client.kling_get_api import encode_jwt_token
from util.util_file import download_file_from_url

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


class KlingVideoModelClient:
    """Kling视频模型客户端"""

    def __init__(self, api_key: str):
        """
        初始化Kling视频模型客户端

        Args:
            api_key (str): Kling API密钥
        """
        self.api_key = api_key
        self.base_url = "https://api-beijing.klingai.com"
        self.base_headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

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
            # 打印请求内容供检查
            logger.info(f"发送POST请求:")
            logger.info(f"URL: {url}")
            logger.info(f"Headers: {json.dumps(headers, ensure_ascii=False, indent=2)}")
            logger.info(f"Data: {json.dumps(data, ensure_ascii=False, indent=2)}")

            response = requests.post(url, headers=headers, json=data)

            # 打印完整的响应信息
            logger.info(f"收到响应 - 状态码: {response.status_code}")
            logger.info(f"响应头: {dict(response.headers)}")
            logger.info(f"响应内容: {response.text}")

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
            # 打印请求内容供检查
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            logger.info(f"发送GET请求:")
            logger.info(f"URL: {url}")
            logger.info(f"Headers: {json.dumps(headers, ensure_ascii=False, indent=2)}")

            response = requests.get(url, headers=headers)
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

    def _wait_for_lip_sync_completion(self, task_url: str, check_interval: int = cfg.INTERVAL_TIME) -> Optional[Dict[Any, Any]]:
        """
        等待对口型任务完成

        Args:
            task_url (str): 任务查询URL
            check_interval (int, optional): 查询间隔时间(秒). Defaults to 20.

        Returns:
            Optional[Dict[Any, Any]]: 完成的任务结果，失败时返回None
        """
        logger.info("开始轮询对口型任务状态...")

        while True:
            time.sleep(check_interval)
            logger.info("检查对口型任务状态...")

            result = self._get_request(task_url)
            if not result:
                return None

            if result.get("code") != 0:
                logger.error(f"任务查询失败: {result.get('message', '未知错误')}")
                return None

            task_status = result.get("data", {}).get("task_status")
            logger.info(f"当前状态: {task_status}")

            if task_status == "succeed":
                logger.info("对口型任务完成成功")
                return result
            elif task_status in ["failed", "canceled"]:
                logger.error(f"对口型任务失败: {json.dumps(result, indent=2, ensure_ascii=False)}")
                return None
            elif task_status in ["submitted", "processing"]:
                logger.info("对口型任务进行中，继续等待...")
            else:
                logger.warning(f"未知状态: {task_status}")


    def identify_face(self, **kwargs) -> Optional[Dict[Any, Any]]:
        """
        人脸识别接口，用于对口型服务前的人脸识别

        Args:
            **kwargs: 识别参数
                video_id (str, optional): 通过可灵AI生成的视频的ID
                video_url (str, optional): 所上传视频的获取URL
                注意：video_id和video_url二选一填写

        Returns:
            Optional[Dict[Any, Any]]: 人脸识别结果，包含session_id和face_data等信息
        """
        video_id = kwargs.get("video_id")
        video_url = kwargs.get("video_url")

        # 参数校验
        logger.info(f"人脸识别参数校验: video_id={video_id}, video_url={video_url}")
        if not video_id and not video_url:
            logger.error("缺少必需参数: video_id 或 video_url")
            return None
        if video_id and video_url:
            logger.error("参数冲突: video_id 和 video_url 不能同时有值")
            return None

        url = f"{self.base_url}/v1/videos/identify-face"

        payload = {}
        if video_id:
            payload["video_id"] = video_id
            payload["video_url"] = ""
        if video_url:
            payload["video_id"] = None
            payload["video_url"] = video_url

        logger.info(f"人脸识别请求URL: {url}")
        logger.info(f"人脸识别请求数据: {json.dumps(payload, ensure_ascii=False)}")
        logger.info("开始人脸识别...")

        # 记录请求头信息
        logger.debug(f"请求头信息: {self.base_headers}")

        result = self._post_request(url, payload, self.base_headers)

        if result:
            logger.info(f"人脸识别响应状态码检查: code={result.get('code')}")
            if result.get("code") == 0:
                logger.info("人脸识别成功")
                logger.debug(f"人脸识别完整响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
                return result
            else:
                error_msg = result.get("message", "未知错误")
                request_id = result.get("request_id", "未知")
                error_code = result.get("code", "未知")
                logger.error(f"人脸识别失败 - 错误码: {error_code}, 错误信息: {error_msg}, 请求ID: {request_id}")
                logger.error(f"人脸识别完整错误响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
                return None
        else:
            logger.error("人脸识别无响应或请求异常")
            return None


    def advanced_lip_sync(self, **kwargs) -> Optional[str]:
        """
        创建对口型任务

        Args:
            **kwargs: 对口型参数
                session_id (str): 会话ID，由人脸识别接口生成
                face_choose (list): 指定人脸对口型参数列表
                    face_id (str): 人脸ID
                    audio_id (str, optional): 音频ID
                    sound_file (str, optional): 音频文件URL或Base64
                    sound_start_time (int): 音频裁剪起点时间(毫秒)
                    sound_end_time (int): 音频裁剪终点时间(毫秒)
                    sound_insert_time (int): 音频插入时间(毫秒)
                    sound_volume (float, optional): 音频音量大小，默认1.0
                    original_audio_volume (float, optional): 原始视频音量大小，默认1.0
                external_task_id (str, optional): 自定义任务ID
                callback_url (str, optional): 回调通知地址

        Returns:
            Optional[str]: 任务ID，失败时返回None
        """
        session_id = kwargs.get("session_id")
        face_choose = kwargs.get("face_choose")

        # 参数校验
        if not session_id:
            logger.error("缺少必需参数: session_id")
            return None
        if not face_choose:
            logger.error("缺少必需参数: face_choose")
            return None

        url = f"{self.base_url}/v1/videos/advanced-lip-sync"

        payload = {
            "session_id": session_id,
            "face_choose": face_choose
        }

        # 添加可选参数
        if "external_task_id" in kwargs:
            payload["external_task_id"] = kwargs["external_task_id"]
        if "callback_url" in kwargs:
            payload["callback_url"] = kwargs["callback_url"]

        logger.info("提交对口型任务...")
        result = self._post_request(url, payload, self.base_headers)

        if result and result.get("code") == 0:
            task_id = result.get("data", {}).get("task_id")
            logger.info(f"对口型任务提交成功，任务ID: {task_id}")
            return task_id
        else:
            error_msg = result.get("message") if result else "未知错误"
            logger.error(f"对口型任务提交失败: {error_msg}")
            return None

    def query_lip_sync_task(self, task_id: str) -> Optional[Dict[Any, Any]]:
        """
        查询对口型任务状态

        Args:
            task_id (str): 对口型任务ID

        Returns:
            Optional[Dict[Any, Any]]: 任务状态信息
        """
        if not task_id:
            logger.error("缺少必需参数: task_id")
            return None

        url = f"{self.base_url}/v1/videos/advanced-lip-sync/{task_id}"

        logger.info(f"查询对口型任务状态，任务ID: {task_id}")
        result = self._get_request(url)

        if result and result.get("code") == 0:
            task_status = result.get("data", {}).get("task_status")
            logger.info(f"任务状态: {task_status}")
            return result
        else:
            error_msg = result.get("message") if result else "未知错误"
            logger.error(f"查询任务失败: {error_msg}")
            return None

    def query_lip_sync_tasks(self, page_num: int = 1, page_size: int = 30) -> Optional[Dict[Any, Any]]:
        """
        查询对口型任务列表

        Args:
            page_num (int, optional): 页码. Defaults to 1.
            page_size (int, optional): 每页数据量. Defaults to 30.

        Returns:
            Optional[Dict[Any, Any]]: 任务列表信息
        """
        url = f"{self.base_url}/v1/videos/advanced-lip-sync"

        # 添加查询参数
        params = []
        if page_num:
            params.append(f"pageNum={page_num}")
        if page_size:
            params.append(f"pageSize={page_size}")

        if params:
            url += "?" + "&".join(params)

        logger.info(f"查询对口型任务列表，页码: {page_num}，每页数量: {page_size}")
        result = self._get_request(url)

        if result and result.get("code") == 0:
            logger.info("任务列表查询成功")
            return result
        else:
            error_msg = result.get("message") if result else "未知错误"
            logger.error(f"查询任务列表失败: {error_msg}")
            return None

    def generate_lip_sync_video(self, video_url: str, audio_url: str, **kwargs) -> Optional[str]:
        """
        生成对口型视频的完整流程

        Args:
            video_url (str): 原始视频URL
            audio_url (str): 音频文件URL
            **kwargs: 其他参数
                sound_start_time (int): 音频裁剪起点时间(毫秒)
                sound_end_time (int): 音频裁剪终点时间(毫秒)
                sound_insert_time (int): 音频插入时间(毫秒)
                sound_volume (float, optional): 音频音量大小
                original_audio_volume (float, optional): 原始视频音量大小

        Returns:
            Optional[str]: 生成的对口型视频URL，失败时返回None
        """
        # 1. 人脸识别
        logger.info("开始对口型视频生成流程...")
        face_result = self.identify_face(video_url=video_url)
        if not face_result:
            logger.error("人脸识别失败，终止对口型视频生成")
            return None

        session_id = face_result.get("data", {}).get("session_id")
        face_data = face_result.get("data", {}).get("face_data", [])

        if not session_id or not face_data:
            logger.error("人脸识别结果不完整，缺少session_id或face_data")
            return None

        # 默认使用第一个人脸
        face_id = face_data[0].get("face_id")
        start_time = face_data[0].get("start_time")
        end_time = face_data[0].get("end_time")

        # 2. 创建对口型任务
        sound_start_time = kwargs.get("sound_start_time", 0)
        sound_end_time = kwargs.get("sound_end_time", end_time - start_time if end_time and start_time else 10000)
        sound_insert_time = kwargs.get("sound_insert_time", start_time if start_time else 0)

        face_choose_params = [{
            "face_id": face_id,
            "sound_file": audio_url,
            "sound_start_time": sound_start_time,
            "sound_end_time": sound_end_time,
            "sound_insert_time": sound_insert_time
        }]

        # 添加可选参数
        if "sound_volume" in kwargs:
            face_choose_params[0]["sound_volume"] = kwargs["sound_volume"]
        if "original_audio_volume" in kwargs:
            face_choose_params[0]["original_audio_volume"] = kwargs["original_audio_volume"]

        task_id = self.advanced_lip_sync(
            session_id=session_id,
            face_choose=face_choose_params
        )

        if not task_id:
            logger.error("对口型任务创建失败")
            return None

        # 3. 等待任务完成
        task_url = f"{self.base_url}/v1/videos/advanced-lip-sync/{task_id}"
        completion_result = self._wait_for_lip_sync_completion(task_url)

        if not completion_result:
            logger.error("对口型任务执行失败")
            return None

        # 4. 获取视频URL
        video_url = completion_result.get("data", {}).get("task_result", {}).get("videos", [{}])[0].get("url")
        if video_url:
            logger.info(f"对口型视频生成完成: {video_url}")
            _log_timing_info(completion_result, "KlingLipSync")

        return video_url


def synthesis_video(api_key: str, model_type: str, **kwargs):
    """
    通用视频生成函数

    Args:
        api_key (str): Kling API密钥
        model_type (str): 模型类型 ('kling-lip-sync')
        **kwargs: 模型特定参数

    Returns:
        tuple: (视频URL, 本地文件路径, 日志信息)
    """
    start_time = time.time()
    logger.info(f"任务开始时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")

    # 根据模型类型选择客户端
    if model_type == "kling-lip-sync":
        client = KlingVideoModelClient(api_key)
        video_url = kwargs.get("video_url")
        audio_url = kwargs.get("audio_url")
        result_video_url = client.generate_lip_sync_video(video_url, audio_url, **kwargs)
        model_name = "KlingLipSync"
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


def test_kling_lip_sync(video_url: str, audio_url: str, **kwargs):
    """
    测试Kling对口型视频生成

    Args:
        video_url (str): 原始视频URL
        audio_url (str): 音频文件URL
        **kwargs: 其他参数

    Returns:
        Optional[str]: 生成的对口型视频URL，失败时返回None
    """
    logger.info("开始测试Kling对口型视频生成")

    start_time = time.time()
    logger.info(f"任务开始时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")

    # 动态获取api token key
    api_key = encode_jwt_token()

    client = KlingVideoModelClient(api_key)
    result_video_url = client.generate_lip_sync_video(video_url, audio_url, **kwargs)

    end_time = time.time()
    duration = end_time - start_time

    logger.info(f"任务结束时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}")
    logger.info(f"任务总耗时: {duration:.2f}秒")

    if result_video_url:
        filename = f"kling_lip_sync_result_{int(time.time())}.mp4"
        file_path = download_file_from_url(result_video_url, cfg.VIDEO_RESULTS_DIR, filename)
        logger.info(f"Kling对口型任务完成 - 耗时: {duration:.2f}秒")
        return result_video_url, file_path
    else:
        logger.error(f"Kling对口型任务失败 - 耗时: {duration:.2f}秒")
        return None, None


if __name__ == "__main__":
    from config.logging_config import setup_logging

    # 项目启动时初始化日志
    setup_logging()

    image_url_list = [
        "https://gitee.com/sad_sad/my_files/raw/master/my_files/my_images/test_man_001.png",
    ]
    video_url_list = [
        "https://gitee.com/sad_sad/my_files/raw/master/my_files/my_vedios/test_video_95s.mp4",
        "https://gitee.com/sad_sad/my_files/raw/master/my_files/my_vedios/test_vedio_man_60s_720p_silent_002.mov",
        "https://help-static-aliyun-doc.aliyuncs.com/file-manage-files/zh-CN/20250717/pvegot/input_video_01.mp4",
        "https://gitee.com/sad_sad/my_files/raw/master/my_files/my_vedios/test_video_man_50s_720p_silent_001.mov",
        "https://my-files-csy.oss-cn-hangzhou.aliyuncs.com/video/test_video_man_50s_720p_silent_001%20%282%29.mov",
    ]
    audio_url_list = [
        "https://gitee.com/sad_sad/my_files/raw/master/my_files/my_audios/test_audio_99s_001.mp3",
        "https://gitee.com/sad_sad/my_files/raw/master/my_files/my_audios/test_audio_longlaotie_v2_46s_002.mp3",
        "https://gitee.com/sad_sad/my_files/raw/master/my_files/my_audios/test_audio_man_20s_20251009.mp3",
        "https://my-files-csy.oss-cn-hangzhou.aliyuncs.com/music/test.mp3",
    ]
    # 示例调用
    res_url, res_path = test_kling_lip_sync(video_url=video_url_list[4], audio_url=audio_url_list[3])

    print(f"url:{res_url}, \npath:{res_path}")

