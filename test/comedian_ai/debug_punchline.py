"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 测试数据或模块
Output: 测试结果
Pos: 测试文件：debug_punchline.py
"""

"""
段子生成调试工具
快速测试 punchline 生成质量，用于提示词工程和知识库优化

使用方式：
    python3 -m test.comedian_ai.debug_punchline
    python3 -m test.comedian_ai.debug_punchline --case 2
    python3 -m test.comedian_ai.debug_punchline --kb  # 使用知识库增强
"""

import sys
import os
import argparse

from data import test_prompt

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from test.comedian_ai.standup_game_core import StandupGameEngine
from config.logging_config import setup_logging, get_logger


# ==================== 颜色输出 ====================
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

logger = get_logger(__name__)

def cprint(text, color=None, bold=False):
    output = ''
    if bold:
        output += Colors.BOLD
    if color:
        output += color
    output += text
    if color or bold:
        output += Colors.RESET
    print(output)


def print_separator(char='=', length=80, color=Colors.CYAN):
    cprint(char * length, color)


def print_header(text, color=Colors.CYAN):
    print()
    print_separator(color=color)
    cprint(text, color, bold=True)
    print_separator(color=color)
    print()


# ==================== 测试用例库 ====================
TEST_CASES = {
    1: {
        "name": "网约车司机迷路",
        "topic": "网约车司机迷路",
        "attitude": "愚蠢/暴怒",
        "premises": [
            "司机明明开着导航，却不断问我路",
            "我说东二环，他问我东二环在哪个方向",
            "他瞪大眼睛看着导航屏幕，像在等包裹出生",
            "他问我：'东二环是往东还是往西？'",
            "我强忍着说：'师傅，东二环就是往东！'"
            "他接着问：'那往东是往哪边开？你给我指一下'",
            "我一边指路一边看着导航，感觉自己像给导航做人工售后",
            "每到一个路口，他都要灵魂发问：'左拐是左边这个吗？'",
            "他还安慰我：'别急别急，我对这附近不熟，慢慢找就熟了'",
            "最后导航说：'前方到达目的地'，他停下车问我：'那现在我们在哪儿？'"
        ]
    },
    2: {
        "name": "地铁安检口奇葩乘客",
        "topic": "早高峰的地铁安检口",
        "attitude": "愚蠢/暴怒",
        "premises": [
            "乘客把包包放进安检机后，站在出口等包",
            "他一直盯着安检机屏幕看，眼睛瞪得大大的",
            "嘴里还念叨：'我的包呢？怎么还没出来？'",
            "后面排了一堆人，他就是不让",
            "安检员说：'先生，您往前走，包会自己出来的'"
            "他还小心翼翼地问安检员：'不会把我包吸进去吧？'",
            "安检员解释了三遍，他点点头，结果又原地不动，像给自己包守灵",
            "后面的人想绕过他，他还护包一样伸手拦：'等我包出来先！'",
            "包终于从另一头出来，他愣了一下，问：'这是我的吗？它怎么从那边出来了？'",
            "拿起包还认真检查了一圈，好像怀疑中间被人换了个芯"
        ]
    },
    3: {
        "name": "外卖小哥送错地址",
        "topic": "外卖小哥找不到地址",
        "attitude": "无奈/困难",
        "premises": [
            "外卖小哥打电话说到了，但我在楼下没看到他",
            "他说：'我在你们小区门口啊'",
            "我说：'哪个门口？我们有东南西北四个门'",
            "他说：'就是那个有保安的门口'",
            "我：'四个门都有保安...'"
            "他沉默了一下，说：'那你出来找我吧，我穿黄衣服的'",
            "我抬头看了一圈，发现门口一排外卖小哥，全穿黄的，像在开年会",
            "我问他：'你旁边有什么？'他说：'有个红色的门牌'",
            "我们小区四个门，全是红色门牌，物业审美特别统一",
            "最后他叹气说：'要不你给我发个定位吧，我再研究研究'",
            "五分钟后他回我：'你这个定位，是在你家里吗？我进不去啊'"
        ]
    },
    4: {
        "name": "火锅店服务员推销",
        "topic": "火锅店服务员疯狂推销",
        "attitude": "奇怪/荒谬",
        "premises": [
            "服务员每隔5分钟就来推销一次",
            "推销的理由越来越奇怪",
            "他说：'您看今天月亮这么圆，不来个海鲜拼盘？'",
            "我说：'今天没有月亮，阴天'",
            "他：'那正好！阴天适合吃牛肉，补阳气！'"
            "隔几分钟他又来：'你看这个锅底在冒泡，说明财运要来了，点个肥牛把运气锁住？'",
            "我低头看手机，他说：'您一直滑手机，说明最近心事多，要不要来个冰粉压压惊？'",
            "我刚想说饱了，他立刻接：'饱了更要吃点蔬菜，帮助消化，要不半份生菜？'",
            "连我咳嗽一声，他都能接：'您看，喉咙有点干，来个酸梅汤正好润一润'",
            "最后他总结：'反正不管晴天阴天、冷天热天，点一个招牌拼盘总没错'",
            "我感觉自己不是在吃火锅，是在现场体验一个行走的算命推广系统"
        ]
    },
    5: {
        "name": "快递驿站取件",
        "topic": "快递驿站取件体验",
        "attitude": "愚蠢/暴怒",
        "premises": [
            "驿站老板说找不到我的快递",
            "我报了取件码，他在货架上翻了半天",
            "他问我：'你确定快递在这儿？'",
            "我说：'短信写的就是这个驿站啊'",
            "他：'那你确定短信没发错？'"
            "我翻给他看短信，他眯着眼看了半天，说：'也有可能是系统瞎发的'",
            "他又问：'你是不是有好几个驿站？可能搞混了'",
            "我说：'就你这一家离我家最近的，他说：那你离得近不代表快递离得近啊'",
            "他提议：'要不你再等等，说不定它突然自己出现了？'",
            "等了十分钟他又翻了两下，同样那几排货架，翻得像在做样子给我看",
            "最后他一本正经地说：'那你回去先观察两天，实在没有，再来问问，看它要不要来'"
        ]
    }
}


# ==================== 核心调试逻辑 ====================
def load_test_case(case_id: int):
    """加载测试用例"""
    if case_id not in TEST_CASES:
        raise ValueError(f"测试用例 {case_id} 不存在，可用: {list(TEST_CASES.keys())}")
    return TEST_CASES[case_id]


def setup_engine_with_case(case_data: dict) -> StandupGameEngine:
    """使用测试用例初始化引擎"""
    engine = StandupGameEngine()
    
    # 设置主题和态度
    engine.select_topic(case_data['topic'])
    engine.select_attitude(case_data['attitude'])
    
    # 直接注入前提（跳过挖掘过程）
    engine.state['premises'] = case_data['premises'].copy()
    
    # 设置怒气值为满（解锁终结技）
    engine.state['rage_meter'] = engine.state['max_rage']
    
    return engine


def display_case_info(case_data: dict):
    """显示测试用例信息"""
    print_header("📋 测试用例信息", Colors.CYAN)
    
    cprint(f"用例名称: {case_data['name']}", Colors.YELLOW, bold=True)
    cprint(f"主题: {case_data['topic']}", Colors.WHITE)
    cprint(f"态度: {case_data['attitude']}", Colors.WHITE)
    
    print()
    cprint("已挖掘的前提:", Colors.YELLOW, bold=True)
    for i, premise in enumerate(case_data['premises'], 1):
        cprint(f"  {i}. {premise}", Colors.WHITE)
    print()


def generate_both_punchlines(engine: StandupGameEngine):
    """生成两种技巧的段子"""
    results = {}
    
    # # 生成呈现技巧段子
    # print_header("🎭 生成段子 - 呈现技巧 (Act-out)", Colors.MAGENTA)
    # cprint("🤖 AI 正在生成...", Colors.CYAN)
    # try:
    #     actout_joke = engine.generate_joke_with_actout()
    #     results['actout'] = actout_joke
    #     print()
    #     cprint(actout_joke, Colors.GREEN)
    # except Exception as e:
    #     results['actout'] = None
    #     cprint(f"❌ 生成失败: {e}", Colors.RED)
    
    # 生成混合技巧段子（两阶段）
    print_header("🌀 生成段子 - 混合技巧 (Mix) 两阶段", Colors.CYAN)
    cprint("🤖 第一阶段：生成基础类比结构...", Colors.CYAN)
    try:
        mix_result = engine.generate_joke_with_mix_v2()
        results['mix'] = mix_result
        
        # 显示第一阶段
        print()
        cprint("【第一阶段：基础版】", Colors.YELLOW, bold=True)
        cprint(f"选择行业: {mix_result['selected_industry']}", Colors.WHITE)
        cprint(mix_result['stage1_draft'], Colors.WHITE)
        
        print()
        cprint("🤖 第二阶段：喜剧强化改写...", Colors.CYAN)
        
        # 显示第二阶段
        print()
        cprint("【第二阶段：强化版】", Colors.GREEN, bold=True)
        cprint(mix_result['stage2_enhanced'], Colors.GREEN)
        
    except Exception as e:
        results['mix'] = None
        cprint(f"❌ 生成失败: {e}", Colors.RED)
    
    return results


def analyze_jokes(results: dict):
    """分析段子质量"""
    print_header("📊 段子分析", Colors.YELLOW)
    
    for technique, content in results.items():
        if content:
            cprint(f"\n【{technique.upper()}】", Colors.CYAN, bold=True)
            
            # 如果是 mix 且是 dict，分析两个阶段
            if technique == 'mix' and isinstance(content, dict):
                stage1 = content['stage1_draft']
                stage2 = content['stage2_enhanced']
                
                cprint("  第一阶段：", Colors.YELLOW)
                cprint(f"    长度: {len(stage1)} 字符", Colors.WHITE)
                has_quote1 = any(char in stage1 for char in ['“', '”', '"', "'"])
                cprint(f"    包含引号: {'是' if has_quote1 else '否'}", Colors.WHITE)
                
                cprint("  第二阶段：", Colors.YELLOW)
                cprint(f"    长度: {len(stage2)} 字符", Colors.WHITE)
                has_quote2 = any(char in stage2 for char in ['“', '”', '"', "'"])
                cprint(f"    包含引号: {'是' if has_quote2 else '否'}", Colors.WHITE)
                has_dialogue = '我' in stage2 and ('他' in stage2 or '她' in stage2)
                cprint(f"    包含对话: {'是' if has_dialogue else '否'}", Colors.WHITE)
                if len(stage1) > 0:
                    increase_pct = int((len(stage2) - len(stage1)) / len(stage1) * 100)
                    cprint(f"    增强比例: {increase_pct}%", Colors.WHITE)
            else:
                # 单一段子分析
                joke = content if isinstance(content, str) else str(content)
                cprint(f"  长度: {len(joke)} 字符", Colors.WHITE)
                has_quote = any(char in joke for char in ['“', '”', '"', "'"])
                cprint(f"  包含引号: {'是' if has_quote else '否'}", Colors.WHITE)
                has_dialogue = '我' in joke and ('他' in joke or '她' in joke)
                cprint(f"  包含对话: {'是' if has_dialogue else '否'}", Colors.WHITE)
        else:
            cprint(f"\n【{technique.upper()}】生成失败", Colors.RED)


def save_results(case_id: int, case_data: dict, results: dict):
    """保存结果到文件"""
    output_dir = os.path.join(os.path.dirname(__file__), "debug_output")
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, f"case_{case_id}_output.txt")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"测试用例: {case_data['name']}\n")
        f.write(f"主题: {case_data['topic']}\n")
        f.write(f"态度: {case_data['attitude']}\n")
        f.write("\n前提:\n")
        for i, p in enumerate(case_data['premises'], 1):
            f.write(f"  {i}. {p}\n")
        
        f.write("\n" + "="*80 + "\n")
        f.write("呈现技巧 (Act-out):\n")
        f.write("="*80 + "\n")
        f.write(results.get('actout', '生成失败') + "\n")
        
        f.write("\n" + "="*80 + "\n")
        f.write("混合技巧 (Mix) - 两阶段\n")
        f.write("="*80 + "\n")
        
        mix_result = results.get('mix')
        if mix_result and isinstance(mix_result, dict):
            f.write(f"选择行业: {mix_result['selected_industry']}\n\n")
            f.write("第一阶段（基础版）:\n")
            f.write("-" * 80 + "\n")
            f.write(mix_result['stage1_draft'] + "\n\n")
            f.write("第二阶段（强化版）:\n")
            f.write("-" * 80 + "\n")
            f.write(mix_result['stage2_enhanced'] + "\n")
        else:
            f.write('生成失败\n')
    
    cprint(f"\n💾 结果已保存到: {output_file}", Colors.GREEN)


# ==================== 主程序 ====================
def main():
    parser = argparse.ArgumentParser(description='段子生成调试工具')
    parser.add_argument('--case', type=int, default=1,
                       help='测试用例编号 (1-5)')
    parser.add_argument('--kb', action='store_true',
                       help='使用知识库增强（待实现）')
    parser.add_argument('--save', action='store_true',
                       help='保存结果到文件')
    parser.add_argument('--list', action='store_true',
                       help='列出所有测试用例')
    
    args = parser.parse_args()
    
    # 初始化日志
    setup_logging()
    logger = get_logger(__name__)
    
    # 列出所有用例
    if args.list:
        print_header("📚 可用测试用例", Colors.CYAN)
        for case_id, case_data in TEST_CASES.items():
            cprint(f"{case_id}. {case_data['name']}", Colors.YELLOW, bold=True)
            cprint(f"   主题: {case_data['topic']}", Colors.WHITE)
            cprint(f"   态度: {case_data['attitude']}", Colors.WHITE)
            cprint(f"   前提数: {len(case_data['premises'])}", Colors.WHITE)
            print()
        return
    
    try:
        # 加载测试用例
        case_data = load_test_case(args.case)
        
        # 显示用例信息
        print_header(f"🎭 AI脱口秀段子生成调试工具", Colors.CYAN)
        display_case_info(case_data)
        
        # 初始化引擎
        logger.info(f"初始化引擎，测试用例: {case_data['name']}")
        engine = setup_engine_with_case(case_data)
        
        # 生成段子
        results = generate_both_punchlines(engine)
        
        # 分析结果
        analyze_jokes(results)
        
        # 保存结果
        if args.save:
            save_results(args.case, case_data, results)
        
        print_header("✅ 调试完成", Colors.GREEN)
        
        # 提示
        print()
        cprint("💡 提示:", Colors.YELLOW, bold=True)
        cprint("  - 使用 --list 查看所有测试用例", Colors.WHITE)
        cprint("  - 使用 --case N 指定测试用例", Colors.WHITE)
        cprint("  - 使用 --save 保存结果到文件", Colors.WHITE)
        cprint("  - 使用 --kb 启用知识库增强（待实现）", Colors.WHITE)
        print()
        
    except Exception as e:
        cprint(f"\n❌ 错误: {e}", Colors.RED)
        logger.error(f"调试失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
