#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 测试数据或模块
Output: 测试结果
Pos: 测试文件：process_video_demo.py
"""

"""
处理指定视频的说话人分离
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from component.diarization import WhisperDiarization
from config.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def main():
    """处理视频音频"""
    print("=" * 80)
    print("🎤 视频说话人分离处理")
    print("=" * 80)
    
    # 音频文件路径（已从视频提取）
    audio_path = project_root / "data" / "Data_results" / "audio_results" / "33189855772-1-192.mp3"
    
    print(f"\n📁 音频文件: {audio_path.name}")
    print(f"   路径: {audio_path}")
    
    if not audio_path.exists():
        print("\n❌ 音频文件不存在")
        return
    
    # 初始化 Whisper Diarization
    print("\n🚀 初始化 Whisper Diarization...")
    try:
        diarizer = WhisperDiarization()
        print("✅ 初始化成功")
    except FileNotFoundError as e:
        print(f"\n❌ 错误: {e}")
        print("\n📖 请先安装 whisper-diarization:")
        print("   cd ~/Code/Python/AI_vedio_demo")
        print("   git clone https://github.com/MahmoudAshraf97/whisper-diarization.git")
        print("   cd whisper-diarization")
        print("   pip install -c constraints.txt -r requirements.txt")
        return
    
    # 处理参数
    print("\n⚙️ 处理参数:")
    print("   模型: small (平衡速度和精度)")
    print("   语言: zh (中文)")
    print("   人声分离: 开启 (去除背景音)")
    print("   设备: cpu")
    
    # 询问是否开始
    choice = input("\n是否开始处理？(y/n, 默认y): ").strip().lower() or 'y'
    
    if choice != 'y':
        print("❌ 取消处理")
        return
    
    print("\n" + "=" * 80)
    print("🔄 开始处理音频...")
    print("⏳ 预计需要 5-10 分钟，请耐心等待...")
    print("=" * 80)
    print()
    
    # 处理音频
    result = diarizer.process_audio(
        audio_path=str(audio_path),
        whisper_model="small",
        language="zh",
        no_stem=False,  # 启用人声分离
        device="cpu"
    )
    
    print("\n" + "=" * 80)
    
    if result["success"]:
        print("✅ 处理成功！")
        print("\n📂 输出文件：")
        
        for file_type, file_path in result["output_files"].items():
            file_path_obj = Path(file_path)
            exists = "✓" if file_path_obj.exists() else "✗"
            size = ""
            if file_path_obj.exists():
                size_bytes = file_path_obj.stat().st_size
                if size_bytes < 1024:
                    size = f" ({size_bytes} B)"
                elif size_bytes < 1024 * 1024:
                    size = f" ({size_bytes / 1024:.1f} KB)"
                else:
                    size = f" ({size_bytes / 1024 / 1024:.1f} MB)"
            
            print(f"   {exists} {file_type:6s}: {file_path}{size}")
        
        # 显示字幕预览
        srt_path = result["output_files"]["srt"]
        if Path(srt_path).exists():
            print("\n📝 字幕预览（前 10 条）：")
            print("=" * 80)
            
            subtitles = diarizer.read_srt(srt_path)
            for sub in subtitles[:10]:
                print(f"[{sub['speaker']}] {sub['start']} --> {sub['end']}")
                print(f"  {sub['text']}")
                print()
            
            if len(subtitles) > 10:
                print(f"... 共 {len(subtitles)} 条字幕 ...\n")
            
            # 说话人统计
            print("📊 说话人统计：")
            print("=" * 80)
            stats = diarizer.get_speaker_statistics(srt_path)
            
            for speaker, info in stats.items():
                print(f"{speaker}:")
                print(f"  段落数量: {info['count']}")
                print(f"  总时长: {info['duration']:.2f} 秒 ({info['duration']/60:.1f} 分钟)")
                print(f"  占比: {info['percentage']:.2f}%")
                print()
            
            # 生成纯文本摘要
            print("📄 生成文本摘要...")
            summary_path = audio_path.parent / f"{audio_path.stem}_summary.txt"
            
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write(f"视频说话人分离结果\n")
                f.write(f"=" * 80 + "\n\n")
                f.write(f"源文件: {audio_path.name}\n")
                f.write(f"处理时间: {Path(srt_path).stat().st_mtime}\n")
                f.write(f"总字幕数: {len(subtitles)}\n")
                f.write(f"说话人数: {len(stats)}\n\n")
                
                f.write("说话人统计:\n")
                f.write("-" * 80 + "\n")
                for speaker, info in stats.items():
                    f.write(f"{speaker}: {info['count']} 段, {info['duration']:.2f}秒, {info['percentage']:.2f}%\n")
                
                f.write("\n\n完整转录:\n")
                f.write("=" * 80 + "\n\n")
                
                current_speaker = None
                for sub in subtitles:
                    if sub['speaker'] != current_speaker:
                        f.write(f"\n[{sub['speaker']}]:\n")
                        current_speaker = sub['speaker']
                    f.write(f"{sub['text']} ")
            
            print(f"✅ 文本摘要已保存: {summary_path}")
            
    else:
        print(f"❌ 处理失败: {result['error']}")
    
    print("\n" + "=" * 80)
    print("✅ 完成")
    print("=" * 80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️ 用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 异常: {e}")
        import traceback
        traceback.print_exc()
