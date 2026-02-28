"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 多个活动实例
Output: 完整的视频处理结果
Pos: 视频复现任务组编排
"""

# 该文件用于视频复刻工作流中，需要使用到到任务组，即连续执行可复用的任务
from pathlib import Path
from typing import List, Tuple, Dict

from component.chat.chat import chat_with_model
from component.muti.synthesis_image import sync_i2i_wan_v25, sync_t2i_wan_v25
from component.muti.visual_understanding import understand_image
from config.logging_config import get_logger
from config import config as cfg
from config import prompt_default as prompt
from util.util_file import extract_audio_from_video, transcribe_audio_to_srt, extract_video_frames_by_interval
from util.util_url import upload_file_to_oss
from dashscope import ImageSynthesis


logger = get_logger(__name__)


def tkg_split_video(
        video_path: str,
        output_dir: str = None,
        frame_interval: float = 2.0,
        model_size: str = "small",
        language: str = "zh"
) -> Dict[str, any]:
    """
    将视频的音频、字幕、分镜图提取并输出
    
    Args:
        video_path: 视频文件路径
        output_dir: 输出目录（默认为视频同目录）
        frame_interval: 抽帧间隔（秒），默认2秒
        model_size: Whisper模型大小（small/medium/large）
        language: 音频语言（zh/en）
        
    Returns:
        Dict: 包含 audio_path, srt_path, frame_paths 的字典
    """
    logger.info(f"🎬 开始视频拆分: {video_path}")
    
    video_path = Path(video_path)
    if not video_path.exists():
        logger.error(f"视频文件不存在: {video_path}")
        return None
    
    # 设置输出目录
    if output_dir is None:
        output_dir = video_path.parent
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    # === 提取音频与字幕 ===
    logger.info("🎵 步骤1: 提取音频与字幕")
    output_srt = output_dir / f"{video_path.stem}.srt"
    audio_path = None
    srt_path = None
    
    try:
        # 提取音频
        audio_path = extract_audio_from_video(video_path)
        logger.info(f"✅ 音频已提取: {audio_path}")

        # 转录
        transcribe_result = transcribe_audio_to_srt(audio_path, output_srt, model_size, language)
        srt_path = output_srt
        logger.info(f"✅ 字幕已生成: {srt_path}")
        logger.info(f"   语言: {transcribe_result['language']}, 字幕数: {transcribe_result['segment_count']}")

    except Exception as e:
        logger.error(f"提取音频/字幕失败: {e}")
        logger.exception(e)

    # === 提取分镜图 ===
    logger.info(f"📸 步骤2: 提取分镜图（间隔{frame_interval}秒）")
    frame_paths = []
    
    try:
        # 设置帧输出目录
        frames_dir = output_dir / f"{video_path.stem}_frames"
        frame_paths = extract_video_frames_by_interval(
            video_path=video_path,
            interval=frame_interval,
            output_dir=frames_dir
        )
        logger.info(f"✅ 分镜图已提取: {len(frame_paths)} 帧")
        
    except Exception as e:
        logger.error(f"提取分镜图失败: {e}")
        logger.exception(e)

    result = {
        "audio_path": str(audio_path) if audio_path else None,
        "srt_path": str(srt_path) if srt_path else None,
        "frame_paths": [str(p) for p in frame_paths]
    }
    
    logger.info(f"✅ 视频拆分完成")
    logger.info(f"   音频: {result['audio_path']}")
    logger.info(f"   字幕: {result['srt_path']}")
    logger.info(f"   帧数: {len(result['frame_paths'])}")
    
    return result


# todo csy 20251112:这个任务组需要添加判断，对重复信息的图片进行去重
def tkg_extract_frame_info(
        api_key: str,
        frame_path_list: List[str],
        instruction: str,
        oss_expire_seconds: int = 3600
) -> Dict[str, List]:
    """
    提取视频帧图片的信息
    
    Args:
        api_key: API密钥
        frame_path_list: 帧图片路径列表
        instruction: 理解指令（如：描述图片中的主要元素）
        oss_expire_seconds: OSS URL过期时间（秒），默认1小时
        
    Returns:
        Dict: 包含 image_info_list 和 image_url_info_list 的字典
    """
    logger.info(f"📸 开始提取图片信息，共 {len(frame_path_list)} 张")
    
    if not frame_path_list:
        logger.warning("帧图片列表为空")
        return {
            "image_info_list": [],
            "image_url_info_list": []
        }

    # === 步骤1: 上传图片到OSS ===
    logger.info("📤 步骤1: 上传图片到OSS...")
    image_url_list = []
    
    for i, frame_path in enumerate(frame_path_list, start=1):
        try:
            image_url = upload_file_to_oss(frame_path, oss_expire_seconds)
            image_url_list.append(image_url)
            logger.info(f"  [{i}/{len(frame_path_list)}] ✅ 已上传: {Path(frame_path).name}")
        except Exception as e:
            logger.error(f"  [{i}/{len(frame_path_list)}] ❌ 上传失败: {frame_path} - {e}")
            image_url_list.append(None)

    # === 步骤2: 理解图片信息 ===
    logger.info("🧠 步骤2: 理解图片信息...")
    image_info_list = []  # 只包含图片理解信息的list
    image_url_info_list = []  # 包含图片url和图片信息的dict的list

    for i, image_url in enumerate(image_url_list, start=1):
        if image_url is None:
            logger.warning(f"  [{i}/{len(image_url_list)}] 跳过（上传失败）")
            continue
            
        try:
            # 理解单张图片
            logger.info(f"  [{i}/{len(image_url_list)}] 🔍 理解中...")
            image_info = understand_image(
                api_key,
                image_url,
                prompt.IMAGE_UNDERSTANDING_PROMPT.substitute(instruction=instruction),
            )

            # 添加到只包含图片信息的列表
            image_info_list.append(image_info)

            # 添加到包含url和信息的字典列表
            image_url_info_list.append({
                "url": image_url,
                "info": image_info
            })
            
            logger.info(f"  [{i}/{len(image_url_list)}] ✅ {image_info[:80]}...")
            
        except Exception as e:
            logger.error(f"  [{i}/{len(image_url_list)}] ❌ 理解失败: {e}")
            logger.exception(e)

    logger.info(f"✅ 图片信息提取完成，成功 {len(image_info_list)}/{len(frame_path_list)} 张")
    
    result = {
        "image_info_list": image_info_list,
        "image_url_info_list": image_url_info_list
    }
    
    return result



def tkg_sync_new_story(
        api_key: str,
        images_info: str,
        subtitle: str,
        instruction: str
) -> dict:
    """
    基于原视频信息生成新故事

    Args:
        api_key: API密钥
        images_info: 图片结构化信息
        subtitle: 字幕文本
        instruction: 用户指令（如：改编为科幻风格）

    Returns:
        新故事的结构化JSON dict
    """

    # ========================================
    # 步骤1：提取原故事摘要
    # ========================================
    logger.info("📖 步骤1：提取原故事摘要...")

    messages = [
        {
            "role": "system",
            "content": prompt.STORY_EXTRACT_SYSTEM,
        },
        {
            "role": "user",
            "content": prompt.STORY_EXTRACT_USER_TEMPLATE.substitute(
                instruction=instruction,
                images_info=images_info,
                subtitle_info=subtitle
            ),
        }
    ]
    ori_story = chat_with_model(
        api_key=api_key,
        model_type="qwen",
        model="qwen-max",
        messages=messages
    )
    logger.info(f"✅ 原故事摘要：\n{ori_story}\n")

    # ========================================
    # 步骤2：生成3个新故事创意
    # ========================================
    logger.info("💡 步骤2：生成3个新故事创意...")

    messages = [
        {
            "role": "system",
            "content": prompt.STORY_IDEA_SYSTEM,
        },
        {
            "role": "user",
            "content": prompt.STORY_IDEA_USER_TEMPLATE.substitute(
                ori_story=ori_story,
                instruction=instruction
            ),
        }
    ]

    new_story_ideas = []
    for i in range(3):
        logger.info(f"  生成创意 {i + 1}/3...")
        idea = chat_with_model(
            api_key=api_key,
            model_type="deepseek",
            model="deepseek-v3.2-exp",
            extra_body={"enable_thinking": True},
            messages=messages
        )
        new_story_ideas.append(idea)
        logger.info(f"  ✅ 创意{i + 1}：{idea[:100]}...\n")

    # ========================================
    # 步骤3：选择最佳创意
    # ========================================
    logger.info("🎯 步骤3：选择最佳创意...")

    messages = [
        {
            "role": "system",
            "content": prompt.STORY_IDEA_SELECT_SYSTEM,
        },
        {
            "role": "user",
            "content": prompt.STORY_IDEA_SELECT_USER_TEMPLATE.substitute(
                idea_1=new_story_ideas[0],
                idea_2=new_story_ideas[1],
                idea_3=new_story_ideas[2],
                instruction=instruction
            ),
        }
    ]

    selection_result = chat_with_model(
        api_key=api_key,
        model_type="qwen",
        model="qwen-plus",
        extra_body={"enable_thinking": True},
        messages=messages
    )
    logger.info(f"✅ 选择结果：\n{selection_result}\n")

    # 解析选择结果（简单处理：查找创意编号）
    selected_idx = 0  # 默认选第一个
    if "创意2" in selection_result or "idea 2" in selection_result.lower() or "编号2" in selection_result:
        selected_idx = 1
    elif "创意3" in selection_result or "idea 3" in selection_result.lower() or "编号3" in selection_result:
        selected_idx = 2

    final_idea = new_story_ideas[selected_idx]
    logger.info(f"🎉 最终选定创意{selected_idx + 1}")

    # ========================================
    # 步骤4：展开完整新故事
    # ========================================
    logger.info("📝 步骤4：展开完整新故事...")

    messages = [
        {
            "role": "system",
            "content": prompt.STORY_EXPAND_SYSTEM,
        },
        {
            "role": "user",
            "content": prompt.STORY_EXPAND_USER_TEMPLATE.substitute(
                final_idea=final_idea,
                reason=selection_result,
                instruction=instruction
            ),
        }
    ]

    new_story = chat_with_model(
        api_key=api_key,
        model_type="qwen",
        model="qwen-max",
        messages=messages
    )
    logger.info(f"✅ 新故事生成完成：\n{new_story}\n")

    return {
        "ori_story": ori_story,
        "ideas": new_story_ideas,
        "selected_idea": final_idea,
        "selection_reason": selection_result,
        "new_story": new_story
    }


def tkg_sync_new_story_frames(api_key: str, ori_images: list, new_story: str, instruction: str, negative_prompt: str = None,
                          size: str = "1280*720"):
    # ========================================
    # 生成新的图提示词
    # ========================================
    new_image_path_list = []
    new_image_url_list = []
    logger.info("生成图提示词，开始...")
    for index, ori_image in enumerate(ori_images, start=1):
        # 打印当前循环进度
        logger.info(f"🔄 开始生成第 {index}/{len(ori_images)} 个生图提示词...")
        # 根据图片信息，重新生成生图提示词
        image_url = ori_image["url"]
        image_info = ori_image["info"]
        messages = [
            {
                "role": "system",
                "content": prompt.IMAGE_PROMPT_SYNC_SYSTEM_TEMPLATE,
            },
            {
                "role": "user",
                "content": prompt.IMAGE_PROMPT_SYNC_USER_TEMPLATE.substitute(image_info=image_info, new_story=new_story,
                                                                             instruction=instruction),
            }
        ]
        image_sync_prompt = chat_with_model(api_key=api_key, model_type="qwen", model="qwen-max", messages=messages)
        logger.info(f"🎨 第 {index} 个绘画提示词生成完成：\n{image_sync_prompt}")

        # 根据生图提示词生图
        logger.info(f"🔄 开始生成第 {index}/{len(ori_images)} 个新图...")
        new_image_path, new_image_url = sync_t2i_wan_v25(
            api_key=api_key,
            prompt=image_sync_prompt,
            negative_prompt=negative_prompt,
            size=size,
            save_dir=cfg.PICTURE_RESULTS_DIR
        )
        new_image_path_list.append(new_image_path)
        new_image_url_list.append(new_image_url)
        logger.info(f"✅ 第 {index} 个新图生成完成：新图已保存至：{new_image_path}")

    return new_image_path_list, new_image_url_list





if __name__ == "__main__":
    import os
    import time  # 添加时间模块
    from dotenv import load_dotenv
    from config.logging_config import setup_logging

    setup_logging()

    logger.info("📋 初始化配置参数")
    # hack csy 20251107:这个加载环境变量的方式，在不同的路径都会改变，回头有时间优化一下
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../env/default.env"))
    api_key = os.getenv("DASHSCOPE_API_KEY")
    #
    # # 检查API密钥是否成功加载
    # if not api_key:
    #     raise ValueError("未找到DashScope API密钥，请检查环境变量DASHSCOPE_API_KEY是否正确配置")
    #
    # start_time = time.time()
    #
    # images_dict_list = []
    # new_story = ""
    #
    # new_image_path, new_image_url = sync_new_story_images(api_key, images_dict_list, new_story, "", "", "1280*720")
    #
    # # 记录结束时间并计算运行时间
    # end_time = time.time()
    # print(f"token_calculate 运行时间: {end_time - start_time:.4f} 秒")
