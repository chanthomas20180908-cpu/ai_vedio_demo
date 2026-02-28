"""
⚠️ 一旦我被更新，务必更新我的开头注释，以及所属的文件夹的md
Input: 测试数据或模块
Output: 测试结果
Pos: 测试文件：debug_sync_wan_t2i.py
"""

from data.test_prompt import TEST_T2I_PROMPT_003, TEST_T2I_PROMPT_004, TEST_T2I_PROMPT_005, TEST_T2I_PROMPT_006, \
    TEST_T2I_PROMPT_007, TEST_T2I_PROMPT_008
from component.muti.synthesis_image import sync_t2i_wan_v25


def debug_sync_t2i_wan_v25():
    import os
    from dotenv import load_dotenv
    from config.logging_config import setup_logging
    import webbrowser

    # 初始化日志
    setup_logging()

    # 加载环境变量
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../env/default.env"))
    api_key = os.getenv("DASHSCOPE_API_KEY")

    # 检查API密钥
    if not api_key:
        raise ValueError("未找到DashScope API密钥，请检查环境变量配置")

    # 测试万象2.5文生图
    print("=" * 50)
    print("测试 sync_t2i_wan_v25 (万象2.5文生图)")
    print("=" * 50)

    prompt2 = TEST_T2I_PROMPT_003

    image_path, image_url = sync_t2i_wan_v25(
        api_key=api_key,
        prompt=prompt2,
        negative_prompt="",
        size="1024*1024",
        seed=88,
        n=1
    )

    if image_url and image_path:
        print(f"✅ 生成成功!")
        print(f"   图片URL: {image_url}")
        print(f"   本地路径: {image_path}")
        # 去掉查询参数
        clean_image_path = image_path.split('?')[0]
        # 检查文件是否存在
        if os.path.exists(clean_image_path):
            webbrowser.open(f"file://{clean_image_path}")
        else:
            print("文件不存在，请检查路径是否正确。")

    else:
        print("❌ 生成失败")


if __name__ == "__main__":

    debug_sync_t2i_wan_v25()