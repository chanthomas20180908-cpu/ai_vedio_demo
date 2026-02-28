#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 测试数据或模块
Output: 测试结果
Pos: 测试文件：test_taobao_with_auth.py
"""

"""
淘宝服务市场爬取完整示例 - 使用Cookie认证
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from component.chat.tools.web_tools_with_auth import AuthenticatedWebTools
from config.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def step1_login():
    """步骤1：登录淘宝并保存Cookie（只需执行一次）"""
    print("\n" + "="*70)
    print("步骤 1: 登录淘宝并保存Cookie")
    print("="*70)
    print("\n这个步骤只需要执行一次，Cookie会保存到:")
    print("  ~/.cache/web_scraper/cookies/fuwu.taobao.com.json")
    print()
    
    auth_tools = AuthenticatedWebTools()
    
    # 登录淘宝服务市场
    result = auth_tools.login_and_save_cookies(
        url='https://fuwu.taobao.com/',
        domain='fuwu.taobao.com'
    )
    
    if result.get('success'):
        print(f"\n✅ Cookie保存成功！")
        print(f"  文件: {result['cookies_file']}")
        print(f"  数量: {result['cookies_count']} 个Cookie")
        print(f"\n现在可以继续执行步骤2")
    else:
        print(f"\n❌ Cookie保存失败: {result.get('error')}")


def step2_check_cookies():
    """步骤2：检查已保存的Cookie"""
    print("\n" + "="*70)
    print("步骤 2: 检查已保存的Cookie")
    print("="*70)
    
    auth_tools = AuthenticatedWebTools()
    saved = auth_tools.list_saved_cookies()
    
    if saved:
        print(f"\n已保存 {len(saved)} 个域名的Cookie:")
        for item in saved:
            print(f"\n域名: {item['domain']}")
            print(f"  保存时间: {item['saved_at']} ({item['age_days']:.1f}天前)")
            print(f"  Cookie数: {item['cookies_count']}")
            
            if item['age_days'] > 7:
                print(f"  ⚠️  Cookie已保存超过7天，建议重新登录")
    else:
        print("\n⚠️  暂无保存的Cookie，请先执行步骤1")


def step3_fetch_product():
    """步骤3：使用Cookie爬取产品详情"""
    print("\n" + "="*70)
    print("步骤 3: 爬取产品详情")
    print("="*70)
    
    auth_tools = AuthenticatedWebTools()
    
    # 测试URL列表
    urls = [
        'https://fuwu.taobao.com/ser/detail.htm?serviceCode=record_2023102415565795811856&tracelog=searchlist',
        'https://fuwu.taobao.com/ser/detail.htm?serviceCode=record_2023121315303472244964&tracelog=searchlist',
    ]
    
    for i, url in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}] 爬取: {url}")
        print("-" * 70)
        
        result = auth_tools.fetch_authenticated_url(
            url=url,
            domain='fuwu.taobao.com',
            wait_time=8,  # 等待8秒让页面充分加载
            extract_main=False,  # 获取全部内容
            scroll_to_bottom=True,
            screenshot=True  # 保存截图以便调试
        )
        
        if result.get('success'):
            print(f"✅ 成功获取内容")
            print(f"  标题: {result['title']}")
            print(f"  内容长度: {result['content_length']} 字符")
            if result.get('screenshot'):
                print(f"  截图: {result['screenshot']}")
            
            # 显示内容预览
            content = result['content']
            print(f"\n内容预览（前500字符）:")
            print("-" * 70)
            print(content[:500])
            
            # 检查关键词
            keywords = ['价格', '功能', '服务', '评价', '购买', '详情']
            print(f"\n关键词检测:")
            for kw in keywords:
                count = content.count(kw)
                status = "✅" if count > 0 else "❌"
                print(f"  {status} '{kw}': {count} 次")
        else:
            print(f"❌ 爬取失败: {result.get('error')}")
        
        print()


def main():
    """主函数 - 交互式菜单"""
    print("\n" + "="*70)
    print("🔐 淘宝服务市场认证爬取工具")
    print("="*70)
    
    while True:
        print("\n请选择操作:")
        print("  1. 登录淘宝并保存Cookie（首次使用必须执行）")
        print("  2. 查看已保存的Cookie")
        print("  3. 爬取产品详情（需要先登录）")
        print("  4. 退出")
        
        choice = input("\n请输入选项 (1-4): ").strip()
        
        if choice == '1':
            step1_login()
        elif choice == '2':
            step2_check_cookies()
        elif choice == '3':
            step3_fetch_product()
        elif choice == '4':
            print("\n👋 再见！")
            break
        else:
            print("\n❌ 无效选项，请重新选择")


if __name__ == "__main__":
    main()
