"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 测试数据或模块
Output: 测试结果
Pos: 测试文件：test_interactive_agent.py
"""

# file: /Users/thomaschan/Code/Python/AI_vedio_demo/pythonProject/test/test_interactive_agent.py
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from component.chat.core.unified_agent import UnifiedAgent, AgentMode
from config.logging_config import setup_logging, get_logger

# 初始化日志
setup_logging()
logger = get_logger(__name__)


def test_interactive_mode():
    """测试交互式 Agent 模式"""
    
    # 加载环境变量
    load_dotenv(dotenv_path=os.path.join(project_root, "env/default.env"))
    api_key = os.getenv("DASHSCOPE_API_KEY")
    
    if not api_key:
        logger.error("未找到 API Key")
        return
    
    # 创建 Agent (启用网络工具)
    agent = UnifiedAgent(
        api_key=api_key,
        model="qwen-plus",
        mode=AgentMode.WEB_ONLY
    )
    
    print("\n" + "=" * 70)
    print("🤖 交互式 Agent 测试")
    print("=" * 70)
    print("\n这个测试会演示当达到 max_iterations 限制时的交互式处理\n")
    
    # 设置一个较低的限制来快速触发
    test_query = "搜索抖音数字人相关的最新信息，并总结要点"
    
    print(f"📝 测试查询: {test_query}")
    print(f"⚙️  最大迭代次数: 5 (故意设置较低以触发交互)\n")
    
    # 调用 Agent (交互模式)
    result = agent.chat(
        user_input=test_query,
        max_iterations=5,
        interactive=True  # 启用交互模式
    )
    
    # 显示结果
    print("\n" + "=" * 70)
    print("📊 执行结果")
    print("=" * 70)
    print(f"\n✅ 最终回答:\n{result.get('answer', 'N/A')}")
    print(f"\n📈 迭代次数: {result.get('iterations', 0)}")
    print(f"🔧 工具调用次数: {len(result.get('tool_calls', []))}")
    print(f"🔄 是否继续执行: {result.get('continued', False)}")
    
    if result.get("warning"):
        print(f"⚠️  警告: {result.get('warning')}")
    
    # 显示所有工具调用
    print(f"\n🔧 调用了 {len(result.get('tool_calls', []))} 个工具:")
    for i, tool_call in enumerate(result.get('tool_calls', []), 1):
        name = tool_call.get('name', 'Unknown')
        success = tool_call.get('result', {}).get('success', False)
        status = '✅' if success else '❌'
        print(f"   {i}. {status} {name}")
        
        # 显示简化的参数
        args = tool_call.get('arguments', {})
        if 'url' in args:
            print(f"      URL: {args['url']}")
        if 'keyword' in args:
            print(f"      关键词: {args['keyword']}")


def test_callback_mode():
    """测试回调函数模式"""
    
    # 加载环境变量
    load_dotenv(dotenv_path=os.path.join(project_root, "env/default.env"))
    api_key = os.getenv("DASHSCOPE_API_KEY")
    
    if not api_key:
        logger.error("未找到 API Key")
        return
    
    # 创建 Agent
    agent = UnifiedAgent(
        api_key=api_key,
        model="qwen-plus",
        mode=AgentMode.WEB_ONLY
    )
    
    print("\n" + "=" * 70)
    print("🤖 回调函数模式测试")
    print("=" * 70)
    print("\n这个测试会使用自定义回调函数来自动处理达到限制的情况\n")
    
    # 自定义回调函数：自动继续执行（增加 10 次迭代）
    continue_count = [0]  # 使用列表来在闭包中修改
    
    def custom_callback(context):
        """自定义回调：最多自动继续 2 次"""
        continue_count[0] += 1
        iterations = context['iterations']
        max_iterations = context['max_iterations']
        tool_calls_count = len(context['tool_calls'])
        
        print(f"\n⚠️  达到限制 {max_iterations}，已执行 {tool_calls_count} 个工具调用")
        
        if continue_count[0] <= 2:
            print(f"🔄 自动继续执行 (第 {continue_count[0]} 次自动继续)")
            return True
        else:
            print("❌ 已达到自动继续次数上限，停止执行")
            return False
    
    test_query = "搜索抖音数字人相关的最新信息，并总结要点"
    
    print(f"📝 测试查询: {test_query}")
    print(f"⚙️  初始最大迭代次数: 3")
    print(f"⚙️  自动继续策略: 最多自动继续 2 次 (每次增加 10 次迭代)\n")
    
    # 调用 Agent (使用回调函数)
    result = agent.chat(
        user_input=test_query,
        max_iterations=3,
        on_max_iterations=custom_callback
    )
    
    # 显示结果
    print("\n" + "=" * 70)
    print("📊 执行结果")
    print("=" * 70)
    print(f"\n✅ 最终回答:\n{result.get('answer', 'N/A')}")
    print(f"\n📈 迭代次数: {result.get('iterations', 0)}")
    print(f"🔧 工具调用次数: {len(result.get('tool_calls', []))}")
    print(f"🔄 是否继续执行: {result.get('continued', False)}")
    print(f"🔄 自动继续次数: {continue_count[0]}")


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("🚀 交互式 Agent 功能测试")
    print("=" * 70)
    print("\n请选择测试模式:")
    print("  1. 交互式模式 (手动选择是否继续)")
    print("  2. 回调函数模式 (自动处理)")
    print("  3. 两种模式都测试")
    
    choice = input("\n请选择 (1-3, 默认1): ").strip() or "1"
    
    if choice == "1":
        test_interactive_mode()
    elif choice == "2":
        test_callback_mode()
    elif choice == "3":
        test_interactive_mode()
        print("\n\n" + "=" * 70)
        print("即将开始第二个测试...")
        print("=" * 70)
        input("\n按 Enter 继续...")
        test_callback_mode()
    else:
        print("无效选择")


if __name__ == "__main__":
    main()
