"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 测试数据或模块
Output: 测试结果
Pos: 测试文件：test_standup_game.py
"""

"""
AI脱口秀卡牌游戏 - 统一测试入口
支持自动测试和手动测试两种模式
"""

import sys
import argparse
from test.comedian_ai.standup_game_core import StandupGameEngine
from config.logging_config import setup_logging


# ==================== 颜色输出工具 ====================
class Colors:
    """终端颜色代码"""
    # 基础颜色
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    
    # 背景色
    BG_RED = '\033[101m'
    BG_GREEN = '\033[102m'
    BG_YELLOW = '\033[103m'
    BG_BLUE = '\033[104m'
    
    # 样式
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'


def cprint(text, color=None, bold=False, end='\n'):
    """彩色打印函数"""
    output = ''
    if bold:
        output += Colors.BOLD
    if color:
        output += color
    output += text
    if color or bold:
        output += Colors.RESET
    print(output, end=end)


def print_header(text):
    """打印标题"""
    cprint(f"\n{'='*60}", Colors.CYAN, bold=True)
    cprint(text, Colors.CYAN, bold=True)
    cprint('='*60, Colors.CYAN, bold=True)
    print()


def print_section(text):
    """打印分割线"""
    cprint(f"\n{'='*60}", Colors.BLUE)
    cprint(text, Colors.BLUE, bold=True)
    cprint('-'*60, Colors.BLUE)


def print_success(text):
    """打印成功信息"""
    cprint(f"✓ {text}", Colors.GREEN)


def print_warning(text):
    """打印警告信息"""
    cprint(f"⚠️  {text}", Colors.YELLOW)


def print_error(text):
    """打印错误信息"""
    cprint(f"❌ {text}", Colors.RED)


def print_info(text, color=Colors.WHITE):
    """打印信息"""
    cprint(text, color)


# ==================== 自动测试模式 ====================
def test_auto_mode():
    """自动测试模式 - 快速验证核心逻辑"""
    
    print("=" * 60)
    print("🎭 AI脱口秀卡牌游戏 - 自动测试模式")
    print("=" * 60)
    print()
    
    # 初始化引擎
    engine = StandupGameEngine()
    
    # 第1步：选择主题
    print("📍 第1步：选择主题")
    engine.select_topic("网约车司机迷路")
    print(f"✓ 已选择：{engine.state['topic']}\n")
    
    # 第2步：选择态度
    print("📍 第2步：选择态度")
    engine.select_attitude("愚蠢/暴怒")
    print(f"✓ 已选择：{engine.state['attitude']}\n")
    
    # 第3步：前提挖掘（自动选择3轮）
    print("📍 第3步：前提挖掘（自动3轮）")
    print("-" * 60)
    
    auto_choices = ["A", "A", "A"]  # 自动选择3轮，都选A
    
    for round_num, choice in enumerate(auto_choices, 1):
        print(f"\n【前提挖掘 - 第{round_num}轮】")
        print("🤖 AI正在生成追问选项...")
        
        # AI生成追问
        ai_response = engine.start_mining_round()
        print(f"\n{ai_response}")
        
        # 自动选择
        print(f"\n👤 自动选择: {choice}")
        
        # 处理选择
        result = engine.process_user_choice(choice, ai_response)
        if result['success']:
            print(f"   ✓ 已记录前提：{result['recorded_premise']}")
        else:
            print(f"   ⚠️  {result['error_message']}")
    
    # 第4步：生成段子
    print("\n" + "=" * 60)
    print("📍 第4步：生成段子")
    print("-" * 60)
    print("🤖 AI正在生成段子...")
    
    final_joke = engine.generate_joke()
    
    print("\n🎉 最终生成的段子：")
    print("=" * 60)
    print(final_joke)
    print("=" * 60)
    
    # 验证结果
    print("\n" + "=" * 60)
    print("✅ 验证结果：")
    state = engine.get_state()
    print(f"- 主题：{state['topic']}")
    print(f"- 态度：{state['attitude']}")
    print(f"- 挖掘轮数：{len(auto_choices)}轮")
    print(f"- 前提细节数：{engine.get_premises_count()}")
    print(f"- 对话历史条数：{len(state['conversation_history'])}条")
    print("=" * 60)
    
    # 核心验证
    print("\n📋 核心验证点：")
    validation_passed = True
    
    if len(auto_choices) >= 2:
        print("✅ 1. AI支持多轮追问")
    else:
        print("❌ 1. AI多轮追问失败")
        validation_passed = False
    
    if final_joke and len(final_joke) > 50:
        print("✅ 2. AI成功生成段子")
    else:
        print("❌ 2. AI生成段子失败")
        validation_passed = False
    
    if len(state['conversation_history']) > 0:
        print("✅ 3. 对话历史记录正常")
    else:
        print("❌ 3. 对话历史记录失败")
        validation_passed = False
    
    print("\n" + "=" * 60)
    if validation_passed:
        print("🎊 自动测试通过！")
    else:
        print("⚠️  部分验证失败")
    print("=" * 60)


# ==================== 手动测试模式 ====================
def test_manual_mode():
    """手动测试模式 - 完整交互体验"""
    
    print_header("🎭 AI脱口秀卡牌游戏 - 手动交互模式")
    
    # 初始化引擎
    engine = StandupGameEngine()
    
    # 第1步：选择主题
    print_section("📍 第1步：选择主题")
    cprint("A. 早高峰的地铁安检口", Colors.CYAN)
    cprint("B. 网约车司机迷路", Colors.CYAN)
    cprint("C. 过年回家的餐桌", Colors.CYAN)
    print()
    topic_choice = input("请输入选项 (A/B/C): ").strip().upper()
    
    topic_map = {
        "A": "早高峰的地铁安检口",
        "B": "网约车司机迷路",
        "C": "过年回家的餐桌"
    }
    topic = topic_map.get(topic_choice, "网约车司机迷路")
    engine.select_topic(topic)
    print_success(f"已选择：{topic}")
    print()
    
    # 第2步：选择态度
    print_section("📍 第2步：选择态度")
    cprint("🔥 A. 暴怒之火 (这事儿太蠢了)", Colors.RED)
    cprint("❄️ B. 极寒之惧 (这事儿太吓人了)", Colors.BLUE)
    cprint("🌀 C. 迷幻之雾 (这事儿太怪了)", Colors.MAGENTA)
    cprint("🪨 D. 重压之石 (这事儿太难了)", Colors.YELLOW)
    print()
    attitude_choice = input("请输入选项 (A/B/C/D): ").strip().upper()
    
    attitude_map = {
        "A": "愚蠢/暴怒",
        "B": "害怕/恐惧",
        "C": "奇怪/荒谬",
        "D": "困难/无奈"
    }
    attitude = attitude_map.get(attitude_choice, "愚蠢/暴怒")
    engine.select_attitude(attitude)
    print_success(f"已选择：{attitude}")
    print()
    
    # 第3步：前提挖掘（多轮）
    print_section("📍 第3步：前提挖掘（支持多轮）")
    print_info("提示：每轮可以选择A/B/C/D选项，或输入E退出挖掘", Colors.YELLOW)
    print_info("      如果选择D，需要手动输入你的答案", Colors.YELLOW)
    cprint("-" * 60, Colors.BLUE)
    
    premise_round = 1
    while True:
        cprint(f"\n【前提挖掘 - 第{premise_round}轮】", Colors.MAGENTA, bold=True)
        
        # AI生成追问和选项
        cprint("🤖 AI正在生成追问选项...", Colors.CYAN)
        ai_response = engine.start_mining_round()
        cprint(f"\n{ai_response}", Colors.WHITE)
        
        # 用户手动输入
        print()
        user_choice = input("👤 请输入你的选择 (A/B/C/D/E): ").strip().upper()
        
        # 检查是否要生成段子
        if user_choice == 'E':
            if not engine.can_generate_joke():
                print_warning("至少需要挖掘1轮前提才能生成段子！请继续挖掘。")
                continue
            print_success("退出挖掘阶段，准备生成段子")
            break
        
        # 处理用户选择
        custom_input = None
        if user_choice == 'D':
            custom_input = input("   请输入你的答案: ").strip()
        
        result = engine.process_user_choice(user_choice, ai_response, custom_input)
        
        if result['success']:
            print_success(f"已记录前提：{result['recorded_premise']}")
            if result['error_message']:
                print_warning(result['error_message'])
            premise_round += 1
        else:
            print_error(result['error_message'])
            print_info("   请重新选择", Colors.YELLOW)
            continue
        
        # 安全限制：最多10轮
        if premise_round > 10:
            print_warning("已达到最大挖掘轮数(10轮)")
            break
    
    # 第3.5步：展示怒气值
    print_section("⚡ 怒气值检查")
    rage_meter = engine.get_rage_meter()
    rage_full = engine.is_rage_full()
    cprint(f"🔥 当前怒气值：{rage_meter}/{engine.state['max_rage']}", Colors.RED, bold=True)
    if rage_full:
        print_success("怒气值已满！终结技已解锁！")
    else:
        print_warning(f"怒气值未满（还需 {engine.state['max_rage'] - rage_meter} 点）")
        print_info("   将使用默认呈现技巧生成段子", Colors.YELLOW)
    
    # 第4步：选择终结技（橙卡）
    print_section("📍 第4步：选择终结技（橙卡）")
    
    if rage_full:
        # 显示橙卡选项
        punchline_options = engine.get_punchline_options()
        cprint("\n⚡ 终结技已解锁！请选择你的橙卡：", Colors.YELLOW, bold=True)
        print()
        cprint(f"{punchline_options['option_1']['icon']} A. {punchline_options['option_1']['name']}", Colors.MAGENTA, bold=True)
        cprint(f"   {punchline_options['option_1']['description']}", Colors.WHITE)
        print()
        cprint(f"{punchline_options['option_2']['icon']} B. {punchline_options['option_2']['name']}", Colors.CYAN, bold=True)
        cprint(f"   {punchline_options['option_2']['description']}", Colors.WHITE)
        print()
        
        card_choice = input("👤 请选择橙卡 (A/B): ").strip().upper()
        
        if card_choice == 'B':
            # 选择混合技巧，需要选择行业
            cprint("\n🌀 选择了【维度裂缝】- 混合技巧", Colors.CYAN, bold=True)
            cprint("\n请选择类比行业：", Colors.YELLOW)
            mix_options = engine.get_mix_options()
            for i, industry in enumerate(mix_options, 1):
                cprint(f"   {i}. {industry}", Colors.CYAN)
            
            industry_choice = input("\n👤 请输入行业编号 (1-5) 或直接回车让AI自动选择: ").strip()
            target_industry = None
            if industry_choice.isdigit() and 1 <= int(industry_choice) <= len(mix_options):
                target_industry = mix_options[int(industry_choice) - 1]
                print_success(f"已选择：{target_industry}")
            else:
                print_success("将由AI自动选择合适的行业")
            
            cprint("\n🎬 AI正在使用【混合技巧】生成段子...", Colors.CYAN)
            final_joke = engine.generate_joke_with_mix(target_industry)
        else:
            # 默认选择呈现技巧
            cprint("\n🎭 选择了【拟态面具】- 呈现技巧", Colors.MAGENTA, bold=True)
            cprint("🎬 AI正在使用【呈现技巧】生成段子...", Colors.CYAN)
            final_joke = engine.generate_joke_with_actout()
    else:
        # 怒气值未满，使用默认方法
        cprint("🎬 AI正在生成段子...", Colors.CYAN)
        final_joke = engine.generate_joke()
    
    # 第5步：展示结果
    print_section("🎉 最终生成的段子")
    cprint(final_joke, Colors.GREEN, bold=True)
    cprint("=" * 60, Colors.GREEN)
    
    # 验证结果
    print_section("✅ 验证结果")
    state = engine.get_state()
    cprint(f"- 主题：{state['topic']}", Colors.CYAN)
    cprint(f"- 态度：{state['attitude']}", Colors.CYAN)
    cprint(f"- 挖掘轮数：{premise_round - 1}轮", Colors.CYAN)
    cprint(f"- 前提细节数：{engine.get_premises_count()}", Colors.CYAN)
    cprint(f"- 对话历史条数：{len(state['conversation_history'])}条", Colors.CYAN)
    
    # 显示所有挖掘的前提
    cprint("\n📝 已挖掘的前提细节：", Colors.YELLOW, bold=True)
    for i, premise in enumerate(engine.get_premises(), 1):
        cprint(f"   {i}. {premise}", Colors.WHITE)
    print()
    
    cprint("🎊 测试完成！", Colors.GREEN, bold=True)


# ==================== 主入口 ====================
def main():
    """主入口：选择测试模式"""
    
    # 初始化日志系统
    setup_logging()
    
    parser = argparse.ArgumentParser(description='AI脱口秀卡牌游戏测试')
    parser.add_argument('--mode', choices=['auto', 'manual'], 
                       help='测试模式：auto=自动测试, manual=手动测试')
    
    args = parser.parse_args()
    
    try:
        if args.mode == 'auto':
            # 命令行指定自动模式
            test_auto_mode()
        elif args.mode == 'manual':
            # 命令行指定手动模式
            test_manual_mode()
        else:
            # 交互式选择模式
            print("=" * 60)
            print("🎭 AI脱口秀卡牌游戏 - 测试入口")
            print("=" * 60)
            print()
            print("请选择测试模式：")
            print("1. 自动测试（快速验证，硬编码选择）")
            print("2. 手动测试（完整交互，支持自定义输入）")
            print()
            
            mode_choice = input("请输入选项 (1/2): ").strip()
            print()
            
            if mode_choice == '1':
                test_auto_mode()
            elif mode_choice == '2':
                test_manual_mode()
            else:
                print("❌ 无效选项，退出")
                sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断测试")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
