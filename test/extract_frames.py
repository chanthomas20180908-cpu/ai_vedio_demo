#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 测试数据或模块
Output: 测试结果
Pos: 测试文件：extract_frames.py
"""

"""
从视频中按秒抽帧截图
"""
import subprocess
from pathlib import Path


def extract_frames_by_interval(video_path: str, interval: float = 1, output_dir: str = None):
    """
    按照指定间隔从视频中抽帧
    
    Args:
        video_path: 视频文件路径
        interval: 抽帧间隔（秒），默认1秒
        output_dir: 输出目录（默认为视频所在目录的frames子目录）
    """
    video_path = Path(video_path)
    
    if not video_path.exists():
        print(f"❌ 视频文件不存在: {video_path}")
        return
    
    # 设置输出目录
    if output_dir is None:
        output_dir = video_path.parent / "frames"
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(exist_ok=True)
    
    print("=" * 80)
    print("🎬 视频抽帧")
    print("=" * 80)
    print(f"📹 视频: {video_path.name}")
    print(f"⏱️  间隔: {interval}秒")
    print(f"📁 输出: {output_dir}")
    
    # 获取视频时长
    duration_cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(video_path)
    ]
    
    try:
        result = subprocess.run(duration_cmd, capture_output=True, text=True, check=True)
        duration = float(result.stdout.strip())
        print(f"⏱️  视频时长: {duration:.2f}秒")
        
        # 计算预计帧数
        estimated_frames = int(duration // interval) + 1
        print(f"📊 预计帧数: {estimated_frames}")
        
    except Exception as e:
        print(f"⚠️  无法获取视频时长: {e}")
        duration = None
    
    # 输出文件模板
    output_pattern = output_dir / f"{video_path.stem}_frame_%04d.jpg"
    
    # ffmpeg命令：每interval秒抽一帧
    # fps=1/interval 表示每interval秒一帧
    cmd = [
        "ffmpeg", "-i", str(video_path),
        "-vf", f"fps=1/{interval}",  # 每interval秒一帧
        "-q:v", "2",                 # JPEG质量（1-31，数字越小质量越高）
        "-y",
        str(output_pattern)
    ]
    
    print("\n🔄 开始抽帧...\n")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        # 统计生成的帧数
        frames = sorted(output_dir.glob(f"{video_path.stem}_frame_*.jpg"))
        
        print(f"✅ 成功抽取 {len(frames)} 帧")
        print(f"📁 输出目录: {output_dir}")
        
        # 显示前5帧
        print("\n📸 抽帧预览：")
        print("=" * 80)
        for i, frame in enumerate(frames[:5], 1):
            file_size = frame.stat().st_size / 1024  # KB
            print(f"  [{i}] {frame.name} ({file_size:.1f} KB)")
        
        if len(frames) > 5:
            print(f"  ... 共 {len(frames)} 帧 ...")
        
        print("\n" + "=" * 80)
        print("✅ 完成")
        print("=" * 80)
        
    else:
        print(f"❌ 抽帧失败")
        print(f"错误信息: {result.stderr}")


def extract_frames_batch(video_dir: str, interval: int = 1):
    """
    批量处理目录中的所有视频文件
    
    Args:
        video_dir: 视频目录
        interval: 抽帧间隔（秒）
    """
    video_dir = Path(video_dir)
    
    if not video_dir.exists():
        print(f"❌ 目录不存在: {video_dir}")
        return
    
    # 支持的视频格式
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']
    video_files = []
    
    for ext in video_extensions:
        video_files.extend(video_dir.glob(f"*{ext}"))
    
    if not video_files:
        print(f"❌ 未找到视频文件")
        return
    
    print("=" * 80)
    print(f"🎬 批量抽帧 - 找到 {len(video_files)} 个视频")
    print("=" * 80)
    
    for i, video_file in enumerate(video_files, 1):
        print(f"\n>>> [{i}/{len(video_files)}] 处理: {video_file.name}")
        
        # 为每个视频创建独立的frames目录
        output_dir = video_file.parent / f"{video_file.stem}_frames"
        extract_frames_by_interval(str(video_file), interval, str(output_dir))
        
        print()


if __name__ == "__main__":
    video_file = "/Users/thomaschan/Code/My_files/my_files/my_scripts/爆款复刻20251106/segment_test/segment_001.mp4"
    extract_frames_by_interval(video_file, interval=1, output_dir="/Users/thomaschan/Code/My_files/my_files/my_scripts/爆款复刻20251106/segment_test/frames_001")
    
    # 示例2: 批量处理segments目录中的所有视频
    # segments_dir = "/Users/thomaschan/Code/My_files/my_files/my_scripts/爆款复刻20251106/segment_test/segments"
    # extract_frames_batch(segments_dir, interval=1)
