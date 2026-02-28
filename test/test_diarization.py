#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 测试数据或模块
Output: 测试结果
Pos: 测试文件：test_diarization.py
"""

"""
Whisper Diarization 测试脚本
测试语音说话人分离功能
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from component.diarization import WhisperDiarization
from config.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def test_diarization_basic():
    """基础测试：处理示例音频"""
    print("=" * 80)
    print("🎤 Whisper Diarization 基础测试")
    print("=" * 80)
    
    try:
        # 初始化客户端
        print("\n1️⃣ 初始化 Whisper Diarization 客户端...")
        diarizer = WhisperDiarization()
        print("✅ 客户端初始化成功")
        
        # 准备测试音频
        print("\n2️⃣ 准备测试音频...")
        print("📝 说明：请准备一个音频文件用于测试")
        print("   支持格式：mp3, wav, m4a, flac 等")
        print("   建议：2-3人对话，时长1-5分钟")
        
        # 检查是否有示例音频
        audio_dir = project_root / "data" / "Data_results" / "audio_results"
        audio_files = []
        
        if audio_dir.exists():
            audio_files = list(audio_dir.glob("*.mp3")) + list(audio_dir.glob("*.wav"))
        
        if audio_files:
            test_audio = audio_files[0]
            print(f"\n✅ 找到测试音频: {test_audio.name}")
            print(f"   路径: {test_audio}")
            
            # 询问是否处理
            choice = input("\n是否开始处理？(y/n, 默认n): ").strip().lower()
            
            if choice == 'y':
                print("\n3️⃣ 开始处理音频...")
                print("⏳ 这可能需要几分钟，请耐心等待...")
                print("-" * 80)
                
                result = diarizer.process_audio(
                    audio_path=str(test_audio),
                    whisper_model="small",  # 使用 small 模型平衡速度和精度
                    language="zh",           # 中文
                    no_stem=False,           # 启用人声分离
                    device="cpu"             # 使用 CPU（MacOS）
                )
                
                print("-" * 80)
                
                if result["success"]:
                    print("\n✅ 处理成功！")
                    print("\n📂 输出文件：")
                    for file_type, file_path in result["output_files"].items():
                        exists = "✓" if Path(file_path).exists() else "✗"
                        print(f"   {exists} {file_type:6s}: {file_path}")
                    
                    # 显示字幕预览
                    srt_path = result["output_files"]["srt"]
                    if Path(srt_path).exists():
                        print("\n📝 字幕预览（前5条）：")
                        print("-" * 80)
                        subtitles = diarizer.read_srt(srt_path)
                        for sub in subtitles[:5]:
                            print(f"[{sub['speaker']}] {sub['start']} --> {sub['end']}")
                            print(f"  {sub['text']}")
                            print()
                        
                        # 说话人统计
                        print("\n📊 说话人统计：")
                        print("-" * 80)
                        stats = diarizer.get_speaker_statistics(srt_path)
                        for speaker, info in stats.items():
                            print(f"{speaker}:")
                            print(f"  段落数: {info['count']}")
                            print(f"  总时长: {info['duration']:.2f} 秒")
                            print(f"  占比: {info['percentage']:.2f}%")
                            print()
                else:
                    print(f"\n❌ 处理失败: {result['error']}")
            else:
                print("\n⏭️ 跳过处理")
        else:
            print("\n⚠️ 未找到测试音频")
            print(f"   请将音频文件放到: {audio_dir}")
        
    except FileNotFoundError as e:
        print(f"\n❌ 错误: {e}")
        print("\n📖 解决方法：")
        print("   1. 打开终端")
        print("   2. 执行以下命令：")
        print("      cd ~/Code/Python/AI_vedio_demo")
        print("      git clone https://github.com/MahmoudAshraf97/whisper-diarization.git")
        print("      cd whisper-diarization")
        print("      pip install -c constraints.txt -r requirements.txt")
    except Exception as e:
        print(f"\n❌ 异常: {e}")
        logger.error("测试失败", exc_info=True)
    
    print("\n" + "=" * 80)
    print("✅ 测试完成")
    print("=" * 80)


def test_diarization_custom():
    """自定义测试：手动指定音频文件"""
    print("=" * 80)
    print("🎤 Whisper Diarization 自定义测试")
    print("=" * 80)
    
    try:
        # 初始化客户端
        diarizer = WhisperDiarization()
        
        # 输入音频路径
        print("\n请输入音频文件路径（或拖拽文件到终端）：")
        audio_path = input("路径: ").strip().strip("'\"")
        
        if not audio_path:
            print("❌ 未输入路径")
            return
        
        audio_path = Path(audio_path).expanduser().resolve()
        
        if not audio_path.exists():
            print(f"❌ 文件不存在: {audio_path}")
            return
        
        # 选择模型
        print("\n选择 Whisper 模型：")
        print("1. tiny   - 最快（不推荐中文）")
        print("2. base   - 快速")
        print("3. small  - 推荐（平衡）")
        print("4. medium - 高精度")
        print("5. large  - 最高精度（最慢）")
        model_choice = input("选择 (1-5, 默认3): ").strip() or "3"
        
        models = {
            "1": "tiny",
            "2": "base",
            "3": "small",
            "4": "medium",
            "5": "large"
        }
        whisper_model = models.get(model_choice, "small")
        
        # 选择语言
        print("\n选择语言：")
        print("1. 中文 (zh)")
        print("2. 英文 (en)")
        print("3. 日文 (ja)")
        print("4. 其他（手动输入）")
        lang_choice = input("选择 (1-4, 默认1): ").strip() or "1"
        
        langs = {
            "1": "zh",
            "2": "en",
            "3": "ja"
        }
        
        if lang_choice == "4":
            language = input("输入语言代码: ").strip()
        else:
            language = langs.get(lang_choice, "zh")
        
        # 其他选项
        no_stem = input("\n是否跳过人声分离？(y/n, 默认n): ").strip().lower() == 'y'
        
        print("\n" + "=" * 80)
        print("🚀 开始处理")
        print("=" * 80)
        print(f"音频文件: {audio_path.name}")
        print(f"Whisper 模型: {whisper_model}")
        print(f"语言: {language}")
        print(f"人声分离: {'关闭' if no_stem else '开启'}")
        print("⏳ 处理中，请稍候...")
        print("=" * 80)
        
        result = diarizer.process_audio(
            audio_path=str(audio_path),
            whisper_model=whisper_model,
            language=language,
            no_stem=no_stem,
            device="cpu"
        )
        
        print("=" * 80)
        
        if result["success"]:
            print("\n✅ 处理成功！")
            print("\n📂 输出文件：")
            for file_type, file_path in result["output_files"].items():
                print(f"   {file_type}: {file_path}")
            
            # 显示部分结果
            srt_path = result["output_files"]["srt"]
            if Path(srt_path).exists():
                subtitles = diarizer.read_srt(srt_path)
                print(f"\n📝 共生成 {len(subtitles)} 条字幕")
                
                stats = diarizer.get_speaker_statistics(srt_path)
                print(f"\n📊 识别到 {len(stats)} 个说话人")
                for speaker, info in stats.items():
                    print(f"   {speaker}: {info['count']} 段, {info['duration']:.2f}秒, {info['percentage']:.2f}%")
        else:
            print(f"\n❌ 处理失败: {result['error']}")
        
    except Exception as e:
        print(f"\n❌ 异常: {e}")
        logger.error("测试失败", exc_info=True)
    
    print("\n" + "=" * 80)


def show_menu():
    """显示菜单"""
    print("\n" + "=" * 80)
    print("🎤 Whisper Diarization 测试工具")
    print("=" * 80)
    print("\n选择测试模式：")
    print("1. 基础测试（自动查找测试音频）")
    print("2. 自定义测试（手动指定音频）")
    print("3. 退出")
    print("=" * 80)
    
    choice = input("\n请选择 (1-3): ").strip()
    
    if choice == "1":
        test_diarization_basic()
    elif choice == "2":
        test_diarization_custom()
    elif choice == "3":
        print("👋 再见！")
        sys.exit(0)
    else:
        print("❌ 无效选择")
        show_menu()


if __name__ == "__main__":
    try:
        show_menu()
    except KeyboardInterrupt:
        print("\n\n👋 用户中断，退出")
        sys.exit(0)
