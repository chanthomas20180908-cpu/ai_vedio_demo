#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 测试数据或模块
Output: 测试结果
Pos: 测试文件：multimode_web_search_demo.py
"""

"""
多模式网络查询功能演示
展示如何在不同场景下使用多模式URL推荐
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from component.chat.tools.web_tools import WebTools
from config.logging_config import setup_logging

def demo_technical_search():
    """演示技术搜索"""
    print("\n" + "="*70)
    print("📚 场景1：技术调研 - 查找开源项目和技术文档")
    print("="*70)
    
    web_tools = WebTools()
    
    queries = [
        ("qwen3", "查找Qwen3大模型"),
        ("langchain", "查找LangChain框架"),
        ("AI Agent架构设计", "搜索AI Agent相关技术"),
    ]
    
    for keyword, desc in queries:
        print(f"\n🔍 {desc}: '{keyword}'")
        result = web_tools.suggest_url(keyword, mode="technical")
        print(f"   → {result['suggested_url']}")
        print(f"   类型: {result['match_type']}")

def demo_product_search():
    """演示产品搜索"""
    print("\n" + "="*70)
    print("💡 场景2：产品学习 - 查找产品方法论和案例")
    print("="*70)
    
    web_tools = WebTools()
    
    queries = [
        ("用户增长", "学习用户增长方法"),
        ("产品经理", "了解产品经理职责"),
        ("敏捷开发实践", "搜索敏捷开发案例"),
    ]
    
    for keyword, desc in queries:
        print(f"\n🔍 {desc}: '{keyword}'")
        result = web_tools.suggest_url(keyword, mode="product")
        print(f"   → {result['suggested_url']}")
        if result['match_type'] == 'search' and 'all_suggestions' in result:
            print(f"   更多选择: {len(result['all_suggestions'])}个平台")

def demo_ai_news_search():
    """演示AI资讯搜索"""
    print("\n" + "="*70)
    print("📰 场景3：AI资讯 - 关注行业动态和研究进展")
    print("="*70)
    
    web_tools = WebTools()
    
    queries = [
        ("机器之心", "访问机器之心"),
        ("量子位", "访问量子位"),
        ("GPT-5最新消息", "搜索GPT-5相关资讯"),
    ]
    
    for keyword, desc in queries:
        print(f"\n🔍 {desc}: '{keyword}'")
        result = web_tools.suggest_url(keyword, mode="ai_news")
        print(f"   → {result['suggested_url']}")
        print(f"   来源: {result['source']}")

def demo_comprehensive_search():
    """演示综合搜索"""
    print("\n" + "="*70)
    print("🌐 场景4：综合调研 - 全方位了解某个主题")
    print("="*70)
    
    web_tools = WebTools()
    
    keyword = "AI Agent"
    print(f"\n🔍 全面调研: '{keyword}'")
    result = web_tools.suggest_url(keyword, mode="comprehensive")
    
    print(f"   推荐: {result['suggested_url']}")
    print(f"   模式: {result['mode_description']}")
    
    if 'all_suggestions' in result:
        print(f"\n   📋 所有推荐平台 ({len(result['all_suggestions'])}个):")
        for i, url in enumerate(result['all_suggestions'][:5], 1):
            print(f"      {i}. {url}")
        if len(result['all_suggestions']) > 5:
            print(f"      ... 还有 {len(result['all_suggestions']) - 5} 个")

def demo_fetch_content():
    """演示获取网页内容"""
    print("\n" + "="*70)
    print("🌐 场景5：访问网页并获取内容")
    print("="*70)
    
    web_tools = WebTools()
    
    # 先获取推荐URL
    print("\n步骤1: 获取推荐URL")
    suggest_result = web_tools.suggest_url("机器之心", mode="ai_news")
    url = suggest_result['suggested_url']
    print(f"   推荐URL: {url}")
    
    # 再访问URL获取内容
    print("\n步骤2: 访问URL并获取内容")
    print("   正在访问...")
    fetch_result = web_tools.fetch_url(url)
    
    if fetch_result.get('success'):
        print(f"   ✅ 成功")
        print(f"   标题: {fetch_result['title']}")
        print(f"   内容长度: {fetch_result['content_length']} 字符")
        print(f"   内容预览: {fetch_result['content'][:100]}...")
    else:
        print(f"   ❌ 失败: {fetch_result.get('error')}")

def demo_mode_comparison():
    """演示不同模式对比"""
    print("\n" + "="*70)
    print("🔄 场景6：同一关键词在不同模式下的推荐")
    print("="*70)
    
    web_tools = WebTools()
    keyword = "AI"
    
    print(f"\n关键词: '{keyword}'\n")
    
    modes = [
        ("technical", "技术"),
        ("product", "产品"),
        ("ai_news", "资讯"),
    ]
    
    for mode, name in modes:
        result = web_tools.suggest_url(keyword, mode=mode)
        print(f"{name}模式:")
        print(f"  → {result['suggested_url']}")
        print(f"  匹配: {result['match_type']}\n")

def main():
    """主函数"""
    setup_logging()
    
    print("\n" + "🎯 " * 25)
    print(" " * 20 + "多模式网络查询功能演示")
    print("🎯 " * 25)
    
    print("\n这个演示展示了如何使用WebTools的多模式URL推荐功能")
    print("支持4种模式：technical（技术）、product（产品）、ai_news（资讯）、comprehensive（综合）")
    
    try:
        # 运行各个场景演示
        demo_technical_search()
        demo_product_search()
        demo_ai_news_search()
        demo_comprehensive_search()
        demo_fetch_content()
        demo_mode_comparison()
        
        print("\n" + "="*70)
        print("✅ 演示完成！")
        print("="*70)
        
        print("\n💡 使用提示：")
        print("1. 技术问题用 mode='technical'，会推荐GitHub、HuggingFace等")
        print("2. 产品问题用 mode='product'，会推荐人人都是产品经理、36氪等")
        print("3. 资讯查询用 mode='ai_news'，会推荐机器之心、量子位等")
        print("4. 不确定时用 mode='comprehensive'，会搜索所有类型网站")
        print("\n📚 详细文档: component/chat/tools/MULTIMODE_WEB_SEARCH_README.md")
        
    except Exception as e:
        print(f"\n❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
