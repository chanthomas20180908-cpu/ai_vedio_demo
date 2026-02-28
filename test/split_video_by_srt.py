#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 测试数据或模块
Output: 测试结果
Pos: 测试文件：split_video_by_srt.py
"""

"""
根据SRT字幕文件拆分视频
"""
import re
import subprocess
from pathlib import Path
from typing import List, Tuple


def parse_srt(srt_path: Path) -> List[Tuple[float, float, str]]:
    """
    解析SRT文件
    
    Returns:
        List of (start_time, end_time, text)
    """
    segments = []
    
    with open(srt_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 分割每个字幕块
    blocks = content.strip().split('\n\n')
    
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) < 3:
            continue
        
        # 解析时间轴
        time_line = lines[1]
        match = re.match(r'(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> (\d{2}):(\d{2}):(\d{2}),(\d{3})', time_line)
        
        if match:
            h1, m1, s1, ms1, h2, m2, s2, ms2 = map(int, match.groups())
            
            start_time = h1 * 3600 + m1 * 60 + s1 + ms1 / 1000.0
            end_time = h2 * 3600 + m2 * 60 + s2 + ms2 / 1000.0
            
            text = '\n'.join(lines[2:])
            
            segments.append((start_time, end_time, text))
    
    return segments


def split_video_by_srt(video_path: str, srt_path: str, output_dir: str = None, end_buffer: float = 0.5):
    """
    根据SRT字幕将视频拆分成多个片段
    
    Args:
        video_path: 视频文件路径
        srt_path: SRT字幕文件路径
        output_dir: 输出目录（默认为视频所在目录的segments子目录）
        end_buffer: 结束时间缓冲（秒），避免片段末尾包含下一片段开头，默认0.1秒
    """
    video_path = Path(video_path)
    srt_path = Path(srt_path)
    
    if not video_path.exists():
        print(f"❌ 视频文件不存在: {video_path}")
        return
    
    if not srt_path.exists():
        print(f"❌ SRT文件不存在: {srt_path}")
        return
    
    # 设置输出目录
    if output_dir is None:
        output_dir = video_path.parent / "segments"
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(exist_ok=True)
    
    print("=" * 80)
    print("✂️  视频拆分")
    print("=" * 80)
    print(f"📹 视频: {video_path.name}")
    print(f"📝 字幕: {srt_path.name}")
    print(f"📁 输出: {output_dir}")
    
    # 解析SRT
    print("\n⏳ 解析SRT文件...")
    segments = parse_srt(srt_path)
    print(f"✅ 找到 {len(segments)} 个片段")
    
    # 拆分视频
    print("\n✂️  开始拆分视频...\n")
    
    for i, (start_time, end_time, text) in enumerate(segments, 1):
        # 应用结束缓冲，避免片段末尾包含下一片段开头
        duration = end_time - start_time - end_buffer
        # 确保duration不会是负数
        if duration < 0.1:
            duration = end_time - start_time
        
        output_file = output_dir / f"{video_path.stem}_segment_{i:03d}.mp4"
        
        # ffmpeg命令：从start_time开始，持续duration秒
        cmd = [
            "ffmpeg", "-i", str(video_path),
            "-ss", str(start_time),
            "-t", str(duration),
            "-c:v", "libx264",  # 重新编码视频
            "-c:a", "aac",      # 重新编码音频
            "-y",               # 覆盖已存在文件
            str(output_file)
        ]
        
        actual_end = start_time + duration
        print(f"[{i}/{len(segments)}] {start_time:.2f}s - {actual_end:.2f}s ({duration:.2f}s) [buffer: {end_buffer}s]")
        print(f"    文本: {text[:50]}{'...' if len(text) > 50 else ''}")
        
        # 执行ffmpeg
        result = subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False
        )
        
        if result.returncode == 0:
            print(f"    ✅ {output_file.name}")
        else:
            print(f"    ❌ 失败: {output_file.name}")
        
        print()
    
    print("=" * 80)
    print(f"✅ 完成！共生成 {len(segments)} 个视频片段")
    print(f"📁 输出目录: {output_dir}")
    print("=" * 80)


if __name__ == "__main__":
    video_file = "/Users/thomaschan/Code/My_files/my_files/my_scripts/爆款复刻20251106/segment_test/segment_001.mp4"
    srt_file = "/Users/thomaschan/Code/My_files/my_files/my_scripts/爆款复刻20251106/segment_test/segment_001.srt"
    
    split_video_by_srt(video_file, srt_file)
