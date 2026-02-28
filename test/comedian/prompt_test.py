"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 测试数据或模块
Output: 测试结果
Pos: 测试文件：prompt_test.py
"""

# file: /Users/thomaschan/Code/Python/AI_vedio_demo/pythonProject/component/chat.py
import os
from dotenv import load_dotenv

from component.chat.chat import chat_with_model
from config.logging_config import get_logger
from test.comedian.comedian_test_prompt import TEST_COMEDIAN_SYSTEM_PROMPT_001, TEST_USER_PROMPT_CASES

if __name__ == "__main__":
    from config.logging_config import setup_logging
    import data.test_prompt as prompt

    # Basic color codes
    class Colors:
        RED = '\033[31m'
        GREEN = '\033[32m'
        YELLOW = '\033[33m'
        BLUE = '\033[34m'
        MAGENTA = '\033[35m'
        CYAN = '\033[36m'
        WHITE = '\033[37m'
        RESET = '\033[0m'

    # 项目启动时初始化日志
    setup_logging()

    # logger.info("📋 初始化配置参数")
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../env/default.env"))

    # 测试Qwen模型
    api_key = os.getenv("DASHSCOPE_API_KEY")
    # dashscope_api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("DASHSCOPE_API_KEY 未配置")


    def test_chat(api_key,
                  messages,
                  model_type="qwen",
                  model="qwen-flash"):
        # 统一定义模型参数

        return chat_with_model(
            api_key=api_key,
            messages=messages,
            model_type=model_type,
            model=model
        )

    for case in TEST_USER_PROMPT_CASES["test_scenarios"]:
        print(f"{Colors.BLUE}case id：{case['id']}{Colors.RESET}")
        print(f"{Colors.BLUE}case input：{case['input']}{Colors.RESET}")
        if case['id'] == 2:
            break

        messages = [
            {
                "role": "system",
                "content": TEST_COMEDIAN_SYSTEM_PROMPT_001,
            },
            {
                "role": "user",
                "content": case["input"],
            }
        ]
        result = test_chat(api_key=api_key, messages=messages)
        print(f"{Colors.GREEN}case output：\n{result}{Colors.RESET}")

        print("\n===============\n")
