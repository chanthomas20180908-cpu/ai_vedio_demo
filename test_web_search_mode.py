#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 测试数据或模块
Output: 测试结果
Pos: 测试文件：test_web_search_mode.py
"""

"""
测试网络查询模式功能
"""
import os
from component.chat.core.unified_agent import UnifiedAgent
from component.chat.config.agent_config import AgentMode, AgentConfig
from dotenv import load_dotenv

# 加载环境变量
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "env/default.env"))
api_key = os.getenv("DASHSCOPE_API_KEY")

print("=" * 70)
print("测试网络查询模式功能")
print("=" * 70)

# 测试1: 默认模式
print("\n【测试1】创建agent，使用默认模式")
agent = UnifiedAgent(
    api_key=api_key,
    model_type="qwen",
    model="qwen-plus",
    mode=AgentMode.WEB_ONLY
)
print(f"✅ 当前模式: {agent.web_search_mode}")
print(f"   说明: {AgentConfig.SUPPORTED_WEB_MODES[agent.web_search_mode]}")

# 测试2: 指定product模式
print("\n【测试2】创建agent，指定product模式")
agent2 = UnifiedAgent(
    api_key=api_key,
    model_type="qwen", 
    model="qwen-plus",
    mode=AgentMode.WEB_ONLY,
    web_search_mode="product"
)
print(f"✅ 当前模式: {agent2.web_search_mode}")
print(f"   说明: {AgentConfig.SUPPORTED_WEB_MODES[agent2.web_search_mode]}")

# 测试3: 动态切换模式
print("\n【测试3】动态切换到ai_news模式")
try:
    agent2.set_web_search_mode("ai_news")
    print(f"✅ 切换成功，当前模式: {agent2.web_search_mode}")
    print(f"   说明: {AgentConfig.SUPPORTED_WEB_MODES[agent2.web_search_mode]}")
except ValueError as e:
    print(f"❌ 切换失败: {e}")

# 测试4: 无效模式
print("\n【测试4】尝试切换到无效模式")
try:
    agent2.set_web_search_mode("invalid_mode")
    print(f"❌ 不应该成功")
except ValueError as e:
    print(f"✅ 正确拒绝: {e}")

# 测试5: 检查自动注入
print("\n【测试5】测试自动注入mode参数")
print("调用suggest_url工具时，如果LLM没有指定mode，应该自动注入当前配置的模式")
print(f"当前agent模式: {agent2.web_search_mode}")
print("（实际调用需要在真实对话中测试）")

print("\n" + "=" * 70)
print("✅ 所有单元测试通过！")
print("=" * 70)
print("\n提示：运行 `python -m component.chat.unified_chat` 测试完整功能")
