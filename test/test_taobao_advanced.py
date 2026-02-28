#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 测试数据或模块
Output: 测试结果
Pos: 测试文件：test_taobao_advanced.py
"""

"""
增强版淘宝服务市场爬取 - 处理反爬虫
"""
import sys
from pathlib import Path
import time

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from config.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def fetch_taobao_product_detail(url: str, wait_time: int = 10):
    """
    使用增强策略爬取淘宝产品详情
    
    Args:
        url: 产品详情页URL
        wait_time: 等待时间（秒）
    """
    logger.info(f"开始爬取淘宝产品页面: {url}")
    
    with sync_playwright() as p:
        # 使用更真实的浏览器环境
        browser = p.chromium.launch(
            headless=False,  # 先用有头模式调试
            args=[
                '--disable-blink-features=AutomationControlled',  # 禁用自动化检测
            ]
        )
        
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='zh-CN',
            timezone_id='Asia/Shanghai',
            # 添加更多真实浏览器特征
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
            }
        )
        
        page = context.new_page()
        
        # 移除 webdriver 标志
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // 添加更多浏览器特征
            window.chrome = {
                runtime: {}
            };
        """)
        
        try:
            logger.info(f"访问页面: {url}")
            page.goto(url, wait_until='networkidle', timeout=30000)
            
            logger.info(f"等待 {wait_time} 秒让页面完全加载...")
            time.sleep(wait_time)
            
            # 尝试滚动页面
            logger.info("滚动页面以触发懒加载...")
            for i in range(3):
                page.evaluate('window.scrollBy(0, 500)')
                time.sleep(1)
            
            # 滚动回顶部
            page.evaluate('window.scrollTo(0, 0)')
            time.sleep(2)
            
            # 获取页面标题
            title = page.title()
            logger.info(f"页面标题: {title}")
            
            # 获取HTML内容
            html_content = page.content()
            
            # 保存HTML到文件用于调试
            debug_file = Path("/tmp/taobao_debug.html")
            debug_file.write_text(html_content, encoding='utf-8')
            logger.info(f"HTML已保存到: {debug_file}")
            
            # 截图
            screenshot_path = "/tmp/taobao_screenshot.png"
            page.screenshot(path=screenshot_path, full_page=True)
            logger.info(f"截图已保存: {screenshot_path}")
            
            # 解析HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 查找产品信息的常见区域
            logger.info("\n尝试提取产品信息...")
            
            # 方法1: 通过ID查找
            main_content = soup.find('div', id='page')
            if main_content:
                logger.info("找到主内容区域 (by id='page')")
            
            # 方法2: 通过class查找
            if not main_content:
                main_content = soup.find('div', class_='content')
                if main_content:
                    logger.info("找到主内容区域 (by class='content')")
            
            # 方法3: 查找所有文本
            all_text = soup.get_text(separator='\n', strip=True)
            
            logger.info(f"\n页面总文本长度: {len(all_text)} 字符")
            logger.info("\n前2000字符预览:")
            logger.info("-" * 70)
            print(all_text[:2000])
            
            # 查找特定关键词
            keywords = ['价格', '功能', '服务', '评价', '购买', '详情', '介绍']
            logger.info("\n关键词出现情况:")
            for kw in keywords:
                count = all_text.count(kw)
                logger.info(f"  '{kw}': {count} 次")
            
            return {
                'success': True,
                'title': title,
                'content': all_text,
                'content_length': len(all_text),
                'html_file': str(debug_file),
                'screenshot': screenshot_path
            }
            
        except Exception as e:
            logger.error(f"爬取失败: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
        
        finally:
            input("\n按回车键关闭浏览器...")
            browser.close()


def test_multiple_urls():
    """测试多个产品URL"""
    urls = [
        'https://fuwu.taobao.com/ser/detail.htm?serviceCode=record_2023102415565795811856&tracelog=searchlist',
        'https://fuwu.taobao.com/ser/detail.htm?serviceCode=record_2023121315303472244964&tracelog=searchlist',
    ]
    
    for i, url in enumerate(urls, 1):
        logger.info(f"\n{'='*70}")
        logger.info(f"测试 {i}/{len(urls)}: {url}")
        logger.info("="*70)
        
        result = fetch_taobao_product_detail(url, wait_time=10)
        
        if result.get('success'):
            logger.info(f"\n✅ 成功")
            logger.info(f"  标题: {result['title']}")
            logger.info(f"  内容长度: {result['content_length']}")
            logger.info(f"  HTML文件: {result['html_file']}")
            logger.info(f"  截图: {result['screenshot']}")
        else:
            logger.error(f"\n❌ 失败: {result.get('error')}")
        
        if i < len(urls):
            logger.info("\n等待5秒后继续...")
            time.sleep(5)


if __name__ == "__main__":
    test_multiple_urls()
