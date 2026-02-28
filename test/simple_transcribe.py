#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 测试数据或模块
Output: 测试结果
Pos: 测试文件：simple_transcribe.py
"""

"""
简单的语音转录（不含说话人分离）
使用 faster-whisper 进行转录
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from faster_whisper import WhisperModel
from config.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def transcribe_audio(audio_path: str, model_size: str = "small", language: str = "zh"):
    """
    转录音频文件
    
    Args:
        audio_path: 音频文件路径
        model_size: 模型大小（tiny/base/small/medium/large）
        language: 语言代码
    """
    audio_path = Path(audio_path)
    
    if not audio_path.exists():
        print(f"❌ 音频文件不存在: {audio_path}")
        return
    
    print("=" * 80)
    print("🎤 Whisper 语音转录")
    print("=" * 80)
    print(f"\n📁 音频文件: {audio_path.name}")
    print(f"📊 模型大小: {model_size}")
    print(f"🌍 语言: {language}")
    print(f"💻 设备: CPU")
    
    print("\n⏳ 加载模型...")
    
    # 加载模型
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    
    print("✅ 模型加载完成")
    print("\n🔄 开始转录...\n")
    
    # 转录
    segments, info = model.transcribe(
        str(audio_path),
        language=language,
        beam_size=5,
        vad_filter=True,  # 启用语音活动检测
        vad_parameters=dict(min_silence_duration_ms=500)
    )
    
    print(f"检测到的语言: {info.language} (概率: {info.language_probability:.2f})")
    print(f"总时长: {info.duration:.2f} 秒\n")
    print("=" * 80)
    
    # 收集所有segments
    all_segments = list(segments)
    
    # 输出文件路径
    txt_path = audio_path.parent / f"{audio_path.stem}.txt"
    srt_path = audio_path.parent / f"{audio_path.stem}.srt"
    
    # 保存为纯文本
    with open(txt_path, 'w', encoding='utf-8') as f:
        for segment in all_segments:
            f.write(segment.text.strip() + " ")
    
    print(f"✅ 文本已保存: {txt_path}")
    
    # 保存为SRT字幕
    with open(srt_path, 'w', encoding='utf-8') as f:
        for i, segment in enumerate(all_segments, 1):
            # 格式化时间戳
            start_time = format_timestamp(segment.start)
            end_time = format_timestamp(segment.end)
            
            f.write(f"{i}\n")
            f.write(f"{start_time} --> {end_time}\n")
            f.write(f"{segment.text.strip()}\n\n")
    
    print(f"✅ 字幕已保存: {srt_path}")
    
    # 显示前10条
    print("\n📝 字幕预览（前10条）：")
    print("=" * 80)
    for i, segment in enumerate(all_segments[:10], 1):
        print(f"[{i}] {format_timestamp(segment.start)} --> {format_timestamp(segment.end)}")
        print(f"  {segment.text.strip()}\n")
    
    if len(all_segments) > 10:
        print(f"... 共 {len(all_segments)} 条字幕 ...")
    
    print("\n" + "=" * 80)
    print("✅ 转录完成")
    print("=" * 80)


def format_timestamp(seconds: float) -> str:
    """格式化时间戳为 SRT 格式"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


if __name__ == "__main__":
    # 音频文件路径
    audio_file = project_root / "data" / "Data_results" / "audio_results" / "33189855772-1-192.mp3"
    
    try:
        transcribe_audio(str(audio_file), model_size="small", language="zh")
    except KeyboardInterrupt:
        print("\n\n⏹️ 用户中断")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
