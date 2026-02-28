"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 视频生成需求、素材
Output: 合成后的视频
Pos: 视频合成代理版本01
"""

from component import synthesize_speech
from component import synthesis_picture
from component import detect_task, submit_task, wait_for_video_completion
from util.util_file import download_file_from_url
from util.util_url import upload_file_and_get_url
import config.config as config
import os
from dotenv import load_dotenv


from config.logging_config import get_logger, setup_logging

# 项目启动时初始化日志
setup_logging()
logger = get_logger(__name__)


def agent_syn_video_01():
    """数字人视频生成主流程"""
    logger.info("🚀 开始数字人视频生成流程")

    try:
        # ========== 初始化配置 ==========
        logger.info("📋 初始化配置参数")
        load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../env/default.env"))
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            raise ValueError("DASHSCOPE_API_KEY 未配置")

        model_name = "wan2.2-s2v"
        detect_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/image2video/face-detect"
        submit_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/image2video/video-synthesis/"
        task_url = "https://dashscope.aliyuncs.com/api/v1/tasks/{}"
        time_delay = 15

        audio_syn_text = '''
            朋友买了个华为手机，我说：哇，这手机信号一定很好吧？
            他点点头说：是的，连隔壁WiFi密码都能收到！
            我愣了一下问：那你咋不上网？
            朋友叹口气：密码输错三次，华为建议我直接换个邻居。
        '''
        picture_syn_text = "生成Tim Cook拿着华为手机开发布会的图片，背景简单，必须是全身或是半身的人像肖像，可以看到清楚的人物身体。"

        logger.info("✅ 配置初始化完成")

        # ========== 生成音频 ==========
        logger.info("🎵 开始生成音频")
        try:
            audio_file_path, audio_public_url = synthesize_speech(
                api_key=api_key,
                text=audio_syn_text,
                speech_rate=1.3,
                output_dir=config.AUDIO_RESULTS_DIR
            )

            if audio_public_url is None:
                logger.info("上传音频文件到OSS")
                audio_public_url = upload_file_and_get_url(api_key, model_name, audio_file_path)

            logger.info(f"✅ 音频生成完成: {audio_public_url}")

        except Exception as e:
            logger.error(f"❌ 音频生成失败: {e}", exc_info=True)
            raise

        # ========== 生成图片 ==========
        logger.info("🖼️ 开始生成图片")
        try:
            picture_file_path, picture_public_url = synthesis_picture(
                api_key=api_key,
                text=picture_syn_text,
                model_name="qwen-image",
                save_dir=config.PICTURE_RESULTS_DIR
            )

            if picture_public_url is None:
                logger.info("上传图片文件到OSS")
                picture_public_url = upload_file_and_get_url(api_key, model_name, picture_file_path)

            logger.info(f"✅ 图片生成完成: {picture_public_url}")

        except Exception as e:
            logger.error(f"❌ 图片生成失败: {e}", exc_info=True)
            raise

        # ========== 图像检测 ==========
        logger.info("🔍 开始图像检测")
        try:
            if not detect_task(api_key, detect_url, picture_public_url):
                raise RuntimeError("图像检测不通过")
            logger.info("✅ 图像检测通过")

        except Exception as e:
            logger.error(f"❌ 图像检测失败: {e}", exc_info=True)
            raise

        # ========== 提交视频生成任务 ==========
        logger.info("📤 提交视频生成任务")
        try:
            task_id = submit_task(api_key, submit_url, picture_public_url, audio_public_url)
            logger.info(f"✅ 任务提交成功: {task_id}")

        except Exception as e:
            logger.error(f"❌ 任务提交失败: {e}", exc_info=True)
            raise

        # ========== 等待视频生成完成 ==========
        logger.info("⏳ 等待视频生成完成")
        try:
            video_url, consume_time = wait_for_video_completion(
                api_key, task_url, task_id, time_delay
            )
            logger.info(f"✅ 视频生成完成: {video_url}, 耗时: {consume_time}")

        except Exception as e:
            logger.error(f"❌ 视频生成失败: {e}", exc_info=True)
            raise

        # ========== 下载视频 ==========
        logger.info("⬇️ 开始下载视频")
        try:
            video_file_path = download_file_from_url(
                video_url, config.VIDEO_RESULTS_DIR, f"my_video_{task_id}"
            )
            logger.info(f"✅ 视频下载完成: {video_file_path}")

        except Exception as e:
            logger.error(f"❌ 视频下载失败: {e}", exc_info=True)
            raise
        # todo csy 20250922:打印时间、文件大小、时长、token
        logger.info("🎉 数字人视频生成流程全部完成")
        return video_file_path

    except Exception as e:
        logger.error(f"💥 数字人视频生成流程失败: {e}", exc_info=True)
        return None


if __name__ == "__main__":
    result = agent_syn_video_01()
    if result:
        logger.info(f"🎬 最终输出: {result}")
    else:
        logger.error("🚫 流程执行失败", exc_info=True)

