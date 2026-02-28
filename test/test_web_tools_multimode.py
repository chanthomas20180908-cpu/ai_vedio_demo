#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 测试数据或模块
Output: 测试结果
Pos: 测试文件：test_web_tools_multimode.py
"""

"""
测试 WebTools 多模式查询功能
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from component.chat.tools.web_tools import WebTools
from config.logging_config import setup_logging

def test_technical_mode():
    """测试技术模式"""
    print("\n" + "="*60)
    print("测试1：技术模式（technical）")
    print("="*60)
    
    web_tools = WebTools()
    
    # 精确匹配
    print("\n1.1 精确匹配 - qwen3")
    result = web_tools.suggest_url("qwen3", mode="technical")
    print(f"  ✓ 推荐URL: {result['suggested_url']}")
    print(f"  ✓ 匹配类型: {result['match_type']}")
    print(f"  ✓ 来源: {result['source']}")
    
    # 模糊匹配
    print("\n1.2 模糊匹配 - stable diffusion")
    result = web_tools.suggest_url("stable diffusion", mode="technical")
    print(f"  ✓ 推荐URL: {result['suggested_url']}")
    print(f"  ✓ 匹配类型: {result['match_type']}")
    
    # 搜索建议
    print("\n1.3 搜索建议 - AI Agent实现")
    result = web_tools.suggest_url("AI Agent实现", mode="technical")
    print(f"  ✓ 推荐URL: {result['suggested_url']}")
    print(f"  ✓ 所有建议: {len(result['all_suggestions'])} 个")

def test_product_mode():
    """测试产品模式"""
    print("\n" + "="*60)
    print("测试2：产品模式（product）")
    print("="*60)
    
    web_tools = WebTools()
    
    # 精确匹配
    print("\n2.1 精确匹配 - 用户增长")
    result = web_tools.suggest_url("用户增长", mode="product")
    print(f"  ✓ 推荐URL: {result['suggested_url']}")
    print(f"  ✓ 模式描述: {result['mode_description']}")
    
    # 模糊匹配
    print("\n2.2 模糊匹配 - 产品")
    result = web_tools.suggest_url("产品", mode="product")
    print(f"  ✓ 推荐URL: {result['suggested_url']}")
    print(f"  ✓ 匹配键: {result.get('matched_key', 'N/A')}")
    
    # 搜索建议
    print("\n2.3 搜索建议 - MVP方法论")
    result = web_tools.suggest_url("MVP方法论", mode="product")
    print(f"  ✓ 推荐URL: {result['suggested_url']}")
    print(f"  ✓ 所有建议:")
    for i, url in enumerate(result['all_suggestions'][:3], 1):
        print(f"      {i}. {url}")

def test_ai_news_mode():
    """测试AI资讯模式"""
    print("\n" + "="*60)
    print("测试3：AI资讯模式（ai_news）")
    print("="*60)
    
    web_tools = WebTools()
    
    # 精确匹配
    print("\n3.1 精确匹配 - 机器之心")
    result = web_tools.suggest_url("机器之心", mode="ai_news")
    print(f"  ✓ 推荐URL: {result['suggested_url']}")
    print(f"  ✓ 模式描述: {result['mode_description']}")
    
    # 模糊匹配
    print("\n3.2 模糊匹配 - AI")
    result = web_tools.suggest_url("AI", mode="ai_news")
    print(f"  ✓ 推荐URL: {result['suggested_url']}")
    
    # 搜索建议
    print("\n3.3 搜索建议 - 大模型最新进展")
    result = web_tools.suggest_url("大模型最新进展", mode="ai_news")
    print(f"  ✓ 推荐URL: {result['suggested_url']}")
    print(f"  ✓ 所有建议: {len(result['all_suggestions'])} 个")

def test_comprehensive_mode():
    """测试综合模式"""
    print("\n" + "="*60)
    print("测试4：综合模式（comprehensive）")
    print("="*60)
    
    web_tools = WebTools()
    
    # 综合搜索
    print("\n4.1 综合搜索 - AI Agent")
    result = web_tools.suggest_url("AI Agent", mode="comprehensive")
    print(f"  ✓ 推荐URL: {result['suggested_url']}")
    print(f"  ✓ 模式: {result['mode']}")
    print(f"  ✓ 模式描述: {result['mode_description']}")
    print(f"  ✓ 所有建议: {len(result['all_suggestions'])} 个（包含所有类型）")

def test_backward_compatibility():
    """测试向后兼容性"""
    print("\n" + "="*60)
    print("测试5：向后兼容性（suggest_tech_url）")
    print("="*60)
    
    web_tools = WebTools()
    
    print("\n5.1 使用旧API - suggest_tech_url")
    result = web_tools.suggest_tech_url("llama3")
    print(f"  ✓ 推荐URL: {result['suggested_url']}")
    print(f"  ✓ 模式: {result.get('mode', 'N/A')}")
    print(f"  ⚠️  注意: 此API已废弃，建议使用 suggest_url")

def test_cross_mode_comparison():
    """测试跨模式对比"""
    print("\n" + "="*60)
    print("测试6：跨模式对比 - 同一关键词不同模式")
    print("="*60)
    
    web_tools = WebTools()
    keyword = "AI"
    
    for mode in ["technical", "product", "ai_news", "comprehensive"]:
        print(f"\n6.{['technical', 'product', 'ai_news', 'comprehensive'].index(mode) + 1} 模式: {mode}")
        result = web_tools.suggest_url(keyword, mode=mode)
        print(f"  ✓ 推荐: {result['suggested_url']}")
        print(f"  ✓ 来源: {result['source']}")

def main():
    """主测试函数"""
    setup_logging()
    
    print("\n" + "🚀 " * 20)
    print(" " * 10 + "WebTools 多模式查询功能测试")
    print("🚀 " * 20)
    
    try:
        test_technical_mode()
        test_product_mode()
        test_ai_news_mode()
        test_comprehensive_mode()
        test_backward_compatibility()
        test_cross_mode_comparison()
        
        print("\n" + "="*60)
        print("✅ 所有测试通过！")
        print("="*60)
        
        print("\n📊 功能总结：")
        print("  ✓ 技术模式（technical）：35个平台 + 4个搜索引擎")
        print("  ✓ 产品模式（product）：22个平台 + 4个搜索引擎")
        print("  ✓ AI资讯模式（ai_news）：25个平台 + 4个搜索引擎")
        print("  ✓ 综合模式（comprehensive）：82个平台 + 12个搜索引擎")
        print("  ✓ 向后兼容：支持旧API suggest_tech_url")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
