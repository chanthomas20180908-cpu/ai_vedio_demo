"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 测试数据或模块
Output: 测试结果
Pos: 测试文件：helloworld.py
"""

from http import HTTPStatus
import os
from openai import OpenAI
from dotenv import load_dotenv

# 指定加载 env/default.env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../env/default.env"))
API_KEY = os.getenv("DASHSCOPE_API_KEY")

client = OpenAI(
    # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
    api_key=API_KEY,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

completion = client.chat.completions.create(
    # 模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
    model="qwen-plus",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "你是谁？"},
    ],
    # Qwen3模型通过enable_thinking参数控制思考过程（开源版默认True，商业版默认False）
    # 使用Qwen3开源版模型时，若未启用流式输出，请将下行取消注释，否则会报错
    # extra_body={"enable_thinking": False},
)
answer_in_json = completion.model_dump_json()
print(f"LLM答案:\n{answer_in_json}")
# print(completion.model_dump_json())


# # Step 2: 调用 TTS（以科大讯飞为例）
# from aip import AipSpeech  # 百度的示例，讯飞类似
#
# APP_ID = '你的APP_ID'
# API_KEY = '你的API_KEY'
# SECRET_KEY = '你的SECRET_KEY'
# client = AipSpeech(APP_ID, API_KEY, SECRET_KEY)
#
#
# def text_to_speech(text):
#     result = client.synthesis(text, 'zh', 1, {'vol': 5, 'per': 4})
#     if not isinstance(result, dict):
#         with open('output.mp3', 'wb') as f:
#             f.write(result)
#
# # Step 3: 串起来
# user_input = "你好，可以介绍一下你自己吗？"
# answer = ask_llm(user_input)
# print("模型回答：", answer)
# text_to_speech(answer)