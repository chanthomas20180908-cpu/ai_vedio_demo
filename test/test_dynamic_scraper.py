#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 测试数据或模块
Output: 测试结果
Pos: 测试文件：test_dynamic_scraper.py
"""

"""
测试动态网页爬取功能
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from component.chat.tools.web_tools import WebTools
from config.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def test_taobao_service_market():
    """测试淘宝服务市场页面爬取"""
    url = "https://fuwu.taobao.com/ser/list.htm?searchType=app&firstCategory=206478911&secondCategory=206476012&sort=default_sort&sortDesc=true&pageSize=30&currentPage=1&tracelog=category&spm=a1z13.fuwu_home_page_2023.0.0.55095aca9yDdaB"
    
    logger.info("=" * 70)
    logger.info("测试 1: 使用普通方法 fetch_url（预期失败）")
    logger.info("=" * 70)
    
    web_tools = WebTools(timeout=30, max_content_length=100000)
    
    result = web_tools.fetch_url(url, extract_main=False)
    
    if result.get('success'):
        logger.info(f"✅ 标题: {result['title']}")
        logger.info(f"✅ 内容长度: {result['content_length']} 字符")
        logger.info(f"✅ 内容预览: {result['content'][:200]}...")
    else:
        logger.error(f"❌ 错误: {result.get('error')}")
    
    logger.info("\n" + "=" * 70)
    logger.info("测试 2: 使用 Playwright 动态爬取 fetch_dynamic_url")
    logger.info("=" * 70)
    
    result = web_tools.fetch_dynamic_url(
        url=url,
        wait_time=5,  # 等待 5 秒让页面充分加载
        extract_main=False,  # 不提取主要内容，获取全部
        scroll_to_bottom=True  # 滚动到底部触发懒加载
    )
    
    if result.get('success'):
        logger.info(f"✅ 标题: {result['title']}")
        logger.info(f"✅ 内容长度: {result['content_length']} 字符")
        logger.info(f"✅ 截断: {result['truncated']}")
        logger.info(f"✅ 方法: {result.get('method')}")
        
        # 检查是否包含产品信息
        content = result['content']
        if 'AI' in content or '直播' in content or '服务' in content:
            logger.info("\n🎉 成功检测到产品相关内容！")
            
            # 提取部分关键信息
            lines = content.split('\n')[:50]  # 前50行
            logger.info("\n📄 内容预览（前50行）:")
            logger.info("-" * 70)
            for line in lines:
                if line.strip():
                    logger.info(line[:100])  # 每行最多100字符
        else:
            logger.warning("⚠️  未检测到明显的产品信息，可能需要调整等待时间")
    else:
        logger.error(f"❌ 错误: {result.get('error')}")
    
    logger.info("\n" + "=" * 70)
    logger.info("测试完成")
    logger.info("=" * 70)


if __name__ == "__main__":
    test_taobao_service_market()
