"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 测试数据或模块
Output: 测试结果
Pos: 测试文件：test_directory_context.py
"""

# file: /Users/thomaschan/Code/Python/AI_vedio_demo/pythonProject/test/test_directory_context.py
"""
测试 Agent 对"同目录下"等目录上下文的理解能力
"""
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


def test_directory_context():
    """测试目录上下文理解"""
    
    # 加载环境变量
    load_dotenv(dotenv_path=os.path.join(project_root, "env/default.env"))
    api_key = os.getenv("DASHSCOPE_API_KEY")
    
    if not api_key:
        logger.error("未找到 API Key")
        return
    
    # 创建 Agent (仅启用知识库工具)
    agent = UnifiedAgent(
        api_key=api_key,
        model="qwen-plus",
        mode=AgentMode.KB_ONLY
    )
    
    print("\n" + "=" * 70)
    print("🧪 测试目录上下文理解能力")
    print("=" * 70)
    
    # 测试场景 1: 读取文件后在同目录创建新文件
    print("\n📝 场景 1: 读取 avater/淘直商品话术&问答对配置sop.md 后,在同目录创建摘要")
    print("-" * 70)
    
    # 第一步: 读取文件
    print("\n步骤 1: 读取原文件...")
    result1 = agent.chat(
        user_input="读取 avater/淘直商品话术&问答对配置sop.md 的前 500 个字符"
    )
    
    if result1.get('tool_called'):
        print(f"✅ 读取成功")
        print(f"   调用工具: {[call['name'] for call in result1.get('tool_calls', [])]}")
    
    # 第二步: 在同目录创建文件
    print("\n步骤 2: 要求在同目录创建摘要文件...")
    result2 = agent.chat(
        user_input="将这个文档的核心要点提炼成摘要,保存为 '核心要点.md',存放在同目录下",
        conversation_history=[
            {"role": "user", "content": result1.get('answer', '')}
        ]
    )
    
    print(f"\n🔧 工具调用记录:")
    for i, call in enumerate(result2.get('tool_calls', []), 1):
        print(f"   {i}. {call['name']}")
        if 'filepath' in call.get('arguments', {}):
            filepath = call['arguments']['filepath']
            print(f"      文件路径: {filepath}")
            
            # 检查路径是否正确
            if filepath.startswith('avater/'):
                print(f"      ✅ 正确: 使用了完整的目录路径")
            else:
                print(f"      ❌ 错误: 未使用完整路径,应该是 'avater/核心要点.md'")
    
    # 测试场景 2: 在指定子目录创建文件
    print("\n\n📝 场景 2: 直接指定在 test_dir 目录下创建文件")
    print("-" * 70)
    
    result3 = agent.chat(
        user_input="在 test_dir 目录下创建一个测试文件 test.txt,内容是 'Hello World'"
    )
    
    print(f"\n🔧 工具调用记录:")
    for i, call in enumerate(result3.get('tool_calls', []), 1):
        print(f"   {i}. {call['name']}")
        if 'filepath' in call.get('arguments', {}):
            filepath = call['arguments']['filepath']
            print(f"      文件路径: {filepath}")
            
            if filepath == 'test_dir/test.txt':
                print(f"      ✅ 正确: 路径格式正确")
            else:
                print(f"      ⚠️  实际路径: {filepath}")
    
    # 总结
    print("\n" + "=" * 70)
    print("📊 测试总结")
    print("=" * 70)
    print("""
改进后的 Agent 应该能够:
1. ✅ 理解"同目录下"指的是对话上下文中最近操作的文档所在目录
2. ✅ 使用完整的相对路径(相对于知识库根目录)
3. ✅ 正确解析用户指定的目录路径

关键改进点:
- 工具描述中明确说明了路径规则和"同目录"的处理方式
- 系统提示词中增加了目录上下文理解的指导
- 工具参数描述更加详细和具体
    """)


def test_with_conversation():
    """测试在完整对话中的目录理解"""
    
    load_dotenv(dotenv_path=os.path.join(project_root, "env/default.env"))
    api_key = os.getenv("DASHSCOPE_API_KEY")
    
    if not api_key:
        logger.error("未找到 API Key")
        return
    
    agent = UnifiedAgent(
        api_key=api_key,
        model="qwen-plus",
        mode=AgentMode.KB_ONLY
    )
    
    print("\n" + "=" * 70)
    print("🗣️  完整对话测试")
    print("=" * 70)
    
    conversation = [
        "列出 avater 目录下的所有文档",
        "读取其中第一个 markdown 文件的内容",
        "把这个内容总结成 200 字以内的摘要,保存到同目录下,命名为 '摘要.md'"
    ]
    
    history = []
    
    for i, user_input in enumerate(conversation, 1):
        print(f"\n👤 用户 {i}: {user_input}")
        
        result = agent.chat(
            user_input=user_input,
            conversation_history=history
        )
        
        answer = result.get('answer', '')
        print(f"🤖 助手: {answer[:200]}{'...' if len(answer) > 200 else ''}")
        
        # 更新对话历史
        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": answer})
        
        # 显示工具调用
        if result.get('tool_called'):
            print(f"\n🔧 调用了 {len(result.get('tool_calls', []))} 个工具:")
            for call in result.get('tool_calls', []):
                name = call['name']
                args = call.get('arguments', {})
                print(f"   - {name}")
                if 'filepath' in args:
                    print(f"     文件: {args['filepath']}")
                if 'directory' in args:
                    print(f"     目录: {args['directory']}")


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("🚀 Agent 目录上下文理解测试")
    print("=" * 70)
    print("\n选择测试模式:")
    print("  1. 基础场景测试")
    print("  2. 完整对话测试")
    print("  3. 两种都测试")
    
    choice = input("\n请选择 (1-3, 默认1): ").strip() or "1"
    
    if choice == "1":
        test_directory_context()
    elif choice == "2":
        test_with_conversation()
    elif choice == "3":
        test_directory_context()
        print("\n\n" + "=" * 70)
        input("\n按 Enter 继续下一个测试...")
        test_with_conversation()
    else:
        print("无效选择")


if __name__ == "__main__":
    main()
