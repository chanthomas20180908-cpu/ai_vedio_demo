#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 测试数据或模块
Output: 测试结果
Pos: 测试文件：extract_video_srt.py
"""

"""
从视频提取字幕到SRT文件
"""
import sys
import subprocess
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from faster_whisper import WhisperModel


def extract_audio_from_video(video_path: Path) -> Path:
    """从视频提取音频"""
    audio_path = video_path.parent / f"{video_path.stem}_temp.mp3"
    
    cmd = [
        "ffmpeg", "-i", str(video_path),
        "-vn", "-acodec", "libmp3lame",
        "-ar", "16000", "-ac", "1",
        "-ab", "128k", "-y",
        str(audio_path)
    ]
    
    print(f"🎬 提取音频: {video_path.name}")
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(f"✅ 音频已提取")
    
    return audio_path


def transcribe_to_srt(audio_path: Path, output_srt: Path, model_size: str = "small", language: str = "zh"):
    """转录音频并保存为SRT"""

    def format_timestamp(seconds: float) -> str:
        """格式化时间戳为 SRT 格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds - int(seconds)) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    print(f"\n⏳ 加载 Whisper 模型 ({model_size})...")
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    
    print("🔄 开始转录...")
    segments, info = model.transcribe(
        str(audio_path),
        language=language,
        beam_size=5,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500)
    )
    
    print(f"✅ 语言: {info.language} (概率: {info.language_probability:.2f})")
    print(f"✅ 时长: {info.duration:.2f} 秒")
    
    # 保存SRT
    all_segments = list(segments)
    with open(output_srt, 'w', encoding='utf-8') as f:
        for i, segment in enumerate(all_segments, 1):
            start_time = format_timestamp(segment.start)
            end_time = format_timestamp(segment.end)
            
            f.write(f"{i}\n")
            f.write(f"{start_time} --> {end_time}\n")
            f.write(f"{segment.text.strip()}\n\n")
    
    print(f"✅ 字幕已保存: {output_srt}")
    print(f"📊 共 {len(all_segments)} 条字幕")


def format_timestamp(seconds: float) -> str:
    """格式化时间戳为 SRT 格式"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def process_video(video_path: str, model_size: str = "small", language: str = "zh"):
    """处理视频：提取音频 -> 转录 -> 保存SRT"""
    video_path = Path(video_path)
    
    if not video_path.exists():
        print(f"❌ 视频文件不存在: {video_path}")
        return
    
    print("=" * 80)
    print("🎬 视频字幕提取")
    print("=" * 80)
    print(f"📁 视频: {video_path}")
    
    # 输出SRT路径（同目录）
    output_srt = video_path.parent / f"{video_path.stem}.srt"
    
    try:
        # 提取音频
        audio_path = extract_audio_from_video(video_path)
        
        # 转录
        transcribe_to_srt(audio_path, output_srt, model_size, language)
        
        # 删除临时音频
        audio_path.unlink()
        print("🗑️  临时音频已删除")
        
        print("\n" + "=" * 80)
        print("✅ 完成")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    video_file = "/Users/thomaschan/Code/My_files/my_files/my_scripts/爆款复刻20251106/segment_test/segment_001.mp4"
    process_video(video_file, model_size="small", language="zh")
