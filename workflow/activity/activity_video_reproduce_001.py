"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 视频处理参数
Output: 处理后的视频片段
Pos: 视频复现活动实现
"""

from pathlib import Path
from typing import List, Optional
import sys

# 添加项目根目录到 sys.path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
from workflow.taskgroup.taskgroup_video_reproduce import (
    tkg_split_video,
    tkg_extract_frame_info,
    tkg_sync_new_story,
    tkg_sync_new_story_frames
)
from config.logging_config import get_logger


logger = get_logger(__name__)


def activity_video_reproduce_001(
        api_key: str,
        video_path: str,
        instruction: str,
        output_dir: str = None,
        frame_interval: float = 2.0,
        image_understanding_instruction: str = "描述图片中的主要场景、人物、动作和情绪",
        model_size: str = "small",
        language: str = "zh",
        negative_prompt: str = None,
        size: str = "1280*720"
) -> Optional[List[str]]:
    """
    视频复刺端到端工作流
    
    工作流步骤：
    1. 视频拆分：提取音频、字幕、分镜图
    2. 图片理解：提取每个分镜图的结构化信息
    3. 故事生成：基于原视频内容生成新故事
    4. 图片生成：根据新故事生成新分镜图
    
    Args:
        api_key: API密钥
        video_path: 输入视频文件路径
        instruction: 改编指令（如：将这个视频改编为科幻风格）
        output_dir: 输出目录（默认为视频同目录）
        frame_interval: 抽帧间隔（秒），默认2秒
        image_understanding_instruction: 图片理解指令
        model_size: Whisper模型大小（small/medium/large）
        language: 音频语言（zh/en）
        negative_prompt: 负面提示词（生图时用）
        size: 生成图片尺寸（默认 1280*720）
        
    Returns:
        List[str]: 生成的新图片路径列表，失败返回 None
        
    Example:
        >>> new_images = activity_video_reproduce_001(
        ...     api_key="your_api_key",
        ...     video_path="/path/to/video.mp4",
        ...     instruction="将这个视频改编为科幻风格",
        ...     frame_interval=3.0
        ... )
    """
    logger.info("=" * 80)
    logger.info("🎬 视频复刻工作流开始")
    logger.info("=" * 80)
    logger.info(f"📹 输入视频: {video_path}")
    logger.info(f"🎯 改编指令: {instruction}")
    logger.info(f"⏱️  抽帧间隔: {frame_interval}秒")
    logger.info("=" * 80)
    
    try:
        # ========================================
        # 步骤1: 视频拆分
        # ========================================
        logger.info("\n📦 阶段1/4: 视频拆分")
        logger.info("-" * 80)
        
        split_result = tkg_split_video(
            video_path=video_path,
            output_dir=output_dir,
            frame_interval=frame_interval,
            model_size=model_size,
            language=language
        )
        
        if not split_result or not split_result.get("frame_paths"):
            logger.error("❌ 视频拆分失败或未提取到帧")
            return None
        
        frame_paths = split_result["frame_paths"]
        srt_path = split_result["srt_path"]
        
        logger.info(f"✅ 视频拆分完成: {len(frame_paths)} 帧, 字幕: {srt_path}")
        
        # ========================================
        # 步骤2: 提取图片信息
        # ========================================
        logger.info("\n📸 阶段2/4: 提取图片信息")
        logger.info("-" * 80)
        
        frame_info_result = tkg_extract_frame_info(
            api_key=api_key,
            frame_path_list=frame_paths,
            instruction=image_understanding_instruction,
            oss_expire_seconds=3600
        )
        
        if not frame_info_result or not frame_info_result.get("image_url_info_list"):
            logger.error("❌ 图片信息提取失败")
            return None
        
        image_url_info_list = frame_info_result["image_url_info_list"]
        image_info_list = frame_info_result["image_info_list"]
        
        logger.info(f"✅ 图片信息提取完成: {len(image_info_list)} 张")
        
        # ========================================
        # 步骤3: 生成新故事
        # ========================================
        logger.info("\n📝 阶段3/4: 生成新故事")
        logger.info("-" * 80)
        
        # 读取字幕文本
        subtitle_text = ""
        if srt_path and Path(srt_path).exists():
            try:
                with open(srt_path, 'r', encoding='utf-8') as f:
                    subtitle_text = f.read()
                logger.info(f"✅ 字幕文本已加载: {len(subtitle_text)} 字符")
            except Exception as e:
                logger.warning(f"⚠️  字幕读取失败: {e}")
        else:
            logger.warning("⚠️  未找到字幕文件，将仅基于图片生成故事")
        
        # 将图片信息列表转为字符串
        images_info_str = "\n".join([
            f"分镜{i+1}: {info}"
            for i, info in enumerate(image_info_list)
        ])
        
        story_result = tkg_sync_new_story(
            api_key=api_key,
            images_info=images_info_str,
            subtitle=subtitle_text,
            instruction=instruction
        )
        
        if not story_result or not story_result.get("new_story"):
            logger.error("❌ 新故事生成失败")
            return None
        
        new_story = story_result["new_story"]
        logger.info(f"✅ 新故事生成完成: {len(new_story)} 字符")
        logger.info(f"   故事预览: {new_story[:200]}...")
        
        # ========================================
        # 步骤4: 生成新分镜图
        # ========================================
        logger.info("\n🎨 阶段4/4: 生成新分镜图")
        logger.info("-" * 80)
        
        new_image_path_list, new_image_url_list = tkg_sync_new_story_frames(
            api_key=api_key,
            ori_images=image_url_info_list,
            new_story=new_story,
            instruction=instruction,
            negative_prompt=negative_prompt,
            size=size
        )
        
        if not new_image_path_list:
            logger.error("❌ 新图片生成失败")
            return None
        
        logger.info(f"✅ 新图片生成完成: {len(new_image_path_list)} 张")
        
        # ========================================
        # 完成
        # ========================================
        logger.info("\n" + "=" * 80)
        logger.info("✨ 视频复刻工作流完成")
        logger.info("=" * 80)
        logger.info(f"📊 结果统计:")
        logger.info(f"   原始帧数: {len(frame_paths)}")
        logger.info(f"   理解图片: {len(image_info_list)}")
        logger.info(f"   生成新图: {len(new_image_path_list)}")
        logger.info(f"\n📁 输出目录: {output_dir or Path(video_path).parent}")
        logger.info(f"\n🎉 成功！新图片已保存")
        logger.info("=" * 80)
        
        return new_image_path_list
        
    except Exception as e:
        logger.error(f"\n❌ 工作流执行失败: {e}")
        logger.exception(e)
        return None


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    from config.logging_config import setup_logging
    
    # 初始化日志
    setup_logging()
    
    # 加载环境变量
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../env/default.env"))
    api_key = os.getenv("DASHSCOPE_API_KEY")
    
    if not api_key:
        raise ValueError("未找到DashScope API密钥，请检查环境变量")
    
    # 示例使用
    video_path = "/Users/thomaschan/Code/My_files/my_files/my_scripts/爆款复刻20251106/segment_test/segment_001_segment_001.mp4"
    instruction = ""
    
    new_images = activity_video_reproduce_001(
        api_key=api_key,
        video_path=video_path,
        instruction=instruction,
        frame_interval=3.0,  # 每3秒抽一帧
        model_size="small",   # 使用小Whisper模型
        size="1280*720"       # 生成720p图片
    )
    
    if new_images:
        logger.info(f"\n✅ 成功生成 {len(new_images)} 张新图片")
        for i, img_path in enumerate(new_images, 1):
            logger.info(f"   [{i}] {img_path}")
    else:
        logger.error("❌ 工作流执行失败")

