"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 文本内容
Output: 音频文件
Pos: 音频合成功能
"""

# file: /Users/thomaschan/Code/Python/AI_vedio_demo/pythonProject/component/synthesis_audio.py
import logging
import os
import time
import dashscope
from dashscope.audio.tts_v2 import SpeechSynthesizer
from dotenv import load_dotenv
import config.config as cfg
from config.logging_config import get_logger
import json
from pydub import AudioSegment
from util.util_file import download_file_from_url

# 项目启动时初始化日志
logger = get_logger(__name__)


class AudioModelClient:
    """音频模型客户端基类"""

    def __init__(self, api_key: str):
        """
        初始化音频模型客户端

        Args:
            api_key (str): DashScope API密钥
        """
        self.api_key = api_key
        dashscope.api_key = api_key

    def _synthesize(self, text: str, model: str, voice: str, speech_rate: float, volume: int) -> bytes:
        """
        执行音频合成

        Args:
            text (str): 要合成的文本
            model (str): 模型名称
            voice (str): 音色
            speech_rate (float): 语速
            volume (int): 音量

        Returns:
            bytes: 音频数据
        """
        try:
            synthesizer = SpeechSynthesizer(
                model=model,
                voice=voice,
                speech_rate=speech_rate,
                volume=volume
            )
            audio = synthesizer.call(text)

            if not audio:
                logger.error("API 返回的音频数据为空，请检查模型名、音色或配额")
                return None

            # 记录API诊断信息
            logger.info(f"[Metric] requestId={synthesizer.get_last_request_id()}")
            logger.info(f"首包延迟={synthesizer.get_first_package_delay()} 毫秒")

            return audio
        except Exception as e:
            logger.error(f"音频合成异常: {e}", exc_info=True)
            return None


class CosyVoiceClient(AudioModelClient):
    """CosyVoice音频合成客户端"""

    def __init__(self, api_key: str):
        """
        初始化CosyVoice音频合成客户端

        Args:
            api_key (str): DashScope API密钥
        """
        super().__init__(api_key)

    def synthesize_audio(self, **kwargs) -> bytes:
        """
        合成音频

        Args:
            **kwargs: 合成参数
                text (str): 要合成的文本
                model (str, optional): 模型名称. Defaults to "cosyvoice-v2".
                voice (str, optional): 音色. Defaults to "longxiaochun_v2".
                speech_rate (float, optional): 语速. Defaults to 1.0.
                volume (int, optional): 音量. Defaults to 50.

        Returns:
            bytes: 音频数据
        """
        text = kwargs.get("text")
        model = kwargs.get("model", "cosyvoice-v2")
        voice = kwargs.get("voice", "longxiaochun_v2")
        speech_rate = kwargs.get("speech_rate", 1.0)
        volume = kwargs.get("volume", 50)

        # 参数校验
        if not text:
            logger.error("缺少必需参数: text")
            return None

        logger.info("开始音频合成...")
        logger.info(f"模型: {model}, 音色: {voice}, 语速: {speech_rate}, 音量: {volume}")

        return self._synthesize(text, model, voice, speech_rate, volume)


def synthesis_audio(api_key: str, model_type: str, **kwargs):
    """
    通用音频合成函数

    Args:
        api_key (str): DashScope API密钥
        model_type (str): 模型类型 ('cosyvoice')
        **kwargs: 模型特定参数

    Returns:
        tuple: (音频文件路径, None, 日志信息)
    """
    start_time = time.time()
    logger.info(f"任务开始时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")

    # 根据模型类型选择客户端
    if model_type == "cosyvoice":
        client = CosyVoiceClient(api_key)
        audio_data = client.synthesize_audio(**kwargs)
        model_name = "CosyVoice"
    else:
        log_info = f"不支持的模型类型: {model_type}"
        logger.error(log_info)
        return None, None, log_info

    end_time = time.time()
    duration = end_time - start_time

    logger.info(f"任务结束时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}")
    logger.info(f"任务总耗时: {duration:.2f}秒")

    if audio_data:
        # 生成带时间戳的文件名（加毫秒避免同秒内高频调用导致覆盖）
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        ms = int((time.time() * 1000) % 1000)
        filename = f"audio_{model_type}_result_{timestamp}_{ms:03d}.mp3"
        save_path = os.path.join(cfg.AUDIO_RESULTS_DIR, filename)

        # 确保保存目录存在
        os.makedirs(cfg.AUDIO_RESULTS_DIR, exist_ok=True)

        # 保存音频文件
        with open(save_path, "wb") as f:
            f.write(audio_data)

        log_info = f"{model_name}任务完成 - 耗时: {duration:.2f}秒，文件已保存至: {save_path}"
        logger.info(log_info)
        return save_path, None, log_info
    else:
        log_info = f"{model_name}任务失败 - 耗时: {duration:.2f}秒"
        logger.error(log_info)
        return None, None, log_info



# 假设你的 synthesis_audio 已经定义好
# from your_module import synthesis_audio, cfg


def generate_dialogue_audio(dialogue_json_path, api_key, model_type="cosyvoice"):
    """
    根据对话JSON生成完整对话音频
    Args:
        dialogue_json_path (str): 对话JSON文件路径
        api_key (str): DashScope API Key
        model_type (str): 模型类型 ('cosyvoice')
    Returns:
        str: 拼接后的完整音频路径
    """

    # === 1. 读取 JSON ===
    with open(dialogue_json_path, "r", encoding="utf-8") as f:
        dialogue_data = json.load(f)

    dialogue_title = dialogue_data.get("dialogue_title", "dialogue_output")
    characters = {c["name"]: c for c in dialogue_data["characters"]}
    script = dialogue_data["script"]

    logger.info(f"开始生成对话音频: {dialogue_title}")

    # 临时保存所有句子的音频路径
    temp_audio_paths = []

    # === 2. 为每句话生成音频 ===
    for i, line in enumerate(script):
        speaker = line["speaker"]
        text = line["text"]
        speech_rate = line.get("speech_rate", 1.0)
        pitch_rate = line.get("pitch_rate", 1.0)
        char_info = characters.get(speaker)

        if not char_info:
            logger.warning(f"未找到角色配置: {speaker}，跳过。")
            continue

        logger.info(f"正在生成语音: [{speaker}] {text}")

        # 调用通用音频合成函数
        save_path, _, log_info = synthesis_audio(
            api_key=api_key,
            model_type=model_type,
            text=text,
            voice=char_info["voice_id"],
            speech_rate=speech_rate,
            pitch_rate=pitch_rate,
        )

        if save_path:
            temp_audio_paths.append(save_path)
            logger.info(f"语音生成成功: {save_path}")
        else:
            logger.error(f"语音生成失败: {speaker} -> {text}")

        # 每句之间留出 0.3 秒间隔
        time.sleep(0.3)

    # === 3. 拼接所有音频 ===
    if not temp_audio_paths:
        logger.error("未生成任何音频文件。")
        return None

    logger.info("开始拼接音频...")

    combined = AudioSegment.empty()
    for path in temp_audio_paths:
        segment = AudioSegment.from_file(path, format="mp3")
        combined += segment + AudioSegment.silent(duration=300)  # 每句间隔0.3秒

    # 生成输出文件名（加毫秒避免同秒内覆盖）
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    ms = int((time.time() * 1000) % 1000)
    output_filename = f"{dialogue_title}_{timestamp}_{ms:03d}.mp3"
    output_path = os.path.join(cfg.AUDIO_RESULTS_DIR, output_filename)
    os.makedirs(cfg.AUDIO_RESULTS_DIR, exist_ok=True)

    combined.export(output_path, format="mp3")
    logger.info(f"✅ 对话音频生成完成: {output_path}")

    return output_path


# === 使用示例 ===
if __name__ == "__main__":
    from config.logging_config import setup_logging

    # 项目启动时初始化日志
    setup_logging()

    # 加载环境变量
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../env/default.env"))
    api_key = os.getenv("DASHSCOPE_API_KEY")

    dialogue_json_path = "/Users/thomaschan/Code/My_files/my_files/my_scripts/小兔相亲20251017/dialogue_v0.2.json"
    output_path = generate_dialogue_audio(dialogue_json_path, api_key)
